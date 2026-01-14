"""Tests for Board class."""

import pytest
from board import Board
from candy import Candy
from constants import GRID_ROWS, GRID_COLS, CANDY_TYPES


class TestBoardCreation:
    """Tests for creating and initializing the board."""

    def test_board_has_correct_dimensions(self):
        """Board has 8x8 grid."""
        board = Board()
        assert board.rows == GRID_ROWS
        assert board.cols == GRID_COLS

    def test_board_initializes_with_candies(self):
        """Board fills all cells with candies on creation."""
        board = Board()
        for row in range(board.rows):
            for col in range(board.cols):
                candy = board.get_candy(row, col)
                assert candy is not None
                assert isinstance(candy, Candy)

    def test_board_no_initial_matches(self):
        """Board has no matches immediately after creation."""
        board = Board()
        matches = board.find_matches()
        assert len(matches) == 0

    def test_board_candies_have_positions(self):
        """All candies know their grid position."""
        board = Board()
        for row in range(board.rows):
            for col in range(board.cols):
                candy = board.get_candy(row, col)
                assert candy.row == row
                assert candy.col == col


class TestBoardAccess:
    """Tests for accessing board cells."""

    def test_get_candy_valid_position(self):
        """Can get candy at valid position."""
        board = Board()
        candy = board.get_candy(0, 0)
        assert candy is not None

    def test_get_candy_out_of_bounds_returns_none(self):
        """Getting candy out of bounds returns None."""
        board = Board()
        assert board.get_candy(-1, 0) is None
        assert board.get_candy(0, -1) is None
        assert board.get_candy(GRID_ROWS, 0) is None
        assert board.get_candy(0, GRID_COLS) is None

    def test_set_candy_valid_position(self):
        """Can set candy at valid position."""
        board = Board()
        new_candy = Candy("virus", row=3, col=4)
        board.set_candy(3, 4, new_candy)
        assert board.get_candy(3, 4) is new_candy

    def test_set_candy_updates_candy_position(self):
        """Setting candy updates its position attributes."""
        board = Board()
        new_candy = Candy("lock")
        board.set_candy(2, 5, new_candy)
        assert new_candy.row == 2
        assert new_candy.col == 5

    def test_is_valid_position(self):
        """Board correctly validates positions."""
        board = Board()
        assert board.is_valid_position(0, 0)
        assert board.is_valid_position(7, 7)
        assert not board.is_valid_position(-1, 0)
        assert not board.is_valid_position(8, 0)


class TestBoardSwap:
    """Tests for swapping candies."""

    def test_swap_adjacent_horizontal(self):
        """Can swap horizontally adjacent candies."""
        board = Board()
        candy1 = board.get_candy(0, 0)
        candy2 = board.get_candy(0, 1)

        board.swap(0, 0, 0, 1)

        assert board.get_candy(0, 0) is candy2
        assert board.get_candy(0, 1) is candy1

    def test_swap_adjacent_vertical(self):
        """Can swap vertically adjacent candies."""
        board = Board()
        candy1 = board.get_candy(0, 0)
        candy2 = board.get_candy(1, 0)

        board.swap(0, 0, 1, 0)

        assert board.get_candy(0, 0) is candy2
        assert board.get_candy(1, 0) is candy1

    def test_swap_updates_candy_positions(self):
        """Swapping updates candy position attributes."""
        board = Board()
        candy1 = board.get_candy(2, 3)
        candy2 = board.get_candy(2, 4)

        board.swap(2, 3, 2, 4)

        assert candy1.row == 2 and candy1.col == 4
        assert candy2.row == 2 and candy2.col == 3

    def test_is_adjacent(self):
        """Board correctly identifies adjacent positions."""
        board = Board()
        assert board.is_adjacent(0, 0, 0, 1)  # horizontal
        assert board.is_adjacent(0, 0, 1, 0)  # vertical
        assert not board.is_adjacent(0, 0, 0, 2)  # too far
        assert not board.is_adjacent(0, 0, 1, 1)  # diagonal


class TestMatchDetection:
    """Tests for match detection logic."""

    def test_detect_horizontal_match_3(self):
        """Detects 3 candies in a horizontal row."""
        board = Board(seed=42)
        # Manually set up a match
        board.set_candy(0, 0, Candy("virus", 0, 0))
        board.set_candy(0, 1, Candy("virus", 0, 1))
        board.set_candy(0, 2, Candy("virus", 0, 2))

        matches = board.find_matches()
        assert len(matches) >= 1
        # Find the match containing our positions
        found = False
        for match in matches:
            if (0, 0) in match and (0, 1) in match and (0, 2) in match:
                found = True
                break
        assert found, "Horizontal match not detected"

    def test_detect_vertical_match_3(self):
        """Detects 3 candies in a vertical column."""
        board = Board(seed=42)
        board.set_candy(0, 0, Candy("lock", 0, 0))
        board.set_candy(1, 0, Candy("lock", 1, 0))
        board.set_candy(2, 0, Candy("lock", 2, 0))

        matches = board.find_matches()
        assert len(matches) >= 1
        found = False
        for match in matches:
            if (0, 0) in match and (1, 0) in match and (2, 0) in match:
                found = True
                break
        assert found, "Vertical match not detected"

    def test_detect_match_4(self):
        """Detects 4 candies in a row."""
        board = Board(seed=42)
        for col in range(4):
            board.set_candy(3, col, Candy("key", 3, col))

        matches = board.find_matches()
        found = False
        for match in matches:
            if all((3, c) in match for c in range(4)):
                found = True
                assert len(match) >= 4
                break
        assert found, "Match of 4 not detected"

    def test_detect_match_5(self):
        """Detects 5 candies in a row."""
        board = Board(seed=42)
        for col in range(5):
            board.set_candy(4, col, Candy("defcon", 4, col))

        matches = board.find_matches()
        found = False
        for match in matches:
            if all((4, c) in match for c in range(5)):
                found = True
                assert len(match) >= 5
                break
        assert found, "Match of 5 not detected"

    def test_detect_l_shape(self):
        """Detects L-shaped match (for wrapped candy)."""
        board = Board(seed=42)
        # Create L shape:
        # X X X
        # X
        # X
        board.set_candy(0, 0, Candy("ronin", 0, 0))
        board.set_candy(0, 1, Candy("ronin", 0, 1))
        board.set_candy(0, 2, Candy("ronin", 0, 2))
        board.set_candy(1, 0, Candy("ronin", 1, 0))
        board.set_candy(2, 0, Candy("ronin", 2, 0))

        matches = board.find_matches()
        # Should merge into one L-shaped match
        found = False
        for match in matches:
            positions = [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)]
            if all(p in match for p in positions):
                found = True
                break
        assert found, "L-shape match not detected"

    def test_detect_t_shape(self):
        """Detects T-shaped match (for wrapped candy)."""
        board = Board(seed=42)
        # Create T shape:
        # X X X
        #   X
        #   X
        board.set_candy(0, 0, Candy("blackhat", 0, 0))
        board.set_candy(0, 1, Candy("blackhat", 0, 1))
        board.set_candy(0, 2, Candy("blackhat", 0, 2))
        board.set_candy(1, 1, Candy("blackhat", 1, 1))
        board.set_candy(2, 1, Candy("blackhat", 2, 1))

        matches = board.find_matches()
        found = False
        for match in matches:
            positions = [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)]
            if all(p in match for p in positions):
                found = True
                break
        assert found, "T-shape match not detected"


class TestMatchClassification:
    """Tests for classifying match patterns."""

    def test_classify_match_3_horizontal(self):
        """Match of 3 horizontal is classified as basic."""
        board = Board(seed=42)
        match = {(0, 0), (0, 1), (0, 2)}
        result = board.classify_match(match)
        assert result["type"] == "basic"
        assert result["count"] == 3

    def test_classify_match_4_horizontal(self):
        """Match of 4 horizontal creates striped candy."""
        board = Board(seed=42)
        match = {(0, 0), (0, 1), (0, 2), (0, 3)}
        result = board.classify_match(match)
        assert result["type"] == "striped"
        assert result["direction"] == "horizontal"

    def test_classify_match_4_vertical(self):
        """Match of 4 vertical creates striped candy."""
        board = Board(seed=42)
        match = {(0, 0), (1, 0), (2, 0), (3, 0)}
        result = board.classify_match(match)
        assert result["type"] == "striped"
        assert result["direction"] == "vertical"

    def test_classify_match_5(self):
        """Match of 5 creates color bomb."""
        board = Board(seed=42)
        match = {(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)}
        result = board.classify_match(match)
        assert result["type"] == "color_bomb"

    def test_classify_l_shape(self):
        """L-shape creates wrapped candy."""
        board = Board(seed=42)
        match = {(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)}
        result = board.classify_match(match)
        assert result["type"] == "wrapped"

    def test_classify_t_shape(self):
        """T-shape creates wrapped candy."""
        board = Board(seed=42)
        match = {(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)}
        result = board.classify_match(match)
        assert result["type"] == "wrapped"


class TestGravity:
    """Tests for gravity and board refill."""

    def test_apply_gravity_single_gap(self):
        """Candies fall down to fill single gap."""
        board = Board(seed=42)
        # Remember candy above the gap
        candy_above = board.get_candy(0, 0)

        # Create gap at bottom
        board.set_candy(7, 0, None)

        # Apply gravity
        board.apply_gravity()

        # Candy should have fallen
        assert board.get_candy(7, 0) is not None
        # Top should be empty (will be refilled separately)
        assert board.get_candy(0, 0) is None

    def test_apply_gravity_multiple_gaps(self):
        """Candies fall through multiple gaps."""
        board = Board(seed=42)
        candy_at_top = board.get_candy(0, 0)

        # Create multiple gaps
        board.set_candy(5, 0, None)
        board.set_candy(6, 0, None)
        board.set_candy(7, 0, None)

        board.apply_gravity()

        # Top 3 rows should be empty
        assert board.get_candy(0, 0) is None
        assert board.get_candy(1, 0) is None
        assert board.get_candy(2, 0) is None

        # Bottom should be filled with fallen candies
        assert board.get_candy(7, 0) is not None
        assert board.get_candy(6, 0) is not None
        assert board.get_candy(5, 0) is not None

    def test_refill_board(self):
        """Empty cells at top are refilled with new candies."""
        board = Board(seed=42)

        # Create gaps and apply gravity
        board.set_candy(7, 0, None)
        board.set_candy(7, 1, None)
        board.apply_gravity()

        # Refill
        board.refill()

        # All cells should have candies
        for row in range(board.rows):
            for col in range(board.cols):
                assert board.get_candy(row, col) is not None

    def test_gravity_updates_candy_positions(self):
        """Falling candies have their position updated."""
        board = Board(seed=42)
        candy = board.get_candy(3, 2)
        original_type = candy.candy_type

        # Create gap below
        board.set_candy(7, 2, None)
        board.set_candy(6, 2, None)
        board.set_candy(5, 2, None)
        board.set_candy(4, 2, None)

        board.apply_gravity()

        # Find where the candy ended up
        found = False
        for row in range(board.rows):
            c = board.get_candy(row, 2)
            if c and c.candy_type == original_type and c is candy:
                assert c.row == row
                assert c.col == 2
                found = True
                break
        assert found

    def test_clear_matches_removes_candies(self):
        """clear_matches removes candies at match positions."""
        board = Board(seed=42)
        # Set up a match
        board.set_candy(0, 0, Candy("virus", 0, 0))
        board.set_candy(0, 1, Candy("virus", 0, 1))
        board.set_candy(0, 2, Candy("virus", 0, 2))

        matches = board.find_matches()
        cleared = board.clear_matches(matches)

        assert cleared >= 3
        assert board.get_candy(0, 0) is None
        assert board.get_candy(0, 1) is None
        assert board.get_candy(0, 2) is None
