# ⚡ System Pulse — Live System Monitor Dashboard

A real-time, cross-platform system monitoring dashboard that runs in your
browser. It streams live CPU, RAM, and storage statistics from your machine
and renders them as an interactive, animated web dashboard.

Access it from your laptop, phone, or any device on the same WiFi network —
instantly, with a built-in QR code.

---

## 📸 Overview

System Pulse runs quietly in the background and serves a beautiful dark-themed
dashboard with:

- Live CPU usage (overall + per-core)
- Live RAM and swap memory usage
- Storage breakdown for every mounted disk
- Smooth animated rings, bars, and charts
- Real-time updates every second (Server-Sent Events)
- One-tap phone access via built-in QR code
- Refresh button and keyboard shortcuts

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| Real-time data | Updated every 1 second via SSE |
| Cross-platform | Works on Linux, macOS, and Windows |
| Web-based UI | No install needed on client — just a browser |
| Mobile-ready | Scan the QR code from your phone |
| Keyboard shortcuts | `1–4` switch tabs, `↑` `↓` navigate, `R` refresh |
| Animated charts | Powered by Chart.js with smooth transitions |
| Auto IP detection | No manual configuration required |
| Background process | Terminal can be closed; server keeps running |
| Dark, modern UI | Glassmorphism design with gradient accents |

---

## 🧩 What It Does

The project collects system information using Python's `psutil` library,
exposes it through a small HTTP API, streams it via Node.js to the browser
using Server-Sent Events (SSE), and renders it inside a modern single-page
dashboard.

**Data flow:**

```
   Your Computer
        │
        ▼
   psutil (Python)        ← reads CPU / RAM / disks
        │
        ▼
   api_server.py          ← JSON API on port 3002
        │
        ▼
   server.js (Node.js)    ← SSE stream on port 3000
        │
        ▼
   Browser (index.html)   ← live dashboard
```

---

## 📋 Requirements

Before you start, make sure you have these installed:

### 1. Miniconda (or Anaconda)
Used to create an isolated Python environment.

- Download: https://docs.conda.io/en/latest/miniconda.html

### 2. Node.js (v18 or newer) + npm
Used to run the web server.

- Download: https://nodejs.org/

### 3. Git (optional but recommended)
Used to clone the repository.

- Download: https://git-scm.com/

> Linux users: install with `sudo apt install nodejs npm git`

---

## 🚀 Installation (First Time Only)

Follow these steps once to set up the project on a new machine.

### Step 1 — Clone the repository

```bash
git clone https://github.com/<your-username>/gui-dashboard.git
cd gui-dashboard
```

(Or simply download the ZIP and extract it.)

### Step 2 — Create and activate the Conda environment

```bash
conda create -n gui-dashboard python=3.11 -y
conda activate gui-dashboard
```

### Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Install Node.js dependencies

```bash
npm install
```

That's it. Setup is complete.

---

## ▶️ Running the Project

### Start the dashboard

From the project folder, run:

```bash
python start.py
```

This will automatically:

1. Free up ports `3000` and `3002` if they were in use
2. Locate the `gui-dashboard` Conda environment
3. Launch the Python API server (`api_server.py`)
4. Launch the Node.js web server (`server.js`)
5. Detect your local IP address
6. Print a QR code in the terminal for mobile access
7. Detach the process so the terminal can be closed safely

You will see output like this:

```
  ╔══════════════════════════════════════════════════╗
  ║       ⚡  System Pulse  —  Live Dashboard         ║
  ╚══════════════════════════════════════════════════╝

   🖥  Local    :  http://localhost:3000
   📱  Network  :  http://192.168.1.42:3000

   Scan this QR with your phone (same WiFi):

   ██████████████████
   ██  ▄▄▄▄▄  ▄▄  ██
   ██  █   █  ██  ██
   ...

  ✅  System Pulse is running in the background (PID 12345).
      Stop with :  python stop.py
```

### Open the dashboard

- On your computer: visit `http://localhost:3000`
- On your phone: scan the QR code in the terminal
  (phone must be on the same WiFi network)

### Stop the dashboard

```bash
python stop.py
```

This shuts down both servers and frees ports 3000 and 3002.

---

## 🔁 Daily Use

Once installed, day-to-day use is a single command:

```bash
python start.py
```

- Terminal can be closed after starting — it runs in the background
- Next time, just open `http://localhost:3000` in your browser
- Run `python stop.py` when you want to shut it down

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1` | Open Overview tab |
| `2` | Open CPU tab |
| `3` | Open Memory tab |
| `4` | Open Storage tab |
| `↑` `↓` | Move between tabs |
| `R` | Refresh dashboard |
| Click | On any disk row → full details |

---

## 📁 Project Structure

```
gui-dashboard/
│
├── api_server.py         # Python HTTP API (port 3002) + QR banner
├── server.js             # Node.js Express server (port 3000) + SSE
├── start.py              # One-command background launcher
├── stop.py               # Stops everything cleanly
│
├── monitor.py            # Collects CPU / RAM / disk data via psutil
├── index.html            # Frontend dashboard (HTML + CSS + JS)
├── package.json          # Node.js dependencies
├── requirements.txt      # Python dependencies
│
├── main.py               # (Optional) Tkinter desktop version
├── dashboard.py          # (Optional) Tkinter GUI logic
├── widgets.py            # (Optional) Tkinter custom widgets
│
└── README.md             # This file
```

### File-by-file breakdown

| File | Purpose |
|------|---------|
| `api_server.py` | Runs the Python API, launches Node.js, prints IP + QR |
| `server.js` | Express server: serves `index.html`, proxies data via SSE |
| `start.py` | Background launcher — detects Conda, frees ports, runs everything |
| `stop.py` | Kills all processes and frees the ports |
| `monitor.py` | Background thread polling system stats every second |
| `index.html` | Complete frontend — sidebar, rings, charts, QR, refresh button |
| `package.json` | Node.js manifest (`express` dependency) |
| `requirements.txt` | Python packages (`psutil`, `qrcode`) |
| `main.py` / `dashboard.py` / `widgets.py` | Original Tkinter desktop version (optional) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| System data | Python, `psutil` |
| API server | Python `http.server` (threaded) |
| Streaming | Server-Sent Events (SSE) |
| Web server | Node.js, Express |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Charts | Chart.js 4 |
| QR codes | qrcodejs |
| Environment | Conda (`gui-dashboard`) |

---

## ⚙️ Ports Used

| Port | Service |
|------|---------|
| `3000` | Node.js web server (browser connects here) |
| `3002` | Python API server (internal only) |

If a port is busy, `start.py` will automatically free it before launching.

---

## 🐛 Troubleshooting

### "EADDRINUSE: address already in use"
Another process is holding the port. `start.py` clears it automatically, but
if the issue persists:

```bash
sudo fuser -k 3000/tcp
sudo fuser -k 3002/tcp
```

### "conda: command not found"
Open a fresh terminal, or run:

```bash
source ~/miniconda3/etc/profile.d/conda.sh
```

### "node: command not found"
Install Node.js:

```bash
sudo apt install nodejs npm      # Ubuntu / Debian
brew install node                # macOS
```

### QR code is not visible in the terminal
Make sure the `qrcode` package is installed:

```bash
pip install qrcode
```

### Phone cannot open the dashboard
- Phone and computer must be on the same WiFi
- Allow ports `3000` and `3002` through your firewall
- Some routers block device-to-device traffic (AP isolation)

### "reconnecting…" shown in the dashboard
The Python API server is not reachable. Run:

```bash
python stop.py
python start.py
```

### Blank white page in the browser
Open Developer Tools (`F12`) → Console tab and check for errors. Make sure
you are using a modern browser (Chrome, Edge, Firefox, Safari).

---

## 🔐 Privacy

System Pulse runs entirely on your local machine. No data is sent to any
external server. The dashboard is only accessible to devices on your local
network.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to
discuss what you would like to change.

---

## 📄 License

This project is released under the MIT License. You are free to use, modify,
and distribute it.

---

## 🙌 Acknowledgements

- [psutil](https://github.com/giampaolo/psutil) — system statistics
- [Chart.js](https://www.chartjs.org/) — live charts
- [Express](https://expressjs.com/) — Node.js web framework
- [qrcodejs](https://github.com/davidshimjs/qrcodejs) — QR code rendering

---

## 📬 Contact

**Author:** Fiazan
**Repository:** https://github.com/<your-username>/gui-dashboard

If you find this project useful, please consider giving it a ⭐ on GitHub.