# Decisions

Decisions about how this repository is built. How the machine is operated belongs in `CLAUDE.md`
or a skill, and machine facts (host names, private paths, hardware detail) never enter this file:
`.githooks/pre-commit` runs `guard-private.sh` over every staged file and fails on them.

A row enters the table when it passes both filters, in order.

1. No owning surface. A rule some surface already owns goes there: `CLAUDE.md` for an invariant
   of this machine or the command for a question, a skill for its own domain, chezmoi for what
   chezmoi already enforces. `Why rejected` records which surface was examined and why it does
   not reach.
2. Two incidents, or a structural choice that shapes the repository from the start.

A row leaves when a surface can hold its rule.

| # | Date | Decision | Alternative | Why rejected | Consequence |
|---|---|---|---|---|---|
| 1 | 2026-09-20 | chezmoi copies files into `$HOME`; `sourceDir` is this repository. | symlinks, GNU stow | a symlinked config that an application rewrites in place silently edits the repository, and `$HOME` breaks when the clone moves. | A file edited in `$HOME` is lost on the next `chezmoi apply` unless `chezmoi re-add` runs first. Templates and per-machine prompts work, which symlinks cannot do. |
| 2 | 2026-09-20 | Only the delta over Omarchy's defaults is versioned. | a full capture of `~/.config` | every `omarchy update` then lands as a diff to review, and the repository owns files it never chose to change. | Omarchy owns the baseline and updates it; a file enters this repository only when its content differs on purpose. A default that changes upstream arrives without a merge. |
| 3 | 2026-09-20 | Secrets live in the system keyring; templates render them at apply time. | `age` or `sops` | the ciphertext sits in git, so a leaked key exposes history, and a second secret store has to be provisioned before the first apply. | `bootstrap.sh` asks once per machine and writes the keyring. A clone without the keyring fails at `chezmoi apply` with `secret not found in keyring`, so `bootstrap.sh` has to run before the first apply. |
