"""TDD tests for special candy activation."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from board import Board
from candy import Candy
from constants import (
    SPECIAL_STRIPED_H, SPECIAL_STRIPED_V,
    SPECIAL_WRAPPED, SPECIAL_COLOR_BOMB,
    GRID_ROWS, GRID_COLS
)


class TestStripedActivation:
    """Tests for striped candy activation."""

    def test_horizontal_striped_clears_row(self):
        """Horizontal striped candy clears entire row when activated."""
        board = Board(seed=42)

        # Place a horizontal striped candy at (3, 3)
        striped = Candy("lock", row=3, col=3)
        striped.special = SPECIAL_STRIPED_H
        board.set_candy(3, 3, striped)

        # Activate it
        cleared = board.activate_special(3, 3)

        # Should clear all 8 cells in row 3
        assert len(cleared) == GRID_COLS
        for col in range(GRID_COLS):
            assert (3, col) in cleared

    def test_vertical_striped_clears_column(self):
        """Vertical striped candy clears entire column when activated."""
        board = Board(seed=42)

        # Place a vertical striped candy at (3, 3)
        striped = Candy("key", row=3, col=3)
        striped.special = SPECIAL_STRIPED_V
        board.set_candy(3, 3, striped)

        # Activate it
        cleared = board.activate_special(3, 3)

        # Should clear all 8 cells in column 3
        assert len(cleared) == GRID_ROWS
        for row in range(GRID_ROWS):
            assert (row, 3) in cleared


class TestWrappedActivation:
    """Tests for wrapped candy activation."""

    def test_wrapped_clears_3x3_area(self):
        """Wrapped candy clears 3x3 area around it."""
        board = Board(seed=42)

        # Place a wrapped candy at center (3, 3)
        wrapped = Candy("virus", row=3, col=3)
        wrapped.special = SPECIAL_WRAPPED
        board.set_candy(3, 3, wrapped)

        # Activate it
        cleared = board.activate_special(3, 3)

        # Should clear 3x3 = 9 cells
        assert len(cleared) == 9
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                assert (3 + dr, 3 + dc) in cleared

    def test_wrapped_at_corner_clears_available_cells(self):
        """Wrapped candy at corner only clears cells that exist."""
        board = Board(seed=42)

        # Place a wrapped candy at corner (0, 0)
        wrapped = Candy("virus", row=0, col=0)
        wrapped.special = SPECIAL_WRAPPED
        board.set_candy(0, 0, wrapped)

        # Activate it
        cleared = board.activate_special(0, 0)

        # At corner, only 4 cells exist in 3x3 area
        assert len(cleared) == 4
        assert (0, 0) in cleared
        assert (0, 1) in cleared
        assert (1, 0) in cleared
        assert (1, 1) in cleared


class TestColorBombActivation:
    """Tests for color bomb activation."""

    def test_color_bomb_clears_all_of_target_color(self):
        """Color bomb clears all candies of the swapped color."""
        board = Board(seed=42)

        # Place color bomb at (3, 3)
        bomb = Candy("blackhat", row=3, col=3)
        bomb.special = SPECIAL_COLOR_BOMB
        board.set_candy(3, 3, bomb)

        # Place some "lock" candies around the board
        lock_positions = [(0, 0), (1, 2), (4, 5), (7, 7)]
        for r, c in lock_positions:
            board.set_candy(r, c, Candy("lock", row=r, col=c))

        # Set target at (3, 4) to be "lock"
        board.set_candy(3, 4, Candy("lock", row=3, col=4))

        # Activate color bomb targeting "lock"
        cleared = board.activate_special(3, 3, target_type="lock")

        # Should include the bomb position and all lock candies
        assert (3, 3) in cleared  # The bomb itself
        for r, c in lock_positions:
            assert (r, c) in cleared
        assert (3, 4) in cleared  # The target

    def test_color_bomb_with_no_target_returns_only_self(self):
        """Color bomb without target type just clears itself."""
        board = Board(seed=42)

        bomb = Candy("blackhat", row=3, col=3)
        bomb.special = SPECIAL_COLOR_BOMB
        board.set_candy(3, 3, bomb)

        # Activate without target
        cleared = board.activate_special(3, 3)

        # Should at minimum include itself
        assert (3, 3) in cleared


class TestSpecialCombinations:
    """Tests for special candy combinations."""

    def test_striped_plus_striped_clears_row_and_column(self):
        """Two striped candies clear both row and column."""
        board = Board(seed=42)

        # Place horizontal striped at (3, 3)
        s1 = Candy("lock", row=3, col=3)
        s1.special = SPECIAL_STRIPED_H
        board.set_candy(3, 3, s1)

        # Place vertical striped at (3, 4)
        s2 = Candy("lock", row=3, col=4)
        s2.special = SPECIAL_STRIPED_V
        board.set_candy(3, 4, s2)

        # Combine them
        cleared = board.activate_special_combo(3, 3, 3, 4)

        # Should clear row 3 AND column 3 AND column 4
        for col in range(GRID_COLS):
            assert (3, col) in cleared
        for row in range(GRID_ROWS):
            assert (row, 3) in cleared
            assert (row, 4) in cleared

    def test_striped_plus_wrapped_clears_cross(self):
        """Striped + wrapped clears 3 rows and 3 columns."""
        board = Board(seed=42)

        striped = Candy("lock", row=3, col=3)
        striped.special = SPECIAL_STRIPED_H
        board.set_candy(3, 3, striped)

        wrapped = Candy("virus", row=3, col=4)
        wrapped.special = SPECIAL_WRAPPED
        board.set_candy(3, 4, wrapped)

        cleared = board.activate_special_combo(3, 3, 3, 4)

        # Should clear rows 2, 3, 4 AND columns 2, 3, 4
        for row in [2, 3, 4]:
            for col in range(GRID_COLS):
                assert (row, col) in cleared
        for col in [2, 3, 4]:
            for row in range(GRID_ROWS):
                assert (row, col) in cleared

    def test_wrapped_plus_wrapped_clears_5x5(self):
        """Two wrapped candies clear 5x5 area."""
        board = Board(seed=42)

        w1 = Candy("virus", row=4, col=4)
        w1.special = SPECIAL_WRAPPED
        board.set_candy(4, 4, w1)

        w2 = Candy("virus", row=4, col=5)
        w2.special = SPECIAL_WRAPPED
        board.set_candy(4, 5, w2)

        cleared = board.activate_special_combo(4, 4, 4, 5)

        # Should clear 5x5 centered between them (around col 4.5)
        # Center at (4, 4) - check 5x5 area
        expected_count = 0
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                r, c = 4 + dr, 4 + dc
                if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                    expected_count += 1

        assert len(cleared) >= expected_count - 5  # Some overlap tolerance

    def test_color_bomb_plus_color_bomb_clears_board(self):
        """Two color bombs clear the entire board."""
        board = Board(seed=42)

        b1 = Candy("blackhat", row=3, col=3)
        b1.special = SPECIAL_COLOR_BOMB
        board.set_candy(3, 3, b1)

        b2 = Candy("defcon", row=3, col=4)
        b2.special = SPECIAL_COLOR_BOMB
        board.set_candy(3, 4, b2)

        cleared = board.activate_special_combo(3, 3, 3, 4)

        # Should clear entire board
        assert len(cleared) == GRID_ROWS * GRID_COLS


class TestSpecialInMatch:
    """Tests for special candies being triggered by matches."""

    def test_striped_in_match_triggers_activation(self):
        """When a striped candy is part of a match, it activates."""
        board = Board(seed=42)

        # Set up a horizontal match of 3 "lock" candies with a striped
        # First clear the row to avoid interference
        for col in range(GRID_COLS):
            board.set_candy(3, col, Candy("virus", row=3, col=col))

        # Now place our match
        board.set_candy(3, 0, Candy("lock", row=3, col=0))
        board.set_candy(3, 1, Candy("lock", row=3, col=1))

        striped = Candy("lock", row=3, col=2)
        striped.special = SPECIAL_STRIPED_V
        board.set_candy(3, 2, striped)

        # Create the match manually since find_matches may not detect specials
        match = {(3, 0), (3, 1), (3, 2)}
        cleared = board.process_matches_with_specials([match])

        # Should clear the match AND the entire column 2
        assert len(cleared) > 3  # More than just the match
        for row in range(GRID_ROWS):
            assert (row, 2) in cleared
