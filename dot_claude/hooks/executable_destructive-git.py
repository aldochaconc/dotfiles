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
import subprocess
import sys
from pathlib import Path

# A hook runs from wherever Claude Code invokes it, so the sibling module is reached by this
# file's own directory. A missing hookaudit disables recording and blocks nothing differently.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hookaudit import record
except ImportError:
    def record(*_a, **_k):
        return False

# A command runs when it opens the line or a segment. `\b` alone matched the name anywhere on
# the line, including inside a quoted argument, so the hook blocked prose that named a command
# instead of running one: measured on 2026-09-23, `herdr agent prompt <pane> "<text>"` was
# refused because the text told that session not to use the force form. Four of five measured
# cases were prose, one of them an instruction against the command it was blocked for.
#
# The anchor is what a segment start looks like: the line start, a separator, a substitution, or
# a quote. The quote is there for `bash -c "git push --force"`, which opens after one and is a
# real command. What it leaves through is prose whose quoted text begins with the command as its
# first words; every measured instance had words before it. Closing that would mean parsing the
# shell, which `gate-skill-writes.py` records as the thing a regex cannot do: three rounds of
# patching there each closed one case and left the family open.
SEGMENT = r"(?:^|[;&|\"']|\$\(|\n)\s*"

PATTERNS = [
    (re.compile(SEGMENT + r"git\s+reset\b[^|;&\n]*--hard\b"), "git reset --hard"),
    (re.compile(SEGMENT + r"git\s+checkout\b[^|;&\n]*\s(--\s|\.\s*$|\.$)"), "git checkout over a path"),
    (re.compile(SEGMENT + r"git\s+clean\b[^|;&\n]*-\w*f\w*"), "git clean -f"),
    (re.compile(SEGMENT + r"git\s+stash\s+(drop|clear)\b"), "git stash drop/clear"),
    # `git restore` is `git checkout -- <path>` in the newer syntax and overwrites the file with
    # no undo. `--staged` alone only unstages, leaving the working tree intact, so it is the
    # `git reset HEAD` of that syntax and is not gated. Everything else is: the bare form
    # defaults to `--worktree`, and `--staged --worktree` together do discard.
    (re.compile(SEGMENT + r"git\s+restore\b(?![^|;&\n]*--staged(?![^|;&\n]*--worktree))"),
     "git restore over a path"),
    (re.compile(SEGMENT + r"git\s+push\b[^|;&\n]*(--force\b|--force-with-lease\b|\s-f\b)"), "git push --force"),
]

# No alternative is named for a force push. `gt submit` force-pushes too, so offering it as the
# safe route would be offering the same overwrite under another name: the destruction is the
# remote history, not the spelling of the command. A session blocked here escalates to the user,
# which is the intended end state rather than a gap.
#
# Which tool governs a repository is a state on disk rather than a preference: Graphite writes
# `.graphite_repo_config` into the git directory at `gt init`, and `gt` exits 0 in a repository
# it does not govern, so the file is the test and the exit code is not. Measured on 2026-09-23
# across three trees, it answered correctly in each.
#
# It changes no verdict here. A force push overwrites remote history whichever tool spells it,
# and Graphite running the stack is not a reason to allow one. What it adds is a line telling a
# blocked session that the stack belongs to Graphite, so the question it takes to the user
# carries that.
#
# Gating plain `git` in such a repository was considered and does not apply. `gt modify` runs
# `git` beneath itself, and a hook cannot tell that call from one the agent wrote — except that
# it never sees it at all: this is `PreToolUse` on `Bash`, so it reads the line the agent typed,
# and a subprocess of `gt` is not a tool call. Measured over 37422 audited commands: 21 lines
# begin with `gt` and 705 with `git`, one line per tool call, and none of Graphite's internal
# calls appear.


def graphite_governs(cwd):
    """Whether `gt init` has run in the repository containing cwd.

    `--git-common-dir` rather than `--absolute-git-dir`, because a linked worktree has a git
    directory of its own under `<main>/.git/worktrees/<name>` and Graphite's config sits in the
    main one. Measured on 2026-09-23 in a live worktree: the absolute form reported plain git
    for a repository Graphite governs, and the common form answered correctly from both the
    worktree and the main checkout.

    Failure returns False. A state read that cannot complete must not change a verdict, and the
    verdict here does not depend on it.
    """
    if not cwd:
        return False
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    if out.returncode != 0:
        return False
    d = out.stdout.strip()
    return bool(d) and Path(d, ".graphite_repo_config").is_file()


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
    record("destructive-git", "block", command)
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
        "git restore src/app.ts",
        "git restore --worktree -- src/app.ts",
        "git restore --staged --worktree -- src/app.ts",
        "git restore --source=HEAD~1 -- src/app.ts",
        "git restore .",
        'bash -c "git push --force"',
        "sh -c 'git reset --hard'",
        "cd /tmp\ngit push --force",
        "echo $(git clean -fd)",
        # Quoted text whose first words are the command still blocks: the command opens the
        # quote, which is the anchor. Every prose instance measured in the field had words
        # before it, and separating these two needs a shell parser.
        "echo 'git reset --hard' > notes.txt",
        "grep -rn 'git push --force' docs/",
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
        # --staged alone unstages and leaves the working tree, so it destroys nothing.
        "git restore --staged -- src/app.ts",
        "git restore --staged .",
        # Prose that names a command instead of running one. The hook blocked all of these
        # before the anchor, including an instruction against the command it flagged.
        'herdr agent prompt w1R:p8 "no uses git push --force aqui"',
        'gh pr comment 938 --body "avoid git push --force"',
        'echo "never run git reset --hard"',
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
