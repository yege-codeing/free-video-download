import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.video_service import (
    parse_video,
    download_video,
    cleanup_file,
    cleanup_old_files,
    get_platforms,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_old_files()
    yield


app = FastAPI(title="万能视频下载 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParseRequest(BaseModel):
    url: str


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: dict | list | None = None


@app.post("/api/parse")
async def api_parse(req: ParseRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="请输入视频链接")
    try:
        data = await parse_video(url)
        return {"code": 0, "message": "success", "data": data}
    except Exception as e:
        return {"code": -1, "message": f"解析失败：{str(e)}", "data": None}


@app.get("/api/download")
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


@app.get("/api/platforms")
async def api_platforms():
    return {"code": 0, "data": get_platforms()}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
