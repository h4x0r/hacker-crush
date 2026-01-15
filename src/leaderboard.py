"""Leaderboard client using Cloudflare Worker proxy (no local storage)."""

import json
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

try:
    import urllib.request
    import urllib.parse
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

from constants import MODE_ENDLESS, MODE_MOVES, MODE_TIMED


# Cloudflare Worker endpoint (proxies to Dreamlo, hides API keys)
LEADERBOARD_API_URL = "https://hacker-crush-leaderboard.securityronin.workers.dev"

# Maximum reasonable score (anti-cheat)
MAX_SCORE = 5_000_000


@dataclass
class LeaderboardEntry:
    """A single leaderboard entry."""
    handle: str
    score: int
    mode: str
    seconds: int = 0
    rank: int = 0
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            "handle": self.handle,
            "score": self.score,
            "mode": self.mode,
            "seconds": self.seconds,
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
            seconds=data.get("seconds", 0),
            rank=data.get("rank", 0),
            timestamp=data.get("timestamp", "")
        )

    @classmethod
    def from_dreamlo(cls, data: Dict[str, Any], rank: int = 0) -> "LeaderboardEntry":
        """Create entry from Dreamlo API response."""
        # Dreamlo returns: name, score, seconds, text, date
        mode = data.get("text", MODE_ENDLESS)
        return cls(
            handle=data.get("name", "???"),
            score=int(data.get("score", 0)),
            mode=mode,
            seconds=int(data.get("seconds", 0)),
            rank=rank,
            timestamp=data.get("date", "")
        )


class LeaderboardClient:
    """Client for leaderboard operations via Cloudflare Worker."""

    def __init__(self):
        """Initialize leaderboard client."""
        self.api_url = LEADERBOARD_API_URL

    def validate_handle(self, handle: str) -> bool:
        """
        Validate a player handle (client-side check).

        Args:
            handle: Handle to validate

        Returns:
            True if valid
        """
        if len(handle) < 2 or len(handle) > 12:
            return False

        # Only alphanumeric, underscore, dash
        if not re.match(r'^[a-zA-Z0-9_\-]+$', handle):
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

    def submit_score(self, entry: LeaderboardEntry) -> bool:
        """
        Submit score via Cloudflare Worker.

        Args:
            entry: Entry to submit

        Returns:
            True if successful, False if failed
        """
        # Validate first
        if not self.validate_handle(entry.handle):
            return False
        if not self.validate_score(entry.score):
            return False

        if not HAS_URLLIB:
            return False

        try:
            url = f"{self.api_url}/scores"
            payload = json.dumps({
                "handle": entry.handle,
                "score": entry.score,
                "seconds": entry.seconds,
                "mode": entry.mode
            }).encode('utf-8')

            req = urllib.request.Request(
                url,
                data=payload,
                method='POST',
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'HackerCrush/1.0'
                }
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200

        except Exception as e:
            print(f"Leaderboard submit failed: {e}")
            return False

    def get_leaderboard(self, mode: str = None, limit: int = 10) -> List[LeaderboardEntry]:
        """
        Get leaderboard entries via Cloudflare Worker.

        Args:
            mode: Game mode to filter (None for all)
            limit: Max entries to return

        Returns:
            List of leaderboard entries (empty list if fetch fails)
        """
        if not HAS_URLLIB:
            return []

        try:
            url = f"{self.api_url}/scores"

            req = urllib.request.Request(url, method='GET')
            req.add_header('User-Agent', 'HackerCrush/1.0')

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))

                    # Dreamlo returns {"dreamlo":{"leaderboard":{"entry":[...]}}}
                    leaderboard = data.get("dreamlo", {}).get("leaderboard", {})
                    if not leaderboard:
                        return []

                    raw_entries = leaderboard.get("entry", [])

                    # Handle single entry (not wrapped in list)
                    if isinstance(raw_entries, dict):
                        raw_entries = [raw_entries]

                    # Parse and filter
                    entries = []
                    rank = 1
                    for raw in raw_entries:
                        entry = LeaderboardEntry.from_dreamlo(raw, rank)
                        if mode is None or entry.mode == mode:
                            entries.append(entry)
                            rank += 1
                            if len(entries) >= limit:
                                break

                    return entries

        except Exception as e:
            print(f"Leaderboard fetch failed: {e}")

        return []

    def is_high_score(self, score: int, mode: str) -> bool:
        """
        Check if score qualifies for leaderboard (any score > 0 qualifies).

        Args:
            score: Score to check
            mode: Game mode

        Returns:
            True if score is worth submitting
        """
        return score > 0


# Singleton instance
_client: Optional[LeaderboardClient] = None


def get_client() -> LeaderboardClient:
    """Get the leaderboard client singleton."""
    global _client
    if _client is None:
        _client = LeaderboardClient()
    return _client
