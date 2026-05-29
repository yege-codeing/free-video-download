"""
Douyin video extraction via signed web API.

yt-dlp's Douyin extractor and SSR RENDER_DATA scraping both fail when
Douyin serves captcha pages. This module calls aweme/detail with a_bogus
signatures and direct CDN URLs for download.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import string
import time
import uuid
import tempfile
import http.cookiejar
import urllib.parse
import urllib.request as urllib_req
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from services.douyin_abogus import generate_a_bogus

TEMP_DIR = os.path.join(tempfile.gettempdir(), "video-downloads")
os.makedirs(TEMP_DIR, exist_ok=True)

_DOUYIN_COOKIES_FILE = os.path.join(TEMP_DIR, "douyin_cookies.txt")
_DOUYIN_COOKIES_EXPIRY = 0.0

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
_RENDER_DATA_RE = re.compile(
    r'<script id="RENDER_DATA"[^>]*>([^<]+)</script>',
    re.DOTALL,
)
_AWEME_DETAIL_API = "https://www.douyin.com/aweme/v1/web/aweme/detail/"


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


def _fetch_ttwid() -> str | None:
    body = json.dumps({
        "region": "cn", "aid": 1128, "needFid": False,
        "service": "www.douyin.com",
        "migrate_info": {"ticket": "", "source": "node"},
        "cbUrlProtocol": "https", "union": True,
    }).encode()
    req = urllib_req.Request(
        "https://ttwid.bytedance.com/ttwid/union/register/",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib_req.urlopen(req, timeout=10)
        for cookie_header in resp.headers.get_all("Set-Cookie") or []:
            if "ttwid=" in cookie_header:
                return cookie_header.split("ttwid=")[1].split(";")[0]
    except OSError:
        pass
    return None


def _generate_s_v_web_id() -> str:
    return f"verify_{uuid.uuid4().hex}"


def _fetch_douyin_cookies() -> str | None:
    global _DOUYIN_COOKIES_EXPIRY
    if os.path.exists(_DOUYIN_COOKIES_FILE) and time.time() < _DOUYIN_COOKIES_EXPIRY:
        return _DOUYIN_COOKIES_FILE

    jar = http.cookiejar.MozillaCookieJar(_DOUYIN_COOKIES_FILE)
    ttwid = _fetch_ttwid()
    s_v_web_id = _generate_s_v_web_id()
    epoch_future = int(time.time()) + 86400 * 30
    for name, value in [("ttwid", ttwid), ("s_v_web_id", s_v_web_id)]:
        if value:
            c = http.cookiejar.Cookie(
                version=0, name=name, value=value,
                port=None, port_specified=False,
                domain=".douyin.com", domain_specified=True, domain_initial_dot=True,
                path="/", path_specified=True,
                secure=True, expires=epoch_future, discard=False,
                comment=None, comment_url=None, rest={}, rfc2109=False,
            )
            jar.set_cookie(c)

    opener = urllib_req.build_opener(urllib_req.HTTPCookieProcessor(jar))
    opener.addheaders = [("User-Agent", _USER_AGENT)]
    try:
        opener.open("https://www.douyin.com/", timeout=10)
    except OSError:
        pass

    try:
        jar.save(ignore_discard=True, ignore_expires=True)
        _DOUYIN_COOKIES_EXPIRY = time.time() + 1800
        return _DOUYIN_COOKIES_FILE
    except OSError:
        return None


def resolve_douyin_url(url: str) -> str:
    """Follow short-link redirects to the canonical douyin.com URL."""
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if hostname in ("v.douyin.com", "www.iesdouyin.com", "iesdouyin.com"):
        session = _load_cookie_session()
        resp = session.get(url, allow_redirects=True, timeout=15)
        return resp.url
    return url


def extract_aweme_id(url: str) -> str | None:
    url = resolve_douyin_url(url)
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if "douyin.com" not in hostname:
        return None

    qs = parse_qs(parsed.query)
    modal_id = qs.get("modal_id", [None])[0]
    if modal_id:
        return str(modal_id)

    path_match = re.search(r"/video/(\d+)", parsed.path)
    if path_match:
        return path_match.group(1)

    note_match = re.search(r"/note/(\d+)", parsed.path)
    if note_match:
        return note_match.group(1)

    return None


def _gen_ms_token() -> str:
    alphabet = string.ascii_letters + string.digits + "_-"
    return "".join(secrets.choice(alphabet) for _ in range(126)) + "=="


def _build_api_params(aweme_id: str) -> dict:
    return {
        "device_platform": "webapp",
        "aid": "6383",
        "channel": "channel_pc_web",
        "pc_client_type": "1",
        "version_code": "290100",
        "version_name": "29.1.0",
        "cookie_enabled": "true",
        "screen_width": "1920",
        "screen_height": "1080",
        "browser_language": "zh-CN",
        "browser_platform": "Win32",
        "browser_name": "Chrome",
        "browser_version": "131.0.0.0",
        "browser_online": "true",
        "engine_name": "Blink",
        "engine_version": "131.0.0.0",
        "os_name": "Windows",
        "os_version": "10",
        "cpu_core_num": "12",
        "device_memory": "8",
        "platform": "PC",
        "downlink": "10",
        "effective_type": "4g",
        "round_trip_time": "0",
        "aweme_id": aweme_id,
        "msToken": _gen_ms_token(),
    }


def _load_cookie_session() -> requests.Session:
    cookie_file = _fetch_douyin_cookies()
    session = requests.Session()
    session.headers.update({
        "User-Agent": _USER_AGENT,
        "Referer": "https://www.douyin.com/",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    if not cookie_file or not os.path.exists(cookie_file):
        session.get("https://www.douyin.com/", timeout=15)
        return session

    with open(cookie_file, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.strip().split("\t")
            if len(parts) >= 7:
                session.cookies.set(parts[5], parts[6], domain=parts[0], path=parts[2])

    # Refresh __ac_nonce / ttwid when the homepage is reachable.
    try:
        session.get("https://www.douyin.com/", timeout=15)
    except OSError:
        pass
    return session


def _fetch_aweme_detail(aweme_id: str) -> dict:
    """Fetch aweme detail via signed web API (avoids RENDER_DATA captcha pages)."""
    last_error: Exception | None = None

    for attempt in range(3):
        session = _load_cookie_session()
        params = _build_api_params(aweme_id)
        a_bogus = generate_a_bogus(params)
        api_url = f"{_AWEME_DETAIL_API}?{urlencode(params)}&a_bogus={a_bogus}"

        try:
            resp = session.get(api_url, timeout=20)
            resp.raise_for_status()
        except OSError as exc:
            last_error = exc
            time.sleep(0.4 * (attempt + 1))
            continue

        if not resp.text.strip():
            last_error = ValueError("empty response")
            time.sleep(0.4 * (attempt + 1))
            continue

        try:
            payload = resp.json()
        except json.JSONDecodeError as exc:
            last_error = exc
            time.sleep(0.4 * (attempt + 1))
            continue

        status_code = payload.get("status_code", 0)
        if status_code != 0:
            message = payload.get("status_msg") or "请稍后重试"
            last_error = ValueError(message)
            time.sleep(0.4 * (attempt + 1))
            continue

        aweme_detail = payload.get("aweme_detail")
        if aweme_detail:
            return aweme_detail

        last_error = ValueError("missing aweme_detail")
        time.sleep(0.4 * (attempt + 1))

    try:
        return _fetch_render_data(aweme_id)
    except Exception as exc:
        if last_error:
            raise ValueError("无法从抖音页面获取视频数据，请稍后重试") from last_error
        raise ValueError("无法从抖音页面获取视频数据，请稍后重试") from exc


def _fetch_render_data(aweme_id: str) -> dict:
    session = _load_cookie_session()
    page_url = f"https://www.douyin.com/jingxuan?modal_id={aweme_id}"
    resp = session.get(page_url, timeout=20)
    resp.raise_for_status()

    match = _RENDER_DATA_RE.search(resp.text)
    if not match:
        raise ValueError("无法从抖音页面获取视频数据，请稍后重试")

    try:
        payload = json.loads(urllib.parse.unquote(match.group(1)))
    except json.JSONDecodeError as exc:
        raise ValueError("抖音页面数据解析失败") from exc

    video_detail = (payload.get("app") or {}).get("videoDetail")
    if not video_detail:
        raise ValueError("该链接可能不是公开视频，或抖音页面结构已变更")

    return video_detail


def _play_urls_from_addr(play_addr) -> list[str]:
    urls: list[str] = []
    if isinstance(play_addr, list):
        for item in play_addr:
            if isinstance(item, dict) and item.get("src"):
                urls.append(item["src"])
    elif isinstance(play_addr, dict):
        for raw in play_addr.get("url_list") or []:
            if raw:
                urls.append(raw)
        if play_addr.get("src"):
            urls.append(play_addr["src"])
    return urls


def _codec_priority_from_flags(is_h265: bool | int | None) -> int:
    return 1 if is_h265 else 0


def _resolve_format_filesize(bitrate: dict, play_addr: dict) -> int | None:
    """Resolve byte size from API fields (never use bit_rate — that is bps, not bytes)."""
    for source in (play_addr, bitrate):
        for key in ("data_size", "dataSize", "file_size", "fileSize"):
            value = source.get(key)
            if value is None:
                continue
            try:
                size = int(value)
            except (TypeError, ValueError):
                continue
            if size > 0:
                return size
    return None


def _extract_formats(video_detail: dict) -> list[dict]:
    video_info = video_detail.get("video") or {}
    formats: list[dict] = []
    seen_heights: set[int] = set()

    bitrates = video_info.get("bit_rate") or video_info.get("bitRateList") or []
    sorted_bitrates = sorted(
        bitrates,
        key=lambda b: (
            int((b.get("play_addr") or b.get("playAddr") or {}).get("height") or 0),
            int(_resolve_format_filesize(b, b.get("play_addr") or b.get("playAddr") or {}) or 0),
            _codec_priority_from_flags(b.get("is_h265") or b.get("isH265")),
        ),
        reverse=True,
    )

    for bitrate in sorted_bitrates:
        if bitrate.get("format") == "dash":
            continue
        play_addr = bitrate.get("play_addr") or bitrate.get("playAddr") or {}
        play_urls = _play_urls_from_addr(play_addr)
        if not play_urls:
            continue

        height = int(play_addr.get("height") or bitrate.get("height") or 0)
        if height in seen_heights:
            continue
        seen_heights.add(height)

        width = int(play_addr.get("width") or bitrate.get("width") or 0)
        is_h265 = bool(bitrate.get("is_h265") or bitrate.get("isH265"))
        filesize = _resolve_format_filesize(bitrate, play_addr)

        formats.append({
            "format_id": str(height) if height else f"br_{len(formats)}",
            "label": _height_label(height),
            "ext": "mp4",
            "resolution": f"{width}x{height}" if width and height else (f"{height}P" if height else None),
            "filesize": filesize,
            "filesize_str": _format_filesize(filesize),
            "url": play_urls[0],
            "height": height,
            "vcodec": "h265" if is_h265 else "h264",
        })

    if not formats:
        play_addrs = [
            video_info.get("play_addr") or video_info.get("playAddr"),
            video_info.get("download_addr") or video_info.get("downloadAddr"),
        ]
        for play_addr in play_addrs:
            for play_url in _play_urls_from_addr(play_addr):
                height = int((play_addr or {}).get("height") or video_info.get("height") or 0)
                filesize = _resolve_format_filesize({}, play_addr or {})
                formats.append({
                    "format_id": "play",
                    "label": "默认画质",
                    "ext": "mp4",
                    "resolution": f"{height}P" if height else None,
                    "filesize": filesize,
                    "filesize_str": _format_filesize(filesize),
                    "url": play_url,
                    "height": height,
                    "vcodec": "h264",
                })
                break
            if formats:
                break

    formats.sort(key=lambda f: f.get("height") or 0, reverse=True)
    return formats


def _height_label(height: int) -> str:
    label_map = {
        2160: "4K 超清",
        1440: "2K 高清",
        1080: "1080P 高清",
        720: "720P",
        480: "480P 标清",
        360: "360P",
        240: "240P",
    }
    return label_map.get(height, f"{height}P" if height else "默认画质")


def _cover_url(video_info: dict) -> str:
    for key in ("coverUrlList", "cover169UrlList"):
        urls = video_info.get(key)
        if isinstance(urls, list) and urls:
            return urls[0]

    for key in ("cover", "origin_cover", "originCover", "dynamic_cover", "dynamicCover"):
        cover = video_info.get(key)
        if isinstance(cover, dict):
            url_list = cover.get("url_list") or cover.get("urlList") or []
            if url_list:
                return url_list[0]
        if isinstance(cover, str) and cover:
            return cover
    return ""


def parse_douyin(url: str) -> dict:
    aweme_id = extract_aweme_id(url)
    if not aweme_id:
        raise ValueError("无法识别抖音视频 ID")

    video_detail = _fetch_aweme_detail(aweme_id)
    video_info = video_detail.get("video") or {}
    author = video_detail.get("author") or video_detail.get("authorInfo") or {}

    duration_raw = video_info.get("duration")
    duration_sec = None
    if duration_raw is not None:
        duration_sec = int(duration_raw)
        if duration_sec > 10_000:
            duration_sec = duration_sec // 1000

    raw_formats = _extract_formats(video_detail)
    if not raw_formats:
        raise ValueError("未找到可下载的视频流")

    api_formats = [{
        "format_id": "best",
        "label": "最佳画质（推荐）",
        "ext": "mp4",
        "resolution": raw_formats[0].get("resolution"),
        "filesize": raw_formats[0].get("filesize"),
        "filesize_str": raw_formats[0].get("filesize_str") or "自动选择",
    }]
    for fmt in raw_formats[:6]:
        api_formats.append({
            "format_id": fmt["format_id"],
            "label": fmt["label"],
            "ext": fmt["ext"],
            "resolution": fmt["resolution"],
            "filesize": fmt["filesize"],
            "filesize_str": fmt["filesize_str"],
        })

    title = (
        video_detail.get("desc")
        or video_detail.get("itemTitle")
        or video_detail.get("item_title")
        or "抖音视频"
    )

    return {
        "title": str(title).split("\n")[0][:100],
        "thumbnail": _cover_url(video_info),
        "duration": duration_sec,
        "duration_str": _format_duration(duration_sec),
        "author": author.get("nickname") or author.get("uniqueId") or "未知作者",
        "platform": "douyin",
        "platform_label": "抖音",
        "formats": api_formats,
        "_douyin_aweme_id": aweme_id,
    }


def _select_download_url(formats: list[dict], format_id: str) -> str:
    if not formats:
        raise ValueError("没有可用下载地址")

    if format_id == "best":
        return formats[0]["url"]

    for fmt in formats:
        if fmt["format_id"] == format_id:
            return fmt["url"]

    try:
        target_h = int(format_id)
        for fmt in formats:
            if fmt.get("height") == target_h:
                return fmt["url"]
    except ValueError:
        pass

    return formats[0]["url"]


def download_douyin(url: str, format_id: str) -> tuple[str, str]:
    aweme_id = extract_aweme_id(url)
    if not aweme_id:
        raise ValueError("无法识别抖音视频 ID")

    video_detail = _fetch_aweme_detail(aweme_id)
    formats = _extract_formats(video_detail)

    if format_id == "audio_only":
        music = video_detail.get("music") or {}
        play_url = music.get("play_url") or music.get("playUrl") or {}
        play_urls = _play_urls_from_addr(play_url)
        if not play_urls:
            raise ValueError("该视频没有单独的音频流，请选择视频格式下载")
        download_url = play_urls[0]
        ext = ".mp3"
    else:
        download_url = _select_download_url(formats, format_id)
        ext = ".mp4"

    title = _sanitize_filename(
        (video_detail.get("desc") or video_detail.get("itemTitle") or video_detail.get("item_title") or "douyin_video").split("\n")[0]
    )

    session = _load_cookie_session()
    unique_id = uuid.uuid4().hex[:8]
    filepath = os.path.join(TEMP_DIR, f"{unique_id}_{title}{ext}")

    with session.get(
        download_url,
        stream=True,
        timeout=120,
        headers={"Referer": "https://www.douyin.com/"},
    ) as resp:
        resp.raise_for_status()
        with open(filepath, "wb") as out:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    out.write(chunk)

    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        raise ValueError("下载失败：文件为空")

    return filepath, f"{title}{ext}"
