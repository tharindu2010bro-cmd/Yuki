#!/usr/bin/env python3
"""Adds an Android home-screen widget ("Airing soon") to the generated Capacitor project.
Run in the workflow AFTER `npx cap add android` / `cap sync`. Safe to run twice.
v47.42: the Photo frame widget was removed; the Airing soon widget was rebuilt (adapts to its size, live countdown, 12/24h clock)."""
import json, os, re, glob

cfg = json.load(open('capacitor.config.json')) if os.path.exists('capacitor.config.json') else {}
PKG = cfg.get('appId', 'com.yuki.tracker')
APP = 'android/app/src/main'
JAVA = os.path.join(APP, 'java', *PKG.split('.'))
RES = os.path.join(APP, 'res')
os.makedirs(JAVA, exist_ok=True)
for d in ('layout', 'drawable', 'xml'):
    os.makedirs(os.path.join(RES, d), exist_ok=True)

def w(path, text):
    open(path, 'w', encoding='utf-8').write(text)

# ---------- clean up the removed Photo frame widget (older runs / cached projects) ----------
for f in (os.path.join(JAVA, 'YukiPhotoWidgetProvider.java'), os.path.join(JAVA, 'YukiPhotoPickActivity.java'),
          os.path.join(RES, 'layout', 'yuki_photo_widget.xml'), os.path.join(RES, 'xml', 'yuki_photo_widget_info.xml')):
    if os.path.exists(f):
        os.remove(f)

# ---------- resources ----------
w(os.path.join(RES, 'drawable', 'yuki_widget_bg.xml'), '''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <gradient android:angle="135" android:startColor="#F21B1740" android:endColor="#F20A0B1C"/>
    <corners android:radius="26dp"/>
    <stroke android:width="1dp" android:color="#408B5CF6"/>
</shape>
''')
w(os.path.join(RES, 'drawable', 'yuki_widget_bar.xml'), '''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <gradient android:angle="270" android:startColor="#A78BFA" android:endColor="#F472B6"/>
    <corners android:radius="3dp"/>
</shape>
''')
w(os.path.join(RES, 'drawable', 'yuki_widget_row.xml'), '''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#1FFFFFFF"/>
    <corners android:radius="14dp"/>
</shape>
''')

MAXROWS = 5
rows = ''
for i in range(1, MAXROWS + 1):
    rows += f'''
    <LinearLayout android:id="@+id/yw_row{i}" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:gravity="center_vertical" android:layout_marginTop="6dp"
        android:paddingStart="8dp" android:paddingEnd="10dp" android:paddingTop="5dp" android:paddingBottom="5dp"
        android:background="@drawable/yuki_widget_row" android:visibility="gone">
        <FrameLayout android:layout_width="4dp" android:layout_height="30dp" android:background="@drawable/yuki_widget_bar"/>
        <LinearLayout android:layout_width="0dp" android:layout_height="wrap_content" android:layout_weight="1"
            android:orientation="vertical" android:layout_marginStart="10dp">
            <TextView android:id="@+id/yw_t{i}" android:layout_width="match_parent" android:layout_height="wrap_content"
                android:textColor="#F4F7FF" android:textSize="13sp" android:textStyle="bold" android:singleLine="true" android:ellipsize="end"/>
            <TextView android:id="@+id/yw_s{i}" android:layout_width="match_parent" android:layout_height="wrap_content"
                android:textColor="#A7ADC8" android:textSize="11sp" android:singleLine="true" android:ellipsize="end"/>
        </LinearLayout>
        <LinearLayout android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:orientation="vertical" android:gravity="end" android:layout_marginStart="8dp">
            <TextView android:id="@+id/yw_day{i}" android:layout_width="wrap_content" android:layout_height="wrap_content"
                android:textColor="#F9A8D4" android:textSize="10sp" android:textStyle="bold" android:singleLine="true"/>
            <TextView android:id="@+id/yw_time{i}" android:layout_width="wrap_content" android:layout_height="wrap_content"
                android:textColor="#DDD6FE" android:textSize="13sp" android:textStyle="bold" android:singleLine="true"/>
        </LinearLayout>
    </LinearLayout>'''

w(os.path.join(RES, 'layout', 'yuki_widget.xml'), f'''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android" android:id="@+id/yw_root"
    android:layout_width="match_parent" android:layout_height="match_parent" android:orientation="vertical"
    android:padding="12dp" android:background="@drawable/yuki_widget_bg">
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content" android:orientation="horizontal">
        <TextView android:layout_width="0dp" android:layout_height="wrap_content" android:layout_weight="1"
            android:text="AIRING SOON" android:textColor="#C4B5FD" android:textSize="11sp" android:textStyle="bold" android:letterSpacing="0.12"/>
        <TextView android:id="@+id/yw_count" android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="Yuki" android:textColor="#F472B6" android:textSize="11sp" android:textStyle="bold"/>
    </LinearLayout>{rows}
    <TextView android:id="@+id/yw_empty" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:layout_marginTop="10dp" android:text="Open Yuki once to load your shows" android:textColor="#9AA0B8" android:textSize="13sp"/>
</LinearLayout>
''')

w(os.path.join(RES, 'xml', 'yuki_widget_info.xml'), '''<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="250dp" android:minHeight="180dp" android:minResizeWidth="180dp" android:minResizeHeight="110dp"
    android:targetCellWidth="4" android:targetCellHeight="3"
    android:updatePeriodMillis="1800000" android:initialLayout="@layout/yuki_widget" android:previewLayout="@layout/yuki_widget"
    android:resizeMode="horizontal|vertical" android:widgetCategory="home_screen"/>
''')

# ---------- java: the widget ----------
w(os.path.join(JAVA, 'YukiWidgetProvider.java'), r'''package __PKG__;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.RemoteViews;
import org.json.JSONArray;
import org.json.JSONObject;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/** "Airing soon": the next episodes of your shows. Shows as many rows as fit the widget size; the clock follows the phone's 12/24h setting. */
public class YukiWidgetProvider extends AppWidgetProvider {
    static final String PREFS = "YukiWidget", KEY = "items";
    static final int MAX = 5;

    @Override
    public void onUpdate(Context c, AppWidgetManager m, int[] ids) {
        for (int id : ids) m.updateAppWidget(id, build(c, m, id));
    }

    @Override
    public void onAppWidgetOptionsChanged(Context c, AppWidgetManager m, int id, Bundle o) {
        m.updateAppWidget(id, build(c, m, id));
    }

    public static void refresh(Context c) {
        AppWidgetManager m = AppWidgetManager.getInstance(c);
        int[] ids = m.getAppWidgetIds(new ComponentName(c, YukiWidgetProvider.class));
        for (int id : ids) m.updateAppWidget(id, build(c, m, id));
    }

    static boolean sameDay(Calendar a, Calendar b) {
        return a.get(Calendar.YEAR) == b.get(Calendar.YEAR) && a.get(Calendar.DAY_OF_YEAR) == b.get(Calendar.DAY_OF_YEAR);
    }

    static String day(long at) {
        Calendar a = Calendar.getInstance(), b = Calendar.getInstance();
        b.setTimeInMillis(at);
        if (sameDay(a, b)) return "TODAY";
        a.add(Calendar.DAY_OF_YEAR, 1);
        if (sameDay(a, b)) return "TOMORROW";
        return new SimpleDateFormat("EEE", Locale.getDefault()).format(new Date(at)).toUpperCase(Locale.getDefault());
    }

    static String clock(Context c, long at) {
        return android.text.format.DateFormat.getTimeFormat(c).format(new Date(at));
    }

    /** "Airing now" / "in 25m" / "in 3h 10m" (only within the next day) */
    static String rel(long at, long now) {
        long d = at - now;
        if (d <= 0) return "Airing now";
        long mins = d / 60000L;
        if (mins < 1) return "in <1m";
        if (mins < 60) return "in " + mins + "m";
        if (mins < 24 * 60) return "in " + (mins / 60) + "h" + (mins % 60 > 0 ? " " + (mins % 60) + "m" : "");
        return "";
    }

    /** how many rows fit: header ~44dp, each row ~44dp */
    static int rowsFor(Bundle o) {
        int h = 180;
        if (o != null) {
            int mn = o.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT, 180);
            int mx = o.getInt(AppWidgetManager.OPTION_APPWIDGET_MAX_HEIGHT, 180);
            h = Math.max(mn, mx);
        }
        int n = (h - 40) / 46;
        return Math.max(1, Math.min(MAX, n));
    }

    static RemoteViews build(Context c, AppWidgetManager m, int id) {
        RemoteViews v = new RemoteViews(c.getPackageName(), R.layout.yuki_widget);
        int[] rows = {R.id.yw_row1, R.id.yw_row2, R.id.yw_row3, R.id.yw_row4, R.id.yw_row5};
        int[] ts = {R.id.yw_t1, R.id.yw_t2, R.id.yw_t3, R.id.yw_t4, R.id.yw_t5};
        int[] ss = {R.id.yw_s1, R.id.yw_s2, R.id.yw_s3, R.id.yw_s4, R.id.yw_s5};
        int[] dy = {R.id.yw_day1, R.id.yw_day2, R.id.yw_day3, R.id.yw_day4, R.id.yw_day5};
        int[] tm = {R.id.yw_time1, R.id.yw_time2, R.id.yw_time3, R.id.yw_time4, R.id.yw_time5};
        int fit = rowsFor(m == null ? null : m.getAppWidgetOptions(id));
        List<long[]> idx = new ArrayList<>();
        List<String> names = new ArrayList<>();
        boolean hasData = false;
        try {
            android.content.SharedPreferences sp = c.getSharedPreferences(PREFS, 0);
            hasData = sp.contains(KEY);
            JSONArray arr = new JSONArray(sp.getString(KEY, "[]"));
            long now = System.currentTimeMillis();
            for (int i = 0; i < arr.length(); i++) {
                JSONObject o = arr.getJSONObject(i);
                long at = o.getLong("a");
                if (at > now - 30 * 60 * 1000L) {
                    idx.add(new long[]{at, o.optLong("e", 0)});
                    names.add(o.optString("t", "?"));
                }
            }
            for (int i = 0; i < idx.size(); i++) for (int j = i + 1; j < idx.size(); j++) if (idx.get(j)[0] < idx.get(i)[0]) {
                Collections.swap(idx, i, j); Collections.swap(names, i, j);
            }
        } catch (Exception e) { }
        long now = System.currentTimeMillis();
        int show = Math.min(fit, idx.size());
        for (int i = 0; i < MAX; i++) {
            if (i < show) {
                long[] it = idx.get(i);
                String r = rel(it[0], now);
                String ep = it[1] > 0 ? "Episode " + it[1] : "New episode";
                v.setViewVisibility(rows[i], View.VISIBLE);
                v.setTextViewText(ts[i], names.get(i));
                v.setTextViewText(ss[i], r.isEmpty() ? ep : ep + " · " + r);
                v.setTextViewText(dy[i], day(it[0]));
                v.setTextViewText(tm[i], clock(c, it[0]));
            } else v.setViewVisibility(rows[i], View.GONE);
        }
        v.setTextViewText(R.id.yw_count, idx.size() > show ? "+" + (idx.size() - show) + " more" : "Yuki \u2744");
        v.setTextViewText(R.id.yw_empty, hasData ? "Nothing airing soon \u2744" : "Open Yuki once to load your shows");
        v.setViewVisibility(R.id.yw_empty, idx.isEmpty() ? View.VISIBLE : View.GONE);
        Intent open = c.getPackageManager().getLaunchIntentForPackage(c.getPackageName());
        if (open != null) {
            PendingIntent pi = PendingIntent.getActivity(c, 0, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            v.setOnClickPendingIntent(R.id.yw_root, pi);
        }
        return v;
    }
}
'''.replace('__PKG__', PKG))

w(os.path.join(JAVA, 'YukiWidgetPlugin.java'), r'''package __PKG__;

import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "YukiWidget")
public class YukiWidgetPlugin extends Plugin {
    @PluginMethod
    public void update(PluginCall call) {
        String items = call.getString("items", "[]");
        getContext().getSharedPreferences(YukiWidgetProvider.PREFS, 0).edit().putString(YukiWidgetProvider.KEY, items).apply();
        YukiWidgetProvider.refresh(getContext());
        call.resolve();
    }
}
'''.replace('__PKG__', PKG))

w(os.path.join(JAVA, 'YukiFilePlugin.java'), r'''package __PKG__;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import androidx.activity.result.ActivityResult;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

/** Opens Android's own "Save as" screen so the backup lands in a folder the user picks (Downloads, Documents, Drive...). */
@CapacitorPlugin(name = "YukiFile")
public class YukiFilePlugin extends Plugin {
    @PluginMethod
    public void save(PluginCall call) {
        String name = call.getString("name", "yuki-backup.json");
        Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("application/json");
        i.putExtra(Intent.EXTRA_TITLE, name);
        startActivityForResult(call, i, "saveResult");
    }

    @ActivityCallback
    private void saveResult(PluginCall call, ActivityResult result) {
        if (call == null) return;
        if (result.getResultCode() != Activity.RESULT_OK || result.getData() == null || result.getData().getData() == null) {
            call.reject("cancelled");
            return;
        }
        Uri uri = result.getData().getData();
        try (OutputStream os = getContext().getContentResolver().openOutputStream(uri, "wt")) {
            os.write(call.getString("data", "").getBytes(StandardCharsets.UTF_8));
            os.flush();
            JSObject r = new JSObject();
            r.put("uri", uri.toString());
            call.resolve(r);
        } catch (Exception e) {
            call.reject("write failed: " + e.getMessage());
        }
    }
}
'''.replace('__PKG__', PKG))

# ---------- background sync (alerts + widget stay fresh while the app is closed) ----------
w(os.path.join(JAVA, 'YukiSync.java'), r'''package __PKG__;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import android.os.SystemClock;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Keeps episode alerts and the home-screen widget fresh while the app is closed. */
public class YukiSync {
    static final String PREFS = "YukiSync";
    static final long DAY = 86400000L;
    static final int REFRESH_CODE = 7001;

    static class A { int code; long t; String title; String body; }

    static SharedPreferences sp(Context c) { return c.getSharedPreferences(PREFS, 0); }

    static JSONArray items(Context c) {
        try { return new JSONArray(sp(c).getString("items", "[]")); } catch (Exception e) { return new JSONArray(); }
    }

    static void save(Context c, boolean enabled, JSONArray items) {
        sp(c).edit().putBoolean("enabled", enabled).putString("items", items.toString()).apply();
    }

    static int armedCount(Context c) {
        try { return new JSONArray(sp(c).getString("armed", "[]")).length(); } catch (Exception e) { return 0; }
    }

    static int codeOf(long id, int ep) { return ((id + "#" + ep).hashCode() & 0x7fffffff) % 2147483000 + 1; }

    static Intent notifyIntent(Context c, int code) {
        return new Intent(c, YukiNotifyReceiver.class).setAction("yuki.NOTIFY").setData(Uri.parse("yuki://ep/" + code));
    }

    static void cancelArmed(Context c) {
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        try {
            JSONArray a = new JSONArray(sp(c).getString("armed", "[]"));
            for (int i = 0; i < a.length(); i++) {
                int code = a.getInt(i);
                PendingIntent pi = PendingIntent.getBroadcast(c, code, notifyIntent(c, code), PendingIntent.FLAG_NO_CREATE | PendingIntent.FLAG_IMMUTABLE);
                if (pi != null) { am.cancel(pi); pi.cancel(); }
            }
        } catch (Exception ex) { }
        sp(c).edit().putString("armed", "[]").apply();
    }

    static void setAlarm(AlarmManager am, long t, PendingIntent pi) {
        try {
            if (Build.VERSION.SDK_INT >= 31 && !am.canScheduleExactAlarms()) { am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, t, pi); return; }
            if (Build.VERSION.SDK_INT >= 23) am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, t, pi);
            else am.setExact(AlarmManager.RTC_WAKEUP, t, pi);
        } catch (SecurityException ex) { am.set(AlarmManager.RTC_WAKEUP, t, pi); }
    }

    static PendingIntent refreshPi(Context c, int flags) {
        Intent i = new Intent(c, YukiSyncReceiver.class).setAction("yuki.SYNC");
        return PendingIntent.getBroadcast(c, REFRESH_CODE, i, flags | PendingIntent.FLAG_IMMUTABLE);
    }

    /** Twice-a-day wake-up that refreshes the airing times from AniList. Armed only once, so a refresh never re-times itself. */
    static void armRefresh(Context c) {
        if (refreshPi(c, PendingIntent.FLAG_NO_CREATE) != null) return;
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        try {
            am.setInexactRepeating(AlarmManager.ELAPSED_REALTIME_WAKEUP, SystemClock.elapsedRealtime() + AlarmManager.INTERVAL_HOUR,
                    AlarmManager.INTERVAL_HALF_DAY, refreshPi(c, PendingIntent.FLAG_UPDATE_CURRENT));
        } catch (Exception ex) { }
    }

    static void cancelRefresh(Context c) {
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        PendingIntent pi = refreshPi(c, PendingIntent.FLAG_NO_CREATE);
        if (pi != null) { am.cancel(pi); pi.cancel(); }
    }

    /** Re-arms every episode alert from the stored list (also used after a reboot or an app update). */
    static void arm(Context c) {
        cancelArmed(c);
        JSONArray items = items(c);
        if (items.length() == 0) { cancelRefresh(c); return; }
        armRefresh(c);
        if (!sp(c).getBoolean("enabled", false)) return;
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        long now = System.currentTimeMillis();
        List<A> list = new ArrayList<A>();
        try {
            for (int i = 0; i < items.length(); i++) {
                JSONObject o = items.getJSONObject(i);
                long id = o.getLong("id");
                int ep = o.getInt("ep");
                long at = o.getLong("at");
                int tot = o.optInt("tot", 0);
                String name = o.optString("name", "?");
                for (int k = 0; k < 6; k++) {
                    int epn = ep + k;
                    long t = at + k * 7 * DAY;
                    if (tot > 0 && epn > tot) break;
                    if (t <= now || t - now >= 42 * DAY) continue;
                    A a = new A();
                    a.code = codeOf(id, epn);
                    a.t = t;
                    a.title = "\uD83D\uDD14 " + name;
                    a.body = k == 0 ? "Episode " + epn + " just aired!" : "Episode " + epn + " is due to air today";
                    list.add(a);
                }
            }
        } catch (Exception ex) { }
        Collections.sort(list, new Comparator<A>() {
            public int compare(A x, A y) { return Long.compare(x.t, y.t); }
        });
        JSONArray armed = new JSONArray();
        for (int i = 0; i < list.size() && i < 120; i++) {
            A a = list.get(i);
            Intent in = notifyIntent(c, a.code).putExtra("title", a.title).putExtra("body", a.body).putExtra("code", a.code);
            PendingIntent pi = PendingIntent.getBroadcast(c, a.code, in, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            setAlarm(am, a.t, pi);
            armed.put(a.code);
        }
        sp(c).edit().putString("armed", armed.toString()).apply();
    }

    /** Same shape the page's own widget feed uses: [{t,a,e}] */
    static void pushWidget(Context c, JSONArray items) {
        try {
            long now = System.currentTimeMillis();
            List<JSONObject> out = new ArrayList<JSONObject>();
            for (int i = 0; i < items.length(); i++) {
                JSONObject o = items.getJSONObject(i);
                int ep = o.getInt("ep");
                long at = o.getLong("at");
                int tot = o.optInt("tot", 0);
                for (int k = 0; k < 3; k++) {
                    int epn = ep + k;
                    long t = at + k * 7 * DAY;
                    if (tot > 0 && epn > tot) break;
                    if (t > now - 30 * 60 * 1000L && t - now < 14 * DAY) {
                        JSONObject r = new JSONObject();
                        r.put("t", o.optString("name", "?"));
                        r.put("a", t);
                        r.put("e", epn);
                        out.add(r);
                    }
                }
            }
            Collections.sort(out, new Comparator<JSONObject>() {
                public int compare(JSONObject x, JSONObject y) { return Long.compare(x.optLong("a"), y.optLong("a")); }
            });
            JSONArray arr = new JSONArray();
            for (int i = 0; i < out.size() && i < 8; i++) arr.put(out.get(i));
            c.getSharedPreferences(YukiWidgetProvider.PREFS, 0).edit().putString(YukiWidgetProvider.KEY, arr.toString()).apply();
            YukiWidgetProvider.refresh(c);
        } catch (Exception ex) { }
    }

    /** Network refresh: asks AniList for the next episode of every tracked show, then re-arms alerts and updates the widget. */
    static void refresh(Context c) {
        JSONArray items = items(c);
        if (items.length() == 0) return;
        HttpURLConnection h = null;
        try {
            JSONArray ids = new JSONArray();
            for (int i = 0; i < items.length(); i++) ids.put(items.getJSONObject(i).getLong("id"));
            JSONObject body = new JSONObject();
            body.put("query", "query($ids:[Int]){Page(perPage:50){media(id_in:$ids,type:ANIME){id episodes nextAiringEpisode{airingAt episode}}}}");
            body.put("variables", new JSONObject().put("ids", ids));
            h = (HttpURLConnection) new URL("https://graphql.anilist.co").openConnection();
            h.setRequestMethod("POST");
            h.setConnectTimeout(15000);
            h.setReadTimeout(25000);
            h.setDoOutput(true);
            h.setRequestProperty("Content-Type", "application/json");
            h.setRequestProperty("Accept", "application/json");
            OutputStream os = h.getOutputStream();
            os.write(body.toString().getBytes(StandardCharsets.UTF_8));
            os.close();
            if (h.getResponseCode() != 200) return;
            BufferedReader br = new BufferedReader(new InputStreamReader(h.getInputStream(), StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) sb.append(line);
            br.close();
            JSONArray media = new JSONObject(sb.toString()).getJSONObject("data").getJSONObject("Page").getJSONArray("media");
            Map<Long, JSONObject> byId = new HashMap<Long, JSONObject>();
            for (int i = 0; i < media.length(); i++) {
                JSONObject m = media.getJSONObject(i);
                byId.put(m.getLong("id"), m);
            }
            JSONArray next = new JSONArray();
            for (int i = 0; i < items.length(); i++) {
                JSONObject o = items.getJSONObject(i);
                JSONObject m = byId.get(o.getLong("id"));
                if (m == null) { next.put(o); continue; }
                JSONObject n = m.optJSONObject("nextAiringEpisode");
                if (n == null) continue;
                o.put("at", n.getLong("airingAt") * 1000L);
                o.put("ep", n.getInt("episode"));
                o.put("tot", m.optInt("episodes", 0));
                next.put(o);
            }
            save(c, sp(c).getBoolean("enabled", false), next);
            arm(c);
            pushWidget(c, next);
            sp(c).edit().putLong("last", System.currentTimeMillis()).apply();
        } catch (Exception ex) {
        } finally {
            if (h != null) h.disconnect();
        }
    }
}
'''.replace('__PKG__', PKG))

w(os.path.join(JAVA, 'YukiSyncReceiver.java'), r'''package __PKG__;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Wakes up twice a day, after a reboot and after an app update. */
public class YukiSyncReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(final Context c, Intent i) {
        String a = i == null ? null : i.getAction();
        if (Intent.ACTION_BOOT_COMPLETED.equals(a) || Intent.ACTION_MY_PACKAGE_REPLACED.equals(a)) {
            try { YukiSync.arm(c); } catch (Throwable t) { }
        }
        final PendingResult pr = goAsync();
        new Thread(new Runnable() {
            public void run() {
                try { YukiSync.refresh(c); } catch (Throwable t) { } finally { pr.finish(); }
            }
        }).start();
    }
}
'''.replace('__PKG__', PKG))

w(os.path.join(JAVA, 'YukiNotifyReceiver.java'), r'''package __PKG__;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

/** Shows one episode alert at the exact time set by YukiSync. */
public class YukiNotifyReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context c, Intent i) {
        try {
            String title = i.getStringExtra("title");
            String body = i.getStringExtra("body");
            int code = i.getIntExtra("code", 1);
            NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
            if (Build.VERSION.SDK_INT >= 26) {
                NotificationChannel ch = new NotificationChannel("yuki_airing", "Episode alerts", NotificationManager.IMPORTANCE_HIGH);
                ch.enableVibration(true);
                nm.createNotificationChannel(ch);
            }
            Intent open = c.getPackageManager().getLaunchIntentForPackage(c.getPackageName());
            PendingIntent pi = open == null ? null : PendingIntent.getActivity(c, code, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(c, "yuki_airing") : new Notification.Builder(c);
            b.setSmallIcon(R.drawable.ic_yuki_notify);
            b.setContentTitle(title == null ? "Yuki" : title);
            b.setContentText(body == null ? "" : body);
            b.setStyle(new Notification.BigTextStyle().bigText(body == null ? "" : body));
            b.setAutoCancel(true);
            if (Build.VERSION.SDK_INT < 26) b.setPriority(Notification.PRIORITY_HIGH);
            if (pi != null) b.setContentIntent(pi);
            nm.notify(code, b.build());
        } catch (Throwable t) { }
    }
}
'''.replace('__PKG__', PKG))

w(os.path.join(JAVA, 'YukiSyncPlugin.java'), r'''package __PKG__;

import android.content.Context;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import org.json.JSONArray;

/** The page tells the native side which shows are tracked; the native side keeps alerts and the widget fresh on its own. */
@CapacitorPlugin(name = "YukiSync")
public class YukiSyncPlugin extends Plugin {
    @PluginMethod
    public void configure(PluginCall call) {
        boolean enabled = Boolean.TRUE.equals(call.getBoolean("enabled", false));
        JSONArray items;
        try { items = new JSONArray(call.getString("items", "[]")); } catch (Exception e) { items = new JSONArray(); }
        Context c = getContext();
        YukiSync.save(c, enabled, items);
        YukiSync.arm(c);
        JSObject r = new JSObject();
        r.put("armed", YukiSync.armedCount(c));
        call.resolve(r);
    }

    @PluginMethod
    public void status(PluginCall call) {
        Context c = getContext();
        JSObject r = new JSObject();
        r.put("armed", YukiSync.armedCount(c));
        r.put("last", YukiSync.sp(c).getLong("last", 0));
        r.put("enabled", YukiSync.sp(c).getBoolean("enabled", false));
        r.put("shows", YukiSync.items(c).length());
        call.resolve(r);
    }

    @PluginMethod
    public void syncNow(final PluginCall call) {
        final Context c = getContext();
        new Thread(new Runnable() {
            public void run() {
                try { YukiSync.refresh(c); } catch (Throwable t) { }
                JSObject r = new JSObject();
                r.put("armed", YukiSync.armedCount(c));
                call.resolve(r);
            }
        }).start();
    }
}
'''.replace('__PKG__', PKG))

w(os.path.join(RES, 'drawable', 'ic_yuki_notify.xml'), '''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF" android:pathData="M12,2l2.9,6.9L22,9.6l-5.4,4.8L18.2,22L12,18.1L5.8,22l1.6,-7.6L2,9.6l7.1,-0.7z"/>
</vector>
''')

# ---------- MainActivity: register the plugins ----------
mains = glob.glob(os.path.join(JAVA, 'MainActivity.java')) or glob.glob(os.path.join(APP, 'java', '**', 'MainActivity.java'), recursive=True)
if not mains:
    raise SystemExit('MainActivity.java not found')
p = mains[0]
s = open(p, encoding='utf-8').read()
REG = ['YukiWidgetPlugin', 'YukiFilePlugin', 'YukiSyncPlugin']
if 'registerPlugin(' not in s:
    if 'import android.os.Bundle;' not in s:
        s = re.sub(r'(package [^;]+;)', lambda m: m.group(1) + '\nimport android.os.Bundle;', s, count=1)
    body = """
    @Override
    public void onCreate(Bundle savedInstanceState) {
""" + ''.join('        registerPlugin(%s.class);\n' % r for r in REG) + """        super.onCreate(savedInstanceState);
    }
"""
    if re.search(r'extends BridgeActivity\s*\{\s*\}', s):
        s = re.sub(r'(extends BridgeActivity\s*\{)\s*\}', lambda m: m.group(1) + body + '}', s, count=1)
    else:
        s = re.sub(r'(extends BridgeActivity\s*\{)', lambda m: m.group(1) + body, s, count=1)
else:
    for r in REG:
        if r not in s:
            s = s.replace('super.onCreate(savedInstanceState);', 'registerPlugin(%s.class);\n        super.onCreate(savedInstanceState);' % r, 1)
open(p, 'w', encoding='utf-8').write(s)

# ---------- manifest: receivers + permissions ----------
M = os.path.join(APP, 'AndroidManifest.xml')
m = open(M, encoding='utf-8').read()
# drop the removed Photo frame widget if an older run added it
m = re.sub(r'\s*<receiver android:name="\.YukiPhotoWidgetProvider".*?</receiver>', '', m, flags=re.S)
m = re.sub(r'\s*<activity android:name="\.YukiPhotoPickActivity".*?</activity>', '', m, flags=re.S)
if 'YukiWidgetProvider' not in m:
    rec = '''
        <receiver android:name=".YukiWidgetProvider" android:label="Airing soon" android:exported="true">
            <intent-filter><action android:name="android.appwidget.action.APPWIDGET_UPDATE"/></intent-filter>
            <meta-data android:name="android.appwidget.provider" android:resource="@xml/yuki_widget_info"/>
        </receiver>
'''
    m = m.replace('</application>', rec + '    </application>', 1)
if 'YukiSyncReceiver' not in m:
    rec = '''
        <receiver android:name=".YukiSyncReceiver" android:exported="false">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED"/>
                <action android:name="android.intent.action.MY_PACKAGE_REPLACED"/>
            </intent-filter>
        </receiver>
        <receiver android:name=".YukiNotifyReceiver" android:exported="false"/>
'''
    m = m.replace('</application>', rec + '    </application>', 1)
for perm in ('SCHEDULE_EXACT_ALARM', 'RECEIVE_BOOT_COMPLETED', 'INTERNET'):
    if 'android.permission.' + perm not in m:
        m = m.replace('<application', '<uses-permission android:name="android.permission.%s"/>\n    <application' % perm, 1)
open(M, 'w', encoding='utf-8').write(m)
print('Airing soon widget + file + background sync added for', PKG)
