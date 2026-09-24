#!/usr/bin/env python3
"""UserPromptSubmit: record whether the prompt that opened this turn came from the keyboard.

A sheep's questions go to its shephrd, because a user who typed into the pane once may have left.
During the turn the user's own prompt started, the user is in front of the pane by definition,
and a question put on screen there is answered. This mark is what tells `ask-gate.py` which turn
that is, and `~/.claude/hooks/gate-skill-writes.py` reads the same file.

A peer message fires this hook too: measured on 2026-09-24, every one of 12 peer prompts in one
transcript carried the hook context of a `UserPromptSubmit` hook. It arrives as text opening with
`Another Claude session sent a message:` and a `<cross-session-message` tag, which is what marks it
as not typed.

The next prompt overwrites the mark, which is what closes the window. It is spoofable by any
session that types into the pane with `herdr agent prompt`, and it only unlocks a menu, never an
authorization: that is what `confirm-gate.py` and the polkit record are for.

Mark: `~/.claude/typed/<pane, ':' as '-'>.json` = `{"session_id", "typed", "at"}`.

Self-check: python3 typed-mark.py --selftest
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

PEER_PREFIX = "Another Claude session sent a message:"


def is_typed(prompt):
    """True when the prompt came from the keyboard, False when a peer session sent it."""
    head = (prompt or "").lstrip().split("\n", 2)
    if head and head[0].startswith(PEER_PREFIX):
        return False
    return not any("<cross-session-message" in line for line in head[:2])


def mark_path(pane, directory=None):
    """Where the mark for this pane lives, or None outside a pane."""
    if not pane:
        return None
    d = Path(directory) if directory else Path(os.environ.get("HOME", "/tmp")) / ".claude" / "typed"
    return d / (pane.replace(":", "-") + ".json")


def write_mark(payload, pane, directory=None, now=None):
    """Overwrite this pane's mark from a UserPromptSubmit payload; return what was written."""
    path = mark_path(pane, directory)
    if path is None:
        return None
    mark = {
        "session_id": payload.get("session_id") or "",
        "typed": is_typed(payload.get("prompt")),
        "at": time.time() if now is None else now,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(mark))
    tmp.replace(path)
    return mark


def read_typed(session_id, pane, directory=None):
    """True only when this pane's mark names this session and says the prompt was typed."""
    path = mark_path(pane, directory)
    if path is None or not session_id:
        return False
    try:
        mark = json.loads(path.read_text())
    except (OSError, ValueError):
        return False
    return mark.get("session_id") == session_id and mark.get("typed") is True


def main():
    """Hook entry point: write the mark and never block the prompt."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        write_mark(payload, (os.environ.get("HERDR_PANE_ID") or "").strip())
    except Exception:
        # A mark that fails leaves the pane gated, which is the safe direction.
        pass
    sys.exit(0)


def selftest():
    """Assert-based self-check, run with --selftest."""
    peer = ('Another Claude session sent a message:\n<cross-session-message from="uds:/x" '
            'from-name="god">\nrun it\n</cross-session-message>')
    with tempfile.TemporaryDirectory() as d:
        # A typed prompt marks the turn.
        m = write_mark({"session_id": "s1", "prompt": "ask user questions"}, "w1:p9", d)
        assert m["typed"] is True, m
        assert read_typed("s1", "w1:p9", d) is True

        # A peer message overwrites the mark as not typed, which closes the window.
        m = write_mark({"session_id": "s1", "prompt": peer}, "w1:p9", d)
        assert m["typed"] is False, m
        assert read_typed("s1", "w1:p9", d) is False

        # The tag alone, without the prefix line, still reads as a peer.
        assert is_typed('<cross-session-message from="x">hi</cross-session-message>') is False
        # A typed prompt that mentions the tag further down is still typed.
        assert is_typed("why did\nthe\nthird line say <cross-session-message>?") is True

        # A mark from another session does not open the window for this one.
        write_mark({"session_id": "old", "prompt": "hello"}, "w1:p9", d)
        assert read_typed("new", "w1:p9", d) is False

        # No mark, no pane or no session id reads as not typed.
        assert read_typed("s1", "w1:pZ", d) is False
        assert read_typed("s1", "", d) is False
        assert read_typed("", "w1:p9", d) is False
        assert write_mark({"session_id": "s1", "prompt": "x"}, "", d) is None

        # An unreadable mark reads as not typed.
        Path(d, "w1-pB.json").write_text("{not json")
        assert read_typed("s1", "w1:pB", d) is False
    print("typed-mark selftest passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
