# Backend image (repo root se build): docker build -f infra/Dockerfile -t svl-backend .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Non-root user (uid 10001)
RUN groupadd --system app && useradd --system --gid app --uid 10001 --home /app app

COPY requirements-prod.txt ./requirements-prod.txt
RUN pip install -r requirements-prod.txt

COPY . .
RUN mkdir -p /app/runs /app/data && chown -R app:app /app/runs

USER app
EXPOSE 8000

# --workers 1: job queue abhi in-memory hai (multi-worker par jobs ek process me hi dikhenge)
CMD ["uvicorn", "--factory", "backend.app:create_app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers"]
