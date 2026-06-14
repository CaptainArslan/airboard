# Development Plan — AirBoard Local MVP

## Milestone 1: Project Setup

**Goal:** Establish repository layout, dependencies, and configuration baseline.

**Tasks:**
- Create `docs/` with all planning files
- Create `src/` package tree with `__init__.py` files
- Add `requirements.txt` with pinned OpenCV and MediaPipe
- Add `README.md` with install and run instructions
- Implement `src/config/settings.py`

**Expected output:** Runnable project skeleton; `settings.py` importable.

**Acceptance criteria:**
- [ ] Folder structure matches architecture doc
- [ ] `pip install -r requirements.txt` succeeds
- [ ] Settings constants accessible from other modules

---

## Milestone 2: Webcam Preview

**Goal:** Display live mirrored webcam feed in an OpenCV window.

**Tasks:**
- Implement `CameraManager` class: open, read, flip, release
- Wire minimal loop in `main.py` showing raw feed
- Handle open failure with clear error message
- Exit on `q` key

**Expected output:** Window titled per settings showing mirrored camera.

**Acceptance criteria:**
- [ ] Webcam opens on index 0
- [ ] Frame is horizontally flipped
- [ ] `q` closes window and releases camera

---

## Milestone 3: Hand Tracking

**Goal:** Detect hand and draw skeleton on frame.

**Tasks:**
- Implement `HandTracker` with MediaPipe Hands init
- Process RGB frames; return landmarks
- Draw `HAND_CONNECTIONS` for debug
- Integrate into main loop

**Expected output:** Hand skeleton overlays when hand visible.

**Acceptance criteria:**
- [ ] Landmarks appear for one hand
- [ ] No crash when hand leaves frame
- [ ] Tracking confidence thresholds from settings applied

---

## Milestone 4: Fingertip Pointer

**Goal:** Show smoothed circle at index fingertip.

**Tasks:**
- Extract index tip landmark (index 8) to pixel coords
- Apply exponential moving average smoothing
- Draw pointer circle in overlay module
- Track position even in pointer-only mode

**Expected output:** Circle follows index fingertip smoothly.

**Acceptance criteria:**
- [ ] Pointer visible at tip of index finger
- [ ] Movement is smoothed (no jitter)
- [ ] Pointer hidden or idle when no hand detected

---

## Milestone 5: Canvas Overlay

**Goal:** Transparent drawing layer composited over webcam.

**Tasks:**
- Implement `Canvas` with numpy buffer matching frame size
- Implement `blend()` with alpha weighting
- Test static line drawing manually

**Expected output:** Drawn lines appear over camera feed.

**Acceptance criteria:**
- [ ] Canvas same dimensions as frame
- [ ] Lines persist across frames until cleared
- [ ] Blend looks like transparent overlay

---

## Milestone 6: Drawing Mode

**Goal:** Draw when only index finger is up.

**Tasks:**
- Implement finger-up detection in `GestureDetector`
- Classify `draw` mode (index up, others down)
- Connect consecutive fingertip points with `cv2.line`
- Reset previous point when entering draw from idle

**Expected output:** Air-drawing with index finger only.

**Acceptance criteria:**
- [ ] Lines follow finger in draw mode
- [ ] No drawing when index finger down
- [ ] Brush color and thickness from settings

---

## Milestone 7: Pointer Mode

**Goal:** Move without drawing when index + middle up.

**Tasks:**
- Detect pointer gesture (index + middle up)
- Call `canvas.reset_previous_point()` on pointer mode
- Update UI mode label

**Expected output:** Reposition finger without stray lines.

**Acceptance criteria:**
- [ ] No line drawn between pointer reposition and next draw stroke
- [ ] Mode label shows POINTER when active

---

## Milestone 8: Clear Gesture

**Goal:** Clear canvas on fist held 1 second.

**Tasks:**
- Detect all fingers closed (fist)
- Start timer on fist; reset when fist opens
- Trigger `canvas.clear()` after 1.0 s hold
- Optional visual feedback during hold

**Expected output:** Canvas wipes after sustained fist.

**Acceptance criteria:**
- [ ] Brief fist does not clear
- [ ] 1 s hold clears all strokes
- [ ] Previous point reset after clear

---

## Milestone 9: Color Selector

**Goal:** Select brush color by hovering fingertip over toolbar swatches.

**Tasks:**
- Draw toolbar with color rectangles in `Overlay`
- Hit-test fingertip against swatch bounds
- Update `canvas.set_color()` on hover
- Highlight active swatch

**Expected output:** User changes draw color via air hover.

**Acceptance criteria:**
- [ ] At least 4 colors selectable
- [ ] New strokes use newly selected color
- [ ] Active color visible in toolbar

---

## Milestone 10: Refactor into Modules

**Goal:** Final clean separation per architecture doc.

**Tasks:**
- Move all logic out of monolithic script into `src/` modules
- Slim `main.py` to orchestration only
- Remove dead code and duplicate constants
- Ensure imports are clean

**Expected output:** Maintainable modular codebase.

**Acceptance criteria:**
- [ ] Each module has single clear responsibility
- [ ] `main.py` under ~80 lines
- [ ] No hardcoded magic numbers outside settings

---

## Milestone 11: Testing and Polish

**Goal:** Validate MVP against checklist; fix bugs.

**Tasks:**
- Run through `docs/05_TESTING_CHECKLIST.md`
- Tune smoothing and gesture thresholds
- Improve error messages for camera failures
- Update README with gesture guide

**Expected output:** Stable MVP ready for demo.

**Acceptance criteria:**
- [ ] All core checklist items pass
- [ ] No resource leaks on exit
- [ ] Acceptable performance on target hardware
