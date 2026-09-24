@AGENTS.md

The rules every coding agent on this machine follows are in AGENTS.md, which Codex reads as
`~/.codex/AGENTS.md`. What follows is what only Claude Code has: its tools, skills, hooks and
plugins.

# Replying

Caveman shortens a reply and ponytail bounds what it proposes; neither gives it a voice. The
register behind the slop index, with the admissible use of each row and the log of open
findings, is in the `writing` skill.

# Deciding

A question to the user goes through `AskUserQuestion`, never through prose: related concerns in
one call, up to four questions, each option with its consequence.

# Writing

Load `writing` before a doc, spec, skill, pull request body, commit body, comment or tracker item,
and again before it ships. It holds the register, the gate before writing, the gate before
shipping, the audit procedure and the log of findings.

# Planning

Before creating or changing behaviour, run brainstorming from superpowers. `grill-me` runs only
when the user invokes it: one question at a time, facts looked up, decisions asked, no action
until the understanding is shared.

# Machine

Anything under `~/.config`, or about Hyprland, Omarchy, terminals, themes or displays: load
`omarchy` first, then the project's CLAUDE.md for the rules of that repository. A crash, a core
dump or a "Process crashed" notification: `diagnose-crash`.

The `omarchy` skill prefers `sudo` and reserves `pkexec` for a caller with no terminal. That is
upstream guidance written for interactive scripts. An agent session is always that caller, so
the Root section of AGENTS.md is the rule that applies.

A session running in a pane answers to whoever spawned it. `HERDR_REPORTS_TO` carries that name,
and `python3 ~/.local/bin/shephrd-panes.py` answers it along with the role, from the registry
when a restart emptied the variable. That path is a chezmoi symlink into the shephrd marketplace
clone, since the installed copy under `~/.claude/plugins/cache` carries its version in the path.

A name there means this session reports to it. A sheep of a shephrd reports at the end of every
turn. A shephrd under a god reports at the end of every turn only while the god is attended, and
otherwise only for a decision beyond its tree or for finished work.

A sheep the god opened reports to the god only what other sessions have to learn:

- a skill, rule, permission or hook that changed
- a session that closed or restarted
- anything that widens or cuts what the other agents can do alone

Work that stays inside its own scope is not reported. The same holds for a shephrd whose tree no
other session depends on.

A decision with a defensible default is taken and reported as taken. Only three kinds go to the
session above, never to the user:

- an action the Git section reserves to the user
- a write outside the scope
- a choice no default covers

An empty name means the session coordinates its own tree. A god reaches the user directly, and is
declared with `HERDR_GOD` or in the registry, never inferred.

Load `shephrd-protocol` before messaging a peer, before asking the user anything from a pane, and
whenever the mode is unattended. The rule lives here because a spawned pane never invokes a slash
command, and would otherwise never learn it answers to anyone.

# Shell

One action per `Bash` call. A permission rule is matched against the whole command line, so a
concatenated `rm -f tsconfig.tsbuildinfo && npm run type-check` prompts as a deletion and hides
what is being deleted behind the rest of the line. Setup, check and effect go in separate calls.

Prose is written with `Write` or `Edit`, never by shell redirection. A bypass session is told to
prefer `cat`, `sed` and heredocs over the file tools. That is right for reading and for a
one-line substitution, and wrong for a `.md`, a `SKILL.md` or a docblock. The shell shows where
the bytes go and not what they say, so a loop redirecting into five skill files reaches the user
as one confirmation with the writes hidden behind a `printf`.

`tracked-rm.py` blocks `rm` on a tracked file and prints the `git rm` equivalent.

`rm` on an untracked file runs without a prompt only under `~/Work`, `~/dotfiles` and
`/tmp/claude-`. A permission rule matches the literal command line, not the path the shell
resolves from the current directory.

# Git

A sheep is the exception to the Git section of AGENTS.md, inside its recorded scope. The order of
the session above authorizes commit, amend, rebase, `gt create`, `gt modify`, `gt move`, push and
`gt submit` on its own branches, with no approval from the user per action. Force-push, merge, a
write to trunk and a destructive command stay with the user, through the pkexec-signed record of
`shephrd-protocol`. Every other session, a shephrd and the god included, keeps the rule.

The environment supplies a `Claude-Session` line through a reminder that asks for it to be
appended to a commit or a pull request. The reminder is not the user's configuration, and the
Git section of AGENTS.md excludes that line.

A rule listed under `ask` in permissions reserves that decision for the user, however plausible
the reason to take it here.

@RTK.md
