"""Drawing tool constants."""

FREEHAND = "freehand"
LINE = "line"
RECTANGLE = "rectangle"
CIRCLE = "circle"
ARROW = "arrow"
TEXT = "text"
ERASER = "eraser"
CLEAR = "clear"

LABELS = {
    FREEHAND: "Freehand",
    LINE: "Line",
    RECTANGLE: "Rectangle",
    CIRCLE: "Circle",
    ARROW: "Arrow",
    TEXT: "Text",
    ERASER: "Eraser",
    CLEAR: "Clear All",
}

KEY_MAP = {
    ord("1"): FREEHAND,
    ord("2"): LINE,
    ord("3"): RECTANGLE,
    ord("4"): CIRCLE,
    ord("5"): ARROW,
    ord("t"): TEXT,
    ord("e"): ERASER,
}

SHAPE_TOOLS = {LINE, RECTANGLE, CIRCLE, ARROW}
DRAW_TOOLS = {FREEHAND, LINE, RECTANGLE, CIRCLE, ARROW, TEXT}
