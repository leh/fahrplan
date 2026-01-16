#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if ! command -v mpremote >/dev/null 2>&1; then
  echo "mpremote nicht gefunden. Installiere es z.B. mit: pipx install mpremote"
  exit 1
fi

SECRETS_FILE=""
if [[ -f "${SCRIPT_DIR}/wifi_secrets.py" ]]; then
  SECRETS_FILE="${SCRIPT_DIR}/wifi_secrets.py"
elif [[ -f "${PROJECT_DIR}/wifi_secrets.py" ]]; then
  SECRETS_FILE="${PROJECT_DIR}/wifi_secrets.py"
else
  echo "Keine wifi_secrets.py gefunden."
  echo "Erstelle ${SCRIPT_DIR}/wifi_secrets.py anhand von ${SCRIPT_DIR}/wifi_secrets.py.example"
  exit 1
fi

echo "Pico per USB anschliessen und sicherstellen, dass er erkannt wird."
echo "Kopiere Dateien mit mpremote ..."

mpremote cp "${SECRETS_FILE}" :wifi_secrets.py
mpremote cp "${SCRIPT_DIR}/main.py" :main.py
mpremote reset

echo "Fertig. Falls nichts passiert, pruefe USB-Verbindung oder BOOTSEL-Modus."
