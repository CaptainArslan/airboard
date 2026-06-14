# Testing Checklist — AirBoard Local MVP

Use this checklist for manual validation before declaring the MVP complete.

## Environment Setup

| # | Test | Steps | Pass |
|---|------|-------|------|
| E-01 | Dependencies install | `pip install -r requirements.txt` | ☐ |
| E-02 | App starts | `python main.py` from project root | ☐ |
| E-03 | Python version | Python 3.10+ confirmed | ☐ |

## Webcam

| # | Test | Steps | Expected | Pass |
|---|------|-------|----------|------|
| W-01 | Webcam opens | Launch app | Live video appears | ☐ |
| W-02 | Mirrored feed | Move hand left/right | On-screen motion matches mirror expectation | ☐ |
| W-03 | Webcam closes safely | Press `q` | Window closes; camera LED off | ☐ |
| W-04 | No frame hang | Cover lens briefly | App does not freeze permanently | ☐ |
| W-05 | Resolution | Observe window size | Matches settings (e.g., 1280×720) | ☐ |

## Hand Detection

| # | Test | Steps | Expected | Pass |
|---|------|-------|----------|------|
| H-01 | Hand detected | Show one hand to camera | Skeleton landmarks visible | ☐ |
| H-02 | Hand lost | Remove hand from frame | No crash; idle mode | ☐ |
| H-03 | Single hand | Two hands in frame | Only one tracked (max_num_hands=1) | ☐ |
| H-04 | Re-acquire | Hand leaves and returns | Tracking resumes | ☐ |

## Fingertip Pointer

| # | Test | Steps | Expected | Pass |
|---|------|-------|----------|------|
| P-01 | Pointer follows tip | Move index finger | Circle tracks fingertip | ☐ |
| P-02 | Smooth motion | Draw slow circle | Pointer not excessively jittery | ☐ |
| P-03 | Pointer in pointer mode | Index + middle up | Pointer visible, no draw | ☐ |

## Drawing

| # | Test | Steps | Expected | Pass |
|---|------|-------|----------|------|
| D-01 | Draw mode activates | Index up only | Mode shows DRAW | ☐ |
| D-02 | Lines appear | Move finger in draw mode | Colored lines on overlay | ☐ |
| D-03 | Lines persist | Stop drawing | Strokes remain visible | ☐ |
| D-04 | No draw when idle | All fingers down | No new lines | ☐ |
| D-05 | Stroke quality | Draw letter "A" | Recognizable shape | ☐ |

## Pointer Mode

| # | Test | Steps | Expected | Pass |
|---|------|-------|----------|------|
| M-01 | Pointer mode activates | Index + middle up | Mode shows POINTER | ☐ |
| M-02 | No drawing in pointer | Move hand in pointer mode | No lines added | ☐ |
| M-03 | No connector line | Draw → pointer → draw elsewhere | No line connecting separate strokes | ☐ |
| M-04 | Mode transition | Switch draw ↔ pointer | Clean transitions | ☐ |

## Clear Gesture

| # | Test | Steps | Expected | Pass |
|---|------|-------|----------|------|
| C-01 | Brief fist no clear | Quick fist < 1 s | Canvas unchanged | ☐ |
| C-02 | Hold fist clears | Fist held ≥ 1 s | All strokes removed | ☐ |
| C-03 | Draw after clear | Draw again after clear | New strokes work | ☐ |
| C-04 | Accidental clear | Normal drawing gestures | Canvas not cleared unexpectedly | ☐ |

## Color Selection

| # | Test | Steps | Expected | Pass |
|---|------|-------|----------|------|
| S-01 | Swatches visible | Look at toolbar | Multiple color boxes shown | ☐ |
| S-02 | Hover selects | Hover index tip on red swatch | Active color = red | ☐ |
| S-03 | Draw new color | Draw after selecting blue | Lines are blue | ☐ |
| S-04 | Active indicator | Select different colors | UI shows current selection | ☐ |

## Stability and Edge Cases

| # | Test | Steps | Expected | Pass |
|---|------|-------|----------|------|
| X-01 | App does not crash | Run 5+ minutes with varied gestures | No exceptions | ☐ |
| X-02 | Rapid mode switching | Flip gestures quickly | Stable behavior | ☐ |
| X-03 | Low-light behavior | Dim room lighting | Degraded but usable or graceful idle | ☐ |
| X-04 | Camera permission denied | Block camera in OS settings | Clear error, clean exit | ☐ |
| X-05 | Camera in use | Open app with camera busy elsewhere | Error message, no hang | ☐ |
| X-06 | Multiple q presses | Press `q` once | Single clean shutdown | ☐ |

## Resource Cleanup

| # | Test | Steps | Expected | Pass |
|---|------|-------|----------|------|
| R-01 | Window destroyed | After exit | No orphan OpenCV windows | ☐ |
| R-02 | Camera released | After exit | Webcam available to other apps | ☐ |
| R-03 | Re-launch | Run app again after exit | Opens normally second time | ☐ |

## Sign-off

| Role | Name | Date | Result |
|------|------|------|--------|
| Tester | | | ☐ Pass / ☐ Fail |
| Notes | | | |
