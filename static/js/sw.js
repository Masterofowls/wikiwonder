/* Service Worker — offline caching + bookmark prefetch + media (v5) */
const CACHE_NAME = 'wikiwonder-v6';
const BOOKMARK_CACHE = 'wikiwonder-bookmarks-v1';
const MEDIA_CACHE = 'wikiwonder-media-v1';
const OFFLINE_URL = '/offline/';
const PRECACHE_URLS = [
  '/',
  OFFLINE_URL,
  '/robots.txt',
  '/static/css/wiki.css',
  '/static/css/media-blocks.css',
  '/static/js/app.js',
  '/static/js/mobile.js',
  '/static/js/share.js',
  '/static/js/media-blocks.js',
  '/static/icons/icon-192.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== CACHE_NAME && k !== BOOKMARK_CACHE && k !== MEDIA_CACHE)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('message', (event) => {
  if (event.data?.type !== 'SYNC_BOOKMARKS') return;
  const urls = Array.isArray(event.data.urls) ? event.data.urls : [];
  event.waitUntil(
    caches.open(BOOKMARK_CACHE).then(async (cache) => {
      const keys = await cache.keys();
      await Promise.all(keys.map((req) => cache.delete(req)));
      await Promise.all(
        urls.map((raw) =>
          fetch(raw)
            .then((response) => {
              if (response.ok) return cache.put(raw, response);
            })
            .catch(() => null)
        )
      );
    })
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/admin/')) return;

  if (url.pathname.startsWith('/wiki/') || url.pathname === '/') {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        const network = fetch(event.request)
          .then((response) => {
            if (response.ok) {
              const clone = response.clone();
              caches.open(CACHE_NAME).then((c) => c.put(event.request, clone));
            }
            return response;
          })
          .catch(() => null);
        return (
          cached ||
          network.then((r) => r || caches.match(OFFLINE_URL))
        );
      })
    );
    return;
  }

  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
    return;
  }

  if (url.pathname.startsWith('/media/')) {
    event.respondWith(
      caches.open(MEDIA_CACHE).then((cache) =>
        cache.match(event.request).then((cached) => {
          const network = fetch(event.request)
            .then((response) => {
              if (response.ok) cache.put(event.request, response.clone());
              return response;
            })
            .catch(() => null);
          return cached || network;
        })
      )
    );
  }
});
