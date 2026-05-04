"""
BFU YouTube Subscriber Counter — Railway Backend
FastAPI proxy between ESP32 and YouTube Data API v3.

ENV variables required:
  YOUTUBE_API_KEY      — YouTube Data API v3 key
  YOUTUBE_CHANNEL_ID   — YouTube channel ID (starts with UC)
  CACHE_TTL_SECONDS    — how long to cache the result (default: 30)
  DEVICE_API_TOKEN     — optional token for X-Device-Token header auth
"""

import io
import os
import time
import logging

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image

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

AVATAR_SIZE = 64  # pixels — must match ESP32 firmware

# ─── IN-MEMORY CACHE ─────────────────────────────────────────────────────────
_cache: dict = {
    "subscribers": None,
    "title": None,
    "avatar_url": None,
    "updated_at": None,
    "timestamp": 0.0,
}

# Avatar pixel cache — converted once, reused until avatar_url changes
_avatar_cache: dict = {
    "url": None,
    "pixels": None,   # list of hex strings e.g. ["FFFF", "0000", ...]
    "width": AVATAR_SIZE,
    "height": AVATAR_SIZE,
}

# ─── APP ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="BFU YouTube Subscriber Counter API",
    description="Proxy backend for ESP32 YouTube subscriber counter. Caches YouTube Data API responses.",
    version="2.0.0",
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
    """Call YouTube Data API v3 (snippet + statistics) and return parsed result dict."""
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY is not configured")
    if not YOUTUBE_CHANNEL_ID:
        raise ValueError("YOUTUBE_CHANNEL_ID is not configured")

    params = {
        "part": "snippet,statistics",
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

    item       = items[0]
    stats      = item.get("statistics", {})
    snippet    = item.get("snippet", {})
    thumbnails = snippet.get("thumbnails", {})

    subscriber_count = int(stats.get("subscriberCount", 0))
    title            = snippet.get("title", "")

    # Prefer medium (240px) thumbnail, fall back to default (88px)
    avatar_url = (
        thumbnails.get("medium", {}).get("url")
        or thumbnails.get("default", {}).get("url")
        or ""
    )

    from datetime import datetime, timezone
    updated_at = datetime.now(timezone.utc).isoformat()

    return {
        "subscribers": subscriber_count,
        "title": title,
        "avatar_url": avatar_url,
        "updated_at": updated_at,
    }


# ─── AVATAR CONVERSION ───────────────────────────────────────────────────────
async def convert_avatar_to_rgb565(url: str) -> list[str]:
    """
    Download avatar image, resize to AVATAR_SIZE x AVATAR_SIZE,
    convert each pixel to RGB565 hex string.
    Returns list of hex strings like ["FFFF", "0000", ...].
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        image_bytes = resp.content

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Crop to square from centre, then resize
    w, h   = img.size
    side   = min(w, h)
    left   = (w - side) // 2
    top    = (h - side) // 2
    img    = img.crop((left, top, left + side, top + side))
    img    = img.resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)

    pixels = []
    for py in range(AVATAR_SIZE):
        for px in range(AVATAR_SIZE):
            r, g, b = img.getpixel((px, py))
            # RGB565: RRRRRGGGGGGBBBBB
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            pixels.append(f"{rgb565:04X}")

    logger.info("Avatar converted: %d pixels from %s", len(pixels), url)
    return pixels


# ─── SHARED CACHE REFRESH ────────────────────────────────────────────────────
async def refresh_cache() -> dict:
    """Fetch fresh data from YouTube and update _cache. Returns the new cache dict."""
    result = await fetch_from_youtube()
    now    = time.time()
    _cache["subscribers"] = result["subscribers"]
    _cache["title"]       = result["title"]
    _cache["avatar_url"]  = result["avatar_url"]
    _cache["updated_at"]  = result["updated_at"]
    _cache["timestamp"]   = now
    logger.info("Cache refreshed: %s subscribers, title=%s", result["subscribers"], result["title"])
    return _cache.copy()


def cache_is_valid() -> bool:
    return (
        _cache["subscribers"] is not None
        and (time.time() - _cache["timestamp"]) < CACHE_TTL_SECONDS
    )


def cache_exists() -> bool:
    return _cache["subscribers"] is not None


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
    check_device_token(request)

    now       = time.time()
    cache_age = now - _cache["timestamp"]

    if cache_is_valid():
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

    try:
        data = await refresh_cache()
        return JSONResponse(content={
            "ok": True,
            "channel_id": YOUTUBE_CHANNEL_ID,
            "subscribers": data["subscribers"],
            "source": "youtube_data_api",
            "updated_at": data["updated_at"],
            "note": "Public YouTube count may be rounded",
            "stale": False,
        })

    except Exception as e:
        logger.error("YouTube API fetch failed: %s", e)

        if cache_exists():
            logger.warning("Returning stale cache (age: %.1fs)", cache_age)
            return JSONResponse(status_code=200, content={
                "ok": True,
                "channel_id": YOUTUBE_CHANNEL_ID,
                "subscribers": _cache["subscribers"],
                "source": "youtube_data_api",
                "updated_at": _cache["updated_at"],
                "note": "Public YouTube count may be rounded",
                "stale": True,
            })

        return JSONResponse(status_code=503, content={
            "ok": False,
            "channel_id": YOUTUBE_CHANNEL_ID,
            "subscribers": 0,
            "error": "YouTube API unavailable and no cached data",
            "stale": False,
        })


@app.get("/api/channel", summary="Get channel info including avatar URL")
async def get_channel(request: Request):
    """
    Returns channel title, subscriber count, and avatar URL.
    Uses the same cache as /api/subscribers.
    """
    check_device_token(request)

    now       = time.time()
    cache_age = now - _cache["timestamp"]

    if cache_is_valid():
        return JSONResponse(content={
            "ok": True,
            "channel_id": YOUTUBE_CHANNEL_ID,
            "title": _cache["title"],
            "subscribers": _cache["subscribers"],
            "avatar_url": _cache["avatar_url"],
            "updated_at": _cache["updated_at"],
            "stale": False,
        })

    try:
        data = await refresh_cache()
        return JSONResponse(content={
            "ok": True,
            "channel_id": YOUTUBE_CHANNEL_ID,
            "title": data["title"],
            "subscribers": data["subscribers"],
            "avatar_url": data["avatar_url"],
            "updated_at": data["updated_at"],
            "stale": False,
        })

    except Exception as e:
        logger.error("YouTube API fetch failed: %s", e)

        if cache_exists():
            return JSONResponse(status_code=200, content={
                "ok": True,
                "channel_id": YOUTUBE_CHANNEL_ID,
                "title": _cache["title"],
                "subscribers": _cache["subscribers"],
                "avatar_url": _cache["avatar_url"],
                "updated_at": _cache["updated_at"],
                "stale": True,
            })

        return JSONResponse(status_code=503, content={
            "ok": False,
            "channel_id": YOUTUBE_CHANNEL_ID,
            "subscribers": 0,
            "error": "YouTube API unavailable and no cached data",
            "stale": False,
        })


@app.get("/api/avatar-rgb565", summary="Get channel avatar as RGB565 pixel array")
async def get_avatar_rgb565(request: Request):
    """
    Downloads the channel avatar, resizes to 64x64, converts to RGB565,
    and returns a JSON array of hex pixel strings.
    The conversion result is cached until the avatar URL changes.
    ESP32 can call this once and render the avatar directly using write_block().
    """
    check_device_token(request)

    # Ensure we have an avatar URL in cache
    if not cache_is_valid():
        try:
            await refresh_cache()
        except Exception as e:
            logger.error("Failed to refresh cache for avatar: %s", e)
            if not cache_exists():
                return JSONResponse(status_code=503, content={
                    "ok": False,
                    "error": "Channel data unavailable",
                })

    avatar_url = _cache.get("avatar_url", "")
    if not avatar_url:
        return JSONResponse(status_code=404, content={
            "ok": False,
            "error": "No avatar URL available for this channel",
        })

    # Return cached conversion if URL hasn't changed
    if _avatar_cache["url"] == avatar_url and _avatar_cache["pixels"] is not None:
        logger.info("Returning cached avatar RGB565 (%d pixels)", len(_avatar_cache["pixels"]))
        return JSONResponse(content={
            "ok": True,
            "width": _avatar_cache["width"],
            "height": _avatar_cache["height"],
            "pixels": _avatar_cache["pixels"],
        })

    # Convert avatar
    try:
        pixels = await convert_avatar_to_rgb565(avatar_url)
        _avatar_cache["url"]    = avatar_url
        _avatar_cache["pixels"] = pixels
        _avatar_cache["width"]  = AVATAR_SIZE
        _avatar_cache["height"] = AVATAR_SIZE
        return JSONResponse(content={
            "ok": True,
            "width": AVATAR_SIZE,
            "height": AVATAR_SIZE,
            "pixels": pixels,
        })
    except Exception as e:
        logger.error("Avatar conversion failed: %s", e)
        return JSONResponse(status_code=502, content={
            "ok": False,
            "error": f"Avatar conversion failed: {str(e)}",
        })
