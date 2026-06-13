"""Authentication helpers: captcha, password check, login rate limiting."""
from __future__ import annotations

import base64
import random
import string
import time
from typing import Optional

import config

CAPTCHA_TTL = 300
CAPTCHA_LENGTH = 4
CAPTCHA_CHARS = "".join(
    ch for ch in (string.ascii_uppercase + string.digits) if ch not in "O0IL1"
)

_login_attempts: dict[str, dict] = {}


def _client_ip(request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def generate_captcha_text() -> str:
    return "".join(random.choices(CAPTCHA_CHARS, k=CAPTCHA_LENGTH))


def generate_captcha_svg(text: str) -> str:
    width, height = 120, 40
    lines = []
    for _ in range(6):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        lines.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="#3A3A48" stroke-width="1"/>'
        )

    chars_svg = []
    for i, ch in enumerate(text):
        x = 14 + i * 24
        y = 28 + random.randint(-4, 4)
        rot = random.randint(-18, 18)
        chars_svg.append(
            f'<text x="{x}" y="{y}" font-size="22" font-family="monospace" '
            f'fill="#F0F0F0" transform="rotate({rot} {x} {y})">{ch}</text>'
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<rect width="100%" height="100%" fill="#1E1E28"/>'
        f'{"".join(lines)}{"".join(chars_svg)}</svg>'
    )
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def create_captcha(session: dict) -> str:
    text = generate_captcha_text()
    session["captcha_text"] = text
    session["captcha_expires"] = time.time() + CAPTCHA_TTL
    return generate_captcha_svg(text)


def verify_captcha(session: dict, answer: str) -> bool:
    stored = session.pop("captcha_text", None)
    expires = session.pop("captcha_expires", 0)
    if not stored or time.time() > expires:
        return False
    return stored.upper() == (answer or "").strip().upper()


def verify_password(plain: str, stored: str) -> bool:
    if not stored:
        return False
    if stored.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            from passlib.hash import bcrypt
            return bcrypt.verify(plain, stored)
        except Exception:
            return False
    return plain == stored


def check_login_allowed(request) -> Optional[str]:
    ip = _client_ip(request)
    record = _login_attempts.get(ip)
    if not record:
        return None
    locked_until = record.get("locked_until", 0)
    if locked_until and time.time() < locked_until:
        remaining = int(locked_until - time.time())
        minutes = max(1, (remaining + 59) // 60)
        return f"登录尝试过多，请 {minutes} 分钟后再试"
    if locked_until and time.time() >= locked_until:
        _login_attempts.pop(ip, None)
    return None


def record_login_failure(request) -> None:
    ip = _client_ip(request)
    record = _login_attempts.setdefault(ip, {"fail_count": 0, "locked_until": 0})
    record["fail_count"] += 1
    if record["fail_count"] >= config.get_auth_login_max_attempts():
        record["locked_until"] = time.time() + config.get_auth_login_lockout_seconds()
        record["fail_count"] = 0


def clear_login_attempts(request) -> None:
    _login_attempts.pop(_client_ip(request), None)


def authenticate(username: str, password: str) -> bool:
    expected_user = config.get_auth_username()
    expected_pass = config.get_auth_password()
    if not expected_user or not expected_pass:
        return False
    if (username or "").strip() != expected_user:
        return False
    return verify_password(password or "", expected_pass)


PUBLIC_API_PREFIXES = (
    "/api/auth/captcha",
    "/api/auth/login",
    "/api/auth/me",
    "/api/auth/logout",
    "/api/health",
)


def is_public_path(path: str) -> bool:
    if path in PUBLIC_API_PREFIXES:
        return True
    if path in ("/docs", "/openapi.json", "/redoc"):
        return True
    return False
