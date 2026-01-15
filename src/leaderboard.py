"""Dreamlo leaderboard client for score submission and retrieval."""

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

try:
    import urllib.request
    import urllib.parse
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

from constants import MODE_ENDLESS, MODE_MOVES, MODE_TIMED


# Dreamlo configuration
# Get your own keys at https://dreamlo.com/
# Free tier is HTTP only; $5 donation unlocks HTTPS
DREAMLO_PUBLIC_KEY = os.environ.get("DREAMLO_PUBLIC_KEY", "696848b68f40bccf80e13a19")
DREAMLO_PRIVATE_KEY = os.environ.get("DREAMLO_PRIVATE_KEY", "REDACTED_USE_ENV_VAR")
DREAMLO_BASE_URL = "https://dreamlo.com/lb"

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
    """Client for Dreamlo leaderboard operations."""

    def __init__(self, private_key: str = None, public_key: str = None):
        """
        Initialize leaderboard client.

        Args:
            private_key: Dreamlo private key (for writes)
            public_key: Dreamlo public key (for reads)
        """
        self.private_key = private_key or DREAMLO_PRIVATE_KEY
        self.public_key = public_key or DREAMLO_PUBLIC_KEY
        self.base_url = DREAMLO_BASE_URL

        # Local cache/fallback
        self._local_scores: Dict[str, List[LeaderboardEntry]] = {
            MODE_ENDLESS: [],
            MODE_MOVES: [],
            MODE_TIMED: []
        }
        self._local_file = os.path.join(
            os.path.dirname(__file__), "..", "data", "local_scores.json"
        )
        self._load_local()

    def is_configured(self) -> bool:
        """Check if Dreamlo keys are configured."""
        return bool(self.private_key and self.public_key)

    def validate_handle(self, handle: str) -> bool:
        """
        Validate a player handle.

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

        # No reserved/offensive words (basic filter)
        banned = ["admin", "root", "system", "null"]
        if handle.lower() in banned:
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

    def submit_score(self, entry: LeaderboardEntry) -> Optional[int]:
        """
        Submit score to Dreamlo leaderboard.

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

        # Always save locally first
        self._save_local(entry)

        # Try Dreamlo if configured
        if self.is_configured() and HAS_URLLIB:
            try:
                # Dreamlo add format: /add/{name}/{score}/{seconds}/{text}
                # Using mode as the "text" field
                # Add timestamp to handle to make unique per submission
                unique_handle = f"{entry.handle}"

                url = (
                    f"{self.base_url}/{self.private_key}/add/"
                    f"{urllib.parse.quote(unique_handle)}/"
                    f"{entry.score}/"
                    f"{entry.seconds}/"
                    f"{urllib.parse.quote(entry.mode)}"
                )

                req = urllib.request.Request(url, method='GET')
                req.add_header('User-Agent', 'HackerCrush/1.0')

                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        # Get rank from local cache
                        return self._get_local_rank(entry)

            except Exception as e:
                print(f"Dreamlo submit failed: {e}")

        # Return local rank as fallback
        return self._get_local_rank(entry)

    def get_leaderboard(self, mode: str = None, limit: int = 10) -> List[LeaderboardEntry]:
        """
        Get leaderboard entries from Dreamlo.

        Args:
            mode: Game mode to filter (None for all)
            limit: Max entries to return

        Returns:
            List of leaderboard entries
        """
        entries = []

        # Try Dreamlo if configured
        if self.is_configured() and HAS_URLLIB:
            try:
                url = f"{self.base_url}/{self.public_key}/json"

                req = urllib.request.Request(url, method='GET')
                req.add_header('User-Agent', 'HackerCrush/1.0')

                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))

                        # Dreamlo returns {"dreamlo":{"leaderboard":{"entry":[...]}}}
                        leaderboard = data.get("dreamlo", {}).get("leaderboard", {})
                        raw_entries = leaderboard.get("entry", [])

                        # Handle single entry (not wrapped in list)
                        if isinstance(raw_entries, dict):
                            raw_entries = [raw_entries]

                        # Parse and filter
                        rank = 1
                        for raw in raw_entries:
                            entry = LeaderboardEntry.from_dreamlo(raw, rank)
                            if mode is None or entry.mode == mode:
                                entries.append(entry)
                                rank += 1
                                if len(entries) >= limit:
                                    break

                        if entries:
                            return entries

            except Exception as e:
                print(f"Dreamlo fetch failed: {e}")

        # Fallback to local scores
        return self.get_local_scores(mode)[:limit]

    def get_local_scores(self, mode: str = None) -> List[LeaderboardEntry]:
        """
        Get local scores.

        Args:
            mode: Game mode (None for all modes combined)

        Returns:
            List of local entries
        """
        if mode:
            return self._local_scores.get(mode, [])

        # Combine all modes, sort by score
        all_scores = []
        for m in [MODE_ENDLESS, MODE_MOVES, MODE_TIMED]:
            all_scores.extend(self._local_scores.get(m, []))
        all_scores.sort(key=lambda e: e.score, reverse=True)
        return all_scores

    def is_high_score(self, score: int, mode: str) -> bool:
        """
        Check if score qualifies for leaderboard.

        Args:
            score: Score to check
            mode: Game mode

        Returns:
            True if score would make top 10
        """
        local = self.get_local_scores(mode)
        if len(local) < 10:
            return score > 0
        return score > local[-1].score

    def _save_local(self, entry: LeaderboardEntry) -> None:
        """Save entry to local storage."""
        mode = entry.mode
        if mode not in self._local_scores:
            self._local_scores[mode] = []

        # Add timestamp if missing
        if not entry.timestamp:
            entry.timestamp = datetime.now().isoformat()

        self._local_scores[mode].append(entry)

        # Sort by score descending
        self._local_scores[mode].sort(key=lambda e: e.score, reverse=True)

        # Keep only top 10
        self._local_scores[mode] = self._local_scores[mode][:10]

        # Assign ranks
        for i, e in enumerate(self._local_scores[mode]):
            e.rank = i + 1

        self._persist_local()

    def _get_local_rank(self, entry: LeaderboardEntry) -> Optional[int]:
        """Get rank for an entry in local scores."""
        local = self.get_local_scores(entry.mode)
        for i, e in enumerate(local):
            if e.handle == entry.handle and e.score == entry.score:
                return i + 1
        return None

    def clear_local(self) -> None:
        """Clear all local scores."""
        self._local_scores = {
            MODE_ENDLESS: [],
            MODE_MOVES: [],
            MODE_TIMED: []
        }
        self._persist_local()

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

    def _persist_local(self) -> None:
        """Save local scores to file."""
        try:
            os.makedirs(os.path.dirname(self._local_file), exist_ok=True)
            data = {}
            for mode, entries in self._local_scores.items():
                data[mode] = [e.to_dict() for e in entries]
            with open(self._local_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass


# Singleton instance
_client: Optional[LeaderboardClient] = None


def get_client() -> LeaderboardClient:
    """Get the leaderboard client singleton."""
    global _client
    if _client is None:
        _client = LeaderboardClient()
    return _client
