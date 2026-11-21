
BASE_W = 7 * 84 + 8 * 18   
BASE_H = 620


BG_EDGE = "#4a0a0a"
BG_CENTER = "#b01e1e"
UI_BG = "#3d2e00"
UI_TEXT = "#e8f5ec"
BTN = "#b88a00"
BTN_HOVER = "#27ad61"
BTN_DISABLED = "#6f8f7c"
GOLD = "#ffd54a"

CARD_FACE = "#fdfdfb"
CARD_EDGE = "#9aa3a8"
SHADOW = "#0a3d22"
RED = "#d62828"
BLACK = "#1b1b1b"
FACE_TINT = {"red": "#fde8e8", "black": "#e9ecef"}

BACK_OUTER = "#f4f4f4"
BACK_BLUE = "#1d3f8f"
BACK_EDGE = "#12296b"
BACK_PATTERN = "#4a73d1"

SLOT_FILL = "#0e7a40"
SLOT_EDGE = "#4fc083"
SLOT_TEXT = "#4fc083"

F_UI = ("Segoe UI", -13, "bold")
F_INFO = ("Segoe UI", -15, "bold")


S = 1.0
X0 = 0.0
CANVAS_W = BASE_W
CANVAS_H = BASE_H
CARD_W = CARD_H = GAP = TOP = TABLEAU_Y = 0.0
FACE_DOWN_OFFSET = FACE_UP_OFFSET = WASTE_FAN = 0.0
F_RANK = F_SMALL_SUIT = F_ACE = F_PIP = F_FACE_LETTER = F_FACE_SUIT = None
F_SLOT = F_COUNT = None


def font(name, size, style=None):
    """Font whose pixel size follows the current scale."""
    px = -max(6, int(round(size * S)))
    return (name, px) if style is None else (name, px, style)


def set_layout(w, h):
    """Recompute every size for a canvas of w x h pixels."""
    global S, X0, CANVAS_W, CANVAS_H
    global CARD_W, CARD_H, GAP, TOP, TABLEAU_Y
    global FACE_DOWN_OFFSET, FACE_UP_OFFSET, WASTE_FAN
    global F_RANK, F_SMALL_SUIT, F_ACE, F_PIP, F_FACE_LETTER, F_FACE_SUIT
    global F_SLOT, F_COUNT

    w, h = max(w, 400), max(h, 300)
    S = min(w / BASE_W, h / BASE_H)
    CANVAS_W, CANVAS_H = w, h
    X0 = (w - BASE_W * S) / 2           

    CARD_W, CARD_H, GAP = 84 * S, 118 * S, 18 * S
    TOP = 16 * S
    TABLEAU_Y = TOP + CARD_H + 30 * S
    FACE_DOWN_OFFSET, FACE_UP_OFFSET, WASTE_FAN = 14 * S, 26 * S, 20 * S

    F_RANK = font("Arial", 16, "bold")
    F_SMALL_SUIT = font("Segoe UI Symbol", 15)
    F_ACE = font("Segoe UI Symbol", 50)
    F_PIP = font("Segoe UI Symbol", 18)
    F_FACE_LETTER = font("Georgia", 36, "bold")
    F_FACE_SUIT = font("Segoe UI Symbol", 18)
    F_SLOT = font("Segoe UI Symbol", 38)
    F_COUNT = font("Arial", 12, "bold")


def blend(c1, c2, t):
    """Mix two '#rrggbb' colors. t = 0 -> c1, t = 1 -> c2."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


set_layout(BASE_W, BASE_H)
