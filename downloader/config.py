"""Runtime settings, overridable through SCRIBD_* environment variables."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # Seconds the browser driver waits for a single command (e.g. printing a page).
    cdp_timeout: int = 600
    # Seconds allowed for one batch of pages to finish loading.
    page_load_timeout: int = 120
    # Pages loaded/exported before their memory is released.
    export_batch_size: int = 8
    # Run the browser without a visible window.
    headless: bool = True
    # "chrome", "edge" or "firefox"; None picks the first one installed.
    browser: str | None = None

    @classmethod
    def from_env(cls):
        return cls(
            browser=os.getenv("SCRIBD_BROWSER") or None,
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
