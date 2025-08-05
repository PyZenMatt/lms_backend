/**
 * 🔥 PHASE 4: Service Worker for Progressive Web App Features
 * 
 * Provides:
 * - Offline support
 * - Background sync
 * - Push notifications
 * - Caching strategies
 */

const CACHE_NAME = 'schoolplatform-v1.0.0';
const STATIC_CACHE = 'schoolplatform-static-v1';
const DYNAMIC_CACHE = 'schoolplatform-dynamic-v1';

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/favicon.ico',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
  /\/api\/v1\/dashboard\//,
  /\/api\/v1\/courses\//,
  /\/api\/v1\/teocoin\//,
  /\/api\/v1\/analytics\//
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('📦 Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('✅ Service Worker: Static assets cached');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('❌ Service Worker: Install failed', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('🔄 Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('🗑️ Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('✅ Service Worker: Activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip extension requests
  if (url.protocol === 'chrome-extension:' || url.protocol === 'moz-extension:') {
    return;
  }

  // Handle different types of requests
  if (isStaticAsset(request)) {
    event.respondWith(cacheFirst(request));
  } else if (isAPIRequest(request)) {
    event.respondWith(networkFirst(request));
  } else if (isImageRequest(request)) {
    event.respondWith(cacheFirst(request));
  } else {
    event.respondWith(staleWhileRevalidate(request));
  }
});

// Push notification event
self.addEventListener('push', (event) => {
  console.log('📬 Service Worker: Push notification received');
  
  const options = {
    body: 'You have new updates!',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-96x96.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'view',
        title: 'View',
        icon: '/icons/action-view.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/icons/action-close.png'
      }
    ]
  };

  if (event.data) {
    const data = event.data.json();
    options.body = data.message || options.body;
    options.title = data.title || 'SchoolPlatform';
    options.data = { ...options.data, ...data };
  }

  event.waitUntil(
    self.registration.showNotification('SchoolPlatform', options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('🖱️ Service Worker: Notification clicked');
  
  event.notification.close();

  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/')
    );
  } else if (event.action === 'close') {
    // Just close the notification
    return;
  } else {
    // Default action - open app
    event.waitUntil(
      clients.matchAll({ type: 'window' })
        .then((clientList) => {
          if (clientList.length > 0) {
            return clientList[0].focus();
          }
          return clients.openWindow('/');
        })
    );
  }
});

// Background sync event
self.addEventListener('sync', (event) => {
  console.log('🔄 Service Worker: Background sync triggered');
  
  if (event.tag === 'background-sync') {
    event.waitUntil(
      // Perform background tasks like syncing offline data
      syncOfflineData()
    );
  }
});

// Message event - communicate with main thread
self.addEventListener('message', (event) => {
  console.log('💬 Service Worker: Message received', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME });
  }
});

// Utility functions
function isStaticAsset(request) {
  const url = new URL(request.url);
  return url.pathname.includes('/static/') || 
         url.pathname.includes('/assets/') ||
         url.pathname.endsWith('.js') ||
         url.pathname.endsWith('.css') ||
         url.pathname.endsWith('.ico');
}

function isAPIRequest(request) {
  const url = new URL(request.url);
  return url.pathname.startsWith('/api/') ||
         API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));
}

function isImageRequest(request) {
  return request.destination === 'image' ||
         request.headers.get('accept')?.includes('image');
}

// Caching strategies
async function cacheFirst(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('❌ Cache first strategy failed:', error);
    return new Response('Offline', { status: 503 });
  }
}

async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('🔄 Network failed, trying cache:', error.message);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    return new Response(
      JSON.stringify({
        error: 'Network unavailable',
        message: 'Please check your internet connection'
      }), 
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(DYNAMIC_CACHE);
  const cachedResponse = await cache.match(request);
  
  const fetchPromise = fetch(request)
    .then((networkResponse) => {
      if (networkResponse.ok) {
        cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    })
    .catch(() => cachedResponse);
  
  return cachedResponse || fetchPromise;
}

// Background sync function
async function syncOfflineData() {
  try {
    console.log('🔄 Service Worker: Syncing offline data...');
    
    // Get stored offline actions
    const offlineActions = await getStoredOfflineActions();
    
    // Process each action
    for (const action of offlineActions) {
      try {
        await processOfflineAction(action);
        await removeOfflineAction(action.id);
      } catch (error) {
        console.error('❌ Failed to sync action:', action, error);
      }
    }
    
    console.log('✅ Service Worker: Offline data synced');
  } catch (error) {
    console.error('❌ Service Worker: Background sync failed:', error);
  }
}

async function getStoredOfflineActions() {
  // This would typically read from IndexedDB
  return [];
}

async function processOfflineAction(action) {
  // Process the offline action (API call, etc.)
  console.log('Processing offline action:', action);
}

async function removeOfflineAction(actionId) {
  // Remove processed action from storage
  console.log('Removing offline action:', actionId);
}
