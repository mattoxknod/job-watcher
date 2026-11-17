/* Service worker: what makes the site open when the computer is offline.
 *
 * Two strategies, because the pages and the data want opposite things:
 *
 *   - The app shell (pages, stylesheet, scripts, icons) is cached on install
 *     and served cache-first, so the site opens instantly and without a
 *     network. A fresh copy is fetched in the background to pick up changes.
 *
 *   - The two data files are network-first. Online, the pages always show what
 *     the pipeline committed most recently; offline, the last copy the cache
 *     saw is served instead, which is the "last data it loaded" the site is
 *     meant to fall back to.
 */

const VERSION = "v1";
const SHELL_CACHE = `job-watcher-shell-${VERSION}`;
const DATA_CACHE = `job-watcher-data-${VERSION}`;

const SHELL = [
  "./",
  "./index.html",
  "./browse.html",
  "./market.html",
  "./assets/style.css",
  "./assets/data.js",
  "./assets/charts.js",
  "./assets/icon.svg",
  "./assets/icon-192.png",
  "./assets/icon-512.png",
  "./manifest.webmanifest",
];

const isData = (url) =>
  url.pathname.endsWith("/data/history.csv") ||
  url.pathname.endsWith("/data/status.json");

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(SHELL_CACHE);
      // addAll fails the whole install if any one file 404s, so each file is
      // added on its own and a missing one does not block installation.
      await Promise.all(
        SHELL.map((path) => cache.add(path).catch(() => undefined)),
      );
      await self.skipWaiting();
    })(),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keep = new Set([SHELL_CACHE, DATA_CACHE]);
      const names = await caches.keys();
      await Promise.all(
        names.filter((name) => !keep.has(name)).map((name) => caches.delete(name)),
      );
      await self.clients.claim();
    })(),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (isData(url)) {
    event.respondWith(networkFirst(request));
    return;
  }

  event.respondWith(cacheFirst(request));
});

/** Fresh data when the network is there, the last copy when it is not. */
async function networkFirst(request) {
  const cache = await caches.open(DATA_CACHE);
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await cache.match(request, { ignoreSearch: true });
    if (cached) return cached;
    throw error;
  }
}

/** The shell, served from cache and refreshed quietly behind the page. */
async function cacheFirst(request) {
  const cache = await caches.open(SHELL_CACHE);
  const cached = await cache.match(request, { ignoreSearch: true });

  const update = fetch(request)
    .then((response) => {
      if (response && response.ok) cache.put(request, response.clone());
      return response;
    })
    .catch(() => undefined);

  if (cached) return cached;

  const fresh = await update;
  if (fresh) return fresh;

  // An offline navigation to a page that was never cached still gets the
  // Today page rather than the browser's error screen.
  if (request.mode === "navigate") {
    const fallback = await cache.match("./index.html");
    if (fallback) return fallback;
  }
  return Response.error();
}
