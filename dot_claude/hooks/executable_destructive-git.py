#!/usr/bin/env python3
"""PreToolUse(Bash): hard-block git commands that discard work.

`reset --hard`, `checkout -- <path>`/`checkout .`, `clean -f`, `stash drop`/`stash clear`, and any
push with `--force`/`-f`/`--force-with-lease` erase commits, working-tree edits, or remote history
with no undo. The Git section of CLAUDE.md already says these are never run to fix a mistake this
session caused; this hook makes that true regardless of the permissions allowlist, model, or
pressure in the moment; being listed under `ask` in settings.json is for the user to decide, not a
plausible reason to decide it here.

`checkout <tree-ish> -- <path>`, `checkout -- <path>` and `restore` over a path, `--source`
included, pass when git reports no uncommitted change, staged or unstaged, in any of the named
paths: a path fresh from a new worktree, or never touched since the commit it was checked out
at, has nothing for the command to overwrite. `--source`'s own value is read as the tree-ish it
is, not as a path. `checkout .` and `restore .`, a glob, a directory, or a path the tokenizer
cannot resolve are not narrowed this way and are refused as before, since nothing short of
naming every path lets this hook confirm nothing is lost. A call with any changed path is
refused and names which ones.

Exit 2 always: there is no allowed form of these commands from this hook, only a human running
them directly.

Self-check: python3 destructive-git.py --selftest
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

# A dangling link or a broken module must never fail the hook: it falls back to the patterns.
try:
    import shell
except Exception:
    shell = None

# The calls come from `shell.py`, the shephrd plugin's parser, linked beside this file by
# chezmoi: each git call's subcommand is found past its global options, and the patterns below
# are matched against that call alone. `git restore` passes when git reports nothing to discard
# for its paths. Measured on 2026-09-30 against the patterns alone: `git restore` on a missing or
# clean path and quoted text naming a command were blocked. A line the parser declines is
# matched raw, as the rest of this comment describes.
#
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

# Options git takes before the subcommand. `git -C <dir> reset --hard` discards exactly what the
# bare form does, and the patterns once required the subcommand right after `git`, so every
# `-C` form passed unexamined: measured on 2026-09-23, a session resolving a merge in a worktree
# ran `git -C <worktree> checkout ...` and nothing here read it.
GIT = (r"git(?:\s+(?:-[Cc]\s+(?:\"[^\"]*\"|'[^']*'|\S+)"
       r"|--(?:git-dir|work-tree|namespace)=\S+|--no-pager|--no-optional-locks))*\s+")

# `checkout --theirs` and `--ours` resolve a conflict: they write one side's stage into the
# working tree while the index keeps both, so `git checkout -m -- <path>` recreates the conflict.
# Outside a conflict git refuses them, since the path has no such stage. Neither discards work.
SIDES = r"(?![^|;&\n]*\s--(?:theirs|ours)\b)"

PATTERNS = [
    (re.compile(SEGMENT + GIT + r"reset\b[^|;&\n]*--hard\b"), "git reset --hard"),
    (re.compile(SEGMENT + GIT + r"checkout\b" + SIDES + r"[^|;&\n]*\s(--\s|\.\s*$|\.$)"),
     "git checkout over a path"),
    (re.compile(SEGMENT + GIT + r"clean\b[^|;&\n]*-\w*f\w*"), "git clean -f"),
    (re.compile(SEGMENT + GIT + r"stash\s+(drop|clear)\b"), "git stash drop/clear"),
    # `git restore` is `git checkout -- <path>` in the newer syntax and overwrites the file with
    # no undo. `--staged` alone only unstages, leaving the working tree intact, so it is the
    # `git reset HEAD` of that syntax and is not gated. Everything else is: the bare form
    # defaults to `--worktree`, and `--staged --worktree` together do discard.
    (re.compile(SEGMENT + GIT + r"restore\b(?![^|;&\n]*--staged(?![^|;&\n]*--worktree))"),
     "git restore over a path"),
    (re.compile(SEGMENT + GIT + r"push\b[^|;&\n]*(--force\b|--force-with-lease\b|\s-f\b)"),
     "git push --force"),
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


GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env",
                     "--exec-path", "--super-prefix"}


def _changed_paths(rest, gdir):
    """The paths among `rest` that `git status --porcelain` reports changed, staged or unstaged,
    in `gdir`, or None when the call cannot be narrowed to a path-by-path answer: `.`, a glob, a
    directory, no paths at all, or a git error. None is the discarding answer everywhere this is
    used, since a path that cannot be checked one by one is treated as changed.

    Each path is asked on its own and any output counts as changed. Porcelain prints paths from
    the repository root, so matching its lines against paths given from a subdirectory read every
    path there as clean, and a staged rename prints `old -> new`, which matched neither.
    """
    paths = [w for w in rest if not w.startswith("-")]
    if not paths or "." in paths or any(c in p for p in paths for c in "*?["):
        return None
    if any(os.path.isdir(os.path.join(gdir, p)) for p in paths):
        return None
    changed = []
    for p in paths:
        try:
            r = subprocess.run(["git", "-C", gdir, "status", "--porcelain", "--", p],
                               capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            return None
        if r.returncode != 0:
            return None
        if r.stdout.strip():
            changed.append(p)
    return changed


def _restore_paths(rest):
    """The path arguments of `git restore <rest>` (past the subcommand): every word but the
    flags, with `-s`/`--source`'s own value dropped too, since it names a tree-ish and not a
    path. `--source=X` carries no separate value word; `-s X` and `--source X` do.
    """
    paths, skip = [], False
    for w in rest:
        if skip:
            skip = False
            continue
        if w in ("-s", "--source"):
            skip = True
            continue
        if w.startswith("-"):
            continue
        paths.append(w)
    return paths


def _checkout_changed(rest, gdir):
    """The changed paths among a `git checkout <rest>` call's targets (already known to match
    the "over a path" pattern), or None when the call cannot be narrowed path by path.

    `rest` is `[<tree-ish>?, "--", <path>...]` or `["--", <path>...]` once the pattern has
    matched, or ends in a bare `.`; the paths are whatever follows `--`, or every non-flag word
    when there is no `--` (the bare-`.` form, which `_changed_paths` already treats as
    unnarrowable).
    """
    if "--" in rest:
        paths = rest[rest.index("--") + 1:]
    else:
        paths = [w for w in rest if not w.startswith("-")]
    return _changed_paths(paths, gdir)


def parsed_hits(command, cwd):
    """What the parsed git calls would discard, or None when the parser declines: no `shfmt` or
    `shell.py`, a parse error, or a git call whose words are only known after expansion or
    arrive on stdin."""
    if shell is None:
        return None
    try:
        cmds = shell.commands(command, cwd)
    except Exception:
        return None
    if cmds is None:
        return None
    found = []
    for c in cmds:
        if Path(c.argv[0]).name != "git":
            continue
        if c.stdin or None in c.argv:
            return None
        i, gdir = 1, c.cwd
        while i < len(c.argv) and c.argv[i].startswith("-"):
            if c.argv[i] in GLOBAL_WITH_VALUE and i + 1 < len(c.argv):
                if c.argv[i] == "-C":
                    gdir = os.path.normpath(os.path.join(gdir, os.path.expanduser(c.argv[i + 1])))
                i += 2
            else:
                i += 1
        rest = c.argv[i:]
        # The subcommand opens the rebuilt line, so a pattern can only match the real call:
        # quoted text naming a command never reaches it.
        line = "git " + " ".join(shlex.quote(w) for w in rest)
        why = [w for pat, w in PATTERNS if pat.match(line)]
        if why and rest and rest[0] == "restore":
            changed = _changed_paths(_restore_paths(rest[1:]), gdir)
            if changed is not None and not changed:
                continue
            if changed:
                why = [w if w != "git restore over a path"
                       else f"git restore over a path (changed: {', '.join(changed)})"
                       for w in why]
        elif why and rest and rest[0] == "checkout" and "git checkout over a path" in why:
            changed = _checkout_changed(rest[1:], gdir)
            if changed is not None and not changed:
                why = [w for w in why if w != "git checkout over a path"]
            elif changed:
                why = [w if w != "git checkout over a path"
                       else f"git checkout over a path (changed: {', '.join(changed)})" for w in why]
        found += why
    return found


def hits(command, cwd=None):
    if "git" not in command:
        return []
    found = parsed_hits(command, cwd or os.getcwd())
    if found is not None:
        return found
    return [why for pat, why in PATTERNS if pat.search(command)]


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    command = (event.get("tool_input") or {}).get("command") or ""
    found = hits(command, event.get("cwd"))
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
        # Options before the subcommand change nothing about what it discards.
        "git -C /tmp/wt reset --hard",
        "git -C /tmp/wt checkout -- docs/a.md",
        "git -C '/tmp/a b' checkout .",
        "git -c core.pager=cat -C /tmp/wt clean -fd",
        "git --no-pager -C /tmp/wt restore src/app.ts",
        "git --git-dir=/x/.git --work-tree=/x push --force",
        "git -C /tmp/wt stash drop",
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
        # A conflict side keeps both stages in the index, so `checkout -m` undoes it.
        "git checkout --theirs -- docs/specs/architecture.md",
        "git -C /tmp/wt checkout --theirs -- docs/specs/architecture.md",
        "git -C /tmp/wt checkout --ours .",
        "git -C /tmp/wt status",
        "git -C /tmp/wt push origin main",
        # Prose that names a command instead of running one. The hook blocked all of these
        # before the anchor, including an instruction against the command it flagged.
        'herdr agent prompt wA:p8 "no uses git push --force aqui"',
        'gh pr comment 938 --body "avoid git push --force"',
        'echo "never run git reset --hard"',
    ]
    import tempfile

    parser = shell is not None and shell.available()
    skipped = 0
    with tempfile.TemporaryDirectory() as root:
        # Outside any work tree `git status` fails, so every restore above counts as discarding.
        for c in flagged:
            assert hits(c, root), f"missed: {c}"
        for c in clean:
            assert not hits(c, root), f"false positive: {c}"
        # Quoted text whose first words are the command: the parser reads it as an argument, and
        # the patterns alone take the quote as the anchor and block it.
        for c in ["echo 'git reset --hard' > notes.txt", "grep -rn 'git push --force' docs/"]:
            assert bool(hits(c, root)) is not parser, c

        # A: a.txt modified, c.txt clean, d/ a tracked directory; N outside any work tree.
        a, n = os.path.join(root, "A"), os.path.join(root, "N")
        os.makedirs(os.path.join(a, "d"))
        os.makedirs(n)
        subprocess.run(["git", "init", "-q", a], check=True)
        for f in ("a.txt", "c.txt", "d/b.txt"):
            Path(a, f).write_text("v1\n")
        subprocess.run(["git", "-C", a, "add", "."], check=True)
        subprocess.run(["git", "-C", a, "-c", "user.email=x@example.com", "-c", "user.name=x",
                        "commit", "-qm", "i"], check=True)
        Path(a, "a.txt").write_text("v2\n")
        Path(a, "d", "b.txt").write_text("v2\n")  # a dirty path below the repository root

        # A fresh worktree of A, checked out at HEAD: every tracked path is clean in it, the
        # case a `checkout <sha> -- <path>` run once per branch there has nothing to discard.
        wt = os.path.join(root, "WT")
        subprocess.run(["git", "-C", a, "worktree", "add", "-q", wt, "HEAD"], check=True)
        sha = subprocess.run(["git", "-C", a, "rev-parse", "HEAD"], capture_output=True,
                             text=True, check=True).stdout.strip()
        Path(wt, "e.txt").write_text("dirty\n")  # one path in the worktree is modified

        rows = [(a, "git restore nope.txt", False), (n, f"git -C {a} restore nope.txt", False),
                (a, "git restore c.txt", False), (a, "git restore a.txt", True),
                (a, "git restore --staged a.txt", False), (a, f"git -C {a} restore a.txt", True),
                (a, "git restore d", True), (a, "git restore '*.txt'", True),
                # --source names a tree-ish to pull from, not a path, and its own value must not
                # be read as one: c.txt is clean, so --source over it discards nothing.
                (a, "git restore --source=HEAD~1 -- c.txt", False),
                (a, "git restore --source HEAD~1 c.txt", False),
                (a, "git restore --source=HEAD~1 -- a.txt", True),
                (a, "git restore --source HEAD~1 a.txt", True),
                (a, "git restore --source=HEAD~1 -- a.txt c.txt", True),
                # --staged alone still passes untouched; --staged --worktree goes through the
                # same per-path check as every other form.
                (a, "git restore --staged --worktree -- c.txt", False),
                (a, "git restore --staged --worktree -- a.txt", True),
                (a, "git restore --worktree -- a.txt", True), (n, f"cd {a} && git restore a.txt", True),
                (a, "git commit -m 'git push --force later'", False),
                # checkout over a path: the same reading restore already had.
                (a, "git checkout -- c.txt", False), (a, "git checkout -- a.txt", True),
                (a, f"git checkout {sha} -- c.txt", False), (a, f"git checkout {sha} -- a.txt", True),
                (a, "git checkout --theirs -- a.txt", False),  # a conflict side, never gated
                (a, "git checkout .", True), (a, "git checkout -- d", True),
                (a, "git checkout -- '*.txt'", True),
                # A dirty path named from a subdirectory: porcelain prints it from the root.
                (os.path.join(a, "d"), "git checkout -- b.txt", True),
                (os.path.join(a, "d"), "git restore b.txt", True),
                (a, f"git -C {a}/d checkout {sha} -- b.txt", True),
                (a, "git checkout -- d/b.txt", True),
                # A fresh worktree: every path clean, so a checkout over one discards nothing.
                (wt, f"git -C {wt} checkout {sha} -- c.txt", False),
                (wt, f"git checkout {sha} -- c.txt", False),
                (n, f"git -C {wt} checkout {sha} -- c.txt", False),
                # The one dirty path in the worktree still refuses.
                (wt, "git checkout -- e.txt", True),
                # A mixed list: one clean, one dirty path refuses, naming only the dirty one.
                (wt, "git checkout -- c.txt e.txt", True),
                (wt, f"git checkout {sha} -- c.txt e.txt", True)]
        declines = ["git ls-files -m | xargs git restore", "git restore $(git ls-files -m)",
                    "bash -c " + shlex.quote("bash -c " + shlex.quote("bash -c " + shlex.quote(
                        "bash -c " + shlex.quote("git reset --hard"))))]
        if parser:
            for cwd, c, want in rows:
                assert bool(hits(c, cwd)) is want, c
            for c in declines:
                assert parsed_hits(c, a) is None, c
            # The mixed-list denial names the dirty path and not the clean one.
            why = hits(f"git checkout {sha} -- c.txt e.txt", wt)
            assert any("e.txt" in w for w in why) and not any("c.txt" in w for w in why), why
        else:
            skipped = len(rows) + len(declines)

        # With `shell` absent from sys.path the hook runs the patterns: a copy alone in a directory.
        with tempfile.TemporaryDirectory() as alone:
            copy = Path(alone, "destructive-git.py")
            copy.write_text(Path(__file__).read_text())
            for c, code, cwd in [("git restore c.txt", 2, a), ("echo 'git reset --hard' > x", 2, a),
                                 ("git status", 0, a),
                                 # Without shfmt no query is run, so a fresh worktree still
                                 # refuses: today's verdict, unchanged by this fix.
                                 (f"git checkout {sha} -- c.txt", 2, wt),
                                 ("git checkout -- c.txt", 2, a),
                                 ("git restore --source=HEAD~1 -- c.txt", 2, a)]:
                p = subprocess.run([sys.executable, str(copy)], cwd=cwd, capture_output=True,
                                   text=True, env={"PATH": os.environ.get("PATH", "")},
                                   input=json.dumps({"tool_input": {"command": c}, "cwd": cwd}))
                assert p.returncode == code, (c, p.returncode, p.stderr)
    print("selftest ok" + (f" ({skipped} parser rows skipped: no shfmt or no shell.py)"
                           if skipped else ""))


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    sys.exit(main())
