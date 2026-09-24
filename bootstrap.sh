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

echo "==> journal retention: 500M, so it stops growing toward journald's 10%-of-disk default"
[[ -f /etc/systemd/journald.conf.d/size.conf ]] || {
  sudo mkdir -p /etc/systemd/journald.conf.d
  printf '[Journal]\nSystemMaxUse=500M\n' | sudo tee /etc/systemd/journald.conf.d/size.conf >/dev/null
  sudo systemctl kill --kill-who=main --signal=SIGUSR2 systemd-journald
}

echo "==> AUR build hygiene: no leftover makedepends, no -debug split packages"
yay -Y --save --removemake >/dev/null
[[ -f /etc/makepkg.conf.d/no-debug.conf ]] || echo 'OPTIONS+=(!debug)' | sudo tee /etc/makepkg.conf.d/no-debug.conf >/dev/null

echo "==> shephrd approve: root-owned helper, its polkit action and the approvals directory"
[[ -x /usr/local/lib/shephrd/approve ]] || sudo sh -c 'install -D -o root -g root -m 0755 "$1/system/shephrd/approve" /usr/local/lib/shephrd/approve && install -D -o root -g root -m 0644 "$1/system/shephrd/local.shephrd.approve.policy" /usr/share/polkit-1/actions/local.shephrd.approve.policy && install -d -o root -g root -m 0755 /var/lib/shephrd/approvals' _ "$here"

echo "==> packages: AUR"
# shellcheck disable=SC2046
omarchy pkg aur add $(pkgs "$here/packages-aur.txt")

echo "==> shell: zsh as login shell, stock oh-my-zsh template when ~/.zshrc is absent"
[[ $(getent passwd "$USER" | cut -d: -f7) == /usr/bin/zsh ]] || chsh -s /usr/bin/zsh
[[ -f ~/.zshrc ]] || cp /usr/share/oh-my-zsh/templates/zshrc.zsh-template ~/.zshrc

echo "==> thpm: theme hook that carries the palette into GTK apps (Thunar, xarchiver and friends)"
thpm install --no-ui
thpm enable gtk-css-compat

echo "==> secrets: stored once in the system keyring; ~/.claude/settings.json is rendered from them"
omarchy pkg add chezmoi
for s in github_token gdrive_client_id gdrive_client_secret; do
  chezmoi secret keyring get --service claude --user "$s" >/dev/null 2>&1 ||
    chezmoi secret keyring set --service claude --user "$s"
done

echo "==> dotfiles via chezmoi (asks the per-machine questions once)"
chezmoi init --source "$here" --apply

echo "==> rtk: Claude Code output filter, static musl build from GitHub Releases"
if ! command -v rtk >/dev/null; then
  tmp=$(mktemp -d)
  curl -fsSL -o "$tmp/rtk.tgz" https://github.com/rtk-ai/rtk/releases/latest/download/rtk-x86_64-unknown-linux-musl.tar.gz
  curl -fsSL -o "$tmp/checksums.txt" https://github.com/rtk-ai/rtk/releases/latest/download/checksums.txt
  (cd "$tmp" && awk '/x86_64-unknown-linux-musl/ {print $1"  rtk.tgz"}' checksums.txt | sha256sum -c -)
  mkdir -p ~/.local/bin && tar -xzf "$tmp/rtk.tgz" -C ~/.local/bin rtk && chmod 755 ~/.local/bin/rtk
  rm -rf "$tmp"
fi

if omarchy hw match omen && ! pacman -Q omen-space-git >/dev/null 2>&1; then
  echo "==> omen-space: HP OMEN fan/RGB/MUX daemon, built as a pacman package from a pinned tag"
  omen_tag=2.0.9
  tmp=$(mktemp -d)
  git clone -q --depth 1 -b "$omen_tag" https://github.com/yunusemreyl/omen-space "$tmp"
  # upstream's PKGBUILD tracks main; pin the source to the same tag we cloned.
  # It also builds with --locked while .gitignore excludes Cargo.lock, so no lock file ever
  # exists in the repo and the build aborts; drop the flag (crates resolve at build time).
  sed -i -e "s|^source=(.*)|source=(\"git+https://github.com/yunusemreyl/omen-space.git#tag=$omen_tag\")|" \
         -e "s/ --locked//" "$tmp/PKGBUILD"
  (cd "$tmp" && makepkg -sri --noconfirm)   # -r drops the build deps (rust) afterwards
  rm -rf "$tmp"
fi

echo "==> toolchains declared in ~/.config/mise/config.toml"
mise install

echo "==> claude code: marketplaces, then the plugins that resolve against them"
# What declares the set is `enabledPlugins` and `extraKnownMarketplaces` in
# .chezmoitemplates/claude-settings.json, already applied by chezmoi above. This section
# clones the marketplaces and unpacks the plugins ahead of the first session instead of
# leaving that to it, and the two .txt lists are the readable form of the same set: a JSON
# file of nested source objects does not say why a plugin is there or why another was
# rejected. Keep the three in step; a plugin missing from the settings template is
# disabled at the next `chezmoi apply` whatever these lists say.
#
# Both commands are idempotent: an already-added marketplace and an already-installed
# plugin report so and exit 0. Neither is allowed to abort the run, because a renamed
# marketplace or a network failure would take the rest of the bootstrap with it under
# `set -e`, and every step below this one is unrelated to Claude Code.
while read -r source sparse; do
  # A local marketplace is written as ~/... so the repository carries no login name. The tilde is
  # not expanded inside quotes, and `claude plugin marketplace add` would be handed a literal.
  source="${source/#\~/$HOME}"
  # shellcheck disable=SC2086 # sparse is a list of paths, word splitting is the point
  claude plugin marketplace add "$source" ${sparse:+--sparse $sparse} ||
    echo "WARN: marketplace $source failed; the settings template still declares it" >&2
done < <(grep -vE '^\s*#|^\s*$' "$here/claude-marketplaces.txt")

while read -r plugin; do
  claude plugin install "$plugin" --scope user -y ||
    echo "WARN: plugin $plugin failed; the settings template still declares it" >&2
done < <(grep -vE '^\s*#|^\s*$' "$here/claude-plugins.txt")

echo "==> omarchy defaults"
omarchy default browser chromium
omarchy default terminal foot
omarchy default editor code

echo "==> chromium: force-install the Claude extension, so Claude Code can drive the browser"
# Claude Code ships the native messaging host in ~/.config/chromium/NativeMessagingHosts/, but
# not the extension itself, and Chromium's Web Store install is unreliable without Google API
# keys. ExtensionInstallForcelist makes Chromium fetch it at startup instead. The id is the one
# the native host already allows in allowed_origins.
[[ -f /etc/chromium/policies/managed/claude-extension.json ]] || {
  sudo mkdir -p /etc/chromium/policies/managed
  printf '{"ExtensionInstallForcelist":["fcoeoabgfenejglbffodgkkbkcdhcgfn;https://clients2.google.com/service/update2/crx"]}\n' |
    sudo tee /etc/chromium/policies/managed/claude-extension.json >/dev/null
}

echo "==> file expiry declared in ~/.config/user-tmpfiles.d (screenshots keep 7 days)"
# The rules are chezmoi-managed; only the timer that acts on them has to be turned on, and it
# ships disabled. The timer runs --clean alone, so --create runs once here to make the
# directories the rules declare; after that omarchy has somewhere to write on the first capture.
systemd-tmpfiles --user --create
systemctl --user enable --now systemd-tmpfiles-clean.timer

echo "==> vscode extensions"
# --install-extension is idempotent on its own but re-downloads each one; comparing against
# --list-extensions first keeps a re-run cheap. local.omarchy-theme is generated by THPM's
# vscode-local-compat integration, so it is never declared here.
comm -23 <(pkgs "$here/vscode-extensions.txt" | tr ' ' '\n' | grep -v '^$' | LC_ALL=C sort) \
         <(code --list-extensions 2>/dev/null | LC_ALL=C sort) |
  while read -r ext; do code --install-extension "$ext" --force; done

echo "==> web apps kept"
omarchy webapp install WhatsApp https://web.whatsapp.com/ whatsapp

echo "==> themes from git (hand-made ones come with chezmoi)"
while read -r url; do
  omarchy theme install "$url"
done < <(grep -vE '^\s*#|^\s*$' "$here/themes.txt")

echo "==> shell plugins from git"
# `omarchy plugin add` refuses a plugin already installed, which is every one on a re-run.
# shell.json, applied above, already places each widget, and an enable without a placement
# leaves it where it is.
while read -r url; do
  omarchy plugin add "$url" --enable --yes ||
    echo "WARN: plugin $url not added; already installed, or see the error above" >&2
done < <(grep -vE '^\s*#|^\s*$' "$here/plugins.txt")

if chezmoi data | jq -e '.hybrid_gpu' >/dev/null 2>&1 && [[ "$(supergfxctl -g 2>/dev/null)" != "Hybrid" ]]; then
  echo "==> hybrid GPU: this machine is not in Hybrid mode. Run:  omarchy toggle hybrid gpu   (reboots)"
fi

cat <<'EOF'

Optional, interactive, run by hand:
  omarchy remove preinstalls      # drops Omarchy's preinstalled apps/webapps; re-run the webapp line above afterwards
EOF

hyprctl reload >/dev/null 2>&1 || true
echo "==> done"
