import * as BunnySDK from "https://esm.sh/@bunny.net/edgescript-sdk@0.11.2";

BunnySDK.net.http.serve(async (request: Request): Promise<Response> => {
  const url = new URL(request.url);
  
  // Logging
  const headers = Object.fromEntries(request.headers.entries());
  console.log(`[DEBUG]: Headers: ${JSON.stringify(headers)}`);

  const clientIp = request.headers.get("bunny-client-ip") || request.headers.get("x-forwarded-for") || "unknown";
  const requestId = request.headers.get("cdn-request-id") || request.headers.get("x-request-id") || "unknown";
  const logData = {
      timestamp: new Date().toISOString(),
      requestId: requestId,
      ip: clientIp,
      method: request.method,
      path: url.pathname,
      params: Object.fromEntries(url.searchParams)
  };
  console.log(`[INFO]: ${JSON.stringify(logData)}`);

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
         return new Response(JSON.stringify({ error: "Invalid date format. Use ISO 8601" }), { 
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!swbResponse.ok) {
       console.log(`[ERROR]: Upstream API Error: ${swbResponse.status} for Request ${requestId}`);
       return new Response(JSON.stringify({ error: `Upstream API Error: ${swbResponse.status}` }), {
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
                 results.push({
                     departure: new Date(journey.departure * 1000).toISOString(),
                     arrival: new Date(journey.arrival * 1000).toISOString(),
                     duration: Math.round((journey.arrival - journey.departure) / 60) + ' min',
                     delay: journey.delay || 0, 
                     line: lineName,
                     transfers: journey.changes,
                     destination: "Königstr. (Bonn)"
                 });
            }
            if (results.length >= limit) break;
        }
    }

    console.log(`[INFO]: Success: Found ${results.length} departures for Request ${requestId}`);
    return new Response(JSON.stringify({
        meta: { requested_date_utc: searchDate.toISOString(), limit: limit },
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
});