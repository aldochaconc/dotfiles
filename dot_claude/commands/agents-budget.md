---
description: Report what every agent pane has left of its context and of the account limits, and say which ones are close to stopping
argument-hint: empty reports this workspace; all reports every workspace
allowed-tools: ["Bash", "ListAgents"]
---

# Agent budget

Two budgets run out and they run out differently. A session's context fills up and the session
compacts, losing detail and continuing. The account limits are shared by every session at once,
and when they go nothing runs anywhere.

Both are read from the status bar of `herdr agent read <pane>`, which carries `ctx`, `5h` and
`7d` and is readable while the pane is mid-turn. Verified on 2026-09-22 against a working pane:
`Opus 5 | ctx:31% | 5h:24% | 7d:75%`.

The reading costs this session context on every pass, which is why the report is asked for
rather than watched. A loop watching the others would spend the coordinating session's own
budget to report on everyone else's.

## Thresholds

| Figure | Report from | Why there |
|---|---|---|
| `ctx` | 80% | A compaction is close. It is survivable, so this is information, not a warning |
| `5h` | 85% | Shared and near its end: whatever has to run in this window is decided now |
| `7d` | 90% | The same, over a window that does not reset for days |

A pane reading `ctx:–` has no figure yet, which is not zero. It is reported as unknown.

## Procedure

1. **Resolve the set.** `herdr agent list` carries every pane and its `workspace_id`. Without
   arguments the set is the panes matching `$HERDR_WORKSPACE_ID`, this session's own included:
   its budget counts as much as any other. With `all`, every pane of every workspace.

2. **Read each status bar.** `herdr agent read <pane>`, taking the last lines. The figures are
   whatever that bar carries, and a missing one is left empty rather than guessed: see
   Staleness.

3. **Report.** One table: pane, name, `agent_status`, `ctx`, `5h`, `7d`. Sorted with the
   closest to a threshold first, since that is the row the question is about.

4. **Say what it means, in one line.** A figure over a threshold is named with what it costs:
   a session near its context will compact and lose detail, and account limits near their end
   stop every session at once. The account figure used for that line is the highest one read,
   for the reason under Staleness. Nothing is closed or restarted from here; `/exit-agents` and
   `/restart-agents` own those.

## Staleness

The account limits are shared, and the figures reported for them are not. A status bar is
redrawn when its own session takes a turn, so an idle pane shows what was true at its last turn
and not what is true now. Measured on 2026-09-22 across three panes of one workspace: `5h` read
24% in the pane that had just worked and 19% in one idle for minutes, with `7d` at 75% and 74%.

The highest reading is therefore the least stale, and it is the one the account is actually at.
Every row still carries its own figures, because the gap between them is what shows which rows
are old.

A pane that has taken no turn yet carries no account figures at all: its bar reads
`Opus 5 | ctx:– | dotfiles(main)`, with `5h` and `7d` simply absent rather than zero. The row is
reported with those cells empty, which says the session has not spent anything since it started.
