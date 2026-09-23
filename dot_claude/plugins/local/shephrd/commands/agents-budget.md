---
description: Report what every session has left of its context and of the account limits, read from the status line payload rather than the rendered bar
argument-hint: empty reports every recorded session; stale <minutes> reports only readings older than that
allowed-tools: ["Bash", "ListAgents"]
---

# Agent budget

Two budgets run out and they run out differently. A session's context fills up and the session
compacts, losing detail and continuing. The account limits are shared by every session at once,
and when they go nothing runs anywhere.

## Where the figures come from

Claude Code hands the status line script a JSON object on stdin every time the bar is redrawn,
and that object is the only place `rate_limits.five_hour` and `rate_limits.seven_day` appear.
Checked on 2026-09-22: no subcommand of the binary reports them, and no file under `~/.claude`
carries them, including `policy-limits.json` and the dashboard cache.

`~/.claude/statusline-command.sh` therefore keeps the object, one file per session at
`~/.claude/budget/<session_id>.json`, with a `recorded_at` timestamp added. This command reads
those files.

It does not read the rendered bar. A bar is redrawn when its own session takes a turn, so
scraping one reports what that pane last drew: measured across three panes of one workspace,
`5h` read 24% in the pane that had just worked and 19% in one idle for minutes. The files carry
the same staleness and say so, which a bar cannot.

## Thresholds

| Figure | Report from | Why there |
|---|---|---|
| `context_window.used_percentage` | 80% | A compaction is close. It is survivable, so this is information rather than a warning |
| `rate_limits.five_hour` | 85% | Shared and near its end: whatever has to run in this window is decided now |
| `rate_limits.seven_day` | 90% | The same, over a window that does not reset for days |

## Procedure

1. **Read the records.** Every `~/.claude/budget/*.json`. The payload carries nineteen fields,
   of which this report uses `session_id`, `session_name`, `cwd`, `model.display_name`, `cost`,
   the three figures and `recorded_at`.

   `session_name` is the name passed to `claude -n`, so the report names sessions the way
   `SendMessage` addresses them without deriving anything. The rest of the payload, including
   `transcript_path`, `effort` and `prompt_cache`, is kept in the file for whatever asks later.

   An empty directory means no session has redrawn its status line since the recording was
   added, which is reported as that rather than as zero usage.

2. **Age each one.** `recorded_at` against now. A record is as old as its session has been idle,
   and an old record is not wrong: it is the last true reading for that session.

3. **Match to live sessions.** `ListAgents` and `herdr agent list` say which sessions are still
   running. A record whose session has exited is left out; a running session with no record has
   not redrawn its bar yet and is reported with empty figures.

4. **Report.** One table: session name, directory, status, `ctx`, `5h`, `7d`, `cost`, age of the
   reading. Sorted with the closest to a threshold first.

5. **Say what it means, in one line.** The account figures are shared, so the newest reading is
   the one the account is actually at, whichever session produced it. A session near its context
   limit will compact and lose detail. Nothing is closed or restarted from here; `/exit-agents`
   and `/restart-agents` own those.

## Scope

A session that has taken no turn has no record at all: the fields are absent rather than zero,
and the row is reported with those cells empty.

The records accumulate one file per session id and are never cleaned by this command. A session
id is not reused, so a directory that grows is a directory of sessions that have ended, and
removing them is the user's.
