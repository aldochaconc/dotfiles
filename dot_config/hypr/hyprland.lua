-- Learn how to configure Hyprland: https://wiki.hypr.land/Configuring/Start/

-- Omarchy's bootstrap keeps path setup out of this user config.
dofile((os.getenv("OMARCHY_PATH") or "/usr/share/omarchy") .. "/default/hypr/bootstrap.lua")

-- Disable all Omarchy default bindings. Add your own in hypr/bindings.lua.
omarchy_default_bindings = false
--
-- Or disable only bindings for Omarchy's preinstalled apps/web apps while
-- keeping core window-manager bindings:
-- omarchy_preinstalled_bindings = false

-- Load Omarchy defaults.
require("default.hypr.omarchy")

-- Put your personal overrides in these files. They're loaded after Omarchy's
-- defaults so package updates can improve the defaults without rewriting your
-- ~/.config/hypr files.
require("hypr.monitors")
require("hypr.input")
require("hypr.bindings")
require("hypr.looknfeel")
require("hypr.autostart")

-- Toggle config flags dynamically.
require("default.hypr.toggles")

-- Add any other personal Hyprland configuration below.
-- o.window("qemu", { workspace = "5" })

-- Messaging apps open straight into the scratchpad, out of the way of whatever workspace is
-- in front. SUPER + SHIFT + W and SUPER + SHIFT + S reveal one, SUPER + S reveals both.
-- "silent" keeps the focus where it already is when they start.
-- Slack closes its window to the tray rather than exiting, so it can come back from its
-- pinned icon too; WhatsApp is a Chromium web app, so closing its window ends the process
-- and the scratchpad is the only thing keeping it alive.
o.window("^(slack)$", { workspace = "special:scratchpad silent" })
o.window("^(chrome-web\\.whatsapp\\.com__-Default)$", { workspace = "special:scratchpad silent" })

-- Window rules Omarchy applies by default (default/hypr/windows.lua, Omarchy 4.0.4-1), for
-- reference. A rule written in this file runs after them; for the same window and property
-- the later rule wins.
--
-- o.window(".*", { suppress_event = "maximize" })
--
-- -- Tag all windows for default opacity (apps can override with -default-opacity tag).
-- o.window(".*", { tag = "+default-opacity" })
--
-- -- Fix some dragging issues with XWayland.
-- o.window({ class = "^$", title = "^$", xwayland = true, float = true, fullscreen = false, pin = false }, { no_focus = true })
--
-- -- App-specific tweaks, one file each in default/hypr/apps/: 1password, battlenet, bitwarden,
-- -- browser, davinci-resolve, geforce, hermes, jetbrains, localsend, moonlight, omarchy-shell,
-- -- pip, qemu, retroarch, screenshot-selection, steam, system, telegram, terminals,
-- -- webcam-overlay.
--
-- -- Apply default opacity after apps have had a chance to opt out.
-- o.window({ tag = "default-opacity" }, { opacity = "0.985 0.96" })
