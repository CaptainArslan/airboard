# Refactor Plan — AirBoard Professional Upgrade

**Date:** 2026-06-14  
**Prerequisite:** Review docs 01–03 and 05 approved  
**Rule:** Implement phase-by-phase; verify acceptance criteria before next phase

---

## Overview

Transform AirBoard from OpenCV prototype to modular desktop app in **9 phases**. Each phase is independently shippable — app must run after every phase.

---

## Phase 1: Stabilize App Shell

**Goal:** Thin entry point; central application class; safe lifecycle.

### Files affected
- `main.py` (shrink to ~5 lines)
- `src/app/application.py` (new)
- `src/app/app_state.py` (new)
- `src/app/__init__.py` (new)

### Tasks
- [ ] Create `AirBoardApplication` with `run()`, `setup()`, `cleanup()`
- [ ] Move main loop from `main.py` into `application.py`
- [ ] Create `AppState` dataclass: `is_fullscreen`, `show_help`, `display_width`, `display_height`
- [ ] Move window setup/teardown to application
- [ ] Ensure `try/finally` releases camera, tracker, windows

### Acceptance criteria
- [ ] `python main.py` works identically to before
- [ ] `main.py` ≤ 10 lines
- [ ] No logic regression in quit/fullscreen/tools

---

## Phase 2: Clean Configuration

**Goal:** Predictable config; fix monitor-vs-window scaling bug.

### Files affected
- `src/config/settings.py`
- `src/ui/theme.py` (new, basic tokens)
- `src/app/application.py`

### Tasks
- [ ] Remove tkinter call from settings import — lazy load in app init
- [ ] Split static config (paths, flags) from runtime config (dimensions)
- [ ] Add `compute_ui_scale(frame_width, frame_height) -> float`
- [ ] Recompute brush/eraser/pointer sizes from **current frame**, not monitor
- [ ] Add `DEBUG_DRAW_SKELETON = False` default
- [ ] Add `logger.py` with INFO/ERROR channels

### Acceptance criteria
- [ ] Windowed 1280×720 has sensible brush/eraser size on 4K monitor
- [ ] Importing settings does not open tkinter
- [ ] Camera failure logs error message

---

## Phase 3: Improve Camera Renderer

**Goal:** Separate capture from composition; handle letterbox correctly.

### Files affected
- `src/camera/camera_manager.py`
- `src/camera/frame_processor.py` (new)
- `src/utils/geometry.py` (new)

### Tasks
- [ ] `CameraManager.read()` returns raw mirrored frame only
- [ ] `FrameProcessor.fit_to_window(frame, w, h)` → letterboxed frame + `ContentRect`
- [ ] Store content rect in `AppState` for optional draw clamping
- [ ] `FrameProcessor.compose(video, canvas, previews)` → single output buffer
- [ ] Preserve canvas on resize: scale buffer with `cv2.resize` instead of wipe

### Acceptance criteria
- [ ] Aspect ratio preserved
- [ ] Fullscreen toggle does not erase drawings
- [ ] No composition logic in `main` or `application` loop body

---

## Phase 4: Improve Gesture State

**Goal:** Type-safe modes; clean detector output.

### Files affected
- `src/gestures/gesture_types.py` (new)
- `src/gestures/gesture_detector.py`
- `src/tracking/hand_models.py` (new — move dataclasses)

### Tasks
- [ ] `HandMode(Enum)`: IDLE, DRAW, POINTER, ERASER, FIST
- [ ] Move `HandGestureState`, `TrackedHand` to dedicated model files
- [ ] Remove string `GestureMode` class
- [ ] Normalize `gesture_detector.py` formatting
- [ ] Document fist → idle mapping in one place

### Acceptance criteria
- [ ] All gesture checks use Enum
- [ ] No regression in draw/pointer/palm eraser detection
- [ ] Type hints pass on gesture modules

---

## Phase 5: Improve Drawing Engine

**Goal:** Split canvas, strokes, shapes; unified input controller.

### Files affected
- `src/drawing/canvas.py`
- `src/drawing/stroke.py` (new)
- `src/drawing/shapes.py` (new)
- `src/drawing/tools.py`
- `src/drawing/hand_manager.py` → refactor to `drawing_controller.py`

### Tasks
- [ ] `ToolMode(Enum)` with FREEHAND, LINE, RECTANGLE, CIRCLE, ARROW, ERASER
- [ ] `StrokeEngine` — per-hand previous points, freehand segments
- [ ] `ShapeEngine` — start/preview/commit FSM
- [ ] `Canvas` — buffer, blend, clear, erase_at only
- [ ] Move shape preview rendering out of Canvas into `shapes.py`
- [ ] Keyboard shortcuts: `1`–`5`, `e`, `x`, `+`, `-` via `InputController`
- [ ] Palm eraser remains gesture-driven; tool `e` optional alias or mode indicator

### Acceptance criteria
- [ ] Two hands draw independently — no line jumps
- [ ] Shape preview + commit on pointer transition
- [ ] `x` clears canvas; `+`/`-` adjust brush
- [ ] No access to `Canvas._previous_points` from outside stroke module

---

## Phase 6: Improve UI Overlay

**Goal:** Professional layout — top bar, left panel, bottom help.

### Files affected
- `src/ui/overlay_renderer.py` (new, replaces `overlay.py`)
- `src/ui/components.py` (new)
- `src/ui/theme.py` (expand)
- Delete or deprecate `src/ui/overlay.py`

### Tasks
- [ ] Implement `TopBarComponent` per design system
- [ ] Implement `LeftToolPanel` with active highlight
- [ ] Implement `BottomHelpBar` (always visible; compact)
- [ ] Implement `HelpOverlay` toggled with `h`
- [ ] Remove duplicate `draw_controls_hint`
- [ ] Color palette with hover hit-test in component
- [ ] Semi-transparent panels (alpha blend onto frame region)

### Acceptance criteria
- [ ] UI matches `05_DESIGN_SYSTEM.md` layout
- [ ] Active tool visibly highlighted
- [ ] Help overlay toggles with `h`
- [ ] Hand skeleton off by default

---

## Phase 7: Add Design System

**Goal:** Centralize all visual tokens; no magic colors in components.

### Files affected
- `src/ui/theme.py`
- All UI components
- Hand indicator renderer

### Tasks
- [ ] Full palette: background, panel, text, accent, eraser, preview
- [ ] Spacing scale: `xs, sm, md, lg` as frame ratios
- [ ] Typography: title, body, caption font scales
- [ ] Eraser: semi-transparent red circle
- [ ] Shape preview: dashed or high-contrast accent
- [ ] Status badges for hand modes (Draw / Pointer / Erase / Idle)

### Acceptance criteria
- [ ] Zero hardcoded BGR tuples in components (all from theme)
- [ ] Readable on 1280×720 and 3440×1440
- [ ] Visual review passes "product prototype" bar

---

## Phase 8: Improve Testing

**Goal:** Prevent regressions on core interactions.

### Files affected
- `tests/` (new)
- `requirements-dev.txt` or optional `pytest` in docs

### Tasks
- [ ] `test_gesture_open_palm`, `test_gesture_draw`, `test_gesture_pointer`
- [ ] `test_per_hand_stroke_isolation`
- [ ] `test_shape_commit_on_mode_change`
- [ ] `test_resize_with_aspect_ratio`
- [ ] `test_canvas_preserve_on_resize`
- [ ] Update `docs/05_TESTING_CHECKLIST.md`

### Acceptance criteria
- [ ] `pytest` passes locally
- [ ] CI-ready test suite (no webcam required for unit tests)

---

## Phase 9: Final Polish

**Goal:** Production-quality local app feel.

### Files affected
- `README.md`
- `docs/02_TECHNICAL_ARCHITECTURE.md` (update)
- Minor fixes across app

### Tasks
- [ ] Update README: gestures, shortcuts, window behavior
- [ ] Remove "MVP" from window title → "AirBoard"
- [ ] Startup status message if model missing (dialog or console)
- [ ] Performance: optional skeleton, avoid redundant frame copies
- [ ] Code pass: type hints, docstrings on public API
- [ ] Manual full checklist run

### Acceptance criteria
- [ ] All 14 final acceptance criteria from master prompt met
- [ ] No obvious prototype junk
- [ ] Review docs archived; architecture doc reflects new structure

---

## Implementation Order (Safe Sequence)

```
Phase 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9
         ↑           ↑
    fix scaling   split drawing before UI depends on new APIs
```

**Parallelizable after Phase 4:** Phase 5 (drawing) and Phase 6 (UI) can overlap if interfaces agreed upfront.

---

## Risk Register

| Risk | Mitigation |
|------|------------|
| OpenCV cannot do true alpha panels | Pre-blend panel color with alpha in numpy ROI |
| Refactor breaks two-hand drawing | Phase 5 unit tests before UI work |
| Keyboard conflicts (`r` rect vs refresh) | Document; use number keys as primary |
| Canvas scale on resize blurs strokes | Accept for v1; document limitation |
| Large refactor scope creep | Stop after each phase; demo to user |

---

## Definition of Done (Full Refactor)

1. App launches with `python main.py`
2. Windowed default; `f` fullscreen; `q`/`Esc` quit
3. Professional UI (top + left + bottom bars)
4. Two-hand independent drawing
5. Palm duster eraser
6. Shape tools with preview
7. Modular `src/` layout per architecture review
8. `main.py` minimal
9. Review docs complete
10. Tests for critical paths
