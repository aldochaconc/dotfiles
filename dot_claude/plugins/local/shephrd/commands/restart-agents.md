---
description: Restart Claude in panes so they pick up new permissions and hooks, keeping each session's name and thread
argument-hint: pane ids or names, space separated, each optionally as <pane>=<new-name>; empty restarts every peer pane but this one
allowed-tools: ["Bash", "Skill", "ListAgents", "AskUserQuestion"]
---

# Restart agent panes

A permission rule and a hook are read once, when a session starts. A session running since before
they changed still holds the old ones, and only a restart replaces them. An instructions file is
different: it is reinjected each turn, so a rule written there is already live everywhere and is
not a reason to restart.

Restarting loses the session name unless the name is passed to the binary, and the thread unless
the session id is. Load
`shephrd-protocol` and read `references/herdr-cli.md` before starting: it holds why two name
records disagree, why an exit is not immediate, and which flag a restart must not drop.

## Procedure

Per pane, in order. The target of each command is the pane id, which never changes.

1. **Read the pane before touching it.** `herdr agent read <pane>` shows an open approval dialog
   or half-typed text. Keys sent into either land in that context instead of the one expected, so
   a pane that is not at a clean prompt is reported and skipped.

   Read its session id in the same step, from `session_id` in `~/.claude/canary/<pane>.json`
   with the colon of the pane id written as `-`, and check that
   `~/.claude/projects/*/<session_id>.jsonl` exists. The beat is rewritten by the next turn, so
   it is read before the exit rather than after the start.

   Read its kind in the same step, from the `agent` field of the pane in `herdr agent list`. The
   field goes with the pane once it exits, so step 6 cannot read it afterwards.

2. **Ask the session what it loses.** A message asking for uncommitted work, anything running,
   and one line on what to resume. The thread resumes from the transcript, and what dies with
   the process is what the transcript does not hold: a command still running, a background task,
   anything held only in memory. A session that does not answer is reported to the user, who decides.

3. **Wait for it to settle.** `herdr agent wait <pane> --until idle --until done --timeout <ms>`.
   A pane whose last turn finished reports `done` rather than `idle`, and a wait on `idle` alone
   timed out on exactly the panes to restart. An exit sent
   mid-turn discards what the turn was producing, including the answer to step 2. The timeout is
   required here: without one a session that never settles holds the whole restart open. A pane
   that times out is reported and left running.

4. **Exit.** `herdr agent prompt <pane> "/exit"`.

   Read the pane's kind in `ListAgents` first. The `/exit` closes an interactive session; a
   session of kind `bg` it moves to the background sessions panel instead, and the pane stays in
   `herdr agent list` (`references/herdr-cli.md`). A `bg` pane is reported and left as it is,
   and two `C-c` with `herdr agent send-keys` bring a session back from the panel.

5. **Wait for the pane to free.** `herdr agent list` until the `pane_id` is gone from it.

6. **Start with the thread, the name and the permission mode.**
   `herdr agent start <temp> --kind <kind> --pane <pane> -- <resume>`, with `<kind>` the pane's
   `agent` field in `herdr agent list`, read at step 1, and `<resume>` from the Agents table of
   `commands/spawning.md`. For `claude` that is `-r <session_id> -n <name>
   --dangerously-skip-permissions`. A kind with no resume cell starts fresh with its start
   arguments, and the report says so.

   `-r <session_id>` resumes the exact thread the pane was running. `-c` is not a substitute: it
   resumes the most recent conversation in the working directory, and two sessions sharing one
   directory make that the wrong one, as two sessions both in `~` did. A pane with no
   beat, or whose transcript is missing, starts fresh with its kind's start arguments from the
   same table, for `claude` `-n <name> --dangerously-skip-permissions`, and the report says so.

   `<temp>` names the herdr record and must differ from `<name>`, since the dead agent's name is
   still reserved. Dropping the permission flag silently changes the mode and costs the pane its
   peer messages; `references/herdr-cli.md` carries what that measured.

7. **Sync the herdr record.** `herdr agent rename <pane> <name>`.

8. **Verify in `ListAgents`, never in `herdr agent list`.** The second reads the record step 7
   just wrote, which tells nothing about what peers see.

A pane whose name did not survive is repaired with `herdr agent prompt <pane> "/rename <name>"`,
with no restart: `ListAgents` showed the new name within 1 s and the thread was kept. A restart
over it would run through step 4, and a pane renamed by the background service is of kind `bg`,
which the `/exit` does not close (`references/herdr-cli.md`).

## Scope

An agent restarts the panes of its own workspace, read from `$HERDR_WORKSPACE_ID` rather than
from what is focused. A pane outside it is delegated by message to an agent running there.

This session never restarts itself: the process running the command is the one that would die.
A session that needs a new name asks a peer to restart it, and the peer passes `<pane>=<name>`:
the pane restarts under `<name>` rather than its current one. `/shephrd` uses this to name the
god.

## Reporting

Per pane: its name, whether it answered step 2, whether it resumed its thread or started fresh,
and the name `ListAgents` reports at the end. A
pane skipped at step 1 is named with what was on screen. A pane whose name did not survive is
named with the generated one peers now have to use.
