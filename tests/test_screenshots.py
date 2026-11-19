"""The README screenshots are captured from a real local run."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ("budget.png", "approval.png", "audit.png", "phone.png")


class ScreenshotTests(unittest.TestCase):
    def test_readme_screenshots_are_real_pngs(self) -> None:
        for name in SHOTS:
            path = ROOT / "docs" / "screenshots" / name
            with self.subTest(name=name):
                self.assertTrue(path.is_file(), name)
                self.assertGreater(path.stat().st_size, 10_000)
                self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
