# 🎮 职画 - Career Planner

一个前后端分离的职业规划 Web 应用，支持用户注册登录、AI 生成职业规划、数据持久化存储。

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
| `/api/ai/generate` | POST | AI 生成（流式） | ✅ |
| `/api/ai/test` | POST | AI 连通性测试 | ✅ |
| `/api/company-links` | POST | 公司招聘链接 | ✅ |
| `/api/change-password` | POST | 修改密码 | ✅ |
| `/api/health` | GET | 健康检查 | ❌ |

## ✨ 功能特性

- **用户系统**：支持用户名+密码登录、邮箱验证码登录
- **AI 职业规划**：DeepSeek AI 生成个性化职业建议、推荐公司、里程碑路线图
- **数据持久化**：所有用户数据存储在 SQLite 数据库中
- **招聘跳转**：点击 AI 推荐的公司名，一键跳转到各大招聘平台
- **游戏化体验**：金币收集、成就系统、小恐龙游戏等待动画
- **主题切换**：6 种颜色主题

## 🌐 部署

### 生产环境推荐

使用 Gunicorn + Nginx 部署：

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 环境变量

部署时建议设置以下环境变量：
- `DEEPSEEK_API_KEY`：AI API Key
- `JWT_SECRET`：强随机密钥
- `SMTP_*`：邮箱发送配置
- `FLASK_ENV=production`：关闭调试模式
