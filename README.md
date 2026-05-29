# SaveAny - 万能视频下载器

一键下载全网视频，支持 B站、抖音、YouTube 等 1800+ 平台，高清无水印。

## 技术栈

- **前端**: Vue 3 + Vite + TailwindCSS
- **后端**: Python FastAPI + yt-dlp（抖音使用自研 SSR 解析，见 [docs/douyin-download-fix.md](docs/douyin-download-fix.md)）
- **无数据库**: 轻量设计，无需任何数据库

## 支持平台

B站 / 抖音 / YouTube / TikTok / 小红书 / X(Twitter) / Instagram / Facebook / 爱奇艺 / 优酷 及 1800+ 其他网站

## 快速启动

### 前置要求

- Python 3.11+
- Node.js 18+
- FFmpeg（[安装指南](https://ffmpeg.org/download.html)，Windows 可用 `winget install Gyan.FFmpeg`）

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
│   ├── requirements.md     # 需求分析
│   ├── design.md           # 方案设计
│   └── douyin-download-fix.md  # 抖音下载问题根因与修复方案
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── components/     # UI 组件
│   │   ├── composables/    # 组合式函数
│   │   ├── api/            # API 封装
│   │   ├── App.vue
│   │   └── style.css       # 全局样式 + 主题
│   └── vite.config.js
├── backend/                # Python 后端
│   ├── main.py             # FastAPI 入口
│   ├── services/
│   │   ├── video_service.py  # 视频服务统一入口
│   │   └── douyin_service.py # 抖音 SSR 解析与下载
│   └── requirements.txt
└── README.md
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/parse | 解析视频链接，返回元数据 |
| GET | /api/download | 下载视频，流式返回文件 |
| GET | /api/platforms | 获取支持的平台列表 |
| GET | /api/health | 健康检查 |

## 后续规划 (V2)

- AI 视频总结
- 字幕提取与翻译
- 批量下载
- 视频编辑
- 付费会员系统

## 声明

本项目基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 开源项目构建，仅供个人学习使用。请遵守相关平台的服务条款。
