#!/usr/bin/env python3
"""PreToolUse(Write|Edit|MultiEdit|Bash): a skill edit waits for a human.

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

`Bash` is covered because the edit tools are not the only way to write a file. A redirect,
`cp`, `mv`, `tee`, `sed -i` or a heredoc naming a skill path all landed unprompted while this
hook watched only the edit tools. The shell test is lexical: the command says where the bytes
go and not what they say, and a writing form plus a skill path is enough to ask.

Self-check: python3 gate-skill-writes.py --selftest
"""
import json
import os
import re
import sys
from pathlib import Path

SKILL_IN_CMD = re.compile(r"SKILL\.md|/skills/")
# A command that can create or overwrite a file. Deliberately conservative: the write
# primitive and the skill path are matched anywhere in the command, not as one token,
# because an indirection separates them. `target=...SKILL.md; printf x > "$target"`,
# `F=...; echo y >> $F` and a `for` over a glob all wrote a skill unprompted while the
# two had to be adjacent. The cost is a command that reads a skill and writes something
# else, which asks without needing to.
# `git` is absent: destructive-git.py owns it, and a checkout restoring a skill is that
# hook's call. Still uncovered, and lexical detection cannot reach it: a command that
# names neither `SKILL.md` nor `/skills/`, such as an external script.
WRITE_PRIMITIVE = re.compile(
    # `>>?` with no whitespace requirement: bash takes `printf x>path` and `x>>path`,
    # and a pattern demanding a space after the operator let both through. `2>&1` and
    # `>=` are excluded so a redirected stderr or a comparison is not a write.
    r">>?(?![&=])"
    r"|\b(cp|mv|install|tee|rsync|truncate)\b"
    r"|\bsed\b[^|;&]*-i"
    r"|\b(rm|unlink)\b"
    # The parenthesis is what separates a call from prose: `Path(p).write_text(x)` is a
    # write and `"testing write_text function"` is not. Requiring the path inside the
    # parens fails, because `Path('...SKILL.md').write_text('x')` puts it before them.
    r"|\bwrite_text\(|\bwriteFileSync\(|\bopen\([^)]*['\"][wa]"
)
ASK_EDIT = (
    "`{where}`, read by every future session.{what}\n\n"
    "State what this write does to the rules: for each rule entering or changing, its line as "
    "it will read, the surface that takes it, and the observation that pays for it. If it only "
    "moves bytes, a rename or a reformat, say that instead. The six actions are in "
    "`skill-growth`."
)
ASK_BASH = (
    "A shell command writes to a skill file. A command shows where bytes go and not what they "
    "say.\n\nIf this adds or changes a rule: state its line, the surface that takes it, and the "
    "observation that pays for it. If it only moves bytes, a rename or a reformat, say that "
    "instead."
)
UNATTENDED_NOTE = (
    "\n\nUnattended run (CLAUDE_UNATTENDED set): the write is denied instead of prompting. "
    "Record the line and the surface it targets, and leave it for the human."
)


def unquoted(cmd):
    """The command with redirect characters inside quotes neutralised.

    `grep "^>" file` reads a skill and writes nothing, but the redirect pattern found the
    `>` and the gate asked on a diff. A redirect operator only redirects outside quotes, so
    `<` and `>` are blanked there. Only those two: blanking the whole quoted run would hide
    `python3 -c "Path(...).write_text(x)"`, which is a real write carried entirely inside
    quotes, and that call must still be caught.
    """
    out, quote = [], None
    for c in cmd:
        if quote:
            out.append(" " if c in "<>" else c)
            if c == quote:
                quote = None
        else:
            if c in "'\"":
                quote = c
            out.append(c)
    return "".join(out)


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

    if tool == "Bash":
        cmd = ti.get("command") or ""
        if not (SKILL_IN_CMD.search(cmd) and WRITE_PRIMITIVE.search(unquoted(cmd))):
            return 0
        emit(*decision(ASK_BASH, env))
        return 0

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

    # gated: any skill file, by any edit tool
    assert edit("/x/.claude/skills/writing/SKILL.md") == "ask"
    assert edit("/x/.claude/skills/writing/SKILL.md", "Edit") == "ask"
    assert edit("/x/.claude/skills/writing/SKILL.md", "MultiEdit") == "ask"
    assert edit("/x/.claude/skills/writing/references/log.md") == "ask"
    # not gated: a non-skill path, or a tool outside the four
    assert edit("/x/src/a.ts") is None
    assert edit("/x/CLAUDE.md") is None
    assert run({"tool_name": "Read", "tool_input": {"file_path": "/x/.claude/skills/a/SKILL.md"}}) is None

    for cmd in [
        "echo x > .claude/skills/writing/SKILL.md",
        "cat <<'EOF' > .claude/skills/a/SKILL.md\nx\nEOF",
        "cp /tmp/x.md .claude/skills/a/SKILL.md",
        "mv /tmp/x.md .claude/skills/a/SKILL.md",
        "sed -i 's/a/b/' .claude/skills/a/SKILL.md",
        "tee .claude/skills/a/SKILL.md < /tmp/x",
        "rm .claude/skills/a/SKILL.md",
        "python3 -c \"Path('.claude/skills/a/SKILL.md').write_text('x')\"",
        # a redirect with no space, which bash accepts
        "printf x>.claude/skills/a/SKILL.md",
        "echo y>>.claude/skills/a/SKILL.md",
        # indirections that separate the primitive from the path
        'target=.claude/skills/a/SKILL.md; printf x > "$target"',
        "F=.claude/skills/a/SKILL.md; echo y >> $F",
        "for f in .claude/skills/*/SKILL.md; do echo x > $f; done",
        # the sibling reference file, which the edit path also gates
        "cat /tmp/new > .claude/skills/a/references/log.md",
        # a glob the upstream literal `SKILL.md` test missed
        "echo x > .claude/skills/a/S*.md",
    ]:
        assert bash(cmd) == "ask", cmd
    for cmd in [
        "cat .claude/skills/writing/SKILL.md",
        "grep -n rule .claude/skills/writing/SKILL.md",
        "wc -l .claude/skills/*/SKILL.md",
        "echo x > src/index.ts",
        "cp a.ts b.ts",
        "git checkout .claude/skills/writing/SKILL.md",
        # a redirected stderr is not a write to the skill it reads
        "node check.js .claude/skills/a/SKILL.md 2>&1 | tail -3",
        # a `>` or `<` inside quotes is data: diffing two skill versions writes nothing
        'diff a/SKILL.md b/SKILL.md | grep "^>" | head -10',
        "diff a/SKILL.md b/SKILL.md | grep '^<' | head -10",
        'grep ">" .claude/skills/a/SKILL.md',
    ]:
        assert bash(cmd) is None, cmd

    assert bash("echo x > .claude/skills/a/SKILL.md", {"CLAUDE_UNATTENDED": "1"}) == "deny"
    assert bash("echo x > .claude/skills/a/SKILL.md", {"CLAUDE_UNATTENDED": "  "}) == "ask"
    v, t = decision("R", {"CLAUDE_UNATTENDED": "1"})
    assert v == "deny" and UNATTENDED_NOTE in t

    print("selftest ok: 7 path + 2 name + 7 tool + 25 shell + 3 verdict")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
