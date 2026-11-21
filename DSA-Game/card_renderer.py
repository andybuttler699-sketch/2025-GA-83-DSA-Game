
import theme as T
from card import SYMBOLS, rank_name


def rounded_rect(canvas, x1, y1, x2, y2, r=None, **kw):
    if r is None:
        r = 9 * T.S
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
           x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
           x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)



_L, _C, _R = 0.31, 0.5, 0.69
_SIX = [(_L, .22), (_R, .22), (_L, .5), (_R, .5), (_L, .78), (_R, .78)]
PIPS = {
    2: [(_C, .22), (_C, .78)],
    3: [(_C, .22), (_C, .5), (_C, .78)],
    4: [(_L, .22), (_R, .22), (_L, .78), (_R, .78)],
    5: [(_L, .22), (_R, .22), (_C, .5), (_L, .78), (_R, .78)],
    6: _SIX,
    7: _SIX + [(_C, .36)],
    8: _SIX + [(_C, .36), (_C, .64)],
    9: [(_L, .22), (_R, .22), (_L, .41), (_R, .41),
        (_L, .59), (_R, .59), (_L, .78), (_R, .78), (_C, .5)],
    10: [(_L, .22), (_R, .22), (_L, .41), (_R, .41),
         (_L, .59), (_R, .59), (_L, .78), (_R, .78), (_C, .31), (_C, .69)],
}


def draw_card(canvas, card, x, y, tags=("card",), lift=False):
    """Draw a face-up card with its top-left corner at (x, y)."""
    s, w, h = T.S, T.CARD_W, T.CARD_H
    off = (5 if lift else 2) * s
    rounded_rect(canvas, x + off, y + off + s, x + w + off, y + h + off + s,
                 fill=T.SHADOW, outline="", tags=tags)
    rounded_rect(canvas, x, y, x + w, y + h,
                 fill=T.CARD_FACE, outline=T.CARD_EDGE, width=1, tags=tags)

    col = T.RED if card.color == "red" else T.BLACK
    sym = SYMBOLS[card.suit]
    r = rank_name(card.rank)


    canvas.create_text(x + 11 * s, y + 14 * s, text=r, fill=col, font=T.F_RANK, tags=tags)
    canvas.create_text(x + 11 * s, y + 30 * s, text=sym, fill=col, font=T.F_SMALL_SUIT, tags=tags)
    canvas.create_text(x + w - 11 * s, y + h - 14 * s, text=r, fill=col,
                       font=T.F_RANK, angle=180, tags=tags)
    canvas.create_text(x + w - 11 * s, y + h - 30 * s, text=sym, fill=col,
                       font=T.F_SMALL_SUIT, angle=180, tags=tags)

    cx, cy = x + w / 2, y + h / 2
    if card.rank == 1:                                
        canvas.create_text(cx, cy, text=sym, fill=col, font=T.F_ACE, tags=tags)
    elif card.rank >= 11:                               
        rounded_rect(canvas, x + w * 0.27, y + h * 0.2, x + w * 0.73, y + h * 0.8, 6 * s,
                     fill=T.FACE_TINT[card.color], outline=col, width=1, tags=tags)
        canvas.create_text(cx, cy, text=r, fill=col, font=T.F_FACE_LETTER, tags=tags)
        canvas.create_text(cx, y + h * 0.3, text=sym, fill=col,
                           font=T.F_FACE_SUIT, tags=tags)
        canvas.create_text(cx, y + h * 0.7, text=sym, fill=col,
                           font=T.F_FACE_SUIT, angle=180, tags=tags)
    else:                                               
        for fx, fy in PIPS[card.rank]:
            canvas.create_text(x + w * fx, y + h * fy, text=sym, fill=col,
                               font=T.F_PIP, angle=180 if fy > 0.5 else 0, tags=tags)


def draw_back(canvas, x, y, tags=("card",)):
    """Draw a face-down card (blue lattice pattern)."""
    s, w, h = T.S, T.CARD_W, T.CARD_H
    rounded_rect(canvas, x + 2 * s, y + 3 * s, x + w + 2 * s, y + h + 3 * s,
                 fill=T.SHADOW, outline="", tags=tags)
    rounded_rect(canvas, x, y, x + w, y + h,
                 fill=T.BACK_OUTER, outline=T.CARD_EDGE, width=1, tags=tags)
    m = 6 * s
    ix1, iy1, ix2, iy2 = x + m, y + m, x + w - m, y + h - m
    rounded_rect(canvas, ix1, iy1, ix2, iy2, 6 * s,
                 fill=T.BACK_BLUE, outline=T.BACK_EDGE, width=2, tags=tags)
    step, r = 13 * s, 4 * s
    row = 0
    gy = iy1 + 12 * s
    while gy < iy2 - 10 * s:
        gx = ix1 + 12 * s + (step / 2 if row % 2 else 0)
        while gx < ix2 - 10 * s:
            canvas.create_polygon(gx, gy - r, gx + r, gy, gx, gy + r, gx - r, gy,
                                  fill=T.BACK_PATTERN, outline="", tags=tags)
            gx += step
        gy += step * 0.8
        row += 1


def draw_slot(canvas, x, y, text="", tags=("slot",)):
    """Empty pile placeholder (dashed outline + optional faint symbol)."""
    w, h = T.CARD_W, T.CARD_H
    rounded_rect(canvas, x, y, x + w, y + h, fill=T.SLOT_FILL,
                 outline=T.SLOT_EDGE, width=2, dash=(5, 4), tags=tags)
    if text:
        canvas.create_text(x + w / 2, y + h / 2, text=text, fill=T.SLOT_TEXT,
                           font=T.F_SLOT, tags=tags)


def draw_highlight(canvas, x1, y1, x2, y2, tags=("hl",)):
    """Golden glow used by the hint system."""
    s = T.S
    rounded_rect(canvas, x1 - 4 * s, y1 - 4 * s, x2 + 4 * s, y2 + 4 * s, 11 * s,
                 fill="", outline=T.GOLD, width=max(3, 4 * s), tags=tags)
    rounded_rect(canvas, x1 - s, y1 - s, x2 + s, y2 + s, 9 * s,
                 fill="", outline="#fff3b0", width=1, tags=tags)
