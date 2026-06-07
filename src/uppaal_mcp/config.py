from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from .paths import is_windows_path, windows_to_wsl_path


DEFAULT_WINDOWS_VERIFYTA = r"C:\Program Files (x86)\UPPAAL-5.0.0\bin\verifyta.exe"
DEFAULT_WSL_VERIFYTA = "/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe"


@dataclass(frozen=True)
class UppaalConfig:
    verifyta_path: str
    workspace: Path
    timeout_sec: float = 60.0

    @classmethod
    def from_env(
        cls,
        verifyta_path: str | None = None,
        workspace: str | Path | None = None,
        timeout_sec: float | None = None,
    ) -> "UppaalConfig":
        resolved_verifyta = resolve_verifyta_path(
            verifyta_path
            or os.getenv("UPPAAL_VERIFYTA_PATH")
            or os.getenv("VERIFYTA_PATH")
        )
        resolved_workspace = Path(
            workspace
            or os.getenv("UPPAAL_MCP_WORKSPACE")
            or Path.cwd() / ".uppaal_mcp_workspace"
        ).expanduser()
        resolved_timeout = float(
            timeout_sec
            if timeout_sec is not None
            else os.getenv("UPPAAL_TIMEOUT_SEC", "60")
        )
        return cls(
            verifyta_path=resolved_verifyta,
            workspace=resolved_workspace,
            timeout_sec=resolved_timeout,
        )


def resolve_verifyta_path(candidate: str | None = None) -> str:
    if candidate:
        return _normalize_candidate(candidate)

    for item in (DEFAULT_WSL_VERIFYTA, DEFAULT_WINDOWS_VERIFYTA):
        normalized = _normalize_candidate(item)
        if Path(normalized).exists():
            return normalized

    for executable in ("verifyta", "verifyta.exe"):
        found = shutil.which(executable)
        if found:
            return found

    return _normalize_candidate(DEFAULT_WINDOWS_VERIFYTA)


def _normalize_candidate(candidate: str) -> str:
    candidate = candidate.strip().strip('"')
    if os.name != "nt" and is_windows_path(candidate):
        return windows_to_wsl_path(candidate)
    return candidate
