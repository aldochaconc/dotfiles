#!/usr/bin/env bash
# Reproduce this Omarchy setup on a fresh install.
# Every step is an omarchy command or chezmoi; nothing is copied into /etc by hand.
# Idempotent: `omarchy pkg add` skips installed packages, `chezmoi apply` is a no-op when in sync.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
pkgs() { grep -vE '^\s*#|^\s*$' "$1" | tr '\n' ' '; }

echo "==> packages: Arch / Omarchy repos"
# shellcheck disable=SC2046
omarchy pkg add $(pkgs "$here/packages.txt")

echo "==> packages: AUR"
# shellcheck disable=SC2046
omarchy pkg aur add $(pkgs "$here/packages-aur.txt")

echo "==> dotfiles via chezmoi (asks the per-machine questions once)"
omarchy pkg add chezmoi
chezmoi init --source "$here" --apply

echo "==> omarchy defaults"
omarchy default browser chromium
omarchy default terminal foot
omarchy default editor code

echo "==> toolchains declared in ~/.config/mise/config.toml"
mise install

echo "==> web apps kept"
omarchy webapp install WhatsApp https://web.whatsapp.com/ whatsapp

echo "==> themes from git (hand-made ones come with chezmoi)"
while read -r url; do
  omarchy theme install "$url"
done < <(grep -vE '^\s*#|^\s*$' "$here/themes.txt")

if chezmoi data | jq -e '.hybrid_gpu' >/dev/null 2>&1 && [[ "$(supergfxctl -g 2>/dev/null)" != "Hybrid" ]]; then
  echo "==> hybrid GPU: this machine is not in Hybrid mode. Run:  omarchy toggle hybrid gpu   (reboots)"
fi

cat <<'EOF'

Optional, interactive, run by hand:
  omarchy remove preinstalls      # drops Omarchy's preinstalled apps/webapps; re-run the webapp line above afterwards
EOF

hyprctl reload >/dev/null 2>&1 || true
echo "==> done"
