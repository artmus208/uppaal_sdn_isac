from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

from .paths import local_path


@dataclass
class ValidationReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    templates: list[str] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def load_text(
    *,
    text: str | None = None,
    path: str | Path | None = None,
    label: str,
) -> tuple[str | None, str | None]:
    if text is not None and path is not None:
        raise ValueError(f"Pass either {label}_text or {label}_path, not both.")
    if text is not None:
        return text, None
    if path is not None:
        resolved = local_path(path)
        return resolved.read_text(encoding="utf-8"), str(resolved)
    return None, None


def validate_model_text(model_xml: str, queries_text: str | None = None) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []
    templates: list[str] = []
    queries: list[str] = []

    try:
        root = ET.fromstring(model_xml)
    except ET.ParseError as exc:
        return ValidationReport(ok=False, errors=[f"XML parse error: {exc}"])

    if root.tag != "nta":
        errors.append("Root element must be <nta>.")

    locations_by_id: set[str] = set()
    for template in root.findall("template"):
        name = _element_text(template.find("name")) or "<unnamed>"
        templates.append(name)
        template_locations = {
            location.attrib.get("id")
            for location in template.findall("location")
            if location.attrib.get("id")
        }
        locations_by_id.update(template_locations)
        if not template_locations:
            errors.append(f"Template {name} has no locations.")
        init = template.find("init")
        if init is None:
            errors.append(f"Template {name} has no initial location.")
        elif init.attrib.get("ref") not in template_locations:
            errors.append(f"Template {name} initial location points to an unknown id.")

        for transition in template.findall("transition"):
            source = transition.find("source")
            target = transition.find("target")
            if source is None or source.attrib.get("ref") not in template_locations:
                errors.append(f"Template {name} has transition with unknown source.")
            if target is None or target.attrib.get("ref") not in template_locations:
                errors.append(f"Template {name} has transition with unknown target.")
            sync_labels = [
                label
                for label in transition.findall("label")
                if label.attrib.get("kind") == "synchronisation"
            ]
            if len(sync_labels) > 1:
                warnings.append(
                    f"Template {name} has a transition with more than one synchronisation label."
                )

    if not templates:
        errors.append("Model has no templates.")

    system = root.find("system")
    if system is None or not _element_text(system):
        errors.append("Model has no <system> declaration.")

    embedded_queries = extract_queries_from_model_xml(model_xml)
    queries = parse_queries_text(queries_text) if queries_text is not None else embedded_queries
    if not queries:
        warnings.append("No queries were found.")

    _warn_about_query_locations(queries, locations_by_id, warnings)
    return ValidationReport(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        templates=templates,
        queries=queries,
    )


def parse_queries_text(queries_text: str) -> list[str]:
    formulas: list[str] = []
    in_block_comment = False
    for raw_line in queries_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("/*"):
            in_block_comment = True
        if in_block_comment:
            if "*/" in line:
                in_block_comment = False
            continue
        if line.startswith("//"):
            continue
        formulas.append(line)
    return formulas


def extract_queries_from_model_xml(model_xml: str) -> list[str]:
    try:
        root = ET.fromstring(model_xml)
    except ET.ParseError:
        return []
    formulas = []
    for formula in root.findall("./queries/query/formula"):
        text = _element_text(formula)
        if text:
            formulas.append(text)
    return formulas


def query_text_from_model_or_query(model_xml: str, queries_text: str | None) -> str:
    if queries_text is not None and queries_text.strip():
        return queries_text
    formulas = extract_queries_from_model_xml(model_xml)
    return "\n".join(formulas) + ("\n" if formulas else "")


def _element_text(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def _warn_about_query_locations(
    queries: Iterable[str],
    location_ids: set[str],
    warnings: list[str],
) -> None:
    if not location_ids:
        return
    for query in queries:
        for ref in re.findall(r"\b[A-Za-z_]\w*\.([A-Za-z_]\w*)\b", query):
            # UPPAAL queries use instance.location names; the XML id is not always the label.
            # This warning is deliberately conservative until a real symbol table is added.
            if ref.startswith("id") and ref not in location_ids:
                warnings.append(f"Query may reference an unknown location id: {ref}.")
