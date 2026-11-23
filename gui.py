# gui.py  -  graphical interface for Klondike Solitaire (Phase 4, optional)
# Run with:  python gui.py
#
# How to play:
#   * Click the stockpile (top-left) to draw.
#   * Click a face-up card (or a run of cards) to select it, then click
#     the pile or foundation where it should go.
#   * Double-click a card to send it to the foundation.
#   * Click an empty pile slot to move a King there.
import tkinter as tk
from tkinter import messagebox

from cards import SUITS, SYMBOLS, RANK_NAMES
from game import Game

CARD_W = 80
CARD_H = 112
GAP = 20
LEFT = 20
TOP_Y = 15
TABLEAU_Y = 170
STEP_DOWN = 16            # vertical space a face-down card shows
STEP_UP = 28              # vertical space a face-up card shows
CANVAS_W = 2 * LEFT + 7 * CARD_W + 6 * GAP
CANVAS_H = 700

TABLE_GREEN = "#0b6623"
RED = "#c0392b"
BACK_BLUE = "#1f3a93"


class SolitaireGUI:
    def __init__(self, root, draw_count):
        self.root = root
        self.root.title("Klondike Solitaire - CSC200")
        self.game = Game(draw_count)
        self.selected = None      # ("tableau", pile, pos) / ("waste", None, None) / ("foundation", suit, None)
        self.regions = []         # clickable rectangles, rebuilt on every refresh
        self.won = False

        bar = tk.Frame(root)
        bar.pack(fill="x", padx=6, pady=4)
        tk.Button(bar, text="New Game", command=self.new_game).pack(side="left", padx=2)
        tk.Button(bar, text="Undo", command=self.undo).pack(side="left", padx=2)
        tk.Button(bar, text="Redo", command=self.redo).pack(side="left", padx=2)
        tk.Button(bar, text="Hint", command=self.hint).pack(side="left", padx=2)
        self.info = tk.Label(bar, text="", font=("Arial", 11))
        self.info.pack(side="right", padx=6)

        self.canvas = tk.Canvas(root, width=CANVAS_W, height=CANVAS_H,
                                bg=TABLE_GREEN, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)

        self.status = tk.Label(root, text="Click the stockpile to draw, or select a card to move it.",
                               anchor="w", font=("Arial", 11))
        self.status.pack(fill="x", padx=6, pady=4)

        self.refresh()
        self.tick()

    # ------------------------------------------------------------ drawing
    def col_x(self, column):
        return LEFT + column * (CARD_W + GAP)

    def set_status(self, text):
        self.status.config(text=text)

    def update_info(self):
        g = self.game
        self.info.config(text="Moves: %d    Score: %d    Time: %s    Draw: %d" % (
            g.moves, g.score, g.elapsed_time(), g.draw_count))

    def tick(self):
        if not self.won:
            self.update_info()
        self.root.after(1000, self.tick)

    def draw_card(self, x, y, card, selected=False):
        outline = "gold" if selected else "black"
        width = 4 if selected else 2
        if card.face_up:
            colour = RED if card.color == "red" else "black"
            self.canvas.create_rectangle(x, y, x + CARD_W, y + CARD_H,
                                         fill="white", outline=outline, width=width)
            label = RANK_NAMES.get(card.rank, str(card.rank)) + SYMBOLS[card.suit]
            self.canvas.create_text(x + 6, y + 5, text=label, anchor="nw",
                                    fill=colour, font=("Arial", 13, "bold"))
            self.canvas.create_text(x + CARD_W / 2, y + CARD_H / 2 + 8,
                                    text=SYMBOLS[card.suit], fill=colour, font=("Arial", 34))
        else:
            self.canvas.create_rectangle(x, y, x + CARD_W, y + CARD_H,
                                         fill=BACK_BLUE, outline="white", width=2)
            self.canvas.create_rectangle(x + 6, y + 6, x + CARD_W - 6, y + CARD_H - 6,
                                         outline="#8fa8e8", width=1)

    def draw_slot(self, x, y, text=""):
        self.canvas.create_rectangle(x, y, x + CARD_W, y + CARD_H,
                                     outline="#7fbf8f", width=2, dash=(4, 4))
        if text:
            self.canvas.create_text(x + CARD_W / 2, y + CARD_H / 2, text=text,
                                    fill="#7fbf8f", font=("Arial", 30))

    def draw_top_row(self):
        g = self.game

        # stockpile (Queue)
        x = self.col_x(0)
        if g.stock.is_empty():
            self.draw_slot(x, TOP_Y, "\u21bb" if not g.waste.is_empty() else "")
        else:
            self.draw_card(x, TOP_Y, g.stock.peek())
        self.regions.append((x, TOP_Y, x + CARD_W, TOP_Y + CARD_H, "stock", None, None))
        self.canvas.create_text(x + CARD_W / 2, TOP_Y + CARD_H + 12,
                                text="%d cards" % g.stock.size(), fill="white", font=("Arial", 10))

        # waste pile (Stack): show up to draw_count cards fanned out
        waste_cards = g.waste.to_list()[-g.draw_count:]
        if not waste_cards:
            self.draw_slot(self.col_x(1), TOP_Y)
        for k, card in enumerate(waste_cards):
            wx = self.col_x(1) + k * 22
            is_top = (k == len(waste_cards) - 1)
            self.draw_card(wx, TOP_Y, card, is_top and self.selected == ("waste", None, None))
            self.regions.append((wx, TOP_Y, wx + CARD_W, TOP_Y + CARD_H, "waste", None, None))

        # four foundation piles (Stacks)
        for k, suit in enumerate(SUITS):
            fx = self.col_x(3 + k)
            top = g.foundation[suit].peek()
            if top is None:
                self.draw_slot(fx, TOP_Y, SYMBOLS[suit])
            else:
                self.draw_card(fx, TOP_Y, top, self.selected == ("foundation", suit, None))
            self.regions.append((fx, TOP_Y, fx + CARD_W, TOP_Y + CARD_H, "foundation", suit, None))

    def draw_tableau(self):
        for i, pile in enumerate(self.game.tableau):       # Linked lists
            x = self.col_x(i)
            cards = pile.to_list()
            if not cards:
                self.draw_slot(x, TABLEAU_Y, "K")
                self.regions.append((x, TABLEAU_Y, x + CARD_W, TABLEAU_Y + CARD_H, "empty", i, None))
                continue

            steps = [STEP_UP if c.face_up else STEP_DOWN for c in cards[:-1]]
            room = CANVAS_H - 10 - TABLEAU_Y - CARD_H      # shrink very tall piles to fit
            total = sum(steps)
            scale = 1.0 if total <= room else room / total

            y = TABLEAU_Y
            for pos, card in enumerate(cards):
                chosen = (self.selected is not None and self.selected[0] == "tableau"
                          and self.selected[1] == i and pos >= self.selected[2])
                self.draw_card(x, y, card, chosen)
                self.regions.append((x, y, x + CARD_W, y + CARD_H, "tableau", i, pos))
                if pos < len(steps):
                    y += steps[pos] * scale

    def refresh(self):
        self.canvas.delete("all")
        self.regions = []
        self.draw_top_row()
        self.draw_tableau()
        self.update_info()

    # ------------------------------------------------------------ clicking
    def find_region(self, x, y):
        # later regions are drawn on top, so search from the end
        for region in reversed(self.regions):
            if region[0] <= x <= region[2] and region[1] <= y <= region[3]:
                return region
        return None

    def finish(self, ok, message):
        self.selected = None
        self.set_status(message)
        self.refresh()
        if self.game.is_won():
            self.show_win()

    def try_select(self, kind, a, b):
        g = self.game
        if kind == "tableau":
            card = g.tableau[a].to_list()[b]
            if card.face_up:
                self.selected = ("tableau", a, b)
            else:
                self.set_status("That card is face down.")
        elif kind == "waste":
            self.selected = ("waste", None, None)
        elif kind == "foundation":
            if not g.foundation[a].is_empty():
                self.selected = ("foundation", a, None)
        self.refresh()

    def move_to_tableau(self, src, dst):
        g = self.game
        if src[0] == "tableau":
            count = g.tableau[src[1]].size() - src[2]
            return g.move_tableau_to_tableau(src[1], dst, count)
        if src[0] == "waste":
            return g.move_waste_to_tableau(dst)
        return g.move_foundation_to_tableau(src[1], dst)

    def move_to_foundation(self, src):
        g = self.game
        if src[0] == "tableau":
            if src[2] != g.tableau[src[1]].size() - 1:
                return False, "Only the top card of a pile can go to the foundation."
            return g.move_tableau_to_foundation(src[1])
        if src[0] == "waste":
            return g.move_waste_to_foundation()
        return False, "That card is already on the foundation."

    def on_click(self, event):
        if self.won:
            return
        region = self.find_region(event.x, event.y)
        if region is None:
            self.selected = None
            self.refresh()
            return
        kind, a, b = region[4], region[5], region[6]

        if kind == "stock":
            self.finish(*self.game.draw_from_stock())
            return

        if self.selected is None:
            self.try_select(kind, a, b)
            return

        src = self.selected
        if kind == "tableau" and src[0] == "tableau" and src[1] == a:
            # clicked inside the pile we already selected from
            if b != src[2] and self.game.tableau[a].to_list()[b].face_up:
                self.selected = ("tableau", a, b)
            else:
                self.selected = None
            self.refresh()
            return
        if kind == "waste":
            self.selected = None if src[0] == "waste" else ("waste", None, None)
            self.refresh()
            return
        if kind in ("tableau", "empty"):
            self.finish(*self.move_to_tableau(src, a))
        elif kind == "foundation":
            self.finish(*self.move_to_foundation(src))

    def on_double_click(self, event):
        if self.won:
            return
        region = self.find_region(event.x, event.y)
        if region is None:
            return
        kind, a, b = region[4], region[5], region[6]
        if kind == "tableau":
            self.finish(*self.move_to_foundation(("tableau", a, b)))
        elif kind == "waste":
            self.finish(*self.game.move_waste_to_foundation())

    # ------------------------------------------------------------ buttons
    def undo(self):
        self.finish(*self.game.undo())

    def redo(self):
        self.finish(*self.game.redo())

    def hint(self):
        text = self.game.get_hint().split(":  ")[0]    # drop the console command
        self.set_status("Hint: " + text)

    def new_game(self):
        draw3 = messagebox.askyesno("New game", "Draw 3 cards at a time?\n\nYes = draw 3, No = draw 1",
                                    parent=self.root)
        self.game.draw_count = 3 if draw3 else 1
        self.game.new_game()
        self.won = False
        self.selected = None
        self.set_status("New game started.")
        self.refresh()

    def show_win(self):
        self.won = True
        self.update_info()
        g = self.game
        messagebox.showinfo("You win!", "Moves: %d\nScore: %d\nTime: %s" % (
            g.moves, g.score, g.elapsed_time()), parent=self.root)
        if messagebox.askyesno("Play again?", "Start a new game?", parent=self.root):
            self.new_game()


def main():
    root = tk.Tk()
    draw3 = messagebox.askyesno("Draw mode", "Draw 3 cards at a time?\n\nYes = draw 3, No = draw 1",
                                parent=root)
    SolitaireGUI(root, 3 if draw3 else 1)
    root.mainloop()


if __name__ == "__main__":
    main()
