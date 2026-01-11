addEventListener('fetch', event => {
  event.respondWith(new Response('Minimal response test', { status: 200 }));
});
