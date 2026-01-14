"""Animation system for smooth visual effects."""

from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum, auto

from constants import (
    CELL_SIZE, GRID_OFFSET_X, GRID_OFFSET_Y,
    ANIM_SWAP, ANIM_INVALID_SWAP, ANIM_MATCH_CLEAR,
    ANIM_CANDY_FALL, ANIM_SPECIAL_CREATE
)
from candy import Candy


class AnimationType(Enum):
    """Types of animations."""
    SWAP = auto()
    INVALID_SWAP = auto()
    FALL = auto()
    CLEAR = auto()
    SPECIAL_CREATE = auto()


@dataclass
class Animation:
    """A single animation instance."""
    anim_type: AnimationType
    candy: Candy
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    duration_ms: float
    elapsed_ms: float = 0
    scale_start: float = 1.0
    scale_end: float = 1.0
    on_complete: Optional[Callable] = None

    @property
    def progress(self) -> float:
        """Get animation progress from 0 to 1."""
        if self.duration_ms <= 0:
            return 1.0
        return min(1.0, self.elapsed_ms / self.duration_ms)

    @property
    def is_complete(self) -> bool:
        """Check if animation is done."""
        return self.elapsed_ms >= self.duration_ms

    @property
    def current_x(self) -> float:
        """Get current x position with easing."""
        t = self._ease_out_quad(self.progress)
        return self.start_x + (self.end_x - self.start_x) * t

    @property
    def current_y(self) -> float:
        """Get current y position with easing."""
        t = self._ease_out_quad(self.progress)
        return self.start_y + (self.end_y - self.start_y) * t

    @property
    def current_scale(self) -> float:
        """Get current scale."""
        t = self.progress
        return self.scale_start + (self.scale_end - self.scale_start) * t

    def _ease_out_quad(self, t: float) -> float:
        """Quadratic ease-out function."""
        return 1 - (1 - t) ** 2

    def update(self, delta_ms: float) -> None:
        """Update animation by delta time."""
        self.elapsed_ms += delta_ms


class AnimationManager:
    """Manages all active animations."""

    def __init__(self):
        self.animations: List[Animation] = []
        self._candy_positions: dict = {}  # candy -> (x, y, scale)

    @property
    def is_animating(self) -> bool:
        """Check if any animations are running."""
        return len(self.animations) > 0

    def update(self, delta_ms: float) -> None:
        """Update all animations."""
        completed = []

        for anim in self.animations:
            anim.update(delta_ms)

            # Update candy position for rendering
            self._candy_positions[anim.candy] = (
                anim.current_x,
                anim.current_y,
                anim.current_scale
            )

            if anim.is_complete:
                completed.append(anim)

        # Remove completed animations
        for anim in completed:
            self.animations.remove(anim)
            if anim.candy in self._candy_positions:
                del self._candy_positions[anim.candy]
            if anim.on_complete:
                anim.on_complete()

    def get_candy_render_pos(self, candy: Candy) -> Tuple[float, float, float]:
        """
        Get render position for a candy.

        Returns:
            (x, y, scale) - either animated position or grid position
        """
        if candy in self._candy_positions:
            return self._candy_positions[candy]

        # Default to grid position
        x = GRID_OFFSET_X + candy.col * CELL_SIZE + CELL_SIZE // 2
        y = GRID_OFFSET_Y + candy.row * CELL_SIZE + CELL_SIZE // 2
        return (x, y, 1.0)

    def add_swap(self, candy1: Candy, candy2: Candy, on_complete: Callable = None) -> None:
        """Add swap animation between two candies."""
        # Get pixel positions
        x1 = GRID_OFFSET_X + candy1.col * CELL_SIZE + CELL_SIZE // 2
        y1 = GRID_OFFSET_Y + candy1.row * CELL_SIZE + CELL_SIZE // 2
        x2 = GRID_OFFSET_X + candy2.col * CELL_SIZE + CELL_SIZE // 2
        y2 = GRID_OFFSET_Y + candy2.row * CELL_SIZE + CELL_SIZE // 2

        # Candy 1 moves to candy 2's position
        self.animations.append(Animation(
            anim_type=AnimationType.SWAP,
            candy=candy1,
            start_x=x1, start_y=y1,
            end_x=x2, end_y=y2,
            duration_ms=ANIM_SWAP
        ))

        # Candy 2 moves to candy 1's position
        self.animations.append(Animation(
            anim_type=AnimationType.SWAP,
            candy=candy2,
            start_x=x2, start_y=y2,
            end_x=x1, end_y=y1,
            duration_ms=ANIM_SWAP,
            on_complete=on_complete
        ))

    def add_invalid_swap(self, candy1: Candy, candy2: Candy, on_complete: Callable = None) -> None:
        """Add invalid swap animation (bounce back)."""
        x1 = GRID_OFFSET_X + candy1.col * CELL_SIZE + CELL_SIZE // 2
        y1 = GRID_OFFSET_Y + candy1.row * CELL_SIZE + CELL_SIZE // 2
        x2 = GRID_OFFSET_X + candy2.col * CELL_SIZE + CELL_SIZE // 2
        y2 = GRID_OFFSET_Y + candy2.row * CELL_SIZE + CELL_SIZE // 2

        # Move halfway then back
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        # This is simplified - would need two-phase animation for true bounce
        self.animations.append(Animation(
            anim_type=AnimationType.INVALID_SWAP,
            candy=candy1,
            start_x=x1, start_y=y1,
            end_x=x1, end_y=y1,  # Returns to start
            duration_ms=ANIM_INVALID_SWAP,
            on_complete=on_complete
        ))

    def add_fall(self, candy: Candy, from_row: int, to_row: int, on_complete: Callable = None) -> None:
        """Add falling animation for a candy."""
        x = GRID_OFFSET_X + candy.col * CELL_SIZE + CELL_SIZE // 2
        start_y = GRID_OFFSET_Y + from_row * CELL_SIZE + CELL_SIZE // 2
        end_y = GRID_OFFSET_Y + to_row * CELL_SIZE + CELL_SIZE // 2

        distance = abs(to_row - from_row)
        duration = max(ANIM_CANDY_FALL * distance, 50)  # Minimum 50ms

        self.animations.append(Animation(
            anim_type=AnimationType.FALL,
            candy=candy,
            start_x=x, start_y=start_y,
            end_x=x, end_y=end_y,
            duration_ms=duration,
            on_complete=on_complete
        ))

    def add_clear(self, candy: Candy, on_complete: Callable = None) -> None:
        """Add clearing animation for a matched candy."""
        x = GRID_OFFSET_X + candy.col * CELL_SIZE + CELL_SIZE // 2
        y = GRID_OFFSET_Y + candy.row * CELL_SIZE + CELL_SIZE // 2

        self.animations.append(Animation(
            anim_type=AnimationType.CLEAR,
            candy=candy,
            start_x=x, start_y=y,
            end_x=x, end_y=y,
            duration_ms=ANIM_MATCH_CLEAR,
            scale_start=1.0,
            scale_end=0.0,
            on_complete=on_complete
        ))

    def add_special_create(self, candy: Candy, on_complete: Callable = None) -> None:
        """Add special candy creation animation."""
        x = GRID_OFFSET_X + candy.col * CELL_SIZE + CELL_SIZE // 2
        y = GRID_OFFSET_Y + candy.row * CELL_SIZE + CELL_SIZE // 2

        self.animations.append(Animation(
            anim_type=AnimationType.SPECIAL_CREATE,
            candy=candy,
            start_x=x, start_y=y,
            end_x=x, end_y=y,
            duration_ms=ANIM_SPECIAL_CREATE,
            scale_start=1.5,
            scale_end=1.0,
            on_complete=on_complete
        ))

    def clear_all(self) -> None:
        """Clear all animations."""
        self.animations.clear()
        self._candy_positions.clear()
