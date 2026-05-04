# BFU YouTube Live Subscriber Counter

> **ESP32-C3 Super Mini** · **GC9A01 Round Display** · **Rotary Encoder** · **MicroPython**

A compact, standalone YouTube subscriber counter that runs entirely on an ESP32-C3 Super Mini. It displays your live subscriber count on a 240×240 round GC9A01 display, lets you navigate a menu with a rotary encoder, and connects to Wi-Fi through a built-in browser-based setup portal — no USB cable or computer required after the initial flash.

---

## Features

- 🟢 **Live subscriber count** — fetches data from YouTube Data API v3 every 60 seconds
- 📡 **Wi-Fi setup portal** — SoftAP + web form at `192.168.4.1`, no app needed
- 📷 **QR code screen** — scan with your phone to connect to the setup AP instantly
- 🎛️ **Rotary encoder navigation** — scroll menu, short click to select, long click to go back
- 🖥️ **GC9A01 round display** — 240×240 px, SPI, full-colour RGB565
- 🇺🇦 **Custom Ukrainian bitmap font** — supports Cyrillic + Latin + digits
- 📊 **Status screen** — shows Wi-Fi connection state and hardware status
- ⚡ **Single-file MicroPython** — no external libraries required

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

## How It Works

1. **Boot** — the device initialises the display and shows the main menu.
2. **Wi-Fi setup** — navigate to *Settings → Wi-Fi*. The device creates a `BFU-SETUP` access point. Connect your phone to it, open `http://192.168.4.1`, select your home network and enter the password.
3. **Subscriber count** — navigate to *Subscribers*. The device calls the YouTube Data API and displays the current count. It refreshes automatically every 60 seconds while the screen is open.
4. **Status screen** — shows ESP32-C3 model, display status, encoder status, and Wi-Fi connection state.

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

## YouTube API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g. `BFU-Counter`)
3. Navigate to **APIs & Services → Library**
4. Search for **YouTube Data API v3** and click **Enable**
5. Go to **APIs & Services → Credentials**
6. Click **Create Credentials → API key**
7. Copy the generated key
8. Open `src/main.py` and replace the placeholder:
   ```python
   YOUTUBE_API_KEY = "PASTE_YOUR_API_KEY_HERE"
   ```
   with your actual key.

> ⚠️ **Security:** Never publish your real API key in a public repository. The `.gitignore` file already excludes `config.py` and `secrets.py`.

---

## Uploading to ESP32-C3 with Thonny

1. Download and install [Thonny IDE](https://thonny.org/)
2. Flash MicroPython firmware to your ESP32-C3:
   - Download the latest ESP32-C3 firmware from [micropython.org/download](https://micropython.org/download/esp32c3/)
   - In Thonny: **Tools → Options → Interpreter** → select *MicroPython (ESP32)* and the correct COM port
   - Click **Install or update MicroPython** and follow the wizard
3. Open `src/main.py` in Thonny
4. Paste your YouTube API key into the `YOUTUBE_API_KEY` variable
5. Click **File → Save as…** → choose *MicroPython device* → save as `main.py`
6. Press the **Reset** button on the ESP32-C3 or click the green **Run** button

---

## Code Architecture

| Module | Description |
|---|---|
| `GC9A01` class | Full SPI display driver — init sequence, `fill_rect`, `write_block`, `text`, `ua_text` |
| `FONT_UA` dict | Custom 5×7 bitmap font supporting Ukrainian Cyrillic, Latin, digits and symbols |
| Rotary encoder | Polling-based with configurable threshold; detects direction and short/long button press |
| Menu system | State machine with `screen_mode` variable; supports nested menus and page screens |
| YouTube API | `fetch_youtube_subscribers()` — HTTP GET to YouTube Data API v3, JSON parsing |
| Wi-Fi portal | `start_wifi_setup_portal()` — SoftAP + non-blocking TCP socket server on port 80 |
| QR code screen | Pre-computed QR matrix rendered pixel-by-pixel using `fill_rect` |
| Main loop | Single `while True` loop — handles portal, encoder, button, and periodic API refresh |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Display shows black screen | Check SPI wiring (SCK, MOSI, DC, CS, RST). Verify 3.3 V power. |
| Encoder does not scroll | Check CLK and DT pins. Try swapping them if direction is reversed. |
| Button does not respond | Check SW pin wiring. Verify `PULL_UP` is active. |
| Wi-Fi portal does not appear | Make sure you selected *Settings → Wi-Fi* and waited 1–2 seconds. |
| YouTube API error | Verify the API key is correct and YouTube Data API v3 is enabled. |
| Subscriber count differs from YouTube Studio | The public API returns a rounded/cached value. This is a YouTube limitation. |
| Memory error on startup | Ensure you are using the latest MicroPython firmware for ESP32-C3. |
| Wrong pin numbers | Double-check the wiring table above. All GPIOs are for ESP32-C3 Super Mini. |

---

## Security Note

- **Do not publish your real YouTube API key** in any public repository.
- The `YOUTUBE_API_KEY` in `src/main.py` is set to `"PASTE_YOUR_API_KEY_HERE"` — replace it locally before uploading to the device.
- `config.py` and `secrets.py` are listed in `.gitignore` and will not be tracked by Git.
- **`wifi_config.json`** stores your Wi-Fi password in plain text on the ESP32 filesystem. Do not commit it to any repository. It is already listed in `.gitignore`.

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
