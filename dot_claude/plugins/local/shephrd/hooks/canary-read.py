#!/usr/bin/env python3
"""Read the canary beats and say which panes have gone quiet.

`canary.py` writes one beat per session at the end of every turn. This reads them and compares
each against the others, because age alone answers nothing: a session nobody has spoken to is
correctly quiet, and one that was sent five messages and has not moved is stalled. Both look
like an old file.

What separates them is whether something is waiting. That is not in the beat, so this reports
the ages and the caller supplies the expectation: a pane sent a message two minutes ago whose
beat is ten minutes old took no turn for it.

Run with no arguments for the table. `--stale <seconds>` limits it to beats older than that.
"""

import json
import os
import sys
import time
from pathlib import Path

DIR = Path(os.environ.get("HOME", "/tmp")) / ".claude" / "canary"


def load(directory=None):
    directory = Path(directory) if directory else DIR
    out = []
    if not directory.is_dir():
        return out
    for f in sorted(directory.glob("*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except Exception:
            # A half-written beat is skipped rather than failing the whole read.
            continue
    return out


def age_rows(records, now=None, stale=None):
    """Sort by age, oldest first. The oldest beat is the pane most likely to be stuck."""
    now = now if now is not None else time.time()
    rows = []
    for r in records:
        age = now - float(r.get("at") or 0)
        if stale is not None and age < stale:
            continue
        # A pane opened by hand has no HERDR_AGENT_NAME, which is most masters. The pane id
        # names it instead, since that is what the reader can act on; falling back to the
        # directory would name several panes the same thing.
        rows.append({
            "name": r.get("name") or r.get("pane") or "(no pane)",
            "pane": r.get("pane") or "(no pane)",
            "role": "slave" if (r.get("master") or "") else "master",
            "master": r.get("master") or "",
            "age": age,
            "at_iso": r.get("at_iso") or "",
            "session_id": r.get("session_id") or "",
        })
    rows.sort(key=lambda x: -x["age"])
    return rows


def human(seconds):
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m{s % 60:02d}s"
    return f"{s // 3600}h{(s % 3600) // 60:02d}m"


def main():
    stale = None
    if "--stale" in sys.argv:
        i = sys.argv.index("--stale")
        if i + 1 < len(sys.argv):
            stale = float(sys.argv[i + 1])

    rows = age_rows(load(), stale=stale)
    if not rows:
        where = "older than %s" % human(stale) if stale else "at all"
        print(f"no beats {where}. A pane with no beat has taken no turn since the hook was installed.")
        return

    print(f"{'name':16} {'pane':10} {'role':7} {'last turn':>10}  master")
    for r in rows:
        print(f"{r['name']:16} {r['pane']:10} {r['role']:7} {human(r['age']):>10}  {r['master']}")

    print("\nOldest beat first. An old beat is not a fault on its own: a pane nobody has asked")
    print("anything is correctly quiet. It is a fault when something was sent and the beat did")
    print("not move, which is what a stalled inbox looks like.")


def selftest():
    now = 1000.0
    recs = [
        {"session_id": "a", "at": 900.0, "name": "alpha", "pane": "w1:p1", "master": ""},
        {"session_id": "b", "at": 400.0, "name": "beta", "pane": "w1:p2", "master": "alpha"},
        {"session_id": "c", "at": 995.0, "name": "gamma", "pane": "w1:p3", "master": "alpha"},
    ]
    rows = age_rows(recs, now=now)
    assert [r["name"] for r in rows] == ["beta", "alpha", "gamma"], rows
    assert rows[0]["age"] == 600.0
    assert rows[0]["role"] == "slave"
    assert rows[1]["role"] == "master"

    # alpha is 100s old and beta 600s, so a 200s threshold keeps only beta.
    only = age_rows(recs, now=now, stale=200.0)
    assert [r["name"] for r in only] == ["beta"], only
    assert [r["name"] for r in age_rows(recs, now=now, stale=50.0)] == ["beta", "alpha"]

    assert age_rows([], now=now) == []
    assert human(45) == "45s"
    assert human(125) == "2m05s"
    assert human(7300) == "2h01m"

    # A record with no timestamp is maximally old rather than crashing the read.
    odd = age_rows([{"session_id": "x"}], now=now)
    assert odd[0]["age"] == now
    assert odd[0]["name"] == "(no pane)"

    # A pane with no agent name is named by its pane id, which is what a master looks like.
    unnamed = age_rows([{"session_id": "y", "at": now, "pane": "w1T:p1"}], now=now)
    assert unnamed[0]["name"] == "w1T:p1"

    print("canary-read selftest: 13 checks passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
