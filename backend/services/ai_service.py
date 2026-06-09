"""MiniMax-backed AI summarization and Q&A.

Talks to MiniMax through its OpenAI-compatible Chat Completions API. All public
functions are blocking generators yielding SSE-style event dicts; FastAPI runs
them in a threadpool via StreamingResponse.
"""
import json

from openai import OpenAI

import config


class AINotConfiguredError(Exception):
    """Raised when no MiniMax API key is available."""


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if not config.is_ai_configured():
        raise AINotConfiguredError("未配置 MiniMax API Key，请在 backend/.env 中设置 MINIMAX_API_KEY")
    api_key = config.get_minimax_api_key()
    base_url = config.get_minimax_base_url()
    if _client is None or getattr(_client, "api_key", None) != api_key:
        _client = OpenAI(api_key=api_key, base_url=base_url)
    return _client


def _fmt_ts(seconds: int) -> str:
    seconds = int(seconds or 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _transcript_for_llm(segments: list[dict], max_chars: int) -> str:
    """Render timestamped transcript, truncated to a character budget."""
    lines = []
    total = 0
    for seg in segments:
        line = f"[{_fmt_ts(seg.get('t', 0))}] {seg.get('text', '')}"
        if total + len(line) > max_chars:
            lines.append("...(字幕过长，已截断)")
            break
        lines.append(line)
        total += len(line) + 1
    return "\n".join(lines)


class _ThinkStripper:
    """Drop <think>...</think> reasoning that some MiniMax models emit inline."""

    def __init__(self):
        self._inside = False
        self._tail = ""

    def feed(self, chunk: str) -> str:
        buf = self._tail + chunk
        out = []
        i = 0
        while i < len(buf):
            if not self._inside:
                start = buf.find("<think>", i)
                if start == -1:
                    # Keep a small tail in case a tag is split across chunks.
                    safe = len(buf) - 6
                    if safe > i:
                        out.append(buf[i:safe])
                        i = safe
                    break
                out.append(buf[i:start])
                i = start + len("<think>")
                self._inside = True
            else:
                end = buf.find("</think>", i)
                if end == -1:
                    break
                i = end + len("</think>")
                self._inside = False
        self._tail = buf[i:]
        return "".join(out)

    def flush(self) -> str:
        if self._inside:
            return ""
        out, self._tail = self._tail, ""
        return out


def _stream_chat(messages: list[dict]):
    """Yield plain text deltas (reasoning stripped) from a streaming completion."""
    client = _get_client()
    stripper = _ThinkStripper()
    stream = client.chat.completions.create(
        model=config.get_minimax_model(),
        messages=messages,
        stream=True,
        extra_body={"reasoning_split": True},
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        text = getattr(delta, "content", None)
        if not text:
            continue
        emit = stripper.feed(text)
        if emit:
            yield emit
    tail = stripper.flush()
    if tail:
        yield tail


def _complete(messages: list[dict]) -> str:
    client = _get_client()
    resp = client.chat.completions.create(
        model=config.get_minimax_model(),
        messages=messages,
        extra_body={"reasoning_split": True},
    )
    content = resp.choices[0].message.content or ""
    stripper = _ThinkStripper()
    return (stripper.feed(content) + stripper.flush()).strip()


def _extract_json(text: str) -> dict:
    """Best-effort JSON parse from a model reply (handles code fences/prose)."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


_SUMMARY_SYSTEM = (
    "你是专业的视频内容分析助手。用户会提供一个视频的标题和带时间戳的字幕文本。"
    "请基于字幕内容，用简体中文输出结构化总结，使用 Markdown 格式，包含以下部分：\n"
    "## 一句话概述\n（用一句话概括视频主旨）\n\n"
    "## 核心要点\n（5-8 条关键要点，用无序列表，每条简洁有信息量）\n\n"
    "## 内容详述\n（分段展开视频的主要内容与逻辑）\n\n"
    "要求：忠于字幕内容、不要编造；语言精炼、重点突出；不要输出与总结无关的客套话。"
)

_STRUCTURE_SYSTEM = (
    "你是专业的视频内容分析助手。基于给定的带时间戳字幕，提取视频的章节结构与思维导图。"
    "只输出一个 JSON 对象，不要任何额外文字或代码块标记。JSON 结构如下：\n"
    '{\n'
    '  "chapters": [{"start": 0, "title": "章节标题", "summary": "本章节要点（1-2句）"}],\n'
    '  "mindmap": "# 视频标题\\n## 分支1\\n- 要点\\n## 分支2\\n- 要点"\n'
    '}\n'
    "其中 start 是该章节开始的秒数（整数，来自字幕时间戳）；chapters 控制在 4-10 个；"
    "mindmap 是一份层级清晰的 Markdown 大纲（用 # / ## / ### 和无序列表表示层级），根节点为视频主题。"
    "全部使用简体中文。"
)


def summarize_stream(title: str, segments: list[dict]):
    """Generator of event dicts: summary deltas, then a structure payload."""
    transcript = _transcript_for_llm(segments, config.get_max_transcript_chars())
    user_content = f"视频标题：{title}\n\n字幕（含时间戳）：\n{transcript}"

    try:
        # Phase 1 — streamed human-readable summary.
        summary_msgs = [
            {"role": "system", "content": _SUMMARY_SYSTEM},
            {"role": "user", "content": user_content},
        ]
        for delta in _stream_chat(summary_msgs):
            yield {"event": "summary", "data": {"text": delta}}

        # Phase 2 — structured chapters + mindmap (single JSON reply).
        structure_msgs = [
            {"role": "system", "content": _STRUCTURE_SYSTEM},
            {"role": "user", "content": user_content},
        ]
        raw = _complete(structure_msgs)
        try:
            structure = _extract_json(raw)
        except (ValueError, json.JSONDecodeError):
            structure = {"chapters": [], "mindmap": ""}

        chapters = structure.get("chapters") or []
        for ch in chapters:
            if isinstance(ch, dict):
                ch["time"] = _fmt_ts(ch.get("start", 0))
        yield {
            "event": "structure",
            "data": {
                "chapters": chapters,
                "mindmap": structure.get("mindmap", "") or "",
            },
        }
        yield {"event": "done", "data": {}}
    except AINotConfiguredError as e:
        yield {"event": "error", "data": {"message": str(e)}}
    except Exception as e:
        yield {"event": "error", "data": {"message": f"AI 总结失败：{e}"}}


_CHAT_SYSTEM = (
    "你是一个视频内容问答助手。下面是某视频的字幕全文，请仅依据该内容回答用户的问题，"
    "用简体中文作答。如果字幕中没有相关信息，请如实说明无法从视频中找到答案，不要编造。\n\n"
    "视频字幕：\n{transcript}"
)


def chat_stream(full_text: str, history: list[dict], question: str):
    """Stateless Q&A over the transcript. Yields delta/done/error events."""
    transcript = full_text[: config.get_max_transcript_chars()]
    messages = [{"role": "system", "content": _CHAT_SYSTEM.format(transcript=transcript)}]
    for turn in history or []:
        role = turn.get("role")
        content = turn.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": question})

    try:
        for delta in _stream_chat(messages):
            yield {"event": "delta", "data": {"text": delta}}
        yield {"event": "done", "data": {}}
    except AINotConfiguredError as e:
        yield {"event": "error", "data": {"message": str(e)}}
    except Exception as e:
        yield {"event": "error", "data": {"message": f"AI 回答失败：{e}"}}
