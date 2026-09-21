-- Keyboard, mouse and touchpad of Hyprland on this machine.
--
-- Every block below is Omarchy's own default, commented out. Omarchy loads its defaults
-- first (default/hypr/input.lua) and this file after them: a commented line changes
-- nothing, an active line replaces the default for that key only. The file holds no active
-- line unless that line changes how the machine behaves.
--
-- Baseline: Omarchy 4.0.4-1, Hyprland 0.56.2.
-- Live default: /usr/share/omarchy/default/hypr/input.lua
-- Reference: https://wiki.hypr.land/Configuring/Basics/Variables/#input
--
-- To change a key, uncomment the hl.config wrapper of its section and the key itself, and
-- keep the default in a trailing comment:
--
--   hl.config({
--     input = {
--       repeat_rate = 60, -- default 40
--       -- repeat_delay = 250,
--     },
--   })
--
-- Validate: hyprctl reload && hyprctl configerrors

-- input ---------------------------------------------------------------------
-- kb_layout and kb_variant are read from /etc/vconsole.conf (XKBLAYOUT=us, XKBVARIANT unset
-- on this machine). For a layout that cannot type Latin letters Omarchy prepends "us," to
-- kb_layout and appends ",grp:alts_toggle" to kb_options; the values below are the resolved
-- ones, without that branch.

-- hl.config({
--   input = {
--     kb_layout = "us",
--     kb_variant = "",
--     kb_model = "",
--     -- CapsLock is the compose key; both Shifts set Caps Lock, and a lone Shift clears it.
--     kb_options = "compose:caps,shift:both_capslock_cancel",
--     kb_rules = "",
--     follow_mouse = 1,
--     sensitivity = 0,
--
--     repeat_rate = 40,
--     repeat_delay = 250,
--     numlock_by_default = true,
--
--     touchpad = {
--       natural_scroll = false,
--       clickfinger_behavior = true,
--       scroll_factor = 0.4,
--     },
--   },
-- })

-- misc ----------------------------------------------------------------------

-- hl.config({
--   misc = {
--     key_press_enables_dpms = true,
--     mouse_move_enables_dpms = true,
--   },
-- })

-- touchpad scroll per app ---------------------------------------------------
-- A rule written here runs after Omarchy's; for the same window and property the later one wins.

-- o.window("(Alacritty|kitty|foot)", { scroll_touchpad = 1.5 })
-- o.window("com.mitchellh.ghostty", { scroll_touchpad = 0.2 })

-- Examples from Omarchy's template ------------------------------------------
-- Suggestions shipped in Omarchy's user template (config/hypr/input.lua), not defaults.

-- hl.config({
--   input = {
--     -- Use multiple keyboard layouts and switch between them with Left Alt + Right Alt.
--     kb_layout = "us,dk,eu",
--     kb_options = "compose:caps,shift:both_capslock_cancel,grp:alts_toggle",
--
--     -- Use a specific keyboard variant if needed (e.g. intl for international keyboards).
--     kb_variant = "intl",
--
--     -- Change speed of keyboard repeat.
--     repeat_rate = 40,
--     repeat_delay = 250,
--
--     -- Start with numlock on by default.
--     numlock_by_default = true,
--
--     -- Increase sensitivity for mouse/trackpad (default: 0).
--     sensitivity = 0.35,
--
--     -- Turn off mouse acceleration (default: adaptive).
--     accel_profile = "flat",
--
--     touchpad = {
--       -- Use natural (inverse) scrolling.
--       natural_scroll = true,
--
--       -- Use two-finger clicks for right-click instead of lower-right corner.
--       clickfinger_behavior = true,
--
--       -- Control the speed of your scrolling.
--       scroll_factor = 0.4,
--
--       -- Enable the touchpad while typing.
--       disable_while_typing = false,
--
--       -- Left-click-and-drag with three fingers.
--       drag_3fg = 1,
--     },
--   },
-- })

-- App-specific touchpad scroll speeds.
-- o.window("(Alacritty|kitty|foot)", { scroll_touchpad = 1.5 })
-- o.window("com.mitchellh.ghostty", { scroll_touchpad = 0.2 })

-- gestures ------------------------------------------------------------------
-- The 3-finger swipe is Hyprland's built-in workspace_swipe, not an hl.gesture binding:
-- it is on by default and needs no line here to work. Its default create_new = true has
-- no ceiling, so a swipe past the last workspace keeps creating new ones. Turning it off
-- makes the swipe stop at the highest existing workspace, which is the bound
-- hypr-workspace-rotate already enforces for SUPER + scroll and SUPER + TAB. Both paths
-- then agree, and neither creates workspace 6..10 by accident.
--
-- workspace_swipe_forever stays false: at the last workspace a further swipe is a no-op
-- rather than wrapping to 1, matching target_for() in hypr-workspace-rotate, which
-- returns nothing at the edge.

hl.config({
  gestures = {
    workspace_swipe_create_new = false, -- default true
    -- workspace_swipe_forever = false,
  },
})

-- An explicit hl.gesture binding is only needed to change fingers or direction, or to run
-- something other than the built-in swipe.
-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Gestures/
-- hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })

-- Enable touchpad gestures for moving focus (helpful on scrolling layout).
-- hl.gesture({ fingers = 3, direction = "left", action = function() hl.dispatch(hl.dsp.focus({ direction = "l" })) end })
-- hl.gesture({ fingers = 3, direction = "right", action = function() hl.dispatch(hl.dsp.focus({ direction = "r" })) end })
