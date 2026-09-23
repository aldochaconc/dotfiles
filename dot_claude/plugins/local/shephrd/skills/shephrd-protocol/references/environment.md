# Pane environment

A pane carries six variables. Two groups, by who writes them.

## Set by the spawn commands

`/spawn-sheep`, `/spawn-shephrd` and `/spawn-watcher` pass them as `--env` at split time, through
`commands/spawning.md`, so the pane holds them before its first turn.

| Variable | Value | Why it cannot be derived later |
|---|---|---|
| `HERDR_AGENT_NAME` | the name passed to `-n` | herdr holds a name per pane and Claude registers its own; a pane reading only one of them can disagree with what peers address |
| `HERDR_AGENT_ROOT` | the directory the pane was opened for | `cwd` moves as the session works, and the directory it was spawned for does not |
| `HERDR_REPORTS_TO` | the name of the session that spawned it | nothing in `herdr agent list` records who a pane answers to |
| `CLAUDE_UNATTENDED` | `1` on a sheep and a watcher, unset on a shephrd and a god | a hook runs outside the session and cannot read the registry's role |

`herdr agent list` carries a `workspace_id` per pane and no field naming a god or shephrd: measured on
across six agents in three workspaces. Deriving the session above from the workspace fails on
the same reading, where one workspace's first pane carried no `name` at all and another pane's
registered name disagreed with the title its terminal still displayed.

## Supplied by herdr

`HERDR_PANE_ID`, `HERDR_TAB_ID` and `HERDR_WORKSPACE_ID` arrive without being set. A pane reads
its own `HERDR_PANE_ID` and finds its record in `herdr agent list`, which carries the workspace,
the working directory and the name herdr knows.

Verified , splitting the bottom pane of a three-pane workspace: the first pane kept
its width of 128 columns while the bottom one went from 28 rows to two of 14, and the new pane
read back all five variables.

## Empty values

An empty `HERDR_PANE_ID` means the session is not running in a herdr pane at all. There is no
workspace to spawn into and no layout to read.

An empty `HERDR_AGENT_NAME` means the pane was opened by hand rather than by a spawn command.
Measured: the first pane of a workspace answered to the god's name in `ListAgents`
with `HERDR_AGENT_NAME` unset. A session spawning from there resolves its own name from
`ListAgents` instead, since passing the empty value through would tell every sheep it has nobody above it.

An empty `HERDR_REPORTS_TO` means the spawn did not set it or a restart cleared it, never that the
session coordinates itself. The registry answers the role, and a pane absent from it was opened by
hand or predates the registry, which is reported rather than read either way.

## CLAUDE_UNATTENDED

Read by `~/.claude/hooks/gate-skill-writes.py`, which asks the user before a write to a skill file
and denies it instead when this variable is non-empty. The denial carries what to do: record the
line and the surface it targets, and leave it for the human.

That is the route `skill-growth` already requires. Its gate states that a rule entering a skill is
never silent, that the line, the surface and the observation are stated before the write, and that
presenting is not permission. A sheep stating the rule and handing it up is complying with that
gate; a sheep raising a prompt in a pane nobody is watching is not.

So the variable changes the route and not what a sheep may contribute. A rule it finds still
reaches the skill, through the session above rather than through a menu.

It goes on a sheep and a watcher, which `/spawn-sheep` and `/spawn-watcher` open. A shephrd and a god reach
the user, so a prompt in their pane is answerable and the variable would deny a write the user
would have approved.

A hook runs outside the session, in its own process, reading the environment it was handed. It
cannot open the registry's role for the pane it is deciding about, which is why this is a variable
rather than a fifth field in the record. Measured: twelve prompts in one hour, every
one an `Edit` to a `SKILL.md`, raised in panes with nobody in front of them, with the variable
unset on every pane on the machine.

## HERDR_GOD

Set on the one session the user watches, and read by `panes.py` as the first of the two things
that decide a role. Any value other than empty, `0`, `false` or `no` means yes.

It is declared rather than inferred because the alternative fails at the moment it matters: a
shephrd that has opened no sheep yet is indistinguishable from a god, and the wrong reading
decides whether a question reaches the user at all.

Like the other variables it lives in the pane's process, so a restart empties it and the registry
answers instead. `panes.py --write <pane> <name> "" <scope> --role god --god` records it.

`--role` is what the resolver trusts, and the flag decides only where no role was recorded. The
two are written together for a god: the flag alone leaves the record on the derivation, which is
right for a god and wrong for the shephrd in the next row.

| Pane | Recorded with |
|---|---|
| god | `--write <pane> <name> "" <scope> --role god --god` |
| shephrd | `--write <pane> <name> <god-name> <scope> --role shephrd` |
| sheep | `--write <pane> <name> <shephrd-name> <scope> --role sheep` |
| watcher | `--write <pane> <name> <god-name> <scope> --role watcher` |

A shephrd reports to the god, so its recipient is not empty and the derivation reads it as a
sheep. Measured: pane `wA:p1` was recorded `shephrd` with the god above it,
and every reader that derived instead of reading called it a sheep. `--role` is the only thing
that separates the two, and a record written without it carries whatever the recipient implies.
