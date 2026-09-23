#!/usr/bin/env python3
"""Stop: a sheep does not end a turn without reporting to its master.

Writing a section headed "Report to <master>" reads exactly like reporting, and it is not: the
text renders in a pane nobody is watching and the master receives nothing. Measured on
2026-09-23: a session produced a full report with headings for done, in flight and blocked, and
its transcript carried one `SendMessage` from hours earlier. The work was real and the master
never heard about it.

Prose cannot fix this, because the failure is the session believing it already complied. So the
turn does not end. `Stop` with exit 2 returns the reason to the model and the turn continues,
which is the one moment a missing report can still be sent.

Only a sheep is gated. A master reports to nobody, and a session with no `HERDR_AGENT_MASTER`
ends its turns freely.

The check is whether a `SendMessage` appears in this turn. It does not read who it went to or
what it said, and that boundary is a split of work rather than a shortcut.

A hook runs on every turn of every pane, so it answers what a regex answers: a message left, or
none did. Whether the reports are any good is a pattern across turns and across sessions, which
`traffic-auditor` reads from the transcripts in its own context when someone asks. A gate that
blocked on a weak report would stop a turn on a judgement it cannot defend, and a session that
disagreed with it could not pass.
"""

import json
import os
import re
import sys

SEND = re.compile(r'"name"\s*:\s*"SendMessage"')
# A turn begins at the user's own message, and `"type":"user"` alone does not find it: a tool
# result carries the same type. Measured on 2026-09-23 over one session's transcript, 649 of 704
# user entries were tool results and 55 were messages, so scanning back to the first `user` line
# stopped at whatever tool ran last.
#
# What that cost: a session that sent its report and then read a file had the read hide the send,
# so the gate blocked a turn that had reported. Measured twice against one pane, each time
# forcing a duplicate report into the master's context, which is the cost the whole design exists
# to avoid.
#
# A real user message has no `tool_result` in its content. A tool result always does, so the
# absence of that string is what separates them.
USER_TURN = re.compile(r'"type"\s*:\s*"user"')
TOOL_RESULT = re.compile(r'"type"\s*:\s*"tool_result"')


def starts_turn(line):
    """Whether this transcript line is the user's own message rather than a tool result."""
    return bool(USER_TURN.search(line)) and not TOOL_RESULT.search(line)


REASON = (
    "Turn not ended: this pane answers to {master} and no SendMessage went out this turn.\n\n"
    "A report written into the reply does not reach {master}. The text renders here, in a pane "
    "nobody is watching, and the turn ends with the master knowing nothing. Send it with "
    "SendMessage to {master}, carrying what was done, what is in flight and what is blocked.\n\n"
    "A turn that produced nothing still reports that it ran: silence and a dead session read the "
    "same from outside. shephrd-protocol holds the rule."
)


def sent_this_turn(transcript_path):
    """Whether a SendMessage appears since the last user turn.

    An unreadable or absent transcript returns True. A gate that blocks because it could not read
    its evidence stops every turn in a session whose transcript moved, which is worse than a
    missed report.
    """
    if not transcript_path or not os.path.isfile(transcript_path):
        return True
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError:
        return True

    for line in reversed(lines):
        if SEND.search(line):
            return True
        if starts_turn(line):
            return False
    return False


def verdict(event, env=None):
    """Return (block, reason). Block is False for a master or a session that already sent."""
    env = env if env is not None else os.environ
    master = (env.get("HERDR_AGENT_MASTER") or "").strip()
    if not master:
        return False, ""
    # An infinite block would trap a session that cannot send at all, so one continuation is
    # enough: Claude Code sets this when the Stop hook already fired for this turn.
    if event.get("stop_hook_active"):
        return False, ""
    if sent_this_turn(event.get("transcript_path") or ""):
        return False, ""
    return True, REASON.format(master=master)


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, EOFError):
        return 0
    block, reason = verdict(event)
    if not block:
        return 0
    print(reason, file=sys.stderr)
    return 2


def selftest():
    import tempfile
    from pathlib import Path

    sheep = {"HERDR_AGENT_MASTER": "lead"}

    # A master is never gated.
    assert verdict({}, {})[0] is False
    assert verdict({}, {"HERDR_AGENT_MASTER": "   "})[0] is False

    with tempfile.TemporaryDirectory() as d:
        sent = Path(d) / "sent.jsonl"
        sent.write_text(
            '{"type":"user"}\n'
            '{"type":"assistant","message":{"content":[{"name":"SendMessage"}]}}\n'
        )
        assert sent_this_turn(str(sent)) is True
        assert verdict({"transcript_path": str(sent)}, sheep)[0] is False

        quiet = Path(d) / "quiet.jsonl"
        quiet.write_text(
            '{"type":"assistant","message":{"content":[{"name":"SendMessage"}]}}\n'
            '{"type":"user"}\n'
            '{"type":"assistant","message":{"content":[{"name":"Bash"}]}}\n'
        )
        # The send is from a previous turn, so it does not count for this one.
        assert sent_this_turn(str(quiet)) is False

        # A tool result after the send is not a turn boundary. This is the case that blocked
        # turns which had reported: the session sent, then read a file, and the read hid it.
        worked = Path(d) / "worked.jsonl"
        worked.write_text(
            '{"type":"user","message":{"content":"do the thing"}}\n'
            '{"type":"assistant","message":{"content":[{"name":"SendMessage"}]}}\n'
            '{"type":"user","message":{"content":[{"type":"tool_result","content":"ok"}]}}\n'
            '{"type":"assistant","message":{"content":[{"name":"Bash"}]}}\n'
            '{"type":"user","message":{"content":[{"type":"tool_result","content":"out"}]}}\n'
        )
        assert sent_this_turn(str(worked)) is True
        assert verdict({"transcript_path": str(worked)}, sheep)[0] is False

        # The boundary test itself, on the two shapes it has to separate.
        assert starts_turn('{"type":"user","message":{"content":"hello"}}') is True
        assert starts_turn(
            '{"type":"user","message":{"content":[{"type":"tool_result"}]}}') is False
        assert starts_turn('{"type":"assistant"}') is False
        block, reason = verdict({"transcript_path": str(quiet)}, sheep)
        assert block is True
        assert "lead" in reason
        assert "SendMessage" in reason

        # A second Stop for the same turn passes, so a session cannot be trapped.
        assert verdict(
            {"transcript_path": str(quiet), "stop_hook_active": True}, sheep
        )[0] is False

    # An unreadable transcript never blocks.
    assert sent_this_turn("/nonexistent/path.jsonl") is True
    assert sent_this_turn("") is True

    print("report-gate selftest: 16 checks passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(main())
