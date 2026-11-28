var CACHE_NAME = "cruciword-static-v6";
var OFFLINE_URL = "/";

var PRECACHE_URLS = [
  OFFLINE_URL,
  "/static/css/tailwind.css",
  "/static/css/themes.css",
  "/static/js/storage.js",
  "/static/js/api.js",
  "/static/js/theme-init.js",
  "/static/js/theme.js",
  "/static/js/audio.js",
  "/static/js/grid-engine.js",
  "/static/js/board.js",
  "/static/js/navigation.js",
  "/static/js/keyboard.js",
  "/static/js/app.js",
  "/static/manifest.json",
  "/static/icons/icon.svg",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/icons/icon-maskable-512.png",
  "/static/fonts/balsamiq-sans-400-latin.woff2",
  "/static/fonts/balsamiq-sans-400-latin-ext.woff2",
  "/static/fonts/balsamiq-sans-700-latin.woff2",
  "/static/fonts/balsamiq-sans-700-latin-ext.woff2"
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then(function (cache) {
        return cache.addAll(PRECACHE_URLS);
      })
      .then(function () {
        return self.skipWaiting();
      })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches
      .keys()
      .then(function (keys) {
        return Promise.all(
          keys
            .filter(function (key) {
              return key !== CACHE_NAME;
            })
            .map(function (key) {
              return caches.delete(key);
            })
        );
      })
      .then(function () {
        return self.clients.claim();
      })
  );
});

function cacheFirst(request) {
  return caches.match(request).then(function (cached) {
    if (cached) {
      return cached;
    }
    return fetch(request).then(function (response) {
      if (response.ok && response.type === "basic") {
        var copy = response.clone();
        caches.open(CACHE_NAME).then(function (cache) {
          cache.put(request, copy);
        });
      }
      return response;
    });
  });
}

function navigationFallback(request) {
  return fetch(request)
    .then(function (response) {
      if (response.ok) {
        var copy = response.clone();
        caches.open(CACHE_NAME).then(function (cache) {
          cache.put(OFFLINE_URL, copy);
        });
      }
      return response;
    })
    .catch(function () {
      return caches.match(OFFLINE_URL);
    });
}

self.addEventListener("fetch", function (event) {
  var request = event.request;
  if (request.method !== "GET") {
    return;
  }

  var url = new URL(request.url);
  if (url.origin !== self.location.origin || url.pathname.indexOf("/api/") === 0) {
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(navigationFallback(request));
    return;
  }

  event.respondWith(cacheFirst(request));
});
