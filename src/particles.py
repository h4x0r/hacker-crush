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
    RING = auto()         # Expanding ring effect
    GLOW = auto()         # Large glowing orb that fades
    DATA_STREAM = auto()  # Fast horizontal data streaks


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
        elif self.particle_type == ParticleType.RING:
            # Expanding ring - size grows over time
            self.color = (0, 255, 150)
            self.size = 20  # Starting radius
        elif self.particle_type == ParticleType.GLOW:
            # Large glowing orb
            self.color = (100, 255, 100)
            self.size = 30
        elif self.particle_type == ParticleType.DATA_STREAM:
            # Fast data streaks
            self.color = (0, 255, 0)
            self.size = 2
            self.char = random.choice(['>', '|', '-', '=', '#'])

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

    def emit_explosion(self, x: float, y: float, count: int = 20, speed: float = 150) -> None:
        """
        Emit explosion particles radiating outward.

        Args:
            x: X position
            y: Y position
            count: Number of particles
            speed: Base speed of particles
        """
        import math
        for i in range(count):
            angle = (2 * math.pi * i) / count + random.uniform(-0.2, 0.2)
            spd = speed * random.uniform(0.7, 1.3)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            lifetime = random.uniform(0.4, 0.8)

            particle = Particle(
                x=x, y=y,
                vx=vx, vy=vy,
                particle_type=ParticleType.EXPLOSION,
                lifetime=lifetime
            )
            self.particles.append(particle)

    def emit_ring(self, x: float, y: float) -> None:
        """
        Emit an expanding ring effect.

        Args:
            x: X position
            y: Y position
        """
        particle = Particle(
            x=x, y=y,
            vx=0, vy=0,
            particle_type=ParticleType.RING,
            lifetime=0.5
        )
        self.particles.append(particle)

    def emit_glow(self, x: float, y: float) -> None:
        """
        Emit a large glowing orb that fades.

        Args:
            x: X position
            y: Y position
        """
        particle = Particle(
            x=x, y=y,
            vx=0, vy=0,
            particle_type=ParticleType.GLOW,
            lifetime=0.6
        )
        self.particles.append(particle)

    def emit_data_streams(self, x: float, y: float, count: int = 8) -> None:
        """
        Emit fast horizontal data stream particles.

        Args:
            x: X position
            y: Y position
            count: Number of streams
        """
        for _ in range(count):
            # Fast horizontal movement (both directions)
            direction = random.choice([-1, 1])
            vx = direction * random.uniform(200, 400)
            vy = random.uniform(-20, 20)
            lifetime = random.uniform(0.3, 0.6)

            particle = Particle(
                x=x, y=y,
                vx=vx, vy=vy,
                particle_type=ParticleType.DATA_STREAM,
                lifetime=lifetime
            )
            self.particles.append(particle)

    def emit_match_effect(self, x: float, y: float, match_size: int = 3) -> None:
        """
        Emit spectacular particles for a match, scaling dramatically with size.

        Args:
            x: X position
            y: Y position
            match_size: Number of candies in the match (more = more spectacular)
        """
        if match_size >= 7:
            # MASSIVE match - full fireworks display
            self.emit_glow(x, y)
            self.emit_ring(x, y)
            self.emit_explosion(x, y, count=30, speed=200)
            self.emit_data_streams(x, y, count=12)
            self.emit_sparks(x, y, count=30)
            self.emit_binary(x, y, count=15)
        elif match_size >= 6:
            # Huge match - explosion with ring
            self.emit_ring(x, y)
            self.emit_explosion(x, y, count=24, speed=180)
            self.emit_data_streams(x, y, count=8)
            self.emit_sparks(x, y, count=24)
            self.emit_binary(x, y, count=10)
        elif match_size >= 5:
            # Big match - explosion effect
            self.emit_glow(x, y)
            self.emit_explosion(x, y, count=16, speed=150)
            self.emit_sparks(x, y, count=18)
            self.emit_binary(x, y, count=6)
        elif match_size >= 4:
            # Good match - enhanced sparks + data streams
            self.emit_sparks(x, y, count=14)
            self.emit_data_streams(x, y, count=4)
            self.emit_binary(x, y, count=3)
        else:
            # Standard 3-match
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
