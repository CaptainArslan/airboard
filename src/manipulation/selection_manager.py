"""Object selection state."""

from __future__ import annotations

from src.drawing_objects.base import DrawableObject


class SelectionManager:
    def __init__(self):
        self._selected_ids: set[str] = set()
        self.box_start: tuple[int, int] | None = None
        self.box_end: tuple[int, int] | None = None

    @property
    def selected_ids(self) -> set[str]:
        return self._selected_ids

    def clear(self, objects: list[DrawableObject] | None = None) -> None:
        if objects:
            for obj in objects:
                obj.selected = False
        self._selected_ids.clear()
        self.box_start = None
        self.box_end = None

    def _apply_selection_flags(self, objects: list[DrawableObject]) -> None:
        for obj in objects:
            obj.selected = obj.id in self._selected_ids

    def select_ids(self, ids: set[str], objects: list[DrawableObject]) -> None:
        self._selected_ids = set(ids)
        self._apply_selection_flags(objects)

    def select_at(self, x: int, y: int, objects: list[DrawableObject], additive: bool = False) -> bool:
        hits = [o for o in objects if o.hit_test(x, y)]
        if not hits:
            if not additive:
                self.clear(objects)
            return False
        nearest = min(hits, key=lambda o: o.distance_to_point(x, y))
        if additive and nearest.id in self._selected_ids:
            self._selected_ids.discard(nearest.id)
        elif additive:
            self._selected_ids.add(nearest.id)
        else:
            self._selected_ids = {nearest.id}
        self._apply_selection_flags(objects)
        return True

    def select_in_rect(
        self,
        x1: int, y1: int, x2: int, y2: int,
        objects: list[DrawableObject],
    ) -> int:
        left, right = sorted((x1, x2))
        top, bottom = sorted((y1, y2))
        ids: set[str] = set()
        for obj in objects:
            ox0, oy0, ox1, oy1 = obj.bounding_box()
            if ox1 >= left and ox0 <= right and oy1 >= top and oy0 <= bottom:
                ids.add(obj.id)
        self._selected_ids = ids
        self._apply_selection_flags(objects)
        return len(ids)

    def get_selected(self, objects: list[DrawableObject]) -> list[DrawableObject]:
        return [o for o in objects if o.id in self._selected_ids]

    def expand_to_groups(self, objects: list[DrawableObject]) -> set[str]:
        """Include all objects sharing group_id with any selected object."""
        selected = self.get_selected(objects)
        group_ids = {o.group_id for o in selected if o.group_id}
        ids = set(self._selected_ids)
        for obj in objects:
            if obj.group_id and obj.group_id in group_ids:
                ids.add(obj.id)
        self._selected_ids = ids
        self._apply_selection_flags(objects)
        return ids
