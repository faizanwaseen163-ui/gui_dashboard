"""
stop.py
-------
Stop System Pulse and free ports 3000 and 3002.
"""

import os
import subprocess

PID_FILE = "/tmp/systempulse.pid"


def kill_port(port):
    try:
        subprocess.run(["fuser", "-k", f"{port}/tcp"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        try:
            out = subprocess.check_output(
                ["lsof", "-t", f"-i:{port}"], stderr=subprocess.DEVNULL
            ).decode().split()
            for pid in out:
                subprocess.run(["kill", "-9", pid],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def main():
    print("  Stopping System Pulse...")

    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 15)
        except Exception:
            pass
        try:
            os.remove(PID_FILE)
        except Exception:
            pass

    kill_port(3000)
    kill_port(3002)

    for pat in ("api_server.py", "server.js"):
        subprocess.run(["pkill", "-f", pat],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("  ✅  Stopped.")


if __name__ == "__main__":
    main()