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
