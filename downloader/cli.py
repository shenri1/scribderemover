"""Terminal entry point."""

from selenium.common.exceptions import WebDriverException

from .exporter import ScribdExporter


def main():
    url = input("Input link Scribd: ").strip()

    try:
        ScribdExporter().export(url)
    except (ValueError, RuntimeError, WebDriverException) as error:
        print(f"Export failed: {error}")
        raise SystemExit(1)
