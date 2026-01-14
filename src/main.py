"""Main entry point for Hacker Crush."""

import asyncio
import pygame

from renderer import Renderer
from game_state import GameState
from audio import AudioManager
from animations import AnimationManager
from constants import MODE_ENDLESS, MODE_MOVES, MODE_TIMED, CELL_SIZE, GRID_OFFSET_X, GRID_OFFSET_Y


class GameController:
    """Controls game flow with animations."""

    def __init__(self):
        self.renderer = Renderer()
        self.audio = AudioManager()
        self.animations = AnimationManager()
        self.state = GameState(MODE_ENDLESS)

        # Pending actions queue (executed after animations complete)
        self.pending_action = None

        # Start background music
        self.audio.start_music()

    def start_swap(self, r1: int, c1: int, r2: int, c2: int) -> None:
        """Start a swap with animation."""
        candy1 = self.state.board.get_candy(r1, c1)
        candy2 = self.state.board.get_candy(r2, c2)

        if not candy1 or not candy2:
            return

        # Check if swap creates a match
        if self.state.board.would_create_match(r1, c1, r2, c2):
            self.audio.play("swap")

            # Animate the swap, then process matches
            self.animations.add_swap(
                candy1, candy2,
                on_complete=lambda: self._complete_swap(r1, c1, r2, c2)
            )
        else:
            # Invalid swap - play sound and shake animation
            self.audio.play("invalid")
            self.animations.add_invalid_swap(candy1, candy2)

    def _complete_swap(self, r1: int, c1: int, r2: int, c2: int) -> None:
        """Complete the swap after animation and process matches."""
        # Actually swap in the board
        self.state.board.swap(r1, c1, r2, c2)

        # Process matches with cascade
        self._process_matches(cascade_level=1)

    def _process_matches(self, cascade_level: int) -> None:
        """Process matches, animate clears, then apply gravity."""
        matches = self.state.board.find_matches()

        if not matches:
            # No more matches - check game state
            self._finish_turn()
            return

        # Play cascade sound
        self.audio.play_cascade(cascade_level)

        # Score and animate each match
        for match in matches:
            self.state.add_match_score(len(match), cascade_level)
            self.audio.play_match(len(match))

            # Check for special candy creation
            classification = self.state.board.classify_match(match)
            if classification["type"] != "basic":
                self.state.add_special_bonus(classification["type"])
                self.audio.play_special(classification["type"])

        # Get candies to animate clearing
        candies_to_clear = []
        for match in matches:
            for (row, col) in match:
                candy = self.state.board.get_candy(row, col)
                if candy:
                    candies_to_clear.append(candy)

        # Animate clearing (last one triggers gravity)
        if candies_to_clear:
            for i, candy in enumerate(candies_to_clear):
                is_last = (i == len(candies_to_clear) - 1)
                self.animations.add_clear(
                    candy,
                    on_complete=lambda cl=cascade_level: self._apply_gravity(cl) if is_last else None
                )

            # Clear matches in board immediately (visually they fade out)
            self.state.board.clear_matches(matches)
        else:
            self._apply_gravity(cascade_level)

    def _apply_gravity(self, cascade_level: int) -> None:
        """Apply gravity with fall animations."""
        # Get fall data before applying gravity
        fall_data = self.state.board.apply_gravity()

        # Animate falls
        fall_count = len(fall_data)
        if fall_count > 0:
            for i, (candy, from_row, to_row, col, _) in enumerate(fall_data):
                is_last = (i == fall_count - 1)
                self.animations.add_fall(
                    candy, from_row, to_row,
                    on_complete=lambda cl=cascade_level: self._refill_board(cl) if is_last else None
                )
        else:
            self._refill_board(cascade_level)

    def _refill_board(self, cascade_level: int) -> None:
        """Refill the board and animate new candies falling in."""
        new_candies = self.state.board.refill()

        # Animate new candies falling from top
        if new_candies:
            for i, (candy, row, col) in enumerate(new_candies):
                is_last = (i == len(new_candies) - 1)
                # Animate from above the grid
                self.animations.add_fall(
                    candy, -1, row,
                    on_complete=lambda cl=cascade_level: self._process_matches(cl + 1) if is_last else None
                )
        else:
            # Continue checking for cascade matches
            self._process_matches(cascade_level + 1)

    def _finish_turn(self) -> None:
        """Finish the turn - use move and check game over."""
        # Use move if in moves mode
        if hasattr(self.state, 'moves_remaining'):
            self.state.use_move()

        # Check for game over
        has_moves = self.state.board.has_valid_moves()
        if not has_moves:
            if self.state.mode == MODE_ENDLESS:
                if self.state.reshuffles_remaining > 0:
                    self.state.use_reshuffle()
                else:
                    self.state.is_game_over = True
                    self.audio.play("game_over")
            else:
                self.state.is_game_over = True
                self.audio.play("game_over")

        self.state.check_game_over(has_moves)

    def draw_board_animated(self) -> None:
        """Draw board with animated positions."""
        board = self.state.board
        static_candies = []
        animated_candies = []

        # Separate static and animated candies
        for row in range(board.rows):
            for col in range(board.cols):
                candy = board.get_candy(row, col)
                if candy:
                    x, y, scale = self.animations.get_candy_render_pos(candy)
                    if candy in self.animations._candy_positions:
                        animated_candies.append((candy, x, y, scale))
                    else:
                        static_candies.append((candy, x, y, scale))

        # Draw static candies first (behind)
        for candy, x, y, scale in static_candies:
            self.renderer.draw_candy(candy, x, y, scale)

        # Draw animated candies on top (in front)
        for candy, x, y, scale in animated_candies:
            self.renderer.draw_candy(candy, x, y, scale)


async def main():
    """Main game loop."""
    game = GameController()

    # Drag state
    dragging = False
    drag_start_pos = None
    drag_start_cell = None

    running = True

    while running:
        delta = game.renderer.tick()
        delta_ms = delta * 1000  # Convert to milliseconds for animations

        # Update animations
        game.animations.update(delta_ms)

        # Handle events (blocked during animation)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game.state.is_game_over:
                        running = False
                    else:
                        dragging = False
                        drag_start_pos = None
                        drag_start_cell = None
                elif event.key == pygame.K_r and game.state.is_game_over:
                    # Restart game
                    game.state = GameState(MODE_ENDLESS)
                    game.animations.clear_all()
                    dragging = False
                    drag_start_pos = None
                    drag_start_cell = None
                elif event.key == pygame.K_m:
                    game.audio.toggle_music()
                elif event.key == pygame.K_s:
                    game.audio.toggle_sfx()

            # Only allow input when not animating
            elif not game.animations.is_animating and not game.state.is_game_over:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = game.renderer.grid_pos_from_mouse(event.pos)
                    if pos:
                        dragging = True
                        drag_start_pos = event.pos
                        drag_start_cell = pos

                elif event.type == pygame.MOUSEBUTTONUP and dragging:
                    if drag_start_cell:
                        end_pos = game.renderer.grid_pos_from_mouse(event.pos)

                        # Calculate drag direction based on movement
                        if end_pos is None and drag_start_pos:
                            dx = event.pos[0] - drag_start_pos[0]
                            dy = event.pos[1] - drag_start_pos[1]

                            r1, c1 = drag_start_cell

                            if abs(dx) > abs(dy):
                                if dx > CELL_SIZE // 3:
                                    end_pos = (r1, c1 + 1)
                                elif dx < -CELL_SIZE // 3:
                                    end_pos = (r1, c1 - 1)
                            else:
                                if dy > CELL_SIZE // 3:
                                    end_pos = (r1 + 1, c1)
                                elif dy < -CELL_SIZE // 3:
                                    end_pos = (r1 - 1, c1)

                        if end_pos and end_pos != drag_start_cell:
                            r1, c1 = drag_start_cell
                            r2, c2 = end_pos

                            if game.state.board.is_adjacent(r1, c1, r2, c2):
                                game.start_swap(r1, c1, r2, c2)

                    dragging = False
                    drag_start_pos = None
                    drag_start_cell = None

        # Update time for timed mode
        if game.state.mode == MODE_TIMED and not game.state.is_game_over:
            game.state.update_time(delta)
            if game.state.is_game_over:
                game.audio.play("game_over")

        # Render
        game.renderer.clear()
        game.renderer.draw_grid()
        game.draw_board_animated()
        game.renderer.draw_score(game.state.score)

        # Mode-specific UI
        if hasattr(game.state, 'moves_remaining'):
            game.renderer.draw_moves(game.state.moves_remaining)
        elif hasattr(game.state, 'time_remaining'):
            game.renderer.draw_time(game.state.time_remaining)

        # Draw drag indicator (only when not animating)
        if dragging and drag_start_cell and drag_start_pos and not game.animations.is_animating:
            game.renderer.draw_selection(drag_start_cell[0], drag_start_cell[1])
            current_pos = pygame.mouse.get_pos()
            game.renderer.draw_drag_line(drag_start_pos, current_pos)

        if game.state.is_game_over:
            game.renderer.draw_game_over(game.state.score)

        game.renderer.update()

        # Yield for Pygbag async
        await asyncio.sleep(0)

    game.audio.cleanup()
    game.renderer.quit()


if __name__ == "__main__":
    asyncio.run(main())
