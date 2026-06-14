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
from src.manipulation.manipulation_controller import ManipulationController
from src.manipulation.selection_manager import SelectionManager
from src.manipulation.selection_overlay import draw_selection_help, draw_selection_overlay
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
    selection_props: dict | None = None


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
        self._selection = SelectionManager()
        self._manipulation = ManipulationController(self._model, self._selection)
        self._last_camera_frame: np.ndarray | None = None
        self.last_hand_states: list[HandGestureState] = []

    @property
    def hand_manager(self) -> HandDrawingManager:
        return self._hand_manager

    @property
    def canvas_model(self) -> CanvasModel:
        return self._model

    @property
    def manipulation(self) -> ManipulationController:
        return self._manipulation

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
        if current_tool != tools.ERASER:
            return
        positions = hand_manager.eraser_preview_positions(hand_states)
        if not positions:
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
            if mode == GestureMode.OPEN_PALM:
                if state.palm_center:
                    px, py = state.palm_center
                    r = max(6, min(frame.shape[:2]) // 80)
                    cv2.circle(frame, (px, py), r, (120, 120, 120), 1)
                continue
            if not state.fingertip:
                if mode == GestureMode.PINCH and state.pinch_center:
                    px, py = state.pinch_center
                    r = max(6, min(frame.shape[:2]) // 80)
                    cv2.circle(frame, (px, py), r + 2, (37, 99, 235), 2)
                    cv2.circle(frame, (px, py), 4, (235, 99, 37), -1)
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
            elif mode == GestureMode.PINCH and state.pinch_center:
                px, py = state.pinch_center
                cv2.circle(frame, (px, py), r + 2, (37, 99, 235), 2)
                cv2.circle(frame, (px, py), 4, (235, 99, 37), -1)

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

        fh, fw = content.shape[:2]
        current_tool = self._hand_manager.current_tool
        self._manipulation.set_tool(current_tool)

        box_rect = None
        if current_tool == tools.SELECT:
            box_rect, _trash_rect = self._manipulation.update(hand_states, (fw, fh))
        else:
            self._manipulation.trash_hover = False

        if current_tool == tools.TEXT:
            pass
        elif current_tool == tools.SELECT:
            pass
        elif current_tool == tools.ERASER:
            self._hand_manager.update(hand_states)
        elif current_tool in tools.DRAW_TOOLS:
            self._hand_manager.update(hand_states)

        active_strokes, shape_previews = self._hand_manager.collect_live_drawables()
        display = compose_frame(
            content,
            self._model.objects,
            active_strokes,
            shape_previews,
        )

        draw_selection_overlay(
            display,
            self._model.objects,
            status_hud=self._manipulation.status_hud,
            box_rect=box_rect,
            grabbed=self._manipulation.is_grabbed,
            control_state=self._manipulation.control_state,
        )
        if self._manipulation.show_selection_help:
            draw_selection_help(display)
        self._manipulation.draw_trash(display)

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
            left_mode=self._display_hand_mode("Left"),
            right_mode=self._display_hand_mode("Right"),
            color_index=self._hand_manager.color_index,
            brush_size=self._hand_manager.brush_size,
            eraser_size=self._hand_manager.eraser_size,
            current_tool=self._hand_manager.current_tool,
            selection_props=self._manipulation.primary_selected_properties(),
        )

    def _display_hand_mode(self, label: str) -> str:
        mode = self._hand_manager.get_hand_mode(label)
        tool = self._hand_manager.current_tool
        if tool == tools.ERASER and mode == GestureMode.OPEN_PALM:
            return "ERASER"
        if tool == tools.SELECT and mode == GestureMode.PINCH:
            return "PINCH"
        return GestureDetector.display_mode(mode)

    def export_png(self, exports_dir: str) -> str | None:
        if self._last_camera_frame is None:
            return None
        path = CanvasModel.make_export_path(exports_dir)
        self._model.export_composite(path, self._last_camera_frame)
        return str(path)

    def close(self):
        self._camera.release()
        self._tracker.close()
