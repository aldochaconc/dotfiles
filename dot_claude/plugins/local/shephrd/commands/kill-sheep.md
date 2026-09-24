---
description: End this sheep: report to the shephrd, write the handoff, close the pane
allowed-tools: ["Bash", "Skill", "SendMessage"]
---

# End this session

The order is fixed and each step is what makes the next survivable: the report, the handoff, the
close. A pane that closes first has nothing left to say it, and the work it was holding becomes
a tree nobody claims.

Run this on the order of the shephrd or the user, never because the work looks finished from
inside the pane. A sheep whose work is done reports, writes its handoff and stays open, so its
context serves the follow-up and its screen still shows what it did. Measured on 2026-09-23: two
sheep that closed themselves on finishing left the user nothing to read, and each follow-up
became a new sheep reloading from a handoff. The shephrd orders the close when the next task
fails the reuse test in `shephrd-protocol`.

A shephrd or a god never runs it: closing a shephrd's pane orphans its sheep, and closing the
god's leaves the user with no window.

## 1. Read what this pane is

    python3 ${CLAUDE_PLUGIN_ROOT}/hooks/panes.py

The `role` decides whether this command applies and the `reports_to` names where the report
goes. A `role` of `shephrd`, `god` or an empty string stops here: say so and run nothing.

A sheep whose `reports_to` is empty stops too. The report is what makes the close survivable and
there is nobody to send it to, so the pane stays open and says that.

## 2. Measure the tree

    git status --short

Closing the pane closes the terminal, so whatever is uncommitted becomes a tree with no session
that knows what it holds. A pane died mid-task leaving four modified
files and an untracked workdoc of 1050 lines, and the untracked file was outside the backup its
shephrd had taken, because `git diff` covers what changed and not what is new.

Both classes go in the report, and they are reported separately. What is modified is recoverable
from the diff; what is untracked is lost whole rather than partially.

## 3. Report to the shephrd

`SendMessage` to the name in `reports_to`, carrying:

| Part | Content |
|---|---|
| done | what landed, by outcome |
| open | what was left, and how far it got |
| tree | modified paths, untracked paths, and what is staged or committed |
| handoff | the path written in step 4 |

This is the last thing this pane will ever say. A report that omits the tree leaves the shephrd
discovering it later, from a pane that no longer exists.

## 4. Write the handoff

    ~/.claude/handoff/<name>-<date>.md

`<name>` is this pane's registered name and `<date>` is `YYYY-MM-DD`. A handoff written when the
work finished is updated rather than written again. The directory is global, so
the shephrd reads it from whatever tree it sits in, and it survives the message going unread.

What it holds is what the report holds, at the length the report could not carry: the decisions
taken and why, what was measured and against what, what is unfinished and what the next session
would have to re-derive. A handoff that restates the commit log is not worth the file.

The directory is `handoff` rather than `sessions`, because `~/.claude/sessions` belongs to Claude
Code.

## 5. Close the pane

    herdr pane close $HERDR_PANE_ID

This is the step the plugin said for a while was impossible, and the claim was about `/exit`.
`/exit` is a terminal command rather than a tool, so a session asked to run it writes its handoff
and stays alive. `herdr pane close` takes any pane id
including the caller's own and reaches the pane from outside the process, so it works.

The pane disappears rather than returning to a shell prompt. `/exit-agents` leaves the shell so a
relaunch can reuse the `pane_id`; this command is for a pane whose work is done and which nothing
will reuse.

Nothing follows this step. The process ends inside it, so a message sent after it is never sent
and a file written after it is never written.
