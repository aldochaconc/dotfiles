#!/usr/bin/env bash
# pre-pr-gate.sh — Claude Code PreToolUse hook
# Fires before every Bash tool call. When a PR-creation or push command is
# detected, emits a reminder to run the full CI suite locally first.
# Exit 0 (soft gate): warns Claude but does not block the command.

set -euo pipefail

input=$(cat)

# Extract the bash command from the JSON tool input.
cmd=$(printf '%s' "$input" | python3 -c \
  "import sys, json; d=json.load(sys.stdin); print(d.get('command', ''))" \
  2>/dev/null || true)

# Detect PR creation / stack submission / push patterns.
if printf '%s' "$cmd" | grep -qE \
  'gh pr create|gt submit|gt stack submit'; then
  cat <<'MSG'
[pre-PR gate] Before opening this PR, confirm the full CI suite passes locally.
Check docs/agents/testing.md for this repo's required commands.
Do not proceed until all checks pass.
MSG
fi

exit 0
