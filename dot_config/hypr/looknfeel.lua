-- Look and feel of Hyprland on this machine.
--
-- Every block below is Omarchy's own default, commented out. Omarchy loads its defaults
-- first (default/hypr/looknfeel.lua) and this file after them: a commented line changes
-- nothing, an active line replaces the default for that key only. The file is the map of
-- what can be changed without opening /usr/share/omarchy, and it holds no active line
-- unless that line changes how the machine behaves.
--
-- Baseline: Omarchy 4.0.4-1, Hyprland 0.56.2.
-- Live default: /usr/share/omarchy/default/hypr/looknfeel.lua
-- Reference: https://wiki.hypr.land/Configuring/Basics/Variables/
--
-- To change a key, uncomment the hl.config wrapper of its section and the key itself, and
-- keep the default in a trailing comment. The other keys of the section stay commented
-- inside the active table:
--
--   hl.config({
--     general = {
--       gaps_in = 3, -- default 5
--       -- gaps_out = 10,
--     },
--   })
--
-- Validate: hyprctl reload && hyprctl configerrors

-- general -------------------------------------------------------------------

-- hl.config({
--   general = {
--     gaps_in = 5,
--     gaps_out = 10,
--     border_size = 2,
--
--     -- Painted by the active theme (omarchy.current.theme.hyprland, generated from the
--     -- theme's colors.toml, accent for the active border), so these fallback values are
--     -- never seen. Set here, one color would stick for every theme.
--     col = {
--       active_border = { colors = { "rgba(33ccffee)", "rgba(00ff99ee)" }, angle = 45 },
--       inactive_border = "rgba(595959aa)",
--     },
--
--     resize_on_border = false,
--     allow_tearing = false,
--     layout = "dwindle",
--   },
-- })

-- decoration ----------------------------------------------------------------

-- hl.config({
--   decoration = {
--     rounding = 0,
--
--     shadow = {
--       enabled = false,
--     },
--
--     blur = {
--       enabled = false,
--     },
--   },
-- })

-- group ---------------------------------------------------------------------

-- hl.config({
--   group = {
--     -- Painted by the active theme, same as general.col.
--     col = {
--       border_active = { colors = { "rgba(33ccffee)", "rgba(00ff99ee)" }, angle = 45 },
--       border_inactive = "rgba(595959aa)",
--     },
--
--     groupbar = {
--       font_size = 12,
--       font_family = "monospace",
--       font_weight_active = "ultraheavy",
--       font_weight_inactive = "normal",
--       indicator_height = 1,
--       indicator_gap = 5,
--       height = 22,
--       gaps_in = 5,
--       gaps_out = 0,
--       text_color = "rgb(ffffff)",
--       text_color_inactive = "rgba(ffffff90)",
--       col = {
--         active = "rgba(00000040)",
--         inactive = "rgba(00000020)",
--       },
--       gradients = true,
--       gradient_rounding = 0,
--       gradient_round_only_edges = false,
--     },
--   },
-- })

-- animations ----------------------------------------------------------------
-- https://wiki.hypr.land/Configuring/Advanced-and-Cool/Animations/
-- The curves exist already from Omarchy's defaults, so one hl.animation line can be
-- activated on its own.

-- hl.config({
--   animations = {
--     enabled = true,
--   },
-- })

-- hl.curve("easeOutQuint", { type = "bezier", points = { { 0.23, 1 }, { 0.32, 1 } } })
-- hl.curve("easeInOutCubic", { type = "bezier", points = { { 0.65, 0.05 }, { 0.36, 1 } } })
-- hl.curve("linear", { type = "bezier", points = { { 0, 0 }, { 1, 1 } } })
-- hl.curve("almostLinear", { type = "bezier", points = { { 0.5, 0.5 }, { 0.75, 1.0 } } })
-- hl.curve("quick", { type = "bezier", points = { { 0.15, 0 }, { 0.1, 1 } } })

-- hl.animation({ leaf = "global", enabled = true, speed = 10, bezier = "default" })
-- hl.animation({ leaf = "border", enabled = true, speed = 5.39, bezier = "easeOutQuint" })
-- hl.animation({ leaf = "windows", enabled = true, speed = 3.79, bezier = "easeOutQuint" })
-- hl.animation({ leaf = "windowsIn", enabled = true, speed = 4.1, bezier = "easeOutQuint", style = "popin 87%" })
-- hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.49, bezier = "linear", style = "popin 87%" })
-- hl.animation({ leaf = "fadeIn", enabled = true, speed = 1.73, bezier = "almostLinear" })
-- hl.animation({ leaf = "fadeOut", enabled = true, speed = 1.46, bezier = "almostLinear" })
-- hl.animation({ leaf = "fade", enabled = true, speed = 3.03, bezier = "quick" })
-- hl.animation({ leaf = "fadeSwitch", enabled = false })
-- hl.animation({ leaf = "layers", enabled = true, speed = 3.81, bezier = "easeOutQuint" })
-- hl.animation({ leaf = "layersIn", enabled = true, speed = 4, bezier = "easeOutQuint", style = "fade" })
-- hl.animation({ leaf = "layersOut", enabled = true, speed = 1.5, bezier = "linear", style = "fade" })
-- hl.animation({ leaf = "fadeLayersIn", enabled = true, speed = 1.79, bezier = "almostLinear" })
-- hl.animation({ leaf = "fadeLayersOut", enabled = true, speed = 1.39, bezier = "almostLinear" })
-- hl.animation({ leaf = "workspaces", enabled = false })
-- hl.animation({ leaf = "specialWorkspace", enabled = true, speed = 3, bezier = "easeOutQuint", style = "slidevert" })

-- Omarchy ships workspaces disabled, so a 3-finger swipe cut between workspaces with
-- nothing on screen showing the direction. "slide" makes the outgoing and incoming
-- workspace travel horizontally, which is the motion the swipe already describes.
-- speed is in deciseconds, and higher is faster: 6 is ~250ms, quick enough to keep up
-- with the fingers while still showing which way the workspaces travelled.
hl.animation({ leaf = "workspaces", enabled = true, speed = 6, bezier = "easeOutQuint", style = "slide" })

-- dwindle -------------------------------------------------------------------

-- hl.config({
--   dwindle = {
--     preserve_split = true,
--     force_split = 2,
--   },
-- })

-- scrolling -----------------------------------------------------------------

-- hl.config({
--   scrolling = {
--     column_width = 0.49,
--   },
-- })

-- master --------------------------------------------------------------------

-- hl.config({
--   master = {
--     new_status = "master",
--   },
-- })

-- misc ----------------------------------------------------------------------

-- hl.config({
--   misc = {
--     disable_hyprland_logo = true,
--     disable_splash_rendering = true,
--     disable_scale_notification = true,
--     focus_on_activate = true,
--     anr_missed_pings = 3,
--     on_focus_under_fullscreen = 1,
--     initial_workspace_tracking = 0,
--     -- Let a fresh shell re-acquire the session lock after the lock client died, so
--     -- omarchy-restart-shell can recover the LOCK failsafe.
--     allow_session_lock_restore = true,
--   },
-- })

-- cursor --------------------------------------------------------------------

-- hl.config({
--   cursor = {
--     hide_on_key_press = true,
--     warp_on_change_workspace = 1,
--   },
-- })

-- binds ---------------------------------------------------------------------

-- hl.config({
--   binds = {
--     hide_special_on_workspace_change = true,
--   },
-- })

-- cursor size (default/hypr/envs.lua) ---------------------------------------

-- hl.env("XCURSOR_SIZE", "24")
-- hl.env("HYPRCURSOR_SIZE", "24")

-- Examples from Omarchy's template ------------------------------------------
-- Suggestions shipped in Omarchy's user template (config/hypr/looknfeel.lua), not defaults.

-- https://wiki.hypr.land/Configuring/Basics/Variables/#general
-- hl.config({
--   general = {
--     -- No gaps between windows or borders.
--     gaps_in = 0,
--     gaps_out = 0,
--     border_size = 0,
--
--     -- Change to niri-like side-scrolling layout.
--     layout = "scrolling",
--   },
-- })

-- https://wiki.hypr.land/Configuring/Basics/Variables/#decoration
-- hl.config({
--   decoration = {
--     -- Use round window corners.
--     rounding = 8,
--
--     -- Dim unfocused windows (0.0 = no dim, 1.0 = fully dimmed).
--     dim_inactive = true,
--     dim_strength = 0.15,
--   },
-- })

-- https://wiki.hypr.land/Configuring/Basics/Variables/#animations
-- hl.config({
--   animations = {
--     -- Disable all animations.
--     enabled = false,
--   },
-- })

-- https://wiki.hypr.land/Configuring/Basics/Variables/#layout
-- hl.config({
--   layout = {
--     -- Avoid overly wide single-window layouts on wide screens.
--     single_window_aspect_ratio = { 1, 1 },
--   },
-- })

-- https://wiki.hypr.land/Configuring/Layouts/Scrolling-Layout/
-- hl.config({
--   scrolling = {
--     -- See only one column per screen instead of two.
--     column_width = 0.97,
--   },
-- })
