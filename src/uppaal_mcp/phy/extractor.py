from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from .defaults import SOURCE, build_default_contract
from .ir import PhyContractModel


@dataclass(frozen=True)
class LatexSection:
    level: str
    title: str
    start_line: int
    end_line: int

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "title": self.title,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "line_count": self.end_line - self.start_line + 1,
        }


@dataclass(frozen=True)
class VerbatimBlock:
    start_line: int
    end_line: int
    text: str

    def to_dict(self) -> dict:
        return {
            "start_line": self.start_line,
            "end_line": self.end_line,
            "line_count": self.end_line - self.start_line + 1,
        }


@dataclass
class ExtractionReport:
    source_name: str
    source_hash: str
    line_count: int
    sections: list[LatexSection]
    verbatim_blocks: list[VerbatimBlock]
    compositions: dict[str, dict]
    x_disc: dict[str, object]
    clock_resets: dict[str, dict]
    invariants: dict[str, dict]
    automata_sketches: dict[str, dict]
    env_sketches: dict[str, dict]
    assume_guarantee: dict[str, dict]
    channels: dict[str, str]
    class_sets: dict[str, list[str]]
    queries: list[str]
    marker_lines: dict[str, list[int]]
    diagnostics: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.diagnostics

    def to_dict(self) -> dict:
        expected = _expected_counts()
        found = {
            "sections": len(self.sections),
            "verbatim_blocks": len(self.verbatim_blocks),
            "compositions": len(self.compositions),
            "x_disc_variables": len(self.x_disc.get("variables", [])),
            "clock_resets": len(self.clock_resets),
            "invariants": len(self.invariants),
            "automata_sketches": len(self.automata_sketches),
            "env_sketches": len(self.env_sketches),
            "assume_guarantee": len(self.assume_guarantee),
            "channels": len(self.channels),
            "class_sets": len(self.class_sets),
            "queries": len(self.queries),
            "markers": sum(1 for lines in self.marker_lines.values() if lines),
        }
        return {
            "ok": self.ok,
            "mode": "section-aware-article-extractor",
            "source_name": self.source_name,
            "source_hash": self.source_hash,
            "line_count": self.line_count,
            "sections": [item.to_dict() for item in self.sections],
            "verbatim_blocks": [item.to_dict() for item in self.verbatim_blocks],
            "compositions": dict(sorted(self.compositions.items())),
            "x_disc": self.x_disc,
            "clock_resets": dict(sorted(self.clock_resets.items())),
            "invariants": dict(sorted(self.invariants.items())),
            "automata_sketches": dict(sorted(self.automata_sketches.items())),
            "env_sketches": dict(sorted(self.env_sketches.items())),
            "assume_guarantee": dict(sorted(self.assume_guarantee.items())),
            "channels": dict(sorted(self.channels.items())),
            "class_sets": dict(sorted(self.class_sets.items())),
            "queries": list(self.queries),
            "marker_lines": {key: list(value) for key, value in sorted(self.marker_lines.items())},
            "diagnostics": list(self.diagnostics),
            "coverage": {
                "found": found,
                "expected": expected,
                "channel_coverage": _ratio(found["channels"], expected["channels"]),
                "class_coverage": _ratio(found["class_sets"], expected["classes"]),
                "query_coverage": _ratio(found["queries"], expected["queries"]),
                "composition_coverage": _ratio(found["compositions"], expected["compositions"]),
                "clock_coverage": _ratio(found["clock_resets"], expected["clocks"]),
                "invariant_coverage": _ratio(found["invariants"], expected["invariants"]),
                "automata_sketch_coverage": _ratio(found["automata_sketches"], expected["automata"]),
                "environment_sketch_coverage": _ratio(found["env_sketches"], expected["environment"]),
                "assume_guarantee_coverage": _ratio(found["assume_guarantee"], expected["automata"]),
            },
            "note": (
                "The extractor derives article structure, channels, class sets, queries, "
                "composition formulas, X_disc, clocks, invariants, automata/environment "
                "sketches, and assume/guarantee evidence from LaTeX, then binds them to "
                "the canonical PHY IR."
            ),
        }


SECTION_RE = re.compile(r"\\(?P<level>section|subsection|subsubsection)\*?\{(?P<title>[^}]*)\}")
QUERY_RE = re.compile(r"(?P<formula>(?:A\[\]|E<>)\s+.+)")
CHANNEL_RE = re.compile(r"^(?P<broadcast>broadcast\s+)?chan\s+(?P<names>[^;]+);")

COMPOSITION_NAMES = ("A_PHY", "A_SYS", "A_ENV")
REQUIRED_INVARIANTS = {
    "MeasurePending": "c_meas <= T_meas + J_meas",
    "SignalReconfiguring": "c_sig <= D_sig",
    "SensingEvaluating": "c_sense <= D_sense",
    "PHYKpiReporting": "c_report <= D_report",
    "BeamRecover": "c_rec <= D_BM",
}


REQUIRED_SECTION_PATTERNS: dict[str, list[str]] = {
    "base_model": [r"Base", r"Базовая модель"],
    "alpha_phy": [r"alpha", r"Абстракция"],
    "assume_guarantee": [r"assume", r"контракт"],
    "operational_semantics": [r"Operational semantics"],
    "phy_automata": [r"Автоматы PHY"],
    "reports": [r"отчет", r"штраф"],
    "verification": [r"observer", r"Верификационные"],
}


REQUIRED_MARKERS: dict[str, tuple[str, list[str]]] = {
    "A_PHY": ("composition", [r"\\A\{PHY\}", r"\bA_PHY\b", r"A\\_PHY"]),
    "A_ENV": ("composition", [r"\\A\{ENV\}", r"\bA_ENV\b", r"A\\_ENV"]),
    "A_SYS": ("composition", [r"\\A\{SYS\}", r"\bA_SYS\b", r"A\\_SYS"]),
    "alpha_PHY": ("alpha", [r"\\alpha_\{PHY\}", r"alpha_PHY", r"alpha_\{PHY\}"]),
    "no_continuous_guards": ("alpha", [r"guards.*class", r"guards.*класс"]),
    "Pi_PHY_external": ("alpha", [r"\\Pi_\{PHY\}", r"Pi_PHY"]),
    "A_CH": ("automata", [r"\\A\{CH\}", r"\bA_CH\b", r"A\\_CH"]),
    "A_SIG": ("automata", [r"\\A\{SIG\}", r"\bA_SIG\b", r"A\\_SIG"]),
    "A_BM": ("automata", [r"\\A\{BM\}", r"\bA_BM\b", r"A\\_BM"]),
    "A_SQ": ("automata", [r"\\A\{SQ\}", r"\bA_SQ\b", r"A\\_SQ"]),
    "A_PH": ("automata", [r"\\A\{PH\}", r"\bA_PH\b", r"A\\_PH"]),
    "ENV_CH": ("environment", [r"\bENV_CH\b", r"ENV\\_CH"]),
    "ENV_TARGET": ("environment", [r"\bENV_TARGET\b", r"ENV\\_TARGET"]),
    "ENV_MAC": ("environment", [r"\bENV_MAC\b", r"ENV\\_MAC"]),
    "ENV_NET": ("environment", [r"\bENV_NET\b", r"ENV\\_NET"]),
    "ObsSenseReport": ("observer", [r"\bObsSenseReport\b"]),
    "ObsFreshness": ("observer", [r"\bObsFreshness\b"]),
    "ObsBeamRecovery": ("observer", [r"\bObsBeamRecovery\b"]),
}


def extract_contract_model(tex_text: str, *, source_name: str = SOURCE) -> dict:
    contract = build_default_contract()
    report = analyze_latex(tex_text, source_name=source_name, contract=contract)
    data = contract.to_dict()
    data["extractor"] = report.to_dict()
    return data


def analyze_latex(
    tex_text: str,
    *,
    source_name: str = SOURCE,
    contract: PhyContractModel | None = None,
) -> ExtractionReport:
    model = contract or build_default_contract()
    source_hash = hashlib.sha256(tex_text.encode("utf-8")).hexdigest()
    sections = parse_latex_sections(tex_text)
    verbatim = parse_verbatim_blocks(tex_text)
    compositions = extract_compositions(tex_text)
    x_disc = extract_x_disc(tex_text, model)
    clock_resets = extract_clock_resets(tex_text)
    invariants = extract_invariants(tex_text)
    automata_sketches = extract_automata_sketches(tex_text, sections, verbatim, model)
    env_sketches = extract_environment_sketches(verbatim)
    assume_guarantee = extract_assume_guarantee(tex_text, verbatim)
    channels = extract_channel_declarations(verbatim)
    class_sets = extract_class_sets(tex_text, model)
    queries = extract_queries(verbatim)
    marker_lines = find_marker_lines(tex_text)
    diagnostics = _diagnostics(
        tex_text=tex_text,
        sections=sections,
        compositions=compositions,
        x_disc=x_disc,
        clock_resets=clock_resets,
        invariants=invariants,
        automata_sketches=automata_sketches,
        env_sketches=env_sketches,
        assume_guarantee=assume_guarantee,
        channels=channels,
        class_sets=class_sets,
        queries=queries,
        marker_lines=marker_lines,
        contract=model,
    )
    return ExtractionReport(
        source_name=source_name,
        source_hash=source_hash,
        line_count=len(tex_text.splitlines()),
        sections=sections,
        verbatim_blocks=verbatim,
        compositions=compositions,
        x_disc=x_disc,
        clock_resets=clock_resets,
        invariants=invariants,
        automata_sketches=automata_sketches,
        env_sketches=env_sketches,
        assume_guarantee=assume_guarantee,
        channels=channels,
        class_sets=class_sets,
        queries=queries,
        marker_lines=marker_lines,
        diagnostics=diagnostics,
    )


def parse_latex_sections(tex_text: str) -> list[LatexSection]:
    lines = tex_text.splitlines()
    starts: list[tuple[str, str, int]] = []
    for line_no, line in enumerate(lines, start=1):
        for match in SECTION_RE.finditer(line):
            starts.append((match.group("level"), match.group("title"), line_no))
    sections: list[LatexSection] = []
    for index, (level, title, start_line) in enumerate(starts):
        next_start = starts[index + 1][2] if index + 1 < len(starts) else len(lines) + 1
        sections.append(LatexSection(level=level, title=title, start_line=start_line, end_line=next_start - 1))
    return sections


def parse_verbatim_blocks(tex_text: str) -> list[VerbatimBlock]:
    blocks: list[VerbatimBlock] = []
    in_block = False
    start_line = 0
    body: list[str] = []
    for line_no, line in enumerate(tex_text.splitlines(), start=1):
        if r"\begin{verbatim}" in line:
            in_block = True
            start_line = line_no + 1
            body = []
            continue
        if r"\end{verbatim}" in line and in_block:
            blocks.append(VerbatimBlock(start_line=start_line, end_line=line_no - 1, text="\n".join(body)))
            in_block = False
            continue
        if in_block:
            body.append(line)
    return blocks


def extract_channel_declarations(blocks: list[VerbatimBlock]) -> dict[str, str]:
    channels: dict[str, str] = {}
    for block in blocks:
        for line in block.text.splitlines():
            match = CHANNEL_RE.match(line.strip())
            if not match:
                continue
            kind = "broadcast" if match.group("broadcast") else "handshake"
            for name in match.group("names").split(","):
                normalized = _normalize_identifier(name.strip())
                if normalized:
                    channels[normalized] = kind
    return channels


def extract_queries(blocks: list[VerbatimBlock]) -> list[str]:
    queries: list[str] = []
    seen: set[str] = set()
    for block in blocks:
        for line in block.text.splitlines():
            match = QUERY_RE.search(line.strip())
            if not match:
                continue
            query = _normalize_query(match.group("formula"))
            if query not in seen:
                queries.append(query)
                seen.add(query)
    return queries


def extract_compositions(tex_text: str) -> dict[str, dict]:
    lines = tex_text.splitlines()
    compositions: dict[str, dict] = {}
    targets = {
        "A_PHY": r"\A{PHY}",
        "A_SYS": r"\A{SYS}",
        "A_ENV": r"\A{ENV}",
    }
    for target, marker in targets.items():
        left_hand = re.compile(rf"{re.escape(marker)}\s*=")
        for index, line in enumerate(lines):
            if not left_hand.search(line):
                continue
            block = _collect_latex_block(lines, index)
            expression = _normalize_latex_text(" ".join(block))
            expression = _compact_spaces(expression)
            components = _composition_components(target, expression)
            compositions[target] = {
                "line": index + 1,
                "expression": expression,
                "components": components,
            }
            break
    return compositions


def extract_x_disc(tex_text: str, contract: PhyContractModel | None = None) -> dict[str, object]:
    model = contract or build_default_contract()
    lines = tex_text.splitlines()
    variables: list[str] = []
    start_line = None
    end_line = None
    for index, line in enumerate(lines):
        if r"X_{disc}" not in line or "=" not in line:
            continue
        block = _collect_latex_block(lines, index)
        start_line = index + 1
        end_line = index + len(block)
        normalized = _normalize_latex_text(" ".join(block))
        for name in re.findall(r"\b[A-Za-z][A-Za-z0-9_]*(?:Class|State)\b", normalized):
            if name not in variables:
                variables.append(name)
        break
    expected = [item.name for item in model.classes]
    return {
        "line": start_line,
        "end_line": end_line,
        "variables": variables,
        "class_sets": extract_class_sets(tex_text, model),
        "missing_from_formula": [name for name in expected if name not in variables],
        "unexpected_in_formula": [name for name in variables if name not in expected],
    }


def extract_clock_resets(tex_text: str) -> dict[str, dict]:
    clocks: dict[str, dict] = {}
    in_clock_table = False
    for line_no, line in enumerate(tex_text.splitlines(), start=1):
        if "Clock &" in line and "Reset" in line:
            in_clock_table = True
            continue
        if in_clock_table and r"\end{longtable}" in line:
            break
        if not in_clock_table:
            continue
        match = re.search(
            r"\\\((?P<clock>[^)]*)\\\)\s*&\s*(?P<meaning>.*?)\s*&\s*(?P<reset>.*?)\\\\",
            line,
        )
        if not match:
            continue
        name = _normalize_identifier(match.group("clock"))
        clocks[name] = {
            "line": line_no,
            "meaning": _normalize_latex_text(match.group("meaning")),
            "reset": _normalize_latex_text(match.group("reset")),
        }
    return clocks


def extract_invariants(tex_text: str) -> dict[str, dict]:
    invariants: dict[str, dict] = {}
    pattern = re.compile(r"Inv\(\\code\{(?P<location>[^}]*)\}\)&:\s*(?P<formula>.*?)(?:,?\\\\|\.)")
    for line_no, line in enumerate(tex_text.splitlines(), start=1):
        match = pattern.search(line)
        if not match:
            continue
        formula = _normalize_latex_text(match.group("formula"))
        bound = None
        bound_match = re.search(r"<=\s*(?P<bound>[A-Za-z0-9_+ ]+)", formula)
        if bound_match:
            bound = _compact_spaces(bound_match.group("bound"))
        invariants[match.group("location")] = {
            "line": line_no,
            "formula": _compact_spaces(formula),
            "bound": bound,
        }
    return invariants


def extract_automata_sketches(
    tex_text: str,
    sections: list[LatexSection],
    blocks: list[VerbatimBlock],
    contract: PhyContractModel | None = None,
) -> dict[str, dict]:
    model = contract or build_default_contract()
    sketches: dict[str, dict] = {}
    lines = tex_text.splitlines()
    for automaton in model.automata:
        section = _find_section_for_automaton(sections, automaton.name)
        if section is None:
            continue
        section_lines = lines[section.start_line - 1 : section.end_line]
        section_text = "\n".join(section_lines)
        location_lines: dict[str, list[int]] = {}
        for location in automaton.locations:
            if location.name.startswith("ContractViolation"):
                continue
            matches = _find_name_lines(section_lines, location.name, base_line=section.start_line)
            if matches:
                location_lines[location.name] = matches
        transition_blocks = [
            block
            for block in blocks
            if section.start_line <= block.start_line <= section.end_line and "--" in block.text
        ]
        transitions: list[dict] = []
        for block in transition_blocks:
            transitions.extend(_extract_transition_statements(block))
        sketches[automaton.name] = {
            "section_title": section.title,
            "start_line": section.start_line,
            "end_line": section.end_line,
            "locations": list(location_lines),
            "location_lines": location_lines,
            "transition_count": len(transitions),
            "transitions": transitions,
            "has_priority_text": "prio" in section_text or r"\prio" in section_text,
        }
    return sketches


def extract_environment_sketches(blocks: list[VerbatimBlock]) -> dict[str, dict]:
    sketches: dict[str, dict] = {}
    for block in blocks:
        if "ENV_CH:" not in block.text:
            continue
        current: str | None = None
        for offset, line in enumerate(block.text.splitlines()):
            stripped = line.strip()
            heading = re.match(r"(?P<name>ENV_[A-Z]+):$", stripped)
            if heading:
                current = heading.group("name")
                sketches[current] = {
                    "line": block.start_line + offset,
                    "statements": [],
                }
                continue
            if current and stripped:
                sketches[current]["statements"].append(_normalize_latex_text(stripped))
    return sketches


def extract_assume_guarantee(tex_text: str, blocks: list[VerbatimBlock]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    row_re = re.compile(
        r"\\\(\\A\{(?P<name>[A-Z]+)\}\\\)\s*&\s*(?P<assumption>.*?)\s*&\s*(?P<guarantee>.*?)\\\\"
    )
    for line_no, line in enumerate(tex_text.splitlines(), start=1):
        match = row_re.search(line)
        if not match:
            continue
        name = f"A_{match.group('name')}"
        result[name] = {
            "line": line_no,
            "assumption": _normalize_latex_text(match.group("assumption")),
            "guarantee": _normalize_latex_text(match.group("guarantee")),
        }
    predicate_to_automaton = {
        "ch": "A_CH",
        "sig": "A_SIG",
        "bm": "A_BM",
        "sq": "A_SQ",
        "ph": "A_PH",
    }
    for block in blocks:
        if "bool ass_ch()" not in block.text:
            continue
        for offset, line in enumerate(block.text.splitlines()):
            stripped = line.strip()
            predicate = re.match(r"bool\s+(?P<kind>ass|gar)_(?P<suffix>[a-z]+)\(\)\s*=\s*(?P<body>.*);", stripped)
            if predicate:
                automaton = predicate_to_automaton.get(predicate.group("suffix"))
                if automaton:
                    entry = result.setdefault(automaton, {})
                    key = "assumption_predicate" if predicate.group("kind") == "ass" else "guarantee_predicate"
                    entry[key] = _normalize_latex_text(predicate.group("body"))
                    entry.setdefault("predicate_lines", []).append(block.start_line + offset)
                continue
            query = re.match(r"A\[\]\s+\((ass_(?P<suffix>[a-z]+)\(\).*?)\)", stripped)
            if query:
                automaton = predicate_to_automaton.get(query.group("suffix"))
                if automaton:
                    entry = result.setdefault(automaton, {})
                    entry.setdefault("queries", []).append(_normalize_query(stripped))
    return result


def extract_class_sets(tex_text: str, contract: PhyContractModel | None = None) -> dict[str, list[str]]:
    model = contract or build_default_contract()
    classes: dict[str, list[str]] = {}
    for item in model.classes:
        values = _extract_one_class_set(tex_text, item.name)
        if values:
            classes[item.name] = values
    return classes


def find_marker_lines(tex_text: str) -> dict[str, list[int]]:
    lines = tex_text.splitlines()
    found: dict[str, list[int]] = {}
    for marker, (_, patterns) in REQUIRED_MARKERS.items():
        marker_lines: list[int] = []
        compiled = [re.compile(pattern, flags=re.IGNORECASE) for pattern in patterns]
        for line_no, line in enumerate(lines, start=1):
            if any(pattern.search(line) for pattern in compiled):
                marker_lines.append(line_no)
        found[marker] = marker_lines
    return found


def _extract_one_class_set(tex_text: str, class_name: str) -> list[str]:
    if class_name == "SINRClass":
        match = re.search(
            r"SINRClass\s*=\s*\\begin\{cases\}(?P<body>.*?)\\end\{cases\}",
            tex_text,
            flags=re.DOTALL,
        )
    else:
        match = re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(class_name)}\s*&\s*\\in\s*\\\{{(?P<body>.*?)\\\}}",
            tex_text,
            flags=re.DOTALL,
        )
    if not match:
        return []
    return [_normalize_identifier(item) for item in re.findall(r"\\code\{([^}]*)\}", match.group("body"))]


def _collect_latex_block(lines: list[str], start_index: int) -> list[str]:
    block: list[str] = []
    for line in lines[start_index:]:
        block.append(line)
        if r"\end{equation}" in line or r"\end{align}" in line or r"\end{aligned}" in line:
            break
    return block


def _composition_components(target: str, expression: str) -> list[str]:
    components: list[str] = []
    for item in re.findall(r"\b(?:A|ENV)_[A-Za-z0-9_]+", expression):
        if item == target or item in components:
            continue
        components.append(item)
    return components


def _find_section_for_automaton(sections: list[LatexSection], automaton_name: str) -> LatexSection | None:
    for section in sections:
        title = _normalize_latex_text(section.title)
        if automaton_name in title:
            return section
    return None


def _find_name_lines(lines: list[str], name: str, *, base_line: int) -> list[int]:
    pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])")
    found: list[int] = []
    for offset, line in enumerate(lines):
        normalized = _normalize_latex_text(line)
        if pattern.search(normalized):
            found.append(base_line + offset)
    return found


def _extract_transition_statements(block: VerbatimBlock) -> list[dict]:
    transitions: list[dict] = []
    pending: list[str] = []
    start_line: int | None = None
    raw_lines = block.text.splitlines()
    for offset, raw_line in enumerate(raw_lines):
        stripped = raw_line.strip()
        if not stripped:
            continue
        starts_transition = " -- " in stripped and not pending
        if starts_transition:
            pending = [stripped]
            start_line = block.start_line + offset
            if "-->" in stripped:
                transitions.append(_transition_statement_to_dict(pending, start_line, block.start_line + offset))
                pending = []
                start_line = None
            continue
        if pending:
            pending.append(stripped)
            if "-->" in stripped:
                transitions.append(_transition_statement_to_dict(pending, start_line or block.start_line, block.start_line + offset))
                pending = []
                start_line = None
    return transitions


def _transition_statement_to_dict(lines: list[str], start_line: int, end_line: int) -> dict:
    statement = _compact_spaces(" ".join(lines))
    first = lines[0]
    source = _compact_spaces(first.split("--", 1)[0])
    target = ""
    for line in reversed(lines):
        if "-->" in line:
            target = _compact_spaces(line.split("-->", 1)[1])
            break
    sync = None
    sync_match = re.search(r"sync:\s*([A-Za-z0-9_]+[!?])", statement)
    if sync_match:
        sync = sync_match.group(1)
    else:
        inline_sync = re.search(r"--\s*([A-Za-z0-9_]+[!?])(?:\s*/|\s*-->)", statement)
        if inline_sync:
            sync = inline_sync.group(1)
    guard = None
    guard_match = re.search(r"guard:\s*(.*?)(?:\s+sync:|\s+update:|-->|$)", statement)
    if guard_match:
        guard = _compact_spaces(guard_match.group(1))
    else:
        between = statement.split("--", 1)[1].split("-->", 1)[0] if "--" in statement else ""
        between = between.split("sync:", 1)[0].split("update:", 1)[0].split("/", 1)[0]
        candidate = _compact_spaces(between)
        if candidate and not re.fullmatch(r"[A-Za-z0-9_]+[!?]", candidate):
            guard = candidate
    assignment = None
    update_match = re.search(r"update:\s*(.*?)(?:-->|$)", statement)
    if update_match:
        assignment = _compact_spaces(update_match.group(1).rstrip(","))
    elif "/" in statement:
        assignment = _compact_spaces(statement.split("/", 1)[1].split("-->", 1)[0])
    return {
        "start_line": start_line,
        "end_line": end_line,
        "source": _normalize_latex_text(source),
        "target": _normalize_latex_text(target),
        "guard": _normalize_latex_text(guard) if guard else None,
        "sync": _normalize_latex_text(sync) if sync else None,
        "assignment": _normalize_latex_text(assignment) if assignment else None,
        "statement": _normalize_latex_text(statement),
    }


def _diagnostics(
    *,
    tex_text: str,
    sections: list[LatexSection],
    compositions: dict[str, dict],
    x_disc: dict[str, object],
    clock_resets: dict[str, dict],
    invariants: dict[str, dict],
    automata_sketches: dict[str, dict],
    env_sketches: dict[str, dict],
    assume_guarantee: dict[str, dict],
    channels: dict[str, str],
    class_sets: dict[str, list[str]],
    queries: list[str],
    marker_lines: dict[str, list[int]],
    contract: PhyContractModel,
) -> list[str]:
    diagnostics: list[str] = []
    section_titles = " ".join(item.title for item in sections)
    for name, patterns in REQUIRED_SECTION_PATTERNS.items():
        if not any(re.search(pattern, section_titles, flags=re.IGNORECASE) for pattern in patterns):
            diagnostics.append(f"Missing expected article section: {name}.")
    for marker, lines in marker_lines.items():
        if not lines:
            category = REQUIRED_MARKERS[marker][0]
            diagnostics.append(f"Missing required {category} marker: {marker}.")
    expected_compositions = {
        "A_PHY": contract.phy_components,
        "A_SYS": ["A_PHY", "A_ENV"],
        "A_ENV": contract.env_components,
    }
    for name, expected_components in expected_compositions.items():
        found = compositions.get(name)
        if not found:
            diagnostics.append(f"Composition formula not extracted: {name}.")
            continue
        if found.get("components") != expected_components:
            diagnostics.append(
                f"Composition mismatch for {name}: expected {expected_components}, found {found.get('components')}."
            )
    expected_x_disc = [item.name for item in contract.classes]
    if x_disc.get("variables") != expected_x_disc:
        diagnostics.append(
            f"X_disc mismatch: expected {expected_x_disc}, found {x_disc.get('variables', [])}."
        )
    for item in contract.clocks:
        if item.name not in clock_resets:
            diagnostics.append(f"Clock reset row not extracted: {item.name}.")
            continue
        if not clock_resets[item.name].get("reset"):
            diagnostics.append(f"Clock reset row has empty reset semantics: {item.name}.")
    for location, expected_formula in REQUIRED_INVARIANTS.items():
        found = invariants.get(location)
        if not found:
            diagnostics.append(f"Invariant not extracted: {location}.")
            continue
        if found.get("formula") != expected_formula:
            diagnostics.append(
                f"Invariant mismatch for {location}: expected {expected_formula}, found {found.get('formula')}."
            )
    for automaton in contract.automata:
        sketch = automata_sketches.get(automaton.name)
        if not sketch:
            diagnostics.append(f"Automaton sketch not extracted: {automaton.name}.")
            continue
        expected_locations = [loc.name for loc in automaton.locations if not loc.name.startswith("ContractViolation")]
        missing_locations = [name for name in expected_locations if name not in sketch.get("locations", [])]
        if missing_locations:
            diagnostics.append(f"Automaton {automaton.name} missing locations in article sketch: {missing_locations}.")
        if int(sketch.get("transition_count", 0)) <= 0:
            diagnostics.append(f"Automaton {automaton.name} has no extracted transition sketch.")
    for name in contract.env_components:
        sketch = env_sketches.get(name)
        if not sketch or not sketch.get("statements"):
            diagnostics.append(f"Environment sketch not extracted: {name}.")
    for automaton in contract.phy_components:
        entry = assume_guarantee.get(automaton)
        if not entry or not entry.get("assumption") or not entry.get("guarantee"):
            diagnostics.append(f"Assume/guarantee row not extracted: {automaton}.")
    expected_channels = {item.name: item.kind for item in contract.channels}
    for name, kind in expected_channels.items():
        if channels.get(name) != kind:
            diagnostics.append(f"Channel {name} expected as {kind}, found {channels.get(name) or 'missing'}.")
    for item in contract.classes:
        values = class_sets.get(item.name)
        if not values:
            diagnostics.append(f"Class set not extracted: {item.name}.")
            continue
        if values != item.values:
            diagnostics.append(f"Class set mismatch for {item.name}: expected {item.values}, found {values}.")
    query_set = set(queries)
    for item in contract.properties:
        if item.query not in query_set:
            diagnostics.append(f"Property query not extracted from LaTeX: {item.name}.")
    if r"\begin{verbatim}" in tex_text and not channels:
        diagnostics.append("Verbatim blocks exist, but no channel declarations were extracted.")
    return diagnostics


def _normalize_identifier(value: str) -> str:
    normalized = value.replace(r"\_", "_")
    normalized = re.sub(r"([A-Za-z])_\{([^}]+)\}", r"\1_\2", normalized)
    return normalized.replace("\\", "").replace("{", "").replace("}", "").strip()


def _normalize_latex_text(value: str | None) -> str:
    if value is None:
        return ""
    normalized = value
    normalized = re.sub(r"\\A\{([^}]*)\}", lambda m: f"A_{m.group(1)}", normalized)
    normalized = re.sub(
        r"\\mathcal\{A\}_\{\\text\{([^}]*)\}\}",
        lambda m: _normalize_identifier(m.group(1)),
        normalized,
    )
    normalized = re.sub(r"\\code\{([^}]*)\}", lambda m: _normalize_identifier(m.group(1)), normalized)
    normalized = re.sub(r"\\text\{([^}]*)\}", lambda m: _normalize_identifier(m.group(1)), normalized)
    replacements = {
        r"\parallel": "||",
        r"\le": "<=",
        r"\ge": ">=",
        r"\ne": "!=",
        r"\neq": "!=",
        r"\wedge": "&&",
        r"\vee": "||",
        r"\neg": "!",
        r"\in": "in",
        r"\notin": "not in",
        r"\tau": "tau",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    normalized = normalized.replace(r"\_", "_")
    normalized = re.sub(r"([A-Za-z])_\{([^}]+)\}", r"\1_\2", normalized)
    normalized = re.sub(r"\\(?:begin|end)\{[^}]+\}", " ", normalized)
    normalized = normalized.replace(r"\(", " ").replace(r"\)", " ")
    normalized = normalized.replace("\\\\", " ")
    normalized = normalized.replace("&", " ")
    normalized = normalized.replace("{", "").replace("}", "")
    normalized = re.sub(r"\\[A-Za-z]+", " ", normalized)
    normalized = re.sub(r"\s*(<=|>=|==|!=)\s*", r" \1 ", normalized)
    normalized = re.sub(r"\s*\+\s*", " + ", normalized)
    return _compact_spaces(normalized)


def _normalize_query(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _compact_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _expected_counts() -> dict[str, int]:
    model = build_default_contract()
    return {
        "classes": len(model.classes),
        "clocks": len(model.clocks),
        "channels": len(model.channels),
        "queries": len(model.properties),
        "compositions": len(COMPOSITION_NAMES),
        "invariants": len(REQUIRED_INVARIANTS),
        "automata": len(model.phy_components),
        "environment": len(model.env_components),
        "markers": len(REQUIRED_MARKERS),
    }


def _ratio(found: int, expected: int) -> float:
    if expected <= 0:
        return 1.0
    return round(found / expected, 4)
