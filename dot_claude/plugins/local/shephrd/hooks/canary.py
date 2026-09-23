#!/usr/bin/env python3
"""Liveness for a pane, written by the pane itself and read by anyone.

A session that stops consuming its inbox looks identical from outside to one that is simply
idle. Measured on 2026-09-22: five `SendMessage` to one pane, none read, the pane reporting
`idle` the whole time; a sixth message would have looked exactly as fine as the first five.
`herdr agent list` reports what the terminal is doing and Claude Code's own status says nothing
about whether messages are being taken off the queue.

So each pane leaves a beat. `Stop` fires when a session finishes a turn, so a file written there
carries the time of the last turn that actually completed. Silence in that file is the signal: a
pane whose beat is older than its peers' has stopped taking turns, whatever its status says.

One file per session under ~/.claude/canary, named by session id, holding the fields a reader
needs to tell a stalled pane from a quiet one. Failure is silent: a hook that breaks must not
take the session with it.
"""

import json
import os
import sys
import time
from pathlib import Path

DIR = Path(os.environ.get("HOME", "/tmp")) / ".claude" / "canary"


def beat(payload, env=None, now=None):
    """Build the record for one turn ending. Returns None when there is no session to name."""
    env = env if env is not None else os.environ
    now = now if now is not None else time.time()

    sid = (payload.get("session_id") or "").strip()
    if not sid:
        return None

    return {
        "session_id": sid,
        "at": now,
        "at_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now)),
        "pane": (env.get("HERDR_PANE_ID") or "").strip(),
        "workspace": (env.get("HERDR_WORKSPACE_ID") or "").strip(),
        "name": (env.get("HERDR_AGENT_NAME") or "").strip(),
        "master": (env.get("HERDR_AGENT_MASTER") or "").strip(),
        "cwd": (payload.get("cwd") or "").strip(),
        "event": (payload.get("hook_event_name") or "").strip(),
    }


def write(record, directory=None):
    """Write one record, replacing the previous beat for that session."""
    directory = Path(directory) if directory else DIR
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{record['session_id']}.json"
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(record))
    tmp.replace(target)
    return target


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        record = beat(payload)
        if record:
            write(record)
    except Exception:
        # A canary that breaks a turn is worse than no canary.
        pass
    sys.exit(0)


def selftest():
    import tempfile

    env = {
        "HERDR_PANE_ID": "w1R:p8",
        "HERDR_WORKSPACE_ID": "w1R",
        "HERDR_AGENT_NAME": "worker-a",
        "HERDR_AGENT_MASTER": "lead",
    }
    r = beat({"session_id": "abc", "cwd": "/tmp/x", "hook_event_name": "Stop"}, env, now=1000.0)
    assert r["session_id"] == "abc"
    assert r["pane"] == "w1R:p8"
    assert r["master"] == "lead"
    assert r["at"] == 1000.0

    # No session id means no record: a beat that cannot name its session identifies nothing.
    assert beat({}, env) is None
    assert beat({"session_id": "   "}, env) is None

    # A master pane has no master and that is a value, not a missing field.
    r2 = beat({"session_id": "m"}, {}, now=1.0)
    assert r2["master"] == ""
    assert r2["pane"] == ""

    with tempfile.TemporaryDirectory() as d:
        p = write(r, d)
        assert p.exists()
        assert json.loads(p.read_text())["pane"] == "w1R:p8"
        # A second beat replaces the first rather than accumulating.
        write(beat({"session_id": "abc"}, env, now=2000.0), d)
        assert json.loads(p.read_text())["at"] == 2000.0
        assert len(list(Path(d).glob("*.json"))) == 1
        assert not list(Path(d).glob("*.tmp"))

    print("canary selftest: 12 checks passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
