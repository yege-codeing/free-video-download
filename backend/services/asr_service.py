"""Local speech-to-text fallback using open-source ONNX models (no login required).

Primary engine: SenseVoice via sherpa-onnx (FunAudioLLM, ONNX Runtime, Chinese-optimized).
Flow: yt-dlp downloads audio → FFmpeg resamples to 16 kHz mono → SenseVoice transcribes.
"""
import os
import re
import uuid
import tarfile
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.request import urlretrieve

import yt_dlp

import config
from services.video_service import _normalize_url, _shared_ydl_opts, cleanup_file
from services.ffmpeg_utils import get_ffmpeg_path, is_ffmpeg_available

SENSEVOICE_ARCHIVE = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/"
    "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2"
)
SENSEVOICE_DIRNAME = "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"

_recognizer = None


class ASRNotAvailableError(Exception):
    """ASR dependencies or model missing."""


def _model_root() -> Path:
    custom = config.get_asr_model_dir()
    if custom:
        return Path(custom)
    return Path(__file__).resolve().parent.parent / "models" / "sensevoice"


def _ensure_sensevoice_model() -> tuple[Path, Path]:
    """Download and return (model.onnx path, tokens.txt path)."""
    root = _model_root()
    extracted = root / SENSEVOICE_DIRNAME
    use_int8 = config.get_sensevoice_use_int8()
    model_name = "model.int8.onnx" if use_int8 else "model.onnx"
    model_path = extracted / model_name
    tokens_path = extracted / "tokens.txt"

    if model_path.is_file() and tokens_path.is_file():
        return model_path, tokens_path

    root.mkdir(parents=True, exist_ok=True)
    archive_path = root / "sensevoice.tar.bz2"
    if not archive_path.is_file():
        urlretrieve(SENSEVOICE_ARCHIVE, archive_path)

    with tarfile.open(archive_path, "r:bz2") as tar:
        tar.extractall(path=root)

    if not model_path.is_file() or not tokens_path.is_file():
        raise ASRNotAvailableError("SenseVoice 模型下载或解压失败")

    return model_path, tokens_path


def is_asr_available() -> bool:
    if not config.is_asr_enabled():
        return False
    if not is_ffmpeg_available():
        return False
    try:
        import sherpa_onnx  # noqa: F401
        return True
    except ImportError:
        return False


def _get_recognizer():
    global _recognizer
    if _recognizer is not None:
        return _recognizer
    import sherpa_onnx

    model_path, tokens_path = _ensure_sensevoice_model()
    _recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=str(model_path),
        tokens=str(tokens_path),
        language="auto",
        use_itn=True,
        num_threads=config.get_asr_threads(),
    )
    return _recognizer


def _audio_ydl_opts(url: str) -> dict:
    uid = uuid.uuid4().hex[:8]
    outtmpl = os.path.join(tempfile.gettempdir(), "video-downloads", f"{uid}_%(title)s.%(ext)s")
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "outtmpl": outtmpl,
        "format": "bestaudio/best",
        **_shared_ydl_opts(for_download=True),
    }
    cookiefile = config.get_ytdlp_cookie_file()
    if cookiefile:
        opts["cookiefile"] = cookiefile
    browser = config.get_ytdlp_cookies_from_browser()
    if browser:
        opts["cookiesfrombrowser"] = (browser,)
    return opts


def _download_audio(url: str) -> tuple[str, dict]:
    url = _normalize_url(url)
    with yt_dlp.YoutubeDL(_audio_ydl_opts(url)) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            raise ValueError("无法下载视频音频")
        filepath = ydl.prepare_filename(info)
        if not os.path.exists(filepath):
            base, _ = os.path.splitext(filepath)
            for ext in (".m4a", ".mp3", ".webm", ".opus", ".mp4", ".mkv"):
                alt = base + ext
                if os.path.exists(alt):
                    filepath = alt
                    break
        if not os.path.exists(filepath):
            raise ValueError("音频下载完成但找不到文件")
        return filepath, info


def _to_wav_16k_mono(src: str) -> str:
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        raise ASRNotAvailableError("需要 FFmpeg 才能进行语音识别")

    dst = os.path.splitext(src)[0] + ".16k.wav"
    cmd = [
        ffmpeg, "-y", "-i", src,
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        dst,
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0 or not os.path.isfile(dst):
        err = (proc.stderr or proc.stdout or b"").decode("utf-8", errors="replace")[-300:]
        raise ValueError(f"音频转码失败：{err}")
    return dst


def _read_wav(path: str):
    import numpy as np
    import soundfile as sf

    samples, sample_rate = sf.read(path, dtype="float32", always_2d=False)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    return samples, sample_rate


def _tokens_to_segments(tokens: list[str], timestamps: list[float]) -> list[dict]:
    """Group SenseVoice token output into readable timestamped segments."""
    if not tokens:
        return []

    segments: list[dict] = []
    buf: list[str] = []
    seg_start = timestamps[0] if timestamps else 0.0

    for i, tok in enumerate(tokens):
        text = tok.replace("▁", " ").strip()
        if not text:
            continue
        buf.append(text)
        end_of_seg = (
            text.endswith(("。", "！", "？", ".", "!", "?"))
            or len(buf) >= 18
            or i == len(tokens) - 1
        )
        if end_of_seg:
            joined = re.sub(r"\s+", " ", "".join(buf)).strip()
            if joined:
                segments.append({"t": int(seg_start), "text": joined})
            buf = []
            if i + 1 < len(timestamps):
                seg_start = timestamps[i + 1]

    return segments


def _transcribe_wav(wav_path: str) -> tuple[list[dict], str]:
    recognizer = _get_recognizer()
    samples, sample_rate = _read_wav(wav_path)

    stream = recognizer.create_stream()
    stream.accept_waveform(sample_rate, samples)
    recognizer.decode_stream(stream)

    result = stream.result
    text = (result.text or "").strip()
    lang = (getattr(result, "lang", None) or "zh").strip("<|>")

    seg_texts = getattr(result, "segment_texts", None) or []
    seg_times = getattr(result, "segment_timestamps", None) or []
    if seg_texts and seg_times:
        segments = []
        for i, seg in enumerate(seg_texts):
            seg = re.sub(r"\s+", " ", (seg or "").replace("▁", " ")).strip()
            if not seg:
                continue
            t = int(seg_times[i]) if i < len(seg_times) else 0
            segments.append({"t": t, "text": seg})
        if segments:
            return segments, lang

    tokens = getattr(result, "tokens", None) or []
    timestamps = getattr(result, "timestamps", None) or []
    segments = _tokens_to_segments(list(tokens), list(timestamps))
    if not segments and text:
        segments = [{"t": 0, "text": text}]

    return segments, lang


def transcribe_url(url: str, info: dict | None = None) -> tuple[list[dict], str]:
    if not is_asr_available():
        raise ASRNotAvailableError(
            "语音识别不可用。请执行 pip install sherpa-onnx soundfile，并确保 FFmpeg 可用"
        )

    meta = info or {}
    duration = meta.get("duration") or 0
    max_dur = config.get_asr_max_duration()
    if duration and duration > max_dur:
        mins = max_dur // 60
        raise ValueError(f"视频时长超过语音识别上限（{mins} 分钟），请换较短的视频")

    audio_path = None
    wav_path = None
    try:
        audio_path, meta = _download_audio(url)
        wav_path = _to_wav_16k_mono(audio_path)
        return _transcribe_wav(wav_path)
    finally:
        if wav_path:
            cleanup_file(wav_path)
        if audio_path:
            cleanup_file(audio_path)


def get_asr_status() -> dict:
    model_ready = False
    model_dir = str(_model_root())
    try:
        if is_asr_available():
            mp, tp = _ensure_sensevoice_model()
            model_ready = mp.is_file() and tp.is_file()
    except Exception:
        model_ready = False

    return {
        "enabled": config.is_asr_enabled(),
        "available": is_asr_available(),
        "engine": "sensevoice-sherpa-onnx",
        "model_ready": model_ready,
        "model_dir": model_dir,
        "max_duration_seconds": config.get_asr_max_duration(),
    }
