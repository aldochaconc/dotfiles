#!/usr/bin/env python3
"""PreToolUse(Write|Edit|MultiEdit): a skill edit waits for a human.

A `SKILL.md` is configuration every future session reads, so a rule entering one is never
silent. No permission surface covers an edit to a skill file before it is staged, which left
this surface with no gate: the write landed and the human found out when the listing changed.

`permissionDecision: "ask"` so the user approves or rejects the write. Unattended runs invert
the verdict: with CLAUDE_UNATTENDED set to anything non-empty the verdict is "deny", because a
prompt with nobody at the keyboard is a deadlock rather than a gate.

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

Self-check: python3 gate-skill-writes.py --selftest
"""
import json
import os
import sys
from pathlib import Path

ASK_EDIT = (
    "`{where}`, read by every future session.{what}\n\n"
    "State what this write does to the rules: for each rule entering or changing, its line as "
    "it will read, the surface that takes it, and the observation that pays for it. If it only "
    "moves bytes, a rename or a reformat, say that instead. The six actions are in "
    "`skill-growth`."
)
UNATTENDED_NOTE = (
    "\n\nUnattended run (CLAUDE_UNATTENDED set): the write is denied instead of prompting. "
    "Record the line and the surface it targets, and leave it for the human."
)


def is_skill(path):
    """A SKILL.md anywhere, plus its sibling reference files under the same skill."""
    p = str(path)
    return p.endswith("SKILL.md") or ("/skills/" in p and p.endswith(".md"))


def skill_name(path):
    """The skill a path belongs to, for the first line of the prompt."""
    parts = Path(path).parts
    if "skills" in parts:
        i = len(parts) - 1 - parts[::-1].index("skills")
        if i + 1 < len(parts):
            return parts[i + 1]
    return Path(path).parent.name


def decision(reason, env=None):
    """(verdict, text). Unattended runs deny, because a prompt nobody answers is a deadlock."""
    env = env if env is not None else os.environ
    if (env.get("CLAUDE_UNATTENDED") or "").strip():
        return "deny", reason + UNATTENDED_NOTE
    return "ask", reason


def emit(verdict, text):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": verdict,
        "permissionDecisionReason": text}}))


def main(event=None, env=None):
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
    emit(*decision(ASK_EDIT.format(where=skill_name(path), what=what), env))
    return 0


def selftest():
    import io
    import contextlib

    for p in ["/x/.claude/skills/documenting/SKILL.md",
              "/x/.claude/skills/writing/references/log.md",
              "/x/dot_claude/skills/skill-growth/SKILL.md"]:
        assert is_skill(p), p
    for p in ["/x/src/index.ts", "/x/README.md", "/x/CLAUDE.md",
              "/x/.claude/skills/a/notes.txt"]:
        assert not is_skill(p), p

    assert skill_name("/x/.claude/skills/writing/SKILL.md") == "writing"
    assert skill_name("/x/.claude/skills/writing/references/log.md") == "writing"

    def run(event, env=None):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main(event, env if env is not None else {})
        out = buf.getvalue().strip()
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None

    def edit(path, tool="Write"):
        return run({"tool_name": tool, "tool_input": {"file_path": path, "content": "x"}})

    def bash(cmd, env=None):
        return run({"tool_name": "Bash", "tool_input": {"command": cmd}}, env)

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

    v, t = decision("R", {"CLAUDE_UNATTENDED": "1"})
    assert v == "deny" and UNATTENDED_NOTE in t
    assert decision("R", {"CLAUDE_UNATTENDED": "  "})[0] == "ask"
    assert edit("/x/.claude/skills/a/SKILL.md") == "ask"

    print("selftest ok: 7 path + 2 name + 7 tool + 6 shell + 3 verdict")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
