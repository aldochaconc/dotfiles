# dotfiles

Omarchy customizations, applied with [chezmoi](https://www.chezmoi.io/). Only the delta over
Omarchy's defaults lives here; the defaults come from `omarchy update`.

## Fresh machine

```sh
git clone <this repo> ~/dotfiles
~/dotfiles/bootstrap.sh
```

`bootstrap.sh` installs the extra packages, runs `chezmoi init --apply` (three yes/no questions
about this machine's displays and GPU), sets the Omarchy defaults and the kept web apps.

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
| `dot_config/omarchy/` | shell, hooks, branding, themes (wallpapers excluded) |
| `dot_config/uwsm/env-hyprland` | `AQ_DRM_DEVICES`; only applied when `hybrid_gpu` is true |
| `dot_local/bin/` | `hypr-workspace-rotate` |
| `packages.txt`, `packages-aur.txt` | packages on top of the Omarchy base |
| `themes.txt` | themes reinstalled from git; `aether`-generated themes are per machine |
| `.claude/` | Claude Code settings for working in this repo; not applied to `$HOME` |
