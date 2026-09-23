---
description: Restart Claude in herdr panes so they pick up new permissions and hooks, keeping each session's name
argument-hint: pane ids or names, space separated; empty restarts every peer pane but this one
allowed-tools: ["Bash", "ListAgents", "AskUserQuestion"]
---

# Restart agent panes

A permission rule and a hook are read once, when a session starts. A session that has been
running since before they changed still holds the old ones, and only a restart replaces them.
An instructions file is different: it is reinjected each turn, so a rule written there is
already live everywhere and is not a reason to restart.

Restarting through `herdr` loses the session name unless the name is passed to the binary. The
procedure below keeps it. Every step was measured on 2026-09-22; the failures it avoids are
recorded with it.

## What the name is, and why two records disagree

`herdr` keeps a name per pane. Claude Code registers its own session name, which is what
`ListAgents` reports and what `SendMessage` addresses. They are separate records.

`claude -n <name>` sets the Claude side and the terminal title together. `herdr agent rename`
sets the `herdr` side alone: run by itself after a restart, the pane reads correct in
`herdr agent list` while peers still see a generated name such as `dotfiles-a2`. Both records
have to be written, which is why the procedure has a rename step even though `-n` is passed.

Without `-n`, Claude builds its own name from the basename of the working directory plus a
suffix: two panes under `~/dotfiles` restarted without it on 2026-09-22 came back as
`dotfiles-9e` and `dotfiles-a2`, and two panes under separate work directories each took their
own basename. The generated name never agrees with the `herdr` record because it never reads it.

## Procedure

Per pane, in order. The target of each command is the pane id, which never changes.

1. **Read the pane before touching it.** `herdr agent read <pane>` shows an open approval
   dialog or half-typed text. Keys sent into either land in that context instead of the one
   expected, so a pane that is not at a clean prompt is reported and skipped.

2. **Ask the session what it loses.** A message asking for uncommitted work, anything running,
   and one line on what to resume. Its context dies with the process, so what is not written to
   disk is gone. A session that does not answer is reported to the user, who decides.

   A message to a session reported as `working` is queued and delivered when its turn ends, so
   the question costs nothing but the wait. The turn is never interrupted.

3. **Wait for it to settle.** `herdr agent wait <pane> --until idle --timeout <ms>`. An exit
   sent mid-turn discards what the turn was producing, including the answer to step 2. Every
   wait carries a timeout: without one it is indefinite, and a session that never settles holds
   the whole restart open. A pane that times out is reported and left running.

4. **Exit.** `herdr agent prompt <pane> "/exit"`.

   `herdr agent send-keys <pane> ctrl+d` does not close it. Measured: the call returns `ok` and
   the agent stays alive.

5. **Wait for the pane to free.** `herdr agent list` until the `pane_id` is gone from it. The
   exit is not immediate, and `agent start` on a pane still closing fails with
   `agent_pane_busy: is not an available shell`.

   `herdr agent read` does not answer this. In that interval it returns the shell prompt with
   Claude's status bar still drawn, so a pane that has already exited reads as alive. The
   disappearance from `agent list` is the signal.

6. **Start with the name and the permission mode.**
   `herdr agent start <temp> --kind claude --pane <pane> -- -n <name>
   --dangerously-skip-permissions`.

   The permission mode is set at launch and is not stored in settings, so a restart without the
   flag silently changes it. A pane in the default mode holds messages from other sessions for
   the user to approve, and they expire unanswered: measured on 2026-09-22, right after four
   panes were restarted without it, three peer messages were lost, one refused and two expired.
   The hooks still run, since a hook decides on its own rather than through the permission layer.

   Everything after `--` goes to the `claude` binary, and `-n <name>` is what survives into
   `ListAgents`. `<temp>` names the `herdr` record and must differ from `<name>`: the dead
   agent's name is still reserved, so reusing the real one fails with `agent_name_taken`. Step 5
   waits for the pane to leave `agent list` and this reserves the name past that point, which is
   why both are needed. A pane id is not a legal value either: a name starts with a lowercase
   letter and carries lowercase letters, digits, `-` or `_`.

7. **Sync the `herdr` record.** `herdr agent rename <pane> <name>`.

8. **Verify in `ListAgents`, never in `herdr agent list`.** The second reads the `herdr` record,
   which step 7 just wrote and which tells nothing about what peers see. Only `ListAgents`
   answers whether the session can be addressed by name.

A pane that came back under a generated name is repaired by running the procedure again over it,
at no cost beyond the restart: the `/exit` reaches whichever agent is running in the pane, which
is the one to close.

## Scope

An agent restarts the panes of its own workspace, which is the one in `$HERDR_WORKSPACE_ID`.
`herdr agent list` carries every pane of every workspace and the `workspace_id` of each, so the
set to restart is the panes matching that variable. A pane outside it is delegated by message to
an agent running there rather than restarted from here: the agent coordinating a workspace is
the one started first in it, and it is the one that knows what its panes are holding.

The variable is read rather than the focused workspace assumed. `herdr pane layout` without a
target returns the layout of whichever workspace the user is looking at, and a command that
reads focus acts on panes belonging to someone else.

This session never restarts itself: the process running the command is the one that would die.
The user restarts it, or it is left running and reported.

## Reporting

Per pane: its name, whether it answered step 2, and the name `ListAgents` reports at the end. A
pane skipped at step 1 is named with what was on screen. A pane whose name did not survive is
named with the generated one peers now have to use.
