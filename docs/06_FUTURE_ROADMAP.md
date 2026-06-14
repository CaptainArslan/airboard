# Future Roadmap — AirBoard

Features intentionally excluded from the local MVP, ordered roughly by suggested implementation priority.

---

## Phase 1: Output Integration

### Google Meet Virtual Camera Integration

- Pipe composited feed (camera + canvas) into a virtual camera device
- Allow AirBoard overlay during Google Meet video calls
- Requires platform-specific virtual cam driver or browser extension bridge

### OBS Virtual Camera Support

- Output same composited stream compatible with OBS Virtual Camera
- Document workflow: AirBoard → OBS → Meet/Zoom/Teams

### pyvirtualcam Support

- Use [`pyvirtualcam`](https://github.com/letmaik/pyvirtualcam) for cross-platform virtual camera on Windows/macOS
- Abstract output layer behind `VirtualCamOutput` module
- Configurable resolution and FPS matching meeting apps

---

## Phase 2: Drawing Enhancements

### Undo / Redo

- Stroke-based history stack
- Gesture or keyboard shortcuts for undo/redo
- Memory cap for long sessions

### Save Screenshot

- Capture current composite frame to PNG
- Keyboard shortcut (e.g., `s`) or gesture

### Export Drawing

- Export canvas layer only (transparent PNG)
- Optional SVG export for vector strokes

### Shape Recognition

- Detect closed loops → render as clean circles/rectangles
- Snap-to-shape after draw completion

---

## Phase 3: Intelligence and Productivity

### Handwriting-to-Text

- OCR on canvas strokes (Tesseract or cloud API)
- Insert recognized text as overlay labels

### AI Diagram Conversion

- Send sketch to vision LLM → structured diagram (flowchart, architecture)
- Replace rough strokes with polished shapes

### Presentation Mode

- Full-screen canvas without camera feed
- Laser-pointer-only mode
- Slide advance via gestures

---

## Phase 4: Platform and Quality

| Item | Description |
|------|-------------|
| Multi-hand support | Second hand for eraser or UI |
| Eraser gesture | Open palm or pinch to erase locally |
| Brush size gesture | Pinch distance controls thickness |
| Settings UI | On-screen panel for thresholds and colors |
| Performance mode | Lower resolution processing, higher display FPS |
| macOS / Linux QA | Formal support matrix and CI |
| Installer | PyInstaller or similar single-file distribution |
| Config file | YAML/JSON user preferences |

---

## Non-Goals (for foreseeable future)

- User accounts and cloud sync
- Real-time collaboration
- Mobile app
- Depth camera requirement (Kinect, LiDAR)

---

## Success Metrics for Future Phases

| Phase | Metric |
|-------|--------|
| Virtual cam | Meet participants see annotations live |
| Undo/redo | Users recover from mistakes without clearing |
| Export | Users save and share sketches outside app |
| AI features | Rough sketch → usable diagram in < 10 s |
