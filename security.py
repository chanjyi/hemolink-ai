"""
Security & personal-data protection helpers (v6.1).

* Rate limits      — sliding-window limits per IP / user, and a login lock after repeated wrong passwords.
* Encryption       — HemoScan report files (PDFs / photos) are encrypted at rest with Fernet (AES-128-CBC + HMAC).
                     Key: HEMOLINK_DATA_KEY, else data_key.txt created next to the database (keep it safe and backed up).
* Security headers — Content-Security-Policy, HSTS (production), Permissions-Policy.
* Privacy notice   — version string recorded with each consent (PDPA 2010 "Notice and Choice" principle).
"""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, Request

PRIVACY_VERSION = "2026-11-08"
ENC_MAGIC = b"HLENC1:"  # prefix of encrypted files; files without it are old plain files (still readable)

# ---------------------------------------------------------------- rate limiting

_hits: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def limit(key: str, max_hits: int, window_s: int, message: str = "Too many requests — please wait a moment.") -> None:
    """Raise 429 if `key` was hit more than max_hits times in the last window_s seconds."""
    if os.getenv("HEMOLINK_RATE_LIMIT", "on") == "off":
        return
    now = time.monotonic()
    with _lock:
        q = _hits[key]
        while q and now - q[0] > window_s:
            q.popleft()
        if len(q) >= max_hits:
            retry = int(window_s - (now - q[0])) + 1
            raise HTTPException(429, message, headers={"Retry-After": str(retry)})
        q.append(now)


# login lock: 5 wrong passwords for one email within 15 minutes → locked for 15 minutes
FAIL_MAX, FAIL_WINDOW = 5, 15 * 60
_fails: dict[str, deque] = defaultdict(deque)


def check_login_allowed(email: str) -> None:
    if os.getenv("HEMOLINK_RATE_LIMIT", "on") == "off":
        return
    now = time.monotonic()
    with _lock:
        q = _fails[email]
        while q and now - q[0] > FAIL_WINDOW:
            q.popleft()
        if len(q) >= FAIL_MAX:
            mins = int((FAIL_WINDOW - (now - q[0])) // 60) + 1
            raise HTTPException(429, f"Too many wrong passwords. This account is locked for {mins} more minute(s).",
                                headers={"Retry-After": str(mins * 60)})


def login_failed(email: str) -> None:
    with _lock:
        _fails[email].append(time.monotonic())


def login_ok(email: str) -> None:
    with _lock:
        _fails.pop(email, None)


def reset_limits() -> None:  # tests
    with _lock:
        _hits.clear()
        _fails.clear()


# ---------------------------------------------------------------- encryption at rest

_fernet: Fernet | None = None


def _key_file() -> Path:
    db = Path(os.environ.get("HEMOLINK_DB_PATH", str(Path(__file__).resolve().parent / "hemolink_v2.db")))
    return db.parent / "data_key.txt"


def fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = os.getenv("HEMOLINK_DATA_KEY", "").strip()
        if not key:
            f = _key_file()
            if f.exists():
                key = f.read_text().strip()
            else:
                key = Fernet.generate_key().decode()
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(key)
                try:
                    f.chmod(0o600)
                except OSError:
                    pass
        try:
            _fernet = Fernet(key.encode())
        except ValueError:  # any other secret (e.g. Render's generated value) → derive a valid Fernet key from it
            import base64
            import hashlib
            _fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest()))
    return _fernet


def encrypt_bytes(data: bytes) -> bytes:
    return ENC_MAGIC + fernet().encrypt(data)


def decrypt_bytes(blob: bytes) -> bytes:
    if not blob.startswith(ENC_MAGIC):
        return blob  # file saved before v6.1
    try:
        return fernet().decrypt(blob[len(ENC_MAGIC):])
    except InvalidToken as exc:
        raise HTTPException(500, "This file can't be decrypted — the data key has changed.") from exc


def write_encrypted(path: Path, data: bytes) -> None:
    path.write_bytes(encrypt_bytes(data))


def read_decrypted(path: Path) -> bytes:
    return decrypt_bytes(path.read_bytes())


# ---------------------------------------------------------------- headers

CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' data: https://fonts.gstatic.com",
    "img-src 'self' data: blob: https://*.tile.openstreetmap.org https://tile.openstreetmap.org",
    "connect-src 'self' https://nominatim.openstreetmap.org",
    "frame-src 'self' blob:",
    "worker-src 'self'",
    "manifest-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
])


def add_headers(response, *, frame_same_origin: bool, production: bool) -> None:
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "SAMEORIGIN" if frame_same_origin else "DENY"
    response.headers["Content-Security-Policy"] = CSP + ("; frame-ancestors 'self'" if frame_same_origin else "; frame-ancestors 'none'")
    response.headers["Permissions-Policy"] = "geolocation=(self), camera=(self), microphone=(), payment=(), usb=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    if production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
