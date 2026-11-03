const CACHE='gundem-auto-v2';
const ASSETS=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));self.clients.claim()});
self.addEventListener('fetch',e=>{
 if(e.request.method!=='GET'||new URL(e.request.url).origin!==self.location.origin)return;
 e.respondWith((async()=>{
   try{let res=await fetch(e.request);if(res.ok){let cache=await caches.open(CACHE);cache.put(e.request,res.clone()).catch(()=>{});}return res;}
   catch(error){let cached=await caches.match(e.request,{ignoreSearch:true});if(cached)return cached;throw error;}
 })());
});
