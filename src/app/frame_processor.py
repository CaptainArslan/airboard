"""Frame processing — camera, tracking, drawing (no UI)."""

from dataclasses import dataclass

import cv2
import numpy as np

from src.app.app_state import AppState
from src.camera.camera_manager import CameraManager
from src.config import settings
from src.drawing import tools
from src.drawing.eraser_preview import draw_eraser_preview
from src.drawing.hand_manager import HandDrawingManager
from src.drawing_objects import CanvasModel
from src.drawing_objects.renderer import compose_frame
from src.gestures.gesture_detector import GestureDetector, GestureMode, HandGestureState
from src.tracking.hand_tracker import HandTracker
from src.utils.display import resize_with_aspect_ratio


@dataclass
class FrameResult:
    frame: np.ndarray
    camera_frame: np.ndarray
    letterbox_w: int
    letterbox_h: int
    hand_states: list[HandGestureState]
    shape_previews: list
    left_mode: str
    right_mode: str
    color_index: int
    brush_size: int
    eraser_size: int
    current_tool: str


class FrameProcessor:
    def __init__(self, app_state: AppState | None = None):
        self.app_state = app_state or AppState()
        self._camera = CameraManager()
        self._tracker = HandTracker()
        self._gestures = GestureDetector()
        self._model = CanvasModel(640, 480)
        self._hand_manager = HandDrawingManager(self._model)
        self._hand_manager.brush_size = settings.DEFAULT_BRUSH_SIZE
        self._hand_manager.set_eraser_size(settings.DEFAULT_ERASER_SIZE)
        self._last_camera_frame: np.ndarray | None = None
        self.last_hand_states: list[HandGestureState] = []

    @property
    def hand_manager(self) -> HandDrawingManager:
        return self._hand_manager

    @property
    def canvas_model(self) -> CanvasModel:
        return self._model

    def _ensure_canvas(self, w: int, h: int):
        if self._model.width != w or self._model.height != h:
            self._model.resize(w, h)
        self.app_state.frame_width = w
        self.app_state.frame_height = h

    @staticmethod
    def _letterbox_size(raw_w: int, raw_h: int, avail_w: int, avail_h: int) -> tuple[int, int]:
        if raw_w <= 0 or raw_h <= 0:
            return avail_w, avail_h
        scale = min(avail_w / raw_w, avail_h / raw_h)
        return max(1, int(raw_w * scale)), max(1, int(raw_h * scale))

    @staticmethod
    def _draw_eraser_previews(
        frame: np.ndarray,
        hand_manager: HandDrawingManager,
        hand_states: list[HandGestureState],
        current_tool: str,
    ):
        radius = hand_manager.eraser_size
        erasing = any(
            s.mode == GestureMode.ERASER and s.palm_center for s in hand_states
        )
        tool_active = current_tool == tools.ERASER
        if not erasing and not tool_active:
            return
        positions = hand_manager.eraser_preview_positions(hand_states)
        if tool_active and not positions:
            h, w = frame.shape[:2]
            positions = [(w // 2, h // 2)]
        seen = set()
        for cx, cy in positions:
            key = (cx // 4, cy // 4)
            if key in seen:
                continue
            seen.add(key)
            draw_eraser_preview(frame, cx, cy, radius)

    @staticmethod
    def _draw_indicators(
        frame: np.ndarray,
        hand_states: list[HandGestureState],
        brush_color: tuple[int, int, int],
    ):
        for state in hand_states:
            mode = GestureMode.FIST if state.mode == GestureMode.FIST else state.mode
            if mode == GestureMode.ERASER:
                continue
            if not state.fingertip:
                continue
            fx, fy = state.fingertip
            r = max(6, min(frame.shape[:2]) // 80)
            if mode == GestureMode.DRAW:
                glow = frame.copy()
                cv2.circle(glow, (fx, fy), r + 5, brush_color, -1)
                cv2.addWeighted(glow, 0.25, frame, 0.75, 0, frame)
                cv2.circle(frame, (fx, fy), r, brush_color, -1)
            elif mode == GestureMode.POINTER:
                cv2.circle(frame, (fx, fy), r, (255, 255, 255), 2)

    def _draw_text_draft(self, display: np.ndarray):
        if not self.app_state.text_input_active or not self.app_state.text_draft:
            return
        pos = self.app_state.text_position
        if pos is None:
            h, w = display.shape[:2]
            pos = (w // 4, h // 2)
        color = settings.COLORS[self.app_state.selected_color_index]
        cv2.putText(
            display, self.app_state.text_draft + "|", pos,
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA,
        )

    def process(self, avail_w: int, avail_h: int) -> FrameResult | None:
        raw = self._camera.read_raw()
        if raw is None:
            return None

        inner_w = max(1, avail_w)
        inner_h = max(1, avail_h)
        lh, lw = raw.shape[:2]
        letter_w, letter_h = self._letterbox_size(lw, lh, inner_w, inner_h)

        content = resize_with_aspect_ratio(raw, letter_w, letter_h)
        self._ensure_canvas(letter_w, letter_h)
        self._last_camera_frame = content.copy()

        hands = self._tracker.process(content)
        hand_states = self._gestures.classify_hands(hands)
        self.last_hand_states = hand_states

        if self.app_state.current_tool.value != tools.TEXT:
            self._hand_manager.update(hand_states)

        active_strokes, shape_previews = self._hand_manager.collect_live_drawables()
        display = compose_frame(
            content,
            self._model.objects,
            active_strokes,
            shape_previews,
        )

        self._draw_eraser_previews(
            display, self._hand_manager, hand_states, self._hand_manager.current_tool,
        )
        self._draw_indicators(display, hand_states, self._hand_manager.color)
        self._draw_text_draft(display)

        return FrameResult(
            frame=display,
            camera_frame=content,
            letterbox_w=letter_w,
            letterbox_h=letter_h,
            hand_states=hand_states,
            shape_previews=shape_previews,
            left_mode=GestureDetector.display_mode(self._hand_manager.get_hand_mode("Left")),
            right_mode=GestureDetector.display_mode(self._hand_manager.get_hand_mode("Right")),
            color_index=self._hand_manager.color_index,
            brush_size=self._hand_manager.brush_size,
            eraser_size=self._hand_manager.eraser_size,
            current_tool=self._hand_manager.current_tool,
        )

    def export_png(self, exports_dir: str) -> str | None:
        if self._last_camera_frame is None:
            return None
        path = CanvasModel.make_export_path(exports_dir)
        self._model.export_composite(path, self._last_camera_frame)
        return str(path)

    def close(self):
        self._camera.release()
        self._tracker.close()
