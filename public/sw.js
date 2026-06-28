const CACHE_NAME = "wikiwonder-v2";
const STATIC_CACHE = "wikiwonder-static-v2";
const OFFLINE_URL = "/offline";

const PRECACHE_URLS = [
  "/",
  "/offline",
  "/search",
  "/bookmarks",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== CACHE_NAME && k !== STATIC_CACHE)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and API requests
  if (request.method !== "GET" || url.pathname.startsWith("/api/")) return;

  // Wiki pages - network first, fallback to cache
  if (url.pathname.startsWith("/wiki/")) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          return response;
        })
        .catch(() =>
          caches.match(request).then((cached) => cached ?? caches.match(OFFLINE_URL))
        )
    );
    return;
  }

  // Static assets - cache first
  if (
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.startsWith("/uploads/") ||
    url.pathname.match(/\.(js|css|png|jpg|gif|svg|ico|woff2?)$/)
  ) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          caches.open(STATIC_CACHE).then((cache) => cache.put(request, response.clone()));
          return response;
        });
      })
    );
    return;
  }

  // Everything else - network first with offline fallback
  event.respondWith(
    fetch(request)
      .catch(() =>
        caches.match(request).then((cached) => cached ?? caches.match(OFFLINE_URL))
      )
  );
});

// Receive bookmark URLs to pre-cache
self.addEventListener("message", (event) => {
  if (event.data?.type === "SYNC_BOOKMARKS") {
    const urls = event.data.urls;
    if (!Array.isArray(urls)) return;
    caches.open(CACHE_NAME).then((cache) => {
      for (const url of urls) {
        fetch(url).then((res) => {
          if (res.ok) cache.put(url, res);
        }).catch(() => {});
      }
    });
  }
});
