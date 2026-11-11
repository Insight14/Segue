# Convo Glasses - Project Specification

Audience: an AI coding agent and the human owner, building this repo one milestone at a time.
Status: the Phase 1 laptop prototype exists (included). Everything else in this document is TO BUILD.
Written: 2026-11-10. Cloud prices and free-tier rules change often - re-verify before relying on them.

---

## 1. Product summary

People who are new to job fairs and networking often freeze or run out of things to say, and
preparing in advance is easy to skip. Convo Glasses is an assistant that:

1. Listens to the person the user is talking to, converts speech to text, and shows 3 short,
   natural suggestions (a follow-up, a way to connect their own background, and something
   lighthearted, e.g. a current-events hook) on a small display in the user's glasses.
2. Uses a companion **mobile app** where the user stores who they are (resume, experience, goals,
   interests, hobbies, key life moments) so suggestions are personal and honest.
3. Includes an **AI guide agent** in the app that helps the user figure out what they care about,
   and turns everything they shared into talking points for an upcoming event or person.
4. Stores every conversation as **text only** (no audio, no video) together with details of the
   person spoken to, and shows it as a browsable history in the app.

### Non-goals (do not build)
- No audio or video retention. Audio is processed in memory and discarded.
- No facial recognition to identify who someone is. (Phase 2 may use faces only to find where
  the active speaker is in the camera frame - on device, never stored.)
- No scraping of people's social profiles. Person details are typed in by the user.
- Not a substitute for preparation; it is a coach, not a script.

---

## 2. Phases

| Phase | What | State |
|---|---|---|
| 1 | Laptop prototype: mic -> Whisper -> LLM -> Grove Beginner Kit OLED over USB serial; button = next suggestion; rating loop for "training" | DONE (see prototypes/phase1-laptop, firmware/phase1-grove-oled) |
| 1.5 | Companion platform: mobile app + cloud backend (this spec, milestones M0-M9). Phase 1 coach is moved behind an API and logs conversations | TO BUILD |
| 1.75 | Glasses firmware on ESP32-S3 (I2S mic, OLED, button) talking to the phone | after hardware is built (M11) |
| 2 | Focus on the person being looked at (camera + mic array + speaker lock) | design only, section 12 |
| 3 | Physical build onto glasses (optics, mounts, battery) | build guide to be written when the owner has all parts |

---

## 3. Architecture

```
 GLASSES (Phase 1.75+)                      MOBILE APP (Expo / React Native)
 ESP32-S3: I2S mic, OLED, button   <--BLE-- text frames + button events
           (camera in Phase 2)     --WiFi-> audio chunks (WebSocket) [or audio captured by phone]
                                                |
                                                | HTTPS: REST + SSE, JWT (Cognito)
                                                v
 AWS ---------------------------------------------------------------------------
  ALB/Ingress -> Kubernetes (EKS): api (FastAPI) | worker (SQS consumer)
  RDS PostgreSQL (+ optional pgvector) | S3 (resume files) | SQS | Cognito
  Secrets Manager | CloudWatch / Prometheus+Grafana | ECR
  LLM providers behind one interface: Groq (free tier) | Ollama (local) | Bedrock (optional)
 -------------------------------------------------------------------------------

 TODAY (Phase 1):  laptop mic -> faster-whisper -> LLM -> USB serial -> Grove kit OLED
```

### Data flows
- **Prep flow:** user adds profile data (typed, or resume upload) -> worker extracts candidate facts ->
  user confirms -> guide agent uses confirmed facts to build talking points for an event/person.
- **Live flow:** speech -> text (STT) -> `POST /coach/suggest` (profile + recent transcript + headlines
  + user's rated examples) -> 3 suggestions -> device display; every message and suggestion is persisted.
- **History flow:** app lists conversations by event/date/person, opens a transcript view with the
  suggestions shown and their ratings, supports search, delete, and export.
- **Offline-first:** crowded venues have bad Wi-Fi. Before an event the client caches the profile
  summary and talking points; if the API is unreachable the live coach falls back to a local LLM
  (Ollama) or cached content, and queues logs to sync later.

---

## 4. Tech stack and why (resume-visible choices)

| Layer | Choice | Notes |
|---|---|---|
| Mobile | React Native + Expo (TypeScript), Expo Router, TanStack Query | Expo Go for early milestones. BLE needs a custom dev client (EAS build), so defer BLE to M11. |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic | OpenAPI is the contract; generate a typed client for the app. |
| Database | PostgreSQL 16 (RDS in AWS) | pgvector is OPTIONAL (M10); a profile is small enough to put in the prompt. |
| Object storage | S3, presigned uploads | Resume files only. |
| Async jobs | SQS + a worker container | Resume parsing, talking-point generation if slow. |
| Auth | Amazon Cognito user pool (hosted UI / Amplify Auth) | Local dev uses an env-guarded auth bypass, never enabled in AWS. |
| LLM | Provider interface with Groq (default, free tier), Ollama (local/offline), Bedrock (AWS-native, paid) | Use OpenAI-compatible client for Groq/Ollama. |
| STT | faster-whisper locally now; later Groq Whisper or Amazon Transcribe | Keep behind an `SttProvider` interface. |
| Containers | Docker (multi-stage, non-root), docker-compose for local dev | MinIO (S3) and ElasticMQ (SQS) emulate AWS locally. |
| Orchestration | Kubernetes: k3d/kind locally, EKS in AWS; Helm or Kustomize | See ADR-1 for the honest trade-off. |
| IaC | Terraform | VPC, EKS, RDS, S3, SQS, Cognito, ECR, IAM (IRSA), Secrets Manager. |
| CI/CD | GitHub Actions (OIDC to AWS, no long-lived keys) | lint, test, build, scan, push to ECR, deploy. |
| Observability | Structured JSON logs, Prometheus + Grafana (or CloudWatch Container Insights) | Optional OpenTelemetry traces. |

### ADR-1: Why Kubernetes (and when it would be the wrong choice)
Kubernetes is far more than this workload needs: one small API, one worker, one database. ECS Fargate
would be simpler and has no control-plane fee. Kubernetes is chosen here deliberately to demonstrate
skills (manifests/Helm, probes, HPA, ingress, secrets, IRSA, GitOps-style deploys). The repo must
therefore (a) run fully on Docker Compose with no AWS account, (b) run on a local k3d cluster, and
(c) deploy to EKS only through scripted `apply` and `destroy` so cost stays low. The README should
state this trade-off plainly; interviewers respect it more than pretending K8s was required.

---

## 5. Data model (PostgreSQL)

All tables have `id` (UUID), `created_at`, `updated_at`. All user-owned rows carry `user_id` and every
query MUST filter by the authenticated user.

| Table | Key columns |
|---|---|
| users | cognito_sub (unique), email, display_name, retention_days (default 90, null = keep), settings (jsonb) |
| profiles | user_id (unique), headline, status (e.g. "CS junior"), goals, tone_preference, summary_md |
| profile_facts | user_id, kind (experience / education / skill / interest / hobby / goal / value / story_success / story_failure / story_collaboration / other), title, body, tags (text[]), source (user / resume / agent), confirmed (bool), embedding (vector, nullable) |
| documents | user_id, s3_key, filename, mime, status (uploaded / parsing / parsed / failed), parsed_text |
| events | user_id, name, date, type (career fair, networking, interview, other), notes |
| contacts | user_id, event_id (nullable), name, company, role, notes, consent_noted (bool) |
| conversations | user_id, contact_id, event_id, started_at, ended_at, summary, source (laptop / phone / glasses) |
| messages | conversation_id, seq, speaker (other / user / unknown), text |
| suggestions | conversation_id, after_message_seq, type, text, shown (bool), selected (bool), rating (1-5, nullable) |
| talking_points | user_id, event_id (nullable), contact_id (nullable), content (jsonb, see 7.3) |
| agent_threads / agent_messages | user_id, mode (discover / prep), role, content |
| devices (later) | user_id, kind, name, paired_at, last_seen |

Retention: a nightly job deletes conversations older than `retention_days`. Hard delete, not soft.

---

## 6. API surface (REST, versioned under /v1)

Auth: Bearer JWT on everything except `/healthz` and `/readyz`.

- Profile: `GET/PUT /profile`, `GET/POST /facts`, `PATCH/DELETE /facts/{id}`
- Documents: `POST /documents/upload-url` (presigned S3 PUT), `POST /documents/{id}/process`, `GET /documents/{id}`
- Guide agent: `POST /agent/threads`, `POST /agent/threads/{id}/messages` (SSE stream), `GET /agent/threads/{id}`
- Talking points: `POST /talking-points` (body: event_id and/or contact_id, free-text notes), `GET /talking-points/{id}`
- Events and contacts: CRUD on `/events`, `/contacts`
- Conversations: `POST /conversations`, `PATCH /conversations/{id}` (end, summary), `GET /conversations` (filter by event, contact, date, text search),
  `GET /conversations/{id}`, `POST /conversations/{id}/messages`, `DELETE /conversations/{id}`, `GET /conversations/{id}/export`
- Live coach: `POST /coach/suggest` (conversation_id; returns up to 3 suggestions and persists them),
  `PATCH /suggestions/{id}` (shown / selected / rating)
- Training data: `GET /training/export` (rated suggestions as JSONL for later fine-tuning)
- Ops: `GET /healthz`, `GET /readyz`, `GET /metrics`

---

## 7. AI agent design

### 7.1 Modes
1. **Discover** - for users unsure what they care about or what to say about themselves. Asks ONE
   question at a time, uses prompts like: what made you lose track of time, a project you are proud of,
   a failure and what changed, a time you worked with others (STAR: Situation, Task, Action, Result).
   After each answer it proposes a fact; the user confirms/edits before it is saved (confirmed=true).
2. **Prep** - given an event and/or a contact plus the confirmed profile, produces talking points (7.3).
3. **Live coach** - the Phase 1 logic exposed as `POST /coach/suggest` (see `prototypes/phase1-laptop/convo_coach.py`:
   `SYSTEM_PROMPT`, `build_prompt`, example retrieval from rated suggestions).

### 7.2 Tools available to the agent
`get_profile`, `list_facts(kind?, tag?)`, `propose_fact` (never auto-confirms), `get_event`, `get_contact`,
`list_recent_conversations`, optional `search_facts` (only if pgvector is enabled).

### 7.3 Talking-points output (JSON schema, validate with Pydantic)
```
{
  "pitch_30s": "string, first person",
  "stories": [{"title": "", "situation": "", "action": "", "result": "", "fact_id": ""}],   // max 3, each tied to a confirmed fact
  "questions_to_ask": ["..."],      // 5, specific to the event/contact when notes exist
  "icebreakers": ["..."],           // 3, include at most one current-events hook, harmless only
  "if_asked_about_weakness": "string, built from a real failure fact if one exists, else null",
  "gaps": ["things the agent could not cover because the profile lacks info"]
}
```

### 7.4 Guardrails (acceptance criteria for M3)
- Never invent experience, employers, numbers, or credentials. Every claim about the user must trace to a confirmed fact.
- Never invent facts about a contact or company. If notes are missing, say so in `gaps` and ask.
- No politics, religion, tragedies, or jokes at someone's expense in icebreakers.
- Keep live suggestions <= 80 ASCII characters (device display is 16 x 8 characters).
- Keep an evaluation set (>= 20 cases) in `services/api/tests/evals/` that checks: no fabricated facts, schema validity,
  length limits, and safe-topic rules. Run it in CI against a mocked provider and on demand against a real one.
- Handle provider rate limits: exponential backoff, a per-user minimum gap between live calls, and graceful degradation.

---

## 8. Mobile app UX (keep navigation minimal)

Four bottom tabs only:
1. **About Me** - profile summary at top; facts grouped by kind; add by typing or uploading a resume; review queue for unconfirmed facts.
2. **Coach** - chat with the guide agent. A mode switch (Discover / Prep) and a "Make talking points" button that picks an event or contact.
3. **History** - conversations grouped by event and date; search; tap to open the transcript (message bubbles, suggestions shown, ratings); delete and export.
4. **Live** - start a session: choose or add the contact (name, company, role, notes) and event, see the consent reminder, then start.
   Shows connection state of the glasses/laptop client, the current suggestions, and a stop button.

Settings (retention days, delete all data, provider choice) lives in a profile sheet, not a fifth tab.

---

## 9. Live session and device protocol

### Phase 1 (exists): USB serial laptop <-> Grove kit
- Laptop -> board, 9600 baud, one frame per line: `line0|line1|...|line7\n` (<= 16 chars per segment, <= 8 segments,
  ASCII only, buffer 140 bytes).
- Board -> laptop: `BTN\n` when the Grove button (D6) is pressed = show next suggestion.

### Phase 1.75 (design target): ESP32-S3 glasses <-> phone
- Control and display text over BLE (low bandwidth): same frame format, plus `BTN` events.
- Audio over Wi-Fi WebSocket (16 kHz, 16-bit mono, chunked, optionally compressed). Raw 16 kHz/16-bit audio is
  about 256 kbit/s, which is tight for BLE in practice, so Wi-Fi (phone hotspot) is the default for audio.
- Whisper is NOT run on the ESP32. STT happens on the phone or in the backend.

---

## 10. Privacy, consent, and safety requirements

- Text only. Never store audio or video. Delete audio buffers immediately after transcription.
- The Live tab shows a consent reminder before every session. Recording-consent laws differ by state and country
  (some require every party's consent). The app must say this plainly and let the user record `consent_noted` per contact.
- Conversation partners are third parties: store only what the user typed plus the transcript; provide delete-all and per-conversation delete.
- Encrypt in transit (TLS) and at rest (RDS/S3 KMS). Secrets only in Secrets Manager / env, never in git.
- Do not infer or store protected characteristics (health, religion, ethnicity, etc.) about the user or contacts.
- Send third-party LLM providers only what is needed. Free tiers may use submitted data to improve their products;
  expose a setting to use the local provider (Ollama) for sensitive sessions.
- Rate-limit and validate all inputs; presigned uploads limited to PDF/DOCX and a size cap; scan or sandbox parsing.
- Threat model note in docs before M9: IDOR on user-owned rows, prompt injection via resume text or transcripts
  (treat all of it as untrusted data, never as instructions), SSRF, secrets leakage.

---

## 11. Infrastructure and delivery

### Target repo layout
```
convo-glasses/
  apps/mobile/                 Expo app
  services/api/                FastAPI app, Alembic migrations, tests (+ evals)
  services/worker/             SQS consumer (resume parsing)
  infra/terraform/             modules + envs
  infra/k8s/                   Helm chart or Kustomize (base + overlays: local, aws)
  firmware/phase1-grove-oled/  (exists)
  firmware/glasses-esp32s3/    (later)
  prototypes/phase1-laptop/    (exists)
  docs/                        this spec, ADRs, threat model, runbook
  .github/workflows/
  docker-compose.yml  Makefile
```

### Cost notes (verified Nov 2026, re-check before deploying)
- EKS control plane: $0.10 per cluster-hour (about $73/month) on a supported Kubernetes version, plus worker nodes,
  load balancer, NAT gateway, and RDS. A cluster left on a version past standard support is billed $0.60/hour
  (about $438/month). Always pick a currently supported version and destroy the cluster when not demoing.
- New AWS accounts get a Free plan with up to $200 in credits for 6 months; the account closes when credits or time run out
  unless upgraded, and some services are not available on the Free plan. Check that EKS is allowed; if not, a Paid plan
  with a budget alert is needed. Set AWS Budgets alerts on day one.
- Daily development should use docker compose and k3d (free). Deploy to AWS only through `terraform apply`, demo, then `terraform destroy`.
- Fallback if cost is a problem: same containers on ECS Fargate or a single EC2 running k3s. Keep manifests portable.
- LLM: Groq free tier is rate limited by tokens as well as requests, so keep prompts lean and enforce a minimum gap between live calls.

---

## 12. Phase 2 design notes (not part of M0-M11)

Goal: only the person the user is facing is audible/transcribed, even when the user looks at a poster, until a new person is faced.
Approach, in build order:
1. Camera finds faces; the face nearest the frame center is the target (head direction = gaze).
2. Active-speaker check: lip-movement from face landmarks correlated with audio activity.
3. Steer a microphone array (beamforming) toward the target's bearing derived from the face's horizontal position.
4. Voiceprint lock: store a speaker embedding for the current target only for the session; gate audio segments that do not match.
5. Low-latency denoise (e.g. RNNoise / DeepFilterNet) and play to earbuds or bone conduction. Keep the audio path very low latency;
   the camera/voiceprint logic can be slower because it only decides what to let through.
6. State machine: keep the lock while the user looks away; switch only when a new face is held near center for ~2 s.
Notes: clothing matching is a weak backup signal only. Needs a Raspberry Pi 4/5 class device or phone for compute if using the ArduCam OV5647
(CSI camera). An ESP32-S3 with a parallel (DVP) camera is a lighter alternative. Faces and voiceprints are biometric data: process on device,
never store, delete at session end.

---

## 13. Milestones and acceptance criteria

Build one milestone per agent session. Do not start the next until acceptance criteria pass. Every milestone adds tests and updates docs.

| ID | Deliverable | Acceptance criteria |
|---|---|---|
| M0 | Monorepo scaffold, docker-compose (api, worker, postgres, minio, elasticmq), Makefile, lint + test CI | `docker compose up` gives `/healthz` 200 and `/readyz` 200; CI green |
| M1 | Auth + profile and facts CRUD, Alembic migrations, OpenAPI client generation | A user can only read/write their own rows (tested); >= 80% coverage on routers |
| M2 | Resume upload (presigned S3), SQS job, worker extracts text and proposes facts, review/confirm endpoints | Sample PDF yields proposed facts; nothing is saved as confirmed without user action |
| M3 | Guide agent: threads, SSE streaming, Discover and Prep modes, talking points, guardrails, eval set | Eval set passes in CI with mocked provider; schema validates; no fabricated facts in test cases |
| M4 | Mobile app MVP: four tabs, profile editing, resume upload, agent chat, talking points | Works end to end on a physical phone via Expo Go against local API |
| M5 | Events, contacts, conversations, history UI with search, delete, export | Create and view a conversation with contact details; delete removes all rows |
| M6 | Live coach in API (`/coach/suggest`), suggestion ratings, `/training/export`; update the laptop prototype to read profile from the API and post messages/suggestions, with local fallback | Mock session is persisted and appears in History; ratings feed the next prompt |
| M7 | Production Dockerfiles, Helm/Kustomize, probes, HPA, local k3d deployment | `make k8s-up` brings the whole stack up on k3d; rolling update works |
| M8 | Terraform for AWS, GitHub Actions OIDC deploy, External Secrets, ALB ingress + TLS, scripted teardown | One command deploys, one destroys; documented monthly cost estimate |
| M9 | Observability (metrics, dashboards, alerts), backups, rate limits, threat-model review, runbook | Dashboard shows latency/error rate; restore from backup tested |
| M10 (opt) | pgvector retrieval over facts | Retrieval beats full-profile prompting on the eval set, or it is not merged |
| M11 | ESP32-S3 glasses firmware + BLE/WebSocket protocol + app pairing screen | Phone shows suggestions on the glasses display; button cycles suggestions |

---

## 14. Hardware notes

- **Temporary display (now):** Grove Beginner Kit for Arduino (Seeeduino Lotus, select "Arduino Uno" in the IDE).
  The owner's board has a **micro-USB** port, so use a micro-USB data cable (not USB-B). Pre-wired: button D6, buzzer D5,
  LED D4, OLED on I2C (0x78), light A6, sound A2, rotary A0, temp/humidity D3, air pressure and accelerometer on I2C.
  Display is 16 x 8 characters using the U8x8 text mode.
- **ESP32-S3 N16R8 (owned):** a good fit as the glasses brain. It has Wi-Fi + BLE, native USB, I2S for a digital MEMS mic,
  I2C for the OLED, 16 MB flash and 8 MB PSRAM. It cannot run Whisper or an LLM, so STT and LLM stay on the phone/cloud.
  On N16R8 boards the octal PSRAM uses GPIO35, 36, 37 (and 33-34 may also be reserved); avoid GPIO33-37 for your own wiring.
  Logic is 3.3 V. Dev boards are bulky for glasses; a smaller module (for example a XIAO ESP32S3 Sense, which bundles a camera and mic)
  can replace it at the final build stage - verify its specs before buying.
- **ArduCam OV5647:** a CSI camera. It does not work with Uno or classic ESP32. It needs a Raspberry Pi (or an ESP32-P4).
- **Glasses build guide: PENDING.** The owner asked to be reminded and asked about this repeatedly. Do not write the build
  procedure until the owner confirms they have the parts.

### Parts status (maintain this list)
| Status | Parts |
|---|---|
| Have | Arduino Uno, Grove Beginner Kit, ESP32-S3 N16R8, ArduCam OV5647, ultrasonic sensor, breadboard, jumpers, buzzer, LEDs, glasses |
| Ordering | SSD1306 0.96" I2C OLED, beamsplitter film, USB-B cable (for the Uno) |
| Still to get (when the owner is ready) | I2S MEMS mic (INMP441 or similar) x1-2, 3.7 V LiPo (500-1000 mAh) with protected charger, small momentary button, thin flexible silicone wire, heat-shrink, hot glue / foam board or 3D-printed bracket |
| Phase 2 only | Raspberry Pi 4/5 (or Zero 2 W for light tasks), multi-mic array, earbuds or bone-conduction speaker |

---

## 15. Open decisions for the owner (ask before building the relevant milestone)
1. Resume bullet focus: platform/DevOps (K8s, Terraform, CI/CD), ML/LLM (agent evals, rating loop), or full-stack mobile? This sets how deep M7-M9 and M3 go.
2. Final cloud target: EKS (max resume value, higher cost) vs ECS Fargate (cheaper) - see ADR-1.
3. LLM default for the deployed app: Groq free tier, Bedrock, or both behind the provider interface.
4. Who is the first real user: only the owner (simpler auth) or friends (needs signup flows, privacy page).
