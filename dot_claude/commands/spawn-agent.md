---
description: Open a Claude pane in the current workspace, split so the first pane stays widest, carrying its identity from the environment
argument-hint: agent name, optionally a path to work in
allowed-tools: ["Bash", "ListAgents", "AskUserQuestion"]
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
   -n <name>`.

   The `-n` is what `ListAgents` reports and what `SendMessage` addresses. Without it Claude
   builds a name from the basename of the working directory and peers cannot address the pane by
   the name intended for it. `/restart-agents` carries the same rule and the failures behind it.

4. **Verify in `ListAgents`.** `herdr agent list` reads herdr's own record and says nothing
   about what peers see.

## Environment

Set at split time, so the pane carries them before its first turn.

| Variable | Value | Why it cannot be derived later |
|---|---|---|
| `HERDR_AGENT_NAME` | the name passed to `-n` | herdr holds a name per pane and Claude registers its own; a pane reading only one of them can disagree with what peers address |
| `HERDR_AGENT_ROOT` | the working directory | `cwd` moves as the session works, and the directory it was spawned for does not |

`HERDR_PANE_ID`, `HERDR_TAB_ID` and `HERDR_WORKSPACE_ID` arrive without being set. A pane reads
its own `HERDR_PANE_ID` and finds its record in `herdr agent list`, which carries the workspace,
the working directory and the name herdr knows.

Verified on 2026-09-22, splitting the bottom pane of a three-pane workspace: the first pane kept
its width of 128 columns while the bottom one went from 28 rows to two of 14, and the new pane
read back all four variables, the two set here and the two herdr supplies.

Reading a pane immediately after `herdr pane run` can return the prompt before the output. The
read is repeated rather than believed the first time.

## Scope

The pane opens in the current workspace. A pane for another workspace is asked for by message to
an agent already running there, which is where `/restart-agents` draws the same line: the agent
coordinating a workspace is the one started first in it.

No name is reused. `herdr agent start` fails with `agent_name_taken` while herdr still holds a
record under that name, including one whose agent has exited.
