# gps_server.py
from flask import Flask, request, jsonify, send_file, Response
from datetime import timedelta, timezone, datetime
from zoneinfo import ZoneInfo
import os, math, io, json, html
from pathlib import Path
from urllib.parse import urlparse

# 환경변수 기반 설정
BASE_DIR = Path(__file__).resolve().parent
APP_PORT = int(os.getenv('PORT', 5000))
KST = ZoneInfo("Asia/Seoul")

# 데이터베이스 설정 (PostgreSQL 또는 SQLite)
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # Railway PostgreSQL
    try:
        import psycopg2
        import psycopg2.extras
        result = urlparse(DATABASE_URL)
        DB_CONFIG = {
            'host': result.hostname,
            'port': result.port,
            'database': result.path[1:],
            'user': result.username,
            'password': result.password
        }
        DB_TYPE = 'postgresql'
    except ImportError:
        print("[WARNING] psycopg2 not installed, falling back to SQLite")
        DB_PATH = str(BASE_DIR / "gps.db")
        DB_TYPE = 'sqlite'
        import sqlite3
else:
    # 로컬 SQLite
    DB_PATH = str(BASE_DIR / "gps.db")
    DB_TYPE = 'sqlite'
    import sqlite3

app = Flask(__name__)


# ---------------------- DB ----------------------
def get_db_connection():
    if DB_TYPE == 'postgresql':
        try:
            return psycopg2.connect(**DB_CONFIG)
        except Exception as e:
            print(f"[ERROR] PostgreSQL connection failed: {e}")
            print("[INFO] Falling back to SQLite")
            return sqlite3.connect(DB_PATH)
    else:
        return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    if DB_TYPE == 'postgresql':
        c.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id SERIAL PRIMARY KEY,
            device_id TEXT,
            ts_utc TEXT,
            ts_kst TEXT,
            lat REAL,
            lon REAL,
            accuracy REAL,
            speed REAL,
            battery REAL,
            provider TEXT
        )
        """)
    else:
        c.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            ts_utc TEXT,
            ts_kst TEXT,
            lat REAL,
            lon REAL,
            accuracy REAL,
            speed REAL,
            battery REAL,
            provider TEXT
        )
        """)
    conn.commit()
    conn.close()

def store_point(device_id, dt_utc, lat, lon, accuracy=None, speed=None, battery=None, provider=None):
    ts_utc_iso = dt_utc.isoformat(timespec="seconds")
    ts_kst_iso = dt_utc.astimezone(KST).isoformat(timespec="seconds")
    conn = get_db_connection()
    c = conn.cursor()
    
    if DB_TYPE == 'postgresql':
        c.execute("""
        INSERT INTO locations (device_id, ts_utc, ts_kst, lat, lon, accuracy, speed, battery, provider)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (device_id, ts_utc_iso, ts_kst_iso, lat, lon, accuracy, speed, battery, provider))
    else:
        c.execute("""
        INSERT INTO locations (device_id, ts_utc, ts_kst, lat, lon, accuracy, speed, battery, provider)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (device_id, ts_utc_iso, ts_kst_iso, lat, lon, accuracy, speed, battery, provider))
    
    conn.commit()
    conn.close()

# -------------------- Helpers -------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0  # meters
    to_rad = math.pi / 180.0
    dlat = (lat2 - lat1) * to_rad
    dlon = (lon2 - lon1) * to_rad
    a = (math.sin(dlat/2)**2
         + math.cos(lat1 * to_rad) * math.cos(lat2 * to_rad) * math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ---------------------- Routes ----------------------
@app.route("/")
def hello():
    return "GPS Logger Server is running. POST /api/loc or /owntracks, view /map or /map2"

@app.route("/api/loc", methods=["POST"])
def receive_generic():
    data = request.get_json(force=True, silent=True) or {}
    try:
        lat = float(data.get("lat", "nan"))
        lon = float(data.get("lon", "nan"))
    except Exception:
        return jsonify({"ok": False, "error": "lat/lon missing"}), 400
    if any(map(math.isnan, [lat, lon])):
        return jsonify({"ok": False, "error": "lat/lon missing"}), 400

    device_id = str(data.get("device_id", "unknown"))
    accuracy = float(data["accuracy"]) if "accuracy" in data and data["accuracy"] is not None else None
    speed = float(data["speed"]) if "speed" in data and data["speed"] is not None else None
    battery = float(data["battery"]) if "battery" in data and data["battery"] is not None else None
    provider = str(data.get("provider", "")) if data.get("provider") is not None else None

    ts_utc = data.get("ts")
    if ts_utc:
        try:
            dt = datetime.fromisoformat(ts_utc.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)

    store_point(device_id, dt, lat, lon, accuracy, speed, battery, provider or "api")
    return jsonify({"ok": True})

@app.route("/owntracks", methods=["POST", "GET"])
def receive_owntracks():
    if request.method == "GET":
        return jsonify({"ok": True, "hint": "POST a OwnTracks JSON here"}), 200

    data = request.get_json(force=True, silent=True) or {}
    if data.get("_type") != "location":
        return jsonify({"ok": False, "error": "not a location payload"}), 400

    try:
        lat = float(data["lat"])
        lon = float(data["lon"])
    except Exception:
        return jsonify({"ok": False, "error": "invalid lat/lon"}), 400

    device_id = str(data.get("tid", "owntracks"))
    accuracy = float(data["acc"]) if "acc" in data and data["acc"] is not None else None
    speed = float(data["vel"]) if "vel" in data and data["vel"] is not None else None
    battery = float(data["batt"]) if "batt" in data and data["batt"] is not None else None

    tst = data.get("tst")
    if tst is not None:
        try:
            dt = datetime.fromtimestamp(int(tst), tz=timezone.utc)
        except Exception:
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)

    store_point(device_id, dt, lat, lon, accuracy, speed, battery, "owntracks")
    return jsonify({"ok": True})

@app.route("/pub", methods=["POST"])
def receive_owntracks_pub():
    # Accept OwnTracks default /pub endpoint
    return receive_owntracks()

@app.route("/map")
def serve_map():
    # Folium map with robust guards
    import folium
    try:
        days = int(request.args.get("days", 7))
    except Exception:
        days = 7

    # all=1이면 기간 필터 없이 전체 출력
    no_filter = str(request.args.get("all", "")).lower() in ("1", "true", "yes")

    conn = get_db_connection()
    c = conn.cursor()
    if no_filter:
        c.execute("""
            SELECT ts_kst, lat, lon
            FROM locations
            ORDER BY ts_utc ASC
        """)
    else:
        # 파이썬에서 UTC 기준 커트오프를 ISO8601(+00:00)로 만들어 비교
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")
        if DB_TYPE == 'postgresql':
            c.execute("""
                SELECT ts_kst, lat, lon
                FROM locations
                WHERE ts_utc >= %s
                ORDER BY ts_utc ASC
            """, (cutoff,))
        else:
            c.execute("""
                SELECT ts_kst, lat, lon
                FROM locations
                WHERE ts_utc >= ?
                ORDER BY ts_utc ASC
            """, (cutoff,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return (
            "데이터가 없습니다. 먼저 앱에서 위치를 보내보세요. "
            f"(POST /api/loc 또는 /owntracks) TIP: /map?days={days} 로 기간 조정"
        ), 200

    path = []
    for _, lat, lon in rows:
        try:
            path.append([float(lat), float(lon)])
        except Exception:
            continue

    if not path:
        return "좌표가 올바르지 않아 지도를 생성할 수 없습니다.", 200

    m = folium.Map(location=path[0], zoom_start=14)

    if len(path) >= 2:
        folium.PolyLine(path, weight=5, opacity=0.8).add_to(m)

    start_time = rows[0][0]
    end_time = rows[-1][0]
    folium.Marker(path[0], tooltip=f"시작 {start_time}").add_to(m)
    folium.Marker(path[-1], tooltip=f"끝 {end_time}").add_to(m)

    dist_m = 0.0
    for i in range(1, len(path)):
        lat1, lon1 = path[i-1]
        lat2, lon2 = path[i]
        dist_m += haversine(lat1, lon1, lat2, lon2)
    dist_km = round(dist_m/1000, 2)

    folium.map.Marker(
        location=path[0],
        icon=folium.DivIcon(html=f"""
        <div style="background:white;padding:8px;border:1px solid #ccc;border-radius:8px; font-size:12px;">
          <b>요약</b><br/>
          기간: 최근 {days}일<br/>
          포인트: {len(path)}개<br/>
          총 이동거리: {dist_km} km
        </div>""")
    ).add_to(m)

    out_html = "map.html"
    try:
        m.save(out_html)
        return send_file(out_html)
    except Exception:
        # Fallback to memory
        html_io = io.BytesIO(m.get_root().render().encode("utf-8"))
        return send_file(html_io, mimetype="text/html", download_name="map.html")

@app.route("/map2")
def serve_map_leaflet():
    #days parameter

    try:
        days = int(request.args.get("days", 7))
    except Exception:
        days = 7

    
    #DB 조회
    conn = get_db_connection()
    c = conn.cursor()
    # 현재 시간에서 days일 전의 ISO 형식 시간 계산
    from datetime import datetime, timedelta, timezone
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_iso = cutoff_time.isoformat(timespec="seconds")
    
    if DB_TYPE == 'postgresql':
        c.execute("""
                  SELECT ts_kst, lat, lon
                  FROM locations
                  WHERE ts_utc >= %s
                  ORDER BY ts_utc ASC
                  """, (cutoff_iso,))
    else:
        c.execute("""
                  SELECT ts_kst, lat, lon
                  FROM locations
                  WHERE ts_utc >= ?
                  ORDER BY ts_utc ASC
                  """, (cutoff_iso,))
    rows = c.fetchall()
    conn.close()
    
    if not rows: 
        return Response("<h3>데이터가 존재하지 않습니다</h3>", mimetype="text/html; charset=utf-8")
    
    # 좌표 정리
    points =[]
    for ts, lat, lon in rows:
        try:
            points.append({"ts":ts, "lat":float(lat), "lon": float(lon)})
        except Exception:
            pass

    if not points:
        return Response("<h3>유효한 좌표가 존재하지 않습니다.</h3>", mimetype="text/html; charset=utf-8")

    #치환용 값
    pts_json = json.dumps(points, ensure_ascii=False)
    start_ts = html.escape(points[0]["ts"])
    end_ts = html.escape(points[-1]["ts"])

    # ★ f-string 아님: 특수 토큰으로 치환
    html_doc = r"""<!doctype html>

<html>
<head>
<meta charset="utf-8"/>
<title>GPS Map (Leaflet)</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#map{height:100%;margin:0}</style>
</head>
<body>
<div id="map"></div>
<script>
  const pts = __PTS__;
  const map = L.map('map').setView([pts[0].lat, pts[0].lon], 14);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
              {maxZoom: 19, attribution: '&copy; OpenStreetMap'}).addTo(map);

  const latlngs = pts.map(p => [p.lat, p.lon]);
  if (latlngs.length >= 2) L.polyline(latlngs, {weight:5}).addTo(map);

  L.marker([pts[0].lat, pts[0].lon]).addTo(map).bindTooltip("시작: __START__");
  L.marker([pts[pts.length-1].lat, pts[pts.length-1].lon]).addTo(map).bindTooltip("끝: __END__");

  function haversine(a,b,c,d){
    const R=6371000,toRad=Math.PI/180;
    const d1=(c-a)*toRad, d2=(d-b)*toRad;
    const x=Math.sin(d1/2)**2 + Math.cos(a*toRad)*Math.cos(c*toRad)*Math.sin(d2/2)**2;
    return 2*R*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));
  }
  let dist=0;
  for(let i=1;i<latlngs.length;i++)
    dist+=haversine(latlngs[i-1][0],latlngs[i-1][1],latlngs[i][0],latlngs[i][1]);

  const box = L.control({position:'topleft'});
  box.onAdd = function(){
    const div = L.DomUtil.create('div');
    div.style.background='#fff';
    div.style.padding='8px';
    div.style.border='1px solid #ccc';
    div.style.borderRadius='8px';
    div.style.fontSize='12px';
    div.innerHTML = `<b>요약</b><br/>기간: 최근 __DAYS__일<br/>포인트: ${latlngs.length}개<br/>총 이동거리: ${(dist/1000).toFixed(2)} km`;
    return div;
  };
  box.addTo(map);
</script>
</body>
</html>"""

    #토큰 치환
    html_doc = (html_doc
                .replace("__PTS__", pts_json)
                .replace("__START__", start_ts)
                .replace("__END__", end_ts)
                .replace("__DAYS__", str(days))
                )
    return Response(html_doc, mimetype="text/html; charset=utf-8")

@app.route("/export.csv")
def export_csv():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
    SELECT device_id, ts_utc, ts_kst, lat, lon, accuracy, speed, battery, provider
    FROM locations
    ORDER BY ts_utc ASC
    """)
    rows = c.fetchall()
    conn.close()

    csv_lines = ["device_id,ts_utc,ts_kst,lat,lon,accuracy,speed,battery,provider"]
    for r in rows:
        csv_lines.append(",".join("" if v is None else str(v) for v in r))
    csv_text = "\n".join(csv_lines)

    return Response(
        csv_text,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=gps_export.csv"}
    )

@app.route("/last")
def last_points():
    try:
        n = int(request.args.get("n", 10))
    except Exception:
        n = 10
    conn = get_db_connection()
    c = conn.cursor()
    
    if DB_TYPE == 'postgresql':
        c.execute("""
            SELECT device_id, ts_kst, lat, lon, accuracy, speed, battery, provider
            FROM locations ORDER BY id DESC LIMIT %s
        """, (n,))
    else:
        c.execute("""
            SELECT device_id, ts_kst, lat, lon, accuracy, speed, battery, provider
            FROM locations ORDER BY id DESC LIMIT ?
        """, (n,))
    rows = c.fetchall()
    conn.close()
    
    cols = ["device_id","ts_kst","lat","lon","accuracy","speed","battery","provider"]
    return jsonify({"count": len(rows), "rows": [dict(zip(cols, r)) for r in rows]})

if __name__ == "__main__":
    import os, time, traceback
    try:
        # 새 DB 생성
        init_db()
    except Exception as e:
        if DB_TYPE == 'sqlite' and "malformed" in str(e).lower():
            # SQLite 손상 감지되면 자동 백업 후 재생성
            bak = f"gps_corrupt_{time.strftime('%Y%m%d_%H%M%S')}.db"
            try: os.replace(DB_PATH, bak)
            except: pass
            init_db()
        else:
            raise
    
    print("[INFO] CWD =", os.getcwd())
    print("[INFO] DB_TYPE =", DB_TYPE)
    if DB_TYPE == 'sqlite':
        print("[INFO] DB  =", os.path.abspath(DB_PATH))
    else:
        print("[INFO] DB  =", DATABASE_URL.split('@')[1] if DATABASE_URL else "Not configured")
    print("[INFO] Routes:", [str(r) for r in app.url_map.iter_rules()])
    app.run(host="0.0.0.0", port=APP_PORT, debug=True, use_reloader=False)

