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

-- Two layouts, us first and latam second, toggled with ALT + SPACE (grp:alt_space_toggle).
-- The toggle is an XKB option, not a Hyprland binding: it never appears in `hyprctl binds`
-- and ALT + SPACE stays free of any o.bind. kb_options replaces the default wholesale, so
-- compose:caps and shift:both_capslock_cancel are repeated here to survive.
hl.config({
  input = {
    kb_layout = "us,latam", -- default us
    kb_options = "compose:caps,shift:both_capslock_cancel,grp:alt_space_toggle",
  },
})

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
-- The 3-finger swipe is NOT on by default: in Hyprland 0.56 the swipe is an explicit
-- `gesture` binding, and `gestures.workspace_swipe` is no longer an option (getoption
-- reports "no such option"). Omarchy ships the equivalent line commented out in
-- config/hypr/input.lua. Without a binding here the swipe does nothing. The other
-- gestures.workspace_swipe_* options do still exist and still apply to it.
--
-- The swipe uses the built-in `workspace` action, not hypr-workspace-rotate, and that
-- is a deliberate reversal of the earlier arrangement here.
--
-- exec_cmd runs a shell script once, when the gesture ends. That is discrete by
-- construction: nothing can drive a script per millimetre of finger travel, so the
-- workspaces only ever jumped after the fingers lifted, with no sense of the motion.
-- The built-in action is continuous, moving the workspaces with the fingers and
-- snapping on release, which is the whole point of a swipe.
--
-- Cost, accepted: no built-in swipe setting expresses the bar's 1..5 ceiling.
-- create_new = false stops at the last *occupied* workspace, so the swipe reaches less
-- far than the bar draws when 4 and 5 are empty; create_new = true would reach them but
-- never stop, creating 6..10 past the end. Stopping short is the smaller error, since it
-- creates nothing that has to be cleaned up.
--
-- SUPER + TAB and SUPER + scroll still go through hypr-workspace-rotate and still reach
-- exactly 1..5, so the ceiling survives on the paths that can express it. Only the swipe
-- trades it for the drag.
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })

-- These tune the built-in action above, so unlike before they now take effect.
-- create_new = false is the bound that replaces the script's: without it the swipe runs
-- off the end creating 6..10. forever = false makes a swipe at the last workspace a
-- no-op rather than wrapping to 1, matching target_for() in hypr-workspace-rotate,
-- which returns nothing at the edge.
hl.config({
  gestures = {
    workspace_swipe_create_new = false, -- default true
    workspace_swipe_forever = false, -- default false, pinned: it is the edge behaviour
  },
})

-- Enable touchpad gestures for moving focus (helpful on scrolling layout).
-- hl.gesture({ fingers = 3, direction = "left", action = function() hl.dispatch(hl.dsp.focus({ direction = "l" })) end })
-- hl.gesture({ fingers = 3, direction = "right", action = function() hl.dispatch(hl.dsp.focus({ direction = "r" })) end })
