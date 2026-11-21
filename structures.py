"""
structures.py
Basic data structures used by the game:
  Stack        (LIFO)        -> foundation piles, waste pile, undo / redo
  Queue        (FIFO)        -> stock pile
  TableauPile  (linked list) -> the 7 tableau columns
"""
from collections import deque


class Stack:
    """LIFO stack."""

    def __init__(self):
        self._data = []

    def push(self, item):
        self._data.append(item)

    def pop(self):
        return self._data.pop()

    def peek(self):
        return self._data[-1]

    def is_empty(self):
        return not self._data

    def clear(self):
        self._data.clear()

    def items(self):
        """Copy of the contents, bottom -> top."""
        return list(self._data)

    def __len__(self):
        return len(self._data)


class Queue:
    """FIFO queue (stock pile)."""

    def __init__(self):
        self._data = deque()

    def enqueue(self, item):
        self._data.append(item)

    def dequeue(self):
        return self._data.popleft()

    def push_front(self, item):
        """Put a card back at the front (needed only for undo)."""
        self._data.appendleft(item)

    def is_empty(self):
        return not self._data

    def items(self):
        return list(self._data)

    def __len__(self):
        return len(self._data)


class Node:
    __slots__ = ("card", "next")

    def __init__(self, card):
        self.card = card
        self.next = None


class TableauPile:
    """Singly linked list. head = bottom card, tail = top (playable) card."""

    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def push(self, card):
        node = Node(card)
        if self.tail is None:
            self.head = self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self.size += 1

    def peek(self):
        return self.tail.card if self.tail else None

    def cards(self):
        out, cur = [], self.head
        while cur:
            out.append(cur.card)
            cur = cur.next
        return out

    def last_n(self, n):
        return self.cards()[self.size - n:]

    def detach_last(self, n):
        """Cut the last n cards off the list and return them in order."""
        if n == self.size:
            cards = self.cards()
            self.head = self.tail = None
            self.size = 0
            return cards
        prev = self.head
        for _ in range(self.size - n - 1):
            prev = prev.next
        cut = prev.next
        prev.next = None
        self.tail = prev
        cards = []
        while cut:
            cards.append(cut.card)
            cut = cut.next
        self.size -= n
        return cards