# 🦉 职画 API 接口文档

本文档详细描述了「职画」应用的所有 API 接口。

---

## 基础信息

- **Base URL**: `http://localhost:5000`
- **认证方式**: JWT Bearer Token
- **Content-Type**: `application/json`

### 认证请求头

除无需认证的接口外，所有请求需携带：

```
Authorization: Bearer <token>
```

### 通用响应格式

```json
{
  "ok": true,       // boolean - 请求是否成功
  "msg": "成功",    // string - 提示信息
  "data": {}        // object - 返回数据（可选）
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或 Token 无效 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁（限流） |
| 500 | 服务器内部错误 |

---

## 认证接口

### 1. 用户注册

**POST** `/api/register`

注册新用户（用户名 + 密码）

**请求参数**

```json
{
  "username": "string",   // 用户名，3-20个字符
  "password": "string",  // 密码，至少6位
  "email": "string"      // 邮箱（可选）
}
```

**响应示例**

```json
{
  "ok": true,
  "msg": "注册成功！",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "nickname": null,
    "avatar": ""
  }
}
```

---

### 2. 用户登录

**POST** `/api/login`

用户名 + 密码登录

**请求参数**

```json
{
  "username": "string",
  "password": "string"
}
```

**响应示例**

```json
{
  "ok": true,
  "msg": "登录成功！",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "nickname": null,
    "avatar": ""
  }
}
```

---

### 3. 发送邮箱验证码

**POST** `/api/send-email-code`

发送邮箱验证码（用于邮箱登录/注册）

**请求参数**

```json
{
  "email": "string",      // 邮箱地址
  "purpose": "login"      // 用途：login 或 register
}
```

**响应示例**

```json
{
  "ok": true,
  "msg": "验证码已发送",
  "dev_code": "123456"    // 仅开发模式下返回（邮件服务未配置时）
}
```

**限流规则**: 同一邮箱 60 秒内只能发送一次

---

### 4. 邮箱验证码登录

**POST** `/api/login-by-email`

通过邮箱 + 验证码登录或自动注册

**请求参数**

```json
{
  "email": "string",      // 邮箱地址
  "code": "string"        // 6位验证码
}
```

**响应示例**

```json
{
  "ok": true,
  "msg": "登录成功！",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 2,
    "username": "user_abc123",
    "email": "user@example.com",
    "nickname": null,
    "avatar": ""
  }
}
```

---

## 用户接口

### 5. 获取用户资料

**GET** `/api/profile`

获取当前登录用户的信息

**响应示例**

```json
{
  "ok": true,
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "phone": null,
    "nickname": "我的昵称",
    "avatar": "data:image/png;base64,...",
    "created_at": "2026-05-11 18:00:00"
  }
}
```

---

### 6. 更新用户资料

**PUT** `/api/profile`

更新用户头像和昵称

**请求参数**

```json
{
  "nickname": "string",   // 昵称（可选）
  "avatar": "string"      // 头像 Base64 或 URL（可选）
}
```

**响应示例**

```json
{
  "ok": true,
  "msg": "资料更新成功"
}
```

---

### 7. 修改密码

**POST** `/api/change-password`

修改当前用户的登录密码

**请求参数**

```json
{
  "old_password": "string",  // 原密码
  "new_password": "string"    // 新密码，至少6位
}
```

**响应示例**

```json
{
  "ok": true,
  "msg": "密码修改成功"
}
```

---

## 职业规划 & 简历接口

> 💡 **说明**：简历数据存储在职业规划数据中，通过 `/api/plan` 接口统一管理。前端调用 `/api/ai/generate` 实现简历评分和 AI 优化建议。

### 8. 获取职业规划

**GET** `/api/plan`

获取当前用户的职业规划数据（含简历信息）

**响应示例**

```json
{
  "ok": true,
  "plan": {
    "id": 1,
    "user_id": 1,
    "form_data": {
      "name": "张三",
      "education": "本科",
      "major": "计算机科学",
      "city": "北京",
      "industry": "互联网",
      // --- 简历相关字段 ---
      "resume": {
        "phone": "138xxxx8888",
        "email": "zhangsan@email.com",
        "skills": ["Python", "JavaScript", "SQL"],
        "projects": [...],
        "experience": [...],
        "certificates": []
      }
    },
    "selected_tags": {
      "industry": ["互联网", "人工智能"],
      "direction": ["后端开发", "算法"]
    },
    "mbti_result": {
      "type": "INTJ",
      "description": "..."
    },
    "ai_plan": "## 职业规划建议\n\n### 短期目标...\n...",
    "plan_title": "我的5年职业规划",
    "api_model": "deepseek-chat",
    "created_at": "2026-05-11 18:00:00",
    "updated_at": "2026-05-11 18:30:00"
  }
}
```

---

### 9. 保存职业规划（含简历）

**POST** `/api/plan`

保存或更新职业规划数据，简历信息包含在 `form_data.resume` 中

**请求参数**

```json
{
  "form_data": {
    "name": "string",
    "education": "string",
    "major": "string",
    "city": "string",
    "industry": "string",
    "resume": {
      "phone": "string",
      "email": "string",
      "skills": ["string"],
      "projects": [
        {
          "name": "项目名称",
          "role": "担任角色",
          "duration": "时间",
          "description": "项目描述"
        }
      ],
      "experience": [
        {
          "company": "公司名",
          "position": "职位",
          "duration": "时间",
          "description": "工作内容"
        }
      ],
      "certificates": ["string"]
    }
  },
  "selected_tags": {
    "industry": ["string"],
    "direction": ["string"]
  },
  "mbti_result": {
    "type": "string",
    "description": "string"
  },
  "ai_plan": "string",      // AI 生成的规划内容（Markdown）
  "plan_title": "string",   // 规划标题
  "api_model": "string"      // 使用的 AI 模型名称
}
```

**响应示例**

```json
{
  "ok": true,
  "msg": "保存成功",
  "plan_id": 1
}
```

---

### 简历优化（AI）

简历优化功能通过调用 `/api/ai/generate` 接口实现，AI 根据用户简历数据和目标岗位生成评分和优化建议。

**前端调用示例**：

```javascript
// 简历评分 & 优化建议 Prompt
const systemPrompt = `你是一个专业的简历优化顾问。请分析用户的简历，给出：
1. 综合评分（0-100）
2. 各维度评分（完整性、专业性、关键词匹配等）
3. 具体的优化建议`;

const userMessage = `
目标岗位：${targetPosition}
用户简历信息：
${JSON.stringify(resumeData, null, 2)}
`;

const response = await fetch('/api/ai/generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    system_prompt: systemPrompt,
    user_message: userMessage
  })
});
// 流式读取 AI 返回的评分和建议...
```

---

## AI 接口

### 10. AI 生成职业规划

**POST** `/api/ai/generate`

服务端代理 AI 请求，流式返回生成内容

**请求参数**

```json
{
  "system_prompt": "string",   // 系统提示词
  "user_message": "string"     // 用户消息
}
```

**响应格式**: Server-Sent Events (SSE) 流式响应

```
data: {"content": "正在分析"}

data: {"content": "## 职业规划建议"}

data: [DONE]
```

**错误响应**

```json
{
  "ok": false,
  "msg": "AI 生成失败: Connection timeout"
}
```

---

### 11. 测试 AI 连通性

**POST** `/api/ai/test`

测试 AI API 是否可连接

**响应示例**

```json
{
  "ok": true,
  "msg": "AI 连接正常 (模型: deepseek-chat)",
  "model": "deepseek-chat",
  "key_source": "server"      // server 表示服务端 Key，user 表示用户自定义 Key
}
```

**需要用户配置 Key 时**

```json
{
  "ok": false,
  "msg": "服务端未配置 AI API Key，请在下方配置你自己的 Key",
  "need_user_key": true
}
```

---

## AI 引擎管理接口

### 12. 获取 AI 引擎列表

**GET** `/api/ai-engines`

获取用户所有 AI 引擎配置

**响应示例**

```json
{
  "ok": true,
  "engines": [
    {
      "id": 1,
      "user_id": 1,
      "name": "DeepSeek",
      "base_url": "https://api.deepseek.com",
      "model": "deepseek-chat",
      "is_valid": 1,
      "masked_key": "sk-****xxxx"
    }
  ],
  "active_engine_id": 1
}
```

---

### 13. 添加 AI 引擎

**POST** `/api/ai-engines`

添加一个新的 AI 引擎配置

**请求参数**

```json
{
  "name": "string",        // 引擎名称
  "api_key": "string",     // API Key
  "base_url": "string",    // API 地址（默认：https://api.deepseek.com）
  "model": "string"        // 模型名称（默认：deepseek-chat）
}
```

**响应示例**

```json
{
  "ok": true,
  "msg": "引擎已添加",
  "engine_id": 2
}
```

---

### 14. 获取引擎详情

**GET** `/api/ai-engines/<engine_id>`

获取单个引擎的完整配置（含掩码 Key）

**响应示例**

```json
{
  "ok": true,
  "engine": {
    "id": 1,
    "name": "DeepSeek",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
    "is_valid": 1,
    "masked_key": "sk-****xxxx"
  }
}
```

---

### 15. 更新 AI 引擎

**PUT** `/api/ai-engines/<engine_id>`

更新引擎配置

**请求参数**

```json
{
  "name": "string",        // 引擎名称
  "api_key": "string",     // API Key（可选）
  "base_url": "string",    // API 地址
  "model": "string"        // 模型名称
}
```

**响应示例**

```json
{
  "ok": true,
  "msg": "引擎已更新"
}
```

---

### 16. 删除 AI 引擎

**DELETE** `/api/ai-engines/<engine_id>`

删除指定的 AI 引擎

**响应示例**

```json
{
  "ok": true,
  "msg": "引擎已删除"
}
```

---

### 17. 切换激活引擎

**POST** `/api/ai-engines/activate`

设置当前激活的 AI 引擎

**请求参数**

```json
{
  "engine_id": 1
}
```

**响应示例**

```json
{
  "ok": true,
  "msg": "已切换引擎",
  "engine_id": 1,
  "model": "deepseek-chat",
  "base_url": "https://api.deepseek.com"
}
```

---

### 18. 测试引擎连通性

**POST** `/api/ai-engines/<engine_id>/test`

测试指定引擎的 API 连通性

**响应示例**

```json
{
  "ok": true,
  "msg": "连接成功 (模型: deepseek-chat)",
  "model": "deepseek-chat"
}
```

**连接失败时**

```json
{
  "ok": false,
  "msg": "连接失败: Connection refused"
}
```

---

## 招聘链接接口

### 19. 获取公司招聘链接

**POST** `/api/company-links`

根据公司名称获取各招聘平台的跳转链接

**请求参数**

```json
{
  "company": "string",     // 公司名称
  "city": "string"         // 期望就业城市（可选，用于事业单位按省份筛选）
}
```

**响应示例**

```json
{
  "ok": true,
  "company": "腾讯",
  "links": [
    {
      "name": "智联招聘",
      "url": "https://www.zhaopin.com/sou/?keyword=%E8%85%BE%E8%AE%AF",
      "icon": "📋",
      "desc": "综合招聘"
    },
    {
      "name": "实习僧",
      "url": "https://www.shixiseng.com/interns?keyword=%E8%85%BE%E8%AE%AF",
      "icon": "🎓",
      "desc": "实习岗位"
    }
  ]
}
```

**智能识别**:
- 检测到「研究所/大学/科学院」等关键词时，额外添加高校人才、科学网等科研平台
- 检测到「公务员/事业单位/体制内」等关键词时，调用 `/api/gwy-links` 返回考公链接

---

### 20. 获取公务员/事业单位链接

**POST** `/api/gwy-links`

获取公务员和事业单位考试的报名/资讯链接

**请求参数**

```json
{
  "city": "string"    // 期望就业城市（可选，用于定位省份）
}
```

**响应示例**

```json
{
  "ok": true,
  "links": [
    {
      "name": "国家公务员考试",
      "url": "http://bm.scs.gov.cn/pp/gkweb/core/web/ui/business/person/person_home.html",
      "icon": "🏛️",
      "desc": "国考公告/报名/职位查询（官方）"
    },
    {
      "name": "省考职位查询（广东）",
      "url": "https://www.offcn.com/gdgwy/",
      "icon": "📋",
      "desc": "广东省公务员考试资讯"
    },
    {
      "name": "广东事业单位招聘",
      "url": "https://sydw.huatu.com/gd/",
      "icon": "🏢",
      "desc": "广东省事业单位招聘信息"
    },
    {
      "name": "公考雷达",
      "url": "https://www.gongkaoleida.com/",
      "icon": "📡",
      "desc": "公职考试选岗工具"
    }
  ]
}
```

---

### 21. 解析 AI 规划中的公司名

**POST** `/api/parse-companies`

从 AI 生成的职业规划文本中提取公司/机构名称

**请求参数**

```json
{
  "ai_plan": "string"    // AI 生成的规划文本
}
```

**响应示例**

```json
{
  "ok": true,
  "companies": ["腾讯", "阿里巴巴", "字节跳动", "华为"]
}
```

---

## 系统接口

### 22. 健康检查

**GET** `/api/health`

检查服务是否正常运行，无需认证

**响应示例**

```json
{
  "ok": true,
  "msg": "Career Planner API is running 🦉"
}
```

---

## 错误码说明

| msg 关键词 | 说明 | 处理建议 |
|-----------|------|---------|
| 用户名和密码不能为空 | 参数缺失 | 检查请求参数 |
| 用户名已被注册 | 用户名冲突 | 换一个用户名 |
| 该邮箱已被注册 | 邮箱冲突 | 换一个邮箱或使用邮箱登录 |
| 验证码错误或已过期 | 验证码无效 | 重新获取验证码 |
| 发送太频繁，请60秒后重试 | 限流触发 | 等待 60 秒后重试 |
| 服务端未配置 AI API Key | AI 未配置 | 配置 DEEPSEEK_API_KEY 或让用户自备 Key |
| AI 生成失败 | AI 请求失败 | 检查 API Key 和网络连接 |
| Token 已过期 | JWT 过期 | 重新登录获取 Token |

---

## 前端调用示例

### fetch 请求封装

```javascript
const API_BASE = '/api';

// 带认证的请求
async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers
  };
  
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });
  
  const data = await res.json();
  if (!data.ok) throw new Error(data.msg);
  return data;
}

// 登录
const loginData = await apiRequest('/login', {
  method: 'POST',
  body: JSON.stringify({ username: 'xxx', password: 'xxx' })
});
localStorage.setItem('token', loginData.token);

// 获取职业规划
const planData = await apiRequest('/plan');
```

### 流式 AI 生成

```javascript
async function* streamAI(systemPrompt, userMessage) {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/ai/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ system_prompt: systemPrompt, user_message: userMessage })
  });
  
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const text = decoder.decode(value);
    const lines = text.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.content) yield data.content;
        if (data.error) throw new Error(data.error);
      }
    }
  }
}

// 使用
let fullText = '';
for await (const chunk of streamAI('你是一个职业规划师', '我是一名计算机专业的学生')) {
  fullText += chunk;
  console.log('AI 输出:', chunk);
}
```
