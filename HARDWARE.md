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
# mit pipx (empfohlen, wenn kein pip vorhanden)
pipx install mpremote

# alternativ mit pip (falls verfügbar)
# pip install mpremote

# Dateien kopieren
mpremote cp wifi_secrets.py :
mpremote cp hardware/main.py : main.py

# Reset ausführen
mpremote reset
```

Tipp: Alternativ gibt es ein fertiges Script, das die Dateien kopiert und den Pico resetet:
```bash
./hardware/upload_mpremote.sh
```

### 3. WLAN-Konfiguration
Erstelle eine Datei `wifi_secrets.py` auf dem Pico (oder lokal und per mpremote kopieren):
```python
WIFI_SSID = "Dein_WLAN_Name"
WIFI_PASSWORD = "Dein_Passwort"
```

### 3. Anzeige-Logik (`hardware/main.py`)
Das Skript führt folgende Schritte alle 30 Sekunden aus:
1. **Wi-Fi Connect:** Verbindung zum lokalen Netzwerk herstellen.
2. **Data Fetch:** `GET` Request an die Bunny Edge API mittels `urequests` (mit Retry).
3. **Parsing:** Extraktion der nächsten 4 Abfahrten aus dem JSON-Response.
4. **Rendering:**
   - Hintergrundfarbe setzen.
   - Header mit Haltestellen und aktueller Uhrzeit (Bonn/Europe/Berlin via NTP).
   - Abfahrtszeit und Verspätung (+Versp.), Halte (H) und Dauer (D) anzeigen.
   - Fortschrittsbalken unten und kleines Fetch-Symbol bei Aktualisierung.
5. **Sleep:** 30 Sekunden warten (Deep Sleep optional zur Stromersparnis).

## Beispiel-Struktur der Anzeige (320x240)
- **Header:** "Auerberger Mitte -> Koenigstr." + Uhrzeit (Blauer Balken)
- **Zeile 1:** 20:09  +2 H1 D18m
- **Zeile 2:** 20:26  +0 H0 D18m
- **Zeile 3:** 20:39  +0 H1 D20m
- **Zeile 4:** 20:56  +0 H0 D18m
- **Legende:** "+Versp. H=Halte D=Dauer"
- **Footer:** Fortschrittsbalken + Fetch-Symbol

## Button-Belegung (Optional)
- **Button A/B/X/Y:** Manueller Refresh (sofortiges Nachladen)

## Debugging (macOS)

### 1) Seriell mit mpremote mitlesen
1. Pico per USB anschließen.
2. Serielles Device finden:
```bash
ls /dev/tty.*
```
3. REPL starten (Beispiel):
```bash
mpremote connect /dev/tty.usbmodemXXXX repl
```
4. Logs ansehen; mit `Ctrl+D` resetten.

### 2) Debug-Logs im Code
In `hardware/main.py` gibt es den Schalter:
```python
DEBUG = True
```
Bei aktiviertem Debug werden u.a. geloggt:
- WLAN-Connect + IP
- NTP-Sync ok/fehlerhaft
- API-Fetch ok/fehlerhaft + Retry
- manueller Refresh
