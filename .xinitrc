#!/bin/bash
[ -r /etc/X11/xinit/.Xmodmap ] && xmodmap /etc/X11/xinit/.Xmodmap
[ -r ~/.Xmodmap ] && xmodmap ~/.Xmodmap
[ -r ~/.Xresources ] && xrdb -merge ~/.Xresources
eval $(gnome-keyring-daemon --start --components=secrets,ssh,gpg,pkcs11)
export SSH_AUTH_SOCK
export SSH_AUTH_SOCK
export GPG_AGENT_INFO

exec dbus-run-session i3
exec i3
