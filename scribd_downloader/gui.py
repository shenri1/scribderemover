"""Small tkinter window with a progress bar."""

import queue
import threading
import tkinter as tk
from tkinter import ttk

from selenium.common.exceptions import WebDriverException

from .exporter import ScribdExporter
from .paths import get_downloads_dir

POLL_INTERVAL_MS = 100
BAR_LENGTH = 420


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Scribd Downloader")
        self.resizable(False, False)

        self.url = tk.StringVar()
        self.status = tk.StringVar(value=f"Saves to: {get_downloads_dir()}")
        # The worker thread never touches widgets; it posts events here instead.
        self.events = queue.Queue()

        self._build_widgets()
        self.after(POLL_INTERVAL_MS, self._poll_events)

    # ----------------------------------------------------------------- layout

    def _build_widgets(self):
        frame = ttk.Frame(self, padding=16)
        frame.grid()

        ttk.Label(frame, text="Scribd link:").grid(row=0, column=0, sticky="w")

        self.entry = ttk.Entry(frame, textvariable=self.url, width=60)
        self.entry.grid(row=1, column=0, pady=(2, 10))
        self.entry.focus()
        self.entry.bind("<Return>", lambda _event: self._start())

        self.button = ttk.Button(frame, text="Download", command=self._start)
        self.button.grid(row=2, column=0, sticky="e")

        self.bar = ttk.Progressbar(frame, length=BAR_LENGTH, maximum=100)
        self.bar.grid(row=3, column=0, pady=(12, 2), sticky="ew")

        ttk.Label(frame, textvariable=self.status, wraplength=BAR_LENGTH).grid(
            row=4, column=0, sticky="w"
        )

    def _set_busy(self, busy):
        state = ["disabled"] if busy else ["!disabled"]
        self.button.state(state)
        self.entry.state(state)

    def _show_progress(self, percent):
        self.bar.stop()
        self.bar.configure(mode="determinate")
        self.bar["value"] = percent

    # ----------------------------------------------------------------- actions

    def _start(self):
        url = self.url.get().strip()
        if not url:
            return

        self._set_busy(True)
        self.bar.configure(mode="indeterminate")
        self.bar.start(12)
        self.status.set("Starting browser and loading document...")

        threading.Thread(target=self._work, args=(url,), daemon=True).start()

    def _work(self, url):
        """Runs on the worker thread."""
        try:
            path = ScribdExporter().export(
                url,
                progress=lambda done, total: self.events.put(("progress", done, total)),
            )
            self.events.put(("done", path))
        except (ValueError, RuntimeError, WebDriverException) as error:
            self.events.put(("error", str(error).splitlines()[0]))

    def _poll_events(self):
        try:
            while True:
                kind, *data = self.events.get_nowait()
                getattr(self, f"_on_{kind}")(*data)
        except queue.Empty:
            pass
        self.after(POLL_INTERVAL_MS, self._poll_events)

    # ------------------------------------------------------------ event hooks

    def _on_progress(self, done, total):
        percent = done * 100 / total
        self._show_progress(percent)
        self.status.set(f"{percent:.0f}% ({done}/{total} pages)")

    def _on_done(self, path):
        self._show_progress(100)
        self.status.set(f"Saved: {path}")
        self._set_busy(False)

    def _on_error(self, message):
        self._show_progress(0)
        self.status.set(f"Error: {message}")
        self._set_busy(False)


def main():
    App().mainloop()
