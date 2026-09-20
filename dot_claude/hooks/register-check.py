#!/usr/bin/env python3
"""PostToolUse(Edit|Write): flag prose tells in written markdown.

Enforces the one grep-detectable tic of the Speaking section in
~/.claude/CLAUDE.md. Only .md files, only prose: fenced code blocks and inline
code spans are exempt, since a tell inside code is data. End-user product copy
is exempt, since Speaking does not govern it.

The dash carries no check here. A blanket ban on `—` and `–` flagged the numeric
range (`2020-2024`) and the paired parenthetical aside, both of which the dash
entry of the `speaking` skill admits, so the rule was moved to that entry and is
judged rather than matched.

Exit 2 feeds stderr back to the model, which then fixes the lines named.

Self-check: python3 register-check.py --selftest
"""
import json
import re
import sys
from pathlib import Path

# Paths exempt from the register (product UI copy). One regex, kept out of the repo.
_exempt_file = Path.home() / ".config" / "dotfiles-guard" / "register-exempt"
EXEMPT_PATH = re.compile(_exempt_file.read_text().strip()) if _exempt_file.is_file() else None
FENCE = re.compile(r"^\s*(```|~~~)")
CODE_SPAN = re.compile(r"`[^`]*`")
MAX_REPORTED = 20

TELLS = [
    (re.compile(r"\bno es\b[^.;]{1,50}[,;]\s*(es|sino)\b", re.I),
     'corrective antithesis "no es X, es Y"; state Y only'),
    (re.compile(r"\bnot\b[^.;]{1,50}\bbut\b", re.I),
     'corrective antithesis "not X but Y"; state Y only'),
]


def scan(lines):
    """Return [(lineno, reason)] for prose lines only."""
    hits, in_fence = [], False
    for n, raw in enumerate(lines, 1):
        if FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = CODE_SPAN.sub("", raw)
        for pat, why in TELLS:
            if pat.search(line):
                hits.append((n, why))
    return hits


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    path = (event.get("tool_input") or {}).get("file_path") or ""
    if not path.endswith(".md") or (EXEMPT_PATH and EXEMPT_PATH.search(path)):
        return 0
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0

    hits = scan(lines)
    if not hits:
        return 0
    print("Speaking violations in written markdown:", file=sys.stderr)
    for n, why in hits[:MAX_REPORTED]:
        print(f"  {path}:{n}: {why}", file=sys.stderr)
    if len(hits) > MAX_REPORTED:
        print(f"  ... {len(hits) - MAX_REPORTED} more", file=sys.stderr)
    return 2


def selftest():
    flagged = [
        "esto no es una regla, es una capa",
        "not a rule but a layer",
    ]
    clean = [
        "prose with — dash: judged against the skill, never matched here",
        "rango 2020–2024 en prosa",
        "el gate corre —en el workspace— y este archivo lo encuentra",
        "plain declarative line",
        "no es suficiente. Falta el hook.",  # separated by a period
        "corregido: `mapper.ts:88`",
    ]
    for line in flagged:
        assert scan([line]), f"missed tell: {line}"
    for line in clean:
        assert not scan([line]), f"false positive: {line}"

    fenced = ["```", "code: no es X, es Y exempt", "```", "prose: no es X, es Y flagged"]
    hits = scan(fenced)
    assert [n for n, _ in hits] == [4], f"fence handling broken: {hits}"

    unclosed = ["```", "code: no es X, es Y exempt to EOF"]
    assert not scan(unclosed), "unclosed fence should stay exempt"
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    sys.exit(main())
