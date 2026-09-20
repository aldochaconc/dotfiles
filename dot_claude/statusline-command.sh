#!/usr/bin/env bash
input=$(cat)

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
