# --- Stage 1: build the frontend ---
FROM node:20-alpine AS frontend

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


# --- Stage 2: Python runtime with both backend + built frontend ---
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

# System deps (httpx + grpc need ca-certificates; alembic doesn't need anything extra)
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY --from=frontend /app/frontend/dist /app/frontend/dist

# Cloud Run sets PORT (defaults to 8080). Bind to 0.0.0.0 so the platform
# can reach the container. Use a single uvicorn worker — agent runs hold
# in-memory background tasks (no shared multi-worker state).
EXPOSE 8080
WORKDIR /app/backend
CMD ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
