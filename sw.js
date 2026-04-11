const CACHE = 'taesan-v1';
const ASSETS = [
  '/rpm-math/student.html',
  '/rpm-math/icon-192.png',
  '/rpm-math/icon-512.png'
];

self.addEventListener('install', function(e){
  e.waitUntil(
    caches.open(CACHE).then(function(c){ return c.addAll(ASSETS); })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function(e){
  e.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.filter(function(k){ return k!==CACHE; }).map(function(k){ return caches.delete(k); }));
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', function(e){
  // 이미지/크롭 파일은 캐시 안 함 (항상 최신 버전)
  if(e.request.url.includes('crops') || e.request.url.includes('firestore') || e.request.url.includes('googleapis')){
    return;
  }
  e.respondWith(
    caches.match(e.request).then(function(cached){
      return cached || fetch(e.request);
    })
  );
});
