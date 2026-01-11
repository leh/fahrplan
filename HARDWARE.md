# Fahrplan Mini-Display (Raspberry Pi Pico 2 W)

Diese Dokumentation beschreibt, wie die Abfahrtsdaten auf einem Raspberry Pi Pico 2 W mit dem Pimoroni Pico Display Pack 2.8" (320x240) angezeigt werden.

## Hardware-Komponenten
- **Controller:** Raspberry Pi Pico 2 W (RP2350 mit Wi-Fi)
- **Display:** [Pimoroni Pico Display Pack 2.8"](https://shop.pimoroni.com/products/pico-display-pack-2-8)
- **Stromversorgung:** Micro-USB Kabel

## Software-Stack
- **Firmware:** [Pimoroni MicroPython (RP2350 Build)](https://github.com/pimoroni/pimoroni-pico/releases)
- **Sprache:** MicroPython
- **API:** Bunny Edge Script (`https://fahrplan-oynwk.bunny.run/`)

## Setup-Plan

### 1. Firmware Installation
- Pimoroni MicroPython `.uf2` für RP2350 herunterladen (siehe [Pimoroni Releases](https://github.com/pimoroni/pimoroni-pico/releases)).
- Pico 2 W mit gedrückter `BOOTSEL`-Taste anschließen.
- Datei auf das erscheinende Laufwerk kopieren.

### 2. Dateitransfer (Thonny oder mpremote)

#### Option A: Thonny (Einsteigerfreundlich)
1. [Thonny IDE](https://thonny.org/) installieren und starten.
2. Unten rechts "MicroPython (Raspberry Pi Pico)" als Interpreter auswählen.
3. Die Dateien `wifi_secrets.py` (lokal erstellen) und `main.py` öffnen.
4. Über `File -> Save as... -> Raspberry Pi Pico` auf dem Gerät speichern.

#### Option B: mpremote (CLI für Profis)
```bash
# mpremote installieren
pip install mpremote

# Dateien kopieren
mpremote cp wifi_secrets.py :
mpremote cp hardware/main.py : main.py

# Reset ausführen
mpremote reset
```

### 3. WLAN-Konfiguration
Erstelle eine Datei `wifi_secrets.py` auf dem Pico:
```python
WIFI_SSID = "Dein_WLAN_Name"
WIFI_PASSWORD = "Dein_Passwort"
```

### 3. Anzeige-Logik (`hardware/main.py`)
Das Skript führt folgende Schritte alle 60 Sekunden aus:
1. **Wi-Fi Connect:** Verbindung zum lokalen Netzwerk herstellen.
2. **Data Fetch:** `GET` Request an die Bunny Edge API mittels `urequests`.
3. **Parsing:** Extraktion der nächsten 3-4 Abfahrten aus dem JSON-Response.
4. **Rendering:**
   - Hintergrundfarbe setzen.
   - Linie ("61") und Ziel ("Königstr.") zeichnen.
   - Abfahrtszeit und Verspätung (delay) farblich hervorheben (z.B. Rot bei delay > 0).
5. **Sleep:** 60 Sekunden warten (Deep Sleep optional zur Stromersparnis).

## Beispiel-Struktur der Anzeige (320x240)
- **Header:** "Abfahrten Auerberger Mitte" (Blauer Balken)
- **Zeile 1:** 12:09 +2min -> Königstr.
- **Zeile 2:** 12:26 +0min -> Königstr.
- **Zeile 3:** 12:39 +0min -> Königstr.
- **Footer:** "Letztes Update: 12:08"

## Button-Belegung (Optional)
- **Button A:** Manueller Refresh
- **Button B:** Display-Helligkeit dimmen
- **Button X/Y:** Zwischen verschiedenen Haltestellen umschalten (falls API erweitert wird)
