#!/usr/bin/env bash
set -euo pipefail

DEVICE=""
for candidate in /dev/tty.usbmodem* /dev/tty.usbserial*; do
  if [[ -e "$candidate" ]]; then
    DEVICE="$candidate"
    break
  fi
done

if [[ -z "$DEVICE" ]]; then
  echo "Kein USB-Serial-Device gefunden."
  echo "Liste vorhandene Devices mit: ls /dev/tty.*"
  exit 1
fi

echo "Verbinde mit: $DEVICE"
echo "Hinweis: Beenden mit Ctrl+]. Reset im REPL mit Ctrl+D."
mpremote connect "$DEVICE" repl
