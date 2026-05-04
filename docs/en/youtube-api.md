# YouTube API Setup

## Overview

This project uses the **YouTube Data API v3** to fetch the subscriber count for a YouTube channel. The API is free for typical usage (up to 10,000 units per day on the default quota).

---

## Step 1 — Create a Google Cloud Project

1. Go to [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Sign in with your Google account.
3. Click the project dropdown at the top of the page.
4. Click **New Project**.
5. Enter a name (e.g. `BFU-Counter`) and click **Create**.
6. Make sure the new project is selected in the dropdown.

---

## Step 2 — Enable YouTube Data API v3

1. In the left sidebar, go to **APIs & Services → Library**.
2. In the search box, type `YouTube Data API v3`.
3. Click on the result and then click **Enable**.

---

## Step 3 — Create an API Key

1. Go to **APIs & Services → Credentials**.
2. Click **Create Credentials → API key**.
3. Google will generate a key — copy it immediately.
4. (Optional but recommended) Click **Restrict Key**:
   - Under **API restrictions**, select **Restrict key**
   - Choose **YouTube Data API v3** from the list
   - Click **Save**

---

## Step 4 — Find Your Channel ID

1. Open [YouTube Studio](https://studio.youtube.com/)
2. Go to **Settings → Channel → Advanced settings**
3. Copy the **Channel ID** (starts with `UC...`)

Alternatively, open your YouTube channel page in a browser and look at the URL:
```
https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxx
```
The part after `/channel/` is your Channel ID.

---

## Step 5 — Add the Key to the Firmware or Backend

### Option A — Railway Backend (Recommended)

The **Railway backend** is the recommended production method. Your API key is stored as a Railway environment variable and never touches the ESP32 firmware.

See **[backend.md](backend.md)** for the full Railway deployment guide.

### Option B — Direct Key in Firmware

1. Open `src/main.py` in Thonny or any text editor.
2. Find this line near the top:
   ```python
   YOUTUBE_API_KEY = "PASTE_YOUR_API_KEY_HERE"
   ```
3. Replace the placeholder with your actual API key:
   ```python
   YOUTUBE_API_KEY = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
   ```
4. The Channel ID is already set in the file:
   ```python
   YOUTUBE_CHANNEL_ID = "UC---ig4FdhPV3bSgE9KPJhg"
   ```
   If you want to track a different channel, replace this value with your own Channel ID.

5. Save the file to the device (see [installation.md](installation.md)).

---

## How the API Call Works

The firmware sends a single HTTP GET request:

```
GET https://www.googleapis.com/youtube/v3/channels
    ?part=statistics
    &id=<CHANNEL_ID>
    &key=<API_KEY>
```

The response is a JSON object. The firmware extracts:
```json
items[0].statistics.subscriberCount
```

---

## Why the Count May Differ from YouTube Studio

The YouTube Data API v3 returns a **public subscriber count**, which is:

- **Rounded** — YouTube rounds public counts to 3 significant figures (e.g. 4,590 may show as 4,500 or 4,600)
- **Cached** — the value may be delayed by several minutes to hours
- **Different from YouTube Studio** — Studio shows the exact real-time count, which is only visible to the channel owner

This is a YouTube platform limitation and cannot be changed in the firmware.

---

## Security

- **Never commit your real API key to a public repository.**
- The `YOUTUBE_API_KEY` in `src/main.py` is set to `"PASTE_YOUR_API_KEY_HERE"` as a safe placeholder.
- `config.py` and `secrets.py` are excluded by `.gitignore`.
- If you accidentally expose a key, go to Google Cloud Console → Credentials and delete or regenerate it immediately.
