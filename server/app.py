"""
职画 - Flask 后端主应用
提供用户认证、数据存储、AI 代理等 API
"""
import os
import re
import json
import secrets
from flask import Flask, request, jsonify, send_from_directory, send_file, g
from flask_cors import CORS

from models import (
    init_db, create_user, get_user_by_username, get_user_by_email,
    get_user_by_id, verify_password, update_user_login, update_user_profile,
    create_email_code, verify_email_code,
    save_career_plan, get_career_plan,
    save_user_settings, get_user_settings,
    add_ai_engine, update_ai_engine, delete_ai_engine, get_ai_engines,
    get_active_engine, set_active_engine, get_ai_engine_full
)
from auth import generate_token, login_required
from email_sender import email_sender
from company_links import get_company_links, get_gwy_links, parse_companies_from_ai_plan

# ===== Flask 应用初始化 =====
app = Flask(__name__, static_folder=None)
CORS(app, supports_credentials=True)

# 配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DeepSeek AI 配置（服务端统一管理）
AI_CONFIG = {
    'api_key': os.environ.get('DEEPSEEK_API_KEY', ''),
    'base_url': os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
    'model': os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat'),
}


# ===== 静态文件服务 =====

@app.route('/')
def serve_index():
    """提供前端主页面"""
    html_path = os.path.join(BASE_DIR, 'career-planner.html')
    if os.path.exists(html_path):
        return send_file(html_path)
    return '前端文件不存在，请确保 career-planner.html 在项目根目录', 404


@app.route('/<path:path>')
def serve_static(path):
    """提供静态文件"""
    file_path = os.path.join(BASE_DIR, path)
    if os.path.isfile(file_path):
        return send_file(file_path)
    return f'文件未找到: {path}', 404


# ===== 注册/登录 API =====

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册（用户名 + 密码 + 可选邮箱）"""
    try:
        data = request.get_json()
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        email = (data.get('email') or '').strip() or None

        # 参数校验
        if not username or not password:
            return jsonify({'ok': False, 'msg': '用户名和密码不能为空'}), 400

        if len(username) < 3 or len(username) > 20:
            return jsonify({'ok': False, 'msg': '用户名长度3-20个字符'}), 400

        if len(password) < 6:
            return jsonify({'ok': False, 'msg': '密码长度至少6位'}), 400

        if email and not re.match(r'^[\w.-]+@[\w.-]+\.\w+$', email):
            return jsonify({'ok': False, 'msg': '邮箱格式不正确'}), 400

        # 检查用户名是否已存在
        if get_user_by_username(username):
            return jsonify({'ok': False, 'msg': '用户名已被注册'}), 409

        # 检查邮箱是否已被使用
        if email and get_user_by_email(email):
            return jsonify({'ok': False, 'msg': '该邮箱已被注册'}), 409

        # 创建用户
        user = create_user(username, password, email=email)
        if not user:
            return jsonify({'ok': False, 'msg': '注册失败，请稍后重试'}), 500

        # 生成 Token
        token = generate_token(user['id'], user['username'])
        update_user_login(user['id'])

        return jsonify({
            'ok': True,
            'msg': '注册成功！',
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'nickname': user['nickname'],
                'avatar': user['avatar']
            }
        })
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'服务器错误: {str(e)}'}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """用户登录（用户名 + 密码）"""
    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"[LOGIN ERROR] JSON 解析失败: {e}")
        return jsonify({'ok': False, 'msg': '请求数据格式错误，请确保发送的是 JSON 格式'}), 400

    if not data:
        return jsonify({'ok': False, 'msg': '请求数据为空'}), 400

    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    print(f"[LOGIN] 尝试登录: username={username}")

    if not username or not password:
        return jsonify({'ok': False, 'msg': '用户名和密码不能为空'}), 400

    user = get_user_by_username(username)
    if not user:
        print(f"[LOGIN FAIL] 用户不存在: {username}")
        return jsonify({'ok': False, 'msg': '用户名或密码错误'}), 401

    print(f"[LOGIN] 用户找到: {username}, 验证密码...")
    pwd_ok = verify_password(password, user['password_hash'])
    print(f"[LOGIN] 密码验证结果: {pwd_ok}, 输入密码长度: {len(password)}")

    if not pwd_ok:
        return jsonify({'ok': False, 'msg': '用户名或密码错误'}), 401

    # 生成 Token
    token = generate_token(user['id'], user['username'])
    update_user_login(user['id'])

    print(f"[LOGIN] 登录成功: {username}")

    return jsonify({
        'ok': True,
        'msg': '登录成功！',
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'nickname': user['nickname'],
            'avatar': user['avatar']
        }
    })


@app.route('/api/send-email-code', methods=['POST'])
def send_email_code():
    """发送邮箱验证码"""
    data = request.get_json()
    email = (data.get('email') or '').strip()
    purpose = (data.get('purpose') or 'login').strip()  # login 或 register

    if not email or not re.match(r'^[\w.-]+@[\w.-]+\.\w+$', email):
        return jsonify({'ok': False, 'msg': '邮箱格式不正确'}), 400

    # 限流检查：同一邮箱60秒内只能发送一次
    from models import get_db
    with get_db() as conn:
        recent = conn.execute(
            """SELECT id FROM email_codes
               WHERE email = ? AND created_at > datetime('now','localtime','-60 seconds')
               ORDER BY created_at DESC LIMIT 1""",
            (email,)
        ).fetchone()
        if recent:
            return jsonify({'ok': False, 'msg': '发送太频繁，请60秒后重试'}), 429

    # 生成验证码
    code = create_email_code(email, purpose)

    # 发送邮件
    success = email_sender.send_code(email, code)
    if not success and email_sender.enabled:
        return jsonify({'ok': False, 'msg': '邮件发送失败，请稍后重试'}), 500

    return jsonify({
        'ok': True,
        'msg': '验证码已发送' if email_sender.enabled else '验证码已生成（邮件服务未配置，请查看服务端日志）',
        'dev_code': code if not email_sender.enabled else None  # 开发模式返回验证码
    })


@app.route('/api/login-by-email', methods=['POST'])
def login_by_email():
    """通过邮箱 + 验证码登录/注册"""
    data = request.get_json()
    email = (data.get('email') or '').strip()
    code = (data.get('code') or '').strip()

    if not email or not code:
        return jsonify({'ok': False, 'msg': '邮箱和验证码不能为空'}), 400

    # 验证验证码
    if not verify_email_code(email, code, 'login'):
        return jsonify({'ok': False, 'msg': '验证码错误或已过期'}), 400

    # 查找或创建用户
    user = get_user_by_email(email)
    if not user:
        # 自动创建账号（邮箱登录时如果用户不存在则注册）
        import uuid
        username = email.split('@')[0]
        # 确保用户名唯一
        base_username = username
        counter = 1
        while get_user_by_username(username):
            username = f"{base_username}_{counter}"
            counter += 1

        random_password = secrets.token_urlsafe(16)
        user = create_user(username, random_password, email=email)
        if not user:
            return jsonify({'ok': False, 'msg': '自动注册失败，请使用用户名注册'}), 500

    # 生成 Token
    token = generate_token(user['id'], user['username'])
    update_user_login(user['id'])

    return jsonify({
        'ok': True,
        'msg': '登录成功！',
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'nickname': user['nickname'],
            'avatar': user['avatar']
        }
    })


# ===== 用户信息 API =====

@app.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    """获取当前用户信息"""
    user = get_user_by_id(g.user_id)
    if not user:
        return jsonify({'ok': False, 'msg': '用户不存在'}), 404

    return jsonify({
        'ok': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'phone': user['phone'],
            'nickname': user['nickname'],
            'avatar': user['avatar'],
            'created_at': user['created_at']
        }
    })


@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新用户资料"""
    data = request.get_json()
    nickname = data.get('nickname')
    avatar = data.get('avatar')

    update_user_profile(g.user_id, nickname=nickname, avatar=avatar)

    return jsonify({'ok': True, 'msg': '资料更新成功'})


# ===== 职业规划数据 API =====

@app.route('/api/plan', methods=['GET'])
@login_required
def get_plan():
    """获取当前用户的职业规划"""
    plan = get_career_plan(g.user_id)
    if plan:
        return jsonify({'ok': True, 'plan': plan})
    return jsonify({'ok': True, 'plan': None})


@app.route('/api/plan', methods=['POST'])
@login_required
def save_plan():
    """保存/更新职业规划"""
    data = request.get_json()
    form_data = data.get('form_data', {})
    selected_tags = data.get('selected_tags', {})
    mbti_result = data.get('mbti_result')
    ai_plan = data.get('ai_plan')
    plan_title = data.get('plan_title', '')
    api_model = data.get('api_model', '')

    plan_id = save_career_plan(
        user_id=g.user_id,
        form_data=form_data,
        selected_tags=selected_tags,
        mbti_result=mbti_result,
        ai_plan=ai_plan,
        plan_title=plan_title,
        api_model=api_model
    )

    return jsonify({'ok': True, 'msg': '保存成功', 'plan_id': plan_id})


# ===== AI 代理 API =====

@app.route('/api/ai/generate', methods=['POST'])
@login_required
def ai_generate():
    """服务端代理 AI 生成请求（服务端 Key 优先，其次用用户自定义 Key）"""
    data = request.get_json()
    system_prompt = data.get('system_prompt', '')
    user_message = data.get('user_message', '')

    if not user_message:
        return jsonify({'ok': False, 'msg': '生成内容不能为空'}), 400

    # 确定使用哪个 API Key：优先级：用户当前激活引擎 > 服务端环境变量 > 旧 user_settings 兼容
    api_key = ''
    base_url = AI_CONFIG['base_url']
    model = AI_CONFIG['model']
    key_source = ''
    
    # 1. 先检查用户当前激活的引擎
    engine = get_active_engine(g.user_id)
    if engine and engine.get('api_key'):
        api_key = engine['api_key']
        base_url = (engine.get('base_url', base_url) or base_url).rstrip('/')
        model = engine.get('model', model)
        key_source = 'user'
    else:
        # 2. 再检查服务端环境变量
        api_key = AI_CONFIG['api_key']
        if api_key:
            key_source = 'server'
        else:
            # 3. 最后兼容旧 user_settings
            settings = get_user_settings(g.user_id)
            if settings and settings.get('ai_api_key'):
                api_key = settings['ai_api_key']
                if settings.get('ai_base_url'):
                    base_url = settings['ai_base_url'].rstrip('/')
                if settings.get('ai_model'):
                    model = settings['ai_model']
                key_source = 'user'

    if not api_key:
        return jsonify({'ok': False, 'msg': '服务端未配置 AI API Key，请在下方配置你自己的 Key'}), 400

    # 统一去除末尾斜杠，防止双斜杠
    base_url = base_url.rstrip('/')

    try:
        import urllib.request
        import ssl

        # 构建 API 请求
        api_url = f"{base_url}/chat/completions"
        payload = json.dumps({
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt} if system_prompt else {},
                {'role': 'user', 'content': user_message}
            ],
            'temperature': 0.7,
            'max_tokens': 4096,
            'stream': False
        }).encode('utf-8')

        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {api_key}"
            }
        )

        # 非流式返回（Flask dev server 下流式响应不稳定）
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                return jsonify({'ok': True, 'content': content, 'model': model})
        except Exception as e:
            return jsonify({'ok': False, 'msg': f'AI 生成失败: {str(e)}'}), 500

    except Exception as e:
        return jsonify({'ok': False, 'msg': f'AI 生成失败: {str(e)}'}), 500


@app.route('/api/ai/test', methods=['POST'])
@login_required
def ai_test():
    """测试 AI 连通性（用户当前激活引擎优先，其次服务端 Key）"""
    api_key = ''
    base_url = AI_CONFIG['base_url']
    model = AI_CONFIG['model']

    # 1. 先检查用户当前激活的引擎
    engine = get_active_engine(g.user_id)
    if engine and engine.get('api_key'):
        api_key = engine['api_key']
        base_url = (engine.get('base_url', base_url) or base_url).rstrip('/')
        model = engine.get('model', model)
    else:
        # 2. 再检查服务端环境变量
        api_key = AI_CONFIG['api_key']
        if not api_key:
            # 3. 最后兼容旧 user_settings
            settings = get_user_settings(g.user_id)
            if settings and settings.get('ai_api_key'):
                api_key = settings['ai_api_key']
                if settings.get('ai_base_url'):
                    base_url = settings['ai_base_url'].rstrip('/')
                if settings.get('ai_model'):
                    model = settings['ai_model']

    if not api_key:
        return jsonify({'ok': False, 'msg': '服务端未配置 AI API Key，请在下方配置你自己的 Key', 'need_user_key': True})

    # 统一去除末尾斜杠，防止双斜杠
    base_url = base_url.rstrip('/')

    try:
        import urllib.request
        import ssl

        api_url = f"{base_url}/chat/completions"
        payload = json.dumps({
            'model': model,
            'messages': [{'role': 'user', 'content': 'Hi'}],
            'max_tokens': 5
        }).encode('utf-8')

        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {api_key}"
            }
        )

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return jsonify({
                'ok': True,
                'msg': f"AI 连接正常 (模型: {model})",
                'model': model,
                'key_source': 'server' if AI_CONFIG['api_key'] else 'user'
            })
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'AI 连接失败: {str(e)}'})


@app.route('/api/ai/checkin-feedback', methods=['POST'])
@login_required
def ai_checkin_feedback():
    """生成打卡后的反馈和建议（基于用户当前进展和时间节点）"""
    data = request.get_json()
    
    # 获取用户基本信息
    user_profile = data.get('user_profile', {})
    # 获取已打卡记录
    checked_nodes = data.get('checked_nodes', {})
    # 获取当前打卡的路标信息
    current_checkin = data.get('current_checkin', {})
    # 获取所有路标（包含未完成的）
    all_milestones = data.get('milestones', [])
    # 获取AI规划建议
    ai_plan = data.get('ai_plan', {})
    
    # 构建反馈Prompt
    feedback_prompt = build_checkin_feedback_prompt(
        user_profile, checked_nodes, current_checkin, all_milestones, ai_plan
    )
    
    # 获取API配置（用户当前激活引擎优先，其次服务端环境变量）
    api_key = ''
    base_url = AI_CONFIG['base_url']
    model = AI_CONFIG['model']
    
    # 1. 先检查用户当前激活的引擎
    engine = get_active_engine(g.user_id)
    print(f"[DEBUG ai_checkin_feedback] get_active_engine result: {engine}")
    if engine and engine.get('api_key'):
        api_key = engine['api_key']
        base_url = (engine.get('base_url', base_url) or base_url).rstrip('/')
        model = engine.get('model', model)
    else:
        # 2. 再检查服务端环境变量
        api_key = AI_CONFIG['api_key']
        print(f"[DEBUG ai_checkin_feedback] AI_CONFIG api_key exists: {bool(api_key)}, user_id: {g.user_id}")
        if not api_key:
            # 3. 最后兼容旧 user_settings
            settings = get_user_settings(g.user_id)
            print(f"[DEBUG ai_checkin_feedback] Fallback to user_settings: {settings}")
            if settings and settings.get('ai_api_key'):
                api_key = settings['ai_api_key']
                if settings.get('ai_base_url'):
                    base_url = settings['ai_base_url'].rstrip('/')
                if settings.get('ai_model'):
                    model = settings['ai_model']
    
    if not api_key:
        print(f"[DEBUG ai_checkin_feedback] No API key found, returning error")
        return jsonify({'ok': False, 'msg': 'AI API Key 未配置，请在设置中配置你的 API Key'}), 400
    
    # 调试日志：显示将要使用的配置
    masked_key = api_key[:4] + '****' + api_key[-4:] if len(api_key) > 8 else '****'
    print(f"[DEBUG ai_checkin_feedback] Using API - base_url: {base_url}, model: {model}, key: {masked_key}, user_id: {g.user_id}")
    
    base_url = base_url.rstrip('/')
    
    try:
        import urllib.request
        import ssl
        
        api_url = f"{base_url}/chat/completions"
        payload = json.dumps({
            'model': model,
            'messages': [
                {'role': 'system', 'content': '你是一位温暖、专业、富有洞察力的职业规划导师。你的风格是：\n1. 善于发现用户的亮点和进步，给予真诚的肯定\n2. 结合用户实际情况给出具体可行的建议\n3. 语言亲切自然，像朋友聊天一样\n4. 建议要具体、有针对性，不要泛泛而谈'},
                {'role': 'user', 'content': feedback_prompt}
            ],
            'temperature': 0.8,
            'max_tokens': 1500
        }).encode('utf-8')
        
        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {api_key}"
            }
        )
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            return jsonify({
                'ok': True,
                'feedback': content,
                'model': model
            })
    
    except Exception as e:
        err_str = str(e)
        print(f"[DEBUG ai_checkin_feedback] API call failed: {err_str}")
        # 对常见的API错误进行友好提示
        if '401' in err_str or 'Unauthorized' in err_str or 'Authorization' in err_str:
            return jsonify({'ok': False, 'msg': 'AI API Key 无效或已过期，请检查你的 API Key 配置'}), 500
        return jsonify({'ok': False, 'msg': f'生成反馈失败: {err_str}'}), 500


def build_checkin_feedback_prompt(user_profile, checked_nodes, current_checkin, all_milestones, ai_plan):
    """构建打卡反馈的Prompt"""
    
    # 用户基本信息
    grade = user_profile.get('grade', '未知')
    major = user_profile.get('major', '未知')
    school = user_profile.get('school', '未知')
    industry = user_profile.get('industry', '未知')
    target_position = user_profile.get('targetPosition', '未知')
    target_company = user_profile.get('targetCompany', '未知')
    
    # 整理已完成的经历
    completed_experiences = []
    for node_id, info in checked_nodes.items():
        milestone = next((m for m in all_milestones if m.get('id') == node_id), {})
        exp = {
            'label': milestone.get('label', '未知'),
            'icon': milestone.get('icon', '📌'),
            'note': info.get('note', ''),
            'time': info.get('time', ''),
        }
        # 根据打卡类型添加额外信息
        if info.get('company'):
            exp['company'] = info.get('company')
        if info.get('role'):
            exp['role'] = info.get('role')
        if info.get('award'):
            exp['award'] = info.get('award')
        if info.get('pubname'):
            exp['pubname'] = info.get('pubname')
        if info.get('feeling'):
            exp['feeling'] = info.get('feeling')
        completed_experiences.append(exp)
    
    # 当前打卡的路标
    current_label = current_checkin.get('label', '未知')
    current_icon = current_checkin.get('icon', '📌')
    current_note = current_checkin.get('note', '')
    current_extra = current_checkin.get('extra', {})
    current_feeling = current_extra.get('feeling', '')
    
    # 未完成的路标（按顺序）
    remaining_milestones = []
    checked_ids = set(checked_nodes.keys())
    for m in all_milestones:
        if m.get('id') not in checked_ids:
            remaining_milestones.append({
                'icon': m.get('icon', '📌'),
                'label': m.get('label', '未知'),
                'time': m.get('time', ''),
                'desc': m.get('desc', '')
            })
    
    # 原有AI规划建议
    ai_advices = ai_plan.get('advices', []) if isinstance(ai_plan, dict) else []
    
    # 构建Prompt
    prompt = f"""## 用户档案
- 年级：{grade}
- 专业：{major}
- 学校：{school}
- 目标行业：{industry}
- 目标岗位：{target_position}
- 目标公司：{target_company}

## 用户已完成的经历（按时间顺序）
"""
    
    for i, exp in enumerate(completed_experiences, 1):
        prompt += f"\n{i}. {exp['icon']} {exp['label']}"
        if exp.get('company'):
            prompt += f"\n   公司：{exp['company']}"
        if exp.get('role'):
            prompt += f"\n   岗位：{exp['role']}"
        if exp.get('award'):
            prompt += f"\n   获奖：{exp['award']}"
        if exp.get('pubname'):
            prompt += f"\n   成果：{exp['pubname']}"
        if exp.get('note'):
            prompt += f"\n   记录：{exp['note']}"
        if exp.get('feeling'):
            prompt += f"\n   心得：{exp['feeling']}"
    
    prompt += f"""

## 刚刚完成的路标
{current_icon} {current_label}
记录：{current_note}
"""
    if current_extra.get('company'):
        prompt += f"公司：{current_extra['company']}\n"
    if current_extra.get('role'):
        prompt += f"岗位：{current_extra['role']}\n"
    if current_extra.get('award'):
        prompt += f"获奖：{current_extra['award']}\n"
    if current_feeling:
        prompt += f"心得：{current_feeling}\n"
    
    if remaining_milestones:
        prompt += "\n## 接下来的路标\n"
        for m in remaining_milestones[:5]:  # 只显示前5个
            prompt += f"- {m['icon']} {m['label']}（{m['time']}）：{m['desc']}\n"
    
    if ai_advices:
        prompt += "\n## 原有AI规划建议摘要\n"
        for advice in ai_advices[:3]:  # 只显示前3条
            if isinstance(advice, dict):
                prompt += f"- {advice.get('text', str(advice))}\n"
            else:
                prompt += f"- {advice}\n"
    
    prompt += """

## 任务要求
请根据以上信息，生成一段温暖的反馈，包含：
1. **真诚的肯定**：发现用户刚才完成的内容中的亮点，予以肯定
2. **基于已有成就的鼓励**：结合用户之前完成的经历，说明这一路走来的进步
3. **下一步具体建议**：结合剩余路标和AI规划，给出1-2个具体可行的下一步行动建议
4. **适度的激励**：用轻松友好的语气结尾

格式要求：
- 总字数控制在200-400字
- 语言亲切自然，像朋友聊天
- 建议要具体、有针对性，不要泛泛而谈
- 不要使用emoji（用户界面会统一添加）

请直接输出反馈内容，不要使用JSON或其他格式。"""

    return prompt


@app.route('/api/ai/adjust-milestones', methods=['POST'])
@login_required
def ai_adjust_milestones():
    """根据用户已完成的打卡动态调整剩余路标
    
    重要原则：
    - 已完成的路标（包括刚打卡的那个）绝对不能被修改、删除或替换
    - 只能调整尚未打卡的路标
    - 不要轻易调整现有的路标，除非对用户未来会有更多帮助
    """
    data = request.get_json()
    
    # 获取用户基本信息
    user_profile = data.get('user_profile', {})
    # 获取已打卡记录
    checked_nodes = data.get('checked_nodes', {})
    # 获取原始路标
    original_milestones = data.get('milestones', [])
    # 获取AI原始规划
    ai_plan = data.get('ai_plan', {})
    
    # 找出已完成的路标（这些绝对不能修改）
    completed_milestones = []
    remaining_milestones = []
    completed_ids = set()  # 用集合存储已完成的路标ID，便于快速查找
    checked_ids = set(checked_nodes.keys())
    
    for m in original_milestones:
        if m.get('id') in checked_ids:
            completed_milestones.append(m)
            completed_ids.add(m.get('id'))
        else:
            remaining_milestones.append(m)
    
    # 记录已完成的数量，用于前端验证
    completed_count = len(completed_milestones)
    
    if not remaining_milestones:
        return jsonify({
            'ok': True, 
            'milestones': original_milestones, 
            'adjusted': False,
            'completed_count': completed_count
        })
    
    # 构建调整Prompt
    adjust_prompt = build_milestone_adjust_prompt(
        user_profile, completed_milestones, remaining_milestones, ai_plan
    )
    
    # 获取API配置（用户当前激活引擎优先，其次服务端环境变量）
    api_key = ''
    base_url = AI_CONFIG['base_url']
    model = AI_CONFIG['model']
    
    # 1. 先检查用户当前激活的引擎
    engine = get_active_engine(g.user_id)
    if engine and engine.get('api_key'):
        api_key = engine['api_key']
        base_url = (engine.get('base_url', base_url) or base_url).rstrip('/')
        model = engine.get('model', model)
    else:
        # 2. 再检查服务端环境变量
        api_key = AI_CONFIG['api_key']
        if not api_key:
            # 3. 最后兼容旧 user_settings
            settings = get_user_settings(g.user_id)
            if settings and settings.get('ai_api_key'):
                api_key = settings['ai_api_key']
                if settings.get('ai_base_url'):
                    base_url = settings['ai_base_url'].rstrip('/')
                if settings.get('ai_model'):
                    model = settings['ai_model']
    
    if not api_key:
        return jsonify({'ok': False, 'msg': 'AI API Key 未配置，请在设置中配置你的 API Key'}), 400
    
    base_url = base_url.rstrip('/')
    
    try:
        import urllib.request
        import ssl
        
        api_url = f"{base_url}/chat/completions"
        payload = json.dumps({
            'model': model,
            'messages': [
                {'role': 'system', 'content': '你是一位专业的职业规划师，擅长根据用户的实际进展动态调整规划路径。重要原则：只有未完成的路标会被调整，已完成的路标必须保持原样。'},
                {'role': 'user', 'content': adjust_prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 2000
        }).encode('utf-8')
        
        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {api_key}"
            }
        )
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 解析JSON返回
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                adjusted = json.loads(json_match.group())
                adjusted_remaining = adjusted.get('remaining_milestones', remaining_milestones)
                
                # 安全检查：确保AI没有返回包含已完成ID的路标
                # 如果AI返回的路标中有已完成路标的ID，忽略它
                safe_remaining = []
                for m in adjusted_remaining:
                    mid = m.get('id')
                    # 如果这个路标的ID是已完成ID之一，跳过它（已完成的路标必须保留）
                    if mid and mid in completed_ids:
                        continue
                    # 如果这个路标的label与某个已完成路标完全相同（可能被改头换面），也要检查
                    is_duplicate = False
                    for cm in completed_milestones:
                        if m.get('label') == cm.get('label') and m.get('icon') == cm.get('icon'):
                            is_duplicate = True
                            break
                    if not is_duplicate:
                        safe_remaining.append(m)
                
                # 合并：已完成的路标 + 调整后的剩余路标（经过安全检查）
                new_milestones = completed_milestones + safe_remaining
                
                # 检查是否真的有调整
                is_actually_adjusted = (len(safe_remaining) != len(remaining_milestones) or
                                        any(safe_remaining[i].get('label') != remaining_milestones[i].get('label') 
                                            for i in range(min(len(safe_remaining), len(remaining_milestones)))))
                
                return jsonify({
                    'ok': True,
                    'milestones': new_milestones,
                    'adjusted': is_actually_adjusted,
                    'reason': adjusted.get('reason', ''),
                    'completed_count': completed_count  # 返回已完成数量，供前端验证
                })
            else:
                return jsonify({
                    'ok': True, 
                    'milestones': original_milestones, 
                    'adjusted': False,
                    'completed_count': completed_count
                })
    
    except Exception as e:
        err_str = str(e)
        # 对常见的API错误进行友好提示
        if '401' in err_str or 'Unauthorized' in err_str or 'Authorization' in err_str:
            return jsonify({'ok': False, 'msg': 'AI API Key 无效或已过期，请检查你的 API Key 配置'}), 500
        return jsonify({'ok': False, 'msg': f'调整路标失败: {err_str}'}), 500


def build_milestone_adjust_prompt(user_profile, completed_milestones, remaining_milestones, ai_plan):
    """构建路标调整的Prompt"""
    
    # 用户基本信息
    grade = user_profile.get('grade', '未知')
    major = user_profile.get('major', '未知')
    school = user_profile.get('school', '未知')
    industry = user_profile.get('industry', '未知')
    target_position = user_profile.get('targetPosition', '未知')
    target_company = user_profile.get('targetCompany', '未知')
    grad_year = user_profile.get('gradYear', '')
    
    prompt = f"""## 用户基本信息
- 年级：{grade}
- 毕业年份：{grad_year}
- 专业：{major}
- 学校：{school}
- 目标行业：{industry}
- 目标岗位：{target_position}
- 目标公司：{target_company}

## 已完成的路标（这些不能修改，保持原样）
"""
    
    for m in completed_milestones:
        prompt += f"- {m.get('icon', '📌')} {m.get('label', '未知')}（已完成）\n"
    
    prompt += "\n## 待调整的剩余路标（可以根据用户实际情况调整）\n"
    for i, m in enumerate(remaining_milestones, 1):
        prompt += f"{i}. {m.get('icon', '📌')} {m.get('label', '未知')}（{m.get('time', '')}）\n"
        prompt += f"   描述：{m.get('desc', '')}\n"
    
    prompt += """
## 调整规则
1. **已完成的路标必须保留**：不能删除或修改任何已完成的路标
2. **可以调整的内容**：
   - 未完成路标的标题、描述、时间节点
   - 路标的顺序（但要保持逻辑性）
   - 可以添加新的路标（如果确实需要）
   - 可以删除明显不合适的路标（需在reason中说明）
3. **调整原则**：
   - 根据用户已完成的经历，适当提前或延后相关路标
   - 如果用户比预期进展快，可以适当增加挑战
   - 如果用户遇到困难，可以适当降低难度或调整方向
   - 保持路标之间的逻辑连贯性

## 返回格式
请返回一个JSON对象，包含：
{
  "reason": "调整原因说明（简要）",
  "remaining_milestones": [
    {
      "icon": "emoji图标",
      "label": "路标标题",
      "time": "时间描述",
      "desc": "详细描述"
    }
  ]
}

请直接输出JSON，不要有其他内容。"""

    return prompt


# ===== 招聘跳转 API =====

@app.route('/api/company-links', methods=['POST'])
@login_required
def get_company_links_api():
    """获取公司招聘链接"""
    data = request.get_json()
    company_name = (data.get('company') or '').strip()
    city = (data.get('city') or '').strip()

    if not company_name:
        return jsonify({'ok': False, 'msg': '公司名称不能为空'}), 400

    links = get_company_links(company_name, city=city)
    return jsonify({'ok': True, 'company': company_name, 'links': links})


@app.route('/api/gwy-links', methods=['POST'])
@login_required
def get_gwy_links_api():
    """获取公务员/事业单位考试报名链接"""
    data = request.get_json()
    city = (data.get('city') or '').strip()

    links = get_gwy_links(city=city)
    return jsonify({'ok': True, 'links': links})


@app.route('/api/parse-companies', methods=['POST'])
@login_required
def parse_companies_api():
    """从 AI 生成的规划文本中解析公司名称"""
    data = request.get_json()
    ai_plan_text = data.get('ai_plan', '')

    if not ai_plan_text:
        return jsonify({'ok': True, 'companies': []})

    companies = parse_companies_from_ai_plan(ai_plan_text)
    return jsonify({'ok': True, 'companies': companies})


# ===== 用户 AI 设置 API =====

@app.route('/api/ai-settings', methods=['GET'])
@login_required
def get_ai_settings():
    """获取当前用户的 AI 设置（API Key 不会完整返回）"""
    settings = get_user_settings(g.user_id)
    if settings:
        key = settings.get('ai_api_key', '')
        # 隐藏 Key 的中间部分
        masked_key = ''
        if key:
            if len(key) > 8:
                masked_key = key[:4] + '****' + key[-4:]
            else:
                masked_key = '****'
        return jsonify({
            'ok': True,
            'settings': {
                'has_key': bool(key),
                'masked_key': masked_key,
                'ai_base_url': settings.get('ai_base_url', ''),
                'ai_model': settings.get('ai_model', '')
            }
        })
    return jsonify({
        'ok': True,
        'settings': {
            'has_key': False,
            'masked_key': '',
            'ai_base_url': '',
            'ai_model': ''
        }
    })


@app.route('/api/ai-settings', methods=['POST'])
@login_required
def save_ai_settings():
    """保存用户的 AI 设置（API Key、Base URL、Model）"""
    data = request.get_json()
    api_key = (data.get('ai_api_key') or '').strip()
    base_url = (data.get('ai_base_url') or '').strip()
    model = (data.get('ai_model') or '').strip()

    # 如果用户清空了 Key，传空字符串
    save_user_settings(g.user_id, ai_api_key=api_key, ai_base_url=base_url or None, ai_model=model or None)

    return jsonify({'ok': True, 'msg': 'AI 设置已保存'})


# ===== AI 引擎管理 API =====

@app.route('/api/ai-engines', methods=['GET'])
@login_required
def list_ai_engines():
    """获取用户所有 AI 引擎列表"""
    engines = get_ai_engines(g.user_id)
    settings = get_user_settings(g.user_id)
    active_id = settings.get('active_engine_id') if settings else None
    return jsonify({'ok': True, 'engines': engines, 'active_engine_id': active_id})


@app.route('/api/ai-engines', methods=['POST'])
@login_required
def create_ai_engine():
    """添加一个新的 AI 引擎"""
    data = request.get_json()
    name = (data.get('name') or '').strip()
    api_key = (data.get('api_key') or '').strip()
    base_url = (data.get('base_url') or '').strip() or 'https://api.deepseek.com'
    model = (data.get('model') or '').strip() or 'deepseek-chat'

    if not api_key:
        return jsonify({'ok': False, 'msg': 'API Key 不能为空'}), 400

    engine_id = add_ai_engine(g.user_id, name, api_key, base_url, model)

    # 添加引擎后自动设为激活引擎
    set_active_engine(g.user_id, engine_id)

    return jsonify({'ok': True, 'msg': '引擎已添加', 'engine_id': engine_id})


@app.route('/api/ai-engines/<int:engine_id>', methods=['GET'])
@login_required
def get_ai_engine_detail(engine_id):
    """获取单个引擎的完整配置（含 api_key，仅供前端编辑回显）"""
    engine = get_ai_engine_full(engine_id, g.user_id)
    if not engine:
        return jsonify({'ok': False, 'msg': '引擎不存在'}), 404
    # 对 api_key 做脱敏，前端编辑时显示掩码，用户改了才传新值
    key = engine.get('api_key', '')
    if key:
        engine['masked_key'] = key[:4] + '****' + key[-4:] if len(key) > 8 else '****'
    else:
        engine['masked_key'] = ''
    engine.pop('api_key', None)
    return jsonify({'ok': True, 'engine': engine})


@app.route('/api/ai-engines/<int:engine_id>', methods=['PUT'])
@login_required
def modify_ai_engine(engine_id):
    """更新 AI 引擎配置"""
    data = request.get_json()
    name = data.get('name')
    api_key = data.get('api_key')
    base_url = data.get('base_url')
    model = data.get('model')

    if name is None and api_key is None and base_url is None and model is None:
        return jsonify({'ok': False, 'msg': '没有要更新的字段'}), 400

    update_ai_engine(engine_id, g.user_id, name=name, api_key=api_key,
                     base_url=base_url, model=model)
    return jsonify({'ok': True, 'msg': '引擎已更新'})


@app.route('/api/ai-engines/<int:engine_id>', methods=['DELETE'])
@login_required
def remove_ai_engine(engine_id):
    """删除 AI 引擎"""
    ok = delete_ai_engine(engine_id, g.user_id)
    if ok:
        return jsonify({'ok': True, 'msg': '引擎已删除'})
    return jsonify({'ok': False, 'msg': '引擎不存在'}), 404


@app.route('/api/ai-engines/activate', methods=['POST'])
@login_required
def activate_ai_engine():
    """切换当前激活的 AI 引擎"""
    data = request.get_json()
    engine_id = data.get('engine_id')
    if not engine_id:
        return jsonify({'ok': False, 'msg': '请指定引擎 ID'}), 400

    # 验证引擎属于当前用户
    engine = get_ai_engine_full(engine_id, g.user_id)
    if not engine:
        return jsonify({'ok': False, 'msg': '引擎不存在'}), 404

    set_active_engine(g.user_id, engine_id)
    return jsonify({'ok': True, 'msg': '已切换引擎', 'engine_id': engine_id,
                    'model': engine.get('model', ''),
                    'base_url': engine.get('base_url', '')})


@app.route('/api/ai-engines/<int:engine_id>/test', methods=['POST'])
@login_required
def test_ai_engine_endpoint(engine_id):
    """测试指定引擎的连通性"""
    engine = get_ai_engine_full(engine_id, g.user_id)
    if not engine:
        return jsonify({'ok': False, 'msg': '引擎不存在'}), 404

    api_key = engine['api_key']
    base_url = (engine.get('base_url') or 'https://api.deepseek.com').rstrip('/')
    model = engine.get('model', 'deepseek-chat')

    try:
        import urllib.request
        import ssl

        api_url = f"{base_url}/chat/completions"
        payload = json.dumps({
            'model': model,
            'messages': [{'role': 'user', 'content': 'Hi'}],
            'max_tokens': 5
        }).encode('utf-8')

        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {api_key}"
            }
        )

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            body = resp.read().decode('utf-8')
            try:
                json.loads(body)
            except json.JSONDecodeError:
                return jsonify({'ok': False, 'msg': f'API 返回了非 JSON 响应，请检查 Base URL 是否正确（当前: {base_url}）。响应前100字符: {body[:100]}'})

            # 测试通过，标记为有效，并自动激活该引擎
            update_ai_engine(engine_id, g.user_id, is_valid=True)
            set_active_engine(g.user_id, engine_id)
            return jsonify({'ok': True, 'msg': f'连接成功 (模型: {model})', 'model': model})
    except Exception as e:
        update_ai_engine(engine_id, g.user_id, is_valid=False)
        return jsonify({'ok': False, 'msg': f'连接失败: {str(e)}'})


# ===== 修改密码 API =====

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return jsonify({'ok': False, 'msg': '原密码和新密码不能为空'}), 400

    if len(new_password) < 6:
        return jsonify({'ok': False, 'msg': '新密码长度至少6位'}), 400

    user = get_user_by_id(g.user_id)
    if not verify_password(old_password, user['password_hash']):
        return jsonify({'ok': False, 'msg': '原密码错误'}), 400

    from models import get_db, hash_password
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(new_password), g.user_id)
        )

    return jsonify({'ok': True, 'msg': '密码修改成功'})


# ===== 健康检查 =====

@app.route('/api/health')
def health():
    """服务健康检查"""
    return jsonify({'ok': True, 'msg': 'Career Planner API is running 🦉'})


# ===== 启动入口 =====

import sys
import io

if __name__ == '__main__':
    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    print("=" * 50)
    print("🦉 职画 - 后端服务")
    print("=" * 50)

    # 初始化数据库
    init_db()

    # 检查 AI 配置
    if AI_CONFIG['api_key']:
        print(f"✅ AI 已配置 (模型: {AI_CONFIG['model']})")
    else:
        print("⚠️  AI 未配置 - 请设置 DEEPSEEK_API_KEY 环境变量")

    # 检查邮箱配置
    if email_sender.enabled:
        print(f"✅ 邮件服务已配置 (SMTP: {email_sender.smtp_host})")
    else:
        print("⚠️  邮件服务未配置 - 验证码将打印到控制台（开发模式）")

    print("-" * 50)
    print("📱 访问地址: http://localhost:5000")
    print("🔑 API 地址: http://localhost:5000/api/health")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=True)
