#!/usr/bin/env python3
"""Now-playing marquee for Waybar.

Uses playerctl -F to follow metadata changes in real-time.
Scrolls long text like a marquee/ticker with a configurable window.
Output: JSON lines for Waybar custom module.
"""
import json
import subprocess
import signal
import sys
import threading
import time

ICON = "󰝚"
MAX_DISPLAY = 36
SCROLL_SPEED = 0.3
SCROLL_PAD = 5
SCROLL_PAUSE = 3

output_lock = threading.Lock()
meta_lock = threading.Lock()
current_artist = ""
current_title = ""
current_album = ""
current_player = ""
current_status = ""
shutdown = threading.Event()


def emit(text="", tooltip="", css_class="stopped"):
    with output_lock:
        print(json.dumps({"text": text, "tooltip": tooltip, "class": css_class}), flush=True)


def build_display_text():
    with meta_lock:
        artist = current_artist
        title = current_title
        status = current_status
    if not title or status == "Stopped":
        return "", "", "stopped"
    if artist:
        text = f"{artist} — {title}"
    else:
        text = title
    full = f"{ICON}  {text}"
    css = "Playing" if status == "Playing" else "Paused"
    return text, full, css


def scroll_loop():
    """Continuously scroll the current track text."""
    prev_text = None
    offset = 0
    pause_until = 0

    while not shutdown.is_set():
        text, full, css = build_display_text()

        if not text:
            emit()
            prev_text = None
            offset = 0
            shutdown.wait(1)
            continue

        with meta_lock:
            artist = current_artist
            title = current_title
            album = current_album
            player = current_player

        tooltip = f"{player}: {artist} — {title}"
        if album:
            tooltip += f"\n{album}"

        # Reset scroll on track change
        if text != prev_text:
            prev_text = text
            offset = 0
            pause_until = time.monotonic() + SCROLL_PAUSE

        if len(full) <= MAX_DISPLAY:
            emit(text=full, tooltip=tooltip, css_class=css)
            shutdown.wait(1)
            continue

        # Scrolling marquee
        padded = text + " · " * SCROLL_PAD + text
        now = time.monotonic()
        if now < pause_until:
            window = text[:MAX_DISPLAY - len(ICON) - 2]
            emit(text=f"{ICON}  {window}", tooltip=tooltip, css_class=css)
            shutdown.wait(SCROLL_SPEED)
            continue

        window_size = MAX_DISPLAY - len(ICON) - 2
        window = padded[offset:offset + window_size]
        emit(text=f"{ICON}  {window}", tooltip=tooltip, css_class=css)

        offset += 1
        cycle_len = len(text) + len(" · " * SCROLL_PAD)
        if offset >= cycle_len:
            offset = 0
            pause_until = time.monotonic() + SCROLL_PAUSE

        shutdown.wait(SCROLL_SPEED)


def metadata_listener():
    """Follow playerctl metadata changes."""
    global current_artist, current_title, current_album, current_player, current_status

    while not shutdown.is_set():
        try:
            proc = subprocess.Popen(
                [
                    "playerctl", "-p", "spotify", "metadata", "--format",
                    "{{playerName}}\t{{status}}\t{{artist}}\t{{title}}\t{{album}}",
                    "-F",
                ],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            )
            for line in proc.stdout:
                if shutdown.is_set():
                    break
                parts = line.strip().split("\t", 4)
                if len(parts) >= 4:
                    with meta_lock:
                        current_player = parts[0]
                        current_status = parts[1]
                        current_artist = parts[2]
                        current_title = parts[3]
                        current_album = parts[4] if len(parts) > 4 else ""
            proc.wait()
        except Exception:
            pass
        if not shutdown.is_set():
            with meta_lock:
                current_status = "Stopped"
            time.sleep(2)


def handle_signal(*_):
    shutdown.set()
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    threading.Thread(target=metadata_listener, daemon=True).start()
    # Give playerctl a moment to emit initial data
    time.sleep(0.3)
    scroll_loop()


if __name__ == "__main__":
    main()
