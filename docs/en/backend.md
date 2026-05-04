# Railway Backend Guide

## Overview

The **Railway backend** is the recommended production method for the BFU YouTube Subscriber Counter. Instead of storing your YouTube API key directly in the ESP32 firmware, you deploy a small FastAPI server to [Railway](https://railway.app/). The ESP32 calls your backend URL, and the backend calls YouTube on its behalf.

```
ESP32  ──►  https://your-app.up.railway.app/api/subscribers  ──►  YouTube Data API v3
```

**Why use the backend?**

| Concern | Direct API (firmware) | Railway backend |
|---|---|---|
| API key location | Inside ESP32 firmware | Railway environment variable only |
| Key exposure risk | High (anyone with the `.py` file) | None (never leaves the server) |
| Caching | None — every refresh hits YouTube | Built-in (default 30 s) |
| Quota usage | 1 unit per ESP32 refresh | 1 unit per cache window |
| Reliability | Fails if YouTube is slow | Returns stale cache if YouTube is down |

> ⚠️ **Note:** The YouTube Data API v3 returns a **public subscriber count**, which YouTube intentionally rounds for channels with more than 1,000 subscribers. This is a YouTube platform limitation and cannot be changed by the backend or the firmware.

---

## Backend Files

All backend files live in the `backend/` folder:

```
backend/
├── main.py            ← FastAPI application
├── requirements.txt   ← Python dependencies
├── Procfile           ← Railway start command
├── .env.example       ← Template for local development
├── .gitignore         ← Excludes .env from git
└── README.md          ← Backend-specific readme
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

> The free quota is **10,000 units/day**. With 30-second caching, even continuous ESP32 polling results in at most ~2,880 API calls/day — well within the free tier.

---

## Step 2 — Deploy to Railway

1. Push this repository to GitHub (if not already done).
2. Go to [railway.app](https://railway.app/) and sign in.
3. Click **New Project → Deploy from GitHub repo**.
4. Select your repository.
5. In the Railway project settings, set the **Root Directory** to `backend`.
6. Go to the **Variables** tab and add:

   | Variable | Value |
   |---|---|
   | `YOUTUBE_API_KEY` | Your YouTube Data API v3 key |
   | `YOUTUBE_CHANNEL_ID` | Your channel ID (starts with `UC`) |
   | `CACHE_TTL_SECONDS` | `30` (optional, default is 30) |
   | `DEVICE_API_TOKEN` | A random secret token (optional) |

7. Railway will detect the `Procfile` and deploy automatically.
8. Your endpoint will be available at:
   ```
   https://YOUR-APP-NAME.up.railway.app/api/subscribers
   ```

---

## Step 3 — Configure the ESP32 Firmware

Open `src/main.py` and update the backend URL constants near the top of the file:

```python
# ─── BACKEND URL (Railway proxy) ─────────────────────────────────────────────
# Set this to your Railway backend URL.
# Leave YOUTUBE_API_KEY as the placeholder — the key lives on the server, not here.
BACKEND_SUBSCRIBERS_URL = "https://YOUR-APP-NAME.up.railway.app/api/subscribers"
BACKEND_AVATAR_URL      = "https://YOUR-APP-NAME.up.railway.app/api/avatar-rgb565"
DEVICE_API_TOKEN        = ""   # Set if you enabled token auth on the backend
```

> If you enabled `DEVICE_API_TOKEN` on the backend, set the same value in `DEVICE_API_TOKEN` in the firmware. The ESP32 will send it as the `X-Device-Token` header.

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

Then test the subscriber endpoint:
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

## Optional: Device Token Authentication

To prevent unauthorised access to your backend endpoint:

1. Generate a random token:
   ```bash
   # PowerShell
   -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
   ```
2. Set `DEVICE_API_TOKEN=your_token` in Railway Variables.
3. Set `DEVICE_API_TOKEN = "your_token"` in `src/main.py`.
4. The ESP32 will automatically send `X-Device-Token: your_token` with every request.

---

## How Caching Works

```
Request 1 (t=0s)   → cache miss  → fetch YouTube API → cache result → return fresh data
Request 2 (t=10s)  → cache hit   → return cached data (no YouTube call)
Request 3 (t=25s)  → cache hit   → return cached data (no YouTube call)
Request 4 (t=35s)  → cache miss  → fetch YouTube API → cache result → return fresh data
```

If the YouTube API is temporarily unavailable, the backend returns the last cached value with `"stale": true`. If there is no cache at all, it returns HTTP 503 with `"ok": false`.

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `YOUTUBE_API_KEY` | ✅ Yes | — | YouTube Data API v3 key |
| `YOUTUBE_CHANNEL_ID` | ✅ Yes | — | Channel ID starting with `UC` |
| `CACHE_TTL_SECONDS` | No | `30` | Cache duration in seconds |
| `DEVICE_API_TOKEN` | No | *(disabled)* | If set, ESP32 must send matching `X-Device-Token` header |

---

## API Endpoints

### `GET /api/subscribers`
Returns the subscriber count. Used by the ESP32 for the main counter display.

### `GET /api/channel`
Returns channel title, subscriber count, and avatar URL. Same cache as `/api/subscribers`.

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
Downloads the channel avatar, resizes it to **64×64 pixels**, converts each pixel to **RGB565** format, and returns a JSON array of hex pixel strings. The conversion is cached on the server — it only runs once per unique avatar URL.

**Response:**
```json
{
  "ok": true,
  "width": 64,
  "height": 64,
  "pixels": ["FFFF", "0000", "F800", "..."]
}
```

The ESP32 firmware calls this endpoint once when the subscriber screen opens, converts the hex strings to a `bytearray`, and renders the avatar using `display.write_block()`. The pixel list is freed from RAM immediately after drawing.

### `GET /`
Health check — returns service status and configuration summary.

---

## Security Notes

- `YOUTUBE_API_KEY` is stored only in Railway environment variables — never in code or on the ESP32.
- The `.env` file is listed in `backend/.gitignore` and will never be committed.
- Logs do not print API keys or tokens.
- `DEVICE_API_TOKEN` is optional but recommended for production deployments.
