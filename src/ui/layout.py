"""Four-zone application layout."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def x2(self) -> int:
        return self.x + self.w

    @property
    def y2(self) -> int:
        return self.y + self.h


@dataclass(frozen=True)
class AppLayout:
    window_w: int
    window_h: int
    top_bar: Rect
    bottom_bar: Rect
    left_sidebar: Rect
    right_sidebar: Rect
    content: Rect

    @classmethod
    def compute(cls, window_w: int, window_h: int) -> "AppLayout":
        top_h = max(60, min(80, int(window_h * 0.089)))
        bottom_h = max(36, min(44, int(window_h * 0.056)))
        left_w = max(200, min(250, int(window_w * 0.172)))
        right_w = max(200, min(250, int(window_w * 0.172)))

        content = Rect(
            x=left_w,
            y=top_h,
            w=max(1, window_w - left_w - right_w),
            h=max(1, window_h - top_h - bottom_h),
        )
        return cls(
            window_w=window_w,
            window_h=window_h,
            top_bar=Rect(0, 0, window_w, top_h),
            bottom_bar=Rect(0, window_h - bottom_h, window_w, bottom_h),
            left_sidebar=Rect(0, top_h, left_w, content.h),
            right_sidebar=Rect(window_w - right_w, top_h, right_w, content.h),
            content=content,
        )
