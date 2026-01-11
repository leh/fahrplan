addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  
  // CORS headers
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  // Handle preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // 1. Parse Parameters
    const dateParam = url.searchParams.get('date');
    const limitParam = url.searchParams.get('limit');
    
    // Date Logic:
    // If dateParam is provided, parse it.
    // If not provided, use new Date() which is "now" (UTC on server).
    // Note: new Date('2026-01-01T12:00') without Z might be interpreted variously.
    // We assume ISO 8601. If the user omits Z, JS Date usually treats it as UTC in standard environments (like Deno/V8),
    // but explicit Z is safer.
    
    let searchDate;
    if (dateParam) {
      searchDate = new Date(dateParam);
      if (isNaN(searchDate.getTime())) {
         return new Response(JSON.stringify({ error: "Invalid date format. Use ISO 8601 (e.g. 2026-01-11T12:00:00Z)" }), { 
             status: 400, 
             headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
         });
      }
    } else {
      searchDate = new Date();
    }

    const limit = limitParam ? parseInt(limitParam, 10) : 6;

    // 2. Construct Upstream Payload
    // Fixed IDs for Auerberger Mitte -> Königstr.
    const payload = {
      "origin": {
        "@ID": "7201",
        "ASSID": "8507",
        "GKZ": "5314000",
        "TariffZones": ["2600"],
        "centerx": "7.076832",
        "centery": "50.755212",
        "class": "Stop",
        "f_type": "stop",
        "gloablId": "de:05314:64512",
        "id": "Stop_7201",
        "jpapi": true,
        "title": "Auerberger Mitte (Bonn)",
        "vrsnr": "64512"
      },
      "destination": {
        "@ID": "1073",
        "ASSID": "1130",
        "GKZ": "5314000",
        "TariffZones": ["2600"],
        "centerx": "7.101765",
        "centery": "50.728288",
        "class": "Stop",
        "f_type": "stop",
        "gloablId": "de:05314:61319",
        "id": "Stop_1073",
        "jpapi": true,
        "title": "Königstr. (Bonn)",
        "vrsnr": "61319"
      },
      "options": {
        "products": ["LightRail"]
      },
      "date": searchDate.toISOString(),
      "departure": "1"
    };

    // 3. Fetch from SWB API
    // We use the same headers as the working curl request to behave like a browser
    const swbResponse = await fetch('https://swb-mobil.de/api/v1/journeys/ass?locale=de-de', {
      method: 'POST',
      headers: {
        'Host': 'swb-mobil.de',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:146.0) Gecko/20100101 Firefox/146.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json',
        'Referer': 'https://www.swb-mobil.de/',
        'Origin': 'https://www.swb-mobil.de',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
      },
      body: JSON.stringify(payload)
    });

    if (!swbResponse.ok) {
       // Pass through upstream errors or handle them
       const text = await swbResponse.text();
       return new Response(JSON.stringify({ error: `Upstream API Error: ${swbResponse.status}`, details: text }), {
           status: 502, // Bad Gateway
           headers: { ...corsHeaders, 'Content-Type': 'application/json' }
       });
    }

    const data = await swbResponse.json();
    
    // 4. Process & Filter Data
    const results = [];
    if (data.data) {
        for (const journey of data.data) {
            // Filter logic: Must start with Line 61
            const firstLeg = journey.legs && journey.legs[0];
            const lineName = firstLeg && firstLeg.product ? firstLeg.product.name : "";
            
            // "61" is the expected name for the tram
            if (lineName === '61') {
                 // API returns timestamps in seconds (Unix Epoch)
                 // These are absolute and UTC-based.
                 const departureTimestamp = journey.departure; 
                 const arrivalTimestamp = journey.arrival; 
                 const delay = journey.delay || 0; // usually minutes or 0
                 
                 const depDate = new Date(departureTimestamp * 1000);
                 const arrDate = new Date(arrivalTimestamp * 1000);
                 
                 results.push({
                     departure: depDate.toISOString(), // Output as ISO UTC string
                     arrival: arrDate.toISOString(),
                     duration: Math.round((arrivalTimestamp - departureTimestamp) / 60) + ' min',
                     delay: delay, 
                     line: lineName,
                     transfers: journey.changes,
                     destination: "Königstr. (Bonn)"
                 });
            }
            
            if (results.length >= limit) break;
        }
    }

    // 5. Response
    // Cache for 60 seconds to allow near-realtime updates but prevent abuse
    return new Response(JSON.stringify({
        meta: {
            requested_date_utc: searchDate.toISOString(),
            limit: limit,
            source: "SWB API proxy"
        },
        departures: results
    }, null, 2), {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=60' 
      }
    });

  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}