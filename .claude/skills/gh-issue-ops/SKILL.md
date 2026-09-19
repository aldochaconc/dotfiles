---
name: gh-issue-ops
description: Use GitHub CLI (gh) to list issues, create new issues, edit issues, read new issue comments during an iteration, reply to comments, close issues, and link an issue to a pull request (via PR body keywords and cross-links).
compatibility: Requires git + GitHub CLI (gh) authenticated; network access to GitHub. jq for JSON filtering.
allowed-tools: Bash(gh:*) Bash(git:*) Bash(jq:*) Read Write
---

# gh issue ops

## Core loop (don’t miss new comments)
When iterating on an issue thread, always:
1) **Sync** new comments since your last sync.
2) Draft your response / make any changes (edit issue or open PR, etc.).
3) **Reply**.
4) **Sync again** to confirm nothing new arrived while you were working.

Keep a checkpoint file per issue, e.g. `$(git rev-parse --git-dir)/agent-state/gh-issue-ops-state.json`:
```json
{ "issue": 123, "since": "2026-01-13T00:00:00Z" }
```

## Identify the issue
If you already have the issue number (recommended), set:
```bash
ISSUE=123
```

If you need to find it:
```bash
gh issue list --limit 20
# or search:
gh issue list --search "keywords" --limit 20
```

Get basic issue info (URL, title, state):
```bash
gh issue view "$ISSUE" --json url,title,state,author -q '{url,title,state,author:.author.login}'
```

## List issues
Common filters:
```bash
gh issue list --limit 50
gh issue list --assignee "@me" --limit 50
gh issue list --label "bug" --state open --limit 50
gh issue list --search "crash on startup" --limit 50
```

## Open a new issue
Interactive:
```bash
gh issue create
```

Explicit:
```bash
gh issue create --title "..." --body "..." --label bug --assignee "@me"
```

## Edit an issue
```bash
gh issue edit "$ISSUE" --title "New title"
gh issue edit "$ISSUE" --body "Updated description..."
gh issue edit "$ISSUE" --add-label "triage" --remove-label "wontfix"
gh issue edit "$ISSUE" --add-assignee "@me"
```

## Read issue comments (all, or only new since last sync)

### Read all comments (quick human scan)
```bash
gh issue view "$ISSUE" --comments
```

### Read only NEW/UPDATED comments since `$SINCE` (reliable for iteration)
Use the Issues Comments API with `since`:

```bash
STATE_FILE="$(git rev-parse --git-dir)/agent-state/gh-issue-ops-state.json"
# Load SINCE from your state file (or set manually)
SINCE="$(jq -r '.since // "1970-01-01T00:00:00Z"' "$STATE_FILE" 2>/dev/null || echo "1970-01-01T00:00:00Z")"

gh api -X GET repos/{owner}/{repo}/issues/$ISSUE/comments   -f since="$SINCE"   --paginate   -q '.[] | {id, user: .user.login, created_at, updated_at, body, html_url}'
```

After you’ve processed + responded, update the checkpoint:
```bash
mkdir -p "$(dirname "$STATE_FILE")"
date -u +"%Y-%m-%dT%H:%M:%SZ" | jq -R --argjson issue "$ISSUE" '{issue: $issue, since: .}' > "$STATE_FILE"
```

## Reply to issue comments
Post a comment:
```bash
gh issue comment "$ISSUE" -b "Thanks! I investigated ... Here’s the update: ..."
```

Tip: If replying to a specific person/comment, quote them (or link their comment URL) so the context is clear.

## Close (or reopen) an issue
```bash
gh issue close "$ISSUE" -c "Closing because ... (reason + next steps)."
gh issue reopen "$ISSUE" -c "Reopening because ..."
```

## Link an issue to a PR
There are two useful “links”:

### A) Cross-link (visibility) — comment the PR in the issue (and/or vice versa)
If you know the PR number:
```bash
PR=456
PR_URL="$(gh pr view "$PR" --json url -q .url)"
gh issue comment "$ISSUE" -b "Tracking work in PR: $PR_URL"
```
GitHub will automatically create backlinks.

### B) Auto-close on merge — add a closing keyword to the PR description
Edit the PR body to include one of: `Fixes #123`, `Closes #123`, or `Resolves #123`.
```bash
gh pr edit "$PR" --body "$(gh pr view "$PR" --json body -q .body)

Fixes #$ISSUE"
```

Rule of thumb:
- Use **A** if you just want association/traceability.
- Use **B** if merging the PR should automatically close the issue.

## Minimal “iteration” template (copy/paste)
```bash
ISSUE=123
STATE_FILE="$(git rev-parse --git-dir)/agent-state/gh-issue-ops-state.json"
# 1) sync new comments since checkpoint
SINCE="$(jq -r '.since // "1970-01-01T00:00:00Z"' "$STATE_FILE" 2>/dev/null || echo "1970-01-01T00:00:00Z")"
gh api -X GET repos/{owner}/{repo}/issues/$ISSUE/comments -f since="$SINCE" --paginate

# 2) reply
gh issue comment "$ISSUE" -b "Update: ..."

# 3) checkpoint
mkdir -p "$(dirname "$STATE_FILE")"
date -u +"%Y-%m-%dT%H:%M:%SZ" | jq -R --argjson issue "$ISSUE" '{issue: $issue, since: .}' > "$STATE_FILE"
```
