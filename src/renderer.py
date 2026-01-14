"""Pygame rendering module."""

import pygame
from typing import Optional, Tuple, List

from constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, CELL_SIZE, FPS,
    GRID_OFFSET_X, GRID_OFFSET_Y, GRID_ROWS, GRID_COLS,
    COLOR_BG, COLOR_GRID, COLOR_PRIMARY, COLOR_ACCENT, COLOR_WHITE,
    SPECIAL_STRIPED_H, SPECIAL_STRIPED_V, SPECIAL_WRAPPED, SPECIAL_COLOR_BOMB
)
from board import Board
from candy import Candy


class Renderer:
    """Handles all Pygame rendering."""

    def __init__(self):
        """Initialize Pygame and create window."""
        pygame.init()
        pygame.display.set_caption("Hacker Crush")

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Placeholder candy colors (will be replaced with sprites)
        self.candy_colors = {
            "blackhat": (40, 40, 40),       # Dark gray
            "defcon": (255, 0, 0),           # Red
            "ronin": (0, 200, 255),          # Cyan
            "lock": (0, 255, 0),             # Green
            "key": (255, 255, 0),            # Yellow
            "virus": (255, 0, 255),          # Magenta
        }

    def clear(self) -> None:
        """Clear screen with background color."""
        self.screen.fill(COLOR_BG)

    def draw_grid(self) -> None:
        """Draw the game grid."""
        for row in range(GRID_ROWS + 1):
            y = GRID_OFFSET_Y + row * CELL_SIZE
            start = (GRID_OFFSET_X, y)
            end = (GRID_OFFSET_X + GRID_COLS * CELL_SIZE, y)
            pygame.draw.line(self.screen, COLOR_GRID, start, end, 1)

        for col in range(GRID_COLS + 1):
            x = GRID_OFFSET_X + col * CELL_SIZE
            start = (x, GRID_OFFSET_Y)
            end = (x, GRID_OFFSET_Y + GRID_ROWS * CELL_SIZE)
            pygame.draw.line(self.screen, COLOR_GRID, start, end, 1)

    def draw_candy(self, candy: Candy, x: float, y: float, scale: float = 1.0) -> None:
        """
        Draw a candy at pixel position.

        Args:
            candy: The candy to draw
            x, y: Pixel position (center of candy)
            scale: Size multiplier for animations
        """
        color = self.candy_colors.get(candy.candy_type, COLOR_WHITE)
        radius = int((CELL_SIZE // 2 - 4) * scale)

        # Draw candy circle
        pygame.draw.circle(self.screen, color, (int(x), int(y)), radius)

        # Draw special indicator
        if candy.is_special():
            self._draw_special_indicator(candy, x, y, radius)

    def _draw_special_indicator(self, candy: Candy, x: float, y: float, radius: int) -> None:
        """Draw indicator for special candies."""
        if candy.special == SPECIAL_STRIPED_H:
            # Horizontal lines
            for i in range(-1, 2):
                pygame.draw.line(
                    self.screen, COLOR_PRIMARY,
                    (int(x - radius), int(y + i * 4)),
                    (int(x + radius), int(y + i * 4)), 2
                )
        elif candy.special == SPECIAL_STRIPED_V:
            # Vertical lines
            for i in range(-1, 2):
                pygame.draw.line(
                    self.screen, COLOR_PRIMARY,
                    (int(x + i * 4), int(y - radius)),
                    (int(x + i * 4), int(y + radius)), 2
                )
        elif candy.special == SPECIAL_WRAPPED:
            # Corner brackets
            pygame.draw.rect(
                self.screen, COLOR_ACCENT,
                (int(x - radius), int(y - radius), radius * 2, radius * 2),
                3
            )
        elif candy.special == SPECIAL_COLOR_BOMB:
            # Outer ring
            pygame.draw.circle(
                self.screen, COLOR_PRIMARY,
                (int(x), int(y)), radius + 4, 3
            )

    def draw_board(self, board: Board) -> None:
        """Draw all candies on the board."""
        for row in range(board.rows):
            for col in range(board.cols):
                candy = board.get_candy(row, col)
                if candy:
                    x = GRID_OFFSET_X + col * CELL_SIZE + CELL_SIZE // 2
                    y = GRID_OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 2
                    self.draw_candy(candy, x, y)

    def draw_score(self, score: int, x: int = 20, y: int = 20) -> None:
        """Draw current score."""
        text = self.font.render(f"SCORE: {score}", True, COLOR_PRIMARY)
        self.screen.blit(text, (x, y))

    def draw_moves(self, moves: int) -> None:
        """Draw moves remaining."""
        text = self.font.render(f"MOVES: {moves}", True, COLOR_PRIMARY)
        self.screen.blit(text, (WINDOW_WIDTH - 150, 20))

    def draw_time(self, seconds: float) -> None:
        """Draw time remaining."""
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        text = self.font.render(f"TIME: {mins}:{secs:02d}", True, COLOR_PRIMARY)
        self.screen.blit(text, (WINDOW_WIDTH - 150, 20))

    def draw_selection(self, row: int, col: int) -> None:
        """Draw selection highlight around a cell."""
        x = GRID_OFFSET_X + col * CELL_SIZE
        y = GRID_OFFSET_Y + row * CELL_SIZE
        pygame.draw.rect(
            self.screen, COLOR_ACCENT,
            (x, y, CELL_SIZE, CELL_SIZE), 3
        )

    def draw_game_over(self, score: int) -> None:
        """Draw game over screen."""
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(COLOR_BG)
        self.screen.blit(overlay, (0, 0))

        # Game over text
        game_over_text = self.font.render("GAME OVER", True, COLOR_PRIMARY)
        score_text = self.font.render(f"Final Score: {score}", True, COLOR_PRIMARY)
        restart_text = self.small_font.render("Press R to restart or ESC to quit", True, COLOR_ACCENT)

        # Center text
        go_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40))
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10))
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60))

        self.screen.blit(game_over_text, go_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(restart_text, restart_rect)

    def grid_pos_from_mouse(self, mouse_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Convert mouse position to grid coordinates.

        Returns:
            (row, col) or None if outside grid
        """
        mx, my = mouse_pos
        col = (mx - GRID_OFFSET_X) // CELL_SIZE
        row = (my - GRID_OFFSET_Y) // CELL_SIZE

        if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
            return (row, col)
        return None

    def update(self) -> None:
        """Update display."""
        pygame.display.flip()

    def tick(self) -> float:
        """
        Tick the clock and return delta time.

        Returns:
            Time since last frame in seconds
        """
        return self.clock.tick(FPS) / 1000.0

    def quit(self) -> None:
        """Clean up Pygame."""
        pygame.quit()
