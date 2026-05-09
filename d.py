#!/usr/bin/env python3
"""
╔═══════════════════════════════════════╗
║   PRIVATE CLOUD DASHBOARD  v2.1       ║
║   Raspberry Pi · Home Lab Monitor     ║
╚═══════════════════════════════════════╝

Usage  : python3 dashboard.py
Requires: Python 3.7+  (stdlib only — no pip needed)
Exit   : Ctrl+C
"""

import os
import sys
import time
import signal
import socket
import subprocess
import io
from datetime import datetime
from pathlib import Path


# ══════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════
REFRESH_INTERVAL = 1          # seconds between redraws
HOSTNAME_LABEL   = None       # None = auto-detect

# Storage: each entry is  label → mount point
# Flash = system SD card at /
# SSD   = NAS drive at /mnt/hdd
DISK_MOUNTS = {
    "Flash": "/",
    "SSD  ": "/mnt/hdd",
}

# SSD block device used for temperature reading via smartctl
SSD_DEVICE = "/dev/sda"

# Network interfaces
IFACE_WIFI = "wlan0"
IFACE_LAN  = "eth0"

# Services to check (label → systemd unit name)
SERVICES = {
    "Samba    ": "smbd",
    "Tailscale": "tailscaled",
    "Ollama   ": "ollama",
}


# ══════════════════════════════════════════════════════
#  ANSI PALETTE
# ══════════════════════════════════════════════════════
class A:
    R        = "\033[0m"
    DIM      = "\033[2m"
    BOLD     = "\033[1m"
    WHITE    = "\033[97m"
    GREY     = "\033[38;5;245m"
    CYAN     = "\033[38;5;80m"
    GREEN    = "\033[38;5;114m"
    YELLOW   = "\033[38;5;221m"
    ORANGE   = "\033[38;5;208m"
    RED      = "\033[38;5;196m"
    ACCENT   = "\033[38;5;39m"


def S(text, *codes):
    return "".join(codes) + str(text) + A.R


# ══════════════════════════════════════════════════════
#  SCREEN PRIMITIVES
# ══════════════════════════════════════════════════════
def tsize():
    try:
        sz = os.get_terminal_size()
        return sz.columns, sz.lines
    except Exception:
        return 80, 24


def clear():
    sys.stdout.write("\033[2J\033[H")


def hide_cursor():
    sys.stdout.write("\033[?25l")


def show_cursor():
    sys.stdout.write("\033[?25h")


# ══════════════════════════════════════════════════════
#  DATA COLLECTION
# ══════════════════════════════════════════════════════
def _read(path, default=""):
    try:
        return Path(path).read_text().strip()
    except Exception:
        return default


def _run(cmd, default=""):
    try:
        return subprocess.check_output(
            cmd, shell=True, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return default


# ── CPU ──────────────────────────────────────────────
_prev_cpu = None

def cpu_percent():
    global _prev_cpu
    try:
        line  = Path("/proc/stat").read_text().splitlines()[0].split()
        vals  = list(map(int, line[1:]))
        idle  = vals[3]
        total = sum(vals)
        if _prev_cpu is None:
            _prev_cpu = (idle, total)
            return 0.0
        di = idle  - _prev_cpu[0]
        dt = total - _prev_cpu[1]
        _prev_cpu = (idle, total)
        return max(0.0, min(100.0, 100.0 * (1 - di / dt) if dt else 0.0))
    except Exception:
        return 0.0


def cpu_freq_mhz():
    raw = _read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq", "0")
    try:
        return int(raw) // 1000
    except ValueError:
        return 0


def cpu_temp():
    raw = _read("/sys/class/thermal/thermal_zone0/temp", "0")
    try:
        return float(raw) / 1000.0
    except ValueError:
        return 0.0


# ── RAM ──────────────────────────────────────────────
def ram_info():
    """Returns (used_mb, total_mb, percent)."""
    try:
        lines = Path("/proc/meminfo").read_text().splitlines()
        info  = {}
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                info[parts[0].rstrip(":")] = int(parts[1])
        total  = info.get("MemTotal", 0)
        free   = info.get("MemFree", 0)
        bufs   = info.get("Buffers", 0)
        cached = info.get("Cached", 0)
        sreclm = info.get("SReclaimable", 0)
        used   = total - free - bufs - cached - sreclm
        pct    = 100.0 * used / total if total else 0.0
        return used // 1024, total // 1024, pct
    except Exception:
        return 0, 0, 0.0


# ── DISK ─────────────────────────────────────────────
def disk_info(mount):
    """
    Returns (used_gb, total_gb, percent) for the given mount point,
    or None if the mount is unavailable / not mounted.
    """
    try:
        st    = os.statvfs(mount)
        total = st.f_frsize * st.f_blocks
        free  = st.f_frsize * st.f_bfree
        used  = total - free
        pct   = 100.0 * used / total if total else 0.0
        return used / 1e9, total / 1e9, pct
    except Exception:
        return None


# ── SSD TEMPERATURE ──────────────────────────────────
def ssd_temp(device=SSD_DEVICE):
    """
    Read SSD temperature from the given block device using smartctl.
    Returns a float (°C) on success, or None if unavailable.
    Tries the 'Temperature_Celsius' SMART attribute first, then
    the NVMe 'Temperature' line as a fallback.
    """
    # ATA / SATA drives
    raw = _run(
        f"smartctl -A {device} 2>/dev/null"
        r" | awk '/Temperature_Celsius/{ print $10; exit }'"
    )
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass

    # NVMe drives
    raw = _run(
        f"smartctl -A {device} 2>/dev/null"
        r" | awk '/^Temperature:/{print $2; exit}'"
    )
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass

    return None


# ── CPU TEMPERATURE ───────────────────────────────────
# (already collected via cpu_temp() — kept separate for clarity)


# ── NETWORK ──────────────────────────────────────────
def iface_ip(iface):
    raw = _run(f"ip -4 addr show {iface} 2>/dev/null | awk '/inet /{{print $2}}'")
    if raw:
        return raw.split("/")[0]
    return "—"


def tailscale_ip():
    raw = _run("tailscale ip -4 2>/dev/null")
    return raw if raw else "—"


# ── UPTIME ───────────────────────────────────────────
def uptime_str():
    try:
        secs  = float(Path("/proc/uptime").read_text().split()[0])
        days  = int(secs // 86400); secs %= 86400
        hours = int(secs // 3600);  secs %= 3600
        mins  = int(secs // 60)
        if days:
            return f"{days}d {hours:02d}h {mins:02d}m"
        return f"{hours:02d}h {mins:02d}m"
    except Exception:
        return "—"


# ── LOAD AVERAGE ─────────────────────────────────────
def load_avg():
    try:
        vals = Path("/proc/loadavg").read_text().split()
        return vals[0], vals[1], vals[2]
    except Exception:
        return "—", "—", "—"


# ── SERVICES ─────────────────────────────────────────
def service_active(unit):
    return _run(f"systemctl is-active {unit} 2>/dev/null") == "active"


# ── HOSTNAME ─────────────────────────────────────────
def hostname():
    if HOSTNAME_LABEL:
        return HOSTNAME_LABEL
    try:
        return socket.gethostname()
    except Exception:
        return "raspberry"


# ══════════════════════════════════════════════════════
#  SNAPSHOT  — all metrics collected once per cycle
# ══════════════════════════════════════════════════════
def snapshot():
    cpu  = cpu_percent()
    freq = cpu_freq_mhz()
    ct   = cpu_temp()
    rm, rt, rp = ram_info()
    l1, l5, l15 = load_avg()

    # Collect each configured disk mount independently
    disks = {label: disk_info(mount) for label, mount in DISK_MOUNTS.items()}

    # SSD temperature from the configured block device
    st = ssd_temp(SSD_DEVICE)

    ip_wifi = iface_ip(IFACE_WIFI)
    ip_lan  = iface_ip(IFACE_LAN)
    ip_ts   = tailscale_ip()

    services = {lbl: service_active(unit) for lbl, unit in SERVICES.items()}

    return {
        "cpu_pct":   cpu,
        "cpu_mhz":   freq,
        "cpu_temp":  ct,
        "ram_used":  rm,
        "ram_total": rt,
        "ram_pct":   rp,
        "load":      (l1, l5, l15),
        "disks":     disks,       # dict: label → (used_gb, total_gb, pct) | None
        "ssd_temp":  st,          # float °C or None
        "ip_wifi":   ip_wifi,
        "ip_lan":    ip_lan,
        "ip_ts":     ip_ts,
        "services":  services,
        "uptime":    uptime_str(),
        "hostname":  hostname(),
        "now":       datetime.now().strftime("%Y-%m-%d  %H:%M:%S"),
    }


# ══════════════════════════════════════════════════════
#  RENDER HELPERS
# ══════════════════════════════════════════════════════
BAR_FULL  = "█"
BAR_EMPTY = "░"


def bar(pct, width=20, warn=70, crit=90):
    filled = max(0, min(width, int(round(pct / 100 * width))))
    empty  = width - filled
    colour = A.RED if pct >= crit else (A.ORANGE if pct >= warn else A.CYAN)
    return S(BAR_FULL * filled, colour) + S(BAR_EMPTY * empty, A.GREY)


def temp_colour(t, warn=65, crit=80):
    if t >= crit:  return A.RED
    if t >= warn:  return A.ORANGE
    return A.GREEN


def pct_colour(p, warn=70, crit=90):
    if p >= crit:  return A.RED
    if p >= warn:  return A.ORANGE
    return A.WHITE


def section(title, width):
    pad = width - len(title) - 3
    return S("  " + title + " ", A.BOLD, A.ACCENT) + S("─" * max(pad, 0), A.DIM, A.GREY)


def status_pill(active):
    if active:
        return S(" ● ACTIVE ", A.GREEN, A.BOLD)
    return     S(" ○ OFFLINE", A.RED,   A.DIM)


def col_width(w):
    return (w - 4) // 2


# ══════════════════════════════════════════════════════
#  DRAW ROUTINES
# ══════════════════════════════════════════════════════
def draw_header(d, width):
    label = "  PRIVATE CLOUD  ·  "
    host  = d["hostname"].upper()
    right = d["now"] + "   up " + d["uptime"]
    gap   = width - 2 - len(label) - len(host) - len(right) - 3

    top = S("╔" + "═" * (width - 2) + "╗", A.DIM, A.GREY)
    mid = (
        S("║", A.DIM, A.GREY)
        + S(label, A.DIM, A.GREY)
        + S(host, A.BOLD, A.ACCENT)
        + S(" " * max(gap, 1), A.GREY)
        + S(d["now"], A.DIM, A.GREY)
        + S("   up ", A.DIM, A.GREY)
        + S(d["uptime"], A.GREY)
        + S("   ║", A.DIM, A.GREY)
    )
    bot = S("╚" + "═" * (width - 2) + "╝", A.DIM, A.GREY)

    print(top)
    print(mid)
    print(bot)


def draw_compute(d, width):
    cpu = d["cpu_pct"]
    ct  = d["cpu_temp"]
    rm, rt, rp = d["ram_used"], d["ram_total"], d["ram_pct"]
    l1, l5, l15 = d["load"]

    print()
    print(section("COMPUTE", width))
    print()

    # CPU row
    freq_str = f"{d['cpu_mhz']} MHz"
    print(
        f"  {S('CPU  ', A.GREY)}"
        f"{bar(cpu, width=24)}"
        f"  {S(f'{cpu:5.1f}%', pct_colour(cpu), A.BOLD)}"
        f"  {S(freq_str, A.GREY)}"
        f"   {S('temp', A.GREY)} {S(f'{ct:.1f}°C', temp_colour(ct), A.BOLD)}"
    )

    # RAM row
    print(
        f"  {S('RAM  ', A.GREY)}"
        f"{bar(rp, width=24)}"
        f"  {S(f'{rp:5.1f}%', pct_colour(rp), A.BOLD)}"
        f"  {S(f'{rm} / {rt} MB', A.GREY)}"
    )

    # Load average
    print()
    print(
        f"  {S('Load   ', A.GREY)}"
        f"{S(l1, A.WHITE)}  {S('5m', A.GREY)} {S(l5, A.WHITE)}"
        f"  {S('15m', A.GREY)} {S(l15, A.WHITE)}"
    )


def draw_storage(d, width):
    """
    Shows each configured disk mount exactly once, then CPU temp and SSD temp.
    Flash (/) and SSD (/mnt/hdd) come from DISK_MOUNTS — no duplication.
    """
    print()
    print(section("STORAGE", width))
    print()

    # ── Disk usage rows ───────────────────────────────
    for label, info in d["disks"].items():
        if info is None:
            # Mount point doesn't exist or isn't accessible
            print(f"  {S(f'{label}', A.GREY)}  {S('unavailable', A.DIM, A.GREY)}")
            continue

        used, total, pct = info
        print(
            f"  {S(label, A.GREY)}"
            f"  {bar(pct, width=22)}"
            f"  {S(f'{pct:5.1f}%', pct_colour(pct), A.BOLD)}"
            f"  {S(f'{used:.1f} / {total:.1f} GB', A.GREY)}"
        )

    # ── Temperature rows ─────────────────────────────
    print()

    # CPU temperature (always available on Pi)
    ct = d["cpu_temp"]
    print(
        f"  {S('CPU temp ', A.GREY)}"
        f" {S(f'{ct:.1f}°C', temp_colour(ct, warn=65, crit=80), A.BOLD)}"
    )

    # SSD temperature — show N/A if smartctl can't read it
    st = d["ssd_temp"]
    if st is not None:
        st_str = S(f"{st:.1f}°C", temp_colour(st, warn=45, crit=60), A.BOLD)
    else:
        st_str = S("N/A", A.DIM, A.GREY)

    print(
        f"  {S('SSD temp ', A.GREY)}"
        f" {st_str}"
    )


def draw_network(d, width):
    print()
    print(section("NETWORK", width))
    print()

    rows = [
        ("WiFi     ", d["ip_wifi"]),
        ("LAN      ", d["ip_lan"]),
        ("Tailscale", d["ip_ts"]),
    ]
    for label, ip in rows:
        avail  = ip != "—"
        dot    = S("●", A.GREEN if avail else A.RED)
        ip_col = A.CYAN if avail else A.GREY
        print(f"  {dot}  {S(label, A.GREY)}  {S(ip, ip_col, A.BOLD)}")


def draw_services(d, width):
    print()
    print(section("SERVICES", width))
    print()

    items = list(d["services"].items())
    half  = (len(items) + 1) // 2
    left  = items[:half]
    right = items[half:]
    cw    = col_width(width)

    for i in range(max(len(left), len(right))):
        row = "  "
        if i < len(left):
            lbl, active = left[i]
            row += S(lbl, A.GREY) + "  " + status_pill(active)
        else:
            row += " " * cw

        if i < len(right):
            lbl, active = right[i]
            gap = cw - 20
            row += " " * max(gap, 4) + S(lbl, A.GREY) + "  " + status_pill(active)

        print(row)


def draw_footer(width):
    print()
    print(S("─" * width, A.DIM, A.GREY))
    print(S("  q / Ctrl+C  exit    r  refresh now", A.DIM, A.GREY))


# ══════════════════════════════════════════════════════
#  FULL FRAME RENDER  (buffer → single write = no flicker)
# ══════════════════════════════════════════════════════
def render(d):
    width, _ = tsize()
    width    = min(width, 100)

    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf

    clear()
    draw_header(d, width)
    draw_compute(d, width)
    draw_storage(d, width)
    draw_network(d, width)
    draw_services(d, width)
    draw_footer(width)

    sys.stdout = old
    old.write(buf.getvalue())
    old.flush()


# ══════════════════════════════════════════════════════
#  MAIN LOOP
# ══════════════════════════════════════════════════════
def on_exit(sig, frame):
    show_cursor()
    w, _ = tsize()
    clear()
    print(S("  Dashboard closed.", A.GREEN, A.BOLD))
    print()
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, on_exit)
    signal.signal(signal.SIGTERM, on_exit)
    hide_cursor()

    # Warm-up tick so cpu_percent() has a baseline diff
    cpu_percent()
    time.sleep(0.2)

    while True:
        d = snapshot()
        render(d)
        time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    main()
