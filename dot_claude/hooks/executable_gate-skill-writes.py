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
UNATTENDED_NOTE = (
    "\n\nUnattended run (CLAUDE_UNATTENDED set): the write is denied instead of prompting. "
    "Record the line and the surface it targets, and leave it for the human."
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


def typed_turn(env, session_id):
    """Whether shephrd's `typed-mark.py` marked this session's current turn as typed.

    ponytail: W is not an authorization boundary. `herdr agent prompt` enters as a typed turn and
    `send-keys` can answer the ask, so a peer can open this window; it only turns a deny into an
    ask a person still has to answer. C, the pkexec-signed record, is what authorizes.
    """
    pane = (env.get("HERDR_PANE_ID") or "").strip()
    if not pane or not session_id:
        return False
    mark_file = Path(env.get("HOME", "/tmp")) / ".claude" / "typed" / (pane.replace(":", "-") + ".json")
    try:
        mark = json.loads(mark_file.read_text())
    except (OSError, ValueError):
        return False
    return mark.get("session_id") == session_id and mark.get("typed") is True


def decision(reason, env=None, session_id=""):
    """(verdict, text). Unattended runs deny, because a prompt nobody answers is a deadlock,
    except in a turn the user typed into the pane, where somebody is there to answer."""
    env = env if env is not None else os.environ
    if (env.get("CLAUDE_UNATTENDED") or "").strip():
        if typed_turn(env, session_id):
            return "ask", reason
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
    verdict, text = decision(ASK_EDIT.format(where=skill_name(path), what=what), env,
                             event.get("session_id") or "")
    record("gate-skill-writes", verdict, f"{tool} {path}")
    emit(verdict, text)
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

    # W: a typed turn of this session reopens the ask; anything else keeps the deny.
    with tempfile.TemporaryDirectory() as home:
        typed_dir = Path(home) / ".claude" / "typed"
        typed_dir.mkdir(parents=True)
        env = {"CLAUDE_UNATTENDED": "1", "HERDR_PANE_ID": "w1:p2", "HOME": home}
        assert decision("R", env, "s1")[0] == "deny", "missing mark"
        mark = typed_dir / "w1-p2.json"
        mark.write_text(json.dumps({"session_id": "s1", "typed": True}))
        assert decision("R", env, "s1")[0] == "ask", "typed mark of this session"
        assert decision("R", env, "s2")[0] == "deny", "mark of another session"
        assert decision("R", env, "")[0] == "deny", "no session id"
        mark.write_text(json.dumps({"session_id": "s1", "typed": False}))
        assert decision("R", env, "s1")[0] == "deny", "peer message turn"

    print("selftest ok: 12 path + 2 name + 7 tool + 6 shell + 3 verdict + 5 typed")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
