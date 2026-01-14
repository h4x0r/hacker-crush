"""Board class managing the game grid."""

import random
from typing import Optional, List, Tuple, Set

from candy import Candy
from constants import GRID_ROWS, GRID_COLS, CANDY_TYPES


class Board:
    """The game board containing candies in a grid."""

    def __init__(self, seed: int = None):
        """
        Create a new board filled with candies.

        Args:
            seed: Random seed for reproducible boards (testing)
        """
        self.rows = GRID_ROWS
        self.cols = GRID_COLS
        self._grid: List[List[Optional[Candy]]] = [
            [None for _ in range(self.cols)] for _ in range(self.rows)
        ]

        if seed is not None:
            random.seed(seed)

        self._fill_board()

    def _fill_board(self) -> None:
        """Fill the board with candies, avoiding initial matches."""
        for row in range(self.rows):
            for col in range(self.cols):
                self._place_candy_no_match(row, col)

    def _place_candy_no_match(self, row: int, col: int) -> None:
        """Place a candy that doesn't create an immediate match."""
        available_types = list(CANDY_TYPES)

        # Check horizontal - avoid 3 in a row
        if col >= 2:
            c1 = self.get_candy(row, col - 1)
            c2 = self.get_candy(row, col - 2)
            if c1 and c2 and c1.candy_type == c2.candy_type:
                if c1.candy_type in available_types:
                    available_types.remove(c1.candy_type)

        # Check vertical - avoid 3 in a row
        if row >= 2:
            c1 = self.get_candy(row - 1, col)
            c2 = self.get_candy(row - 2, col)
            if c1 and c2 and c1.candy_type == c2.candy_type:
                if c1.candy_type in available_types:
                    available_types.remove(c1.candy_type)

        candy_type = random.choice(available_types)
        candy = Candy(candy_type, row=row, col=col)
        self._grid[row][col] = candy

    def is_valid_position(self, row: int, col: int) -> bool:
        """Check if position is within grid bounds."""
        return 0 <= row < self.rows and 0 <= col < self.cols

    def get_candy(self, row: int, col: int) -> Optional[Candy]:
        """Get candy at position, or None if out of bounds."""
        if not self.is_valid_position(row, col):
            return None
        return self._grid[row][col]

    def set_candy(self, row: int, col: int, candy: Optional[Candy]) -> None:
        """Set candy at position and update its position attributes."""
        if not self.is_valid_position(row, col):
            return

        self._grid[row][col] = candy
        if candy is not None:
            candy.row = row
            candy.col = col

    def is_adjacent(self, r1: int, c1: int, r2: int, c2: int) -> bool:
        """Check if two positions are adjacent (not diagonal)."""
        row_diff = abs(r1 - r2)
        col_diff = abs(c1 - c2)
        return (row_diff == 1 and col_diff == 0) or (row_diff == 0 and col_diff == 1)

    def swap(self, r1: int, c1: int, r2: int, c2: int) -> None:
        """Swap candies at two positions."""
        candy1 = self.get_candy(r1, c1)
        candy2 = self.get_candy(r2, c2)

        self.set_candy(r1, c1, candy2)
        self.set_candy(r2, c2, candy1)

    def find_matches(self) -> List[Set[Tuple[int, int]]]:
        """
        Find all matches of 3+ candies.

        Returns:
            List of sets, each set containing (row, col) tuples of matched candies
        """
        matches = []

        # Check horizontal matches
        for row in range(self.rows):
            col = 0
            while col < self.cols:
                match = self._find_horizontal_match(row, col)
                if len(match) >= 3:
                    matches.append(match)
                    col += len(match)
                else:
                    col += 1

        # Check vertical matches
        for col in range(self.cols):
            row = 0
            while row < self.rows:
                match = self._find_vertical_match(row, col)
                if len(match) >= 3:
                    matches.append(match)
                    row += len(match)
                else:
                    row += 1

        # Merge overlapping matches
        return self._merge_matches(matches)

    def _find_horizontal_match(self, row: int, start_col: int) -> Set[Tuple[int, int]]:
        """Find horizontal match starting at position."""
        match = set()
        candy = self.get_candy(row, start_col)
        if candy is None:
            return match

        match.add((row, start_col))
        for col in range(start_col + 1, self.cols):
            other = self.get_candy(row, col)
            if other and candy.matches(other) and not other.is_special():
                match.add((row, col))
            else:
                break

        return match

    def _find_vertical_match(self, start_row: int, col: int) -> Set[Tuple[int, int]]:
        """Find vertical match starting at position."""
        match = set()
        candy = self.get_candy(start_row, col)
        if candy is None:
            return match

        match.add((start_row, col))
        for row in range(start_row + 1, self.rows):
            other = self.get_candy(row, col)
            if other and candy.matches(other) and not other.is_special():
                match.add((row, col))
            else:
                break

        return match

    def _merge_matches(self, matches: List[Set[Tuple[int, int]]]) -> List[Set[Tuple[int, int]]]:
        """Merge overlapping match sets."""
        if not matches:
            return []

        merged = []
        for match in matches:
            found_merge = False
            for existing in merged:
                if match & existing:  # If they overlap
                    existing.update(match)
                    found_merge = True
                    break
            if not found_merge:
                merged.append(match.copy())

        return merged
