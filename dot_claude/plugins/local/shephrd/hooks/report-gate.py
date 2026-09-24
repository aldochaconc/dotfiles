#!/usr/bin/env python3
"""Stop: a sheep does not end a turn without reporting to its master.

Writing a section headed "Report to <master>" reads exactly like reporting, and it is not: the
text renders in a pane nobody is watching and the master receives nothing. Measured on
a session produced a full report with headings for done, in flight and blocked, and
its transcript carried one `SendMessage` from hours earlier. The work was real and the master
never heard about it.

Prose cannot fix this, because the failure is the session believing it already complied. So the
turn does not end. `Stop` with exit 2 returns the reason to the model and the turn continues,
which is the one moment a missing report can still be sent.

A god is ungated, because it reports to nobody. A sheep reports to its shephrd every turn. A
shephrd under a god is gated only while the god's registry record carries `attended: true`: the
god reads a routine report only when the user is in front of it, and an unattended god holding
twenty of them has buried the one that needed it. What needs the god is sent regardless, and no
regex can tell which turn that is, so the gate stays off rather than forcing the routine one.

Who that is comes from the registry before the variable. `HERDR_REPORTS_TO` does not survive a
restart, since `herdr agent start` takes no `--env`: Measured: a restarted sheep
read as answering to nobody and ended its turns ungated, which is the failure this hook exists to
stop, arriving through the path that was supposed to be covered.

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
from pathlib import Path


def _registry(env, registry_dir=None):
    """This pane's registry record, or an empty one.

    Importing `panes` is avoided, the same way `canary.py` and `ask-gate.py` avoid it: a hook
    that fails on a missing sibling fails on every turn. Any failure gives an empty record, which
    the caller treats as an unresolved role rather than as permission to end the turn.
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


def recipient(env, registry_dir=None):
    """The session this pane reports to, or `""` when it reports to nobody.

    A god reports to nobody and is never gated. Everyone else reports upward, so what
    this answers is the name a report has to reach, not the role.

    The registry is read before the variable for the reason `panes.py` records: `herdr agent
    start` takes no `--env`, so a restarted pane loses `HERDR_REPORTS_TO` while keeping its pane
    id. Measured: a restarted sheep read as reporting to nobody and ended its turns
    ungated, which is the whole failure this hook exists to stop.
    """
    rec = _registry(env, registry_dir)
    role = (rec.get("role") or "").strip().lower()
    if role == "god":
        return ""
    if (env.get("HERDR_GOD") or "").strip().lower() not in ("", "0", "false", "no"):
        return ""
    if bool(rec.get("god")):
        return ""
    return (env.get("HERDR_REPORTS_TO") or "").strip() or (
        rec.get("reports_to") or "").strip()

SEND = re.compile(r'"name"\s*:\s*"SendMessage"')
# A turn begins at the user's own message, and `"type":"user"` alone does not find it: a tool
# result carries the same type. Measured: over one session's transcript, 649 of 704
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
    """Whether this transcript line is the user's own message rather than a tool result.

    The fallback boundary, for a transcript whose lines carry no `promptId`.
    """
    return bool(USER_TURN.search(line)) and not TOOL_RESULT.search(line)


# A second shape hides a send the same way, and the test above cannot see it. Loading a skill
# writes the skill's text as a `"type":"user"` line with `isMeta` and no `tool_result`, so a
# session that sent its report and then loaded a skill read as a new turn with nothing sent.
# Measured in this plugin's own transcripts: two skill loads sat inside one turn as user lines,
# and a pane reported duplicates twice (msg_ids c64b9bfa then ff2abb50, 87137ea8 then ff60ed4f).
#
# What every user line of one turn shares is its `promptId`: the prompt, its tool results and a
# skill load alike. A peer message arriving mid-turn is written as an `attachment`, not as a user
# line, so it never starts a turn. The turn is therefore the run of lines back to the first user
# line carrying a different `promptId`. An escaped key inside quoted content reads `\"promptId\"`
# and does not match.
PROMPT_ID = re.compile(r'"promptId"\s*:\s*"([^"]+)"')


def in_this_turn(transcript_path, pattern):
    """Whether `pattern` matches a line of the current turn.

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

    # The turn starts at its earliest user line, so assistant lines between the previous turn's
    # last user line and this turn's first belong to the previous turn.
    turn, start = None, None
    for i in range(len(lines) - 1, -1, -1):
        m = PROMPT_ID.search(lines[i])
        if m:
            if turn is None:
                turn = m.group(1)
            elif m.group(1) != turn:
                break
            start = i
        elif turn is None and starts_turn(lines[i]):
            start = i
            break
    if start is None:
        start = 0
    return any(pattern.search(line) for line in lines[start:])


REASON = (
    "Turn not ended: this pane answers to {master} and no SendMessage went out this turn.\n\n"
    "A report written into the reply does not reach {master}. The text renders here, in a pane "
    "nobody is watching, and the turn ends with the master knowing nothing. Send it with "
    "SendMessage to {master}, carrying what was done, what is in flight and what is blocked.\n\n"
    "A turn that produced nothing still reports that it ran: silence and a dead session read the "
    "same from outside. A send that fails because {master} is not reachable counts as sent: "
    "try once and end the turn. shephrd-protocol holds the rule."
)


def sent_this_turn(transcript_path):
    """Whether a SendMessage was called this turn, whatever it returned.

    The call is what counts, not its result. A send to a recipient that has gone, which returns
    `No agent named '<name>' is reachable`, is still the report this pane could make, and a gate
    that waited for a delivered one would hold the turn until a restart elsewhere finished.
    """
    return in_this_turn(transcript_path, SEND)


def god_attended(master, registry_dir=None, env=None):
    """Whether `master` is a god whose registry record carries `attended: true`.

    `panes.py --attended <god-pane>` writes the flag, the same one `ask-gate.py` reads for any
    pane. Several records can carry the god's name, since a god from an earlier workspace leaves
    its file behind; the most recently written one is the live god. No record, or one without the
    flag, reads as unattended, which is the registry's default for every pane.

    Returns None when no record names `master` as a god, so the caller can tell a shephrd under
    another shephrd from one under a god.
    """
    env = env if env is not None else os.environ
    d = Path(registry_dir) if registry_dir else Path(
        env.get("HOME", "/tmp")) / ".claude" / "panes"
    found = []
    try:
        files = list(d.glob("*.json"))
    except OSError:
        files = []
    for f in files:
        try:
            rec = json.loads(f.read_text())
            mtime = f.stat().st_mtime
        except (OSError, ValueError):
            continue
        if not isinstance(rec, dict) or (rec.get("name") or "").strip() != master:
            continue
        if (rec.get("role") or "").strip().lower() == "god" or rec.get("god") is True:
            found.append((mtime, rec))
    if not found:
        return None
    return max(found, key=lambda x: x[0])[1].get("attended") is True


def verdict(event, env=None, registry_dir=None):
    """Return (block, reason). Block is False for a god or a session that already sent.

    The recipient comes from `recipient`, which reads the registry before the variable. Reading
    `HERDR_REPORTS_TO` alone let a restarted sheep end its turns without reporting: the variable
    does not survive `herdr agent start`, so the pane came back looking like a session that
    answers to nobody. Measured: .

    A pane with no recipient at all is not blocked. A block here is only useful because it names
    where the report goes; with nothing to name, the session has no action that would satisfy the
    gate and would be held for a turn it cannot complete. A pane in that state is visible through
    its canary beat instead.

    `ask-gate.py` permits on the same evidence, for the same reason: gating is opted into by a
    recorded recipient rather than assumed from its absence.
    """
    env = env if env is not None else os.environ
    master = recipient(env, registry_dir)
    if not master:
        return False, ""
    # An infinite block would trap a session that cannot send at all, so one continuation is
    # enough: Claude Code sets this when the Stop hook already fired for this turn.
    if event.get("stop_hook_active"):
        return False, ""
    path = event.get("transcript_path") or ""
    if sent_this_turn(path):
        return False, ""
    rec = _registry(env, registry_dir)
    # `autoreport: false` releases one pane from the every-turn report, leaving it to send when
    # asked. It is per pane and written by hand, so the default stays on: a pane that reports
    # only on demand is indistinguishable from a dead one until somebody asks, which is the cost
    # the user accepts for the pane they are sitting in front of. The canary beat still answers
    # whether it takes turns.
    if rec.get("autoreport") is False:
        return False, ""
    role = (rec.get("role") or "").strip().lower()
    # A shephrd under a god sends the routine report only while the god is attended. A sheep is
    # untouched: its shephrd is a session, never the user, and reads every report.
    if role == "shephrd" and god_attended(master, registry_dir, env) is False:
        return False, ""
    return True, REASON.format(master=master)


def main():
    """Hook entry point: exit 2 with the reason when the turn ends without a report."""
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
    """Assert-based self-check, run with --selftest."""
    import tempfile
    from pathlib import Path

    sheep = {"HERDR_REPORTS_TO": "lead"}

    # A master is never gated.
    assert verdict({}, {})[0] is False
    assert verdict({}, {"HERDR_REPORTS_TO": "   "})[0] is False

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
            '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash"}]}}\n'
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
            '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash"}]}}\n'
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

    with tempfile.TemporaryDirectory() as d:
        # A skill load after the send is a user line with no tool_result, and the same promptId.
        # It hid the send and forced duplicate reports before the turn was read by promptId.
        skill = Path(d) / "skill.jsonl"
        skill.write_text(
            '{"type":"user","promptId":"p0","message":{"content":"earlier"}}\n'
            '{"type":"user","promptId":"p1","isMeta":true,"message":{"content":"go"}}\n'
            '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"SendMessage"}]}}\n'
            '{"type":"user","promptId":"p1","message":{"content":[{"type":"tool_result"}]}}\n'
            '{"type":"user","promptId":"p1","isMeta":true,"message":{"content":[{"type":"text","text":"Base directory for this skill"}]}}\n'
            '{"type":"assistant","message":{"content":[{"type":"text","text":"done"}]}}\n'
        )
        assert sent_this_turn(str(skill)) is True
        # A peer message mid-turn is an attachment and does not start a turn either.
        peer = Path(d) / "peer.jsonl"
        peer.write_text(
            '{"type":"user","promptId":"p1","message":{"content":"go"}}\n'
            '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"SendMessage"}]}}\n'
            '{"type":"attachment","attachment":{"type":"queued_command"}}\n'
        )
        assert sent_this_turn(str(peer)) is True
        # The previous turn's send does not count: a different promptId closes the turn.
        prev = Path(d) / "prev.jsonl"
        prev.write_text(
            '{"type":"user","promptId":"p1","message":{"content":"go"}}\n'
            '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"SendMessage"}]}}\n'
            '{"type":"user","promptId":"p2","message":{"content":"again"}}\n'
            '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash"}]}}\n'
        )
        assert sent_this_turn(str(prev)) is False
        # A send that failed because the recipient is gone still counts.
        gone = Path(d) / "gone.jsonl"
        gone.write_text(
            '{"type":"user","promptId":"p1","message":{"content":"go"}}\n'
            '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"SendMessage"}]}}\n'
            '{"type":"user","promptId":"p1","message":{"content":[{"type":"tool_result","is_error":true,"content":"No agent named \'god\' is reachable"}]}}\n'
        )
        assert verdict({"transcript_path": str(gone)}, sheep)[0] is False

    # An unreadable transcript never blocks.
    assert sent_this_turn("/nonexistent/path.jsonl") is True
    assert sent_this_turn("") is True

    # The recipient comes from the registry before the variable, so a restart does not release a
    # pane from the gate. Every row here has the variable empty, which is what a restart leaves.
    with tempfile.TemporaryDirectory() as d:
        def record(pane, **fields):
            """Write a registry record for the test pane."""
            Path(d, pane.replace(":", "-") + ".json").write_text(json.dumps(fields))

        quiet = Path(d) / "quiet.jsonl"
        quiet.write_text(
            '{"type":"user","message":{"content":"go"}}\n'
            '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash"}]}}\n'
        )
        event = {"transcript_path": str(quiet)}

        # The case that was live: a restarted sheep kept its pane id and lost every variable.
        record("w3:p1", name="worker", reports_to="lead", role="sheep")
        assert recipient({"HERDR_PANE_ID": "w3:p1"}, d) == "lead"
        block, reason = verdict(event, {"HERDR_PANE_ID": "w3:p1"}, d)
        assert block is True
        assert "lead" in reason

        # A shephrd under a god is gated only while the god is attended.
        record("w3:p2", name="tree-a", reports_to="god", role="shephrd")
        record("w3:pG", name="god", reports_to="", god=True, role="god")
        assert god_attended("god", d) is False
        assert verdict(event, {"HERDR_PANE_ID": "w3:p2"}, d)[0] is False
        record("w3:pG", name="god", reports_to="", god=True, role="god", attended=True)
        assert god_attended("god", d) is True
        assert verdict(event, {"HERDR_PANE_ID": "w3:p2"}, d)[0] is True
        # A sheep is gated whatever the god's state: its shephrd reads every report.
        record("w3:p3", name="helper", reports_to="tree-a", role="sheep")
        assert verdict(event, {"HERDR_PANE_ID": "w3:p3"}, d)[0] is True
        # A shephrd under a recipient that is not a god stays gated.
        record("w3:pS", name="sub", reports_to="tree-a", role="shephrd")
        assert god_attended("tree-a", d) is None
        assert verdict(event, {"HERDR_PANE_ID": "w3:pS"}, d)[0] is True
        # A stale god record under the same name loses to the newer one.
        record("w3:pO", name="god", reports_to="", god=True, role="god", attended=False)
        os.utime(Path(d, "w3-pO.json"), (1, 1))
        assert god_attended("god", d) is True

        # `autoreport: false` releases a pane that would otherwise be gated, and only that pane.
        record("w3:p8", name="hands-on", reports_to="god", role="shephrd", autoreport=False)
        assert verdict(event, {"HERDR_PANE_ID": "w3:p8"}, d)[0] is False
        # Absent, true, or any other value leaves the gate on: the release is opted into.
        record("w3:p9", name="normal", reports_to="god", role="shephrd", autoreport=True)
        assert verdict(event, {"HERDR_PANE_ID": "w3:p9"}, d)[0] is True
        record("w3:pA", name="typo", reports_to="god", role="shephrd", autoreport="false")
        assert verdict(event, {"HERDR_PANE_ID": "w3:pA"}, d)[0] is True

        # A god reports to nobody, by the recorded role and by the flag alike.
        record("w3:p4", name="god", reports_to="", god=True, role="god")
        assert recipient({"HERDR_PANE_ID": "w3:p4"}, d) == ""
        assert verdict(event, {"HERDR_PANE_ID": "w3:p4"}, d)[0] is False
        record("w3:p5", name="g", reports_to="god", role="god")
        assert recipient({"HERDR_PANE_ID": "w3:p5"}, d) == ""
        assert recipient({"HERDR_PANE_ID": "w3:pZ", "HERDR_GOD": "1"}, d) == ""

        # A shephrd with nobody above it reports to nobody and ends its turns freely.
        record("w3:p6", name="lone", reports_to="", role="shephrd")
        assert verdict(event, {"HERDR_PANE_ID": "w3:p6"}, d)[0] is False

        # The variable still answers where the registry has nothing, which is a pane opened
        # before the registry existed.
        assert recipient({"HERDR_PANE_ID": "w3:pZ", "HERDR_REPORTS_TO": "lead"}, d) == "lead"
        # And a pane with neither is not blocked: a gate that named no recipient would hold a
        # turn the session has no way to complete.
        assert verdict(event, {"HERDR_PANE_ID": "w3:pZ"}, d)[0] is False
        # A malformed record reads as nothing recorded rather than raising.
        Path(d, "w3-p7.json").write_text("{not json")
        assert recipient({"HERDR_PANE_ID": "w3:p7", "HERDR_REPORTS_TO": "lead"}, d) == "lead"

    print("report-gate selftest passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(main())
