"""
monitor.py
----------
Cross-platform system data collector (Windows / Linux / macOS).
Runs a background thread that continuously polls CPU, RAM and Disk
using psutil and keeps rolling histories for live charts.
"""

import platform
import threading
import time
from collections import deque

import psutil


def bytes_to_human(n):
    """Convert bytes to readable string."""
    if n is None:
        return "N/A"
    step = 1024.0
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(n) < step:
            return f"{n:.2f} {unit}"
        n /= step
    return f"{n:.2f} EB"


def seconds_to_uptime(boot_time):
    elapsed = max(0, time.time() - boot_time)
    days, rem = divmod(int(elapsed), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    if days:
        return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m"


class SystemMonitor:
    """Background thread that polls system stats."""

    def __init__(self, history_len=60):
        self.history_len = history_len
        self.cpu_history = deque([0.0] * history_len, maxlen=history_len)
        self.ram_history = deque([0.0] * history_len, maxlen=history_len)

        self._lock = threading.Lock()
        self._data = {}
        self._running = False
        self._thread = None

        # Prime cpu_percent so first reading is accurate
        psutil.cpu_percent(percpu=True)
        self._data = self._collect()

    def start(self, interval=1.0):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, args=(interval,), daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self, interval):
        while self._running:
            try:
                data = self._collect()
                with self._lock:
                    self._data = data
                    self.cpu_history.append(data["cpu"]["percent"])
                    self.ram_history.append(data["ram"]["percent"])
            except Exception:
                pass
            time.sleep(interval)

    def _collect(self):
        cpu_percent = psutil.cpu_percent(interval=None)
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        try:
            freq = psutil.cpu_freq()
            freq_cur = round(freq.current, 0) if freq else None
        except Exception:
            freq_cur = None

        vm = psutil.virtual_memory()
        try:
            sw = psutil.swap_memory()
        except Exception:
            sw = None

        disks = []
        for part in psutil.disk_partitions(all=False):
            if not part.mountpoint or "cdrom" in (part.opts or ""):
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except (PermissionError, FileNotFoundError, OSError):
                continue
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype or "N/A",
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            })

        total_disk = sum(d["total"] for d in disks)
        used_disk = sum(d["used"] for d in disks)
        free_disk = sum(d["free"] for d in disks)
        disk_percent = (used_disk / total_disk * 100) if total_disk else 0.0

        return {
            "cpu": {
                "percent": cpu_percent,
                "per_core": per_core,
                "cores_logical": psutil.cpu_count(logical=True) or 1,
                "cores_physical": psutil.cpu_count(logical=False) or 1,
                "freq": freq_cur,
            },
            "ram": {
                "total": vm.total,
                "used": vm.used,
                "available": vm.available,
                "percent": vm.percent,
                "swap_total": sw.total if sw else 0,
                "swap_used": sw.used if sw else 0,
                "swap_percent": sw.percent if sw else 0,
            },
            "disks": disks,
            "disk_totals": {
                "total": total_disk,
                "used": used_disk,
                "free": free_disk,
                "percent": disk_percent,
            },
            "boot_time": psutil.boot_time(),
            "process_count": len(psutil.pids()),
            "os": f"{platform.system()} {platform.release()}",
            "machine": platform.machine(),
            "node": platform.node(),
        }

    def get_data(self):
        with self._lock:
            return dict(self._data)

    def get_cpu_history(self):
        with self._lock:
            return list(self.cpu_history)

    def get_ram_history(self):
        with self._lock:
            return list(self.ram_history)