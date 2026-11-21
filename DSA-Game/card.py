
import random

SUITS = ("S", "H", "D", "C")
SYMBOLS = {"S": "\u2660", "H": "\u2665", "D": "\u2666", "C": "\u2663"}
RANK_NAMES = {1: "A", 11: "J", 12: "Q", 13: "K"}


def rank_name(rank):
    return RANK_NAMES.get(rank, str(rank))


class Card:
    def __init__(self, suit, rank, face_up=False):
        self.suit = suit
        self.rank = rank
        self.face_up = face_up

    @property
    def color(self):
        return "red" if self.suit in ("H", "D") else "black"

    @property
    def key(self):
        return (self.suit, self.rank)

    def label(self):
        return f"{rank_name(self.rank)}{SYMBOLS[self.suit]}"

    def __repr__(self):
        return self.label() if self.face_up else "##"


class Deck:
    """Array/list of 52 cards."""

    def __init__(self, rng=None):
        self.cards = [Card(s, r) for s in SUITS for r in range(1, 14)]
        self.rng = rng or random.Random()

    def shuffle(self):
   
        for i in range(len(self.cards) - 1, 0, -1):
            j = self.rng.randint(0, i)
            self.cards[i], self.cards[j] = self.cards[j], self.cards[i]

    def deal(self):
        return self.cards.pop()

    def __len__(self):
        return len(self.cards)
