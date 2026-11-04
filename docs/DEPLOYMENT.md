# Deployment

Local: `./scripts/setup_truemax.sh`. Docker: `docker compose -f infra/docker-compose.yml up --build`. CI: `.github/workflows/ci.yml`.

## Plain HTTP stack (default)

```bash
python -m cli.main make-sample
python -m cli.main make-options-sample
cp infra/.env.example infra/.env   # then set API_KEY (32+ random chars)
docker compose -f infra/docker-compose.yml up -d --build
```

- Frontend: `http://127.0.0.1:8080` (bind is localhost-only).
- Backend: internal `backend:8000`; `/api/*` is proxied by nginx.
- `DATA_DIR=/app/data/samples`; `HUB_DB_PATH=/app/runs/hub.db` (writable, may stay empty).
- Run records are written to `runs/<run_id>/` and mirrored to `DATABASE_URL` SQLite for durable query/backup.
- `runs-init` chowns the host `./runs` bind mount to UID/GID 10001.
- Docker json-file logs rotate at 10 MB × 5 for backend and web.
- Backend rate limits to `RATE_LIMIT_PER_MINUTE` (default 120) and nginx limits `/api/` to 10 r/s with burst 20.
- All sample datasets are labelled `synthetic` by API/report/UI. Do not present them as market evidence.

## HTTPS / TLS (prepared, disabled until DNS + certs exist)

The TLS front door is a Compose profile; it does not start by default.

```bash
mkdir -p infra/certs
# copy fullchain.pem and privkey.pem from certbot/your CA into infra/certs/
# set DOMAIN in infra/.env
docker compose \
  -f infra/docker-compose.yml \
  -f infra/docker-compose.tls.yml \
  --profile tls up -d --build
```

`infra/nginx.tls.conf.template` listens on 80/443, redirects HTTP to HTTPS, terminates TLS 1.2/1.3,
sets HSTS, and proxies to the existing web service. Keep port 8080 local or blocked at the firewall.
Do **not** enable this profile until you control the domain and certificates.

## Backups and restore test

```bash
python scripts/backup.py --runs-root runs --out-dir backups
python scripts/backup.py --verify-restore backups/svl-backup-<timestamp>
```

The script archives `runs/` (including job state), copies the SQLite DB with SQLite's backup API,
writes a SHA-256 manifest, and never deletes older backups. Restore verification happens in a temp dir.
Store `backups/` outside the web root and keep it out of git (already ignored).

## SQLite migrations

```bash
python scripts/migrate.py --sqlite runs/svl.sqlite3
```

Migrations are append-only and idempotent (`persistence/migrations/sqlite/`). The PostgreSQL schema in
`persistence/migrations/001_initial.sql` is not wired to a production adapter yet.

## Operational checks

```bash
curl -fsS http://127.0.0.1:8080/api/health
docker compose -f infra/docker-compose.yml ps
docker inspect --format '{{.State.Health.Status}}' strategy-lab-backend-1
docker inspect --format '{{.State.Health.Status}}' strategy-lab-web-1
```

Rotate `API_KEY` by updating `infra/.env` and recreating the backend/web containers. Never commit it.
