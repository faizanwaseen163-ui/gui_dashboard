"""
start.py
--------
System Pulse — launch everything in the background with ONE command.

Usage:
    python start.py       # start
    python stop.py        # stop
"""

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = "/tmp/systempulse.log"
PID_FILE = "/tmp/systempulse.pid"


def kill_port(port):
    """Kill any process listening on the given TCP port."""
    try:
        subprocess.run(
            ["fuser", "-k", f"{port}/tcp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
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


def activate_conda_env():
    """Best-effort: find conda and set the env's python for this script."""
    for base in [
        os.path.expanduser("~/miniconda3"),
        os.path.expanduser("~/anaconda3"),
        "/opt/conda",
        os.path.expanduser("~/miniforge3"),
    ]:
        env_py = os.path.join(base, "envs", "gui-dashboard", "bin", "python")
        if os.path.exists(env_py):
            return env_py
    return sys.executable


def is_running():
    if not os.path.exists(PID_FILE):
        return False
    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def main():
    os.chdir(HERE)

    if is_running():
        print("  ℹ  System Pulse is already running.")
        print("     Open:  http://localhost:3000")
        print("     Stop:  python stop.py")
        return

    print("  Cleaning up old processes on ports 3000, 3002...")
    kill_port(3000)
    kill_port(3002)
    time.sleep(0.6)

    python_bin = activate_conda_env()
    print(f"  Using Python: {python_bin}")

    api_path = os.path.join(HERE, "api_server.py")
    if not os.path.exists(api_path):
        print("  [error] api_server.py not found in this folder.")
        sys.exit(1)

    with open(LOG, "wb") as log:
        proc = subprocess.Popen(
            [python_bin, api_path],
            cwd=HERE,
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))

    time.sleep(3.5)

    try:
        with open(LOG, "r") as f:
            print(f.read())
    except Exception:
        pass

    print(f"  ✅  System Pulse is running in the background (PID {proc.pid}).")
    print(f"      Log file  :  {LOG}")
    print(f"      Stop with :  python stop.py")
    print()


if __name__ == "__main__":
    main()