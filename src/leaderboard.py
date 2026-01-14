"""Leaderboard client for score submission and retrieval."""

import json
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from constants import MODE_ENDLESS, MODE_MOVES, MODE_TIMED


# Maximum reasonable score (anti-cheat)
MAX_SCORE = 5_000_000


@dataclass
class LeaderboardEntry:
    """A single leaderboard entry."""
    handle: str
    score: int
    mode: str
    rank: int = 0
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            "handle": self.handle,
            "score": self.score,
            "mode": self.mode,
            "rank": self.rank,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LeaderboardEntry":
        """Create entry from dictionary."""
        return cls(
            handle=data.get("handle", ""),
            score=data.get("score", 0),
            mode=data.get("mode", MODE_ENDLESS),
            rank=data.get("rank", 0),
            timestamp=data.get("timestamp", "")
        )


class LeaderboardClient:
    """Client for leaderboard operations."""

    def __init__(self, api_url: str = None):
        """
        Initialize leaderboard client.

        Args:
            api_url: Base URL for API (None for local-only mode)
        """
        self.api_url = api_url
        self._local_scores: Dict[str, List[LeaderboardEntry]] = {
            MODE_ENDLESS: [],
            MODE_MOVES: [],
            MODE_TIMED: []
        }
        self._local_file = os.path.join(
            os.path.dirname(__file__), "..", "data", "local_scores.json"
        )
        self._load_local()

    def validate_handle(self, handle: str) -> bool:
        """
        Validate a player handle.

        Args:
            handle: Handle to validate

        Returns:
            True if valid
        """
        if len(handle) < 3 or len(handle) > 12:
            return False

        # Only alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', handle):
            return False

        return True

    def validate_score(self, score: int) -> bool:
        """
        Validate a score (basic anti-cheat).

        Args:
            score: Score to validate

        Returns:
            True if score is reasonable
        """
        if score < 0:
            return False
        if score > MAX_SCORE:
            return False
        return True

    def format_submit_request(self, entry: LeaderboardEntry) -> Dict[str, Any]:
        """
        Format entry for API submission.

        Args:
            entry: Entry to format

        Returns:
            Request data dict
        """
        return {
            "handle": entry.handle,
            "score": entry.score,
            "mode": entry.mode
        }

    async def submit_score(self, entry: LeaderboardEntry) -> Optional[int]:
        """
        Submit score to leaderboard.

        Args:
            entry: Entry to submit

        Returns:
            Rank if successful, None if failed
        """
        # Validate first
        if not self.validate_handle(entry.handle):
            return None
        if not self.validate_score(entry.score):
            return None

        # Always save locally
        self.save_local(entry)

        # If API available, try to submit
        if self.api_url:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    data = self.format_submit_request(entry)
                    async with session.post(
                        f"{self.api_url}/api/scores",
                        json=data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get("rank")
            except Exception:
                pass  # Fall back to local

        # Return local rank
        local = self.get_local_scores(entry.mode)
        for i, e in enumerate(local):
            if e.handle == entry.handle and e.score == entry.score:
                return i + 1
        return None

    async def get_leaderboard(self, mode: str, limit: int = 10) -> List[LeaderboardEntry]:
        """
        Get leaderboard entries.

        Args:
            mode: Game mode
            limit: Max entries to return

        Returns:
            List of leaderboard entries
        """
        # If API available, try to fetch
        if self.api_url:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.api_url}/api/scores",
                        params={"mode": mode, "limit": limit}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return [LeaderboardEntry.from_dict(d) for d in data]
            except Exception:
                pass

        # Return local scores
        return self.get_local_scores(mode)[:limit]

    def save_local(self, entry: LeaderboardEntry) -> None:
        """
        Save entry to local storage.

        Args:
            entry: Entry to save
        """
        mode = entry.mode
        if mode not in self._local_scores:
            self._local_scores[mode] = []

        self._local_scores[mode].append(entry)

        # Sort by score descending
        self._local_scores[mode].sort(key=lambda e: e.score, reverse=True)

        # Keep only top 10
        self._local_scores[mode] = self._local_scores[mode][:10]

        # Assign ranks
        for i, e in enumerate(self._local_scores[mode]):
            e.rank = i + 1

        self._save_local()

    def get_local_scores(self, mode: str) -> List[LeaderboardEntry]:
        """
        Get local scores for a mode.

        Args:
            mode: Game mode

        Returns:
            List of local entries
        """
        return self._local_scores.get(mode, [])

    def clear_local(self) -> None:
        """Clear all local scores."""
        self._local_scores = {
            MODE_ENDLESS: [],
            MODE_MOVES: [],
            MODE_TIMED: []
        }
        self._save_local()

    def _load_local(self) -> None:
        """Load local scores from file."""
        try:
            if os.path.exists(self._local_file):
                with open(self._local_file, 'r') as f:
                    data = json.load(f)
                    for mode in [MODE_ENDLESS, MODE_MOVES, MODE_TIMED]:
                        if mode in data:
                            self._local_scores[mode] = [
                                LeaderboardEntry.from_dict(d) for d in data[mode]
                            ]
        except Exception:
            pass

    def _save_local(self) -> None:
        """Save local scores to file."""
        try:
            os.makedirs(os.path.dirname(self._local_file), exist_ok=True)
            data = {}
            for mode, entries in self._local_scores.items():
                data[mode] = [e.to_dict() for e in entries]
            with open(self._local_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass
