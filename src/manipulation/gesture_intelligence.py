"""Smoothing, thresholds, anchors, handle detection, trash zones."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from src.drawing_objects.transform import angle_deg, distance

SMOOTH_PREV = 0.75
SMOOTH_CUR = 0.25

MIN_MOVEMENT = 6
MOVE_THRESHOLD = 6
SCALE_THRESHOLD = 25
ROTATION_THRESHOLD = 18.0
TWO_HAND_HOLD_SEC = 0.4
SNAP_DISTANCE = 120
SNAP_STRENGTH = 0.25
TRASH_VISUAL_SIZE = 60
TRASH_HIT_SIZE = 180
HANDLE_GRAB_RADIUS = 40
MIN_OBJECT_SCALE = 0.25
MAX_OBJECT_SCALE = 4.0
THROW_SPEED_THRESHOLD = 35.0
THROW_ALIGNMENT_MIN = 0.65


class HandleKind(str, Enum):
    CORNER = "corner"
    EDGE_H = "edge_h"
    EDGE_V = "edge_v"
    ROTATE = "rotate"


class TwoHandLock(str, Enum):
    NONE = "none"
    MOVE = "move"
    SCALE = "scale"
    ROTATE = "rotate"
    STRETCH_W = "stretch_w"
    STRETCH_H = "stretch_h"


@dataclass
class HandleHit:
    kind: HandleKind
    axis: str
    x: int
    y: int


@dataclass
class TwoHandAnchors:
    """Frozen reference values when two-hand control activates."""

    left: tuple[float, float]
    right: tuple[float, float]
    midpoint: tuple[float, float]
    distance: float
    angle: float
    sep_x: float
    sep_y: float
    object_center: tuple[float, float]
    scales: list[tuple[float, float]] = field(default_factory=list)
    rotations: list[float] = field(default_factory=list)
    stretch_w: bool = False
    stretch_h: bool = False


class PointSmoother:
    def __init__(self, prev_weight: float = SMOOTH_PREV, cur_weight: float = SMOOTH_CUR):
        self._prev_w = prev_weight
        self._cur_w = cur_weight
        self._store: dict[str, tuple[float, float]] = {}

    def smooth(self, key: str, x: float, y: float) -> tuple[int, int]:
        if key not in self._store:
            self._store[key] = (x, y)
        else:
            px, py = self._store[key]
            self._store[key] = (
                px * self._prev_w + x * self._cur_w,
                py * self._prev_w + y * self._cur_w,
            )
        sx, sy = self._store[key]
        return int(sx), int(sy)

    def clear(self) -> None:
        self._store.clear()


@dataclass
class TrashZone:
    frame_w: int
    frame_h: int

    @property
    def visual_rect(self) -> tuple[int, int, int, int]:
        size = TRASH_VISUAL_SIZE
        x1, y1 = self.frame_w - 16, self.frame_h - 16
        return x1 - size, y1 - size, x1, y1

    @property
    def hit_rect(self) -> tuple[int, int, int, int]:
        cx, cy = self.center
        half = TRASH_HIT_SIZE // 2
        return int(cx - half), int(cy - half), int(cx + half), int(cy + half)

    @property
    def center(self) -> tuple[float, float]:
        x0, y0, x1, y1 = self.visual_rect
        return (x0 + x1) / 2, (y0 + y1) / 2

    def contains_point(self, x: float, y: float) -> bool:
        x0, y0, x1, y1 = self.hit_rect
        return x0 <= x <= x1 and y0 <= y <= y1

    def contains_center(self, objects: list) -> bool:
        cx, cy = selection_center(objects)
        return self.contains_point(cx, cy)

    def dist_to(self, x: float, y: float) -> float:
        tcx, tcy = self.center
        return distance(x, y, tcx, tcy)

    def should_snap(self, x: float, y: float) -> bool:
        return self.dist_to(x, y) <= SNAP_DISTANCE


def clamp_scale(value: float) -> float:
    return max(MIN_OBJECT_SCALE, min(MAX_OBJECT_SCALE, value))


def normalize_angle_delta(delta: float) -> float:
    while delta > 180:
        delta -= 360
    while delta < -180:
        delta += 360
    return delta


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_point(
    p: tuple[float, float],
    q: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    return lerp(p[0], q[0], t), lerp(p[1], q[1], t)


def apply_magnetic_snap(
    x: float,
    y: float,
    trash: TrashZone,
) -> tuple[float, float, bool]:
    if not trash.should_snap(x, y):
        return x, y, False
    tcx, tcy = trash.center
    nx = lerp(x, tcx, SNAP_STRENGTH)
    ny = lerp(y, tcy, SNAP_STRENGTH)
    return nx, ny, True


def throw_alignment(
    velocity: tuple[float, float],
    from_x: float,
    from_y: float,
    trash: TrashZone,
) -> tuple[float, float]:
    """Return (speed, alignment) for throw-to-trash detection."""
    vx, vy = velocity
    speed = math.hypot(vx, vy)
    if speed < 0.01:
        return 0.0, 0.0
    tcx, tcy = trash.center
    tx, ty = tcx - from_x, tcy - from_y
    t_len = math.hypot(tx, ty)
    if t_len < 0.01:
        return speed, 1.0
    dot = (vx / speed) * (tx / t_len) + (vy / speed) * (ty / t_len)
    return speed, dot


def selection_center(objects: list) -> tuple[float, float]:
    if not objects:
        return 0.0, 0.0
    xs: list[float] = []
    ys: list[float] = []
    for obj in objects:
        x0, y0, x1, y1 = obj.bounding_box()
        xs.extend([x0, x1])
        ys.extend([y0, y1])
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def selection_bounds(objects: list) -> tuple[int, int, int, int]:
    if not objects:
        return 0, 0, 0, 0
    xs: list[int] = []
    ys: list[int] = []
    for obj in objects:
        x0, y0, x1, y1 = obj.bounding_box()
        xs.extend([x0, x1])
        ys.extend([y0, y1])
    return min(xs), min(ys), max(xs), max(ys)


def move_selection_to_center(objects: list, tx: float, ty: float) -> None:
    cx, cy = selection_center(objects)
    dx, dy = tx - cx, ty - cy
    if abs(dx) < MIN_MOVEMENT and abs(dy) < MIN_MOVEMENT:
        return
    for obj in objects:
        obj.move_by(dx, dy)


def _handle_points(x0: int, y0: int, x1: int, y1: int) -> list[HandleHit]:
    mx, my = (x0 + x1) // 2, (y0 + y1) // 2
    return [
        HandleHit(HandleKind.CORNER, "both", x0, y0),
        HandleHit(HandleKind.CORNER, "both", x1, y0),
        HandleHit(HandleKind.CORNER, "both", x0, y1),
        HandleHit(HandleKind.CORNER, "both", x1, y1),
        HandleHit(HandleKind.EDGE_H, "x", x0, my),
        HandleHit(HandleKind.EDGE_H, "x", x1, my),
        HandleHit(HandleKind.EDGE_V, "y", mx, y0),
        HandleHit(HandleKind.EDGE_V, "y", mx, y1),
        HandleHit(HandleKind.ROTATE, "both", mx, y0 - 24),
    ]


def nearest_handle(x: int, y: int, objects: list) -> HandleHit | None:
    if not objects:
        return None
    x0, y0, x1, y1 = selection_bounds(objects)
    best: HandleHit | None = None
    best_d = float("inf")
    for handle in _handle_points(x0, y0, x1, y1):
        d = distance(x, y, handle.x, handle.y)
        if d < best_d and d <= HANDLE_GRAB_RADIUS:
            best_d = d
            best = handle
    return best


def stretch_mode_from_handles(h1: HandleHit | None, h2: HandleHit | None) -> TwoHandLock | None:
    if not h1 or not h2:
        return None
    if h1.kind == HandleKind.EDGE_H and h2.kind == HandleKind.EDGE_H:
        return TwoHandLock.STRETCH_W
    if h1.kind == HandleKind.EDGE_V and h2.kind == HandleKind.EDGE_V:
        return TwoHandLock.STRETCH_H
    return None


def resolve_two_hand_lock(
    anchors: TwoHandAnchors,
    c1: tuple[int, int],
    c2: tuple[int, int],
    current_lock: TwoHandLock,
) -> TwoHandLock:
    if current_lock != TwoHandLock.NONE:
        return current_lock

    if anchors.stretch_w:
        return TwoHandLock.STRETCH_W
    if anchors.stretch_h:
        return TwoHandLock.STRETCH_H

    mid = ((c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2)
    dist = distance(c1[0], c1[1], c2[0], c2[1])
    ang = angle_deg(c1[0], c1[1], c2[0], c2[1])

    dist_change = abs(dist - anchors.distance)
    ang_change = abs(normalize_angle_delta(ang - anchors.angle))
    mid_change = distance(mid[0], mid[1], anchors.midpoint[0], anchors.midpoint[1])

    if dist_change > SCALE_THRESHOLD and ang_change < ROTATION_THRESHOLD:
        return TwoHandLock.SCALE
    if ang_change > ROTATION_THRESHOLD and dist_change < SCALE_THRESHOLD:
        return TwoHandLock.ROTATE
    if (
        mid_change > MOVE_THRESHOLD
        and dist_change < SCALE_THRESHOLD
        and ang_change < ROTATION_THRESHOLD
    ):
        return TwoHandLock.MOVE
    return TwoHandLock.NONE
