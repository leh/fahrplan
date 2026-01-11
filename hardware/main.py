import network
import time
import urequests
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P4
from wifi_secrets import WIFI_SSID, WIFI_PASSWORD

# Display Setup (320x240)
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_P4)
display.set_backlight(0.8)

# Farben definieren (RGB)
WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)
BLUE = display.create_pen(0, 0, 150)
RED = display.create_pen(200, 0, 0)
GREEN = display.create_pen(0, 200, 0)

def connect_wifi():
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
        display.set_pen(RED)
        display.text("WiFi Failed!", 10, 40, 240, 3)
        display.update()
        return False
    return True

def draw_header():
    display.set_pen(BLUE)
    display.rectangle(0, 0, 320, 40)
    display.set_pen(WHITE)
    display.text("Auerberger Mitte", 10, 8, 300, 3)

def fetch_data():
    try:
        r = urequests.get("https://fahrplan-oynwk.bunny.run/")
        data = r.json()
        r.close()
        return data.get("departures", [])
    except Exception as e:
        print("Fetch Error:", e)
        return None

def render_departures(departures):
    display.set_pen(BLACK)
    display.clear()
    draw_header()
    
    if not departures:
        display.set_pen(WHITE)
        display.text("No data available", 10, 60, 300, 3)
    else:
        y_pos = 60
        for dep in departures[:5]: # Max 5 Einträge
            # Zeit extrahieren (HH:MM)
            # ISO String: 2026-01-11T12:09:20.000Z -> 12:09
            time_str = dep["departure"].split("T")[1][:5]
            delay = dep["delay"]
            
            # Zeile zeichnen
            display.set_pen(WHITE)
            display.text(f"{time_str}", 10, y_pos, 300, 4)
            
            # Delay Anzeige
            if delay > 0:
                display.set_pen(RED)
                display.text(f"+{delay}", 110, y_pos, 300, 3)
            else:
                display.set_pen(GREEN)
                display.text("ok", 110, y_pos, 300, 2)
            
            display.set_pen(WHITE)
            display.text("-> Koenigstr.", 170, y_pos + 5, 300, 2)
            
            y_pos += 35
            
    display.update()

# Hauptschleife
if connect_wifi():
    while True:
        data = fetch_data()
        if data is not None:
            render_departures(data)
        time.sleep(60)
