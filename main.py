# main.py  -  text interface (Phase 4)
from game import Game
from cards import SUITS, SYMBOLS

LETTER_TO_SUIT = {"h": "Hearts", "d": "Diamonds", "c": "Clubs", "s": "Spades"}
RANK_LETTERS = {"a": 1, "j": 11, "q": 12, "k": 13}

HELP = """
Commands (piles are numbered 1-7)
  d              draw from the stockpile
  m A B [N]      move N cards (default 1) from pile A to pile B
  w B            move the top waste card to pile B
  f A            move the top card of pile A to the foundation
  fw             move the top waste card to the foundation
  b X B          move foundation card back to pile B (X = h, d, c or s)
  x RANKSUIT     find where a card is (e.g. x 7h, x qs, x ad)
  u / r          undo / redo
  h              hint
  n              new game
  ?              show this help
  q              quit
"""


def show_board(game):
    print("\n" + "=" * 54)
    print("Moves: %d   Score: %d   Time: %s" % (game.moves, game.score, game.elapsed_time()))

    waste_cards = game.waste.to_list()[-game.draw_count:]
    waste_text = " ".join(str(c) for c in waste_cards) if waste_cards else "(empty)"
    print("Stock: %d card(s)    Waste: %s" % (game.stock.size(), waste_text))

    parts = []
    for suit in SUITS:
        top = game.foundation[suit].peek()
        parts.append("%s %s" % (SYMBOLS[suit], str(top) if top else "--"))
    print("Foundation:  " + "   ".join(parts))
    print("-" * 54)

    columns = [pile.to_list() for pile in game.tableau]
    print("".join(("  %d" % (i + 1)).ljust(7) for i in range(7)))
    tallest = max(max(len(c) for c in columns), 1)
    for row in range(tallest):
        line = ""
        for col in columns:
            if row < len(col):
                text = str(col[row])
            elif row == 0:
                text = "[ ]"
            else:
                text = ""
            line += ("  " + text).ljust(7)
        print(line)
    print("=" * 54)


def parse_pile(text):
    number = int(text)
    if number < 1 or number > 7:
        raise ValueError
    return number - 1


def handle(game, cmd, args):
    if cmd == "d":
        return game.draw_from_stock()
    if cmd == "m":
        if len(args) < 2:
            return False, "Usage: m FROM TO [COUNT]"
        count = int(args[2]) if len(args) > 2 else 1
        return game.move_tableau_to_tableau(parse_pile(args[0]), parse_pile(args[1]), count)
    if cmd == "w":
        return game.move_waste_to_tableau(parse_pile(args[0]))
    if cmd == "f":
        return game.move_tableau_to_foundation(parse_pile(args[0]))
    if cmd == "fw":
        return game.move_waste_to_foundation()
    if cmd == "b":
        if len(args) < 2 or args[0] not in LETTER_TO_SUIT:
            return False, "Usage: b h|d|c|s PILE"
        return game.move_foundation_to_tableau(LETTER_TO_SUIT[args[0]], parse_pile(args[1]))
    if cmd == "x":
        if not args:
            return False, "Usage: x RANKSUIT (e.g. x 7h, x qs, x ad)"
        text = args[0].lower()
        rank = RANK_LETTERS.get(text[:-1])
        if rank is None and text[:-1].isdigit():
            rank = int(text[:-1])
        if rank is None or not 1 <= rank <= 13 or text[-1] not in LETTER_TO_SUIT:
            return False, "Usage: x RANKSUIT (e.g. x 7h, x qs, x ad)"
        return True, game.locate(rank, LETTER_TO_SUIT[text[-1]])
    if cmd == "u":
        return game.undo()
    if cmd == "r":
        return game.redo()
    if cmd == "h":
        return True, "Hint: " + game.get_hint()
    return False, "Unknown command. Type ? for help."


def ask_draw_count():
    choice = input("Draw 1 or 3 cards at a time? (1/3): ").strip()
    return 3 if choice == "3" else 1


BANNER = """
======================================================
        KLONDIKE SOLITAIRE  -  Card Game
        CSC200  |  Data Structures & Algorithms
======================================================
"""


def main():
    print(BANNER)
    game = Game(ask_draw_count())
    print(HELP)
    while True:
        show_board(game)
        if game.is_won():
            print("YOU WIN!  Moves: %d  Score: %d  Time: %s" % (game.moves, game.score, game.elapsed_time()))
            break
        try:
            raw = input("> ").strip().lower().split()
        except (EOFError, KeyboardInterrupt):
            print()
            print("Bye!")
            break
        if not raw:
            continue
        cmd, args = raw[0], raw[1:]
        if cmd == "q":
            print("Bye!")
            break
        if cmd == "?":
            print(HELP)
            continue
        if cmd == "n":
            game = Game(ask_draw_count())
            continue
        try:
            ok, message = handle(game, cmd, args)
        except (ValueError, IndexError):
            ok, message = False, "Invalid input. Type ? for help."
        print(message)


if __name__ == "__main__":
    main()