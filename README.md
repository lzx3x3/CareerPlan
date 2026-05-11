# 🦉 职画 - Career Planner

一个前后端分离的职业规划 Web 应用，支持用户注册登录、AI 生成职业规划、数据持久化存储。以超级马里奥为灵感的游戏化界面，让职业规划更有趣！

## 🎯 核心功能

### 1. 用户系统
- **多种登录方式**：用户名+密码、邮箱+验证码一键登录/注册
- **用户资料**：头像、昵称、个人资料管理
- **密码安全**：支持修改密码，SHA-256 哈希存储

### 2. AI 职业规划（核心）
- **智能生成**：基于 DeepSeek/GLM 等大模型，生成个性化职业建议
- **多引擎支持**：用户可添加管理多个 AI 引擎配置，自由切换
- **流式输出**：实时展示 AI 生成内容，体验流畅
- **推荐公司**：AI 推荐适合的目标公司，一键跳转招聘平台
- **里程碑路线图**：短期/中期/长期职业发展路径

### 3. 简历信息收集
- 个人信息、教育背景、技能特长、项目经验、实习经历
- 数据自动同步到简历预览和求职广场

### 4. 简历优化（AI）
- **综合评分**：从完整性、专业性、关键词匹配等多维度评分
- **AI 分析建议**：针对目标岗位给出简历优化建议
- **简历预览**：4 种精美模板（经典/现代/简约/专业）
- **多格式导出**：支持 PDF、Word、打印

### 5. 求职广场
- 聚合多个招聘平台岗位搜索
- 按行业/城市筛选
- 一键跳转到 Boss直聘、实习僧、智联招聘等平台

### 6. 招聘跳转链接
- **企业**：智联招聘、实习僧、Boss直聘、前程无忧、牛客网
- **高校/科研**：高校人才网、科学网
- **公务员/事业单位**：国家公务员考试、各省省考、事业单位招聘
- **智能识别**：根据公司类型自动推荐合适平台

### 7. 游戏化体验
- **超级马里奥风格界面**：云朵、金币、水管等经典元素
- **金币收集**：完成里程碑获得金币奖励
- **成就系统**：记录用户的职业规划进度
- **小恐龙游戏**：AI 生成时的趣味等待动画

### 8. 主题定制
- 6 种精美主题：默认/森林/海洋/夜间/樱花/橙色

## 🚀 快速启动

### 1. 安装依赖

```bash
cd server
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

必须配置项：
- `DEEPSEEK_API_KEY`：DeepSeek AI API Key（服务端统一管理，用户无需自己填写）

可选配置项：
- `SMTP_HOST` / `SMTP_USER` / `SMTP_PASS`：邮箱 SMTP 配置（不配则验证码打印到控制台）
- `JWT_SECRET`：JWT 密钥（建议修改为随机字符串）

### 3. 启动服务

```bash
cd server
python app.py
```

访问地址：http://localhost:5000

## 📁 项目结构

```
CareerPlan/
├── server/
│   ├── app.py              # Flask 主应用 + 所有 API 路由
│   ├── models.py           # SQLite 数据库模型（用户/规划/验证码）
│   ├── auth.py             # JWT 认证模块
│   ├── email_sender.py     # 邮箱验证码发送
│   ├── company_links.py    # 招聘平台链接生成器
│   ├── .env.example        # 环境变量配置模板
│   ├── requirements.txt    # Python 依赖
│   ├── start.bat           # Windows 启动脚本
│   └── career_planner.db   # SQLite 数据库（运行后自动生成）
├── career-planner.html     # 前端主页面
└── README.md
```

## 🔑 API 接口

详细接口文档请参考 [API.md](./API.md)

### 认证方式

所有带 ✅ 的接口需要在请求头中携带 JWT Token：

```
Authorization: Bearer <token>
```

### 通用响应格式

```json
{
  "ok": true,      // 请求是否成功
  "msg": "提示信息",  // 提示信息
  "data": {}       // 返回数据（可选）
}
```

### 主要接口一览

| 接口 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/register` | POST | 用户注册（用户名+密码） | ❌ |
| `/api/login` | POST | 用户登录 | ❌ |
| `/api/login-by-email` | POST | 邮箱验证码登录/注册 | ❌ |
| `/api/send-email-code` | POST | 发送邮箱验证码 | ❌ |
| `/api/profile` | GET | 获取用户信息 | ✅ |
| `/api/profile` | PUT | 更新用户资料 | ✅ |
| `/api/plan` | GET | 获取职业规划 | ✅ |
| `/api/plan` | POST | 保存职业规划 | ✅ |
| `/api/ai/generate` | POST | AI 生成职业规划（流式） | ✅ |
| `/api/ai/test` | POST | AI 连通性测试 | ✅ |
| `/api/ai-engines` | GET | 获取 AI 引擎列表 | ✅ |
| `/api/ai-engines` | POST | 添加 AI 引擎 | ✅ |
| `/api/ai-engines/<id>` | PUT | 更新 AI 引擎 | ✅ |
| `/api/ai-engines/<id>` | DELETE | 删除 AI 引擎 | ✅ |
| `/api/ai-engines/activate` | POST | 切换激活引擎 | ✅ |
| `/api/ai-engines/<id>/test` | POST | 测试引擎连通性 | ✅ |
| `/api/company-links` | POST | 获取公司招聘链接 | ✅ |
| `/api/gwy-links` | POST | 获取公务员/事业单位链接 | ✅ |
| `/api/parse-companies` | POST | 从 AI 规划解析公司名 | ✅ |
| `/api/change-password` | POST | 修改密码 | ✅ |
| `/api/health` | GET | 健康检查 | ❌ |

## 🌐 部署

### 开发环境

```bash
cd server
pip install -r requirements.txt
python app.py
```

访问 http://localhost:5000

### 生产环境推荐

使用 Gunicorn + Nginx 部署：

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 环境变量

部署时建议设置以下环境变量：
- `DEEPSEEK_API_KEY`：AI API Key（服务端统一管理）
- `DEEPSEEK_BASE_URL`：AI API 地址（默认：https://api.deepseek.com）
- `DEEPSEEK_MODEL`：AI 模型名称（默认：deepseek-chat）
- `JWT_SECRET`：JWT 密钥（建议修改为随机字符串）
- `SMTP_HOST/SMTP_USER/SMTP_PASS/SMTP_PORT`：邮箱发送配置
- `FLASK_ENV=production`：关闭调试模式

> 💡 **提示**：如果未配置 AI API Key，用户可以在网页端自行配置自己的 Key。
