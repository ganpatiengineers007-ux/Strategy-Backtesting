"""Session management + login rate limiting."""
import hmac
import os
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional

import bcrypt

from backend.middleware.authentication import is_authorized as _legacy_is_authorized


@dataclass
class Session:
    username: str
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)


class SessionStore:
    """In-memory session store (single process). Production me Redis use karo."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._lock = Lock()

    def create(self, username: str) -> str:
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[token] = Session(username=username)
        return token

    def get(self, token: str) -> Optional[Session]:
        with self._lock:
            sess = self._sessions.get(token)
            if sess:
                sess.last_activity = time.time()
                return sess
        return None

    def delete(self, token: str) -> bool:
        with self._lock:
            return self._sessions.pop(token, None) is not None

    def cleanup_expired(self, max_age: int = 86400) -> int:
        """Sessions older than max_age seconds ko hatao. Returns count removed."""
        now = time.time()
        removed = 0
        with self._lock:
            expired = [t for t, s in self._sessions.items() if now - s.last_activity > max_age]
            for t in expired:
                self._sessions.pop(t, None)
                removed += 1
        return removed


class LoginLimiter:
    """IP + username combination par 5 failed attempts = 15 min lockout."""

    def __init__(self, max_attempts: int = 5, lockout_seconds: int = 900):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._lockouts: dict[str, float] = {}
        self._lock = Lock()

    def _key(self, ip: str, username: str) -> str:
        return f"{ip}:{username.lower()}"

    def is_locked(self, ip: str, username: str) -> tuple[bool, int]:
        key = self._key(ip, username)
        with self._lock:
            until = self._lockouts.get(key, 0)
            if until > time.time():
                return True, int(until - time.time())
        return False, 0

    def record_failure(self, ip: str, username: str) -> int:
        """Failure record karo. Returns remaining attempts before lockout."""
        key = self._key(ip, username)
        now = time.time()
        with self._lock:
            # Purane attempts (15 min se zyada) hatao
            cutoff = now - self.lockout_seconds
            self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]
            self._attempts[key].append(now)
            count = len(self._attempts[key])
            if count >= self.max_attempts:
                self._lockouts[key] = now + self.lockout_seconds
                self._attempts[key].clear()
                return 0
            return self.max_attempts - count

    def record_success(self, ip: str, username: str) -> None:
        """Success pe attempts clear karo."""
        key = self._key(ip, username)
        with self._lock:
            self._attempts.pop(key, None)
            self._lockouts.pop(key, None)


# Global instances
session_store = SessionStore()
login_limiter = LoginLimiter()

# Config env se dynamically padhi jaati hai (tests/turant badlav ke liye)
def admin_user() -> str:
    return os.environ.get("ADMIN_USER", "").strip()


def admin_password_hash() -> str:
    return os.environ.get("ADMIN_PASSWORD_HASH", "").strip()


def get_client_ip(request) -> str:
    """Client IP nikaalo (headers se)."""
    real = request.headers.get("x-real-ip")
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    return real or forwarded or (request.client.host if request.client else "unknown")


def verify_credentials(username: str, password: str) -> bool:
    """Constant-time credential verification."""
    expected_user = admin_user()
    expected_hash = admin_password_hash()
    if not expected_user or not expected_hash:
        return False
    if not hmac.compare_digest(username, expected_user):
        # Dummy hash compare karo timing attack avoid karne ke liye
        bcrypt.checkpw(b"dummy", expected_hash.encode())
        return False
    return bcrypt.checkpw(password.encode(), expected_hash.encode())


def set_session_cookie(response, token: str, secure: bool = False):
    """HttpOnly, SameSite=Strict session cookie set karo."""
    response.set_cookie(
        key="session_id",
        value=token,
        httponly=True,
        secure=secure,
        samesite="strict",
        max_age=86400,  # 24 hours
        path="/",
    )


def clear_session_cookie(response):
    """Session cookie clear karo."""
    response.delete_cookie(key="session_id", path="/", httponly=True, secure=False, samesite="strict")


def get_session_id(request) -> Optional[str]:
    """Request se session_id nikaalo."""
    return request.cookies.get("session_id")


def is_authorized(headers, expected_key: str, cookies=None) -> bool:
    """Authorization check: session cookie OR X-API-Key."""
    # 1. Session cookie check
    if cookies:
        session_id = cookies.get("session_id")
        if session_id and session_store.get(session_id):
            return True
    # 2. Legacy X-API-Key check (for scripts/tests)
    return _legacy_is_authorized(headers, expected_key)


def audit_login_event(event: str, username: str, ip: str, success: bool, details: str = ""):
    """Login/logout/failed login audit log."""
    from backend.api.common import runs_root
    from persistence import audit
    audit.log(
        runs_root(),
        event=event,
        username=username,
        ip=ip,
        success=success,
        details=details,
    )