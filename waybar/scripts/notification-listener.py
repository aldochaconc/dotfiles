#!/usr/bin/env python3
"""Notification widget for Waybar.

Shows notifications in a compact format. Empty when idle.

Features:
- Typewriter effect on new notifications
- Queue with (+n) counter
- 4 blinks before auto-dismiss
- Click: dismiss current, show next. Right-click: dismiss all.
- SIGUSR1: dismiss current / SIGUSR2: dismiss all
"""
import json
import queue
import re
import signal
import subprocess
import sys
import threading
import time
from html import escape as esc

TIMEOUT = 4
TYPE_DELAY = 0.015
MAX_LENGTH = 60

DOT_COLORS = {"low": "#9ea1a7", "normal": "#8bae79", "critical": "#E46876"}

notif_queue = queue.Queue()
interrupt = threading.Event()
clear_all = threading.Event()
output_lock = threading.Lock()


def emit(text="", tooltip="", css_class="empty"):
    with output_lock:
        print(json.dumps({"text": text, "tooltip": tooltip, "class": css_class}), flush=True)


def truncate_body(summary, body):
    if not body:
        return ""
    if 2 + len(summary) + 2 + len(body) > MAX_LENGTH:
        avail = MAX_LENGTH - 2 - len(summary) - 3
        return body[:avail] + "\u2026" if avail > 0 else ""
    return body


def build_markup(summary, body, dot_color, pending, typed=None):
    full = summary + ("  " + body if body else "")
    # Right-to-left reveal: show last `typed` chars (dot stays static)
    if typed is not None:
        shown = full[len(full) - typed:]
    else:
        shown = full

    parts = []
    if pending > 0:
        parts.append(f"<span foreground='{dot_color}'>(+{pending})</span>  ")

    parts.append(f"<span foreground='{dot_color}'><b>\u25cf</b></span>  ")

    if len(shown) <= len(summary) or typed is not None and typed < len(full):
        # During typing or partial reveal — no bold distinction
        parts.append(esc(shown))
    else:
        parts.append(f"<b>{esc(summary)}</b>{esc(shown[len(summary):])}")

    return "".join(parts)


def drain():
    while not notif_queue.empty():
        try:
            notif_queue.get_nowait()
        except queue.Empty:
            break


def finish():
    if clear_all.is_set():
        clear_all.clear()
        drain()
    if interrupt.is_set():
        interrupt.clear()
    if notif_queue.empty():
        emit()


def is_interrupted():
    return interrupt.is_set() or clear_all.is_set()


def display_loop():
    while True:
        try:
            notif = notif_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        if clear_all.is_set():
            finish()
            continue

        summary, body, urgency_class, timeout_s = notif
        dot_color = DOT_COLORS.get(urgency_class, "#9ea1a7")
        body = truncate_body(summary, body)
        full = summary + ("  " + body if body else "")
        tooltip = f"{summary}\n{body}".strip()

        # --- Typing effect ---
        typed_ok = True
        for i in range(1, len(full) + 1):
            if is_interrupted():
                typed_ok = False
                break
            emit(
                text=build_markup(summary, body, dot_color, notif_queue.qsize(), typed=i),
                tooltip=tooltip, css_class=urgency_class,
            )
            time.sleep(TYPE_DELAY)

        if not typed_ok:
            finish()
            continue

        emit(
            text=build_markup(summary, body, dot_color, notif_queue.qsize()),
            tooltip=tooltip, css_class=urgency_class,
        )

        # --- Hold period ---
        if timeout_s > 0:
            deadline = time.monotonic() + timeout_s
            prev = notif_queue.qsize()
            while time.monotonic() < deadline:
                if is_interrupted():
                    break
                cur = notif_queue.qsize()
                if cur != prev:
                    emit(
                        text=build_markup(summary, body, dot_color, cur),
                        tooltip=tooltip, css_class=urgency_class,
                    )
                    prev = cur
                time.sleep(0.1)
        else:
            prev = notif_queue.qsize()
            while not is_interrupted():
                cur = notif_queue.qsize()
                if cur != prev:
                    emit(
                        text=build_markup(summary, body, dot_color, cur),
                        tooltip=tooltip, css_class=urgency_class,
                    )
                    prev = cur
                time.sleep(0.1)

        finish()


# --- D-Bus notification monitor ---

def dbus_monitor():
    proc = subprocess.Popen(
        ["dbus-monitor", "--session",
         "interface='org.freedesktop.Notifications',member='Notify',type='method_call'"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
    )

    in_notify = False
    top_strings = []
    urgency = 1
    in_urgency = False

    for line in proc.stdout:
        line = line.rstrip()

        if "member=Notify" in line and "method call" in line:
            in_notify = True
            top_strings = []
            urgency = 1
            in_urgency = False
            continue

        if not in_notify:
            continue

        m = re.match(r'^   string "(.*)"$', line)
        if m:
            top_strings.append(m.group(1))
            continue

        if 'string "urgency"' in line:
            in_urgency = True
            continue

        if in_urgency:
            m_byte = re.search(r'byte (\d+)', line)
            if m_byte:
                urgency = int(m_byte.group(1))
            in_urgency = False
            continue

        m_t = re.match(r'^   int32 (-?\d+)', line)
        if m_t:
            summary = top_strings[2] if len(top_strings) > 2 else ""
            body = top_strings[3] if len(top_strings) > 3 else ""

            if summary or body:
                expire = int(m_t.group(1))
                uc = {0: "low", 1: "normal", 2: "critical"}.get(urgency, "normal")
                ts = expire / 1000 if expire > 0 else TIMEOUT
                if urgency == 2:
                    ts = 0
                notif_queue.put((summary, body, uc, ts))

            in_notify = False


# --- Signals ---

def handle_usr1(*_):
    interrupt.set()


def handle_usr2(*_):
    clear_all.set()
    interrupt.set()


def main():
    signal.signal(signal.SIGUSR1, handle_usr1)
    signal.signal(signal.SIGUSR2, handle_usr2)
    emit()

    threading.Thread(target=display_loop, daemon=True).start()
    dbus_monitor()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
