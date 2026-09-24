#!/usr/bin/env python3
"""PreToolUse(Bash): marking a pane attended is the user's call, not the pane's.

`attended: true` in `~/.claude/panes/<pane>.json` releases that pane from `ask-gate.py`, which
otherwise redirects a sheep's questions to its shephrd. `panes.py --attended <pane>` writes the
flag, and a session can run it against its own pane: measured on 2026-09-23, a sheep ran it to
find out whether the feature existed and ungated itself in one command, with nothing recording
that it had.

A gate the gated thing can switch off is not a gate. `ask` returns the decision to the user,
who is the only one who knows whether somebody is sitting in front of that pane, which is the
entire claim the flag makes.

The hole this does not close: a session with `Bash` can edit the registry file directly, or edit
`ask-gate.py`. `file-protection.py` and `gate-skill-writes.py` cover the second; the first is
one `python3 -c` away and nothing here reaches it. What this stops is the supported path being
a bypass, not a determined session.

`--unattended` passes. Putting a pane back under the gate needs no permission, and asking for it
would make the safe direction the expensive one.

Self-check: python3 gate-attended.py --selftest
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hookaudit import record
except ImportError:
    def record(*_a, **_k):
        return False

# The same anchor the other Bash gates use: a command runs when it opens the line or a segment,
# so the name inside a quoted argument or in prose does not match.
SEGMENT = r"(?:^|[;&|\"']|\$\(|\n)\s*"

# `panes.py --attended <pane>`, however the script is reached: by path, through `python3`, or
# from a plugin directory that a future move renames. `--unattended` is deliberately not here.
#
# The pane argument is required rather than decorative. The anchor accepts a quote as a segment
# start, which is what lets `bash -c "python3 panes.py --attended w1:p2"` match, and prose quoted
# inside a message is indistinguishable from it up to the flag. A pane id after the flag is what
# a real invocation carries and a sentence about the flag does not.
ATTENDED = re.compile(
    SEGMENT + r"(?:python3?\s+)?\S*panes\.py\b[^|;&\n]*\s--attended\s+\S*\w+[:-]p?\d")

REASON = (
    "Marking a pane attended is the user's decision.\n\n"
    "`attended: true` releases that pane from `ask-gate.py`, so its questions render on its own "
    "screen instead of going to its shephrd. The claim the flag makes is that somebody is "
    "sitting in front of that pane, which only the user knows.\n\n"
    "A session marking its own pane would be switching off the gate that governs it. "
    "`--unattended` needs no permission and runs unprompted."
)


def hits(command):
    return bool(ATTENDED.search(command or ""))


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    command = (event.get("tool_input") or {}).get("command") or ""
    if not hits(command):
        return 0
    record("gate-attended", "ask", command)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": REASON,
    }}))
    return 0


def selftest():
    flagged = [
        "python3 ~/.claude/plugins/local/shephrd/hooks/panes.py --attended w1:p2",
        "python3 panes.py --attended w1:p2",
        "~/.claude/plugins/local/shephrd/hooks/panes.py --attended w1:p2",
        "cd /x && python3 panes.py --attended w1:p2",
        "python panes.py --attended w1:p2",
        'bash -c "python3 panes.py --attended w1:p2"',
    ]
    clean = [
        # Putting a pane back under the gate is free.
        "python3 panes.py --unattended w1:p2",
        "python3 ~/.claude/plugins/local/shephrd/hooks/panes.py --unattended w1:p2",
        # Every other use of the script.
        "python3 panes.py",
        "python3 panes.py --selftest",
        "python3 panes.py --help",
        "python3 panes.py --write w1:p2 worker lead --role sheep",
        # Prose and messages that name the flag rather than running it.
        'herdr agent prompt w1:p1 "run panes.py --attended when you are watching"',
        'gh pr comment 9 --body "panes.py --attended marks a watched pane"',
        # An unrelated script whose name is a prefix.
        "python3 panes-report.py --all",
        # The flag with no pane writes nothing: `panes.py` prints its usage and exits 2, so
        # there is no decision to put to the user.
        "python3 panes.py --attended",
    ]
    for c in flagged:
        assert hits(c), f"missed: {c}"
    for c in clean:
        assert not hits(c), f"false positive: {c}"
    print(f"gate-attended selftest: {len(flagged) + len(clean)} checks passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    sys.exit(main())
