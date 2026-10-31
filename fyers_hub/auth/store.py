"""Token ko file me rakhna (permission 600, repo ke bahar). Token kabhi print nahi hota."""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

from fyers_hub.timeutil import IST


@dataclass
class Token:
    access_token: str
    refresh_token: str
    app_id: str
    issued_at: int
    expires_at: int

    def valid(self, now: float | None = None, margin: int = 120) -> bool:
        return bool(self.access_token) and (now or time.time()) < self.expires_at - margin


def next_expiry(now: float | None = None) -> int:
    """Access token roz badalta hai - agle din subah 6 baje IST tak maante hain.
    Asli expiry alag ho to API auth-error dega aur refresh apne aap chalega."""
    dt = datetime.fromtimestamp(now or time.time(), IST)
    nxt = (dt + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
    return int(nxt.timestamp())


def save_token(path: Path, tok: Token) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(asdict(tok), f)
    os.replace(tmp, path)
    os.chmod(path, 0o600)


def load_token(path: Path) -> Token | None:
    path = Path(path)
    if not path.is_file():
        return None
    try:
        return Token(**json.loads(path.read_text(encoding="utf-8")))
    except (ValueError, TypeError):
        return None
