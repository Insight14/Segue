# Instructions for the coding agent

Read `docs/PROJECT_SPEC.md` fully before writing anything. It is the source of truth.

## How to work
1. Build **one milestone at a time** (spec section 13), starting with M0. Do not begin the next milestone until the
   current one's acceptance criteria pass. Tell the owner which milestone you are on and what is left.
2. If something in the spec is ambiguous or a decision is listed under "Open decisions", **ask the owner** instead of guessing.
3. Do not modify `prototypes/phase1-laptop/` or `firmware/phase1-grove-oled/` except in milestone M6, and keep
   them working without the cloud (local fallback) when you do.
4. Prefer boring, well-documented tools. Pin dependency versions. No abandoned packages.

## Quality bar
- Every milestone ships with tests, a short doc update, and a working `make` target to run it.
- Python: type hints, ruff + mypy (or pyright), pytest. TypeScript: strict mode, eslint.
- Every API route filters by the authenticated user. Add a test that proves user A cannot read user B's data.
- Treat resume text, transcripts, and contact notes as **untrusted input** (prompt injection). Never let them change system instructions or tool permissions.
- Never log secrets, tokens, resume contents, or full transcripts at INFO level.
- Never commit secrets. Use `.env.example` plus Secrets Manager in AWS.
- Docker images: multi-stage, non-root, pinned base images, a healthcheck.
- Infra must be reproducible: Terraform for AWS, a single command to deploy and a single command to destroy.

## Cost and safety rules for cloud work
- Do not create AWS resources on your own. Generate Terraform and let the owner run `plan` and `apply`.
- Use a currently supported Kubernetes version on EKS (past-support versions cost 6x more per hour). Document the destroy step.
- Add AWS Budgets alerts in the Terraform before anything expensive.

## Privacy rules (non-negotiable)
- Text only: never store audio or video. Never identify people from faces.
- Keep the consent reminder in the Live flow and the delete/export features in History.

## Definition of done for a milestone
Acceptance criteria pass, tests are green in CI, docs updated, and you have listed any open questions or follow-ups for the owner.
