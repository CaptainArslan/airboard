# Design System — AirBoard

**Version:** 1.0  
**Date:** 2026-06-14  
**Platform:** OpenCV-rendered local desktop overlay

---

## Brand

| Token | Value |
|-------|-------|
| App name | **AirBoard** |
| Window title | `AirBoard` |
| Tagline (help only) | Draw in the air. |
| Tone | Clean, dark, professional, minimal |

---

## Color Palette

All colors BGR (OpenCV). Define in `src/ui/theme.py`.

### Core

| Token | BGR | Usage |
|-------|-----|-------|
| `COLOR_BG_PANEL` | `(30, 30, 30)` | Solid panel base |
| `COLOR_BG_PANEL_ALPHA` | 0.75 | Translucent panel overlay |
| `COLOR_BG_VIDEO_LETTERBOX` | `(0, 0, 0)` | Letterbox bars |
| `COLOR_TEXT_PRIMARY` | `(255, 255, 255)` | Main labels |
| `COLOR_TEXT_SECONDARY` | `(180, 180, 180)` | Hints, shortcuts |
| `COLOR_TEXT_MUTED` | `(120, 120, 120)` | Disabled items |
| `COLOR_ACCENT` | `(255, 140, 0)` | Active tool, focus ring (orange) |
| `COLOR_BORDER` | `(70, 70, 70)` | Panel edges |

### Drawing palette (user-facing)

| Name | BGR | Label |
|------|-----|-------|
| Red | `(0, 0, 255)` | Red |
| Green | `(0, 255, 0)` | Green |
| Blue | `(255, 0, 0)` | Blue |
| Yellow | `(0, 255, 255)` | Yellow |
| Magenta | `(255, 0, 255)` | Magenta |
| White | `(255, 255, 255)` | White |

### Semantic

| Token | BGR | Usage |
|-------|-----|-------|
| `COLOR_POINTER` | `(255, 255, 255)` | Pointer mode ring |
| `COLOR_ERASER` | `(0, 0, 220)` | Eraser fill (red) |
| `COLOR_ERASER_ALPHA` | 0.40 | Semi-transparent duster |
| `COLOR_PREVIEW` | `(255, 200, 100)` | Shape preview (light accent) |
| `COLOR_DRAW_CURSOR` | *matches active color* | Draw fingertip |

### Status badges

| Mode | Background | Text |
|------|------------|------|
| Draw | `(0, 120, 0)` dark green tint | `DRAW` |
| Pointer | `(120, 120, 120)` | `POINTER` |
| Eraser | `(0, 0, 160)` red tint | `ERASE` |
| Idle | `(60, 60, 60)` | `IDLE` |

---

## Typography

OpenCV `FONT_HERSHEY_SIMPLEX` only (no custom fonts in v1).

| Role | Scale formula | Weight |
|------|---------------|--------|
| Title (`AirBoard`) | `frame_min * 0.0012` | thickness 2 |
| Body (toolbar items) | `frame_min * 0.0009` | thickness 1 |
| Caption (help bar) | `frame_min * 0.00075` | thickness 1 |
| Badge | `frame_min * 0.0007` | thickness 1 |

`frame_min = min(width, height)` — recalculate each frame.

**Rules:**
- Max 2 font sizes on screen at once (title + body)
- Help overlay may use caption size only
- No ALL CAPS except badge labels (DRAW, IDLE)

---

## Spacing & Layout

All spacing as **ratios of frame dimensions**.

| Token | Ratio | Axis |
|-------|-------|------|
| `SPACE_XS` | 0.006 | min |
| `SPACE_SM` | 0.012 | min |
| `SPACE_MD` | 0.020 | min |
| `SPACE_LG` | 0.030 | min |

### Screen regions

```
┌──────────────────────────────────────────────────────────┐
│ TOP BAR (height: 8% of frame)                            │
├───┬──────────────────────────────────────────────────────┤
│ L │                                                      │
│ E │              VIDEO + DRAWING LAYER                   │
│ F │                                                      │
│ T │                                                      │
│   │                                                      │
│ P │                                                      │
│ A │                                                      │
│ N │                                                      │
│ E │                                                      │
│   │                                                      │
│(12%│                                                     │
│ w) │                                                     │
├───┴──────────────────────────────────────────────────────┤
│ BOTTOM HELP BAR (height: 5% of frame)                    │
└──────────────────────────────────────────────────────────┘
```

---

## Top Toolbar

**Height:** 8% of frame height  
**Style:** Dark translucent strip (`COLOR_BG_PANEL` @ 75% alpha)

**Content (single row, left → right):**

```
AirBoard  |  Tool: Freehand  |  Color: Blue  |  Brush: 6  |  L: Draw  |  R: Idle  |  [H Help]
```

| Element | Behavior |
|---------|----------|
| App name | Bold white, fixed left padding |
| Tool | Shows `ToolMode` label |
| Color | Swatch + name |
| Brush | Numeric size |
| L / R badges | Hand status pills |
| Help | `[H Help]` hint — opens overlay |

**Separator:** ` | ` in muted gray between groups.

---

## Left Tool Panel

**Width:** 12% of frame width  
**Position:** Below top bar, flush left  
**Style:** Same translucent panel as top bar

### Tools (vertical list)

| Icon | Label | Key |
|------|-------|-----|
| `[~]` or `Free` | Freehand | `1` |
| `/` | Line | `2` |
| `[ ]` | Rectangle | `3` |
| `O` | Circle | `4` |
| `->` | Arrow | `5` |
| `[=]` | Eraser tool | `e` |
| `X` | Clear | `x` |

Use plain ASCII if Unicode fails on platform:

```
Freehand
Line
Rectangle
Circle
Arrow
Eraser
Clear
```

### Tool button states

| State | Visual |
|-------|--------|
| Default | Muted text, no border |
| Hover | Light border (future — N/A for air UI) |
| **Active** | Orange left bar 4px + white text + subtle highlight fill |
| Disabled | Muted gray |

---

## Color Palette (in top bar or left panel footer)

- Swatches in horizontal row
- Size: 3.5% of frame width (square)
- Gap: `SPACE_SM`
- Active color: white 2px outer ring + orange inner ring
- Hover select: finger dwell 3 frames (unchanged logic)

---

## Bottom Help Bar

**Height:** 5% of frame  
**Style:** Darker strip, caption typography

**Default text:**
```
q/Esc Quit  |  f Fullscreen  |  h Help  |  1 Freehand  2 Line  3 Rect  4 Circle  5 Arrow  |  e Eraser  x Clear  |  +/- Brush
```

**Rules:**
- Always visible when `show_help_bar = True`
- Centered or left-aligned with padding `SPACE_MD`
- Hide when full help overlay open (optional)

---

## Help Overlay

**Trigger:** `h` toggle  
**Style:** Full-frame semi-transparent scrim `(0,0,0)` @ 60% alpha

**Content card:** Centered panel 50% × 60% frame

```
AirBoard — Keyboard Shortcuts

Window
  q / Esc     Quit
  f           Toggle fullscreen

Tools
  1           Freehand
  2           Line
  ...

Gestures
  Index finger        Draw
  Index + middle      Pointer
  Open palm           Eraser (duster)

Press H to close
```

---

## Gesture Indicators

### Draw mode
- Filled circle at index tip
- Radius: 0.8% of frame min
- Color: active drawing color
- Optional 1px white outline for contrast

### Pointer mode
- Hollow white circle, 0.8% radius
- 2px stroke
- Small center dot (2px)

### Eraser mode (open palm)
- Circle centered on palm (landmarks 0,5,9,13,17 avg)
- Radius: `ERASER_RADIUS` (scaled to frame)
- Fill: `COLOR_ERASER` @ 40% alpha
- Outer ring: 2px solid red @ 80% alpha
- **Not** lavender (current prototype color)

### Shape preview
- Color: `COLOR_PREVIEW`
- Style: dashed if feasible; else 2px solid + 30% thicker ghost outline
- Never written to permanent canvas until commit

---

## Fullscreen / Window Controls

| State | Indicator |
|-------|-----------|
| Windowed | No badge (default) |
| Fullscreen | Small top-right badge: `FULLSCREEN` muted, or `f to exit` in help bar |

**Behavior:**
- Start windowed 1280×720
- Never auto-fullscreen
- Esc always quits (not exit fullscreen only — per spec)

---

## Component API Sketch

```python
# components.py
def draw_top_bar(frame, app_state, theme) -> None
def draw_left_panel(frame, app_state, theme) -> None
def draw_bottom_help(frame, app_state, theme) -> None
def draw_help_overlay(frame, theme) -> None
def draw_hand_indicator(frame, hand_state, theme) -> None
def draw_color_swatch_row(frame, rect, ...) -> None
```

```python
# theme.py
@dataclass(frozen=True)
class Theme:
    colors: ColorTokens
    spacing: SpacingTokens
    fonts: FontTokens

    @classmethod
    def for_frame(cls, width: int, height: int) -> Theme: ...
```

---

## Accessibility & UX Notes

- High contrast text on dark panels
- Minimum touch target for color swatches: 32px at 720p (scale up)
- Do not rely on color alone for active tool — use border + label
- Keep video unobstructed — panels occupy ≤ 20% combined width/height

---

## Out of Scope (v1 Design)

- Custom icons / PNG assets
- Animations / transitions
- Light theme
- Google Meet / virtual camera chrome

---

## Visual Reference (ASCII)

```
┌─ AirBoard ──────────────────────────────────────────────────────────────┐
│ AirBoard | Tool: Line | Color: Blue | Brush: 6 | L:DRAW R:IDLE | H    │
├──┬────────────────────────────────────────────────────────────────────┤
│ >│                                                                    │
│Fr│                     [ webcam + drawings ]                          │
│Li│                                                                    │
│Re│                              (o) ← draw cursor                     │
│Ct│                                                                    │
│..│                                                                    │
├──┴────────────────────────────────────────────────────────────────────┤
│ q Quit | f Fullscreen | h Help | 1-5 Tools | e Erase | x Clear | +/-  │
└───────────────────────────────────────────────────────────────────────┘
```

Active tool `Line` shows orange bar on left panel row `> Line`.
