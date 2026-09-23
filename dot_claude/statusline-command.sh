#!/usr/bin/env bash
# Claude Code feeds this script a JSON object on stdin every time the status line is redrawn,
# and that object is the only place the account figures appear: `rate_limits.five_hour` and
# `rate_limits.seven_day` are published nowhere else, not by a subcommand and not in any state
# file under ~/.claude. Reading them back off the rendered bar is screen scraping, and it
# reports whatever a pane last drew rather than what is true.
#
# So the object is kept. One file per session under ~/.claude/budget, holding the payload plus
# the time it arrived, which is what makes a stale reading legible as stale.
input=$(cat)

# Best effort and silent: a status line that fails or stalls is worse than one without a record.
budget_record() {
  local dir="$HOME/.claude/budget" id
  id=$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null)
  [ -n "$id" ] || return 0
  mkdir -p "$dir" 2>/dev/null || return 0
  printf '%s' "$input" \
    | jq -c --arg at "$(date -Is)" '. + {recorded_at: $at}' \
    > "$dir/$id.json.tmp" 2>/dev/null \
    && mv "$dir/$id.json.tmp" "$dir/$id.json" 2>/dev/null
  return 0
}
budget_record

model=$(echo "$input" | jq -r '.model.display_name // "unknown"')

used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
if [ -n "$used_pct" ]; then
  ctx=$(printf "ctx:%.0f%%" "$used_pct")
else
  ctx="ctx:–"
fi

five=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
if [ -n "$five" ]; then
  five_str=$(printf "5h:%.0f%%" "$five")
else
  five_str=""
fi

week=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
if [ -n "$week" ]; then
  week_str=$(printf "7d:%.0f%%" "$week")
else
  week_str=""
fi

cwd=$(echo "$input" | jq -r '.workspace.current_dir // ""')
folder=$(basename "$cwd")
branch=$(git -C "$cwd" --no-optional-locks rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ -n "$branch" ]; then
  location="${folder}(${branch})"
else
  location="${folder}"
fi

parts=("$model" "$ctx")
[ -n "$five_str" ] && parts+=("$five_str")
[ -n "$week_str" ] && parts+=("$week_str")
parts+=("$location")

out=""
for p in "${parts[@]}"; do
  if [ -z "$out" ]; then out="$p"; else out="$out | $p"; fi
done
printf "%s" "$out"
