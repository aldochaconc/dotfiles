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
import subprocess
import sys
import time
from pathlib import Path

DIR = Path(os.environ.get("HOME", "/tmp")) / ".claude" / "canary"


def _master(env, registry_dir=None):
    """The master this pane answers to, from the environment or the registry behind it.

    Importing `panes` is avoided: a hook that fails on a missing sibling stops writing beats,
    and a beat is what makes a stalled pane visible. The file is read directly and any failure
    leaves the field empty, which is what the variable alone would have given.
    """
    value = (env.get("HERDR_AGENT_MASTER") or "").strip()
    if value:
        return value
    pane = (env.get("HERDR_PANE_ID") or "").strip()
    if not pane:
        return ""
    d = Path(registry_dir) if registry_dir else Path(
        env.get("HOME", "/tmp")) / ".claude" / "panes"
    try:
        return (json.loads((d / (pane.replace(":", "-") + ".json")).read_text())
                .get("master") or "").strip()
    except (OSError, ValueError, AttributeError):
        return ""


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
        # The registry answers what the environment lost. A restarted pane has no
        # HERDR_AGENT_MASTER, and a beat that read only the variable listed a sheep as a master:
        # measured on 2026-09-23 on two panes whose threads had resumed correctly.
        "master": _master(env),
        "cwd": (payload.get("cwd") or "").strip(),
        "event": (payload.get("hook_event_name") or "").strip(),
        **where(payload.get("cwd") or ""),
    }


def where(cwd):
    """The repository a pane is working in, and the branch, when there is one.

    A pane inside a linked worktree has a `cwd` under a scratchpad and a branch nobody else is
    on, so the directory alone says neither which repository it belongs to nor what it is
    building. Measured on 2026-09-23: one workspace held a worktree at a session scratchpad path
    while the main checkout sat elsewhere on another branch.

    `--git-common-dir` answers the main repository from either side. Everything here is best
    effort: a read that fails leaves the fields empty rather than failing the beat.
    """
    out = {"repo": "", "branch": "", "worktree": False}
    if not cwd:
        return out
    try:
        common = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, timeout=5,
        )
        if common.returncode != 0:
            return out
        common_dir = common.stdout.strip()
        out["repo"] = str(Path(common_dir).parent) if common_dir.endswith(".git") else common_dir

        top = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if top.returncode == 0 and top.stdout.strip():
            out["worktree"] = str(Path(top.stdout.strip())) != out["repo"]

        branch = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if branch.returncode == 0:
            out["branch"] = branch.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return out
    return out


def beat_key(record):
    """The file name a beat is written under.

    A pane is what the reader watches, so the pane id is the key where there is one. Keying by
    session id instead accumulates a file per session in one pane, and a pane that restarts or
    compacts gets a new session id: measured on 2026-09-22, the first real run produced two
    beats six minutes apart for pane w1T:p1, which the reader listed as two panes.

    A session outside a pane keeps its session id, since it has no pane to be confused with.
    """
    pane = (record.get("pane") or "").strip()
    return (pane.replace(":", "-") if pane else record["session_id"]) + ".json"


def write(record, directory=None):
    """Write one record, replacing the previous beat for that pane."""
    directory = Path(directory) if directory else DIR
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / beat_key(record)
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

    # The key is the pane, so a colon does not become a directory separator.
    assert beat_key(r) == "w1R-p8.json"
    assert beat_key({"session_id": "s", "pane": ""}) == "s.json"
    assert beat_key({"session_id": "s"}) == "s.json"

    with tempfile.TemporaryDirectory() as d:
        p = write(r, d)
        assert p.exists()
        assert json.loads(p.read_text())["pane"] == "w1R:p8"
        # A second beat replaces the first rather than accumulating.
        write(beat({"session_id": "abc"}, env, now=2000.0), d)
        assert json.loads(p.read_text())["at"] == 2000.0
        assert len(list(Path(d).glob("*.json"))) == 1
        assert not list(Path(d).glob("*.tmp"))

        # A new session in the same pane replaces the beat rather than adding one. This is the
        # defect the first real run exposed: a restart or a compaction changes the session id.
        write(beat({"session_id": "different"}, env, now=3000.0), d)
        assert len(list(Path(d).glob("*.json"))) == 1
        assert json.loads(p.read_text())["at"] == 3000.0

        # A session with no pane still gets its own file.
        write(beat({"session_id": "nopane"}, {}, now=4000.0), d)
        assert len(list(Path(d).glob("*.json"))) == 2

    # The master falls back to the registry when the variable is empty, which is what a restart
    # leaves behind.
    with tempfile.TemporaryDirectory() as d:
        Path(d, "w9-p9.json").write_text(json.dumps({"master": "lead"}))
        assert _master({"HERDR_PANE_ID": "w9:p9"}, d) == "lead"
        # The variable wins when it has a value.
        assert _master({"HERDR_PANE_ID": "w9:p9", "HERDR_AGENT_MASTER": "other"}, d) == "other"
        # A pane with no entry, and no pane at all, both read empty rather than raising.
        assert _master({"HERDR_PANE_ID": "w9:pZ"}, d) == ""
        assert _master({}, d) == ""
        # A master records an empty master and the registry does not override it.
        Path(d, "w9-p8.json").write_text(json.dumps({"master": ""}))
        assert _master({"HERDR_PANE_ID": "w9:p8"}, d) == ""
        # Malformed JSON is a missing answer, not a crash.
        Path(d, "w9-p7.json").write_text("{not json")
        assert _master({"HERDR_PANE_ID": "w9:p7"}, d) == ""

    # Location is best effort and never raises: a path that is not a repository, and one that
    # does not exist, both come back empty rather than failing the beat.
    assert where("") == {"repo": "", "branch": "", "worktree": False}
    assert where("/nonexistent/xyz")["repo"] == ""
    assert where("/tmp")["repo"] == ""

    # A real repository answers its own path and is not a worktree. This file lives in one, so
    # its own directory is the fixture and no path is written out.
    repo = str(Path(__file__).resolve().parents[5])
    here = where(repo)
    assert here["repo"] == repo, here
    assert here["worktree"] is False
    assert here["branch"]

    # The fields ride on the beat rather than being computed by the reader.
    r3 = beat({"session_id": "loc", "cwd": repo}, env)
    assert r3["repo"] == repo
    assert r3["worktree"] is False

    print("canary selftest: 33 checks passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
