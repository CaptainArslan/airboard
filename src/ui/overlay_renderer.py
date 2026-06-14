"""Composites content and renders the full application chrome."""

from __future__ import annotations

import cv2
import numpy as np

from src.app.app_state import AppState
from src.drawing import tools
from src.drawing.canvas import Canvas
from src.ui.components import (
    BottomStatusBar,
    HandIndicators,
    HelpPanel,
    RightSidebar,
    Toolbar,
    ToolButton,
)
from src.ui.layout import AppLayout
from src.ui.theme import Theme
from src.utils.display import resize_with_aspect_ratio


class OverlayRenderer:
    def __init__(self):
        self._tool_button = ToolButton()

    def fit_content(self, frame: np.ndarray, layout: AppLayout, theme: Theme) -> np.ndarray:
        """Letterbox camera frame into content rect."""
        content = layout.content
        fitted = resize_with_aspect_ratio(frame, content.w, content.h)
        # Replace black letterbox with app background
        mask = np.all(fitted == 0, axis=2)
        fitted[mask] = theme.colors.content_letterbox
        return fitted

    def compose_window(
        self,
        window_w: int,
        window_h: int,
        content_frame: np.ndarray,
    ) -> tuple[np.ndarray, AppLayout, tuple[int, int]]:
        layout = AppLayout.compute(window_w, window_h)
        theme = Theme(window_w, window_h)
        app_frame = np.full(
            (window_h, window_w, 3), theme.colors.bg_app, dtype=np.uint8,
        )
        c = layout.content
        ch, cw = content_frame.shape[:2]
        app_frame[c.y:c.y + ch, c.x:c.x + cw] = content_frame[:ch, :cw]
        return app_frame, layout, (c.x, c.y)

    def render(
        self,
        app_frame: np.ndarray,
        layout: AppLayout,
        app_state: AppState,
        current_tool: str,
        left_mode: str,
        right_mode: str,
        gesture_states,
        brush_color: tuple[int, int, int],
        eraser_radius: int,
        shape_previews: list,
        content_offset: tuple[int, int],
    ):
        theme = Theme(layout.window_w, layout.window_h)

        Toolbar.draw(
            app_frame, layout.top_bar, current_tool,
            app_state.selected_color_index, app_state.brush_size,
            left_mode, right_mode, theme,
        )
        self._tool_button.draw_sidebar(
            app_frame, layout.left_sidebar, current_tool,
            app_state.selected_color_index, theme,
        )
        RightSidebar.draw(
            app_frame, layout.right_sidebar, left_mode, right_mode, theme,
        )
        BottomStatusBar.draw(app_frame, layout.bottom_bar, theme)

        ox, oy = content_offset
        for preview in shape_previews:
            tool, start, end, color, thickness = preview
            if start and end:
                s = (start[0] + ox, start[1] + oy)
                e = (end[0] + ox, end[1] + oy)
                Canvas.draw_shape_preview(app_frame, tool, s, e, color, thickness)

        HandIndicators.draw(
            app_frame, content_offset, gesture_states,
            brush_color, eraser_radius, theme,
        )

        if app_state.show_help:
            HelpPanel.draw(app_frame, theme)

    def build_hit_regions(self, layout: AppLayout, current_tool: str, color_index: int) -> ToolButton:
        """Build sidebar hit-test regions without rendering."""
        theme = Theme(layout.window_w, layout.window_h)
        tb = ToolButton()
        sidebar = layout.left_sidebar
        px = sidebar.x + theme.pad_md()
        py = sidebar.y + theme.pad_md() + 32
        row_h = max(34, int(sidebar.h * 0.055))
        from src.ui.layout import Rect
        from src.ui.theme import DRAWING_SWATCHES
        for tool_id, _, _ in ToolButton.TOOL_ITEMS:
            tb._rects[tool_id] = Rect(px - 4, py - 20, sidebar.w - theme.pad_md() * 2, row_h)
            py += row_h
        py += theme.pad_sm() + 28
        cols, swatch, gap = 4, max(22, min(32, (sidebar.w - theme.pad_md() * 2 - 12) // 4)), 8
        for i in range(len(DRAWING_SWATCHES)):
            col, row = i % cols, i // cols
            sx = px + col * (swatch + gap)
            sy = py + row * (swatch + gap)
            tb._color_rects.append((Rect(sx, sy, swatch, swatch), i))
        return tb

    def process_click(self, x: int, y: int, layout: AppLayout, current_tool: str,
                      color_index: int, hand_manager, app_state: AppState) -> bool:
        tb = self.build_hit_regions(layout, current_tool, color_index)
        tool = tb.hit_test_tool(x, y)
        if tool == tools.CLEAR:
            hand_manager.clear_canvas()
            return True
        if tool and tool != tools.CLEAR:
            hand_manager.set_tool(tool)
            return True
        idx = tb.hit_test_color(x, y)
        if idx is not None:
            hand_manager.set_color_index(idx)
            app_state.selected_color_index = idx
            return True
        return False
