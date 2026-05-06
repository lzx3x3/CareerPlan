import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

db_path = 'career_planner.db'
print(f"DB path: {os.path.abspath(db_path)}")
print(f"DB exists: {os.path.exists(db_path)}")

conn = sqlite3.connect(db_path)
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cur.fetchall()
table_names = [t[0] for t in tables]
print(f"\nAll tables: {table_names}")

# Check ai_engines table
if 'ai_engines' in table_names:
    print("\n[OK] ai_engines table exists")
    cur = conn.execute("PRAGMA table_info(ai_engines)")
    cols = cur.fetchall()
    print(f"Columns: {[c[1] for c in cols]}")
    cur = conn.execute("SELECT COUNT(*) FROM ai_engines")
    print(f"Row count: {cur.fetchone()[0]}")
else:
    print("\n[FAIL] ai_engines table NOT found!")

# Check user_settings table for active_engine_id column
cur = conn.execute("PRAGMA table_info(user_settings)")
cols = [c[1] for c in cur.fetchall()]
print(f"\nuser_settings columns: {cols}")
if 'active_engine_id' not in cols:
    print("[FAIL] user_settings missing active_engine_id column!")
else:
    print("[OK] user_settings has active_engine_id")

conn.close()
print("\nDone.")
