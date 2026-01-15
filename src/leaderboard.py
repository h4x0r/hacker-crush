"""Leaderboard client using Cloudflare Worker proxy (no local storage).

Supports both native Python (urllib) and WASM/browser (platform.window JS interop).
"""

import json
import re
import sys
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# Detect if running in web/WASM environment
IS_WEB = sys.platform in ('emscripten', 'wasi')

if IS_WEB:
    import platform
    import asyncio
    HAS_WEB_FETCH = True
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
_fetch_task = None


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


def _js_xhr_get(url: str) -> Optional[str]:
    """Execute synchronous XHR GET via JavaScript (pygbag interop)."""
    # This uses platform.window to call browser's XMLHttpRequest
    # Synchronous XHR is used for simplicity in game loop context
    # The URL is hardcoded to our API endpoint, not user-supplied
    js_code = """
    (function() {
        var xhr = new XMLHttpRequest();
        xhr.open("GET", "%s", false);
        xhr.send();
        if (xhr.status === 200) {
            return xhr.responseText;
        }
        return null;
    })()
    """ % url
    try:
        return platform.window.eval(js_code)
    except Exception:
        return None


def _js_xhr_post(url: str, payload: str) -> int:
    """Execute synchronous XHR POST via JavaScript (pygbag interop)."""
    # Escapes payload for safe embedding in JS string
    escaped_payload = payload.replace("\\", "\\\\").replace("'", "\\'")
    js_code = """
    (function() {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "%s", false);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.send('%s');
        return xhr.status;
    })()
    """ % (url, escaped_payload)
    try:
        return platform.window.eval(js_code)
    except Exception:
        return 0


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
        """Submit score via Cloudflare Worker."""
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
        """Submit score using JavaScript XHR (web/WASM)."""
        try:
            url = f"{self.api_url}/scores"
            payload = json.dumps({
                "handle": entry.handle,
                "score": entry.score,
                "seconds": entry.seconds,
                "mode": entry.mode
            })

            status = _js_xhr_post(url, payload)
            print(f"Leaderboard submit status: {status}")
            return status == 200

        except Exception as e:
            print(f"Leaderboard submit failed (web): {e}")
            return False

    def get_leaderboard(self, mode: str = None, limit: int = 10) -> List[LeaderboardEntry]:
        """Get leaderboard entries via Cloudflare Worker."""
        global _cached_entries

        if IS_WEB and HAS_WEB_FETCH:
            entries = self._fetch_leaderboard_web(mode, limit)
            if entries:
                _cached_entries = entries
            return _cached_entries if _cached_entries else []
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

    def _fetch_leaderboard_web(self, mode: str = None, limit: int = 10) -> List[LeaderboardEntry]:
        """Fetch leaderboard using JavaScript XHR (web/WASM)."""
        try:
            url = f"{self.api_url}/scores"
            response_text = _js_xhr_get(url)

            if response_text:
                data = json.loads(response_text)
                entries = _parse_leaderboard_response(data, mode, limit)
                print(f"Leaderboard loaded: {len(entries)} entries")
                return entries
            else:
                print("Leaderboard fetch: no response")

        except Exception as e:
            print(f"Leaderboard fetch failed (web): {e}")

        return []

    def is_high_score(self, score: int, mode: str) -> bool:
        """Check if score qualifies for leaderboard (any score > 0 qualifies)."""
        return score > 0

    def get_cached_entries(self) -> List[LeaderboardEntry]:
        """Get cached leaderboard entries."""
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
