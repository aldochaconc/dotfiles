#!/usr/bin/env python3
"""PreToolUse(Write|Edit|MultiEdit): a skill edit waits for a human.

A `SKILL.md` is configuration every future session reads, so a rule entering one is never
silent. No permission surface covers an edit to a skill file before it is staged, which left
this surface with no gate: the write landed and the human found out when the listing changed.

`permissionDecision: "ask"` so the user approves or rejects the write, in every session: the
user attends each pane, so no environment turns the ask into a deny.

What waits for a human is the decision to put a rule in a skill, not the write. The reason text
asks for that decision: the rule's line, the surface that takes it, and the observation that
pays for it. No hook can read the observation, so the agent states it. Which of the six actions
in `skill-growth` applies is part of the answer, and plumbing that moves bytes without touching
a rule is one of the admissible answers.

No rule counting. The upstream version reported a rule-shaped-line delta, matching bullets of
the form `- ... because ...`; measured against every skill in this repository it read zero,
because these skills are written as prose and tables. A number that is always zero is not
evidence, so the prompt asks unconditionally instead.

`Bash` was covered here once and is not any more. Deciding whether a shell line writes is a
judgement a regex cannot make: bash resolves a redirect while parsing, and a pattern over the
raw line only guesses. Three rounds of patching proved it, each closing one case and leaving
the family open — `2>&1`, then a `>` inside quotes, then `2>/dev/null` on a plain `ls`. Every
false positive taught the agent to route around the gate, which is how a `for` loop came to
redirect into five skill files under one confirmation.

The edit tools carry the path as a field, so the test here is exact.

A shell write to a skill file is therefore not gated, and nothing mechanical closes that: a
`deny` rule matches the command line as text, which is the same guessing in another layer.
What closes it is the incentive. `Write` and `Edit` are allowed under the work paths, so the
correct tool now costs no confirmation where it used to cost two, and the Shell section of
CLAUDE.md says prose is written with them. The cheap path and the right path are the same one.

The shephrd plugin is exempt, in its source and in its applied copy. Measured on 2026-09-23: 32 of
the day's 55 asks were writes to `shephrd-protocol`, and the user released that plugin from the
gate so that protocol rounds stop at review rather than at every write. Skills in repositories
under ~/Work are exempt too, since the pull request is where the user reviews them: measured on
2026-09-24, four fixes in one repository's skills were denied to its sheep. Every other skill
still asks.

Self-check: python3 gate-skill-writes.py --selftest
"""
import json
import os
import subprocess
import sys
from pathlib import Path

# A hook runs from wherever Claude Code invokes it, so the sibling module is reached by this
# file's own directory rather than the working one. A missing hookaudit disables recording
# and changes no verdict: see the module docstring on why logging never fails a gate.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from hookaudit import record
except ImportError:
    def record(*_a, **_k):
        return False

ASK_EDIT = (
    "`{where}`, read by every future session.{what}\n\n"
    "State what this write does to the rules: for each rule entering or changing, its line as "
    "it will read, the surface that takes it, and the observation that pays for it. If it only "
    "moves bytes, a rename or a reformat, say that instead. The six actions are in "
    "`skill-growth`."
)


# The shephrd plugin is exempt wherever its source lives: its marketplace clone keeps it under
# plugins/shephrd/, and the old machine-local copy sat under plugins/local/shephrd/.
EXEMPT = ("/plugins/shephrd/", "/plugins/local/shephrd/")
# A skill inside a work repository reaches anyone else only through a pull request the user
# reviews, so the review is the gate there. Skills under ~/dotfiles and ~/.claude apply to every
# session on this machine with no review, and stay gated.
EXEMPT_ROOTS = (os.path.expanduser("~/Work/"),)


def in_work_repo(path):
    """Whether `path` belongs to a repository whose main checkout sits under ~/Work.

    A worktree can live anywhere, and measured on 2026-09-24 a sheep's worktree under /tmp kept
    its skill writes gated although the repository was under ~/Work. The shared git directory
    names the repository whatever the checkout's path.
    """
    d = os.path.dirname(os.path.abspath(path))
    while d and not os.path.isdir(d):
        d = os.path.dirname(d)
    try:
        common = subprocess.run(
            ["git", "-C", d, "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return False
    return bool(common) and common.startswith(EXEMPT_ROOTS)


def is_skill(path):
    """A SKILL.md anywhere, plus its sibling reference files under the same skill."""
    p = str(path)
    if any(e in p for e in EXEMPT) or p.startswith(EXEMPT_ROOTS):
        return False
    if (p.endswith("SKILL.md") or "/skills/" in p) and in_work_repo(p):
        return False
    return p.endswith("SKILL.md") or ("/skills/" in p and p.endswith(".md"))


def skill_name(path):
    """The skill a path belongs to, for the first line of the prompt."""
    parts = Path(path).parts
    if "skills" in parts:
        i = len(parts) - 1 - parts[::-1].index("skills")
        if i + 1 < len(parts):
            return parts[i + 1]
    return Path(path).parent.name


def emit(verdict, text):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": verdict,
        "permissionDecisionReason": text}}))


def main(event=None):
    """Emit the ask, or exit silently for a tool or a path this gate does not cover."""
    try:
        event = event if event is not None else json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, EOFError):
        return 0
    tool = event.get("tool_name") or ""
    ti = event.get("tool_input") or {}

    if tool not in {"Write", "Edit", "MultiEdit"}:
        return 0
    path = ti.get("file_path") or ""
    if not path or not is_skill(path):
        return 0

    what = (" This creates the file, so every rule in it is new."
            if not Path(path).exists() else "")
    record("gate-skill-writes", "ask", f"{tool} {path}")
    emit("ask", ASK_EDIT.format(where=skill_name(path), what=what))
    return 0


def selftest():
    import io
    import contextlib

    # The selftest exercises the ask path, which records. Left alone it would write its
    # fixtures into the real verdict log and inflate the counts the log exists to answer.
    global record
    record = lambda *_a, **_k: False

    for p in ["/x/.claude/skills/documenting/SKILL.md",
              "/x/.claude/skills/writing/references/log.md",
              "/x/dot_claude/skills/skill-growth/SKILL.md"]:
        assert is_skill(p), p
    for p in ["/x/src/index.ts", "/x/README.md", "/x/CLAUDE.md",
              "/x/.claude/skills/a/notes.txt",
              "/x/dot_claude/plugins/local/shephrd/skills/shephrd-protocol/SKILL.md",
              "/x/.claude/plugins/local/shephrd/skills/shephrd-protocol/references/roles.md",
              "/x/clone/plugins/shephrd/skills/shephrd-protocol/SKILL.md",
              os.path.expanduser("~/Work/repo/.claude/skills/board/SKILL.md")]:
        assert not is_skill(p), p
    # Outside ~/Work a skill stays gated, including one whose path merely contains "Work".
    assert is_skill(os.path.expanduser("~/dotfiles/dot_claude/skills/writing/SKILL.md"))
    assert is_skill("/x/Work/repo/.claude/skills/a/SKILL.md")
    # A repository outside ~/Work stays gated, and so does a directory that is no repository.
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        assert is_skill(os.path.join(d, ".claude/skills/a/SKILL.md"))
        subprocess.run(["git", "init", "-q", d], check=True)
        assert is_skill(os.path.join(d, ".claude/skills/a/SKILL.md"))

    assert skill_name("/x/.claude/skills/writing/SKILL.md") == "writing"
    assert skill_name("/x/.claude/skills/writing/references/log.md") == "writing"

    def run(event):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main(event)
        out = buf.getvalue().strip()
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None

    def edit(path, tool="Write"):
        return run({"tool_name": tool, "tool_input": {"file_path": path, "content": "x"}})

    def bash(cmd):
        return run({"tool_name": "Bash", "tool_input": {"command": cmd}})

    # gated: any skill file, by any edit tool. Bash is not this hook's surface any more:
    # a `deny` permission rule refuses a shell write to a skill path before it runs.
    assert edit("/x/.claude/skills/writing/SKILL.md") == "ask"
    assert edit("/x/.claude/skills/writing/SKILL.md", "Edit") == "ask"
    assert edit("/x/.claude/skills/writing/SKILL.md", "MultiEdit") == "ask"
    assert edit("/x/.claude/skills/writing/references/log.md") == "ask"
    # not gated: a non-skill path, or a tool outside the four
    assert edit("/x/src/a.ts") is None
    assert edit("/x/CLAUDE.md") is None
    assert run({"tool_name": "Read", "tool_input": {"file_path": "/x/.claude/skills/a/SKILL.md"}}) is None

    # Every Bash line passes, whether it writes a skill or only reads one. The three the
    # lexical test used to get wrong are kept as the reason the surface was dropped.
    for cmd in [
        "echo x > .claude/skills/writing/SKILL.md",
        "cp /tmp/x.md .claude/skills/a/SKILL.md",
        "cat .claude/skills/writing/SKILL.md",
        "ls ~/.claude/skills/ 2>/dev/null | grep -v synced",
        'diff a/SKILL.md b/SKILL.md | grep "^>" | head -10',
        "node check.js .claude/skills/a/SKILL.md 2>&1 | tail -3",
    ]:
        assert bash(cmd) is None, cmd

    # A pane still carrying the retired CLAUDE_UNATTENDED gets the ask like any other.
    saved = os.environ.get("CLAUDE_UNATTENDED")
    os.environ["CLAUDE_UNATTENDED"] = "1"
    try:
        assert edit("/x/.claude/skills/a/SKILL.md") == "ask"
    finally:
        if saved is None:
            del os.environ["CLAUDE_UNATTENDED"]
        else:
            os.environ["CLAUDE_UNATTENDED"] = saved

    print("selftest ok: 12 path + 2 name + 7 tool + 6 shell + 1 env")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
