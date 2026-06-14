"""AirBoard design tokens — colors, typography, spacing."""

from dataclasses import dataclass


def hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (b, g, r)


@dataclass(frozen=True)
class ColorTokens:
    bg_app: tuple[int, int, int] = hex_to_bgr("#0B1220")
    bg_panel: tuple[int, int, int] = hex_to_bgr("#111827")
    border: tuple[int, int, int] = hex_to_bgr("#1F2937")
    text_primary: tuple[int, int, int] = hex_to_bgr("#F9FAFB")
    text_secondary: tuple[int, int, int] = hex_to_bgr("#9CA3AF")
    accent: tuple[int, int, int] = hex_to_bgr("#2563EB")
    accent_soft: tuple[int, int, int] = hex_to_bgr("#1E3A5F")
    success: tuple[int, int, int] = hex_to_bgr("#22C55E")
    warning: tuple[int, int, int] = hex_to_bgr("#F59E0B")
    danger: tuple[int, int, int] = hex_to_bgr("#EF4444")
    danger_soft: tuple[int, int, int] = (68, 68, 239)
    preview: tuple[int, int, int] = hex_to_bgr("#2563EB")
    pointer: tuple[int, int, int] = (255, 255, 255)
    badge_idle_bg: tuple[int, int, int] = hex_to_bgr("#374151")
    content_letterbox: tuple[int, int, int] = hex_to_bgr("#0B1220")


COLOR_NAMES = ("Blue", "Red", "Green", "Yellow", "Magenta", "White")

# Drawing swatches (BGR) — matches settings.COLORS order
DRAWING_SWATCHES: tuple[tuple[int, int, int], ...] = (
    (255, 0, 0),    # Blue
    (0, 0, 255),    # Red
    (0, 255, 0),    # Green
    (0, 255, 255),  # Yellow
    (255, 0, 255),  # Magenta
    (255, 255, 255),  # White
)


@dataclass
class Theme:
    """Runtime theme scaled to window size."""

    width: int
    height: int
    colors: ColorTokens = ColorTokens()

    @property
    def frame_min(self) -> int:
        return min(self.width, self.height)

    def font_title(self) -> float:
        return max(0.55, 24 / 720 * self.height / 24)

    def font_section(self) -> float:
        return max(0.45, 16 / 720 * self.height / 24)

    def font_label(self) -> float:
        return max(0.4, 14 / 720 * self.height / 24)

    def font_help(self) -> float:
        return max(0.35, 12 / 720 * self.height / 24)

    def thickness_title(self) -> int:
        return 2

    def thickness_body(self) -> int:
        return 1

    def radius_md(self) -> int:
        return max(6, int(self.frame_min * 0.008))

    def pad_sm(self) -> int:
        return max(6, int(self.frame_min * 0.008))

    def pad_md(self) -> int:
        return max(10, int(self.frame_min * 0.014))

    def pad_lg(self) -> int:
        return max(16, int(self.frame_min * 0.022))
