# dotfiles

This repository is the chezmoi source for one Omarchy machine, and the handbook for how that
machine is put together. chezmoi copies each file into `$HOME`, so the machine keeps working if
this checkout is moved or deleted. Omarchy owns the defaults and ships them with
`omarchy update`, and only the delta over them lives here.

The agent working in this repository reads `CLAUDE.md`, which holds the rules of this machine
and the toolbelt. This file describes how the pieces fit, and it does not restate those rules.

## Fresh machine

```sh
git clone <this repo> ~/dotfiles
~/dotfiles/bootstrap.sh
```

`bootstrap.sh` is safe to re-run. It asks for a password when a step writes under `/etc`. Its
steps, in order:

1. Packages from `packages.txt`, through `omarchy pkg add`.
2. Journal capped at 500M, and AUR builds without leftover makedepends or `-debug` packages.
3. The shephrd approve helper, installed from `system/shephrd` to `/usr/local/lib/shephrd`.
4. AUR packages from `packages-aur.txt`.
5. zsh as the login shell, and thpm with its GTK integration.
6. Three secrets stored in the system keyring, then `chezmoi init --apply`.
7. rtk from its release tarball, checked against its sha256.
8. The HP OMEN daemon, built from a pinned tag on OMEN hardware only.
9. `mise install`, then the Claude Code marketplaces and plugins.
10. The Omarchy defaults (browser, terminal, editor) and the Chromium policy that installs the
    Claude extension.
11. User tmpfiles, VS Code extensions and the WhatsApp web app.
12. The themes in `themes.txt` and the shell plugins in `plugins.txt`.

`chezmoi init` asks four questions once per machine and stores the answers in
`~/.config/chezmoi/chezmoi.toml`. Without a TTY, answer them on the command line.
`--promptBool` is keyed by the prompt text:

```sh
chezmoi init --source ~/dotfiles \
  --promptBool "Hybrid AMD+NVIDIA laptop (supergfxd Hybrid, AQ_DRM_DEVICES for Hyprland)=true" \
  --promptBool "Laptop panel eDP-1 pinned to 1920x1080@144=true" \
  --promptBool "External HDMI-A-1 pinned to 1920x1080@100=true" \
  --promptString "Path to the Google Drive MCP build (index.js), empty if none="
```

The boot and login screen is one manual step per machine, and it needs sudo. It shows tux on
solid black with white text, independent of the active theme, and the same file reapplies it
after an update restores the stock logo:

```sh
~/.config/omarchy/hooks/post-update.d/plymouth-boot.hook
```

## Day to day

| Change made | Command |
|---|---|
| in the repo | `chezmoi diff`, then `chezmoi apply <target>` |
| in place under `$HOME` | `chezmoi re-add <target>` |
| file to remove | `chezmoi destroy <target>`, which drops source, target and state together |
| file moved inside the source | `chezmoi destroy` the old target, since `apply` never removes what the source no longer holds |

A panel or a plugin that saves settings writes `~/.config/omarchy/shell.json`, and the next
`chezmoi apply` reverts it. Run `chezmoi re-add ~/.config/omarchy/shell.json` after any change
made from the bar.

## How Omarchy is put together

Omarchy 4.0.4 installs everything it owns under `/usr/share/omarchy`, read-only. The scripts are
`/usr/bin/omarchy-*`, dispatched by the `omarchy <group> <action>` CLI, and `omarchy commands`
lists them all.

| Directory | Holds |
|---|---|
| `config/` | templates copied into `~/.config` at install time |
| `default/` | defaults that stay in place: `hypr/*.lua`, `uwsm/`, `systemd/`, `themed/*.tpl`, the menu |
| `shell/` | the Quickshell application: `shell.qml`, `services/`, first-party `plugins/` |
| `themes/` | stock themes |
| `migrations/` | `<epoch>.sh` scripts, each run once and marked in `~/.local/state/omarchy/migrations` |
| `install/` | the installer and the base package lists |

### Hyprland

`~/.config/hypr/hyprland.lua` loads everything in a fixed order, and the last rule or `hl.env`
wins:

1. `$OMARCHY_PATH/default/hypr/bootstrap.lua` sets `package.path` to `~/.local/state`,
   `~/.config` and `$OMARCHY_PATH`, in that order.
2. `omarchy_default_bindings = false`. Every stock binding is off, so a key missing from
   `bindings.lua` does nothing.
3. `default.hypr.omarchy` loads the helpers, autostart, envs, look and feel, input and window
   rules, then the current theme's `hyprland.lua`.
4. The user files: `monitors`, `input`, `bindings`, `looknfeel`, `autostart`.
5. `default.hypr.toggles` loads every file under `~/.local/state/omarchy/toggles/hypr`, which
   `omarchy toggle` writes and chezmoi does not track.
6. The window rules at the end of `hyprland.lua`.

`omarchy refresh hyprland` overwrites the user files. `chezmoi apply` restores the versioned
ones, and a toggle reset by the refresh has to be redone by hand.

### Shell and bar

Hyprland's autostart runs `omarchy-launch-shell`, which starts `quickshell -p
$OMARCHY_PATH/shell` and relaunches it up to five times a minute. There is no systemd unit:
the logs are in `journalctl -t omarchy-shell`, `omarchy-shell` only talks to the running
process over IPC, and `omarchy restart shell` restarts it.

`~/.config/omarchy/shell.json` replaces the default shell.json whole when it carries
`version: 1`. It holds the bar layout, idle timers, the enabled third-party plugins and the
disabled first-party ones. The shell reloads it on save.

Plugins come from `$OMARCHY_PATH/shell/plugins` and from `~/.config/omarchy/plugins/<id>`.
Their kinds are `bar`, `bar-widget`, `panel`, `overlay`, `menu` and `service`. A plugin whose
manifest declares `clonedFrom` replaces the built-in it names, and removing it brings the
built-in back. One bar runs at a time: `bar.id` picks it, and `omarchy.bar` is the default.

Community plugins run unsandboxed inside the shell, and marketplace approval is not a security
audit. Each line of `plugins.txt` carries the commit its source was read at and what the review
found. Plugins that stay installed but off the bar are listed there too, with
`omarchy plugin enable <id>` to bring one back.

### Themes

`omarchy theme set <name>` copies the stock theme, overlays `~/.config/omarchy/themes/<name>`
on it, renders the `themed/*.tpl` templates, swaps the result into
`~/.local/state/omarchy/current/theme` and restarts what reads it. It then runs the `theme-set`
hooks.

### Hooks

`omarchy-hook <event>` runs every file in `~/.config/omarchy/hooks/<event>.d`.

| Event | Fired by | Hooks in this repo |
|---|---|---|
| `theme-set` | `omarchy theme set` | `moon-sync.hook` |
| `font-set` | `omarchy font set` | `gsettings-sync.hook` |
| `post-update` | `omarchy update` | `plymouth-boot.hook`, `setup-agent.hook` |
| `post-boot` | Hyprland autostart | none |
| `battery-low` | the battery service | none |

### Environment

The session environment is built in layers, and a later one overrides an earlier one:

| Layer | Source | Set here |
|---|---|---|
| login shells and uwsm | `default/bash/env-bootstrap`, `/usr/share/uwsm/env.d/10-omarchy` | `OMARCHY_PATH`, `TERMINAL`, `EDITOR`, mise |
| uwsm, user | `~/.config/uwsm/env-hyprland`, `~/.config/uwsm/env.d/*` | `AQ_DRM_DEVICES` (hybrid GPU only), `OMARCHY_SCREENSHOT_DIR` |
| Hyprland | `default/hypr/envs.lua`, then `hl.env` in the user files | Wayland and toolkit variables; `LIBVA_DRIVER_NAME`, `GDK_SCALE` |
| systemd user and D-Bus | Hyprland autostart imports the whole environment | |

`~/.config/uwsm/env.d/secrets` exports the tokens the Claude Code MCP servers read. It is
written by hand and ignored by git.

### Updates

`omarchy update` asks for confirmation, prunes the package cache and takes a snapper snapshot.
It then updates the keyring and the system packages, runs pending migrations and the
`post-update` hooks, and updates AUR, mise and orphans. Run it from a terminal: `-y` skips every
prompt, and under `pkexec` the AUR and mise steps run as root and fail.

## What this repository changes

| Source | Target | Contents |
|---|---|---|
| `dot_config/hypr/` | `~/.config/hypr/` | `bindings.lua` with every binding on the machine; `hyprland.lua` with the load order and window rules; `input.lua` with `us,latam` switched by ALT+SPACE; `looknfeel.lua` with the master layout; `monitors.lua` from the chezmoi answers |
| `dot_config/omarchy/private_shell.json` | `~/.config/omarchy/shell.json` | bar layout and enabled plugins |
| `dot_config/omarchy/private_shell.toml` | `~/.config/omarchy/shell.toml` | shell font size |
| `dot_config/omarchy/hooks/` | `~/.config/omarchy/hooks/` | the hooks in the table above |
| `dot_config/omarchy/branding/` | `~/.config/omarchy/branding/` | about and screensaver text, the boot logo |
| `dot_config/omarchy/themes/private_moon/` | `~/.config/omarchy/themes/moon/` | theme generated with aether from the moon wallpapers |
| `dot_config/omarchy/plugins/private_local.workspaces/` | `~/.config/omarchy/plugins/local.workspaces/` | workspaces widget cloned from `omarchy.workspaces` |
| `dot_config/omarchy/create_spotlight.json` | `~/.config/omarchy/spotlight.json` | written once, so Spotlight never binds ALT+SPACE |
| `dot_config/uwsm/` | `~/.config/uwsm/` | the environment rows above |
| `dot_config/systemd/user/` | `~/.config/systemd/user/` | `battery-brownout-logger.service` |
| `dot_config/user-tmpfiles.d/` | `~/.config/user-tmpfiles.d/` | 90-day expiry on build caches, 7 days on screenshots |
| `dot_config/mise/` | `~/.config/mise/` | node, go, claude, codex, and `bw` from npm |
| `dot_config/foot/`, `git/`, `go/`, `btop/`, `Code/`, `Thunar/`, `xfce4/`, `aether/`, `rtk/`, `herdr/` | `~/.config/…` | per-application settings |
| `dot_config/mimeapps.list` | `~/.config/mimeapps.list` | default applications; restore it with `chezmoi apply --force` after `omarchy nvim setup` |
| `dot_local/bin/` | `~/.local/bin/` | the scripts below |
| `dot_claude/` | `~/.claude/` | the agentic setup below |

Scripts in `dot_local/bin`:

| Script | Does |
|---|---|
| `hypr-focus-or-rotate` | moves focus, or rotates to the next workspace at an edge |
| `hypr-window-rotate` | next window in visual order, crossing into the neighbouring workspace |
| `hypr-workspace-rotate` | next or previous workspace among 1 to 5 and any higher one with windows |
| `hypr-workspace-layout-cycle` | cycles master, dwindle and scrolling per workspace |
| `hypr-app-here`, `hypr-app-scratchpad` | bring a single-instance app to the focused workspace or the scratchpad |
| `thunar-cwd` | opens Thunar in the focused terminal's directory |
| `cc` | starts Claude Code under a name other sessions can address |
| `battery-brownout-logger` | one fsynced battery sample per second, so the last line survives a power cut |
| `theme-preview-shot` | composes a theme's `preview.png` |
| `fototeca-flatten`, `fototeca-move-drive-zips` | photo library maintenance, dry run unless `--apply` |

## Agentic system

Claude Code runs under `~/.claude`, and `dot_claude/` is its source. Sessions run in herdr
panes and coordinate through the shephrd plugin.

| Piece | Source | Role |
|---|---|---|
| global instructions | `dot_claude/CLAUDE.md` | reply register, deciding, writing, machine, shell and git rules for every session |
| settings | `.chezmoitemplates/claude-settings.json` | permissions, hooks, plugins and MCP servers |
| settings writer | `dot_claude/modify_private_settings.json.tmpl` | renders the template, and keeps the keys Claude Code rewrites itself: model, theme, effort, default mode, additional directories |
| global hooks | `dot_claude/hooks/` | audit, rtk rewriting, prose register checks, and gates on destructive git, `git add -A`, `rm` on tracked files, uploads and skill writes |
| skills | `dot_claude/skills/` | `writing`, `skill-growth`, `grill-me`, the Obsidian pair, and links to Omarchy's own skills |
| status line | `dot_claude/statusline-command.sh` | model, context and usage limits, and a copy of each payload for `/agents-budget` |
| local marketplace | `dot_claude/plugins/local/` | `machine-local`, which carries shephrd |
| approve helper | `system/shephrd/` | root-owned helper and polkit action, installed by `bootstrap.sh` |

The plugin set is declared in three files that change together: `enabledPlugins` and
`extraKnownMarketplaces` in the settings template, `claude-plugins.txt` and
`claude-marketplaces.txt`. A plugin missing from the template is disabled at the next
`chezmoi apply`. The two text files carry why each plugin is there, and `bootstrap.sh` replays
them.

herdr owns the panes and restores their layout from `~/.config/herdr/session.json`. It does not
restore the agent running inside a pane. shephrd decides who may speak:

| Role | Reaches the user | Reports to |
|---|---|---|
| god | yes, and is the window the user watches | nobody |
| shephrd | through the god | the god |
| sheep | no | its shephrd, or the god that opened it |

The role and scope of each pane are recorded in `~/.claude/panes/<pane>.json`. Each finished
turn writes a beat to `~/.claude/canary`, and a closed session leaves its account in
`~/.claude/handoff`. The shephrd hooks deny a question from a sheep and redirect it to the
session above. They also refuse to end a sheep's turn without a report, and run a command
marked `# shephrd:confirm` only against a single-use approval that the root-owned helper
signed. `shephrd-protocol` holds the full rules.

## Files kept out of `$HOME`

`.chezmoiignore` names them.

| Path | Purpose |
|---|---|
| `bootstrap.sh`, `packages.txt`, `packages-aur.txt`, `themes.txt`, `plugins.txt`, `vscode-extensions.txt`, `claude-plugins.txt`, `claude-marketplaces.txt` | the fresh-machine replay |
| `CLAUDE.md` | rules of this machine and toolbelt, for the agent working here |
| `adr.md` | decisions no other surface owns, each seen twice or structural |
| `multi-session-workspace.md` | design proposal on hold since 2026-09-22 |
| `.claude/` | Claude Code settings and the `finding-the-omarchy-command` skill for this repository |
| `.claude/hooks/guard-private.sh`, `.githooks/pre-commit` | refuse a file that carries the login, the home path or a private term; enable with `git config core.hooksPath .githooks` |
| `.github/pull_request_template.md` | pull request skeleton |
| `system/` | files installed outside `$HOME` by `bootstrap.sh` |

## Known gaps

- Keyring secrets: `bootstrap.sh` stores three secrets in the keyring and no template reads
  them. The settings template takes `${GITHUB_PAT}`, `${GCP_CLIENT_ID}` and
  `${GCP_CLIENT_SECRET}` from the environment.
- Google Drive MCP: `~/.config/uwsm/env.d/secrets` exports `GDRIVE_CLIENT_ID` and
  `GDRIVE_CLIENT_SECRET`, names the template does not read, so the server starts without
  credentials.
- `gdrive_mcp_path`: the answer is stored and nothing reads it. The template hardcodes the
  build path.
- `hdmi_100hz`: the prompt names HDMI-A-1 and the rule it guards sets DP-1.
- `claude_additional_dirs`: set in `.chezmoi.toml.tmpl` and read by no template. The settings
  writer keeps the live value instead.
- `~/.config/mimeapps.list`: omamail registered itself as the `mailto` handler, and the source
  has no such line.
- `~/.config/systemd/user`: mode 0700 in `$HOME` and 0755 in the source.
