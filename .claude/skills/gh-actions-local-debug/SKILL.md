---
name: gh-actions-local-debug
description: Debug GitHub Actions workflows locally with act and Docker, including mapping failed PR runs to local reproduction, injecting secrets/env, and attaching an interactive shell to the runner container. Use when Codex/Claude needs to reproduce or investigate GitHub Actions failures locally.
compatibility:
  - Requires act and Docker.
  - Optional: GitHub CLI (gh) for querying PR checks/runs.
allowed-tools: Bash(act:*) Bash(docker:*) Bash(gh:*) Read Write
---

# gh actions local debug

## When to use this skill
- A GitHub Actions workflow fails and you want a local repro with act.
- You need to inspect the runner container interactively.
- You need to inject secrets/env files to mirror CI.
- You want to correlate a PR check failure with a local act run.

## Inputs the agent needs
- Repo root and the target workflow file (or event type + job name).
- The failing job name (or the PR run/check details).
- Any required secrets/env values (prefer local files, never commit secrets).
- Whether gh is available for querying runs.

## Setup (local prerequisites)
- Ensure Docker is installed and the daemon is running.
- Install act if missing:
```bash
brew install act
```
- Optional: install and authenticate GitHub CLI (`gh`) to query PR runs.

## Helper scripts (preferred)
These are installed under the skill directory:
- `scripts/act_list_jobs.sh` — list workflows/jobs (optionally for a single workflow file).
- `scripts/act_run_job.sh` — run a specific job with optional event/secrets/env files; auto-sets `--container-architecture linux/amd64` on Apple Silicon (override with `ACT_CONTAINER_ARCH`).
- `scripts/act_attach_shell.sh` — attach to a running act container shell.

Examples:
```bash
scripts/act_list_jobs.sh
scripts/act_list_jobs.sh .github/workflows/ci.yml

scripts/act_run_job.sh -j <job-id> -W .github/workflows/ci.yml \
  -e /path/to/event.json -s .env.secrets -E .env.ci

scripts/act_attach_shell.sh
```

## Quick start (act only)
1) List workflows and jobs:
```bash
act -l
```
2) Run a job locally (replace placeholders):
```bash
act -j <job-id> -W .github/workflows/<workflow>.yml
```
3) Provide an event payload if needed:
```bash
act -j <job-id> -W .github/workflows/<workflow>.yml -e /path/to/event.json
```
Tip: run `act --help` to confirm flags for your installed version.

## Identify what failed (optional gh)
If gh is available, use it to locate the failing run tied to your PR:

```bash
# current PR for the branch
gh pr view --json number,headRefName,url

# list recent runs for this branch or PR event
gh run list --branch <branch> --event pull_request

# inspect a specific run
gh run view <run-id>
```
Then extract the workflow name and job name to reproduce locally with act.

## Secrets and env injection
Prefer local files, never commit secrets.

Common approaches (check `act --help` for exact flags in your version):
- Provide a secrets file (key=value per line).
- Provide an env file (key=value per line).
- Provide single secret/env entries via CLI flags.

Example (flag names may differ by version):
```bash
act -j <job-id> -W .github/workflows/<workflow>.yml \
  --secret-file .env.secrets \
  --env-file .env.ci
```

## Interactive shell in the runner container
Goal: keep the runner alive long enough to attach with Docker.

1) Add a temporary debug step to the job (local-only change):
```yaml
- name: Debug shell
  run: |
    echo "Runner ready"; sleep 3600
```
2) Start the job with act.
3) Find the runner container and attach:
```bash
docker ps --filter "name=act" --format "{{.ID}} {{.Names}}"
docker exec -it <container-id> /bin/bash
```
Remove the debug step after you are done.

## Rerun a failed step only (no direct step flag)
act typically runs a full job. To isolate a step:
- Re-run the job with act and temporarily guard earlier steps using `if:` conditions.
- Use env-based gates for local-only runs (example):
```yaml
- name: Setup
  if: ${{ !env.ACT_SKIP_SETUP }}
  run: ./setup.sh
```
Then run:
```bash
ACT_SKIP_SETUP=1 act -j <job-id> -W .github/workflows/<workflow>.yml
```
This keeps changes local and avoids altering CI behavior.

## Debug checklist
- Confirm Docker daemon is running.
- Run `act -l` and verify the job id matches the workflow.
- Align event payloads (`pull_request`, `push`, etc.).
- Inject secrets/env needed by the job (local files only).
- Keep changes local (avoid committing debug-only steps or secrets).

## Extension points
- Add helper scripts for common patterns (list jobs, run job with env/secret files).
- Add a reference file with org-specific secrets mapping and event payload templates.
