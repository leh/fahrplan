addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  return new Response(JSON.stringify({ message: "Hello from Bunny Edge Scripting!" }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  });
}