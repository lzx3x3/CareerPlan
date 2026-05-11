"""
数据库模型 - SQLite
用户表 + 职业规划数据表 + 邮箱验证码表
"""
import sqlite3
import hashlib
import os
import json
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), 'career_planner.db')


def get_db_path():
    return DB_PATH


@contextmanager
def get_db():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _ensure_column(conn, table, column, col_def):
    """如果表 table 没有 column 字段，则执行 ALTER TABLE 添加"""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    names = [r[1] for r in rows]
    if column not in names:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
        print(f"[OK] 已添加字段 {table}.{column}")


def init_db():
    """初始化数据库表结构，并自动补充缺失字段"""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                nickname TEXT,
                avatar TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                last_login TEXT
            );

            CREATE TABLE IF NOT EXISTS email_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                code TEXT NOT NULL,
                purpose TEXT DEFAULT 'login',
                expires_at TEXT NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                ai_api_key TEXT DEFAULT '',
                ai_base_url TEXT DEFAULT '',
                ai_model TEXT DEFAULT '',
                active_engine_id INTEGER DEFAULT NULL,
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ai_engines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                api_key TEXT NOT NULL DEFAULT '',
                base_url TEXT DEFAULT 'https://api.deepseek.com',
                model TEXT DEFAULT 'deepseek-chat',
                is_valid INTEGER DEFAULT 0,
                last_tested_at TEXT,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_ai_engines_user ON ai_engines(user_id);

            CREATE TABLE IF NOT EXISTS career_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                form_data TEXT,
                selected_tags TEXT,
                mbti_result TEXT,
                ai_plan TEXT,
                plan_title TEXT DEFAULT '',
                api_model TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_email_codes_email ON email_codes(email);
            CREATE INDEX IF NOT EXISTS idx_career_plans_user ON career_plans(user_id);
        """)

        # 自动补充已有表中缺失的字段（向前兼容）
        _ensure_column(conn, 'user_settings', 'active_engine_id', 'INTEGER DEFAULT NULL')
        _ensure_column(conn, 'ai_engines', 'name', "TEXT NOT NULL DEFAULT ''")

        print(f"[OK] 数据库初始化完成: {DB_PATH}")


def hash_password(password: str) -> str:
    """密码哈希（SHA-256 + salt）"""
    salt = "career_planner_2026_salt"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash


# ===== 用户操作 =====

def create_user(username: str, password: str, email: str = None, phone: str = None) -> dict:
    """创建用户，返回用户信息字典或 None（用户名已存在）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, email, phone) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), email, phone)
        )
        conn.commit()
        user_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        result = dict(row) if row else None
        conn.close()
        return result
    except sqlite3.IntegrityError as e:
        conn.close()
        print(f"[WARN] User creation failed (integrity): {e}")
        return None
    except Exception as e:
        conn.close()
        print(f"[ERROR] User creation failed: {e}")
        return None


def get_user_by_username(username: str) -> dict:
    """通过用户名查找用户"""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> dict:
    """通过邮箱查找用户"""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict:
    """通过 ID 查找用户"""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def update_user_login(user_id: int):
    """更新最后登录时间"""
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET last_login = datetime('now','localtime') WHERE id = ?",
            (user_id,)
        )


def update_user_profile(user_id: int, nickname: str = None, avatar: str = None):
    """更新用户资料"""
    with get_db() as conn:
        if nickname is not None:
            conn.execute("UPDATE users SET nickname = ? WHERE id = ?", (nickname, user_id))
        if avatar is not None:
            conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar, user_id))


# ===== 邮箱验证码 =====

def create_email_code(email: str, purpose: str = 'login') -> str:
    """生成6位验证码，存入数据库，返回验证码"""
    import random
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    expires_at = datetime.now() + timedelta(minutes=10)

    with get_db() as conn:
        # 将同一邮箱之前的未使用验证码标记为已使用
        conn.execute(
            "UPDATE email_codes SET used = 1 WHERE email = ? AND used = 0",
            (email,)
        )
        conn.execute(
            "INSERT INTO email_codes (email, code, purpose, expires_at) VALUES (?, ?, ?, ?)",
            (email, code, purpose, expires_at.strftime('%Y-%m-%d %H:%M:%S'))
        )
    return code


def verify_email_code(email: str, code: str, purpose: str = 'login') -> bool:
    """验证邮箱验证码"""
    with get_db() as conn:
        row = conn.execute(
            """SELECT * FROM email_codes
               WHERE email = ? AND code = ? AND purpose = ? AND used = 0
               AND expires_at > datetime('now','localtime')
               ORDER BY created_at DESC LIMIT 1""",
            (email, code, purpose)
        ).fetchone()
        if row:
            conn.execute("UPDATE email_codes SET used = 1 WHERE id = ?", (row['id'],))
            return True
        return False


# ===== 职业规划数据 =====

def save_career_plan(user_id: int, form_data: dict, selected_tags: dict,
                     mbti_result: dict = None, ai_plan: str = None,
                     plan_title: str = '', api_model: str = '') -> int:
    """保存/更新职业规划，返回 plan id"""
    with get_db() as conn:
        # 检查是否已有规划
        existing = conn.execute(
            "SELECT id FROM career_plans WHERE user_id = ?", (user_id,)
        ).fetchone()

        form_json = json.dumps(form_data, ensure_ascii=False)
        tags_json = json.dumps(selected_tags, ensure_ascii=False)
        mbti_json = json.dumps(mbti_result, ensure_ascii=False) if mbti_result else None
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if existing:
            if ai_plan is None:
                # 草稿暂存：不覆盖已有的 AI 规划
                conn.execute(
                    """UPDATE career_plans SET
                       form_data=?, selected_tags=?, mbti_result=?,
                       plan_title=?, api_model=?, updated_at=?
                       WHERE user_id = ?""",
                    (form_json, tags_json, mbti_json, plan_title, api_model, now, user_id)
                )
            else:
                conn.execute(
                    """UPDATE career_plans SET
                       form_data=?, selected_tags=?, mbti_result=?, ai_plan=?,
                       plan_title=?, api_model=?, updated_at=?
                       WHERE user_id = ?""",
                    (form_json, tags_json, mbti_json, ai_plan, plan_title, api_model, now, user_id)
                )
            return existing['id']
        else:
            cursor = conn.execute(
                """INSERT INTO career_plans
                   (user_id, form_data, selected_tags, mbti_result, ai_plan, plan_title, api_model)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, form_json, tags_json, mbti_json, ai_plan, plan_title, api_model)
            )
            return cursor.lastrowid


def get_career_plan(user_id: int) -> dict:
    """获取用户的职业规划数据"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM career_plans WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row:
            data = dict(row)
            data['form_data'] = json.loads(data['form_data']) if data['form_data'] else {}
            data['selected_tags'] = json.loads(data['selected_tags']) if data['selected_tags'] else {}
            data['mbti_result'] = json.loads(data['mbti_result']) if data['mbti_result'] else None
            return data
        return None


# ===== 用户设置（API Key 等） =====

def save_user_settings(user_id: int, ai_api_key: str = None, ai_base_url: str = None, ai_model: str = None) -> int:
    """保存/更新用户设置，返回设置 id"""
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM user_settings WHERE user_id = ?", (user_id,)
        ).fetchone()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if existing:
            if ai_api_key is not None:
                conn.execute("UPDATE user_settings SET ai_api_key=?, updated_at=? WHERE user_id=?",
                             (ai_api_key, now, user_id))
            if ai_base_url is not None:
                conn.execute("UPDATE user_settings SET ai_base_url=?, updated_at=? WHERE user_id=?",
                             (ai_base_url, now, user_id))
            if ai_model is not None:
                conn.execute("UPDATE user_settings SET ai_model=?, updated_at=? WHERE user_id=?",
                             (ai_model, now, user_id))
            return existing['id']
        else:
            cursor = conn.execute(
                "INSERT INTO user_settings (user_id, ai_api_key, ai_base_url, ai_model) VALUES (?,?,?,?)",
                (user_id, ai_api_key or '', ai_base_url or '', ai_model or '')
            )
            return cursor.lastrowid


def get_user_settings(user_id: int) -> dict:
    """获取用户设置"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM user_settings WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def set_active_engine(user_id: int, engine_id: int = None):
    """设置用户当前激活的 AI 引擎"""
    with get_db() as conn:
        # 确保 user_settings 行存在
        existing = conn.execute(
            "SELECT id FROM user_settings WHERE user_id = ?", (user_id,)
        ).fetchone()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not existing:
            conn.execute(
                "INSERT INTO user_settings (user_id, active_engine_id, updated_at) VALUES (?, ?, ?)",
                (user_id, engine_id, now)
            )
        else:
            conn.execute(
                "UPDATE user_settings SET active_engine_id=?, updated_at=? WHERE user_id=?",
                (engine_id, now, user_id)
            )


def get_active_engine(user_id: int) -> dict:
    """获取用户当前激活的 AI 引擎配置"""
    settings = get_user_settings(user_id)
    if not settings or not settings.get('active_engine_id'):
        return None
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM ai_engines WHERE id = ? AND user_id = ?",
            (settings['active_engine_id'], user_id)
        ).fetchone()
        return dict(row) if row else None


# ===== AI 引擎管理 =====

def add_ai_engine(user_id: int, name: str, api_key: str, base_url: str = 'https://api.deepseek.com',
                  model: str = 'deepseek-chat') -> int:
    """添加一个 AI 引擎，返回引擎 id"""
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO ai_engines (user_id, name, api_key, base_url, model)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, name or '未命名引擎', api_key, base_url or 'https://api.deepseek.com', model or 'deepseek-chat')
        )
        return cursor.lastrowid


def update_ai_engine(engine_id: int, user_id: int, name: str = None, api_key: str = None,
                     base_url: str = None, model: str = None, is_valid: bool = None):
    """更新 AI 引擎配置"""
    with get_db() as conn:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if name is not None:
            conn.execute("UPDATE ai_engines SET name=?, updated_at=? WHERE id=? AND user_id=?",
                         (name, now, engine_id, user_id))
        if api_key is not None:
            conn.execute("UPDATE ai_engines SET api_key=?, updated_at=? WHERE id=? AND user_id=?",
                         (api_key, now, engine_id, user_id))
        if base_url is not None:
            conn.execute("UPDATE ai_engines SET base_url=?, updated_at=? WHERE id=? AND user_id=?",
                         (base_url, now, engine_id, user_id))
        if model is not None:
            conn.execute("UPDATE ai_engines SET model=?, updated_at=? WHERE id=? AND user_id=?",
                         (model, now, engine_id, user_id))
        if is_valid is not None:
            conn.execute("UPDATE ai_engines SET is_valid=?, last_tested_at=? WHERE id=? AND user_id=?",
                         (1 if is_valid else 0, now, engine_id, user_id))


def delete_ai_engine(engine_id: int, user_id: int) -> bool:
    """删除 AI 引擎，返回是否成功"""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM ai_engines WHERE id = ? AND user_id = ?", (engine_id, user_id)
        )
        # 如果删除的是当前激活的引擎，清空 active_engine_id
        if cursor.rowcount > 0:
            settings = get_user_settings(user_id)
            if settings and settings.get('active_engine_id') == engine_id:
                conn.execute(
                    "UPDATE user_settings SET active_engine_id = NULL WHERE user_id = ?", (user_id,)
                )
        return cursor.rowcount > 0


def get_ai_engines(user_id: int) -> list:
    """获取用户所有 AI 引擎列表（不含完整 api_key）"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM ai_engines WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            # 隐藏 Key 中间部分
            key = d.get('api_key', '')
            if key and len(key) > 8:
                d['masked_key'] = key[:4] + '****' + key[-4:]
            else:
                d['masked_key'] = '****'
            # 不返回完整 key
            d.pop('api_key', None)
            result.append(d)
        return result


def get_ai_engine_full(engine_id: int, user_id: int) -> dict:
    """获取引擎完整配置（含 api_key），仅供服务端内部调用"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM ai_engines WHERE id = ? AND user_id = ?",
            (engine_id, user_id)
        ).fetchone()
        return dict(row) if row else None
