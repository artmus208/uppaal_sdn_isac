from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable


@dataclass(frozen=True)
class LayerAdapter:
    layer_id: str
    source_name: str
    extract_contract: Callable
    validate_contract: Callable
    generate_model: Callable
    generate_property_pack: Callable
    validate_model: Callable
    generate_report: Callable
    list_scenarios: Callable | None = None
    list_benchmarks: Callable | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        for key in ("extract_contract", "validate_contract", "generate_model", "generate_property_pack", "validate_model", "generate_report", "list_scenarios", "list_benchmarks"):
            data[key] = getattr(self, key) is not None
        return data

