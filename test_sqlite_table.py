import sqlite3
import os

from gps_server import DB_PATH

# SQLite 데이터베이스 생성
DB_PATH = "gps.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 테이블 생성
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
    provider TEXT)
    """)

conn.commit()
conn.close()
print("SQLite 테이블 생성 완료")
