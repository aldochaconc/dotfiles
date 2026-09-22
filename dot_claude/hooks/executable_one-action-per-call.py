#!/usr/bin/env python3
"""PreToolUse(Bash): split a command that chains distinct actions with `&&`.

The Shell section of CLAUDE.md says setup, check and effect go in separate calls, because a
permission rule matches the whole command line: `rm -f tsconfig.tsbuildinfo && npm run
type-check` prompts as a deletion and hides what is being deleted behind the rest of the line.
The rule existed and was not followed, so this hook states the split.

`permissionDecision: "ask"` with the calls written out, not exit 2. Chaining is a style rule,
not a danger: the command is legal and the user may have a reason, so the decision is theirs.
tracked-rm.py and destructive-git.py exit 2 because there the alternative form is mandatory.

What does NOT match is the point of the file. `&&` inside one action is the common case and a
hook that flags it is worse than no hook, so a chain passes when:
  - every segment shares the same head command (`git add a && git add b`);
  - the chain is a guard, a test or a `[` reading state before one effect;
  - it is `cd` into a directory followed by work there, which is one action in two verbs;
  - any segment carries a shell construct that cannot be split: a loop, a function, a heredoc,
    a pipeline into the next segment, a `||` fallback that belongs to one attempt.
A chain matches only when two or more segments are distinct EFFECTS: commands that change
state on their own and would each carry their own permission decision.

Self-check: python3 one-action-per-call.py --selftest
"""
import json
import re
import shlex
import sys

# Commands that change state. A chain of two of these is what the rule is about: each would
# carry its own permission decision, and joining them hides the first behind the line.
EFFECT = {
    "rm", "mv", "cp", "install", "tee", "truncate", "dd", "mkfs", "chmod", "chown", "ln",
    "npm", "pnpm", "yarn", "pip", "cargo", "make", "pacman", "systemctl", "chezmoi",
    "curl", "wget", "ssh", "scp", "rsync", "docker", "kubectl", "gh", "omarchy",
}
# Reading state never counts as an effect, whatever it is chained to.
READONLY = {
    "cd", "echo", "printf", "test", "[", "true", "false", "ls", "cat", "grep", "find", "wc",
    "head", "tail", "sed", "awk", "which", "command", "pwd", "diff", "stat", "sort", "uniq",
    "jq", "python3", "node", "date", "env", "export", "read", "mkdir", "touch", "set",
}
# A construct that cannot survive being cut at `&&`.
UNSPLITTABLE = re.compile(r"\b(for|while|until|if|case|function)\b|<<|\|\||\$\(|`|\{|\}")


def head(segment):
    """The command a segment runs, ignoring env assignments and `sudo`-like prefixes."""
    try:
        words = shlex.split(segment)
    except ValueError:
        return None
    for w in words:
        if "=" in w and not w.startswith("-"):
            continue
        if w in {"sudo", "pkexec", "command", "exec", "nohup", "time", "rtk", "proxy"}:
            continue
        return w.split("/")[-1]
    return None


def effects(command):
    """The distinct effect heads in a top-level `&&` chain, or [] when it must not split."""
    if UNSPLITTABLE.search(command):
        return []
    # Only split on `&&` outside quotes; a quoted `&&` is data, not a connector.
    segments, buf, quote, i = [], "", None, 0
    while i < len(command):
        c = command[i]
        if quote:
            if c == quote:
                quote = None
            buf += c
        elif c in "'\"":
            quote = c
            buf += c
        elif c == "&" and command[i:i + 2] == "&&":
            segments.append(buf)
            buf = ""
            i += 1
        elif c in ";|":
            # A pipeline or a sequence is not this hook's business.
            return []
        else:
            buf += c
        i += 1
    segments.append(buf)
    if len(segments) < 2:
        return []

    heads = [head(s) for s in segments]
    if any(h is None for h in heads):
        return []
    if len(set(heads)) == 1:
        return []          # `git add a && git add b` is one action in two calls
    found = [h for h in heads if h in EFFECT and h not in READONLY]
    return found if len(found) >= 2 else []


def main(event=None):
    try:
        event = event if event is not None else json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, EOFError):
        return 0
    if (event.get("tool_name") or "") != "Bash":
        return 0
    command = (event.get("tool_input") or {}).get("command") or ""
    found = effects(command)
    if not found:
        return 0
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": (
            "One action per Bash call (CLAUDE.md, Shell). This line chains distinct effects: "
            + ", ".join(found)
            + ". A permission rule matches the whole command line, so the first effect is "
            "hidden behind the rest and prompts as something else. Send each as its own "
            "call, in order, unless this line has to run as one.")}}))
    return 0


def selftest():
    # chained distinct effects: the case the rule is about
    for cmd in [
        "rm -f tsconfig.tsbuildinfo && npm run type-check",
        "cp a b && systemctl --user restart x",
        "chezmoi apply && omarchy restart shell",
    ]:
        assert effects(cmd), cmd

    # one action, must not fire
    for cmd in [
        "git add a && git add b",                      # same head
        "cd /tmp && ls",                               # readonly pair
        "mkdir -p x && cd x",                          # setup, no effect head
        "test -f x && rm x",                           # guard before one effect
        "grep -q foo file && npm run build",           # check before one effect
        "npm ci && npm test",                          # same head
        "for f in *; do rm $f; done && echo ok",       # loop
        "cat <<'EOF' > f && rm g\nx\nEOF",             # heredoc
        "rm a || true && echo x",                      # || fallback
        "echo 'a && b' && ls",                         # quoted &&
        "rm a | tee log && ls",                        # pipeline
        "rm a; npm test",                              # sequence, not &&
        "npm run build",                               # no chain
    ]:
        assert not effects(cmd), cmd

    def run(cmd):
        return main({"tool_name": "Bash", "tool_input": {"command": cmd}})

    import io, contextlib

    def verdict(cmd):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main({"tool_name": "Bash", "tool_input": {"command": cmd}})
        out = buf.getvalue().strip()
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None

    assert verdict("rm -f x && npm run build") == "ask"
    assert verdict("git add a && git add b") is None
    assert main({"tool_name": "Read", "tool_input": {}}) == 0

    print("selftest ok: 3 chained + 13 single + 3 verdict")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
