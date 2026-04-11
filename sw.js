const CACHE = 'taesan-v2';
const ASSETS = [
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

self.addEventListener('message', function(e){
  if(e.data && e.data.type === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('fetch', function(e){
  // student.html은 항상 네트워크에서 최신 버전 가져오기
  if(e.request.url.includes('student.html')){
    e.respondWith(
      fetch(e.request).catch(function(){
        return caches.match(e.request);
      })
    );
    return;
  }
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
