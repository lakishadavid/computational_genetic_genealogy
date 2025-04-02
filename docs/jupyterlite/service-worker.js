// JupyterLite service worker for Computational Genetic Genealogy course
// This enhances the standard JupyterLite service worker with custom caching for genetic data

// Cache version - increment when updating the service worker
const CACHE_VERSION = 'v1';
const CACHE_NAME = `genealogy-cache-${CACHE_VERSION}`;

// Resources to cache on install
const INITIAL_CACHED_RESOURCES = [
  '/index.html',
  '/lab',
  '/notebooks',
  '/datasets/small_sample.json'
];

// Files with predefined responses
const FILE_MAPPINGS = {};

// Dataset sizes
const DATASET_SIZES = {
  'small': 5,  // ~5MB
  'medium': 20, // ~20MB
  'large': 50   // ~50MB
};

// Install event - cache initial resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Caching initial resources');
        return cache.addAll(INITIAL_CACHED_RESOURCES);
      })
      .then(() => {
        return self.skipWaiting();
      })
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', event => {
  // Special handling for dataset requests
  if (event.request.url.includes('/datasets/')) {
    handleDatasetRequest(event);
    return;
  }

  // Default fetch handling
  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(event.request);
      })
      .catch(error => {
        console.error('Fetch error:', error);
        return new Response('Network error', { status: 503 });
      })
  );
});

// Handle dataset requests - apply size limitations and caching
function handleDatasetRequest(event) {
  const url = new URL(event.request.url);
  const datasetPath = url.pathname;
  
  // Check user preferences for dataset sizes
  const userPreferredSize = getUserPreferredSize();
  
  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        if (cachedResponse) {
          return cachedResponse;
        }
        
        // If not in cache, fetch from network
        return fetch(event.request.url)
          .then(response => {
            // Clone the response for caching
            const responseToCache = response.clone();
            
            // Check response size before caching
            return response.blob()
              .then(blob => {
                const sizeMB = blob.size / (1024 * 1024);
                
                // Only cache if size is within user preference
                if (sizeMB <= DATASET_SIZES[userPreferredSize]) {
                  caches.open(CACHE_NAME)
                    .then(cache => {
                      cache.put(event.request, responseToCache);
                    });
                }
                
                return response;
              });
          });
      })
  );
}

// Get user's preferred dataset size from client storage
function getUserPreferredSize() {
  // Default to small if not specified
  return 'small';
}

// Message handling for cache control
self.addEventListener('message', event => {
  if (event.data && event.data.action) {
    switch (event.data.action) {
      case 'clearCache':
        clearCache();
        break;
      case 'updatePreferredSize':
        // Would implement updating user size preference
        break;
    }
  }
});

// Clear the cache
function clearCache() {
  return caches.delete(CACHE_NAME)
    .then(() => {
      return caches.open(CACHE_NAME);
    })
    .then(cache => {
      return cache.addAll(INITIAL_CACHED_RESOURCES);
    });
}