"""Shared geographic calculations."""
from __future__ import annotations

import math

from common.wire import Position

EARTH_R = 6_371_000.0


def haversine_m(a: Position, b: Position) -> float:
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dphi = math.radians(b.lat - a.lat)
    dlmb = math.radians(b.lon - a.lon)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_R * math.asin(min(1.0, math.sqrt(h)))


def offset_m(pos: Position, north_m: float, east_m: float) -> Position:
    dlat = north_m / EARTH_R
    dlon = east_m / (EARTH_R * math.cos(math.radians(pos.lat)))
    return Position(
        lat=pos.lat + math.degrees(dlat),
        lon=pos.lon + math.degrees(dlon),
        alt_m=pos.alt_m,
    )
