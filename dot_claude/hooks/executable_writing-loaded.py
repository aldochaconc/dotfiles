#!/usr/bin/env python3
"""PreToolUse(Write|Edit|MultiEdit): prose is not written before `writing` is loaded.

CLAUDE.md requires the `writing` skill before a doc, a skill, a commit body or a comment, and
the requirement failed twice in one session: once because the skill was never invoked, once
because it was invoked and the register was not applied to the text. A line of prose asking
for it is the mechanism that already failed, so this is the mechanism that does not ask.

It decides on its own and stays silent when it can. The session transcript records every
`Skill` call, so the hook reads it: `writing` already invoked means the write proceeds with no
output at all. Only an unloaded skill produces anything, and what it produces goes to the
agent, not to the user: exit 2 feeds stderr back, the agent invokes the skill and retries.
The user is never prompted, because nothing here is theirs to decide.

Scope is prose, by extension. A `.md` is prose entire; a `.py` carries a module docstring and
comments the register governs. Config, data, lockfiles and images carry no sentence to check,
so they are not gated: a hook that fires where no rule applies teaches the agent to route
around it, which is how a loop of shell redirects came to write five skill files.

Self-check: python3 writing-loaded.py --selftest
"""
import json
import os
import re
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

PROSE = (".md", ".py")
# Two ways a skill loads, and a gate that knows only one is a gate that fires on a loaded
# session. The agent calls the `Skill` tool; the user types `/writing`, which never produces
# that call and appears as a command-name block instead. The tool *definition* also carries
# the string `"name":"Skill"` from the first line of every transcript, so the skill name has
# to sit inside the same object or the gate always passes.
INVOKED = re.compile(
    r'"name"\s*:\s*"Skill"\s*,\s*"input"\s*:\s*\{[^}]*"skill"\s*:\s*"writing"'
    r'|<command-name>/writing</command-name>')
REASON = (
    "Prose write with the `writing` skill not loaded. CLAUDE.md requires it before a doc, a "
    "skill, a commit body or a comment.\n\n"
    "Invoke the `writing` skill, then retry this write. Its register is what the text is "
    "checked against: loading it is not applying it, so read the text against the rows before "
    "writing, not after."
)


def is_prose(path):
    """A file whose content the register governs."""
    return str(path).endswith(PROSE)


def loaded(transcript_path):
    """Whether `writing` was invoked in this session.

    An unreadable or absent transcript returns True: a gate that blocks because it could not
    read its evidence is a gate that blocks everything the first time something moves.
    """
    if not transcript_path or not os.path.isfile(transcript_path):
        return True
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as fh:
            return any(INVOKED.search(line) for line in fh)
    except OSError:
        return True


def main(event=None):
    try:
        event = event if event is not None else json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, EOFError):
        return 0
    if (event.get("tool_name") or "") not in {"Write", "Edit", "MultiEdit"}:
        return 0
    path = (event.get("tool_input") or {}).get("file_path") or ""
    if not path or not is_prose(path):
        return 0
    if loaded(event.get("transcript_path") or ""):
        return 0
    record("writing-loaded", "block", f"{event.get('tool_name')} {path}")
    print(REASON, file=sys.stderr)
    return 2


def selftest():
    import tempfile

    # The block path records, and left alone the fixtures below would land in the real
    # verdict log and inflate the counts it exists to answer.
    global record
    record = lambda *_a, **_k: False

    for p in ["/x/CLAUDE.md", "/x/.claude/skills/a/SKILL.md", "/x/hooks/gate.py"]:
        assert is_prose(p), p
    for p in ["/x/settings.json", "/x/bindings.lua", "/x/a.toml", "/x/img.png", "/x/list.txt"]:
        assert not is_prose(p), p

    with tempfile.TemporaryDirectory() as d:
        real = os.path.join(d, "real.jsonl")
        with open(real, "w") as fh:
            fh.write('{"type":"assistant"}\n')
            fh.write('{"message":{"content":[{"name":"Skill","input":{"skill":"writing"}}]}}\n')
        # the user typing /writing, which produces no Skill call
        slash = os.path.join(d, "slash.jsonl")
        with open(slash, "w") as fh:
            fh.write('{"content":"<command-name>/writing</command-name>"}\n')
        other = os.path.join(d, "other.jsonl")
        with open(other, "w") as fh:
            fh.write('{"message":{"content":[{"name":"Skill","input":{"skill":"omarchy"}}]}}\n')
        # The tool definition mentions Skill but invokes nothing: must not count as loaded.
        defn = os.path.join(d, "defn.jsonl")
        with open(defn, "w") as fh:
            fh.write('{"tools":[{"name":"Skill","description":"Invoke a skill. writing ..."}]}\n')

        assert loaded(real)
        assert loaded(slash)
        assert not loaded(other)
        assert not loaded(defn)
        assert loaded("")                      # no transcript: never block
        assert loaded("/nonexistent/x.jsonl")  # unreadable: never block

        def run(path, transcript, tool="Write"):
            return main({"tool_name": tool, "tool_input": {"file_path": path},
                         "transcript_path": transcript})

        assert run("/x/a.md", other) == 2          # prose, not loaded
        assert run("/x/a.py", other) == 2
        assert run("/x/a.md", real) == 0           # prose, loaded
        assert run("/x/a.json", other) == 0        # not prose
        assert run("/x/a.md", other, "Read") == 0  # not a write

    print("selftest ok: 8 path + 6 transcript + 5 verdict")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
