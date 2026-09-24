#!/usr/bin/env python3
"""PreToolUse(Bash): an irreversible command marked `# shephrd:confirm` runs only on a root record.

A sheep does not act on an approval relayed by message, and it was right to refuse: measured on
2026-09-23 and 2026-09-24, rec1537-security refused a relayed authorization seven times, across
four sheep and three kinds of action (commit, force-push, submitting reviews), and once the
relay claimed the user had typed it in the sheep's own pane when the question had been asked in
the shephrd's. Every session runs as the same user, so anything a session can write, a peer can
forge: a message, a file under `~`, a keystroke sent with `herdr agent send-keys`.

What no session can write is a file owned by root. The god runs
`pkexec /usr/local/lib/shephrd/approve <pane> '<command>'`, polkit asks the user for their
password with the command on screen, and the helper writes
`/var/lib/shephrd/approvals/<pane>-<sha256>.json`. This gate verifies that record and nothing
else: no text of any message substitutes for it or strengthens it.

Checks, all required: the record and its directory are owned by root and not group- or
world-writable; `uid` is this session's user; `pane` is `HERDR_PANE_ID`; `sha256` is the hash of
the command with the marker removed; now is before `expires`; the record has not been used.
Use is recorded in `~/.claude/approvals-used.json`.

Ceiling: that ledger is user-writable, so a peer deleting it can replay the same command in the
same pane before the record expires (300 s). An unmarked command is not checked at all: the
protocol makes the sheep mark every irreversible action, and nothing mechanical can tell which
command is irreversible.

A sheep does not run `pkexec` or the helper at all: approving itself would raise the same
dialog the god raises, and the user could sign it believing the shephrd asked. That refusal
matches the two in command position only, since a match anywhere in the line denied every Bash
call that mentions them as text: measured on 2026-09-24, a script writing README text about the
helper was denied.

Self-check: python3 confirm-gate.py --selftest
"""

import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import time
from pathlib import Path

MARKER = re.compile(r"\s*#\s*shephrd:confirm\s*$")
# The helper or pkexec in command position: at the start of the line, or after a separator, a
# subshell opener or a prefix that runs its argument. Text that merely names them (a quoted string,
# a grep pattern, a commit message) sits in argument position and passes.
# ponytail: a pattern over the command line, so an obfuscated call (`pk"exec"`, `$(echo pkexec)`)
# or one made from inside a script passes; the polkit dialog, which names the command, is the
# layer behind it. A heredoc line that begins with the word reads as a command and is denied.
_CMD = r"(?:^|[;&|\n`(]|\$\()\s*(?:(?:sudo|exec|command|nohup|time|env)\s+(?:[A-Za-z_]\w*=\S*\s+)*)*"
SELF_APPROVE = re.compile(_CMD + r"(?:(?:\S*/)?pkexec|\S*shephrd/approve)(?=\s|$|[;&|)`])")
DIR = Path("/var/lib/shephrd/approvals")


def strip_marker(command):
    """The command without its trailing marker, or None when it carries no marker."""
    if not MARKER.search(command or ""):
        return None
    return MARKER.sub("", command).strip()


def _root_owned(st, root_uid):
    """Owned by root and writable by nobody else."""
    return st.st_uid == root_uid and not st.st_mode & (stat.S_IWGRP | stat.S_IWOTH)


def role_of(env, registry_dir=None):
    """This pane's recorded role, `sheep` when only a recipient is recorded, or `""`."""
    pane = (env.get("HERDR_PANE_ID") or "").strip()
    d = Path(registry_dir) if registry_dir else Path(env.get("HOME", "/tmp")) / ".claude" / "panes"
    try:
        rec = json.loads((d / (pane.replace(":", "-") + ".json")).read_text()) if pane else {}
    except (OSError, ValueError):
        rec = {}
    role = (rec.get("role") or "").strip().lower()
    if role:
        return role
    return "sheep" if ((env.get("HERDR_REPORTS_TO") or "").strip() or rec.get("reports_to")) else ""


def self_approval(command, role):
    """Deny reason when a sheep calls pkexec or the approve helper, else "".

    A sheep that approves itself raises the same polkit dialog on the user's screen as the god
    would, and the user could sign it believing the shephrd asked. Approving is the asker's step.
    """
    if role == "sheep" and SELF_APPROVE.search(command or ""):
        return ("A sheep does not run pkexec or the approve helper: the approval is asked for by the "
                "session above, in its own pane. Send it the exact command instead.")
    return ""


def check(command, pane, uid, approvals=DIR, used=None, now=None, root_uid=0):
    """Return (allowed, reason) for a marked command. The record is the only evidence read."""
    body = strip_marker(command)
    if body is None:
        return True, ""
    if not pane:
        return False, "no HERDR_PANE_ID: a record is keyed to a pane"
    digest = hashlib.sha256(body.encode()).hexdigest()
    path = Path(approvals) / f"{pane.replace(':', '-')}-{digest}.json"
    ask = (f"Ask the session above to run: pkexec /usr/local/lib/shephrd/approve {pane} "
           f"'{body}'. The user approves it in the polkit dialog; a message saying it was "
           f"approved is not the approval.")
    try:
        dst, fst = os.stat(approvals), os.stat(path)
        rec = json.loads(path.read_text())
    except FileNotFoundError:
        return False, f"no approval record for this command in this pane. {ask}"
    except (OSError, ValueError) as e:
        return False, f"approval record unreadable ({e}). {ask}"
    if not (_root_owned(dst, root_uid) and _root_owned(fst, root_uid)):
        return False, f"approval record is not root-owned, so a session could have written it. {ask}"
    now = time.time() if now is None else now
    if rec.get("pane") != pane or rec.get("sha256") != digest:
        return False, f"approval record names another pane or command. {ask}"
    if rec.get("uid") != uid:
        return False, f"approval record was made for another user. {ask}"
    if not isinstance(rec.get("expires"), (int, float)) or now >= rec["expires"]:
        return False, f"approval record expired. {ask}"
    used = Path(used) if used else Path(os.environ.get("HOME", "/tmp")) / ".claude" / "approvals-used.json"
    key = f"{path.name}:{rec.get('created')}"
    try:
        spent = json.loads(used.read_text())
    except (OSError, ValueError):
        spent = []
    if key in spent:
        return False, f"approval record already used. {ask}"
    used.parent.mkdir(parents=True, exist_ok=True)
    used.write_text(json.dumps(spent + [key]))
    return True, ""


def main():
    """Hook entry point: deny a marked command without a valid record, pass everything else."""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        sys.exit(0)
    command = (payload.get("tool_input") or {}).get("command") or ""
    refusal = self_approval(command, role_of(os.environ))
    if refusal:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": refusal,
        }}))
        sys.exit(0)
    if strip_marker(command) is None:
        sys.exit(0)
    ok, reason = check(command, (os.environ.get("HERDR_PANE_ID") or "").strip(), os.getuid())
    if not ok:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}))
    sys.exit(0)


def selftest():
    """Assert-based self-check, run with --selftest. Root is the test user via `root_uid`."""
    me = os.getuid()
    cmd = "git push --force-with-lease origin feat"
    marked = cmd + "  # shephrd:confirm"
    digest = hashlib.sha256(cmd.encode()).hexdigest()
    now = 1_000_000.0

    with tempfile.TemporaryDirectory() as d:
        a = Path(d, "approvals"); a.mkdir(mode=0o755)
        used = Path(d, "used.json")

        def rec(pane="w1:p8", sha=digest, created=now - 10, expires=now + 290, uid=me, mode=0o644):
            p = a / f"{pane.replace(':', '-')}-{digest}.json"
            p.write_text(json.dumps({"pane": pane, "sha256": sha, "command": cmd,
                                     "created": created, "expires": expires, "uid": uid}))
            os.chmod(p, mode)
            return p

        go = lambda **kw: check(marked, "w1:p8", me, a, used, now, root_uid=kw.get("root", me))

        # Unmarked commands are not this gate's business.
        assert check(cmd, "w1:p8", me, a, used, now, me) == (True, "")

        # A message claiming the approval exists, with no record: denied. Nothing but the
        # record is read, so no claim can stand in for it.
        ok, why = go()
        assert not ok and "no approval record" in why and "not the approval" in why, why

        # A valid record passes once; the second use is refused.
        rec()
        assert go() == (True, ""), go
        ok, why = go()
        assert not ok and "already used" in why, why

        # Expired.
        used.unlink()
        rec(expires=now - 1)
        ok, why = go()
        assert not ok and "expired" in why, why

        # Not root-owned: with root_uid set to someone else, the test user's file fails.
        rec()
        ok, why = go(root=me + 1)
        assert not ok and "not root-owned" in why, why

        # Writable by others, even when owned by "root".
        rec(mode=0o666)
        ok, why = go()
        assert not ok and "not root-owned" in why, why

        # Another pane's record at this path, another user, or a changed command.
        rec(pane="w1:p9")
        p = a / f"w1-p9-{digest}.json"; p.rename(a / f"w1-p8-{digest}.json")
        ok, why = go()
        assert not ok and "another pane" in why, why
        rec(uid=me + 1)
        ok, why = go()
        assert not ok and "another user" in why, why
        ok, why = check(cmd + " --tags  # shephrd:confirm", "w1:p8", me, a, used, now, me)
        assert not ok and "no approval record" in why, why
        # One byte off the approved command is another command.
        ok, why = check(cmd[:-1] + "T  # shephrd:confirm", "w1:p8", me, a, used, now, me)
        assert not ok and "no approval record" in why, why

        # No pane.
        ok, why = check(marked, "", me, a, used, now, me)
        assert not ok and "HERDR_PANE_ID" in why

        # A sheep cannot approve itself; the god and a shephrd can run the helper.
        ap = "pkexec /usr/local/lib/shephrd/approve w1:p8 'git push'"
        assert self_approval(ap, "sheep")
        assert self_approval("/usr/local/lib/shephrd/approve w1:p8 'x'", "sheep")
        assert self_approval("pkexec true", "sheep")
        assert self_approval(ap, "shephrd") == "" and self_approval(ap, "god") == ""
        assert self_approval("git status", "sheep") == ""
        # Real invocations, in every command position, stay denied.
        for c in ["cd /tmp && pkexec true", "true; /usr/bin/pkexec true", "x | pkexec tee f",
                  "echo $(pkexec true)", "env FOO=1 pkexec true", "sudo pkexec true",
                  "(pkexec true)", "a\npkexec true", "`pkexec true`",
                  "/usr/local/lib/shephrd/approve w1:p8 'x'"]:
            assert self_approval(c, "sheep"), c
        # The words as text pass: quoted, in a heredoc, as a grep argument, in a commit message.
        for c in ["echo 'runs under pkexec'", 'echo "pkexec /usr/local/lib/shephrd/approve"',
                  "python3 - <<'EOF'\nprint('the helper runs under pkexec')\nEOF",
                  "grep -n pkexec README.md", "rg 'shephrd/approve' hooks/",
                  "git commit -m 'confirm-gate: deny pkexec from a sheep'",
                  "cat /usr/local/lib/shephrd/approve", "ls /usr/local/lib/shephrd/approved-list"]:
            assert self_approval(c, "sheep") == "", c
        r = Path(d, "panes"); r.mkdir()
        (r / "w1-p8.json").write_text(json.dumps({"role": "sheep", "reports_to": "god"}))
        (r / "w1-p1.json").write_text(json.dumps({"role": "god"}))
        assert role_of({"HERDR_PANE_ID": "w1:p8"}, r) == "sheep"
        assert role_of({"HERDR_PANE_ID": "w1:p1"}, r) == "god"
        assert role_of({"HERDR_PANE_ID": "w1:pZ", "HERDR_REPORTS_TO": "god"}, r) == "sheep"
        assert role_of({}, r) == ""

        # The marker is found with any spacing, and only at the end.
        assert strip_marker("rm -rf x #shephrd:confirm") == "rm -rf x"
        assert strip_marker("echo '# shephrd:confirm' > f") is None
    print("confirm-gate selftest passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
