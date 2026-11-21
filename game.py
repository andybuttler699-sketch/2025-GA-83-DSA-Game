
import random
import time

from card import Card, Deck, SUITS
from structures import Stack, Queue, TableauPile


class Game:
    def __init__(self, draw_count=1, seed=None):
        if draw_count not in (1, 3):
            raise ValueError("draw_count must be 1 or 3")
        self.draw_count = draw_count
        self.rng = random.Random(seed)
        self.new_game()


    def new_game(self):
        deck = Deck(self.rng)
        deck.shuffle()
        self.tableau = {i: TableauPile() for i in range(1, 8)}
        self.foundation = {s: Stack() for s in SUITS}
        self.stock = Queue()
        self.waste = Stack()
        self.where = {}               
        self.undo_stack = Stack()
        self.redo_stack = Stack()
        self.score = 0
        self.start_time = time.time()
        self.end_time = None

        for i in range(1, 8):          
            for j in range(i):
                c = deck.deal()
                c.face_up = (j == i - 1)
                self.tableau[i].push(c)
                self.where[c.key] = f"T{i}"
        while len(deck):               
            c = deck.deal()
            c.face_up = False
            self.stock.enqueue(c)
            self.where[c.key] = "STOCK"


    @staticmethod
    def _label(loc):
        if loc[0] == "W":
            return "WASTE"
        if loc[0] == "F":
            return f"F-{loc[1]}"
        return f"T{loc[1]}"

    def _take(self, loc, n):
        if loc[0] == "W":
            return [self.waste.pop()]
        if loc[0] == "F":
            return [self.foundation[loc[1]].pop()]
        return self.tableau[loc[1]].detach_last(n)

    def _put(self, loc, cards):
        label = self._label(loc)
        for c in cards:
            if loc[0] == "W":
                c.face_up = True
                self.waste.push(c)
            elif loc[0] == "F":
                c.face_up = True
                self.foundation[loc[1]].push(c)
            else:
                self.tableau[loc[1]].push(c)
            self.where[c.key] = label

    def cards_at(self, loc, n=1):
        """The cards that a move from loc with n cards would pick up."""
        if loc[0] == "W":
            return [self.waste.peek()]
        if loc[0] == "F":
            return [self.foundation[loc[1]].peek()]
        return self.tableau[loc[1]].last_n(n)

    @staticmethod
    def _is_sequence(cards):
        for a, b in zip(cards, cards[1:]):
            if a.color == b.color or a.rank != b.rank + 1:
                return False
        return True

    def _validate(self, src, dst, n):
        """Returns (error_message_or_None, cards, normalised_dst)."""

        if src[0] == "W":
            if self.waste.is_empty():
                return "Waste pile is empty.", None, dst
            if n != 1:
                return "Only one card can be moved from the waste.", None, dst
            cards = [self.waste.peek()]
        elif src[0] == "F":
            stack = self.foundation[src[1]]
            if stack.is_empty():
                return "That foundation pile is empty.", None, dst
            if n != 1:
                return "Only one card can be moved from a foundation.", None, dst
            cards = [stack.peek()]
        else:
            pile = self.tableau[src[1]]
            if n < 1 or n > pile.size:
                return "Invalid number of cards for that pile.", None, dst
            cards = pile.last_n(n)
            if not all(c.face_up for c in cards):
                return "Face-down cards cannot be moved.", None, dst
            if not self._is_sequence(cards):
                return "Cards must be in alternating colors and descending rank.", None, dst

  
        if dst[0] == "F":
            if src[0] == "F":
                return "Cannot move from foundation to foundation.", None, dst
            if len(cards) != 1:
                return "Only one card at a time goes to the foundation.", None, dst
            card = cards[0]
            dst = ("F", card.suit)
            stack = self.foundation[card.suit]
            if stack.is_empty():
                if card.rank != 1:
                    return "Only an Ace can start a foundation.", None, dst
            elif stack.peek().rank + 1 != card.rank:
                return "Foundation needs the next rank of the same suit.", None, dst
        else:
            if src == dst:
                return "Source and destination are the same.", None, dst
            pile = self.tableau[dst[1]]
            base = cards[0]
            if pile.size == 0:
                if base.rank != 13:
                    return "Only a King can go on an empty column.", None, dst
            else:
                top = pile.peek()
                if top.color == base.color or top.rank != base.rank + 1:
                    return "Must be placed on opposite color, one rank higher.", None, dst
        return None, cards, dst


    def _apply(self, m):
        t = m["type"]
        if t == "DRAW":
            for _ in range(m["n"]):
                c = self.stock.dequeue()
                c.face_up = True
                self.waste.push(c)
                self.where[c.key] = "WASTE"
        elif t == "RECYCLE":
            for c in self.waste.items():         
                c.face_up = False
                self.stock.enqueue(c)
                self.where[c.key] = "STOCK"
            self.waste.clear()
        else:
            src, dst = m["src"], m["dst"]
            self._put(dst, self._take(src, m["n"]))
            delta = 0
            if dst[0] == "F":
                delta += 10
            elif src[0] == "W":
                delta += 5
            if src[0] == "F":
                delta -= 15
            m["flip"] = False
            if src[0] == "T":                 
                pile = self.tableau[src[1]]
                if pile.size and not pile.peek().face_up:
                    pile.peek().face_up = True
                    m["flip"] = True
                    delta += 5
            m["delta"] = delta
        self.score += m["delta"]

    def _revert(self, m):
        t = m["type"]
        if t == "DRAW":
            for _ in range(m["n"]):
                c = self.waste.pop()
                c.face_up = False
                self.stock.push_front(c)
                self.where[c.key] = "STOCK"
        elif t == "RECYCLE":
            while not self.stock.is_empty():
                c = self.stock.dequeue()
                c.face_up = True
                self.waste.push(c)
                self.where[c.key] = "WASTE"
        else:
            src, dst = m["src"], m["dst"]
            if m["flip"]:
                self.tableau[src[1]].peek().face_up = False
            self._put(src, self._take(dst, m["n"]))
        self.score -= m["delta"]

    def draw(self):
        if self.stock.is_empty() and self.waste.is_empty():
            return False, "No cards left to draw."
        if self.stock.is_empty():
            m = {"type": "RECYCLE", "delta": -20}
        else:
            m = {"type": "DRAW", "n": min(self.draw_count, len(self.stock)), "delta": 0}
        self._apply(m)
        self.undo_stack.push(m)
        self.redo_stack.clear()
        return True, "Waste turned back into stock." if m["type"] == "RECYCLE" else ""

    def move(self, src, dst, n=1):
        err, cards, dst = self._validate(src, dst, n)
        if err:
            return False, err
        m = {"type": "MOVE", "src": src, "dst": dst, "n": len(cards),
             "flip": False, "delta": 0}
        self._apply(m)
        self.undo_stack.push(m)
        self.redo_stack.clear()
        return True, ""

    def undo(self):
        if self.undo_stack.is_empty():
            return False, "Nothing to undo."
        m = self.undo_stack.pop()
        self._revert(m)
        self.redo_stack.push(m)
        return True, ""

    def redo(self):
        if self.redo_stack.is_empty():
            return False, "Nothing to redo."
        m = self.redo_stack.pop()
        self._apply(m)
        self.undo_stack.push(m)
        return True, ""

    def auto_step(self):
        """Move ONE card to the foundation if possible."""
        for src in [("W",)] + [("T", i) for i in range(1, 8)]:
            ok, _ = self.move(src, ("F", None), 1)
            if ok:
                return True
        return False

    def auto_foundation(self):
        count = 0
        while self.auto_step():
            count += 1
        return count


    def is_won(self):
        return all(len(s) == 13 for s in self.foundation.values())

    def check_win(self):
        if self.is_won() and self.end_time is None:
            self.end_time = time.time()
        return self.is_won()

    def seconds(self):
        return int((self.end_time or time.time()) - self.start_time)

    def elapsed(self):
        t = self.seconds()
        return f"{t // 60:02d}:{t % 60:02d}"

    def time_bonus(self):
        return max(0, 700 - self.seconds())

    def final_score(self):
        return self.score + self.time_bonus()

    def find_hint(self):
        """Returns (src, dst, n, text). src == 'DRAW' -> draw from stock,
        src is None -> nothing to do."""
        def check(s, d, n):
            err, _, nd = self._validate(s, d, n)
            return err is None, nd

        if not self.waste.is_empty():
            ok, nd = check(("W",), ("F", None), 1)
            if ok:
                c = self.waste.peek()
                return ("W",), nd, 1, f"move {c.label()} from the waste to the foundation"
        for i in range(1, 8):
            if self.tableau[i].size:
                ok, nd = check(("T", i), ("F", None), 1)
                if ok:
                    c = self.tableau[i].peek()
                    return ("T", i), nd, 1, f"move {c.label()} to the foundation"
        for i in range(1, 8):
            cards = self.tableau[i].cards()
            for idx, c in enumerate(cards):
                if not c.face_up:
                    continue
                n = len(cards) - idx
                for j in range(1, 8):
                    if j == i:
                        continue
                    ok, nd = check(("T", i), ("T", j), n)
                    if not ok:
                        continue
                    reveals = idx > 0 and not cards[idx - 1].face_up
                    empties = idx == 0 and c.rank != 13
                    if reveals or empties:
                        return ("T", i), nd, n, f"move {c.label()} to column {j}"
        if not self.waste.is_empty():
            for j in range(1, 8):
                ok, nd = check(("W",), ("T", j), 1)
                if ok:
                    c = self.waste.peek()
                    return ("W",), nd, 1, f"move {c.label()} from the waste to column {j}"
        if not self.stock.is_empty() or not self.waste.is_empty():
            return "DRAW", None, 0, "draw a card from the stock"
        return None, None, 0, "no moves available - try Undo or New Game"


    def verify(self):
        seen = {}
        for i, pile in self.tableau.items():
            for c in pile.cards():
                seen[c.key] = f"T{i}"
        for s, st in self.foundation.items():
            for c in st.items():
                seen[c.key] = f"F-{s}"
        for c in self.waste.items():
            seen[c.key] = "WASTE"
        for c in self.stock.items():
            seen[c.key] = "STOCK"
        return len(seen) == 52 and seen == self.where
