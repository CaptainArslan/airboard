# Architecture Review — AirBoard Local MVP

**Reviewer role:** Senior Python architect  
**Date:** 2026-06-14

---

## Current Module Structure

```
airboard-local/
  main.py                    # Entry + game loop + input + window + orchestration
  src/
    camera/
      camera_manager.py      # Capture, flip, aspect-ratio resize
    tracking/
      hand_tracker.py        # MediaPipe, TrackedHand dataclass
    gestures/
      gesture_detector.py    # GestureMode, HandGestureState, classify
    drawing/
      canvas.py              # Buffer, strokes, shapes, erase, blend
      hand_manager.py        # Per-hand draw/shape/erase orchestration
      tools.py               # Tool string constants + KEY_MAP
    ui/
      overlay.py             # All UI drawing + color hit-test
    config/
      settings.py            # Constants, monitor detect, scaled values
    utils/
      display.py             # Monitor size, aspect resize, window helpers
  docs/                      # Original MVP planning (partially stale)
  models/
    hand_landmarker.task
```

---

## Module Responsibilities (As-Is)

| Module | Responsibility | Assessment |
|--------|----------------|------------|
| `main.py` | Everything wiring | ❌ Too much |
| `camera_manager` | Webcam I/O + resize | ✅ Focused |
| `hand_tracker` | ML inference + skeleton debug draw | ⚠️ Debug draw should leave tracking |
| `gesture_detector` | Finger state → mode | ✅ Reasonable |
| `canvas` | Buffer + draw + erase + blend + preview | ❌ Overloaded |
| `hand_manager` | Per-hand logic + tool selection side effects | ⚠️ Needs split |
| `overlay` | Layout + render + input hit-test | ❌ Overloaded |
| `settings` | Config + monitor probe + UI scale | ⚠️ Import side effects |
| `display` | Window + geometry utils | ✅ Good seed for `utils/` |

---

## Coupling Analysis

```
                    main.py
                       │
     ┌─────────────────┼─────────────────┐
     ▼                 ▼                 ▼
 CameraManager    HandTracker      GestureDetector
     │                 │                 │
     └────────────┬────┴────────┬────────┘
                  ▼             ▼
           HandDrawingManager  Overlay
                  │
                  ▼
               Canvas
```

**Tight couplings:**
- `main` → knows gesture modes, tool keys, overlay hover, canvas resize, display dimensions
- `hand_manager` → `GestureMode`, `HandGestureState`, `tools`, `Canvas._previous_points`
- `overlay` → `tools.LABELS`, `GestureMode`, raw `settings` ratios
- `settings` → `display.get_primary_monitor_size()` at import (config depends on GUI tkinter)

**Missing layers:**
- No `Application` / `AppState`
- No `InputController` for keyboard
- No `FrameProcessor` separating camera image from composited output
- No `Theme` / `UIComponents`

---

## Mixed Responsibilities

| Location | Mixed concerns |
|----------|----------------|
| `main.py` | Lifecycle + event loop + input mapping + lazy init |
| `Canvas.draw_shape_preview` | UI preview on display frame inside data layer |
| `HandTracker.draw_skeleton` | Inference + debug rendering |
| `Overlay.check_color_hover` | Input detection + state mutation + rendering prep |
| `hand_manager.update` | Gesture interpretation + tool application + shape FSM |

---

## How State Should Be Organized

### Recommended state model

```python
AppState
├── window: WindowState (width, height, is_fullscreen, show_help)
├── tool: ToolMode
├── brush: BrushState (size, color_index, color_bgr)
└── hands: dict[str, HandState]  # "Left", "Right"

HandState
├── gesture: HandMode          # from detector this frame
├── point: Point | None
├── stroke: StrokeState        # previous_point for freehand
└── shape: ShapeState          # start, preview

CanvasState
└── pixel_buffer: ndarray      # only permanent pixels
```

**Rules:**
- Gesture detection produces **read-only** `HandGestureState` per frame.
- Drawing controller **mutates** `HandState` and canvas buffer based on gestures + active tool.
- UI **reads** `AppState` only — never mutates drawing state.
- Window state changes go through `Application` — not scattered in `main`.

---

## Communication Flow (Target)

```
Frame tick:
  1. InputController.poll_keys() → updates AppState
  2. CameraManager.read(size) → BGR frame
  3. HandTracker.process(frame) → list[TrackedHand]
  4. GestureDetector.classify(hands) → list[HandGestureState]
  5. DrawingController.update(app_state, gestures) → mutates canvas + hand stroke state
  6. FrameProcessor.compose(frame, canvas, previews) → composited BGR
  7. OverlayRenderer.render(composited, app_state) → final BGR
  8. Display.present(final)
```

All modules communicate through **explicit inputs/outputs**, not by reaching into private fields.

---

## Target Module Structure (From Spec)

```
src/
  app/
    application.py       # AirBoardApplication.run() main loop
    app_state.py         # AppState, WindowState dataclasses
  camera/
    camera_manager.py    # Capture only
    frame_processor.py   # Letterbox, compose video + canvas + preview layer
  tracking/
    hand_tracker.py      # Inference only
    hand_models.py       # TrackedHand, LandmarkWrapper
  gestures/
    gesture_detector.py  # Classification only
    gesture_types.py     # HandMode Enum, HandGestureState
  drawing/
    canvas.py            # Pixel buffer, blend, clear
    stroke.py            # Per-hand freehand continuity
    shapes.py            # Shape commit + preview geometry
    tools.py             # ToolMode Enum, shortcuts
  ui/
    overlay_renderer.py  # Orchestrates components
    components.py        # TopBar, LeftPanel, HelpBar, indicators
    theme.py             # Colors, spacing, fonts
  utils/
    display.py           # Monitor, window, aspect ratio
    geometry.py          # Point, distance, hit tests
    logger.py            # Structured logging
  config/
    settings.py          # Paths, defaults, feature flags (no tkinter at import)
```

---

## Data Flow Issues (Current)

### Letterbox coordinate problem
Hand landmarks are computed on the **letterboxed frame** (including black bars). Fingertip at video edge ≠ drawable edge. Architecture should either:
- Crop to content region and map coordinates, or
- Document content rect and clamp drawing to it

### Fullscreen resize data loss
`Canvas.resize()` allocates new buffer — architectural bug in lifecycle. `FrameProcessor` should scale existing canvas or decouple canvas resolution from display resolution.

### Tool vs gesture eraser
Two concepts:
- **Gesture eraser:** open palm → `erase_at`
- **Tool eraser (spec):** `e` key → tool mode

Need unified policy in `DrawingController`.

---

## Configuration Architecture

**Current:** Monolithic `settings.py` with runtime probe at import.

**Target:**
```python
# settings.py — static defaults only
# runtime_config.py or AppState — dynamic width/height, brush
# theme.py — visual tokens
```

Avoid tkinter in `settings` import path; lazy-call `get_primary_monitor_size()` inside `Application.__init__`.

---

## Testing Architecture (Missing)

```
tests/
  test_gesture_detector.py
  test_stroke_isolation.py
  test_aspect_ratio.py
  test_shape_commit.py
  smoke_test_main.py
```

No test folder exists today.

---

## Architecture Strengths (Keep)

- Per-hand stroke dictionaries in `Canvas` — correct direction
- MediaPipe Tasks API wrapper isolated in `hand_tracker`
- Aspect-ratio helper in `display.py`
- Dataclass usage started (`TrackedHand`, `HandGestureState`, `HandDrawingState`)
- Separation of camera vs tracking vs gestures (loose but present)

---

## Architecture Debt Summary

| Debt | Effort to fix |
|------|---------------|
| Extract Application class | Medium |
| Split Canvas / UI | Medium |
| Enum migration | Low |
| Theme + components | High (UI) |
| FrameProcessor + content rect | Medium |
| Canvas preserve on resize | Low |
| Logger + error UX | Low |
