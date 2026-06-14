# AirBoard UI Redesign v2 — Planning Document

**Version:** 2.0  
**Date:** 2026-06-14  
**Status:** Planning only — no implementation until approved  
**Author:** Architecture / UI review

---

## Executive Summary

AirBoard v1 UI improved structure (4-zone layout, theme tokens, component classes) but still renders every pixel through **OpenCV `putText` / `rectangle` / `addWeighted` on a single BGR frame**. That approach has a hard ceiling: it cannot deliver OBS/Miro/Figma-quality typography, interaction, or layout fidelity.

**UI v2 proposes migrating the presentation layer to PySide6 (Qt)** while keeping OpenCV + MediaPipe + the existing drawing engine unchanged. The webcam becomes a **Qt widget** fed by numpy frames; all chrome becomes **native Qt widgets**.

---

## Part 1 — Current UI Weaknesses

### 1.1 Fundamental technology limit

| Issue | Why it matters |
|-------|----------------|
| **OpenCV is not a UI toolkit** | No real widgets, layouts, fonts, hover, focus, or accessibility |
| **`FONT_HERSHEY_SIMPLEX` only** | Cannot match Inter/system UI fonts; kerning and weights are poor |
| **Pixel-drawn “panels”** | Rectangles with alpha blend ≠ cards with radius, shadow, elevation |
| **Manual hit-testing** | Sidebar clicks rebuilt via rect math each frame; fragile at scale |
| **Single `cv2.imshow` window** | No native title bar styling, DPI awareness, or OS integration |

Even with theme tokens and 4 zones, the result reads as **“styled OpenCV demo”** because the rendering primitive is wrong for product UI.

### 1.2 Layout weaknesses (v1)

| Area | Problem |
|------|---------|
| **Top toolbar** | Cramped; mixes brand, metadata, hand badges, and hints in one row |
| **Left sidebar** | Fixed ratio width (~220px); not true 300px card stack; tools lack card containers |
| **Right sidebar** | Hand status is minimal; no gesture detail, color, or session info |
| **Webcam area** | Letterboxed inside content rect but **no panel frame** — no radius, shadow, or padding |
| **Bottom bar** | Plain text strip; duplicates right sidebar shortcuts |
| **Help overlay** | Drawn on video buffer; blocks content awkwardly |

### 1.3 Interaction weaknesses

- Keyboard handling via `cv2.waitKey` — no modifier keys, no focus model
- Mouse only via `setMouseCallback` — no hover states on tools
- Fullscreen toggled via OpenCV property — inconsistent across OS/DPI
- No scroll for future sidebar content (“Future Space” requirement)
- Color/tool selection not visually animated

### 1.4 Architecture weaknesses

```
Current stack:
  Camera → numpy → Hand track → Draw → blend → OverlayRenderer (OpenCV draw) → imshow
```

UI state (`AppState`, tool selection, help flag) lives in Python while UI rendering is **procedural drawing** each frame. There is no separation between **view** (Qt) and **presenter** (application logic).

### 1.5 Visual comparison gap

| Product quality | AirBoard v1 |
|-----------------|-------------|
| OBS: native panels, crisp type | Approximated with putText |
| Figma: 8px grid, elevation | Manual padding ratios |
| Miro: card sidebar, keycaps | Text shortcuts `[1] Freehand` drawn as text |
| Loom: embedded video in frame | Video flush in rect, no shadow |

**Screenshot test:** Users still identify v1 as a CV project, not shipping software.

---

## Part 2 — Technology Evaluation: PySide6

### 2.1 Recommendation

**Adopt PySide6 for all UI chrome.** Keep OpenCV and MediaPipe in the processing pipeline.

| Layer | Technology |
|-------|------------|
| Window, layout, widgets | **PySide6** |
| Webcam display | **QLabel** or **QOpenGLWidget** / custom `QWidget.paintEvent` with `QImage` |
| Frame processing | **OpenCV** (capture, resize, blend) |
| Hand tracking | **MediaPipe** (unchanged) |
| Drawing buffer | **NumPy + OpenCV** (`Canvas` class, unchanged) |
| Main loop | **Qt event loop** (`QTimer` @ 30–60 FPS) replaces `while True` + `waitKey` |

### 2.2 Why PySide6 (not Tkinter, Dear PyGui, etc.)

| Option | Verdict |
|--------|---------|
| **PySide6** | ✅ Native look, layouts, fonts, stylesheets, LGPL, widely used in desktop apps |
| Tkinter | ❌ Dated aesthetics; harder to reach Figma/OBS quality |
| Dear PyGui | ⚠️ Game-like UI; not dashboard/product style |
| OpenCV only | ❌ Already at ceiling |
| Electron + web | ⚠️ Heavy; overkill for local MVP |

### 2.3 Dependency impact

```txt
# requirements.txt addition
PySide6>=6.6
```

Estimated install size: +~80–150 MB. Acceptable for desktop product.

### 2.4 Webcam embedding strategy

**Recommended: `QLabel` + `QImage` from numpy BGR**

```python
# Pseudocode — each frame tick
rgb = cv2.cvtColor(composited_frame, cv2.COLOR_BGR2RGB)
h, w, ch = rgb.shape
qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
label.setPixmap(QPixmap.fromImage(qimg).scaled(
    label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
))
```

**Gesture indicators** (draw cursor, eraser circle, shape preview) can be:
- **Option A:** Burned into numpy before Qt display (simpler migration)
- **Option B:** Qt overlay widgets positioned absolutely (cleaner long-term)

Phase 1 migration: **Option A** (minimal risk). Phase 2: optional Qt overlay layer.

### 2.5 What stays OpenCV

- `CameraManager.read_raw()`
- `Canvas` blend, stroke, shape, erase
- `HandTracker`, `GestureDetector`, `HandDrawingManager`
- `resize_with_aspect_ratio()` for internal content sizing

### 2.6 What is removed (after migration)

- `src/ui/components.py` OpenCV draw paths
- `src/ui/overlay_renderer.py` compositor
- `cv2.imshow`, `cv2.waitKey`, `cv2.setMouseCallback`
- `setup_windowed_window`, `set_fullscreen` in `display.py` (Qt handles window)

---

## Part 3 — New Layout Strategy

### 3.1 Window structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TOP TOOLBAR (56–64px fixed)                                            │
│  AirBoard logo | Tool | Color | Brush | Session | Help | Fullscreen    │
├──────────────┬──────────────────────────────────────────┬──────────────┤
│              │  ┌────────────────────────────────────┐  │              │
│  LEFT        │  │                                    │  │  RIGHT       │
│  SIDEBAR     │  │     WEBCAM PANEL (rounded)         │  │  SIDEBAR     │
│  300px       │  │     video + drawing layer          │  │  280px       │
│              │  │                                    │  │              │
│  [Cards]     │  └────────────────────────────────────┘  │  [Cards]     │
│              │                                          │              │
├──────────────┴──────────────────────────────────────────┴──────────────┤
│  BOTTOM STATUS BAR (40px) — gesture hints | q/Esc | f | h               │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Qt layout hierarchy

```
QMainWindow
└── QWidget (central, dark bg #0B1220)
    └── QVBoxLayout (0 margins)
        ├── TopToolbar (QWidget, fixed height)
        ├── QHBoxLayout (stretch)
        │   ├── LeftSidebar (QScrollArea or QWidget, fixed 300px)
        │   ├── WebcamPanel (QFrame, stretch=1, rounded + shadow)
        │   │   └── VideoLabel (QLabel, align center)
        │   └── RightSidebar (QScrollArea, fixed 280px)
        └── BottomStatusBar (QWidget, fixed 40px)
```

### 3.3 Sizing rules

| Region | Width / height | Behavior |
|--------|----------------|----------|
| Left sidebar | **300px** fixed | Scroll if content overflows |
| Right sidebar | **280px** fixed | Scroll for shortcuts + future |
| Top toolbar | **56–64px** | Fixed |
| Bottom bar | **40px** | Fixed |
| Webcam panel | **Remaining** | Expands; video letterboxed inside |
| Min window | **1280 × 720** | Default size |
| Fullscreen | `QMainWindow.showFullScreen()` | Native toggle with `F11` or `F` |

### 3.4 Webcam panel design

- `QFrame` with `border-radius: 12px`, `border: 1px solid #1F2937`
- `box-shadow` via Qt graphics effect (`QGraphicsDropShadowEffect`)
- Inner padding: **16px**
- Background: `#0B1220` (matches app)
- Video centered with **Qt.KeepAspectRatio** — never stretch

---

## Part 4 — New Component System

All components live under `src/ui/qt/` (new package).

### 4.1 Component catalog

| Component | Qt base | Responsibility |
|-----------|---------|----------------|
| `ToolCard` | `QFrame` | Groups tool list; title “Tools” |
| `ToolButtonRow` | `QPushButton` or custom | Single tool with icon + label + active state |
| `ColorChip` | `QPushButton` | Circular color swatch, selectable |
| `ColorPickerCard` | `QFrame` | Grid of `ColorChip` |
| `BrushSelector` | `QWidget` | Slider or +/- stepper, shows “6px” |
| `CurrentToolCard` | `QFrame` | Large active tool summary |
| `HandStatusBadge` | compact inline widget | Dot + status text |
| `HandStatusCard` | `QFrame` | Full card per hand (see §4.2) |
| `StatusCard` | `QFrame` | Generic titled card container |
| `ShortcutCard` | `QFrame` | Keycap rows |
| `KeycapLabel` | `QLabel` | Styled `[1]` keycap |
| `SessionStatusCard` | `QFrame` | FPS, hands detected, canvas state |
| `TopToolbar` | `QWidget` | Composes logo + metadata + actions |
| `BottomStatusBar` | `QWidget` | Hint line |
| `WebcamPanel` | `QFrame` | Video container |
| `HelpDialog` | `QDialog` or overlay `QWidget` | Shortcuts reference |

### 4.2 Hand status card (per hand)

```
┌─────────────────────────────┐
│  LEFT HAND                  │
│  ─────────────────────────  │
│  Status      Drawing        │
│  Gesture     Index finger   │
│  Color       ● Blue         │
└─────────────────────────────┘
```

Separate card for **RIGHT HAND**. Use `HandStatusCard(left=True)`.

Data bound from `HandGestureState` + `HandDrawingState` via signals or direct poll in timer.

### 4.3 Shortcut keycap design

Not plain text. Each row:

```
[ 1 ]  Freehand
[ 2 ]  Line
```

`KeycapLabel`: fixed size ~28×24px, `#374151` background, `#F9FAFB` text, `border-radius: 4px`, `border: 1px solid #1F2937`.

### 4.4 Card container pattern

```python
class StatusCard(QFrame):
    """Base card: padding 16px, radius 8px, bg #111827, border #1F2937."""
```

All sidebar sections use `StatusCard` subclassing for consistency.

---

## Part 5 — New Design System

### 5.1 Color tokens (unchanged from v1 spec, now in Qt stylesheet)

| Token | Hex | Usage |
|-------|-----|-------|
| `bg.app` | `#0B1220` | Window background |
| `bg.panel` | `#111827` | Cards, sidebars |
| `border.default` | `#1F2937` | Card borders |
| `text.primary` | `#F9FAFB` | Headings, values |
| `text.secondary` | `#9CA3AF` | Labels, hints |
| `accent.primary` | `#2563EB` | Active tool, links |
| `accent.soft` | `#1E3A5F` | Active tool background |
| `status.success` | `#22C55E` | Idle |
| `status.warning` | `#F59E0B` | Pointer |
| `status.danger` | `#EF4444` | Eraser |

### 5.2 Typography (Qt fonts)

| Role | Size | Weight | Widget |
|------|------|--------|--------|
| Title | **24px** | 600 | App name, dialog titles |
| Section | **16px** | 600 | Card headers (“Tools”, “Hand Status”) |
| Body | **14px** | 400 | Values, tool names |
| Help | **12px** | 400 | Bottom bar, shortcut descriptions |

```python
# theme.py
FONT_FAMILY = "Inter, Segoe UI, sans-serif"
```

Load Inter if bundled; fallback to Segoe UI on Windows.

### 5.3 Spacing grid (8px base)

| Token | Value |
|-------|-------|
| `space.xs` | 4px |
| `space.sm` | 8px |
| `space.md` | 16px |
| `space.lg` | 24px |
| `space.xl` | 32px |

### 5.4 Elevation

| Level | Shadow |
|-------|--------|
| Card | `0 1px 3px rgba(0,0,0,0.4)` |
| Webcam panel | `0 4px 24px rgba(0,0,0,0.5)` |
| Help dialog | `0 8px 32px rgba(0,0,0,0.6)` |

Use `QGraphicsDropShadowEffect` on webcam panel and modals.

### 5.5 Stylesheet strategy

Central `styles.qss` loaded at startup:

```python
app.setStyleSheet(load_theme_qss())
```

Object names for targeting: `ToolButton[active="true"]`, `ColorChip`, `HandStatusCard`.

### 5.6 Gesture indicators (on video)

| Mode | Visual |
|------|--------|
| Draw | Colored circle + subtle glow (numpy or Qt overlay) |
| Pointer | White ring, 2px |
| Eraser | Semi-transparent red circle, 40% alpha |
| Shape preview | Accent blue `#2563EB`, dashed if possible |

---

## Part 6 — Application Architecture (Post-Migration)

```
src/
  app/
    application.py      → AirBoardApplication (Qt QMainWindow host)
    app_state.py          → dataclass state
    frame_worker.py       → QTimer tick: camera + track + draw
  camera/                 → unchanged
  tracking/               → unchanged
  gestures/               → unchanged
  drawing/                → unchanged
  ui/
    qt/
      main_window.py      → QMainWindow assembly
      top_toolbar.py
      left_sidebar.py
      right_sidebar.py
      bottom_status_bar.py
      webcam_panel.py
      components/
        tool_card.py
        status_card.py
        shortcut_card.py
        color_chip.py
        brush_selector.py
        hand_status_badge.py
      theme.py              → tokens + load_qss()
      styles.qss
    legacy/               → move old OpenCV ui (delete after cutover)
  config/
  utils/
```

### 6.1 Event flow

```
QTimer (33ms)
  → read camera
  → process hands + gestures
  → update HandDrawingManager
  → blend canvas
  → draw gesture indicators (numpy)
  → emit QImage to WebcamPanel
  → update sidebar labels from AppState
```

Keyboard shortcuts: `QShortcut` on `QMainWindow` (cleaner than waitKey).

### 6.2 main.py (target)

```python
from src.app.application import main

if __name__ == "__main__":
    main()
```

```python
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(load_theme_qss())
    window = AirBoardMainWindow()
    window.show()
    sys.exit(app.exec())
```

---

## Part 7 — Migration Strategy

### Phase 0 — Approval gate (current)

- [x] Write this document
- [ ] Stakeholder review
- [ ] Approve PySide6 dependency

### Phase 1 — Qt shell (no behavior change)

**Goal:** Window with layout zones; black placeholder in webcam panel.

- Add PySide6 to requirements
- Create `MainWindow` with top/left/right/bottom + empty video panel
- Move keyboard shortcuts to `QShortcut`
- **Acceptance:** App opens; panels visible; quit works; no camera yet

### Phase 2 — Embed video pipeline

**Goal:** Replace `cv2.imshow` with Qt video label.

- Port `AirBoardApplication` loop to `QTimer`
- Feed composited numpy frame to `WebcamPanel`
- Preserve aspect ratio inside panel
- **Acceptance:** Drawing + gestures work as v1

### Phase 3 — Sidebar components

**Goal:** Replace OpenCV-drawn sidebars with Qt cards.

- Implement `ToolCard`, `ColorPickerCard`, `BrushSelector`
- Wire clicks to `HandDrawingManager`
- Remove OpenCV overlay renderer

### Phase 4 — Right sidebar + keycaps

**Goal:** Hand status cards + shortcut keycaps.

- `HandStatusCard` × 2 with live updates
- `ShortcutCard` with `KeycapLabel`
- `SessionStatusCard` (hands detected, tool name)

### Phase 5 — Webcam panel polish

**Goal:** Rounded corners, shadow, padding.

- `QFrame` styling + graphics effect
- Dark letterbox inside panel only

### Phase 6 — Help dialog + fullscreen

**Goal:** Native `HelpDialog`; `showFullScreen()`.

- Remove OpenCV window utilities
- Test 1280×720 and ultrawide

### Phase 7 — Cleanup

- Delete `src/ui/components.py`, `overlay_renderer.py`, `layout.py` (OpenCV)
- Update README, screenshots
- Manual QA against checklist below

### Rollback plan

Keep git tag `ui-v1-opencv` before Phase 1. Each phase is one PR; revert single PR if blocked.

---

## Part 8 — Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Qt + OpenCV thread safety | Medium | All processing on main thread via QTimer first; later QThread if needed |
| FPS drop from QImage conversion | Low | Reuse buffer; limit to 30 FPS; profile on target hardware |
| PySide6 install size | Low | Document in README |
| DPI scaling on Windows | Medium | Enable `Qt.AA_EnableHighDpiScaling` |
| Gesture coords vs letterbox | Medium | Single `ContentRect` helper maps panel size → canvas size |
| Migration scope creep | High | Strict phase gates; no new features during UI v2 |

---

## Part 9 — Final Acceptance Criteria

The redesign is complete when:

1. **No OpenCV text or panels** are used for UI chrome.
2. Window uses **PySide6 QMainWindow** with fixed **300px** left and **280px** right sidebars.
3. Webcam sits in a **rounded, bordered, shadowed panel** with padding.
4. Typography uses **Qt fonts** at 24 / 16 / 14 / 12 px hierarchy.
5. Hand status shown in **separate cards** with status, gesture, and color.
6. Shortcuts rendered as **keycaps**, not plain text.
7. All v1 features preserved: two-hand draw, shapes, palm eraser, clear, brush +/-.
8. Default **1280×720** windowed; **F** fullscreen; **Q/Esc** quit.
9. **Screenshot test:** independent reviewers classify app as “real product” not “CV demo.”

---

## Part 10 — Open Questions (Resolve Before Phase 1)

| # | Question | Recommendation |
|---|----------|----------------|
| 1 | Bundle Inter font or use system font? | System Segoe UI first; bundle Inter later |
| 2 | Tool icons: SVG vs Unicode? | Qt icon theme + simple SVG assets in `assets/icons/` |
| 3 | Eraser tool `e` vs palm-only? | Keep palm gesture; `e` highlights eraser mode in UI only |
| 4 | Air hover color pick on video? | Defer; sidebar + keyboard sufficient for v2 |
| 5 | macOS/Linux QA priority? | Windows first; Qt eases cross-platform follow-up |

---

## Appendix A — Files to Deprecate

| File | Action |
|------|--------|
| `src/ui/components.py` | Remove after Phase 3 |
| `src/ui/overlay_renderer.py` | Remove after Phase 2 |
| `src/ui/layout.py` | Remove after Phase 2 |
| `src/ui/theme.py` (OpenCV) | Replace with `src/ui/qt/theme.py` |
| `display.py` window functions | Remove `setup_windowed_window`, `set_fullscreen` |

## Appendix B — Files to Create

| File | Phase |
|------|-------|
| `src/ui/qt/main_window.py` | 1 |
| `src/ui/qt/webcam_panel.py` | 2 |
| `src/ui/qt/components/*.py` | 3–4 |
| `src/ui/qt/styles.qss` | 1 |
| `src/app/frame_worker.py` | 2 |

---

**Next step:** Review and approve this document. Implementation begins at **Phase 1 — Qt shell** only after approval.
