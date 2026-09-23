#!/usr/bin/env python3
"""Who a pane answers to, kept outside the process that forgets it.

The spawn commands pass `HERDR_AGENT_NAME` and `HERDR_REPORTS_TO` with `--env` at split time,
and those live in the pane's process. A restart replaces that process: `herdr agent start` takes
no `--env` and creates no pane, so the variables are gone and the session reads as a shephrd.
Measured: two panes restarted with their threads intact came back with both empty,
and the canary listed a sheep as a shephrd.

So the spawn also writes the pair to `~/.claude/panes/<pane>.json`, which survives the process.
A session with an empty variable reads the file for its own pane before concluding it
coordinates itself.

The file carries a third field the environment never had: what the pane may touch. A directory
does not say it, and  four panes sat on one repository and three were nested inside
each other with nothing distinguishing their work. Nothing enforces it; it is what a session
reads to know whether a file it is about to change belongs to someone else.

The file is a record of what a spawn declared, not an authority. A pane whose environment says
one thing and whose file says another trusts the environment: the variable was set by the spawn
that is running now, and the file may describe a pane that was reused for something else.

The canary's beat cannot serve as this record, though it carries the same two fields. A beat
reports what the process holds at the end of a turn, so a restarted pane overwrites it with the
empty values it lost: Measured: `wA-p8` reported a name and an empty recipient while
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
    "  panes.py --write <pane> <name> [reports-to] [scope] [--scope S] [--role R] [--god]\n"
    "  panes.py --attended <pane>                        render menus in this pane\n"
    "  panes.py --unattended <pane>                      redirect them to the shephrd\n"
    "\n"
    "Scope is the rest of the line after reports-to, or the value of --scope. --role takes god, shephrd, sheep or\n"
    "watcher and is what the resolver trusts; without it the role is derived from reports-to,\n"
    "which reads a shephrd reporting to a god as a sheep.\n"
    "\n"
    "--attended marks a pane somebody is sitting in front of, so ask-gate.py renders its\n"
    "questions there instead of redirecting them. It edits one field of an existing record;\n"
    "--write replaces the whole record and clears it."
)


def key(pane):
    """A pane id as a file name. The colon is not a path separator anywhere it lands."""
    return (pane or "").strip().replace(":", "-") + ".json"


def truthy(value):
    """Whether a flag string means yes. Empty, `0`, `false` and `no` mean no."""
    return (value or "").strip().lower() not in ("", "0", "false", "no")


def role_of(reports_to, god=False, declared=""):
    """The role, declared where it was recorded and derived only where it was not.

    Deriving it from `reports_to` alone collapses two different facts. A shephrd reports to the
    god and is not a sheep for doing so: Measured: a shephrd recorded with the god
    as its recipient read back as a sheep, and the same reading would have called it a shephrd
    had the field been left empty, which is the other half wrong.

    So a spawn says which it opened. The derivation stays for a pane recorded before the field
    existed, where `reports_to` is still the only evidence there is.
    """
    declared = (declared or "").strip().lower()
    if declared in ("god", "shephrd", "sheep", "watcher"):
        return declared
    return _derive_role(reports_to, god)


def _derive_role(reports_to, god=False):
    """The role a pane's recipient implies, for a record that declares none.

    A pane with someone above it reads as a sheep and one without as a shephrd, which is right
    for every pane opened before the role was recorded and wrong for a shephrd that reports to a
    god. That is what the declared role fixes; this is the fallback.

    A god is the session the user watches, and the only one they watch when everything runs
    unattended and they are reading from a phone. It is declared rather than inferred: a
    shephrd with no sheep yet is indistinguishable from outside, and reading the role wrong
    here decides whether a question reaches the user at all.

    What makes it work is what does not reach it. Every shephrd gates before sending, so a god
    sees decisions only the user can take, a tree that is blocked, a milestone that landed, and a
    command needing elevation. A shephrd that forwards everything turns the one window into
    noise, which is the failure this role is built to avoid.
    """
    if god:
        return "god"
    return "sheep" if (reports_to or "").strip() else "shephrd"


def write(pane, name, reports_to, scope=None, god=False, role="", directory=None):
    """Record what a spawn declared for one pane. Returns the path, or None with no pane.

    `scope` is what this pane may touch, which a directory does not say: four panes sat on one
    repository  with nothing distinguishing their work. It is free text, since the
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
        "reports_to": (reports_to or "").strip(),
        "scope": (scope or "").strip(),
        "god": bool(god),
        "role": (role or "").strip().lower(),
    }))
    tmp.replace(target)
    return target


def set_attended(pane, value, directory=None):
    """Turn the `attended` flag on or off, leaving the rest of the record alone.

    It is its own entry point rather than a parameter of `write` because `write` replaces the
    whole record: a spawn passing no flag would clear a pane the user had marked, and a pane is
    marked long after it was spawned. Returns the path, or None when nothing was recorded.

    What the flag means: somebody is sitting in front of this pane and wants a menu rendered
    here. `ask-gate.py` redirects a sheep's question to its shephrd, which is the right default
    because nobody is watching, and this is the record of the case where that is untrue.
    """
    pane = (pane or "").strip()
    if not pane:
        return None
    directory = Path(directory) if directory else DIR
    target = directory / key(pane)
    try:
        rec = json.loads(target.read_text())
    except (OSError, ValueError):
        return None
    rec["attended"] = bool(value)
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rec))
    tmp.replace(target)
    return target


def read(pane, directory=None):
    """What was recorded for a pane. Empty fields when nothing was, or the file is unreadable."""
    blank = {"pane": (pane or "").strip(), "name": "", "reports_to": "", "scope": "",
             "god": False, "role": "", "attended": False}
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
        "reports_to": (d.get("reports_to") or "").strip(),
        "scope": (d.get("scope") or "").strip(),
        "god": bool(d.get("god")),
        "role": (d.get("role") or "").strip().lower(),
        # Written by `set_attended` and read by `ask-gate.py` straight from the file. It is
        # reported here too because a session asking this module what it is would otherwise be
        # told its role and not that the flag had released it from the redirection.
        "attended": bool(d.get("attended")),
    }


def resolve(env=None, directory=None):
    """The identity this session should act on.

    The environment wins where it has a value, since it was set by the spawn now running. The
    file answers only what the environment left empty, which is what a restart produces.
    """
    env = env if env is not None else os.environ
    pane = (env.get("HERDR_PANE_ID") or "").strip()
    name = (env.get("HERDR_AGENT_NAME") or "").strip()
    reports_to = (env.get("HERDR_REPORTS_TO") or "").strip()
    source = "env"
    scope = ""

    god = truthy(env.get("HERDR_GOD"))
    rec = {"role": ""}

    if pane:
        rec = read(pane, directory)
        # Scope has no environment variable: the registry is where it lives at all.
        scope = rec["scope"]
        if not name and rec["name"]:
            name, source = rec["name"], "registry"
        if not reports_to and rec["reports_to"]:
            reports_to, source = rec["reports_to"], "registry"
        # The flag lives in the process and a restart empties it, so the registry answers for it
        # exactly as it does for the reports_to.
        god = god or rec["god"]

    return {
        "pane": pane,
        "name": name,
        "reports_to": reports_to,
        "scope": scope,
        "god": god,
        "role": role_of(reports_to, god, rec.get("role", "")),
        # No environment variable carries this: the record is the only place it lives, so a
        # session with no pane reads as unattended, which is the default the gate assumes.
        "attended": bool(rec.get("attended")),
        "source": source,
    }


def _take(args, flag):
    """The value after `flag` and the arguments without the pair. Empty when the flag is absent."""
    if flag not in args:
        return "", args
    i = args.index(flag)
    value = args[i + 1] if i + 1 < len(args) else ""
    return value, args[:i] + args[i + 2:]


def main(argv=None):
    """`--write <pane> <name> [reports_to] [scope]` records one; no arguments resolves this session."""
    argv = list(sys.argv[1:] if argv is None else argv)

    # An unknown flag used to fall through to the read branch, which printed this pane's record
    # and looked like success: Measured: a caller passing `--scope "<text>"` after
    # the positional arguments lost a turn to that. Every argument is positional after `--write`,
    # and anything else is refused with the usage line.
    if "--help" in argv or "-h" in argv:
        print(USAGE)
        return 0
    unknown = [a for a in argv
               if a.startswith("-") and a not in ("--write", "--selftest", "--god", "--role",
                                                  "--scope", "--attended", "--unattended")]
    if unknown:
        print(f"unknown argument: {unknown[0]}\n{USAGE}", file=sys.stderr)
        return 2

    if "--attended" in argv or "--unattended" in argv:
        flag = "--attended" in argv
        rest = [a for a in argv if a not in ("--attended", "--unattended")]
        if not rest:
            print(USAGE, file=sys.stderr)
            return 2
        target = set_attended(rest[0], flag)
        if target is None:
            print(f"no record for pane: {rest[0]}", file=sys.stderr)
            return 2
        print(target)
        return 0

    if "--write" in argv:
        god = "--god" in argv
        rest = [a for a in argv[argv.index("--write") + 1:] if a != "--god"]
        role, rest = _take(rest, "--role")
        # `--scope` is the spelling callers reach for. It was once joined into the positional
        # scope as a literal: measured, `--write w9Z:p1 tester boss --scope "read-only"` recorded
        # `"--scope read-only"`. Taking it as a flag removes the only wrong form anyone wrote.
        scope_flag, rest = _take(rest, "--scope")
        if not rest:
            print(USAGE, file=sys.stderr)
            return 2
        pane = rest[0]
        name = rest[1] if len(rest) > 1 else ""
        reports_to = rest[2] if len(rest) > 2 else ""
        scope = scope_flag or (" ".join(rest[3:]) if len(rest) > 3 else "")
        target = write(pane, name, reports_to, scope, god, role)
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
        assert key("wA:p8") == "wA-p8.json"
        assert write("", "n", "m", directory=d) is None

        p = write("wA:p8", "worker-a", "lead", directory=d)
        assert p.exists()
        assert read("wA:p8", d)["reports_to"] == "lead"
        assert read("wA:p8", d)["name"] == "worker-a"

        # A pane never recorded, and an unreadable file, both read as empty.
        assert read("w9:p9", d)["reports_to"] == ""
        assert read("", d)["reports_to"] == ""

        # A restart: the pane id survives, the two names do not.
        r = resolve({"HERDR_PANE_ID": "wA:p8"}, d)
        assert r["reports_to"] == "lead", r
        assert r["name"] == "worker-a"
        assert r["source"] == "registry"

        # The environment wins where it has a value.
        r2 = resolve({
            "HERDR_PANE_ID": "wA:p8",
            "HERDR_AGENT_NAME": "renamed",
            "HERDR_REPORTS_TO": "other",
        }, d)
        assert r2["reports_to"] == "other", r2
        assert r2["name"] == "renamed"
        assert r2["source"] == "env"

        # A reports_to records an empty reports_to, and that stays empty rather than being filled in.
        write("wB:p1", "os-reports_to", "", directory=d)
        assert resolve({"HERDR_PANE_ID": "wB:p1"}, d)["reports_to"] == ""

        # No pane at all: nothing to look up.
        assert resolve({}, d)["pane"] == ""
        assert resolve({})["source"] == "env"

    with tempfile.TemporaryDirectory() as d:
        # Scope rides with the pane and survives a restart, since no variable carries it.
        write("wA:p9", "reviewer", "lead", "read-only: four PR bodies", directory=d)
        assert read("wA:p9", d)["scope"] == "read-only: four PR bodies"
        r = resolve({"HERDR_PANE_ID": "wA:p9"}, d)
        assert r["scope"] == "read-only: four PR bodies", r
        assert r["reports_to"] == "lead"

        # A pane recorded without one has no scope rather than a missing key.
        write("wB:p6", "worker", "lead", None, directory=d)
        assert read("wB:p6", d)["scope"] == ""
        # Scope is read even when the environment supplies both names.
        full = resolve({
            "HERDR_PANE_ID": "wA:p9",
            "HERDR_AGENT_NAME": "reviewer",
            "HERDR_REPORTS_TO": "lead",
        }, d)
        assert full["scope"] == "read-only: four PR bodies", full
        assert full["source"] == "env"

    # The write path the spawn calls, checked for its argument handling rather than its target.
    assert main(["--write"]) == 2
    assert main(["--write", ""]) == 2

    # A declared role wins over the derivation, which is what a shephrd reporting to a god needs.
    assert role_of("god", declared="shephrd") == "shephrd"
    assert role_of("", declared="watcher") == "watcher"
    # An unknown or empty declaration falls through to the derivation.
    assert role_of("lead", declared="") == "sheep"
    assert role_of("lead", declared="nonsense") == "sheep"
    assert role_of("", declared="  GOD  ") == "god"

    with tempfile.TemporaryDirectory() as d:
        write("w2:p1", "tree-a", "god", "one tree", role="shephrd", directory=d)
        assert read("w2:p1", d)["role"] == "shephrd"
        r = resolve({"HERDR_PANE_ID": "w2:p1"}, d)
        assert r["role"] == "shephrd", r
        assert r["reports_to"] == "god"
        # A record written before the field existed still resolves by derivation.
        write("w2:p2", "worker", "tree-a", "", directory=d)
        assert resolve({"HERDR_PANE_ID": "w2:p2"}, d)["role"] == "sheep"

    # The three roles, from the two things that decide them.
    assert role_of("") == "shephrd"
    assert role_of("lead") == "sheep"
    assert role_of("", god=True) == "god"
    # A god with a reports_to is a contradiction the flag wins, since only a spawn sets a reports_to and
    # only the user declares a god.
    assert role_of("lead", god=True) == "god"

    assert truthy("1") is True
    assert truthy("") is False
    assert truthy("false") is False
    assert truthy("  no  ") is False

    with tempfile.TemporaryDirectory() as d:
        # The flag survives a restart the same way the reports_to does.
        write("wB:p1", "os-reports_to", "", "dotfiles", god=True, directory=d)
        assert read("wB:p1", d)["god"] is True
        r = resolve({"HERDR_PANE_ID": "wB:p1"}, d)
        assert r["role"] == "god", r
        # The environment declares one where the registry has no entry at all.
        assert resolve({"HERDR_PANE_ID": "w9:p9", "HERDR_GOD": "1"}, d)["role"] == "god"
        # And a pane recorded without it stays a shephrd.
        write("wA:p1", "herder-b", "", "one tree", directory=d)
        assert resolve({"HERDR_PANE_ID": "wA:p1"}, d)["role"] == "shephrd"

        # `attended` is written on its own and leaves the rest of the record standing.
        write("w8:p1", "worker", "lead", "one path", role="sheep", directory=d)
        assert json.loads(Path(d, key("w8:p1")).read_text()).get("attended") is None
        assert set_attended("w8:p1", True, d) is not None
        rec = json.loads(Path(d, key("w8:p1")).read_text())
        assert rec["attended"] is True, rec
        assert rec["name"] == "worker" and rec["role"] == "sheep" and rec["scope"] == "one path"
        assert set_attended("w8:p1", False, d) is not None
        assert json.loads(Path(d, key("w8:p1")).read_text())["attended"] is False
        # A pane with no record cannot be marked: there is nothing to edit one field of.
        assert set_attended("w8:pZ", True, d) is None
        assert set_attended("", True, d) is None
        # `--write` replaces the record, so a mark set earlier is gone after one.
        set_attended("w8:p1", True, d)
        write("w8:p1", "worker", "lead", "one path", role="sheep", directory=d)
        assert json.loads(Path(d, key("w8:p1")).read_text()).get("attended") is None

        # The flag is reported, not only written. `ask-gate.py` reads the file directly, so a
        # session asking this module what it is was told its role and not that it had been
        # released from the redirection.
        set_attended("w8:p1", True, d)
        assert read("w8:p1", d)["attended"] is True
        assert resolve({"HERDR_PANE_ID": "w8:p1"}, d)["attended"] is True
        set_attended("w8:p1", False, d)
        assert read("w8:p1", d)["attended"] is False
        assert resolve({"HERDR_PANE_ID": "w8:p1"}, d)["attended"] is False
        # A record written before the field existed, and a session with no pane at all, both
        # read as unattended: the gate's default is what an absent flag means.
        write("w8:p2", "old", "lead", "one path", role="sheep", directory=d)
        assert read("w8:p2", d)["attended"] is False
        assert read("w8:pZ", d)["attended"] is False
        assert resolve({}, d)["attended"] is False

    # An unknown flag is refused rather than falling through to the read branch, which printed a
    # record and looked like success.
    assert main(["--bogus", "x"]) == 2
    # `--scope` is a flag of `--write`, in either position, and never lands in the value.
    global DIR
    saved = DIR
    with tempfile.TemporaryDirectory() as d:
        DIR = Path(d)
        try:
            assert main(["--write", "w:p", "n", "m", "--scope", "read-only: x"]) == 0
            assert read("w:p", d)["scope"] == "read-only: x", read("w:p", d)
            assert main(["--write", "w:q", "n", "m", "--scope", "a b", "--role", "sheep"]) == 0
            assert read("w:q", d)["scope"] == "a b" and read("w:q", d)["role"] == "sheep"
            assert main(["--write", "w:r", "n", "m", "positional", "scope"]) == 0
            assert read("w:r", d)["scope"] == "positional scope"
        finally:
            DIR = saved
    assert main(["--help"]) == 0
    assert main(["-h"]) == 0
    # The two new flags are known, and a pane with no record is an error rather than a silent
    # success: the mark has nothing to attach to.
    assert main(["--attended"]) == 2
    assert main(["--attended", "wZ:pZ"]) == 2

    print("panes selftest passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(main())
