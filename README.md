# Fahrplan App

Meine Familie nutzt die Straßenbahn um morgens zur Schule und zur Arbeit zu kommen.

Beispiel-Requests

curl 'https://swb-mobil.de/api/v1/journeys/ass?locale=de-de' \
  -X POST \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:146.0) Gecko/20100101 Firefox/146.0' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: de,en-US;q=0.7,en;q=0.3' \
  -H 'Accept-Encoding: gzip, deflate, br, zstd' \
  -H 'Content-Type: application/json' \
  -H 'Referer: https://www.swb-mobil.de/' \
  -H 'Cache-Control: no-cache' \
  -H 'X-App-Version: 2.5.2' \
  -H 'Origin: https://www.swb-mobil.de' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-site' \
  -H 'Connection: keep-alive' \
  -H 'Priority: u=0' \
  -H 'TE: trailers' \
  --data-raw $'{"origin":{"@ID":"7201","ASSID":"8507","GKZ":"5314000","TariffZones":["2600"],"centerx":"7.076832","centery":"50.755212","class":"Stop","f_type":"stop","gloablId":"de:05314:64512","id":"Stop_7201","jpapi":true,"title":"Auerberger Mitte (Bonn)","vrsnr":"64512"},"destination":{"@ID":"1073","ASSID":"1130","GKZ":"5314000","TariffZones":["2600"],"centerx":"7.101765","centery":"50.728288","class":"Stop","f_type":"stop","gloablId":"de:05314:61319","id":"Stop_1073","jpapi":true,"title":"K\xf6nigstr. (Bonn)","vrsnr":"61319"},"options":{"products":["LightRail"]},"date":"2026-01-12T05:55:00.000Z","departure":"1"}'


curl 'https://swb-mobil.de/api/v1/journeys/ass?locale=de-de' \
  -X POST \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:146.0) Gecko/20100101 Firefox/146.0' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: de,en-US;q=0.7,en;q=0.3' \
  -H 'Accept-Encoding: gzip, deflate, br, zstd' \
  -H 'Content-Type: application/json' \
  -H 'Referer: https://www.swb-mobil.de/' \
  -H 'Cache-Control: no-cache' \
  -H 'X-App-Version: 2.5.2' \
  -H 'Origin: https://www.swb-mobil.de' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-site' \
  -H 'Connection: keep-alive' \
  -H 'Priority: u=0' \
  -H 'TE: trailers' \
  --data-raw $'{"origin":{"@ID":"7201","ASSID":"8507","GKZ":"5314000","TariffZones":["2600"],"centerx":"7.076832","centery":"50.755212","class":"Stop","f_type":"stop","gloablId":"de:05314:64512","id":"Stop_7201","jpapi":true,"title":"Auerberger Mitte (Bonn)","vrsnr":"64512"},"destination":{"@ID":"1073","ASSID":"1130","GKZ":"5314000","TariffZones":["2600"],"centerx":"7.101765","centery":"50.728288","class":"Stop","f_type":"stop","gloablId":"de:05314:61319","id":"Stop_1073","jpapi":true,"title":"K\xf6nigstr. (Bonn)","vrsnr":"61319"},"options":{"products":["LightRail"]},"date":"2026-01-11T10:55:00.000Z","departure":"1"}'
