/* eslint-disable no-restricted-globals */

const CACHE_NAME = 'krish-ai-v1';
const RUNTIME = 'runtime';

// Resources to pre-cache
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/favicon.ico',
  '/logo192.png',
  '/logo512.png',
  '/offline.html'
];

// Install event - Pre-cache resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE_URLS))
      .then(self.skipWaiting())
  );
});

// Activate event - Clean up old caches
self.addEventListener('activate', event => {
  const currentCaches = [CACHE_NAME, RUNTIME];
  event.waitUntil(
    caches
      .keys()
      .then(cacheNames => {
        return cacheNames.filter(cacheName => !currentCaches.includes(cacheName));
      })
      .then(cachesToDelete => {
        return Promise.all(
          cachesToDelete.map(cacheToDelete => {
            return caches.delete(cacheToDelete);
          })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - Network-first strategy with offline fallback
self.addEventListener('fetch', event => {
  // Skip cross-origin requests
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  // Handle API requests
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return caches.match('/offline.html');
        })
    );
    return;
  }

  // Handle static assets and navigation requests
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      if (cachedResponse) {
        return cachedResponse;
      }

      return caches.open(RUNTIME).then(cache => {
        return fetch(event.request).then(response => {
          // Put a copy of the response in the runtime cache
          return cache.put(event.request, response.clone()).then(() => {
            return response;
          });
        });
      });
    })
  );
});

// Background sync for offline actions
self.addEventListener('sync', event => {
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncMessages());
  }
});

// Push notification handling
self.addEventListener('push', event => {
  const data = event.data.json();
  
  const options = {
    body: data.body,
    icon: '/logo192.png',
    badge: '/notification-badge.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'View Details',
        icon: '/checkmark.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/xmark.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
  event.notification.close();

  event.waitUntil(
    clients.matchAll({
      type: 'window'
    })
    .then(function(clientList) {
      if (clientList.length > 0) {
        let client = clientList[0];
        for (let i = 0; i < clientList.length; i++) {
          if (clientList[i].focused) {
            client = clientList[i];
          }
        }
        return client.focus();
      }
      return clients.openWindow('/');
    })
  );
});

// Helper function for background sync
async function syncMessages() {
  try {
    const messageQueue = await idb.openDB('messageQueue');
    const messages = await messageQueue.getAll('outbox');
    
    await Promise.all(messages.map(async message => {
      try {
        await fetch('/api/messages', {
          method: 'POST',
          body: JSON.stringify(message),
          headers: {
            'Content-Type': 'application/json'
          }
        });
        await messageQueue.delete('outbox', message.id);
      } catch (error) {
        console.error('Error syncing message:', error);
      }
    }));
  } catch (error) {
    console.error('Error processing message queue:', error);
  }
}

// Periodic background sync for content updates
self.addEventListener('periodicsync', event => {
  if (event.tag === 'update-content') {
    event.waitUntil(updateContent());
  }
});

// Helper function for periodic content updates
async function updateContent() {
  try {
    const cache = await caches.open(CACHE_NAME);
    await cache.add('/api/content/latest');
  } catch (error) {
    console.error('Error updating content:', error);
  }
}

// Handle offline fallback
self.addEventListener('fetch', event => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return caches.match('/offline.html');
        })
    );
  }
});
