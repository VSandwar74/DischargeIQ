# DischargeIQ — Multi-stage build (backend + frontend)
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend
COPY src/frontend/package.json src/frontend/package-lock.json* ./
RUN npm ci
COPY src/frontend/ ./
RUN npm run build


FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY src/ src/
COPY migrations/ migrations/
COPY alembic.ini .

# Copy built frontend into static dir served by FastAPI
COPY --from=frontend-build /app/frontend/build /app/static

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

EXPOSE 8000

# Start: run migrations then launch uvicorn
CMD ["sh", "-c", "\
    if [ \"$DEV_MODE\" != 'true' ]; then \
        alembic upgrade head 2>/dev/null || true; \
    fi && \
    uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000} \
"]
