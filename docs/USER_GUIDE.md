# AirBoard User Guide

## Run the App

```powershell
cd airboard-local
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Download `hand_landmarker.task` into `models/` (see README).

## Layout

- **Top toolbar** — current tool, color, brush, hand status, help, fullscreen
- **Left sidebar** — tools, colors, brush size
- **Center** — webcam + drawing overlay (aspect ratio preserved)
- **Right sidebar** — hand status cards, keyboard shortcuts
- **Bottom bar** — gesture hints

## Gestures

| Gesture | Action |
|---------|--------|
| Index finger extended | Draw with selected tool |
| Index + middle extended | Pointer (no draw) |
| Open palm | Eraser — removes whole objects under palm |

## Tools

| Key | Tool |
|-----|------|
| 1 | Freehand |
| 2 | Line |
| 3 | Rectangle |
| 4 | Circle |
| 5 | Arrow |
| T | Text (type, Enter to commit) |
| E | Eraser (gesture mode) |
| X | Clear canvas |

Shapes: start with index finger, move to preview, release gesture to commit.

## Text Tool

1. Press **T** or select Text in the sidebar
2. Type in the input bar
3. **Enter** — places text at hand pointer (or canvas center)
4. **Esc** — cancel

## Save

Press **S** to export PNG to `exports/airboard_YYYYMMDD_HHMMSS.png` (camera + drawing).

## Undo / Redo

- **Z** or **Ctrl+Z** — undo
- **Y** or **Ctrl+Y** — redo

Clear is undoable.

## Window

- **F** — fullscreen
- **H** — help
- **Q** / **Esc** — quit
