"""URL parsing and output-file location helpers."""

import ctypes
import os
import re
import uuid
from urllib.parse import unquote, urlparse

# Any host variant: www, language subdomains (pt, es, de...) or bare scribd.com.
_SCRIBD_URL = re.compile(
    r"https?://(?:[a-z0-9-]+\.)?scribd\.com/(?:document|doc)/(\d+)", re.IGNORECASE
)
_FOLDERID_DOWNLOADS = "374DE290-123F-4565-9164-39C4925E467B"


def embed_url(url):
    """Convert a Scribd document URL (any language host) into its www embed URL."""
    match = _SCRIBD_URL.search(url)
    if not match:
        raise ValueError(
            "Invalid Scribd URL. Example: "
            "https://www.scribd.com/document/123456789/Document-Title"
        )
    return f"https://www.scribd.com/embeds/{match.group(1)}/content"


def filename_from_url(url):
    path = urlparse(url).path.rstrip("/")
    last_segment = path.split("/")[-1] if path else "scribd_document"
    return safe_filename(f"{unquote(last_segment)}.pdf")


def safe_filename(name):
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip()
    return cleaned or "scribd_document.pdf"


def unique_path(path):
    """Return `path`, or `path (1)`, `path (2)`... if it already exists."""
    base, ext = os.path.splitext(path)
    candidate, counter = path, 1
    while os.path.exists(candidate):
        candidate = f"{base} ({counter}){ext}"
        counter += 1
    return candidate


def _windows_downloads_dir():
    guid = (ctypes.c_byte * 16).from_buffer_copy(
        uuid.UUID(_FOLDERID_DOWNLOADS).bytes_le
    )
    raw = ctypes.c_wchar_p()
    try:
        ctypes.windll.shell32.SHGetKnownFolderPath(
            ctypes.byref(guid), 0, None, ctypes.byref(raw)
        )
        return raw.value
    except (OSError, AttributeError):
        return None
    finally:
        ctypes.windll.ole32.CoTaskMemFree(raw)


def _linux_downloads_dir():
    config_home = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    try:
        with open(os.path.join(config_home, "user-dirs.dirs"), encoding="utf-8") as f:
            match = re.search(
                r'^XDG_DOWNLOAD_DIR="?([^"\n]+)"?', f.read(), re.MULTILINE
            )
    except OSError:
        return None
    if not match:
        return None
    return match.group(1).replace("$HOME", os.path.expanduser("~"))


def get_downloads_dir():
    """Return the system Downloads folder (Windows or Linux), creating it if needed."""
    finder = _windows_downloads_dir if os.name == "nt" else _linux_downloads_dir
    path = finder() or os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(path, exist_ok=True)
    return path
