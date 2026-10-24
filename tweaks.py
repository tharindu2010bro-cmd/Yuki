# Build-time tweaks for the APK. Runs in GitHub Actions before the build.
# For future changes, just replace THIS file. The workflow stays the same.
import shutil
import urllib.request

P = 'www/index.html'
s = open(P, encoding='utf-8').read()


def head(html):
    global s
    i = s.find('<head>')
    if i < 0:
        raise SystemExit('<head> not found in www/index.html')
    s = s[:i + 6] + html + s[i + 6:]


# 1. Native bridge (share, save file, vibrate, notifications)
shutil.copy('bridge.js', 'www/bridge.js')
head('<script src="bridge.js"></script>')

# 2. Bundle the remote images into the app
IMAGES = {
    'bg.png': 'https://i.ibb.co/cKHsySXs/upscaled-4k-143280.png',
    'welcome.png': 'https://i.ibb.co/zVX9YvRJ/143272.png',
    'nf.png': 'https://i.ibb.co/1f5KKn3q/144244.png',
}
import os
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

open(P, 'w', encoding='utf-8').write(s)
print('tweaks done')
