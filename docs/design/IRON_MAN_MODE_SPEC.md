# Iron Man Mode — Interactive Object Manipulation

**Version:** 1.0  
**Status:** Phase 1 implemented  
**Goal:** Every canvas object is selectable, transformable, and manipulable via hand gestures.

---

## Architecture

```
FrameProcessor
  ├── HandDrawingManager (draw tools — disabled during pinch/manipulate)
  ├── ManipulationController
  │     ├── SelectionManager
  │     ├── TransformEngine
  │     └── GroupManager
  └── SelectionOverlay (bounding boxes, handles, rotation HUD)
```

## Object Model (DrawableObject)

| Field | Type | Purpose |
|-------|------|---------|
| `id` | str | Unique identifier |
| `type` | str | stroke, line, rectangle, … |
| `offset_x`, `offset_y` | float | Translation |
| `scale_x`, `scale_y` | float | Non-uniform scale (default 1) |
| `rotation` | float | Degrees |
| `z_index` | int | Layer order |
| `selected` | bool | Selection state |
| `group_id` | str \| None | Group membership |
| `created_at`, `updated_at` | str | Timestamps |

Geometry stays in local space; transforms applied at render/hit-test time.

## Gestures (Phase 1)

| Gesture | Mode | Action |
|---------|------|--------|
| Thumb + index pinch | `PINCH` | Select nearest object / grab |
| Pinch + move | `PINCH` | Translate selection |
| Two-hand pinch | `PINCH` × 2 | Scale (distance ratio) + rotate (angle delta) |
| Two pointer hands + Select tool | `POINTER` × 2 | Box selection |
| Open palm | `ERASER` | Erase (unchanged) |
| Index only | `DRAW` | Draw (when not pinching) |

## Keyboard (Phase 1)

| Key | Action |
|-----|--------|
| V | Select / Manipulate mode |
| Delete | Delete selection |
| Ctrl+D | Duplicate selection |
| Ctrl+G | Group selection |
| Ctrl+Shift+G | Ungroup |
| Page Up / Page Down | Layer forward / backward |

## Trash

Bottom-right zone on camera view. Drag selection into trash on pinch release → delete (undoable).

## Future (not Phase 1)

- Throw-to-delete physics
- Pinch eraser resize
- AI diagram rearrange
- Infinite canvas pan/zoom
- Sticky notes, images
