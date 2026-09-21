# dotfiles

Omarchy customizations, applied with [chezmoi](https://www.chezmoi.io/). Only the delta over
Omarchy's defaults lives here; the defaults come from `omarchy update`.

## Fresh machine

```sh
git clone <this repo> ~/dotfiles
~/dotfiles/bootstrap.sh
```

`bootstrap.sh` installs the extra packages, sets zsh as the login shell, runs `chezmoi init --apply` (three yes/no questions
about this machine's displays and GPU, plus the Google Drive MCP path, empty if none), sets the Omarchy defaults and the kept web apps.
Before `chezmoi apply` it asks for three secrets once (GitHub token, Google Drive OAuth id and
secret) and stores them in the system keyring; `~/.claude/settings.json` is rendered from there.

One manual step after that, once per machine (sudo): the boot and login screen, tux from the `moon`
theme (`unlock.png`) on solid black, text in the theme foreground. The same file runs as a
`post-update.d` hook and reapplies when an Omarchy update restores the stock logo or the palette moves.

```sh
~/.config/omarchy/hooks/post-update.d/plymouth-moon.hook
```

Without a TTY, answer the prompts on the command line; `--promptBool` is keyed by the prompt text:

```sh
chezmoi init --source ~/dotfiles \
  --promptBool "Hybrid AMD+NVIDIA laptop (supergfxd Hybrid, AQ_DRM_DEVICES for Hyprland)=true" \
  --promptBool "Laptop panel eDP-1 pinned to 1920x1080@144=true" \
  --promptBool "External HDMI-A-1 pinned to 1920x1080@100=true"
```

## Day to day

```sh
chezmoi diff            # what differs between repo and ~/.config
chezmoi apply           # repo -> ~/.config
chezmoi add ~/.config/hypr/bindings.lua   # ~/.config -> repo, after editing in place
```

Files are copied, never symlinked: deleting or moving this repo leaves `~/.config` intact.

## Layout

| Path | Target |
|---|---|
| `dot_config/hypr/` | `~/.config/hypr/` (`bindings.lua`, `monitors.lua` template) |
| `dot_config/omarchy/` | shell, hooks, branding (`about.txt`/`screensaver.txt` are what `omarchy branding` edits), theme `moon` (palette generated with aether from the moon wallpapers, no per-app overrides, tux `unlock.png`, 7 wallpapers in `backgrounds/`, screenshot `preview.png`) |
| `dot_config/uwsm/env-hyprland` | `AQ_DRM_DEVICES`; only applied when `hybrid_gpu` is true |
| `dot_local/bin/` | `hypr-workspace-rotate`; `battery-brownout-logger` (one battery sample per second, fsynced, so the last line survives a hard power cut; its user service is in `dot_config/systemd/user/`); `theme-preview-shot [theme]` composes the switcher preview (nvim, btop, fastfetch, Nautilus) and writes `preview.png` |
| `dot_config/omarchy/hooks/theme-set.d/moon-sync.hook` | after `omarchy theme set moon`: aether's files (`colors.toml`, `icons.theme`, `backgrounds/`) into this repo, the repo's (`unlock.png`, `preview.png`) back into HOME, `preview-unlock.png` regenerated, Slack theme string in `~/.local/state/omarchy/slack-theme.txt` |
| `dot_config/omarchy/hooks/font-set.d/gsettings-sync.hook` | after `omarchy font set`: syncs `org.gnome.desktop.interface monospace-font-name`, which Omarchy never writes, so GTK/Electron apps without their own font setting stop falling back to Adwaita Mono |
| `dot_config/Code/User/settings.json` | VS Code: watcher, search and explorer exclusions so the home directory can be the workspace; monospace family pinned for editor and integrated terminal; Python venv auto-activation off |
| `vscode-extensions.txt` | VS Code extensions installed by `bootstrap.sh`; the editor itself comes from `packages.txt`, its theme from Omarchy |
| `dot_config/mise/config.toml` | toolchains (`node`, `go`, `claude`, `codex`); `bootstrap.sh` runs `mise install` |
| `packages.txt`, `packages-aur.txt` | packages on top of the Omarchy base |
| `themes.txt` | themes reinstalled from git; `aether`-generated themes are per machine |
| `bootstrap.sh` thpm step | `thpm` (AUR) hooks into `theme-set.d`; its `gtk-css-compat` integration writes `~/.config/gtk-{3,4}.0/gtk.css` from the palette so Nautilus and other GTK apps follow the theme. `thpm doctor` reports the state |
| `bootstrap.sh` omen-space step | HP OMEN only (`omarchy hw match omen`): builds `omen-space-git` from the pinned upstream tag with `makepkg`, so pacman owns the daemon, CLI, GUI and the `hp-omen-extra` DKMS module |
| `dot_claude/` | `~/.claude`: settings (secrets rendered from the keyring), CLAUDE.md, hooks, skills |
| `dot_config/rtk/` | rtk config; the binary comes from `bootstrap.sh` |
| `.claude/` | Claude Code settings for working in this repo; not applied to `$HOME` |
| `CLAUDE.md` | facts and toolbelt for the agent working in this repo; not applied to `$HOME` |
| `.claude/hooks/guard-private.sh`, `.githooks/` | refuse files that leak the login, `/home/<login>`, `~/Work`, `~/Projects` or a term from `~/.config/dotfiles-guard/terms` (kept out of git); wired as git pre-commit (`git config core.hooksPath .githooks`, once) and as a Claude Code `PostToolUse` hook |
