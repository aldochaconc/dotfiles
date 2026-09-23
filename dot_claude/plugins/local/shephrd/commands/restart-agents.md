---
description: Restart Claude in panes so they pick up new permissions and hooks, keeping each session's name
argument-hint: pane ids or names, space separated; empty restarts every peer pane but this one
allowed-tools: ["Bash", "Skill", "ListAgents", "AskUserQuestion"]
---

# Restart agent panes

A permission rule and a hook are read once, when a session starts. A session running since before
they changed still holds the old ones, and only a restart replaces them. An instructions file is
different: it is reinjected each turn, so a rule written there is already live everywhere and is
not a reason to restart.

Restarting loses the session name unless the name is passed to the binary. Load
`shephrd-protocol` and read `references/herdr-cli.md` before starting: it holds why two name
records disagree, why an exit is not immediate, and which flag a restart must not drop.

## Procedure

Per pane, in order. The target of each command is the pane id, which never changes.

1. **Read the pane before touching it.** `herdr agent read <pane>` shows an open approval dialog
   or half-typed text. Keys sent into either land in that context instead of the one expected, so
   a pane that is not at a clean prompt is reported and skipped.

2. **Ask the session what it loses.** A message asking for uncommitted work, anything running,
   and one line on what to resume. Its context dies with the process, so what is not written to
   disk is gone. A session that does not answer is reported to the user, who decides.

3. **Wait for it to settle.** `herdr agent wait <pane> --until idle --timeout <ms>`. An exit sent
   mid-turn discards what the turn was producing, including the answer to step 2. The timeout is
   required here: without one a session that never settles holds the whole restart open. A pane
   that times out is reported and left running.

4. **Exit.** `herdr agent prompt <pane> "/exit"`.

5. **Wait for the pane to free.** `herdr agent list` until the `pane_id` is gone from it.

6. **Start with the name and the permission mode.**
   `herdr agent start <temp> --kind claude --pane <pane> -- -n <name>
   --dangerously-skip-permissions`.

   `<temp>` names the herdr record and must differ from `<name>`, since the dead agent's name is
   still reserved. Dropping the permission flag silently changes the mode and costs the pane its
   peer messages; `references/herdr-cli.md` carries what that measured.

7. **Sync the herdr record.** `herdr agent rename <pane> <name>`.

8. **Verify in `ListAgents`, never in `herdr agent list`.** The second reads the record step 7
   just wrote, which tells nothing about what peers see.

A pane that came back under a generated name is repaired by running the procedure again over it:
the `/exit` reaches whichever agent is running in the pane, which is the one to close.

## Scope

An agent restarts the panes of its own workspace, read from `$HERDR_WORKSPACE_ID` rather than
from what is focused. A pane outside it is delegated by message to an agent running there.

This session never restarts itself: the process running the command is the one that would die.

## Reporting

Per pane: its name, whether it answered step 2, and the name `ListAgents` reports at the end. A
pane skipped at step 1 is named with what was on screen. A pane whose name did not survive is
named with the generated one peers now have to use.
