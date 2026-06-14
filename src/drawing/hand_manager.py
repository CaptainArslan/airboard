"""Per-hand drawing orchestration using object-based canvas."""

from dataclasses import dataclass, field

from src.config import settings
from src.drawing import tools
from src.drawing.eraser_controller import DEFAULT_ERASER_SIZE, EraserController
from src.drawing_objects import (
    Arrow,
    CanvasModel,
    Circle,
    Line,
    Rectangle,
    Stroke,
    Text,
)
from src.drawing_objects.renderer import create_preview_shape
from src.gestures.gesture_detector import GestureMode, HandGestureState

# Minimum pixel distance between freehand points (live stroke smoothing)
MIN_LIVE_POINT_DISTANCE = 3


@dataclass
class HandDrawingState:
    hand_id: int
    handedness: str
    current_position: tuple[int, int] | None = None
    previous_mode: str = GestureMode.IDLE
    current_mode: str = GestureMode.IDLE
    selected_color: tuple[int, int, int] = field(
        default_factory=lambda: settings.COLORS[settings.DEFAULT_COLOR_INDEX]
    )
    brush_size: int = settings.DEFAULT_BRUSH_SIZE
    shape_start_point: tuple[int, int] | None = None
    shape_preview_point: tuple[int, int] | None = None
    active_stroke: Stroke | None = None


class HandDrawingManager:
    """Orchestrates per-hand draw, erase, and shape logic on CanvasModel."""

    def __init__(self, model: CanvasModel):
        self.model = model
        self.current_tool = tools.FREEHAND
        self.brush_size = settings.DEFAULT_BRUSH_SIZE
        self.eraser = EraserController(size=DEFAULT_ERASER_SIZE)
        self._color_index = settings.DEFAULT_COLOR_INDEX
        self._hands: dict[str, HandDrawingState] = {}
        self._erasing_hands: set[str] = set()
        self._last_erase_positions: list[tuple[int, int]] = []

    @property
    def color_index(self) -> int:
        return self._color_index

    @property
    def color(self) -> tuple[int, int, int]:
        return settings.COLORS[self._color_index]

    @property
    def hands(self) -> dict[str, HandDrawingState]:
        return self._hands

    def set_tool(self, tool: str):
        if tool in tools.LABELS and tool != tools.CLEAR:
            self.current_tool = tool

    def set_color_index(self, index: int):
        if 0 <= index < len(settings.COLORS):
            self._color_index = index
            color = settings.COLORS[index]
            for hand in self._hands.values():
                hand.selected_color = color
                if hand.active_stroke is not None:
                    hand.active_stroke.color = color

    def adjust_brush(self, delta: int):
        self.brush_size = max(1, min(40, self.brush_size + delta))
        for hand in self._hands.values():
            hand.brush_size = self.brush_size
            if hand.active_stroke is not None:
                hand.active_stroke.thickness = self.brush_size

    def adjust_eraser(self, delta: int) -> int:
        return self.eraser.adjust(delta)

    def set_eraser_size(self, size: int) -> int:
        return self.eraser.set_size(size)

    @property
    def eraser_size(self) -> int:
        return self.eraser.size

    def eraser_preview_positions(
        self,
        hand_states: list[HandGestureState],
    ) -> list[tuple[int, int]]:
        """Positions where eraser preview circle should render (eraser tool only)."""
        if self.current_tool != tools.ERASER:
            return []
        positions: list[tuple[int, int]] = []
        for state in hand_states:
            if state.mode == GestureMode.OPEN_PALM and state.palm_center:
                positions.append(state.palm_center)
            elif state.fingertip:
                positions.append(state.fingertip)
        return positions

    def clear_canvas(self):
        self.model.clear()
        for hand in self._hands.values():
            hand.shape_start_point = None
            hand.shape_preview_point = None
            hand.active_stroke = None

    def undo(self) -> bool:
        return self.model.undo()

    def redo(self) -> bool:
        return self.model.redo()

    def add_text(self, content: str, position: tuple[int, int], font_size: int = 24):
        if not content.strip():
            return
        self.model.add_object(Text(
            position=position,
            content=content.strip(),
            font_size=font_size,
            color=self.color,
            thickness=1,
        ))

    def collect_live_drawables(self) -> tuple[list[Stroke], list]:
        """Return active strokes and shape preview objects for live rendering."""
        active_strokes: list[Stroke] = []
        shape_previews = []
        for hand in self._hands.values():
            if hand.active_stroke is not None and hand.active_stroke.points:
                active_strokes.append(hand.active_stroke)
            if (
                hand.shape_start_point is not None
                and hand.shape_preview_point is not None
                and self.current_tool in tools.SHAPE_TOOLS
            ):
                preview = create_preview_shape(
                    self.current_tool,
                    hand.shape_start_point,
                    hand.shape_preview_point,
                    hand.selected_color,
                    hand.brush_size,
                )
                if preview is not None:
                    shape_previews.append(preview)
        return active_strokes, shape_previews

    def _hand_label(self, state: HandGestureState) -> str:
        return state.handedness if state.handedness in settings.HAND_LABELS else f"Hand{state.hand_id}"

    def _get_hand(self, state: HandGestureState) -> HandDrawingState:
        label = self._hand_label(state)
        if label not in self._hands:
            self._hands[label] = HandDrawingState(
                hand_id=state.hand_id,
                handedness=label,
                selected_color=self.color,
                brush_size=self.brush_size,
            )
        return self._hands[label]

    def _clear_shape_state(self, hand: HandDrawingState):
        hand.shape_start_point = None
        hand.shape_preview_point = None

    def _clear_active_stroke(self, hand: HandDrawingState):
        hand.active_stroke = None

    def _ensure_active_stroke(self, hand: HandDrawingState) -> Stroke:
        if hand.active_stroke is None:
            hand.active_stroke = Stroke(
                points=[],
                color=hand.selected_color,
                thickness=hand.brush_size,
            )
        return hand.active_stroke

    def _append_stroke_point(self, hand: HandDrawingState, point: tuple[int, int]):
        stroke = self._ensure_active_stroke(hand)
        pts = stroke.points
        if pts:
            last = pts[-1]
            dist_sq = (point[0] - last[0]) ** 2 + (point[1] - last[1]) ** 2
            if dist_sq < MIN_LIVE_POINT_DISTANCE ** 2:
                return
        pts.append(point)

    def _commit_stroke(self, hand: HandDrawingState):
        if hand.active_stroke is not None and hand.active_stroke.points:
            committed = Stroke(
                points=hand.active_stroke.points[:],
                color=hand.active_stroke.color,
                thickness=hand.active_stroke.thickness,
            )
            self.model.add_object(committed)
        hand.active_stroke = None

    def _commit_shape(self, hand: HandDrawingState):
        if hand.shape_start_point is None or hand.shape_preview_point is None:
            self._clear_shape_state(hand)
            return
        start, end = hand.shape_start_point, hand.shape_preview_point
        color, th = hand.selected_color, hand.brush_size
        tool = self.current_tool
        if tool == tools.LINE:
            self.model.add_object(Line(start_point=start, end_point=end, color=color, thickness=th))
        elif tool == tools.RECTANGLE:
            self.model.add_object(Rectangle(start_point=start, end_point=end, color=color, thickness=th))
        elif tool == tools.CIRCLE:
            self.model.add_object(Circle.from_points(start, end, color, th))
        elif tool == tools.ARROW:
            self.model.add_object(Arrow(start_point=start, end_point=end, color=color, thickness=th))
        self._clear_shape_state(hand)

    def _on_mode_exit_draw(self, hand: HandDrawingState):
        if self.current_tool == tools.FREEHAND:
            self._commit_stroke(hand)
        elif self.current_tool in tools.SHAPE_TOOLS:
            self._commit_shape(hand)
        else:
            self._clear_active_stroke(hand)
            self._clear_shape_state(hand)

    def _on_hand_lost(self, label: str):
        hand = self._hands.get(label)
        if hand is None:
            return
        if hand.previous_mode == GestureMode.OPEN_PALM:
            self._end_hand_erase(label)
        if hand.previous_mode == GestureMode.DRAW:
            self._on_mode_exit_draw(hand)
        hand.current_mode = GestureMode.IDLE
        hand.previous_mode = GestureMode.IDLE
        hand.current_position = None

    def _begin_hand_erase(self, label: str) -> None:
        if label not in self._erasing_hands:
            if not self._erasing_hands:
                self.model.begin_erase_batch()
            self._erasing_hands.add(label)

    def _end_hand_erase(self, label: str) -> None:
        if label in self._erasing_hands:
            self._erasing_hands.discard(label)
            if not self._erasing_hands:
                self.model.end_erase_batch()

    def _handle_erase_gesture(self, hand: HandDrawingState, label: str, px: int, py: int) -> None:
        self._begin_hand_erase(label)
        self.model.apply_eraser(px, py, self.eraser.size)
        hand.active_stroke = None
        self._clear_shape_state(hand)
        self._last_erase_positions.append((px, py))

    def _erase_position(self, state: HandGestureState) -> tuple[int, int] | None:
        if state.mode == GestureMode.OPEN_PALM and state.palm_center:
            return state.palm_center
        if state.mode == GestureMode.DRAW and state.fingertip:
            return state.fingertip
        return None

    def update(self, hand_states: list[HandGestureState]) -> None:
        active_labels = set()
        self._last_erase_positions.clear()
        tool = self.current_tool
        can_erase = tool == tools.ERASER
        can_draw = tool in tools.DRAW_TOOLS and tool != tools.TEXT

        for state in hand_states:
            label = self._hand_label(state)
            active_labels.add(label)
            hand = self._get_hand(state)
            prev_mode = hand.previous_mode
            hand.current_mode = state.mode
            hand.current_position = state.fingertip

            if prev_mode == GestureMode.DRAW and state.mode != GestureMode.DRAW:
                self._on_mode_exit_draw(hand)

            if prev_mode == GestureMode.OPEN_PALM and state.mode != GestureMode.OPEN_PALM:
                self._end_hand_erase(label)

            if can_erase:
                pos = self._erase_position(state)
                if pos is not None:
                    self._handle_erase_gesture(hand, label, pos[0], pos[1])

            elif can_draw and state.mode == GestureMode.DRAW and state.fingertip is not None:
                if tool == tools.FREEHAND:
                    self._append_stroke_point(hand, state.fingertip)
                    self._clear_shape_state(hand)
                elif tool in tools.SHAPE_TOOLS:
                    if hand.shape_start_point is None:
                        hand.shape_start_point = state.fingertip
                    hand.shape_preview_point = state.fingertip
                    hand.active_stroke = None

            hand.previous_mode = state.mode

        for label in list(self._hands.keys()):
            if label not in active_labels:
                self._on_hand_lost(label)

    def get_hand_mode(self, label: str) -> str:
        hand = self._hands.get(label)
        if hand is None:
            return GestureMode.IDLE
        mode = hand.current_mode
        if mode == GestureMode.FIST:
            return GestureMode.IDLE
        return mode

    def pointer_position(self, hand_states: list[HandGestureState]) -> tuple[int, int] | None:
        for state in hand_states:
            if state.mode in (GestureMode.DRAW, GestureMode.POINTER) and state.fingertip:
                return state.fingertip
        for state in hand_states:
            if state.fingertip:
                return state.fingertip
        return None
