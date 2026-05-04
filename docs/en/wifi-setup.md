# Wi-Fi Setup Guide

## Overview

The device includes a built-in Wi-Fi setup portal. When you select **Settings → Wi-Fi** from the menu, the ESP32-C3 creates a Wi-Fi access point called `BFU-SETUP`. You connect your phone or computer to this network, open a web page, and enter your home Wi-Fi credentials — all without a USB cable or computer.

---

## How the Portal Works

1. The ESP32-C3 activates its **SoftAP** (software access point) mode.
2. A small **HTTP server** starts on port 80 at IP address `192.168.4.1`.
3. The server is **non-blocking** — it runs inside the main loop, so the display and encoder remain responsive.
4. When you submit the form, the device connects to your home Wi-Fi and stops the portal.

---

## Step-by-Step Instructions

### Step 1 — Start the Portal

1. On the device, rotate the encoder to highlight **НАЛАШТУВАННЯ** (Settings).
2. Press the encoder button to enter the Settings menu.
3. Rotate to highlight **WI-FI** and press the button.
4. The display will show a QR code and the text `BFU-SETUP`.

---

### Step 2 — Connect Your Phone

**Option A — Scan the QR code (recommended)**

1. Open your phone camera app.
2. Point it at the QR code on the display.
3. Tap the notification to connect to `BFU-SETUP`.

**Option B — Connect manually**

1. Open your phone's Wi-Fi settings.
2. Find the network `BFU-SETUP` in the list.
3. Connect using the password: `12345678`

---

### Step 3 — Open the Setup Page

1. Open a browser on your phone (Chrome, Safari, Firefox, etc.).
2. Type `http://192.168.4.1` in the address bar and press Enter.
3. The BFU Wi-Fi Setup page will load.

> ℹ️ Some phones may show a "No internet" warning when connected to `BFU-SETUP`. This is normal — tap **Stay connected** or **Use this network anyway**.

---

### Step 4 — Enter Your Wi-Fi Credentials

1. The page shows a dropdown list of nearby Wi-Fi networks (scanned automatically).
2. Select your home Wi-Fi network from the dropdown.
3. Enter your Wi-Fi password in the password field.
4. Press **Connect**.

---

### Step 5 — Wait for Connection

1. The browser will show: *"Connecting to Wi-Fi. Check the device screen."*
2. On the device display, you will see the connecting screen.
3. After up to 20 seconds:
   - **Success** — the display shows **ПІДКЛЮЧЕНО** (Connected) and the assigned IP address.
   - **Failure** — the display shows **ПОМИЛКА** (Error). Check your password and try again.

---

### Step 6 — Return to Menu

1. Press the encoder button to return to the main menu.
2. The Wi-Fi connection is now active.
3. Navigate to **ПІДПИСНИКИ** (Subscribers) to fetch your YouTube subscriber count.

---

## Portal Access Point Details

| Setting | Value |
|---|---|
| SSID | `BFU-SETUP` |
| Password | `12345678` |
| IP Address | `192.168.4.1` |
| Port | 80 (HTTP) |

---

## Notes

- The portal stops automatically after a successful Wi-Fi connection.
- Press the encoder button at any time to cancel the portal and return to the menu.
- The device does not save Wi-Fi credentials between reboots. You will need to reconnect after each power cycle. (This is a MicroPython limitation — persistent storage can be added manually if needed.)
- The portal page scans for nearby networks each time it loads. If your network does not appear, move the device closer to your router and reload the page.
