# Deployment

Local: `./scripts/setup_truemax.sh`. Docker: `docker compose -f infra/docker-compose.yml up --build`. CI: `.github/workflows/ci.yml`.

Docker data path: compose mounts `./data` read-only at `/app/data` and sets `DATA_DIR=/app/data/samples`.
The `runs-init` one-shot service chowns the host `./runs` bind mount to UID/GID 10001 before the backend starts,
so the non-root backend can write reports. The frontend is exposed on `http://localhost:8080` and proxies `/api`.

Sample datasets (gitignored) can be generated before starting the stack:

```bash
python -m cli.main make-sample
python -m cli.main make-options-sample
```
