#!/bin/bash

systemctl --user import-environment DISPLAY XAUTHORITY
dbus-update-activation-environment --systemd DBUS_SESSION_BUS_ADDRESS DISPLAY XAUTHORITY

# --- Core X Customizations ---
[ -r /etc/X11/xinit/.Xmodmap ] && xmodmap /etc/X11/xinit/.Xmodmap
[ -r ~/.Xmodmap ] && xmodmap ~/.Xmodmap
[ -r ~/.Xresources ] && xrdb -merge ~/.Xresources

export XDG_CACHE_HOME="$HOME/.cache"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_DATA_DIRS="/usr/share:/usr/local/share"

export XDG_SESSION_TYPE="x11"
export XDG_CURRENT_DESKTOP="i3"
export DESKTOP_SESSION="i3"
export GDK_BACKEND="x11"

export QT_AUTO_SCREEN_SCALE_FACTOR=0
export QT_QPA_PLATFORMTHEME="qt5ct"

export EDITOR="$(if [[ -n $DISPLAY ]]; then echo 'vim'; else echo 'nvim'; fi)" 

eval $(gnome-keyring-daemon --start --components=secrets,ssh,gpg,pkcs11)

/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &

batsignal -b &
libinput-gestures &

if [ -d /etc/X11/xinit/xinitrc.d ] ; then
    for f in /etc/X11/xinit/xinitrc.d/?*.sh ; do
        [ -x "$f" ] && . "$f"
    done
    unset f
fi


exec i3
