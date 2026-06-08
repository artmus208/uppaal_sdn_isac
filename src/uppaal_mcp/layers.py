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


def available_layer_adapters() -> dict[str, LayerAdapter]:
    from .mac import tools as mac_tools
    from .phy import tools as phy_tools
    from .sdn import tools as sdn_tools

    return {
        "phy": LayerAdapter(
            layer_id="phy",
            source_name="PHY_level_formalization_reviewed-2026-06-06-143000.tex",
            extract_contract=phy_tools.extract_contract,
            validate_contract=phy_tools.validate_contract,
            generate_model=phy_tools.generate_uppaal_from_contract,
            generate_property_pack=phy_tools.generate_property_pack,
            validate_model=phy_tools.validate_contract,
            generate_report=phy_tools.generate_report,
            list_scenarios=phy_tools.phy_list_scenarios,
            list_benchmarks=phy_tools.phy_list_benchmarks,
        ),
        "mac": LayerAdapter(
            layer_id="mac",
            source_name="MAC_resource_scheduling_formalization.tex",
            extract_contract=mac_tools.extract_contract,
            validate_contract=mac_tools.validate_contract,
            generate_model=mac_tools.generate_uppaal_from_contract,
            generate_property_pack=mac_tools.generate_property_pack,
            validate_model=mac_tools.validate_contract,
            generate_report=mac_tools.generate_report,
            list_scenarios=mac_tools.mac_list_scenarios,
            list_benchmarks=mac_tools.mac_list_benchmarks,
        ),
        "sdn": LayerAdapter(
            layer_id="sdn",
            source_name="SDN_RIC_control_plane_formalization.tex",
            extract_contract=sdn_tools.extract_contract,
            validate_contract=sdn_tools.validate_contract,
            generate_model=sdn_tools.generate_uppaal_from_contract,
            generate_property_pack=sdn_tools.generate_property_pack,
            validate_model=sdn_tools.validate_contract,
            generate_report=sdn_tools.generate_report,
            list_scenarios=sdn_tools.sdn_list_scenarios,
            list_benchmarks=sdn_tools.sdn_list_benchmarks,
        ),
    }
