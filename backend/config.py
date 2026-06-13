"""Application configuration loaded from environment variables.

The AI summarization feature talks to MiniMax through its OpenAI-compatible
endpoint. Keep secrets in `backend/.env` (git-ignored), never in source.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

_BACKEND_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _BACKEND_DIR.parent

# Common locations users put .env (backend/.env is the canonical path).
_ENV_CANDIDATES = (
    _BACKEND_DIR / ".env",
    _ROOT_DIR / ".env",
    Path.cwd() / ".env",
    Path.cwd() / "backend" / ".env",
)

_loaded_env_files: list[str] = []


def _load_env_files() -> list[str]:
    """Load all existing .env files; later files override earlier ones."""
    global _loaded_env_files
    if load_dotenv is None:
        return _loaded_env_files

    loaded: list[str] = []
    seen: set[str] = set()
    for path in _ENV_CANDIDATES:
        resolved = str(path.resolve())
        if path.is_file() and resolved not in seen:
            load_dotenv(path, override=True, encoding="utf-8")
            loaded.append(resolved)
            seen.add(resolved)
    _loaded_env_files = loaded
    return loaded


def _read_env(name: str, default: str = "") -> str:
    _load_env_files()
    return os.getenv(name, default).strip()


_PLACEHOLDER_KEYS = frozenset({
    "",
    "your_minimax_api_key_here",
    "your-api-key-here",
    "YOUR_API_KEY",
})


def get_minimax_api_key() -> str:
    for name in ("MINIMAX_API_KEY", "MINIMAX_KEY", "MINIMAX_API_TOKEN"):
        value = _read_env(name)
        if value not in _PLACEHOLDER_KEYS:
            return value
    return ""


def get_minimax_base_url() -> str:
    return _read_env("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1")


def get_minimax_model() -> str:
    return _read_env("MINIMAX_MODEL", "MiniMax-M2.7")


def get_max_transcript_chars() -> int:
    raw = _read_env("MAX_TRANSCRIPT_CHARS", "60000")
    try:
        return int(raw)
    except ValueError:
        return 60000


def is_asr_enabled() -> bool:
    return _read_env("ASR_ENABLED", "true").lower() in ("1", "true", "yes", "on")


def get_asr_model_dir() -> str:
    return _read_env("ASR_MODEL_DIR")


def get_sensevoice_use_int8() -> bool:
    return _read_env("SENSEVOICE_USE_INT8", "true").lower() in ("1", "true", "yes", "on")


def get_asr_threads() -> int:
    raw = _read_env("ASR_THREADS", "2")
    try:
        return max(1, int(raw))
    except ValueError:
        return 2


def get_asr_max_duration() -> int:
    raw = _read_env("ASR_MAX_DURATION_SECONDS", "1800")
    try:
        return int(raw)
    except ValueError:
        return 1800


def get_ytdlp_cookie_file() -> str:
    path = _read_env("YTDLP_COOKIE_FILE")
    return path if path and os.path.isfile(path) else ""


def get_ytdlp_cookies_from_browser() -> str:
    return _read_env("YTDLP_COOKIES_FROM_BROWSER")


def is_auth_enabled() -> bool:
    return _read_env("AUTH_ENABLED", "true").lower() in ("1", "true", "yes", "on")


def get_auth_username() -> str:
    return _read_env("AUTH_USERNAME")


def get_auth_password() -> str:
    return _read_env("AUTH_PASSWORD")


def get_auth_session_secret() -> str:
    return _read_env("AUTH_SESSION_SECRET", "change-me-in-production")


def get_auth_session_max_age() -> int:
    raw = _read_env("AUTH_SESSION_MAX_AGE", "86400")
    try:
        return max(300, int(raw))
    except ValueError:
        return 86400


def get_auth_login_max_attempts() -> int:
    raw = _read_env("AUTH_LOGIN_MAX_ATTEMPTS", "5")
    try:
        return max(1, int(raw))
    except ValueError:
        return 5


def get_auth_login_lockout_seconds() -> int:
    raw = _read_env("AUTH_LOGIN_LOCKOUT_SECONDS", "300")
    try:
        return max(60, int(raw))
    except ValueError:
        return 300


def get_cors_origins() -> list[str]:
    raw = _read_env("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def is_ai_configured() -> bool:
    return bool(get_minimax_api_key())


def get_ai_status_detail() -> dict:
    """Debug info for /api/ai-status when configuration looks wrong."""
    _load_env_files()
    key = get_minimax_api_key()
    example_has_key = False
    example_path = _BACKEND_DIR / ".env.example"
    if example_path.is_file() and not key:
        try:
            text = example_path.read_text(encoding="utf-8-sig")
            for line in text.splitlines():
                if line.strip().startswith("MINIMAX_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    example_has_key = val not in _PLACEHOLDER_KEYS
                    break
        except OSError:
            pass

    hint = None
    if not key:
        if example_has_key and not (_BACKEND_DIR / ".env").is_file():
            hint = "检测到密钥写在 backend/.env.example 中。请复制为 backend/.env：copy .env.example .env"
        elif not _loaded_env_files:
            hint = "未找到 .env 文件。请在 backend 目录创建 .env 并设置 MINIMAX_API_KEY=你的密钥"
        else:
            hint = "已加载 .env 但未读取到有效的 MINIMAX_API_KEY，请检查变量名与取值"

    detail = {
        "configured": bool(key),
        "loaded_env_files": _loaded_env_files,
        "env_candidates": [str(p) for p in _ENV_CANDIDATES],
        "hint": hint,
    }
    try:
        from services import asr_service
        detail["asr"] = asr_service.get_asr_status()
    except Exception:
        detail["asr"] = {"enabled": is_asr_enabled(), "available": False}
    return detail


# Backward-compatible module-level names (re-read on import).
_load_env_files()
MINIMAX_API_KEY = get_minimax_api_key()
MINIMAX_BASE_URL = get_minimax_base_url()
MINIMAX_MODEL = get_minimax_model()
MAX_TRANSCRIPT_CHARS = get_max_transcript_chars()
