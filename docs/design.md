# 万能视频下载网站 - 方案设计文档

> 版本：V1.0  
> 创建日期：2026-05-19  
> 状态：已确认

---

## 一、系统架构

### 1.1 整体架构

采用前后端分离架构，前端负责界面展示和用户交互，后端负责视频解析和下载处理。

```
┌─────────────────────────────────────────────────────┐
│                    用户浏览器                         │
│  ┌───────────────────────────────────────────────┐  │
│  │           Vue 3 前端应用 (SPA)                 │  │
│  │  ┌─────────┐ ┌──────────┐ ┌───────────────┐  │  │
│  │  │URL输入   │ │视频信息卡│ │格式选择/下载   │  │  │
│  │  └────┬────┘ └────▲─────┘ └───────┬───────┘  │  │
│  │       │           │               │           │  │
│  │       ▼           │               ▼           │  │
│  │  ┌────────────────┴───────────────────────┐   │  │
│  │  │          Axios HTTP 客户端              │   │  │
│  │  └────────────────┬───────────────────────┘   │  │
│  └───────────────────┼───────────────────────────┘  │
└──────────────────────┼──────────────────────────────┘
                       │ HTTP API
┌──────────────────────┼──────────────────────────────┐
│                      ▼                               │
│  ┌───────────────────────────────────────────────┐  │
│  │           FastAPI 后端服务                      │  │
│  │  ┌─────────────┐  ┌────────────────────────┐  │  │
│  │  │ API 路由层   │  │   CORS 中间件          │  │  │
│  │  └──────┬──────┘  └────────────────────────┘  │  │
│  │         ▼                                      │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │         视频服务层 (VideoService)         │  │  │
│  │  │  ┌───────────┐  ┌───────────────────┐   │  │  │
│  │  │  │ 解析视频   │  │ 下载视频+流式传输  │   │  │  │
│  │  │  └─────┬─────┘  └────────┬──────────┘   │  │  │
│  │  └────────┼─────────────────┼──────────────┘  │  │
│  │           ▼                 ▼                  │  │
│  │  ┌──────────────┐  ┌─────────────────────┐  │  │
│  │  │ douyin_service│  │ yt-dlp（其它平台）   │  │  │
│  │  │ SSR 解析抖音  │  │                     │  │  │
│  │  └──────────────┘  └─────────────────────┘  │  │
│  │                    │                           │  │
│  │  ┌─────────────────▼───────────────────────┐  │  │
│  │  │        临时文件目录 (/tmp/downloads)      │  │  │
│  │  │        (定时清理，不持久化存储)            │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
│                  Python 后端服务器                    │
└─────────────────────────────────────────────────────┘
```

### 1.2 技术栈

| 层级 | 技术选型 | 版本 | 选型理由 |
|------|---------|------|---------|
| 前端框架 | Vue 3 (Composition API) | 3.x | 轻量、响应式好、中文生态强 |
| 构建工具 | Vite | 6.x | 极速 HMR，开发体验好 |
| CSS 框架 | TailwindCSS | 4.x | 原子化 CSS，定制性强 |
| HTTP 客户端 | Axios | 1.x | 成熟稳定，拦截器支持好 |
| 后端框架 | FastAPI | 0.115+ | 异步高性能，自动文档 |
| 视频引擎 | yt-dlp | 2026.03+ | 支持 1800+ 网站，社区活跃 |
| Python 运行时 | Python | 3.11+ | 异步支持好，性能优 |
| ASGI 服务器 | uvicorn | 0.34+ | FastAPI 官方推荐 |

### 1.3 数据流

```
用户操作流程：

1. 粘贴链接
   用户 → [粘贴URL] → 前端UrlInput组件

2. 解析视频
   前端 → POST /api/parse {url} → 后端
   后端 → yt-dlp.extract_info(url, download=False) → 返回视频元数据
   后端 → 响应 {title, thumbnail, duration, author, formats[]} → 前端
   前端 → 渲染 VideoCard + FormatSelector

3. 下载视频
   用户 → [选择格式] → [点击下载]
   前端 → GET /api/download?url=xxx&format_id=xxx → 后端
   后端 → yt-dlp.download(url, format) → 临时文件
   后端 → StreamingResponse(临时文件) → 前端
   浏览器 → 触发文件下载保存对话框
   后端 → 清理临时文件
```

## 二、后端设计

### 2.1 API 接口设计

#### POST /api/parse

解析视频链接，返回视频元数据。

**请求：**
```json
{
  "url": "https://www.bilibili.com/video/BVxxxxxxxxxx"
}
```

**成功响应 (200)：**
```json
{
  "code": 0,
  "data": {
    "title": "视频标题",
    "thumbnail": "https://xxx/cover.jpg",
    "duration": 180,
    "duration_str": "03:00",
    "author": "UP主名称",
    "platform": "bilibili",
    "platform_label": "B站",
    "formats": [
      {
        "format_id": "137+140",
        "label": "1080P 高清",
        "ext": "mp4",
        "resolution": "1920x1080",
        "filesize": 52428800,
        "filesize_str": "50.0 MB",
        "vcodec": "avc1",
        "acodec": "mp4a"
      },
      {
        "format_id": "136+140",
        "label": "720P",
        "ext": "mp4",
        "resolution": "1280x720",
        "filesize": 31457280,
        "filesize_str": "30.0 MB",
        "vcodec": "avc1",
        "acodec": "mp4a"
      },
      {
        "format_id": "audio_best",
        "label": "仅音频 (MP3)",
        "ext": "mp3",
        "resolution": null,
        "filesize": 5242880,
        "filesize_str": "5.0 MB",
        "vcodec": "none",
        "acodec": "mp4a"
      }
    ]
  }
}
```

**错误响应 (400/500)：**
```json
{
  "code": -1,
  "message": "不支持的视频链接，请检查 URL 是否正确"
}
```

#### GET /api/download

下载视频文件，以流式方式返回。

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 是 | 视频 URL |
| format_id | string | 是 | 格式 ID（从 parse 接口获取） |

**响应：** `application/octet-stream` 文件流

**响应头：**
```
Content-Disposition: attachment; filename="视频标题.mp4"
Content-Type: application/octet-stream
Content-Length: 52428800
```

#### GET /api/platforms

获取支持的平台列表。

**响应 (200)：**
```json
{
  "code": 0,
  "data": [
    { "id": "bilibili", "name": "B站", "icon": "bilibili", "color": "#00A1D6" },
    { "id": "douyin", "name": "抖音", "icon": "douyin", "color": "#000000" },
    { "id": "youtube", "name": "YouTube", "icon": "youtube", "color": "#FF0000" },
    { "id": "tiktok", "name": "TikTok", "icon": "tiktok", "color": "#010101" },
    { "id": "xiaohongshu", "name": "小红书", "icon": "xiaohongshu", "color": "#FF2442" },
    { "id": "twitter", "name": "X/Twitter", "icon": "twitter", "color": "#1DA1F2" },
    { "id": "instagram", "name": "Instagram", "icon": "instagram", "color": "#E4405F" },
    { "id": "more", "name": "更多平台", "icon": "more", "color": "#888888" }
  ]
}
```

### 2.2 核心服务层

`backend/services/video_service.py` — 统一入口；抖音分流至 `douyin_service.py`，其余平台封装 yt-dlp：

`backend/services/douyin_service.py` — 抖音 SSR 解析与直链下载（见 [douyin-download-fix.md](./douyin-download-fix.md)）

`video_service.py` 主要职责：

```python
class VideoService:
    """yt-dlp 封装服务"""
    
    async def parse_video(url: str) -> dict:
        """解析视频信息，不下载"""
        # 调用 yt-dlp extract_info
        # 格式化返回数据
        
    async def download_video(url: str, format_id: str) -> str:
        """下载视频到临时目录，返回文件路径"""
        # 调用 yt-dlp download
        # 返回临时文件路径
        
    def cleanup_file(filepath: str):
        """清理临时文件"""
        
    def _format_filesize(size_bytes: int) -> str:
        """格式化文件大小"""
        
    def _detect_platform(url: str) -> tuple[str, str]:
        """根据 URL 识别平台"""
```

### 2.3 临时文件管理

- 下载目录：`/tmp/video-downloads/` (系统临时目录)
- 文件命名：`{uuid}_{sanitized_title}.{ext}`
- 清理策略：下载完成流式传输后立即删除
- 备用清理：启动时清理超过 1 小时的残留文件

## 三、前端设计

> **V2 交互式产品演示布局**（2026-06-13）：详见 [interactive-product-demo-design.md](interactive-product-demo-design.md)。

### 3.1 UI 设计规范

#### 配色方案

```
主色调（暗色背景系列）：
  - 主背景:     #0B0B0F  (近黑色，带微蓝)
  - 次背景:     #16161D  (深灰，用于卡片)
  - 三级背景:   #1E1E28  (稍浅灰，用于输入框)
  - 边框色:     #2A2A35  (微妙的分隔线)

强调色（暖色渐变系列）：
  - 主强调色:   #FF6B6B  (珊瑚橙)
  - 渐变终点:   #FFD93D  (琥珀金)
  - 渐变方向:   135deg (左上到右下)
  - 悬浮态:     增加亮度 10%

文字色：
  - 主文字:     #F0F0F0  (几乎纯白)
  - 次文字:     #9CA3AF  (灰色)
  - 三级文字:   #6B7280  (更浅灰)
  - 强调文字:   渐变色 (与强调色一致)

状态色：
  - 成功:       #10B981
  - 警告:       #F59E0B
  - 错误:       #EF4444
  - 信息:       #3B82F6
```

#### 字体

```
标题字体:  "Inter", "PingFang SC", "Microsoft YaHei", sans-serif
正文字体:  "Inter", "PingFang SC", "Microsoft YaHei", sans-serif
等宽字体:  "JetBrains Mono", "Fira Code", monospace
```

#### 圆角和阴影

```
圆角:
  - 小圆角:   8px  (标签、小按钮)
  - 中圆角:   12px (卡片)
  - 大圆角:   16px (输入框、大按钮)
  - 全圆角:   9999px (药丸形状)

阴影:
  - 卡片阴影:   0 4px 24px rgba(0, 0, 0, 0.3)
  - 悬浮阴影:   0 8px 32px rgba(0, 0, 0, 0.4)
  - 光晕效果:   0 0 20px rgba(255, 107, 107, 0.15)  (输入框聚焦)
```

#### 毛玻璃效果

```css
.glass-card {
  background: rgba(22, 22, 29, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.05);
}
```

### 3.2 组件设计

#### 组件树

```
App.vue
├── NavBar.vue                 # 顶部导航栏
│   ├── Logo
│   └── 导航链接
├── HeroSection.vue            # 英雄区域
│   ├── 渐变标题
│   ├── 副标题
│   └── UrlInput.vue           # 核心输入组件
│       ├── 输入框 (发光边框)
│       └── 解析按钮
├── PlatformIcons.vue          # 支持平台图标行
├── VideoCard.vue              # 视频信息卡片 (解析后显示)
│   ├── 封面缩略图
│   ├── 视频元信息
│   └── FormatSelector.vue     # 格式选择器
│       ├── 格式列表
│       └── 下载按钮
├── ComingSoon.vue             # 即将上线功能预告
├── Footer.vue                 # 页脚
└── LoadingOverlay.vue         # 全局加载遮罩
```

#### 关键交互状态

```
页面状态流转：

[空闲状态] → 用户粘贴链接 → [解析中...] → 成功 → [展示视频信息]
                                          → 失败 → [显示错误提示]
                                          
[展示视频信息] → 用户选择格式 → 点击下载 → [下载中...] → 完成 → [下载成功提示]
                                                      → 失败 → [下载失败提示]
```

### 3.3 响应式断点

```
移动端:    < 640px   (sm)   — 单列布局，全宽组件
平板端:    640-1024px (md)  — 适当留白，组件宽度受限
桌面端:    > 1024px   (lg)  — 居中布局，最大宽度 960px
```

## 四、项目目录结构

```
free-video-download/
├── docs/                          # 项目文档
│   ├── requirements.md            # 需求分析文档
│   ├── design.md                  # 方案设计文档（本文档）
│   └── douyin-download-fix.md     # 抖音下载故障排查与修复说明
├── frontend/                      # Vue 3 前端
│   ├── public/                    # 静态资源
│   │   └── favicon.svg
│   ├── src/
│   │   ├── assets/                # 图片、图标等资源
│   │   ├── components/            # Vue 组件
│   │   │   ├── NavBar.vue
│   │   │   ├── HeroSection.vue
│   │   │   ├── UrlInput.vue
│   │   │   ├── VideoCard.vue
│   │   │   ├── FormatSelector.vue
│   │   │   ├── PlatformIcons.vue
│   │   │   ├── ComingSoon.vue
│   │   │   ├── Footer.vue
│   │   │   └── LoadingOverlay.vue
│   │   ├── composables/           # 组合式函数
│   │   │   └── useVideoDownload.js
│   │   ├── api/                   # API 调用封装
│   │   │   └── video.js
│   │   ├── App.vue                # 根组件
│   │   ├── main.js                # 入口文件
│   │   └── style.css              # 全局样式
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── backend/                       # Python FastAPI 后端
│   ├── main.py                    # FastAPI 入口 + 路由
│   ├── services/
│   │   ├── video_service.py       # 视频服务统一入口
│   │   └── douyin_service.py      # 抖音 SSR 解析（绕过 yt-dlp API）
│   └── requirements.txt           # Python 依赖
└── README.md                      # 项目说明
```

## 五、开发与运行

### 5.1 后端启动

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API 文档自动生成：`http://localhost:8000/docs`

### 5.2 前端启动

```bash
cd frontend
npm install
npm run dev
```

开发服务器：`http://localhost:5173`

### 5.3 前端代理配置

`vite.config.js` 中配置代理，将 `/api` 请求转发到后端：

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## 六、扩展性设计

### 6.1 后端扩展点

- **抖音专用通道**：因 yt-dlp 抖音提取器长期受 `a_bogus` API 签名限制，已实现 `services/douyin_service.py`（SSR + `RENDER_DATA`），详见 [douyin-download-fix.md](./douyin-download-fix.md)
- **新平台支持**：yt-dlp 自动更新即可覆盖新平台；对于不支持的平台（如视频号），可在 `video_service.py` 中添加自定义下载逻辑
- **AI 功能**：新增 `services/ai_service.py`，封装 AI 大模型调用
- **字幕处理**：新增 `services/subtitle_service.py`，使用 yt-dlp 的字幕提取功能 + 翻译 API
- **付费系统**：新增 `services/payment_service.py` + 引入轻量数据库（SQLite）

### 6.2 前端扩展点

- **新功能页面**：使用 Vue Router 添加新页面（视频总结、字幕翻译等）
- **付费弹窗**：新增 `components/PaymentModal.vue`
- **用户系统**：已实现 `composables/useAuth.js` + `LoginPage.vue`，详见 [auth-login-design.md](./auth-login-design.md)
- **批量下载**：扩展 `UrlInput.vue` 支持多 URL 输入

### 6.3 部署扩展

- **Docker 化**：添加 `Dockerfile` + `docker-compose.yml`
- **反向代理**：Nginx 配置静态文件服务 + API 反向代理
- **CDN**：前端静态资源上 CDN 加速
