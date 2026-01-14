"""Particle effects system for visual feedback."""

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional


class ParticleType(Enum):
    """Types of particles."""
    SPARK = auto()
    BINARY = auto()
    EXPLOSION = auto()


@dataclass
class Particle:
    """A single particle with position, velocity, and lifetime."""

    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    particle_type: ParticleType = ParticleType.SPARK
    lifetime: float = 1.0

    # Derived properties set in __post_init__
    age: float = field(default=0.0, init=False)
    color: tuple = field(default=(0, 255, 0), init=False)
    size: int = field(default=3, init=False)
    char: str = field(default="", init=False)
    alpha: float = field(default=1.0, init=False)

    def __post_init__(self):
        """Initialize type-specific properties."""
        if self.particle_type == ParticleType.SPARK:
            # Green sparks for hacker theme
            self.color = (0, 255, 0)
            self.size = 3
        elif self.particle_type == ParticleType.BINARY:
            # Binary digits
            self.color = (0, 200, 0)
            self.size = 4
            self.char = random.choice(['0', '1'])
        elif self.particle_type == ParticleType.EXPLOSION:
            # Larger explosion particles
            self.color = (0, 255, 100)
            self.size = 6

    @property
    def is_alive(self) -> bool:
        """Check if particle is still alive."""
        return self.age < self.lifetime

    def update(self, dt: float) -> None:
        """
        Update particle state.

        Args:
            dt: Delta time in seconds
        """
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Fade alpha over lifetime
        if self.lifetime > 0:
            remaining = max(0, 1 - (self.age / self.lifetime))
            self.alpha = remaining


class ParticleSystem:
    """Manages collections of particles."""

    def __init__(self):
        """Initialize empty particle system."""
        self.particles: List[Particle] = []

    def emit_sparks(self, x: float, y: float, count: int = 10) -> None:
        """
        Emit spark particles at position.

        Args:
            x: X position
            y: Y position
            count: Number of particles to emit
        """
        for _ in range(count):
            vx = random.uniform(-50, 50)
            vy = random.uniform(-80, -20)
            lifetime = random.uniform(0.5, 1.5)

            particle = Particle(
                x=x, y=y,
                vx=vx, vy=vy,
                particle_type=ParticleType.SPARK,
                lifetime=lifetime
            )
            self.particles.append(particle)

    def emit_binary(self, x: float, y: float, count: int = 5) -> None:
        """
        Emit binary digit particles at position.

        Args:
            x: X position
            y: Y position
            count: Number of particles to emit
        """
        for _ in range(count):
            vx = random.uniform(-30, 30)
            vy = random.uniform(-60, -10)
            lifetime = random.uniform(0.8, 2.0)

            particle = Particle(
                x=x, y=y,
                vx=vx, vy=vy,
                particle_type=ParticleType.BINARY,
                lifetime=lifetime
            )
            self.particles.append(particle)

    def emit_match_effect(self, x: float, y: float) -> None:
        """
        Emit particles for a match at position.

        Args:
            x: X position
            y: Y position
        """
        self.emit_sparks(x, y, count=8)

    def emit_special_effect(self, x: float, y: float) -> None:
        """
        Emit particles for special candy activation.

        Args:
            x: X position
            y: Y position
        """
        # More particles for special effects
        self.emit_sparks(x, y, count=15)
        self.emit_binary(x, y, count=5)

    def emit_combo_effect(self, x: float, y: float, combo_level: int = 1) -> None:
        """
        Emit particles for combo effect.

        Args:
            x: X position
            y: Y position
            combo_level: Combo multiplier level
        """
        # Scale particles with combo level
        count = 5 + combo_level * 3
        self.emit_binary(x, y, count=count)

    def update(self, dt: float) -> None:
        """
        Update all particles and remove dead ones.

        Args:
            dt: Delta time in seconds
        """
        for particle in self.particles:
            particle.update(dt)

        # Remove dead particles
        self.particles = [p for p in self.particles if p.is_alive]

    def clear(self) -> None:
        """Remove all particles."""
        self.particles.clear()
