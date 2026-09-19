#!/usr/bin/env bash
set -euo pipefail

# pr_sync_comments.sh
# Emit a JSON bundle of "new/updated PR feedback since last sync" and advance the sync checkpoint.
#
# Usage:
#   scripts/pr_sync_comments.sh                 # auto-detect PR for current branch
#   scripts/pr_sync_comments.sh 123             # explicit PR number
#   scripts/pr_sync_comments.sh 123 path/to/state.json
#
# Output schema:
# {
#   "pr": 123,
#   "since": "2026-01-01T00:00:00Z",
#   "syncStartedAt": "2026-01-13T12:34:56Z",
#   "issueComments": [...],
#   "inlineReviewComments": [...],
#   "reviews": [...]
# }
#
# Notes:
# - We update the checkpoint to *syncStartedAt* (captured before any API calls).
#   This prevents missing comments created mid-sync in streams that were already queried.
# - You may see duplicates across syncs. De-dupe by (id, updated_at) and ignore comments by your own login.

PR_REF="${1:-}"
STATE_FILE="${2:-}"
if [[ -z "${STATE_FILE}" ]]; then
  if GIT_DIR="$(git rev-parse --git-dir 2>/dev/null)"; then
    STATE_FILE="${GIT_DIR}/agent-state/gh-pr-ops-state.json"
  elif [[ -n "${XDG_STATE_HOME:-}" ]]; then
    STATE_FILE="${XDG_STATE_HOME}/agent-state/gh-pr-ops-state.json"
  elif [[ -n "${HOME:-}" ]]; then
    STATE_FILE="${HOME}/.local/state/agent-state/gh-pr-ops-state.json"
  elif [[ -n "${TMPDIR:-}" ]]; then
    STATE_FILE="${TMPDIR%/}/agent-state/gh-pr-ops-state.json"
  else
    STATE_FILE="/tmp/agent-state/gh-pr-ops-state.json"
  fi
fi

# Resolve PR number
if [[ -z "${PR_REF}" ]]; then
  PR_REF="$(gh pr view --json number -q .number)"
fi

if [[ "${PR_REF}" =~ ^[0-9]+$ ]]; then
  PR_NUMBER="${PR_REF}"
else
  PR_NUMBER="$(gh pr view "${PR_REF}" --json number -q .number)"
fi

mkdir -p "$(dirname "${STATE_FILE}")"

SINCE="1970-01-01T00:00:00Z"
if [[ -f "${STATE_FILE}" ]]; then
  # jq is required for state file parsing
  SINCE="$(jq -r '.since // "1970-01-01T00:00:00Z"' "${STATE_FILE}")"
fi

SYNC_STARTED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# 1) PR Conversation comments (issue comments)
ISSUE_PAGES="$(gh api -X GET repos/{owner}/{repo}/issues/${PR_NUMBER}/comments   -f since="${SINCE}"   --paginate --slurp)"

# 2) Inline review comments (Files changed comments + replies)
INLINE_PAGES="$(gh api -X GET repos/{owner}/{repo}/pulls/${PR_NUMBER}/comments   -f since="${SINCE}" -f sort=updated -f direction=asc   --paginate --slurp)"

# 3) Reviews (top-level review bodies). No since param; filter client-side.
REVIEWS_PAGES="$(gh api repos/{owner}/{repo}/pulls/${PR_NUMBER}/reviews   --paginate --slurp)"

jq -n   --arg pr "${PR_NUMBER}"   --arg since "${SINCE}"   --arg syncStartedAt "${SYNC_STARTED_AT}"   --argjson issuePages "${ISSUE_PAGES}"   --argjson inlinePages "${INLINE_PAGES}"   --argjson reviewsPages "${REVIEWS_PAGES}"   '
  def flatten_pages: (add // []);

  {
    pr: ($pr|tonumber),
    since: $since,
    syncStartedAt: $syncStartedAt,

    issueComments: ($issuePages | flatten_pages),
    inlineReviewComments: ($inlinePages | flatten_pages),

    # reviews are filtered to those submitted after the previous checkpoint
    reviews: (
      $reviewsPages
      | flatten_pages
      | map(select(.submitted_at != null and .submitted_at > $since))
    )
  }'

# Advance checkpoint to the start of this sync (safe against mid-sync arrivals)
jq -n   --arg pr "${PR_NUMBER}"   --arg since "${SYNC_STARTED_AT}"   '{pr: ($pr|tonumber), since: $since}' > "${STATE_FILE}"
