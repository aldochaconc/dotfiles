# System Profile - crystal's Arch Linux / Omarchy Setup

This document describes the full system environment for LLM-assisted work: ricing, development, technical support, and troubleshooting.

## Hardware

- **CPU**: AMD Ryzen 7 5800H (8C/16T, Zen 3, integrated Radeon Vega)
- **GPU (dedicated)**: NVIDIA GeForce RTX 3050 Ti Laptop (GA107M)
- **GPU (integrated)**: AMD Cezanne Radeon Vega
- **RAM**: 16 GB DDR4
- **Storage**: 465.8 GB NVMe (LUKS-encrypted, btrfs), 119.2 GB NVMe (Windows/NTFS)
- **Swap**: 7.5 GB zram
- **Display**: Laptop 1920x1080@144Hz (eDP-1) + External 1920x1080@60Hz (HDMI-A-1)

## OS & Desktop Environment

- **OS**: Arch Linux (kernel 6.x, rolling release)
- **DE Framework**: [Omarchy](https://omarchy.com) v3.4.1 (Hyprland-based Arch environment by DHH)
- **Compositor**: Hyprland (Wayland)
- **Session manager**: UWSM
- **Display manager**: SDDM
- **Theme**: Crystal (active, Kanso Zen bg + Kanagawa warm fg), Archenemy (custom theme also available)
- **Notification daemon**: Mako
- **Status bar**: Waybar
- **App launcher**: Walker (with Elephant providers)
- **Volume OSD**: SwayOSD
- **Idle/Lock**: Hypridle + Hyprlock
- **Night light**: Hyprsunset
- **Screenshot**: Grim + Slurp + Satty
- **Wallpaper**: Swaybg

## GPU / Graphics Configuration

Hybrid NVIDIA + AMD iGPU setup. Key env vars in `hypr/envs.conf`:

- `AQ_DRM_DEVICES="/dev/dri/nvidia-gpu:/dev/dri/amd-igpu"` (dual GPU render order)
- `LIBVA_DRIVER_NAME=nvidia`, `NVD_BACKEND=direct` (NVIDIA VA-API)
- `__GLX_VENDOR_LIBRARY_NAME=nvidia` (GLX on dGPU)
- `WLR_DRM_NO_ATOMIC=1` (workaround for NVIDIA atomic modesetting)
- `cursor { no_hardware_cursors = true }` (NVIDIA cursor fix)
- VRR/VFR enabled, G-Sync allowed
- NVIDIA driver: 590.48.01 (nvidia-open-dkms)

## Terminal & Shell

- **Shell**: Zsh with Oh My Zsh (robbyrussell theme, plugins: git, nvm)
- **Terminal emulators**: Alacritty, Ghostty, Kitty (launched via `xdg-terminal-exec`)
- **Prompt**: Starship
- **System fetch**: Fastfetch (runs on shell start)
- **Multiplexer**: tmux

## Development Stack

### Languages & Runtimes
- **Node.js**: v24.x (managed via NVM + mise)
- **Go**: 1.26.x
- **Rust**: 1.93.x (system rustc)
- **Python**: 3.14.x
- **.NET**: dotnet-runtime + dotnet-runtime-9.0
- **Ruby**, **Lua** (luarocks), **C/C++** (clang, cmake, meson)

### Package Managers
- **System**: pacman + yay (AUR)
- **Node**: pnpm, npm (via nvm)
- **Python**: uv, poetry
- **Rust**: cargo
- **Runtime version manager**: mise

### Editors & IDEs
- **Primary**: Neovim (omarchy-nvim, LazyVim-based with cached plugins)
- **Secondary**: Cursor (AI-enhanced VS Code fork), Code OSS
- **AI coding**: Claude Code, OpenAI Codex

### Dev Tools
- **Git GUI**: Lazygit
- **Docker GUI**: Lazydocker
- **Docker**: Docker 29.x + Buildx + Compose
- **Git workflow**: Graphite (stacked PRs)
- **GitHub CLI**: gh
- **Database**: DBeaver (MariaDB, PostgreSQL client libs installed)
- **Search**: ripgrep, fd, fzf, plocate
- **File listing**: eza, lsd, tree
- **Misc**: bat, jq, yq, dust, tldr, inxi

### Cloud & Infra
- **AWS**: aws-cli-v2
- **Containers**: Docker + Docker Compose

## Input Method

- **Framework**: Fcitx5 (for multilingual input, likely Japanese/CJK support)
- **Env vars**: `INPUT_METHOD=fcitx`, `QT_IM_MODULE=fcitx`, `XMODIFIERS=@im=fcitx`

## Keyboard Layout

- **Layouts**: US + Latin American (`us,latam`)
- **Toggle**: Alt+Space (`grp:alt_space_toggle`)
- **Repeat rate**: 40, delay: 600

## Hyprland Keybindings (User Overrides)

- `SUPER+H/J/K/L`: Vim-style window focus (left/down/up/right)
- `SUPER+RETURN`: Terminal (with CWD preservation)
- `SUPER+F`: Full width | `SUPER+ALT+F`: Fullscreen | `SUPER+CTRL+F`: Tiled fullscreen
- `SUPER+SHIFT+T`: btop activity monitor
- **Browser**: Thorium (`$browser = thorium-browser`)
- **Tearing**: Allowed (`allow_tearing = true`)

## Filesystem

- **Root + Home**: Single LUKS-encrypted btrfs partition (`/dev/mapper/root`, 464 GB)
- **Boot**: 2 GB FAT32 (`/boot`)
- **Bootloader**: Limine
- **Snapshots**: Snapper (btrfs snapshots)
- **Dual boot**: Windows on separate NVMe (ntfs)

## Audio

- **Server**: PipeWire (+ pipewire-pulse, pipewire-jack, pipewire-alsa)
- **Session manager**: WirePlumber
- **Noise suppression**: RNNoise
- **Mixer**: Wiremix

## Networking

- **WiFi**: iwd
- **Firewall**: UFW (+ ufw-docker)
- **Discovery**: nss-mdns (mDNS/Avahi)
- **File sharing**: gvfs-mtp, gvfs-nfs, gvfs-smb
- **Bluetooth**: BlueTUI

## Fonts

- Cascadia Mono Nerd, JetBrains Mono Nerd, Meslo Nerd, Fira Code
- IA Writer (monospace/serif)
- Monaco
- Noto fonts (full: CJK, emoji, extra)
- Font Awesome (woff2)
- Omarchy custom font (omarchy.ttf)

## Notable Apps

- **Browser**: Thorium (primary), Firefox, Brave, Chromium, Google Chrome
- **Music**: Spotify (via spotify-launcher)
- **Notes**: Obsidian
- **Chat**: Slack
- **PDF**: Evince, Xournal++
- **Video**: MPV, KDEnlive
- **E-books**: Calibre
- **Image viewer**: imv
- **File manager**: Nautilus
- **Screen recorder**: GPU Screen Recorder
- **LAN sharing**: LocalSend
- **Guitar tuner**: Lingot

## Dotfiles Repo Structure

```
shell/          # .zshrc (sanitized), .bash_profile, secrets template
hypr/           # Hyprland: monitors, bindings, input, envs, autostart, looknfeel
waybar/         # Status bar config + style
omarchy/        # Custom Omarchy themes (crystal, archenemy)
omarchy-config/ # Omarchy hooks
alacritty/      # Terminal config
ghostty/        # Terminal config
kitty/          # Terminal config
mako/           # Notification daemon
walker/         # App launcher
swayosd/        # Volume/brightness OSD
fastfetch/      # System fetch
btop/           # System monitor + themes
starship.toml   # Shell prompt
nvim/           # (managed by omarchy-nvim)
lazygit/        # Git TUI
lazydocker/     # Docker TUI
mise/           # Runtime version manager
git/            # Git global config + fontconfig
cursor/         # Cursor editor settings + keybindings
code-oss/       # VS Code OSS settings
environment.d/  # XDG environment (fcitx)
fontconfig/     # Font rendering
fcitx5/         # Input method
uwsm/           # Session manager
systemd/user/   # User systemd units (elephant, battery monitor)
nwg-displays/   # Display layout tool
```

## Omarchy Theming Reference

Omarchy's theming system is template-driven. Understanding the layering is critical for customization.

### Architecture

1. **Built-in themes** live at `~/.local/share/omarchy/themes/<name>/` (managed by pacman, never edit)
2. **User themes** live at `~/.config/omarchy/themes/<name>/` (this is what we track in dotfiles)
3. **Active theme** is assembled at `~/.config/omarchy/current/theme/` by `omarchy-theme-set`

### Theme Application Order (`omarchy-theme-set`)

```
1. Copy built-in theme files:     ~/.local/share/omarchy/themes/<name>/*  -> current/next-theme/
2. Overlay user theme files:      ~/.config/omarchy/themes/<name>/*       -> current/next-theme/  (overwrites)
3. Generate templated configs:    default/themed/*.tpl + colors.toml      -> current/next-theme/  (only if file doesn't exist yet)
4. Atomic swap:                   current/next-theme/                     -> current/theme/
5. Restart components:            waybar, swayosd, terminal, hyprctl, btop, mako, etc.
6. Set app themes:                gnome, browser, vscode, obsidian, keyboard
7. Run hook:                      ~/.config/omarchy/hooks/theme-set
```

User theme files take precedence over built-in ones. Template-generated files are only created if neither the built-in nor user theme provided that file.

### Theme File Structure

A theme directory can contain any subset of these files:

| File | Purpose |
|------|---------|
| `colors.toml` | **Core** - defines all color variables used by templates |
| `backgrounds/` | Wallpaper images (cycled by `omarchy-theme-bg-next`) |
| `alacritty.toml` | Alacritty color override (skips template if present) |
| `ghostty.conf` | Ghostty color override |
| `kitty.conf` | Kitty color override |
| `hyprland.conf` | Hyprland theme vars (borders, shadows, etc.) |
| `hyprlock.conf` | Lock screen styling |
| `waybar.css` | Status bar styling |
| `walker.css` | App launcher styling |
| `swayosd.css` | Volume/brightness OSD styling |
| `mako.ini` | Notification styling |
| `btop.theme` | System monitor theme |
| `neovim.lua` | Neovim colorscheme config |
| `vscode.json` | VS Code theme mapping |
| `chromium.theme` | Browser theme |
| `obsidian.css` | Obsidian note theme |
| `icons.theme` | Icon theme name |
| `preview.png` | Theme preview image |

### `colors.toml` Format

The only required file for template generation. Defines variables for `{{ variable }}` placeholders in `.tpl` files:

```toml
accent = "#8BA4B0"
cursor = "#c8c093"
foreground = "#dcd7ba"
background = "#090E13"
selection_foreground = "#c8c093"
selection_background = "#24262D"

color0 = "#1C1E25"    # black (zenBg1)
color1 = "#C4746E"    # red (Kanso red3)
color2 = "#8A9A7B"    # green (Kanso green3)
color3 = "#C4B28A"    # yellow (Kanso yellow3)
color4 = "#8BA4B0"    # blue (Kanso blue3)
color5 = "#A292A3"    # magenta (Kanso pink)
color6 = "#8EA4A2"    # cyan (Kanso aqua)
color7 = "#dcd7ba"    # white (Kanagawa warm)
color8 = "#9E9B93"    # bright black (Kanso gray2)
color9 = "#E46876"    # bright red (Kanso red2)
color10 = "#87A987"   # bright green (Kanso green2)
color11 = "#E6C384"   # bright yellow (Kanso yellow2)
color12 = "#7FB4CA"   # bright blue (Kanso blue)
color13 = "#938AA9"   # bright magenta (Kanso violet)
color14 = "#7AA89F"   # bright cyan (Kanso green5)
color15 = "#dcd7ba"   # bright white (Kanagawa warm)
```

Template variables: `{{ key }}` (raw value), `{{ key_strip }}` (hex without `#`), `{{ key_rgb }}` (decimal R,G,B).

### Theme Commands

| Command | Description |
|---------|-------------|
| `omarchy-theme-set <name>` | Apply a theme (user themes override built-in) |
| `omarchy-theme-list` | List all available themes (built-in + user) |
| `omarchy-theme-current` | Show current theme name |
| `omarchy-theme-bg-next` | Cycle to next background image |
| `omarchy-theme-bg-set <path>` | Set specific background |
| `omarchy-theme-bg-install` | Install a background image |
| `omarchy-theme-refresh` | Regenerate current theme from templates |
| `omarchy-theme-install` | Install a theme from URL/file |
| `omarchy-theme-remove` | Remove a user theme |
| `omarchy-theme-update` | Update themes |

### User Backgrounds

Per-theme user backgrounds can be placed at `~/.config/omarchy/backgrounds/<theme-name>/`. These are merged with the theme's built-in backgrounds when cycling.

### Hooks

User hooks live at `~/.config/omarchy/hooks/`:

| Hook | Trigger | Args |
|------|---------|------|
| `theme-set` | After theme is applied | `$1` = theme name |
| `font-set` | After font is changed | `$1` = font name |
| `post-update` | After Omarchy updates | none |

### Custom Theme: Crystal

The `crystal` theme (`~/.config/omarchy/themes/crystal/`) is built on **Kanso Zen** backgrounds with **Kanagawa-warm** foreground for readability. Theme source is tracked separately in `~/Work/omarchy-theme-crystal/` (not in this dotfiles repo).

**Color architecture**: `colors.toml` is the single source of truth. All apps read from it:
- Terminals (kitty, alacritty, ghostty): via `.tpl` templates at theme-set time
- Waybar, mako, walker, swayosd: via `.tpl` templates at theme-set time
- **Neovim**: `neovim.lua` reads `colors.toml` at startup and maps values to [kanso.nvim](https://github.com/webhooked/kanso.nvim) palette overrides — no hardcoded hex values
- VS Code: Kanso Zen extension (`vscode.json`)
- Zed: Custom Crystal theme (`~/.config/zed/themes/crystal.json`) — scaffolded from Aether

**To customize**:

1. Edit `~/.config/omarchy/themes/crystal/colors.toml` — this propagates everywhere
2. Run `omarchy-theme-set crystal` to apply
3. Neovim picks up changes on next launch (reads from `~/.config/omarchy/current/theme/colors.toml`)

**Design decisions**:
- Backgrounds from Kanso Zen (`#090E13`, `#1C1E25`, `#22262D`) — deep, rich darks
- Foreground from Kanagawa (`#dcd7ba`) — warm golden tone, more readable than Kanso's cooler `#C5C9C7`
- Neovim uses `webhooked/kanso.nvim` with palette overrides sourced from `colors.toml` to prevent drift

### Omarchy Config Layering (General)

Omarchy uses a consistent override pattern across all configs:

```
~/.local/share/omarchy/default/   <-- Framework defaults (never edit, managed by pacman)
~/.local/share/omarchy/config/    <-- Default user configs (refreshed by omarchy-refresh-config)
~/.config/                        <-- User overrides (what we track in dotfiles)
```

For Hyprland specifically, `~/.config/hypr/hyprland.conf` sources defaults first, then user overrides:
```
source = ~/.local/share/omarchy/default/hypr/*.conf     # Omarchy defaults
source = ~/.config/omarchy/current/theme/hyprland.conf   # Theme colors
source = ~/.config/hypr/*.conf                            # User overrides (tracked here)
```

### Omarchy Command Naming Convention

All commands start with `omarchy-`. Prefixes indicate purpose:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `cmd-` | Utility checks | `omarchy-cmd-missing`, `omarchy-cmd-terminal-cwd` |
| `pkg-` | Package management | `omarchy-pkg-add`, `omarchy-pkg-missing` |
| `hw-` | Hardware detection | `omarchy-hw-asus-rog` |
| `refresh-` | Copy default config to `~/.config/` | `omarchy-refresh-config` |
| `restart-` | Restart a component | `omarchy-restart-waybar` |
| `launch-` | Open applications | `omarchy-launch-tui` |
| `install-` | Install optional software | `omarchy-install-*` |
| `setup-` | Interactive setup wizards | `omarchy-setup-*` |
| `toggle-` | Toggle features | `omarchy-toggle-*` |
| `theme-` | Theme management | `omarchy-theme-set`, `omarchy-theme-list` |
| `update-` | Update components | `omarchy-update-*` |

## Conventions for LLM Assistance

- **Config edits**: Omarchy sources defaults from `~/.local/share/omarchy/default/` then user overrides from `~/.config/hypr/`. Always edit user overrides, never default files.
- **Theme edits**: Edit files in `~/.config/omarchy/themes/crystal/`, then run `omarchy-theme-set crystal` to apply. Never edit `~/.local/share/omarchy/themes/` or `~/.config/omarchy/current/theme/` directly.
- **Package installation**: Use `yay` (handles both pacman and AUR).
- **Service management**: `systemctl --user` for user units, `sudo systemctl` for system units.
- **NVIDIA troubleshooting**: Check `hypr/envs.conf` for GPU env vars. The system uses nvidia-open-dkms with hybrid GPU setup.
- **Secrets**: Never hardcode tokens. Use `~/.zshrc.local` (sourced by .zshrc, gitignored).
- **Bootloader**: Limine (not GRUB). Config is at `/boot/limine.conf`.
- **Encryption**: Root is LUKS-encrypted btrfs. Be careful with partition operations.
