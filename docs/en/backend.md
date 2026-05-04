# Railway Backend Guide

## Overview

The **Railway backend** is the **required** architecture for BFU YouTube Subscriber Counter. The ESP32-C3 firmware does not support direct YouTube API calls — all data is fetched through the Railway proxy.

```
ESP32-C3  ──►  https://your-app.up.railway.app/api/subscribers   ──►  YouTube Data API v3
ESP32-C3  ──►  https://your-app.up.railway.app/api/avatar-rgb565 ──►  YouTube channel avatar
```

**Why Railway backend?**

| Concern | Direct API (firmware) | Railway backend |
|---|---|---|
| API key location | Inside ESP32 firmware | Railway env vars only |
| Key leak risk | High (anyone with the `.py` file) | None (key never leaves server) |
| Caching | None — every refresh hits YouTube | Built-in (default 30 s) |
| Quota usage | 1 unit per ESP32 refresh | 1 unit per cache window |
| Reliability | Fails if YouTube is slow | Returns stale cache if YouTube is down |
| Avatar | Not supported | Binary RGB565, 2048 bytes, memory-safe |

> ⚠️ **Note:** YouTube Data API v3 returns the **public subscriber count**, which YouTube intentionally rounds for channels with more than 1,000 subscribers. This is a YouTube platform limitation and cannot be changed by the backend or firmware.

---

## Backend Files

All backend files are in the `backend/` folder:

```
backend/
├── main.py            ← FastAPI application
├── requirements.txt   ← Python dependencies (includes Pillow>=11.0.0)
├── runtime.txt        ← Python version pin for Railway (python-3.12.8)
├── Procfile           ← Railway start command
├── .env.example       ← Template for local development
├── .gitignore         ← Excludes .env from git
└── README.md          ← Backend README
```

---

## Step 1 — Get a YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g. `BFU-Counter`)
3. Navigate to **APIs & Services → Library**
4. Search for **YouTube Data API v3** and click **Enable**
5. Go to **APIs & Services → Credentials**
6. Click **Create Credentials → API key**
7. Copy the generated key

> The free quota is **10,000 units/day**. With 30-second caching, even continuous ESP32 polling produces at most ~2,880 API requests/day — well within the free tier.

---

## Step 2 — Deploy to Railway

1. Push this repository to GitHub (if not already done).
2. Go to [railway.app](https://railway.app/) and sign in.
3. Click **New Project → Deploy from GitHub repo**.
4. Select your repository.
5. In the Railway project settings, set **Root Directory** to `backend`.
6. Go to the **Variables** tab and add:

   | Variable | Value |
   |---|---|
   | `YOUTUBE_API_KEY` | Your YouTube Data API v3 key |
   | `YOUTUBE_CHANNEL_ID` | Your channel ID (starts with `UC`) |
   | `CACHE_TTL_SECONDS` | `30` (optional, default is 30) |
   | `DEVICE_API_TOKEN` | A random secret token (optional) |

7. Railway will automatically detect `Procfile` and deploy the app.
8. Your endpoints will be available at:
   ```
   https://YOUR-APP-NAME.up.railway.app/api/subscribers
   https://YOUR-APP-NAME.up.railway.app/api/avatar-rgb565
   ```

---

## Step 3 — Configure the ESP32 Firmware

Open `src/main.py` and update the backend URL constants at the top of the file:

```python
# ─── RAILWAY BACKEND ─────────────────────────────────────────────────────────
BACKEND_SUBSCRIBERS_URL = "https://YOUR-APP-NAME.up.railway.app/api/subscribers"
BACKEND_AVATAR_URL      = "https://YOUR-APP-NAME.up.railway.app/api/avatar-rgb565"
DEVICE_API_TOKEN        = ""   # Set if you enabled token auth on the backend
```

> If you enabled `DEVICE_API_TOKEN` on the backend — set the same value in `DEVICE_API_TOKEN` in the firmware. The ESP32 will automatically send it as an `X-Device-Token` header with every request.

---

## Step 4 — Verify the Backend

Open a browser or use `curl` to test:

```
https://YOUR-APP-NAME.up.railway.app/
```

Expected response:
```json
{
  "service": "BFU YouTube Subscriber Counter API",
  "status": "ok",
  "channel_id": "UCxxxxxxxxx",
  "cache_ttl_seconds": 30,
  "auth_enabled": false
}
```

Then check the subscriber endpoint:
```
https://YOUR-APP-NAME.up.railway.app/api/subscribers
```

Expected response:
```json
{
  "ok": true,
  "channel_id": "UCxxxxxxxxx",
  "subscribers": 4590,
  "source": "youtube_data_api",
  "updated_at": "2025-01-01T12:00:00+00:00",
  "note": "Public YouTube count may be rounded",
  "stale": false
}
```

---

## Local Development

To run the backend locally before deploying:

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

copy .env.example .env
# Edit .env and add your real keys

uvicorn main:app --reload --port 8000
```

Open: [http://localhost:8000/api/subscribers](http://localhost:8000/api/subscribers)

---

## Optional: Device Token Auth

To protect the backend endpoints from unauthorised access:

1. Generate a random token:
   ```bash
   # PowerShell
   -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
   ```
2. Set `DEVICE_API_TOKEN=your_token` in Railway variables.
3. Set `DEVICE_API_TOKEN = "your_token"` in `src/main.py`.
4. The ESP32 will automatically send `X-Device-Token: your_token` with every request.

---

## How Caching Works

```
Request 1 (t=0s)   → cache miss  → fetch from YouTube API → cache → return fresh data
Request 2 (t=10s)  → cache hit   → return cached data (no YouTube call)
Request 3 (t=25s)  → cache hit   → return cached data (no YouTube call)
Request 4 (t=35s)  → cache miss  → fetch from YouTube API → cache → return fresh data
```

If the YouTube API is temporarily unavailable, the backend returns the last cached value with `"stale": true`. If there is no cache at all, it returns HTTP 503 with `"ok": false`.

---

## API Endpoints

### `GET /api/subscribers`
Returns the subscriber count as JSON. Used by the ESP32 for the main counter display.

**Response:**
```json
{
  "ok": true,
  "channel_id": "UCxxxxx",
  "subscribers": 4670,
  "source": "youtube_data_api",
  "updated_at": "2024-01-01T12:00:00+00:00",
  "note": "Public YouTube count may be rounded",
  "stale": false
}
```

### `GET /api/channel`
Returns channel title, subscriber count, and avatar URL. Uses the same cache as `/api/subscribers`.

**Response:**
```json
{
  "ok": true,
  "channel_id": "UCxxxxx",
  "title": "BFU Electronics",
  "subscribers": 4670,
  "avatar_url": "https://yt3.ggpht.com/...",
  "updated_at": "2024-01-01T12:00:00+00:00",
  "stale": false
}
```

### `GET /api/avatar-rgb565`
Downloads the channel avatar, crops to square, resizes to **32×32 pixels**, converts each pixel to big-endian **RGB565**, and returns the raw bytes as `application/octet-stream`.

**Response:**
- Content-Type: `application/octet-stream`
- Body: `32 × 32 × 2 = 2048 bytes` of raw RGB565 data
- Header: `X-Avatar-Size: 32`

**Why binary instead of JSON?**

The previous JSON approach returned a list of 4096 hex strings (e.g. `["FFFF", "0000", ...]`). Parsing this on the ESP32-C3 required:
- Allocating the full JSON string in RAM
- Building a Python list of 4096 strings
- Converting each string with `int(px, 16)` in a loop
- Building a separate `bytearray`

This exceeded the ESP32-C3's available heap and caused boot failures.

The binary approach sends exactly 2048 bytes. The ESP32 reads `response.content` directly into a `bytearray` and passes it to `display.write_block()` — no parsing, no intermediate list, no conversion loop. The buffer is freed with `del buf; gc.collect()` immediately after rendering.

**Conversion is cached on the server** — performed only once per unique avatar URL.

### `GET /`
Service health check — returns status and configuration summary.

---

## Environment Variable Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `YOUTUBE_API_KEY` | ✅ Yes | — | YouTube Data API v3 key |
| `YOUTUBE_CHANNEL_ID` | ✅ Yes | — | Channel ID starting with `UC` |
| `CACHE_TTL_SECONDS` | No | `30` | Cache duration in seconds |
| `DEVICE_API_TOKEN` | No | *(disabled)* | If set, ESP32 must send matching `X-Device-Token` header |

---

## Security Notes

- `YOUTUBE_API_KEY` is stored only in Railway variables — never in code or on the ESP32.
- The `.env` file is listed in `backend/.gitignore` and will never be committed.
- Logs do not print API keys or tokens.
- `DEVICE_API_TOKEN` is optional but recommended for production deployments.
