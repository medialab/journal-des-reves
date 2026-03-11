// Service Worker - Journal des Rêves
// Version : incrémenter à chaque déploiement pour forcer le rafraîchissement
var CACHE_VERSION = 'reves-v1';
var CACHE_NAME = CACHE_VERSION + '-' + new Date().getTime();

// Assets à mettre en cache dès l'installation
var ASSETS_TO_CACHE = [
    '/polls/',
    '/offline',
    '/static/polls/style.css',
    '/static/polls/forms.css',
    '/static/polls/pages.css',
    '/static/polls/notifications.css',
    '/static/polls/notifications.js',
    '/static/polls/icons/icon-192x192.png',
    '/static/polls/icons/icon-512x512.png',
];

// ─────────────────────────────────────────────
// INSTALL : mise en cache des assets statiques
// ─────────────────────────────────────────────
self.addEventListener('install', function(event) {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then(function(cache) {
            return cache.addAll(ASSETS_TO_CACHE);
        }).catch(function(err) {
            console.warn('[SW] Erreur install cache:', err);
        })
    );
});

// ─────────────────────────────────────────────
// ACTIVATE : suppression des anciens caches
// ─────────────────────────────────────────────
self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames
                    .filter(function(name) {
                        return name.startsWith('reves-') && name !== CACHE_NAME;
                    })
                    .map(function(name) {
                        return caches.delete(name);
                    })
            );
        }).then(function() {
            return self.clients.claim();
        })
    );
});

// ─────────────────────────────────────────────
// FETCH : stratégie Network-first pour les pages,
//         Cache-first pour les assets statiques
// ─────────────────────────────────────────────
self.addEventListener('fetch', function(event) {
    var url = new URL(event.request.url);

    // Ignorer les requêtes non-GET, non-HTTP/S, et les API
    if (event.request.method !== 'GET') return;
    if (!url.protocol.startsWith('http')) return;
    if (url.pathname.startsWith('/polls/api/')) return;
    if (url.pathname.startsWith('/webpush/')) return;
    if (url.pathname.startsWith('/admin/')) return;
    // Ne JAMAIS mettre en cache les pages d'auth : le token CSRF est unique
    // à chaque chargement ; s'il est servi depuis le cache il sera périmé
    if (url.pathname.startsWith('/accounts/')) return;

    // Assets statiques → Cache-first
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(event.request).then(function(cached) {
                return cached || fetch(event.request).then(function(response) {
                    var clone = response.clone();
                    caches.open(CACHE_NAME).then(function(cache) {
                        cache.put(event.request, clone);
                    });
                    return response;
                });
            })
        );
        return;
    }

    // Pages → Network-first, fallback cache, fallback /offline
    event.respondWith(
        fetch(event.request).then(function(response) {
            var clone = response.clone();
            caches.open(CACHE_NAME).then(function(cache) {
                cache.put(event.request, clone);
            });
            return response;
        }).catch(function() {
            return caches.match(event.request).then(function(cached) {
                return cached || caches.match('/offline');
            });
        })
    );
});

// ─────────────────────────────────────────────
// PUSH : notification reçue depuis le serveur
// ─────────────────────────────────────────────
self.addEventListener('push', function(event) {
    var data = {};
    if (event.data) {
        try {
            data = event.data.json();
        } catch(e) {
            data = { head: 'Journal des Rêves', body: event.data.text() };
        }
    }

    var title = data.head || 'Journal des Rêves 🌙';
    var options = {
        body: data.body || "N'oublie pas de noter ton rêve !",
        icon: data.icon || '/static/polls/icons/icon-192x192.png',
        badge: '/static/polls/icons/icon-72x72.png',
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/polls/enregistrer/'
        },
        actions: [
            { action: 'enregistrer', title: '✍ Enregistrer mon rêve' },
            { action: 'fermer',      title: 'Plus tard' },
        ]
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// ─────────────────────────────────────────────
// NOTIFICATIONCLICK : ouvrir la bonne page
// ─────────────────────────────────────────────
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    var targetUrl = '/polls/enregistrer/';

    if (event.action === 'fermer') return;
    if (event.notification.data && event.notification.data.url) {
        targetUrl = event.notification.data.url;
    }

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
            for (var i = 0; i < clientList.length; i++) {
                var client = clientList[i];
                if (client.url.includes(targetUrl) && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});
