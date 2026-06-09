"""Subtitle extraction for the AI summary feature.

Priority: yt-dlp platform subs → Bilibili /x/v2/dm/view (no cookie) → SenseVoice ASR.
"""
import re
import json
import asyncio
from urllib.parse import urlparse, parse_qs

import requests
import yt_dlp

import config
from services.video_service import (
    _normalize_url,
    _shared_ydl_opts,
    _detect_platform,
    _format_duration,
    _is_douyin,
    _is_bilibili,
)


class NoSubtitleError(Exception):
    """Raised when the video has no extractable subtitle track."""


# Preferred parse order when several formats exist for one language.
_EXT_PRIORITY = {"json3": 0, "srv3": 1, "vtt": 2, "srt": 3, "json": 4, "ass": 5}

# Bilibili exposes bullet comments (danmaku) as a pseudo "subtitle" track — skip it.
_SKIP_TRACK_LANGS = frozenset({"danmaku"})
_SKIP_TRACK_EXTS = frozenset({"xml"})


def _headers_for_url(url: str) -> dict:
    referer = "https://www.bilibili.com" if _is_bilibili(url) else "https://www.youtube.com/"
    headers = {
        "Referer": referer,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    }
    if _is_bilibili(url):
        headers["Origin"] = "https://www.bilibili.com"
    return headers


def _lang_rank(lang: str) -> int:
    """Lower is better: Chinese first, then English, then anything else."""
    l = (lang or "").lower()
    if "zh" in l or "chi" in l or "cn" in l:
        return 0
    if "en" in l:
        return 1
    return 2


def _is_transcript_track(lang: str, entry: dict) -> bool:
    """True for real caption tracks; False for danmaku / bullet-comment XML."""
    if (lang or "").lower() in _SKIP_TRACK_LANGS:
        return False
    ext = (entry.get("ext") or "").lower()
    if ext in _SKIP_TRACK_EXTS:
        return False
    url = entry.get("url") or ""
    if "comment.bilibili.com" in url:
        return False
    return bool(entry.get("url") or entry.get("data"))


def _pick_track(subs: dict, auto: dict) -> tuple[str, dict] | None:
    """Choose (lang, format_entry) preferring manual subs over auto-captions."""
    for source in (subs, auto):
        if not source:
            continue
        langs = sorted(source.keys(), key=_lang_rank)
        for lang in langs:
            entries = [e for e in (source.get(lang) or []) if _is_transcript_track(lang, e)]
            if not entries:
                continue
            # Prefer inline data (yt-dlp may embed SRT) then best format ext.
            entries = sorted(
                entries,
                key=lambda e: (
                    0 if e.get("data") else 1,
                    _EXT_PRIORITY.get((e.get("ext") or "").lower(), 99),
                ),
            )
            return lang, entries[0]
    return None


def _ts_to_seconds(ts: str) -> float:
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    try:
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        if len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        return float(parts[0])
    except ValueError:
        return 0.0


def _clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)  # strip vtt/ass inline tags
    return text.replace("\u200b", "").strip()


def _parse_vtt_srt(content: str) -> list[dict]:
    segments: list[dict] = []
    blocks = re.split(r"\n\s*\n", content.strip())
    time_re = re.compile(
        r"(\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}|\d{1,2}:\d{2}[.,]\d{1,3})\s*-->\s*([\d:.,]+)"
    )
    for block in blocks:
        lines = [l for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        start = None
        text_lines = []
        for line in lines:
            m = time_re.search(line)
            if m:
                start = _ts_to_seconds(m.group(1))
            elif line.strip().isdigit() and start is None:
                continue  # srt index line
            elif line.strip().upper() == "WEBVTT":
                continue
            else:
                text_lines.append(line)
        text = _clean_text(" ".join(text_lines))
        if start is not None and text:
            segments.append({"t": int(start), "text": text})
    return segments


def _parse_json_subtitle(content: str) -> list[dict]:
    """Handle YouTube json3 (events) and Bilibili (body) JSON formats."""
    data = json.loads(content)
    segments: list[dict] = []

    # YouTube json3 / srv3
    if isinstance(data, dict) and "events" in data:
        for ev in data.get("events") or []:
            segs = ev.get("segs") or []
            text = _clean_text("".join(s.get("utf8", "") for s in segs))
            start = (ev.get("tStartMs") or 0) / 1000.0
            if text:
                segments.append({"t": int(start), "text": text})
        return segments

    # Bilibili subtitle JSON
    if isinstance(data, dict) and "body" in data:
        for item in data.get("body") or []:
            text = _clean_text(item.get("content", ""))
            start = item.get("from", 0) or 0
            if text:
                segments.append({"t": int(float(start)), "text": text})
        return segments

    return segments


def _parse_subtitle(content: str, ext: str) -> list[dict]:
    ext = (ext or "").lower()
    stripped = content.lstrip()
    if ext in ("json3", "srv3", "json") or stripped.startswith("{") or stripped.startswith("["):
        try:
            segs = _parse_json_subtitle(content)
            if segs:
                return segs
        except (ValueError, json.JSONDecodeError):
            pass
    return _parse_vtt_srt(content)


def _fetch_track_raw(url: str, entry: dict) -> str:
    raw = entry.get("data")
    if raw:
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace")
        return str(raw)
    resp = requests.get(entry["url"], headers=_headers_for_url(url), timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.encoding or "utf-8"
    return resp.text


def _bilibili_bvid(url: str, info: dict) -> str | None:
    m = re.search(r"(BV[\w]+)", url)
    if m:
        return m.group(1)
    vid = info.get("id") or info.get("bvid")
    if isinstance(vid, str) and vid.upper().startswith("BV"):
        return vid
    return None


def _bilibili_page(url: str) -> int:
    try:
        return max(1, int(parse_qs(urlparse(url).query).get("p", ["1"])[0]))
    except (ValueError, IndexError):
        return 1


def _bilibili_subtitle_rank(sub: dict) -> tuple[int, int]:
    """Pick best Bilibili CC track: zh-Hans > zh-CN > zh > ai-zh > zh-Hant > en."""
    lan = (sub.get("lan") or "").lower()
    order = {
        "zh-hans": 0,
        "zh-cn": 1,
        "zh": 2,
        "ai-zh": 3,
        "zh-hant": 4,
        "en": 5,
    }
    if lan in order:
        return order[lan], 0
    return 99, 1


def _normalize_subtitle_url(sub_url: str) -> str:
    if sub_url.startswith("//"):
        return f"https:{sub_url}"
    return sub_url


def _try_bilibili_subtitles(url: str, info: dict) -> tuple[str, list[dict]] | None:
    """Bilibili dm/view API — official CC/AI subs without login."""
    bvid = _bilibili_bvid(url, info)
    if not bvid:
        return None

    headers = _headers_for_url(url)
    view_resp = requests.get(
        "https://api.bilibili.com/x/web-interface/view",
        params={"bvid": bvid},
        headers=headers,
        timeout=30,
    )
    view_resp.raise_for_status()
    view_json = view_resp.json()
    if view_json.get("code") != 0:
        return None

    view_data = view_json.get("data") or {}
    aid = view_data.get("aid")
    pages = view_data.get("pages") or []
    if not aid or not pages:
        return None

    page_idx = min(_bilibili_page(url), len(pages)) - 1
    cid = pages[page_idx].get("cid")
    if not cid:
        return None

    dm_resp = requests.get(
        "https://api.bilibili.com/x/v2/dm/view",
        params={"type": 1, "oid": cid, "pid": aid},
        headers=headers,
        timeout=30,
    )
    dm_resp.raise_for_status()
    dm_json = dm_resp.json()
    if dm_json.get("code") != 0:
        return None

    sub_list = (dm_json.get("data") or {}).get("subtitle", {}).get("subtitles") or []
    if not sub_list:
        return None

    sub_list = sorted(sub_list, key=_bilibili_subtitle_rank)
    for sub in sub_list:
        sub_url = sub.get("subtitle_url")
        if not sub_url:
            continue
        sub_resp = requests.get(_normalize_subtitle_url(sub_url), headers=headers, timeout=30)
        sub_resp.raise_for_status()
        segments = _parse_subtitle(sub_resp.text, "json")
        if segments:
            return sub.get("lan") or "zh", segments
    return None


def _subtitle_ydl_opts(url: str) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "no_color": True,
        **_shared_ydl_opts(),
    }
    cookiefile = config.get_ytdlp_cookie_file()
    if cookiefile:
        opts["cookiefile"] = cookiefile
    browser = config.get_ytdlp_cookies_from_browser()
    if browser:
        opts["cookiesfrombrowser"] = (browser,)
    return opts


def _try_asr(url: str, info: dict) -> tuple[str, list[dict], str] | None:
    """SenseVoice ASR fallback when platform subtitles are unavailable."""
    from services import asr_service

    if not asr_service.is_asr_available():
        return None
    try:
        segments, lang = asr_service.transcribe_url(url, info)
        return lang, segments, "asr"
    except Exception as e:
        raise NoSubtitleError(f"语音识别失败：{e}") from e


def _no_subtitle_message(url: str) -> str:
    from services import asr_service

    if asr_service.is_asr_available():
        return "该视频没有可用字幕，且语音识别未能生成文本"
    if _is_bilibili(url):
        return "该视频没有可用字幕。请安装 sherpa-onnx 与 soundfile 启用语音识别兜底"
    return "该视频没有可用字幕，暂不支持 AI 总结"


def _extract_sync(url: str) -> dict:
    url = _normalize_url(url)

    with yt_dlp.YoutubeDL(_subtitle_ydl_opts(url)) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        raise ValueError("无法解析该视频链接")

    lang: str | None = None
    segments: list[dict] = []
    source = "subtitle"
    source_label = "平台字幕"

    if not _is_douyin(url):
        subs = info.get("subtitles") or {}
        auto = info.get("automatic_captions") or {}
        picked = _pick_track(subs, auto)

        if picked:
            lang, entry = picked
            raw = _fetch_track_raw(url, entry)
            segments = _parse_subtitle(raw, entry.get("ext", ""))

        if not segments and _is_bilibili(url):
            bili = _try_bilibili_subtitles(url, info)
            if bili:
                lang, segments = bili
                source_label = "B站官方字幕"

    if not segments:
        asr = _try_asr(url, info)
        if asr:
            lang, segments, source = asr
            source_label = "语音识别（SenseVoice）"

    if not segments:
        raise NoSubtitleError(_no_subtitle_message(url))

    full_text = "\n".join(s["text"] for s in segments)
    platform_id, platform_label = _detect_platform(url)

    return {
        "title": info.get("title", "未知标题"),
        "author": info.get("uploader") or info.get("channel") or "未知作者",
        "thumbnail": info.get("thumbnail", ""),
        "duration": info.get("duration"),
        "duration_str": _format_duration(info.get("duration")),
        "platform": platform_id,
        "platform_label": platform_label,
        "language": lang or "unknown",
        "source": source,
        "source_label": source_label,
        "segments": segments,
        "full_text": full_text,
        "webpage_url": info.get("webpage_url") or url,
    }


async def get_transcript(url: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract_sync, url)
