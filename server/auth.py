"""
认证模块 - JWT Token 生成与验证
"""
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g

SECRET_KEY = os.environ.get('JWT_SECRET', 'career_planner_secret_key_2026')
TOKEN_EXPIRE_HOURS = 168  # 7天


def generate_token(user_id: int, username: str) -> str:
    """生成 JWT Token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def verify_token(token: str) -> dict:
    """验证 JWT Token，返回 payload 或 None"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'ok': False, 'msg': '未登录，请先登录'}), 401

        token = auth_header[7:]
        payload = verify_token(token)
        if not payload:
            return jsonify({'ok': False, 'msg': '登录已过期，请重新登录'}), 401

        g.user_id = payload['user_id']
        g.username = payload['username']
        return f(*args, **kwargs)
    return decorated_function
