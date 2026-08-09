#!/usr/bin/env python3
"""Power monitor sparklines for Waybar.

Runs a single process that writes multiple named-pipe outputs for separate
Waybar modules. Each module gets its own sparkline graph.

Usage: power-monitor.py <metric>
  metric: voltage | cpu | gpu | power

Each outputs JSON lines for a Waybar custom module.
"""
import json
import subprocess
import signal
import sys
import time
from collections import deque
from pathlib import Path

INTERVAL = 2
HISTORY = 20
SPARKS = "▁▂▃▄▅▆▇█"
PAD = "▁" * HISTORY  # padding for consistent width before history fills

BAT_PATH = Path("/sys/class/power_supply/BAT0")


def spark(values, vmin, vmax):
    if not values:
        return PAD
    rng = vmax - vmin
    if rng <= 0:
        return SPARKS[0] * HISTORY
    out = []
    for v in values:
        idx = int((v - vmin) / rng * (len(SPARKS) - 1))
        idx = max(0, min(len(SPARKS) - 1, idx))
        out.append(SPARKS[idx])
    # Pad left to fixed width
    return PAD[:HISTORY - len(out)] + "".join(out)


def read_sysfs(path):
    try:
        return float(Path(path).read_text().strip())
    except Exception:
        return None


def get_voltage():
    v = read_sysfs(BAT_PATH / "voltage_now")
    return v / 1e6 if v is not None else None


def get_energy_rate():
    v = read_sysfs(BAT_PATH / "power_now")
    if v is not None:
        return v / 1e6
    try:
        out = subprocess.check_output(
            ["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT0"],
            stderr=subprocess.DEVNULL, text=True, timeout=3
        )
        for line in out.splitlines():
            if "energy-rate" in line:
                return float(line.split(":")[1].strip().split()[0])
    except Exception:
        pass
    return None


def get_cpu():
    try:
        with open("/proc/stat") as f:
            parts = f.readline().split()
        total = sum(int(x) for x in parts[1:])
        idle = int(parts[4]) + int(parts[5])
        return total, idle
    except Exception:
        return None, None


def get_gpu_power():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL, text=True, timeout=3
        )
        return float(out.strip())
    except Exception:
        return None


def emit(text, tooltip, css_class=""):
    print(json.dumps({"text": text, "tooltip": tooltip, "class": css_class}), flush=True)


def run_voltage():
    hist = deque(maxlen=HISTORY)
    while True:
        v = get_voltage()
        if v is not None:
            hist.append(v)
        graph = spark(list(hist), 10.0, 13.0)
        now = f"{v:.2f}" if v else "?"
        css = ""
        if v is not None and v < 10.5:
            css = "critical"
        elif v is not None and v < 11.0:
            css = "warning"
        emit(f"⚡{now}V {graph}", f"Battery voltage: {now}V\nMin design: 11.58V\n{HISTORY} samples, {INTERVAL}s each", css)
        time.sleep(INTERVAL)


def run_cpu():
    hist = deque(maxlen=HISTORY)
    prev_total, prev_idle = get_cpu()
    while True:
        cur_total, cur_idle = get_cpu()
        if prev_total is not None and cur_total is not None:
            dt = cur_total - prev_total
            di = cur_idle - prev_idle
            pct = ((dt - di) / dt * 100) if dt > 0 else 0
            hist.append(pct)
        prev_total, prev_idle = cur_total, cur_idle
        graph = spark(list(hist), 0, 100)
        now = f"{pct:.0f}" if hist else "?"
        css = ""
        if hist and hist[-1] > 90:
            css = "critical"
        elif hist and hist[-1] > 70:
            css = "warning"
        emit(f"󰍛 {now:>3s}% {graph}", f"CPU usage: {now}%\n{HISTORY} samples, {INTERVAL}s each", css)
        time.sleep(INTERVAL)


def run_gpu():
    hist = deque(maxlen=HISTORY)
    while True:
        w = get_gpu_power()
        if w is not None:
            hist.append(w)
        graph = spark(list(hist), 0, 60)
        now = f"{w:.0f}" if w is not None else "?"
        css = ""
        if w is not None and w > 45:
            css = "critical"
        elif w is not None and w > 25:
            css = "warning"
        emit(f"󰢮 {now:>2s}W {graph}", f"GPU power draw: {now}W\nDefault limit: 60W\n{HISTORY} samples, {INTERVAL}s each", css)
        time.sleep(INTERVAL)


def run_power():
    hist = deque(maxlen=HISTORY)
    while True:
        w = get_energy_rate()
        if w is not None:
            hist.append(w)
        graph = spark(list(hist), 0, 60)
        now = f"{w:.0f}" if w is not None else "?"
        css = ""
        if w is not None and w > 40:
            css = "critical"
        elif w is not None and w > 25:
            css = "warning"
        emit(f"⚡{now:>2s}W {graph}", f"Total system draw: {now}W\n{HISTORY} samples, {INTERVAL}s each", css)
        time.sleep(INTERVAL)


def main():
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

    if len(sys.argv) < 2:
        print("Usage: power-monitor.py <voltage|cpu|gpu|power>", file=sys.stderr)
        sys.exit(1)

    metric = sys.argv[1]
    runners = {
        "voltage": run_voltage,
        "cpu": run_cpu,
        "gpu": run_gpu,
        "power": run_power,
    }
    if metric not in runners:
        print(f"Unknown metric: {metric}", file=sys.stderr)
        sys.exit(1)
    runners[metric]()


if __name__ == "__main__":
    main()
