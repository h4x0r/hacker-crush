"""Candy class representing game pieces."""

from constants import (
    CANDY_TYPES, SPECIAL_NONE, SPECIAL_STRIPED_H,
    SPECIAL_STRIPED_V, SPECIAL_WRAPPED, SPECIAL_COLOR_BOMB
)


class Candy:
    """A candy piece on the game board."""

    def __init__(self, candy_type: str, row: int = None, col: int = None):
        """
        Create a new candy.

        Args:
            candy_type: One of CANDY_TYPES
            row: Grid row position (optional)
            col: Grid column position (optional)

        Raises:
            ValueError: If candy_type is not valid
        """
        if candy_type not in CANDY_TYPES:
            raise ValueError(f"Invalid candy type: {candy_type}")

        self.candy_type = candy_type
        self.row = row
        self.col = col
        self.special = SPECIAL_NONE

    def is_special(self) -> bool:
        """Return True if this candy has a special effect."""
        return self.special != SPECIAL_NONE

    def make_striped_horizontal(self) -> None:
        """Convert this candy to a horizontal striped candy."""
        self.special = SPECIAL_STRIPED_H

    def make_striped_vertical(self) -> None:
        """Convert this candy to a vertical striped candy."""
        self.special = SPECIAL_STRIPED_V

    def make_wrapped(self) -> None:
        """Convert this candy to a wrapped candy."""
        self.special = SPECIAL_WRAPPED

    def make_color_bomb(self) -> None:
        """Convert this candy to a color bomb."""
        self.special = SPECIAL_COLOR_BOMB

    def matches(self, other: "Candy") -> bool:
        """
        Check if this candy matches another for clearing.

        Color bombs match any candy type.

        Args:
            other: Another candy to compare

        Returns:
            True if candies match
        """
        if other is None:
            return False

        # Color bombs match anything
        if self.special == SPECIAL_COLOR_BOMB or other.special == SPECIAL_COLOR_BOMB:
            return True

        return self.candy_type == other.candy_type

    def __repr__(self) -> str:
        special_str = ""
        if self.special == SPECIAL_STRIPED_H:
            special_str = "[H]"
        elif self.special == SPECIAL_STRIPED_V:
            special_str = "[V]"
        elif self.special == SPECIAL_WRAPPED:
            special_str = "[W]"
        elif self.special == SPECIAL_COLOR_BOMB:
            special_str = "[B]"

        return f"Candy({self.candy_type}{special_str}@{self.row},{self.col})"
