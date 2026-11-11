# Stage 1: Build stage
FROM python:3.12.8-slim-bookworm AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.12.8-slim-bookworm AS runner

# Run as non-root user
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY src/ /app/src/

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import time, sys; from pathlib import Path; f = Path('/tmp/worker_healthy'); sys.exit(0 if f.exists() and time.time() - float(f.read_text()) < 60 else 1)"

CMD ["python", "-m", "worker.main"]

