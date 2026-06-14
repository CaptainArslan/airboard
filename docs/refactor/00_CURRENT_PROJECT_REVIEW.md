# AirBoard — Current Project Review

**Date:** 2026-06-14  
**Purpose:** Baseline assessment before professional foundation refactor (pre–Google Meet)

---

## 1. Current Folder Structure

```
airboard-local/
├── main.py                    → Qt entry (qt_application)
├── requirements.txt           → opencv, mediapipe, numpy, PySide6
├── assets/fonts/              → Poppins TTF files
├── docs/                      → PRD, architecture, design, reviews
├── models/                    → hand_landmarker.task (runtime, not committed)
└── src/
    ├── app/
    │   ├── application.py     → Legacy OpenCV loop (unused)
    │   ├── qt_application.py  → Active PySide6 shell
    │   ├── frame_processor.py → Active camera/track/draw pipeline
    │   └── app_state.py       → Legacy OpenCV state dataclass
    ├── camera/camera_manager.py
    ├── config/settings.py
    ├── drawing/
    │   ├── canvas.py          → Pixel raster buffer (cv2 primitives)
    │   ├── hand_manager.py    → Per-hand draw/erase/shape orchestration
    │   └── tools.py           → Tool constants + key map
    ├── gestures/gesture_detector.py
    ├── tracking/hand_tracker.py
    ├── ui/                    → Legacy OpenCV UI (unused)
    │   ├── components.py, layout.py, overlay_renderer.py, theme.py
    │   └── qt/                → Active PySide6 UI (v3)
    └── utils/display.py
```

**Missing for target architecture:** `drawing_objects/`, `ui_qt/` (canonical layout), `exports/`, unified `app_state`/`hand_state`, undo/redo, text tool, PNG export.

---

## 2. Current Main App Flow

```
main.py
  └── QtApplication (src/app/qt_application.py)
        ├── QApplication + Poppins + styles.qss
        ├── MainWindow (src/ui/qt/main_window.py)
        ├── FrameProcessor (src/app/frame_processor.py)
        └── QTimer ~30 FPS
              └── process(avail_w, avail_h)
                    ├── CameraManager.read_raw()
                    ├── letterbox resize
                    ├── HandTracker.process()
                    ├── GestureDetector.classify_hands()
                    ├── HandDrawingManager.update() → mutates pixel Canvas
                    ├── blend + shape previews + indicators
                    └── MainWindow.bind_state() → WebcamPanel QPixmap
```

Keyboard/mouse: Qt signals and `QShortcut` → `HandDrawingManager` tool/color/brush. Gestures drive drawing only through `FrameProcessor`.

---

## 3. Current UI Problems

| Issue | Status |
|-------|--------|
| OpenCV demo aesthetic | **Mostly fixed** in PySide6 v3 — dark theme, Poppins, cards |
| Layout breaks on resize | **Fixed** via Qt layouts + `LayoutMetrics` |
| Webcam stretch | **Fixed** — contain mode letterbox |
| UI split across `ui/` and `ui/qt/` | **Problem** — duplicate dead OpenCV code, non-standard paths |
| No Text tool in sidebar | **Missing** |
| No undo/redo UI hints | **Missing** |
| Toolbar not split into modules | **Minor** — monolithic `main_window.py` |

---

## 4. Current Drawing / Canvas Problems

| Issue | Detail |
|-------|--------|
| **Pixel-based only** | All strokes committed to `numpy` buffer via `cv2.line/circle/...` |
| **No object model** | Cannot select, undo individual strokes, or export vector data |
| **No undo/redo** | Clear is destructive with no history |
| **Eraser is pixel paint** | Paints black circles — not object removal |
| **Resize blurs art** | `cv2.resize` on pixel buffer when window changes |
| **Preview vs commit** | Shapes preview on display frame; commit on gesture exit — **good pattern to keep** |
| **Per-hand state** | `HandDrawingState` per Left/Right — **good pattern to keep** |

---

## 5. Current Gesture Problems

| Issue | Detail |
|-------|--------|
| String modes (`"draw"`, `"eraser"`) | Works but not typed — needs `GestureType`/`HandMode` enums |
| `gesture_detector.py` formatting | Excessive blank lines; otherwise logic is sound |
| FIST → IDLE mapping | Correct for UI display |
| Two-hand independence | **Working** — separate `HandDrawingState` per label |
| No text-placement gesture | Text tool will use keyboard + pointer position |

**Preserve:** DRAW (index), POINTER (index+middle), ERASER (open palm), smoothing EMA.

---

## 6. Current Architecture Problems

| Issue | Detail |
|-------|--------|
| Dual UI stacks | OpenCV path dead but still in repo |
| Dual theme files | `ui/theme.py` vs `ui/qt/theme.py` |
| `main.py` imports `qt_application` not `application` | Spec wants `AirBoardApplication` |
| `app_state.py` tied to OpenCV path only | Needs unified state for Qt + engine |
| `FrameProcessor` imports from `ui.qt.theme` | Engine should not depend on UI package |
| No export directory or save pipeline | Missing |
| Docs lag code | README/architecture describe v1 OpenCV |

---

## 7. What Must Be Preserved

- **Camera:** `CameraManager` — capture, flip, release
- **Tracking:** `HandTracker` — MediaPipe HandLandmarker Tasks API
- **Gestures:** Classification logic (draw/pointer/eraser/idle)
- **Two-hand drawing:** Independent per-hand state
- **Shape preview → commit on gesture end:** UX pattern
- **PySide6 v3 visual design:** Dark theme, Poppins, 4-zone layout, contain-mode video
- **Keyboard shortcuts:** 1–5 tools, E eraser, X clear, +/- brush, F/H/Q
- **Tool constants:** `src/drawing/tools.py` (extend with TEXT)

---

## 8. What Must Be Replaced

| Remove / Replace | With |
|------------------|------|
| `src/drawing/canvas.py` (pixel buffer) | `src/drawing_objects/canvas_model.py` + `renderer.py` |
| `HandDrawingManager` canvas mutations | Object add/remove via `CanvasModel` |
| Pixel eraser | Object hit-test eraser (bbox overlap) |
| `src/ui/` OpenCV files | Delete after migration |
| `src/ui/qt/` layout | `src/ui_qt/` modular package |
| `src/app/qt_application.py` as entry | `src/app/application.py` → `AirBoardApplication` |
| Legacy `app_state.py` | New enums + `AppState` + `HandState` |
| `FrameProcessor` → `ui.qt.theme` import | Use `config/settings` colors only |

---

## 9. Refactor Order (Approved)

1. ✅ This review document  
2. App state models (`ToolMode`, `HandMode`, `GestureType`, dataclasses)  
3. Object-based canvas (`drawing_objects/`)  
4. PySide6 shell (`ui_qt/`)  
5. Connect engine to object canvas  
6. Restore freehand + two-hand + shapes  
7. Undo/redo (Ctrl+Z/Y, Z/Y)  
8. Text tool (T + keyboard input)  
9. Save PNG (S → `exports/`)  
10. Polish UI + update docs  

---

## 10. Acceptance Gap Summary

| Criterion | Current | Target |
|-----------|---------|--------|
| PySide6 professional UI | ✅ Mostly | Modular `ui_qt/` |
| Object canvas | ❌ | ✅ |
| Undo/redo | ❌ | ✅ |
| Text tool | ❌ | ✅ |
| Save PNG | ❌ | ✅ |
| Clean main.py | ⚠️ | `AirBoardApplication` |
| Modular code | ⚠️ | Split UI modules |
