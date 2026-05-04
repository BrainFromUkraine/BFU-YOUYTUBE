from machine import Pin, SPI
import time
import network
import ntptime
import urequests
import ujson
import gc
import socket

# ─── DISPLAY PINS ────────────────────────────────────────────────────────────
PIN_SCK  = 4
PIN_MOSI = 6
PIN_DC   = 7
PIN_CS   = 10
PIN_RST  = 5

# ─── ROTARY ENCODER PINS ─────────────────────────────────────────────────────
PIN_ENC_CLK = 3
PIN_ENC_DT  = 2
PIN_ENC_SW  = 1

ENCODER_THRESHOLD = 2
LONG_PRESS_MS     = 900

# ─── RAILWAY BACKEND ─────────────────────────────────────────────────────────
# Set these to your Railway app URLs.
# Leave empty to disable (status will show "НЕМА API").
BACKEND_SUBSCRIBERS_URL = "https://bfu-youytube-production.up.railway.app/api/subscribers"
BACKEND_AVATAR_URL      = "https://bfu-youytube-production.up.railway.app/api/avatar-rgb565"
DEVICE_API_TOKEN        = "BFU_ESP32_YT_9kP7xQ_2026"

YOUTUBE_UPDATE_MS    = 60000  # Refresh interval in milliseconds (60 seconds)
UK_TIME_OFFSET_HOURS = 1      # UTC+1 for BST; change to 0 for GMT

# ─── WI-FI SETUP PORTAL ──────────────────────────────────────────────────────
AP_SSID     = "BFU-SETUP"
AP_PASSWORD = "12345678"
AP_IP       = "192.168.4.1"

# ─── COLOUR PALETTE (RGB565) ─────────────────────────────────────────────────
BLACK  = 0x0000
WHITE  = 0xFFFF
BLUE   = 0x001F
RED    = 0xF800
GREEN  = 0x07E0
YELLOW = 0xFFE0
CYAN   = 0x07FF
ORANGE = 0xFD20
DARK   = 0x0841
GREY   = 0x7BEF

# ─── MENU LAYOUT CONSTANTS ───────────────────────────────────────────────────
MENU_X       = 25
MENU_W       = 190
MENU_H       = 25
MENU_Y_START = 82
MENU_Y_STEP  = 34


def color_bytes(color, count):
    return bytes([color >> 8, color & 0xFF]) * count


# ─── CUSTOM BITMAP FONT (Ukrainian uppercase + required Latin uppercase + digits + symbols) ──
# Trimmed to only characters used in the UI to save RAM on ESP32-C3.
FONT_UA = {
    # ── Ukrainian uppercase ───────────────────────────────────────────────────
    "А": ["01110","10001","10001","11111","10001","10001","10001"],
    "Б": ["11111","10000","10000","11110","10001","10001","11110"],
    "В": ["11110","10001","10001","11110","10001","10001","11110"],
    "Г": ["11111","10000","10000","10000","10000","10000","10000"],
    "Д": ["00111","01001","10001","10001","10001","10001","11111"],
    "Е": ["11111","10000","10000","11110","10000","10000","11111"],
    "З": ["11110","00001","00001","01110","00001","00001","11110"],
    "И": ["10001","10011","10101","10101","11001","10001","10001"],
    "І": ["11111","00100","00100","00100","00100","00100","11111"],
    "К": ["10001","10010","10100","11000","10100","10010","10001"],
    "Л": ["00111","01001","10001","10001","10001","10001","10001"],
    "М": ["10001","11011","10101","10101","10001","10001","10001"],
    "Н": ["10001","10001","10001","11111","10001","10001","10001"],
    "О": ["01110","10001","10001","10001","10001","10001","01110"],
    "П": ["11111","10001","10001","10001","10001","10001","10001"],
    "Р": ["11110","10001","10001","11110","10000","10000","10000"],
    "С": ["01111","10000","10000","10000","10000","10000","01111"],
    "Т": ["11111","00100","00100","00100","00100","00100","00100"],
    "У": ["10001","10001","10001","01111","00001","00001","11110"],
    "Х": ["10001","10001","01010","00100","01010","10001","10001"],
    "Ц": ["10001","10001","10001","10001","10001","11111","00001"],
    "Ч": ["10001","10001","10001","01111","00001","00001","00001"],
    "Ш": ["10101","10101","10101","10101","10101","10101","11111"],
    "Щ": ["10101","10101","10101","10101","10101","11111","00001"],
    "Ь": ["10000","10000","10000","11110","10001","10001","11110"],
    "Ю": ["10010","10101","10101","11101","10101","10101","10010"],
    "Я": ["01111","10001","10001","01111","00101","01001","10001"],
    # ── Latin uppercase (only letters used in UI strings) ─────────────────────
    "A": ["01110","10001","10001","11111","10001","10001","10001"],
    "B": ["11110","10001","10001","11110","10001","10001","11110"],
    "C": ["01111","10000","10000","10000","10000","10000","01111"],
    "E": ["11111","10000","10000","11110","10000","10000","11111"],
    "F": ["11111","10000","10000","11110","10000","10000","10000"],
    "I": ["11111","00100","00100","00100","00100","00100","11111"],
    "K": ["10001","10010","10100","11000","10100","10010","10001"],
    "L": ["10000","10000","10000","10000","10000","10000","11111"],
    "N": ["10001","11001","10101","10011","10001","10001","10001"],
    "O": ["01110","10001","10001","10001","10001","10001","01110"],
    "P": ["11110","10001","10001","11110","10000","10000","10000"],
    "R": ["11110","10001","10001","11110","10100","10010","10001"],
    "S": ["01111","10000","10000","01110","00001","00001","11110"],
    "T": ["11111","00100","00100","00100","00100","00100","00100"],
    "U": ["10001","10001","10001","10001","10001","10001","01110"],
    "W": ["10001","10001","10001","10101","10101","11011","10001"],
    "Y": ["10001","10001","01010","00100","00100","00100","00100"],
    # ── Digits ────────────────────────────────────────────────────────────────
    "0": ["01110","10001","10011","10101","11001","10001","01110"],
    "1": ["00100","01100","00100","00100","00100","00100","01110"],
    "2": ["01110","10001","00001","00010","00100","01000","11111"],
    "3": ["11110","00001","00001","01110","00001","00001","11110"],
    "4": ["00010","00110","01010","10010","11111","00010","00010"],
    "5": ["11111","10000","10000","11110","00001","00001","11110"],
    "6": ["01110","10000","10000","11110","10001","10001","01110"],
    "7": ["11111","00001","00010","00100","01000","01000","01000"],
    "8": ["01110","10001","10001","01110","10001","10001","01110"],
    "9": ["01110","10001","10001","01111","00001","00001","01110"],
    # ── Symbols ───────────────────────────────────────────────────────────────
    "-": ["00000","00000","00000","11111","00000","00000","00000"],
    "_": ["00000","00000","00000","00000","00000","00000","11111"],
    ".": ["00000","00000","00000","00000","00000","00100","00100"],
    "/": ["00001","00010","00010","00100","01000","01000","10000"],
    ":": ["00000","00100","00100","00000","00100","00100","00000"],
    "!": ["00100","00100","00100","00100","00100","00000","00100"],
    "?": ["01110","10001","00001","00010","00100","00000","00100"],
    " ": ["00000","00000","00000","00000","00000","00000","00000"],
}


# ─── GC9A01 DISPLAY DRIVER ───────────────────────────────────────────────────
class GC9A01:
    def __init__(self, spi, cs, dc, rst):
        self.spi = spi
        self.cs  = Pin(cs,  Pin.OUT, value=1)
        self.dc  = Pin(dc,  Pin.OUT, value=0)
        self.rst = Pin(rst, Pin.OUT, value=1)
        self.reset()
        self.init_display()

    def reset(self):
        self.rst.value(1)
        time.sleep_ms(50)
        self.rst.value(0)
        time.sleep_ms(50)
        self.rst.value(1)
        time.sleep_ms(120)

    def cmd(self, command):
        self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytes([command]))
        self.cs.value(1)

    def data(self, data):
        self.cs.value(0)
        self.dc.value(1)
        self.spi.write(data)
        self.cs.value(1)

    def init_display(self):
        self.cmd(0xEF)
        self.cmd(0xEB); self.data(b'\x14')
        self.cmd(0xFE); self.cmd(0xEF)
        self.cmd(0xEB); self.data(b'\x14')
        self.cmd(0x84); self.data(b'\x40')
        self.cmd(0x85); self.data(b'\xFF')
        self.cmd(0x86); self.data(b'\xFF')
        self.cmd(0x87); self.data(b'\xFF')
        self.cmd(0x88); self.data(b'\x0A')
        self.cmd(0x89); self.data(b'\x21')
        self.cmd(0x8A); self.data(b'\x00')
        self.cmd(0x8B); self.data(b'\x80')
        self.cmd(0x8C); self.data(b'\x01')
        self.cmd(0x8D); self.data(b'\x01')
        self.cmd(0x8E); self.data(b'\xFF')
        self.cmd(0x8F); self.data(b'\xFF')
        self.cmd(0xB6); self.data(b'\x00\x20')
        self.cmd(0x36); self.data(b'\x08')
        self.cmd(0x3A); self.data(b'\x05')
        self.cmd(0x90); self.data(b'\x08\x08\x08\x08')
        self.cmd(0xBD); self.data(b'\x06')
        self.cmd(0xBC); self.data(b'\x00')
        self.cmd(0xFF); self.data(b'\x60\x01\x04')
        self.cmd(0xC3); self.data(b'\x13')
        self.cmd(0xC4); self.data(b'\x13')
        self.cmd(0xC9); self.data(b'\x22')
        self.cmd(0xBE); self.data(b'\x11')
        self.cmd(0xE1); self.data(b'\x10\x0E')
        self.cmd(0xDF); self.data(b'\x21\x0C\x02')
        self.cmd(0xF0); self.data(b'\x45\x09\x08\x08\x26\x2A')
        self.cmd(0xF1); self.data(b'\x43\x70\x72\x36\x37\x6F')
        self.cmd(0xF2); self.data(b'\x45\x09\x08\x08\x26\x2A')
        self.cmd(0xF3); self.data(b'\x43\x70\x72\x36\x37\x6F')
        self.cmd(0xED); self.data(b'\x1B\x0B')
        self.cmd(0xAE); self.data(b'\x77')
        self.cmd(0xCD); self.data(b'\x63')
        self.cmd(0x70); self.data(b'\x07\x07\x04\x0E\x0F\x09\x07\x08\x03')
        self.cmd(0xE8); self.data(b'\x34')
        self.cmd(0x62); self.data(b'\x18\x0D\x71\xED\x70\x70\x18\x0F\x71\xEF\x70\x70')
        self.cmd(0x63); self.data(b'\x18\x11\x71\xF1\x70\x70\x18\x13\x71\xF3\x70\x70')
        self.cmd(0x64); self.data(b'\x28\x29\xF1\x01\xF1\x00\x07')
        self.cmd(0x66); self.data(b'\x3C\x00\xCD\x67\x45\x45\x10\x00\x00\x00')
        self.cmd(0x67); self.data(b'\x00\x3C\x00\x00\x00\x01\x54\x10\x32\x98')
        self.cmd(0x74); self.data(b'\x10\x85\x80\x00\x00\x4E\x00')
        self.cmd(0x98); self.data(b'\x3E\x07')
        self.cmd(0x35)
        self.cmd(0x21)
        self.cmd(0x11)
        time.sleep_ms(120)
        self.cmd(0x29)

    def window(self, x0, y0, x1, y1):
        self.cmd(0x2A)
        self.data(bytes([x0 >> 8, x0 & 255, x1 >> 8, x1 & 255]))
        self.cmd(0x2B)
        self.data(bytes([y0 >> 8, y0 & 255, y1 >> 8, y1 & 255]))
        self.cmd(0x2C)

    def write_block(self, x, y, w, h, buf):
        if w <= 0 or h <= 0:
            return
        self.window(x, y, x + w - 1, y + h - 1)
        self.cs.value(0)
        self.dc.value(1)
        self.spi.write(buf)
        self.cs.value(1)

    def fill_rect(self, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return
        self.window(x, y, x + w - 1, y + h - 1)
        line = color_bytes(color, w)
        self.cs.value(0)
        self.dc.value(1)
        for _ in range(h):
            self.spi.write(line)
        self.cs.value(1)

    def fill(self, color):
        self.fill_rect(0, 0, 240, 240, color)

    def ua_text(self, txt, x, y, color=WHITE, bg=BLACK, scale=1):
        """Render text using the custom Ukrainian/Latin bitmap font with optional scaling."""
        char_w = 6 * scale
        char_h = 8 * scale
        w = len(txt) * char_w
        h = char_h
        if w <= 0 or h <= 0:
            return
        buf = bytearray(w * h * 2)
        bg_hi = bg >> 8
        bg_lo = bg & 0xFF
        fg_hi = color >> 8
        fg_lo = color & 0xFF
        for i in range(0, len(buf), 2):
            buf[i]     = bg_hi
            buf[i + 1] = bg_lo
        for char_index, ch in enumerate(txt):
            glyph  = FONT_UA.get(ch, FONT_UA[" "])
            base_x = char_index * char_w
            for row_index, row in enumerate(glyph):
                for col_index, pixel in enumerate(row):
                    if pixel == "1":
                        for sy in range(scale):
                            for sx in range(scale):
                                px  = base_x + col_index * scale + sx
                                py  = row_index * scale + sy
                                pos = (py * w + px) * 2
                                buf[pos]     = fg_hi
                                buf[pos + 1] = fg_lo
        self.write_block(x, y, w, h, buf)


# ─── HARDWARE INITIALISATION ─────────────────────────────────────────────────
spi     = SPI(1, baudrate=30000000, polarity=0, phase=0, sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI))
display = GC9A01(spi, PIN_CS, PIN_DC, PIN_RST)

enc_clk = Pin(PIN_ENC_CLK, Pin.IN, Pin.PULL_UP)
enc_dt  = Pin(PIN_ENC_DT,  Pin.IN, Pin.PULL_UP)
enc_sw  = Pin(PIN_ENC_SW,  Pin.IN, Pin.PULL_UP)

gc.collect()
print("Free memory before WiFi:", gc.mem_free())
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
ap   = network.WLAN(network.AP_IF)

# ─── MENU STATE ──────────────────────────────────────────────────────────────
main_menu_items     = ["ПІДПИСНИКИ", "СТАТУС", "НАЛАШТУВАННЯ"]
settings_menu_items = ["WI-FI", "НАЗАД"]

current_menu     = "MAIN"
selected         = 0
inside_page      = False
last_clk         = enc_clk.value()
last_sw          = enc_sw.value()
encoder_step     = 0
button_down      = False
button_down_time = 0

# ─── YOUTUBE STATE ───────────────────────────────────────────────────────────
subscriber_count    = 0
last_youtube_update = 0
youtube_status_text = "НЕ ОНОВЛЕНО"

# ─── WI-FI STATE ─────────────────────────────────────────────────────────────
wifi_status_text    = "НЕ ПІДКЛЮЧЕНО"
wifi_portal_running = False
server_socket       = None
screen_mode         = "MENU"

# ─── QR CODE ─────────────────────────────────────────────────────────────────
# Real QR code for: WIFI:T:WPA;S:BFU-SETUP;P:12345678;;
QR_WIFI_SETUP = [
    "000000000000000000000000000000000",
    "000000000000000000000000000000000",
    "001111111001010001110100111111100",
    "001000001001010000011000100000100",
    "001011101010110010100000101110100",
    "001011101011001000000010101110100",
    "001011101011001111000010101110100",
    "001000001011011111101010100000100",
    "001111111010101010101010111111100",
    "000000000011110100001010000000000",
    "001011111001010010111010111110000",
    "000101100011100000010010101011000",
    "000010011101010001111001110100000",
    "001010110100110010001011101001100",
    "000100111111011000111010011110000",
    "001110100111001110000011011011000",
    "000100111000001111001011010010000",
    "001010010001010101000011100100000",
    "000001011000010010111000010101100",
    "001110110010100000000011001101000",
    "001011101100111001111010011000000",
    "001011100100011010101101101000100",
    "001001101000010001111011111110000",
    "000000000011001110000110001010000",
    "001111111000100111011010101010000",
    "001000001010101100100110001100100",
    "001011101011101011111011111101000",
    "001011101011010100000100001101100",
    "001011101011010101100110011111000",
    "001000001001101101101010001101000",
    "001111111011110101111000001100000",
    "000000000000000000000000000000000",
    "000000000000000000000000000000000",
]


# ─── WI-FI PERSISTENT CONFIG (JSON) ─────────────────────────────────────────
WIFI_CONFIG_FILE = "wifi_config.json"


def save_wifi_config(ssid, password):
    try:
        cfg = {"ssid": ssid, "password": password}
        with open(WIFI_CONFIG_FILE, "w") as f:
            ujson.dump(cfg, f)
        print("WiFi config saved:", ssid)
    except Exception as e:
        print("save_wifi_config error:", e)


def load_wifi_config():
    try:
        with open(WIFI_CONFIG_FILE, "r") as f:
            cfg = ujson.load(f)
        ssid     = cfg.get("ssid", "")
        password = cfg.get("password", "")
        if ssid:
            print("WiFi config loaded:", ssid)
            return ssid, password
        return None, None
    except Exception as e:
        print("load_wifi_config error:", e)
        return None, None


def _reset_sta():
    """Disable AP, reset STA interface — prevents 0x0102 error."""
    ap.active(False)
    print("AP disabled before saved STA connect")
    time.sleep_ms(500)
    wlan.active(False)
    time.sleep_ms(500)
    wlan.active(True)
    time.sleep_ms(500)
    print("STA reset before saved connect")


def connect_saved_wifi():
    """Try to connect to the saved Wi-Fi network on boot. Non-blocking with timeout."""
    global wifi_status_text
    ssid, password = load_wifi_config()
    if ssid is None:
        wifi_status_text = "НЕ ПІДКЛЮЧЕНО"
        print("No saved WiFi config")
        return False
    try:
        if wlan.isconnected():
            wifi_status_text = "WI-FI OK"
            print("Already connected:", wlan.ifconfig()[0])
            return True
        _reset_sta()
        print("Auto-connecting to:", ssid)
        wlan.connect(ssid, password)
        start = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > 15000:
                break
            time.sleep_ms(300)
        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            wifi_status_text = "WI-FI OK"
            print("Auto-connected:", ip)
            sync_time()
            return True
        else:
            wifi_status_text = "WI-FI ПОМИЛКА"
            print("Auto-connect failed")
            return False
    except Exception as e:
        print("connect_saved_wifi error:", e)
        wifi_status_text = "WI-FI ПОМИЛКА"
        return False


# ─── NTP TIME SYNC ───────────────────────────────────────────────────────────
def sync_time():
    """Sync RTC from NTP. Safe — does not crash if NTP is unreachable."""
    try:
        ntptime.settime()
        print("NTP time synced")
        print("UTC:", time.localtime())
        print("LOCAL:", get_local_time())
    except Exception as e:
        print("NTP sync failed:", e)


# ─── LOCAL TIME ──────────────────────────────────────────────────────────────
def get_local_time():
    """Return local time tuple adjusted by UK_TIME_OFFSET_HOURS."""
    return time.localtime(time.time() + UK_TIME_OFFSET_HOURS * 3600)


# ─── UTILITY ─────────────────────────────────────────────────────────────────
def center_x(text, scale):
    return (240 - len(text) * 6 * scale) // 2


# ─── YOUTUBE / BACKEND ───────────────────────────────────────────────────────
def fetch_youtube_subscribers():
    global subscriber_count, youtube_status_text, last_youtube_update

    if not wlan.isconnected():
        youtube_status_text = "НЕМА WI-FI"
        return False

    if not BACKEND_SUBSCRIBERS_URL:
        youtube_status_text = "НЕМА API"
        return False

    try:
        gc.collect()
        headers = {}
        if DEVICE_API_TOKEN:
            headers["X-Device-Token"] = DEVICE_API_TOKEN
        response = urequests.get(BACKEND_SUBSCRIBERS_URL, headers=headers)
        data     = response.json()
        response.close()
        if data.get("ok"):
            subscriber_count    = int(data["subscribers"])
            last_youtube_update = time.ticks_ms()
            youtube_status_text = "КЕШ" if data.get("stale") else "ОНОВЛЕНО"
            print("Backend subscribers:", subscriber_count)
            return True
        else:
            youtube_status_text = "API ПОМИЛКА"
            print("Backend error:", data.get("error", "unknown"))
            return False
    except Exception as e:
        print("Backend fetch error:", e)
        youtube_status_text = "API ПОМИЛКА"
        return False


# ─── CHANNEL AVATAR ──────────────────────────────────────────────────────────
AVATAR_X    = 88   # centred: (240-64)//2
AVATAR_Y    = 48
AVATAR_SIZE = 64   # must match backend AVATAR_SIZE


def draw_circle_outline(cx, cy, r, color):
    """Draw a 1-pixel-wide circle outline using the midpoint algorithm."""
    x = r
    y = 0
    err = 0
    while x >= y:
        for dx, dy in ((x, y), (y, x), (-y, x), (-x, y),
                       (-x, -y), (-y, -x), (y, -x), (x, -y)):
            display.fill_rect(cx + dx, cy + dy, 1, 1, color)
        y += 1
        if err <= 0:
            err += 2 * y + 1
        if err > 0:
            x -= 1
            err -= 2 * x + 1


def draw_avatar_frame():
    """Draw a yellow ring around the avatar and black corners to create a circular crop effect."""
    cx = AVATAR_X + AVATAR_SIZE // 2
    cy = AVATAR_Y + AVATAR_SIZE // 2
    # Black out the four square corners outside the inner circle (r=32)
    inner_r = AVATAR_SIZE // 2  # 32
    for dy in range(AVATAR_SIZE):
        for dx in range(AVATAR_SIZE):
            dist2 = (dx - inner_r) * (dx - inner_r) + (dy - inner_r) * (dy - inner_r)
            if dist2 > inner_r * inner_r:
                display.fill_rect(AVATAR_X + dx, AVATAR_Y + dy, 1, 1, BLACK)
    # Yellow ring: draw concentric outlines at r=33 and r=34
    draw_circle_outline(cx, cy, inner_r + 1, YELLOW)
    draw_circle_outline(cx, cy, inner_r + 2, YELLOW)
    draw_circle_outline(cx, cy, inner_r + 3, YELLOW)


def fetch_channel_avatar():
    """
    Fetch AVATAR_SIZE x AVATAR_SIZE raw RGB565 binary from backend
    (application/octet-stream, AVATAR_SIZE * AVATAR_SIZE * 2 bytes).
    No JSON parsing — read bytes directly and write_block().
    After drawing, applies a circular yellow frame.
    """
    if not BACKEND_AVATAR_URL:
        return False
    if not wlan.isconnected():
        return False
    try:
        gc.collect()
        headers = {}
        if DEVICE_API_TOKEN:
            headers["X-Device-Token"] = DEVICE_API_TOKEN
        response = urequests.get(BACKEND_AVATAR_URL, headers=headers)
        buf      = response.content
        response.close()
        gc.collect()

        expected = AVATAR_SIZE * AVATAR_SIZE * 2
        print("Avatar bytes:", len(buf), "expected:", expected)
        if len(buf) != expected:
            print("Avatar size mismatch — skipping draw")
            return False

        display.write_block(AVATAR_X, AVATAR_Y, AVATAR_SIZE, AVATAR_SIZE, buf)
        del buf
        gc.collect()
        print("Avatar drawn:", AVATAR_SIZE, "x", AVATAR_SIZE)
        draw_avatar_frame()
        return True
    except Exception as e:
        print("Avatar fetch/draw error:", e)
        return False


# ─── MENU HELPERS ────────────────────────────────────────────────────────────
def get_active_menu_items():
    if current_menu == "MAIN":
        return main_menu_items
    if current_menu == "SETTINGS":
        return settings_menu_items
    return main_menu_items


def draw_header(title):
    display.fill_rect(0, 0, 240, 38, BLUE)
    bfu_text = "BFU ELECTRONICS"
    # Render header text using ua_text (no framebuf needed)
    display.ua_text(bfu_text, (240 - len(bfu_text) * 6) // 2, 24, WHITE, BLUE, 1)
    if title:
        display.ua_text(title, center_x(title, 1), 8, CYAN, BLUE, 1)


def draw_footer():
    display.fill_rect(0, 212, 240, 28, DARK)
    t1 = "ОБЕРТАЙ = МЕНЮ"
    t2 = "НАТИСНИ = ВИБІР"
    display.ua_text(t1, center_x(t1, 1), 216, WHITE, DARK, 1)
    display.ua_text(t2, center_x(t2, 1), 228, CYAN,  DARK, 1)


def draw_back_footer():
    display.fill_rect(0, 212, 240, 28, DARK)
    t = "НАТИСНИ = НАЗАД"
    display.ua_text(t, center_x(t, 1), 222, CYAN, DARK, 1)


def draw_wifi_footer(text1, text2):
    display.fill_rect(0, 212, 240, 28, DARK)
    display.ua_text(text1, center_x(text1, 1), 216, WHITE, DARK, 1)
    display.ua_text(text2, center_x(text2, 1), 228, CYAN,  DARK, 1)


def get_menu_y(index):
    return MENU_Y_START + index * MENU_Y_STEP


def draw_menu_item(index):
    items = get_active_menu_items()
    item  = items[index]
    y     = get_menu_y(index)
    if index == selected:
        bg    = ORANGE
        color = BLACK
    else:
        bg    = DARK
        color = WHITE
    display.fill_rect(MENU_X, y - 5, MENU_W, MENU_H, bg)
    text_w = len(item) * 6 * 2
    text_x = MENU_X + (MENU_W - text_w) // 2
    display.ua_text(item, text_x, y + 2, color, bg, 2)


def draw_menu():
    global screen_mode
    screen_mode = "MENU"
    display.fill(BLACK)
    draw_header("")
    if current_menu == "SETTINGS":
        t = "НАЛАШТУВАННЯ"
        display.ua_text(t, center_x(t, 2), 44, CYAN, BLACK, 2)
    items = get_active_menu_items()
    for i in range(len(items)):
        draw_menu_item(i)
    draw_footer()


def update_menu_selection(old_index, new_index):
    draw_menu_item(old_index)
    draw_menu_item(new_index)


# ─── CLOCK ───────────────────────────────────────────────────────────────────
def draw_clock_static_digits():
    """Clear the full clock area and draw only HH and MM at fixed positions.
    The colon column is left black — call draw_clock_colon() separately."""
    t      = get_local_time()
    hour   = t[3]
    minute = t[4]
    display.fill_rect(40, 184, 160, 32, BLACK)
    display.ua_text("{:02d}".format(hour),   57,  186, CYAN, BLACK, 3)
    display.ua_text("{:02d}".format(minute), 129, 186, CYAN, BLACK, 3)


def draw_clock_colon(visible):
    """Redraw only the colon column — does not touch HH or MM digits."""
    display.fill_rect(108, 186, 24, 24, BLACK)
    if visible:
        display.ua_text(":", 111, 186, CYAN, BLACK, 3)


def draw_clock(colon_visible=True):
    """Convenience wrapper: draw static digits then the colon."""
    draw_clock_static_digits()
    draw_clock_colon(colon_visible)


# ─── SUBSCRIBER PAGE ─────────────────────────────────────────────────────────
def draw_subscriber_number():
    display.fill_rect(35, 124, 170, 28, BLACK)
    count_text = str(subscriber_count)
    count_w    = len(count_text) * 6 * 3
    count_x    = (240 - count_w) // 2
    display.ua_text(count_text, count_x, 124, GREEN, BLACK, 3)


def draw_subscribers_page():
    global screen_mode
    screen_mode = "SUBSCRIBERS"
    display.fill(BLACK)
    draw_header("")
    # Avatar placeholder (grey square) — replaced by avatar if fetch succeeds
    display.fill_rect(AVATAR_X, AVATAR_Y, AVATAR_SIZE, AVATAR_SIZE, DARK)
    # Subscriber number below avatar (y=124)
    draw_subscriber_number()
    # Label below number (y=158)
    display.ua_text("ПІДПИСНИКИ", center_x("ПІДПИСНИКИ", 1), 158, YELLOW, BLACK, 1)
    # Clock at bottom (y=186)
    draw_clock()
    # Fetch data
    fetch_youtube_subscribers()
    draw_subscriber_number()
    fetch_channel_avatar()


# ─── STATUS PAGE ─────────────────────────────────────────────────────────────
def draw_status_page():
    global screen_mode
    screen_mode = "STATUS"
    display.fill(BLACK)
    draw_header("СТАТУС")
    display.fill_rect(25, 58, 190, 120, DARK)
    display.fill_rect(35, 68, 170, 100, BLACK)
    display.ua_text("ESP32-C3",       74, 78,  CYAN,   BLACK, 1)
    display.ua_text("ДИСПЛЕЙ OK",     60, 100, GREEN,  BLACK, 1)
    display.ua_text("ЕНКОДЕР OK",     60, 120, GREEN,  BLACK, 1)
    display.ua_text(wifi_status_text, 48, 140, YELLOW, BLACK, 1)
    draw_back_footer()


# ─── WI-FI SETUP PORTAL (SoftAP + web form) ──────────────────────────────────
def draw_qr(matrix, x, y, scale):
    size = len(matrix)
    display.fill_rect(x - 4, y - 4, size * scale + 8, size * scale + 8, WHITE)
    for row in range(size):
        for col in range(size):
            if matrix[row][col] == "1":
                display.fill_rect(x + col * scale, y + row * scale, scale, scale, BLACK)


def draw_wifi_portal_qr_page():
    global screen_mode
    screen_mode = "WIFI_PORTAL"
    display.fill(BLACK)
    draw_header("WI-FI SETUP")
    display.ua_text("СКАНУЙ КОД", 66, 45, CYAN, BLACK, 1)
    draw_qr(QR_WIFI_SETUP, 54, 62, 4)
    display.ua_text("BFU-SETUP", 72, 198, YELLOW, BLACK, 1)
    draw_wifi_footer("PASS: 12345678", "IP: 192.168.4.1")


def draw_wifi_portal_ip_page():
    global screen_mode
    screen_mode = "WIFI_PORTAL"
    display.fill(BLACK)
    draw_header("WI-FI SETUP")
    display.fill_rect(20, 58, 200, 130, DARK)
    display.fill_rect(30, 68, 180, 110, BLACK)
    display.ua_text("ПІДКЛЮЧИСЬ",  60, 78,  CYAN,   BLACK, 1)
    display.ua_text("BFU-SETUP",   72, 100, YELLOW, BLACK, 1)
    display.ua_text("PASS:",       54, 122, WHITE,  BLACK, 1)
    display.ua_text("12345678",    90, 122, GREEN,  BLACK, 1)
    display.ua_text("ВІДКРИЙ:",    72, 146, WHITE,  BLACK, 1)
    display.ua_text("192.168.4.1", 60, 164, GREEN,  BLACK, 1)
    draw_wifi_footer("QR АБО РУЧНО", "КЛІК = НАЗАД")


def url_decode(text):
    text   = text.replace("+", " ")
    parts  = text.split("%")
    result = parts[0]
    for item in parts[1:]:
        if len(item) >= 2:
            try:
                result += chr(int(item[:2], 16)) + item[2:]
            except:
                result += "%" + item
        else:
            result += "%" + item
    return result


def html_escape(text):
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    return text


def get_wifi_scan_options():
    try:
        wlan.active(True)
        raw   = wlan.scan()
        found = []
        for net in raw:
            ssid = net[0].decode("utf-8", "ignore")
            if ssid and ssid not in found:
                found.append(ssid)
        html = ""
        for ssid in found:
            safe  = html_escape(ssid)
            html += '<option value="' + safe + '">' + safe + '</option>'
        if not html:
            html = '<option value="">No networks found</option>'
        return html
    except Exception as e:
        print("WiFi scan web error:", e)
        return '<option value="">Scan error</option>'


def web_page():
    options = get_wifi_scan_options()
    return (
        "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n"
        "<!DOCTYPE html><html><head>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>BFU Wi-Fi Setup</title>"
        "<style>body{font-family:Arial;background:#111;color:white;padding:20px;}"
        ".card{max-width:420px;margin:auto;background:#1e1e1e;padding:20px;border-radius:16px;}"
        "h1{color:#00e5ff;text-align:center;margin-top:0;}"
        "label{display:block;margin-top:16px;font-weight:bold;}"
        "select,input,button{width:100%;box-sizing:border-box;padding:14px;margin-top:8px;"
        "border-radius:10px;border:none;font-size:16px;}"
        "button{background:orange;color:black;font-weight:bold;margin-top:22px;}"
        ".small{color:#aaa;text-align:center;font-size:13px;}</style></head><body>"
        "<div class='card'><h1>BFU Wi-Fi Setup</h1>"
        "<p class='small'>Select your Wi-Fi network, enter password, then press Connect.</p>"
        "<form action='/connect' method='GET'>"
        "<label>Wi-Fi Network</label><select name='ssid'>" + options + "</select>"
        "<label>Password</label>"
        "<input name='password' type='password' placeholder='Wi-Fi password'>"
        "<button type='submit'>Connect</button></form>"
        "<p class='small'>Device AP: BFU-SETUP / 12345678</p>"
        "</div></body></html>"
    )


def web_result_page(text):
    return (
        "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n"
        "<!DOCTYPE html><html><head>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>BFU Wi-Fi Setup</title>"
        "<style>body{font-family:Arial;background:#111;color:white;padding:20px;text-align:center;}"
        ".card{max-width:420px;margin:auto;background:#1e1e1e;padding:20px;border-radius:16px;}"
        "h1{color:#00e5ff;}</style></head><body>"
        "<div class='card'><h1>BFU Wi-Fi Setup</h1><p>" + text + "</p></div></body></html>"
    )


def start_wifi_setup_portal():
    global wifi_portal_running, server_socket
    draw_wifi_portal_qr_page()
    try:
        ap.active(True)
        try:
            ap.config(essid=AP_SSID, password=AP_PASSWORD, authmode=network.AUTH_WPA_WPA2_PSK)
        except:
            ap.config(essid=AP_SSID, password=AP_PASSWORD)
        time.sleep_ms(700)

        if server_socket:
            try:
                server_socket.close()
            except:
                pass

        addr          = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(addr)
        server_socket.listen(1)
        server_socket.settimeout(0.05)

        wifi_portal_running = True
        print("WiFi setup portal started — AP:", AP_SSID, "/ http://" + AP_IP)
    except Exception as e:
        print("Portal start error:", e)


def stop_wifi_setup_portal():
    global wifi_portal_running, server_socket
    wifi_portal_running = False
    try:
        if server_socket:
            server_socket.close()
    except:
        pass
    server_socket = None
    try:
        ap.active(False)
    except:
        pass


def parse_connect_request(request):
    try:
        first_line = request.split("\r\n")[0]
        if "GET /connect?" not in first_line:
            return None, None
        query    = first_line.split("GET /connect?")[1].split(" ")[0]
        ssid     = ""
        password = ""
        for p in query.split("&"):
            if p.startswith("ssid="):
                ssid = url_decode(p[5:])
            elif p.startswith("password="):
                password = url_decode(p[9:])
        return ssid, password
    except Exception as e:
        print("Parse request error:", e)
        return None, None


def connect_to_selected_wifi(ssid, password):
    global wifi_status_text
    draw_wifi_connecting_page()
    try:
        _reset_sta()
        print("Connecting to:", ssid)
        wlan.connect(ssid, password)
        start = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > 20000:
                break
            time.sleep_ms(300)
        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            wifi_status_text = "WI-FI OK"
            print("WiFi connected:", ip)
            save_wifi_config(ssid, password)
            sync_time()
            stop_wifi_setup_portal()
            draw_wifi_result_page(True, ip)
            return True
        else:
            wifi_status_text = "WI-FI ПОМИЛКА"
            print("WiFi connection failed")
            draw_wifi_result_page(False)
            return False
    except Exception as e:
        print("Connect selected WiFi error:", e)
        wifi_status_text = "WI-FI ПОМИЛКА"
        draw_wifi_result_page(False)
        return False


def draw_wifi_connecting_page():
    global screen_mode
    screen_mode = "WIFI_CONNECTING"
    display.fill(BLACK)
    draw_header("WI-FI")
    display.fill_rect(25, 70, 190, 90, DARK)
    display.fill_rect(35, 80, 170, 70, BLACK)
    display.ua_text("ПІДКЛЮЧЕННЯ", 54, 95,  YELLOW, BLACK, 1)
    display.ua_text("ЗАЧЕКАЙ",     78, 120, CYAN,   BLACK, 1)
    draw_wifi_footer("НЕ ВИМИКАЙ", "WI-FI")


def draw_wifi_result_page(ok, ip_text=""):
    global screen_mode, wifi_status_text
    screen_mode = "WIFI_RESULT"
    display.fill(BLACK)
    draw_header("WI-FI")
    display.fill_rect(25, 58, 190, 120, DARK)
    display.fill_rect(35, 68, 170, 100, BLACK)
    if ok:
        wifi_status_text = "WI-FI OK"
        display.ua_text("ПІДКЛЮЧЕНО", 60, 82, GREEN, BLACK, 1)
        if ip_text:
            if len(ip_text) > 16:
                ip_text = ip_text[:16]
            display.ua_text("IP:",    48, 112, CYAN,  BLACK, 1)
            display.ua_text(ip_text, 72, 112, WHITE, BLACK, 1)
    else:
        wifi_status_text = "WI-FI ПОМИЛКА"
        display.ua_text("ПОМИЛКА",       78, 90,  RED,    BLACK, 1)
        display.ua_text("НЕ ПІДКЛЮЧЕНО", 42, 120, YELLOW, BLACK, 1)
    draw_wifi_footer("КЛІК = НАЗАД", "ДО МЕНЮ")


def handle_wifi_portal():
    global server_socket
    if not wifi_portal_running or server_socket is None:
        return
    try:
        conn, addr = server_socket.accept()
        print("Web client:", addr)
        request = conn.recv(2048).decode("utf-8", "ignore")

        if "GET /connect?" in request:
            ssid, password = parse_connect_request(request)
            if ssid:
                conn.send(web_result_page("Connecting to Wi-Fi. Check the device screen."))
                conn.close()
                connect_to_selected_wifi(ssid, password)
                return
            else:
                conn.send(web_result_page("SSID error. Try again."))
                conn.close()
                return

        if "GET /favicon.ico" in request:
            conn.send("HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")
            conn.close()
            return

        conn.send(web_page())
        conn.close()

        if screen_mode == "WIFI_PORTAL":
            draw_wifi_portal_ip_page()

    except OSError:
        pass
    except Exception as e:
        print("Portal handle error:", e)


# ─── NAVIGATION ──────────────────────────────────────────────────────────────
def open_selected_item():
    global current_menu, selected, inside_page
    items        = get_active_menu_items()
    current_item = items[selected]

    if current_menu == "MAIN":
        if current_item == "ПІДПИСНИКИ":
            inside_page = True
            draw_subscribers_page()
        elif current_item == "СТАТУС":
            inside_page = True
            draw_status_page()
        elif current_item == "НАЛАШТУВАННЯ":
            current_menu = "SETTINGS"
            selected     = 0
            inside_page  = False
            draw_menu()

    elif current_menu == "SETTINGS":
        if current_item == "WI-FI":
            inside_page = True
            start_wifi_setup_portal()
        elif current_item == "НАЗАД":
            current_menu = "MAIN"
            selected     = 0
            inside_page  = False
            draw_menu()


def go_back():
    global current_menu, selected, inside_page, screen_mode

    if screen_mode in ("SUBSCRIBERS", "STATUS"):
        inside_page = False
        draw_menu()
        return

    if screen_mode in ("WIFI_RESULT", "WIFI_PORTAL", "WIFI_CONNECTING"):
        stop_wifi_setup_portal()
        inside_page = False
        screen_mode = "MENU"
        draw_menu()
        return

    if current_menu == "SETTINGS":
        current_menu = "MAIN"
        selected     = 0
        draw_menu()
        return


def rotate_right():
    global selected
    if screen_mode == "MENU" and not inside_page:
        old_selected = selected
        items        = get_active_menu_items()
        selected     = (selected + 1) % len(items)
        update_menu_selection(old_selected, selected)
        print("Selected:", items[selected])


def rotate_left():
    global selected
    if screen_mode == "MENU" and not inside_page:
        old_selected = selected
        items        = get_active_menu_items()
        selected     = (selected - 1) % len(items)
        update_menu_selection(old_selected, selected)
        print("Selected:", items[selected])


def handle_short_click():
    global inside_page
    if screen_mode == "MENU":
        open_selected_item()
    elif screen_mode in ("SUBSCRIBERS", "STATUS"):
        go_back()
    elif screen_mode == "WIFI_PORTAL":
        go_back()
    elif screen_mode == "WIFI_RESULT":
        inside_page = False
        draw_menu()


def handle_long_click():
    if screen_mode in ("WIFI_RESULT", "WIFI_PORTAL", "WIFI_CONNECTING"):
        go_back()
    elif screen_mode in ("SUBSCRIBERS", "STATUS"):
        go_back()


# ─── STARTUP ─────────────────────────────────────────────────────────────────
connect_saved_wifi()
draw_menu()

print("=================================")
print("BFU YOUTUBE COUNTER STARTED")
print("AP SSID =", AP_SSID)
print("WEB SETUP = http://" + AP_IP)
print("ENCODER THRESHOLD =", ENCODER_THRESHOLD)
print("=================================")

# ─── CLOCK STATE ─────────────────────────────────────────────────────────────
_clock_colon_visible = True   # current colon blink state
_last_colon_blink_ms = 0      # last time colon was toggled
_last_clock_minute   = -1     # last drawn minute — triggers digit redraw on change

# ─── MAIN LOOP ───────────────────────────────────────────────────────────────
while True:
    handle_wifi_portal()

    clk_now = enc_clk.value()
    if clk_now != last_clk:
        if enc_dt.value() != clk_now:
            encoder_step += 1
        else:
            encoder_step -= 1

        if encoder_step >= ENCODER_THRESHOLD:
            encoder_step = 0
            rotate_right()
        elif encoder_step <= -ENCODER_THRESHOLD:
            encoder_step = 0
            rotate_left()

        last_clk = clk_now

    if screen_mode == "SUBSCRIBERS":
        # Refresh subscriber count every YOUTUBE_UPDATE_MS
        if time.ticks_diff(time.ticks_ms(), last_youtube_update) > YOUTUBE_UPDATE_MS:
            if fetch_youtube_subscribers():
                draw_subscriber_number()

        # Redraw static digits when minute changes; blink only colon every 500 ms
        _local = get_local_time()
        _current_minute = _local[4]
        if _current_minute != _last_clock_minute:
            _last_clock_minute   = _current_minute
            _clock_colon_visible = True
            draw_clock_static_digits()
            draw_clock_colon(True)

        now_ms = time.ticks_ms()
        if time.ticks_diff(now_ms, _last_colon_blink_ms) > 500:
            _last_colon_blink_ms = now_ms
            _clock_colon_visible = not _clock_colon_visible
            draw_clock_colon(_clock_colon_visible)

    sw_now = enc_sw.value()
    if last_sw == 1 and sw_now == 0:
        button_down      = True
        button_down_time = time.ticks_ms()

    if last_sw == 0 and sw_now == 1:
        if button_down:
            press_time = time.ticks_diff(time.ticks_ms(), button_down_time)
            if press_time >= LONG_PRESS_MS:
                print("Long click")
                handle_long_click()
            else:
                print("Short click")
                handle_short_click()
        button_down = False
        time.sleep_ms(120)

    last_sw = sw_now
    time.sleep_ms(1)
