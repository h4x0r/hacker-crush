"""TDD tests for leaderboard system."""

import pytest
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leaderboard import LeaderboardClient, LeaderboardEntry
from constants import MODE_ENDLESS, MODE_MOVES, MODE_TIMED


class TestLeaderboardEntry:
    """Tests for leaderboard entry data."""

    def test_create_entry(self):
        """Can create a leaderboard entry."""
        entry = LeaderboardEntry(
            handle="h4x0r",
            score=15000,
            mode=MODE_ENDLESS
        )
        assert entry.handle == "h4x0r"
        assert entry.score == 15000
        assert entry.mode == MODE_ENDLESS

    def test_entry_to_dict(self):
        """Entry can be serialized to dict."""
        entry = LeaderboardEntry(
            handle="test",
            score=10000,
            mode=MODE_MOVES
        )
        data = entry.to_dict()
        assert data["handle"] == "test"
        assert data["score"] == 10000
        assert data["mode"] == MODE_MOVES

    def test_entry_from_dict(self):
        """Entry can be created from dict."""
        data = {"handle": "player1", "score": 5000, "mode": MODE_TIMED, "rank": 5}
        entry = LeaderboardEntry.from_dict(data)
        assert entry.handle == "player1"
        assert entry.score == 5000
        assert entry.rank == 5


class TestHandleValidation:
    """Tests for handle validation."""

    def test_valid_handle(self):
        """Valid handles are accepted."""
        client = LeaderboardClient()
        assert client.validate_handle("h4x0r") is True
        assert client.validate_handle("test_user") is True
        assert client.validate_handle("abc") is True
        assert client.validate_handle("user123name") is True

    def test_handle_too_short(self):
        """Handles under 3 chars are rejected."""
        client = LeaderboardClient()
        assert client.validate_handle("ab") is False
        assert client.validate_handle("x") is False

    def test_handle_too_long(self):
        """Handles over 12 chars are rejected."""
        client = LeaderboardClient()
        assert client.validate_handle("a" * 13) is False
        assert client.validate_handle("verylonghandle") is False

    def test_handle_invalid_chars(self):
        """Handles with invalid chars are rejected."""
        client = LeaderboardClient()
        assert client.validate_handle("has space") is False
        assert client.validate_handle("has@symbol") is False
        assert client.validate_handle("has-dash") is False


class TestLeaderboardClient:
    """Tests for leaderboard client."""

    def test_client_creation(self):
        """Can create leaderboard client."""
        client = LeaderboardClient()
        assert client is not None

    def test_client_has_submit_method(self):
        """Client has submit_score method."""
        client = LeaderboardClient()
        assert hasattr(client, 'submit_score')

    def test_client_has_get_leaderboard_method(self):
        """Client has get_leaderboard method."""
        client = LeaderboardClient()
        assert hasattr(client, 'get_leaderboard')

    def test_format_submit_request(self):
        """Client formats submit request correctly."""
        client = LeaderboardClient()
        entry = LeaderboardEntry(handle="test", score=10000, mode=MODE_ENDLESS)
        request_data = client.format_submit_request(entry)

        assert request_data["handle"] == "test"
        assert request_data["score"] == 10000
        assert request_data["mode"] == MODE_ENDLESS


class TestScoreValidation:
    """Tests for score validation (anti-cheat)."""

    def test_reject_negative_score(self):
        """Negative scores are rejected."""
        client = LeaderboardClient()
        assert client.validate_score(-100) is False

    def test_reject_impossibly_high_score(self):
        """Impossibly high scores are rejected."""
        client = LeaderboardClient()
        # Max reasonable score per move is about 5000 (color bomb combos)
        # 30 moves * 10 cascades * 5000 = 1.5M theoretical max
        assert client.validate_score(10_000_000) is False  # Too high

    def test_accept_reasonable_score(self):
        """Reasonable scores are accepted."""
        client = LeaderboardClient()
        assert client.validate_score(0) is True
        assert client.validate_score(15000) is True
        assert client.validate_score(500000) is True


class TestLocalLeaderboard:
    """Tests for local leaderboard storage (fallback when offline)."""

    def test_save_local_entry(self):
        """Can save entry locally."""
        client = LeaderboardClient()
        entry = LeaderboardEntry(handle="local", score=5000, mode=MODE_ENDLESS)
        client.save_local(entry)

        local_scores = client.get_local_scores(MODE_ENDLESS)
        assert len(local_scores) >= 1
        assert any(e.handle == "local" for e in local_scores)

    def test_local_scores_sorted(self):
        """Local scores are sorted by score descending."""
        client = LeaderboardClient()
        client.clear_local()

        client.save_local(LeaderboardEntry("a", 100, MODE_ENDLESS))
        client.save_local(LeaderboardEntry("b", 300, MODE_ENDLESS))
        client.save_local(LeaderboardEntry("c", 200, MODE_ENDLESS))

        scores = client.get_local_scores(MODE_ENDLESS)
        assert scores[0].score >= scores[1].score >= scores[2].score

    def test_local_scores_limited(self):
        """Local scores are limited to top 10."""
        client = LeaderboardClient()
        client.clear_local()

        for i in range(15):
            client.save_local(LeaderboardEntry(f"p{i}", i * 100, MODE_ENDLESS))

        scores = client.get_local_scores(MODE_ENDLESS)
        assert len(scores) <= 10
