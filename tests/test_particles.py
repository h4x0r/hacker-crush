"""TDD tests for particle effects system."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from particles import Particle, ParticleSystem, ParticleType


class TestParticle:
    """Tests for individual particles."""

    def test_create_particle(self):
        """Can create a particle."""
        particle = Particle(
            x=100, y=100,
            vx=5, vy=-10,
            particle_type=ParticleType.SPARK
        )
        assert particle.x == 100
        assert particle.y == 100
        assert particle.vx == 5
        assert particle.vy == -10

    def test_particle_updates_position(self):
        """Particle position updates with velocity."""
        particle = Particle(x=100, y=100, vx=10, vy=5)
        particle.update(1.0)  # 1 second
        assert particle.x == 110
        assert particle.y == 105

    def test_particle_has_lifetime(self):
        """Particles have limited lifetime."""
        particle = Particle(x=0, y=0, lifetime=1.0)
        assert particle.is_alive is True

        particle.update(0.5)
        assert particle.is_alive is True

        particle.update(0.6)  # Total 1.1 seconds
        assert particle.is_alive is False

    def test_particle_alpha_fades(self):
        """Particle alpha fades as it ages."""
        particle = Particle(x=0, y=0, lifetime=1.0)
        initial_alpha = particle.alpha

        particle.update(0.5)
        assert particle.alpha < initial_alpha

        particle.update(0.4)  # 90% through lifetime
        assert particle.alpha < 0.2  # Nearly faded


class TestParticleSystem:
    """Tests for particle system management."""

    def test_create_system(self):
        """Can create particle system."""
        system = ParticleSystem()
        assert system is not None
        assert len(system.particles) == 0

    def test_emit_spark_particles(self):
        """Can emit spark particles."""
        system = ParticleSystem()
        system.emit_sparks(100, 100, count=10)
        assert len(system.particles) == 10

    def test_emit_binary_particles(self):
        """Can emit binary digit particles."""
        system = ParticleSystem()
        system.emit_binary(200, 200, count=5)
        assert len(system.particles) == 5

    def test_update_removes_dead_particles(self):
        """Update removes dead particles."""
        system = ParticleSystem()
        system.emit_sparks(100, 100, count=5)

        # Fast forward time to kill particles
        for _ in range(100):
            system.update(0.1)  # 10 seconds total

        assert len(system.particles) == 0

    def test_clear_all_particles(self):
        """Can clear all particles."""
        system = ParticleSystem()
        system.emit_sparks(100, 100, count=20)
        assert len(system.particles) == 20

        system.clear()
        assert len(system.particles) == 0


class TestParticleTypes:
    """Tests for different particle types."""

    def test_spark_has_color(self):
        """Spark particles have green color."""
        particle = Particle(x=0, y=0, particle_type=ParticleType.SPARK)
        assert particle.color[1] > 200  # Green channel high

    def test_binary_has_character(self):
        """Binary particles have 0 or 1 character."""
        particle = Particle(x=0, y=0, particle_type=ParticleType.BINARY)
        assert particle.char in ['0', '1']

    def test_explosion_particles_larger(self):
        """Explosion particles are larger."""
        spark = Particle(x=0, y=0, particle_type=ParticleType.SPARK)
        explosion = Particle(x=0, y=0, particle_type=ParticleType.EXPLOSION)
        assert explosion.size >= spark.size


class TestParticleEffects:
    """Tests for pre-defined particle effects."""

    def test_match_effect(self):
        """Match effect emits sparks at position."""
        system = ParticleSystem()
        system.emit_match_effect(150, 150)
        assert len(system.particles) >= 5

    def test_special_effect(self):
        """Special candy effect emits more particles."""
        system = ParticleSystem()
        system.emit_special_effect(200, 200)
        assert len(system.particles) >= 10

    def test_combo_effect(self):
        """Combo effect emits binary particles."""
        system = ParticleSystem()
        system.emit_combo_effect(100, 100, combo_level=3)
        # More particles for higher combo
        assert len(system.particles) >= 5
