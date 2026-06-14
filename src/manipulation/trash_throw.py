"""Trash throw fly-in animation."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.manipulation.gesture_intelligence import TrashZone, lerp, lerp_point, selection_center


@dataclass
class TrashThrowAnimation:
    progress: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    start_centers: dict[str, tuple[float, float]] = field(default_factory=dict)
    start_scales: dict[str, tuple[float, float]] = field(default_factory=dict)
    object_ids: list[str] = field(default_factory=list)

    @property
    def active(self) -> bool:
        return bool(self.object_ids)

    def start(self, objects: list, trash: TrashZone) -> None:
        tcx, tcy = trash.center
        self.target_x, self.target_y = tcx, tcy
        self.progress = 0.0
        self.object_ids = [o.id for o in objects]
        self.start_centers = {}
        self.start_scales = {}
        for obj in objects:
            self.start_centers[obj.id] = selection_center([obj])
            self.start_scales[obj.id] = (obj.scale_x, obj.scale_y)

    def tick(self, objects: list, dt: float = 0.033) -> bool:
        """Advance animation; return True when complete."""
        if not self.active:
            return False
        self.progress = min(1.0, self.progress + dt * 2.8)
        t = self.progress
        ease = t * t * (3 - 2 * t)
        for obj in objects:
            if obj.id not in self.object_ids:
                continue
            sc = self.start_centers[obj.id]
            nx, ny = lerp_point(sc, (self.target_x, self.target_y), ease)
            cx, cy = selection_center([obj])
            obj.move_by(nx - cx, ny - cy)
            bsx, bsy = self.start_scales[obj.id]
            shrink = lerp(1.0, 0.05, ease)
            obj.scale_x = max(0.05, bsx * shrink)
            obj.scale_y = max(0.05, bsy * shrink)
            obj.touch()
        return self.progress >= 1.0

    def clear(self) -> None:
        self.object_ids.clear()
        self.start_centers.clear()
        self.start_scales.clear()
        self.progress = 0.0
