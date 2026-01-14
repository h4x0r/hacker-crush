"""Main entry point for Hacker Crush."""

import asyncio
import pygame

from renderer import Renderer
from game_state import GameState
from audio import AudioManager
from animations import AnimationManager
from menu import Menu, MenuState
from constants import MODE_ENDLESS, MODE_MOVES, MODE_TIMED, CELL_SIZE, GRID_OFFSET_X, GRID_OFFSET_Y


class GameController:
    """Controls game flow with animations."""

    def __init__(self):
        self.renderer = None  # Set by main()
        self.audio = None  # Set by main()
        self.animations = AnimationManager()
        self.state = None  # Set by main()

        # Pending actions queue (executed after animations complete)
        self.pending_action = None

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
            for i, (candy, from_row, from_col, to_row, to_col) in enumerate(fall_data):
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
    renderer = Renderer()
    audio = AudioManager()
    menu = Menu()
    game = None

    # Drag state
    dragging = False
    drag_start_pos = None
    drag_start_cell = None

    # Start background music
    audio.start_music()

    running = True

    while running:
        delta = renderer.tick()
        delta_ms = delta * 1000

        # Handle events based on current state
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # Global keys
                if event.key == pygame.K_m:
                    audio.toggle_music()
                elif event.key == pygame.K_s:
                    audio.toggle_sfx()

                # Menu navigation
                elif menu.state == MenuState.MAIN_MENU:
                    if event.key == pygame.K_UP:
                        menu.navigate_up()
                    elif event.key == pygame.K_DOWN:
                        menu.navigate_down()
                    elif event.key == pygame.K_RETURN:
                        mode = menu.confirm()
                        if menu.state == MenuState.GAME_STARTING:
                            game = GameController()
                            game.state = GameState(mode)
                            game.renderer = renderer
                            game.audio = audio
                            dragging = False
                    elif event.key == pygame.K_ESCAPE:
                        running = False

                # Game over menu
                elif menu.state == MenuState.GAME_OVER:
                    if event.key == pygame.K_UP:
                        menu.navigate_up()
                    elif event.key == pygame.K_DOWN:
                        menu.navigate_down()
                    elif event.key == pygame.K_RETURN:
                        result = menu.confirm()
                        if result == "play_again":
                            game = GameController()
                            game.state = GameState(menu.last_mode)
                            game.renderer = renderer
                            game.audio = audio
                            dragging = False
                        elif result == "main_menu":
                            game = None

                # In-game keys
                elif menu.state == MenuState.GAME_STARTING and game:
                    if event.key == pygame.K_ESCAPE:
                        if game.state.is_game_over:
                            menu.show_game_over(game.state.score)
                        else:
                            # Return to main menu
                            menu.reset()
                            game = None

            # Game input (only when playing)
            elif menu.state == MenuState.GAME_STARTING and game:
                if not game.animations.is_animating and not game.state.is_game_over:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        pos = renderer.grid_pos_from_mouse(event.pos)
                        if pos:
                            dragging = True
                            drag_start_pos = event.pos
                            drag_start_cell = pos

                    elif event.type == pygame.MOUSEBUTTONUP and dragging:
                        if drag_start_cell:
                            end_pos = renderer.grid_pos_from_mouse(event.pos)

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

        # Update game state
        if menu.state == MenuState.GAME_STARTING and game:
            game.animations.update(delta_ms)

            # Update time for timed mode
            if game.state.mode == MODE_TIMED and not game.state.is_game_over:
                game.state.update_time(delta)
                if game.state.is_game_over:
                    audio.play("game_over")
                    menu.show_game_over(game.state.score)

            # Check for game over transition
            if game.state.is_game_over and menu.state != MenuState.GAME_OVER:
                menu.show_game_over(game.state.score)

        # Render
        renderer.clear()

        if menu.state == MenuState.MAIN_MENU:
            renderer.draw_menu(menu.get_options(), menu.selected_index)

        elif menu.state == MenuState.GAME_STARTING and game:
            renderer.draw_grid()
            game.draw_board_animated()
            renderer.draw_score(game.state.score)

            if hasattr(game.state, 'moves_remaining'):
                renderer.draw_moves(game.state.moves_remaining)
            elif hasattr(game.state, 'time_remaining'):
                renderer.draw_time(game.state.time_remaining)

            if dragging and drag_start_cell and drag_start_pos and not game.animations.is_animating:
                renderer.draw_selection(drag_start_cell[0], drag_start_cell[1])
                current_pos = pygame.mouse.get_pos()
                renderer.draw_drag_line(drag_start_pos, current_pos)

        elif menu.state == MenuState.GAME_OVER:
            # Draw game in background
            if game:
                renderer.draw_grid()
                game.draw_board_animated()
            renderer.draw_game_over_menu(menu.final_score, menu.get_options(), menu.selected_index)

        renderer.update()
        await asyncio.sleep(0)

    audio.cleanup()
    renderer.quit()


if __name__ == "__main__":
    asyncio.run(main())
