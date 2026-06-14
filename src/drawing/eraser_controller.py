"""Eraser size configuration and controller."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_ERASER_SIZE = 30
MIN_ERASER_SIZE = 10
MAX_ERASER_SIZE = 100


def clamp_eraser_size(size: int) -> int:
    return max(MIN_ERASER_SIZE, min(MAX_ERASER_SIZE, size))


@dataclass
class EraserController:
    """Manages eraser radius; supports future pinch-based resizing."""

    size: int = DEFAULT_ERASER_SIZE
    _pinch_enabled: bool = False

    def __post_init__(self):
        self.size = clamp_eraser_size(self.size)

    def set_size(self, size: int) -> int:
        self.size = clamp_eraser_size(size)
        return self.size

    def adjust(self, delta: int) -> int:
        return self.set_size(self.size + delta)

    def set_from_pinch(
        self,
        thumb_index_distance: float,
        min_distance: float = 20.0,
        max_distance: float = 150.0,
    ) -> int:
        """Future: map pinch distance to eraser size. Stub-ready API."""
        if not self._pinch_enabled:
            return self.size
        if max_distance <= min_distance:
            return self.size
        t = (thumb_index_distance - min_distance) / (max_distance - min_distance)
        t = max(0.0, min(1.0, t))
        mapped = MIN_ERASER_SIZE + t * (MAX_ERASER_SIZE - MIN_ERASER_SIZE)
        return self.set_size(int(mapped))

    def enable_pinch_resize(self, enabled: bool = True) -> None:
        self._pinch_enabled = enabled
