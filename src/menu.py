"""Menu system for game mode selection and game over screens."""

from enum import Enum, auto
from typing import List, Dict, Optional

from constants import MODE_ENDLESS, MODE_MOVES, MODE_TIMED


class MenuState(Enum):
    """States the menu can be in."""
    MAIN_MENU = auto()
    GAME_STARTING = auto()
    GAME_OVER = auto()
    LEADERBOARD = auto()


class Menu:
    """Manages game menus and mode selection."""

    def __init__(self):
        """Initialize menu system."""
        self.state = MenuState.MAIN_MENU
        self.selected_index = 0
        self.final_score = 0
        self.last_mode = MODE_ENDLESS
        self._options: List[Dict] = []
        self._setup_main_menu()

    def _setup_main_menu(self) -> None:
        """Set up main menu options."""
        self._options = [
            {
                "id": MODE_ENDLESS,
                "name": "ZEN HACK",
                "description": "No limits. Play until stuck."
            },
            {
                "id": MODE_MOVES,
                "name": "PRECISION STRIKE",
                "description": "30 moves to hit the target."
            },
            {
                "id": MODE_TIMED,
                "name": "SPEED RUN",
                "description": "90 seconds. Race the clock."
            },
        ]

    def _setup_game_over_menu(self) -> None:
        """Set up game over menu options."""
        self._options = [
            {
                "id": "play_again",
                "name": "REINITIALIZE",
                "description": "Play the same mode again."
            },
            {
                "id": "main_menu",
                "name": "DISCONNECT",
                "description": "Return to main menu."
            },
        ]

    def get_options(self) -> List[Dict]:
        """Get current menu options."""
        return self._options

    def navigate_up(self) -> None:
        """Move selection up."""
        self.selected_index = (self.selected_index - 1) % len(self._options)

    def navigate_down(self) -> None:
        """Move selection down."""
        self.selected_index = (self.selected_index + 1) % len(self._options)

    def confirm(self) -> str:
        """Confirm current selection."""
        option_id = self._options[self.selected_index]["id"]
        return self.select_option(option_id)

    def select_option(self, option_id: str) -> str:
        """
        Select a menu option by ID.

        Args:
            option_id: The option to select

        Returns:
            The selected option ID
        """
        if self.state == MenuState.MAIN_MENU:
            if option_id in [MODE_ENDLESS, MODE_MOVES, MODE_TIMED]:
                self.last_mode = option_id
                self.state = MenuState.GAME_STARTING
                return option_id

        elif self.state == MenuState.GAME_OVER:
            if option_id == "play_again":
                self.state = MenuState.GAME_STARTING
                return "play_again"
            elif option_id == "main_menu":
                self.state = MenuState.MAIN_MENU
                self._setup_main_menu()
                self.selected_index = 0
                return "main_menu"

        return option_id

    def show_game_over(self, score: int) -> None:
        """
        Show game over menu.

        Args:
            score: Final score to display
        """
        self.final_score = score
        self.state = MenuState.GAME_OVER
        self._setup_game_over_menu()
        self.selected_index = 0

    def reset(self) -> None:
        """Reset menu to main menu state."""
        self.state = MenuState.MAIN_MENU
        self._setup_main_menu()
        self.selected_index = 0
