from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class TransitionGeometry:
    labels: dict[str, Point]
    nails: list[Point] = field(default_factory=list)
