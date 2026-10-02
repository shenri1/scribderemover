"""Detect an installed browser (Chrome, Edge or Firefox) and start it with Selenium."""

import os
import shutil
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions


class BrowserNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True)
class BrowserSpec:
    key: str
    label: str
    download_url: str
    windows_exe: str
    linux_commands: tuple
    # Env var + relative path pairs checked on Windows if the registry has no entry.
    windows_paths: tuple


@dataclass(frozen=True)
class Browser:
    spec: BrowserSpec
    binary: str

    @property
    def key(self):
        return self.spec.key

    @property
    def label(self):
        return self.spec.label

    @property
    def is_chromium(self):
        return self.key in {"chrome", "edge"}


# Order = preference when no browser is requested explicitly.
BROWSER_SPECS = (
    BrowserSpec(
        key="chrome",
        label="Google Chrome",
        download_url="https://www.google.com/chrome/",
        windows_exe="chrome.exe",
        linux_commands=(
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
        ),
        windows_paths=(
            ("PROGRAMFILES", r"Google\Chrome\Application\chrome.exe"),
            ("PROGRAMFILES(X86)", r"Google\Chrome\Application\chrome.exe"),
            ("LOCALAPPDATA", r"Google\Chrome\Application\chrome.exe"),
        ),
    ),
    BrowserSpec(
        key="edge",
        label="Microsoft Edge",
        download_url="https://www.microsoft.com/edge",
        windows_exe="msedge.exe",
        linux_commands=("microsoft-edge", "microsoft-edge-stable"),
        windows_paths=(
            ("PROGRAMFILES(X86)", r"Microsoft\Edge\Application\msedge.exe"),
            ("PROGRAMFILES", r"Microsoft\Edge\Application\msedge.exe"),
        ),
    ),
    BrowserSpec(
        key="firefox",
        label="Mozilla Firefox",
        download_url="https://www.mozilla.org/firefox/",
        windows_exe="firefox.exe",
        linux_commands=("firefox",),
        windows_paths=(
            ("PROGRAMFILES", r"Mozilla Firefox\firefox.exe"),
            ("PROGRAMFILES(X86)", r"Mozilla Firefox\firefox.exe"),
        ),
    ),
)

CHROMIUM_ARGUMENTS = (
    "--window-size=1600,2200",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--remote-debugging-port=0",
    "--disable-blink-features=AutomationControlled",
    "--force-color-profile=srgb",
    "--hide-scrollbars",
)


# -------------------------------------------------------------------- detection


def _windows_registered_path(exe):
    import winreg

    key_path = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}"
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(root, key_path) as key:
                return winreg.QueryValue(key, None)
        except OSError:
            continue
    return None


def _find_binary(spec):
    candidates = []

    if os.name == "nt":
        candidates.append(_windows_registered_path(spec.windows_exe))
        for variable, relative in spec.windows_paths:
            base = os.getenv(variable)
            if base:
                candidates.append(os.path.join(base, relative))
        candidates.append(shutil.which(spec.windows_exe))
    else:
        candidates.extend(shutil.which(command) for command in spec.linux_commands)

    return next((path for path in candidates if path and os.path.isfile(path)), None)


def find_browsers():
    """Return every installed supported browser, in order of preference."""
    found = []
    for spec in BROWSER_SPECS:
        binary = _find_binary(spec)
        if binary:
            found.append(Browser(spec, binary))
    return found


def select_browser(preferred=None):
    """Return the preferred browser if installed, else the first one found."""
    browsers = find_browsers()

    if preferred:
        for browser in browsers:
            if browser.key == preferred.lower():
                return browser
        raise BrowserNotFoundError(
            f"Browser '{preferred}' was not found. "
            f"Installed: {', '.join(b.key for b in browsers) or 'none'}."
        )

    if browsers:
        return browsers[0]

    options = "\n".join(f"  - {s.label}: {s.download_url}" for s in BROWSER_SPECS)
    raise BrowserNotFoundError(
        "No supported browser found. Install one of:\n" + options
    )


# ------------------------------------------------------------------ driver setup


def _chromium_driver(browser, options_class, driver_class, profile_dir, headless):
    options = options_class()
    options.binary_location = browser.binary
    if headless:
        options.add_argument("--headless=new")
    for argument in CHROMIUM_ARGUMENTS:
        options.add_argument(argument)
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return driver_class(options=options)


def _firefox_driver(browser, headless):
    options = FirefoxOptions()
    options.binary_location = browser.binary
    if headless:
        options.add_argument("-headless")
    options.add_argument("--width=1600")
    options.add_argument("--height=2200")
    return webdriver.Firefox(options=options)


def create_driver(browser, profile_dir, headless=True):
    """Start `browser` and return a Selenium driver for it."""
    if browser.key == "chrome":
        return _chromium_driver(
            browser, ChromeOptions, webdriver.Chrome, profile_dir, headless
        )
    if browser.key == "edge":
        return _chromium_driver(
            browser, EdgeOptions, webdriver.Edge, profile_dir, headless
        )
    return _firefox_driver(browser, headless)
