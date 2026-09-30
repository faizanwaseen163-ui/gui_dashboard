"""
widgets.py - Animated widgets with BIG readable fonts.
"""

import random
import tkinter as tk
import customtkinter as ctk

PALETTE = {
    "bg": "#eef1f5",
    "sidebar": "#dfe4ea",
    "card": "#ffffff",
    "card_border": "#c9d2dc",
    "metal_dark": "#b9c2cd",
    "accent": "#2563eb",
    "good": "#16a34a",
    "warn": "#f59e0b",
    "danger": "#dc2626",
    "text_main": "#0f172a",
    "text_sub": "#334155",
}


def lerp(a, b, t):
    return a + (b - a) * t


def _clamp(v, lo=0, hi=255):
    return max(lo, min(hi, int(v)))


def lerp_color(c1, c2, t):
    c1 = c1.lstrip("#")
    c2 = c2.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = _clamp(lerp(r1, r2, t))
    g = _clamp(lerp(g1, g2, t))
    b = _clamp(lerp(b1, b2, t))
    return f"#{r:02x}{g:02x}{b:02x}"


def percent_color(p):
    if p < 60:
        return lerp_color(PALETTE["good"], PALETTE["warn"], p / 60)
    if p < 85:
        return lerp_color(PALETTE["warn"], PALETTE["danger"], (p - 60) / 25)
    return PALETTE["danger"]


class ParticleBackground(tk.Canvas):
    def __init__(self, master, width=1000, height=110, n_particles=26, **kw):
        super().__init__(master, width=width, height=height,
                         highlightthickness=0, bd=0, **kw)
        self._cw = width
        self._ch = height
        self._particles = []
        for _ in range(n_particles):
            self._particles.append({
                "x": random.uniform(0, width),
                "y": random.uniform(0, height),
                "r": random.uniform(2, 5.5),
                "vx": random.uniform(-0.35, 0.35),
                "vy": random.uniform(-0.18, 0.18),
                "a": random.uniform(0.15, 0.55),
            })
        self._sheen_x = -200
        self._running = True
        self.bind("<Configure>", self._on_resize)
        self._draw_static()
        self._animate()

    def _on_resize(self, event):
        self._cw, self._ch = event.width, event.height

    def _draw_static(self):
        self.delete("bg")
        steps = 40
        for i in range(steps):
            t = i / steps
            color = lerp_color("#dfe7f2", "#c3ccd8", t)
            self.create_rectangle(0, self._ch * t, self._cw,
                                  self._ch * (t + 1.0 / steps) + 1,
                                  fill=color, outline="", tags="bg")
        self.tag_lower("bg")

    def _animate(self):
        if not self._running:
            return
        self.delete("particle")
        self.delete("sheen")

        self._sheen_x += 2.2
        if self._sheen_x > self._cw + 250:
            self._sheen_x = -250
        self.create_polygon(
            self._sheen_x, 0, self._sheen_x + 90, 0,
            self._sheen_x - 60, self._ch, self._sheen_x - 150, self._ch,
            fill="#ffffff", stipple="gray25", outline="", tags="sheen")

        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["x"] < -10:
                p["x"] = self._cw + 10
            elif p["x"] > self._cw + 10:
                p["x"] = -10
            if p["y"] < -10:
                p["y"] = self._ch + 10
            elif p["y"] > self._ch + 10:
                p["y"] = -10

            shade = int(120 + p["a"] * 100)
            color = f"#{shade:02x}{min(shade+20,255):02x}{min(shade+45,255):02x}"
            self.create_oval(p["x"] - p["r"], p["y"] - p["r"],
                             p["x"] + p["r"], p["y"] + p["r"],
                             fill=color, outline="", tags="particle")
        self.tag_raise("particle")
        self.after(40, self._animate)

    def destroy(self):
        self._running = False
        super().destroy()


class AnimatedRing(tk.Canvas):
    def __init__(self, master, size=200, thickness=18, label="CPU", unit="%", **kw):
        bgc = kw.pop("bg", PALETTE["card"])
        super().__init__(master, width=size, height=size,
                         highlightthickness=0, bg=bgc)
        self.size = size
        self.thickness = thickness
        self.label = label
        self.unit = unit
        self.value = 0.0
        self.target = 0.0
        self.sub_text = ""
        self._draw()

    def set_value(self, target, sub_text=""):
        self.target = max(0.0, min(100.0, target))
        self.sub_text = sub_text
        self._step()

    def _step(self):
        diff = self.target - self.value
        if abs(diff) < 0.15:
            self.value = self.target
        else:
            self.value += diff * 0.18
        self._draw()
        if abs(self.target - self.value) > 0.15:
            self.after(30, self._step)

    def _draw(self):
        self.delete("all")
        pad = self.thickness
        x0, y0 = pad, pad
        x1, y1 = self.size - pad, self.size - pad

        self.create_oval(x0, y0, x1, y1,
                         outline=PALETTE["metal_dark"], width=self.thickness)
        extent = -(self.value / 100.0) * 360
        color = percent_color(self.value)
        if self.value > 0:
            self.create_arc(x0, y0, x1, y1, start=90, extent=extent,
                            style="arc", outline=color, width=self.thickness)
        cx = self.size / 2
        # BIG percentage text
        self.create_text(cx, self.size / 2 - 14,
                         text=f"{self.value:.0f}{self.unit}",
                         font=("Segoe UI", int(self.size * 0.22), "bold"),
                         fill=PALETTE["text_main"])
        # Label under it
        self.create_text(cx, self.size / 2 + 22,
                         text=self.label,
                         font=("Segoe UI", int(self.size * 0.10), "bold"),
                         fill=PALETTE["text_sub"])
        if self.sub_text:
            self.create_text(cx, self.size / 2 + 48,
                             text=self.sub_text,
                             font=("Segoe UI", int(self.size * 0.08)),
                             fill=PALETTE["text_sub"])


class AnimatedBar(tk.Canvas):
    def __init__(self, master, width=260, height=20, **kw):
        bgc = kw.pop("bg", PALETTE["card"])
        super().__init__(master, width=width, height=height,
                         highlightthickness=0, bg=bgc)
        self._cw = width
        self._ch = height
        self.value = 0.0
        self.target = 0.0
        self.bind("<Configure>", self._on_resize)
        self._draw()

    def _on_resize(self, event):
        self._cw = event.width

    def set_value(self, target):
        self.target = max(0.0, min(100.0, target))
        self._step()

    def _step(self):
        diff = self.target - self.value
        if abs(diff) < 0.2:
            self.value = self.target
        else:
            self.value += diff * 0.2
        self._draw()
        if abs(self.target - self.value) > 0.2:
            self.after(30, self._step)

    def _draw(self):
        self.delete("all")
        self.create_rectangle(0, 0, self._cw, self._ch,
                              fill=PALETTE["metal_dark"], outline="", width=0)
        fill_w = max(self._ch, self._cw * (self.value / 100.0))
        color = percent_color(self.value)
        self.create_rectangle(0, 0, fill_w, self._ch, fill=color, outline="")


class GlassCard(ctk.CTkFrame):
    def __init__(self, master, **kw):
        kw.setdefault("fg_color", PALETTE["card"])
        kw.setdefault("corner_radius", 14)
        kw.setdefault("border_width", 2)
        kw.setdefault("border_color", PALETTE["card_border"])
        super().__init__(master, **kw)

    def _on_enter(self, _e):
        pass

    def _on_leave(self, _e):
        pass


class NavButton(ctk.CTkButton):
    def __init__(self, master, text, icon="", command=None, **kw):
        super().__init__(
            master,
            text=f"  {icon}   {text}",
            command=command,
            anchor="w",
            corner_radius=10,
            fg_color="transparent",
            text_color=PALETTE["text_main"],
            hover_color="#c9d6e8",
            font=("Segoe UI", 18, "bold"),
            height=56,
            **kw,
        )

    def set_active(self, active):
        if active:
            self.configure(fg_color=PALETTE["accent"], text_color="white")
        else:
            self.configure(fg_color="transparent", text_color=PALETTE["text_main"])