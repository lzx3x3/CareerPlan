# 🦉 职画 - 鸿蒙版

## 应用概述

将"职画"Web 应用封装为 HarmonyOS 原生应用，通过 WebView 加载前端页面，同时利用 HarmonyOS 原生能力提供更好的用户体验。

### 核心特性

- **WebView 加载**：无缝加载现有 Web 前端，功能完整
- **沉浸式体验**：状态栏沉浸式布局，全屏加载体验
- **错误处理**：网络异常时显示原生错误页面，支持重试
- **进度指示**：页面加载进度条，提升等待体验
- **离线感知**：智能检测后端服务状态

## 开发环境准备

### 必要工具

1. **DevEco Studio**（下载地址：[华为开发者联盟](https://developer.huawei.com/consumer/cn/deveco-studio/)）
2. **HarmonyOS SDK**（API 11+，可在 DevEco Studio 内安装）
3. **Node.js** v16+（用于 Hvigor 构建）

### 导入项目

1. 打开 DevEco Studio → 选择 `文件 → 打开`
2. 选择 `harmonyos/` 目录
3. 等待 Gradle 同步完成
4. 配置 `local.properties` 中的 SDK 路径

### 配置服务器地址

> 开发阶段修改 `entry/src/main/ets/utils/WebController.ets` 中的 `SERVER_URL`

```typescript
// 开发环境（电脑局域网 IP）
export const SERVER_URL = 'http://192.168.x.x:5000';

// 生产环境（域名）
// export const SERVER_URL = 'https://your-domain.com';
```

## 构建与运行

### 真机调试

1. 手机开启开发者模式 → 连接 USB
2. DevEco Studio 中选择设备 → 点击运行
3. 确保电脑上的 Flask 后端已启动：
   ```bash
   cd ../server
   python app.py
   ```

### 打包发布

1. 配置签名证书（华为开发者联盟申请）
2. 构建 HAP/APP 包

## 项目结构

```
harmonyos/
├── AppScope/                          # 应用级配置
│   └── app.json5                      # 应用全局配置
├── entry/                             # 应用主模块
│   ├── src/main/
│   │   ├── ets/
│   │   │   ├── entryability/          # Ability 生命周期
│   │   │   ├── pages/                 # 页面组件
│   │   │   │   └── Index.ets          # 主页面（WebView）
│   │   │   └── utils/                 # 工具函数
│   │   ├── module.json5               # 模块配置
│   │   └── resources/                 # 资源文件
│   ├── build-profile.json5            # 构建配置
│   └── oh-package.json5               # 包管理
├── build-profile.json5                # 项目构建配置
├── hvigor/                            # Hvigor 构建工具配置
├── local.properties                   # 本地环境配置
├── oh-package.json5                   # 项目包管理
└── .gitignore
```

## 参赛亮点

### 鸿蒙特性运用

| 特性 | 应用场景 | 实现方式 |
|------|---------|---------|
| Web 组件 | 加载现有 Web 前端 | @kit.ArkWeb WebviewController |
| 沉浸式窗口 | 全屏无边框体验 | window.setWindowLayoutFullScreen |
| Stage 模型 | 应用生命周期管理 | UIAbility + WindowStage |
| 多语言 | 中英文自动适配 | resources/ base / en_US / zh_CN |
| 本地存储 | 偏好设置持久化 | @kit.ArkData Preferences |
| 响应式布局 | 适配手机/平板/2in1 | deviceTypes 配置 |

### 创新点

1. **Web + 原生混合架构**：保留完整 Web 功能的同时获得原生体验
2. **智能错误容灾**：网络异常时自动提示并检查后端状态
3. **跨屏适配**：一套代码同时适配手机、平板、2in1 设备
4. **职业数据本地缓存**：Preferences 保存用户数据，减少网络依赖

## 贡献指南

欢迎提交 Issue 和 PR，共同完善职画鸿蒙版！
