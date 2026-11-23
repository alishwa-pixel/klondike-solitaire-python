# cards.py  -  Card and Deck (Phase 1)
import random

SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
SYMBOLS = {"Hearts": "♥", "Diamonds": "♦", "Clubs": "♣", "Spades": "♠"}
RANK_NAMES = {1: "A", 11: "J", 12: "Q", 13: "K"}


class Card:
    def __init__(self, suit, rank):
        self.suit = suit          # "Hearts", "Diamonds", "Clubs", "Spades"
        self.rank = rank          # 1 (Ace) to 13 (King)
        self.face_up = False      # every card starts face down

    @property
    def color(self):
        if self.suit in ("Hearts", "Diamonds"):
            return "red"
        return "black"

    def __str__(self):
        if not self.face_up:
            return "[##]"
        name = RANK_NAMES.get(self.rank, str(self.rank))
        return name + SYMBOLS[self.suit]


class Deck:
    def __init__(self):
        self.cards = []           # Array/List: the 52 cards
        for suit in SUITS:
            for rank in range(1, 14):
                self.cards.append(Card(suit, rank))

    def shuffle(self):
        # Fisher-Yates shuffle: walk from the last index down to 1,
        # swap each card with a random card at or before it.
        for i in range(len(self.cards) - 1, 0, -1):
            j = random.randint(0, i)
            self.cards[i], self.cards[j] = self.cards[j], self.cards[i]

    def draw(self):
        return self.cards.pop()   # removes and returns the last card
