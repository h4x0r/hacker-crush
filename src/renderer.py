"""Pygame rendering module with hacker theme."""

import pygame
import random
import os
from typing import Optional, Tuple, List

from constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, CELL_SIZE, FPS,
    GRID_OFFSET_X, GRID_OFFSET_Y, GRID_ROWS, GRID_COLS,
    COLOR_BG, COLOR_GRID, COLOR_PRIMARY, COLOR_ACCENT, COLOR_WHITE,
    SPECIAL_STRIPED_H, SPECIAL_STRIPED_V, SPECIAL_WRAPPED, SPECIAL_COLOR_BOMB,
    MODE_ENDLESS, MODE_MOVES, MODE_TIMED
)
from board import Board
from candy import Candy
from particles import Particle, ParticleSystem, ParticleType


class MatrixRain:
    """Falling matrix-style characters effect."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.chars = "01アイウエオカキクケコサシスセソタチツテト"
        self.font_size = 14
        self.columns = width // self.font_size
        self.drops = [random.randint(-20, 0) for _ in range(self.columns)]
        self.font = None  # Set after pygame init

    def init_font(self):
        """Initialize font after pygame is ready."""
        self.font = pygame.font.Font(None, self.font_size)

    def update(self) -> None:
        """Update rain positions."""
        for i in range(len(self.drops)):
            self.drops[i] += 1
            if self.drops[i] * self.font_size > self.height and random.random() > 0.975:
                self.drops[i] = 0

    def draw(self, surface: pygame.Surface) -> None:
        """Draw matrix rain effect."""
        if not self.font:
            self.init_font()

        for i, drop in enumerate(self.drops):
            char = random.choice(self.chars)
            # Dim green for background effect
            color = (0, random.randint(40, 80), 0)
            text = self.font.render(char, True, color)
            x = i * self.font_size
            y = drop * self.font_size
            if 0 <= y < self.height:
                surface.blit(text, (x, y))


class Renderer:
    """Handles all Pygame rendering with hacker theme."""

    def __init__(self):
        """Initialize Pygame and create window."""
        pygame.init()
        pygame.display.set_caption("Hacker Crush")

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        # Try to load monospace font
        self.font = self._load_font(36)
        self.small_font = self._load_font(24)
        self.title_font = self._load_font(48)

        # Load candy sprites
        self.sprites = self._load_sprites()

        # Fallback colors if sprites fail to load
        self.candy_colors = {
            "blackhat": (40, 40, 40),
            "defcon": (255, 0, 0),
            "ronin": (0, 200, 255),
            "lock": (0, 255, 0),
            "key": (255, 255, 0),
            "virus": (255, 0, 255),
        }

        # Matrix rain effect
        self.matrix_rain = MatrixRain(WINDOW_WIDTH, WINDOW_HEIGHT)

        # CRT scanline overlay
        self.scanlines = self._create_scanlines()

        # Dragging state
        self.drag_start = None
        self.drag_candy = None

    def _load_font(self, size: int) -> pygame.font.Font:
        """Load monospace font, fallback to default."""
        # Try common monospace fonts
        mono_fonts = ["Courier New", "Consolas", "Monaco", "monospace"]
        for font_name in mono_fonts:
            try:
                font = pygame.font.SysFont(font_name, size)
                return font
            except:
                continue
        return pygame.font.Font(None, size)

    def _load_sprites(self) -> dict:
        """Load candy sprite images."""
        sprites = {}
        sprite_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "images")

        candy_types = ["blackhat", "defcon", "ronin", "lock", "key", "virus"]

        for candy_type in candy_types:
            path = os.path.join(sprite_dir, f"{candy_type}.png")
            try:
                img = pygame.image.load(path).convert_alpha()
                # Scale to fit cell (with padding)
                target_size = CELL_SIZE - 8
                img = pygame.transform.smoothscale(img, (target_size, target_size))
                sprites[candy_type] = img
            except Exception as e:
                print(f"Warning: Could not load sprite {candy_type}: {e}")
                sprites[candy_type] = None

        return sprites

    def _create_scanlines(self) -> pygame.Surface:
        """Create CRT scanline overlay effect."""
        scanlines = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)

        # Draw horizontal lines every 2 pixels
        for y in range(0, WINDOW_HEIGHT, 3):
            pygame.draw.line(scanlines, (0, 0, 0, 30), (0, y), (WINDOW_WIDTH, y))

        return scanlines

    def clear(self) -> None:
        """Clear screen with background color and draw matrix rain."""
        self.screen.fill(COLOR_BG)

        # Update and draw matrix rain
        self.matrix_rain.update()
        self.matrix_rain.draw(self.screen)

    def draw_grid(self) -> None:
        """Draw the game grid with glow effect."""
        # Draw grid cells with subtle glow
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = GRID_OFFSET_X + col * CELL_SIZE
                y = GRID_OFFSET_Y + row * CELL_SIZE
                # Dark cell background
                pygame.draw.rect(self.screen, (10, 15, 10), (x, y, CELL_SIZE, CELL_SIZE))

        # Draw grid lines
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
        Draw a candy at pixel position using sprite.

        Args:
            candy: The candy to draw
            x, y: Pixel position (center of candy)
            scale: Size multiplier for animations
        """
        sprite = self.sprites.get(candy.candy_type)

        if sprite:
            # Scale sprite if needed
            if scale != 1.0:
                size = int((CELL_SIZE - 8) * scale)
                scaled = pygame.transform.smoothscale(sprite, (size, size))
            else:
                scaled = sprite
                size = CELL_SIZE - 8

            # Center the sprite
            rect = scaled.get_rect(center=(int(x), int(y)))
            self.screen.blit(scaled, rect)
        else:
            # Fallback to colored circle
            color = self.candy_colors.get(candy.candy_type, COLOR_WHITE)
            radius = int((CELL_SIZE // 2 - 4) * scale)
            pygame.draw.circle(self.screen, color, (int(x), int(y)), radius)

        # Draw special indicator overlay
        if candy.is_special():
            self._draw_special_indicator(candy, x, y, int((CELL_SIZE // 2 - 4) * scale))

    def _draw_special_indicator(self, candy: Candy, x: float, y: float, radius: int) -> None:
        """Draw indicator for special candies."""
        if candy.special == SPECIAL_STRIPED_H:
            # Horizontal scan lines
            for i in range(-1, 2):
                pygame.draw.line(
                    self.screen, COLOR_PRIMARY,
                    (int(x - radius), int(y + i * 5)),
                    (int(x + radius), int(y + i * 5)), 3
                )
        elif candy.special == SPECIAL_STRIPED_V:
            # Vertical scan lines
            for i in range(-1, 2):
                pygame.draw.line(
                    self.screen, COLOR_PRIMARY,
                    (int(x + i * 5), int(y - radius)),
                    (int(x + i * 5), int(y + radius)), 3
                )
        elif candy.special == SPECIAL_WRAPPED:
            # Pulsing border with corner brackets
            pygame.draw.rect(
                self.screen, COLOR_ACCENT,
                (int(x - radius), int(y - radius), radius * 2, radius * 2),
                3
            )
        elif candy.special == SPECIAL_COLOR_BOMB:
            # Outer glowing ring
            pygame.draw.circle(
                self.screen, COLOR_PRIMARY,
                (int(x), int(y)), radius + 6, 3
            )
            pygame.draw.circle(
                self.screen, COLOR_ACCENT,
                (int(x), int(y)), radius + 3, 2
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
        """Draw current score with terminal style."""
        # Blinking cursor effect
        cursor = "_" if pygame.time.get_ticks() % 1000 < 500 else " "
        text = self.font.render(f"> SCORE: {score}{cursor}", True, COLOR_PRIMARY)
        self.screen.blit(text, (x, y))

    def draw_moves(self, moves: int) -> None:
        """Draw moves remaining."""
        text = self.font.render(f"MOVES: {moves}", True, COLOR_PRIMARY)
        self.screen.blit(text, (WINDOW_WIDTH - 180, 20))

    def draw_time(self, seconds: float) -> None:
        """Draw time remaining."""
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        text = self.font.render(f"TIME: {mins}:{secs:02d}", True, COLOR_PRIMARY)
        # Right-align with padding from edge
        text_rect = text.get_rect(right=WINDOW_WIDTH - 20, top=20)
        self.screen.blit(text, text_rect)

    def draw_selection(self, row: int, col: int) -> None:
        """Draw selection highlight around a cell."""
        x = GRID_OFFSET_X + col * CELL_SIZE
        y = GRID_OFFSET_Y + row * CELL_SIZE
        pygame.draw.rect(
            self.screen, COLOR_ACCENT,
            (x, y, CELL_SIZE, CELL_SIZE), 3
        )

    def draw_drag_line(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> None:
        """Draw line showing drag direction."""
        pygame.draw.line(self.screen, COLOR_ACCENT, start_pos, end_pos, 2)

    def draw_particles(self, particle_system: ParticleSystem) -> None:
        """
        Draw all particles in the system.

        Args:
            particle_system: The particle system to render
        """
        for particle in particle_system.particles:
            # Calculate alpha-adjusted color
            r, g, b = particle.color
            alpha = int(particle.alpha * 255)

            if particle.particle_type == ParticleType.BINARY:
                # Draw binary digit as text
                if not hasattr(self, '_particle_font'):
                    self._particle_font = self._load_font(16)

                # Create surface with alpha
                text_surface = self._particle_font.render(particle.char, True, (r, g, b))
                text_surface.set_alpha(alpha)
                self.screen.blit(text_surface, (int(particle.x), int(particle.y)))
            else:
                # Draw as glowing circle
                size = particle.size

                # Outer glow (larger, more transparent)
                glow_surface = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
                glow_alpha = int(alpha * 0.3)
                pygame.draw.circle(glow_surface, (r, g, b, glow_alpha),
                                 (size * 2, size * 2), size * 2)
                self.screen.blit(glow_surface,
                               (int(particle.x - size * 2), int(particle.y - size * 2)))

                # Inner bright core
                core_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(core_surface, (r, g, b, alpha),
                                 (size, size), size)
                self.screen.blit(core_surface,
                               (int(particle.x - size), int(particle.y - size)))

    def draw_game_over(self, score: int) -> None:
        """Draw game over screen with hacker style."""
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(COLOR_BG)
        self.screen.blit(overlay, (0, 0))

        # Glitch effect box
        box_width, box_height = 400, 200
        box_x = (WINDOW_WIDTH - box_width) // 2
        box_y = (WINDOW_HEIGHT - box_height) // 2

        pygame.draw.rect(self.screen, COLOR_PRIMARY,
                        (box_x, box_y, box_width, box_height), 2)

        # Terminal-style text
        lines = [
            "> SYSTEM BREACH TERMINATED",
            f"> FINAL_SCORE = {score}",
            "",
            "[R] REINITIALIZE",
            "[ESC] DISCONNECT"
        ]

        for i, line in enumerate(lines):
            font = self.font if i < 2 else self.small_font
            color = COLOR_PRIMARY if i < 2 else COLOR_ACCENT
            text = font.render(line, True, color)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, box_y + 40 + i * 35))
            self.screen.blit(text, text_rect)

    def draw_scanlines(self) -> None:
        """Draw CRT scanline overlay."""
        self.screen.blit(self.scanlines, (0, 0))

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
        """Update display with scanline overlay."""
        self.draw_scanlines()
        pygame.display.flip()

    def tick(self) -> float:
        """
        Tick the clock and return delta time.

        Returns:
            Time since last frame in seconds
        """
        return self.clock.tick(FPS) / 1000.0

    def draw_menu(self, options: list, selected_index: int, title: str = "HACKER CRUSH") -> None:
        """
        Draw the main menu.

        Args:
            options: List of menu option dicts with 'name' and 'description'
            selected_index: Currently selected option index
            title: Menu title
        """
        # Draw title with glitch effect
        title_text = self.title_font.render(f"> {title}_", True, COLOR_PRIMARY)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 100))
        self.screen.blit(title_text, title_rect)

        # Draw subtitle
        subtitle = self.small_font.render("[ SELECT OPERATION MODE ]", True, COLOR_ACCENT)
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(subtitle, subtitle_rect)

        # Draw options
        start_y = 220
        spacing = 80

        for i, option in enumerate(options):
            y = start_y + i * spacing
            is_selected = (i == selected_index)

            # Draw selection indicator
            if is_selected:
                # Draw box around selected
                box_width = 400
                box_height = 60
                box_x = (WINDOW_WIDTH - box_width) // 2
                box_y = y - 10
                pygame.draw.rect(self.screen, COLOR_PRIMARY,
                               (box_x, box_y, box_width, box_height), 2)

                # Blinking cursor
                cursor = ">" if pygame.time.get_ticks() % 500 < 250 else " "
                prefix = cursor
            else:
                prefix = " "

            # Draw option name
            color = COLOR_PRIMARY if is_selected else COLOR_ACCENT
            name_text = self.font.render(f"{prefix} {option['name']}", True, color)
            name_rect = name_text.get_rect(center=(WINDOW_WIDTH // 2, y + 10))
            self.screen.blit(name_text, name_rect)

            # Draw description
            desc_color = COLOR_WHITE if is_selected else (100, 100, 100)
            desc_text = self.small_font.render(option.get('description', ''), True, desc_color)
            desc_rect = desc_text.get_rect(center=(WINDOW_WIDTH // 2, y + 35))
            self.screen.blit(desc_text, desc_rect)

        # Draw controls hint
        controls = self.small_font.render("[UP/DOWN] Navigate  [ENTER] Select", True, (80, 80, 80))
        controls_rect = controls.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
        self.screen.blit(controls, controls_rect)

    def draw_game_over_menu(self, score: int, options: list, selected_index: int) -> None:
        """
        Draw game over screen with menu options.

        Args:
            score: Final score
            options: Menu options
            selected_index: Currently selected option
        """
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill(COLOR_BG)
        self.screen.blit(overlay, (0, 0))

        # Title
        title_text = self.title_font.render("> BREACH TERMINATED_", True, COLOR_PRIMARY)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(title_text, title_rect)

        # Score
        score_text = self.font.render(f"FINAL_SCORE = {score}", True, COLOR_ACCENT)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, 220))
        self.screen.blit(score_text, score_rect)

        # Options
        start_y = 320
        spacing = 70

        for i, option in enumerate(options):
            y = start_y + i * spacing
            is_selected = (i == selected_index)

            if is_selected:
                box_width = 300
                box_height = 50
                box_x = (WINDOW_WIDTH - box_width) // 2
                box_y = y - 5
                pygame.draw.rect(self.screen, COLOR_PRIMARY,
                               (box_x, box_y, box_width, box_height), 2)
                prefix = ">"
            else:
                prefix = " "

            color = COLOR_PRIMARY if is_selected else COLOR_ACCENT
            text = self.font.render(f"{prefix} [{option['name']}]", True, color)
            rect = text.get_rect(center=(WINDOW_WIDTH // 2, y + 15))
            self.screen.blit(text, rect)

    def quit(self) -> None:
        """Clean up Pygame."""
        pygame.quit()
