import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

db_path = 'career_planner.db'
conn = sqlite3.connect(db_path)

# Check if column exists
cur = conn.execute("PRAGMA table_info(user_settings)")
cols = [c[1] for c in cur.fetchall()]
print(f"Existing columns: {cols}")

if 'active_engine_id' not in cols:
    print("Adding active_engine_id column...")
    conn.execute("ALTER TABLE user_settings ADD COLUMN active_engine_id INTEGER DEFAULT NULL")
    conn.commit()
    print("Done!")
else:
    print("Column already exists.")

# Verify
cur = conn.execute("PRAGMA table_info(user_settings)")
cols = [c[1] for c in cur.fetchall()]
print(f"Updated columns: {cols}")

conn.close()
