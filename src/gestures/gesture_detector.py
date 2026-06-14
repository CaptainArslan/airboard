import time

from dataclasses import dataclass



from src.config import settings

from src.tracking.hand_tracker import TrackedHand



# MediaPipe landmark indices

WRIST = 0

THUMB_TIP = 4

THUMB_IP = 3

INDEX_TIP = 8

INDEX_PIP = 6

MIDDLE_TIP = 12

MIDDLE_PIP = 10

RING_TIP = 16

RING_PIP = 14

PINKY_TIP = 20

PINKY_PIP = 18





class GestureMode:

    IDLE = "IDLE"

    DRAW = "DRAW"

    POINTER = "POINTER"

    FIST = "FIST"

    OPEN_PALM = "OPEN_PALM"

    PINCH = "PINCH"





@dataclass

class HandGestureState:

    """Gesture classification result for one hand."""



    hand_id: int

    mode: str

    handedness: str

    fingertip: tuple[int, int] | None

    palm_center: tuple[int, int] | None

    pinch_center: tuple[int, int] | None = None

    pinch_distance: float = 0.0

    thumb_tip: tuple[int, int] | None = None





class GestureDetector:

    """Classifies hand poses per hand into draw, pointer, eraser, fist, or idle."""



    def __init__(self):

        self._smoothed_tips: dict[str, tuple[int, int]] = {}

        self._smoothed_palms: dict[str, tuple[int, int]] = {}



    def _finger_up(self, landmarks, tip_idx, pip_idx):

        return landmarks.landmark[tip_idx].y < landmarks.landmark[pip_idx].y



    def _thumb_up(self, landmarks, handedness):

        tip = landmarks.landmark[THUMB_TIP]

        ip = landmarks.landmark[THUMB_IP]

        if handedness == "Right":

            return tip.x > ip.x

        return tip.x < ip.x



    def _get_finger_states(self, landmarks, handedness):

        return {

            "thumb": self._thumb_up(landmarks, handedness),

            "index": self._finger_up(landmarks, INDEX_TIP, INDEX_PIP),

            "middle": self._finger_up(landmarks, MIDDLE_TIP, MIDDLE_PIP),

            "ring": self._finger_up(landmarks, RING_TIP, RING_PIP),

            "pinky": self._finger_up(landmarks, PINKY_TIP, PINKY_PIP),

        }



    @staticmethod

    def detect_open_palm(fingers):

        return all(fingers.values())



    @staticmethod

    def get_palm_center(hand: TrackedHand) -> tuple[int, int]:

        """Average of wrist and MCP landmarks (0, 5, 9, 13, 17)."""

        indices = settings.PALM_LANDMARKS

        xs = [hand.pixel_coords[i][0] for i in indices]

        ys = [hand.pixel_coords[i][1] for i in indices]

        return int(sum(xs) / len(xs)), int(sum(ys) / len(ys))



    def _pinch_distance(self, hand: TrackedHand) -> float:
        tx, ty = hand.pixel_coords[THUMB_TIP]
        ix, iy = hand.pixel_coords[INDEX_TIP]
        return ((tx - ix) ** 2 + (ty - iy) ** 2) ** 0.5

    def _classify_mode(self, fingers, hand: TrackedHand):

        if not any(fingers.values()):

            return GestureMode.FIST



        if self.detect_open_palm(fingers):

            return GestureMode.OPEN_PALM



        if fingers["thumb"] and fingers["index"] and not fingers["middle"]:

            if self._pinch_distance(hand) < settings.PINCH_THRESHOLD:

                return GestureMode.PINCH



        if (

            fingers["index"]

            and fingers["middle"]

            and not fingers["ring"]

            and not fingers["pinky"]

        ):

            return GestureMode.POINTER



        if (

            fingers["index"]

            and not fingers["middle"]

            and not fingers["ring"]

            and not fingers["pinky"]

        ):

            return GestureMode.DRAW



        return GestureMode.IDLE



    def _smooth_point(self, store: dict, key: str, raw_x: int, raw_y: int):

        alpha = settings.SMOOTHING_ALPHA

        if key not in store:

            store[key] = (raw_x, raw_y)

        else:

            prev_x, prev_y = store[key]

            store[key] = (

                int(alpha * raw_x + (1 - alpha) * prev_x),

                int(alpha * raw_y + (1 - alpha) * prev_y),

            )

        return store[key]



    def _hand_key(self, hand: TrackedHand, index: int) -> str:

        return f"{hand.handedness}_{index}"



    def classify_hand(self, hand: TrackedHand, index: int) -> HandGestureState:

        key = self._hand_key(hand, index)

        handedness = hand.handedness



        tip_x, tip_y = hand.pixel_coords[INDEX_TIP]

        palm_raw = self.get_palm_center(hand)

        smoothed_palm = self._smooth_point(

            self._smoothed_palms, key, palm_raw[0], palm_raw[1]

        )



        fingers = self._get_finger_states(hand.landmarks, handedness)

        mode = self._classify_mode(fingers, hand)

        thumb = hand.pixel_coords[THUMB_TIP]
        pinch_center = None
        pinch_distance = 0.0
        if mode == GestureMode.PINCH:
            ix, iy = hand.pixel_coords[INDEX_TIP]
            tx, ty = thumb
            pinch_center = ((tx + ix) // 2, (ty + iy) // 2)
            pinch_distance = self._pinch_distance(hand)
            smoothed_tip = self._smooth_point(
                self._smoothed_tips, key + "_pinch", pinch_center[0], pinch_center[1],
            )
        else:
            smoothed_tip = self._smooth_point(self._smoothed_tips, key, tip_x, tip_y)



        return HandGestureState(

            hand_id=index,

            mode=mode,

            handedness=handedness,

            fingertip=smoothed_tip,

            palm_center=smoothed_palm if mode == GestureMode.OPEN_PALM else None,

            pinch_center=pinch_center,

            pinch_distance=pinch_distance,

            thumb_tip=thumb,

        )



    def classify_hands(self, hands: list[TrackedHand]) -> list[HandGestureState]:

        active_keys = {self._hand_key(h, i) for i, h in enumerate(hands)}



        for key in list(self._smoothed_tips.keys()):

            if key not in active_keys:

                del self._smoothed_tips[key]

        for key in list(self._smoothed_palms.keys()):

            if key not in active_keys:

                del self._smoothed_palms[key]



        return [self.classify_hand(hand, i) for i, hand in enumerate(hands)]



    @staticmethod

    def display_mode(mode: str) -> str:

        if mode == GestureMode.FIST:

            return GestureMode.IDLE

        if mode == GestureMode.PINCH:

            return "PINCH"

        if mode == GestureMode.OPEN_PALM:

            return "OPEN_PALM"

        return mode


