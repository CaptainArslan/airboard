"""Selection bounding box, handles, trash zone, and HUD overlays."""

from __future__ import annotations

import cv2
import numpy as np

from src.manipulation.gesture_intelligence import TrashZone
from src.manipulation.gesture_state import ControlState

_HANDLE = 7
_OUTLINE = (235, 99, 37)
_GLOW = (37, 99, 235)
_CORNER_COLOR = (80, 200, 255)
_EDGE_H_COLOR = (255, 200, 80)
_EDGE_V_COLOR = (200, 255, 80)
_ROTATE_COLOR = (255, 120, 255)
_TRASH_RED = (60, 60, 239)
_TRASH_GLOW = (80, 80, 255)


def draw_selection_overlay(
    frame: np.ndarray,
    objects: list,
    status_hud: str | None = None,
    box_rect: tuple[int, int, int, int] | None = None,
    grabbed: bool = False,
    control_state: ControlState | str | None = None,
) -> None:
    """Draw selection boxes, labeled handles, box-select rect, status HUD."""
    if box_rect:
        x1, y1, x2, y2 = box_rect
        cv2.rectangle(frame, (x1, y1), (x2, y2), _GLOW, 2, cv2.LINE_AA)

    state_val = control_state.value if isinstance(control_state, ControlState) else control_state

    for obj in objects:
        if not getattr(obj, "selected", False):
            continue
        x0, y0, x1, y1 = obj.bounding_box()
        mx, my = (x0 + x1) // 2, (y0 + y1) // 2
        glow_alpha = 0.16 if grabbed else 0.08
        overlay = frame.copy()
        cv2.rectangle(overlay, (x0, y0), (x1, y1), _GLOW, -1)
        cv2.addWeighted(overlay, glow_alpha, frame, 1 - glow_alpha, 0, frame)
        cv2.rectangle(frame, (x0, y0), (x1, y1), _OUTLINE, 2, cv2.LINE_AA)

        handles = [
            (_CORNER_COLOR, x0, y0), (_CORNER_COLOR, x1, y0),
            (_CORNER_COLOR, x0, y1), (_CORNER_COLOR, x1, y1),
            (_EDGE_H_COLOR, x0, my), (_EDGE_H_COLOR, x1, my),
            (_EDGE_V_COLOR, mx, y0), (_EDGE_V_COLOR, mx, y1),
            (_ROTATE_COLOR, mx, y0 - 24),
        ]
        for color, hx, hy in handles:
            cv2.circle(frame, (hx, hy), _HANDLE, color, -1, cv2.LINE_AA)
            cv2.circle(frame, (hx, hy), _HANDLE, (255, 255, 255), 1, cv2.LINE_AA)

    label = status_hud or _state_label(state_val)
    if label:
        bar = frame.copy()
        cv2.rectangle(bar, (8, 8), (min(frame.shape[1] - 8, 420), 44), (16, 16, 28), -1)
        cv2.addWeighted(bar, 0.75, frame, 0.25, 0, frame)
        cv2.putText(
            frame, label, (16, 34),
            cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA,
        )


def _state_label(state_val: str | None) -> str | None:
    if not state_val:
        return None
    return {
        ControlState.SELECTING.value: "Selected",
        ControlState.GRABBING.value: "Grabbed",
        ControlState.MOVING.value: "Moving",
        ControlState.SCALING.value: "Scaling",
        ControlState.ROTATING.value: "Rotating",
        ControlState.STRETCHING.value: "Stretching",
        ControlState.TRASHING.value: "Delete Ready",
        ControlState.TRASH_ANIM.value: "Throw Detected",
        ControlState.TWO_HAND_ARMING.value: "Hold… two-hand control",
        ControlState.TWO_HAND_READY.value: "Two-Hand Control Active",
    }.get(state_val)


def draw_trash_zone(
    frame: np.ndarray,
    trash: TrashZone | None = None,
    hover: bool = False,
    release_hint: bool = False,
    animating: bool = False,
) -> tuple[int, int, int, int]:
    """Draw trash icon (50px visual) and optional 150px hit zone hint."""
    h, w = frame.shape[:2]
    if trash is None:
        trash = TrashZone(w, h)
    x0, y0, x1, y1 = trash.visual_rect
    hx0, hy0, hx1, hy1 = trash.hit_rect

    if hover or release_hint:
        glow = frame.copy()
        cv2.rectangle(glow, (hx0, hy0), (hx1, hy1), _TRASH_GLOW, -1)
        cv2.addWeighted(glow, 0.2, frame, 0.8, 0, frame)
        cv2.rectangle(frame, (hx0, hy0), (hx1, hy1), _TRASH_RED, 2, cv2.LINE_AA)

    scale = 1.35 if (hover or animating) else 1.0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    half = int((x1 - x0) / 2 * scale)
    vx0, vy0 = int(cx - half), int(cy - half)
    vx1, vy1 = int(cx + half), int(cy + half)

    fill = (50, 50, 180) if (hover or animating) else (20, 20, 40)
    border = _TRASH_RED if (hover or release_hint) else (80, 80, 120)
    overlay = frame.copy()
    cv2.rectangle(overlay, (vx0, vy0), (vx1, vy1), fill, -1)
    cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
    cv2.rectangle(frame, (vx0, vy0), (vx1, vy1), border, 2, cv2.LINE_AA)

    icx, icy = int(cx), int(cy) + 4
    cv2.line(frame, (icx - 12, icy - 8), (icx + 12, icy - 8), border, 2, cv2.LINE_AA)
    cv2.line(frame, (icx - 8, icy - 8), (icx - 6, icy + 10), border, 2, cv2.LINE_AA)
    cv2.line(frame, (icx + 8, icy - 8), (icx + 6, icy + 10), border, 2, cv2.LINE_AA)
    cv2.line(frame, (icx - 6, icy + 10), (icx + 6, icy + 10), border, 2, cv2.LINE_AA)
    cv2.putText(
        frame, "TRASH", (vx0 + 4, vy1 - 4),
        cv2.FONT_HERSHEY_SIMPLEX, 0.32, (200, 200, 200), 1, cv2.LINE_AA,
    )
    if release_hint:
        cv2.putText(
            frame, "Release To Delete", (max(8, hx0 - 100), hy0 - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.52, _TRASH_RED, 2, cv2.LINE_AA,
        )
    if animating:
        cv2.putText(
            frame, "Deleted!", (max(8, hx0 - 40), hy0 - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 255, 100), 2, cv2.LINE_AA,
        )
    return vx0, vy0, vx1, vy1


def point_in_rect(x: int, y: int, rect: tuple[int, int, int, int]) -> bool:
    x0, y0, x1, y1 = rect
    return x0 <= x <= x1 and y0 <= y <= y1


_SELECTION_HELP_LINES = (
    "Selection Mode",
    "Pinch once: Select",
    "Pinch + hold: Move (grab offset)",
    "Two-hand pinch 0.4s → scale / rotate / move",
    "Pull hands apart: Bigger · Together: Smaller",
    "Side handles: Stretch · Throw at trash: Auto-delete",
    "Press B: Draw   Press E: Eraser",
)


def draw_selection_help(frame: np.ndarray) -> None:
    """On-screen gesture guide while Pointer tool is idle."""
    h, w = frame.shape[:2]
    line_h = 20
    pad_x, pad_y = 14, 12
    box_h = pad_y * 2 + line_h * len(_SELECTION_HELP_LINES)
    box_w = min(w - 32, 360)
    x0, y0 = 16, h - box_h - 16

    overlay = frame.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + box_w, y0 + box_h), (16, 16, 28), -1)
    cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)
    cv2.rectangle(frame, (x0, y0), (x0 + box_w, y0 + box_h), _GLOW, 1, cv2.LINE_AA)

    for i, line in enumerate(_SELECTION_HELP_LINES):
        y = y0 + pad_y + (i + 1) * line_h - 5
        weight = 2 if i == 0 else 1
        scale = 0.55 if i == 0 else 0.45
        color = (255, 255, 255) if i == 0 else (200, 210, 220)
        cv2.putText(
            frame, line, (x0 + pad_x, y),
            cv2.FONT_HERSHEY_SIMPLEX, scale, color, weight, cv2.LINE_AA,
        )
