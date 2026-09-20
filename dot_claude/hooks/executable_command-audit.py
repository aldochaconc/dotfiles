#!/usr/bin/env python3
"""Log every Bash command Claude runs with timestamp and description.

Rotates before writing: past MAX_BYTES the log is renamed with the date of its last
line and a new one starts. Measured 2026-09-08 at 32 MB and 310.130 lines with no
rotation in place, growing about 150.000 lines a month, and a single `.bak.20260321`
showing the shape had been applied once by hand.

KEEP is the number of rotated files that survive. The oldest is unlinked, because an
audit log answers what ran recently and a year of it answers nothing anyone asks.

Self-check: python3 command-audit.py --selftest
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(os.path.expanduser("~/.claude/hooks/command-audit.log"))
MAX_BYTES = 8 * 1024 * 1024
KEEP = 3


def rotate(path=LOG_PATH, max_bytes=MAX_BYTES, keep=KEEP):
    """Rename the log when it passes max_bytes, and unlink the oldest beyond keep."""
    try:
        if path.stat().st_size < max_bytes:
            return None
    except OSError:
        return None

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = path.with_name(f"{path.name}.{stamp}")
    # Two rotations inside one second would collide on the name and the rename would
    # overwrite the first, losing a whole file.
    n = 1
    while target.exists():
        target = path.with_name(f"{path.name}.{stamp}-{n}")
        n += 1
    try:
        path.rename(target)
    except OSError:
        return None

    # By mtime, never by name: the hand-made `.bak.20260321` sorts after every dated
    # rotation lexically, so a name sort would read it as the newest and unlink the rest.
    rotated = sorted(path.parent.glob(f"{path.name}.*"), key=lambda f: f.stat().st_mtime)
    for old in rotated[:-keep] if keep else rotated:
        try:
            old.unlink()
        except OSError:
            pass
    return target


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return 0

    ti = data.get("tool_input") or {}
    command = ti.get("command") or ""
    if not command:
        return 0

    description = ti.get("description") or "No description"
    cwd = data.get("cwd", "?")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rotate()
    try:
        with LOG_PATH.open("a") as f:
            f.write(f"[{timestamp}] [{cwd}] {command}  # {description}\n")
    except OSError:
        pass
    return 0


def _selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        log = Path(d) / "t.log"

        # under the threshold: nothing moves
        log.write_text("x" * 100)
        assert rotate(log, max_bytes=1000) is None
        assert log.exists() and log.stat().st_size == 100

        # over it: renamed, and the original is gone
        log.write_text("y" * 2000)
        t = rotate(log, max_bytes=1000)
        assert t is not None and t.exists(), t
        assert not log.exists()
        assert t.read_text() == "y" * 2000

        # two rotations in one second take distinct names
        log.write_text("a" * 2000); r1 = rotate(log, max_bytes=1000, keep=9)
        log.write_text("b" * 2000); r2 = rotate(log, max_bytes=1000, keep=9)
        assert r1 != r2, (r1, r2)
        assert r1.read_text() == "a" * 2000 and r2.read_text() == "b" * 2000

        # keep=2 leaves the two newest by mtime, and a name that sorts last does not win
        for n, name in enumerate(["t.log.bak.19990101", "t.log.20260101-000000"]):
            f = Path(d) / name; f.write_text("old"); os.utime(f, (n, n))
        log.write_text("c" * 2000)
        r3 = rotate(log, max_bytes=1000, keep=2)
        left = sorted(f.name for f in Path(d).glob("t.log.*"))
        assert len(left) == 2, left
        assert r3.name in left, (r3.name, left)
        assert "t.log.bak.19990101" not in left, left

        # a missing log is not an error
        assert rotate(Path(d) / "absent.log") is None

    print("ok: 4 threshold + 1 keep + 1 missing cases")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
        sys.exit(0)
    sys.exit(main())
