"""Vercel serverless function for leaderboard API."""

import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import urllib.request


KV_URL = os.environ.get("KV_REST_API_URL", "")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN", "")

MAX_SCORE = 10_000_000  # Anti-cheat: reject impossibly high scores


def kv_request(method: str, path: str, body: dict = None) -> dict:
    """Make request to Vercel KV."""
    if not KV_URL or not KV_TOKEN:
        return {"error": "KV not configured"}

    url = f"{KV_URL}{path}"
    headers = {
        "Authorization": f"Bearer {KV_TOKEN}",
        "Content-Type": "application/json"
    }

    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}


def get_leaderboard(mode: str, limit: int = 10) -> list:
    """Get top scores for a mode."""
    key = f"leaderboard:{mode}"
    result = kv_request("GET", f"/zrange/{key}/0/{limit - 1}/REV/WITHSCORES")

    if "result" not in result:
        return []

    # Parse response: [name, score, name, score, ...]
    items = result.get("result", [])
    leaderboard = []
    for i in range(0, len(items), 2):
        if i + 1 < len(items):
            leaderboard.append({
                "handle": items[i],
                "score": int(float(items[i + 1])),
                "rank": len(leaderboard) + 1
            })

    return leaderboard


def submit_score(mode: str, handle: str, score: int) -> dict:
    """Submit a score and return rank."""
    # Validate
    if score > MAX_SCORE or score < 0:
        return {"error": "Invalid score"}
    if not handle or len(handle) < 1 or len(handle) > 12:
        return {"error": "Invalid handle"}
    if mode not in ["endless", "moves", "timed"]:
        return {"error": "Invalid mode"}

    # Sanitize handle
    handle = "".join(c for c in handle if c.isalnum() or c == "_")[:12]

    if not handle:
        return {"error": "Invalid handle"}

    key = f"leaderboard:{mode}"

    # Add to sorted set (higher score = better)
    kv_request("POST", f"/zadd/{key}", {"score": score, "member": handle})

    # Get rank
    rank_result = kv_request("GET", f"/zrevrank/{key}/{handle}")
    rank = rank_result.get("result", 0) + 1

    return {"rank": rank, "handle": handle, "score": score}


class handler(BaseHTTPRequestHandler):
    """HTTP request handler for Vercel."""

    def send_cors_headers(self):
        """Send CORS headers."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_GET(self):
        """Handle GET requests - retrieve leaderboard."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        mode = params.get("mode", ["endless"])[0]
        limit = min(int(params.get("limit", ["10"])[0]), 100)

        leaderboard = get_leaderboard(mode, limit)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(leaderboard).encode())

    def do_POST(self):
        """Handle POST requests - submit score."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()

        try:
            data = json.loads(body)
            mode = data.get("mode", "endless")
            handle = data.get("handle", "")
            score = int(data.get("score", 0))

            result = submit_score(mode, handle, score)

            status = 200 if "error" not in result else 400
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
