#!/usr/bin/env python3
"""PreToolUse(Bash): hard-block git commands that discard work.

`reset --hard`, `checkout -- <path>`/`checkout .`, `clean -f`, `stash drop`/`stash clear`, and any
push with `--force`/`-f`/`--force-with-lease` erase commits, working-tree edits, or remote history
with no undo. The Git section of CLAUDE.md already says these are never run to fix a mistake this
session caused; this hook makes that true regardless of the permissions allowlist, model, or
pressure in the moment; being listed under `ask` in settings.json is for the user to decide, not a
plausible reason to decide it here.

Exit 2 always: there is no allowed form of these commands from this hook, only a human running
them directly.

Self-check: python3 destructive-git.py --selftest
"""
import json
import re
import sys

PATTERNS = [
    (re.compile(r"\bgit\s+reset\b[^|;&\n]*--hard\b"), "git reset --hard"),
    (re.compile(r"\bgit\s+checkout\b[^|;&\n]*\s(--\s|\.\s*$|\.$)"), "git checkout over a path"),
    (re.compile(r"\bgit\s+clean\b[^|;&\n]*-\w*f\w*"), "git clean -f"),
    (re.compile(r"\bgit\s+stash\s+(drop|clear)\b"), "git stash drop/clear"),
    (re.compile(r"\bgit\s+push\b[^|;&\n]*(--force\b|--force-with-lease\b|\s-f\b)"), "git push --force"),
]


def hits(command):
    return [why for pat, why in PATTERNS if pat.search(command)]


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    command = (event.get("tool_input") or {}).get("command") or ""
    found = hits(command)
    if not found:
        return 0
    print("BLOCKED: destructive git command, no exception from this session:", file=sys.stderr)
    for why in found:
        print(f"  {why}", file=sys.stderr)
    print("Tell the user what would be discarded and wait. They run it themselves if they want it.",
          file=sys.stderr)
    return 2


def selftest():
    flagged = [
        "git reset --hard 619c263",
        "git reset --hard",
        "cd /x && git reset --hard HEAD",
        "git checkout -- foo.txt",
        "git checkout .",
        "git clean -fd",
        "git clean -xdf",
        "git stash drop",
        "git stash clear",
        "git push --force",
        "git push origin main --force-with-lease",
        "git push -f origin main",
        "echo 'git reset --hard' > notes.txt",  # substring match over-blocks quoted text too;
                                                 # accepted, since under-blocking the real command is worse
    ]
    clean = [
        "git reset HEAD~1",
        "git checkout main",
        "git checkout -b feature",
        "git clean -n",
        "git stash list",
        "git stash pop",
        "git push origin main",
        "git status",
        "git log --oneline",
    ]
    for c in flagged:
        assert hits(c), f"missed: {c}"
    for c in clean:
        assert not hits(c), f"false positive: {c}"
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    sys.exit(main())
