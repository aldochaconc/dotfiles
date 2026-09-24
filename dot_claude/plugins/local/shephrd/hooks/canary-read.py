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
    """Every beat under the canary directory; an unreadable file is skipped."""
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
        # A pane opened by hand has no HERDR_AGENT_NAME, which is most shephrds. The pane id
        # names it instead, since that is what the reader can act on; falling back to the
        # directory would name several panes the same thing.
        rows.append({
            "name": r.get("name") or r.get("pane") or "(no pane)",
            "pane": r.get("pane") or "(no pane)",
            # The beat carries the role. Deriving it here from an empty reports_to would call
            # every god a shephrd, since a god is declared rather than inferred; a beat
            # written before the field existed falls back to the derivation.
            "role": r.get("role") or
                    ("sheep" if (r.get("reports_to") or "") else "shephrd"),
            "reports_to": r.get("reports_to") or "",
            "age": age,
            "at_iso": r.get("at_iso") or "",
            "session_id": r.get("session_id") or "",
            "repo": Path(r.get("repo") or "").name,
            "branch": r.get("branch") or "",
            "worktree": bool(r.get("worktree")),
        })
    rows.sort(key=lambda x: -x["age"])
    return rows


def human(seconds):
    """Render an age in seconds as the shortest readable unit."""
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m{s % 60:02d}s"
    return f"{s // 3600}h{(s % 3600) // 60:02d}m"


def main():
    """Print the beats oldest first, optionally only those older than --stale seconds."""
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

    print(f"{'name':16} {'pane':10} {'role':7} {'last turn':>10}  {'where':28} reports to")
    for r in rows:
        where = r["repo"] or ""
        if r["branch"]:
            where += f"({r['branch']})"
        if r["worktree"]:
            where += " wt"
        print(f"{r['name']:16} {r['pane']:10} {r['role']:7} {human(r['age']):>10}  "
              f"{where[:28]:28} {r['reports_to']}")

    print("\nOldest beat first. An old beat is not a fault on its own: a pane nobody has asked")
    print("anything is correctly quiet. It is a fault when something was sent and the beat did")
    print("not move, which is what a stalled inbox looks like.")


def selftest():
    """Assert-based self-check, run with --selftest."""
    now = 1000.0
    recs = [
        {"session_id": "a", "at": 900.0, "name": "alpha", "pane": "w1:p1", "reports_to": ""},
        {"session_id": "b", "at": 400.0, "name": "beta", "pane": "w1:p2", "reports_to": "alpha"},
        {"session_id": "c", "at": 995.0, "name": "gamma", "pane": "w1:p3", "reports_to": "alpha"},
    ]
    rows = age_rows(recs, now=now)
    assert [r["name"] for r in rows] == ["beta", "alpha", "gamma"], rows
    assert rows[0]["age"] == 600.0
    assert rows[0]["role"] == "sheep"
    assert rows[1]["role"] == "shephrd"

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

    # The role rides on the beat: a god declared in the registry is not derived from having
    # nobody above it, and a reader that guessed would call it a shephrd.
    god = age_rows([{"session_id": "g", "at": now, "pane": "wB:p1",
                     "reports_to": "", "role": "god"}], now=now)[0]
    assert god["role"] == "god", god
    # A beat written before the field existed still resolves.
    assert age_rows([{"session_id": "o", "at": now, "pane": "w1:p9",
                      "reports_to": "lead"}], now=now)[0]["role"] == "sheep"
    assert age_rows([{"session_id": "o", "at": now, "pane": "w1:p9"}],
                    now=now)[0]["role"] == "shephrd"

    # A pane with no agent name is named by its pane id, which is what a shephrd looks like.
    unnamed = age_rows([{"session_id": "y", "at": now, "pane": "wB:p1"}], now=now)
    assert unnamed[0]["name"] == "wB:p1"

    # Location rides on the beat. The repository shows as its basename, since the full path
    # would push the master off the line and carry the home directory with it.
    loc = age_rows([{
        "session_id": "z", "at": now, "pane": "wB:p2",
        "repo": "/home/x/Work/parser", "branch": "bugfix/parser", "worktree": True,
    }], now=now)[0]
    assert loc["repo"] == "parser", loc
    assert loc["branch"] == "bugfix/parser"
    assert loc["worktree"] is True

    # A beat written before these fields existed reads as empty rather than failing.
    old = age_rows([{"session_id": "w", "at": now, "pane": "wB:p3"}], now=now)[0]
    assert old["repo"] == ""
    assert old["worktree"] is False

    print("canary-read selftest passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
