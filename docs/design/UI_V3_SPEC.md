# AirBoard UI Quality Pass v3 — Specification

**Version:** 3.0  
**Date:** 2026-06-14  
**Status:** Approved for implementation  
**Stack:** PySide6 (UI) + OpenCV (video/drawing) + MediaPipe (tracking)

---

## 1. Goals

| Goal | Metric |
|------|--------|
| Responsive | Window resize never breaks layout or overlaps text |
| Video | Webcam always **contain** mode — never stretch |
| Typography | **Poppins** at defined scale; no OpenCV text |
| Polish | Dashboard quality comparable to OBS / Figma / Miro |
| Scope | UI only — no new product features |

---

## 2. Layout Measurements

### 2.1 Base grid

- **8px base unit** — all spacing multiples of 8
- **Min window:** 1024 × 640  
- **Default window:** 1280 × 720  
- **Max:** unconstrained (responsive)

### 2.2 Region formulas (relative to `window_width`, `window_height`)

| Region | Formula | Clamp |
|--------|---------|-------|
| Top toolbar | `toolbar_h = int(window_height * 0.08)` | 56–72 px |
| Bottom status | `status_h = int(window_height * 0.055)` | 36–44 px |
| Left sidebar | `left_w = int(window_width * 0.18)` | 240–320 px |
| Right sidebar | `right_w = int(window_width * 0.16)` | 220–300 px |
| Content (webcam) | remainder | min 400 px wide |

```python
content_w = window_w - left_w - right_w
content_h = window_h - toolbar_h - status_h
```

### 2.3 Webcam panel (inside content area)

| Token | Value |
|-------|-------|
| Panel padding | 16px (`2 × base`) |
| Panel radius | 12px |
| Panel border | 1px `#1F2937` |
| Shadow blur | 24px, opacity 40% |
| Letterbox color | `#0B1220` |

**Contain algorithm:**

```python
scale = min(avail_w / frame_w, avail_h / frame_h)
display_w = int(frame_w * scale)
display_h = int(frame_h * scale)
# center in avail rect; pad with letterbox color
```

Canvas resolution = **letterboxed pixel size** (not widget size) for accurate hand mapping.

---

## 3. Responsive Rules

1. **Qt layouts only** — `QVBoxLayout`, `QHBoxLayout`, `QGridLayout`, `QScrollArea`. No `move(x,y)` for chrome.
2. **Fixed sidebar widths** computed on `resizeEvent` → set `setFixedWidth(left_w)`.
3. **Toolbar / status bar** — `setFixedHeight()` from formulas.
4. **Webcam** — `QLabel` with `Qt.KeepAspectRatio` + `Qt.SmoothTransformation`.
5. **Sidebars scroll** when content height > available (`QScrollArea`, `widgetResizable=True`).
6. **Font sizes scale** slightly below 720p height (floor at 12px body).
7. **Canvas resize** on content dimension change; scale buffer with `cv2.resize` (preserve drawings).

---

## 4. Typography Scale (Poppins)

| Role | Size | Weight | Qt weight | Usage |
|------|------|--------|-----------|-------|
| App title | 24px | SemiBold | 600 | Logo area |
| Section | 16px | Medium | 500 | TOOLS, COLORS, Hand Status |
| Body / label | 14px | Regular | 400 | Tool names, values |
| Helper | 12px | Regular | 400 | Bottom bar, hints |
| Badge | 13px | Medium | 500 | Status pills |

**Loading:** `assets/fonts/Poppins-*.ttf` via `QFontDatabase.addApplicationFont`.  
**Fallback:** `"Poppins", "Segoe UI", sans-serif`

**Prohibited:** `cv2.putText`, `FONT_HERSHEY_*` for UI chrome.

---

## 5. Spacing System

| Token | px | Use |
|-------|-----|-----|
| `section_gap` | 24 | Section title → first item |
| `item_gap` | 12 | Between tool rows / shortcut rows |
| `card_padding` | 16 | Inside cards |
| `sidebar_padding` | 16 | Sidebar outer padding |
| `divider_margin` | 16 | Above/below horizontal rules |

---

## 6. Theme System

### 6.1 Color tokens

| Token | Hex |
|-------|-----|
| `bg.app` | `#0B1220` |
| `bg.panel` | `#111827` |
| `border.default` | `#1F2937` |
| `text.primary` | `#F9FAFB` |
| `text.secondary` | `#9CA3AF` |
| `accent.primary` | `#2563EB` |
| `accent.soft` | `#1E3A5F` |
| `status.success` | `#22C55E` |
| `status.danger` | `#EF4444` |
| `status.warning` | `#F59E0B` |

### 6.2 Component tokens

| Component | Radius | Border |
|-----------|--------|--------|
| Card | 8px | 1px `#1F2937` |
| Tool button | 8px | 1px transparent → `#1F2937` hover |
| Color chip (selected) | 50% | 2px `#2563EB` + glow |
| Pill badge | 12px | none |
| Keycap | 4px | 1px `#374151` |

---

## 7. Component Library

| Component | File | States |
|-----------|------|--------|
| `ToolButton` | `tool_button.py` | default, hover, selected, pressed |
| `ColorChip` | `color_chip.py` | default, selected (ring+glow) |
| `BrushSelector` | `brush_selector.py` | +/- controls |
| `HandStatusCard` | `hand_status_card.py` | per-hand card |
| `ShortcutCard` | `shortcut_card.py` | keycap rows |
| `StatusPill` | `status_pill.py` | colored badge |
| `SectionHeader` | `section_header.py` | 16px Medium label |
| `DashboardCard` | `dashboard_card.py` | base QFrame |
| `TopToolbar` | `top_toolbar.py` | logo, pills, buttons |
| `LeftSidebar` | `left_sidebar.py` | tools, colors, brush |
| `RightSidebar` | `right_sidebar.py` | hands, shortcuts |
| `BottomStatusBar` | `bottom_status_bar.py` | hints |
| `WebcamPanel` | `webcam_panel.py` | contain video |

### 7.1 Tool button (selected)

- Background: `#1E3A5F`
- Left accent bar: 4px `#2563EB`
- Text: `#F9FAFB` weight 500
- Border-radius: 8px

### 7.2 Hand status card content

```
LEFT HAND          (section, 13px secondary)
● Drawing          (badge)
Gesture: Index finger
Color: ● Blue
```

### 7.3 Keycap shortcut row

```
┌───┐
│ 1 │  Freehand
└───┘
```

---

## 8. Window Resize Behavior

```
User resizes window
    → QMainWindow.resizeEvent
    → Layout recalculates sidebar widths/heights
    → WebcamPanel updates available rect
    → FrameProcessor asked for new letterbox (w,h)
    → Canvas.resize(w,h) if changed
    → Next QTimer tick renders frame at new resolution
    → QLabel.setPixmap(scaled KeepAspectRatio)
```

**No** OpenCV window resize — single Qt window only.

---

## 9. Architecture

```
main.py
  └── QtApplication
        ├── MainWindow (layouts)
        ├── FrameProcessor (camera, track, draw) — no UI
        └── QTimer 30 FPS → update frame + bind state to widgets
```

**Removed from UI path:** `overlay_renderer.py`, OpenCV `imshow`, manual hit rects.

---

## 10. Acceptance Checklist

- [x] Resize window — no overlap, no broken panels
- [x] Webcam always proportional (contain)
- [x] Poppins used for all UI text
- [x] Tools section: 24px title gap, 12px item gap
- [x] Tool hover/selected states
- [x] Color selected ring + glow
- [x] Hand cards with status/gesture/color
- [x] Toolbar uses pills and buttons
- [x] Screenshot suitable for investor demo

---

## 11. Migration from v1 OpenCV UI

| Remove | Replace with |
|--------|--------------|
| `src/ui/components.py` | `src/ui/qt/components/*` |
| `src/ui/overlay_renderer.py` | Qt layouts |
| `src/ui/layout.py` (OpenCV Rect) | Qt layouts + `layout_metrics.py` |
| `cv2.imshow` loop in `application.py` | `qt_application.py` |

Drawing engine (`canvas`, `hand_manager`, `gestures`, `tracking`, `camera`) unchanged.
