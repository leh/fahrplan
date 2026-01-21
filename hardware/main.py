import network
import time
import ntptime
import urequests
from machine import Pin, WDT, reset
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P4
from wifi_secrets import WIFI_SSID, WIFI_PASSWORD

# --- Konfiguration ---
REFRESH_INTERVAL = 30
MAX_RETRIES = 10         # Reboot nach 10 Fehlern
WDT_TIMEOUT = 8000       # 8 Sekunden (Max für RP2040 ist ca. 8.3s)
DEBUG = True

# --- Display Setup ---
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_P4)
BRIGHT_LEVELS = [0.1, 0.2, 0.35, 0.5, 0.65, 0.8, 1.0]
bright_index = 3 # Start mit 50%
display.set_backlight(BRIGHT_LEVELS[bright_index])
display.set_font("bitmap8")

# --- Farben ---
WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)
BLUE = display.create_pen(0, 0, 150)
RED = display.create_pen(200, 0, 0)
GREEN = display.create_pen(0, 200, 0)
YELLOW = display.create_pen(255, 200, 0)

# --- Layout ---
HEADER_H = 48
LEGEND_Y = 216
PROGRESS_Y = 232
PROGRESS_H = 6
FETCH_ICON_X = 304
FETCH_ICON_Y = 224

# --- Hardware Buttons ---
button_a = Pin(12, Pin.IN, Pin.PULL_UP)
button_b = Pin(13, Pin.IN, Pin.PULL_UP)
button_x = Pin(14, Pin.IN, Pin.PULL_UP)
button_y = Pin(15, Pin.IN, Pin.PULL_UP)

# --- Globale Objekte ---
# Watchdog initialisieren - ab jetzt muss wdt.feed() regelmäßig gerufen werden!
try:
    wdt = WDT(timeout=WDT_TIMEOUT)
except Exception as e:
    print("WDT Init failed:", e)
    wdt = None # Fallback falls WDT nicht verfügbar (z.B. Emulator)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

def feed_watchdog():
    if wdt:
        wdt.feed()

def ensure_wifi():
    feed_watchdog()
    if wlan.isconnected():
        return True
    
    if DEBUG:
        print("WiFi: connecting...")
    
    # Versuch zu verbinden
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    
    # Warten (max 5 Sekunden, damit Watchdog nicht zuschlägt)
    for _ in range(50):
        if wlan.isconnected():
            if DEBUG:
                print("WiFi: connected, IP", wlan.ifconfig()[0])
            return True
        time.sleep(0.1)
        feed_watchdog()
        
    if DEBUG:
        print("WiFi: failed")
    return False

def sync_time():
    try:
        ntptime.host = "de.pool.ntp.org"
        ntptime.settime()
        if DEBUG:
            print("NTP: sync ok")
        return True
    except Exception as e:
        print("NTP Error:", e)
        return False

# --- Helper Funktionen ---

def _last_sunday(year, month):
    for day in range(31, 24, -1):
        try:
            secs = time.mktime((year, month, day, 0, 0, 0, 0, 0))
        except OSError:
            continue
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

def iso_to_berlin_time(iso_str):
    try:
        year = int(iso_str[0:4])
        month = int(iso_str[5:7])
        day = int(iso_str[8:10])
        hour = int(iso_str[11:13])
        minute = int(iso_str[14:16])
        utc_secs = time.mktime((year, month, day, hour, minute, 0, 0, 0))
        local = time.localtime(utc_secs + _berlin_offset_seconds(utc_secs))
        return format_time_hhmm(local)
    except:
        return "??"

def compact_duration(duration):
    if duration and duration.endswith(" min"):
        return duration.replace(" min", "m")
    return duration

# --- Zeichenfunktionen ---

def draw_header(time_str=None):
    display.set_pen(BLUE)
    display.rectangle(0, 0, 320, HEADER_H)
    display.set_pen(WHITE)
    display.text("Auerberger Mitte -> Koenigstr.", 6, 10, 220, 2)
    if time_str:
        display.text(time_str, 230, 8, 80, 3)

def draw_progress(seconds_left, total):
    display.set_pen(BLACK)
    display.rectangle(0, PROGRESS_Y, 320, PROGRESS_H)
    if total > 0:
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

def render_departures(departures, error_msg=None):
    display.set_pen(BLACK)
    display.clear()
    draw_header(format_time_hhmm(berlin_time_tuple()))
    
    if error_msg:
        display.set_pen(RED)
        display.text(error_msg, 10, 80, 300, 3)
    elif not departures:
        display.set_pen(WHITE)
        display.text("Keine Daten", 10, 80, 300, 3)
    else:
        y_pos = 60
        for dep in departures[:4]:
            time_str = iso_to_berlin_time(dep.get("departure", ""))
            delay = dep.get("delay", 0)
            stops = dep.get("transfers")
            duration = compact_duration(dep.get("duration"))
            
            display.set_pen(WHITE)
            display.text(f"{time_str}", 10, y_pos, 300, 4)
            
            if delay > 0:
                display.set_pen(RED)
            else:
                display.set_pen(GREEN)
            
            extra = []
            if stops is not None:
                extra.append(f"H{stops}")
            if duration:
                extra.append(f"D{duration}")
                
            info_text = f"+{delay}"
            if extra:
                info_text += " " + " ".join(extra)
                
            display.text(info_text, 110, y_pos, 200, 3)
            y_pos += 35

    display.set_pen(WHITE)
    display.text("Legende: +Versp. H=Halte D=Dauer", 6, LEGEND_Y, 310, 2)
    display.update()

def fetch_data():
    try:
        # Request kann blockieren, Watchdog vorher füttern
        feed_watchdog() 
        if DEBUG: print("API: fetching...")
        r = urequests.get("https://fahrplan-oynwk.bunny.run/")
        data = r.json()
        r.close()
        feed_watchdog()
        return data.get("departures", [])
    except Exception as e:
        print("API Error:", e)
        return None

# --- Main Logic ---

def main():
    error_count = 0
    last_departures = None
    
    # Erster Connect Versuch mit Anzeige
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    display.text("Booting...", 10, 10, 320, 3)
    display.update()
    
    ensure_wifi()
    sync_time()

    while True:
        feed_watchdog()
        force_refresh = False
        
        # 1. Verbindung prüfen
        if not ensure_wifi():
            error_count += 1
            print(f"Error: WiFi lost ({error_count}/{MAX_RETRIES})")
            if last_departures is None:
                render_departures([], error_msg="WiFi Fehler")
        else:
            # 2. Daten laden
            draw_fetch_icon(True)
            data = fetch_data()
            draw_fetch_icon(False)
            
            if data is None:
                error_count += 1
                print(f"Error: Fetch failed ({error_count}/{MAX_RETRIES})")
                # Bei Fehler alte Daten anzeigen (falls vorhanden) oder Fehler
                if last_departures is None:
                    render_departures([], error_msg="Daten Fehler")
            else:
                # Erfolg!
                error_count = 0
                last_departures = data
                render_departures(data)
        
        # 3. Robustheits-Check
        if error_count >= MAX_RETRIES:
            print("MAX ERRORS REACHED. REBOOTING.")
            display.set_pen(RED)
            display.clear()
            display.text("FATAL ERROR", 10, 50, 320, 4)
            display.text("Rebooting...", 10, 100, 320, 3)
            display.update()
            time.sleep(2)
            reset() # Hard Reset

        # 4. Warte-Schleife (mit UI Interaktion)
        # Wenn wir Fehler haben, warten wir kürzer für Retry (5s), sonst Normal (30s)
        wait_time = 5 if error_count > 0 else REFRESH_INTERVAL
        
        for remaining in range(wait_time, 0, -1):
            feed_watchdog()
            
            # Header Update (Uhrzeit) jede Sekunde
            draw_header(format_time_hhmm(berlin_time_tuple()))
            draw_progress(remaining, wait_time)
            
            # Button Polling (responsive)
            global bright_index
            steps = 10
            for _ in range(steps):
                if not button_b.value(): # Brightness
                    bright_index = (bright_index + 1) % len(BRIGHT_LEVELS)
                    display.set_backlight(BRIGHT_LEVELS[bright_index])
                    time.sleep(0.2)
                
                if not button_a.value() or not button_x.value() or not button_y.value():
                    force_refresh = True
                    break
                
                time.sleep(1.0 / steps)
            
            if force_refresh:
                break

if __name__ == "__main__":
    main()