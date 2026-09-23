#!/usr/bin/env python3
"""Who a pane answers to, kept outside the process that forgets it.

`/spawn-agent` passes `HERDR_AGENT_NAME` and `HERDR_AGENT_MASTER` with `--env` at split time,
and those live in the pane's process. A restart replaces that process: `herdr agent start` takes
no `--env` and creates no pane, so the variables are gone and the session reads as a master.
Measured on 2026-09-23: two panes restarted with their threads intact came back with both empty,
and the canary listed a sheep as a master.

So the spawn also writes the pair to `~/.claude/panes/<pane>.json`, which survives the process.
A session with an empty variable reads the file for its own pane before concluding it
coordinates itself.

The file carries a third field the environment never had: what the pane may touch. A directory
does not say it, and on 2026-09-23 four panes sat on one repository and three were nested inside
each other with nothing distinguishing their work. Nothing enforces it; it is what a session
reads to know whether a file it is about to change belongs to someone else.

The file is a record of what a spawn declared, not an authority. A pane whose environment says
one thing and whose file says another trusts the environment: the variable was set by the spawn
that is running now, and the file may describe a pane that was reused for something else.

The canary's beat cannot serve as this record, though it carries the same two fields. A beat
reports what the process holds at the end of a turn, so a restarted pane overwrites it with the
empty values it lost: measured on 2026-09-23, `w1R-p8` reported a name and an empty master while
that pane was a sheep. The registry is written once by the spawn and is not touched by a restart.
Two files, two owners.
"""

import json
import os
import sys
from pathlib import Path

DIR = Path(os.environ.get("HOME", "/tmp")) / ".claude" / "panes"

USAGE = (
    "usage:\n"
    "  panes.py                                          resolve this session's identity\n"
    "  panes.py --write <pane> <name> [master] [scope]   record one pane\n"
    "  panes.py --write <pane> <name> \"\" <scope> --god  record the session the user watches\n"
    "\n"
    "Every argument after --write is positional except --god, which is a flag. Scope is the\n"
    "rest of the line, unquoted or quoted, and takes no flag of its own."
)


def key(pane):
    """A pane id as a file name. The colon is not a path separator anywhere it lands."""
    return (pane or "").strip().replace(":", "-") + ".json"


def truthy(value):
    """Whether a flag string means yes. Empty, `0`, `false` and `no` mean no."""
    return (value or "").strip().lower() not in ("", "0", "false", "no")


def role_of(master, god=False):
    """One of `god`, `shepherd` or `sheep`.

    A sheep answers to a master. A shepherd answers to nobody and herds sheep.

    A god is the session the user watches, and the only one they watch when everything runs
    unattended and they are reading from a phone. It is declared rather than inferred: a
    shepherd with no sheep yet is indistinguishable from outside, and reading the role wrong
    here decides whether a question reaches the user at all.

    What makes it work is what does not reach it. Every shepherd gates before sending, so a god
    sees decisions only the user can take, a tree that is blocked, a milestone that landed, and a
    command needing elevation. A shepherd that forwards everything turns the one window into
    noise, which is the failure this role is built to avoid.
    """
    if god:
        return "god"
    return "sheep" if (master or "").strip() else "shepherd"


def write(pane, name, master, scope=None, god=False, directory=None):
    """Record what a spawn declared for one pane. Returns the path, or None with no pane.

    `scope` is what this pane may touch, which a directory does not say: four panes sat on one
    repository on 2026-09-23 with nothing distinguishing their work. It is free text, since the
    unit varies between a path, a subtree and a branch, and it is for a human or a session to
    read rather than for anything to enforce.
    """
    pane = (pane or "").strip()
    if not pane:
        return None
    directory = Path(directory) if directory else DIR
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / key(pane)
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({
        "pane": pane,
        "name": (name or "").strip(),
        "master": (master or "").strip(),
        "scope": (scope or "").strip(),
        "god": bool(god),
    }))
    tmp.replace(target)
    return target


def read(pane, directory=None):
    """What was recorded for a pane. Empty fields when nothing was, or the file is unreadable."""
    blank = {"pane": (pane or "").strip(), "name": "", "master": "", "scope": "",
             "god": False}
    pane = (pane or "").strip()
    if not pane:
        return blank
    directory = Path(directory) if directory else DIR
    f = directory / key(pane)
    try:
        d = json.loads(f.read_text())
    except (OSError, ValueError):
        return blank
    return {
        "pane": d.get("pane") or pane,
        "name": (d.get("name") or "").strip(),
        "master": (d.get("master") or "").strip(),
        "scope": (d.get("scope") or "").strip(),
        "god": bool(d.get("god")),
    }


def resolve(env=None, directory=None):
    """The identity this session should act on.

    The environment wins where it has a value, since it was set by the spawn now running. The
    file answers only what the environment left empty, which is what a restart produces.
    """
    env = env if env is not None else os.environ
    pane = (env.get("HERDR_PANE_ID") or "").strip()
    name = (env.get("HERDR_AGENT_NAME") or "").strip()
    master = (env.get("HERDR_AGENT_MASTER") or "").strip()
    source = "env"
    scope = ""

    god = truthy(env.get("HERDR_GOD"))

    if pane:
        rec = read(pane, directory)
        # Scope has no environment variable: the registry is where it lives at all.
        scope = rec["scope"]
        if not name and rec["name"]:
            name, source = rec["name"], "registry"
        if not master and rec["master"]:
            master, source = rec["master"], "registry"
        # The flag lives in the process and a restart empties it, so the registry answers for it
        # exactly as it does for the master.
        god = god or rec["god"]

    return {
        "pane": pane,
        "name": name,
        "master": master,
        "scope": scope,
        "god": god,
        "role": role_of(master, god),
        "source": source,
    }


def main(argv=None):
    """`--write <pane> <name> [master] [scope]` records one; no arguments resolves this session."""
    argv = list(sys.argv[1:] if argv is None else argv)

    # An unknown flag used to fall through to the read branch, which printed this pane's record
    # and looked like success: measured on 2026-09-23, a caller passing `--scope "<text>"` after
    # the positional arguments lost a turn to that. Every argument is positional after `--write`,
    # and anything else is refused with the usage line.
    if "--help" in argv or "-h" in argv:
        print(USAGE)
        return 0
    unknown = [a for a in argv
               if a.startswith("-") and a not in ("--write", "--selftest", "--god")]
    if unknown:
        print(f"unknown argument: {unknown[0]}\n{USAGE}", file=sys.stderr)
        return 2

    if "--write" in argv:
        god = "--god" in argv
        rest = [a for a in argv[argv.index("--write") + 1:] if a != "--god"]
        if not rest:
            print(USAGE, file=sys.stderr)
            return 2
        pane = rest[0]
        name = rest[1] if len(rest) > 1 else ""
        master = rest[2] if len(rest) > 2 else ""
        scope = " ".join(rest[3:]) if len(rest) > 3 else ""
        target = write(pane, name, master, scope, god)
        if target is None:
            print("no pane given", file=sys.stderr)
            return 2
        print(target)
        return 0
    print(json.dumps(resolve(), indent=2))
    return 0


def selftest():
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        assert key("w1R:p8") == "w1R-p8.json"
        assert write("", "n", "m", directory=d) is None

        p = write("w1R:p8", "worker-a", "lead", directory=d)
        assert p.exists()
        assert read("w1R:p8", d)["master"] == "lead"
        assert read("w1R:p8", d)["name"] == "worker-a"

        # A pane never recorded, and an unreadable file, both read as empty.
        assert read("w9:p9", d)["master"] == ""
        assert read("", d)["master"] == ""

        # A restart: the pane id survives, the two names do not.
        r = resolve({"HERDR_PANE_ID": "w1R:p8"}, d)
        assert r["master"] == "lead", r
        assert r["name"] == "worker-a"
        assert r["source"] == "registry"

        # The environment wins where it has a value.
        r2 = resolve({
            "HERDR_PANE_ID": "w1R:p8",
            "HERDR_AGENT_NAME": "renamed",
            "HERDR_AGENT_MASTER": "other",
        }, d)
        assert r2["master"] == "other", r2
        assert r2["name"] == "renamed"
        assert r2["source"] == "env"

        # A master records an empty master, and that stays empty rather than being filled in.
        write("w1T:p1", "os-master", "", directory=d)
        assert resolve({"HERDR_PANE_ID": "w1T:p1"}, d)["master"] == ""

        # No pane at all: nothing to look up.
        assert resolve({}, d)["pane"] == ""
        assert resolve({})["source"] == "env"

    with tempfile.TemporaryDirectory() as d:
        # Scope rides with the pane and survives a restart, since no variable carries it.
        write("w1R:p9", "pr-reviewer", "lead", "read-only: the four PR bodies", directory=d)
        assert read("w1R:p9", d)["scope"] == "read-only: the four PR bodies"
        r = resolve({"HERDR_PANE_ID": "w1R:p9"}, d)
        assert r["scope"] == "read-only: the four PR bodies", r
        assert r["master"] == "lead"

        # A pane recorded without one has no scope rather than a missing key.
        write("w1T:p6", "worker", "lead", None, directory=d)
        assert read("w1T:p6", d)["scope"] == ""
        # Scope is read even when the environment supplies both names.
        full = resolve({
            "HERDR_PANE_ID": "w1R:p9",
            "HERDR_AGENT_NAME": "pr-reviewer",
            "HERDR_AGENT_MASTER": "lead",
        }, d)
        assert full["scope"] == "read-only: the four PR bodies", full
        assert full["source"] == "env"

    # The write path the spawn calls, checked for its argument handling rather than its target.
    assert main(["--write"]) == 2
    assert main(["--write", ""]) == 2

    # The three roles, from the two things that decide them.
    assert role_of("") == "shepherd"
    assert role_of("lead") == "sheep"
    assert role_of("", god=True) == "god"
    # A god with a master is a contradiction the flag wins, since only a spawn sets a master and
    # only the user declares a god.
    assert role_of("lead", god=True) == "god"

    assert truthy("1") is True
    assert truthy("") is False
    assert truthy("false") is False
    assert truthy("  no  ") is False

    with tempfile.TemporaryDirectory() as d:
        # The flag survives a restart the same way the master does.
        write("w1T:p1", "os-master", "", "dotfiles", god=True, directory=d)
        assert read("w1T:p1", d)["god"] is True
        r = resolve({"HERDR_PANE_ID": "w1T:p1"}, d)
        assert r["role"] == "god", r
        # The environment declares one where the registry has no entry at all.
        assert resolve({"HERDR_PANE_ID": "w9:p9", "HERDR_GOD": "1"}, d)["role"] == "god"
        # And a pane recorded without it stays a shepherd.
        write("w1R:p1", "herder-b", "", "one tree", directory=d)
        assert resolve({"HERDR_PANE_ID": "w1R:p1"}, d)["role"] == "shepherd"

    # An unknown flag is refused rather than falling through to the read branch, which printed a
    # record and looked like success.
    assert main(["--scope", "x"]) == 2
    assert main(["--write", "w:p", "n", "m", "--scope", "x"]) == 2
    assert main(["--help"]) == 0
    assert main(["-h"]) == 0

    print("panes selftest: 43 checks passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(main())
