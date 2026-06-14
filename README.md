# AirBoard Local MVP

A local webcam-based air whiteboard. Draw in the air using your index finger—the app tracks your hand with MediaPipe and renders strokes on a transparent overlay above the live camera feed.

## Requirements

- Python 3.10+
- Webcam
- Windows, macOS, or Linux

## Installation

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

Download the MediaPipe hand landmarker model (required once):

```bash
mkdir models
curl -L -o models/hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

On Windows PowerShell:

```powershell
mkdir models -Force
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -OutFile "models\hand_landmarker.task"
```

## Run

```bash
python main.py
```

Press **`q`** to exit.

## Gestures

| Gesture | Action |
|---------|--------|
| Index finger up only | Draw |
| Index + middle fingers up | Move pointer without drawing |
| Closed fist held ~1 second | Clear canvas |
| Hover index fingertip over color swatch | Select color |

## Project Structure

```
airboard-local/
  main.py              # Application entry point
  requirements.txt
  docs/                # Planning documents (PRD, architecture, etc.)
  src/
    camera/            # Webcam capture
    tracking/          # MediaPipe hand tracking
    gestures/          # Gesture classification
    drawing/           # Canvas and strokes
    ui/                # Toolbar and pointer overlay
    config/            # Settings and constants
```

## Configuration

Edit `src/config/settings.py` to adjust camera index, resolution, brush size, gesture thresholds, and colors.

## Documentation

See the `docs/` folder for full product and technical planning:

- `01_PRD.md` — Product requirements
- `02_TECHNICAL_ARCHITECTURE.md` — System design
- `03_DEVELOPMENT_PLAN.md` — Milestones
- `04_GESTURE_LOGIC.md` — Gesture detection details
- `05_TESTING_CHECKLIST.md` — Manual test checklist
- `06_FUTURE_ROADMAP.md` — Planned future features

## License

MIT (or your chosen license)
