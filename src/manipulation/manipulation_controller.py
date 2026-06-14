"""Strict intent-locked manipulation — reliable two-hand scale & trash throw."""

from __future__ import annotations

import time

from src.drawing import tools
from src.drawing_objects.canvas_model import CanvasModel
from src.drawing_objects.transform import angle_deg, distance
from src.gestures.gesture_detector import GestureMode, HandGestureState
from src.manipulation.gesture_intelligence import (
    MIN_MOVEMENT,
    ROTATION_THRESHOLD,
    SCALE_THRESHOLD,
    THROW_ALIGNMENT_MIN,
    THROW_SPEED_THRESHOLD,
    TWO_HAND_HOLD_SEC,
    PointSmoother,
    TrashZone,
    TwoHandAnchors,
    TwoHandLock,
    apply_magnetic_snap,
    clamp_scale,
    move_selection_to_center,
    nearest_handle,
    normalize_angle_delta,
    resolve_two_hand_lock,
    selection_center,
    stretch_mode_from_handles,
    throw_alignment,
)
from src.manipulation.gesture_state import ControlState
from src.manipulation.group_manager import group_objects, ungroup_objects
from src.manipulation.selection_manager import SelectionManager
from src.manipulation.selection_overlay import draw_trash_zone
from src.manipulation.trash_throw import TrashThrowAnimation

PINCH_HOLD_MS = 180
PINCH_MOVE_PX = 12


class ManipulationController:
    def __init__(self, model: CanvasModel, selection: SelectionManager):
        self.model = model
        self.selection = selection
        self.current_tool = tools.FREEHAND
        self.control_state = ControlState.IDLE
        self.status_hud: str | None = None
        self.trash_hover = False
        self.trash_snapping = False
        self.is_grabbed = False
        self._smoother = PointSmoother()
        self._selection_locked = False
        self._gesture_lock: TwoHandLock = TwoHandLock.NONE
        self._single_lock: ControlState | None = None
        self._two_hand_arm_start: float | None = None
        self._two_hand_ready = False
        self._anchors: TwoHandAnchors | None = None
        self._batch_active = False
        self._pinch_engaged = False
        self._pinch_start: tuple[int, int] | None = None
        self._pinch_start_time: float = 0.0
        self._grab_offset: tuple[float, float] = (0.0, 0.0)
        self._was_grabbed = False
        self._prev_object_center: tuple[float, float] | None = None
        self._velocity: tuple[float, float] = (0.0, 0.0)
        self._box_select_active = False
        self._delete_on_release = False
        self._trash: TrashZone | None = None
        self._throw_anim = TrashThrowAnimation()
        self._pending_delete_after_anim = False

    @property
    def is_manipulating(self) -> bool:
        return (
            self._single_lock is not None
            or self._two_hand_ready
            or self._throw_anim.active
        )

    @property
    def show_trash(self) -> bool:
        return bool(self.selection.selected_ids) or self._throw_anim.active

    @property
    def show_selection_help(self) -> bool:
        return (
            self.current_tool == tools.SELECT
            and self.control_state == ControlState.IDLE
            and not self.selection.selected_ids
            and not self._throw_anim.active
        )

    @property
    def selection_fade(self) -> float:
        if self.control_state == ControlState.TRASHING:
            return 0.55
        return 1.0

    def set_tool(self, tool: str) -> None:
        if tool != tools.SELECT and self.is_manipulating:
            self._reset_session(commit_batch=True)
        if tool != tools.SELECT:
            self.control_state = ControlState.IDLE
            self.status_hud = None
        elif self.selection.selected_ids:
            self.control_state = ControlState.SELECTING
        self.current_tool = tool

    def _pinch_hands(self, hand_states: list[HandGestureState]) -> list[HandGestureState]:
        return [s for s in hand_states if s.mode == GestureMode.PINCH and s.pinch_center]

    def _smooth_pinches(self, pinches: list[HandGestureState]) -> list[tuple[int, int]]:
        pts: list[tuple[int, int]] = []
        for i, s in enumerate(pinches):
            if s.pinch_center:
                key = f"{s.handedness}_{i}"
                pts.append(self._smoother.smooth(key, s.pinch_center[0], s.pinch_center[1]))
        return pts

    def _reset_session(self, commit_batch: bool = True) -> None:
        if commit_batch and self._batch_active:
            self.model.end_manipulation_batch()
        self._batch_active = False
        self._gesture_lock = TwoHandLock.NONE
        self._single_lock = None
        self._two_hand_ready = False
        self._two_hand_arm_start = None
        self._anchors = None
        self._pinch_engaged = False
        self._selection_locked = False
        self._pinch_start = None
        self._grab_offset = (0.0, 0.0)
        self._was_grabbed = False
        self._prev_object_center = None
        self._velocity = (0.0, 0.0)
        self._smoother.clear()
        self.is_grabbed = False
        self.trash_hover = False
        self.trash_snapping = False
        self._delete_on_release = False
        if self.selection.selected_ids:
            self.control_state = ControlState.SELECTING
        else:
            self.control_state = ControlState.IDLE

    def _begin_batch(self) -> None:
        if not self._batch_active:
            self.model.begin_manipulation_batch()
            self._batch_active = True

    def _track_velocity(self) -> None:
        selected = self.selection.get_selected(self.model.objects)
        if not selected:
            return
        cx, cy = selection_center(selected)
        if self._prev_object_center is not None:
            self._velocity = (cx - self._prev_object_center[0], cy - self._prev_object_center[1])
        self._prev_object_center = (cx, cy)

    def _apply_grab_offset(self, hand_x: float, hand_y: float) -> None:
        selected = self.selection.get_selected(self.model.objects)
        if not selected:
            return
        tx = hand_x - self._grab_offset[0]
        ty = hand_y - self._grab_offset[1]
        move_selection_to_center(selected, tx, ty)
        self.model.mark_manipulation_changed()
        self._track_velocity()

    def _begin_single_grab(self, center: tuple[int, int]) -> None:
        selected = self.selection.get_selected(self.model.objects)
        if not selected:
            return
        self._begin_batch()
        cx, cy = selection_center(selected)
        gx, gy = self._pinch_start or center
        self._grab_offset = (gx - cx, gy - cy)
        self._single_lock = ControlState.MOVING
        self.is_grabbed = True
        self._was_grabbed = True
        self.control_state = ControlState.GRABBING
        self.status_hud = "Grabbed"

    def _build_anchors(self, c1: tuple[int, int], c2: tuple[int, int]) -> TwoHandAnchors:
        selected = self.selection.get_selected(self.model.objects)
        h1 = nearest_handle(c1[0], c1[1], selected)
        h2 = nearest_handle(c2[0], c2[1], selected)
        stretch = stretch_mode_from_handles(h1, h2)
        mid = ((c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2)
        dist = max(distance(c1[0], c1[1], c2[0], c2[1]), 1.0)
        return TwoHandAnchors(
            left=(float(c1[0]), float(c1[1])),
            right=(float(c2[0]), float(c2[1])),
            midpoint=mid,
            distance=dist,
            angle=angle_deg(c1[0], c1[1], c2[0], c2[1]),
            sep_x=max(abs(c1[0] - c2[0]), 1.0),
            sep_y=max(abs(c1[1] - c2[1]), 1.0),
            object_center=selection_center(selected),
            scales=[(o.scale_x, o.scale_y) for o in selected],
            rotations=[o.rotation for o in selected],
            stretch_w=stretch == TwoHandLock.STRETCH_W,
            stretch_h=stretch == TwoHandLock.STRETCH_H,
        )

    def _enter_two_hand_ready(self, c1: tuple[int, int], c2: tuple[int, int]) -> None:
        self._begin_batch()
        self._two_hand_ready = True
        self._two_hand_arm_start = None
        self._anchors = self._build_anchors(c1, c2)
        self._gesture_lock = TwoHandLock.NONE
        self._single_lock = None
        self.is_grabbed = True
        self._was_grabbed = True
        self.control_state = ControlState.TWO_HAND_READY
        self.status_hud = "Two-Hand Control Active"

    def _lock_from_two_hand(self, lock: TwoHandLock) -> ControlState:
        return {
            TwoHandLock.MOVE: ControlState.MOVING,
            TwoHandLock.SCALE: ControlState.SCALING,
            TwoHandLock.ROTATE: ControlState.ROTATING,
            TwoHandLock.STRETCH_W: ControlState.STRETCHING,
            TwoHandLock.STRETCH_H: ControlState.STRETCHING,
        }[lock]

    def _hud_for_lock(self, lock: TwoHandLock) -> str:
        return {
            TwoHandLock.MOVE: "Move Locked",
            TwoHandLock.SCALE: "Scaling Locked",
            TwoHandLock.ROTATE: "Rotation Locked",
            TwoHandLock.STRETCH_W: "Stretching Locked",
            TwoHandLock.STRETCH_H: "Stretching Locked",
        }.get(lock, "Two-Hand Control Active")

    def _apply_two_hand(self, c1: tuple[int, int], c2: tuple[int, int]) -> None:
        if not self._anchors:
            return
        selected = self.selection.get_selected(self.model.objects)
        if not selected:
            return

        a = self._anchors
        mid = ((c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2)
        dist = distance(c1[0], c1[1], c2[0], c2[1])
        ang = angle_deg(c1[0], c1[1], c2[0], c2[1])
        sep_x = max(abs(c1[0] - c2[0]), 1.0)
        sep_y = max(abs(c1[1] - c2[1]), 1.0)

        if self._gesture_lock == TwoHandLock.NONE:
            self._gesture_lock = resolve_two_hand_lock(a, c1, c2, TwoHandLock.NONE)
            if self._gesture_lock != TwoHandLock.NONE:
                self.control_state = self._lock_from_two_hand(self._gesture_lock)
                self.status_hud = self._hud_for_lock(self._gesture_lock)

        lock = self._gesture_lock
        if lock == TwoHandLock.NONE:
            return

        selected = self.selection.get_selected(self.model.objects)
        if not selected:
            return

        if lock == TwoHandLock.MOVE:
            tx = a.object_center[0] + (mid[0] - a.midpoint[0])
            ty = a.object_center[1] + (mid[1] - a.midpoint[1])
            move_selection_to_center(selected, tx, ty)
            self.model.mark_manipulation_changed()
            self.status_hud = "Move Locked"

        elif lock == TwoHandLock.SCALE:
            dist_change = abs(dist - a.distance)
            if dist_change >= SCALE_THRESHOLD:
                ratio = dist / a.distance
                for i, obj in enumerate(selected):
                    if i < len(a.scales):
                        bsx, bsy = a.scales[i]
                        obj.scale_x = clamp_scale(bsx * ratio)
                        obj.scale_y = clamp_scale(bsy * ratio)
                    obj.touch()
                self.model.mark_manipulation_changed()
            pct = int(selected[0].scale_x * 100)
            self.status_hud = f"Scaling Locked — {pct}%"

        elif lock == TwoHandLock.ROTATE:
            delta = normalize_angle_delta(ang - a.angle)
            if abs(delta) >= ROTATION_THRESHOLD * 0.5:
                for i, obj in enumerate(selected):
                    if i < len(a.rotations):
                        obj.rotation = (a.rotations[i] + delta) % 360
                    obj.touch()
                self.model.mark_manipulation_changed()
            self.status_hud = f"Rotation Locked — {int(selected[0].rotation)}°"

        elif lock == TwoHandLock.STRETCH_W:
            if abs(sep_x - a.sep_x) >= SCALE_THRESHOLD:
                ratio = sep_x / a.sep_x
                for i, obj in enumerate(selected):
                    if i < len(a.scales):
                        bsx, bsy = a.scales[i]
                        obj.scale_x = clamp_scale(bsx * ratio)
                        obj.scale_y = bsy
                    obj.touch()
                self.model.mark_manipulation_changed()
            x0, y0, x1, y1 = selected[0].bounding_box()
            self.status_hud = f"Stretching Locked — W:{int(x1 - x0)}"

        elif lock == TwoHandLock.STRETCH_H:
            if abs(sep_y - a.sep_y) >= SCALE_THRESHOLD:
                ratio = sep_y / a.sep_y
                for i, obj in enumerate(selected):
                    if i < len(a.scales):
                        bsx, bsy = a.scales[i]
                        obj.scale_x = bsx
                        obj.scale_y = clamp_scale(bsy * ratio)
                    obj.touch()
                self.model.mark_manipulation_changed()
            x0, y0, x1, y1 = selected[0].bounding_box()
            self.status_hud = f"Stretching Locked — H:{int(y1 - y0)}"

    def _update_trash_interaction(self, hand_x: float, hand_y: float) -> tuple[float, float]:
        if not self._trash:
            return hand_x, hand_y
        selected = self.selection.get_selected(self.model.objects)
        nx, ny, snapped = apply_magnetic_snap(hand_x, hand_y, self._trash)
        if snapped:
            self.trash_snapping = True
            move_selection_to_center(selected, nx, ny)
            self.model.mark_manipulation_changed()
        else:
            self.trash_snapping = False

        in_zone = self._trash.contains_center(selected) if selected else self._trash.contains_point(hand_x, hand_y)
        near = self._trash.should_snap(hand_x, hand_y)
        self.trash_hover = in_zone or near
        self._delete_on_release = in_zone
        if in_zone:
            self.control_state = ControlState.TRASHING
            self.status_hud = "Release to Delete"
        elif near:
            self.status_hud = "Release to Delete"
        return nx, ny

    def _start_throw_delete(self) -> None:
        if not self._trash:
            return
        selected = self.selection.get_selected(self.model.objects)
        if not selected:
            return
        self._begin_batch()
        self._throw_anim.start(selected, self._trash)
        self._pending_delete_after_anim = True
        self.control_state = ControlState.TRASH_ANIM
        self.status_hud = "Throw Detected"

    def _on_pinch_down(self, center: tuple[int, int]) -> None:
        self._pinch_start = center
        self._pinch_start_time = time.monotonic()
        self._pinch_engaged = True
        if not self._selection_locked:
            self.selection.select_at(center[0], center[1], self.model.objects)
            self.selection.expand_to_groups(self.model.objects)
            self._selection_locked = True
        if self.selection.selected_ids:
            self.control_state = ControlState.SELECTING
            self.status_hud = "Selected"
        else:
            self.control_state = ControlState.IDLE
            self.status_hud = None

    def _should_begin_grab(self, center: tuple[int, int]) -> bool:
        if not self._pinch_start or not self.selection.selected_ids:
            return False
        held_ms = (time.monotonic() - self._pinch_start_time) * 1000
        moved = distance(center[0], center[1], self._pinch_start[0], self._pinch_start[1])
        return held_ms >= PINCH_HOLD_MS or moved >= PINCH_MOVE_PX

    def _on_pinch_up(self) -> None:
        selected = self.selection.get_selected(self.model.objects)
        cx, cy = selection_center(selected) if selected else (0.0, 0.0)

        if self._delete_on_release:
            self.delete_selected()
            self.status_hud = "Deleted"
        elif self._was_grabbed and self._trash and selected:
            speed, align = throw_alignment(self._velocity, cx, cy, self._trash)
            if speed >= THROW_SPEED_THRESHOLD and align >= THROW_ALIGNMENT_MIN:
                self._start_throw_delete()
            elif self._batch_active:
                self.model.end_manipulation_batch()
                self._batch_active = False
        elif self._batch_active:
            self.model.end_manipulation_batch()
            self._batch_active = False

        if not self._throw_anim.active:
            self._gesture_lock = TwoHandLock.NONE
            self._single_lock = None
            self._two_hand_ready = False
            self._anchors = None
            self._pinch_engaged = False
            self._selection_locked = False
            self._pinch_start = None
            self._was_grabbed = False
            self._prev_object_center = None
            self._velocity = (0.0, 0.0)
            self.is_grabbed = False
            self.trash_hover = False
            self.trash_snapping = False
            self._delete_on_release = False
            if self.selection.selected_ids and self.control_state != ControlState.TRASH_ANIM:
                self.control_state = ControlState.SELECTING
                self.status_hud = "Selected"
            elif not self.selection.selected_ids:
                self.control_state = ControlState.IDLE
                self.status_hud = None

    def tick_throw_animation(self) -> None:
        if not self._throw_anim.active:
            return
        selected = self.selection.get_selected(self.model.objects)
        done = self._throw_anim.tick(selected)
        if done and self._pending_delete_after_anim:
            self.delete_selected()
            self.status_hud = "Deleted"
            self._throw_anim.clear()
            self._pending_delete_after_anim = False

    def update(
        self,
        hand_states: list[HandGestureState],
        frame_size: tuple[int, int],
    ) -> tuple[tuple[int, int, int, int] | None, tuple[int, int, int, int] | None]:
        self.tick_throw_animation()
        w, h = frame_size
        self._trash = TrashZone(w, h)

        if self.current_tool != tools.SELECT or self._throw_anim.active:
            self.trash_hover = False
            return None, self._trash.visual_rect if self._trash else None

        pinches = self._pinch_hands(hand_states)
        smooth = self._smooth_pinches(pinches)
        was_pinching = self._pinch_engaged and not self._two_hand_ready

        pointers = [s for s in hand_states if s.mode == GestureMode.POINTER and s.fingertip]
        box_rect = None
        if len(pointers) >= 2 and not self._pinch_engaged and not self._two_hand_ready:
            p1, p2 = pointers[0].fingertip, pointers[1].fingertip
            assert p1 and p2
            self.selection.box_start = p1
            self.selection.box_end = p2
            box_rect = (p1[0], p1[1], p2[0], p2[1])
            self._box_select_active = True
        elif self._box_select_active and self.selection.box_start and self.selection.box_end:
            a, b = self.selection.box_start, self.selection.box_end
            self.selection.select_in_rect(a[0], a[1], b[0], b[1], self.model.objects)
            self.selection.expand_to_groups(self.model.objects)
            self.selection.box_start = None
            self.selection.box_end = None
            self._box_select_active = False
            if self.selection.selected_ids:
                self.control_state = ControlState.SELECTING

        # Two-hand: arm → ready → locked transform
        if len(hand_states) >= 2 and len(smooth) >= 2 and self.selection.selected_ids:
            c1, c2 = smooth[0], smooth[1]
            if not self._two_hand_ready:
                if self._two_hand_arm_start is None:
                    self._two_hand_arm_start = time.monotonic()
                    self.control_state = ControlState.TWO_HAND_ARMING
                    self.status_hud = "Hold… two-hand control"
                elif time.monotonic() - self._two_hand_arm_start >= TWO_HAND_HOLD_SEC:
                    self._single_lock = None
                    self._enter_two_hand_ready(c1, c2)
                return box_rect, self._trash.visual_rect
            self._apply_two_hand(c1, c2)
            return box_rect, self._trash.visual_rect

        if self._two_hand_arm_start and len(smooth) < 2:
            self._two_hand_arm_start = None
            if self.control_state == ControlState.TWO_HAND_ARMING:
                self.control_state = (
                    ControlState.SELECTING if self.selection.selected_ids else ControlState.IDLE
                )
                self.status_hud = "Selected" if self.selection.selected_ids else None

        if self._two_hand_ready and len(smooth) < 2:
            self._on_pinch_up()

        # Single-hand pinch
        if len(smooth) == 1:
            center = smooth[0]
            if not self._pinch_engaged:
                self._on_pinch_down(center)
            elif self._single_lock is None and self._should_begin_grab(center):
                self._begin_single_grab(center)

            if self._single_lock == ControlState.MOVING:
                self._apply_grab_offset(center[0], center[1])
                self._update_trash_interaction(center[0], center[1])
                if self.control_state != ControlState.TRASHING:
                    self.control_state = ControlState.MOVING
                    self.status_hud = "Moving"
            return box_rect, self._trash.visual_rect

        if was_pinching:
            self._on_pinch_up()

        return box_rect, self._trash.visual_rect

    def delete_selected(self) -> None:
        ids = set(self.selection.selected_ids)
        if ids:
            self.model.delete_objects(ids)
            self.selection.clear(self.model.objects)
            self.control_state = ControlState.IDLE
            self.status_hud = None
            self._batch_active = False

    def duplicate_selected(self) -> None:
        self.model.duplicate_objects(self.selection.selected_ids)

    def group_selected(self) -> None:
        group_objects(self.model.objects, self.selection.selected_ids)
        self.model.commit_manipulation()

    def ungroup_selected(self) -> None:
        ungroup_objects(self.model.objects, self.selection.selected_ids)
        self.model.commit_manipulation()

    def layer_forward(self) -> None:
        self.model.layer_selected(self.selection.selected_ids, 1)

    def layer_backward(self) -> None:
        self.model.layer_selected(self.selection.selected_ids, -1)

    def draw_trash(self, frame) -> None:
        if not self.show_trash or not self._trash:
            return
        draw_trash_zone(
            frame,
            trash=self._trash,
            hover=self.trash_hover,
            release_hint=self._delete_on_release or self.trash_snapping,
            animating=self._throw_anim.active,
        )

    def primary_selected_properties(self) -> dict | None:
        selected = self.selection.get_selected(self.model.objects)
        if not selected:
            return None
        obj = selected[0]
        x0, y0, x1, y1 = obj.bounding_box()
        return {
            "type": obj.type,
            "x": int(x0),
            "y": int(y0),
            "width": int(x1 - x0),
            "height": int(y1 - y0),
            "rotation": int(obj.rotation),
            "scale_x": round(obj.scale_x, 2),
            "scale_y": round(obj.scale_y, 2),
            "color": obj.color,
            "thickness": obj.thickness,
            "z_index": obj.z_index,
            "group_id": obj.group_id or "—",
            "count": len(selected),
            "grabbed": self.is_grabbed,
            "control_state": self.control_state.value,
        }
