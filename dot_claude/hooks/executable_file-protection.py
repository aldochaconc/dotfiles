#!/usr/bin/env python3
"""Block edits to lock files, generated files, and production configs."""
import json
import sys
import os

# Exact filenames to block (matched against basename)
BLOCKED_BASENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "poetry.lock",
    "composer.lock",
    "Gemfile.lock",
    "go.sum",
    "uv.lock",
}

# Path patterns to block (substring match)
BLOCKED_PATTERNS = [
    "/dist/",
    "/build/",
    "/node_modules/",
    "/.git/",
    "__pycache__/",
    ".min.js",
    ".min.css",
]

try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, EOFError):
    sys.exit(0)

file_path = data.get("tool_input", {}).get("file_path", "")
if not file_path:
    sys.exit(0)

basename = os.path.basename(file_path)

# Check exact basename matches
if basename in BLOCKED_BASENAMES:
    print(
        f"BLOCKED: '{basename}' is a lock/generated file. "
        f"Do not edit it directly — run the package manager instead.",
        file=sys.stderr,
    )
    sys.exit(2)

# Check path pattern matches
for pattern in BLOCKED_PATTERNS:
    if pattern in file_path:
        print(
            f"BLOCKED: '{file_path}' matches protected pattern '{pattern}'. "
            f"This looks like a generated/vendor file — do not edit.",
            file=sys.stderr,
        )
        sys.exit(2)

sys.exit(0)
