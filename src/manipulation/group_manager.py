"""Object grouping helpers."""

from __future__ import annotations

import uuid

from src.drawing_objects.base import DrawableObject


def group_objects(objects: list[DrawableObject], ids: set[str]) -> str | None:
    targets = [o for o in objects if o.id in ids]
    if len(targets) < 2:
        return None
    gid = str(uuid.uuid4())
    for obj in targets:
        obj.group_id = gid
        obj.touch()
    return gid


def ungroup_objects(objects: list[DrawableObject], ids: set[str]) -> int:
    count = 0
    group_ids = {o.group_id for o in objects if o.id in ids and o.group_id}
    for obj in objects:
        if obj.group_id in group_ids:
            obj.group_id = None
            obj.touch()
            count += 1
    return count
