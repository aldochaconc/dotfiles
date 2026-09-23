#!/usr/bin/env python3
"""PreToolUse(Bash): staging everything is never what one session meant.

`git add -A`, `git add .`, `git commit -a` and the `gt` commands that wrap them stage whatever
is in the tree, including files another session is writing. Measured on 2026-09-23: a sweeping
`git add -A` collected another pane's fix into a commit whose message described something else,
so the fix landed with no commit explaining it and the session that made it had not committed
anything. Several panes share one working tree here, which is the arrangement that makes the
flag wrong rather than merely broad.

Naming the paths is the repair and it costs one line. `git add <path>...` stages what this
session changed; `git commit -- <path>` limits a commit the same way. A session that cannot list
what it changed does not know what it is committing.

Exit 2 so the reason reaches the model rather than the user: the turn continues and the command
is rewritten with its paths.

Self-check: python3 no-add-all.py --selftest
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

# A command runs when it opens the line or a segment, the same anchor destructive-git.py uses:
# `\b` alone matched the name inside a quoted argument and refused prose that named a command.
SEGMENT = r"(?:^|[;&|\"']|\$\(|\n)\s*"

PATTERNS = [
    # `git add -A`, `--all`, and the bare `.` or `:/` that mean the same thing.
    (re.compile(SEGMENT + r"git\s+add\b[^|;&\n]*(\s-A\b|\s--all\b)"), "git add -A"),
    (re.compile(SEGMENT + r"git\s+add\s+(\.|:/)(\s|$)"), "git add ."),
    # `-a` on a commit stages every tracked change without naming one.
    (re.compile(SEGMENT + r"git\s+commit\b[^|;&\n]*\s-(?!-)[a-zA-Z]*a"), "git commit -a"),
    (re.compile(SEGMENT + r"git\s+commit\b[^|;&\n]*\s--all\b"), "git commit --all"),
    # Graphite wraps the same thing: `gt create -a` and `gt modify -a` stage the whole tree.
    (re.compile(SEGMENT + r"gt\s+(create|modify|absorb)\b[^|;&\n]*(\s-a\b|\s--all\b)"),
     "gt with -a"),
]

REASON = (
    "BLOCKED: {why} stages the whole working tree.\n\n"
    "Several sessions share a tree on this machine, so everything includes files another pane "
    "is writing. Measured on 2026-09-23: a sweeping add collected another session's fix into a "
    "commit whose message described something else, leaving that fix with no commit explaining "
    "it.\n\n"
    "Name the paths: `git add <path>...`, or `git commit -- <path>` to limit a commit. "
    "`git status --short` lists what is there, and what this session changed is the subset it "
    "can name."
)


# A heredoc body is data, not commands. The anchor treats a newline as a segment start, so every
# line of a commit message that begins with a command-looking phrase read as one: measured on
# 2026-09-23, this gate refused its own commit because the message explained what it blocks.
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")


def strip_heredocs(command):
    """The command line with every heredoc body removed.

    The delimiter is whatever word follows `<<`, and the body runs to a line holding that word
    alone. Anything unterminated is dropped to the end, which is the safe direction: a body is
    never a command, so removing too much can only miss a pattern that was inside data.
    """
    out, pos = [], 0
    for m in HEREDOC.finditer(command):
        out.append(command[pos:m.end()])
        end = re.compile(r"^\s*" + re.escape(m.group(2)) + r"\s*$", re.M).search(command, m.end())
        pos = end.end() if end else len(command)
    out.append(command[pos:])
    return "".join(out)


def hits(command):
    return [why for pat, why in PATTERNS if pat.search(strip_heredocs(command))]


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    command = (event.get("tool_input") or {}).get("command") or ""
    found = hits(command)
    if not found:
        return 0
    record("no-add-all", "block", command)
    print(REASON.format(why=found[0]), file=sys.stderr)
    return 2


def selftest():
    flagged = [
        "git add -A",
        "git add --all",
        "git add -A .",
        "git add .",
        "git add :/",
        "cd /x && git add -A",
        "git commit -a -m x",
        "git commit -am x",
        "git commit --all",
        "gt create -a -m x",
        "gt modify -a",
        "gt create --all",
        "gt absorb -a",
        'bash -c "git add -A"',
        # A real command after a heredoc closes is still a command.
        "git commit -F - <<'EOF'\nmessage\nEOF\ngit add -A",
    ]
    clean = [
        "git add src/app.ts",
        "git add src/ docs/",
        "git add -p",
        "git add --patch",
        "git commit -m x",
        "git commit -F -",
        "git commit -- src/app.ts",
        "gt create -m x",
        "gt modify -c",
        "gt submit",
        "git status --short",
        "git diff --cached",
        # Prose that names the flag rather than running it. The anchor is what allows this.
        'herdr agent prompt w1:p1 "never use git add -A here"',
        'gh pr comment 9 --body "avoid git add -A"',
        # An unrelated command whose argument happens to contain the letters.
        "npm run add-all-fixtures",
        # A heredoc body is data. This gate refused its own commit before the body was stripped,
        # because the message explained the flag it blocks and the anchor counts a newline.
        "git commit -F - <<'EOF'\nfix: something\n\ngit add -A collected another pane's work\nEOF",
        'git commit -F - <<"MSG"\nwhy gt create -a is refused\nMSG',
        "git commit -F - <<EOF\ngit commit -a stages everything\nEOF",
    ]
    for c in flagged:
        assert hits(c), f"missed: {c}"
    for c in clean:
        assert not hits(c), f"false positive: {c}"
    print(f"no-add-all selftest: {len(flagged) + len(clean)} checks passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    sys.exit(main())
