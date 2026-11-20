"""The burst-guard confirmation dialog.

Runs as its own process for the same reason the overlay does: Tk only paints
from the main thread, and the tray already owns the parent's. Prints the
choice - "stop" or "allow_hour" - on stdout. Deciding nothing means stop,
because that is the safe answer to a burst you were not expecting.

Two details exist for macOS specifically:

* ``tk.Button`` ignores ``bg``/``fg`` under the Aqua theme, so the buttons are
  drawn from ``Frame`` + ``Label``. Otherwise both buttons render as identical
  grey slabs and the labels are barely legible.
* The window height is measured after layout, because the Chinese body text
  wraps to a different number of lines than the English one.
"""
from __future__ import annotations

import argparse
import math
import sys
import tkinter as tk
from tkinter import font as tkfont

from yesdev.core import i18n

LIMIT_SECONDS = 15.0
BG = "#1f2430"
FG = "#e8ecf4"
MUTED = "#a7b0c0"
ACCENT = "#d9534f"
ACCENT_HOVER = "#e2685f"
NEUTRAL = "#39404f"
NEUTRAL_HOVER = "#495061"
WINDOW_WIDTH = 500


def _draw_button(parent: tk.Misc, text: str, *, bg: str, hover: str, fg: str,
                 font: tkfont.Font, command) -> tk.Frame:
    """A button made of a Frame and a Label.

    macOS draws ``tk.Button`` with the system theme and ignores the colours
    given to it, which made the stop/allow pair indistinguishable. A Frame
    keeps the colours we ask for on every platform.
    """
    holder = tk.Frame(parent, bg=bg, cursor="hand2")
    label = tk.Label(holder, text=text, bg=bg, fg=fg, font=font,
                     padx=18, pady=9)
    label.pack(fill="both", expand=True)

    def enter(_event=None):
        holder.configure(bg=hover)
        label.configure(bg=hover)

    def leave(_event=None):
        holder.configure(bg=bg)
        label.configure(bg=bg)

    for widget in (holder, label):
        widget.bind("<Button-1>", lambda _e: command())
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    return holder


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Warn that approvals look like a burst, and offer to stop.")
    parser.add_argument("count", nargs="?", default="?",
                        help="approvals seen in the last minute")
    parser.add_argument("app", nargs="?", default="Yes, Dev",
                        help="application name shown in the window title")
    args = parser.parse_args()
    count, app = args.count, args.app

    root = tk.Tk()
    root.title(app)
    root.configure(bg=BG)
    root.resizable(False, False)
    root.attributes("-topmost", True)

    choice = {"value": "stop"}
    heading = tkfont.nametofont("TkDefaultFont").copy()
    heading.configure(size=12, weight="bold")
    action = tkfont.nametofont("TkDefaultFont").copy()
    action.configure(size=11, weight="bold")

    tk.Label(root, text=i18n.t("burst.title", count=count),
             bg=BG, fg=FG, font=heading, anchor="w",
             wraplength=WINDOW_WIDTH - 40, justify="left",
             ).pack(fill="x", padx=20, pady=(18, 6))
    tk.Label(root, text=i18n.t("burst.body", app=app),
             bg=BG, fg=MUTED, anchor="w", justify="left",
             wraplength=WINDOW_WIDTH - 40,
             ).pack(fill="x", padx=20)

    countdown = tk.Label(root, text="", bg=BG, fg=ACCENT, anchor="w")
    countdown.pack(fill="x", padx=20, pady=(14, 6))

    track = tk.Canvas(root, height=4, bg=NEUTRAL, highlightthickness=0)
    track.pack(fill="x", padx=20)
    bar = track.create_rectangle(0, 0, 0, 4, fill=ACCENT, width=0)

    def pick(value: str) -> None:
        choice["value"] = value
        root.destroy()

    row = tk.Frame(root, bg=BG)
    row.pack(fill="x", padx=20, pady=16)

    allow = _draw_button(row, i18n.t("burst.allow"), bg=NEUTRAL, hover=NEUTRAL_HOVER,
                         fg=FG, font=action, command=lambda: pick("allow_hour"))
    allow.pack(side="right", padx=(10, 0))

    stop = _draw_button(row, i18n.t("burst.stop", app=app), bg=ACCENT,
                        hover=ACCENT_HOVER, fg="#ffffff", font=action,
                        command=lambda: pick("stop"))
    stop.pack(side="right")

    # Ask Tk how tall the content actually is, then centre the window with that
    # height. Fixed heights clip the Chinese text on some font sizes.
    root.update_idletasks()
    height = max(220, root.winfo_reqheight())
    root.geometry(f"{WINDOW_WIDTH}x{height}"
                  f"+{(root.winfo_screenwidth() - WINDOW_WIDTH) // 2}"
                  f"+{(root.winfo_screenheight() - height) // 3}")

    remaining = [LIMIT_SECONDS]

    def tick() -> None:
        remaining[0] -= 0.1
        if remaining[0] <= 0:
            pick("stop")
            return
        seconds = max(1, math.ceil(remaining[0]))
        countdown.config(text=i18n.t("burst.countdown", seconds=seconds))
        frac = remaining[0] / LIMIT_SECONDS
        track.coords(bar, 0, 0, track.winfo_width() * frac, 4)
        root.after(100, tick)

    root.after(100, tick)
    root.lift()
    root.focus_force()
    root.protocol("WM_DELETE_WINDOW", lambda: pick("stop"))
    root.mainloop()

    print(choice["value"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
