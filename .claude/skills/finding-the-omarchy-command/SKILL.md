---
name: finding-the-omarchy-command
description: Use when changing anything on this Omarchy machine (GPU mode, displays, defaults, packages, themes, services, boot screen, permissions) or when about to run a low-level tool (supergfxctl, pacman, xdg-settings, hyprctl keyword, systemctl) or edit a file under /etc or ~/.config by hand. Also when asked whether Omarchy has a bar widget, panel or plugin for something, before answering that none exists.
---

# Finding the Omarchy command

## Wrapper over tool

Omarchy wraps the low-level tool and also handles what the tool does not know about:
hooks, systemd drop-ins, state files, config regeneration. Calling the tool directly
leaves those behind. The wrapper decides every side effect; the tool only runs the last
step of it.

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

## Plugin the machine does not have yet

`/usr/share/omarchy/shell/plugins/` holds what Omarchy ships plus what is already
installed, and `omarchy plugin list` shows both. Neither covers the community
marketplace, so a bar widget absent from the local tree is not a widget that does not
exist. Answering from the local tree alone is how a search for removable-drive mounting
concluded that Omarchy had nothing, while three approved plugins for it were listed.

The marketplace is `omacom/omarchy-plugin-marketplace` on GitHub, published at
plugins.omarchy.org. Its issues carry the state, one per submission, and are what a
search reads:

```sh
gh search issues --repo omacom/omarchy-plugin-marketplace "<purpose>" --label listed
```

`registry.json` in that repo answers the same question and is 6.5 MB, large enough that
a fetch summarizes it instead of searching it: a read of it reported no drive plugins
while three were listed. Search the issues.

| Label | Meaning |
|---|---|
| `listed` with `approved-and-verified` | Published, current approval |
| `listed` with `approved-for-listing` | Published under the legacy approval, closed to new submissions |
| `validated` alone | Automated checks passed, no maintainer decision yet |
| `needs-fixes`, `security-needs-fixes` | Rejected pending changes |
| `manual-setup` | `omarchy plugin add` alone does not produce a working plugin |

Install with `omarchy plugin add <git-url> --enable`; `omarchy plugin` also carries
`clone`, `disable`, `enable`, `list`, `remove`, `update` and `validate`. A plugin outside
the marketplace may install by other means, which is a reason to prefer a listed one.

The marketplace states that community plugins "execute as unsandboxed code and may
access or modify files", and that its checks "are not a security audit, certification,
endorsement, or guarantee that a plugin is safe". Read the source before installing:
what commands it runs, whether it reaches the network, and whether it writes to disks.
This repository records that review per entry in `plugins.txt`.

## Cost of the direct call

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
