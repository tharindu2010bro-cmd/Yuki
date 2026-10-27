/* Yuki's Anime Tracker · offline support (v46.29)
   - app page: opens instantly from the saved copy, updates itself in the background (new version shows on the next launch)
   - images / fonts / scripts: saved on first view, served instantly after */
const V='yuki-sw-v2',IMG='yuki-img-v1',MAXIMG=200;
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(['./','./index.html'])).then(()=>self.skipWaiting()).catch(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(n=>n!==V&&n!==IMG).map(n=>caches.delete(n)))).then(()=>self.clients.claim()))});
const trim=async()=>{try{const c=await caches.open(IMG),k=await c.keys();if(k.length>MAXIMG)await Promise.all(k.slice(0,k.length-MAXIMG).map(x=>c.delete(x)))}catch(e){}};
self.addEventListener('fetch',e=>{
  const r=e.request;if(r.method!=='GET')return;
  const u=new URL(r.url);
  if(r.mode==='navigate'||(u.origin===location.origin&&(u.pathname.endsWith('/')||u.pathname.endsWith('.html')))){
    e.respondWith((async()=>{
      /* instant start: show the saved copy now, fetch the newest one in the background for next launch */
      const c=await caches.open(V),hit=await c.match('./index.html');
      const upd=fetch(u.origin+u.pathname,{cache:'no-cache'}).then(n=>{if(n&&n.ok)c.put('./index.html',n.clone());return n}).catch(()=>null);
      if(hit){e.waitUntil(upd);return hit}
      return (await upd)||(await c.match('./'))||Response.error();
    })());
    return;
  }
  if(r.destination==='image'||r.destination==='font'||r.destination==='style'||(r.destination==='script'&&u.origin!==location.origin)){
    e.respondWith((async()=>{
      const c=await caches.open(IMG),hit=await c.match(r);
      const net=fetch(r).then(x=>{if(x&&(x.ok||x.type==='opaque')){c.put(r,x.clone());trim()}return x}).catch(()=>null);
      return hit||(await net)||Response.error();
    })());
  }
});
