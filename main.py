"""
main.py  -  START HERE (set this as the Startup File in Visual Studio)
"""
import tkinter as tk

from gui import SolitaireApp


def main():
    root = tk.Tk()
    SolitaireApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()