# Genesis cloud demo image — one container, one port.
# Multi-stage: Node builds the static frontend, Python serves it and /api from
# the SAME origin (no proxy, no CORS). Built for Hugging Face Spaces (port 7860)
# but runs anywhere Docker does:  docker build -f deploy/Dockerfile -t genesis-demo .

FROM node:20-bookworm-slim AS web
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY frontend/ .
# relative API base: the page calls /api on its own origin, served by FastAPI
RUN NEXT_PUBLIC_API_URL="" NEXT_EXPORT=1 npx next build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    GENESIS_STATIC_DIR=/app/frontend/out \
    GENESIS_OFFLINE=0 \
    TOR_ENABLED=0
COPY --from=web /build/out /app/frontend/out
COPY backend/ /app/backend/
COPY README.md LICENSE /app/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt "uvicorn[standard]"
EXPOSE 7860
WORKDIR /app/backend
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
