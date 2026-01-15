"""Leaderboard client using Cloudflare Worker proxy (no local storage).

Supports both native Python (urllib) and WASM/browser (platform.window.fetch).
"""

import json
import re
import sys
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# Detect if running in web/WASM environment
IS_WEB = sys.platform in ('emscripten', 'wasi')

if IS_WEB:
    try:
        from platform import window
        HAS_WEB_FETCH = True
    except ImportError:
        HAS_WEB_FETCH = False
    HAS_URLLIB = False
else:
    HAS_WEB_FETCH = False
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

# Cache for leaderboard data (refreshed on fetch)
_cached_entries: List["LeaderboardEntry"] = []
_fetch_in_progress = False
_last_submit_result: Optional[bool] = None


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


def _parse_leaderboard_response(data: Dict, mode: str = None, limit: int = 10) -> List[LeaderboardEntry]:
    """Parse Dreamlo API response into LeaderboardEntry objects."""
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


class LeaderboardClient:
    """Client for leaderboard operations via Cloudflare Worker."""

    def __init__(self):
        """Initialize leaderboard client."""
        self.api_url = LEADERBOARD_API_URL

    def validate_handle(self, handle: str) -> bool:
        """Validate a player handle (client-side check)."""
        if len(handle) < 2 or len(handle) > 12:
            return False
        if not re.match(r'^[a-zA-Z0-9_\-]+$', handle):
            return False
        return True

    def validate_score(self, score: int) -> bool:
        """Validate a score (basic anti-cheat)."""
        if score < 0:
            return False
        if score > MAX_SCORE:
            return False
        return True

    def submit_score(self, entry: LeaderboardEntry) -> bool:
        """
        Submit score via Cloudflare Worker.
        For web builds, this initiates an async fetch - check submit_in_progress().
        """
        if not self.validate_handle(entry.handle):
            return False
        if not self.validate_score(entry.score):
            return False

        if IS_WEB and HAS_WEB_FETCH:
            return self._submit_score_web(entry)
        elif HAS_URLLIB:
            return self._submit_score_native(entry)
        return False

    def _submit_score_native(self, entry: LeaderboardEntry) -> bool:
        """Submit score using urllib (native Python)."""
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

    def _submit_score_web(self, entry: LeaderboardEntry) -> bool:
        """Submit score using JavaScript fetch (web/WASM)."""
        global _fetch_in_progress, _last_submit_result

        try:
            url = f"{self.api_url}/scores"
            payload = json.dumps({
                "handle": entry.handle,
                "score": entry.score,
                "seconds": entry.seconds,
                "mode": entry.mode
            })

            _fetch_in_progress = True
            _last_submit_result = None

            # Use JavaScript fetch via pygbag's window object
            def on_success(response):
                global _fetch_in_progress, _last_submit_result
                _fetch_in_progress = False
                _last_submit_result = response.ok
                print(f"Leaderboard submit: {'success' if response.ok else 'failed'}")

            def on_error(error):
                global _fetch_in_progress, _last_submit_result
                _fetch_in_progress = False
                _last_submit_result = False
                print(f"Leaderboard submit error: {error}")

            # Create fetch options
            options = window.Object.new()
            options.method = "POST"
            options.headers = window.Object.new()
            options.headers["Content-Type"] = "application/json"
            options.headers["User-Agent"] = "HackerCrush/1.0"
            options.body = payload

            # Execute fetch with promise handlers
            promise = window.fetch(url, options)
            promise.then(on_success).catch(on_error)

            return True  # Request initiated (async)

        except Exception as e:
            print(f"Leaderboard submit failed (web): {e}")
            _fetch_in_progress = False
            return False

    def get_leaderboard(self, mode: str = None, limit: int = 10) -> List[LeaderboardEntry]:
        """
        Get leaderboard entries via Cloudflare Worker.
        For web builds, returns cached data and initiates async refresh.
        """
        global _cached_entries

        if IS_WEB and HAS_WEB_FETCH:
            self._fetch_leaderboard_web(mode, limit)
            return _cached_entries
        elif HAS_URLLIB:
            return self._fetch_leaderboard_native(mode, limit)
        return []

    def _fetch_leaderboard_native(self, mode: str = None, limit: int = 10) -> List[LeaderboardEntry]:
        """Fetch leaderboard using urllib (native Python)."""
        try:
            url = f"{self.api_url}/scores"

            req = urllib.request.Request(url, method='GET')
            req.add_header('User-Agent', 'HackerCrush/1.0')

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return _parse_leaderboard_response(data, mode, limit)

        except Exception as e:
            print(f"Leaderboard fetch failed: {e}")

        return []

    def _fetch_leaderboard_web(self, mode: str = None, limit: int = 10) -> None:
        """Fetch leaderboard using JavaScript fetch (web/WASM)."""
        global _fetch_in_progress, _cached_entries

        if _fetch_in_progress:
            return  # Already fetching

        try:
            url = f"{self.api_url}/scores"
            _fetch_in_progress = True

            def on_response(response):
                if response.ok:
                    response.json().then(on_json).catch(on_error)
                else:
                    on_error(f"HTTP {response.status}")

            def on_json(data):
                global _fetch_in_progress, _cached_entries
                _fetch_in_progress = False
                # Convert JS object to Python dict
                try:
                    # pygbag should auto-convert, but handle edge cases
                    if hasattr(data, 'to_py'):
                        data = data.to_py()
                    _cached_entries = _parse_leaderboard_response(data, mode, limit)
                    print(f"Leaderboard loaded: {len(_cached_entries)} entries")
                except Exception as e:
                    print(f"Leaderboard parse error: {e}")
                    _cached_entries = []

            def on_error(error):
                global _fetch_in_progress
                _fetch_in_progress = False
                print(f"Leaderboard fetch error: {error}")

            # Execute fetch
            promise = window.fetch(url)
            promise.then(on_response).catch(on_error)

        except Exception as e:
            print(f"Leaderboard fetch failed (web): {e}")
            _fetch_in_progress = False

    def is_high_score(self, score: int, mode: str) -> bool:
        """Check if score qualifies for leaderboard (any score > 0 qualifies)."""
        return score > 0

    def get_cached_entries(self) -> List[LeaderboardEntry]:
        """Get cached leaderboard entries (for web async pattern)."""
        return _cached_entries

    def is_fetch_in_progress(self) -> bool:
        """Check if a fetch is currently in progress."""
        return _fetch_in_progress


# Singleton instance
_client: Optional[LeaderboardClient] = None


def get_client() -> LeaderboardClient:
    """Get the leaderboard client singleton."""
    global _client
    if _client is None:
        _client = LeaderboardClient()
    return _client
