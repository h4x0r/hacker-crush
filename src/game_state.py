"""Game state management."""

from board import Board
from constants import (
    MODE_ENDLESS, MODE_MOVES, MODE_TIMED,
    MOVES_INITIAL, MOVES_TARGET_BASE,
    TIMED_INITIAL_SECONDS, TIMED_BONUS_SPECIAL, TIMED_BONUS_COMBO,
    SCORE_BASE, CASCADE_MULTIPLIER,
    SCORE_STRIPED_BONUS, SCORE_WRAPPED_BONUS, SCORE_COLOR_BOMB_BONUS,
    ENDLESS_MAX_RESHUFFLES
)


class GameState:
    """Manages game state for all modes."""

    def __init__(self, mode: str, seed: int = None):
        """
        Initialize game state.

        Args:
            mode: One of MODE_ENDLESS, MODE_MOVES, MODE_TIMED
            seed: Random seed for board (testing)
        """
        self.mode = mode
        self.board = Board(seed=seed)
        self.score = 0
        self.is_game_over = False
        self.cascade_level = 1

        # Mode-specific state
        if mode == MODE_MOVES:
            self.moves_remaining = MOVES_INITIAL
            self.target_score = MOVES_TARGET_BASE
            self.level = 1
        elif mode == MODE_TIMED:
            self.time_remaining = float(TIMED_INITIAL_SECONDS)
        elif mode == MODE_ENDLESS:
            self.reshuffles_remaining = ENDLESS_MAX_RESHUFFLES

    def add_match_score(self, candy_count: int, cascade_level: int = 1) -> int:
        """
        Add score for a match.

        Args:
            candy_count: Number of candies in match
            cascade_level: Current cascade level for multiplier

        Returns:
            Points added
        """
        base_score = candy_count * SCORE_BASE
        multiplier = CASCADE_MULTIPLIER ** (cascade_level - 1)
        points = int(base_score * multiplier)
        self.score += points
        return points

    def add_special_bonus(self, special_type: str) -> int:
        """
        Add bonus for creating a special candy.

        Args:
            special_type: "striped", "wrapped", or "color_bomb"

        Returns:
            Bonus points added
        """
        bonus_map = {
            "striped": SCORE_STRIPED_BONUS,
            "wrapped": SCORE_WRAPPED_BONUS,
            "color_bomb": SCORE_COLOR_BOMB_BONUS,
        }
        bonus = bonus_map.get(special_type, 0)
        self.score += bonus
        return bonus

    # Moves mode methods
    def use_move(self) -> None:
        """Decrement moves counter."""
        if hasattr(self, 'moves_remaining'):
            self.moves_remaining = max(0, self.moves_remaining - 1)

    # Timed mode methods
    def update_time(self, delta_seconds: float) -> None:
        """
        Update time remaining.

        Args:
            delta_seconds: Seconds elapsed since last update
        """
        if hasattr(self, 'time_remaining'):
            self.time_remaining -= delta_seconds
            if self.time_remaining <= 0:
                self.time_remaining = 0
                self.is_game_over = True

    def add_time_bonus_special(self) -> None:
        """Add time bonus for creating special candy."""
        if hasattr(self, 'time_remaining'):
            self.time_remaining += TIMED_BONUS_SPECIAL

    def add_time_bonus_combo(self) -> None:
        """Add time bonus for combo."""
        if hasattr(self, 'time_remaining'):
            self.time_remaining += TIMED_BONUS_COMBO

    # Endless mode methods
    def use_reshuffle(self) -> bool:
        """
        Use a reshuffle if available.

        Returns:
            True if reshuffle was used
        """
        if hasattr(self, 'reshuffles_remaining') and self.reshuffles_remaining > 0:
            self.reshuffles_remaining -= 1
            self.board.shuffle()
            return True
        return False

    def check_game_over(self, has_valid_moves: bool) -> bool:
        """
        Check if game is over based on mode rules.

        Args:
            has_valid_moves: Whether the board has valid moves

        Returns:
            True if game is over
        """
        if self.is_game_over:
            return True

        if self.mode == MODE_MOVES:
            if self.moves_remaining <= 0:
                self.is_game_over = True
        elif self.mode == MODE_ENDLESS:
            if not has_valid_moves:
                if self.reshuffles_remaining <= 0:
                    self.is_game_over = True
        # Timed mode is handled in update_time

        return self.is_game_over
