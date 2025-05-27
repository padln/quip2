// cache.js
const CACHE_KEY = "quipCache";
const MAX_ENTRIES = 500;
const EXPIRY_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

// Load the entire cache
export async function loadCache() {
  return new Promise((resolve) => {
    chrome.storage.local.get([CACHE_KEY], (result) => {
      resolve(result[CACHE_KEY] || {});
    });
  });
}

// Save the cache
export async function saveCache(cache) {
  return new Promise((resolve) => {
    chrome.storage.local.set({ [CACHE_KEY]: cache }, resolve);
  });
}

// Get a cached result (by URL or Blake3 key)
export async function getFromCache(key) {
  const cache = await loadCache();
  const entry = cache[key];
  if (!entry) return null;

  const isExpired = Date.now() - new Date(entry.timestamp).getTime() > EXPIRY_MS;
  return isExpired ? null : entry;
}

// Add or update an entry
export async function addToCache(key, resultData) {
  const cache = await loadCache();

  // Remove oldest if over limit
  const keys = Object.keys(cache);
  if (keys.length >= MAX_ENTRIES) {
    keys.sort((a, b) => new Date(cache[a].timestamp) - new Date(cache[b].timestamp));
    delete cache[keys[0]];
  }

  cache[key] = {
    ...resultData,
    timestamp: new Date().toISOString(),
  };

  await saveCache(cache);
}

export async function pruneExpiredEntries() {
  const cache = await loadCache();
  const now = Date.now();
  const pruned = {};

  const entries = Object.entries(cache).filter(([_, entry]) => {
    const age = now - new Date(entry.timestamp).getTime();
    return age <= EXPIRY_MS;
  });

  // Sort by most recent
  entries.sort(([, a], [, b]) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  // Trim to MAX_ENTRIES
  for (let i = 0; i < Math.min(entries.length, MAX_ENTRIES); i++) {
    const [key, value] = entries[i];
    pruned[key] = value;
  }

  await saveCache(pruned);
}