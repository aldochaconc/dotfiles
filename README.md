# dotfiles

Arch Linux + [Omarchy](https://omarchy.com) (Hyprland) dotfiles with the **Crystal** theme.

Kanso Zen backgrounds, Kanagawa-warm foreground, deep darks.

![Desktop](preview.png)
![Editor](preview_2.png)
![Terminal](preview_3.png)

## Stack

- **WM**: Hyprland (Wayland)
- **Bar**: Waybar
- **Notifications**: Mako / Dunst (typewriter effect)
- **Launcher**: Rofi
- **Terminal**: Kitty
- **Shell**: Zsh
- **Editor**: Neovim

## Setup

Built on Omarchy's layered config system. User overrides in `~/.config/` take precedence over framework defaults.

```
make install
omarchy-theme-set crystal
```
