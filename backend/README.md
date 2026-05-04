# BFU YouTube Subscriber Counter — Railway Backend

> **FastAPI** · **Railway** · **YouTube Data API v3** · **ESP32 proxy**

A lightweight FastAPI backend that acts as a proxy between the ESP32 YouTube Subscriber Counter and the YouTube Data API v3. It caches responses so the ESP32 can poll frequently without exhausting the YouTube API quota.

---

## Why a Backend?

- **Security** — the YouTube API key never lives on the ESP32 or in the firmware.
- **Caching** — multiple ESP32 requests within the cache window hit the backend only, not Google.
- **Reliability** — stale cache is returned if YouTube API is temporarily unavailable.
- **Optional auth** — protect the endpoint with a device token.

---

## Endpoints

### `GET /`

Returns service health status.

```json
{
  "service": "BFU YouTube Subscriber Counter API",
  "status": "ok",
  "channel_id": "UCxxxxxxxxx",
  "cache_ttl_seconds": 30,
  "auth_enabled": false
}
```

### `GET /api/subscribers`

Returns the subscriber count for the configured channel.

**Success response:**
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

**Stale cache response** (YouTube API temporarily unavailable):
```json
{
  "ok": true,
  "subscribers": 4590,
  "stale": true,
  ...
}
```

**Error response** (no cache, API down):
```json
{
  "ok": false,
  "error": "YouTube API unavailable and no cached data",
  "subscribers": 0
}
```

---

## Railway Variables (Environment Variables)

Set these in your Railway project → **Variables** tab:

| Variable | Required | Description |
|---|---|---|
| `YOUTUBE_API_KEY` | ✅ Yes | YouTube Data API v3 key |
| `YOUTUBE_CHANNEL_ID` | ✅ Yes | Channel ID starting with `UC` |
| `CACHE_TTL_SECONDS` | Optional | Cache duration in seconds (default: `30`) |
| `DEVICE_API_TOKEN` | Optional | If set, ESP32 must send `X-Device-Token: <value>` header |

> ⚠️ **Never commit real API keys.** Use `.env` locally and Railway Variables in production.

---

## How to Get a YouTube Data API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g. `BFU-Counter`)
3. Navigate to **APIs & Services → Library**
4. Search for **YouTube Data API v3** and click **Enable**
5. Go to **APIs & Services → Credentials**
6. Click **Create Credentials → API key**
7. Copy the generated key
8. Add it as `YOUTUBE_API_KEY` in Railway Variables

> The free quota is **10,000 units/day**. Each subscriber fetch uses 1 unit. With 30-second caching, even 1 request/second from the ESP32 results in at most 2,880 API calls/day — well within the free tier.

---

## Deploy to Railway via GitHub

1. Push this repository to GitHub.
2. Go to [railway.app](https://railway.app/) and create a new project.
3. Click **Deploy from GitHub repo** and select your repository.
4. Set the **Root Directory** to `backend` in Railway project settings.
5. Add the required **Variables** (see table above).
6. Railway will automatically detect `Procfile` and deploy.
7. Your endpoint will be available at:
   ```
   https://YOUR-APP-NAME.up.railway.app/api/subscribers
   ```

---

## Local Development

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

# Create .env from example
copy .env.example .env
# Edit .env and add your real keys

uvicorn main:app --reload --port 8000
```

Open: http://localhost:8000/api/subscribers

---

## ESP32 Configuration

In `src/main.py` on the ESP32, set:

```python
BACKEND_SUBSCRIBERS_URL = "https://YOUR-APP-NAME.up.railway.app/api/subscribers"
DEVICE_API_TOKEN = ""  # leave empty if auth is disabled, or set your token
```

The ESP32 will call this URL instead of the YouTube API directly.

---

## Optional: Enable Device Token Auth

1. Generate a random token (e.g. `openssl rand -hex 16`).
2. Set `DEVICE_API_TOKEN=your_token` in Railway Variables.
3. Set `DEVICE_API_TOKEN = "your_token"` in `src/main.py` on the ESP32.
4. The ESP32 will automatically send `X-Device-Token: your_token` with every request.

---

## Why Public Subscriber Count May Be Rounded

The YouTube Data API v3 returns the **public subscriber count**, which YouTube intentionally rounds:

- Channels with **< 1,000** subscribers: exact count
- Channels with **1,000–9,999**: rounded to nearest 100
- Channels with **10,000+**: rounded to nearest 1,000

This is a YouTube platform policy and cannot be changed via the API. YouTube Studio shows the exact count, but that requires OAuth authentication which is not practical for an embedded device.

---

## Security Notes

- `YOUTUBE_API_KEY` is stored only in Railway environment variables — never in code or on the ESP32.
- `DEVICE_API_TOKEN` is optional but recommended for production deployments.
- The `.env` file is listed in `.gitignore` and will never be committed.
- Logs do not print API keys or tokens.
