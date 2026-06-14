# Gesture Logic — AirBoard Local MVP

## MVP Gesture Table

| Gesture | Finger State | Action |
|---------|--------------|--------|
| Draw | Index up only | Draw continuous lines on canvas |
| Pointer | Index + middle up | Move fingertip pointer without drawing |
| Clear | Closed fist held ≥ 1 s | Clear entire canvas |
| Color select | Fingertip over toolbar swatch | Change active brush color |

## MediaPipe Hand Landmarks Used

MediaPipe Hands provides 21 landmarks per hand (normalized x, y, z in [0, 1] for x/y).

| Landmark | Index | Use |
|----------|-------|-----|
| WRIST | 0 | Reference (optional) |
| THUMB_TIP | 4 | Fist detection |
| THUMB_IP | 3 | Thumb extended check |
| INDEX_FINGER_TIP | 8 | Pointer position, color hover |
| INDEX_FINGER_PIP | 6 | Index extended check |
| MIDDLE_FINGER_TIP | 12 | Pointer mode |
| MIDDLE_FINGER_PIP | 10 | Middle extended check |
| RING_FINGER_TIP | 16 | Draw mode isolation |
| RING_FINGER_PIP | 14 | Ring extended check |
| PINKY_TIP | 20 | Draw mode isolation |
| PINKY_PIP | 18 | Pinky extended check |

### Pixel Conversion

```python
x_px = int(landmark.x * frame_width)
y_px = int(landmark.y * frame_height)
```

## How Finger States Are Detected

MediaPipe uses a normalized coordinate system where **y increases downward**.

For **index, middle, ring, pinky** (non-thumb fingers):

```python
finger_up = tip.y < pip.y
```

A finger is considered **down** when `tip.y >= pip.y`.

For **thumb**, handedness matters. Compare thumb tip to thumb IP joint:

- **Right hand** (label from MediaPipe): thumb up if `tip.x > ip.x`
- **Left hand**: thumb up if `tip.x < ip.x`

If handedness is unavailable, use distance from wrist or assume mirrored right-hand logic with flipped frame.

### Combined States

| State | Condition |
|-------|-----------|
| `index_up` | INDEX_TIP.y < INDEX_PIP.y |
| `middle_up` | MIDDLE_TIP.y < MIDDLE_PIP.y |
| `ring_up` | RING_TIP.y < RING_PIP.y |
| `pinky_up` | PINKY_TIP.y < PINKY_PIP.y |
| `thumb_up` | thumb tip vs IP per handedness |

## Gesture Classification Priority

Evaluate in order to avoid ambiguity:

1. **Fist** — `not index_up and not middle_up and not ring_up and not pinky_up and not thumb_up`
2. **Pointer** — `index_up and middle_up and not ring_up and not pinky_up`
3. **Draw** — `index_up and not middle_up and not ring_up and not pinky_up`
4. **Idle** — otherwise (e.g., all fingers up, or ambiguous partial poses)

Fist is checked first so a closed hand does not accidentally register as draw.

## Clear Gesture — Fist Hold Timer

### Behavior

- When fist detected: start `fist_start_time` if not already started.
- Each frame while fist continues: `elapsed = now - fist_start_time`.
- When `elapsed >= FIST_HOLD_SECONDS` (1.0): call `canvas.clear()`, reset timer, reset draw previous point.
- When fist opens before threshold: reset `fist_start_time` to `None` (no clear).

### Avoiding Accidental Clearing

| Safeguard | Rationale |
|-----------|-----------|
| 1 second hold required | Brief fist during transitions won't clear |
| All fingers must be down | Partial curl won't trigger fist |
| Clear fires once per hold | After clear, require fist open + re-close to clear again |
| Draw/pointer take precedence when fingers extended | Open hand never classified as fist |
| Optional cooldown (0.3 s) after clear | Prevents double-clear from timer edge cases |

### Visual Feedback

Show "Hold to clear..." or a progress bar filling over 1 s while fist is held, so users understand intentional action.

## Resetting Previous Drawing Points

Stray lines occur when `cv2.line` connects the last draw point to a new point after the user moved without intending to draw.

**Reset `previous_point` when:**

- Mode changes from `draw` to anything else
- Mode changes to `draw` from `idle` or `pointer` (start fresh stroke)
- Canvas is cleared
- Hand is lost (no landmarks for N frames)
- Color swatch hover selects new color (optional: start new stroke)

**Do not reset** when staying in `draw` mode with continuous motion.

## Smoothing Fingertip Movement

Raw landmark positions jitter. Apply **exponential moving average (EMA)**:

```python
smoothed_x = alpha * raw_x + (1 - alpha) * prev_smoothed_x
smoothed_y = alpha * raw_y + (1 - alpha) * prev_smoothed_y
```

Recommended `alpha = 0.4` (settings: `SMOOTHING_ALPHA`).

- Lower alpha → smoother but more lag
- Higher alpha → snappier but jittery

Only update smoothed position when valid index tip is available; decay or freeze when hand lost.

### Minimum Movement Threshold

Ignore movements smaller than `MIN_DRAW_DISTANCE` pixels (e.g., 3 px) to reduce noise dots when hand is still.

## Color Selection via Hover

Toolbar occupies top `TOOLBAR_HEIGHT` pixels (e.g., 60 px).

- Swatches laid out horizontally with padding.
- Each swatch: rectangle `(x1, y1, x2, y2)`.
- If `swatch.y1 <= fingertip.y <= swatch.y2` and x in range → select color.
- Only active in non-fist modes when index tip position is valid.
- Debounce: require fingertip inside swatch for 3 consecutive frames before switching (optional, reduces flicker).

## Mode Summary Diagram

```
                    Hand detected?
                         │
              No ────────┴──────── Yes
               │                    │
            IDLE              Read finger states
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
                 FIST          Index+Middle      Index only
                    │               │               │
              Hold ≥ 1s?        POINTER           DRAW
                    │
                   CLEAR
```
