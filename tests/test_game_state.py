"""Tests for GameState class."""

import pytest
from game_state import GameState
from board import Board
from constants import (
    MODE_ENDLESS, MODE_MOVES, MODE_TIMED,
    MOVES_INITIAL, TIMED_INITIAL_SECONDS
)


class TestGameStateCreation:
    """Tests for creating game states."""

    def test_create_endless_mode(self):
        """Can create game in endless mode."""
        state = GameState(MODE_ENDLESS)
        assert state.mode == MODE_ENDLESS
        assert state.score == 0
        assert state.is_game_over is False

    def test_create_moves_mode(self):
        """Moves mode starts with initial moves."""
        state = GameState(MODE_MOVES)
        assert state.mode == MODE_MOVES
        assert state.moves_remaining == MOVES_INITIAL

    def test_create_timed_mode(self):
        """Timed mode starts with initial time."""
        state = GameState(MODE_TIMED)
        assert state.mode == MODE_TIMED
        assert state.time_remaining == TIMED_INITIAL_SECONDS

    def test_state_has_board(self):
        """Game state contains a board."""
        state = GameState(MODE_ENDLESS)
        assert state.board is not None
        assert isinstance(state.board, Board)


class TestScoring:
    """Tests for score calculation."""

    def test_add_score_basic_match(self):
        """Basic match adds points."""
        state = GameState(MODE_ENDLESS)
        state.add_match_score(3, cascade_level=1)
        assert state.score == 30  # 3 * 10 base

    def test_cascade_multiplier(self):
        """Higher cascade levels multiply score."""
        state = GameState(MODE_ENDLESS)
        state.add_match_score(3, cascade_level=2)
        assert state.score == 45  # 30 * 1.5

    def test_special_bonus_striped(self):
        """Striped candy gives bonus."""
        state = GameState(MODE_ENDLESS)
        state.add_special_bonus("striped")
        assert state.score == 50

    def test_special_bonus_wrapped(self):
        """Wrapped candy gives bonus."""
        state = GameState(MODE_ENDLESS)
        state.add_special_bonus("wrapped")
        assert state.score == 100

    def test_special_bonus_color_bomb(self):
        """Color bomb gives bonus."""
        state = GameState(MODE_ENDLESS)
        state.add_special_bonus("color_bomb")
        assert state.score == 500


class TestMovesMode:
    """Tests for moves mode gameplay."""

    def test_use_move_decrements(self):
        """Using a move decrements counter."""
        state = GameState(MODE_MOVES)
        initial = state.moves_remaining
        state.use_move()
        assert state.moves_remaining == initial - 1

    def test_game_over_when_no_moves(self):
        """Game ends when moves run out."""
        state = GameState(MODE_MOVES)
        state.moves_remaining = 1
        state.use_move()
        assert state.moves_remaining == 0
        # Game over checked separately based on target

    def test_moves_mode_has_target(self):
        """Moves mode has a target score."""
        state = GameState(MODE_MOVES)
        assert state.target_score > 0


class TestTimedMode:
    """Tests for timed mode gameplay."""

    def test_update_time(self):
        """Time decreases with update."""
        state = GameState(MODE_TIMED)
        initial = state.time_remaining
        state.update_time(1.0)  # 1 second
        assert state.time_remaining == initial - 1.0

    def test_game_over_when_time_out(self):
        """Game ends when time runs out."""
        state = GameState(MODE_TIMED)
        state.time_remaining = 0.5
        state.update_time(1.0)
        assert state.time_remaining <= 0
        assert state.is_game_over

    def test_time_bonus_for_special(self):
        """Creating special adds time."""
        state = GameState(MODE_TIMED)
        initial = state.time_remaining
        state.add_time_bonus_special()
        assert state.time_remaining == initial + 3

    def test_time_bonus_for_combo(self):
        """Combos add time."""
        state = GameState(MODE_TIMED)
        initial = state.time_remaining
        state.add_time_bonus_combo()
        assert state.time_remaining == initial + 5


class TestEndlessMode:
    """Tests for endless mode gameplay."""

    def test_endless_has_reshuffles(self):
        """Endless mode starts with reshuffle allowance."""
        state = GameState(MODE_ENDLESS)
        assert state.reshuffles_remaining == 3

    def test_use_reshuffle(self):
        """Using reshuffle decrements counter."""
        state = GameState(MODE_ENDLESS)
        state.use_reshuffle()
        assert state.reshuffles_remaining == 2

    def test_game_over_no_moves_no_reshuffles(self):
        """Endless ends when no moves and no reshuffles."""
        state = GameState(MODE_ENDLESS)
        state.reshuffles_remaining = 0
        # Simulate board with no valid moves
        state.check_game_over(has_valid_moves=False)
        assert state.is_game_over
