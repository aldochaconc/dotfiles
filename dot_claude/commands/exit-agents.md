---
description: Close Claude in herdr panes after each session writes what it was doing, leaving the panes at their shell prompt
argument-hint: pane ids or names, space separated; empty closes every pane of this workspace but this one
allowed-tools: ["Bash", "ListAgents", "SendMessage", "AskUserQuestion"]
---

# Close agent panes

A session's context dies with its process, and closing is where that becomes permanent: a
restart at least brings the session back to the same tree, a close does not. What the session
knows and never wrote down is the loss, and it is the only party that can write it.

The pane stays at its shell prompt. Closing the pane as well would recompose the layout and
force a spawn to get it back, while a pane left open takes a relaunch on the same `pane_id` with
the layout untouched.

## Procedure

Per pane, in order. A pane that fails a check is reported and left running.

1. **Resolve the set.** `herdr agent list` carries every pane and its `workspace_id`. Without
   arguments the set is the panes matching `$HERDR_WORKSPACE_ID`, minus this session's own
   `$HERDR_PANE_ID`. A pane in another workspace is not closed from here: it is delegated by
   message to an agent running there.

   This session never closes itself. The process running the command is the one that would die,
   and the user closes it.

2. **Check the state.** `agent_status` of `working` means the session is mid-operation, and
   closing it cuts that operation. It is reported and skipped, not waited on: what it is doing
   is unknown from here, and a wait with no bound is worse than a report.

3. **Check the tree.** `git -C <cwd> status --short` on the session's working directory. This is
   the loss that can be seen from outside without asking anyone, and it is the one that matters:
   uncommitted work in a tree nobody is watching. It is reported with the pane rather than
   resolved, since committing is the user's.

4. **Ask for the summary.** One message to the session asking it to write, before exiting, a
   file under `~/.claude/sessions/<name>-<date>.md` holding what it did, what is unfinished,
   and what the next session on that tree has to know. That directory is outside chezmoi, which
   is correct: a summary is machine state and not configuration.

   The reply says whether the file was written. A session that does not answer is reported and
   left running, because silence and "nothing to save" are not the same answer.

5. **Read the budget.** The status bar in `herdr agent read <pane>` carries `ctx`, `5h` and
   `7d`. A session out of context cannot write a summary, and asking it again only burns what is
   left: it is closed with what exists, and the report says the summary is missing and why.

6. **Exit.** `herdr agent prompt <pane> "/exit"`.

   `herdr agent send-keys <pane> ctrl+d` does not close it: the call returns `ok` and the agent
   stays alive.

7. **Confirm.** `herdr agent list` until the `pane_id` is gone. The exit is not immediate, and
   `herdr agent read` in that interval returns the shell prompt with Claude's status bar still
   drawn, so a pane that has already exited reads as alive.

## Reporting

One line per pane: its name, whether a summary was written and where, what `git status` showed,
and whether it closed. A pane skipped at step 2 or 3 is named with the reason, so the decision
to close it anyway stays the user's.
