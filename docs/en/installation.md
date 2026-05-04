# Installation Guide

## Requirements

- ESP32-C3 Super Mini board
- USB-C cable
- Computer with [Thonny IDE](https://thonny.org/) installed
- Internet connection (for downloading firmware)

---

## Step 1 — Flash MicroPython Firmware

1. Download the latest MicroPython firmware for ESP32-C3:
   - Go to [https://micropython.org/download/esp32c3/](https://micropython.org/download/esp32c3/)
   - Download the latest `.bin` file (e.g. `ESP32_GENERIC_C3-20240602-v1.23.0.bin`)

2. Connect the ESP32-C3 to your computer via USB-C.

3. Open **Thonny IDE**.

4. Go to **Tools → Options → Interpreter**.

5. Select **MicroPython (ESP32)** from the dropdown.

6. Select the correct COM port (e.g. `COM3` on Windows, `/dev/ttyUSB0` on Linux/macOS).

7. Click **Install or update MicroPython (esptool)**.

8. In the dialog:
   - Select your device port
   - Click **Browse** and select the downloaded `.bin` file
   - Click **Install**

9. Wait for the flash to complete. The device will reboot automatically.

---

## Step 2 — Open the Project File

1. In Thonny, click **File → Open**.
2. Navigate to the project folder and open `src/main.py`.
3. Before uploading, paste your YouTube API key:
   ```python
   YOUTUBE_API_KEY = "PASTE_YOUR_API_KEY_HERE"
   ```
   Replace the placeholder with your real key.
   See [youtube-api.md](youtube-api.md) for instructions on getting a key.

---

## Step 3 — Upload to the Device

1. In Thonny, click **File → Save as…**
2. A dialog will appear — choose **MicroPython device**.
3. Type `main.py` as the filename and click **OK**.
4. The file is now saved directly to the ESP32-C3 flash memory.

---

## Step 4 — Run the Project

1. Press the **Reset** button on the ESP32-C3, or click the green **Run** button in Thonny.
2. The display should light up and show the main menu.
3. If the display stays black, check your wiring — see [wiring.md](wiring.md).

---

## Notes

- The file must be saved as `main.py` on the device. MicroPython runs `main.py` automatically on boot.
- You do not need to keep the USB cable connected after uploading. The device runs standalone from any 3.3–5 V power source.
- If you need to re-upload, simply reconnect via USB and repeat Step 3.
