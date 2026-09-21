-- Every keybinding on this machine is defined in this file. Omarchy's own bindings are
-- switched off in hyprland.lua (omarchy_default_bindings = false): a key that is not
-- written here does nothing. Baseline: Omarchy 4.0.4-1.
--
-- View: omarchy menu keybindings --print   |   SUPER + SHIFT + SLASH

hl.config({ binds = { window_direction_monitor_fallback = true } })

-- Windows -------------------------------------------------------------------

-- close
o.bind("SUPER + W", "Close window", hl.dsp.window.close())
o.bind("CTRL + ALT + DELETE", "Close all windows", "omarchy-hyprland-window-close-all")

-- float and tile
o.bind("SUPER + T", "Toggle window floating/tiling", hl.dsp.window.float({ action = "toggle" }))
o.bind("SUPER + P", "Pseudo window", hl.dsp.window.pseudo())
o.bind("SUPER + O", "Pop window out (float & pin)", "omarchy-hyprland-window-pop")

-- fullscreen
o.bind("SUPER + F", "Full width", hl.dsp.window.fullscreen({ mode = "maximized" }))
o.bind("SUPER + CTRL + F", "Full screen", hl.dsp.window.fullscreen({ mode = "fullscreen" }))
o.bind("SUPER + ALT + F", "Tiled full screen", "omarchy-hyprland-window-tiled-fullscreen-toggle")

-- width
o.bind("SUPER + Home", "Restore window width", "omarchy-hyprland-window-width restore")
o.bind("SUPER + ALT + Home", "Save window width", "omarchy-hyprland-window-width save")

-- scratchpad
o.bind("SUPER + S", "Toggle scratchpad", hl.dsp.workspace.toggle_special("scratchpad"))
o.bind("SUPER + ALT + S", "Move window to scratchpad", hl.dsp.window.move({ workspace = "special:scratchpad", follow = false }))

-- mouse
o.bind("SUPER + mouse:272", "Move window", hl.dsp.window.drag(), { mouse = true })
o.bind("SUPER + mouse:273", "Resize window", hl.dsp.window.resize(), { mouse = true })

-- Focus ---------------------------------------------------------------------

-- by direction, hjkl
--
-- These go through hypr-focus-or-rotate, which falls through to the
-- neighbouring workspace when no window lies that way. Hyprland's movefocus
-- stops at the edge and has no option to carry the focus across
-- (hyprwm/Hyprland#11874), so the decision is made in the script: it moves the
-- focus, then compares the focused window before and after, and rotates only
-- when nothing moved.
--
-- All four rotate, up and down included, so the keys behave alike; the
-- animation slides horizontally whichever one crossed.
local focus_or_rotate = os.getenv("HOME") .. "/.local/bin/hypr-focus-or-rotate"
o.bind("SUPER + H", "Move window focus left", hl.dsp.exec_cmd(focus_or_rotate .. " l"))
o.bind("SUPER + J", "Move window focus down", hl.dsp.exec_cmd(focus_or_rotate .. " d"))
o.bind("SUPER + K", "Move window focus up", hl.dsp.exec_cmd(focus_or_rotate .. " u"))
o.bind("SUPER + L", "Move window focus right", hl.dsp.exec_cmd(focus_or_rotate .. " r"))

-- by direction, arrows. These keep Hyprland's movefocus, which stops at the
-- edge: the same four moves without the workspace crossing.
o.bind("SUPER + LEFT", "Focus on left window", hl.dsp.focus({ direction = "l" }))
o.bind("SUPER + RIGHT", "Focus on right window", hl.dsp.focus({ direction = "r" }))
o.bind("SUPER + UP", "Focus on above window", hl.dsp.focus({ direction = "u" }))
o.bind("SUPER + DOWN", "Focus on below window", hl.dsp.focus({ direction = "d" }))

-- cycle windows. Each key is bound twice on purpose: Hyprland runs both handlers in
-- order, so the window is raised after the focus moves.
o.bind("ALT + TAB", "Focus on next window", hl.dsp.window.cycle_next())
o.bind("ALT + TAB", "Reveal active window on top", hl.dsp.window.bring_to_top())
o.bind("ALT + SHIFT + TAB", "Focus on previous window", hl.dsp.window.cycle_next({ next = false }))
o.bind("ALT + SHIFT + TAB", "Reveal active window on top", hl.dsp.window.bring_to_top())

-- cycle monitors
o.bind("CTRL + ALT + TAB", "Focus on next monitor", hl.dsp.focus({ monitor = "+1" }))
o.bind("CTRL + ALT + SHIFT + TAB", "Focus on previous monitor", hl.dsp.focus({ monitor = "-1" }))

-- Move and swap -------------------------------------------------------------

-- move window, hjkl
o.bind("SUPER + CTRL + H", "Move window left", hl.dsp.window.move({ direction = "l" }))
o.bind("SUPER + CTRL + J", "Move window down", hl.dsp.window.move({ direction = "d" }))
o.bind("SUPER + CTRL + K", "Move window up", hl.dsp.window.move({ direction = "u" }))
o.bind("SUPER + CTRL + L", "Move window right", hl.dsp.window.move({ direction = "r" }))

-- move window, arrows
o.bind("SUPER + CTRL + LEFT", "Move window left", hl.dsp.window.move({ direction = "l" }))
o.bind("SUPER + CTRL + RIGHT", "Move window right", hl.dsp.window.move({ direction = "r" }))
o.bind("SUPER + CTRL + UP", "Move window up", hl.dsp.window.move({ direction = "u" }))
o.bind("SUPER + CTRL + DOWN", "Move window down", hl.dsp.window.move({ direction = "d" }))

-- swap window, arrows. SUPER + SHIFT + hjkl is not a second row for this: SHIFT is the
-- launcher modifier on this machine, and hjkl movement lives on SUPER + CTRL.
o.bind("SUPER + SHIFT + LEFT", "Swap window to the left", hl.dsp.window.swap({ direction = "l" }))
o.bind("SUPER + SHIFT + RIGHT", "Swap window to the right", hl.dsp.window.swap({ direction = "r" }))
o.bind("SUPER + SHIFT + UP", "Swap window up", hl.dsp.window.swap({ direction = "u" }))
o.bind("SUPER + SHIFT + DOWN", "Swap window down", hl.dsp.window.swap({ direction = "d" }))

-- move workspace to monitor
o.bind("SUPER + SHIFT + ALT + LEFT", "Move workspace to left monitor", hl.dsp.workspace.move({ monitor = "l" }))
o.bind("SUPER + SHIFT + ALT + RIGHT", "Move workspace to right monitor", hl.dsp.workspace.move({ monitor = "r" }))
o.bind("SUPER + SHIFT + ALT + UP", "Move workspace to up monitor", hl.dsp.workspace.move({ monitor = "u" }))
o.bind("SUPER + SHIFT + ALT + DOWN", "Move workspace to down monitor", hl.dsp.workspace.move({ monitor = "d" }))

-- Resize (code:20 = MINUS, code:21 = EQUAL) ---------------------------------

-- resizeactive changes the window's width and height, it does not move one edge: a
-- negative value shrinks, a positive one grows. MINUS shrinks and EQUAL grows, in both
-- axes. Step: SUPER alone 100px, ALT 25px, CTRL 300px.

-- width
o.bind("SUPER + code:20", "Narrower window", hl.dsp.window.resize({ x = -100, y = 0, relative = true }))
o.bind("SUPER + code:21", "Wider window", hl.dsp.window.resize({ x = 100, y = 0, relative = true }))
o.bind("SUPER + ALT + code:20", "Narrower window a little", hl.dsp.window.resize({ x = -25, y = 0, relative = true }))
o.bind("SUPER + ALT + code:21", "Wider window a little", hl.dsp.window.resize({ x = 25, y = 0, relative = true }))
o.bind("SUPER + CTRL + code:20", "Narrower window a lot", hl.dsp.window.resize({ x = -300, y = 0, relative = true }))
o.bind("SUPER + CTRL + code:21", "Wider window a lot", hl.dsp.window.resize({ x = 300, y = 0, relative = true }))

-- height: SHIFT switches the axis
o.bind("SUPER + SHIFT + code:20", "Shorter window", hl.dsp.window.resize({ x = 0, y = -100, relative = true }))
o.bind("SUPER + SHIFT + code:21", "Taller window", hl.dsp.window.resize({ x = 0, y = 100, relative = true }))
o.bind("SUPER + SHIFT + ALT + code:20", "Shorter window a little", hl.dsp.window.resize({ x = 0, y = -25, relative = true }))
o.bind("SUPER + SHIFT + ALT + code:21", "Taller window a little", hl.dsp.window.resize({ x = 0, y = 25, relative = true }))
o.bind("SUPER + CTRL + SHIFT + code:20", "Shorter window a lot", hl.dsp.window.resize({ x = 0, y = -300, relative = true }))
o.bind("SUPER + CTRL + SHIFT + code:21", "Taller window a lot", hl.dsp.window.resize({ x = 0, y = 300, relative = true }))

-- Groups --------------------------------------------------------------------

-- group and ungroup
o.bind("SUPER + G", "Toggle window grouping", hl.dsp.group.toggle())
o.bind("SUPER + ALT + G", "Move active window out of group", hl.dsp.window.move({ out_of_group = true }))

-- move window into a group
o.bind("SUPER + ALT + LEFT", "Move window to group on left", hl.dsp.window.move({ into_group = "l" }))
o.bind("SUPER + ALT + RIGHT", "Move window to group on right", hl.dsp.window.move({ into_group = "r" }))
o.bind("SUPER + ALT + UP", "Move window to group on top", hl.dsp.window.move({ into_group = "u" }))
o.bind("SUPER + ALT + DOWN", "Move window to group on bottom", hl.dsp.window.move({ into_group = "d" }))

-- cycle within the group, by key. Omarchy cycles groups on SUPER + ALT + TAB; this pair
-- duplicated it on a key Omarchy gives to "Former workspace", and the wheel and
-- SUPER + ALT + 1..5 below cover the same dispatchers. Freed for the layout toggle.
-- o.bind("SUPER + CTRL + TAB", "Next window in group", hl.dsp.group.next())
-- o.bind("SUPER + CTRL + SHIFT + TAB", "Previous window in group", hl.dsp.group.prev())
o.bind("SUPER + ALT + TAB", "Next window in group", hl.dsp.group.next())
o.bind("SUPER + ALT + SHIFT + TAB", "Previous window in group", hl.dsp.group.prev())

-- cycle within the group, by wheel
o.bind("SUPER + ALT + mouse_down", "Next window in group", hl.dsp.group.next())
o.bind("SUPER + ALT + mouse_up", "Previous window in group", hl.dsp.group.prev())

-- rotate windows by wheel, crossing into the neighbouring workspace at either end.
-- cyclenext wraps inside the workspace and never leaves it, so the traversal goes through
-- hypr-window-rotate, which orders windows by position rather than focus history.
local window_rotate = os.getenv("HOME") .. "/.local/bin/hypr-window-rotate"
o.bind("SUPER + mouse_down", "Next window", window_rotate .. " next")
o.bind("SUPER + mouse_up", "Previous window", window_rotate .. " prev")

-- jump to a window by index
for index = 1, 5 do
  o.bind("SUPER + ALT + code:" .. tostring(index + 9), "Switch to group window " .. index, hl.dsp.group.active({ index = index }))
end

-- Workspaces ----------------------------------------------------------------

-- switch and move to a numbered workspace
for workspace = 1, 10 do
  local key = "code:" .. tostring(workspace + 9)
  o.bind("SUPER + " .. key, "Switch to workspace " .. workspace, hl.dsp.focus({ workspace = tostring(workspace) }))
  o.bind("SUPER + SHIFT + " .. key, "Move window to workspace " .. workspace, hl.dsp.window.move({ workspace = tostring(workspace) }))
  o.bind("SUPER + SHIFT + ALT + " .. key, "Move window silently to workspace " .. workspace, hl.dsp.window.move({ workspace = tostring(workspace), follow = false }))
end

-- Rotation goes through hypr-workspace-rotate: Hyprland's selectors cannot express a
-- ceiling (r+1 creates without bound, e+1 wraps). The script creates and clamps to what
-- the bar shows: 1..5, plus higher workspaces while they hold windows.
local rotate = os.getenv("HOME") .. "/.local/bin/hypr-workspace-rotate"
-- rotate, by tab
o.bind("SUPER + TAB", "Next workspace", rotate .. " next")
o.bind("SUPER + SHIFT + TAB", "Previous workspace", rotate .. " prev")

-- rotate, by page keys
o.bind("SUPER + Prior", "Next workspace", rotate .. " next")
o.bind("SUPER + Next", "Previous workspace", rotate .. " prev")

-- The wheel rotates windows, not workspaces: see the Windows section. Workspace rotation
-- stays on TAB, the page keys, and the wheel over the bar's workspace widget.

-- layout. Cycles the active workspace between master, dwindle and scrolling, and saves the
-- choice to ~/.local/state/omarchy/workspace-layouts/<id>.lua, which
-- default/hypr/workspace-layouts.lua reloads at startup. A rule written there outranks
-- general.layout, so a workspace left on scrolling stays there across restarts.
--
-- master reserves a left area at master.mfact (0.55) and stacks the rest down the right.
-- dwindle splits each new window off the focused one, Fibonacci-style. scrolling gives every
-- window a full-height column of equal width at scrolling.column_width (0.49, two per screen)
-- and scrolls the rest off-screen rather than shrinking them.
--
-- hypr-workspace-layout-cycle rather than omarchy-hyprland-workspace-layout-toggle, which is
-- two-way: it sends anything that is not dwindle to dwindle, so master, the default layout
-- here, would be left on the first press with no key to return to it.
--
-- Omarchy binds this to SUPER + L, which is focus-right here.
o.bind("SUPER + CTRL + TAB", "Cycle workspace layout", os.getenv("HOME") .. "/.local/bin/hypr-workspace-layout-cycle")

-- Monitors ------------------------------------------------------------------

-- scaling
o.bind("SUPER + SLASH", "Monitor scaling up", "omarchy-hyprland-monitor-scaling up")
o.bind("SUPER + ALT + SLASH", "Monitor scaling down", "omarchy-hyprland-monitor-scaling down")

-- laptop display
o.bind("SUPER + CTRL + Delete", "Toggle laptop display", "omarchy-hyprland-monitor-internal toggle")
o.bind("SUPER + CTRL + ALT + Delete", "Toggle laptop display mirroring", "omarchy-hyprland-monitor-internal-mirror toggle")

-- lid
o.bind("switch:on:Lid Switch", nil, "omarchy-system-lid-close", { locked = true })
o.bind("switch:off:Lid Switch", nil, "omarchy-hyprland-monitor-clamshell", { locked = true })

-- Menus and bar -------------------------------------------------------------

-- root and apps
o.bind("SUPER + SPACE", "Omarchy menu", "omarchy-menu toggle")
o.bind("SUPER + SHIFT + code:201", "Omarchy menu", "omarchy-menu toggle root")
o.bind("SUPER + SEMICOLON", "Apps menu", "omarchy-menu toggle apps")
o.bind("SUPER + ALT + SPACE", "Apps menu", "omarchy-menu toggle apps")

-- system and power
o.bind("SUPER + ESCAPE", "System menu", "omarchy-menu toggle system")
o.bind("XF86PowerOff", "Power menu", "omarchy-menu toggle system", { locked = true })

-- by task
o.bind("SUPER + CTRL + C", "Capture menu", "omarchy-menu toggle capture")
o.bind("SUPER + CTRL + O", "Toggle menu", "omarchy-menu toggle toggle")
o.bind("SUPER + CTRL + S", "Share", "omarchy-menu toggle share")

-- appearance
o.bind("SUPER + CTRL + SPACE", "Background switcher", "omarchy-menu toggle background")
o.bind("SUPER + SHIFT + CTRL + SPACE", "Theme menu", "omarchy-menu toggle theme")

-- keybinding reference
o.bind("SUPER + SHIFT + SLASH", "Keybindings", "omarchy-menu-keybindings")
o.bind("SUPER + ALT + K", "Tmux keybindings", "omarchy-menu-tmux-keybindings")

-- bar
o.bind_toggle("SUPER + SHIFT + SPACE", "Toggle top bar", "bar")

-- bar panels, SUPER + CTRL + letter
o.bind("SUPER + CTRL + A", "Audio", "omarchy-shell shell toggle omarchy.audio")
o.bind("SUPER + CTRL + B", "Bluetooth", "omarchy-shell shell toggle omarchy.bluetooth")
o.bind("SUPER + CTRL + D", "Display", "omarchy-shell shell toggle omarchy.monitor")
o.bind("SUPER + CTRL + E", "Emojis", "omarchy-shell shell toggle omarchy.emojis")
o.bind("SUPER + CTRL + P", "Power", "omarchy-shell shell toggle omarchy.power")
o.bind("SUPER + CTRL + W", "Network", "omarchy-shell shell toggle omarchy.network")
o.bind("SUPER + CTRL + ALT + D", "Calendar", "omarchy-shell shell toggle omarchy.clock")
-- bar panels, by position: 1 is the leftmost panel in the bar's right section.
for panel = 1, 9 do
  o.bind("SUPER + CTRL + code:" .. tostring(panel + 9), "Bar panel " .. panel, "omarchy-shell -q shell togglePanelAt right " .. panel)
end

-- Notifications -------------------------------------------------------------

-- xkbcommon names the comma keysym "comma"; the upper-case "COMMA" does not match.
o.bind("SUPER + comma", "Dismiss last notification", "omarchy-shell notifications dismissOne")
o.bind("SUPER + SHIFT + comma", "Dismiss all notifications", "omarchy-shell notifications dismissAll")
o.bind_toggle("SUPER + CTRL + comma", "Toggle silencing notifications", "notification-silencing")
o.bind("SUPER + ALT + comma", "Invoke last notification", "omarchy-shell notifications invokeLast")
o.bind("SUPER + SHIFT + ALT + comma", "Open notification history", "omarchy-shell notifications showHistory")

-- Visual toggles ------------------------------------------------------------

-- window appearance
o.bind("SUPER + BACKSPACE", "Toggle window transparency", "omarchy-hyprland-window-transparency-toggle")
o.bind("SUPER + SHIFT + BACKSPACE", "Toggle window gaps", "omarchy-hyprland-window-gaps-toggle")
o.bind("SUPER + CTRL + BACKSPACE", "Toggle single-window square aspect", "omarchy-hyprland-window-single-square-aspect-toggle")

-- screen behaviour
o.bind_toggle("SUPER + CTRL + I", "Toggle locking on idle", "idle")
o.bind_toggle("SUPER + CTRL + N", "Toggle nightlight", "nightlight")

-- zoom
o.bind("SUPER + CTRL + Z", "Zoom in", function()
  local zoom = hl.get_config("cursor.zoom_factor") or 1
  hl.config({ cursor = { zoom_factor = zoom + 1 } })
end)
o.bind("SUPER + CTRL + ALT + Z", "Reset zoom", function()
  hl.config({ cursor = { zoom_factor = 1 } })
end)

-- Capture -------------------------------------------------------------------

-- print key
o.bind("PRINT", "Screenshot", "omarchy-capture-screenshot")
o.bind("ALT + PRINT", "Screenrecording", "omarchy-capture-screenrecording --stop-recording || omarchy-menu toggle trigger.capture.screenrecord")
o.bind("SUPER + PRINT", "Color picker", "pkill hyprpicker || hyprpicker -a")
o.bind("SUPER + CTRL + PRINT", "Extract text (OCR) from screenshot", "omarchy-capture-text")

-- webcam overlay (code:34 = BRACKETLEFT, code:35 = BRACKETRIGHT)
o.bind("SUPER + ALT + code:34", "Make webcam overlay smaller", "omarchy-capture-webcam-resize smaller")
o.bind("SUPER + ALT + code:35", "Make webcam overlay larger", "omarchy-capture-webcam-resize larger")

-- Keyboard control for the slurp region picker (see omarchy-capture-region). The binds
-- live exactly as long as a selection layer is on screen (slurp opens one per monitor).
-- Each handle is kept and removed individually so a same-key binding above survives.
local selection_layers = 0
local selection_binds = {}

hl.on("layer.opened", function(layer)
  if layer.namespace == "selection" then
    selection_layers = selection_layers + 1
    if selection_layers == 1 then
      selection_binds = {
        hl.bind("RETURN", hl.dsp.exec_cmd("omarchy-capture-region --take-window"), { description = "Capture highlighted window" }),
        hl.bind("CTRL + RETURN", hl.dsp.exec_cmd("omarchy-capture-region --take-fullscreen"), { description = "Capture entire screen" }),
        hl.bind("TAB", hl.dsp.exec_cmd("omarchy-capture-region --select-window next"), { description = "Select next window to capture" }),
        hl.bind("CTRL + TAB", hl.dsp.exec_cmd("omarchy-capture-region --select-window prev"), { description = "Select previous window to capture" }),
      }
      for _, direction in ipairs({ "left", "right", "up", "down" }) do
        table.insert(
          selection_binds,
          hl.bind(direction:upper(), hl.dsp.exec_cmd("omarchy-capture-region --select-window " .. direction), { description = "Select window to capture" })
        )
      end
    end
  end
end)

hl.on("layer.closed", function(layer)
  if layer.namespace == "selection" and selection_layers > 0 then
    selection_layers = selection_layers - 1
    if selection_layers == 0 then
      for _, keybind in ipairs(selection_binds) do
        keybind:unbind()
      end
      selection_binds = {}
    end
  end
end)

-- Utilities -----------------------------------------------------------------

-- session
o.bind("SUPER + CTRL + ESCAPE", "Lock system", "omarchy-system-lock")

-- reminders
o.bind("SUPER + CTRL + R", "Set reminder", "omarchy-menu toggle reminder-set")
o.bind("SUPER + CTRL + ALT + R", "Show reminders", "omarchy-reminder show")
o.bind("SUPER + SHIFT + CTRL + R", "Clear reminders", "omarchy-reminder clear")

-- status notifications
o.bind("SUPER + CTRL + ALT + B", "Show battery remaining", "omarchy-notification-battery")
o.bind("SUPER + CTRL + ALT + T", "Show time", "omarchy-notification-time")
o.bind("SUPER + CTRL + ALT + W", "Toggle weather", "omarchy-notification-weather")

-- Applications --------------------------------------------------------------

-- terminal
o.bind("SUPER + RETURN", "Terminal", { omarchy = "terminal" })

-- browser
o.bind("SUPER + SHIFT + RETURN", "Browser", { omarchy = "browser" })
o.bind("SUPER + SHIFT + B", "Browser", { omarchy = "browser" })
o.bind("SUPER + SHIFT + ALT + B", "Browser (private)", { omarchy = "browser --private" })

-- file manager. Thunar rather than Omarchy's nautilus: it has a native image preview side
-- pane (View > Side Pane > Image Preview), which Nautilus dropped upstream. There is no
-- `omarchy default file-manager`, so omarchy-launch-nautilus cannot be pointed elsewhere
-- and these name the app directly. thunar-cwd is in dot_local/bin.
o.bind("SUPER + SHIFT + F", "File manager", { launch = "thunar" })
o.bind("SUPER + ALT + SHIFT + F", "File manager (cwd)", "thunar-cwd")

-- editor
o.bind("SUPER + SHIFT + N", "Editor", { omarchy = "editor" })

-- tools that open a window. SUPER + CTRL elsewhere in this file changes the environment
-- (menus, toggles, window geometry); anything that puts a window on screen belongs here.
o.bind("SUPER + SHIFT + T", "Activity", { tui = "btop" })
o.bind("SUPER + SHIFT + C", "Calculator", "omacalc")
o.bind("XF86Calculator", "Calculator", "omacalc")
o.bind("SUPER + SHIFT + A", "Agent", "omarchy-agent --pick")
o.bind("SUPER + SHIFT + P", "Transcode", "omarchy-transcode")

-- vault. Obsidian is single instance: a second launch hands over to the running process and
-- exits, so a plain launch announces itself and no window appears. launch_sole focuses the
-- existing one instead. No workspace rule, so it opens wherever the focus already is.
--
-- The pattern is the full class, not the bare word: launch_sole matches title as well as
-- class, and any terminal whose title carries "obsidian" would be focused instead.
o.bind("SUPER + SHIFT + O", "Obsidian", o.launch_sole("md\\.obsidian\\.Obsidian", "obsidian"))

-- music. Starts Spotify the first time and focuses it afterwards, which pulls workspace 6
-- along (see the window rule in hyprland.lua). launch_sole matches on word boundaries, so
-- the pattern is bare: anchoring it with ^...$ would never match.
o.bind("SUPER + SHIFT + M", "Spotify", o.launch_sole("Spotify", "spotify"))

-- messaging. Both live in the scratchpad (see the window rules in hyprland.lua). The key
-- starts the app the first time and reveals the scratchpad on it afterwards; a window the
-- app opened somewhere else is pulled into the scratchpad first, so neither one ever ends
-- up covering the workspace in front. SUPER + S hides the scratchpad again.
local scratch = os.getenv("HOME") .. "/.local/bin/hypr-app-scratchpad"
o.bind("SUPER + SHIFT + W", "WhatsApp", scratch .. " '^chrome-web\\.whatsapp\\.com__-Default$' 'omarchy-launch-webapp https://web.whatsapp.com/'")
o.bind("SUPER + SHIFT + S", "Slack", scratch .. " '^slack$' 'uwsm-app -- /usr/bin/slack --gtk-version=3 -s'")

-- herdr. A singleton that follows the workspace in front rather than living on one: the key
-- brings the window to the focused workspace instead of switching the view to it. foot's
-- own class is plain "foot", shared with every other terminal here, so --app-id gives this
-- one a class of its own for the pattern to anchor on.
local here = os.getenv("HOME") .. "/.local/bin/hypr-app-here"
o.bind("SUPER + SHIFT + H", "herdr", here .. " '^herdr$' 'uwsm-app -- foot --app-id=herdr herdr'")

-- Clipboard -----------------------------------------------------------------

-- Send with explicit mods to the focused surface by omitting the window target, so the
-- universal shortcuts reach both normal windows and focused layer-shell surfaces such as
-- Omarchy panels. A virtual keyboard (wtype) won't do: the physically held SUPER merges
-- into the injected chord at the seat. The down/up split works around Hyprland
-- send_shortcut sometimes leaving synthetic key state stuck/repeating.
-- https://github.com/hyprwm/Hyprland/discussions/14099
local function send_shortcut_once(mods, key)
  return function()
    hl.dispatch(hl.dsp.send_key_state({ mods = mods, key = key, state = "down" }))

    hl.timer(function()
      hl.dispatch(hl.dsp.send_key_state({ mods = mods, key = key, state = "up" }))
    end, { timeout = 50, type = "oneshot" })
  end
end

-- Terminals carry the "terminal" tag from default/hypr/apps/terminals.lua. Dynamic tags
-- carry a trailing "*".
local function active_window_is_terminal()
  local window = hl.get_active_window()
  if not window then
    return false
  end

  for _, tag in ipairs(window.tags or {}) do
    if tag:gsub("%*$", "") == "terminal" then
      return true
    end
  end

  return false
end

local function universal_clipboard_shortcut(default_mods, default_key, terminal_mods, terminal_key)
  return function()
    if active_window_is_terminal() then
      send_shortcut_once(terminal_mods, terminal_key)()
    else
      send_shortcut_once(default_mods, default_key)()
    end
  end
end

-- copy, cut and paste
o.bind("SUPER + C", "Universal copy", universal_clipboard_shortcut("CTRL", "C", "CTRL", "Insert"))
o.bind("SUPER + V", "Universal paste", universal_clipboard_shortcut("CTRL", "V", "SHIFT", "Insert"))
o.bind("SUPER + X", "Universal cut", send_shortcut_once("CTRL", "X"))

-- history
o.bind("SUPER + CTRL + V", "Clipboard manager", "omarchy-shell shell toggle omarchy.clipboard")

-- Media keys ----------------------------------------------------------------

-- volume: ALT for 1% steps, SHIFT to switch output
o.bind("XF86AudioRaiseVolume", "Volume up", "omarchy-audio-output-volume raise", { locked = true, repeating = true })
o.bind("XF86AudioLowerVolume", "Volume down", "omarchy-audio-output-volume lower", { locked = true, repeating = true })
o.bind("ALT + XF86AudioRaiseVolume", "Volume up precise", "omarchy-audio-output-volume +1", { locked = true, repeating = true })
o.bind("ALT + XF86AudioLowerVolume", "Volume down precise", "omarchy-audio-output-volume -1", { locked = true, repeating = true })
o.bind("XF86AudioMute", "Mute", "omarchy-audio-output-volume mute-toggle", { locked = true })
o.bind("SHIFT + XF86AudioMute", "Switch audio output", "omarchy-audio-output-switch", { locked = true })
o.bind("XF86AudioMicMute", "Mute microphone", "omarchy-audio-input-mute", { locked = true })

-- display brightness: ALT for 1% steps, SHIFT for the extremes
o.bind("XF86MonBrightnessUp", "Brightness up", "omarchy-brightness-display +5%", { locked = true, repeating = true })
o.bind("XF86MonBrightnessDown", "Brightness down", "omarchy-brightness-display 5%-", { locked = true, repeating = true })
o.bind("ALT + XF86MonBrightnessUp", "Brightness up precise", "omarchy-brightness-display +1%", { locked = true, repeating = true })
o.bind("ALT + XF86MonBrightnessDown", "Brightness down precise", "omarchy-brightness-display 1%-", { locked = true, repeating = true })
o.bind("SHIFT + XF86MonBrightnessUp", "Brightness maximum", "omarchy-brightness-display 100%", { locked = true, repeating = true })
o.bind("SHIFT + XF86MonBrightnessDown", "Brightness minimum", "omarchy-brightness-display 1%", { locked = true, repeating = true })

-- keyboard backlight
o.bind("XF86KbdBrightnessUp", "Keyboard brightness up", "omarchy-brightness-keyboard up", { locked = true, repeating = true })
o.bind("XF86KbdBrightnessDown", "Keyboard brightness down", "omarchy-brightness-keyboard down", { locked = true, repeating = true })
o.bind("XF86KbdLightOnOff", "Keyboard backlight cycle", "omarchy-brightness-keyboard cycle", { locked = true })

-- touchpad
o.bind_toggle("XF86TouchpadToggle", "Toggle touchpad", "touchpad", { locked = true })
o.bind("XF86TouchpadOn", "Enable touchpad", "omarchy-toggle-touchpad on", { locked = true })
o.bind("XF86TouchpadOff", "Disable touchpad", "omarchy-toggle-touchpad off", { locked = true })

-- playback: ALT for track, SHIFT to switch source
o.bind("XF86AudioPlay", "Play", "omarchy-shell media playPause", { locked = true })
o.bind("XF86AudioPause", "Pause", "omarchy-shell media playPause", { locked = true })
o.bind("XF86AudioNext", "Next track", "omarchy-shell media next", { locked = true })
o.bind("XF86AudioPrev", "Previous track", "omarchy-shell media previous", { locked = true })
o.bind("ALT + XF86AudioPlay", "Next track", "omarchy-shell media next", { locked = true })
o.bind("ALT + SHIFT + XF86AudioPlay", "Previous track", "omarchy-shell media previous", { locked = true })
o.bind("SHIFT + XF86AudioPlay", "Switch media source", "omarchy-audio-source-switch", { locked = true })
o.bind("SHIFT + XF86AudioPause", "Switch media source", "omarchy-audio-source-switch", { locked = true })

-- eject
o.bind("XF86Eject", "Eject media", "eject", { locked = true })
