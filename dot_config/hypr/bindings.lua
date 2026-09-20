-- Keep only your personal keybinding overrides here. Add new bindings or
-- unbind defaults before replacing them.

-- See current bindings and descriptions:
--   omarchy menu keybindings --print

-- To disable every Omarchy default binding, set this in
-- ~/.config/hypr/hyprland.lua before require("default.hypr.omarchy"), then add
-- only the bindings you want below:
--   omarchy_default_bindings = false

-- To disable all preinstalled app/webapp bindings, set:
--   omarchy_preinstalled_bindings = false

-- Add a new binding.
-- o.bind("SUPER + SHIFT + R", "SSH", "alacritty -e ssh your-server")

-- Change an existing binding by unbinding it first, then binding the key again.
-- This example changes SUPER+SPACE from the launcher to the Omarchy root menu.
-- hl.unbind("SUPER + SPACE")
-- o.bind("SUPER + SPACE", "Omarchy menu", "omarchy-menu toggle root")

-- Disable a default binding without replacing it.
-- hl.unbind("SUPER + SHIFT + B")

-- Logitech MX Keys examples:
-- o.bind("SUPER + SHIFT + S", nil, "omarchy-capture-screenshot")
-- o.bind("SUPER + H", nil, "voxtype record toggle")
-- o.bind("SUPER + PERIOD", nil, "omarchy-shell shell toggle omarchy.emojis")

-- === VIM-style window control ===

-- Cross monitor boundaries when moving a window past a tiling edge.
hl.config({ binds = { window_direction_monitor_fallback = true } })

-- Focus: SUPER + HJKL. The arrow keys keep Omarchy's defaults.
-- Replaced defaults: J was "Toggle window split", K was "Keybindings",
-- L was "Toggle workspace layout". H was unbound.
hl.unbind("SUPER + J")
hl.unbind("SUPER + K")
hl.unbind("SUPER + L")

o.bind("SUPER + H", "Move window focus left", hl.dsp.focus({ direction = "l" }))
o.bind("SUPER + L", "Move window focus right", hl.dsp.focus({ direction = "r" }))
o.bind("SUPER + K", "Move window focus up", hl.dsp.focus({ direction = "u" }))
o.bind("SUPER + J", "Move window focus down", hl.dsp.focus({ direction = "d" }))

-- Move window: SUPER + CTRL + HJKL, with the arrows as aliases.
-- Replaced default: CTRL + L was "Lock system", rebound to CTRL + ESCAPE below.
hl.unbind("SUPER + CTRL + L")

o.bind("SUPER + CTRL + H", "Move window left", hl.dsp.window.move({ direction = "l" }))
o.bind("SUPER + CTRL + L", "Move window right", hl.dsp.window.move({ direction = "r" }))
o.bind("SUPER + CTRL + K", "Move window up", hl.dsp.window.move({ direction = "u" }))
o.bind("SUPER + CTRL + J", "Move window down", hl.dsp.window.move({ direction = "d" }))

o.bind("SUPER + CTRL + LEFT", "Move window left", hl.dsp.window.move({ direction = "l" }))
o.bind("SUPER + CTRL + RIGHT", "Move window right", hl.dsp.window.move({ direction = "r" }))
o.bind("SUPER + CTRL + UP", "Move window up", hl.dsp.window.move({ direction = "u" }))
o.bind("SUPER + CTRL + DOWN", "Move window down", hl.dsp.window.move({ direction = "d" }))

-- Lock screen, displaced from SUPER + CTRL + L by the binding above.
o.bind("SUPER + CTRL + ESCAPE", "Lock system", "omarchy-lock-screen")

-- === Workspace rotation ===

-- The workspace selectors cannot express a ceiling: r+1 creates the missing
-- workspace but never stops climbing, and e+1 stops at what exists but wraps.
-- hypr-workspace-rotate creates and clamps to 1..9.
local rotate = os.getenv("HOME") .. "/.local/bin/hypr-workspace-rotate"

o.bind("SUPER + Prior", "Next workspace", rotate .. " next")
o.bind("SUPER + Next", "Previous workspace", rotate .. " prev")

-- Omarchy binds SUPER + wheel to e+1/e-1 with the opposite direction; realign it.
hl.unbind("SUPER + mouse_down")
hl.unbind("SUPER + mouse_up")

o.bind("SUPER + mouse_up", "Next workspace", rotate .. " next")
o.bind("SUPER + mouse_down", "Previous workspace", rotate .. " prev")

-- SUPER + TAB defaults to e+1/e-1 too (wraps, never creates). Same clamp.
hl.unbind("SUPER + TAB")
hl.unbind("SUPER + SHIFT + TAB")

o.bind("SUPER + TAB", "Next workspace", rotate .. " next")
o.bind("SUPER + SHIFT + TAB", "Previous workspace", rotate .. " prev")

-- === Launcher ===

-- Reach the app launcher from the home row. SUPER + SPACE keeps the root menu
-- and SUPER + ALT + SPACE keeps the same apps menu.
o.bind("SUPER + SEMICOLON", "Apps menu", "omarchy-menu toggle apps")
