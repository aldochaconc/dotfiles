#!/usr/bin/env python3
"""PreToolUse(Bash): block curl and wget when they send data out of the machine.

The repositories under ~/Work denied `Bash(curl:*)` outright, which also blocked every read:
measured on 2026-09-24, a session could not fetch CodeRabbit's public schema. A prefix rule
cannot tell a GET from an upload, and the user asked for the deny to go while uploads stay
blocked. So the read passes and the send is refused here, in every repository and every pane.

What counts as a send is a flag that puts a body, a form, a file or a writing method on the
request. A plain GET with headers passes: a header can carry a token, but a token alone moves
no file.

Exit 2 names the flag that tripped it, so the next attempt is either a read or a question to
the user.

Self-check: python3 block-uploads.py --selftest
"""
import json
import re
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hookaudit import record
except ImportError:
    def record(*_a, **_k):
        return False

CURL_SEND = ("-d", "--data", "-F", "--form", "-T", "--upload-file", "--json")
WGET_SEND = ("--post-data", "--post-file", "--body-data", "--body-file")
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SEGMENT = re.compile(r"[;&|\n]+")


def sends(words):
    """The flag that makes this curl or wget call send data, or None."""
    if not words:
        return None
    tool = Path(words[0]).name
    if tool not in ("curl", "wget"):
        return None
    args = words[1:]
    for i, w in enumerate(args):
        if tool == "curl":
            if w.startswith("--"):
                name, _, value = w.partition("=")
                if name.startswith(CURL_SEND[1]) or name in CURL_SEND[2:]:
                    return name
                if name == "--request":
                    method = value or (args[i + 1] if i + 1 < len(args) else "")
                    if method.upper() in WRITE_METHODS:
                        return f"--request {method}"
            elif w.startswith("-") and len(w) > 1:
                # Short flags combine, `-sd` or `-XPOST`: the letter decides, not the token.
                letters = w[1:]
                for j, ch in enumerate(letters):
                    if ch in "dFT":
                        return f"-{ch}"
                    if ch == "X":
                        method = letters[j + 1:] or (args[i + 1] if i + 1 < len(args) else "")
                        if method.upper() in WRITE_METHODS:
                            return f"-X {method}"
                        break
        else:
            name, _, value = w.partition("=")
            if name in WGET_SEND:
                return name
            if name == "--method":
                method = value or (args[i + 1] if i + 1 < len(args) else "")
                if method.upper() in WRITE_METHODS:
                    return f"--method {method}"
    return None


def verdict(command):
    """The reason to block, or None when every curl and wget call only reads."""
    for segment in SEGMENT.split(command or ""):
        try:
            words = shlex.split(segment)
        except ValueError:
            words = segment.split()
        # A prefix such as `sudo`, `env X=1` or `timeout 5` does not change what the call sends.
        while words and (words[0] in ("sudo", "env", "command", "exec", "timeout", "rtk", "proxy")
                         or "=" in words[0] or words[0].isdigit()):
            words = words[1:]
        flag = sends(words)
        if flag:
            return (f"Blocked: `{Path(words[0]).name} {flag}` sends data out of this machine. "
                    "Reads with curl and wget are allowed; an upload, a form, a body or a "
                    "writing method needs the user, so ask them instead.")
    return None


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, EOFError):
        return 0
    if event.get("tool_name") != "Bash":
        return 0
    reason = verdict((event.get("tool_input") or {}).get("command", ""))
    if not reason:
        return 0
    record("block-uploads", "block", event["tool_input"]["command"][:200])
    print(reason, file=sys.stderr)
    return 2


def selftest():
    global record
    record = lambda *_a, **_k: False
    u = "https://example.com/x"
    for cmd in [f"curl -d a=1 {u}", f"curl --data-binary @f {u}", f"curl -F file=@f {u}",
                f"curl -T f {u}", f"curl --upload-file f {u}", f"curl -X POST {u}",
                f"curl -XPUT {u}", f"curl --request=DELETE {u}", f"curl -sd a {u}",
                f"curl --json '{{}}' {u}", f"wget --post-data a=1 {u}",
                f"wget --method=PUT {u}", f"ls | curl -d @- {u}", f"sudo curl -d a {u}",
                f"/usr/bin/curl -d a {u}", f"cat f; curl -F x=@f {u}"]:
        assert verdict(cmd), cmd
    for cmd in [f"curl -sL {u}", f"curl -H 'Accept: x' {u}", f"curl -X GET {u}",
                f"curl -o out {u}", f"wget -q {u}", "echo curl -d", "git commit -m 'curl -d'",
                f"curl -I {u}", "ls -d /tmp"]:
        assert not verdict(cmd), cmd
    print("block-uploads selftest ok: 16 blocked + 9 allowed")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
