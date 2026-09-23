---
description: Open a Claude pane in the current workspace, split so the first pane stays widest, carrying its identity from the environment
argument-hint: agent name, optionally a path to work in
allowed-tools: ["Bash", "Skill", "ListAgents", "AskUserQuestion"]
---

# Spawn an agent pane

A pane opened by hand has to be told what it is afterwards, and a session restarted later comes
back under a generated name. Both are cases of the same thing: identity written after the fact
instead of carried from the start.

`herdr pane split --env` sets variables on the launched process, and `HERDR_PANE_ID` arrives on
its own. A pane can therefore know its own name, its workspace and its working directory before
its first turn, without anyone writing them down.

## Layout

The first pane of a workspace stays widest and is never split again: it is the one holding the
conversation, and a column that keeps shrinking is unreadable. Every later pane splits the
bottom of the right column.

| Panes after | Split |
|---|---|
| 2 | `--direction right --ratio 0.59` on the first pane |
| 3 or more | `--direction down --ratio 0.5` on the bottom pane of the right column |

`herdr pane layout` gives every pane's rectangle. The right column is the set of panes whose `x`
is greater than the first pane's, and its bottom pane is the one with the largest `y` among
them. One pane means the second rule has nothing to read, which is why the first row exists.

A ratio of 0.59 on the first split is what the hand-built layout measured, leaving the first
pane about three fifths of the width.

## Procedure

1. **Read the layout of this session's own workspace.**
   `herdr pane layout --pane "$HERDR_PANE_ID"` gives the pane count, each rectangle and the
   `workspace_id`. The pane to split and the direction follow from the table above.

   The `--pane` is what makes the read correct. Without it `herdr pane layout` returns the
   layout of the *focused* workspace, which is whichever one the user is looking at and not the
   one the calling session lives in. Measured on 2026-09-22: a session in one workspace read
   back the three panes of another. A spawn computed from that layout opens in the wrong
   workspace or fails.

   An empty `HERDR_PANE_ID` means the session is not running in a herdr pane at all, and there
   is no workspace to spawn into: the command stops and says so.

2. **Split.** `herdr pane split <target> --direction <dir> --ratio <r> --cwd <path> --no-focus`
   plus one `--env` per variable below. `--no-focus` keeps the conversation where it is; a
   spawn that steals focus interrupts the person who asked for it.

   `<target>` is always written out. The pane argument is optional and a split without it falls
   back to the focused pane, which carries the same defect as step 1: the focused pane can sit
   in another workspace.

   Without `--cwd` the new pane inherits the current working directory, which is right when the
   agent works the same repository and wrong otherwise.

3. **Start Claude with its name.** `herdr agent start <name> --kind claude --pane <pane> --
   -n <name> --dangerously-skip-permissions`.

   The permission mode is set at launch and is not stored in settings, so a pane started without
   the flag comes up asking. What it asks about includes messages from other sessions: a pane in
   the default mode holds them for the user to approve, and they expire unanswered. Measured on
   2026-09-22, after four panes were restarted without it: three peer messages were lost, one
   refused and two expired. The hooks still run in this mode, since a hook decides on its own
   rather than through the permission layer.

   The `-n` is what `ListAgents` reports and what `SendMessage` addresses. Without it Claude
   builds a name from the basename of the working directory and peers cannot address the pane by
   the name intended for it. `/restart-agents` carries the same rule and the failures behind it.

4. **Record the pair outside the process.**
   `python3 ${CLAUDE_PLUGIN_ROOT}/hooks/roster.py --write <pane> <name> <master>`.

   The `--env` of step 2 lives in the pane's process, and a restart replaces that process:
   `herdr agent start` takes no `--env` and creates no pane. Measured on 2026-09-23, two panes
   restarted with their threads intact came back with both variables empty, and a slave read as
   a master. The roster survives that, and a session with an empty variable reads its own pane
   there before concluding it coordinates itself.

5. **Label the pane.** `herdr pane rename <pane> <name>`, with the same name passed to `-n`.

   A pane with no label shows as a number in the sidebar, and so does a tab: measured on
   2026-09-23, three tabs carried `label` equal to their index and two panes carried none. A
   workspace of numbered panes cannot be read at a glance, and `/shephrd` offers stored panes by
   their label when it restores a workspace, so an unlabelled pane comes back identified only by
   its directory.

   This is a third name record, beside the two `/restart-agents` describes. It feeds the
   sidebar and `~/.config/herdr/session.json`; it is not what `SendMessage` addresses.

6. **Name the tab if it has none.** `herdr tab list` shows a `label` per tab, and a tab whose
   label is its own number was never named. `herdr tab rename <tab> <name>` takes the tree the
   workspace works on, which is the name the user reads in the sidebar.

   Only when it has none. A tab already named belongs to the workspace rather than to this
   spawn, and renaming it on every spawn would rename it after whichever agent opened last.

7. **Verify in `ListAgents`.** `herdr agent list` reads herdr's own record and says nothing
   about what peers see.

## Environment

Set at split time with one `--env` each, so the pane carries them before its first turn:
`HERDR_AGENT_NAME`, `HERDR_AGENT_ROOT` and `HERDR_AGENT_MASTER`.

`HERDR_AGENT_MASTER` takes this session's own name, which is what makes the spawned pane know who
to report to. Read it from `HERDR_AGENT_NAME`, and from this session's entry in `ListAgents` when
that is empty, which is the case for any pane opened by hand rather than by this command. A spawn
that can resolve neither stops rather than opening a pane answering to nobody.

Setting it is also what puts the pane in unattended mode, with no command sent to it. The pane has
nobody watching it from the moment it opens, so it asks this session rather than the user for
every decision from its first turn; `shephrd-protocol` is where that follows from the variable.

`shephrd-protocol` holds what each variable means and the measurements behind them, in
`references/environment.md`.

## Scope

The pane opens in the current workspace. A pane for another workspace is asked for by message to
an agent already running there.

No name is reused. `herdr agent start` fails with `agent_name_taken` while herdr still holds a
record under that name, including one whose agent has exited.
