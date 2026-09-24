---
description: Close Claude in herdr panes after each session writes what it was doing, leaving the panes at their shell prompt
argument-hint: pane ids or names, space separated; empty closes every pane of this workspace but this one
allowed-tools: ["Bash", "Skill", "ListAgents", "SendMessage", "AskUserQuestion"]
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

2. **Separate the panes that can be closed from the one that cannot.** `agent_status` of
   `blocked` means a dialog is open in that pane and nothing programmatic reaches it. Measured on
   `herdr agent prompt` refused with `agent_blocked: agent <pane> is blocked and
   requires interactive input`, so the pane could be neither asked for a handoff nor exited.

   | Status | What this command can do |
   |---|---|
   | `idle`, `done` | ask for the handoff, then exit |
   | `working` | wait, then the same |
   | `blocked` | read the screen, ask the user, and dismiss only if they say so |

   A blocked pane is recoverable rather than lost. `herdr agent send-keys <pane> Escape` reaches
   it where a prompt cannot, because keys go to the terminal rather than through the agent:
   A pane blocked for over an hour returned `{"type":"ok"}`, moved to
   `done`, and kept its context at 9%. It could then be asked for a handoff like any other.

   Escape discards what the dialog was asking, so it is the user's call and not this command's.
   Report what `herdr agent read` shows, and ask: a question they still want to answer is
   answered in that pane, and dismissing it throws away the reasoning behind the options.

   A pane left blocked writes no handoff, so what it knows is lost unless another session
   recorded it.

   What is on disk survives it regardless, and that is worth measuring before the report says
   work is at risk: `git -C <cwd> status --short` and `git -C <cwd> stash list` say what the
   close would and would not cost. a blocked pane's three fixes were all on disk,
   one staged and two in a labelled stash, so what was lost was the analysis and not the code.

3. **Ask before waiting on a working session.** `agent_status` of `working` means the session is
   mid-operation, and finishing that turn spends context the session will not have afterwards.
   The choice is the user's, and it is asked with the figures in hand: the pane's name, what
   `herdr agent read <pane>` shows for `ctx`, `5h` and `7d`, and the two outcomes.

   | Answer | What happens |
   |---|---|
   | let it finish | `herdr agent wait <pane> --until idle --until done`, no timeout. The turn runs to its end whatever it costs |
   | close now | no wait: step 4 runs, step 5 is skipped and the report says the handoff is missing, and step 6 sends the exit mid-turn, losing whatever the turn was producing |

   The wait is deliberately unbounded, because a timeout here would decide the same question by
   expiry that the user just answered. A session reported as `idle` needs no question and no
   wait.

   The turn is not interrupted to ask: the question goes to the user, not to the session. A
   message sent to a working session is queued and delivered when it settles, so nothing is lost
   by waiting.

4. **Check the tree.** `git -C <cwd> status --short` on the session's working directory. This is
   the loss that can be seen from outside without asking anyone, and it is the one that matters:
   uncommitted work in a tree nobody is watching. It is reported with the pane rather than
   resolved, since committing is the user's.

5. **Read the budget, then ask for the summary.** The status bar in `herdr agent read <pane>`
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

   The message asks for the file and for a reply, and never for the exit. A session cannot run
   `/exit` on itself, which step 6 records; asking it to produces a session that wrote its
   handoff, said it cannot close, and is still running.

   What the message carries decides whether the handoff is worth having. Naming the sections is
   not enough: a session writes what it did, which is the part already visible from outside.
   Ask for what is not on disk anywhere else, which is the only thing that dies with the
   process. that produced three files of 7 to 15 KB carrying a scope that was
   never recorded, seven figures one session had passed wrong and another had corrected, and a
   working-tree arrangement that had contained two losses of work that day.

   The reply says whether the file was written. A session that does not answer is reported and
   left running, because silence and "nothing to save" are not the same answer. Writing the
   summary is itself a turn, so the session goes to `working` again and the wait from step 3
   applies before the exit.

6. **Exit.** `herdr agent prompt <pane> "/exit"`, run from this session against that pane.

   Read the pane's kind in `ListAgents` first. The `/exit` closes an interactive session; a
   session of kind `bg` it moves to the background sessions panel instead, and the pane stays in
   `herdr agent list` (`references/herdr-cli.md`). A `bg` pane is reported and left as it is,
   and two `C-c` with `herdr agent send-keys` bring a session back from the panel.

   A session cannot close itself, and asking it to is the mistake this step exists to prevent.
   `/exit` is a command the terminal interprets, not a tool a session can call: measured on
two sessions were each asked to write a handoff and then exit, both wrote the file
   and both answered that they had no way to run the command. They stayed alive with their work
   saved, which is the harmless version of the failure; the harmful one is a close reported as
   done that never happened.

   So the message asks only for the handoff and the reply. The exit is this session's to send,
   after the reply confirms the file exists.

   `herdr agent send-keys <pane> ctrl+d` does not close it: the call returns `ok` and the agent
   stays alive.

7. **Confirm.** `herdr agent list` until the `pane_id` is gone. The exit is not immediate, and
   `herdr agent read` in that interval returns the shell prompt with Claude's status bar still
   drawn, so a pane that has already exited reads as alive.

## Reporting

One line per pane: its name, whether a summary was written and where, what `git status` showed,
and whether it closed. A pane left running is named with the reason, which is one of four: it was
blocked on a dialog, the wait timed out, the session never answered, or its tree carries
uncommitted work. The decision to close it anyway stays the user's, and for a blocked pane it is
not the user's to make from here at all: the dialog has to be answered in that pane first.

A summary missing for want of context is reported as that, not as a failure: the session was
closed deliberately with what it had.
