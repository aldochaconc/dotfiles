# dotfiles

Omarchy customizations applied with chezmoi. This repo is the chezmoi source (`sourceDir = ~/dotfiles`);
files are copied into `$HOME`, never symlinked. Edited in place → `chezmoi re-add <file>`;
edited here → `chezmoi diff`, then `chezmoi apply`.

Decisions no rule surface owns are logged in [`adr.md`](adr.md). A lesson from a session belongs
in the surface that owns it, `Rules of this machine` below or a skill, and reaches `adr.md` only
when no surface owns it and it has happened twice.

## Rules of this machine

- Every Hyprland keybinding lives in `dot_config/hypr/bindings.lua`. Omarchy's defaults are off
  (`omarchy_default_bindings = false` in `hyprland.lua`): a key not in that file does nothing.
- `.claude/settings.json` is an allowlist by tool. A tool missing there prompts once; add it as
  `Bash(<tool>:*)`, never as the literal command line.
- Deleting a file already applied to `$HOME`: `chezmoi destroy <target>` removes it from the
  source state, from `$HOME` and from chezmoi's state in one step. A bare `rm` on an applied
  file is undone by the next `chezmoi apply`, which restores it from the source state.
- No secret enters the repo. `~/.claude/settings.json` renders them from the system keyring
  (`chezmoi secret keyring get --service claude --user <name>`).
- Omarchy's own tree (`/usr/share/omarchy`) is read-only; overrides go in `~/.config`.

## Toolbelt

| Area | Use |
|---|---|
| GPU (AMD iGPU + NVIDIA, Hybrid) | `supergfxctl -g`, `nvidia-smi`, `prime-run <app>`, `omarchy toggle hybrid gpu` |
| Displays | `hyprctl monitors all`, `omarchy hyprland monitor …`, `dot_config/hypr/monitors.lua.tmpl` |
| Keybindings | `omarchy menu keybindings --print`, `SUPER+SHIFT+K` |
| Audio | `wpctl`, `pw-cli`, `pw-dump`, `pactl` |
| Bluetooth | `bluetoothctl` |
| Power | `powerprofilesctl`, `upower` |
| HP OMEN hardware (fans, RGB, MUX, power limits) | `omen-cli {fetch,system,fan,rgb,power,overlay}`, daemon `omen-space-daemon` (D-Bus `org.hp.omen`), GUI `omen-gui` |
| Network | `iw`, `nmcli` |
| Packages | `omarchy pkg add / drop / aur add`, `pacman -Q…` for queries, `packages*.txt` here |
| Omarchy | `omarchy <group> <action>`, `omarchy commands`, `omarchy <group> --help` |
| System | `systemctl`, `journalctl -b`, `loginctl` |
| Claude Code output | the `rtk` hook filters Bash output; `rtk proxy <cmd>` returns it raw |

## Omarchy commands that move the system

`omarchy commands --all` lists everything; `omarchy <group> --help` documents a group. Grouped by effect:

**Read-only, diagnostics**

| Question | Command |
|---|---|
| Version, channel, last package upgrade | `omarchy version`, `omarchy version channel`, `omarchy version pkgs` |
| Hardware facts | `omarchy hw hybrid gpu`, `omarchy hw nvidia`, `omarchy hw laptop`, `omarchy hw external monitors`, `omarchy hw display`, `omarchy hw touchpad` |
| Monitors as Hyprland sees them | `omarchy hyprland monitor focused`, `omarchy hyprland monitor laptop`, `omarchy monitor state`, `hyprctl monitors all` |
| Theme, font, toggles | `omarchy theme current`, `omarchy theme list`, `omarchy theme dir <name>`, `omarchy font current`, `omarchy toggle enabled <name>` |
| Packages present or missing | `omarchy pkg present <pkgs>`, `omarchy pkg missing <pkgs>` |
| Power, battery, network | `omarchy power present`, `omarchy battery status`, `omarchy powerprofiles list`, `omarchy network status`, `omarchy network band` |
| Updates and their logs | `omarchy update available`, `omarchy update analyze logs` |
| A crashed process | `omarchy agent crash <pid>` (uses `coredumpctl`; see the `diagnose-crash` skill) |
| Diagnostics dump | `omarchy debug --no-sudo --print` (always these two flags: the default asks for sudo interactively) |

**User configuration, no sudo**

| Change | Command |
|---|---|
| Defaults | `omarchy default {browser,terminal,editor,agent} <name>` |
| Theme and wallpaper | `omarchy theme {set,install,remove,update}`, `omarchy theme bg {set,next}` |
| Font, text scale | `omarchy font set <family>`, `omarchy display text size {<n>,reset}` |
| Bar, shell plugins, hooks | `omarchy bar …`, `omarchy plugin {add,clone,enable,disable}`, `omarchy hook install <type> <script>` |
| Web apps | `omarchy webapp install <name> <url> <icon>`, `omarchy webapp remove <name>` |
| Feature toggles | `omarchy toggle {nightlight,idle,bar,touchpad,touchscreen,suspend,screensaver,notification silencing}` |
| Displays | `omarchy hyprland monitor internal {on,off,toggle,recover}`, `… internal mirror …`, `… scaling {up,down,<n>}` |
| Audio, Bluetooth, brightness, power profile | `omarchy audio output {set default,switch}`, `omarchy bluetooth {power,device}`, `omarchy brightness {display,keyboard}`, `omarchy powerprofiles set` |
| Reload after a config edit | `omarchy restart {shell,hyprctl,terminal,hyprsunset,tmux,xcompose}`; services: `omarchy restart {audio,bluetooth,wifi}` |

**Packages and system, sudo**

| Change | Command |
|---|---|
| Packages | `omarchy pkg add <pkgs>`, `omarchy pkg aur add <pkgs>`, `omarchy pkg drop <pkgs>` |
| Updates | `omarchy update`; pieces: `omarchy update {system pkgs,aur pkgs,firmware,orphan pkgs,pkg prune,mise}` |
| GPU mode (hybrid laptop) | `omarchy toggle hybrid gpu` (edits `/etc/supergfxd.conf`, reboots) |
| Migrations, snapshots | `omarchy migrate`, `omarchy snapshot` |
| Optional software | `omarchy install {dev-env,browser,editor} …`, `omarchy remove {preinstalls,browser,dev env} …` |
| Security | `omarchy setup security {fingerprint,fido2,sshd,sudoless docker}`, `omarchy remove security …` |

**Reset, destructive** (they back up first, then overwrite)

| Scope | Command |
|---|---|
| One user config from the shipped template | `omarchy refresh config <path-under-~/.config>` |
| Hyprland Lua files, shell.json, hyprsunset, tmux | `omarchy refresh {hyprland,shell,hyprsunset,tmux}` |
| Everything Omarchy owns in `$HOME` | `omarchy reinstall configs`; packages too: `omarchy reinstall` |

`refresh hyprland` overwrites all seven files under `hypr/`: `.luarc.json`, `autostart.lua`,
`bindings.lua`, `input.lua`, `looknfeel.lua`, `hyprland.lua`, `monitors.lua`. It also copies
`toggles/flags.lua` into `~/.local/state/omarchy/toggles/hypr/`, outside chezmoi's reach.
After it, `chezmoi apply` restores the versioned files. A toggle state reset by that copy is
not restored by chezmoi and has to be redone by hand.

`omarchy font set` never writes `org.gnome.desktop.interface monospace-font-name`: GTK/Electron
apps without their own font setting (Chromium, Slack, Obsidian) fall back to that gsetting, which
otherwise stays at its GNOME default. `hooks/font-set.d/gsettings-sync.hook` re-resolves the active
font with `fc-match` and syncs it after every `omarchy font set`; an already-running app needs a
restart to pick up the new gsetting, since GTK reads it once at startup.

`omarchy nvim {setup,refresh}` and `omarchy reinstall configs` run `xdg-mime default nvim.desktop`
on 17 text types. After them, `chezmoi apply --force ~/.config/mimeapps.list` restores `code`
(`omarchy default editor` never touches MIME).
