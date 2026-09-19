# Customization Guide

This guide explains how to adapt the agent scaffolding in `docs/agents/` to this repo.

## Incorporate existing standards
- If the repo already has standards, link to them from `docs/agents/standards.md` instead of duplicating.
- Keep the doc short: capture only decisions that agents must follow (versions, commands, conventions).
- Prefer links to canonical sources (CONTRIBUTING.md, wiki) over copy/paste.

## Decision logging guidance
- Keep high-impact decisions in `docs/agents/decisions.md` as short ADR-style entries.
- Prefer one decision per entry with explicit context, decision, consequences, and alternatives considered.
- If an ADR location already exists, link from `docs/agents/decisions.md` rather than duplicating records.

## Testing guidance
- If testing is documented elsewhere, add a short summary in `docs/agents/testing.md` with links.
- Include at least one fast command and one full/CI-equivalent command.
- Note required test data, services, or environment variables.

## Branching conventions

Branch prefixes are defined in `AGENTS.md` and that file is authoritative. Keep any
tooling configuration consistent with it rather than the other way around:

```
feature/<slug>    product work
bugfix/<slug>     bug fixes
spike/<slug>      exploratory throwaway work
docs/<slug>       documentation-only changes
chore/<slug>      tooling/CI/refactors, no product behavior change
```

## Maintainability tips
- Avoid conflicting instructions across `README.md`, `AGENTS.md` and `docs/agents/*`.
- Keep `docs/agents/status.md` current; it is the single source of "what's next".
- `AGENTS.md` and `CLAUDE.md` hold the same content; change both together.

## Common pitfalls
- Adding broad `.gitignore` rules that hide scaffolding files.
- Editing docs without recording intent in `docs/agents/decisions.md`.
