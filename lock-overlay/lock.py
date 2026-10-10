# lock-overlay/lock.py
import json
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk

CONFIG_PATH = Path(__file__).parent / "config.json"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def shutdown_pc(delay=5):
    subprocess.Popen(
        ["shutdown", "/s", "/t", str(delay), "/c", "Lock overlay: wrong password."],
        shell=False,
    )

class LockOverlay:
    def __init__(self, root, cfg):
        self.root = root
        self.cfg = cfg
        self.password = cfg["password"]
        self.seconds_left = int(cfg["duration_seconds"])
        self.escape_combo = cfg.get("escape_combo", "<Control-Alt-q>")

        self._setup_window()
        self._build_ui()
        self._bind_events()
        self._tick()

    def _setup_window(self):
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.configure(bg="black")
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_w}x{screen_h}+0+0")

    def _build_ui(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(
            self.root, width=screen_w, height=screen_h,
            highlightthickness=0, bd=0, bg="black",
        )
        self.canvas.pack(fill="both", expand=True)

        img_path = Path(self.cfg["image"])
        if not img_path.is_absolute():
            img_path = Path(__file__).parent / img_path

        if img_path.exists():
            img = Image.open(img_path).convert("RGB")
            img = img.resize((screen_w, screen_h), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor="nw", image=self.bg_photo)

        panel_w = 520
        panel_h = 260
        px = (screen_w - panel_w) // 2
        py = (screen_h - panel_h) // 2

        self.canvas.create_rectangle(
            px, py, px + panel_w, py + panel_h,
            fill="#0b0b0b", outline="#2a2a2a", width=2,
        )

        self.canvas.create_text(
            screen_w // 2, py + 30,
            text=self.cfg.get("title", "Locked"),
            fill="#e8e8e8", font=("Segoe UI", 22, "bold"),
        )

        self.canvas.create_text(
            screen_w // 2, py + 75,
            text=self.cfg.get("subtitle", "Enter password to unlock."),
            fill="#9a9a9a", font=("Segoe UI", 11),
        )

        self.timer_id = self.canvas.create_text(
            screen_w // 2, py + 120,
            text="", fill="#ff5555", font=("Consolas", 28, "bold"),
        )

        self.entry = tk.Entry(
            self.root, show="*", font=("Segoe UI", 14),
            bg="#151515", fg="#e8e8e8", insertbackground="#e8e8e8",
            relief="flat", justify="center",
        )
        self.entry.place(x=screen_w // 2 - 180, y=py + 165, width=360, height=36)
        self.entry.focus_force()

        self.status_id = self.canvas.create_text(
            screen_w // 2, py + 225,
            text="", fill="#888888", font=("Segoe UI", 10),
        )

    def _bind_events(self):
        self.entry.bind("<Return>", self._check_password)
        self.root.bind(self.escape_combo, self._escape)
        self.root.bind_all(self.escape_combo, self._escape)
        self.root.bind("<Escape>", lambda e: "break")
        self.root.bind("<Alt-F4>", lambda e: "break")

    def _check_password(self, event=None):
        entered = self.entry.get()
        if entered == self.password:
            self.canvas.itemconfigure(self.status_id, text="Unlocked.", fill="#66ff88")
            self.root.after(300, self._quit)
        else:
            self.canvas.itemconfigure(
                self.status_id,
                text="Wrong password. Shutting down...",
                fill="#ff4444",
            )
            self.root.after(400, lambda: shutdown_pc(5))

    def _tick(self):
        if self.seconds_left <= 0:
            self.canvas.itemconfigure(self.timer_id, text="00:00")
            self.canvas.itemconfigure(
                self.status_id,
                text="Time expired. Shutting down...",
                fill="#ff4444",
            )
            self.root.after(400, lambda: shutdown_pc(5))
            return

        m, s = divmod(self.seconds_left, 60)
        self.canvas.itemconfigure(self.timer_id, text=f"{m:02d}:{s:02d}")
        self.seconds_left -= 1
        self.root.after(1000, self._tick)

    def _escape(self, event=None):
        self._quit()

    def _quit(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        sys.exit(0)

def main():
    if not CONFIG_PATH.exists():
        print(f"missing config: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)

    cfg = load_config()
    root = tk.Tk()
    LockOverlay(root, cfg)
    root.mainloop()

if __name__ == "__main__":
    main()
