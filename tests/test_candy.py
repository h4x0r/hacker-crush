"""Tests for Candy class."""

import pytest
from candy import Candy
from constants import (
    CANDY_TYPES, SPECIAL_NONE, SPECIAL_STRIPED_H,
    SPECIAL_STRIPED_V, SPECIAL_WRAPPED, SPECIAL_COLOR_BOMB
)


class TestCandyCreation:
    """Tests for creating Candy instances."""

    def test_create_candy_with_valid_type(self):
        """Candy can be created with a valid type."""
        candy = Candy("blackhat")
        assert candy.candy_type == "blackhat"
        assert candy.special == SPECIAL_NONE

    def test_create_candy_with_all_types(self):
        """All candy types can be created."""
        for candy_type in CANDY_TYPES:
            candy = Candy(candy_type)
            assert candy.candy_type == candy_type

    def test_create_candy_with_invalid_type_raises(self):
        """Creating candy with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid candy type"):
            Candy("invalid")

    def test_candy_has_grid_position(self):
        """Candy tracks its grid position."""
        candy = Candy("lock", row=3, col=5)
        assert candy.row == 3
        assert candy.col == 5

    def test_candy_default_position_is_none(self):
        """Candy position defaults to None."""
        candy = Candy("key")
        assert candy.row is None
        assert candy.col is None


class TestCandySpecials:
    """Tests for special candy functionality."""

    def test_candy_default_not_special(self):
        """Candy is not special by default."""
        candy = Candy("virus")
        assert not candy.is_special()

    def test_make_striped_horizontal(self):
        """Candy can become horizontally striped."""
        candy = Candy("defcon")
        candy.make_striped_horizontal()
        assert candy.special == SPECIAL_STRIPED_H
        assert candy.is_special()

    def test_make_striped_vertical(self):
        """Candy can become vertically striped."""
        candy = Candy("ronin")
        candy.make_striped_vertical()
        assert candy.special == SPECIAL_STRIPED_V
        assert candy.is_special()

    def test_make_wrapped(self):
        """Candy can become wrapped."""
        candy = Candy("lock")
        candy.make_wrapped()
        assert candy.special == SPECIAL_WRAPPED
        assert candy.is_special()

    def test_make_color_bomb(self):
        """Candy can become a color bomb."""
        candy = Candy("key")
        candy.make_color_bomb()
        assert candy.special == SPECIAL_COLOR_BOMB
        assert candy.is_special()


class TestCandyEquality:
    """Tests for candy comparison."""

    def test_candies_match_same_type(self):
        """Candies of same type match."""
        candy1 = Candy("blackhat")
        candy2 = Candy("blackhat")
        assert candy1.matches(candy2)

    def test_candies_dont_match_different_type(self):
        """Candies of different types don't match."""
        candy1 = Candy("blackhat")
        candy2 = Candy("virus")
        assert not candy1.matches(candy2)

    def test_color_bomb_matches_anything(self):
        """Color bomb matches any candy type."""
        bomb = Candy("blackhat")
        bomb.make_color_bomb()
        other = Candy("virus")
        assert bomb.matches(other)

    def test_anything_matches_color_bomb(self):
        """Any candy matches a color bomb."""
        bomb = Candy("virus")
        bomb.make_color_bomb()
        other = Candy("lock")
        assert other.matches(bomb)
