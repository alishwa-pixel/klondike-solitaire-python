# test_game.py - pytest suite for the CSC200 Klondike Solitaire project.
# Covers the four rows of the teacher's "Validation and Testing" table:
#   Legal Moves, Card Flipping, Win Condition, Game Flow.
# Run with:  pytest -v      (install pytest first with:  pip install pytest)

import random

import pytest

from cards import Card, Deck, SUITS
from game import Game
from structures import LinkedList, Queue, Stack


@pytest.fixture
def game():
    """A fresh draw-1 game for each test."""
    return Game(draw_count=1)


def find_legal_run_move(g):
    """Return (src, dst, count) for any legal tableau-to-tableau run move."""
    for src in range(7):
        cards = g.tableau[src].to_list()
        for idx, card in enumerate(cards):
            if not card.face_up:
                continue
            for dst in range(7):
                if dst == src:
                    continue
                if g._can_place_on_tableau(card, dst):
                    if idx == 0 and g.tableau[dst].is_empty():
                        continue          # moving a whole pile to an empty pile
                    return src, dst, len(cards) - idx
    return None


# ------------------------------------------------------- legal moves (row 1)

def test_deck_is_52_unique_cards():
    pairs = [(c.suit, c.rank) for c in Deck().cards]
    assert len(pairs) == 52
    assert len(set(pairs)) == 52


def test_stack_is_lifo_and_queue_is_fifo():
    stack = Stack()
    for i in range(3):
        stack.push(i)
    assert [stack.pop(), stack.pop(), stack.pop()] == [2, 1, 0]
    queue = Queue()
    for i in range(3):
        queue.enqueue(i)
    assert [queue.dequeue(), queue.dequeue(), queue.dequeue()] == [0, 1, 2]


def test_linked_list_splits_a_run():
    pile = LinkedList()
    for i in range(5):
        pile.append(i)
    cut = pile.split_from(2)
    assert pile.to_list() == [0, 1] and cut == [2, 3, 4]


def test_only_alternating_colors_build_on_tableau():
    g = Game()
    g.tableau[0] = LinkedList()
    king = Card("Spades", 13)
    king.face_up = True
    g.tableau[0].append(king)
    assert g._can_place_on_tableau(Card("Hearts", 12), 0)      # red queen on black king
    assert not g._can_place_on_tableau(Card("Clubs", 12), 0)   # black queen refused
    assert not g._can_place_on_tableau(Card("Hearts", 13), 0)  # same rank refused


def test_only_a_king_starts_an_empty_pile():
    g = Game()
    g.tableau[3] = LinkedList()          # empty pile 4 first
    assert not g._can_place_on_tableau(Card("Hearts", 5), 3)
    assert g._can_place_on_tableau(Card("Hearts", 13), 3)


def test_foundation_builds_ace_to_king_by_suit():
    g = Game()
    assert g._can_place_on_foundation(Card("Hearts", 1))
    assert not g._can_place_on_foundation(Card("Hearts", 2))    # no ace yet
    g.foundation["Hearts"].push(Card("Hearts", 1))
    assert g._can_place_on_foundation(Card("Hearts", 2))
    assert not g._can_place_on_foundation(Card("Spades", 2))    # wrong suit pile


def test_illegal_moves_are_rejected_and_change_nothing(game):
    snapshot = game._snapshot()
    assert not game.move_tableau_to_tableau(0, 0, 1)[0]    # same pile
    assert not game.move_tableau_to_tableau(0, 1, 99)[0]   # pile has fewer cards
    assert not game.move_waste_to_tableau(0)[0]            # waste is empty at deal
    assert game._snapshot() == snapshot                    # board untouched


# ---------------------------------------------------- card flipping (row 2)

def test_deal_turns_only_the_top_card_face_up():
    random.seed(10)
    g = Game()
    for pile in g.tableau:
        cards = pile.to_list()
        assert all(not c.face_up for c in cards[:-1])
        assert cards[-1].face_up


def test_face_down_cards_cannot_be_moved():
    random.seed(11)
    g = Game()
    # pile 7 has 7 cards but only its top is face up, so moving 2 is illegal
    ok, message = g.move_tableau_to_tableau(6, 0, 2)
    assert not ok
    assert "face-down" in message


def test_new_card_flips_after_a_move_off_its_pile():
    random.seed(12)
    g = Game()
    move = find_legal_run_move(g)
    assert move is not None, "seeded deal has no legal run move"
    src, dst, count = move
    dst_before = g.tableau[dst].size()
    ok, message = g.move_tableau_to_tableau(src, dst, count)
    assert ok, message
    assert g.tableau[dst].size() == dst_before + count
    if not g.tableau[src].is_empty():
        assert g.tableau[src].last().face_up      # the exposed card was flipped


# ---------------------------------------------------- win condition (row 3)

def test_win_requires_all_four_complete_foundations():
    g = Game()
    for suit in SUITS:
        for rank in range(1, 14):
            g.foundation[suit].push(Card(suit, rank))
    assert g.is_won()
    g.foundation["Hearts"].pop()                 # one card short of a win
    assert not g.is_won()


def test_victory_reached_through_legal_moves_only():
    # Endgame position: A..Q already on every foundation and the four kings
    # face-up on the tableau. Only four legal foundation moves remain, and
    # the game must declare victory after the last one.
    g = Game()
    g.tableau = [LinkedList() for _ in range(7)]
    g.stock = Queue()
    g.waste = Stack()
    g.location = {}
    for suit in SUITS:
        for rank in range(1, 13):
            card = Card(suit, rank)
            card.face_up = True
            g.foundation[suit].push(card)
    for i, suit in enumerate(SUITS):
        king = Card(suit, 13)
        king.face_up = True
        g.tableau[i].append(king)
        g._set_loc(king, "tableau", i)
    assert not g.is_won()
    for i in range(4):
        ok, message = g.move_tableau_to_foundation(i)
        assert ok, message
    assert g.is_won()


# -------------------------------------------------------- game flow (row 4)

def test_initial_deal_and_dictionary_tracking():
    random.seed(13)
    g = Game()
    assert [p.size() for p in g.tableau] == [1, 2, 3, 4, 5, 6, 7]
    assert g.stock.size() == 24
    assert sum(p.size() for p in g.tableau) + g.stock.size() == 52
    assert len(g.location) == 52                 # dictionary tracks all cards
    for i in range(7):
        assert g.tableau[i].last().face_up


def test_stock_drains_then_recycles_in_the_same_order():
    random.seed(14)
    g = Game()
    drawn_order = []
    while not g.stock.is_empty():
        g.draw_from_stock()
        drawn_order.append(g.waste.peek())
    assert g.waste.size() == 24
    g.draw_from_stock()                          # recycle: waste flips to stock
    assert g.stock.size() == 24 and g.waste.is_empty()
    g.draw_from_stock()                          # first card of the new pass
    assert g.waste.peek() is drawn_order[0]


def test_undo_then_redo_round_trip():
    random.seed(12)
    g = Game()
    move = find_legal_run_move(g)
    assert move is not None, "seeded deal has no legal run move"
    src, dst, count = move
    before = g._snapshot()
    assert g.move_tableau_to_tableau(src, dst, count)[0]
    assert g._snapshot() != before
    assert g.undo()[0]
    assert g._snapshot() == before
    assert g.redo()[0]
    assert g._snapshot() != before


def test_undo_on_empty_history_is_refused(game):
    ok, _ = game.undo()
    assert not ok


def test_rejected_moves_never_enter_the_history(game):
    depth = game.undo_stack.size()
    game.move_tableau_to_tableau(0, 0, 1)        # same pile: rejected
    game.move_waste_to_foundation()              # empty waste: rejected
    assert game.undo_stack.size() == depth


def test_locate_command_uses_the_dictionary():
    random.seed(16)
    g = Game()
    top = g.tableau[6].last()
    assert "pile 7" in g.locate(top.rank, top.suit)
    assert "face up" in g.locate(top.rank, top.suit)
    buried = g.tableau[6].to_list()[0]
    assert "pile 7" in g.locate(buried.rank, buried.suit)
    assert "face down" in g.locate(buried.rank, buried.suit)
    stock_card = g.stock.peek()
    assert "stockpile" in g.locate(stock_card.rank, stock_card.suit)


def test_locate_finds_foundation_cards(game):
    ace = Card("Hearts", 1)
    ace.face_up = True
    game.foundation["Hearts"].push(ace)
    game._set_loc(ace, "foundation", "Hearts")
    assert "foundation" in game.locate(1, "Hearts")


def test_draw_three_mode_draws_three_cards():
    random.seed(17)
    g = Game(draw_count=3)
    g.draw_from_stock()
    assert g.waste.size() == 3


def test_long_session_keeps_all_52_cards_accounted_for():
    random.seed(18)
    for trial in range(3):
        g = Game(draw_count=1 if trial % 2 == 0 else 3)
        for _ in range(200):
            if g.is_won():
                break
            played = False
            waste_card = g.waste.peek()
            if waste_card is not None and g._can_place_on_foundation(waste_card):
                g.move_waste_to_foundation()
                played = True
            for i in range(7):
                top = g.tableau[i].last()
                if top is not None and top.face_up and g._can_place_on_foundation(top):
                    g.move_tableau_to_foundation(i)
                    played = True
                    break
            if not played:
                move = find_legal_run_move(g)
                if move is not None:
                    g.move_tableau_to_tableau(*move)
                    played = True
            if not played:
                g.draw_from_stock()
            total = (sum(p.size() for p in g.tableau)
                     + sum(s.size() for s in g.foundation.values())
                     + g.stock.size() + g.waste.size())
            assert total == 52                   # no card ever lost or duplicated
            assert len(g.location) == 52


# ------------------------------------- dictionary and stack-style tableau

def dictionary_matches_board(g):
    """Every card's dictionary entry must equal its real pile and face state."""
    for i, pile in enumerate(g.tableau):
        for c in pile.to_list():
            if g.location[(c.suit, c.rank)] != ("tableau", i, c.face_up):
                return False
    for suit, stack in g.foundation.items():
        for c in stack.to_list():
            if g.location[(c.suit, c.rank)] != ("foundation", suit, c.face_up):
                return False
    for c in g.stock.to_list():
        if g.location[(c.suit, c.rank)] != ("stock", None, c.face_up):
            return False
    for c in g.waste.to_list():
        if g.location[(c.suit, c.rank)] != ("waste", None, c.face_up):
            return False
    return len(g.location) == 52


def test_dictionary_tracks_pile_and_face_state_through_play():
    random.seed(21)
    for trial in range(5):
        g = Game(draw_count=1 if trial % 2 == 0 else 3)
        assert dictionary_matches_board(g)
        for _ in range(250):
            r = random.random()
            if r < 0.25:
                g.draw_from_stock()
            elif r < 0.5:
                g.move_tableau_to_tableau(random.randrange(7), random.randrange(7), random.randint(1, 4))
            elif r < 0.62:
                g.move_waste_to_tableau(random.randrange(7))
            elif r < 0.75:
                g.move_tableau_to_foundation(random.randrange(7))
            elif r < 0.82:
                g.move_waste_to_foundation()
            elif r < 0.86:
                g.move_foundation_to_tableau(random.choice(SUITS), random.randrange(7))
            elif r < 0.93:
                g.undo()
            else:
                g.redo()
            assert dictionary_matches_board(g)


def test_tableau_pile_works_like_a_stack_on_its_top_card():
    pile = LinkedList()
    for i in range(3):
        pile.push(i)
    assert pile.peek() == 2
    assert pile.pop() == 2 and pile.pop() == 1
    assert pile.to_list() == [0]
