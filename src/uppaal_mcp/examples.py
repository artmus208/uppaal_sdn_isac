from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib import resources


@dataclass(frozen=True)
class BuiltinExample:
    name: str
    description: str
    category: str
    model_xml: str
    queries: str

    def to_dict(self) -> dict:
        return asdict(self)


EXAMPLE_METADATA = {
    "deadlock_free": {
        "category": "generic",
        "description": "Tiny model where time can always pass; A[] not deadlock should be satisfied.",
    },
    "deadlock": {
        "category": "generic",
        "description": "Urgent stuck location; A[] not deadlock should be violated.",
    },
    "queue_overflow": {
        "category": "generic",
        "description": "Small bounded queue model with an reachable Overflow location.",
    },
    "bounded_response": {
        "category": "generic",
        "description": "Controller skeleton with a deadline invariant and Done reachability.",
    },
    "phy_contract_skeleton": {
        "category": "phy",
        "description": "Minimal PHY-contract shape: A_CH/A_SIG/A_BM/A_SQ/A_PH plus ENV.",
    },
}

EXAMPLE_DESCRIPTIONS = {
    name: metadata["description"]
    for name, metadata in EXAMPLE_METADATA.items()
}


def list_builtin_examples() -> list[dict]:
    return [
        {
            "name": name,
            "category": EXAMPLE_METADATA[name]["category"],
            "description": EXAMPLE_METADATA[name]["description"],
            "is_phy": EXAMPLE_METADATA[name]["category"] == "phy",
        }
        for name in sorted(EXAMPLE_METADATA)
    ]


def get_builtin_example(name: str) -> BuiltinExample:
    if name not in EXAMPLE_METADATA:
        known = ", ".join(sorted(EXAMPLE_METADATA))
        raise KeyError(f"Unknown example {name!r}. Known examples: {known}.")
    base = resources.files("uppaal_mcp").joinpath("builtin_examples", name)
    model_xml = base.joinpath("model.xml").read_text(encoding="utf-8")
    queries = base.joinpath("queries.q").read_text(encoding="utf-8")
    return BuiltinExample(
        name=name,
        description=EXAMPLE_METADATA[name]["description"],
        category=EXAMPLE_METADATA[name]["category"],
        model_xml=model_xml,
        queries=queries,
    )
