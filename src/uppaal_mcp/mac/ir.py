from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Provenance:
    source: str
    section: str
    line: int | None = None


@dataclass(frozen=True)
class ClassSpec:
    name: str
    values: list[str]
    provenance: Provenance | None = None


@dataclass(frozen=True)
class ClockSpec:
    name: str
    meaning: str
    reset: str
    provenance: Provenance | None = None


@dataclass(frozen=True)
class VariableSpec:
    name: str
    type_name: str
    initial: str | None = None
    role: str = ""
    provenance: Provenance | None = None


@dataclass(frozen=True)
class ChannelSpec:
    name: str
    kind: str
    role: str
    provenance: Provenance | None = None


@dataclass(frozen=True)
class LocationSpec:
    name: str
    invariant: str | None = None
    provenance: Provenance | None = None


@dataclass(frozen=True)
class TransitionSpec:
    source: str
    target: str
    guard: str | None = None
    sync: str | None = None
    assignment: str | None = None
    provenance: Provenance | None = None


@dataclass(frozen=True)
class AutomatonSpec:
    name: str
    initial: str
    locations: list[LocationSpec]
    transitions: list[TransitionSpec] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    guarantees: list[str] = field(default_factory=list)
    provenance: Provenance | None = None


@dataclass(frozen=True)
class EnvSpec:
    name: str
    initial: str
    locations: list[LocationSpec]
    transitions: list[TransitionSpec] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    provenance: Provenance | None = None


@dataclass(frozen=True)
class ObserverSpec:
    name: str
    trigger: str
    responses: list[str]
    deadline: str
    violation_query: str
    provenance: Provenance | None = None


@dataclass(frozen=True)
class PolicySpec:
    name: str
    guard: str
    mode: str
    outcome: str
    provenance: Provenance | None = None


@dataclass(frozen=True)
class PropertySpec:
    name: str
    query: str
    category: str
    interpretation: str
    provenance: Provenance | None = None


@dataclass(frozen=True)
class ContractSpec:
    name: str
    assumptions: list[str]
    guarantees: list[str]
    provenance: Provenance | None = None


@dataclass(frozen=True)
class MacContractModel:
    source_name: str
    layer_id: str
    mac_components: list[str]
    env_components: list[str]
    classes: list[ClassSpec]
    clocks: list[ClockSpec]
    variables: list[VariableSpec]
    channels: list[ChannelSpec]
    automata: list[AutomatonSpec]
    env: list[EnvSpec]
    observers: list[ObserverSpec]
    policies: list[PolicySpec]
    properties: list[PropertySpec]
    contracts: list[ContractSpec]
    mappings: dict[str, Any] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MacContractModel":
        def prov(value: dict[str, Any] | None) -> Provenance | None:
            return Provenance(**value) if value else None

        def locs(items: list[dict[str, Any]]) -> list[LocationSpec]:
            return [
                LocationSpec(name=item["name"], invariant=item.get("invariant"), provenance=prov(item.get("provenance")))
                for item in items
            ]

        def transitions(items: list[dict[str, Any]]) -> list[TransitionSpec]:
            return [
                TransitionSpec(
                    source=item["source"],
                    target=item["target"],
                    guard=item.get("guard"),
                    sync=item.get("sync"),
                    assignment=item.get("assignment"),
                    provenance=prov(item.get("provenance")),
                )
                for item in items
            ]

        return cls(
            source_name=data["source_name"],
            layer_id=data.get("layer_id", "mac"),
            mac_components=list(data["mac_components"]),
            env_components=list(data["env_components"]),
            classes=[ClassSpec(item["name"], list(item["values"]), prov(item.get("provenance"))) for item in data["classes"]],
            clocks=[ClockSpec(item["name"], item["meaning"], item["reset"], prov(item.get("provenance"))) for item in data["clocks"]],
            variables=[
                VariableSpec(item["name"], item["type_name"], item.get("initial"), item.get("role", ""), prov(item.get("provenance")))
                for item in data["variables"]
            ],
            channels=[
                ChannelSpec(item["name"], item["kind"], item["role"], prov(item.get("provenance")))
                for item in data["channels"]
            ],
            automata=[
                AutomatonSpec(
                    item["name"],
                    item["initial"],
                    locs(item["locations"]),
                    transitions(item.get("transitions", [])),
                    list(item.get("assumptions", [])),
                    list(item.get("guarantees", [])),
                    prov(item.get("provenance")),
                )
                for item in data["automata"]
            ],
            env=[
                EnvSpec(
                    item["name"],
                    item["initial"],
                    locs(item["locations"]),
                    transitions(item.get("transitions", [])),
                    list(item.get("assumptions", [])),
                    prov(item.get("provenance")),
                )
                for item in data.get("env", [])
            ],
            observers=[
                ObserverSpec(item["name"], item["trigger"], list(item["responses"]), item["deadline"], item["violation_query"], prov(item.get("provenance")))
                for item in data["observers"]
            ],
            policies=[
                PolicySpec(item["name"], item["guard"], item["mode"], item["outcome"], prov(item.get("provenance")))
                for item in data["policies"]
            ],
            properties=[
                PropertySpec(item["name"], item["query"], item["category"], item["interpretation"], prov(item.get("provenance")))
                for item in data["properties"]
            ],
            contracts=[
                ContractSpec(item["name"], list(item["assumptions"]), list(item["guarantees"]), prov(item.get("provenance")))
                for item in data["contracts"]
            ],
            mappings=dict(data.get("mappings", {})),
            limitations=list(data.get("limitations", [])),
        )

