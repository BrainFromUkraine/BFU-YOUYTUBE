"""
BFU YouTube Subscriber Counter — Railway Backend
FastAPI proxy between ESP32 and YouTube Data API v3.

ENV variables required:
  YOUTUBE_API_KEY      — YouTube Data API v3 key
  YOUTUBE_CHANNEL_ID   — YouTube channel ID (starts with UC)
  CACHE_TTL_SECONDS    — how long to cache the result (default: 30)
  DEVICE_API_TOKEN     — optional token for X-Device-Token header auth
"""

import os
import time
import logging

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ─── LOGGING ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ─── CONFIG FROM ENV ─────────────────────────────────────────────────────────
YOUTUBE_API_KEY    = os.environ.get("YOUTUBE_API_KEY", "")
YOUTUBE_CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID", "")
CACHE_TTL_SECONDS  = int(os.environ.get("CACHE_TTL_SECONDS", "30"))
DEVICE_API_TOKEN   = os.environ.get("DEVICE_API_TOKEN", "")

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/channels"
REQUEST_TIMEOUT = 10  # seconds

# ─── IN-MEMORY CACHE ─────────────────────────────────────────────────────────
_cache: dict = {
    "subscribers": None,
    "updated_at": None,
    "timestamp": 0.0,
}

# ─── APP ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="BFU YouTube Subscriber Counter API",
    description="Proxy backend for ESP32 YouTube subscriber counter. Caches YouTube Data API responses.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ─── AUTH DEPENDENCY ─────────────────────────────────────────────────────────
def check_device_token(request: Request) -> None:
    """If DEVICE_API_TOKEN is set, require matching X-Device-Token header."""
    if not DEVICE_API_TOKEN:
        return  # auth disabled
    token = request.headers.get("X-Device-Token", "")
    if token != DEVICE_API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid or missing X-Device-Token")


# ─── YOUTUBE FETCH ───────────────────────────────────────────────────────────
async def fetch_from_youtube() -> dict:
    """Call YouTube Data API v3 and return parsed result dict."""
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY is not configured")
    if not YOUTUBE_CHANNEL_ID:
        raise ValueError("YOUTUBE_CHANNEL_ID is not configured")

    params = {
        "part": "statistics",
        "id": YOUTUBE_CHANNEL_ID,
        "key": YOUTUBE_API_KEY,
    }

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(YOUTUBE_API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    items = data.get("items", [])
    if not items:
        raise ValueError(f"YouTube API returned empty items for channel: {YOUTUBE_CHANNEL_ID}")

    stats = items[0].get("statistics", {})
    subscriber_count = int(stats.get("subscriberCount", 0))

    from datetime import datetime, timezone
    updated_at = datetime.now(timezone.utc).isoformat()

    return {
        "subscribers": subscriber_count,
        "updated_at": updated_at,
    }


# ─── ROUTES ──────────────────────────────────────────────────────────────────
@app.get("/", summary="Service health check")
async def root():
    """Returns basic service status."""
    return {
        "service": "BFU YouTube Subscriber Counter API",
        "status": "ok",
        "channel_id": YOUTUBE_CHANNEL_ID or "not configured",
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
        "auth_enabled": bool(DEVICE_API_TOKEN),
    }


@app.get("/api/subscribers", summary="Get subscriber count")
async def get_subscribers(request: Request):
    """
    Returns the YouTube subscriber count for the configured channel.
    Caches the result for CACHE_TTL_SECONDS to avoid hitting YouTube API on every ESP32 request.
    """
    # Auth check
    check_device_token(request)

    now = time.time()
    cache_age = now - _cache["timestamp"]
    cache_valid = _cache["subscribers"] is not None and cache_age < CACHE_TTL_SECONDS

    # Return fresh cache
    if cache_valid:
        logger.info("Returning cached subscriber count: %s (age: %.1fs)", _cache["subscribers"], cache_age)
        return JSONResponse(content={
            "ok": True,
            "channel_id": YOUTUBE_CHANNEL_ID,
            "subscribers": _cache["subscribers"],
            "source": "youtube_data_api",
            "updated_at": _cache["updated_at"],
            "note": "Public YouTube count may be rounded",
            "stale": False,
        })

    # Try to fetch fresh data
    try:
        result = await fetch_from_youtube()
        _cache["subscribers"] = result["subscribers"]
        _cache["updated_at"]  = result["updated_at"]
        _cache["timestamp"]   = now

        logger.info("Fetched fresh subscriber count: %s", result["subscribers"])
        return JSONResponse(content={
            "ok": True,
            "channel_id": YOUTUBE_CHANNEL_ID,
            "subscribers": result["subscribers"],
            "source": "youtube_data_api",
            "updated_at": result["updated_at"],
            "note": "Public YouTube count may be rounded",
            "stale": False,
        })

    except Exception as e:
        logger.error("YouTube API fetch failed: %s", e)

        # Return stale cache if available
        if _cache["subscribers"] is not None:
            logger.warning("Returning stale cache (age: %.1fs)", cache_age)
            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "channel_id": YOUTUBE_CHANNEL_ID,
                    "subscribers": _cache["subscribers"],
                    "source": "youtube_data_api",
                    "updated_at": _cache["updated_at"],
                    "note": "Public YouTube count may be rounded",
                    "stale": True,
                },
            )

        # No cache at all — return error
        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "channel_id": YOUTUBE_CHANNEL_ID,
                "subscribers": 0,
                "error": "YouTube API unavailable and no cached data",
                "stale": False,
            },
        )
