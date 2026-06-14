"""Object-based erasing with partial stroke support."""

from __future__ import annotations

import math

from src.drawing_objects.arrow import Arrow
from src.drawing_objects.base import DrawableObject
from src.drawing_objects.circle import Circle
from src.drawing_objects.line import Line
from src.drawing_objects.rectangle import Rectangle
from src.drawing_objects.stroke import Stroke
from src.drawing_objects.text import Text


def _point_in_circle(px: int, py: int, cx: int, cy: int, radius: int) -> bool:
    return (px - cx) ** 2 + (py - cy) ** 2 <= radius * radius


def _segment_intersects_circle(
    p1: tuple[int, int],
    p2: tuple[int, int],
    cx: int,
    cy: int,
    radius: int,
) -> bool:
    if _point_in_circle(p1[0], p1[1], cx, cy, radius):
        return True
    if _point_in_circle(p2[0], p2[1], cx, cy, radius):
        return True
    steps = max(4, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) // 4))
    for i in range(steps + 1):
        t = i / steps
        x = int(p1[0] + t * (p2[0] - p1[0]))
        y = int(p1[1] + t * (p2[1] - p1[1]))
        if _point_in_circle(x, y, cx, cy, radius):
            return True
    return False


def split_stroke_by_eraser(stroke: Stroke, cx: int, cy: int, radius: int) -> list[Stroke]:
    """Split a stroke into fragments, removing portions inside the eraser circle."""
    points = stroke.points
    if not points:
        return []

    effective_r = radius + stroke.thickness // 2
    fragments: list[list[tuple[int, int]]] = []
    current: list[tuple[int, int]] = []

    for i, p in enumerate(points):
        inside = _point_in_circle(p[0], p[1], cx, cy, effective_r)
        if i > 0:
            prev = points[i - 1]
            if _segment_intersects_circle(prev, p, cx, cy, effective_r):
                inside = True

        if inside:
            if len(current) >= 2:
                fragments.append(current)
            elif len(current) == 1:
                if not _point_in_circle(current[0][0], current[0][1], cx, cy, effective_r):
                    fragments.append(current)
            current = []
        else:
            current.append(p)

    if len(current) >= 2:
        fragments.append(current)
    elif len(current) == 1 and not _point_in_circle(
        current[0][0], current[0][1], cx, cy, effective_r
    ):
        fragments.append(current)

    if len(fragments) == 1 and fragments[0] == points:
        return [stroke]

    return [
        Stroke(points=seg, color=stroke.color, thickness=stroke.thickness)
        for seg in fragments
    ]


def apply_eraser_to_objects(
    objects: list[DrawableObject],
    cx: int,
    cy: int,
    radius: int,
) -> tuple[list[DrawableObject], bool]:
    """Return new object list after erasing at (cx, cy). True if anything changed."""
    result: list[DrawableObject] = []
    changed = False

    for obj in objects:
        if isinstance(obj, Stroke):
            fragments = split_stroke_by_eraser(obj, cx, cy, radius)
            if len(fragments) == 1 and fragments[0].points == obj.points:
                result.append(obj)
            else:
                changed = True
                result.extend(fragments)
        elif obj.hit_test(cx, cy, radius):
            changed = True
        else:
            result.append(obj)

    return result, changed
