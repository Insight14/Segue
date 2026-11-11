# Convo Glasses API

FastAPI companion backend for the Convo Glasses smart-glasses assistant.

## Ops Probes
- `GET /healthz`: Liveness probe (process up)
- `GET /readyz`: Readiness probe (database connectivity)
- `GET /metrics`: Metrics probe

## Running locally
```bash
uvicorn api.main:app --reload --port 8000
```

