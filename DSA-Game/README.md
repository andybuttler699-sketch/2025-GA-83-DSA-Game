# solitaire-python
Solitaire in Python using Stack, Queue, Linked List and Hash Map (CSC200 DSA project)
A fully playable graphical Klondike Solitaire game built for **CSC200 – Data Structures & Algorithms** (Mid Term Project).

## Data Structures Used

| Data structure | Where it is used |
|---|---|
| **Stack (LIFO)** | Foundation piles, waste pile, undo & redo history |
| **Queue (FIFO)** | Stock (draw) pile |
| **Linked List** | Tableau columns |
| **Array / List** | 52-card deck, Fisher-Yates shuffle |
| **Hash Map (Dictionary)** | Tracks the location of every card |

## Features
- Drag & drop cards, double-click to send a card to the foundation
- Move validation (alternating colors, descending ranks, King on empty column)
- Undo / Redo
- Hint system with glowing highlight
- Auto-complete, scoring and timer
- Draw-1 and Draw-3 modes
- Resizable / full-screen UI (F11), win screen with confetti

## How to Run
Requires Python 3 (Tkinter is included).

```bash
git clone https://github.com/andybuttler699-sketch/2025-GA-83-DSA-Game.git
cd 2025-GA-83-DSA-Game
python main.py
```

## Controls
| Action | Control |
|---|---|
| Move cards | Drag & drop |
| Send card to foundation | Double-click |
| Draw from stock | Click the stock pile |
| Undo / Redo | `Ctrl+Z` / `Ctrl+Y` |
| Hint | `H` |
| Auto-complete | `A` |
| New game | `N` |
| Full screen | `F11` (exit with `Esc`) |

## Project Structure
```
structures.py      Stack, Queue, Linked List
card.py            Card and Deck
game.py            Game rules, undo/redo, hints
theme.py           Colors and scaling
card_renderer.py   Card drawing
gui.py             Tkinter interface
main.py            Entry point
```
