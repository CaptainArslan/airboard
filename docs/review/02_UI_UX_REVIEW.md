# UI/UX Review — AirBoard Local MVP

**Reviewer role:** UI/UX engineer  
**Date:** 2026-06-14

---

## Executive Summary

AirBoard functions but presents as **raw OpenCV debug output**: text stacked in a gray bar, hand skeletons visible by default, duplicate shortcut hints, no side tool panel, and no visual hierarchy between "product UI" and "computer vision overlay."

---

## Why It Looks Unprofessional

1. **OpenCV `putText` as the entire UI** — No panels, no padding system, no consistent typography; text baselines vary with resolution.
2. **Debug skeleton on by default** — Green lines and red dots on the user's face/hands scream "developer prototype."
3. **Flat gray toolbar** — Opaque `#282828` block with no translucency, shadow, or separation from video.
4. **No brand presence** — Window title says "AirBoard Local MVP"; toolbar never shows product name.
5. **Letterboxing invisible to user** — Black bars from aspect-ratio fit look like broken layout; no indication that drawing area includes bars.
6. **Competing text zones** — Toolbar lists 4 lines of keys; separate hint says "q/Esc | f"; information overload at top-left.
7. **No active-state design** — Selected tool is text-only in a crowded paragraph, not a highlighted panel item.

---

## Toolbar Design Problems

| Problem | Detail |
|---------|--------|
| **Overloaded** | Color swatches + 4 lines of status/keys in one 10% height band |
| **No hierarchy** | Tool name, hand modes, and keyboard cheatsheet same visual weight |
| **Cramped on ultrawide** | Swatches left, text immediately after — vast empty space on 3440px width unused |
| **Missing spec items** | No "AirBoard" title, brush size, color name, or Help badge |
| **Not translucent** | Spec asks dark translucent bar; current is solid opaque rectangle |
| **Color swatches too small** | Hard to hit with finger hover on large screens without scaling logic tied to window |

**Current toolbar content (approximate):**
```
[swatches] Tool: Freehand
           Left Hand: DRAW
           Right Hand: IDLE
           Keys: h=Freehand l=Line ...
[q/Esc = Quit | f = Toggle Fullscreen]  ← overlaps toolbar zone
```

---

## Instruction / Help Problems

| Issue | Impact |
|-------|--------|
| Duplicate quit/fullscreen hints | User distrust — which is correct? |
| Outdated key map in toolbar (`h` freehand) vs target spec (`1`–`5` tools) | Learning curve |
| No help overlay toggle | Spec requires `h` = help; not implemented |
| No bottom help bar | Spec wants dedicated bottom strip; everything crammed top |
| README documents fist-clear | Feature removed/changed — user confusion |

---

## Fullscreen / Window Behavior

**Fixed recently (partial):**
- Windowed default 1280×720 ✓
- `f` toggle ✓
- `q` / Esc quit ✓
- Aspect ratio preserved ✓

**Remaining UX issues:**

| Issue | Detail |
|-------|--------|
| Canvas cleared on resize | Toggling fullscreen wipes drawings — feels broken |
| No on-screen "Windowed" / "Fullscreen" badge | User may not know how they entered fullscreen |
| OpenCV window chrome | Cannot style title bar; looks like generic CV window |
| No escape hatch hint on first launch | Hint exists but small and top-left |
| Fullscreen uses full monitor including ultrawide | Toolbar spans entire 3440px — text still left-clustered |

---

## Shape Selection UX

| Problem | Detail |
|---------|--------|
| Keyboard-only | `h/l/r/c/a` not discoverable; no side panel |
| No numeric shortcuts | Target spec wants `1`–`5` — not implemented |
| No active tool highlight | User cannot see selected tool at a glance |
| Preview is thin gray | Low contrast on video; not dashed as spec suggests |
| Shape + freehand tool confusion | Eraser is gesture (palm) AND spec wants tool `e` — dual model |

---

## Gesture Feedback Problems

| Mode | Current | Spec target | Gap |
|------|---------|-------------|-----|
| Draw | Filled color dot | Colored fingertip circle | OK |
| Pointer | White ring | White circle | OK |
| Eraser | Lavender outline | Semi-transparent **red** duster | Wrong color; not semi-transparent |
| Fist | Mapped to IDLE | Stop/idle | No visual feedback |
| Shape preview | Solid gray stroke | Dashed/highlighted | Weak contrast |

**Hand skeleton:** Should be off in production; when on, clashes with draw indicators.

---

## Visual Hierarchy Problems

```
Current stacking (top → bottom):
1. Solid toolbar (dominates)
2. Duplicate control hint text
3. Hand skeleton (debug)
4. Drawings
5. Webcam video
6. (nothing at bottom — help should be here)
```

**Ideal hierarchy:**
1. Video (primary)
2. Drawings (content layer)
3. Gesture indicators (subtle)
4. Top status bar (compact, translucent)
5. Left tool rail (persistent navigation)
6. Bottom help bar (optional / toggle)

---

## How to Make It Feel Like a Real Product

### Immediate wins
- Disable skeleton by default
- Single bottom help bar; remove duplicate top hint
- Left panel with tool list + active highlight
- Compact top bar: `AirBoard | Tool | Color | Brush | L: Draw | R: Idle | H: Help`
- Semi-transparent panels using alpha-blended overlays
- Status badge for window mode (Windowed / Fullscreen)

### Medium effort
- Theme module (`theme.py`) with palette, spacing, fonts
- Component-based UI (`draw_panel`, `draw_badge`, `draw_tool_button`)
- Help overlay (full semi-transparent sheet with shortcuts)
- Color names ("Blue") not just swatches
- Brush size indicator with `+`/`-` feedback animation

### Polish
- Subtle shadow under panels
- Eraser: red fill at 40% alpha
- Dashed shape preview via line pattern
- First-run tooltip: "Press H for help, Q to quit"

---

## UX Acceptance Gap (Current vs Target)

| Requirement | Status |
|-------------|--------|
| Top toolbar professional layout | ❌ Partial |
| Left tool panel | ❌ Missing |
| Bottom help bar | ❌ Missing |
| Help overlay (`h`) | ❌ Missing |
| Numeric tool keys 1–5 | ❌ Missing |
| Clear tool (`x`) keyboard | ❌ Missing |
| Brush +/- | ❌ Missing |
| Active tool highlight | ❌ Missing |
| Eraser visual (red, semi-transparent) | ❌ Wrong style |
| No debug overlay for users | ❌ Skeleton on |

---

## Recommended UI Architecture

```
OverlayRenderer
├── TopBarComponent      (brand, status, hand badges)
├── LeftToolPanel        (tools, active state)
├── ColorPalette         (swatches, hover hit-test)
├── BottomHelpBar        (shortcuts, toggleable)
├── HelpOverlay          (full screen, on H)
└── HandIndicatorLayer   (draw/pointer/eraser cursors)
```

All layout from `theme.py` spacing tokens and frame-size percentages — never absolute pixels tied to monitor at import.
