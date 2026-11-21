"""
gui.py
Phase 4: graphical interface (Tkinter canvas).

Features
  * drag & drop cards (whole sequences from the tableau)
  * double-click a card to fly it to the foundation
  * click the stock to draw, animated snap-back on illegal moves
  * Undo / Redo, Hint (golden glow), Auto-complete, Draw-1 / Draw-3
  * live score, moves and timer, win screen with confetti
Keyboard: Ctrl+Z undo, Ctrl+Y redo, H hint, A auto, N new game, D/Space draw,
          F11 full screen, Esc leave full screen
"""
import random
import tkinter as tk
from tkinter import messagebox

import card_renderer as cr
import theme as T
from card import SUITS, SYMBOLS
from game import Game


class SolitaireApp:
    def __init__(self, root):
        self.root = root
        root.title("Klondike Solitaire  -  CSC200 DSA Mid Term Project")
        root.configure(bg=T.UI_BG)
        root.resizable(True, True)
        root.minsize(640, 520)
        self.fullscreen = False

        self.game = Game(draw_count=1)

        self.items = []          # (card, x, y, loc, n_draggable) in draw order
        self.zones = []          # (loc, drop_rect, last_card_rect)
        self.stock_rect = (0, 0, 0, 0)
        self.drag = None
        self.hidden = set()      # card keys not drawn in their pile (being moved)
        self.hint_keys = set()
        self.hint_dst = None
        self.hint_stock = False
        self._hint_job = None
        self.animating = False
        self.confetti = []
        self._drop_err = ""
        self._lastx = self._lasty = 0

        self._build_toolbar()
        self.status = tk.StringVar(value="Drag cards to move them. Double-click sends a card to the foundation.")
        tk.Label(root, textvariable=self.status, bg=T.UI_BG, fg=T.UI_TEXT,
                 font=T.F_UI, anchor="w", padx=10, pady=5).pack(side="bottom", fill="x")
        self.canvas = tk.Canvas(root, width=T.BASE_W, height=T.BASE_H,
                                bg=T.BG_EDGE, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        c = self.canvas
        c.bind("<ButtonPress-1>", self.on_press)
        c.bind("<B1-Motion>", self.on_drag)
        c.bind("<ButtonRelease-1>", self.on_release)
        c.bind("<Double-Button-1>", self.on_double)
        c.bind("<Motion>", self.on_hover)
        c.bind("<Configure>", self.on_resize)
        root.bind("<Control-z>", lambda e: self.undo())
        root.bind("<Control-y>", lambda e: self.redo())
        root.bind("<h>", lambda e: self.hint())
        root.bind("<a>", lambda e: self.auto())
        root.bind("<n>", lambda e: self.new_game())
        root.bind("<d>", lambda e: self.do_draw())
        root.bind("<space>", lambda e: self.do_draw())
        root.bind("<F11>", lambda e: self.toggle_fullscreen())
        root.bind("<Escape>", lambda e: self.toggle_fullscreen(False))

        self._draw_background()
        self.render()
        self._update_info()
        self._tick()
        try:                                   # start maximised
            root.state("zoomed")
        except tk.TclError:
            try:
                root.attributes("-zoomed", True)
            except tk.TclError:
                pass

    # ------------------------------------------------------------------
    # toolbar / info
    # ------------------------------------------------------------------
    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg=T.UI_BG, pady=7)
        bar.pack(fill="x")

        def button(text, cmd):
            b = tk.Button(bar, text=text, command=cmd, bg=T.BTN, fg="white",
                          activebackground=T.BTN_HOVER, activeforeground="white",
                          disabledforeground=T.BTN_DISABLED, relief="flat", bd=0,
                          padx=12, pady=5, font=T.F_UI, cursor="hand2")
            b.pack(side="left", padx=(8, 0))
            b.bind("<Enter>", lambda e: b["state"] == "normal" and b.config(bg=T.BTN_HOVER))
            b.bind("<Leave>", lambda e: b.config(bg=T.BTN))
            return b

        button("New Game", self.new_game)
        self.undo_btn = button("Undo", self.undo)
        self.redo_btn = button("Redo", self.redo)
        button("Hint", self.hint)
        button("Auto", self.auto)
        self.draw_btn = button("Draw: 1", self.toggle_draw)
        button("Full Screen", self.toggle_fullscreen)

        self.info = tk.Label(bar, text="", bg=T.UI_BG, fg=T.GOLD, font=T.F_INFO)
        self.info.pack(side="right", padx=12)

    def _update_info(self):
        g = self.game
        self.info.config(text=f"Score {g.score}     Moves {len(g.undo_stack)}     Time {g.elapsed()}")
        self.undo_btn.config(state="normal" if len(g.undo_stack) else "disabled")
        self.redo_btn.config(state="normal" if len(g.redo_stack) else "disabled")

    def _set_status(self, text):
        self.status.set(text)

    def _tick(self):
        self._update_info()
        self.root.after(500, self._tick)

    # ------------------------------------------------------------------
    # drawing
    # ------------------------------------------------------------------
    def _draw_background(self):
        """Green felt with a soft radial glow."""
        c = self.canvas
        c.delete("bg")
        cx, cy = T.CANVAS_W / 2, T.CANVAS_H / 2
        steps = 18
        for i in range(steps):
            t = i / (steps - 1)
            rx = T.CANVAS_W * 0.85 * (1 - t) + 60
            ry = T.CANVAS_H * 0.85 * (1 - t) + 60
            c.create_oval(cx - rx, cy - ry, cx + rx, cy + ry,
                          fill=T.blend(T.BG_EDGE, T.BG_CENTER, t), outline="", tags="bg")

    @staticmethod
    def _col_x(col):
        """x position of column 0..6."""
        return T.X0 + T.GAP + col * (T.CARD_W + T.GAP)

    @staticmethod
    def _tableau_y(cards):
        """y position of every card in a tableau column (squeezes if too tall)."""
        n_down = sum(1 for k in cards if not k.face_up)
        n_up = len(cards) - n_down
        fd, fu = T.FACE_DOWN_OFFSET, T.FACE_UP_OFFSET
        avail = T.CANVAS_H - 14 * T.S - T.TABLEAU_Y - T.CARD_H
        need = n_down * fd + max(0, n_up - 1) * fu
        if need > avail and need > 0:
            k = avail / need
            fd, fu = fd * k, fu * k
        ys, y = [], T.TABLEAU_Y
        for card in cards:
            ys.append(y)
            y += fu if card.face_up else fd
        return ys

    def render(self):
        c, g, hidden = self.canvas, self.game, self.hidden
        c.delete("card")
        c.delete("slot")
        c.delete("hl")
        self.items = []
        self.zones = []

        # ---- stock (queue) ----
        sx = self._col_x(0)
        self.stock_rect = (sx, T.TOP, sx + T.CARD_W, T.TOP + T.CARD_H)
        if len(g.stock):
            cr.draw_back(c, sx, T.TOP)
            c.create_text(sx + T.CARD_W / 2, T.TOP + T.CARD_H - 16 * T.S, text=str(len(g.stock)),
                          fill="white", font=T.F_COUNT, tags="card")
        else:
            cr.draw_slot(c, sx, T.TOP, "\u21bb" if len(g.waste) else "")

        # ---- waste (stack) ----
        wx = self._col_x(1)
        cr.draw_slot(c, wx, T.TOP)
        all_w = g.waste.items()
        shown = [k for k in all_w if k.key not in hidden][-g.draw_count:]
        for k, card in enumerate(shown):
            x = wx + k * T.WASTE_FAN
            cr.draw_card(c, card, x, T.TOP)
            is_top = (k == len(shown) - 1 and card is all_w[-1])
            self.items.append((card, x, T.TOP, ("W",), 1 if is_top else 0))

        # ---- foundations (stacks) ----
        for i, s in enumerate(SUITS):
            x = self._col_x(3 + i)
            cr.draw_slot(c, x, T.TOP, SYMBOLS[s])
            rect = (x, T.TOP, x + T.CARD_W, T.TOP + T.CARD_H)
            self.zones.append((("F", s), rect, rect))
            pile = g.foundation[s].items()
            vis = [k for k in pile if k.key not in hidden]
            if vis:
                card = vis[-1]
                cr.draw_card(c, card, x, T.TOP)
                self.items.append((card, x, T.TOP, ("F", s), 1 if card is pile[-1] else 0))

        # ---- tableau (linked lists) ----
        for col in range(1, 8):
            x = self._col_x(col - 1)
            cr.draw_slot(c, x, T.TABLEAU_Y, "K")
            cards = g.tableau[col].cards()
            ys = self._tableau_y(cards)
            last_y = T.TABLEAU_Y
            for idx, (card, y) in enumerate(zip(cards, ys)):
                if card.key in hidden:
                    continue
                if card.face_up:
                    cr.draw_card(c, card, x, y)
                    n = len(cards) - idx if g._is_sequence(cards[idx:]) else 0
                else:
                    cr.draw_back(c, x, y)
                    n = 0
                self.items.append((card, x, y, ("T", col), n))
                last_y = y
            full = (x, T.TABLEAU_Y, x + T.CARD_W, last_y + T.CARD_H)
            last = (x, last_y, x + T.CARD_W, last_y + T.CARD_H)
            self.zones.append((("T", col), full, last))

        # ---- hint glow ----
        if self.hint_stock:
            cr.draw_highlight(c, *self.stock_rect)
        for card, x, y, loc, n in self.items:
            if card.key in self.hint_keys:
                cr.draw_highlight(c, x, y, x + T.CARD_W, y + T.CARD_H)
        if self.hint_dst is not None:
            for loc, full, last in self.zones:
                if loc == self.hint_dst:
                    cr.draw_highlight(c, *last)

    # ------------------------------------------------------------------
    # window size / full screen
    # ------------------------------------------------------------------
    def on_resize(self, e):
        if e.width < 100 or e.height < 100:
            return
        if (e.width, e.height) == (T.CANVAS_W, T.CANVAS_H):
            return
        T.set_layout(e.width, e.height)
        self._draw_background()
        self.canvas.tag_lower("bg")
        if not self.drag:
            self.render()
        if self.game.is_won():
            self.canvas.delete("overlay")
            self._draw_overlay()

    def toggle_fullscreen(self, state=None):
        self.fullscreen = (not self.fullscreen) if state is None else state
        self.root.attributes("-fullscreen", self.fullscreen)

    # ------------------------------------------------------------------
    # mouse handling
    # ------------------------------------------------------------------
    def _entry_at(self, x, y):
        for entry in reversed(self.items):
            _, cx, cy, _, _ = entry
            if cx <= x <= cx + T.CARD_W and cy <= y <= cy + T.CARD_H:
                return entry
        return None

    @staticmethod
    def _inside(rect, x, y):
        return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]

    def on_hover(self, e):
        if self.drag:
            return
        entry = self._entry_at(e.x, e.y)
        hand = self._inside(self.stock_rect, e.x, e.y) or (entry is not None and entry[4] > 0)
        self.canvas.config(cursor="hand2" if hand else "")

    def on_press(self, e):
        if self.animating or self.drag or self.game.is_won():
            return
        self._clear_hint()
        if self._inside(self.stock_rect, e.x, e.y):
            self.do_draw()
            return
        entry = self._entry_at(e.x, e.y)
        if entry is None or entry[4] == 0:
            return
        card, cx, cy, loc, n = entry
        cards = self.game.cards_at(loc, n)
        self.drag = {"cards": cards, "loc": loc, "n": n,
                     "x0": cx, "y0": cy, "x": cx, "y": cy, "moved": False}
        self._lastx, self._lasty = e.x, e.y
        self.hidden = {k.key for k in cards}
        self.render()
        for k, cd in enumerate(cards):
            cr.draw_card(self.canvas, cd, cx, cy + k * T.FACE_UP_OFFSET, ("drag",), lift=True)
        self.canvas.tag_raise("drag")

    def on_drag(self, e):
        d = self.drag
        if not d:
            return
        dx, dy = e.x - self._lastx, e.y - self._lasty
        self._lastx, self._lasty = e.x, e.y
        d["x"] += dx
        d["y"] += dy
        if abs(d["x"] - d["x0"]) + abs(d["y"] - d["y0"]) > 4:
            d["moved"] = True
        self.canvas.move("drag", dx, dy)

    def on_release(self, e):
        d = self.drag
        if not d:
            return
        self.drag = None
        if not d["moved"]:                      # just a click
            self.canvas.delete("drag")
            self.hidden = set()
            self.render()
            return
        target = self._find_drop(d)
        if target is not None:
            self.canvas.delete("drag")
            self.hidden = set()
            self.game.move(d["loc"], target, d["n"])
            self.render()
            self._after_action("")
        else:
            def back():
                self.canvas.delete("drag")
                self.hidden = set()
                self.render()
                self._set_status(self._drop_err or "That move is not allowed.")
            self._fly(d["x"], d["y"], d["x0"], d["y0"], back)

    def _find_drop(self, d):
        """Best legal destination under the dragged cards (by overlap area)."""
        x, y, w, h = d["x"], d["y"], T.CARD_W, T.CARD_H
        cands = []
        for loc, zone, _ in self.zones:
            ox = min(x + w, zone[2]) - max(x, zone[0])
            oy = min(y + h, zone[3]) - max(y, zone[1])
            if ox > 0 and oy > 0 and ox * oy > 0.1 * w * h:
                cands.append((ox * oy, loc))
        cands.sort(reverse=True)
        self._drop_err = ""
        for _, loc in cands:
            if loc == d["loc"]:
                continue
            err = self.game._validate(d["loc"], loc, d["n"])[0]
            if err is None:
                return loc
            if not self._drop_err:
                self._drop_err = err
        return None

    def on_double(self, e):
        """Double-click: fly the card to its foundation pile."""
        if self.animating or self.game.is_won():
            return
        entry = self._entry_at(e.x, e.y)
        if entry is None:
            return
        card, cx, cy, loc, n = entry
        if loc[0] == "F" or n != 1:
            return
        err, _, dst = self.game._validate(loc, ("F", None), 1)
        if err:
            self._set_status(err)
            return
        self._clear_hint()
        self.hidden = {card.key}
        self.render()
        cr.draw_card(self.canvas, card, cx, cy, ("drag",), lift=True)
        self.canvas.tag_raise("drag")
        tx = self._col_x(3 + SUITS.index(dst[1]))

        def done():
            self.canvas.delete("drag")
            self.hidden = set()
            self.game.move(loc, ("F", None), 1)
            self.render()
            self._after_action("")
        self._fly(cx, cy, tx, T.TOP, done)

    # ------------------------------------------------------------------
    # animation
    # ------------------------------------------------------------------
    def _fly(self, x0, y0, tx, ty, done, steps=12):
        """Slide everything tagged 'drag' from (x0,y0) to (tx,ty), ease-out."""
        self.animating = True
        pos = {"x": x0, "y": y0}

        def step(i):
            f = 1 - (1 - i / steps) ** 3
            nx, ny = x0 + (tx - x0) * f, y0 + (ty - y0) * f
            self.canvas.move("drag", nx - pos["x"], ny - pos["y"])
            pos["x"], pos["y"] = nx, ny
            if i < steps:
                self.root.after(14, step, i + 1)
            else:
                self.animating = False
                done()
        step(1)

    # ------------------------------------------------------------------
    # actions (buttons / keys)
    # ------------------------------------------------------------------
    def _after_action(self, msg):
        self._update_info()
        self._set_status(msg)
        if self.game.check_win():
            self._on_win()

    def _busy(self):
        return self.animating or self.drag is not None

    def do_draw(self):
        if self._busy() or self.game.is_won():
            return
        self._clear_hint()
        ok, msg = self.game.draw()
        self.render()
        self._after_action(msg)

    def undo(self):
        if self._busy() or self.game.is_won():
            return
        self._clear_hint()
        ok, msg = self.game.undo()
        self.render()
        self._after_action(msg)

    def redo(self):
        if self._busy() or self.game.is_won():
            return
        self._clear_hint()
        ok, msg = self.game.redo()
        self.render()
        self._after_action(msg)

    def hint(self):
        if self._busy() or self.game.is_won():
            return
        self._clear_hint()
        src, dst, n, text = self.game.find_hint()
        if src == "DRAW":
            self.hint_stock = True
        elif src is not None:
            self.hint_keys = {k.key for k in self.game.cards_at(src, n)}
            self.hint_dst = dst
        self._set_status("Hint: " + text)
        self.render()
        self._hint_job = self.root.after(3000, self._clear_hint)

    def _clear_hint(self):
        if self._hint_job is not None:
            self.root.after_cancel(self._hint_job)
            self._hint_job = None
        if self.hint_keys or self.hint_dst is not None or self.hint_stock:
            self.hint_keys, self.hint_dst, self.hint_stock = set(), None, False
            if not self.drag:
                self.render()

    def auto(self):
        if self._busy() or self.game.is_won():
            return
        self._clear_hint()
        self.animating = True
        self._auto_loop(True)

    def _auto_loop(self, first=False):
        if self.game.auto_step():
            self.render()
            self._update_info()
            self._set_status("")
            if self.game.check_win():
                self.animating = False
                self._on_win()
                return
            self.root.after(110, self._auto_loop)
        else:
            self.animating = False
            if first:
                self._set_status("No card can go to the foundation right now.")

    def toggle_draw(self):
        if self._busy():
            return
        g = self.game
        if len(g.undo_stack) and not g.is_won():
            if not messagebox.askyesno("Change mode",
                                       "Changing the draw mode starts a new game. Continue?"):
                return
        g.draw_count = 3 if g.draw_count == 1 else 1
        self.draw_btn.config(text=f"Draw: {g.draw_count}")
        self.new_game(ask=False)

    def new_game(self, ask=True):
        if self._busy():
            return
        g = self.game
        if ask and len(g.undo_stack) and not g.is_won():
            if not messagebox.askyesno("New game", "Abandon the current game?"):
                return
        self._stop_win()
        self._clear_hint()
        g.new_game()
        self.hidden = set()
        self.render()
        self._update_info()
        self._set_status("New game - good luck!")

    # ------------------------------------------------------------------
    # win screen
    # ------------------------------------------------------------------
    def _on_win(self):
        self._set_status("Congratulations - you won!  Press N for a new game.")
        self._clear_hint()
        self._draw_overlay()
        palette = ["#ff5252", "#ffd54a", "#4fc3f7", "#81c784", "#ba68c8", "#ffffff"]
        self.confetti = [{"x": random.uniform(0, T.CANVAS_W),
                          "y": random.uniform(-T.CANVAS_H, 0),
                          "vx": random.uniform(-1, 1), "vy": random.uniform(2, 5),
                          "w": random.randint(5, 10), "h": random.randint(8, 14),
                          "color": random.choice(palette)} for _ in range(150)]
        self._confetti_step()

    def _draw_overlay(self):
        g, c, s = self.game, self.canvas, T.S
        cx, cy = T.CANVAS_W / 2, T.CANVAS_H / 2
        cr.rounded_rect(c, cx - 240 * s, cy - 115 * s, cx + 240 * s, cy + 115 * s, 26 * s,
                        fill="#0f2a1b", outline=T.GOLD, width=4, tags="overlay")
        c.create_text(cx, cy - 58 * s, text="YOU WIN!", fill=T.GOLD,
                      font=T.font("Georgia", 54, "bold"), tags="overlay")
        c.create_text(cx, cy + 2 * s, fill="white", font=T.font("Segoe UI", 17, "bold"),
                      tags="overlay", text=f"Score {g.score}  +  time bonus {g.time_bonus()}")
        c.create_text(cx, cy + 32 * s, fill=T.GOLD, font=T.font("Segoe UI", 22, "bold"),
                      tags="overlay", text=f"Final score: {g.final_score()}")
        c.create_text(cx, cy + 68 * s, fill="#b9d8c4", font=T.font("Segoe UI", 14),
                      tags="overlay",
                      text=f"{len(g.undo_stack)} moves   |   {g.elapsed()}   |   press N for a new game")
        c.tag_raise("overlay")

    def _confetti_step(self):
        if not self.confetti:
            return
        c = self.canvas
        c.delete("confetti")
        for p in self.confetti:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vx"] += random.uniform(-0.15, 0.15)
            if p["y"] > T.CANVAS_H + 10:
                p["y"] = -12
                p["x"] = random.uniform(0, T.CANVAS_W)
            c.create_rectangle(p["x"], p["y"], p["x"] + p["w"], p["y"] + p["h"],
                               fill=p["color"], outline="", tags="confetti")
        c.tag_raise("overlay")
        self.root.after(33, self._confetti_step)

    def _stop_win(self):
        self.confetti = []
        self.canvas.delete("confetti")
        self.canvas.delete("overlay")