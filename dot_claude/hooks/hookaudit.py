#!/usr/bin/env python3
"""Record what a hook decided, for hooks that block, deny or ask.

command-audit.log answers what ran. It cannot answer what a hook stopped, because a blocked
command never runs and never reaches it: a hook that works erases its own evidence. Asking
whether `tracked-rm` still earns its place meant re-running it over two weeks of history to
reconstruct verdicts nothing had stored.

One line per verdict, tab separated, so a count is a `grep -c` and a review is a `cut`:

    2026-09-22T17:40:11	destructive-git	block	git checkout -- config.json

The command is stored whole. Without it a count says a hook fired and not whether it should
have, which is the question a false positive raises, and every false positive this session
produced was found by reading the command.

Nothing here can change a verdict. Every failure path returns silently: a full disk, a
read-only home or a race on the rename leaves the hook deciding exactly as it would with no
log at all. A gate that stops working because its logging broke is worse than an unlogged one.

Self-check: python3 hookaudit.py --selftest
"""
import os
import sys
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(os.path.expanduser("~/.claude/hooks/hook-verdicts.log"))
MAX_BYTES = 4 * 1024 * 1024
KEEP = 3


def _rotate(path, max_bytes, keep):
    """Rename past max_bytes and unlink the oldest beyond keep. Silent on any failure."""
    try:
        if path.stat().st_size < max_bytes:
            return None
    except OSError:
        return None

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = path.with_name(f"{path.name}.{stamp}")
    n = 1
    while target.exists():
        target = path.with_name(f"{path.name}.{stamp}-{n}")
        n += 1
    try:
        path.rename(target)
    except OSError:
        return None

    # By mtime, never by name, for the same reason command-audit.py sorts that way: a
    # hand-made suffix sorts after every dated one and a name sort would keep the wrong file.
    try:
        rotated = sorted(path.parent.glob(f"{path.name}.*"), key=lambda f: f.stat().st_mtime)
    except OSError:
        return target
    for old in rotated[:-keep] if keep else rotated:
        try:
            old.unlink()
        except OSError:
            pass
    return target


def record(hook, verdict, command, path=LOG_PATH, max_bytes=MAX_BYTES, keep=KEEP):
    """Append one verdict line. Returns True when written, False on any failure."""
    if not hook or not verdict:
        return False
    # Tabs and newlines are the field and record separators, so a command carrying either
    # would split into columns that were never fields. A heredoc writing a skill does.
    flat = " ".join((command or "").split())
    line = f"{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}\t{hook}\t{verdict}\t{flat}\n"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        _rotate(path, max_bytes, keep)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line)
        return True
    except OSError:
        return False


def selftest():
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        log = Path(d) / "v.log"

        assert record("gate", "ask", "echo x > SKILL.md", path=log)
        assert record("tracked-rm", "block", "rm src/a.ts", path=log)
        rows = [l.rstrip("\n").split("\t") for l in log.read_text().splitlines()]
        assert len(rows) == 2, rows
        assert rows[0][1:] == ["gate", "ask", "echo x > SKILL.md"], rows[0]
        assert rows[1][1] == "tracked-rm"
        # the timestamp is sortable, which is what makes `sort` on this file meaningful
        assert rows[0][0][:4].isdigit() and "T" in rows[0][0]

        # a multi-line command stays one record
        assert record("gate", "ask", "cat <<'EOF' > a\nx\nEOF", path=log)
        assert len(log.read_text().splitlines()) == 3
        assert "\n" not in log.read_text().splitlines()[2]

        # a tab inside the command does not invent a column
        assert record("gate", "ask", "echo a\tb", path=log)
        assert len(log.read_text().splitlines()[3].split("\t")) == 4

        # missing hook or verdict writes nothing
        assert not record("", "ask", "x", path=log)
        assert not record("gate", "", "x", path=log)
        assert len(log.read_text().splitlines()) == 4

        # an empty command still records: the verdict is the fact
        assert record("gate", "deny", "", path=log)

        # rotation keeps `keep` files and the live log restarts empty
        rot = Path(d) / "r.log"
        for i in range(60):
            record("h", "block", "x" * 200, path=rot, max_bytes=1024, keep=2)
        assert rot.exists()
        assert len(list(Path(d).glob("r.log.*"))) <= 2, list(Path(d).glob("r.log.*"))

        # an unwritable path never raises, it reports False
        assert not record("h", "block", "x", path=Path("/proc/nonexistent/x.log"))

    print("selftest ok: 2 write + 2 escaping + 3 guard + 2 rotation + 1 failure")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 0)
