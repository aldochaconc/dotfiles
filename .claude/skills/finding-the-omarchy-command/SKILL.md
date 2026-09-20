---
name: finding-the-omarchy-command
description: Use when changing anything on this Omarchy machine (GPU mode, displays, defaults, packages, themes, services, boot screen, permissions) or when about to run a low-level tool (supergfxctl, pacman, xdg-settings, hyprctl keyword, systemctl) or edit a file under /etc or ~/.config by hand.
---

# Finding the Omarchy command

## Overview

Omarchy wraps the low-level tool and also handles what the tool does not know about:
hooks, systemd drop-ins, state files, config regeneration. Calling the tool directly
leaves those behind. The wrapper is the source of truth for side effects; the tool is
only the last step of it.

## Recipe

1. Look up the route before touching anything:
   `omarchy commands --all | grep -i <topic>` (json: `omarchy commands --json`).
2. Read the wrapper, not just its summary: `cat "$(which omarchy-<route-with-dashes>)"`.
   Note `omarchy:requires-sudo`, `gum confirm` prompts, and every path it writes.
3. Run the wrapper. If it prompts for sudo or confirmation, hand the command to the
   user with `!` instead of running it.
4. No wrapper for the change? Identify the owner of the file first:
   `pacman -Qo <file>`. Package-owned (`omarchy`, `omarchy-settings`, anything under
   `/usr/share/omarchy`): do not edit, it is restored on update; find the user override
   (`~/.config/...`) or the toggle. User-owned: edit, reload, then `chezmoi re-add`.
5. Verify with the command that shows the effect, not the file
   (`supergfxctl -g`, `xdg-settings get`, `hyprctl monitors`, `systemctl status`).

## Why the tool alone fails here

| Direct call | What it leaves behind |
|---|---|
| `supergfxctl -m Hybrid` | `/usr/lib/systemd/system-sleep/force-igpu` keeps reverting to Integrated after suspend; `supergfxd.service.d/delay-start.conf` stays. `omarchy toggle hybrid gpu` removes both. |
| `xdg-settings set default-web-browser` | Omarchy's browser default and its launcher entries are not updated. `omarchy default browser <name>` does both. |
| editing `/etc/supergfxd.conf` | The daemon rewrites it; the wrapper edits it through `sed` at the right moment and reboots. |
| `hyprctl keyword monitor ...` | Lost on reload. `~/.config/hypr/monitors.lua` is the persistent place. |

## Rationalizations seen in baseline runs

| Excuse | Reality |
|---|---|
| "The daemon's CLI is the correct way (D-Bus)" | Correct for the daemon, blind to Omarchy's hooks around it. |
| "No time for a wrapper hunt, we have a call in five" | `omarchy commands --all \| grep -i gpu` takes one second. |
| "The wrapper is just a thin alias" | Read it. `omarchy-toggle-hybrid-gpu` is 100 lines and removes two files the tool never touches. |
