const CACHE_NAME = 'shiksha-v1';

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim());
});

self.addEventListener('fetch', (event) => {
    // Agar request POST hai (jaise AI Search, Login, Form Submit), 
    // toh Service worker interfere nahi karega.
    if (event.request.method !== 'GET') {
        return; 
    }

    event.respondWith(
        fetch(event.request).catch(() => {
            return new Response('Offline mode');
        })
    );
});