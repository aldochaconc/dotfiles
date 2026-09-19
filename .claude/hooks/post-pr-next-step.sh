#!/usr/bin/env bash
set -euo pipefail

TRUNK_BRANCHES="main master develop staging prod dev"
DELETE_REMOTE="true"
REMOTE_NAME="origin"
PULL_TRUNK="true"
WORKFLOW_MODE="auto"
ENABLED="true"
WORKDOCS_DIR="workdocs"
DOCS_AGENTS_DIR="docs/agents"
STATUS_GREENFIELD="docs/agents/status.md"
STATUS_BROWNFIELD_TEMPLATE="{{workdocs_dir}}/{{workdoc_id}}/status.md"
OPEN_PR_REGEX=$(cat <<'REGEX'
(?i)\bPR\s*#?\d+\b.*\bopen\b
REGEX
)
CLOSE_PR_TEMPLATE=$(cat <<'TEMPLATE'
Update {{status_path}} by marking the previous "PR open" entry as closed:
{{open_pr_line}}
TEMPLATE
)
IF_NONE="prompt"
TOOL="claude"
CONFIG_WORKFLOW_TYPE="greenfield"
BRANCH_PREFIX=""
BRANCH_PREFIXES=""
PLAN_SUFFIX=""
STEP_PATTERN=""

usage() {
  cat <<'USAGE'
Usage: ./post-pr-next-step.sh [--tool <tool>]

Options:
  --tool <tool>   Override tool for this run (codex|claude|claude-code|cursor|none)
  --tool=<tool>   Same as above.
  -h, --help      Show this help message.
USAGE
}

normalize_tool() {
  local value
  value="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$value" in
    codex|claude|claude-code|cursor|none)
      printf '%s' "$value"
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

parse_args() {
  local tool_override=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --tool)
        shift
        if [[ $# -eq 0 ]]; then
          echo "Error: --tool requires a value."
          exit 1
        fi
        tool_override="$1"
        ;;
      --tool=*)
        tool_override="${1#*=}"
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Error: unknown argument: $1"
        usage
        exit 1
        ;;
    esac
    shift
  done

  if [[ -n "$tool_override" ]]; then
    local normalized_tool
    if ! normalized_tool="$(normalize_tool "$tool_override")"; then
      echo "Error: invalid --tool value \"$tool_override\" (valid: codex, claude, claude-code, cursor, none)."
      exit 1
    fi
    TOOL="$normalized_tool"
  fi
}

parse_args "$@"

# Respect the enabled flag and short-circuit early.
if [[ "$ENABLED" != "true" ]]; then
  echo "post-pr-next-step disabled; exiting."
  exit 0
fi

if [[ -z "$DOCS_AGENTS_DIR" ]]; then
  DOCS_AGENTS_DIR="docs/agents"
fi
DOCS_AGENTS_DIR="${DOCS_AGENTS_DIR%/}"

# Ensure we're in a git repo.
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "Error: not inside a git repository."
  exit 1
}

# Normalize branch prefix list for matching.
if [[ -z "$BRANCH_PREFIXES" && -n "$BRANCH_PREFIX" ]]; then
  BRANCH_PREFIXES="$BRANCH_PREFIX"
fi

matches_branch_prefix() {
  local branch="$1"
  for prefix in $BRANCH_PREFIXES; do
    if [[ -n "$prefix" && "$branch" == "$prefix"* ]]; then
      return 0
    fi
  done
  return 1
}

# Clean up the current feature branch when safe to do so.
current_branch="$(git rev-parse --abbrev-ref HEAD)"
original_branch="$current_branch"
if [[ "$current_branch" == "HEAD" ]]; then
  echo "Note: detached HEAD; skipping branch cleanup."
else
  is_trunk=false
  for b in $TRUNK_BRANCHES; do
    if [[ "$current_branch" == "$b" ]]; then
      is_trunk=true
      break
    fi
  done

  # Feature/fix/etc: branch with a slash or matching a configured prefix.
  is_feature_branch=false
  if [[ "$current_branch" == */* ]]; then
    is_feature_branch=true
  elif matches_branch_prefix "$current_branch"; then
    is_feature_branch=true
  fi

  if [[ "$is_trunk" == "false" && "$is_feature_branch" == "true" ]]; then
    # Safety: don't switch/delete with uncommitted changes.
    if ! git diff-index --quiet HEAD --; then
      echo "Error: working tree has uncommitted changes. Commit or stash before running."
      exit 1
    fi

    # Prefer switching to main; fall back to remote default if needed.
    main_branch="main"
    if ! git show-ref --verify --quiet "refs/heads/$main_branch"; then
      if git symbolic-ref --quiet --short refs/remotes/origin/HEAD >/dev/null 2>&1; then
        main_branch="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD | sed 's|^origin/||')"
      elif git show-ref --verify --quiet refs/heads/master; then
        main_branch="master"
      elif git show-ref --verify --quiet refs/heads/develop; then
        main_branch="develop"
      fi
    fi

    echo "Cleaning up feature branch: $current_branch"
    git switch "$main_branch" 2>/dev/null || git checkout "$main_branch"

    if [[ "$PULL_TRUNK" == "true" ]]; then
      git pull
    fi

    # Delete local branch.
    git branch -D "$current_branch"

    # Optionally delete the remote branch.
    if [[ "$DELETE_REMOTE" == "true" ]]; then
      remote="$REMOTE_NAME"
      if [[ -z "$remote" ]]; then
        if git remote get-url origin >/dev/null 2>&1; then
          remote="origin"
        else
          remote="$(git remote | head -n1 || true)"
        fi
      fi

      if [[ -n "$remote" ]]; then
        if git ls-remote --exit-code --heads "$remote" "$current_branch" >/dev/null 2>&1; then
          git push "$remote" --delete "$current_branch"
        else
          echo "Remote branch '$remote/$current_branch' not found; skipping remote delete."
        fi
      else
        echo "No git remote found; skipping remote delete."
      fi
    fi
  fi
fi

# Decide workflow mode when set to auto.
workflow_mode="$WORKFLOW_MODE"
if [[ "$workflow_mode" == "auto" ]]; then
  if [[ "$CONFIG_WORKFLOW_TYPE" == brownfield-* ]]; then
    workflow_mode="brownfield"
  else
    workflow_mode="greenfield"
  fi
fi

# Escape regex characters for safe sed usage.
escape_regex() {
  printf '%s' "$1" | sed -E 's/[][(){}.^$+*?|\\/\\\\]/\\\\&/g'
}

strip_branch_prefix() {
  local branch="$1"
  for prefix in $BRANCH_PREFIXES; do
    if [[ -n "$prefix" && "$branch" == "$prefix"* ]]; then
      printf '%s' "${branch#${prefix}}"
      return 0
    fi
  done
  printf '%s' "$branch"
  return 0
}

# Derive a workdoc id from the branch naming convention.
derive_workdoc_id() {
  local branch="$1"
  local candidate=""

  candidate="$(strip_branch_prefix "$branch")"
  if [[ "$candidate" == "$branch" ]]; then
    candidate="${branch##*/}"
  fi

  if [[ -n "$PLAN_SUFFIX" && "$candidate" == *"$PLAN_SUFFIX" ]]; then
    candidate="${candidate%$PLAN_SUFFIX}"
  fi

  if [[ -n "$STEP_PATTERN" ]]; then
    local placeholder="__STEP_N__"
    local step_pattern="${STEP_PATTERN//\{n\}/$placeholder}"
    local escaped
    escaped="$(escape_regex "$step_pattern")"
    local step_regex="${escaped//$placeholder/[0-9]+}"
    if [[ -n "$step_regex" ]]; then
      candidate="$(printf '%s' "$candidate" | sed -E "s/${step_regex}$//")"
    fi
  fi

  if [[ "$candidate" == *"--"* ]]; then
    candidate="${candidate%%--*}"
  fi

  printf '%s' "$candidate"
}

# Resolve the status file path (greenfield: fixed path, brownfield: templated).
# Resolve the status file path (greenfield: fixed path, brownfield: templated).
status_path=""
workdoc_id=""
if [[ "$workflow_mode" == "brownfield" ]]; then
  is_original_trunk=false
  for b in $TRUNK_BRANCHES; do
    if [[ "$original_branch" == "$b" ]]; then
      is_original_trunk=true
      break
    fi
  done

  if [[ "$is_original_trunk" != "true" ]]; then
    if [[ "$original_branch" == */* ]]; then
      workdoc_id="$(derive_workdoc_id "$original_branch")"
    elif matches_branch_prefix "$original_branch"; then
      workdoc_id="$(derive_workdoc_id "$original_branch")"
    elif [[ -n "$STEP_PATTERN" ]]; then
      workdoc_id="$(derive_workdoc_id "$original_branch")"
    fi
  fi
  if [[ -z "$workdoc_id" ]]; then
    read -r -p "Enter WORKDOC_ID: " workdoc_id
  fi
  if [[ -n "$workdoc_id" ]]; then
    status_path="$STATUS_BROWNFIELD_TEMPLATE"
    status_path="${status_path//\{\{workdocs_dir\}\}/$WORKDOCS_DIR}"
    status_path="${status_path//\{\{workdoc_id\}\}/$workdoc_id}"
  fi
else
  status_path="$STATUS_GREENFIELD"
fi

# Anchor relative status paths to the repo root so subdirectory runs still work.
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if [[ -n "$status_path" && "$status_path" != /* ]]; then
  status_path="${repo_root}/${status_path}"
fi

# Locate the last "PR open" line in the status file.
open_pr_line=""
if [[ -n "$status_path" && -f "$status_path" && -n "$OPEN_PR_REGEX" ]]; then
  if command -v perl >/dev/null 2>&1; then
    open_pr_line="$(OPEN_PR_REGEX="$OPEN_PR_REGEX" perl -ne 'if (m{$ENV{OPEN_PR_REGEX}}) { chomp; $last=$_ } END { print $last if defined $last }' "$status_path")"
  elif printf '%s\n' "__regex_probe__" | grep -P -q "__regex_probe__" >/dev/null 2>&1; then
    open_pr_line="$(grep -P "$OPEN_PR_REGEX" "$status_path" | tail -n 1 || true)"
  else
    sanitized_regex="$(printf '%s' "$OPEN_PR_REGEX" | sed -E 's/\(\?i\)//g; s/\\b//g; s/\\s/[[:space:]]/g; s/\\S/[^[:space:]]/g; s/\\d/[0-9]/g; s/\\D/[^0-9]/g; s/\\w/[[:alnum:]_]/g; s/\\W/[^[:alnum:]_]/g')"
    open_pr_line="$(grep -i -E "$sanitized_regex" "$status_path" | tail -n 1 || true)"
  fi
fi

# Build the close-previous-PR instruction if available.
close_instruction=""
if [[ -n "$open_pr_line" ]]; then
  close_instruction="$CLOSE_PR_TEMPLATE"
  close_instruction="${close_instruction//\{\{status_path\}\}/$status_path}"
  close_instruction="${close_instruction//\{\{open_pr_line\}\}/$open_pr_line}"
elif [[ "$IF_NONE" != "none" ]]; then
  if [[ -z "$status_path" ]]; then
    close_instruction="Locate the status file and close any previous \"PR open\" entry."
  elif [[ ! -f "$status_path" ]]; then
    close_instruction="Status file not found at $status_path. Create or repair it, then close any previous \"PR open\" entry."
  else
    close_instruction="No previous \"PR open\" entry found in $status_path. Manually verify and close any lingering open marker."
  fi
fi

# Assemble the prompt shown to the next agent or CLI tool.
prompt_lines=(
  "A PR has just been merged."
  ""
)

if [[ -n "$status_path" ]]; then
  prompt_lines+=("Read protocol docs in this order: AGENTS.md, README.md, $status_path, $DOCS_AGENTS_DIR/design.md, the current phase plan, and $DOCS_AGENTS_DIR/standards.md + $DOCS_AGENTS_DIR/stack.md + $DOCS_AGENTS_DIR/decisions.md (if present).")
else
  prompt_lines+=("Read protocol docs in this order: AGENTS.md, README.md, $DOCS_AGENTS_DIR/status.md, $DOCS_AGENTS_DIR/design.md, the current phase plan, and $DOCS_AGENTS_DIR/standards.md + $DOCS_AGENTS_DIR/stack.md + $DOCS_AGENTS_DIR/decisions.md (if present).")
fi

if [[ -n "$close_instruction" ]]; then
  prompt_lines+=("" "$close_instruction")
fi

prompt_lines+=("" "Proceed with the next step for this workflow. If no next step is listed, ask the user what to do next.")

PROMPT="$(printf "%s\n" "${prompt_lines[@]}")"

# Hand off to the requested tool when available; otherwise echo the prompt.
case "$TOOL" in
  codex)
    if command -v codex >/dev/null 2>&1; then
      exec codex "$PROMPT"
    fi
    ;;
  claude|claude-code)
    if command -v claude >/dev/null 2>&1; then
      exec claude "$PROMPT"
    fi
    ;;
  cursor)
    if command -v agent >/dev/null 2>&1; then
      exec agent "$PROMPT"
    fi
    copied=false
    if command -v pbcopy >/dev/null 2>&1; then
      printf '%s' "$PROMPT" | pbcopy && copied=true
    fi
    if ! $copied && command -v wl-copy >/dev/null 2>&1; then
      printf '%s' "$PROMPT" | wl-copy && copied=true
    fi
    if ! $copied && command -v xclip >/dev/null 2>&1; then
      printf '%s' "$PROMPT" | xclip -selection clipboard && copied=true
    fi
    if ! $copied && command -v xsel >/dev/null 2>&1; then
      printf '%s' "$PROMPT" | xsel --clipboard --input && copied=true
    fi
    if $copied; then
      echo "Prompt copied to clipboard. Paste it into Cursor to continue."
    else
      echo "Paste the following prompt into Cursor to continue:"
    fi
    echo ""
    echo "$PROMPT"
    exit 0
    ;;
esac

echo "$PROMPT"
