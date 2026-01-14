"""TDD tests for level progression in Moves mode."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from game_state import GameState
from constants import (
    MODE_MOVES, MOVES_INITIAL, MOVES_TARGET_BASE,
    MOVES_TARGET_MULTIPLIER, MOVES_BONUS_PER_UNUSED
)


class TestLevelProgression:
    """Tests for level progression mechanics."""

    def test_starts_at_level_1(self):
        """Game starts at level 1."""
        state = GameState(MODE_MOVES)
        assert state.level == 1

    def test_initial_target_score(self):
        """Level 1 has base target score."""
        state = GameState(MODE_MOVES)
        assert state.target_score == MOVES_TARGET_BASE

    def test_level_up_when_target_reached(self):
        """Level increases when target score is reached."""
        state = GameState(MODE_MOVES, seed=42)
        state.score = MOVES_TARGET_BASE + 1
        state.check_level_complete()
        assert state.level == 2

    def test_target_increases_each_level(self):
        """Target score increases with each level."""
        state = GameState(MODE_MOVES, seed=42)

        # Complete level 1
        state.score = MOVES_TARGET_BASE + 1
        state.check_level_complete()

        # Level 2 should have higher target
        expected_target = int(MOVES_TARGET_BASE * MOVES_TARGET_MULTIPLIER)
        assert state.target_score == expected_target

    def test_moves_reset_on_level_up(self):
        """Moves reset to initial value on level up."""
        state = GameState(MODE_MOVES, seed=42)
        state.moves_remaining = 5  # Used some moves

        # Complete level
        state.score = MOVES_TARGET_BASE + 1
        state.check_level_complete()

        assert state.moves_remaining == MOVES_INITIAL

    def test_bonus_for_unused_moves(self):
        """Unused moves give bonus points on level complete."""
        state = GameState(MODE_MOVES, seed=42)
        state.moves_remaining = 10  # 10 unused moves
        initial_score = MOVES_TARGET_BASE + 100
        state.score = initial_score

        state.check_level_complete()

        # Should have bonus for 10 unused moves
        expected_bonus = 10 * MOVES_BONUS_PER_UNUSED
        assert state.score == initial_score + expected_bonus

    def test_stars_one_for_reaching_target(self):
        """1 star for reaching target score."""
        state = GameState(MODE_MOVES, seed=42)
        state.score = MOVES_TARGET_BASE
        stars = state.calculate_stars()
        assert stars >= 1

    def test_stars_two_for_1_5x_target(self):
        """2 stars for reaching 1.5x target score."""
        state = GameState(MODE_MOVES, seed=42)
        state.score = int(MOVES_TARGET_BASE * 1.5)
        stars = state.calculate_stars()
        assert stars >= 2

    def test_stars_three_for_2x_target(self):
        """3 stars for reaching 2x target score."""
        state = GameState(MODE_MOVES, seed=42)
        state.score = int(MOVES_TARGET_BASE * 2)
        stars = state.calculate_stars()
        assert stars == 3

    def test_stars_zero_below_target(self):
        """0 stars if target not reached."""
        state = GameState(MODE_MOVES, seed=42)
        state.score = MOVES_TARGET_BASE - 100
        stars = state.calculate_stars()
        assert stars == 0


class TestGameOverMoves:
    """Tests for game over in Moves mode."""

    def test_game_over_when_out_of_moves_below_target(self):
        """Game over when out of moves and below target."""
        state = GameState(MODE_MOVES, seed=42)
        state.score = MOVES_TARGET_BASE - 100
        state.moves_remaining = 0
        state.check_game_over(has_valid_moves=True)
        assert state.is_game_over is True

    def test_level_complete_when_out_of_moves_above_target(self):
        """Level completes when out of moves and above target."""
        state = GameState(MODE_MOVES, seed=42)
        state.score = MOVES_TARGET_BASE + 100
        state.moves_remaining = 0
        state.check_level_complete()
        assert state.level == 2
        assert state.is_game_over is False


class TestLevelDisplay:
    """Tests for level display info."""

    def test_get_level_info(self):
        """Can get level info for display."""
        state = GameState(MODE_MOVES, seed=42)
        info = state.get_level_info()

        assert "level" in info
        assert "target" in info
        assert "progress" in info

    def test_progress_percentage(self):
        """Progress shows correct percentage."""
        state = GameState(MODE_MOVES, seed=42)
        state.score = MOVES_TARGET_BASE // 2

        info = state.get_level_info()
        assert info["progress"] == 50  # 50% to target
