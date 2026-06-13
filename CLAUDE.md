# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SaveAny (万能视频下载器)** — A cross-platform video downloader web app powered by yt-dlp.
- Frontend: Vue 3 + Vite + TailwindCSS 4 (SPA)
- Backend: Python FastAPI + yt-dlp
- No database; all downloads are temporary files streamed to the client

## Development Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
API docs at http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev      # dev server at http://localhost:5173
npm run build    # production build
```

The Vite dev server proxies `/api/*` to `http://localhost:8000` (configured in `vite.config.js`).

### System Requirements
- **Python 3.11+** (backend)
- **Node.js 18+** (frontend)
- **FFmpeg** — required for merging video+audio streams. Without it, downloads fall back to single-stream formats. Windows: `winget install Gyan.FFmpeg`

## Architecture

### Request Flow
```
User pastes URL
  → POST /api/parse → yt-dlp.extract_info() → metadata (title, formats)
  → User selects format
  → GET /api/download → yt-dlp downloads to temp → StreamingResponse → browser saves file
  → background_tasks.cleanup_file() deletes temp file
```

### Backend Structure
```
backend/
├── main.py              # FastAPI entry, CORS, lifespan (cleanup on start)
├── config.py            # Env config (MiniMax key/base_url/model) via python-dotenv
├── services/
│   ├── video_service.py # Core: parse_video(), download_video(), cleanup_file()
│   ├── douyin_service.py # Special handling for Douyin short links + modal URLs
│   ├── transcript_service.py # AI summary: subtitles → segments; ASR fallback
│   ├── asr_service.py   # SenseVoice via sherpa-onnx (no login, no PyTorch)
│   └── ai_service.py    # MiniMax (OpenAI-compatible): summarize_stream/chat_stream
└── requirements.txt
```

**AI summary feature (V2):** see [docs/ai-summary-design.md](docs/ai-summary-design.md).
- `transcript_service.py` extracts subtitles via yt-dlp, then Bilibili `/x/v2/dm/view` (no cookie) for official CC/AI subs, then `asr_service.py` when none exist. Bilibili requests include `Origin: https://www.bilibili.com` to avoid HTTP 412. Returns `source` / `source_label` (`subtitle` vs `asr`).
- `asr_service.py` downloads audio via yt-dlp, resamples with FFmpeg, transcribes with SenseVoice (sherpa-onnx). Model auto-downloads to `backend/models/sensevoice/` on first use (~200MB). Config: `ASR_ENABLED`, `SENSEVOICE_USE_INT8`, `ASR_MAX_DURATION_SECONDS`.
- `ai_service.py` calls MiniMax-M2.7 via the OpenAI SDK (`base_url=https://api.minimaxi.com/v1`). Streams the summary then a structured chapters+mindmap JSON; strips `<think>` reasoning.
- Requires `MINIMAX_API_KEY` in `backend/.env` (copy from `.env.example`). Download features work without it.

**Key services in `video_service.py`:**
- `_normalize_url()` — converts Douyin short/modal URLs to `/video/{id}` format
- `_is_douyin()` — Douyin gets its own service path (`douyin_service.py`)
- `_build_format_list()` — deduplicates yt-dlp formats, limits to 6 video + audio_only
- `cleanup_old_files()` — runs on server start; removes temp files > 1 hour old

**Temp files:** stored in `tempfile.gettempdir()/video-downloads/`, named `{uuid}_{title}.{ext}`

### Frontend Structure
```
frontend/src/
├── App.vue              # Root; orchestrates state via useVideoDownload composable
├── components/          # NavBar, HeroSection, DemoFrame, DemoWalkthrough, UrlInput, VideoCard, etc.
├── composables/
│   ├── useVideoDownload.js  # All video state + API calls
│   └── useVideoSummary.js   # AI summary state + SSE
├── api/
│   ├── video.js        # parseVideo(), fetchDownloadVideo(), getPlatforms()
│   └── summary.js      # getTranscript(), streamSummarize(), streamChat()
└── style.css           # CSS variables, gradients, glass-card, demo layout utilities
```

**Interactive Product Demo layout:** see [docs/interactive-product-demo-design.md](docs/interactive-product-demo-design.md).

**MindMap PNG export (`MindMap.vue`):** uses `html-to-image` `toPng()` on the viewport wrapper (not raw SVG serialization—markmap text lives in `foreignObject`). Before capture, inline `color: #ffffff` on `.markmap-foreign` nodes so export matches dark-theme display. `SummaryPanel` switches to the mindmap tab and calls `mindmapRef.exportPng()` via `TabActions`.

**Important state in `useVideoDownload`:**
- `downloadPhase`: `idle | processing | transferring | saving`
- During `processing`: the server is running yt-dlp (slow); a JS interval creeps progress toward 97% so the UI doesn't freeze
- `stopPrepProgress()` is called the moment server headers are received

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/parse` | Parse URL → metadata with format list |
| GET | `/api/download` | Stream video file (client must cleanup via `background_tasks`) |
| POST | `/api/transcript` | Extract subtitles → `segments` + `full_text` (AI summary) |
| POST | `/api/summarize` | SSE stream: summary deltas → chapters+mindmap structure |
| POST | `/api/chat` | SSE stream: stateless Q&A over the transcript |
| GET | `/api/platforms` | Static list of supported platforms |
| GET | `/api/ai-status` | Whether MiniMax API key is configured |
| GET | `/api/health` | Health check |

## Styling System

Colors and utilities are defined as CSS variables in `style.css` (used via TailwindCSS 4 `@theme`):

| Variable | Value | Use |
|----------|-------|-----|
| `--color-bg-primary` | `#0B0B0F` | Page background |
| `--color-accent` | `#FF6B6B` | Primary accent (coral) |
| `--color-accent-gold` | `#FFD93D` | Gradient endpoint (amber) |

Key utility classes: `.gradient-text`, `.gradient-bg`, `.glass-card`, `.glow-input:focus-within`, `.btn-primary`

## Adding a New Platform

yt-dlp supports most platforms automatically. For a new custom extractor:

1. Add domain → platform mapping in `PLATFORM_MAP` in `video_service.py`
2. If the platform needs special URL normalization (like Douyin), add a `_normalize_{platform}()` helper and update `_normalize_url()`
3. If yt-dlp alone isn't enough, create a new service file (e.g., `douyin_service.py`) and call it from `parse_video()` / `download_video()`
4. Add the platform to `SUPPORTED_PLATFORMS` list for the `/api/platforms` response