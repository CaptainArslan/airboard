"""Responsive layout metrics — all sizes derived from window dimensions."""

from dataclasses import dataclass


@dataclass
class LayoutMetrics:
    window_w: int
    window_h: int
    toolbar_h: int
    status_h: int
    left_w: int
    right_w: int
    content_w: int
    content_h: int

    @classmethod
    def from_window(cls, window_w: int, window_h: int) -> "LayoutMetrics":
        toolbar_h = max(56, min(72, int(window_h * 0.08)))
        status_h = max(36, min(44, int(window_h * 0.055)))
        left_w = max(240, min(320, int(window_w * 0.18)))
        right_w = max(220, min(300, int(window_w * 0.16)))
        content_w = max(400, window_w - left_w - right_w)
        content_h = max(300, window_h - toolbar_h - status_h)
        return cls(
            window_w=window_w,
            window_h=window_h,
            toolbar_h=toolbar_h,
            status_h=status_h,
            left_w=left_w,
            right_w=right_w,
            content_w=content_w,
            content_h=content_h,
        )
