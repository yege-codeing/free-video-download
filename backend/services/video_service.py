import os
import re
import uuid
import tempfile
import asyncio
from urllib.parse import urlparse, parse_qs

import yt_dlp

from services.ffmpeg_utils import get_ffmpeg_path, is_ffmpeg_available


TEMP_DIR = os.path.join(tempfile.gettempdir(), "video-downloads")
os.makedirs(TEMP_DIR, exist_ok=True)

PLATFORM_MAP = {
    "bilibili.com": ("bilibili", "B站"),
    "b23.tv": ("bilibili", "B站"),
    "douyin.com": ("douyin", "抖音"),
    "youtube.com": ("youtube", "YouTube"),
    "youtu.be": ("youtube", "YouTube"),
    "tiktok.com": ("tiktok", "TikTok"),
    "xiaohongshu.com": ("xiaohongshu", "小红书"),
    "xhslink.com": ("xiaohongshu", "小红书"),
    "twitter.com": ("twitter", "X/Twitter"),
    "x.com": ("twitter", "X/Twitter"),
    "instagram.com": ("instagram", "Instagram"),
    "facebook.com": ("facebook", "Facebook"),
    "iqiyi.com": ("iqiyi", "爱奇艺"),
    "youku.com": ("youku", "优酷"),
}

SUPPORTED_PLATFORMS = [
    {"id": "bilibili", "name": "B站", "icon": "bilibili", "color": "#00A1D6"},
    {"id": "douyin", "name": "抖音", "icon": "douyin", "color": "#000000"},
    {"id": "youtube", "name": "YouTube", "icon": "youtube", "color": "#FF0000"},
    {"id": "tiktok", "name": "TikTok", "icon": "tiktok", "color": "#010101"},
    {"id": "xiaohongshu", "name": "小红书", "icon": "xiaohongshu", "color": "#FF2442"},
    {"id": "twitter", "name": "X/Twitter", "icon": "twitter", "color": "#1DA1F2"},
    {"id": "instagram", "name": "Instagram", "icon": "instagram", "color": "#E4405F"},
    {"id": "facebook", "name": "Facebook", "icon": "facebook", "color": "#1877F2"},
    {"id": "more", "name": "1800+更多", "icon": "more", "color": "#888888"},
]


def _detect_platform(url: str) -> tuple[str, str]:
    try:
        hostname = urlparse(url).hostname or ""
        for domain, (pid, label) in PLATFORM_MAP.items():
            if domain in hostname:
                return pid, label
    except Exception:
        pass
    return "other", "其他平台"


def _is_bilibili(url: str) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    return "bilibili.com" in hostname or hostname == "b23.tv"


def _normalize_bilibili_url(url: str) -> str:
    """Strip tracking params; canonicalize BV/av video URLs for yt-dlp."""
    hostname = (urlparse(url).hostname or "").lower()
    if "bilibili.com" not in hostname:
        return url

    bv_match = re.search(r"(BV[\w]+)", url)
    if bv_match:
        # BV IDs are base58 — case-sensitive; do not upper-case
        return f"https://www.bilibili.com/video/{bv_match.group(1)}"

    av_match = re.search(r"/video/av(\d+)", url, re.I)
    if av_match:
        return f"https://www.bilibili.com/video/av{av_match.group(1)}"

    return url.split("?")[0].rstrip("/")


def _shared_ydl_opts(*, for_download: bool = False) -> dict:
    """Network options shared by parse/download (Bilibili often needs longer timeouts)."""
    opts = {
        "socket_timeout": 60,
        "retries": 3,
        "http_headers": {
            "Referer": "https://www.bilibili.com",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        },
    }
    if for_download:
        ffmpeg = get_ffmpeg_path()
        if ffmpeg:
            # yt-dlp needs the full executable path when using bundled ffmpeg
            opts["ffmpeg_location"] = ffmpeg
    return opts


def _normalize_url(url: str) -> str:
    """Convert non-standard platform URLs to yt-dlp compatible formats."""
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    # Douyin: normalize short links and modal_id URLs to /video/{id}
    if "douyin.com" in hostname or hostname in ("v.douyin.com", "www.iesdouyin.com", "iesdouyin.com"):
        from services.douyin_service import resolve_douyin_url, extract_aweme_id

        url = resolve_douyin_url(url)
        aweme_id = extract_aweme_id(url)
        if aweme_id:
            return f"https://www.douyin.com/video/{aweme_id}"

    if _is_bilibili(url):
        return _normalize_bilibili_url(url)

    return url


def _is_douyin(url: str) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    return "douyin.com" in hostname


def _format_filesize(size_bytes) -> str:
    if not size_bytes:
        return "未知大小"
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _format_duration(seconds) -> str:
    if not seconds:
        return "未知时长"
    seconds = int(seconds)
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name[:100].strip() or "video"


def _codec_priority(fmt: dict) -> int:
    """Prefer H.264 for broader player compatibility when resolutions tie."""
    vcodec = (fmt.get("vcodec") or "").lower()
    if "avc" in vcodec or "h264" in vcodec:
        return 0
    if "hev" in vcodec or "h265" in vcodec:
        return 1
    if "av01" in vcodec or "av1" in vcodec:
        return 2
    return 3


def _build_format_list(info: dict) -> list[dict]:
    """Build a simplified, deduplicated format list from yt-dlp info."""
    formats_raw = info.get("formats") or []
    if not formats_raw:
        return [{"format_id": "best", "label": "最佳画质", "ext": "mp4",
                 "resolution": None, "filesize": None, "filesize_str": "未知大小"}]

    seen_resolutions = set()
    result = []

    # Sort by quality descending; prefer H.264 at the same resolution (e.g. Bilibili DASH)
    sorted_fmts = sorted(
        formats_raw,
        key=lambda f: (
            f.get("height") or 0,
            f.get("tbr") or 0,
            -_codec_priority(f),
        ),
        reverse=True,
    )

    for fmt in sorted_fmts:
        height = fmt.get("height")
        vcodec = fmt.get("vcodec", "none")
        acodec = fmt.get("acodec", "none")
        has_video = vcodec and vcodec != "none"
        has_audio = acodec and acodec != "none"

        if has_video and height:
            res_key = height
            if res_key in seen_resolutions:
                continue
            seen_resolutions.add(res_key)

            label_map = {2160: "4K 超清", 1440: "2K 高清", 1080: "1080P 高清",
                         720: "720P", 480: "480P 标清", 360: "360P", 240: "240P"}
            label = label_map.get(height, f"{height}P")
            width = fmt.get("width") or 0
            filesize = fmt.get("filesize") or fmt.get("filesize_approx")

            result.append({
                "format_id": fmt.get("format_id", "best"),
                "label": label,
                "ext": fmt.get("ext", "mp4"),
                "resolution": f"{width}x{height}" if width else f"{height}P",
                "filesize": filesize,
                "filesize_str": _format_filesize(filesize),
            })

        if len(result) >= 6:
            break

    # Always add a "best" option at the top
    best_entry = {
        "format_id": "best",
        "label": "最佳画质（推荐）",
        "ext": "mp4",
        "resolution": None,
        "filesize": None,
        "filesize_str": "自动选择",
    }
    result.insert(0, best_entry)

    # Add audio-only option
    result.append({
        "format_id": "audio_only",
        "label": "仅音频 (MP3)",
        "ext": "mp3",
        "resolution": None,
        "filesize": None,
        "filesize_str": "未知大小",
    })

    return result


# Bilibili DASH: prefer H.264 for player compatibility (AV1/HEVC often won't play)
_BILI_BEST_VIDEO = "bestvideo[vcodec^=avc1]/bestvideo[vcodec^=hev1]/bestvideo/best"
_BILI_BEST_MERGE = "bestvideo[vcodec^=avc1]+bestaudio/best"


def _build_download_format(url: str, format_id: str) -> dict:
    """Map UI format choice to yt-dlp format selector (Bilibili uses separate A/V streams)."""
    dash_only = _is_bilibili(url)
    can_merge = is_ffmpeg_available()

    if format_id == "audio_only":
        if can_merge:
            return {
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
        return {"format": "bestaudio/best"}

    if format_id == "best":
        if can_merge:
            if dash_only:
                return {
                    "format": _BILI_BEST_MERGE,
                    "merge_output_format": "mp4",
                }
            return {
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
            }
        if dash_only:
            return {"format": _BILI_BEST_VIDEO}
        return {"format": "best"}

    if can_merge:
        return {
            "format": f"{format_id}+bestaudio/{format_id}/best",
            "merge_output_format": "mp4",
        }
    if dash_only:
        return {"format": format_id}
    return {"format": f"{format_id}/best"}


async def parse_video(url: str) -> dict:
    """Extract video metadata without downloading."""
    url = _normalize_url(url)

    if _is_douyin(url):
        from services.douyin_service import parse_douyin

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, parse_douyin, url)
        result.pop("_douyin_aweme_id", None)
        return result

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignoreerrors": False,
        "no_color": True,
        **_shared_ydl_opts(),
    }

    loop = asyncio.get_event_loop()

    def _extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    info = await loop.run_in_executor(None, _extract)
    if not info:
        raise ValueError("无法解析该视频链接")

    platform_id, platform_label = _detect_platform(url)

    return {
        "title": info.get("title", "未知标题"),
        "thumbnail": info.get("thumbnail", ""),
        "duration": info.get("duration"),
        "duration_str": _format_duration(info.get("duration")),
        "author": info.get("uploader") or info.get("channel") or "未知作者",
        "platform": platform_id,
        "platform_label": platform_label,
        "formats": _build_format_list(info),
    }


async def download_video(url: str, format_id: str) -> tuple[str, str]:
    """Download video and return (file_path, filename)."""
    url = _normalize_url(url)

    if _is_douyin(url):
        from services.douyin_service import download_douyin

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, download_douyin, url, format_id)

    unique_id = uuid.uuid4().hex[:8]
    outtmpl = os.path.join(TEMP_DIR, f"{unique_id}_%(title)s.%(ext)s")

    base_opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": outtmpl,
        "abort_on_error": False,
        "noprogress": True,
        **_shared_ydl_opts(for_download=True),
    }

    base_opts.update(_build_download_format(url, format_id))

    loop = asyncio.get_event_loop()

    def _download():
        with yt_dlp.YoutubeDL(base_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise ValueError("下载失败")

            filepath = ydl.prepare_filename(info)
            if format_id == "audio_only":
                mp3_path = os.path.splitext(filepath)[0] + ".mp3"
                if os.path.exists(mp3_path):
                    filepath = mp3_path
            if not os.path.exists(filepath):
                for ext in [".mp4", ".mkv", ".webm"]:
                    alt = os.path.splitext(filepath)[0] + ext
                    if os.path.exists(alt):
                        filepath = alt
                        break
            if not os.path.exists(filepath):
                for f in os.listdir(TEMP_DIR):
                    if f.startswith(unique_id):
                        filepath = os.path.join(TEMP_DIR, f)
                        break
            if not os.path.exists(filepath):
                raise ValueError("下载完成但找不到文件")
            title = _sanitize_filename(info.get("title", "video"))
            ext = os.path.splitext(filepath)[1] or ".mp4"
            return filepath, f"{title}{ext}"

    return await loop.run_in_executor(None, _download)


def cleanup_file(filepath: str):
    """Remove a temporary file."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except OSError:
        pass


def cleanup_old_files(max_age_seconds: int = 3600):
    """Remove temp files older than max_age_seconds."""
    import time
    now = time.time()
    try:
        for f in os.listdir(TEMP_DIR):
            fpath = os.path.join(TEMP_DIR, f)
            if os.path.isfile(fpath) and now - os.path.getmtime(fpath) > max_age_seconds:
                os.remove(fpath)
    except OSError:
        pass


def get_platforms() -> list[dict]:
    return SUPPORTED_PLATFORMS
