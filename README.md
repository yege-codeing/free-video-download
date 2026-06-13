# SaveAny - 万能视频下载器

一键下载全网视频，支持 B站、抖音、YouTube 等 1800+ 平台，高清无水印；内置 AI 视频总结。

## 技术栈

- **前端**: Vue 3 + Vite + TailwindCSS
- **后端**: Python FastAPI + yt-dlp（抖音使用自研 SSR 解析，见 [docs/douyin-download-fix.md](docs/douyin-download-fix.md)）
- **无数据库**: 轻量设计，登录账号通过环境变量配置

## 支持平台

B站 / 抖音 / YouTube / TikTok / 小红书 / X(Twitter) / Instagram / Facebook / 爱奇艺 / 优酷 及 1800+ 其他网站

## 快速启动

### 前置要求

- Python 3.11+
- Node.js 18+
- FFmpeg（[安装指南](https://ffmpeg.org/download.html)，Windows 可用 `winget install Gyan.FFmpeg`）

### 配置登录（可选）

复制环境变量模板并配置账号（默认开启登录门禁）：

```bash
cd backend
copy .env.example .env   # Windows
# 编辑 .env，至少设置：
# AUTH_USERNAME=admin
# AUTH_PASSWORD=你的密码
# AUTH_SESSION_SECRET=随机32位以上字符串
```

本地开发可设 `AUTH_ENABLED=false` 跳过登录。详见 [docs/auth-login-design.md](docs/auth-login-design.md)。

### 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API 文档: http://localhost:8000/docs

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问: http://localhost:5173

## 项目结构

```
free-video-download/
├── docs/                   # 项目文档
│   ├── requirements.md       # 需求分析
│   ├── design.md           # 架构设计
│   ├── auth-login-design.md  # 登录功能方案与实现
│   ├── ai-summary-design.md  # AI 总结方案
│   ├── operations.md       # 开发/部署操作指南
│   └── douyin-download-fix.md  # 抖音下载修复方案
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── components/     # UI 组件（含 LoginPage）
│   │   ├── composables/    # 组合式函数（含 useAuth）
│   │   ├── api/            # API 封装（含 auth.js）
│   │   ├── App.vue
│   │   └── style.css       # 全局样式 + 主题
│   └── vite.config.js
├── backend/                # Python 后端
│   ├── main.py             # FastAPI 入口
│   ├── services/
│   │   ├── video_service.py  # 视频服务统一入口
│   │   ├── auth_service.py   # 登录验证码与鉴权
│   │   └── douyin_service.py # 抖音 SSR 解析与下载
│   └── requirements.txt
└── README.md
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/auth/captcha | 获取登录验证码 |
| POST | /api/auth/login | 登录（账号+密码+验证码） |
| GET | /api/auth/me | 当前登录状态 |
| POST | /api/auth/logout | 退出登录 |
| POST | /api/parse | 解析视频链接，返回元数据 |
| GET | /api/download | 下载视频，流式返回文件 |
| POST | /api/transcript | 提取字幕（AI 总结） |
| POST | /api/summarize | SSE 流式 AI 总结 |
| POST | /api/chat | SSE AI 追问 |
| GET | /api/platforms | 获取支持的平台列表 |
| GET | /api/ai-status | AI / ASR 配置状态 |
| GET | /api/health | 健康检查 |

> `AUTH_ENABLED=true` 时，除 auth 接口与 `/api/health` 外，所有业务 API 需有效 Session Cookie。

## 功能概览

- **视频下载**：粘贴链接 → 解析 → 选择格式 → 本地下载
- **AI 总结**：字幕提取 → 流式总结 → 章节 / 思维导图 / 追问
- **登录门禁**：单账号 + 验证码，Session Cookie 鉴权

## 后续规划

- 字幕提取与翻译
- 批量下载
- 视频编辑
- 付费会员系统

## 声明

本项目基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 开源项目构建，仅供个人学习使用。请遵守相关平台的服务条款。
