#!/usr/bin/env bash
# Fails when a repo file leaks the login name, the home path, or a private term.
# Terms: $USER, $HOME, plus one per line in ~/.config/dotfiles-guard/terms (kept out of git).
# Usage: guard-private.sh <file>...   (exit 1 on a hit; prints file:line:match)
set -u
terms_file="${DOTFILES_GUARD_TERMS:-$HOME/.config/dotfiles-guard/terms}"
skip='^(dot_config/git/config|\.claude/hooks/guard-private\.sh|\.githooks/.*)$'   # git identity is versioned on purpose
patterns=("$USER" "$HOME" "/home/$USER" '~/Work/' '~/Projects/' "$HOME/Work" "$HOME/Projects")
[[ -r $terms_file ]] && while IFS= read -r t; do [[ -n $t && $t != \#* ]] && patterns+=("$t"); done < "$terms_file"
status=0
for f in "$@"; do
  [[ -f $f ]] || continue
  rel=${f#"$PWD/"}
  [[ $rel =~ $skip ]] && continue
  grep -qI . "$f" 2>/dev/null || continue            # binary: skip
  for p in "${patterns[@]}"; do
    while IFS= read -r line; do
      printf '%s:%s\n' "$rel" "$line"; status=1
    done < <(grep -n -i -F -- "$p" "$f" 2>/dev/null)
  done
done
(( status )) && echo "guard-private: use \$USER, \$HOME or ~ instead of literal names; move project references out of the repo." >&2
exit $status
