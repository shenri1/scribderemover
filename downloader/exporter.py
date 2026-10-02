"""Drive a headless browser (Chrome, Edge or Firefox) to export a Scribd document
as a PDF, page by page."""

import base64
import os
import tempfile
import time
from io import BytesIO

from pypdf import PdfReader, PdfWriter
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.print_page_options import PrintOptions

from . import browsers, paths, scripts
from .config import Config

CSS_PX_PER_INCH = 96.0
CM_PER_INCH = 2.54


class ScribdExporter:
    """Exports a Scribd document to the system Downloads folder.

    `progress(done, total)` is called as pages are exported; `log(message)`
    receives human-readable status lines.
    """

    def __init__(self, config=None, log=print):
        self.config = config or Config.from_env()
        self.log = log

    # ----------------------------------------------------------------- public

    def export(self, url, progress=None):
        """Export `url` and return the saved file path.

        Raises ValueError for an invalid URL, and RuntimeError or
        selenium's WebDriverException if the export fails.
        """
        embed = paths.embed_url(url)
        output = paths.unique_path(
            os.path.join(paths.get_downloads_dir(), paths.filename_from_url(url))
        )
        self.log(f"Link embed: {embed}")
        self.log(f"Output file: {output}")

        browser = browsers.select_browser(self.config.browser)

        with tempfile.TemporaryDirectory(prefix="scribd-browser-profile-") as profile:
            self.log(f"Starting {browser.label}...")
            driver = browsers.create_driver(browser, profile, self.config.headless)
            try:
                self._open_document(driver, embed)
                self._export_pages(driver, output, progress)
            finally:
                driver.quit()
                self.log("Browser closed.")

        self.log(f"PDF saved successfully to: {output}")
        return output

    # ---------------------------------------------------------------- browser

    @staticmethod
    def _set_command_timeout(driver, seconds):
        executor = getattr(driver, "command_executor", None)
        if executor is None:
            return
        client_config = getattr(executor, "client_config", None) or getattr(
            executor, "_client_config", None
        )
        if client_config is not None:
            client_config.timeout = seconds

    def _open_document(self, driver, embed_url):
        driver.get(embed_url)
        time.sleep(1)

        driver.execute_script(scripts.HIDE_COOKIES)
        self.log("Cookie dialogs hidden.")

        if driver.execute_script(scripts.COUNT_PAGES) == 0:
            raise RuntimeError("No printable document pages were detected.")

        removed = driver.execute_script(scripts.PREPARE_FOR_PRINT)
        if removed["toolbarTop"]:
            self.log("Top toolbar removed.")
        if removed["toolbarBottom"]:
            self.log("Bottom toolbar removed.")
        self.log(f"Adjusted {removed['containers']} scroll containers for print.")

        driver.execute_script(scripts.INJECT_PRINT_STYLES)
        self.log("Print CSS injected.")

        driver.execute_script("window.scrollTo(0, 0)")

    # ----------------------------------------------------------- page export

    def _export_pages(self, driver, output, progress):
        batch_size = self.config.export_batch_size
        self._set_command_timeout(driver, self.config.cdp_timeout)

        total = driver.execute_script(scripts.COUNT_PAGES)
        if total <= 0:
            raise RuntimeError("No .outer_page elements found.")

        self.log(f"Exporting {total} pages in batches of {batch_size}...")

        with tempfile.TemporaryDirectory(prefix="scribd-pdf-pages-") as spool:
            page_files = []
            batch = []

            for index in range(total):
                if progress:
                    progress(index, total)

                if index % batch_size == 0:
                    batch = list(range(index + 1, min(total, index + batch_size) + 1))
                    self.log(f"  Loading pages {batch[0]}-{batch[-1]}/{total}...")
                    self._load_pages(driver, batch)

                page_pdf = self._render_page(driver, index, total)
                if page_pdf:
                    page_path = os.path.join(spool, f"page-{index + 1:08d}.pdf")
                    with open(page_path, "wb") as handle:
                        handle.write(page_pdf)
                    page_files.append(page_path)

                if (index + 1) % batch_size == 0 or index + 1 == total:
                    self._release_pages(driver, batch)

            if progress:
                progress(total, total)

            if not page_files:
                raise RuntimeError("No valid document pages were exported.")

            self._merge(page_files, output)

    def _load_pages(self, driver, page_numbers):
        timeout = self.config.page_load_timeout
        self._set_command_timeout(driver, timeout + 10)
        driver.set_script_timeout(timeout + 10)

        result = driver.execute_async_script(
            scripts.LOAD_PAGES, list(page_numbers), timeout * 1000
        )

        if not result.get("supported"):
            raise RuntimeError("Scribd direct page loader is unavailable.")

        if result["failed"]:
            details = ", ".join(
                f"{item['pageNum']} ({item['reason']})" for item in result["failed"]
            )
            raise RuntimeError(f"Failed to load Scribd page(s): {details}")

    @staticmethod
    def _release_pages(driver, page_numbers):
        driver.execute_script(scripts.RELEASE_PAGES, list(page_numbers))
        # Chromium only, best effort: ask the browser to reclaim memory.
        collect = getattr(driver, "execute_cdp_cmd", None)
        if collect:
            try:
                collect("HeapProfiler.collectGarbage", {})
            except WebDriverException:
                pass

    def _render_page(self, driver, index, total):
        """Print one page to PDF bytes, or return None if it must be skipped."""
        size = driver.execute_script(scripts.ISOLATE_PAGE, index)
        if not size:
            self.log(f"  Skipping page {index + 1}: element missing")
            return None

        width_px, height_px = int(size["width"]), int(size["height"])
        if width_px <= 0 or height_px <= 0:
            self.log(
                f"  Skipping page {index + 1}: invalid geometry {width_px}x{height_px}"
            )
            return None

        width_in = width_px / CSS_PX_PER_INCH
        height_in = height_px / CSS_PX_PER_INCH
        self.log(
            f"  Page {index + 1}/{total} {width_px}x{height_px}px "
            f'-> {width_in:.3f}"x{height_in:.3f}"'
        )

        # WebDriver's standard print command: same call on Chrome, Edge and Firefox.
        options = PrintOptions()
        options.background = True
        options.scale = 1
        options.shrink_to_fit = False
        options.page_width = width_in * CM_PER_INCH
        options.page_height = height_in * CM_PER_INCH
        options.margin_top = options.margin_bottom = 0
        options.margin_left = options.margin_right = 0
        options.page_ranges = ["1"]

        pdf_bytes = base64.b64decode(driver.print_page(options))

        sheets = len(PdfReader(BytesIO(pdf_bytes)).pages)
        if sheets != 1:
            raise RuntimeError(
                f"Document page {index + 1} produced {sheets} PDF sheets; expected 1."
            )
        return pdf_bytes

    def _merge(self, page_files, output):
        self.log(f"Merging {len(page_files)} disk-spooled PDF pages...")
        writer = PdfWriter()
        try:
            for page_path in page_files:
                writer.append(page_path)
            with open(output, "wb") as handle:
                writer.write(handle)
        finally:
            writer.close()
