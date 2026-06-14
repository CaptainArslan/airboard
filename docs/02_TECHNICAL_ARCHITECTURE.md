# Technical Architecture — AirBoard Local MVP

## System Overview

AirBoard Local MVP is a single-process desktop application built in Python. It captures webcam frames, runs hand landmark detection via MediaPipe, interprets gestures, maintains a transparent drawing canvas, composites layers, and displays the result in an OpenCV window. There is no server, database, or external API.

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                              │
│              (orchestration + event loop)                   │
└──────────┬──────────┬──────────┬──────────┬─────────────────┘
           │          │          │          │
     ┌─────▼────┐ ┌───▼───┐ ┌────▼────┐ ┌───▼───┐ ┌──────▼─────┐
     │  Camera  │ │ Track │ │ Gesture │ │ Canvas│ │  Overlay   │
     │  Manager │ │  Hand │ │ Detector│ │       │ │   (UI)     │
     └─────┬────┘ └───┬───┘ └────┬────┘ └───┬───┘ └──────┬─────┘
           │          │          │          │            │
           └──────────┴──────────┴──────────┴────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  config/settings  │
                    └───────────────────┘
```

## Application Flow

1. **Initialize** — Load settings; open webcam; create MediaPipe Hands, canvas, gesture detector, overlay.
2. **Capture** — Read BGR frame from camera; flip horizontally.
3. **Track** — Convert to RGB; run MediaPipe; extract landmarks if present.
4. **Detect gesture** — Classify finger states → mode: `draw`, `pointer`, `fist`, or `idle`.
5. **Update canvas** — If draw mode and fingertip moved, line from previous to current point. If fist held ≥ 1 s, clear. If pointer over color swatch, update color.
6. **Composite** — Blend canvas onto camera frame; draw UI toolbar, mode text, pointer circle, optional skeleton.
7. **Display** — `cv2.imshow`; check `q` key; repeat until exit.
8. **Cleanup** — Release camera; close MediaPipe; destroy windows.

## Module Responsibilities

| Module | File | Responsibility |
|--------|------|----------------|
| Config | `src/config/settings.py` | Constants: resolution, colors, thresholds, window name |
| Camera | `src/camera/camera_manager.py` | Webcam lifecycle, frame read, mirror |
| Tracking | `src/tracking/hand_tracker.py` | MediaPipe init/process, landmark access, skeleton draw |
| Gestures | `src/gestures/gesture_detector.py` | Finger up/down, mode classification, fist timer |
| Drawing | `src/drawing/canvas.py` | Transparent layer, lines, clear, color, brush |
| UI | `src/ui/overlay.py` | Toolbar, swatches, mode label, fingertip pointer |
| Entry | `main.py` | Wire modules; main loop; keyboard exit |

## Camera Layer

- Uses `cv2.VideoCapture(CAMERA_INDEX)`.
- Sets width/height from settings when supported.
- Each frame: `read()` → `flip(frame, 1)` for mirror effect.
- On shutdown: `release()`.

## Hand Tracking Layer

- MediaPipe **HandLandmarker** (Tasks API) with VIDEO mode, `num_hands=1`.
- Requires `models/hand_landmarker.task` model file (see README).
- Input: RGB numpy array via `mp.Image`; output: normalized landmark list (21 points per hand).
- Provides pixel coordinates: `(int(lm.x * w), int(lm.y * h))`.
- Optional debug: draw `HAND_CONNECTIONS` on composite frame.

## Gesture Detection Layer

- **Finger state**: Compare fingertip vs PIP joint (y-axis for index/middle/ring/pinky; x-axis for thumb based on handedness).
- **Draw**: index up, others down.
- **Pointer**: index + middle up, ring + pinky down.
- **Fist**: all fingers down (including thumb).
- **Clear**: fist state maintained for `FIST_HOLD_SECONDS` (1.0 s).
- Returns enum/string mode + raw finger booleans for UI.

## Drawing Canvas Layer

- Separate `numpy` array same size as frame (BGR, uint8), initially zeros.
- Lines drawn with `cv2.line` using selected color and brush thickness.
- Alpha blend onto camera: `cv2.addWeighted`.
- `reset_previous_point()` when switching modes or after clear to prevent stray connectors.
- Exponential moving average on fingertip for smoothing before drawing.

## UI Overlay Layer

- Top horizontal toolbar (semi-opaque bar).
- Color swatches as rectangles; hit-test using fingertip pixel bounds.
- Text: current mode (`DRAW`, `POINTER`, `IDLE`, `CLEARING...`).
- Fingertip circle (hollow or filled) at smoothed position.
- Fist hold progress indicator (optional bar) during clear countdown.

## Main Event Loop

```python
while running:
    frame = camera.read()
    landmarks = tracker.process(frame)
    mode, fingertip = gesture_detector.update(landmarks, frame.shape)
    if mode == DRAW and fingertip:
        canvas.draw_line(fingertip)
    elif mode == POINTER and fingertip:
        canvas.reset_previous_point()
    if gesture_detector.should_clear():
        canvas.clear()
    overlay.draw_toolbar(frame)
    overlay.draw_pointer(frame, fingertip)
    composite = canvas.blend(frame)
    cv2.imshow(WINDOW_NAME, composite)
    if key == ord('q'): break
cleanup()
```

## Data Flow (Text Diagram)

```
Webcam BGR Frame
       │
       ▼
  [Flip Horizontal]
       │
       ├──────────────────────────────────┐
       ▼                                  ▼
  RGB for MediaPipe                  Original BGR
       │                                  │
       ▼                                  │
  Hand Landmarks (21 pts)                 │
       │                                  │
       ▼                                  │
  Gesture Detector ──► Mode + Fingertip   │
       │                    │             │
       │                    ▼             │
       │              Canvas (draw/clear)  │
       │                    │             │
       └────────────────────┼─────────────┘
                            ▼
                    Blend Canvas + Frame
                            │
                            ▼
                    UI Overlay (toolbar, pointer)
                            │
                            ▼
                    cv2.imshow → Display
```

## Folder Structure

```
airboard-local/
  main.py                 # Entry point, event loop
  requirements.txt        # Python dependencies
  README.md               # Setup and usage
  docs/                   # Planning documents
  src/
    __init__.py
    config/
      __init__.py
      settings.py         # All tunable constants
    camera/
      __init__.py
      camera_manager.py
    tracking/
      __init__.py
      hand_tracker.py
    gestures/
      __init__.py
      gesture_detector.py
    drawing/
      __init__.py
      canvas.py
    ui/
      __init__.py
      overlay.py
```

## Dependency Explanation

| Package | Role |
|---------|------|
| **opencv-python** | Webcam capture, image ops, line drawing, window display, alpha blending |
| **mediapipe** | Real-time hand landmark detection (21 3D points per hand) |
| **numpy** | Canvas buffer, coordinate math, array operations |

No additional GUI framework is required; OpenCV's highgui provides the display window and keyboard polling.
