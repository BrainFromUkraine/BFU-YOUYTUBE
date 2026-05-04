# Wiring Guide

## Overview

All components operate at **3.3 V logic**. The ESP32-C3 Super Mini provides 3.3 V on its VCC/3V3 pin. Do not connect any component directly to 5 V.

---

## GC9A01 Round Display

The display uses a 4-wire SPI interface.

| Display Pin | ESP32-C3 GPIO | Notes |
|---|---|---|
| SCK | GPIO 4 | SPI clock |
| MOSI | GPIO 6 | SPI data (master out) |
| DC | GPIO 7 | Data / Command select |
| CS | GPIO 10 | Chip select (active LOW) |
| RST | GPIO 5 | Reset (active LOW) |
| VCC | 3.3 V | Power — use 3.3 V only |
| GND | GND | Ground |

> ℹ️ The GC9A01 does not have a MISO pin — it is write-only.

---

## Rotary Encoder

The encoder uses three GPIO pins with internal pull-up resistors enabled in firmware.

| Encoder Pin | ESP32-C3 GPIO | Notes |
|---|---|---|
| CLK | GPIO 3 | Encoder channel A |
| DT | GPIO 2 | Encoder channel B |
| SW | GPIO 1 | Push button (active LOW) |
| VCC | 3.3 V | Power |
| GND | GND | Ground |

> ℹ️ All encoder pins use `Pin.PULL_UP` in firmware. No external resistors are needed.

---

## Wiring Diagram (Text)

```
ESP32-C3 Super Mini
┌─────────────────────┐
│ GPIO 4  ──────────── SCK  (Display)
│ GPIO 6  ──────────── MOSI (Display)
│ GPIO 7  ──────────── DC   (Display)
│ GPIO 10 ──────────── CS   (Display)
│ GPIO 5  ──────────── RST  (Display)
│ 3.3V    ──────────── VCC  (Display)
│ GND     ──────────── GND  (Display)
│                      
│ GPIO 3  ──────────── CLK  (Encoder)
│ GPIO 2  ──────────── DT   (Encoder)
│ GPIO 1  ──────────── SW   (Encoder)
│ 3.3V    ──────────── VCC  (Encoder)
│ GND     ──────────── GND  (Encoder)
└─────────────────────┘
```

---

## Important Warnings

- ⚠️ **Use 3.3 V only.** The ESP32-C3 GPIO pins are not 5 V tolerant. Connecting 5 V to any GPIO will permanently damage the chip.
- ⚠️ **Check wiring before powering on.** A short circuit between VCC and GND can damage the board.
- ⚠️ **SPI bus is shared** between the display and the SPI peripheral. Do not connect other SPI devices to the same SCK/MOSI lines without adding proper CS logic.
- ℹ️ If the encoder scrolls in the wrong direction, swap the CLK and DT wires.
- ℹ️ If the display shows a white or garbled image, check the DC and RST pins first.
