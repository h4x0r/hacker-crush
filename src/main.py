"""Main entry point for Hacker Crush."""

import asyncio
import pygame

from renderer import Renderer
from game_state import GameState
from audio import AudioManager
from constants import MODE_ENDLESS, MODE_MOVES, MODE_TIMED, CELL_SIZE


async def main():
    """Main game loop."""
    renderer = Renderer()
    audio = AudioManager()
    state = GameState(MODE_ENDLESS)

    # Start background music
    audio.start_music()

    # Drag state
    dragging = False
    drag_start_pos = None
    drag_start_cell = None

    running = True

    while running:
        delta = renderer.tick()

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state.is_game_over:
                        running = False
                    else:
                        dragging = False
                        drag_start_pos = None
                        drag_start_cell = None
                elif event.key == pygame.K_r and state.is_game_over:
                    # Restart game
                    state = GameState(MODE_ENDLESS)
                    dragging = False
                    drag_start_pos = None
                    drag_start_cell = None
                elif event.key == pygame.K_m:
                    # Toggle music
                    audio.toggle_music()
                elif event.key == pygame.K_s:
                    # Toggle sound effects
                    audio.toggle_sfx()

            elif event.type == pygame.MOUSEBUTTONDOWN and not state.is_game_over:
                pos = renderer.grid_pos_from_mouse(event.pos)
                if pos:
                    dragging = True
                    drag_start_pos = event.pos
                    drag_start_cell = pos

            elif event.type == pygame.MOUSEBUTTONUP and dragging:
                if drag_start_cell:
                    end_pos = renderer.grid_pos_from_mouse(event.pos)

                    # Calculate drag direction based on movement
                    if end_pos is None and drag_start_pos:
                        # Dragged outside grid - determine direction from delta
                        dx = event.pos[0] - drag_start_pos[0]
                        dy = event.pos[1] - drag_start_pos[1]

                        r1, c1 = drag_start_cell

                        # Determine target cell based on drag direction
                        if abs(dx) > abs(dy):
                            # Horizontal drag
                            if dx > CELL_SIZE // 3:
                                end_pos = (r1, c1 + 1)
                            elif dx < -CELL_SIZE // 3:
                                end_pos = (r1, c1 - 1)
                        else:
                            # Vertical drag
                            if dy > CELL_SIZE // 3:
                                end_pos = (r1 + 1, c1)
                            elif dy < -CELL_SIZE // 3:
                                end_pos = (r1 - 1, c1)

                    if end_pos and end_pos != drag_start_cell:
                        r1, c1 = drag_start_cell
                        r2, c2 = end_pos

                        # Check if it's a valid adjacent swap
                        if state.board.is_adjacent(r1, c1, r2, c2):
                            if state.board.would_create_match(r1, c1, r2, c2):
                                state.board.swap(r1, c1, r2, c2)
                                audio.play("swap")

                                # Process matches
                                cascade_level = 1
                                while True:
                                    matches = state.board.find_matches()
                                    if not matches:
                                        break

                                    # Play cascade sound
                                    audio.play_cascade(cascade_level)

                                    # Score for matches
                                    for match in matches:
                                        state.add_match_score(len(match), cascade_level)
                                        audio.play_match(len(match))

                                        # Check for special candy creation
                                        classification = state.board.classify_match(match)
                                        if classification["type"] != "basic":
                                            state.add_special_bonus(classification["type"])
                                            audio.play_special(classification["type"])

                                    # Clear, gravity, refill
                                    state.board.clear_matches(matches)
                                    state.board.apply_gravity()
                                    state.board.refill()
                                    cascade_level += 1

                                # Use move if in moves mode
                                if hasattr(state, 'moves_remaining'):
                                    state.use_move()

                                # Check for game over
                                has_moves = state.board.has_valid_moves()
                                if not has_moves:
                                    if state.mode == MODE_ENDLESS:
                                        if state.reshuffles_remaining > 0:
                                            state.use_reshuffle()
                                        else:
                                            state.is_game_over = True
                                            audio.play("game_over")
                                    else:
                                        state.is_game_over = True
                                        audio.play("game_over")

                                state.check_game_over(has_moves)
                            else:
                                # Invalid swap
                                audio.play("invalid")

                dragging = False
                drag_start_pos = None
                drag_start_cell = None

            elif event.type == pygame.MOUSEMOTION and dragging:
                # Could add visual feedback during drag here
                pass

        # Update time for timed mode
        if state.mode == MODE_TIMED and not state.is_game_over:
            state.update_time(delta)
            if state.is_game_over:
                audio.play("game_over")

        # Render
        renderer.clear()
        renderer.draw_grid()
        renderer.draw_board(state.board)
        renderer.draw_score(state.score)

        # Mode-specific UI
        if hasattr(state, 'moves_remaining'):
            renderer.draw_moves(state.moves_remaining)
        elif hasattr(state, 'time_remaining'):
            renderer.draw_time(state.time_remaining)

        # Draw drag indicator
        if dragging and drag_start_cell and drag_start_pos:
            renderer.draw_selection(drag_start_cell[0], drag_start_cell[1])
            current_pos = pygame.mouse.get_pos()
            renderer.draw_drag_line(drag_start_pos, current_pos)

        if state.is_game_over:
            renderer.draw_game_over(state.score)

        renderer.update()

        # Yield for Pygbag async
        await asyncio.sleep(0)

    audio.cleanup()
    renderer.quit()


if __name__ == "__main__":
    asyncio.run(main())
