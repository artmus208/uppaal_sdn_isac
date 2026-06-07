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
class EnvSpec:
    name: str
    initial: str
    locations: list[LocationSpec]
    transitions: list[TransitionSpec] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
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
class ObserverSpec:
    name: str
    trigger: str
    responses: list[str]
    deadline: str
    violation_query: str
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
    automaton: str
    assumptions: list[str]
    guarantees: list[str]
    violation_location: str
    violation_channel: str
    provenance: Provenance | None = None


@dataclass(frozen=True)
class PhyContractModel:
    source_name: str
    phy_components: list[str]
    env_components: list[str]
    classes: list[ClassSpec]
    clocks: list[ClockSpec]
    channels: list[ChannelSpec]
    automata: list[AutomatonSpec]
    observers: list[ObserverSpec]
    properties: list[PropertySpec]
    contracts: list[ContractSpec]
    variables: list[VariableSpec] = field(default_factory=list)
    env: list[EnvSpec] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PhyContractModel":
        def prov(value: dict[str, Any] | None) -> Provenance | None:
            return Provenance(**value) if value else None

        classes = [
            ClassSpec(name=item["name"], values=list(item["values"]), provenance=prov(item.get("provenance")))
            for item in data["classes"]
        ]
        clocks = [
            ClockSpec(
                name=item["name"],
                meaning=item["meaning"],
                reset=item["reset"],
                provenance=prov(item.get("provenance")),
            )
            for item in data["clocks"]
        ]
        variables = [
            VariableSpec(
                name=item["name"],
                type_name=item["type_name"],
                initial=item.get("initial"),
                role=item.get("role", ""),
                provenance=prov(item.get("provenance")),
            )
            for item in data.get("variables", [])
        ]
        channels = [
            ChannelSpec(
                name=item["name"],
                kind=item["kind"],
                role=item["role"],
                provenance=prov(item.get("provenance")),
            )
            for item in data["channels"]
        ]
        automata = []
        for item in data["automata"]:
            locations = [
                LocationSpec(
                    name=loc["name"],
                    invariant=loc.get("invariant"),
                    provenance=prov(loc.get("provenance")),
                )
                for loc in item["locations"]
            ]
            transitions = [
                TransitionSpec(
                    source=tr["source"],
                    target=tr["target"],
                    guard=tr.get("guard"),
                    sync=tr.get("sync"),
                    assignment=tr.get("assignment"),
                    provenance=prov(tr.get("provenance")),
                )
                for tr in item.get("transitions", [])
            ]
            automata.append(
                AutomatonSpec(
                    name=item["name"],
                    initial=item["initial"],
                    locations=locations,
                    transitions=transitions,
                    assumptions=list(item.get("assumptions", [])),
                    guarantees=list(item.get("guarantees", [])),
                    provenance=prov(item.get("provenance")),
                )
            )
        observers = [
            ObserverSpec(
                name=item["name"],
                trigger=item["trigger"],
                responses=list(item["responses"]),
                deadline=item["deadline"],
                violation_query=item["violation_query"],
                provenance=prov(item.get("provenance")),
            )
            for item in data["observers"]
        ]
        properties = [
            PropertySpec(
                name=item["name"],
                query=item["query"],
                category=item["category"],
                interpretation=item["interpretation"],
                provenance=prov(item.get("provenance")),
            )
            for item in data["properties"]
        ]
        contracts = [
            ContractSpec(
                automaton=item["automaton"],
                assumptions=list(item["assumptions"]),
                guarantees=list(item["guarantees"]),
                violation_location=item["violation_location"],
                violation_channel=item["violation_channel"],
                provenance=prov(item.get("provenance")),
            )
            for item in data["contracts"]
        ]
        env = []
        for item in data.get("env", []):
            locations = [
                LocationSpec(
                    name=loc["name"],
                    invariant=loc.get("invariant"),
                    provenance=prov(loc.get("provenance")),
                )
                for loc in item["locations"]
            ]
            transitions = [
                TransitionSpec(
                    source=tr["source"],
                    target=tr["target"],
                    guard=tr.get("guard"),
                    sync=tr.get("sync"),
                    assignment=tr.get("assignment"),
                    provenance=prov(tr.get("provenance")),
                )
                for tr in item.get("transitions", [])
            ]
            env.append(
                EnvSpec(
                    name=item["name"],
                    initial=item["initial"],
                    locations=locations,
                    transitions=transitions,
                    assumptions=list(item.get("assumptions", [])),
                    provenance=prov(item.get("provenance")),
                )
            )
        return cls(
            source_name=data["source_name"],
            phy_components=list(data["phy_components"]),
            env_components=list(data["env_components"]),
            classes=classes,
            clocks=clocks,
            channels=channels,
            automata=automata,
            observers=observers,
            properties=properties,
            contracts=contracts,
            variables=variables,
            env=env,
            invariants=list(data.get("invariants", [])),
            limitations=list(data.get("limitations", [])),
        )
