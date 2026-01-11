# SWB Line 61 Edge Function

Dieser Service stellt eine vereinfachte JSON-API bereit, um die nächsten Abfahrten der Straßenbahnlinie 61 von **Auerberger Mitte** nach **Königstr. (Bonn)** abzurufen.

Er dient als Proxy zur SWB API und filtert spezifisch nach dieser Verbindung.

## Endpunkt

`GET /` (oder URL des Edge Scripts)

## Parameter

| Parameter | Typ     | Beschreibung | Default |
|-----------|---------|--------------|---------|
| `date`    | String  | Startdatum für die Suche im ISO 8601 Format. | Jetzt (`new Date()`) |
| `limit`   | Integer | Maximale Anzahl der zurückgegebenen Verbindungen. | 6 |

### Beispiele

**Nächste 6 Abfahrten ab jetzt:**
```
GET /
```

**Abfahrten ab einem bestimmten Zeitpunkt (z.B. 12. Januar 2026, 08:00 UTC):**
```
GET /?date=2026-01-12T08:00:00Z
```

**Nur die nächsten 2 Abfahrten:**
```
GET /?limit=2
```

## Antwortformat

Die API antwortet mit `application/json`. Alle Zeitangaben sind **UTC** (ISO 8601).

```json
{
  "meta": {
    "requested_date_utc": "2026-01-11T12:00:00.000Z",
    "limit": 6,
    "source": "SWB API proxy"
  },
  "departures": [
    {
      "departure": "2026-01-11T12:09:20.000Z",
      "arrival": "2026-01-11T12:29:20.000Z",
      "duration": "20 min",
      "delay": 0,
      "line": "61",
      "transfers": 1,
      "destination": "Königstr. (Bonn)"
    },
    ...
  ]
}
```

## Technische Details

### Zeitzonen
- **Input:** Der Parameter `date` wird als UTC interpretiert, wenn `Z` angegeben ist (empfohlen). Ohne Zeitzone wird es vom Server (Bunny Edge) als UTC behandelt.
- **Verarbeitung:** Die SWB API arbeitet intern mit Unix-Timestamps (Sekunden seit 1970 UTC).
- **Output:** Alle Zeitstempel (`departure`, `arrival`) werden als ISO-String in UTC (`...Z`) ausgegeben.
- **Client-Side:** Der Client (Frontend/App) ist dafür verantwortlich, diese UTC-Zeiten in die lokale Zeitzone des Nutzers (z.B. Europe/Berlin) umzurechnen.

### Verspätungen
- Das Feld `delay` gibt die Verspätung in Minuten an (falls von der SWB API bereitgestellt).
- Die `departure` Zeit beinhaltet in der Regel bereits die Verspätung (Prognose), aber das `delay` Feld weist explizit darauf hin.

### Caching
- Antworten werden mit `Cache-Control: public, max-age=60` ausgeliefert.
- Clients sollten die Daten maximal 60 Sekunden cachen, um Echtzeit-Informationen zu gewährleisten.

## Wartung
Die Logik befindet sich in `script.ts`.
Die IDs für Start- und Zielhaltestelle sind im Code hartkodiert (`Stop_7201` und `Stop_1073`). Sollten sich diese ändern, müssen sie im `payload` Objekt aktualisiert werden.
