# Product Requirements Document — AirBoard Local MVP

## Product Name

**AirBoard Local MVP**

## Product Vision

AirBoard enables users to draw and annotate in the air using only their webcam and hand gestures—no stylus, touch screen, or special hardware required. The local MVP proves the core interaction model: see yourself on camera, point with your index finger, and draw on a transparent overlay as if the screen were a whiteboard floating in front of you.

## Problem Statement

Traditional whiteboard and annotation tools require a mouse, pen, or touch input. In presentations, brainstorming sessions, or quick explanations, users often want to sketch ideas naturally with hand gestures while staying visible on camera. Existing solutions either need expensive hardware (IR pens, depth cameras) or complex setup. AirBoard solves this with a standard webcam and computer vision.

## Target Users

- **Educators and trainers** who want to annotate while on camera
- **Remote workers** doing informal whiteboard-style explanations locally before sharing
- **Developers and makers** prototyping gesture-based interfaces
- **Students and hobbyists** experimenting with computer vision and air-drawing

## MVP Objective

Deliver a single-machine desktop application that opens the webcam, tracks the user's index finger, and allows drawing, pointer movement, canvas clearing, and color selection through hand gestures—all without network connectivity, cloud services, or virtual camera output.

## Included Features

| # | Feature |
|---|---------|
| 1 | Live webcam preview (mirrored for natural interaction) |
| 2 | MediaPipe hand detection with visible skeleton (debug) |
| 3 | Index fingertip pointer overlay |
| 4 | Draw mode: index finger up only |
| 5 | Pointer mode: index + middle fingers up (move without drawing) |
| 6 | Clear canvas: closed fist held for 1 second |
| 7 | Color selector toolbar with hover-to-select |
| 8 | Safe exit via `q` key |
| 9 | Persistent drawing layer until cleared |

## Excluded Features

- Google Meet / Zoom / Teams integration
- Virtual camera output (OBS, pyvirtualcam)
- Cloud sync, login, or accounts
- Database or file persistence (save/export)
- Undo/redo
- Shape recognition or AI features
- Multi-hand support
- Audio or recording

## User Journey

1. User launches `python main.py` from the project directory.
2. Webcam permission is granted (if prompted by OS).
3. User sees live mirrored camera feed with a toolbar at the top.
4. User raises hand into frame; hand skeleton appears.
5. User raises index finger only → enters draw mode; moving finger leaves colored trails.
6. User raises index + middle fingers → pointer moves without drawing (avoids stray marks when repositioning).
7. User hovers index fingertip over a color swatch → brush color changes.
8. User makes a fist and holds ~1 second → canvas clears.
9. User presses `q` → webcam releases, windows close, app exits cleanly.

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-01 | App shall open default webcam (index 0) at configured resolution. |
| FR-02 | App shall mirror frames horizontally for intuitive left/right movement. |
| FR-03 | App shall detect at most one hand per frame using MediaPipe Hands. |
| FR-04 | App shall display hand landmarks when a hand is detected. |
| FR-05 | App shall show a circular pointer at the smoothed index fingertip position. |
| FR-06 | When only index finger is extended, app shall draw continuous lines on the canvas. |
| FR-07 | When index and middle fingers are extended, app shall move pointer without drawing. |
| FR-08 | When fist is held continuously for 1 second, app shall clear all drawings. |
| FR-09 | When fingertip overlaps a toolbar color box, app shall update the active brush color. |
| FR-10 | Pressing `q` shall terminate the main loop and release all resources. |
| FR-11 | Toolbar shall display current mode (Draw / Pointer / Idle) and selected color. |

## Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-01 | Target ≥ 15 FPS on a typical laptop with built-in webcam. |
| NFR-02 | Latency from finger movement to pointer update should feel responsive (< 100 ms perceived). |
| NFR-03 | App shall not require internet after dependencies are installed. |
| NFR-04 | Code shall be modular (camera, tracking, gestures, drawing, UI, config). |
| NFR-05 | App shall handle webcam read failures gracefully (exit loop, release camera). |
| NFR-06 | Gesture false positives (accidental clear) shall be minimized via hold timer and finger-state checks. |

## Success Criteria

- User can draw recognizable shapes (circle, line, letter) in the air.
- Switching from draw to pointer mode does not leave connecting lines between modes.
- Clear gesture works reliably without triggering during normal drawing.
- At least 4 distinct colors are selectable from the toolbar.
- Application runs end-to-end with `python main.py` on Windows with Python 3.10+.

## Definition of Done

The MVP is **done** when all of the following are true:

- [ ] All six planning documents exist in `docs/`.
- [ ] Project structure matches the specified `src/` layout.
- [ ] `python main.py` starts without errors.
- [ ] Webcam opens and displays mirrored feed.
- [ ] Hand skeleton visible when hand is in frame.
- [ ] Fingertip pointer tracks index finger smoothly.
- [ ] Draw, pointer, clear, and color-select gestures work as specified.
- [ ] Pressing `q` closes the app and releases the webcam.
- [ ] Manual testing checklist in `docs/05_TESTING_CHECKLIST.md` passes for core scenarios.
