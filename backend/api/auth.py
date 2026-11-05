"""/api/auth/* endpoints: login, me, logout."""
import os
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from backend.auth.session import (
    audit_login_event,
    clear_session_cookie,
    get_client_ip,
    is_authorized,
    login_limiter,
    session_store,
    set_session_cookie,
    verify_credentials,
)
from persistence import audit as audit_module


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    ok: bool = True
    user: str


class MeResponse(BaseModel):
    authenticated: bool
    user: str | None = None


def get_audit_root():
    from backend.api.common import runs_root
    return runs_root()


router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: Request, response: Response, body: LoginRequest):
    ip = get_client_ip(request)
    username = body.username.strip()
    password = body.password

    # Lock check
    locked, remaining_seconds = login_limiter.is_locked(ip, username)
    if locked:
        audit_login_event("login_failed", username, ip, False, f"locked for {remaining_seconds}s")
        raise HTTPException(status_code=429, detail=f"Too many attempts. Try again in {remaining_seconds} seconds.")

    # Verify credentials
    if not verify_credentials(username, password):
        remaining = login_limiter.record_failure(ip, username)
        audit_login_event("login_failed", username, ip, False, f"remaining attempts: {remaining}")
        if remaining == 0:
            raise HTTPException(status_code=429, detail="Too many failed attempts. Locked for 15 minutes.")
        raise HTTPException(status_code=401, detail=f"Invalid credentials. {remaining} attempts remaining.")

    # Success
    login_limiter.record_success(ip, username)
    token = session_store.create(username)
    secure = os.environ.get("HTTPS", "").lower() in ("1", "true", "yes")
    set_session_cookie(response, token, secure=secure)
    audit_login_event("login_success", username, ip, True)
    return LoginResponse(user=username)


@router.post("/auth/logout")
async def logout(request: Request, response: Response, session_id: str | None = Cookie(default=None, alias="session_id")):
    ip = get_client_ip(request)
    username = "unknown"
    if session_id:
        sess = session_store.get(session_id)
        if sess:
            username = sess.username
        session_store.delete(session_id)
    clear_session_cookie(response)
    audit_login_event("logout", username, ip, True)
    return {"ok": True}


@router.get("/auth/me", response_model=MeResponse)
async def me(request: Request, session_id: str | None = Cookie(default=None, alias="session_id")):
    if session_id:
        sess = session_store.get(session_id)
        if sess:
            return MeResponse(authenticated=True, user=sess.username)
    raise HTTPException(status_code=401, detail="unauthorized")