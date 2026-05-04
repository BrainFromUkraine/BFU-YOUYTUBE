# Troubleshooting

## Display Shows a Black Screen

**Symptoms:** The display does not light up after powering on.

**Possible causes and fixes:**

1. **Wrong wiring** — Check every SPI pin against the wiring table:
   - SCK → GPIO 4
   - MOSI → GPIO 6
   - DC → GPIO 7
   - CS → GPIO 10
   - RST → GPIO 5
2. **Power issue** — Make sure VCC is connected to the **3.3 V** pin, not 5 V.
3. **Loose connection** — Re-seat all jumper wires.
4. **Firmware not running** — Open Thonny, connect to the device, and check the REPL for error messages.

---

## Encoder Does Not Scroll the Menu

**Symptoms:** Rotating the encoder does nothing, or the menu jumps erratically.

**Possible causes and fixes:**

1. **Wrong pins** — Verify CLK → GPIO 3, DT → GPIO 2.
2. **Reversed direction** — If the menu scrolls in the wrong direction, swap the CLK and DT wires.
3. **Threshold too high** — The default `ENCODER_THRESHOLD = 2` requires 2 pulses per step. If the encoder is very sensitive, reduce it to `1` in `src/main.py`.
4. **Floating pins** — All encoder pins use `Pin.PULL_UP`. If you see random movement, check that the encoder GND is properly connected.

---

## Button Does Not Respond

**Symptoms:** Pressing the encoder button does nothing.

**Possible causes and fixes:**

1. **Wrong pin** — Verify SW → GPIO 1.
2. **Loose wire** — Check the SW and GND connections.
3. **Debounce delay** — After a click, the firmware waits 120 ms before accepting the next input. This is normal.
4. **Long press threshold** — A press shorter than 900 ms is a short click; longer is a long click. Make sure you are not holding the button too long when you expect a short click.

---

## Wi-Fi Portal Does Not Open

**Symptoms:** After selecting Wi-Fi in the menu, the `BFU-SETUP` network does not appear on your phone.

**Possible causes and fixes:**

1. **Wait a moment** — The AP takes 1–2 seconds to start. Wait and refresh your phone's Wi-Fi list.
2. **AP already active** — If the portal was previously started and not stopped, try pressing the button to go back and re-entering the Wi-Fi menu.
3. **Socket error** — Check the Thonny REPL for `Portal start error`. This may indicate a port conflict. Reset the device and try again.
4. **Phone auto-disconnects** — Some phones disconnect from networks with no internet. Tap **Stay connected** when prompted.

---

## YouTube API Error

**Symptoms:** The subscriber screen shows `API ПОМИЛКА` (API Error).

**Possible causes and fixes:**

1. **No Wi-Fi** — The device must be connected to Wi-Fi first. Check the Status screen.
2. **Wrong API key** — Verify that `YOUTUBE_API_KEY` in `src/main.py` is your real key, not the placeholder.
3. **API not enabled** — Go to Google Cloud Console and confirm that **YouTube Data API v3** is enabled for your project.
4. **Quota exceeded** — The free quota is 10,000 units/day. Each subscriber fetch uses 1 unit. This is unlikely to be exceeded in normal use.
5. **Wrong Channel ID** — Verify `YOUTUBE_CHANNEL_ID` is correct. It should start with `UC`.
6. **Network timeout** — The request has no explicit timeout. If the network is slow, it may hang. Reset the device and try again.

---

## Subscriber Count Differs from YouTube Studio

**Symptoms:** The displayed count is lower or different from what you see in YouTube Studio.

**Explanation:**

This is expected behaviour. The YouTube Data API v3 returns a **public subscriber count**, which is:

- **Rounded** to 3 significant figures for channels with more than 1,000 subscribers
- **Cached** — may be delayed by minutes to hours compared to the real-time count

YouTube Studio shows the exact count, which is only available to the channel owner through the authenticated API. The public API used in this project does not support authentication.

This is a YouTube platform limitation and cannot be fixed in the firmware.

---

## Memory Error on Startup

**Symptoms:** The device crashes with `MemoryError` or `OSError: [Errno 12] ENOMEM`.

**Possible causes and fixes:**

1. **Outdated firmware** — Flash the latest MicroPython firmware for ESP32-C3 (see [installation.md](installation.md)).
2. **Large font dictionary** — The `FONT_UA` dictionary uses significant RAM. Run `gc.collect()` before large operations (already done in `fetch_youtube_subscribers()`).
3. **Heap fragmentation** — Reset the device. If the error persists after a fresh boot, re-flash the firmware.

---

## Wrong Pin Numbers / Nothing Works

**Symptoms:** Multiple components fail to work after assembly.

**Checklist:**

- [ ] Are you using an **ESP32-C3 Super Mini** specifically? Other ESP32 variants have different pin layouts.
- [ ] Is the display connected to **SPI bus 1** (GPIO 4 = SCK, GPIO 6 = MOSI)?
- [ ] Is VCC connected to **3.3 V**, not 5 V?
- [ ] Are all GND connections made?
- [ ] Does the Thonny REPL show any error messages on startup?

If all else fails, open Thonny, connect to the device, and run:
```python
from machine import Pin
p = Pin(4, Pin.OUT)
p.value(1)
```
This tests whether GPIO 4 responds. If it does not, the board may be damaged.
