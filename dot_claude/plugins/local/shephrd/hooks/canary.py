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


def _registry(env, registry_dir=None):
    """This pane's registry record, or an empty one.

    Importing `panes` is avoided: a hook that fails on a missing sibling stops writing beats,
    and a beat is what makes a stalled pane visible. The file is read directly and any failure
    gives empty fields, which is what the variables alone would have given.
    """
    pane = (env.get("HERDR_PANE_ID") or "").strip()
    if not pane:
        return {}
    d = Path(registry_dir) if registry_dir else Path(
        env.get("HOME", "/tmp")) / ".claude" / "panes"
    try:
        return json.loads((d / (pane.replace(":", "-") + ".json")).read_text())
    except (OSError, ValueError, AttributeError):
        return {}


def _identity(env, registry_dir=None):
    """This pane's name, who it reports to, and what role it holds.

    Every answer comes from the variable first and the registry behind it, because a restart
    empties the process and leaves the registry as the only record. All three fall back, not
    just the one that prompted the fallback: measured on 2026-09-23, a restarted pane wrote a
    beat with the role right and the name blank, because only two of the three read the file.

    The role rides on the beat rather than being inferred by a reader. A god is declared, not
    derived from having no one above it, and a reader that guessed would call every god a
    shephrd.

    The registry answers the role where it recorded one. Deriving it from `reports_to` reads a
    shephrd reporting to the god as a sheep, which `panes.py` fixed on 2026-09-23 and this
    writer kept for another day. Measured on 2026-09-23: pane `w1R:p1` is recorded `shephrd`
    with `os-master` above it, and the beat written for it carried `sheep`. `canary-read.py`
    already held this precedence, so the reader was correct about a field the writer spoiled.
    The derivation stays for a record written before the field existed.
    """
    rec = _registry(env, registry_dir)
    name = (env.get("HERDR_AGENT_NAME") or "").strip() or (rec.get("name") or "").strip()
    reports_to = (env.get("HERDR_REPORTS_TO") or "").strip() or (
        rec.get("reports_to") or "").strip()
    god = (env.get("HERDR_GOD") or "").strip().lower() not in ("", "0", "false", "no")
    god = god or bool(rec.get("god"))
    role = (rec.get("role") or "").strip().lower()
    if role not in ("god", "shephrd", "sheep", "watcher"):
        role = "god" if god else ("sheep" if reports_to else "shephrd")
    return name, reports_to, role


def beat(payload, env=None, now=None, registry_dir=None):
    """Build the record for one turn ending. Returns None when there is no session to name.

    `registry_dir` exists for the selftest. Without it the identity fields could only be checked
    against whatever the machine's own registry holds, so the beat's role went unverified while
    `_identity` had a test and the wrong value shipped anyway.
    """
    env = env if env is not None else os.environ
    now = now if now is not None else time.time()

    sid = (payload.get("session_id") or "").strip()
    if not sid:
        return None

    # The registry answers what the environment lost, for all three fields. A restarted pane has
    # none of the variables: measured on 2026-09-23, one wrote a beat with no name at all and an
    # earlier one listed a sheep as a shephrd.
    name, reports_to, role = _identity(env, registry_dir)

    return {
        "session_id": sid,
        "at": now,
        "at_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now)),
        "pane": (env.get("HERDR_PANE_ID") or "").strip(),
        "workspace": (env.get("HERDR_WORKSPACE_ID") or "").strip(),
        "name": name,
        "reports_to": reports_to,
        "role": role,
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
        "HERDR_REPORTS_TO": "lead",
    }
    r = beat({"session_id": "abc", "cwd": "/tmp/x", "hook_event_name": "Stop"}, env, now=1000.0)
    assert r["session_id"] == "abc"
    assert r["pane"] == "w1R:p8"
    assert r["reports_to"] == "lead"
    assert r["at"] == 1000.0

    # No session id means no record: a beat that cannot name its session identifies nothing.
    assert beat({}, env) is None
    assert beat({"session_id": "   "}, env) is None

    # A shephrd has no master and that is a value, not a missing field.
    r2 = beat({"session_id": "m"}, {}, now=1.0)
    assert r2["reports_to"] == ""
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

    # A restart empties every variable, so all three come from the registry together. The name
    # was the one that did not, and a restarted pane wrote a beat with no name at all.
    with tempfile.TemporaryDirectory() as d:
        Path(d, "w5-p5.json").write_text(json.dumps(
            {"name": "herder-c", "reports_to": "", "god": False}))
        assert _identity({"HERDR_PANE_ID": "w5:p5"}, d) == ("herder-c", "", "shephrd")
        # The variable still wins where it has a value.
        assert _identity(
            {"HERDR_PANE_ID": "w5:p5", "HERDR_AGENT_NAME": "renamed"}, d)[0] == "renamed"

    # The recipient falls back to the registry when the variable is empty, which is what a restart
    # leaves behind.
    with tempfile.TemporaryDirectory() as d:
        Path(d, "w9-p9.json").write_text(json.dumps({"reports_to": "lead"}))
        assert _identity({"HERDR_PANE_ID": "w9:p9"}, d)[1] == "lead"
        # The variable wins when it has a value.
        assert _identity({"HERDR_PANE_ID": "w9:p9", "HERDR_REPORTS_TO": "other"}, d)[1] == "other"
        # A pane with no entry, and no pane at all, both read empty rather than raising.
        assert _identity({"HERDR_PANE_ID": "w9:pZ"}, d)[1] == ""
        assert _identity({}, d)[1] == ""
        # A shephrd records an empty master and the registry does not override it.
        Path(d, "w9-p8.json").write_text(json.dumps({"reports_to": ""}))
        assert _identity({"HERDR_PANE_ID": "w9:p8"}, d)[1] == ""
        # Malformed JSON is a missing answer, not a crash.
        Path(d, "w9-p7.json").write_text("{not json")
        assert _identity({"HERDR_PANE_ID": "w9:p7"}, d)[1] == ""

    # The recorded role wins over the derivation, which is the whole case: a shephrd reporting
    # to the god derives as a sheep and is recorded as a shephrd. Every row here disagrees with
    # what the derivation would produce, so a writer that dropped back to it fails all of them.
    with tempfile.TemporaryDirectory() as d:
        Path(d, "w2-p1.json").write_text(json.dumps(
            {"name": "tree-a", "reports_to": "os-master", "role": "shephrd"}))
        assert _identity({"HERDR_PANE_ID": "w2:p1"}, d) == ("tree-a", "os-master", "shephrd")
        # The variables being present changes nothing: the role has no variable to win with.
        assert _identity({"HERDR_PANE_ID": "w2:p1", "HERDR_AGENT_NAME": "tree-a",
                          "HERDR_REPORTS_TO": "os-master"}, d)[2] == "shephrd"
        # A watcher has someone above it and is not a sheep.
        Path(d, "w2-p2.json").write_text(json.dumps(
            {"name": "notes", "reports_to": "os-master", "role": "watcher"}))
        assert _identity({"HERDR_PANE_ID": "w2:p2"}, d)[2] == "watcher"
        # A god is recorded as one even with nothing in the flag.
        Path(d, "w2-p3.json").write_text(json.dumps(
            {"name": "os-master", "reports_to": "", "god": False, "role": "god"}))
        assert _identity({"HERDR_PANE_ID": "w2:p3"}, d)[2] == "god"
        # A sheep recorded with no one above it keeps what was recorded.
        Path(d, "w2-p4.json").write_text(json.dumps(
            {"name": "orphan", "reports_to": "", "role": "sheep"}))
        assert _identity({"HERDR_PANE_ID": "w2:p4"}, d)[2] == "sheep"
        # A record written before the field existed, and one with a value that is not a role,
        # both fall back to the derivation.
        Path(d, "w2-p5.json").write_text(json.dumps({"name": "old", "reports_to": "lead"}))
        assert _identity({"HERDR_PANE_ID": "w2:p5"}, d)[2] == "sheep"
        Path(d, "w2-p6.json").write_text(json.dumps(
            {"name": "bad", "reports_to": "", "role": "nonsense"}))
        assert _identity({"HERDR_PANE_ID": "w2:p6"}, d)[2] == "shephrd"
        # The flag still decides where no role was recorded.
        Path(d, "w2-p7.json").write_text(json.dumps({"name": "g", "reports_to": "", "god": True}))
        assert _identity({"HERDR_PANE_ID": "w2:p7"}, d)[2] == "god"
        # And the role rides onto the beat rather than stopping at _identity, which is the path
        # the hook actually runs. The written beat is what a reader consults.
        r4 = beat({"session_id": "role"}, {"HERDR_PANE_ID": "w2:p1"}, now=1.0, registry_dir=d)
        assert r4["role"] == "shephrd", r4
        assert r4["reports_to"] == "os-master"
        with tempfile.TemporaryDirectory() as out:
            assert json.loads(write(r4, out).read_text())["role"] == "shephrd"

    # Location is best effort and never raises: a path that is not a repository, and one that
    # does not exist, both come back empty rather than failing the beat.
    assert where("") == {"repo": "", "branch": "", "worktree": False}
    assert where("/nonexistent/xyz")["repo"] == ""
    assert where("/tmp")["repo"] == ""

    # A real repository answers its own path and is not a worktree. The fixture is built rather
    # than assumed from this file's location: the installed copy lives outside any repository,
    # where deriving one gave an empty reading and failed a test that was measuring nothing.
    with tempfile.TemporaryDirectory() as d:
        repo = str(Path(d).resolve())
        for cmd in (["init", "-q"], ["config", "user.email", "t@e"], ["config", "user.name", "t"]):
            subprocess.run(["git", "-C", repo] + cmd, capture_output=True, timeout=10)
        Path(repo, "f").write_text("x")
        subprocess.run(["git", "-C", repo, "add", "f"], capture_output=True, timeout=10)
        subprocess.run(["git", "-C", repo, "commit", "-qm", "init"], capture_output=True, timeout=10)

        here = where(repo)
        assert here["repo"] == repo, here
        assert here["worktree"] is False
        assert here["branch"]

        # The fields ride on the beat rather than being computed by the reader.
        r3 = beat({"session_id": "loc", "cwd": repo}, env)
        assert r3["repo"] == repo
        assert r3["worktree"] is False

    print("canary selftest: 46 checks passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
