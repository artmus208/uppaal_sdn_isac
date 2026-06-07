from __future__ import annotations

import hashlib
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .config import UppaalConfig
from .paths import local_path, path_for_verifyta_arg
from .validation import (
    load_text,
    parse_queries_text,
    query_text_from_model_or_query,
    validate_model_text,
)

VERIFYTA_OPTION_PRESETS: dict[str, list[str]] = {
    "normal": [],
    "trace_on_violation": ["-t0"],
    "diagnostic": ["-t0"],
}


@dataclass
class QueryOutcome:
    index: int
    formula: str | None
    status: str
    raw_line: str


@dataclass
class VerificationResult:
    status: str
    returncode: int | None
    command: list[str]
    model_path: str | None
    query_path: str | None
    stdout: str = ""
    stderr: str = ""
    elapsed_ms: int | None = None
    timeout_sec: float | None = None
    query_results: list[QueryOutcome] = field(default_factory=list)
    validation: dict | None = None
    artifact_dir: str | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["query_results"] = [asdict(item) for item in self.query_results]
        return data


class VerifytaRunner:
    def __init__(self, config: UppaalConfig | None = None) -> None:
        self.config = config or UppaalConfig.from_env()

    def get_version(self) -> VerificationResult:
        command = [self.config.verifyta_path, "--version"]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except FileNotFoundError as exc:
            return VerificationResult(
                status="tool_not_found",
                returncode=None,
                command=command,
                model_path=None,
                query_path=None,
                stderr=str(exc),
            )
        except subprocess.TimeoutExpired as exc:
            return VerificationResult(
                status="timeout",
                returncode=None,
                command=command,
                model_path=None,
                query_path=None,
                stdout=_to_text(exc.stdout),
                stderr=_to_text(exc.stderr),
                timeout_sec=15,
            )
        return VerificationResult(
            status="ok" if completed.returncode == 0 else "error",
            returncode=completed.returncode,
            command=command,
            model_path=None,
            query_path=None,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    def validate(
        self,
        *,
        model_xml: str | None = None,
        model_path: str | Path | None = None,
        queries: str | None = None,
        query_path: str | Path | None = None,
    ) -> dict:
        loaded_model, _ = load_text(text=model_xml, path=model_path, label="model")
        if loaded_model is None:
            raise ValueError("Pass model_xml or model_path.")
        loaded_queries, _ = load_text(text=queries, path=query_path, label="query")
        return validate_model_text(loaded_model, loaded_queries).to_dict()

    def verify(
        self,
        *,
        model_xml: str | None = None,
        model_path: str | Path | None = None,
        queries: str | None = None,
        query_path: str | Path | None = None,
        options: list[str] | None = None,
        options_preset: str | None = None,
        timeout_sec: float | None = None,
        keep_artifacts: bool = True,
    ) -> VerificationResult:
        loaded_model, source_model_path = load_text(
            text=model_xml,
            path=model_path,
            label="model",
        )
        if loaded_model is None and source_model_path is None:
            raise ValueError("Pass model_xml or model_path.")

        loaded_queries, source_query_path = load_text(
            text=queries,
            path=query_path,
            label="query",
        )
        if loaded_queries is None and loaded_model:
            loaded_queries = query_text_from_model_or_query(loaded_model, None)

        if loaded_queries is None and source_query_path is None:
            raise ValueError("Pass queries/query_path or embed <queries> in model_xml.")

        validation = None
        if loaded_model is not None:
            validation = validate_model_text(loaded_model, loaded_queries).to_dict()

        artifact_dir: Path | None = None
        model_file: Path
        query_file: Path
        if loaded_model is not None or loaded_queries is not None:
            artifact_dir = self._make_artifact_dir(loaded_model or "", loaded_queries or "")
            model_file = artifact_dir / "model.xml"
            query_file = artifact_dir / "queries.q"
            if loaded_model is not None:
                model_file.write_text(loaded_model, encoding="utf-8")
            else:
                model_file = local_path(source_model_path or "")
            if loaded_queries is not None:
                query_file.write_text(loaded_queries, encoding="utf-8")
            else:
                query_file = local_path(source_query_path or "")
        else:
            model_file = local_path(source_model_path or "")
            query_file = local_path(source_query_path or "")

        formulas = (
            parse_queries_text(loaded_queries)
            if loaded_queries is not None
            else parse_queries_text(query_file.read_text(encoding="utf-8"))
        )

        resolved_options = resolve_verifyta_options(options=options, options_preset=options_preset)
        command = [
            self.config.verifyta_path,
            *resolved_options,
            path_for_verifyta_arg(model_file, self.config.verifyta_path),
            path_for_verifyta_arg(query_file, self.config.verifyta_path),
        ]
        timeout = float(timeout_sec if timeout_sec is not None else self.config.timeout_sec)

        started = datetime.now(timezone.utc)
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            return VerificationResult(
                status="tool_not_found",
                returncode=None,
                command=command,
                model_path=str(model_file),
                query_path=str(query_file),
                stderr=str(exc),
                timeout_sec=timeout,
                validation=validation,
                artifact_dir=str(artifact_dir) if artifact_dir and keep_artifacts else None,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = _elapsed_ms(started)
            return VerificationResult(
                status="timeout",
                returncode=None,
                command=command,
                model_path=str(model_file),
                query_path=str(query_file),
                stdout=_to_text(exc.stdout),
                stderr=_to_text(exc.stderr),
                elapsed_ms=elapsed,
                timeout_sec=timeout,
                validation=validation,
                artifact_dir=str(artifact_dir) if artifact_dir and keep_artifacts else None,
            )

        outcomes = parse_verifyta_outcomes(completed.stdout, formulas)
        status = summarize_status(completed.returncode, outcomes, completed.stdout, completed.stderr)
        return VerificationResult(
            status=status,
            returncode=completed.returncode,
            command=command,
            model_path=str(model_file),
            query_path=str(query_file),
            stdout=completed.stdout,
            stderr=completed.stderr,
            elapsed_ms=_elapsed_ms(started),
            timeout_sec=timeout,
            query_results=outcomes,
            validation=validation,
            artifact_dir=str(artifact_dir) if artifact_dir and keep_artifacts else None,
        )

    def verify_batch(
        self,
        items: list[dict],
        *,
        options: list[str] | None = None,
        options_preset: str | None = None,
        timeout_sec: float | None = None,
    ) -> list[dict]:
        results: list[dict] = []
        for item in items:
            result = self.verify(
                model_xml=item.get("model_xml"),
                model_path=item.get("model_path"),
                queries=item.get("queries"),
                query_path=item.get("query_path"),
                options=item.get("options", options),
                options_preset=item.get("options_preset", options_preset),
                timeout_sec=item.get("timeout_sec", timeout_sec),
                keep_artifacts=item.get("keep_artifacts", True),
            )
            data = result.to_dict()
            if "name" in item:
                data["name"] = item["name"]
            results.append(data)
        return results

    def _make_artifact_dir(self, model_xml: str, queries: str) -> Path:
        self.config.workspace.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256((model_xml + "\n---queries---\n" + queries).encode()).hexdigest()[:12]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self.config.workspace / "runs" / f"{timestamp}-{digest}-{uuid4().hex[:8]}"
        path.mkdir(parents=True, exist_ok=False)
        return path


def resolve_verifyta_options(
    *,
    options: list[str] | None = None,
    options_preset: str | None = None,
) -> list[str]:
    preset_name = (options_preset or "normal").strip().lower()
    if preset_name not in VERIFYTA_OPTION_PRESETS:
        allowed = ", ".join(sorted(VERIFYTA_OPTION_PRESETS))
        raise ValueError(f"Unsupported verifyta options_preset {options_preset!r}. Use one of: {allowed}.")
    return [*VERIFYTA_OPTION_PRESETS[preset_name], *(options or [])]


def parse_verifyta_outcomes(stdout: str, formulas: list[str]) -> list[QueryOutcome]:
    outcomes: list[QueryOutcome] = []
    for line in stdout.splitlines():
        lowered = line.lower()
        status = None
        if "formula is not satisfied" in lowered:
            status = "not_satisfied"
        elif "formula is satisfied" in lowered:
            status = "satisfied"
        elif "formula may be satisfied" in lowered or "formula is maybe satisfied" in lowered:
            status = "maybe"
        elif "formula is inconclusive" in lowered:
            status = "inconclusive"
        if status:
            index = len(outcomes) + 1
            formula = formulas[index - 1] if index - 1 < len(formulas) else None
            outcomes.append(
                QueryOutcome(
                    index=index,
                    formula=formula,
                    status=status,
                    raw_line=line.strip(),
                )
            )
    return outcomes


def summarize_status(
    returncode: int,
    outcomes: list[QueryOutcome],
    stdout: str,
    stderr: str,
) -> str:
    if outcomes:
        statuses = {outcome.status for outcome in outcomes}
        if "not_satisfied" in statuses:
            return "not_satisfied"
        if statuses == {"satisfied"}:
            return "satisfied"
        if "maybe" in statuses or "inconclusive" in statuses:
            return "inconclusive"
        return "mixed"
    combined = f"{stdout}\n{stderr}".lower()
    if returncode != 0:
        return "error"
    if "syntax error" in combined or "error" in combined:
        return "error"
    return "unknown"


def _elapsed_ms(started: datetime) -> int:
    return int((datetime.now(timezone.utc) - started).total_seconds() * 1000)


def _to_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
