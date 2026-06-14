"""Design tokens and font loading."""

from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"

COLORS = {
    "bg_app": "#0B1220",
    "bg_panel": "#111827",
    "bg_panel_alt": "#1F2937",
    "border": "#273449",
    "text_primary": "#F9FAFB",
    "text_muted": "#9CA3AF",
    "accent": "#2563EB",
    "success": "#22C55E",
    "danger": "#EF4444",
    "warning": "#F59E0B",
}

COLOR_NAMES = ("Blue", "Red", "Green", "Yellow", "Magenta", "White")

DRAWING_COLORS_BGR = [
    (255, 0, 0),
    (0, 0, 255),
    (0, 255, 0),
    (0, 255, 255),
    (255, 0, 255),
    (255, 255, 255),
]

_fonts_loaded = False


def load_poppins() -> str:
    global _fonts_loaded
    if _fonts_loaded:
        return "Poppins" if "Poppins" in QFontDatabase.families() else "Segoe UI"
    for name in ("Poppins-Regular.ttf", "Poppins-Medium.ttf", "Poppins-SemiBold.ttf"):
        path = FONTS_DIR / name
        if path.is_file():
            QFontDatabase.addApplicationFont(str(path))
    _fonts_loaded = True
    if "Poppins" in QFontDatabase.families():
        return "Poppins"
    return "Segoe UI"


def app_font(size: int, weight: int = QFont.Weight.Normal) -> QFont:
    f = QFont(load_poppins(), size)
    f.setWeight(weight)
    return f


def load_stylesheet() -> str:
    return (Path(__file__).parent / "styles.qss").read_text(encoding="utf-8")
