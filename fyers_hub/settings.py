"""Settings. Secrets sirf environment / ~/.fyers_hub/.env se aate hain - repo me kabhi nahi."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
DEFAULT_REDIRECT = "https://trade.fyers.in/api-login/redirect-uri/index.html"

# Fyers jo resolutions khud deta hai (baaki hum khud banate hain)
NATIVE_TFS = ("5S", "10S", "15S", "30S", "45S", "1", "2", "3", "5", "10", "15", "20", "30", "60", "120", "240", "D")
# Default: base me sirf 1 minute aur 1 din khinchte hain; baaki inse derive hote hain
DEFAULT_BASE_TFS = ("1", "D")
DEFAULT_DERIVED_TFS = ("2", "3", "5", "10", "15", "30", "60", "15D")


def home_dir() -> Path:
    return Path(os.getenv("FYERS_HUB_HOME", str(Path.home() / ".fyers_hub")))


def load_env_file(path: str | os.PathLike | None = None) -> None:
    p = Path(path or os.getenv("FYERS_ENV_FILE") or home_dir() / ".env")
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    home: Path
    db_path: Path
    token_path: Path
    log_dir: Path
    app_id: str
    secret_key: str
    redirect_uri: str
    pin: str
    max_per_sec: int
    max_per_min: int
    risk_free_rate: float

    def require_app(self) -> None:
        missing = [n for n, v in (("FYERS_APP_ID", self.app_id), ("FYERS_SECRET_KEY", self.secret_key)) if not v]
        if missing:
            raise RuntimeError(f"{', '.join(missing)} set nahi hai. {self.home}/.env check karo (env.example dekho).")


def get_settings() -> Settings:
    load_env_file()
    home = home_dir()
    return Settings(
        home=home,
        db_path=Path(os.getenv("HUB_DB_PATH", str(home / "hub.db"))),
        token_path=Path(os.getenv("FYERS_TOKEN_PATH", str(home / "token.json"))),
        log_dir=home / "logs",
        app_id=os.getenv("FYERS_APP_ID", "").strip(),
        secret_key=os.getenv("FYERS_SECRET_KEY", "").strip(),
        redirect_uri=os.getenv("FYERS_REDIRECT_URI", DEFAULT_REDIRECT).strip(),
        pin=os.getenv("FYERS_PIN", "").strip(),
        max_per_sec=int(os.getenv("FYERS_MAX_PER_SEC", "5")),
        max_per_min=int(os.getenv("FYERS_MAX_PER_MIN", "50")),
        risk_free_rate=float(os.getenv("HUB_RISK_FREE_RATE", "0.07")),
    )


def read_symbol_file(name: str, home: Path | None = None) -> list[str]:
    """~/.fyers_hub/<name> ho to wahi, warna package ka default."""
    home = home or home_dir()
    p = home / name
    if not p.is_file():
        p = PKG_DIR / "config" / name
    out: list[str] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out
