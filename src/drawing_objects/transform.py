"""2D transform math for canvas objects."""

from __future__ import annotations

import math


def transform_point(
    x: float,
    y: float,
    pivot_x: float,
    pivot_y: float,
    scale_x: float,
    scale_y: float,
    rotation_deg: float,
    offset_x: float,
    offset_y: float,
) -> tuple[int, int]:
    """Scale and rotate around pivot, then translate."""
    dx = x - pivot_x
    dy = y - pivot_y
    sx = dx * scale_x
    sy = dy * scale_y
    rad = math.radians(rotation_deg)
    cos_r = math.cos(rad)
    sin_r = math.sin(rad)
    rx = sx * cos_r - sy * sin_r
    ry = sx * sin_r + sy * cos_r
    return int(rx + pivot_x + offset_x), int(ry + pivot_y + offset_y)


def bbox_from_points(points: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    if not points:
        return (0, 0, 0, 0)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def angle_deg(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.degrees(math.atan2(y2 - y1, x2 - x1))
