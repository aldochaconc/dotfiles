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

2. **Ask before waiting on a working session.** `agent_status` of `working` means the session is
   mid-operation, and finishing that turn spends context the session will not have afterwards.
   The choice is the user's, and it is asked with the figures in hand: the pane's name, what
   `herdr agent read <pane>` shows for `ctx`, `5h` and `7d`, and the two outcomes.

   | Answer | What happens |
   |---|---|
   | let it finish | `herdr agent wait <pane> --until idle`, no timeout. The turn runs to its end whatever it costs |
   | close now | the exit is sent mid-turn and whatever the turn was producing is lost |

   The wait is deliberately unbounded, because a timeout here would decide the same question by
   expiry that the user just answered. A session reported as `idle` needs no question and no
   wait.

   The turn is not interrupted to ask: the question goes to the user, not to the session. A
   message sent to a working session is queued and delivered when it settles, so nothing is lost
   by waiting.

3. **Check the tree.** `git -C <cwd> status --short` on the session's working directory. This is
   the loss that can be seen from outside without asking anyone, and it is the one that matters:
   uncommitted work in a tree nobody is watching. It is reported with the pane rather than
   resolved, since committing is the user's.

4. **Read the budget, then ask for the summary.** The status bar in `herdr agent read <pane>`
   carries `ctx`, `5h` and `7d`, and it is read after the wait rather than before: the turn that
   just ended spent context, so a figure taken earlier describes a session that no longer exists.

   A session with no context left cannot write a summary, and asking costs it the little that
   remains. It is closed with what exists and the report says the summary is missing and why.

   Otherwise one message asks it to write, before exiting, a file under
   `~/.claude/handoff/<name>-<date>.md` holding what it did, what is unfinished, and what the
   next session on that tree has to know. A summary is machine state rather than configuration,
   so it is written where the machine keeps state and not into any repository.

   The directory is `handoff` and not `sessions`, because `~/.claude/sessions` belongs to Claude
   Code, which keeps ten files of its own there named by process id.

   The reply says whether the file was written. A session that does not answer is reported and
   left running, because silence and "nothing to save" are not the same answer. Writing the
   summary is itself a turn, so the session goes to `working` again and the wait from step 2
   applies before the exit.

5. **Exit.** `herdr agent prompt <pane> "/exit"`.

   `herdr agent send-keys <pane> ctrl+d` does not close it: the call returns `ok` and the agent
   stays alive.

6. **Confirm.** `herdr agent list` until the `pane_id` is gone. The exit is not immediate, and
   `herdr agent read` in that interval returns the shell prompt with Claude's status bar still
   drawn, so a pane that has already exited reads as alive.

## Reporting

One line per pane: its name, whether a summary was written and where, what `git status` showed,
and whether it closed. A pane left running is named with the reason, which is one of three: the
wait timed out, the session never answered, or its tree carries uncommitted work. The decision
to close it anyway stays the user's.

A summary missing for want of context is reported as that, not as a failure: the session was
closed deliberately with what it had.
