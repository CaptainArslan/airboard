# AirBoard Architecture

## Overview

AirBoard is a local desktop app: webcam + MediaPipe hand tracking + air drawing. The UI is PySide6; the engine is OpenCV + MediaPipe + an object-based canvas.

```
main.py
  └── AirBoardApplication (src/app/application.py)
        ├── MainWindow (src/ui_qt/)
        ├── FrameProcessor (src/app/frame_processor.py)
        └── QTimer ~30 FPS
```

## Layers

| Layer | Responsibility |
|-------|----------------|
| `ui_qt/` | Window, layout, toolbar, sidebars, theme, shortcuts |
| `app/` | Application shell, `AppState`, frame loop |
| `camera/` | Webcam capture |
| `tracking/` | MediaPipe HandLandmarker |
| `gestures/` | Finger pose → draw / pointer / eraser |
| `drawing/` | `HandDrawingManager` — per-hand tool logic |
| `drawing_objects/` | Object model, render, undo/redo, export |

## Object Canvas

Drawings are stored as objects (`Stroke`, `Line`, `Rectangle`, `Circle`, `Arrow`, `Text`) in `CanvasModel`. Each frame:

1. Render all objects to a transparent layer
2. Alpha-blend onto the letterboxed camera frame
3. Draw ephemeral shape previews and gesture indicators

Undo/redo uses snapshot history on `CanvasModel`.

## Data Flow

```
Camera → letterbox → HandTracker → GestureDetector → HandDrawingManager → CanvasModel
                                                                              ↓
MainWindow ← bind_state ← FrameResult ← blend + previews + indicators ← render
```

## Key Files

- `src/app/application.py` — entry orchestration
- `src/app/frame_processor.py` — per-frame pipeline
- `src/drawing_objects/canvas_model.py` — objects + history
- `src/drawing/hand_manager.py` — two-hand draw/erase/shape logic
- `src/ui_qt/main_window.py` — 4-zone responsive layout

## Not Included (Yet)

- Google Meet / virtual camera
- Cloud sync
- Pixel-perfect partial eraser
