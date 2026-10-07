const C='ageop-v1';
self.addEventListener('install',e=>{self.skipWaiting();e.waitUntil(caches.open(C).then(c=>c.addAll(['./','index.html'])))});
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;const d=new URL(e.request.url).pathname.includes('/data/');
e.respondWith(d?fetch(e.request).then(r=>{const k=r.clone();caches.open(C).then(c=>c.put(e.request,k));return r}).catch(()=>caches.match(e.request)):caches.match(e.request).then(r=>r||fetch(e.request)))});
