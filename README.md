# BFU YouTube Live Subscriber Counter

> **ESP32-C3 Super Mini** · **GC9A01 Round Display** · **Rotary Encoder** · **MicroPython**

A compact, standalone YouTube subscriber counter that runs entirely on an ESP32-C3 Super Mini. It displays your live subscriber count on a 240×240 round GC9A01 display, lets you navigate a menu with a rotary encoder, and connects to Wi-Fi through a built-in browser-based setup portal — no USB cable or computer required after the initial flash.

---

## Features

- 🟢 **Live subscriber count** — fetches data via Railway backend every 60 seconds
- 🖼️ **Channel avatar** — displays the 32×32 channel avatar using binary RGB565 (memory-safe, no JSON)
- 📡 **Wi-Fi setup portal** — SoftAP + web form at `192.168.4.1`, no app needed
- 📷 **QR code screen** — scan with your phone to connect to the setup AP instantly
- 🎛️ **Rotary encoder navigation** — scroll menu, short click to select, long click to go back
- 🖥️ **GC9A01 round display** — 240×240 px, SPI, full-colour RGB565
- 🇺🇦 **Custom Ukrainian bitmap font** — supports Cyrillic + Latin + digits, no `framebuf` dependency
- 📊 **Status screen** — shows Wi-Fi connection state and hardware status
- ⚡ **Single-file MicroPython** — no external libraries required on the device
- 🔒 **Railway backend required** — API key never stored on the ESP32

---

## Hardware Required

| Component | Details |
|---|---|
| ESP32-C3 Super Mini | Main microcontroller |
| GC9A01 Round Display | 240×240 px, SPI interface |
| Rotary Encoder (KY-040 or similar) | With push button |
| Breadboard + jumper wires | For prototyping |
| USB-C cable | For flashing and power |

---

## Wiring

### GC9A01 Display

| Display Pin | ESP32-C3 GPIO |
|---|---|
| SCK | GPIO 4 |
| MOSI | GPIO 6 |
| DC | GPIO 7 |
| CS | GPIO 10 |
| RST | GPIO 5 |
| VCC | 3.3 V |
| GND | GND |

### Rotary Encoder

| Encoder Pin | ESP32-C3 GPIO |
|---|---|
| CLK | GPIO 3 |
| DT | GPIO 2 |
| SW | GPIO 1 |
| VCC | 3.3 V |
| GND | GND |

> ⚠️ **Important:** The ESP32-C3 operates at **3.3 V logic**. Do not connect any pin directly to 5 V.

---

## Architecture

```
ESP32-C3  ──►  Railway Backend  ──►  YouTube Data API v3
                    │
                    └──►  /api/subscribers   (JSON, subscriber count)
                    └──►  /api/avatar-rgb565 (binary RGB565, 2048 bytes)
```

The Railway backend acts as a secure proxy:
- Your YouTube API key is stored **only** in Railway environment variables — never on the ESP32.
- The backend caches responses (default 30 s) to minimise YouTube API quota usage.
- The ESP32 makes two HTTP requests on the subscriber screen: one for the count, one for the avatar.

---

## How It Works

1. **Boot** — the device initialises the display, resets the Wi-Fi interface, and attempts to connect to the saved network.
2. **Wi-Fi setup** — navigate to *Settings → Wi-Fi*. The device creates a `BFU-SETUP` access point. Connect your phone to it, open `http://192.168.4.1`, select your home network and enter the password. Credentials are saved to `wifi_config.json` on the device.
3. **Subscriber count** — navigate to *Subscribers*. The device calls the Railway backend and displays the current count. It refreshes automatically every 60 seconds while the screen is open.
4. **Channel avatar** — after the subscriber count loads, the device fetches a 32×32 raw binary RGB565 image (2048 bytes) from the backend and renders it directly using `display.write_block()`. No JSON parsing, no pixel conversion loop — memory-safe for ESP32-C3.
5. **Status screen** — shows ESP32-C3 model, display status, encoder status, and Wi-Fi connection state.

---

## Wi-Fi Setup Portal

| Step | Action |
|---|---|
| 1 | Navigate to **Settings → Wi-Fi** on the device |
| 2 | The display shows a QR code — scan it with your phone camera |
| 3 | Your phone connects to the `BFU-SETUP` network (password: `12345678`) |
| 4 | Open a browser and go to `http://192.168.4.1` |
| 5 | Select your home Wi-Fi network from the dropdown |
| 6 | Enter your Wi-Fi password and press **Connect** |
| 7 | The device connects and shows the assigned IP address |

---

## Railway Backend Setup

The Railway backend is **required** — the firmware does not support direct YouTube API calls.

See **[docs/en/backend.md](docs/en/backend.md)** for the full Railway deployment guide.

```
ESP32  ──►  https://your-app.up.railway.app/api/subscribers
ESP32  ──►  https://your-app.up.railway.app/api/avatar-rgb565
```

After deploying, open `src/main.py` and set:

```python
BACKEND_SUBSCRIBERS_URL = "https://YOUR-APP-NAME.up.railway.app/api/subscribers"
BACKEND_AVATAR_URL      = "https://YOUR-APP-NAME.up.railway.app/api/avatar-rgb565"
DEVICE_API_TOKEN        = "your_optional_token"
```

> ℹ️ **Note:** The YouTube Data API v3 returns a **public subscriber count**, which YouTube rounds for channels with more than 1,000 subscribers. This is a YouTube platform limitation.

---

## Uploading to ESP32-C3 with Thonny

1. Download and install [Thonny IDE](https://thonny.org/)
2. Flash MicroPython firmware to your ESP32-C3:
   - Download the latest ESP32-C3 firmware from [micropython.org/download](https://micropython.org/download/esp32c3/)
   - In Thonny: **Tools → Options → Interpreter** → select *MicroPython (ESP32)* and the correct COM port
   - Click **Install or update MicroPython** and follow the wizard
3. Open `src/main.py` in Thonny
4. Set `BACKEND_SUBSCRIBERS_URL` and `BACKEND_AVATAR_URL` to your Railway app URLs
5. Click **File → Save as…** → choose *MicroPython device* → save as `main.py`
6. Press the **Reset** button on the ESP32-C3

---

## Code Architecture

| Module | Description |
|---|---|
| `GC9A01` class | Full SPI display driver — init sequence, `fill_rect`, `write_block`, `ua_text` |
| `FONT_UA` dict | Custom 5×7 bitmap font — Ukrainian Cyrillic, Latin, digits, symbols. No `framebuf` used. |
| `fetch_youtube_subscribers()` | HTTP GET to Railway backend `/api/subscribers`, JSON response |
| `fetch_channel_avatar()` | HTTP GET to Railway backend `/api/avatar-rgb565`, raw binary response (2048 bytes), direct `write_block()` |
| `_reset_sta()` | Disables AP and resets STA before connecting — prevents Wi-Fi error 0x0102 |
| Rotary encoder | Polling-based with configurable threshold; detects direction and short/long button press |
| Menu system | State machine with `screen_mode` variable; supports nested menus and page screens |
| Wi-Fi portal | `start_wifi_setup_portal()` — SoftAP + non-blocking TCP socket server on port 80 |
| QR code screen | Pre-computed QR matrix rendered pixel-by-pixel using `fill_rect` |
| Main loop | Single `while True` loop — handles portal, encoder, button, and periodic API refresh |

### Memory optimisations (ESP32-C3)

- `framebuf` module removed — all text rendered via custom `ua_text()` with direct pixel writes
- Avatar delivered as raw binary RGB565 (2048 bytes) — no JSON parsing, no pixel list, no `int(px, 16)` loop
- Pixel buffer freed with `del buf; gc.collect()` immediately after `write_block()`
- Manual Wi-Fi password entry UI removed — replaced by web portal (saves ~150 lines and associated RAM)
- Direct YouTube API fallback removed — Railway backend is the only data path

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Display shows black screen | Check SPI wiring (SCK, MOSI, DC, CS, RST). Verify 3.3 V power. |
| Encoder does not scroll | Check CLK and DT pins. Try swapping them if direction is reversed. |
| Button does not respond | Check SW pin wiring. Verify `PULL_UP` is active. |
| Wi-Fi portal does not appear | Navigate to *Settings → Wi-Fi* and wait 1–2 seconds for the AP to start. |
| Status shows "НЕМА API" | `BACKEND_SUBSCRIBERS_URL` is empty — set it to your Railway URL. |
| Status shows "API ПОМИЛКА" | Railway backend is unreachable or returned an error. Check Railway logs. |
| Status shows "НЕМА WI-FI" | Device is not connected to Wi-Fi. Use the portal to configure. |
| Wi-Fi error 0x0102 | Fixed in firmware — `_reset_sta()` disables AP and resets STA before connecting. |
| Avatar not showing | Check `BACKEND_AVATAR_URL`. Backend must return exactly 2048 bytes. |
| Subscriber count differs from YouTube Studio | The public API returns a rounded/cached value. This is a YouTube limitation. |
| Memory error on startup | Ensure you are using the latest MicroPython firmware for ESP32-C3. |

---

## Security Note

- Your YouTube API key is stored **only** in Railway environment variables — never in the firmware or on the device.
- `wifi_config.json` stores your Wi-Fi password in plain text on the ESP32 filesystem. Do not commit it to any repository. It is already listed in `.gitignore`.
- `DEVICE_API_TOKEN` is optional but recommended for production deployments.

---

## Build Stream

This project was built live on stream. Watch the full process here:

▶️ **[BFU YouTube Subscriber Counter — Live Build Stream](https://www.youtube.com/watch?v=ARB0xlgDCNw&t=598s)**

---

## Credits

**Brain From Ukraine / BFU Electronics**

Educational open-source hardware and firmware projects for the Ukrainian maker community.

- YouTube: [BFU Electronics](https://www.youtube.com/@BFUelectronics)
- License: MIT
