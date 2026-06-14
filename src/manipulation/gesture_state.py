"""Gesture control state machine."""

from enum import Enum


class ControlState(str, Enum):
    IDLE = "idle"
    SELECTING = "object_selected"
    GRABBING = "object_grabbed"
    MOVING = "object_grabbed"
    TWO_HAND_ARMING = "two_hand_arming"
    TWO_HAND_READY = "two_hand_ready"
    SCALING = "two_hand_scaling"
    ROTATING = "two_hand_rotating"
    STRETCHING = "two_hand_stretching"
    TRASHING = "trash_throwing"
    TRASH_ANIM = "trash_animating"
    ERASING = "erasing"

    OBJECT_SELECTED = "object_selected"
