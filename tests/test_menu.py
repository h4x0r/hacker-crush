"""TDD tests for game menu system."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from menu import Menu, MenuState
from constants import MODE_ENDLESS, MODE_MOVES, MODE_TIMED


class TestMenuState:
    """Tests for menu state management."""

    def test_initial_state_is_main_menu(self):
        """Menu starts in main menu state."""
        menu = Menu()
        assert menu.state == MenuState.MAIN_MENU

    def test_has_three_game_modes(self):
        """Main menu has all three game modes."""
        menu = Menu()
        options = menu.get_options()
        assert len(options) >= 3
        mode_ids = [opt["id"] for opt in options]
        assert MODE_ENDLESS in mode_ids
        assert MODE_MOVES in mode_ids
        assert MODE_TIMED in mode_ids

    def test_select_endless_mode(self):
        """Selecting endless mode returns correct mode."""
        menu = Menu()
        result = menu.select_option(MODE_ENDLESS)
        assert result == MODE_ENDLESS
        assert menu.state == MenuState.GAME_STARTING

    def test_select_moves_mode(self):
        """Selecting moves mode returns correct mode."""
        menu = Menu()
        result = menu.select_option(MODE_MOVES)
        assert result == MODE_MOVES
        assert menu.state == MenuState.GAME_STARTING

    def test_select_timed_mode(self):
        """Selecting timed mode returns correct mode."""
        menu = Menu()
        result = menu.select_option(MODE_TIMED)
        assert result == MODE_TIMED
        assert menu.state == MenuState.GAME_STARTING


class TestMenuNavigation:
    """Tests for menu navigation."""

    def test_navigate_up(self):
        """Navigate up moves selection."""
        menu = Menu()
        initial = menu.selected_index
        menu.navigate_up()
        # Should wrap or move
        assert menu.selected_index != initial or len(menu.get_options()) == 1

    def test_navigate_down(self):
        """Navigate down moves selection."""
        menu = Menu()
        menu.navigate_down()
        assert menu.selected_index == 1

    def test_navigation_wraps(self):
        """Navigation wraps at boundaries."""
        menu = Menu()
        num_options = len(menu.get_options())

        # Go down past end
        for _ in range(num_options + 1):
            menu.navigate_down()
        assert menu.selected_index == 1  # Wrapped to second item

        # Go up past start
        menu.selected_index = 0
        menu.navigate_up()
        assert menu.selected_index == num_options - 1

    def test_confirm_selection(self):
        """Confirm triggers selection of current option."""
        menu = Menu()
        menu.selected_index = 1  # Moves mode
        result = menu.confirm()
        assert result == MODE_MOVES


class TestMenuModeDescriptions:
    """Tests for mode descriptions."""

    def test_endless_has_description(self):
        """Endless mode has description."""
        menu = Menu()
        options = menu.get_options()
        endless = next(opt for opt in options if opt["id"] == MODE_ENDLESS)
        assert "description" in endless
        assert len(endless["description"]) > 0

    def test_moves_has_description(self):
        """Moves mode has description."""
        menu = Menu()
        options = menu.get_options()
        moves = next(opt for opt in options if opt["id"] == MODE_MOVES)
        assert "description" in moves
        assert len(moves["description"]) > 0

    def test_timed_has_description(self):
        """Timed mode has description."""
        menu = Menu()
        options = menu.get_options()
        timed = next(opt for opt in options if opt["id"] == MODE_TIMED)
        assert "description" in timed
        assert len(timed["description"]) > 0


class TestGameOverMenu:
    """Tests for game over menu."""

    def test_game_over_menu_has_options(self):
        """Game over menu has play again and quit options."""
        menu = Menu()
        menu.show_game_over(12500)
        assert menu.state == MenuState.GAME_OVER
        options = menu.get_options()
        option_ids = [opt["id"] for opt in options]
        assert "play_again" in option_ids
        assert "main_menu" in option_ids

    def test_game_over_stores_score(self):
        """Game over stores final score."""
        menu = Menu()
        menu.show_game_over(15000)
        assert menu.final_score == 15000

    def test_play_again_returns_to_game(self):
        """Play again option starts new game."""
        menu = Menu()
        menu.show_game_over(10000)
        result = menu.select_option("play_again")
        assert result == "play_again"
        assert menu.state == MenuState.GAME_STARTING

    def test_main_menu_returns_to_main(self):
        """Main menu option returns to main menu."""
        menu = Menu()
        menu.show_game_over(10000)
        result = menu.select_option("main_menu")
        assert result == "main_menu"
        assert menu.state == MenuState.MAIN_MENU
