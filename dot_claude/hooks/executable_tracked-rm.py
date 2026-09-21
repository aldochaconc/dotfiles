#!/usr/bin/env python3
"""PreToolUse(Bash): redirect `rm` on a git-tracked file to `git rm`.

Measured over 333.973 logged commands: 179 deletions of source files used `rm` against 58 that
used `git rm`. Both delete the file; only `git rm` records the deletion in the index, so the `rm`
form leaves a removal that a later `git add -A` has to catch, and a `git commit <path>` silently
does not. The Shell section of CLAUDE.md says `git rm`; this hook makes it true when the rule is
forgotten mid-session.

Exit 2 with the `git rm` equivalent, never a plain block: unlike a destructive git command there
is an allowed form, and naming it is what makes the next attempt correct.

Untracked files, build artifacts, temporaries and anything outside a work tree pass through. The
check is per path, so `rm dist/bundle.js src/a.ts` is redirected only when a path is tracked.

Self-check: python3 tracked-rm.py --selftest
"""
import json
import os
import re
import shlex
import subprocess
import sys

# A path is only worth a git query when the command actually deletes it. `rm` inside a quoted
# string, a variable name ending in "rm", or `git rm` itself must not match.
RM_CALL = re.compile(r"(?:^|[;&|(]|\s)rm\s+(?P<args>[^;&|)\n]*)")


def tracked(path, cwd):
    """True when git knows the path in the work tree containing it."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", path],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def targets(command):
    """Every path `rm` is called on, flags and redirections dropped."""
    found = []
    for match in RM_CALL.finditer(command):
        # `git rm` is the correct form; the regex sees the bare `rm` inside it.
        if command[: match.start("args")].rstrip().endswith("git rm"):
            continue
        try:
            words = shlex.split(match.group("args"))
        except ValueError:
            continue
        for word in words:
            if word.startswith("-") or word.startswith(">") or "$" in word or "*" in word:
                continue
            found.append(word)
    return found


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    command = (event.get("tool_input") or {}).get("command") or ""
    if "rm" not in command:
        return 0

    cwd = event.get("cwd") or os.getcwd()
    hits = [p for p in targets(command) if tracked(p, cwd)]
    if not hits:
        return 0

    print("BLOCKED: rm on a git-tracked file. Use git rm, which records the deletion in the index:",
          file=sys.stderr)
    print(f"  git rm {' '.join(shlex.quote(p) for p in hits)}", file=sys.stderr)
    return 2


def selftest():
    cases = [
        ("rm src/a.ts", ["src/a.ts"]),
        ("rm -f src/a.ts src/b.ts", ["src/a.ts", "src/b.ts"]),
        ("cd /x && rm src/a.ts", ["src/a.ts"]),
        ("rm -rf dist", ["dist"]),
        ("git rm src/a.ts", []),
        ("rtk proxy git rm -qf src/a.ts", []),
        ("echo rm", []),
        ("rm -f $TMPFILE", []),
        ("rm -f *.tsbuildinfo", []),
        ("npm run build; rm -f tsconfig.tsbuildinfo", ["tsconfig.tsbuildinfo"]),
    ]
    failed = 0
    for command, want in cases:
        got = targets(command)
        if got != want:
            print(f"FAIL {command!r}: want {want}, got {got}")
            failed += 1
    print("selftest:", "ok" if not failed else f"{failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
