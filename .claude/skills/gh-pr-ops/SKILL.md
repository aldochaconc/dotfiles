---
name: gh-pr-ops
description: Use GitHub CLI (gh) to create pull requests, read and reply to PR feedback (conversation comments, review bodies, and inline comments), add reviewers, check CI/CD status, and revert merged PRs. Use this to safely iterate on a PR without missing new reviewer comments between review rounds.
compatibility: Requires git, GitHub CLI (gh) authenticated with repo access, and jq for JSON filtering. Works best inside a git repo, or with GH_REPO / -R.
allowed-tools: Bash(gh:*) Bash(git:*) Bash(jq:*) Read Write
---

# gh PR ops

## Purpose

This skill teaches an agent to use `gh` for common pull request operations, with a **focus on PR comment workflows**:

- Open a PR
- Read **all** PR feedback (conversation comments, review bodies, inline “Files changed” comments)
- Reply to PR feedback (conversation + inline threads)
- Check whether CI/CD is finished and its status
- Add reviewers
- Revert a merged PR

### Prime directive: do not miss feedback during iteration

When iterating on a PR, always follow this loop:

1. **Sync new feedback**
2. Implement changes (commit + push)
3. Reply to feedback you addressed
4. **Sync again** (to catch any replies that arrived while you were coding)

This avoids the common failure mode where the agent only reads the PR “Conversation” tab and misses inline comments under “Files changed”.

## Mental model: PR feedback comes from 3 different sources

GitHub exposes PR feedback in multiple “channels”. You must check all of them:

1. **Conversation comments** (PR-as-issue comments)  
   - Appear on the PR “Conversation” tab.
2. **Review bodies**  
   - Top-level text attached to an “Approve / Request changes / Comment” review submission.
3. **Inline review comments**  
   - Comments on specific files/lines under “Files changed” (plus replies in those threads).

`gh pr view --comments` is helpful, but **do not rely on it as your only source**. For full coverage, use `gh api` to pull *issue comments*, *review comments*, and *reviews*.

## Always start by identifying the PR

If the user didn’t provide a PR number/URL, assume the PR for the current branch:

```bash
PR_NUMBER="$(gh pr view --json number -q .number)"
PR_URL="$(gh pr view --json url -q .url)"
```

If you are not in the repo directory, use either:
- `GH_REPO=OWNER/REPO` environment variable, or
- `-R OWNER/REPO` on commands that support it.

# Core workflow: read all new comments safely

## Recommended approach: checkpointed “sync” (no missed comments)

Maintain a small state file per repo, e.g.:

- `$(git rev-parse --git-dir)/agent-state/gh-pr-ops-state.json`

Example:

```json
{ "pr": 123, "since": "2026-01-13T00:00:00Z" }
```

Where:
- `pr` is the PR number you’re iterating on
- `since` is the last sync checkpoint

### Important: set the checkpoint to the *start* of a sync, not the end

When you fetch multiple streams (issue comments, inline comments, reviews), new feedback can arrive between your first and last API call.

If you set your checkpoint to “now (end of sync)”, you can permanently miss comments created mid-sync in a stream you already queried.

**Safe rule:** record `syncStartedAt` at the beginning of the sync and store that as the next `since`.

This may cause duplicates on the next sync, but duplicates are far better than missed feedback. Ignore duplicates by:
- skipping comments authored by you, and/or
- de-duping by `(id, updated_at)`.

## One-command sync script

This bundle installs the script under the skill directory. Run:

`<SKILLS_DIR>/gh-pr-ops/scripts/pr_sync_comments.sh`

Where `<SKILLS_DIR>` is one of:
- `.codex/skills`
- `.claude/skills`
- `.cursor/skills`

It prints a JSON object containing:
- `issueComments` (Conversation tab)
- `inlineReviewComments` (Files changed comments + replies)
- `reviews` (review bodies filtered to those submitted after `since`)

…and updates `$(git rev-parse --git-dir)/agent-state/gh-pr-ops-state.json` to checkpoint the sync.

Example:

```bash
chmod +x <SKILLS_DIR>/gh-pr-ops/scripts/pr_sync_comments.sh
<SKILLS_DIR>/gh-pr-ops/scripts/pr_sync_comments.sh 123
# or: <SKILLS_DIR>/gh-pr-ops/scripts/pr_sync_comments.sh (auto-detect PR for current branch)
```

## Manual sync (without script)

### 1) Conversation comments (PR-as-issue comments)

```bash
gh api -X GET repos/{owner}/{repo}/issues/$PR_NUMBER/comments   -f since="$SINCE"   --paginate   -q '.[] | {id, user: .user.login, created_at, updated_at, body, html_url}'
```

### 2) Inline review comments (Files changed)

```bash
gh api -X GET repos/{owner}/{repo}/pulls/$PR_NUMBER/comments   -f since="$SINCE" -f sort=updated -f direction=asc   --paginate   -q '.[] | {id, in_reply_to_id, user: .user.login, path, line, side, created_at, updated_at, body, html_url}'
```

### 3) Review bodies (Approve / Request changes / Comment)

```bash
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/reviews   --paginate   -q '.[] | {id, user: .user.login, state, submitted_at, body, html_url}'
```

Filter to `submitted_at > $SINCE` on the client side.

# Replying to PR feedback

## Reply to Conversation comments
Conversation comments are not threaded replies in the same way as inline comments.
Reply by posting a new PR comment and quoting the context.

```bash
gh pr comment $PR_NUMBER -b $'Replying to @reviewer:

> (quote)

Applied fix in commit abc123. Details: ...'
```

(Equivalent via API)

```bash
gh api repos/{owner}/{repo}/issues/$PR_NUMBER/comments -f body='...'
```

## Reply to inline “Files changed” threads
Inline comments are pull request review comments. To reply in-thread, reply to the **top-level** comment in the thread.

```bash
gh api -X POST repos/{owner}/{repo}/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies   -f body='Thanks — fixed in abc123. I changed X by doing Y...'
```

If you only have a reply comment id, first look up `in_reply_to_id` and reply to that top-level id.

# Other common operations

## Opening a PR

```bash
gh pr create --fill
```

### PR body requirements (enforced)

- Always populate the PR **Description** using the repository PR template (for example `.github/PULL_REQUEST_TEMPLATE/...`).
- Never leave PR Description empty and never rely on comments for core context.
- For frontend/UI changes, embed screenshots directly in the PR Description under an explicit section (for example `## Screenshots`).
- Use markdown image links that render on GitHub (for example committed image paths/URLs). Do not use escaped markdown like `\\n` literals.

When providing a multiline body, avoid plain `"..."` strings (they can render literal `\n`).
Use a newline-safe form instead:

```bash
gh pr create --title "..." --base main --head my-branch --body $'Summary\n\nDetails...'
```

```bash
gh pr create --title "..." --base main --head my-branch --body-file - <<'EOF'
Summary

Details...
EOF
```

```bash
cat > /tmp/pr_body.txt <<'EOF'
Summary

Details...
EOF
gh pr create --title "..." --base main --head my-branch --body-file /tmp/pr_body.txt
```

## Checking CI/CD status

Human output:

```bash
gh pr checks $PR_NUMBER
```

Wait for completion:

```bash
gh pr checks $PR_NUMBER --watch
```

Machine-readable:

```bash
gh pr checks $PR_NUMBER --json name,state,bucket,startedAt,completedAt,link
```

Interpretation:
- `bucket=pending` → still running
- any `bucket=fail` → failing checks
- no pending and no fail → green

## Adding reviewers

```bash
gh pr edit $PR_NUMBER --add-reviewer "octocat,my-org/my-team"
```

## Reverting a merged PR (creates a revert PR)

```bash
gh pr revert $PR_NUMBER --title "Revert: ..." --body "Reason: ..." --draft
```

# Practical checklist for an agent iteration

1. Identify PR number + URL.
2. Sync feedback (script or manual).
3. Enumerate each new comment/thread and decide:
   - what code change is required,
   - what reply should be posted.
4. Implement fixes; commit + push.
5. Reply:
   - conversation: `gh pr comment`
   - inline threads: `gh api .../replies`
6. Sync again. Only then report completion.

If the user says “I left comments”, do **not** assume they’re only in the PR body or Conversation tab—always sync all three sources.
