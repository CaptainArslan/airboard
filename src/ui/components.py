"""Reusable UI components for AirBoard."""

from __future__ import annotations

import cv2
import numpy as np

from src.drawing import tools
from src.gestures.gesture_detector import GestureMode
from src.ui.layout import Rect
from src.ui.theme import COLOR_NAMES, DRAWING_SWATCHES, Theme


def _blend_rect(frame: np.ndarray, rect: Rect, color: tuple[int, int, int], alpha: float):
    x1, y1 = max(0, rect.x), max(0, rect.y)
    x2, y2 = min(frame.shape[1], rect.x2), min(frame.shape[0], rect.y2)
    if x2 <= x1 or y2 <= y1:
        return
    roi = frame[y1:y2, x1:x2]
    overlay = np.full_like(roi, color)
    cv2.addWeighted(overlay, alpha, roi, 1 - alpha, 0, roi)


def _draw_rounded_panel(frame: np.ndarray, rect: Rect, theme: Theme, alpha: float = 0.92):
    _blend_rect(frame, rect, theme.colors.bg_panel, alpha)
    cv2.rectangle(
        frame, (rect.x, rect.y), (rect.x2 - 1, rect.y2 - 1),
        theme.colors.border, 1,
    )


def _text(frame, text, x, y, theme: Theme, scale_key: str = "label", color=None, thickness=None):
    scale = {
        "title": theme.font_title(),
        "section": theme.font_section(),
        "label": theme.font_label(),
        "help": theme.font_help(),
    }[scale_key]
    thick = thickness or (theme.thickness_title() if scale_key == "title" else theme.thickness_body())
    cv2.putText(
        frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
        scale, color or theme.colors.text_primary, thick, cv2.LINE_AA,
    )


class StatusBadge:
    @staticmethod
    def draw(frame, x, y, label: str, status: str, theme: Theme):
        status_upper = status.upper()
        if status_upper in ("DRAW",):
            dot_color = theme.colors.accent
        elif status_upper == "POINTER":
            dot_color = theme.colors.warning
        elif status_upper == "ERASER":
            dot_color = theme.colors.danger
        elif status_upper == "IDLE":
            dot_color = theme.colors.success
        else:
            dot_color = theme.colors.text_secondary

        _text(frame, label, x, y, theme, "label", theme.colors.text_secondary)
        cv2.circle(frame, (x + 8, y + 18), 5, dot_color, -1)
        _text(frame, status_upper.capitalize(), x + 20, y + 22, theme, "help", theme.colors.text_primary)


class ToolButton:
    TOOL_ITEMS = (
        (tools.FREEHAND, "Freehand", "~"),
        (tools.LINE, "Line", "/"),
        (tools.RECTANGLE, "Rectangle", "[]"),
        (tools.CIRCLE, "Circle", "O"),
        (tools.ARROW, "Arrow", ">"),
        (tools.ERASER, "Eraser", "="),
        (tools.CLEAR, "Clear All", "x"),
    )

    def __init__(self):
        self._rects: dict[str, Rect] = {}
        self._color_rects: list[tuple[Rect, int]] = []

    def hit_test_tool(self, x: int, y: int) -> str | None:
        for tool_id, rect in self._rects.items():
            if rect.x <= x < rect.x2 and rect.y <= y < rect.y2:
                return tool_id
        return None

    def hit_test_color(self, x: int, y: int) -> int | None:
        for rect, idx in self._color_rects:
            if rect.x <= x < rect.x2 and rect.y <= y < rect.y2:
                return idx
        return None

    def draw_sidebar(
        self,
        frame: np.ndarray,
        rect: Rect,
        current_tool: str,
        color_index: int,
        theme: Theme,
    ):
        self._rects.clear()
        self._color_rects.clear()
        _draw_rounded_panel(frame, rect, theme)

        x = rect.x + theme.pad_md()
        y = rect.y + theme.pad_md()
        _text(frame, "Tools", x, y + 16, theme, "section")
        y += 32

        row_h = max(34, int(rect.h * 0.055))
        for tool_id, label, icon in self.TOOL_ITEMS:
            item_rect = Rect(x - 4, y - 20, rect.w - theme.pad_md() * 2, row_h)
            self._rects[tool_id] = item_rect
            is_active = tool_id == current_tool
            if is_active:
                cv2.rectangle(
                    frame, (item_rect.x, item_rect.y + 2),
                    (item_rect.x2, item_rect.y2 - 2),
                    theme.colors.accent_soft, -1,
                )
                cv2.rectangle(
                    frame, (item_rect.x, item_rect.y + 2),
                    (item_rect.x + 3, item_rect.y2 - 2),
                    theme.colors.accent, -1,
                )
            _text(
                frame, f"{icon}  {label}", x + 8, y,
                theme, "label",
                theme.colors.text_primary if is_active else theme.colors.text_secondary,
            )
            y += row_h

        y += theme.pad_sm()
        _text(frame, "Colors", x, y + 14, theme, "section")
        y += 28

        cols = 4
        swatch = max(22, min(32, (rect.w - theme.pad_md() * 2 - 12) // cols))
        gap = 8
        for i, color in enumerate(DRAWING_SWATCHES):
            col = i % cols
            row = i // cols
            sx = x + col * (swatch + gap)
            sy = y + row * (swatch + gap)
            sw_rect = Rect(sx, sy, swatch, swatch)
            self._color_rects.append((sw_rect, i))
            cv2.circle(frame, (sx + swatch // 2, sy + swatch // 2), swatch // 2, color, -1)
            if i == color_index:
                cv2.circle(
                    frame, (sx + swatch // 2, sy + swatch // 2),
                    swatch // 2 + 2, theme.colors.accent, 2,
                )


class Toolbar:
    @staticmethod
    def draw(
        frame: np.ndarray,
        rect: Rect,
        current_tool: str,
        color_index: int,
        brush_size: int,
        left_mode: str,
        right_mode: str,
        theme: Theme,
    ):
        _blend_rect(frame, rect, theme.colors.bg_panel, 0.95)
        cv2.line(
            frame, (rect.x, rect.y2 - 1), (rect.x2, rect.y2 - 1),
            theme.colors.border, 1,
        )

        x = theme.pad_lg()
        y = rect.y + int(rect.h * 0.62)

        # Logo mark
        cv2.rectangle(
            frame, (x, rect.y + 18), (x + 28, rect.y + 46),
            theme.colors.accent, -1,
        )
        _text(frame, "AirBoard", x + 40, y, theme, "title")

        sections = [
            ("Tool", tools.LABELS.get(current_tool, current_tool)),
            ("Color", COLOR_NAMES[color_index] if color_index < len(COLOR_NAMES) else "?"),
            ("Brush Size", f"{brush_size}px"),
        ]
        sx = x + 200
        for title, value in sections:
            _text(frame, title, sx, rect.y + int(rect.h * 0.38), theme, "help", theme.colors.text_secondary)
            _text(frame, value, sx, y, theme, "label")
            sx += 140

        StatusBadge.draw(frame, sx, rect.y + int(rect.h * 0.28), "Left Hand", left_mode, theme)
        StatusBadge.draw(frame, sx + 130, rect.y + int(rect.h * 0.28), "Right Hand", right_mode, theme)

        help_x = rect.x2 - 220
        _text(frame, "?  Help (H)", help_x, y, theme, "label", theme.colors.text_secondary)
        _text(frame, "[] Fullscreen (F)", help_x + 110, y, theme, "help", theme.colors.text_secondary)


class RightSidebar:
    SHORTCUTS = (
        ("1", "Freehand"),
        ("2", "Line"),
        ("3", "Rectangle"),
        ("4", "Circle"),
        ("5", "Arrow"),
        ("E", "Eraser"),
        ("X", "Clear"),
        ("F", "Fullscreen"),
        ("H", "Help"),
        ("Q", "Quit"),
    )

    @staticmethod
    def draw(
        frame: np.ndarray,
        rect: Rect,
        left_mode: str,
        right_mode: str,
        theme: Theme,
    ):
        _draw_rounded_panel(frame, rect, theme)
        x = rect.x + theme.pad_md()
        y = rect.y + theme.pad_lg()

        _text(frame, "Hand Status", x, y, theme, "section")
        y += 36
        for label, mode in (("Left Hand", left_mode), ("Right Hand", right_mode)):
            card_y = y
            cv2.rectangle(
                frame, (x, card_y), (rect.x2 - theme.pad_md(), card_y + 56),
                theme.colors.badge_idle_bg, -1,
            )
            cv2.rectangle(
                frame, (x, card_y), (rect.x2 - theme.pad_md(), card_y + 56),
                theme.colors.border, 1,
            )
            icon_x = x + 28
            icon_y = card_y + 28
            cv2.circle(frame, (icon_x, icon_y), 18, theme.colors.accent_soft, -1)
            _text(frame, label[:1], icon_x - 5, icon_y + 6, theme, "label")
            _text(frame, label, x + 56, card_y + 24, theme, "label")
            status_color = theme.colors.success if mode.upper() == "IDLE" else theme.colors.accent
            cv2.circle(frame, (x + 56, card_y + 40), 4, status_color, -1)
            _text(frame, mode.capitalize(), x + 68, card_y + 44, theme, "help")
            y += 68

        y += theme.pad_md()
        _text(frame, "Shortcuts", x, y, theme, "section")
        y += 28
        for key, action in RightSidebar.SHORTCUTS:
            _text(frame, key, x, y, theme, "help", theme.colors.accent)
            _text(frame, action, x + 28, y, theme, "help", theme.colors.text_secondary)
            y += 22


class BottomStatusBar:
    @staticmethod
    def draw(frame: np.ndarray, rect: Rect, theme: Theme):
        _blend_rect(frame, rect, theme.colors.bg_panel, 0.95)
        cv2.line(frame, (rect.x, rect.y), (rect.x2, rect.y), theme.colors.border, 1)
        y = rect.y + int(rect.h * 0.68)
        _text(
            frame,
            "Draw with index finger  |  Open palm to erase  |  Two fingers for pointer",
            theme.pad_lg(), y, theme, "help", theme.colors.text_secondary,
        )
        _text(
            frame, "q / Esc = Quit  |  f = Fullscreen  |  h = Help",
            rect.x2 - 340, y, theme, "help", theme.colors.text_secondary,
        )


class HelpPanel:
    @staticmethod
    def draw(frame: np.ndarray, theme: Theme):
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

        cx, cy = frame.shape[1] // 2, frame.shape[0] // 2
        card_w, card_h = int(frame.shape[1] * 0.45), int(frame.shape[0] * 0.55)
        card = Rect(cx - card_w // 2, cy - card_h // 2, card_w, card_h)
        _draw_rounded_panel(frame, card, theme, alpha=0.98)

        x = card.x + theme.pad_lg()
        y = card.y + theme.pad_lg() + 20
        _text(frame, "AirBoard — Help", x, y, theme, "title")
        y += 40
        lines = [
            "Window:  Q / Esc Quit   F Fullscreen   H Close help",
            "",
            "Tools:   1 Freehand  2 Line  3 Rectangle",
            "         4 Circle  5 Arrow  E Eraser  X Clear",
            "",
            "Brush:   + larger   - smaller",
            "",
            "Gestures:",
            "  Index finger only      Draw",
            "  Index + middle         Pointer (move)",
            "  Open palm              Eraser duster",
        ]
        for line in lines:
            _text(frame, line, x, y, theme, "help", theme.colors.text_secondary)
            y += 24


class HandIndicators:
    @staticmethod
    def draw(
        frame: np.ndarray,
        content_offset: tuple[int, int],
        gesture_states,
        brush_color: tuple[int, int, int],
        eraser_radius: int,
        theme: Theme,
    ):
        ox, oy = content_offset
        for state in gesture_states:
            mode = GestureMode.FIST if state.mode == GestureMode.FIST else state.mode

            if mode == GestureMode.ERASER and state.palm_center:
                px, py = state.palm_center[0] + ox, state.palm_center[1] + oy
                overlay = frame.copy()
                cv2.circle(overlay, (px, py), eraser_radius, theme.colors.danger, -1)
                cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)
                cv2.circle(frame, (px, py), eraser_radius, theme.colors.danger, 2)
                continue

            if not state.fingertip:
                continue
            fx, fy = state.fingertip[0] + ox, state.fingertip[1] + oy
            r = max(6, int(theme.frame_min * 0.009))

            if mode == GestureMode.DRAW:
                glow = frame.copy()
                cv2.circle(glow, (fx, fy), r + 6, brush_color, -1)
                cv2.addWeighted(glow, 0.25, frame, 0.75, 0, frame)
                cv2.circle(frame, (fx, fy), r, brush_color, -1)
                cv2.circle(frame, (fx, fy), r + 2, brush_color, 1)
            elif mode == GestureMode.POINTER:
                cv2.circle(frame, (fx, fy), r - 1, theme.colors.pointer, 2)
                cv2.circle(frame, (fx, fy), 2, theme.colors.pointer, -1)
