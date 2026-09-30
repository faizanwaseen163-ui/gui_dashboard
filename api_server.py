"""
api_server.py
-------------
ONE command launches everything:
  - Python HTTP API on port 3002 (in a thread)
  - Node.js web server on port 3000 (as subprocess)
  - Auto-detects your LAN IP
  - Prints a scannable QR code for mobile
"""

import atexit
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from monitor import SystemMonitor, bytes_to_human, seconds_to_uptime

PORT_API = 3002
PORT_WEB = 3000
HERE = os.path.dirname(os.path.abspath(__file__))

MONITOR = SystemMonitor(history_len=60)
MONITOR.start(interval=1.0)

_node_proc = None
_py_server = None


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def build_snapshot():
    data = MONITOR.get_data()
    if not data:
        return {}
    cpu = data["cpu"]
    ram = data["ram"]
    dtot = data["disk_totals"]

    disks = [{
        "device": d["device"],
        "mountpoint": d["mountpoint"],
        "fstype": d["fstype"],
        "total": d["total"],
        "total_h": bytes_to_human(d["total"]),
        "used": d["used"],
        "used_h": bytes_to_human(d["used"]),
        "free": d["free"],
        "free_h": bytes_to_human(d["free"]),
        "percent": d["percent"],
    } for d in data["disks"]]

    return {
        "cpu": {
            "percent": cpu["percent"],
            "per_core": cpu["per_core"],
            "cores_logical": cpu["cores_logical"],
            "cores_physical": cpu["cores_physical"],
            "freq": cpu["freq"],
            "history": MONITOR.get_cpu_history(),
        },
        "ram": {
            "total": ram["total"],
            "total_h": bytes_to_human(ram["total"]),
            "used": ram["used"],
            "used_h": bytes_to_human(ram["used"]),
            "available": ram["available"],
            "available_h": bytes_to_human(ram["available"]),
            "percent": ram["percent"],
            "swap_total": ram["swap_total"],
            "swap_total_h": bytes_to_human(ram["swap_total"]),
            "swap_used": ram["swap_used"],
            "swap_used_h": bytes_to_human(ram["swap_used"]),
            "swap_percent": ram["swap_percent"],
            "history": MONITOR.get_ram_history(),
        },
        "disks": disks,
        "disk_totals": {
            "total": dtot["total"],
            "total_h": bytes_to_human(dtot["total"]),
            "used": dtot["used"],
            "used_h": bytes_to_human(dtot["used"]),
            "free": dtot["free"],
            "free_h": bytes_to_human(dtot["free"]),
            "percent": dtot["percent"],
        },
        "boot_time": data["boot_time"],
        "uptime": seconds_to_uptime(data["boot_time"]),
        "process_count": data["process_count"],
        "os": data["os"],
        "machine": data["machine"],
        "node": data["node"],
        "timestamp": time.time(),
    }


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/stream"):
            self._stream_sse()
        elif self.path.startswith("/api"):
            self._json()
        else:
            self.send_response(404)
            self._cors()
            self.end_headers()
            self.wfile.write(b'{"error":"not found"}')

    def _json(self):
        body = json.dumps(build_snapshot()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _stream_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._cors()
        self.end_headers()
        try:
            while True:
                payload = f"data: {json.dumps(build_snapshot())}\n\n"
                self.wfile.write(payload.encode())
                self.wfile.flush()
                time.sleep(1.0)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, fmt, *args):
        pass


def start_python_api():
    global _py_server
    _py_server = ThreadingHTTPServer(("0.0.0.0", PORT_API), Handler)
    threading.Thread(target=_py_server.serve_forever, daemon=True).start()


def start_node_server():
    global _node_proc
    if not os.path.exists(os.path.join(HERE, "server.js")):
        print("  [error] server.js not found!")
        return
    try:
        _node_proc = subprocess.Popen(
            ["node", "server.js"],
            cwd=HERE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print("  [error] Node.js not installed. Run: sudo apt install nodejs npm")


def print_banner():
    ip = get_local_ip()
    local = f"http://localhost:{PORT_WEB}"
    network = f"http://{ip}:{PORT_WEB}"

    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║       ⚡  System Pulse  —  Live Dashboard         ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print()
    print(f"   🖥  Local    :  {local}")
    print(f"   📱  Network  :  {network}")
    print()
    print("   Scan this QR with your phone (same WiFi):")
    print()

    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(network)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except ImportError:
        print("   [tip] pip install qrcode  →  QR will show here next time")

    print()
    print("   Press  Ctrl + C  to stop everything.")
    print()


def cleanup(*_):
    print("\n  Shutting down System Pulse...")
    if _node_proc and _node_proc.poll() is None:
        try:
            _node_proc.terminate()
            _node_proc.wait(timeout=3)
        except Exception:
            try:
                _node_proc.kill()
            except Exception:
                pass
    if _py_server:
        try:
            _py_server.shutdown()
        except Exception:
            pass
    MONITOR.stop()
    print("  Stopped. Goodbye!\n")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    atexit.register(lambda: None)

    start_python_api()
    start_node_server()
    time.sleep(0.8)
    print_banner()

    try:
        while True:
            time.sleep(1)
            if _node_proc and _node_proc.poll() is not None:
                print("\n  [warn] Node server stopped unexpectedly.")
                cleanup()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()