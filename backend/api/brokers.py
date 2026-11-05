"""Broker endpoints: Fyers connect, status, refresh, disconnect.
Interface designed to be extensible for other brokers (Dhan, etc.) later."""
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Body, Cookie, HTTPException, Request
from pydantic import BaseModel

from backend.auth.session import is_authorized
from fyers_hub.auth import flow
from fyers_hub.auth.store import load_token
from fyers_hub.settings import get_settings, home_dir


class BrokerStatus(BaseModel):
    broker: str
    connected: bool
    expires_at: Optional[int] = None
    expires_in_hours: Optional[int] = None
    error: Optional[str] = None


class ConnectRequest(BaseModel):
    redirect_url: str  # Full redirect URL from Fyers after login


class ConnectResponse(BaseModel):
    ok: bool
    message: str


class RefreshResponse(BaseModel):
    ok: bool
    message: str
    expires_at: Optional[int] = None


router = APIRouter()


def _require_auth(request: Request):
    if not is_authorized(request.headers, os.environ.get("API_KEY", ""), request.cookies):
        raise HTTPException(status_code=401, detail="unauthorized")


@router.get("/brokers/fyers/status", response_model=BrokerStatus)
async def fyers_status(request: Request):
    _require_auth(request)
    try:
        s = get_settings()
        tok = load_token(s.token_path)
        if tok and tok.valid():
            import time
            expires_in = int((tok.expires_at - time.time()) / 3600)
            return BrokerStatus(
                broker="fyers",
                connected=True,
                expires_at=tok.expires_at,
                expires_in_hours=max(0, expires_in),
            )
        return BrokerStatus(broker="fyers", connected=False, error="Not connected or token expired")
    except Exception as e:
        return BrokerStatus(broker="fyers", connected=False, error=str(e))


@router.get("/brokers/fyers/auth-url")
async def fyers_auth_url(request: Request):
    _require_auth(request)
    try:
        s = get_settings()
        s.require_app()
        url = flow.login_url(s)
        return {"auth_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/brokers/fyers/connect", response_model=ConnectResponse)
async def fyers_connect(request: Request, body: ConnectRequest):
    _require_auth(request)
    try:
        s = get_settings()
        s.require_app()
        auth_code = flow.parse_auth_code(body.redirect_url, s)
        flow.exchange_code(auth_code, s)
        return ConnectResponse(ok=True, message="Fyers connected successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/brokers/fyers/refresh", response_model=RefreshResponse)
async def fyers_refresh(request: Request):
    _require_auth(request)
    try:
        s = get_settings()
        s.require_app()
        tok = flow.refresh(s)
        return RefreshResponse(ok=True, message="Token refreshed", expires_at=tok.expires_at)
    except flow.NeedsLogin as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/brokers/fyers/disconnect")
async def fyers_disconnect(request: Request):
    _require_auth(request)
    try:
        s = get_settings()
        token_path = s.token_path
        if token_path.exists():
            token_path.unlink()
        return {"ok": True, "message": "Fyers disconnected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))