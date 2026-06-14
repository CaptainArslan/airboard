"""Design tokens and font loading for Qt UI."""

from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"

# Hex colors for QSS and programmatic use
COLORS = {
    "bg_app": "#0B1220",
    "bg_panel": "#111827",
    "border": "#1F2937",
    "text_primary": "#F9FAFB",
    "text_secondary": "#9CA3AF",
    "accent": "#2563EB",
    "accent_soft": "#1E3A5F",
    "success": "#22C55E",
    "danger": "#EF4444",
    "warning": "#F59E0B",
    "keycap_bg": "#374151",
}

COLOR_NAMES = ("Blue", "Red", "Green", "Yellow", "Magenta", "White")

# BGR for drawing engine
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
    """Register Poppins TTF files; return family name."""
    global _fonts_loaded
    family = "Poppins"
    if _fonts_loaded:
        return family

    font_files = [
        "Poppins-Regular.ttf",
        "Poppins-Medium.ttf",
        "Poppins-SemiBold.ttf",
    ]
    for name in font_files:
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
    path = Path(__file__).parent / "styles.qss"
    return path.read_text(encoding="utf-8")
