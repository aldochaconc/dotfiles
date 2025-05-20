#!/bin/bash

# --- Systemd User Session Integration ---
# Ensure DISPLAY and XAUTHORITY are available to systemd user services
systemctl --user import-environment DISPLAY XAUTHORITY
dbus-update-activation-environment --systemd DBUS_SESSION_BUS_ADDRESS DISPLAY XAUTHORITY
# Start the target that our user services (picom, dunst, etc.) depend on
# systemctl --user start graphical-session.target

# --- Core X Customizations ---
# Keyboard mapping
[ -r /etc/X11/xinit/.Xmodmap ] && xmodmap /etc/X11/xinit/.Xmodmap
[ -r ~/.Xmodmap ] && xmodmap ~/.Xmodmap
# X resources (for urxvt, etc.)
[ -r ~/.Xresources ] && xrdb -merge ~/.Xresources

# --- Environment Variables ---
# XDG Base Directory Specification
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
# XDG_DATA_DIRS: Standard paths for application data files.
export XDG_DATA_DIRS="/usr/share:/usr/local/share"

# Desktop Environment Specifics
export XDG_SESSION_TYPE="x11" # Explicitly set for clarity
export XDG_CURRENT_DESKTOP="i3"
export DESKTOP_SESSION="i3"
export GDK_BACKEND="x11" # Ensure GDK (GTK) apps use the X11 backend

# Qt Theming (if using qt5ct)
export QT_AUTO_SCREEN_SCALE_FACTOR=0
export QT_QPA_PLATFORMTHEME="qt5ct"

# Editor Preference
export EDITOR="$(if [[ -n $DISPLAY ]]; then echo 'vim'; else echo 'nvim'; fi)" # Or your preferred X11/CLI editors

# --- Session Services & Agents ---
# GNOME Keyring (for SSH, GPG, secrets)
eval $(gnome-keyring-daemon --start --components=secrets,ssh,gpg,pkcs11)

# Polkit (PolicyKit) Authentication Agent for GUI privilege escalation
/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &

# Automatic Screen Locking (Optional - requires 'xss-lock' package)
# xss-lock --transfer-sleep-lock -- i3lock -n --nofork &

# User Daemons
batsignal -b &
libinput-gestures &

# --- System-wide xinitrc.d scripts ---
# Source system-provided X session startup scripts
if [ -d /etc/X11/xinit/xinitrc.d ] ; then
    for f in /etc/X11/xinit/xinitrc.d/?*.sh ; do
        [ -x "$f" ] && . "$f"
    done
    unset f
fi

# --- D-Bus Session ---
# The systemd user session (graphical-session.target) should provide a D-Bus session.
# The 'systemctl --user import-environment' command should make DBUS_SESSION_BUS_ADDRESS available.
# The manual dbus-launch block below is likely redundant and can be removed.
# If issues arise, you might consider 'exec dbus-launch --exit-with-session i3' as the final line.

# [ -z "${XDG_RUNTIME_DIR}" ] && export XDG_RUNTIME_DIR=/run/user/$(id -ru)
# chmod 700 "$XDG_RUNTIME_DIR"
# export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u $USER)/bus"

# eval $(dbus-launch --sh-syntax)
# export DBUS_SESSION_BUS_ADDRESS
# export DBUS_SESSION_BUS_PID

# if [ -d "$XDG_RUNTIME_DIR/bus" ]; then
#    chmod 700 "$XDG_RUNTIME_DIR/bus"
# fi


# --- Execute Window Manager ---
# This should be the last command.
exec i3
