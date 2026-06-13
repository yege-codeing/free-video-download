import os
import json
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

import config
from services.video_service import (
    parse_video,
    download_video,
    cleanup_file,
    cleanup_old_files,
    get_platforms,
)
from services.transcript_service import get_transcript, NoSubtitleError
from services import ai_service
from services import auth_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_old_files()
    yield


app = FastAPI(title="万能视频下载 API", version="1.0.0", lifespan=lifespan)


async def require_auth(request: Request) -> None:
    if not config.is_auth_enabled():
        return
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="未登录")


app.add_middleware(
    SessionMiddleware,
    secret_key=config.get_auth_session_secret(),
    max_age=config.get_auth_session_max_age(),
    same_site="lax",
    https_only=False,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParseRequest(BaseModel):
    url: str


class TranscriptRequest(BaseModel):
    url: str


class SummarizeRequest(BaseModel):
    title: str = ""
    segments: list[dict] = []


class ChatRequest(BaseModel):
    full_text: str = ""
    history: list[dict] = []
    question: str


class LoginRequest(BaseModel):
    username: str
    password: str
    captcha: str


def _sse(event_iter):
    """Serialize event dicts to the text/event-stream wire format."""
    for evt in event_iter:
        name = evt.get("event", "message")
        payload = json.dumps(evt.get("data", {}), ensure_ascii=False)
        yield f"event: {name}\ndata: {payload}\n\n"


_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: dict | list | None = None


@app.get("/api/auth/captcha")
async def api_auth_captcha(request: Request):
    image = auth_service.create_captcha(request.session)
    return {"code": 0, "message": "success", "data": {"image": image}}


@app.post("/api/auth/login")
async def api_auth_login(request: Request, req: LoginRequest):
    if not config.is_auth_enabled():
        return {"code": 0, "message": "登录成功", "data": {"username": req.username}}

    lock_msg = auth_service.check_login_allowed(request)
    if lock_msg:
        return {"code": -1, "message": lock_msg, "data": None}

    if not auth_service.verify_captcha(request.session, req.captcha):
        auth_service.record_login_failure(request)
        return {"code": -1, "message": "验证码错误", "data": None}

    if not auth_service.authenticate(req.username, req.password):
        auth_service.record_login_failure(request)
        return {"code": -1, "message": "账号或密码错误", "data": None}

    auth_service.clear_login_attempts(request)
    request.session.clear()
    request.session["authenticated"] = True
    request.session["username"] = config.get_auth_username()
    request.session["login_at"] = int(time.time())
    return {
        "code": 0,
        "message": "登录成功",
        "data": {"username": config.get_auth_username()},
    }


@app.get("/api/auth/me")
async def api_auth_me(request: Request):
    if not config.is_auth_enabled():
        return {
            "code": 0,
            "data": {"authenticated": True, "username": "dev", "auth_enabled": False},
        }
    authenticated = bool(request.session.get("authenticated"))
    return {
        "code": 0,
        "data": {
            "authenticated": authenticated,
            "username": request.session.get("username", "") if authenticated else "",
            "auth_enabled": True,
        },
    }


@app.post("/api/auth/logout")
async def api_auth_logout(request: Request):
    request.session.clear()
    return {"code": 0, "message": "已退出登录", "data": None}


@app.post("/api/parse", dependencies=[Depends(require_auth)])
async def api_parse(req: ParseRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="请输入视频链接")
    try:
        data = await parse_video(url)
        return {"code": 0, "message": "success", "data": data}
    except Exception as e:
        return {"code": -1, "message": f"解析失败：{str(e)}", "data": None}


@app.get("/api/download", dependencies=[Depends(require_auth)])
async def api_download(url: str, format_id: str, background_tasks: BackgroundTasks):
    if not url or not format_id:
        raise HTTPException(status_code=400, detail="缺少参数")
    try:
        filepath, filename = await download_video(url, format_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败：{str(e)}")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=500, detail="文件生成失败")

    file_size = os.path.getsize(filepath)

    def iter_file():
        with open(filepath, "rb") as f:
            while chunk := f.read(1024 * 1024):  # 1MB chunks
                yield chunk

    background_tasks.add_task(cleanup_file, filepath)

    # Encode filename for Content-Disposition header
    from urllib.parse import quote
    encoded_filename = quote(filename)

    return StreamingResponse(
        iter_file(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Content-Length": str(file_size),
        },
    )


@app.post("/api/transcript", dependencies=[Depends(require_auth)])
async def api_transcript(req: TranscriptRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="请输入视频链接")
    if not config.is_ai_configured():
        return {"code": -2, "message": "未配置 MiniMax API Key，AI 功能不可用", "data": None}
    try:
        data = await get_transcript(url)
        return {"code": 0, "message": "success", "data": data}
    except NoSubtitleError as e:
        return {"code": 1, "message": str(e), "data": None}
    except Exception as e:
        return {"code": -1, "message": f"字幕提取失败：{str(e)}", "data": None}


@app.post("/api/summarize", dependencies=[Depends(require_auth)])
async def api_summarize(req: SummarizeRequest):
    if not req.segments:
        raise HTTPException(status_code=400, detail="缺少字幕内容")
    return StreamingResponse(
        _sse(ai_service.summarize_stream(req.title, req.segments)),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@app.post("/api/chat", dependencies=[Depends(require_auth)])
async def api_chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="请输入问题")
    if not req.full_text.strip():
        raise HTTPException(status_code=400, detail="缺少视频字幕上下文")
    return StreamingResponse(
        _sse(ai_service.chat_stream(req.full_text, req.history, req.question)),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@app.get("/api/platforms", dependencies=[Depends(require_auth)])
async def api_platforms():
    return {"code": 0, "data": get_platforms()}


@app.get("/api/ai-status", dependencies=[Depends(require_auth)])
async def api_ai_status():
    return {"code": 0, "data": config.get_ai_status_detail()}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
