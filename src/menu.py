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
    ENTERING_HANDLE = auto()


class Menu:
    """Manages game menus and mode selection."""

    def __init__(self):
        """Initialize menu system."""
        self.state = MenuState.MAIN_MENU
        self.selected_index = 0
        self.final_score = 0
        self.last_mode = MODE_ENDLESS
        self._options: List[Dict] = []

        # Handle input state
        self.handle_input = ""
        self.handle_cursor_visible = True
        self.handle_cursor_timer = 0
        self.pending_score_entry = None  # LeaderboardEntry waiting for handle

        # Leaderboard view state
        self.leaderboard_mode_index = 0  # 0=all, 1=endless, 2=moves, 3=timed
        self.leaderboard_modes = [None, MODE_ENDLESS, MODE_MOVES, MODE_TIMED]
        self.leaderboard_mode_names = ["ALL MODES", "ZEN HACK", "PRECISION", "SPEED RUN"]

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
            {
                "id": "high_scores",
                "name": "HIGH SCORES",
                "description": "View the leaderboard."
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
        if self.state == MenuState.LEADERBOARD:
            self.leaderboard_mode_index = (self.leaderboard_mode_index - 1) % len(self.leaderboard_modes)
        else:
            self.selected_index = (self.selected_index - 1) % len(self._options)

    def navigate_down(self) -> None:
        """Move selection down."""
        if self.state == MenuState.LEADERBOARD:
            self.leaderboard_mode_index = (self.leaderboard_mode_index + 1) % len(self.leaderboard_modes)
        else:
            self.selected_index = (self.selected_index + 1) % len(self._options)

    def confirm(self) -> str:
        """Confirm current selection."""
        if self.state == MenuState.ENTERING_HANDLE:
            return self._confirm_handle()
        elif self.state == MenuState.LEADERBOARD:
            # ESC or Enter returns to previous menu
            self._return_from_leaderboard()
            return "back"

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
            elif option_id == "high_scores":
                self.state = MenuState.LEADERBOARD
                self.leaderboard_mode_index = 0
                return "high_scores"

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

    def show_game_over(self, score: int, is_high_score: bool = False) -> None:
        """
        Show game over menu.

        Args:
            score: Final score to display
            is_high_score: Whether this qualifies for leaderboard
        """
        self.final_score = score

        if is_high_score:
            # Prompt for handle entry
            self.state = MenuState.ENTERING_HANDLE
            self.handle_input = ""
            self.handle_cursor_visible = True
            self.handle_cursor_timer = 0
        else:
            self.state = MenuState.GAME_OVER
            self._setup_game_over_menu()
            self.selected_index = 0

    def show_leaderboard(self) -> None:
        """Show the leaderboard screen."""
        self.state = MenuState.LEADERBOARD
        self.leaderboard_mode_index = 0

    def _return_from_leaderboard(self) -> None:
        """Return from leaderboard to appropriate menu."""
        self.state = MenuState.MAIN_MENU
        self._setup_main_menu()
        self.selected_index = 3  # High Scores option

    def get_current_leaderboard_mode(self) -> Optional[str]:
        """Get the currently selected leaderboard filter mode."""
        return self.leaderboard_modes[self.leaderboard_mode_index]

    def get_current_leaderboard_mode_name(self) -> str:
        """Get display name for current leaderboard mode."""
        return self.leaderboard_mode_names[self.leaderboard_mode_index]

    # Handle input methods
    def handle_text_input(self, char: str) -> None:
        """
        Handle text input for handle entry.

        Args:
            char: Character to add
        """
        if self.state != MenuState.ENTERING_HANDLE:
            return

        # Only allow valid characters
        if char.isalnum() or char in "_-":
            if len(self.handle_input) < 12:
                self.handle_input += char

    def handle_backspace(self) -> None:
        """Handle backspace in handle entry."""
        if self.state == MenuState.ENTERING_HANDLE:
            self.handle_input = self.handle_input[:-1]

    def _confirm_handle(self) -> str:
        """Confirm entered handle and proceed."""
        if len(self.handle_input) >= 2:
            # Valid handle, proceed to game over
            self.state = MenuState.GAME_OVER
            self._setup_game_over_menu()
            self.selected_index = 0
            return "handle_confirmed"
        return "handle_invalid"

    def cancel_handle_entry(self) -> None:
        """Cancel handle entry and go to game over without saving."""
        self.handle_input = ""
        self.pending_score_entry = None
        self.state = MenuState.GAME_OVER
        self._setup_game_over_menu()
        self.selected_index = 0

    def update_cursor(self, dt: float) -> None:
        """
        Update cursor blink animation.

        Args:
            dt: Delta time in seconds
        """
        if self.state == MenuState.ENTERING_HANDLE:
            self.handle_cursor_timer += dt
            if self.handle_cursor_timer >= 0.5:
                self.handle_cursor_timer = 0
                self.handle_cursor_visible = not self.handle_cursor_visible

    def reset(self) -> None:
        """Reset menu to main menu state."""
        self.state = MenuState.MAIN_MENU
        self._setup_main_menu()
        self.selected_index = 0
        self.handle_input = ""
        self.pending_score_entry = None
