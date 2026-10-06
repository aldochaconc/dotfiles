#!/usr/bin/env python3
"""PreToolUse(Bash): decide `rm`'s `permissionDecision` per target, git-tracked status first.

Measured over 333.973 logged commands: 179 deletions of source files used `rm` against 58 that
used `git rm`. Both delete the file; only `git rm` records the deletion in the index, so the `rm`
form leaves a removal that a later `git add -A` has to catch, and a `git commit <path>` silently
does not. The Shell section of CLAUDE.md says `git rm`; this hook makes it true when the rule is
forgotten mid-session.

Six readings of a target, strictest wins when `rm` names several:

| Target | Verdict |
|---|---|
| a file an earlier command of the same line created, absent before the line (parser only) | `allow`, with no git query |
| tracked by git (a file, or a directory holding one) | `deny`, naming the `git rm` equivalent |
| under `/tmp/<anything>` | `allow` |
| ignored by git (`git check-ignore`: `node_modules`, `dist`, a build artifact) | `allow` |
| untracked, not ignored, inside a repository | `ask` |
| outside any repository and outside `/tmp` | `ask` |

`ask` covers the case measured on 2026-09-24: a pane died mid-task with an untracked 1050-line
workdoc that `git diff` never showed, because nothing short of asking catches a delete that
leaves no trace in either the index or `.gitignore`. A path the parser cannot resolve to a literal
(a variable, an unexpanded glob) reads the same as outside any repository: `ask` rather than a
silent pass.

The commands come from `shell.py`, the shephrd plugin's parser, linked beside this file by
chezmoi. Each path is looked up in the work tree that holds it, from the event's cwd and from any
`cd` before the `rm`.

A file is created by a `>`, `>>` or `>|` redirection, by the destination of `cp` or `mv`, by
`tee` and by `touch`, resolved against the same `cd` chain as the `rm` targets. `mkdir` creates
no file, so `rm -rf` of a directory it made keeps its verdict. An `mv` destination counts only
when its source was itself created in the line, since it holds a file that existed before.

A line the parser declines keeps the pattern below, which answers only tracked-or-not: no
`shfmt`, no plugin, a parse error, or an `rm` whose paths do not arrive as words (`xargs rm`,
`find -exec rm {} +`, `find -delete`).

Self-check: python3 tracked-rm.py --selftest
"""
import json
import os
import re
import shlex
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

# A dangling link or a broken module must never fail the hook: it falls back to the pattern.
try:
    import shell
except Exception:
    shell = None

# The fallback. A path is only worth a git query when the command actually deletes it. `rm`
# inside a quoted string, a variable name ending in "rm", or `git rm` itself must not match.
RM_CALL = re.compile(r"(?:^|[;&|(]|\s)rm\s+(?P<args>[^;&|)\n]*)")

BLOCK, ASK, ALLOW = "block", "ask", "allow"
STRICTNESS = {BLOCK: 2, ASK: 1, ALLOW: 0}


def tracked(path, cwd):
    """True when git knows the path in the work tree containing it. The fallback reading, over
    the raw path text rather than a resolved absolute one."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", path],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


RECURSIVE_FLAGS = {"-r", "-R", "-rf", "-fr", "-Rf", "-fR", "--recursive"}


def _is_recursive(word):
    """Whether a flag word asks `rm` to recurse: `-r`, `-R`, a combined short form such as `-rf`
    or `-fr`, or `--recursive`. A combined form is recognized letter-wise rather than by a fixed
    list, since `-rf`, `-fr`, `-vrf` and `-rvf` are all the same request in a different order."""
    if word in RECURSIVE_FLAGS:
        return True
    if word.startswith("--"):
        return word == "--recursive"
    if word.startswith("-") and len(word) > 1 and "-" not in word[1:]:
        return "r" in word or "R" in word
    return False


def _rm_calls(command):
    """Every `rm` invocation in `command` as `(flag_words, target_words)`, the fallback's own
    split of a matched call's argument text, flags from targets."""
    calls = []
    for match in RM_CALL.finditer(command):
        # `git rm` is the correct form; the regex sees the bare `rm` inside it.
        if command[: match.start("args")].rstrip().endswith("git rm"):
            continue
        try:
            words = shlex.split(match.group("args"))
        except ValueError:
            continue
        flags, paths = [], []
        for word in words:
            if word.startswith(">") or "$" in word or "*" in word:
                continue
            if word.startswith("-"):
                flags.append(word)
            else:
                paths.append(word)
        calls.append((flags, paths))
    return calls


def targets(command):
    """Every path `rm` is called on, flags and redirections dropped. The fallback reading."""
    found = []
    for _flags, paths in _rm_calls(command):
        found.extend(paths)
    return found


def _git_dir_of(path):
    """The directory to run git in for `path`: its own directory if that exists, walking up
    until one does, so a path that does not exist yet (nothing to delete) still resolves."""
    d = os.path.dirname(path)
    while d and not os.path.isdir(d):
        d = os.path.dirname(d)
    return d or "/"


def tracked_abs(path):
    """True when git knows `path` as a file, asked in the work tree that holds it."""
    try:
        result = subprocess.run(
            ["git", "-C", _git_dir_of(path), "ls-files", "--error-unmatch", "--", path],
            capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def tracked_under(path):
    """True when git lists any tracked file at or under `path`, file or directory alike."""
    try:
        result = subprocess.run(
            ["git", "-C", _git_dir_of(path), "ls-files", "--", path],
            capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def ignored(path):
    """True when git ignores `path`, file or directory alike (`git check-ignore` answers both).
    False when `path` is not inside a repository at all: `check-ignore` then has nothing to run
    in, which reads the same as "not ignored" and lets `in_repo` decide."""
    d = _git_dir_of(path)
    try:
        result = subprocess.run(["git", "-C", d, "check-ignore", "-q", "--", path],
                                capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return False
    # Exit 128 means `path` is outside any work tree; only 0 (ignored) counts.
    return result.returncode == 0


def in_repo(path):
    """True when `path` sits inside some git work tree, tracked or not."""
    d = _git_dir_of(path)
    try:
        result = subprocess.run(["git", "-C", d, "rev-parse", "--is-inside-work-tree"],
                                capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def untracked_unignored_under(path):
    """True when `path` itself, or anything under it, is untracked and not ignored.

    For a file this is simply "not tracked and not ignored". For a directory, `git status
    --porcelain` already walks it and reports exactly the untracked files git would otherwise
    silently drop on `rm -rf`, `.gitignore` entries excluded by `--ignored=no` (the default).
    """
    if os.path.isdir(path) and not os.path.islink(path):
        try:
            result = subprocess.run(
                ["git", "-C", _git_dir_of(path), "status", "--porcelain", "--", path],
                capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            return False
        return result.returncode == 0 and any(
            line.startswith("??") for line in result.stdout.splitlines())
    return not tracked_abs(path) and not ignored(path)


def target_verdict(path):
    """The verdict for one resolved path: BLOCK, ASK or ALLOW, by the table in the docstring."""
    if tracked_abs(path) or tracked_under(path):
        return BLOCK
    if path.startswith("/tmp/") or path == "/tmp":
        return ALLOW
    if ignored(path):
        return ALLOW
    if in_repo(path):
        return ASK if untracked_unignored_under(path) else ALLOW
    return ASK


def _resolve(word, cwd_candidates):
    """The first existing absolute path `word` resolves to under any of `cwd_candidates`, or the
    first candidate's join when none exists (a target `rm` would create the absence of)."""
    joined = []
    for base in dict.fromkeys(cwd_candidates):
        full = os.path.normpath(os.path.join(base, os.path.expanduser(word)))
        joined.append(full)
        if os.path.exists(full):
            return full
    return joined[0] if joined else None


_DECLINE = object()  # the parser could not answer this line at all

# Redirections that create the file they name. `Op` is a token number a shfmt release can
# renumber, so the operator is read from the line between `OpPos` and the word instead.
CREATING_REDIRECTS = {">", ">>", ">|"}


def _abs(word, cwd):
    return os.path.normpath(os.path.join(cwd, os.path.expanduser(word)))


def _walk(command, cwd):
    """`(commands, redirects)` for `command`, or None on a decline. `redirects` holds
    `(index, path)` for each file a creating redirection names, `index` being the position in
    `commands` from which the file exists. A redirection inside a nested `bash -c` script is not
    collected, so an `rm` of its file keeps today's verdict."""
    source = (command or "").encode("utf-8")

    class Walk(shell._Walk):
        def __init__(self, cwd, depth):
            super().__init__(cwd, depth)
            self.redirects = []

        # A statement of a list reaches `stmt`; one side of `&&`, `||` or `|` reaches `node`.
        def stmt(self, s):
            super().stmt(s)
            self.record(s)

        def node(self, n):
            super().node(n)
            if isinstance(n, dict) and "Cmd" in n:
                self.record(n)

        def record(self, s):
            if self.depth == 0:
                for r in s.get("Redirs") or []:
                    try:
                        # shfmt offsets count bytes, so the slice is taken on the encoded line.
                        op = source[r["OpPos"]["Offset"]:r["Word"]["Pos"]["Offset"]]
                        op = op.decode("utf-8", "replace").strip()
                    except (KeyError, TypeError):
                        continue
                    target = shell.word(r["Word"])
                    if op in CREATING_REDIRECTS and target:
                        self.redirects.append((len(self.out), _abs(target, self.cwd)))

    tree = shell.parse(command or "")
    if tree is None:
        return None
    w = Walk(cwd or os.getcwd(), 0)
    try:
        w.node(tree)
    except shell.Decline:
        return None
    return w.out, w.redirects


def _positionals(args, valued):
    """`(flags, positionals)` of `args`, a flag in `valued` taking the next word."""
    flags, pos, i, dashdash = [], [], 0, False
    while i < len(args):
        a = args[i]
        if not dashdash and isinstance(a, str) and a == "--":
            dashdash = True
        elif not dashdash and isinstance(a, str) and a.startswith("-") and a != "-":
            flags.append(a)
            if a in valued and i + 1 < len(args):
                flags.append(args[i + 1])
                i += 1
        else:
            pos.append(a)
        i += 1
    return flags, pos


def _created_by(c):
    """`(path, moved_from)` for each file command `c` creates: the destination of `cp` and `mv`,
    each file `tee` writes, each file `touch` makes. `moved_from` is the source of an `mv`, whose
    destination holds the moved file and so passes only when that source was created in the line
    too. A dynamic word creates nothing this hook can name."""
    if not c.argv or c.stdin or not c.argv[0]:
        return []
    name = os.path.basename(c.argv[0])
    args = c.argv[1:]
    if name in ("cp", "mv"):
        flags, pos = _positionals(args, {"-t", "--target-directory", "-S", "--suffix"})
        named = [flags[i + 1] for i, f in enumerate(flags[:-1]) if f in ("-t", "--target-directory")]
        named += [f.split("=", 1)[1] for f in flags
                  if isinstance(f, str) and f.startswith("--target-directory=")]
        if named and not named[-1]:
            return []
        directory = named[-1] if named else None
        if directory is None:
            if len(pos) < 2:
                return []
            dest, pos = pos[-1], pos[:-1]
            if dest is None:
                return []
            into = "-T" not in flags and (len(pos) > 1 or dest.endswith("/")
                                          or os.path.isdir(_abs(dest, c.cwd)))
            if not into:
                if name == "cp":
                    return [(_abs(dest, c.cwd), None)]
                return [(_abs(dest, c.cwd), _abs(pos[0], c.cwd) if pos[0] else False)]
            directory = dest
        out = []
        for src in pos:
            if src is None:
                continue
            path = _abs(os.path.join(directory, os.path.basename(src.rstrip("/"))), c.cwd)
            out.append((path, _abs(src, c.cwd) if name == "mv" else None))
        return out
    if name == "tee":
        _flags, pos = _positionals(args, set())
        return [(_abs(p, c.cwd), None) for p in pos if p]
    if name == "touch":
        flags, pos = _positionals(args, {"-r", "-d", "-t", "--reference", "--date"})
        if any(f == "--no-create" or (f.startswith("-") and not f.startswith("--") and "c" in f)
               for f in flags if isinstance(f, str)):
            return []
        return [(_abs(p, c.cwd), None) for p in pos if p]
    return []


def _parsed_verdict_or_decline(command, cwd):
    """The strictest verdict among every parsed `rm` target, `_DECLINE` when the parser cannot
    answer this line, or None when it answers confidently that nothing needs a decision (no `rm`
    call at all, or every one of them is `git rm` and not the bare command).

    A target an earlier command of the same line created as a file passes with no git query:
    measured on 2026-10-02, a probe test written into a repository, run and removed in one line
    asked on its own cleanup. `mkdir` creates no file, so `rm -rf` on a directory it made keeps
    today's verdict."""
    if shell is None:
        return _DECLINE
    try:
        walked = _walk(command, cwd)
    except Exception:
        return _DECLINE
    if walked is None:
        return _DECLINE
    cmds, redirects = walked
    # A path already on disk was not created by this line: a tracked file truncated by `>`, or a
    # directory `touch` only dated, keeps today's verdict. Read once, before any rm is judged.
    existed = {p for _at, p in redirects if os.path.lexists(p)}
    existed.update(p for c in cmds for p, _m in _created_by(c) if os.path.lexists(p))
    created = set()
    worst = None
    saw_rm = False
    for i, c in enumerate(cmds):
        created.update(p for at, p in redirects if at <= i and p not in existed)
        name = os.path.basename(c.argv[0]) if c.argv and c.argv[0] else ""
        if name != "rm":
            for path, moved_from in _created_by(c):
                # An `mv` destination holds a file that existed before the line; it passes only
                # when that file was itself created in the line.
                if moved_from is False or (moved_from and moved_from not in created):
                    continue
                if path not in existed:
                    created.add(path)
        if name == "find" and "-delete" in c.argv:
            return _DECLINE
        if name != "rm":
            continue
        if c.stdin:
            return _DECLINE
        paths, dashdash = [], False
        for w in c.argv[1:]:
            if w is None:
                # A word only known after expansion: this target cannot be resolved.
                saw_rm = True
                if worst is None or STRICTNESS[ASK] > STRICTNESS[worst]:
                    worst = ASK
                continue
            if w == "--" and not dashdash:
                dashdash = True
            elif (w.startswith("-") and not dashdash) or any(g in w for g in "*?["):
                continue
            else:
                paths.append(w)
        for p in paths:
            saw_rm = True
            if _abs(p, c.cwd) in created:
                v = ALLOW
            else:
                full = _resolve(p, (c.cwd, cwd))
                v = ASK if full is None else target_verdict(full)
            if worst is None or STRICTNESS[v] > STRICTNESS[worst]:
                worst = v
    return worst if saw_rm else None


def parsed_verdict(command, cwd):
    """The strictest verdict among every parsed `rm` target, or None when the parser declines or
    confidently finds no bare `rm` call (only `git rm`, or none at all)."""
    v = _parsed_verdict_or_decline(command, cwd)
    return None if v is _DECLINE else v


def fallback_verdict(command, cwd):
    """The pattern-only reading, used when the parser cannot answer this line at all.

    Tracked wins as before: a path the pattern finds tracked blocks regardless of flags. Failing
    open otherwise is what this reading did before task 6b, and recursive deletion is exactly the
    case a wrong ALLOW here cannot recover from: `rm -rf` on an untracked, un-ignored path (the
    workdoc measured on 2026-09-24, 1050 lines, gone whole) reads the same as `rm -rf` on a build
    directory, since the pattern alone does not run git at all. So a recursive `rm` call with no
    tracked hit asks, unless every literal target of that call starts with `/tmp/`: a path under
    `/tmp` is disposable by the convention `core/blocked.py` and `core/gates.py` already use, and
    asking there would hold a turn on cleanup the user never has to see. A non-recursive `rm`
    keeps today's fallback verdict, tracked-or-nothing, since it cannot delete a directory whole
    and the untracked-workdoc failure mode does not apply to one file named on purpose.
    """
    worst = None
    for flags, paths in _rm_calls(command):
        tracked_hits = [p for p in paths if tracked(p, cwd)]
        if tracked_hits:
            return BLOCK
        if not paths:
            continue
        if any(_is_recursive(f) for f in flags):
            if not all(p.startswith("/tmp/") for p in paths):
                worst = ASK
    return worst


def verdict(command, cwd):
    """The strictest `rm` verdict for `command`, or None when nothing in it needs a decision."""
    parsed = _parsed_verdict_or_decline(command, cwd)
    if parsed is not _DECLINE:
        return parsed
    return fallback_verdict(command, cwd)


def _deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": reason}}))


def _ask(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "ask",
        "permissionDecisionReason": reason}}))


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    command = (event.get("tool_input") or {}).get("command") or ""
    if "rm" not in command:
        return 0

    cwd = event.get("cwd") or os.getcwd()
    v = verdict(command, cwd)
    if v is None or v == ALLOW:
        return 0

    if v == BLOCK:
        record("tracked-rm", "block", command)
        hits = [p for p in targets(command) if tracked(p, cwd)]
        lines = ["BLOCKED: rm on a git-tracked file. Use git rm, which records the deletion in "
                "the index:"]
        for p in hits:
            if os.path.isabs(p):
                lines.append(f"  git -C {shlex.quote(os.path.dirname(p))} rm -- {shlex.quote(p)}")
            else:
                lines.append(f"  git rm -- {shlex.quote(p)}")
        _deny("\n".join(lines))
        print(lines[0], file=sys.stderr)
        return 2

    # v == ASK
    record("tracked-rm", "ask", command)
    _ask("rm on a path this hook cannot confirm is safe to lose: untracked and not ignored by "
        "git, or outside any repository and outside /tmp. Confirm the target is disposable, or "
        "use git rm / move it under /tmp first.")
    return 0


def _fixture(root):
    """Repository A (a.txt modified, c.txt and d/b.txt clean, u.txt untracked), B, and N."""
    a, b, n = (os.path.join(root, x) for x in ("A", "B", "N"))
    for r in (a, b):
        os.makedirs(r)
        subprocess.run(["git", "init", "-q", r], check=True)
    os.makedirs(os.path.join(a, "d"))
    os.makedirs(n)
    for f in ("a.txt", "c.txt", "d/b.txt"):
        Path(a, f).write_text("v1\n")
    Path(b, "z.txt").write_text("z\n")
    for r in (a, b):
        subprocess.run(["git", "-C", r, "add", "."], check=True)
        subprocess.run(["git", "-C", r, "-c", "user.email=x@example.com", "-c", "user.name=x",
                        "commit", "-qm", "i"], check=True)
    Path(a, "a.txt").write_text("v2\n")
    Path(a, "u.txt").write_text("u\n")
    Path(n, "n.txt").write_text("n\n")
    # A directory of build output, listed in .gitignore, inside A.
    Path(a, ".gitignore").write_text("node_modules\ndist\n")
    os.makedirs(os.path.join(a, "node_modules"))
    Path(a, "node_modules", "x.js").write_text("x\n")
    os.makedirs(os.path.join(a, "workdocs"))
    Path(a, "workdocs", "X").write_text("plan\n")
    os.makedirs(os.path.join(a, "d2"))
    Path(a, "d2", "tracked.txt").write_text("t\n")
    Path(a, "d2", "untracked.txt").write_text("u\n")
    subprocess.run(["git", "-C", a, "add", ".gitignore", "d2/tracked.txt"], check=True)
    subprocess.run(["git", "-C", a, "-c", "user.email=x@example.com", "-c", "user.name=x",
                    "commit", "-qm", "j"], check=True)
    return a, b, n


def selftest():
    import tempfile

    failed = 0
    # The fixture repositories must not sit under /tmp themselves: this hook treats every path
    # under /tmp as disposable, and a repo fixture placed there would read as ALLOW before any
    # of its tracked-or-not rows are exercised. ~/.cache is writable, not synced, and not /tmp.
    non_tmp_base = Path(os.path.expanduser("~/.cache/tracked-rm-selftest"))
    non_tmp_base.mkdir(parents=True, exist_ok=True)

    def check(got, want, what):
        nonlocal failed
        if got != want:
            print(f"FAIL {what!r}: want {want}, got {got}")
            failed += 1

    # The fallback reading, unchanged.
    for command, want in [
        ("rm src/a.ts", ["src/a.ts"]),
        ("rm -f src/a.ts src/b.ts", ["src/a.ts", "src/b.ts"]),
        ("cd /x && rm src/a.ts", ["src/a.ts"]),
        ("rm -rf dist", ["dist"]),
        ("git rm src/a.ts", []),
        ("rtk proxy git rm -qf src/a.ts", []),
        ("echo rm", []),
        ("rm -f $TMPFILE", []),
        ("rm -f *.tsbuildinfo", []),
        ("npm run build; rm -f tsconfig.tsbuildinfo", ["tsconfig.tsbuildinfo"]),
    ]:
        check(targets(command), want, command)

    skipped = 0
    with tempfile.TemporaryDirectory(dir=non_tmp_base) as root:
        A, B, N = _fixture(root)
        # (cwd, command, verdict): tracked rows block as before; the new rows exercise each of
        # the five readings and the directory-contents check.
        rows = [
            (A, f"git -C {A} rm a.txt", None), (A, f"git -C {A} rm -r -q d", None),
            (A, f"git -C {A} -c core.x=1 rm a.txt", None), (N, f"git -C {A} rm a.txt", None),
            (A, "grep -n rm a.txt", None), (A, "echo remove with: rm a.txt", None),
            (N, f"rm {A}/a.txt", BLOCK), (B, f"rm {A}/a.txt", BLOCK),
            (N, f"cd {A} && rm a.txt", BLOCK),
            (A, "rm a.txt", BLOCK), (A, f"rm -f {A}/a.txt", BLOCK),
            (A, "git status; rm a.txt", BLOCK),
            (A, f"git -C {A} rm c.txt && rm d/b.txt", BLOCK), (A, 'bash -c "rm a.txt"', BLOCK),
            (A, "rm -f a.txt c.txt", BLOCK), (A, "rm -rf d", BLOCK),
            (A, "npm run build; rm -f c.txt", BLOCK), (A, "'rm' a.txt", BLOCK),
            (A, "rm -- a.txt", BLOCK),
            (A, "sh -c 'rm a.txt'", BLOCK), (A, "(cd d && rm b.txt)", BLOCK),
            (A, "rm ~/nonexistent a.txt", BLOCK), (A, "git rm a.txt", None),
            (A, "rtk proxy git rm -qf a.txt", None), (A, f"cd {A} && git -C . rm a.txt", None),
            (A, "echo rm", None), (A, "git commit -m 'rm a.txt later'", None),
            (A, 'echo "rm a.txt"', None),
            (A, "timeout 5 rm a.txt", BLOCK), (A, "env X=1 rm c.txt", BLOCK),
            (A, "rm -r -- d", BLOCK),
            (A, "cat <<'EOF'\nrm a.txt\nEOF", None),
            # Task 6's new rows.
            (A, "rm -rf /tmp/build-smoke", ALLOW),
            (A, "rm -rf node_modules", ALLOW),
            (A, "rm -rf workdocs/X", ASK),
            (A, "rm $DIR", ASK),
            (A, "rm -rf $DIR", ASK),
            (A, f"cd {A} && rm -rf node_modules && git status", ALLOW),
            (N, "rm -rf anything_here", ASK),
            # d2 holds both a tracked file and an untracked, unignored one: block wins, the
            # strictest verdict among what rm -rf d2 would delete.
            (A, "rm -rf d2", BLOCK),
            # A file an earlier command of the line created passes. The measured line of
            # 2026-10-02: a probe written to a scratchpad, copied into the repo, run, removed.
            (A, f"cat > {root}/probe.ts <<'EOF'\ntest('x', () => {{}})\nEOF\n"
                f"cp {root}/probe.ts tests/x/probe.test.ts && npx jest tests/x; "
                "rm tests/x/probe.test.ts", ALLOW),
            (A, "rm tests/x/probe.test.ts", ASK),
            (A, "echo x > made.txt && rm u.txt", ASK),
            (A, "echo x > made.txt && rm made.txt a.txt", BLOCK),
            (A, "mkdir newdir && rm -rf newdir", ASK),
            (A, "touch newdir/f && rm -rf newdir", ASK),
            (A, "rm made.txt && echo x > made.txt", ASK),
            (A, "echo x > ./d/../made.txt && rm made.txt", ALLOW),
            (A, "cd d && echo x > n.txt && cd .. && rm d/n.txt", ALLOW),
            (A, "echo x >> made.txt; rm made.txt", ALLOW),
            (A, "echo x >| made.txt; rm made.txt", ALLOW),
            (A, "echo x 2> made.txt; rm made.txt", ALLOW),
            (A, "echo x | tee -a made.txt other.txt; rm other.txt", ALLOW),
            (A, "touch made.txt && rm made.txt", ALLOW),
            (A, "touch -c made.txt && rm made.txt", ASK),
            (A, "cp a.txt d && rm d/a.txt", ALLOW),
            (A, "cp -t d a.txt && rm d/a.txt", ALLOW),
            (A, "mv u.txt moved.txt && rm moved.txt", ASK),
            (A, "touch t.txt && mv t.txt moved.txt && rm moved.txt", ALLOW),
            # A path on disk before the line was not created by it.
            (A, "echo x > c.txt && rm c.txt", BLOCK),
            (A, "echo x > u.txt && rm u.txt", ASK),
            (A, "touch d2 && rm -rf d2", BLOCK),
            # A redirection only reads, or only duplicates a descriptor.
            (A, "cat < made.txt; rm made.txt", ASK),
            (A, "echo x > made.txt 2>&1 && rm made.txt", ALLOW),
            # A redirection inside a nested script is not collected.
            (A, "bash -c 'echo x > made.txt' && rm made.txt", ASK),
            (A, "echo 'ñandú' > made.txt && rm made.txt", ALLOW),
        ]
        declines = ["find . -name a.txt | xargs rm", "find . -name a.txt -exec rm {} +",
                    "find . -name a.txt -delete",
                    "bash -c " + shlex.quote("bash -c " + shlex.quote("bash -c " + shlex.quote(
                        "bash -c " + shlex.quote("rm a.txt"))))]
        if shell is not None and shell.available():
            for cwd, command, want in rows:
                check(verdict(command, cwd), want, command)
            for command in declines:
                check(parsed_verdict(command, A), None, command)
        else:
            skipped = len(rows) + len(declines)

        # rm -rf /tmp/build-smoke, outside any fixture repo, under a real scratchpad-style path.
        scratch = Path(root, "claude-scratch")
        scratch.mkdir()
        if shell is not None and shell.available():
            check(verdict(f"rm -rf {scratch}", str(scratch)), ASK,
                  "non-tmp scratch dir, outside any repo")
        check(verdict("rm -rf /tmp/claude-1000/some-session/scratchpad/x", "/"),
              ALLOW if shell is not None and shell.available() else None,
              "a real /tmp scratchpad path")

        # fallback_verdict alone, parser-independent: the three rows task 6b asks for by name.
        check(fallback_verdict("rm -rf workdocs/X", A), ASK, "fallback: rm -rf workdocs/X")
        check(fallback_verdict("rm -rf /tmp/x", A), None, "fallback: rm -rf /tmp/x")
        check(fallback_verdict("rm a.txt", A), BLOCK, "fallback: rm a.txt (tracked)")
        # A plain, non-recursive rm on an untracked path keeps the old fallback verdict: no
        # finding, since one named file is not the untracked-directory failure mode.
        check(fallback_verdict("rm u.txt", A), None, "fallback: rm u.txt (untracked, not -r)")
        # A recursive call naming only /tmp targets stays silent even with several targets.
        check(fallback_verdict("rm -rf /tmp/a /tmp/b", A), None, "fallback: rm -rf /tmp/a /tmp/b")
        # One non-/tmp target among several recursive ones still asks.
        check(fallback_verdict("rm -rf /tmp/a workdocs/X", A), ASK,
              "fallback: rm -rf /tmp/a workdocs/X")

        # With `shell` absent from sys.path the hook runs the pattern alone: tracked blocks
        # (exit 2), a recursive call with no tracked hit and a target outside /tmp asks (exit 0,
        # an "ask" permissionDecision on stdout, not a block), and everything else passes.
        with tempfile.TemporaryDirectory() as alone:
            copy = Path(alone, "tracked-rm.py")
            copy.write_text(Path(__file__).read_text())
            for command, code in [
                    ("grep -n rm a.txt", 2), (f"git -C {A} rm a.txt", 2),
                    ("rm u.txt", 0), ("rm a.txt", 2),
                    # task 6b: the fail-open fix, exercised with no parser at all.
                    ("rm -rf workdocs/X", 0), ("rm -rf /tmp/x", 0), ("rm a.txt", 2)]:
                p = subprocess.run([sys.executable, str(copy)], cwd=A, capture_output=True,
                                   text=True, env={"PATH": os.environ.get("PATH", "")},
                                   input=json.dumps({"tool_input": {"command": command}, "cwd": A}))
                check(p.returncode, code, "without shell: " + command)
            # The two ask/allow rows above both exit 0; what distinguishes them is the
            # permissionDecision each prints, which is what task 6b actually changed.
            # The measured line keeps today's fallback verdict: a non-recursive rm of an
            # untracked path passes, with or without the creation before it.
            for command, decision in [("rm -rf workdocs/X", "ask"), ("rm -rf /tmp/x", None),
                                      ("echo x > made.txt && rm made.txt", None),
                                      ("mkdir newdir && rm -rf newdir", "ask")]:
                p = subprocess.run([sys.executable, str(copy)], cwd=A, capture_output=True,
                                   text=True, env={"PATH": os.environ.get("PATH", "")},
                                   input=json.dumps({"tool_input": {"command": command}, "cwd": A}))
                got = (json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"]
                       if p.stdout.strip() else None)
                check(got, decision, "without shell, decision: " + command)

    print("selftest:", "ok" if not failed else f"{failed} failed",
          f"({skipped} parser rows skipped: no shfmt or no shell.py)" if skipped else "")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
