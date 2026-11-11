# Convo Glasses

Smart-glasses conversation coach for job fairs and networking: it listens to the person you are talking to,
shows short suggestions on a tiny display, and a companion mobile app stores your background, helps you
discover what you care about, builds talking points, and keeps a text-only history of your conversations.

## What is in this folder

| Path | What it is | State |
|---|---|---|
| `docs/PROJECT_SPEC.md` | Full specification: architecture, stack, data model, API, agent design, milestones | read this first |
| `AGENTS.md` | Working rules for the AI coding agent | read this second |
| `services/api/` | FastAPI backend service (endpoints, Alembic, health probes) | M0 scaffolded |
| `services/worker/` | SQS background job consumer | M0 scaffolded |
| `apps/mobile/` | Expo / React Native companion app | M0 scaffolded |
| `infra/` | Terraform (`infra/terraform`) and K8s manifests (`infra/k8s`) | M0 scaffolded |
| `prototypes/phase1-laptop/` | Python app: mic -> Whisper -> LLM -> suggestions -> Arduino OLED; rating loop | working prototype |
| `firmware/phase1-grove-oled/` | Arduino sketch for the Grove Beginner Kit OLED + button | working prototype |
| `firmware/glasses-esp32s3/` | Target ESP32-S3 firmware | planned (M11) |

## Development & Monorepo Workflow

### Quickstart
- Install dependencies: `make install`
- Run linting (ruff, mypy): `make lint`
- Run tests: `make test`
- Start local infrastructure stack: `make up` (requires Docker)
- Stop local infrastructure stack: `make down`

### Milestones Progress
- [x] **M0**: Monorepo scaffold, docker-compose (`api`, `worker`, `postgres`, `minio`, `elasticmq`), Makefile, lint + test CI.
- [x] **M1**: Auth + profile and facts CRUD, Alembic migrations, OpenAPI client generation.
- [x] **M2**: Resume upload (presigned S3), SQS job, worker fact extraction, review/confirm endpoints.
- [x] **M3**: Guide agent (Discover & Prep modes, talking points, guardrails, 20-case eval set).
- [x] **M4**: Mobile app MVP (four tabs: About Me, Coach, History, Live via Expo Router).
- [ ] **M5**: Events, contacts, conversations, history UI.
- [ ] **M6**: Live coach in API (`/coach/suggest`), suggestion ratings, laptop prototype integration.
- [ ] **M7**: Production Dockerfiles, Helm/Kustomize, k3d deployment.
- [ ] **M8**: Terraform for AWS, GitHub Actions OIDC deploy.
- [ ] **M9**: Observability, backups, rate limits, threat model.
- [ ] **M10**: pgvector retrieval over facts (optional).
- [ ] **M11**: ESP32-S3 glasses firmware + BLE/WebSocket protocol.

## Handing this to an IDE agent

Open this folder as the workspace and say:

> Read AGENTS.md and docs/PROJECT_SPEC.md. Start with milestone M0 only. Stop when its acceptance criteria pass and summarize what you did and what you need from me.

Then repeat one milestone at a time (M1, M2, ...).

## Running the Phase 1 prototype

1. Arduino IDE: install the **U8g2** library, open `firmware/phase1-grove-oled/arduino_oled.ino`, board **Arduino Uno**, upload.
   The Grove Beginner Kit board uses a **micro-USB** port. If no serial port appears, install the CP2102 driver from Seeed's wiki.
2. `cd prototypes/phase1-laptop && pip install -r requirements.txt`
   (Linux also needs `sudo apt install libportaudio2`.)
3. Edit `profile.json` (it will later come from the app/API).
4. Free API key from console.groq.com, then set `GROQ_API_KEY` in your terminal.
5. `python convo_coach.py --llm groq` (add `--no-arduino` to test without the board, or `--llm ollama` for fully local).
6. After a session: `python review.py` to rate suggestions; `python review.py --export` for fine-tuning data later.

Tuning: `--whisper small.en` for accuracy, `--thresh 0.02` if it triggers on background noise, `--device N` to pick a mic.

## Privacy

Text only. No audio or video is stored. Recording-consent laws vary by location; tell the people you talk to.
