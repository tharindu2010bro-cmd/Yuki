# Build-time tweaks for the APK. Runs in GitHub Actions before the build.
# For future changes, just replace THIS file. The workflow stays the same.
import os
import re
import shutil
import urllib.request

P = 'www/index.html'
s = open(P, encoding='utf-8').read()


def head(html):
    """Insert html right after the opening <head> tag."""
    global s
    m = re.search(r'<head[^>]*>', s, re.I)
    if not m:
        raise SystemExit('<head> not found in www/index.html')
    s = s[:m.end()] + html + s[m.end():]


# 1. Native bridge (share, save file, vibrate, notifications)
shutil.copy('bridge.js', 'www/bridge.js')
head('<script src="bridge.js"></script>')

# 2. Bundle the remote images into the app
IMAGES = {
    'bg.png': 'https://i.ibb.co/cKHsySXs/upscaled-4k-143280.png',
    'welcome.png': 'https://i.ibb.co/zVX9YvRJ/143272.png',
    'nf.png': 'https://i.ibb.co/1f5KKn3q/144244.png',
}
os.makedirs('www/img', exist_ok=True)
for name, url in IMAGES.items():
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = urllib.request.urlopen(req, timeout=60).read()
        if len(data) > 1000:
            open('www/img/' + name, 'wb').write(data)
            s = s.replace(url, '/img/' + name)
            print('image ok', name, len(data))
    except Exception as e:
        print('image fail', name, e)

# 3. Bottom spacing (app default is 38px, too much inside the APK)
head('<style>html:root{--yw:10px !important}</style>')

# 4. On-screen error report (so a blank screen explains itself).
# Invisible when everything works: the box removes itself after 9 s unless an error was caught.
DIAG = r"""<script>(function(){var box;
function show(t){try{if(!box){box=document.createElement('pre');box.id='yDiag';
box.style.cssText='position:fixed;left:0;right:0;top:0;max-height:70%;overflow:auto;margin:0;padding:40px 10px 10px;z-index:2147483647;background:rgba(110,0,0,.93);color:#fff;font:11px/1.4 monospace;white-space:pre-wrap;word-break:break-all';
(document.body||document.documentElement).appendChild(box)}box.textContent+=t+'\n'}catch(e){}}
window.addEventListener('error',function(e){var t=e.target;
if(t&&t!==window&&(t.src||t.href)){if((t.src||t.href)===location.href)return;show('RES FAIL '+(t.src||t.href));return}
show('ERR '+e.message+' @'+String(e.filename||'').split('/').pop()+':'+e.lineno+':'+e.colno)},true);
window.addEventListener('unhandledrejection',function(e){show('REJ '+((e.reason&&e.reason.message)||e.reason))});
show('boot '+location.href+' '+navigator.userAgent.replace(/.*Android/,'Android').slice(0,40));
setTimeout(function(){var sp=document.getElementById('splash');
show('t+5s splash='+(sp?sp.className:'none')+' bodyKids='+(document.body?document.body.children.length:'nobody'))},5000);
setTimeout(function(){var b=document.getElementById('yDiag');if(b&&!/ERR|REJ|RES FAIL/.test(b.textContent))b.remove()},9000)})();</script>"""
head(DIAG)

open(P, 'w', encoding='utf-8').write(s)
print('tweaks done')
