import network
import time
import ntptime
import urequests
from machine import Pin
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P4
from wifi_secrets import WIFI_SSID, WIFI_PASSWORD

# Display Setup (320x240)
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_P4)
BRIGHT_LEVELS = [0.1, 0.2, 0.35, 0.5, 0.65, 0.8, 1.0]
bright_index = 3
display.set_backlight(BRIGHT_LEVELS[bright_index])
display.set_font("bitmap8")
DEBUG = True

# Farben definieren (RGB)
WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)
BLUE = display.create_pen(0, 0, 150)
RED = display.create_pen(200, 0, 0)
GREEN = display.create_pen(0, 200, 0)
YELLOW = display.create_pen(255, 200, 0)

REFRESH_INTERVAL = 30
HEADER_H = 48
LEGEND_Y = 216
PROGRESS_Y = 232
PROGRESS_H = 6
NTP_HOST = "de.pool.ntp.org"
FETCH_ICON_X = 304
FETCH_ICON_Y = 224

# Buttons on Pico Display Pack 2.8" (active low)
button_a = Pin(12, Pin.IN, Pin.PULL_UP)
button_b = Pin(13, Pin.IN, Pin.PULL_UP)
button_x = Pin(14, Pin.IN, Pin.PULL_UP)
button_y = Pin(15, Pin.IN, Pin.PULL_UP)

def connect_wifi():
    if DEBUG:
        print("WiFi: connecting...")
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    display.text("Connecting to WiFi...", 10, 10, 240, 3)
    display.update()
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        time.sleep(1)
    
    if wlan.status() != 3:
        if DEBUG:
            print("WiFi: failed, status", wlan.status())
        display.set_pen(RED)
        display.text("WiFi Failed!", 10, 40, 240, 3)
        display.update()
        return False
    if DEBUG:
        print("WiFi: connected, status", wlan.status(), "ip", wlan.ifconfig()[0])
    return True

def draw_header(time_str=None):
    display.set_pen(BLUE)
    display.rectangle(0, 0, 320, HEADER_H)
    display.set_pen(WHITE)
    display.text("Auerberger Mitte -> Koenigstr.", 6, 10, 220, 2)
    if time_str:
        display.text(time_str, 230, 8, 80, 3)

def sync_time():
    try:
        ntptime.host = NTP_HOST
        ntptime.settime()
        if DEBUG:
            print("NTP: sync ok")
        return True
    except Exception as e:
        if DEBUG:
            print("NTP: sync failed", e)
        print("NTP Error:", e)
        return False

def _last_sunday(year, month):
    for day in range(31, 24, -1):
        try:
            secs = time.mktime((year, month, day, 0, 0, 0, 0, 0))
        except OSError:
            continue
        # weekday: Monday=0 ... Sunday=6
        if time.localtime(secs)[6] == 6:
            return day
    return 31

def _berlin_offset_seconds(utc_secs):
    year = time.localtime(utc_secs)[0]
    start_day = _last_sunday(year, 3)
    end_day = _last_sunday(year, 10)
    dst_start = time.mktime((year, 3, start_day, 1, 0, 0, 0, 0))
    dst_end = time.mktime((year, 10, end_day, 1, 0, 0, 0, 0))
    if dst_start <= utc_secs < dst_end:
        return 2 * 3600
    return 1 * 3600

def berlin_time_tuple():
    utc_secs = time.time()
    return time.localtime(utc_secs + _berlin_offset_seconds(utc_secs))

def format_time_hhmm(t):
    return "{:02d}:{:02d}".format(t[3], t[4])

def fetch_data():
    try:
        if DEBUG:
            print("API: fetch start")
        r = urequests.get("https://fahrplan-oynwk.bunny.run/")
        data = r.json()
        r.close()
        if DEBUG:
            print("API: fetch ok, departures", len(data.get("departures", [])))
        return data.get("departures", [])
    except Exception as e:
        if DEBUG:
            print("API: fetch failed", e)
        print("Fetch Error:", e)
        return None

def fetch_data_retry():
    delay = 2
    while True:
        data = fetch_data()
        if data is not None:
            return data
        if DEBUG:
            print("API: retry in", delay, "s")
        time.sleep(delay)
        if delay < 8:
            delay += 1

def iso_to_berlin_time(iso_str):
    # Example: 2026-01-11T12:09:20.000Z
    year = int(iso_str[0:4])
    month = int(iso_str[5:7])
    day = int(iso_str[8:10])
    hour = int(iso_str[11:13])
    minute = int(iso_str[14:16])
    utc_secs = time.mktime((year, month, day, hour, minute, 0, 0, 0))
    local = time.localtime(utc_secs + _berlin_offset_seconds(utc_secs))
    return format_time_hhmm(local)

def compact_duration(duration):
    if duration and duration.endswith(" min"):
        return duration.replace(" min", "m")
    return duration

def render_departures(departures):
    display.set_pen(BLACK)
    display.clear()
    draw_header(format_time_hhmm(berlin_time_tuple()))
    
    if not departures:
        display.set_pen(WHITE)
        display.text("No data available", 10, 60, 300, 3)
    else:
        y_pos = 60
        for dep in departures[:4]: # Max 4 Eintraege
            # Zeit extrahieren (HH:MM)
            # ISO String: 2026-01-11T12:09:20.000Z -> 12:09
            time_str = iso_to_berlin_time(dep["departure"])
            delay = dep["delay"]
            stops = dep.get("transfers")
            duration = compact_duration(dep.get("duration"))
            
            # Zeile zeichnen
            display.set_pen(WHITE)
            display.text(f"{time_str}", 10, y_pos, 300, 4)
            
            # Delay Anzeige
            if delay > 0:
                display.set_pen(RED)
            else:
                display.set_pen(GREEN)
            extra = []
            if stops is not None:
                extra.append(f"H{stops}")
            if duration:
                extra.append(f"D{duration}")
            if extra:
                display.text(f"+{delay} " + " ".join(extra), 110, y_pos, 200, 3)
            else:
                display.text(f"+{delay}", 110, y_pos, 140, 3)
            
            y_pos += 35

    display.set_pen(WHITE)
    display.text("Legende: +Versp. H=Halte D=Dauer", 6, LEGEND_Y, 310, 2)
            
    display.update()

def draw_progress(seconds_left, total):
    # Clear progress area
    display.set_pen(BLACK)
    display.rectangle(0, PROGRESS_Y, 320, PROGRESS_H)

    # Draw progress bar
    width = int((seconds_left / total) * 320)
    display.set_pen(YELLOW)
    display.rectangle(0, PROGRESS_Y, width, PROGRESS_H)
    display.update()

def draw_fetch_icon(show):
    size = 10
    display.set_pen(BLACK)
    display.rectangle(FETCH_ICON_X - 2, FETCH_ICON_Y - 2, size + 4, size + 4)
    if show:
        display.set_pen(YELLOW)
        display.circle(FETCH_ICON_X + size // 2, FETCH_ICON_Y + size // 2, size // 2)
    display.update()

def play_refresh_animation():
    display.set_pen(WHITE)
    display.clear()
    display.update()
    time.sleep(0.03)
    display.set_pen(BLACK)
    display.clear()
    draw_header(format_time_hhmm(berlin_time_tuple()))
    display.update()

def departures_key(departures):
    if departures is None:
        return None
    if not departures:
        return ("empty",)
    first = departures[0]
    return (
        first.get("departure"),
        first.get("arrival"),
        first.get("delay"),
        first.get("transfers"),
    )

def any_button_pressed():
    return (
        not button_a.value()
        or not button_x.value()
        or not button_y.value()
    )

def dim_button_pressed():
    return not button_b.value()

def toggle_brightness():
    global bright_index
    bright_index = (bright_index + 1) % len(BRIGHT_LEVELS)
    display.set_backlight(BRIGHT_LEVELS[bright_index])
    if DEBUG:
        print("UI: brightness", BRIGHT_LEVELS[bright_index])

# Hauptschleife
if connect_wifi():
    sync_time()
    last_key = None
    last_departures = None
    force_refresh = False
    while True:
        draw_fetch_icon(True)
        data = fetch_data_retry()
        render_departures(data)
        last_key = departures_key(data)
        last_departures = data
        force_refresh = False
        draw_fetch_icon(False)
        for remaining in range(REFRESH_INTERVAL, 0, -1):
            # Update header time each second
            draw_header(format_time_hhmm(berlin_time_tuple()))
            draw_progress(remaining, REFRESH_INTERVAL)
            for _ in range(10):
                if dim_button_pressed():
                    toggle_brightness()
                    time.sleep(0.15)
                if any_button_pressed():
                    force_refresh = True
                    if DEBUG:
                        print("UI: manual refresh")
                    time.sleep(0.15)
                    break
                time.sleep(0.1)
            if force_refresh:
                break
