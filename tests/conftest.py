"""Pytest fixtures for Hacker Crush tests."""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def empty_grid():
    """Return an 8x8 grid of None values."""
    return [[None for _ in range(8)] for _ in range(8)]


@pytest.fixture
def sample_candy_grid():
    """Return a simple grid with known candy positions for testing."""
    # Grid with a horizontal match in row 0
    grid = [[None for _ in range(8)] for _ in range(8)]
    return grid
