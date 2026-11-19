"""Keep private roster material and live-account names out of the demo sources."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("atrium", "docs", "scripts", ".github")
SCAN_FILES = ("README.md", "SECURITY.md", "pyproject.toml", "LICENSE", ".env.example")
FORBIDDEN = (
    "amanda",
    "robinhood",
    "whatsapp",
    "brokerage",
    "ystudio",
    "telegram",
)
WORD_FORBIDDEN = ("rio", "sterling", "juno")


TEXT_SUFFIXES = {".py", ".md", ".toml", ".yml", ".yaml", ".css", ".js", ".html", ".txt"}
EXTRA_NAMES = {".env.example", ".gitignore", "LICENSE"}
SKIP_PARTS = {".git", "__pycache__", ".ruff_cache", ".venv"}


def _sources() -> list[Path]:
    found: list[Path] = []
    for name in SCAN_FILES:
        path = ROOT / name
        if path.exists():
            found.append(path)
    for folder in SCAN_ROOTS:
        root = ROOT / folder
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
                continue
            if path.suffix.lower() in TEXT_SUFFIXES or path.name in EXTRA_NAMES:
                found.append(path)
    return found


class FictionBoundaryTests(unittest.TestCase):
    def test_sources_stay_fictional(self) -> None:
        for path in _sources():
            text = path.read_text(encoding="utf-8", errors="replace")
            lowered = text.casefold()
            for needle in FORBIDDEN:
                with self.subTest(path=str(path), needle=needle):
                    self.assertNotIn(needle, lowered)
            for word in WORD_FORBIDDEN:
                with self.subTest(path=str(path), word=word):
                    self.assertIsNone(
                        re.search(rf"\b{word}\b", lowered),
                        f"{word} appeared in {path}",
                    )

    def test_email_addresses_use_the_example_domain(self) -> None:
        for path in _sources():
            text = path.read_text(encoding="utf-8", errors="replace")
            for email in re.findall(r"[\w.+-]+@[\w.-]+\.\w+", text):
                with self.subTest(path=str(path), email=email):
                    self.assertTrue(email.endswith(".example"), email)


if __name__ == "__main__":
    unittest.main()
