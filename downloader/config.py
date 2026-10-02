"""Runtime settings, overridable through SCRIBD_* environment variables."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # Seconds ChromeDriver waits for a single command (e.g. printToPDF).
    cdp_timeout: int = 600
    # Seconds allowed for one batch of pages to finish loading.
    page_load_timeout: int = 120
    # Pages loaded/exported before their memory is released.
    export_batch_size: int = 8
    # Run Chrome without a visible window.
    headless: bool = True

    @classmethod
    def from_env(cls):
        return cls(
            cdp_timeout=int(os.getenv("SCRIBD_CDP_TIMEOUT", cls.cdp_timeout)),
            page_load_timeout=max(
                10, int(os.getenv("SCRIBD_PAGE_LOAD_TIMEOUT", cls.page_load_timeout))
            ),
            export_batch_size=max(
                1, int(os.getenv("SCRIBD_EXPORT_BATCH_SIZE", cls.export_batch_size))
            ),
            headless=os.getenv("SCRIBD_HEADLESS", "1").strip().lower()
            not in {"0", "false", "no"},
        )
