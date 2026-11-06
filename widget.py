#!/usr/bin/env python3
"""Adds an Android home-screen widget ("Airing soon") to the generated Capacitor project.
Run in the workflow AFTER `npx cap add android` / `cap sync`. Safe to run twice."""
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

# ---------- resources ----------
w(os.path.join(RES, 'drawable', 'yuki_widget_bg.xml'), '''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#E6101224"/>
    <corners android:radius="22dp"/>
    <stroke android:width="1dp" android:color="#338B5CF6"/>
</shape>
''')

rows = ''
for i in (1, 2, 3):
    rows += f'''
    <LinearLayout android:id="@+id/yw_row{i}" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="horizontal" android:layout_marginTop="6dp" android:visibility="gone">
        <TextView android:id="@+id/yw_t{i}" android:layout_width="0dp" android:layout_height="wrap_content" android:layout_weight="1"
            android:textColor="#F4F7FF" android:textSize="14sp" android:singleLine="true" android:ellipsize="end"/>
        <TextView android:id="@+id/yw_d{i}" android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:layout_marginStart="8dp" android:textColor="#C4B5FD" android:textSize="12sp" android:singleLine="true"/>
    </LinearLayout>'''

w(os.path.join(RES, 'layout', 'yuki_widget.xml'), f'''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android" android:id="@+id/yw_root"
    android:layout_width="match_parent" android:layout_height="match_parent" android:orientation="vertical"
    android:padding="14dp" android:background="@drawable/yuki_widget_bg">
    <TextView android:layout_width="match_parent" android:layout_height="wrap_content" android:text="Yuki · Airing soon"
        android:textColor="#A78BFA" android:textSize="12sp" android:textStyle="bold"/>{rows}
    <TextView android:id="@+id/yw_empty" android:layout_width="match_parent" android:layout_height="wrap_content"
        android:layout_marginTop="8dp" android:text="Open Yuki once to load your shows" android:textColor="#9AA0B8" android:textSize="13sp"/>
</LinearLayout>
''')

w(os.path.join(RES, 'xml', 'yuki_widget_info.xml'), '''<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="250dp" android:minHeight="110dp" android:targetCellWidth="4" android:targetCellHeight="2"
    android:updatePeriodMillis="1800000" android:initialLayout="@layout/yuki_widget"
    android:resizeMode="horizontal|vertical" android:widgetCategory="home_screen"/>
''')

# ---------- java ----------
w(os.path.join(JAVA, 'YukiWidgetProvider.java'), f'''package {PKG};

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
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

public class YukiWidgetProvider extends AppWidgetProvider {{
    static final String PREFS = "YukiWidget", KEY = "items";

    @Override
    public void onUpdate(Context c, AppWidgetManager m, int[] ids) {{
        for (int id : ids) m.updateAppWidget(id, build(c));
    }}

    public static void refresh(Context c) {{
        AppWidgetManager m = AppWidgetManager.getInstance(c);
        int[] ids = m.getAppWidgetIds(new ComponentName(c, YukiWidgetProvider.class));
        for (int id : ids) m.updateAppWidget(id, build(c));
    }}

    static String when(long at) {{
        Calendar a = Calendar.getInstance(), b = Calendar.getInstance();
        b.setTimeInMillis(at);
        String t = new SimpleDateFormat("h:mm a", Locale.getDefault()).format(new Date(at));
        if (a.get(Calendar.YEAR) == b.get(Calendar.YEAR) && a.get(Calendar.DAY_OF_YEAR) == b.get(Calendar.DAY_OF_YEAR)) return "Today " + t;
        a.add(Calendar.DAY_OF_YEAR, 1);
        if (a.get(Calendar.YEAR) == b.get(Calendar.YEAR) && a.get(Calendar.DAY_OF_YEAR) == b.get(Calendar.DAY_OF_YEAR)) return "Tomorrow " + t;
        return new SimpleDateFormat("EEE h:mm a", Locale.getDefault()).format(new Date(at));
    }}

    static RemoteViews build(Context c) {{
        RemoteViews v = new RemoteViews(c.getPackageName(), R.layout.yuki_widget);
        int[] rows = {{R.id.yw_row1, R.id.yw_row2, R.id.yw_row3}};
        int[] ts = {{R.id.yw_t1, R.id.yw_t2, R.id.yw_t3}};
        int[] ds = {{R.id.yw_d1, R.id.yw_d2, R.id.yw_d3}};
        List<long[]> idx = new ArrayList<>();
        List<String> names = new ArrayList<>();
        try {{
            String raw = c.getSharedPreferences(PREFS, 0).getString(KEY, "[]");
            JSONArray arr = new JSONArray(raw);
            long now = System.currentTimeMillis();
            for (int i = 0; i < arr.length(); i++) {{
                JSONObject o = arr.getJSONObject(i);
                long at = o.getLong("a");
                if (at > now - 30 * 60 * 1000L) {{
                    idx.add(new long[]{{at, o.optLong("e", 0)}});
                    names.add(o.optString("t", "?"));
                }}
            }}
            // sort by time (simple selection since list is tiny)
            for (int i = 0; i < idx.size(); i++) for (int j = i + 1; j < idx.size(); j++) if (idx.get(j)[0] < idx.get(i)[0]) {{
                Collections.swap(idx, i, j); Collections.swap(names, i, j);
            }}
        }} catch (Exception e) {{ }}
        for (int i = 0; i < 3; i++) {{
            if (i < idx.size()) {{
                long[] it = idx.get(i);
                v.setViewVisibility(rows[i], android.view.View.VISIBLE);
                v.setTextViewText(ts[i], names.get(i) + (it[1] > 0 ? "  ·  Ep " + it[1] : ""));
                v.setTextViewText(ds[i], when(it[0]));
            }} else v.setViewVisibility(rows[i], android.view.View.GONE);
        }}
        v.setViewVisibility(R.id.yw_empty, idx.isEmpty() ? android.view.View.VISIBLE : android.view.View.GONE);
        Intent open = c.getPackageManager().getLaunchIntentForPackage(c.getPackageName());
        if (open != null) {{
            PendingIntent pi = PendingIntent.getActivity(c, 0, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            v.setOnClickPendingIntent(R.id.yw_root, pi);
        }}
        return v;
    }}
}}
''')

w(os.path.join(JAVA, 'YukiWidgetPlugin.java'), f'''package {PKG};

import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "YukiWidget")
public class YukiWidgetPlugin extends Plugin {{
    @PluginMethod
    public void update(PluginCall call) {{
        String items = call.getString("items", "[]");
        getContext().getSharedPreferences(YukiWidgetProvider.PREFS, 0).edit().putString(YukiWidgetProvider.KEY, items).apply();
        YukiWidgetProvider.refresh(getContext());
        call.resolve();
    }}
}}
''')

# ---------- MainActivity: register the plugin ----------
mains = glob.glob(os.path.join(JAVA, 'MainActivity.java')) or glob.glob(os.path.join(APP, 'java', '**', 'MainActivity.java'), recursive=True)
if not mains:
    raise SystemExit('MainActivity.java not found')
p = mains[0]
s = open(p, encoding='utf-8').read()
if 'YukiWidgetPlugin' not in s:
    if 'import android.os.Bundle;' not in s:
        s = re.sub(r'(package [^;]+;)', lambda m: m.group(1) + '\nimport android.os.Bundle;', s, count=1)
    body = """
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(YukiWidgetPlugin.class);
        super.onCreate(savedInstanceState);
    }
"""
    if re.search(r'extends BridgeActivity\s*\{\s*\}', s):
        s = re.sub(r'(extends BridgeActivity\s*\{)\s*\}', lambda m: m.group(1) + body + '}', s, count=1)
    else:
        s = re.sub(r'(extends BridgeActivity\s*\{)', lambda m: m.group(1) + body, s, count=1)
    open(p, 'w', encoding='utf-8').write(s)

# ---------- manifest: receiver ----------
M = os.path.join(APP, 'AndroidManifest.xml')
m = open(M, encoding='utf-8').read()
if 'YukiWidgetProvider' not in m:
    rec = '''
        <receiver android:name=".YukiWidgetProvider" android:exported="true">
            <intent-filter><action android:name="android.appwidget.action.APPWIDGET_UPDATE"/></intent-filter>
            <meta-data android:name="android.appwidget.provider" android:resource="@xml/yuki_widget_info"/>
        </receiver>
'''
    m = m.replace('</application>', rec + '    </application>', 1)
    open(M, 'w', encoding='utf-8').write(m)
print('widget added for', PKG)
