addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  if (request.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const dateParam = url.searchParams.get('date');
    const limitParam = url.searchParams.get('limit');
    
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

    const swbResponse = await fetch('https://swb-mobil.de/api/v1/journeys/ass?locale=de-de', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'BunnyEdgeScript/1.0',
        'Accept': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!swbResponse.ok) {
       const text = await swbResponse.text();
       return new Response(JSON.stringify({ error: `Upstream API Error: ${swbResponse.status}`, details: text.substring(0, 200) }), {
           status: 502,
           headers: { ...corsHeaders, 'Content-Type': 'application/json' }
       });
    }

    const data = await swbResponse.json();
    
    const results = [];
    if (data.data) {
        for (const journey of data.data) {
            const firstLeg = journey.legs && journey.legs[0];
            const lineName = firstLeg && firstLeg.product ? firstLeg.product.name : "";
            
            if (lineName === '61') {
                 const departureTimestamp = journey.departure; 
                 const arrivalTimestamp = journey.arrival; 
                 const delay = journey.delay || 0;
                 
                 const depDate = new Date(departureTimestamp * 1000);
                 const arrDate = new Date(arrivalTimestamp * 1000);
                 
                 results.push({
                     departure: depDate.toISOString(),
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
