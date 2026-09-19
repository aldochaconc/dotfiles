# AGENTS.md

This file defines the **default operating protocol** for LLM agents (e.g., Codex CLI, Claude Code) collaborating with human SWEs in this repository.

Repository: **dotfiles**

It is optimized for **greenfield, fast-iteration** work: prototypes, spikes, MVPs, and early product exploration. It assumes **little prior structure**, and it tells the agent how to create and maintain the minimal set of artifacts that keep development aligned and repeatable.

## Golden rules (read first)

1. **Artifacts > chat memory.**  
   Persist intent, decisions, and “what’s next” in repo docs. Assume chat context can disappear at any time.

2. **Docs-first, then code.**  
   Before writing or changing production code, ensure the relevant docs exist and reflect the intended behavior.

3. **Prefer Makefile targets when available.**  
   If a `Makefile` is present, use `make` targets (e.g., `make lint`, `make test`, `make build`) instead of raw commands when possible.

4. **Skeleton-first.**  
   Build an end-to-end “walking skeleton” (wiring + interfaces + smoke test) early, then fill in real behavior.

5. **Small, reviewable PRs.**  
   Prefer multiple small PRs that keep `main` green over one big bang.

6. **Stop after opening a PR.**  
   After creating a PR, switch to **review-support mode**. Do not start new feature work until a human responds. This is mandatory.

7. **No secrets.**  
   Never add tokens, passwords, API keys, private URLs, or customer/user data to code, logs, screenshots, fixtures, or docs.

8. **Prefer boring, maintainable choices.**  
   In greenfield work, novelty compounds. Choose simple, well-maintained dependencies and patterns unless there’s a clear reason not to.

9. **Keep a single source of truth for “what’s next.”**  
   `docs/agents/status.md` is the driver. Update it whenever direction or progress changes.

10. **Treat protocol adherence as required work.**  
    Do not improvise around this file. If instructions conflict or are unclear, pause and ask the SWE before proceeding.

## What you must read at session start

When a new session begins, read **all** of the following before proposing changes:

1. `AGENTS.md` (this file)
2. `README.md` (how to run, test, and contribute)
3. `docs/agents/status.md` (current state and next steps)
4. `docs/agents/design.md` (project purpose + architecture + phased plan)
5. The **current phase plan** (any `docs/agents/phase_*.md` that `status.md` points to)
6. `docs/agents/standards.md` and `docs/agents/stack.md` (if present)
7. `docs/agents/decisions.md` (if present)

If any of these are missing, **create minimal versions in a docs-only PR** (see “Plan PR” below).

## Source of truth hierarchy

When information conflicts, prefer in this order:

1. `docs/agents/status.md` (what we’re doing next and why, right now)
2. `docs/agents/design.md` (overall product + architecture truth)
3. The current `docs/agents/phase_*.md` plan (next slice details)
4. `docs/agents/standards.md` (coding standards and principles, stack-specific)
5. `docs/agents/stack.md` (technology choices)
6. GitHub Issues / Discussions / PR descriptions
7. Everything else

**Hard rule:** Call out contradictions rather than silently choosing.

## Directory & artifact conventions

### The minimum required docs

The agent docs should have this file structure:

```
docs/agents/
  design.md
  status.md
  stack.md        (recommended)
  standards.md    (recommended)
  decisions.md    (optional, recommended once tradeoffs exist)
  phase_1_*.md    (optional; add when work becomes multi-step)
  phase_2_*.md    (optional)
```

If the repo already has a different docs structure, follow it, but keep the **same intent**:
- one doc for **design**
- one doc for **status/next steps**
- one doc for **stack choices**
- one doc for **style principles**

### `docs/agents/design.md` (project truth)

Must include (keep it short; expand only as needed):
- Purpose and target user(s)
- Key user stories (3–7 is plenty)
- In-scope and out-of-scope
- High-level architecture (include a Mermaid diagram if relevant)
- Data model & major flows (as applicable)
- Interfaces: API endpoints, CLI commands, UI routes, events/messages (as applicable)
- Non-functional requirements: auth, privacy, performance, observability (only include if applicable)
- A **high-level phased plan**:
  - MVP / V1 build-out phases
  - Planned V2+ expansion phases

### `docs/agents/status.md` (the driver)

`status.md` is the best “what’s next?” source. It must contain:
- **Last updated date**
- **Commit hash** of `main` at time of update
- Current milestone/phase and objective (1–2 sentences)
- A short checklist of next steps (each step ideally PR-sized), with links to PRs/issues
- Blockers/questions (if any)

Update `status.md` whenever you:
- complete a meaningful step
- open/merge a PR that changes behavior
- discover a blocker
- change direction

### `docs/agents/phase_*.md` (mini design docs)

Create a phase plan when a milestone needs multiple PRs or coordination.

Each phase plan should include:
- Goals / non-goals
- Acceptance criteria
- Components/modules involved
- Public interfaces affected
- Testing strategy (unit/integration/e2e smoke)
- Rollout notes (if any)
- Step breakdown (PR-sized), with step numbers that can be referenced from `status.md`

### `docs/agents/decisions.md` (optional, recommended)

Use this to record important tradeoffs (short ADR-style notes):
- Context
- Decision
- Alternatives considered
- Consequences

## Branching, commits, and PRs

### Default branching model: GitHub Flow

- Long-lived branch: `main`
- Never commit directly to `main`
- Everything goes through PRs

Branch name prefixes:
- `feature/<slug>` — product work
- `bugfix/<slug>` — bug fixes
- `spike/<slug>` — exploratory throwaway work
- `docs/<slug>` — documentation-only changes
- `chore/<slug>` — tooling/CI/refactors with no product behavior changes

### Stacked PRs

Stacking changes how branches relate to each other, not what they are called. A stack uses the same branch names as any other work, one branch per stack entry, each parented to the previous one.

This file is authoritative for branch names, commit messages, and PR titles. A tooling skill, plugin, or agent that proposes a different format does not override it. If a tool refuses to work under these names, stop and ask the SWE rather than renaming.

### Commit messages & PR titles

Use **Conventional Commits**:
```
<type>(optional-scope): <description>
```

Examples:
- `feat(api): add create-project endpoint`
- `fix(ui): prevent crash on empty state`
- `chore(ci): add basic test workflow`
- `docs: document local run commands`

PR titles use the same Conventional Commit format as commit messages.

If the repository tracks work in an external tracker, prefix the title with the bracketed
work item ID: `[<TRACKER-ID>] <type>(optional-scope): <description>`. Without an external
tracker, omit the prefix.

### PR description must include

- What changed and why (link to `docs/agents/design.md` or a phase plan)
- How to test (exact commands)
- Risks / limitations / follow-ups
- Any new configuration (env vars; update `.env.example` if applicable)
- UI changes: screenshots directly in PR Description (not only comments) when applicable
- Repository PR template usage (for example `.github/PULL_REQUEST_TEMPLATE/...`) when available
- Multiline bodies provided via newline-safe methods (`--body-file` / heredoc), never escaped `\\n` literals

### “Stop after PR” rule

After opening a PR:
- provide a brief PR summary + test commands
- respond to review feedback
- **do not** start new feature work until the SWE instructs you to do so

## Session algorithm (do this every session)

This is the default “what should I do now?” algorithm for an agent session.

### 0) Establish the session intent

Determine which of these applies (prefer explicit instructions from the SWE):
- **A. Planned work**: implement the next step already described in `status.md` / current phase doc.
- **B. New feature**: the SWE requests a feature not currently described in `design.md` or phase plans.
- **C. Bugfix**: the SWE requests a bug fix (via issue link or interactive reproduction).

If unsure, default to **A** by reading `status.md` and picking the next unchecked step.

### 1) Sync and sanity-check the repo state

Before making changes:
- Ensure you’re on a clean working tree (no uncommitted changes).
- Pull latest `main`.
- Check for open PRs you previously opened; if present, default to **review-support mode**.

### 2) Read the docs (session startup checklist)

Read the required docs listed above. If missing:
- Create a **docs-only Plan PR** that adds minimal versions, then **stop**.

### 3) Choose the correct flow

- If **A (Planned work)**: follow “Flow A — Implement the next planned step”.
- If **B (New feature)**: follow “Flow B — Add an unplanned feature”.
- If **C (Bugfix)**: follow “Flow C — Fix a bug”.
- If you open a PR at any point: immediately switch to “Flow D — Review-support mode”.

## Flow A — Implement the next planned step (most common)

This is the default in greenfield projects: complete MVP/V1, then expand with planned V2 features.

1. In `docs/agents/status.md`, locate:
   - current phase
   - the next incomplete step (prefer the first unchecked item)
   - any referenced `docs/agents/phase_*.md` section/step number
2. Read the relevant phase doc section for that step:
   - acceptance criteria
   - interfaces and constraints
   - testing expectations
3. Create a branch:
   - `feature/<phase-slug>-step-<N>` (or `bugfix/...` if the step is explicitly a bugfix)
4. Implement the step with tests:
   - Write/extend tests first where practical (TDD for business logic)
   - Add/extend integration tests at trust boundaries
   - Keep changes narrowly scoped to the step
5. Update `docs/agents/status.md`:
   - mark the step complete
   - link the PR
   - record tests run (exact commands)
   - note any follow-ups / discovered work as new checklist items or issues
6. Open a PR and **stop**.

## Flow B — Add an unplanned feature (SWE request / user feedback)

Sometimes the SWE (or users) request features not anticipated in the original plan.

### B0) Triage size and documentation impact

Classify the request:

- **Small (single PR)**: can be implemented end-to-end in one PR without major architecture changes.
- **Medium (1–3 PRs)**: requires a few steps but still a bounded effort.
- **Large (new phase)**: requires multiple PRs, introduces new components, or changes architecture/interfaces meaningfully.

### B1) If Large (new phase): create a phase plan first (docs-only PR) and stop

1. Update `docs/agents/design.md` to mention the new feature at the right level:
   - add to phased plan (e.g., “V2 / Phase X”)
   - update architecture/interface sections if needed
2. Create a new phase plan doc:
   - `docs/agents/phase_<N>_<slug>.md`
   - include goals, acceptance criteria, interfaces, and **step breakdown**
3. Update `docs/agents/status.md`:
   - set current phase to the new phase (or note it is “up next”)
   - add the step checklist with references to the phase doc
4. Open a **docs-only Plan PR** and **stop**.

After the plan is approved, proceed via **Flow A** for each step.

### B2) If Medium: decide whether to create a phase plan

Default behavior:
- If it’s clearly multi-step (2–3 PRs), create a short phase plan (like B1).
- If it’s borderline, you may proceed in one PR but must keep it tight.

At minimum:
- Update `docs/agents/status.md` with a checklist for the work.
- If it meaningfully changes product scope or architecture, also update `docs/agents/design.md`.

### B3) If Small (single PR): implement + record

1. Create a `feature/<slug>` branch.
2. Implement with tests (include at least one regression/smoke path if applicable).
3. Update `docs/agents/status.md`:
   - record what was added and why
   - link the PR
   - record tests run
4. If non-trivial, also update `docs/agents/design.md` (e.g., new capability, endpoint, UI flow).
5. Open PR and **stop**.

## Flow C — Fix a bug (issue-driven or interactive)

Bugfixes should be fast, safe, and regression-tested.

1. Identify the bug source:
   - Link to GH/JIRA issue if available, or write a short problem statement in the PR description.
2. Reproduce the bug:
   - Capture exact repro steps and expected vs actual behavior.
   - If possible, add a failing test that demonstrates the bug.
3. Create a branch:
   - `bugfix/<slug>`
4. Fix the bug with minimal change:
   - Prefer the smallest correct fix
   - Avoid refactors unless necessary
5. Add/keep a regression test:
   - Unit test preferred; integration/e2e if bug spans boundaries
6. Update `docs/agents/status.md`:
   - link the issue and PR
   - record repro steps and tests run (exact commands)
7. Open PR and **stop**.

If the bug reveals a gap in intended behavior, update `docs/agents/design.md` or the relevant phase doc to clarify.

## Flow D — Review-support mode (after any PR)

After opening a PR, do not start new work unless instructed.

1. Re-read PR comments carefully.
2. Make minimal, targeted changes that address the feedback.
3. Update `docs/agents/status.md` **only** if the plan/steps materially changed.
4. Push updates and leave a concise PR comment summarizing what changed.
5. **Stop**.

## Spikes (optional, encouraged when uncertain)

Use spikes to test assumptions quickly (libraries, architecture, performance, feasibility).

Rules:
- Branch prefix: `spike/`
- Timebox the scope: answer 1–3 questions, not “build the feature”
- Record findings in `docs/agents/decisions.md` (or the relevant phase plan)
- Do **not** merge spike code into `main` as-is  
  - Either delete it, or re-implement cleanly on a `feature/` branch

If a spike introduces a dependency, justify it in docs and add a minimal “hello world” usage + test.

## Plan PR (docs-only) rules

A Plan PR is required when:
- `docs/agents/` files are missing
- a **new phase** is needed (large unplanned feature)
- architecture/interfaces are changing materially

Plan PR guidelines:
- No production code.
- Use diagrams, schemas, payload shapes, signatures, and step checklists.
- Ensure `status.md` clearly states what’s next and links to the plan.

## Testing & quality bar (greenfield-friendly)

- Prefer a testing pyramid: **unit > integration > e2e smoke**.
- Mock at **trust boundaries** (DB, network, external APIs), not internal helpers.
- Keep at least one **fast** test command that runs locally in under a minute when possible.
- Keep `main` green: if CI is red, prioritize fixing it.

**Failure rule:** if the same test failure happens **3 times** after attempted fixes, stop and ask for human help. Document what you tried in `docs/agents/status.md`.

## Safety, security, and configuration

- Never commit secrets. Use environment variables and keep a checked-in `.env.example`.
- Do not log sensitive user data. Sanitize at trust boundaries.
- Avoid adding heavy dependencies without a clear win. Prefer well-maintained libraries.
- If you touch auth, permissions, encryption, payment flows, or multi-tenant isolation: **stop and ask** before proceeding.

## Documentation conventions

- Design specs live in `docs/specs/` with the naming pattern `YYYY-MM-DD-<topic>-design.md`
- Implementation plans live in `docs/plans/` with the naming pattern `YYYY-MM-DD-<topic>.md`
- When using brainstorming or planning skills that default to other locations (e.g., `docs/superpowers/specs/`), override the default and write to the project-standard locations above

## Final reminder

**Write it down. Build a skeleton. Ship in small slices. Stop after PRs. Keep `status.md` current.**
