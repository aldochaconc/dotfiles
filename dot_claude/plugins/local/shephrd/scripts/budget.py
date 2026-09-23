#!/usr/bin/env python3
"""What every session has left of its context and of the account limits.

Two budgets run out and they run out differently. A session's context fills and the session
compacts, losing detail and continuing. The account limits are shared by every session at once,
and when they go nothing runs anywhere.

Claude Code hands the status line script a JSON object on stdin every time the bar is redrawn,
and that object is the only place `rate_limits.five_hour` and `rate_limits.seven_day` appear.
Checked: no subcommand of the binary reports them, and no file under `~/.claude`
carries them. `~/.claude/statusline-command.sh` keeps each object at
`~/.claude/budget/<session_id>.json` with a `recorded_at` added, and this reads those files.

It does not scrape the rendered bar. A bar is redrawn when its own session takes a turn, so
reading one reports what that pane last drew: measured across three panes of one workspace, the
five-hour figure read 24% in the pane that had just worked and 19% in one idle for minutes. The
files carry the same staleness and say so, which a bar cannot.

Read-only. It reads the budget files and asks the roster which sessions are alive.

Self-check: python3 budget.py --selftest
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DIR = Path(os.environ.get("HOME", "/tmp")) / ".claude" / "budget"

# A figure is reported from its threshold up. Each one is where the number starts changing what
# the reader would do, not where it becomes alarming.
THRESHOLDS = {
    # A compaction is close. It is survivable, so this is information rather than a warning.
    "ctx": 80,
    # Shared and near its end: whatever has to run in this window is decided now.
    "5h": 85,
    # The same, over a window that does not reset for days.
    "7d": 90,
}


def records(directory=None):
    """Every budget record, newest reading first. An unreadable file is skipped."""
    d = Path(directory) if directory else DIR
    out = []
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except (OSError, ValueError):
            continue
    return out


def live_names():
    """Session names the roster reports as running, or None when herdr is unreachable.

    None and an empty set mean different things: nothing answered, against nothing is running.
    A caller that cannot tell them apart drops every row.
    """
    try:
        r = subprocess.run(["herdr", "agent", "list"], capture_output=True, text=True, timeout=10)
        agents = json.loads(r.stdout)["result"]["agents"]
    except Exception:
        return None
    return {a.get("name") or a.get("terminal_title_stripped", "") for a in agents}


def age_seconds(recorded_at, now=None):
    """Seconds since a reading, or None when the timestamp does not parse."""
    if not recorded_at:
        return None
    try:
        then = datetime.fromisoformat(recorded_at)
    except (TypeError, ValueError):
        return None
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    now = now if now is not None else datetime.now(timezone.utc).timestamp()
    return int(now - then.timestamp())


def row(rec, now=None, live=None):
    """One record flattened to what the table prints.

    A missing figure stays None rather than becoming zero. A session that has taken no turn has
    no figures at all, and reporting that as zero usage inverts the fact.
    """
    ctx = (rec.get("context_window") or {}).get("used_percentage")
    limits = rec.get("rate_limits") or {}
    return {
        "name": rec.get("session_name") or "",
        "cwd": rec.get("cwd") or "",
        "model": (rec.get("model") or {}).get("display_name") or "",
        "ctx": ctx,
        "5h": (limits.get("five_hour") or {}).get("used_percentage"),
        "7d": (limits.get("seven_day") or {}).get("used_percentage"),
        "cost": (rec.get("cost") or {}).get("total_cost_usd"),
        "age": age_seconds(rec.get("recorded_at"), now),
        "live": None if live is None else (rec.get("session_name") or "") in live,
    }


def pressure(r):
    """How close this row is to any threshold, as the sort key. Highest first."""
    return max((r[k] or 0) - t for k, t in THRESHOLDS.items())


_UNSET = object()


def rows(recs=None, now=None, live=_UNSET):
    """Rows for live sessions, closest to a threshold first.

    A record whose session has exited is dropped: it is the last true reading for a session that
    is no longer spending anything. When the roster does not answer, every record is kept, since
    dropping them all would report an empty account rather than an unknown one.

    `live` takes a sentinel rather than None as its default, because None is the value that says
    the roster did not answer. Defaulting to None would make an unreachable roster and an
    unspecified argument the same call, and they decide opposite things about every row.
    """
    recs = records() if recs is None else recs
    live = live_names() if live is _UNSET else live
    out = [row(r, now, live) for r in recs]
    if live is not None:
        out = [r for r in out if r["live"]]

    # One record per session name, the newest kept. A name is reused across restarts and the
    # roster matches on it, so a restarted session's dead records all read as live: one name has
    # carried three records, two of them from sessions fourteen and sixteen hours gone. The newest is the only one describing what is running now.
    newest = {}
    for r in out:
        prev = newest.get(r["name"])
        if prev is None or (r["age"] is not None
                            and (prev["age"] is None or r["age"] < prev["age"])):
            newest[r["name"]] = r
    return sorted(newest.values(), key=pressure, reverse=True)


def _pct(v, key):
    if v is None:
        return "-"
    return f"{v}%!" if v >= THRESHOLDS[key] else f"{v}%"


def _age(s):
    if s is None:
        return "-"
    if s < 90:
        return f"{s}s"
    if s < 5400:
        return f"{s // 60}m"
    return f"{s // 3600}h"


def render(data):
    if not data:
        return ("No session has redrawn its status line since the recording was added. "
                "That is an empty record set, not zero usage.")
    head = f"{'session':16} {'model':14} {'ctx':6} {'5h':6} {'7d':6} {'cost':9} {'read':5}"
    lines = [head, "-" * len(head)]
    for r in data:
        cost = "-" if r["cost"] is None else f"${r['cost']:.2f}"
        lines.append(f"{r['name'][:16]:16} {r['model'][:14]:14} {_pct(r['ctx'], 'ctx'):6} "
                     f"{_pct(r['5h'], '5h'):6} {_pct(r['7d'], '7d'):6} {cost:9} "
                     f"{_age(r['age']):5}")

    # The account figures are shared, so the newest reading is where the account actually is,
    # whichever session produced it. An older row showing less is not a second opinion.
    freshest = min((r for r in data if r["age"] is not None),
                   key=lambda r: r["age"], default=None)
    if freshest and freshest["5h"] is not None:
        lines.append("")
        lines.append(f"account, newest reading ({_age(freshest['age'])} old): "
                     f"5h {freshest['5h']}%, 7d {freshest['7d']}%")

    near = [r for r in data if r["ctx"] is not None and r["ctx"] >= THRESHOLDS["ctx"]]
    if near:
        lines.append("")
        for r in near:
            lines.append(f"{r['name']} is at {r['ctx']}% context and will compact, losing detail")
    return "\n".join(lines)


def selftest():
    now = datetime(2026, 9, 23, 17, 0, tzinfo=timezone.utc).timestamp()
    mk = lambda name, ctx, h5, d7, cost, when: {
        "session_name": name, "cwd": "/x", "model": {"display_name": "Opus"},
        "context_window": {"used_percentage": ctx},
        "rate_limits": {"five_hour": {"used_percentage": h5},
                        "seven_day": {"used_percentage": d7}},
        "cost": {"total_cost_usd": cost}, "recorded_at": when,
    }
    recs = [
        mk("quiet", 10, 20, 5, 1.0, "2026-09-23T16:00:00+00:00"),
        mk("busy", 91, 60, 8, 52.5, "2026-09-23T16:59:00+00:00"),
        mk("gone", 30, 20, 5, 2.0, "2026-09-23T16:30:00+00:00"),
    ]
    live = {"quiet", "busy"}

    data = rows(recs, now, live)
    # A session the roster does not list is dropped: it spends nothing now.
    assert [r["name"] for r in data] == ["busy", "quiet"], data
    # Sorted by distance to a threshold, so the one about to compact leads.
    assert data[0]["name"] == "busy"
    assert data[0]["ctx"] == 91

    # An unreachable roster keeps every record rather than reporting an empty account.
    assert len(rows(recs, now, None)) == 3

    # A name reused across restarts carries one record per session and the roster matches on the
    # name, so every dead record of a restarted session reads as live. Only the newest describes
    # what is running.
    dup = [
        mk("worker", 30, 20, 5, 2.0, "2026-09-23T02:00:00+00:00"),
        mk("worker", 70, 60, 8, 40.0, "2026-09-23T16:59:00+00:00"),
        mk("worker", 50, 40, 6, 9.0, "2026-09-23T09:00:00+00:00"),
    ]
    once = rows(dup, now, {"worker"})
    assert len(once) == 1, once
    assert once[0]["ctx"] == 70, once
    assert once[0]["age"] == 60

    # Ages come from the timestamp, in seconds.
    assert data[0]["age"] == 60
    assert data[1]["age"] == 3600
    assert age_seconds(None) is None
    assert age_seconds("not a date") is None

    # A missing figure stays absent rather than becoming zero.
    bare = row({"session_name": "new"}, now, live)
    assert bare["ctx"] is None and bare["5h"] is None and bare["cost"] is None
    assert _pct(None, "ctx") == "-"
    # A figure at or over its threshold is marked; under it is not.
    assert _pct(80, "ctx") == "80%!"
    assert _pct(79, "ctx") == "79%"
    assert _pct(85, "5h") == "85%!"
    assert _pct(84, "5h") == "84%"

    assert _age(None) == "-"
    assert _age(60) == "60s"
    assert _age(600) == "10m"
    assert _age(7200) == "2h"

    text = render(data)
    assert "busy" in text and "quiet" in text
    assert "gone" not in text
    # The account line quotes the newest reading, not the highest.
    assert "5h 60%, 7d 8%" in text, text
    assert "will compact" in text

    # An empty set says so rather than printing a bare header.
    assert "not zero usage" in render([])

    print("budget selftest passed")


def main():
    if "--json" in sys.argv:
        print(json.dumps(rows(), indent=2))
        return 0
    print(render(rows()))
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    sys.exit(main())
