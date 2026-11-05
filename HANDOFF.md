# HANDOFF — Login + Broker Connect

Last updated: 2026-11-05

## Kya ban chuka hai (Done)

### A) Login (backend + frontend)
- `backend/auth/session.py`: in-memory `SessionStore`, `LoginLimiter` (5 failures / 15 min lockout on IP+username), bcrypt `verify_credentials` (constant-time user compare), cookie helpers.
- `backend/api/auth.py`:
  - `POST /auth/login` → success par `HttpOnly`, `SameSite=Strict`, `Secure` (jab `HTTPS=1`) session cookie.
  - `GET /auth/me` → `{authenticated, user}`.
  - `POST /auth/logout` → session delete + cookie clear.
- Login/logout/failed-login `persistence.audit` me log hote hain (`login_success`, `login_failed`, `logout`).
- `backend/app.py`: middleware ab **session cookie YA X-API-Key** dono accept karta hai; `/health`, `/auth/*` public.
- `scripts/make_admin.py`: hidden prompt se password leta hai (>=10 chars), bcrypt hash bana kar `infra/.env` me `ADMIN_USER` + `ADMIN_PASSWORD_HASH` likhta hai.
- Frontend: naya `#login` page (`frontend/src/pages/login.ts`), dark theme + existing `global.css` classes (`card`, `error`, inputs).
- `frontend/src/app.ts`: auth check + protected routes; bina login `#login` par redirect; nav me username + Logout.
- `frontend/src/api/client.ts`: `credentials: "include"` (cookie bhejne ke liye).

### B) Broker connect (Fyers first)
- `backend/api/brokers.py`:
  - `GET /brokers/fyers/status` → Connected / Not connected, `expires_at`, `expires_in_hours` (token kabhi response me nahi).
  - `GET /brokers/fyers/auth-url` → `fyers_hub.auth.flow.login_url`.
  - `POST /brokers/fyers/connect` → poora redirect URL se auth_code nikaal kar token `~/.fyers_hub` me save.
  - `POST /brokers/fyers/refresh` → `FYERS_PIN` se refresh.
  - `POST /brokers/fyers/disconnect` → token file delete.
- Interface future brokers (Dhan) ke liye alag endpoints/status per-broker pattern me rakha gaya hai. Koi order/trading code nahi.
- Settings page me "Brokers" card: status badge, token expiry, Connect (login URL + redirect URL paste box), Refresh, Disconnect. Token/secret/PIN kabhi render nahi hote.

## Kya baaki hai (Remaining / NOT done)
- **Docker wiring (zaroori)**: `infra/docker-compose.yml` abhi `ADMIN_USER`/`ADMIN_PASSWORD_HASH` backend ko pass nahi karta; `~/.fyers_hub/.env` read-only mount bhi nahi hai (spec B5). `FYERS_HUB_HOME` / `FYERS_ENV_FILE` set karna hoga.
- **Dependency**: `requirements-prod.txt` me `bcrypt` nahi hai → production/Docker image me import fail karega. Add karna hoga (`bcrypt>=4,<5`).
- **A6 adhoora**: Settings se legacy API-key form hatana baaki hai (abhi "API Key (Legacy)" ke roop me maujood hai).
- **Deploy verification**: `docker compose up -d --build` nahi chalaya gaya.
- **UI tests 16/16**: repo me koi UI/E2E test suite maujood nahi (sirf REPORT_FINAL.md/PRODUCTION_GAPS.md me zikr hai). Naye UI tests likhne/run karne hain.
- **Session store in-memory** hai; `--workers 1` par theek hai, multi-worker/restart par sessions chale jayenge (Redis/file store future me).
- Dhan broker sirf design-level placeholder hai (implement nahi).

## Test status
- Full `python -m pytest`: **302 passed** (280 purane + 22 naye), 0 failed.
- `npm run typecheck`: **pass**.
- `npm run build`: **pass** (vite build OK).
- Naye tests:
  - `tests/unit/backend/api/test_auth.py` (12): sahi/galat password, unknown user, 5-failure lockout, cookie flags, /me, logout, audit logs, X-API-Key, protected endpoint.
  - `tests/unit/backend/api/test_brokers.py` (10): status (connected/not), auth-url, connect (success/invalid), refresh (success/needs login), disconnect, token response me nahi, unauthorized.
- `tests/unit/backend/conftest.py`: `make_app` factory + autouse state reset (session/limiter).

## Badli / nayi files
Modified:
- `backend/app.py` — auth middleware (cookie + API key), public `/auth/*`, auth+brokers routers.
- `frontend/src/api/client.ts` — `credentials: "include"`.
- `frontend/src/app.ts` — auth guard, routing, nav + logout.
- `frontend/src/pages/settings.ts` — Brokers card (Fyers).

New:
- `backend/auth/session.py`
- `backend/api/auth.py`
- `backend/api/brokers.py`
- `frontend/src/pages/login.ts`
- `scripts/make_admin.py`
- `tests/unit/backend/conftest.py`
- `tests/unit/backend/api/test_auth.py`
- `tests/unit/backend/api/test_brokers.py`

## Agla kadam (suggested order)
1. `requirements-prod.txt` me `bcrypt` add karo.
2. Compose me admin env vars + `~/.fyers_hub` read-only mount + `FYERS_HUB_HOME` set karo.
3. Settings se legacy API-key form hatao.
4. `docker compose up -d --build` + manual login/broker smoke test.
5. UI E2E tests (16) likho/run karo.
