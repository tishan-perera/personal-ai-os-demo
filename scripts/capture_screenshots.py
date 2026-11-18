"""Capture the README screenshots from a running local demo.

Start the desk first: python3 -m atrium --port 8787
"""

import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8787"
OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
SHOTS = (
    ("budget", "budget.png"),
    ("queue", "approval.png"),
    ("audit", "audit.png"),
)


def reset() -> None:
    request = urllib.request.Request(
        BASE + "/api/reset",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        response.read()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        for demo, name in SHOTS:
            reset()
            page.goto(f"{BASE}/?demo={demo}", wait_until="networkidle")
            page.wait_for_function("() => document.body.dataset.ready === 'true'")
            if demo == "queue":
                page.wait_for_selector(".ticket.pending button.approve")
            elif demo == "audit":
                page.wait_for_selector(".ticket.executed")
            elif demo == "budget":
                page.get_by_text("Left to assign").wait_for()
            page.screenshot(path=str(OUT / name))
            print(OUT / name)
        narrow = browser.new_page(viewport={"width": 390, "height": 844})
        reset()
        narrow.goto(BASE + "/?demo=queue", wait_until="networkidle")
        narrow.wait_for_selector(".ticket.pending")
        narrow.screenshot(path=str(OUT / "phone.png"), full_page=True)
        print(OUT / "phone.png")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
