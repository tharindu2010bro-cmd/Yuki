/* Yuki native bridge — runs only inside the Android app.
   Makes the app's existing web code (share, download, vibrate, Notification)
   use native features. You never need to edit this when you edit index.html. */
(function () {
  var C = window.Capacitor;
  if (!C || !C.isNativePlatform || !C.isNativePlatform()) return;
  var P = C.Plugins || {};
  var FS = P.Filesystem, Share = P.Share, Haptics = P.Haptics, LN = P.LocalNotifications;

  function def(obj, key, val) {
    try { Object.defineProperty(obj, key, { value: val, configurable: true, writable: true }); }
    catch (e) { try { obj[key] = val; } catch (_) {} }
  }
  function toast(m) { try { if (typeof window.toast === 'function') window.toast(m); } catch (_) {} }
  function safeName(n) { return String(n || 'file').replace(/[^\w.\- ]+/g, '_'); }
  function isCancel(e) { return e && /cancel/i.test(String(e.message || e)); }
  function abortErr() { try { return new DOMException('Share canceled', 'AbortError'); } catch (_) { var e = new Error('Share canceled'); e.name = 'AbortError'; return e; } }

  function blobToBase64(blob) {
    return new Promise(function (res, rej) {
      var r = new FileReader();
      r.onload = function () { res(String(r.result).split(',')[1] || ''); };
      r.onerror = function () { rej(r.error); };
      r.readAsDataURL(blob);
    });
  }
  async function writeTemp(blob, name) {
    var data = await blobToBase64(blob);
    var w = await FS.writeFile({
      path: 'yuki/' + Date.now() + '-' + safeName(name),
      data: data, directory: 'CACHE', recursive: true
    });
    return w.uri;
  }

  /* ---------- Share ---------- */
  if (Share && FS) {
    def(navigator, 'canShare', function (d) {
      return !!(d && (d.files || d.text || d.title || d.url));
    });
    def(navigator, 'share', async function (d) {
      d = d || {};
      try {
        var opts = { title: d.title, text: d.text, url: d.url, dialogTitle: d.title || 'Share' };
        if (d.files && d.files.length) {
          opts.files = [];
          for (var i = 0; i < d.files.length; i++) opts.files.push(await writeTemp(d.files[i], d.files[i].name));
        }
        await Share.share(opts);
      } catch (e) {
        if (isCancel(e)) throw abortErr();
        throw e;
      }
    });

    /* ---------- File save / export (a[download] with blob:/data: link) ---------- */
    var origClick = HTMLAnchorElement.prototype.click;
    HTMLAnchorElement.prototype.click = function () {
      var a = this;
      if (a.hasAttribute('download') && /^(blob|data):/.test(a.href)) {
        var name = a.getAttribute('download') || 'file';
        fetch(a.href).then(function (r) { return r.blob(); })
          .then(function (b) { return writeTemp(b, name); })
          .then(function (uri) { return Share.share({ title: name, files: [uri], dialogTitle: 'Save ' + name }); })
          .then(function () { toast('📁 ' + name); })
          .catch(function (e) { if (!isCancel(e)) { try { console.warn('[Yuki bridge]', e); } catch (_) {} toast('⚠️ Could not save file'); } });
        return;
      }
      return origClick.apply(this, arguments);
    };
  }

  /* ---------- Vibration ---------- */
  if (Haptics) {
    def(navigator, 'vibrate', function (p) {
      var ms = Array.isArray(p) ? p.filter(function (_, i) { return i % 2 === 0; }).reduce(function (a, b) { return a + b; }, 0) : p;
      ms = Math.max(10, Math.min(+ms || 0, 2000));
      try { Haptics.vibrate({ duration: ms }); } catch (_) {}
      return true;
    });
  }

  /* ---------- Notifications ---------- */
  if (LN) {
    var perm = 'default';
    function map(r) { return r === 'granted' ? 'granted' : (r === 'denied' ? 'denied' : 'default'); }
    try { LN.checkPermissions().then(function (r) { perm = map(r.display); }); } catch (_) {}

    function Notif(title, o) {
      o = o || {};
      this.title = title; this.body = o.body || ''; this.close = function () {}; this.onclick = null;
      try {
        LN.schedule({ notifications: [{
          id: Math.floor(Date.now() % 2147483000) + Math.floor(Math.random() * 500),
          title: String(title || ''), body: String(o.body || '')
        }] });
      } catch (_) {}
    }
    Notif.requestPermission = async function (cb) {
      try { var r = await LN.requestPermissions(); perm = map(r.display); } catch (_) { perm = 'denied'; }
      if (typeof cb === 'function') cb(perm);
      return perm;
    };
    Object.defineProperty(Notif, 'permission', { get: function () { return perm; } });
    def(window, 'Notification', Notif);
  }
})();
