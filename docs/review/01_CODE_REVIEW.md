# Code Review — AirBoard Local MVP

**Reviewer role:** Senior Python architect  
**Date:** 2026-06-14  
**Scope:** Full `src/` tree, `main.py`, config, utilities

---

## Executive Summary

The application works and demonstrates meaningful features (two-hand drawing, shapes, eraser, fullscreen toggle), but the codebase still reads like an iterative prototype. Logic is spread across `main.py`, `HandDrawingManager`, `Canvas`, and `Overlay` with overlapping responsibilities, stringly-typed modes, and UI concerns mixed into the render loop.

---

## Bad Practices Found

| Issue | Location | Detail |
|-------|----------|--------|
| **God loop** | `main.py` | 120-line file orchestrates camera, gestures, color hover, drawing, rendering, keyboard, and window mode in one `while True` block |
| **String modes** | `gesture_detector.py`, `hand_manager.py` | `GestureMode` and tools use class constants / raw strings instead of `Enum` |
| **Private attribute access** | `hand_manager.py:131` | `self.canvas._previous_points.get(label)` breaks encapsulation |
| **Duplicate state** | `Canvas`, `HandDrawingState` | Previous points exist in both `Canvas._previous_points` and `HandDrawingState.previous_position`; only canvas dict is used |
| **Debug left on** | `settings.py` | `DRAW_HAND_SKELETON = True` exposes green/red landmark debug art to end users |
| **Settings side effects at import** | `settings.py` | Calls `get_primary_monitor_size()` and computes scaled pixels at import time; windowed 1280×720 uses monitor-scaled brush/eraser sizes |
| **Inconsistent keyboard docs** | `overlay.py`, `tools.py`, `README.md` | Toolbar says `h=Freehand`; README still mentions fist-clear; no `e`, `x`, `+`, `-` shortcuts from target spec |
| **No logging** | Entire project | Failures print nothing; camera/model errors only raise at init |
| **Bare except** | `display.py:22` | `except Exception: pass` hides monitor detection failures |

---

## Duplicate Code

1. **Shape drawing** — `Canvas.commit_shape`, `Canvas.draw_shape_preview`, and individual `draw_*_shape` methods repeat the same tool→OpenCV mapping.
2. **Mode display** — `GestureDetector.display_mode()` and fist→idle mapping duplicated in `overlay.draw_hand_feedback`.
3. **Layout math** — `scale_from_screen(...)` called repeatedly in `overlay.py` with similar ratio patterns; no shared layout helper.
4. **Hand label resolution** — `_hand_label()` in `HandDrawingManager` vs `settings.HAND_LABELS` vs MediaPipe `handedness` strings used inconsistently.

---

## Hardcoded Values

| Value | Where | Problem |
|-------|-------|---------|
| `(40, 40, 40)` toolbar | `settings.TOOLBAR_BG_COLOR` | Not in theme system |
| `(0, 255, 0)` skeleton | `hand_tracker.draw_skeleton` | Debug colors hardcoded |
| `2`, `3` pixel radii | `hand_tracker`, `overlay` | Not scaled from frame |
| `tipLength=0.25` | `canvas.py` | Magic number for arrows |
| `CANVAS_ALPHA = 0.85` | settings | Not user-configurable |
| OpenCV font | `FONT_HERSHEY_SIMPLEX` everywhere | No typography abstraction |

**Scaling bug:** Brush/eraser/UI radii are computed from **monitor** size at import, but the app often runs at **1280×720**. A 3440×1440 monitor yields oversized eraser radius when windowed.

---

## Poor Function / Class Names

| Current | Issue | Suggested |
|---------|-------|-----------|
| `HandDrawingManager` | Does gestures + tools + per-hand state | `DrawingController` or split into `StrokeController` + `ShapeController` |
| `Overlay` | Toolbar + swatches + hand feedback + hints | Split into `ToolbarRenderer`, `HandIndicatorRenderer`, `HelpBarRenderer` |
| `tools.py` | Module name collides with concept of "tools" | `tool_modes.py` or `ToolMode` enum module |
| `draw_to` | Unclear vs shape draw | `draw_freehand_segment` |
| `_LandmarkWrapper` | Leaky adapter for MediaPipe | Move to `hand_models.py` as documented type |

---

## Poor Class Design

### `Canvas`
- Owns pixel buffer **and** per-hand stroke continuity **and** shape primitives **and** preview rendering (static method on wrong class).
- `resize()` **wipes all drawings** when toggling fullscreen — data loss with no user warning.
- `blend()` copies full frame every frame — acceptable for MVP, not documented.

### `HandDrawingManager`
- Knows about `GestureMode`, `HandGestureState`, tools, and canvas internals.
- Gesture-driven eraser (open palm) and tool-driven drawing share one `current_tool` but eraser is not a tool in `tools.py`.
- No keyboard-triggered clear (`x`) or brush resize (`+`/`-`).

### `GestureDetector`
- `GestureMode` as plain class constants — not an Enum, no type safety.
- Smoothing keyed by `{handedness}_{index}` but drawing keyed by `Left`/`Right` only — two hands same label edge case unhandled.
- `gesture_detector.py` has excessive blank lines (formatting drift).

### `Overlay`
- Single class handles layout, hit-testing, and drawing — violates single responsibility.
- `check_color_hover` mutates hover state as side effect of read operation.
- Instructions duplicated: toolbar line 81 + `draw_controls_hint()`.

---

## Missing Error Handling

| Scenario | Current behavior |
|----------|------------------|
| Webcam frame read fails | Silent `break` from loop — no message |
| Model file missing | `FileNotFoundError` at startup only — good |
| MediaPipe init failure | Uncaught |
| Canvas resize on fullscreen | Drawings lost silently |
| Invalid hand label | Falls back to `Hand{id}` without logging |
| tkinter unavailable | Falls back to 1920×1080 silently |

---

## State Management Problems

```
main.py
  ├── is_fullscreen, display_width/height  (window — should be AppState)
  ├── canvas, hand_manager                 (lazy init)
  └── overlay hover counts                 (inside Overlay)

HandDrawingManager
  ├── current_tool                         (global tool)
  └── _hands[Left|Right]                   (per-hand draw/shape/color)

Canvas
  ├── _previous_points[Left|Right]         (actual stroke continuity)
  └── color_index / color                  (global color, duplicated per hand)
```

**Problems:**
- Window state lives in `main.py`, not a dedicated `AppState`.
- Global `current_tool` vs per-hand gesture eraser — two eraser concepts (palm vs tool `e`) not unified.
- Color selection updates one hand but also mutates global `canvas.color`.
- No single source of truth for "what is the app doing right now."

---

## Performance Issues

| Issue | Impact | Severity |
|-------|--------|----------|
| Full frame `copy()` in `blend()` every frame | Memory + CPU at 3440×1440 | Medium |
| Hand skeleton drawn by default | Visual noise + ~42 lines + 21 circles per hand | Low |
| Layout recalc only on size change | Good | — |
| MediaPipe on full letterboxed frame including black bars | Landmarks mapped to letterbox coords — drawing on black bars possible | Medium UX |
| No frame skip / target FPS cap | CPU burn on fast machines | Low |

---

## Testing Gaps

- No unit tests for gesture classification, aspect-ratio resize, or per-hand stroke isolation.
- No automated smoke test for `python main.py`.
- Manual checklist in `docs/05_TESTING_CHECKLIST.md` is outdated (fist clear, 1280×720 only).

---

## Suggested Fixes (Priority Order)

1. Introduce `AppState` dataclass and move loop to `AirBoardApplication`.
2. Replace string modes with `Enum` (`ToolMode`, `HandMode`).
3. Split `Canvas` (buffer) from `StrokeEngine` / `ShapeEngine`.
4. Fix scale-at-import bug — derive brush/UI sizes from **current frame size**, not monitor.
5. Add `logger.py` and user-visible error toasts or status bar messages.
6. Turn off skeleton by default; gate behind debug flag.
7. Preserve canvas content on resize (scale buffer with `cv2.resize`).
8. Consolidate keyboard handling into one `InputController`.
9. Add type hints to all public methods (partial today).
10. Remove duplicate instruction strings; single help overlay source.

---

## Files Needing Most Attention

| File | Severity |
|------|----------|
| `main.py` | High — refactor first |
| `src/ui/overlay.py` | High — UX bottleneck |
| `src/drawing/hand_manager.py` | High — state complexity |
| `src/config/settings.py` | Medium — scaling + organization |
| `src/drawing/canvas.py` | Medium — split responsibilities |
| `src/gestures/gesture_detector.py` | Medium — enums + cleanup |
| `README.md` | Low — stale docs |
