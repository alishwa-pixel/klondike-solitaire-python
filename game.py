# game.py  -  Klondike rules, moves, undo/redo, hints, locate, score (Phases 2 and 3)
import time
from cards import Deck, Card, SUITS, RANK_NAMES, SYMBOLS
from structures import Stack, Queue, LinkedList


class Game:
    def __init__(self, draw_count=1):
        self.draw_count = draw_count      # 1 or 3 cards per draw
        self.new_game()

    # ---------------------------------------------------------- setup
    def new_game(self):
        deck = Deck()
        deck.shuffle()

        self.tableau = [LinkedList() for _ in range(7)]       # Linked lists
        self.foundation = {s: Stack() for s in SUITS}          # Stacks
        self.stock = Queue()                                   # Queue
        self.waste = Stack()                                   # Stack
        self.location = {}        # Dictionary: (suit, rank) -> (pile name, index/suit, face_up)
        self.moves = 0
        self.score = 0
        self.start_time = time.time()
        self.undo_stack = Stack()
        self.redo_stack = Stack()

        # deal 1,2,...,7 cards, last card of each pile face up
        for i in range(7):
            for _ in range(i + 1):
                card = deck.draw()
                self.tableau[i].append(card)
                self._set_loc(card, "tableau", i)
            top = self.tableau[i].last()
            top.face_up = True
            self._set_loc(top, "tableau", i)     # refresh: its state changed

        # remaining 24 cards go to the stockpile queue
        while deck.cards:
            card = deck.draw()
            self.stock.enqueue(card)
            self._set_loc(card, "stock", None)

    def _set_loc(self, card, pile, where):
        # the dictionary records the pile AND whether the card is face up or down
        self.location[(card.suit, card.rank)] = (pile, where, card.face_up)

    def _card_name(self, rank, suit):
        return RANK_NAMES.get(rank, str(rank)) + SYMBOLS[suit]

    def locate(self, rank, suit):
        """Dictionary lookup: (suit, rank) -> which pile holds the card.
        The dictionary gives an O(1) jump to the right pile, then one short
        scan inside that pile finds the exact position."""
        spot = self.location.get((suit, rank))
        if spot is None:
            return "That card is not in this game."
        pile, where, face_up = spot
        name = self._card_name(rank, suit)
        if pile == "tableau":
            for pos, card in enumerate(self.tableau[where].to_list(), start=1):
                if card.rank == rank and card.suit == suit:
                    state = "face up" if face_up else "face down"   # state comes from the dictionary
                    return "%s is card %d of tableau pile %d (%s)." % (
                        name, pos, where + 1, state)
        if pile == "foundation":
            return "%s is the top card of the %s foundation pile (card %d of 13)." % (
                name, where, self.foundation[where].size())
        if pile == "stock":
            for pos, card in enumerate(self.stock.to_list(), start=1):
                if card.rank == rank and card.suit == suit:
                    draws_needed = (pos + self.draw_count - 1) // self.draw_count
                    if draws_needed == 1:
                        return "%s is number %d in the stockpile. It is the next card to be drawn." % (
                            name, pos)
                    return "%s is number %d in the stockpile. It comes out after %d more draw(s)." % (
                        name, pos, draws_needed - 1)
        if pile == "waste":
            cards = self.waste.to_list()
            for pos, card in enumerate(cards, start=1):
                if card.rank == rank and card.suit == suit:
                    depth = len(cards) - pos          # cards sitting on top of it
                    if depth == 0:
                        return "%s is on top of the waste pile." % name
                    return "%s is buried %d card(s) deep in the waste pile." % (
                        name, depth)
        return "That card could not be found."

    def elapsed_time(self):
        seconds = int(time.time() - self.start_time)
        return "%02d:%02d" % (seconds // 60, seconds % 60)

    # ---------------------------------------------------------- undo / redo
    def _snapshot(self):
        def pack(cards):
            return [(c.suit, c.rank, c.face_up) for c in cards]
        return {
            "tableau": [pack(p.to_list()) for p in self.tableau],
            "foundation": {s: pack(st.to_list()) for s, st in self.foundation.items()},
            "stock": pack(self.stock.to_list()),
            "waste": pack(self.waste.to_list()),
            "moves": self.moves,
            "score": self.score,
        }

    def _restore(self, snap):
        def unpack(data):
            cards = []
            for suit, rank, face_up in data:
                card = Card(suit, rank)
                card.face_up = face_up
                cards.append(card)
            return cards

        self.location = {}
        self.tableau = []
        for i, pile in enumerate(snap["tableau"]):
            linked = LinkedList()
            for card in unpack(pile):
                linked.append(card)
                self._set_loc(card, "tableau", i)
            self.tableau.append(linked)

        self.foundation = {}
        for suit, data in snap["foundation"].items():
            stack = Stack()
            for card in unpack(data):
                stack.push(card)
                self._set_loc(card, "foundation", suit)
            self.foundation[suit] = stack

        self.stock = Queue()
        for card in unpack(snap["stock"]):
            self.stock.enqueue(card)
            self._set_loc(card, "stock", None)

        self.waste = Stack()
        for card in unpack(snap["waste"]):
            self.waste.push(card)
            self._set_loc(card, "waste", None)

        self.moves = snap["moves"]
        self.score = snap["score"]

    def _save_for_undo(self):
        self.undo_stack.push(self._snapshot())
        self.redo_stack = Stack()         # a new move clears the redo history

    def undo(self):
        if self.undo_stack.is_empty():
            return False, "Nothing to undo."
        self.redo_stack.push(self._snapshot())
        self._restore(self.undo_stack.pop())
        return True, "Move undone."

    def redo(self):
        if self.redo_stack.is_empty():
            return False, "Nothing to redo."
        self.undo_stack.push(self._snapshot())
        self._restore(self.redo_stack.pop())
        return True, "Move redone."

    # ---------------------------------------------------------- rule checks
    def _can_place_on_tableau(self, card, dst):
        pile = self.tableau[dst]
        if pile.is_empty():
            return card.rank == 13                       # only a King on an empty pile
        top = pile.last()
        return top.face_up and top.color != card.color and top.rank == card.rank + 1

    def _can_place_on_foundation(self, card):
        stack = self.foundation[card.suit]
        if stack.is_empty():
            return card.rank == 1                        # Ace starts the pile
        return stack.peek().rank == card.rank - 1

    def _flip_top(self, pile_index):
        top = self.tableau[pile_index].last()
        if top is not None and not top.face_up:
            top.face_up = True
            self._set_loc(top, "tableau", pile_index)   # keep the dictionary in step
            self.score += 5
            return True
        return False

    # ---------------------------------------------------------- moves
    def draw_from_stock(self):
        if self.stock.is_empty() and self.waste.is_empty():
            return False, "No cards left to draw."
        self._save_for_undo()
        if self.stock.is_empty():
            # turn the waste pile over to make a new stockpile
            cards = []
            while not self.waste.is_empty():
                cards.append(self.waste.pop())
            cards.reverse()                              # first drawn card comes out first again
            for card in cards:
                card.face_up = False
                self.stock.enqueue(card)
                self._set_loc(card, "stock", None)
            self.moves += 1
            return True, "Waste pile turned back into the stockpile."
        for _ in range(self.draw_count):
            if self.stock.is_empty():
                break
            card = self.stock.dequeue()
            card.face_up = True
            self.waste.push(card)
            self._set_loc(card, "waste", None)
        self.moves += 1
        return True, "Drew from the stockpile."

    def move_tableau_to_tableau(self, src, dst, count=1):
        if src == dst:
            return False, "Source and destination are the same pile."
        pile = self.tableau[src]
        if count < 1 or count > pile.size():
            return False, "That pile does not have %d card(s)." % count
        start = pile.size() - count
        cards = pile.to_list()[start:]
        if not all(c.face_up for c in cards):
            return False, "You cannot move face-down cards."
        for upper, lower in zip(cards, cards[1:]):
            if upper.color == lower.color or upper.rank != lower.rank + 1:
                return False, "Those cards do not form a valid run."
        if not self._can_place_on_tableau(cards[0], dst):
            return False, "Illegal move: needs alternating color and rank one lower (King on empty pile)."
        self._save_for_undo()
        moved = pile.split_from(start)
        self.tableau[dst].extend(moved)
        for card in moved:
            self._set_loc(card, "tableau", dst)
        self._flip_top(src)
        self.moves += 1
        return True, "Moved %d card(s)." % count

    def move_waste_to_tableau(self, dst):
        card = self.waste.peek()
        if card is None:
            return False, "The waste pile is empty."
        if not self._can_place_on_tableau(card, dst):
            return False, "Illegal move."
        self._save_for_undo()
        self.waste.pop()
        self.tableau[dst].push(card)
        self._set_loc(card, "tableau", dst)
        self.score += 5
        self.moves += 1
        return True, "Moved waste card to pile %d." % (dst + 1)

    def move_tableau_to_foundation(self, src):
        card = self.tableau[src].last()
        if card is None:
            return False, "That pile is empty."
        if not card.face_up or not self._can_place_on_foundation(card):
            return False, "Illegal move: foundation builds A to K in one suit."
        self._save_for_undo()
        self.tableau[src].pop()
        self.foundation[card.suit].push(card)
        self._set_loc(card, "foundation", card.suit)
        self._flip_top(src)
        self.score += 10
        self.moves += 1
        return True, "Moved to foundation."

    def move_waste_to_foundation(self):
        card = self.waste.peek()
        if card is None:
            return False, "The waste pile is empty."
        if not self._can_place_on_foundation(card):
            return False, "Illegal move: foundation builds A to K in one suit."
        self._save_for_undo()
        self.waste.pop()
        self.foundation[card.suit].push(card)
        self._set_loc(card, "foundation", card.suit)
        self.score += 10
        self.moves += 1
        return True, "Moved to foundation."

    def move_foundation_to_tableau(self, suit, dst):
        card = self.foundation[suit].peek()
        if card is None:
            return False, "That foundation pile is empty."
        if not self._can_place_on_tableau(card, dst):
            return False, "Illegal move."
        self._save_for_undo()
        self.foundation[suit].pop()
        self.tableau[dst].push(card)
        self._set_loc(card, "tableau", dst)
        self.score = max(0, self.score - 15)
        self.moves += 1
        return True, "Moved back to pile %d." % (dst + 1)

    # ---------------------------------------------------------- win and hint
    def is_won(self):
        return all(st.size() == 13 for st in self.foundation.values())

    def get_hint(self):
        waste_card = self.waste.peek()
        if waste_card is not None and self._can_place_on_foundation(waste_card):
            return "Move the waste card to the foundation:  fw"
        for i in range(7):
            top = self.tableau[i].last()
            if top is not None and top.face_up and self._can_place_on_foundation(top):
                return "Move the top card of pile %d to the foundation:  f %d" % (i + 1, i + 1)
        if waste_card is not None:
            for d in range(7):
                if self._can_place_on_tableau(waste_card, d):
                    return "Move the waste card to pile %d:  w %d" % (d + 1, d + 1)
        for s in range(7):
            cards = self.tableau[s].to_list()
            for index, card in enumerate(cards):
                if not card.face_up:
                    continue
                for d in range(7):
                    if d == s or not self._can_place_on_tableau(card, d):
                        continue
                    if index == 0 and self.tableau[d].is_empty():
                        continue                      # pointless: King pile to empty pile
                    count = len(cards) - index
                    return "Move %d card(s) from pile %d to pile %d:  m %d %d %d" % (
                        count, s + 1, d + 1, s + 1, d + 1, count)
        if not self.stock.is_empty() or not self.waste.is_empty():
            return "No move found on the board. Draw from the stockpile:  d"
        return "No moves left. Try undo (u) or start a new game (n)."
