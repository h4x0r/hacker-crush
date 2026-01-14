"""Main entry point for Hacker Crush."""

import asyncio
import pygame

from renderer import Renderer
from game_state import GameState
from constants import MODE_ENDLESS, MODE_MOVES, MODE_TIMED


async def main():
    """Main game loop."""
    renderer = Renderer()
    state = GameState(MODE_ENDLESS)

    selected = None  # Currently selected cell
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
                        selected = None
                elif event.key == pygame.K_r and state.is_game_over:
                    # Restart game
                    state = GameState(MODE_ENDLESS)
                    selected = None

            elif event.type == pygame.MOUSEBUTTONDOWN and not state.is_game_over:
                pos = renderer.grid_pos_from_mouse(event.pos)
                if pos:
                    if selected is None:
                        selected = pos
                    else:
                        # Try to swap
                        r1, c1 = selected
                        r2, c2 = pos

                        if state.board.is_adjacent(r1, c1, r2, c2):
                            if state.board.would_create_match(r1, c1, r2, c2):
                                state.board.swap(r1, c1, r2, c2)

                                # Process matches
                                cascade_level = 1
                                while True:
                                    matches = state.board.find_matches()
                                    if not matches:
                                        break

                                    # Score for matches
                                    for match in matches:
                                        state.add_match_score(len(match), cascade_level)

                                        # Check for special candy creation
                                        classification = state.board.classify_match(match)
                                        if classification["type"] != "basic":
                                            state.add_special_bonus(classification["type"])

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
                                    else:
                                        state.is_game_over = True

                                state.check_game_over(has_moves)

                        selected = None

        # Update time for timed mode
        if state.mode == MODE_TIMED and not state.is_game_over:
            state.update_time(delta)

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

        if selected:
            renderer.draw_selection(selected[0], selected[1])

        if state.is_game_over:
            renderer.draw_game_over(state.score)

        renderer.update()

        # Yield for Pygbag async
        await asyncio.sleep(0)

    renderer.quit()


if __name__ == "__main__":
    asyncio.run(main())
