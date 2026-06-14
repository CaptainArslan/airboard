"""Application-wide constants and tunable parameters."""

import os

from src.utils.display import get_primary_monitor_size, scale_from_screen

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HAND_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "hand_landmarker.task")

# Primary monitor (detected at startup)
SCREEN_WIDTH, SCREEN_HEIGHT = get_primary_monitor_size()
_UI_SCALE = min(SCREEN_WIDTH, SCREEN_HEIGHT)

# Camera
CAMERA_INDEX = 0

# Window
WINDOW_NAME = "AirBoard"
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 720
DEFAULT_BRUSH_SIZE = 6

# Eraser (fixed pixel sizes per spec)
DEFAULT_ERASER_SIZE = 30
MIN_ERASER_SIZE = 10
MAX_ERASER_SIZE = 100
ERASER_RADIUS = DEFAULT_ERASER_SIZE  # legacy alias

# MediaPipe Hands
MAX_NUM_HANDS = 2
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.7

# Drawing (scaled to default window)
_BRUSH_BASE = scale_from_screen(0.005, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
BRUSH_THICKNESS = _BRUSH_BASE
CANVAS_ALPHA = 0.85
SMOOTHING_ALPHA = 0.4
MIN_DRAW_DISTANCE = scale_from_screen(0.003, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, axis="min")
PALM_LANDMARKS = (0, 5, 9, 13, 17)
COLOR_HOVER_FRAMES = 3

# BGR drawing palette (index order matches theme.COLOR_NAMES)
COLORS = [
    (255, 0, 0),      # Blue
    (0, 0, 255),      # Red
    (0, 255, 0),      # Green
    (0, 255, 255),    # Yellow
    (255, 0, 255),    # Magenta
    (255, 255, 255),  # White
]

DEFAULT_COLOR_INDEX = 0
DRAW_POINTER_RADIUS = scale_from_screen(0.008, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, axis="min")
POINTER_MODE_RADIUS = DRAW_POINTER_RADIUS
POINTER_MODE_COLOR = (255, 255, 255)
ERASER_VISUAL_RADIUS = DEFAULT_ERASER_SIZE
PREVIEW_COLOR = (235, 99, 37)
HAND_LABELS = ("Left", "Right")

# Debug — off for production UI
DRAW_HAND_SKELETON = False
