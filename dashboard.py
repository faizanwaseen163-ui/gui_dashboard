"""
dashboard.py - Har lafz bara aur prominent.
"""

import time
import tkinter as tk

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from monitor import SystemMonitor, bytes_to_human, seconds_to_uptime
from widgets import (PALETTE, AnimatedBar, AnimatedRing, GlassCard,
                     NavButton, ParticleBackground)

REFRESH_MS = 1000
TAB_ORDER = ["overview", "cpu", "ram", "storage"]


# ---------------- UNIFORM FONT SIZES ---------------- #
class FontManager:
    # Har size bara aur consistent
    BASE_SIZES = {
        "tiny": 20,
        "small": 22,
        "normal": 26,
        "big": 32,
        "huge": 44,
        "title": 56,
    }

    def __init__(self):
        self.zoom = 1.0
        self.listeners = []

    def get(self, key):
        base = self.BASE_SIZES[key]
        return max(16, int(base * self.zoom))

    def set_zoom(self, z):
        self.zoom = max(0.75, min(2.0, z))
        for cb in self.listeners:
            cb()

    def zoom_in(self):
        self.set_zoom(self.zoom + 0.1)

    def zoom_out(self):
        self.set_zoom(self.zoom - 0.1)

    def reset(self):
        self.set_zoom(1.0)

    def subscribe(self, cb):
        self.listeners.append(cb)


FONTS = FontManager()


# ---------------- LIVE CHART ---------------- #
class LiveChart(ctk.CTkFrame):
    def __init__(self, master, color="#2563eb", **kw):
        kw.setdefault("fg_color", PALETTE["card"])
        super().__init__(master, **kw)
        self.color = color
        self.fig = Figure(figsize=(4.4, 2.2), dpi=90)
        self.fig.patch.set_facecolor(PALETTE["card"])
        self.ax = self.fig.add_subplot(111)
        self._style_axes()
        (self.line,) = self.ax.plot([], [], color=color, linewidth=3.0)
        self.fill = None
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)

    def _style_axes(self):
        self.ax.set_facecolor(PALETTE["card"])
        self.ax.set_ylim(0, 100)
        self.ax.set_xticks([])
        for spine in ("top", "right", "left", "bottom"):
            self.ax.spines[spine].set_visible(False)
        self.ax.tick_params(axis="y", labelsize=16, colors=PALETTE["text_sub"])
        self.ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.4)

    def update_data(self, history):
        xs = list(range(len(history)))
        self.line.set_data(xs, history)
        self.ax.set_xlim(0, max(1, len(history) - 1))
        if self.fill is not None:
            try:
                self.fill.remove()
            except Exception:
                pass
        self.fill = self.ax.fill_between(xs, history, 0, color=self.color, alpha=0.18)
        self.canvas.draw_idle()


# ---------------- OVERVIEW TAB ---------------- #
class OverviewTab(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)

        rings_row = ctk.CTkFrame(self, fg_color="transparent")
        rings_row.pack(fill="x", pady=(6, 18))

        self.cpu_ring = self._ring_card(rings_row, "CPU")
        self.ram_ring = self._ring_card(rings_row, "RAM")
        self.disk_ring = self._ring_card(rings_row, "STORAGE")

        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 18))
        self.stat_cores = self._stat_card(stats_row, "CPU Cores")
        self.stat_ram_total = self._stat_card(stats_row, "Total RAM")
        self.stat_disk_total = self._stat_card(stats_row, "Total Storage")
        self.stat_uptime = self._stat_card(stats_row, "Uptime")

        chart_row = ctk.CTkFrame(self, fg_color="transparent")
        chart_row.pack(fill="both", expand=True)
        chart_row.grid_columnconfigure((0, 1), weight=1)

        cpu_card = GlassCard(chart_row)
        cpu_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.cpu_title = ctk.CTkLabel(cpu_card, text="CPU Usage - Live",
                                      font=self._font("big"),
                                      text_color=PALETTE["text_main"])
        self.cpu_title.pack(anchor="w", padx=20, pady=(16, 0))
        self.cpu_chart = LiveChart(cpu_card, color=PALETTE["accent"])
        self.cpu_chart.pack(fill="both", expand=True)

        ram_card = GlassCard(chart_row)
        ram_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.ram_title = ctk.CTkLabel(ram_card, text="RAM Usage - Live",
                                      font=self._font("big"),
                                      text_color=PALETTE["text_main"])
        self.ram_title.pack(anchor="w", padx=20, pady=(16, 0))
        self.ram_chart = LiveChart(ram_card, color="#8b5cf6")
        self.ram_chart.pack(fill="both", expand=True)

    def _font(self, key):
        return ctk.CTkFont(family="Segoe UI", size=FONTS.get(key),
                           weight="bold" if key in ("big", "huge", "title") else "normal")

    def _ring_card(self, parent, label):
        card = GlassCard(parent)
        card.pack(side="left", expand=True, fill="both", padx=10, ipady=10)
        ring = AnimatedRing(card, size=270, thickness=24, label=label, bg=PALETTE["card"])
        ring.pack(padx=20, pady=20)
        return ring

    def _stat_card(self, parent, title):
        card = GlassCard(parent)
        card.pack(side="left", expand=True, fill="both", padx=8)
        ctk.CTkLabel(card, text=title, font=self._font("normal"),
                     text_color=PALETTE["text_sub"]).pack(anchor="w", padx=18, pady=(18, 4))
        val = ctk.CTkLabel(card, text="-", font=self._font("huge"),
                           text_color=PALETTE["text_main"])
        val.pack(anchor="w", padx=18, pady=(0, 18))
        return val

    def update_from(self, data, cpu_hist, ram_hist):
        cpu = data["cpu"]
        ram = data["ram"]
        dtot = data["disk_totals"]

        self.cpu_ring.set_value(cpu["percent"])
        self.ram_ring.set_value(ram["percent"], sub_text=bytes_to_human(ram["used"]))
        self.disk_ring.set_value(dtot["percent"], sub_text=bytes_to_human(dtot["used"]))

        self.stat_cores.configure(
            text=f'{cpu["cores_physical"]} / {cpu["cores_logical"]}')
        self.stat_ram_total.configure(text=bytes_to_human(ram["total"]))
        self.stat_disk_total.configure(text=bytes_to_human(dtot["total"]))
        self.stat_uptime.configure(text=seconds_to_uptime(data["boot_time"]))

        self.cpu_chart.update_data(cpu_hist)
        self.ram_chart.update_data(ram_hist)

    def reapply_fonts(self):
        self.cpu_title.configure(font=self._font("big"))
        self.ram_title.configure(font=self._font("big"))


# ---------------- CPU TAB ---------------- #
class CpuTab(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x")

        left = GlassCard(top)
        left.pack(side="left", padx=(0, 10), pady=6)
        self.ring = AnimatedRing(left, size=300, thickness=26, label="CPU TOTAL",
                                 bg=PALETTE["card"])
        self.ring.pack(padx=22, pady=22)

        right = GlassCard(top)
        right.pack(side="left", fill="both", expand=True, pady=6)
        self.chart_title = ctk.CTkLabel(right, text="CPU Load History",
                                        font=self._font("big"),
                                        text_color=PALETTE["text_main"])
        self.chart_title.pack(anchor="w", padx=20, pady=(16, 0))
        self.chart = LiveChart(right, color=PALETTE["accent"])
        self.chart.pack(fill="both", expand=True)

        self.info_label = ctk.CTkLabel(self, text="", font=self._font("normal"),
                                       text_color=PALETTE["text_sub"])
        self.info_label.pack(anchor="w", pady=(16, 10))

        cores_card = GlassCard(self)
        cores_card.pack(fill="both", expand=True, pady=(0, 6))
        self.cores_title = ctk.CTkLabel(cores_card, text="Per-Core Usage",
                                        font=self._font("big"),
                                        text_color=PALETTE["text_main"])
        self.cores_title.pack(anchor="w", padx=20, pady=(16, 6))

        self.core_holder = ctk.CTkFrame(cores_card, fg_color="transparent")
        self.core_holder.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        self.core_bars = []
        self.core_labels = []
        self.core_names = []

    def _font(self, key):
        return ctk.CTkFont(family="Segoe UI", size=FONTS.get(key),
                           weight="bold" if key in ("big", "huge", "title") else "normal")

    def _ensure_core_widgets(self, n):
        if len(self.core_bars) == n:
            return
        for w in self.core_holder.winfo_children():
            w.destroy()
        self.core_bars, self.core_labels, self.core_names = [], [], []
        for i in range(n):
            row, col = divmod(i, 2)
            cell = ctk.CTkFrame(self.core_holder, fg_color="transparent")
            cell.grid(row=row, column=col, sticky="ew", padx=12, pady=10)
            self.core_holder.grid_columnconfigure(col, weight=1)
            name_lbl = ctk.CTkLabel(cell, text=f"Core {i}", font=self._font("small"),
                                    text_color=PALETTE["text_sub"], width=140, anchor="w")
            name_lbl.pack(side="left")
            bar = AnimatedBar(cell, width=220, height=28, bg=PALETTE["card"])
            bar.pack(side="left", fill="x", expand=True, padx=10)
            val = ctk.CTkLabel(cell, text="0%", font=self._font("small"), width=110)
            val.pack(side="left")
            self.core_bars.append(bar)
            self.core_labels.append(val)
            self.core_names.append(name_lbl)

    def update_from(self, data, cpu_hist):
        cpu = data["cpu"]
        self.ring.set_value(cpu["percent"])
        self.chart.update_data(cpu_hist)
        freq_txt = f'{cpu["freq"]:.0f} MHz' if cpu["freq"] else "N/A"
        self.info_label.configure(
            text=f'Physical: {cpu["cores_physical"]}   |   '
                 f'Logical: {cpu["cores_logical"]}   |   Freq: {freq_txt}')
        self._ensure_core_widgets(len(cpu["per_core"]))
        for i, val in enumerate(cpu["per_core"]):
            self.core_bars[i].set_value(val)
            self.core_labels[i].configure(text=f"{val:.0f}%")

    def reapply_fonts(self):
        self.chart_title.configure(font=self._font("big"))
        self.cores_title.configure(font=self._font("big"))
        self.info_label.configure(font=self._font("normal"))
        for lbl in self.core_names:
            lbl.configure(font=self._font("small"))
        for lbl in self.core_labels:
            lbl.configure(font=self._font("small"))


# ---------------- RAM TAB ---------------- #
class RamTab(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)

        self._row_labels = []

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x")

        left = GlassCard(top)
        left.pack(side="left", padx=(0, 10), pady=6)
        self.ring = AnimatedRing(left, size=300, thickness=26, label="RAM",
                                 bg=PALETTE["card"])
        self.ring.pack(padx=22, pady=22)

        right = GlassCard(top)
        right.pack(side="left", fill="both", expand=True, pady=6)
        self.chart_title = ctk.CTkLabel(right, text="RAM Usage History",
                                        font=self._font("big"),
                                        text_color=PALETTE["text_main"])
        self.chart_title.pack(anchor="w", padx=20, pady=(16, 0))
        self.chart = LiveChart(right, color="#8b5cf6")
        self.chart.pack(fill="both", expand=True)

        detail = GlassCard(self)
        detail.pack(fill="x", pady=(18, 6))
        grid = ctk.CTkFrame(detail, fg_color="transparent")
        grid.pack(fill="x", padx=26, pady=24)
        self.total_val = self._row(grid, 0, "Total RAM")
        self.used_val = self._row(grid, 1, "Used RAM")
        self.avail_val = self._row(grid, 2, "Available RAM")
        self.swap_val = self._row(grid, 3, "Swap Used")

    def _font(self, key):
        return ctk.CTkFont(family="Segoe UI", size=FONTS.get(key),
                           weight="bold" if key in ("big", "huge", "title") else "normal")

    def _row(self, grid, r, title):
        lbl = ctk.CTkLabel(grid, text=title, font=self._font("big"),
                           text_color=PALETTE["text_sub"], width=340, anchor="w")
        lbl.grid(row=r, column=0, sticky="w", pady=14)
        val = ctk.CTkLabel(grid, text="-", font=self._font("huge"),
                           text_color=PALETTE["text_main"], anchor="w")
        val.grid(row=r, column=1, sticky="w", pady=14, padx=(20, 0))
        self._row_labels.append(lbl)
        return val

    def update_from(self, data, ram_hist):
        ram = data["ram"]
        self.ring.set_value(ram["percent"])
        self.chart.update_data(ram_hist)
        self.total_val.configure(text=bytes_to_human(ram["total"]))
        self.used_val.configure(text=f'{bytes_to_human(ram["used"])}  ({ram["percent"]:.0f}%)')
        self.avail_val.configure(text=bytes_to_human(ram["available"]))
        swap_txt = (f'{bytes_to_human(ram["swap_used"])} / {bytes_to_human(ram["swap_total"])}'
                    if ram["swap_total"] else "No swap")
        self.swap_val.configure(text=swap_txt)

    def reapply_fonts(self):
        self.chart_title.configure(font=self._font("big"))
        for lbl in self._row_labels:
            lbl.configure(font=self._font("big"))
        for val in (self.total_val, self.used_val, self.avail_val, self.swap_val):
            val.configure(font=self._font("huge"))


# ---------------- STORAGE TAB ---------------- #
class StorageTab(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color="transparent", **kw)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x")

        left = GlassCard(top)
        left.pack(side="left", padx=(0, 10), pady=6)
        self.ring = AnimatedRing(left, size=270, thickness=24, label="ALL DISKS",
                                 bg=PALETTE["card"])
        self.ring.pack(padx=20, pady=20)

        info = GlassCard(top)
        info.pack(side="left", fill="both", expand=True, pady=6)
        self.summary_title = ctk.CTkLabel(info, text="Combined Storage",
                                          font=self._font("big"),
                                          text_color=PALETTE["text_main"])
        self.summary_title.pack(anchor="w", padx=22, pady=(20, 10))
        self.summary_label = ctk.CTkLabel(info, text="-", font=self._font("normal"),
                                          text_color=PALETTE["text_sub"], justify="left")
        self.summary_label.pack(anchor="w", padx=22, pady=(0, 20))

        self.devices_title = ctk.CTkLabel(self,
                                          text="Devices  (click a row for full details)",
                                          font=self._font("big"),
                                          text_color=PALETTE["text_main"])
        self.devices_title.pack(anchor="w", pady=(20, 10))

        self.list_holder = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_holder.pack(fill="both", expand=True)
        self._row_widgets = {}

    def _font(self, key):
        return ctk.CTkFont(family="Segoe UI", size=FONTS.get(key),
                           weight="bold" if key in ("big", "huge", "title") else "normal")

    def update_from(self, data):
        dtot = data["disk_totals"]
        self.ring.set_value(dtot["percent"])
        self.summary_label.configure(
            text=f'Total: {bytes_to_human(dtot["total"])}     '
                 f'Used: {bytes_to_human(dtot["used"])}     '
                 f'Free: {bytes_to_human(dtot["free"])}')

        seen = set()
        for disk in data["disks"]:
            key = disk["mountpoint"]
            seen.add(key)
            if key not in self._row_widgets:
                self._row_widgets[key] = self._build_row(disk)
            self._update_row(self._row_widgets[key], disk)

        for key in list(self._row_widgets.keys()):
            if key not in seen:
                self._row_widgets[key]["frame"].destroy()
                del self._row_widgets[key]

    def _build_row(self, disk):
        card = GlassCard(self.list_holder)
        card.pack(fill="x", pady=10, padx=4)

        name = ctk.CTkLabel(card, text=f'{disk["device"]}   ->   {disk["mountpoint"]}',
                            font=self._font("normal"),
                            text_color=PALETTE["text_main"], anchor="w")
        name.pack(anchor="w", padx=20, pady=(14, 8))

        bar_row = ctk.CTkFrame(card, fg_color="transparent")
        bar_row.pack(fill="x", padx=20, pady=(0, 14))
        bar = AnimatedBar(bar_row, width=320, height=28, bg=PALETTE["card"])
        bar.pack(side="left", fill="x", expand=True)
        pct_label = ctk.CTkLabel(bar_row, text="0%", width=120, font=self._font("normal"))
        pct_label.pack(side="left", padx=(14, 0))

        detail_label = ctk.CTkLabel(card, text="", font=self._font("small"),
                                    text_color=PALETTE["text_sub"], anchor="w")
        detail_label.pack(anchor="w", padx=20, pady=(0, 16))

        widgets = {"frame": card, "bar": bar, "pct": pct_label,
                   "detail": detail_label, "name": name}

        def on_click(_e=None, d=disk["mountpoint"]):
            self._open_detail(d)

        for w in (card, name, bar_row, detail_label):
            w.bind("<Button-1>", on_click)
            try:
                w.configure(cursor="hand2")
            except Exception:
                pass
        return widgets

    def _update_row(self, widgets, disk):
        widgets["bar"].set_value(disk["percent"])
        widgets["pct"].configure(text=f'{disk["percent"]:.0f}%')
        widgets["detail"].configure(
            text=(f'{bytes_to_human(disk["total"])} total   |   '
                  f'{bytes_to_human(disk["used"])} used   |   '
                  f'{bytes_to_human(disk["free"])} free   |   {disk["fstype"]}'))
        widgets["_disk"] = disk

    def _open_detail(self, mountpoint):
        disk = self._row_widgets[mountpoint].get("_disk")
        if not disk:
            return
        win = ctk.CTkToplevel(self)
        win.title(f'Drive detail - {disk["mountpoint"]}')
        w, h = 620, 720
        root = self.winfo_toplevel()
        rx, ry = root.winfo_rootx(), root.winfo_rooty()
        rw, rh = root.winfo_width(), root.winfo_height()
        x = rx + max(0, (rw - w) // 2)
        y = ry + max(0, (rh - h) // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.configure(fg_color=PALETTE["bg"])

        ctk.CTkLabel(win, text=disk["device"], font=self._font("title"),
                     text_color=PALETTE["text_main"]).pack(pady=(28, 8))
        ring = AnimatedRing(win, size=270, thickness=24, label="USED", bg=PALETTE["bg"])
        ring.pack(pady=14)
        ring.set_value(disk["percent"])

        rows = [("Mount point", disk["mountpoint"]),
                ("File system", disk["fstype"]),
                ("Total size", bytes_to_human(disk["total"])),
                ("Used space", bytes_to_human(disk["used"])),
                ("Free space", bytes_to_human(disk["free"]))]
        grid = ctk.CTkFrame(win, fg_color="transparent")
        grid.pack(pady=16, padx=30, fill="x")
        for i, (k, v) in enumerate(rows):
            ctk.CTkLabel(grid, text=k, font=self._font("normal"),
                         text_color=PALETTE["text_sub"], anchor="w"
                         ).grid(row=i, column=0, sticky="w", pady=10)
            ctk.CTkLabel(grid, text=v, font=self._font("normal"),
                         text_color=PALETTE["text_main"], anchor="w"
                         ).grid(row=i, column=1, sticky="w", padx=(20, 0), pady=10)


# ---------------- MAIN APP ---------------- #
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("System Pulse - Live Resource Dashboard")
        self.geometry("1600x1000")
        self.minsize(1300, 850)
        self.configure(fg_color=PALETTE["bg"])

        self.monitor = SystemMonitor(history_len=60)
        self.monitor.start(interval=1.0)

        self._current_tab = "overview"

        self._build_layout()
        self._build_tabs()
        self._select_tab("overview")
        self.after(300, self._refresh_loop)
        self._bind_keys()

        FONTS.subscribe(self._reapply_all_fonts)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self):
        header = ctk.CTkFrame(self, height=170, corner_radius=0, fg_color=PALETTE["sidebar"])
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        self._particles = ParticleBackground(header, width=1600, height=170)
        self._particles.place(x=0, y=0, relwidth=1, relheight=1)
        header.bind("<Configure>",
                    lambda e: self._particles.place(x=0, y=0, width=e.width, height=e.height))

        self.title_lbl = ctk.CTkLabel(header, text="System Pulse",
                                      font=self._font("title"),
                                      text_color=PALETTE["text_main"], fg_color="transparent")
        self.title_lbl.place(x=40, y=34)

        self.sub_lbl = ctk.CTkLabel(header, text="Real-time CPU | RAM | Storage monitor",
                                    font=self._font("normal"),
                                    text_color=PALETTE["text_sub"], fg_color="transparent")
        self.sub_lbl.place(x=42, y=110)

        self.clock_lbl = ctk.CTkLabel(header, text="", font=self._font("big"),
                                      text_color=PALETTE["text_main"], fg_color="transparent")
        self.clock_lbl.place(relx=1.0, x=-36, y=42, anchor="ne")

        self.os_lbl = ctk.CTkLabel(header, text="", font=self._font("normal"),
                                   text_color=PALETTE["text_sub"], fg_color="transparent")
        self.os_lbl.place(relx=1.0, x=-36, y=100, anchor="ne")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        self.sidebar = ctk.CTkFrame(body, width=360, corner_radius=0,
                                    fg_color=PALETTE["sidebar"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.nav_buttons = {}
        nav_items = [("overview", "Overview", "1"),
                     ("cpu", "CPU", "2"),
                     ("ram", "Memory", "3"),
                     ("storage", "Storage", "4")]

        self.nav_title = ctk.CTkLabel(self.sidebar, text="NAVIGATION",
                                      font=self._font("big"),
                                      text_color=PALETTE["text_sub"])
        self.nav_title.pack(anchor="w", padx=32, pady=(32, 18))

        for key, label, num in nav_items:
            btn = NavButton(self.sidebar, f"{label}   [{num}]",
                            command=lambda k=key: self._select_tab(k))
            btn.pack(fill="x", padx=22, pady=10)
            self.nav_buttons[key] = btn

        self.hint = ctk.CTkLabel(self.sidebar,
                                 text="Shortcuts:\n"
                                      "  1-4  ->  switch tab\n"
                                      "  Up/Down  ->  navigate\n"
                                      "  Ctrl +  ->  zoom in\n"
                                      "  Ctrl -  ->  zoom out\n"
                                      "  Ctrl 0  ->  reset zoom",
                                 font=self._font("normal"), justify="left",
                                 text_color=PALETTE["text_sub"])
        self.hint.pack(side="bottom", anchor="w", padx=28, pady=(0, 20))

        self.status_lbl = ctk.CTkLabel(self.sidebar, text="Processes: -",
                                       font=self._font("normal"),
                                       text_color=PALETTE["text_sub"], justify="left")
        self.status_lbl.pack(side="bottom", anchor="w", padx=28, pady=(0, 16))

        self.content = ctk.CTkFrame(body, fg_color=PALETTE["bg"])
        self.content.pack(side="left", fill="both", expand=True, padx=22, pady=20)

    def _font(self, key):
        return ctk.CTkFont(family="Segoe UI", size=FONTS.get(key),
                           weight="bold" if key in ("big", "huge", "title") else "normal")

    def _build_tabs(self):
        self.tabs = {
            "overview": OverviewTab(self.content),
            "cpu": CpuTab(self.content),
            "ram": RamTab(self.content),
            "storage": StorageTab(self.content),
        }
        for tab in self.tabs.values():
            tab.place(relx=1.5, rely=0, relwidth=1, relheight=1)

    def _select_tab(self, key):
        self._current_tab = key
        for k, btn in self.nav_buttons.items():
            btn.set_active(k == key)
        target = self.tabs[key]
        target.lift()
        self._slide_in(target)

    def _slide_in(self, frame, x=1.0):
        if x <= 0.001:
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            return
        frame.place(relx=x, rely=0, relwidth=1, relheight=1)
        self.after(12, lambda: self._slide_in(frame, x * 0.65 if x > 0.02 else 0))

    def _bind_keys(self):
        self.bind("<Key-1>", lambda e: self._select_tab("overview"))
        self.bind("<Key-2>", lambda e: self._select_tab("cpu"))
        self.bind("<Key-3>", lambda e: self._select_tab("ram"))
        self.bind("<Key-4>", lambda e: self._select_tab("storage"))
        self.bind("<Up>", lambda e: self._navigate(-1))
        self.bind("<Down>", lambda e: self._navigate(1))
        self.bind("<Control-plus>", lambda e: FONTS.zoom_in())
        self.bind("<Control-equal>", lambda e: FONTS.zoom_in())
        self.bind("<Control-minus>", lambda e: FONTS.zoom_out())
        self.bind("<Control-Key-0>", lambda e: FONTS.reset())
        self.bind("<Control-MouseWheel>",
                  lambda e: FONTS.zoom_in() if e.delta > 0 else FONTS.zoom_out())
        self.bind("<Control-Button-4>", lambda e: FONTS.zoom_in())
        self.bind("<Control-Button-5>", lambda e: FONTS.zoom_out())

    def _navigate(self, direction):
        idx = TAB_ORDER.index(self._current_tab)
        idx = (idx + direction) % len(TAB_ORDER)
        self._select_tab(TAB_ORDER[idx])

    def _reapply_all_fonts(self):
        self.title_lbl.configure(font=self._font("title"))
        self.sub_lbl.configure(font=self._font("normal"))
        self.clock_lbl.configure(font=self._font("big"))
        self.os_lbl.configure(font=self._font("normal"))
        self.nav_title.configure(font=self._font("big"))
        self.hint.configure(font=self._font("normal"))
        self.status_lbl.configure(font=self._font("normal"))
        for btn in self.nav_buttons.values():
            btn.configure(font=self._font("big"))
        for tab in self.tabs.values():
            if hasattr(tab, "reapply_fonts"):
                tab.reapply_fonts()

    def _refresh_loop(self):
        data = self.monitor.get_data()
        if data:
            cpu_hist = self.monitor.get_cpu_history()
            ram_hist = self.monitor.get_ram_history()
            self.tabs["overview"].update_from(data, cpu_hist, ram_hist)
            self.tabs["cpu"].update_from(data, cpu_hist)
            self.tabs["ram"].update_from(data, ram_hist)
            self.tabs["storage"].update_from(data)
            self.status_lbl.configure(
                text=f'Processes: {data["process_count"]}\n{data["os"]}')
            self.os_lbl.configure(text=f'{data["os"]}  ({data["machine"]})')

        self.clock_lbl.configure(text=time.strftime("%H:%M:%S  |  %d %b %Y"))
        self.after(REFRESH_MS, self._refresh_loop)

    def _on_close(self):
        self.monitor.stop()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()