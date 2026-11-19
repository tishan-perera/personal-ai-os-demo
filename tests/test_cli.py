import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from atrium.cli import _load_office, main, run_demo


class CliTests(unittest.TestCase):
    def test_demo_transcript_shows_the_gate(self) -> None:
        text = run_demo()
        self.assertIn("fictional demo", text)
        self.assertIn("No bank was contacted", text)
        self.assertIn("rejected", text)
        self.assertIn("recorded-simulated", text)
        self.assertIn("sent messages 0", text)

    def test_demo_command_exits_cleanly(self) -> None:
        with redirect_stdout(io.StringIO()) as stdout:
            code = main(["demo"])
        self.assertEqual(code, 0)
        self.assertIn("Audit", stdout.getvalue())

    def test_module_entrypoint(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "atrium", "demo"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No bank was contacted", result.stdout)

    def test_missing_proposal_is_a_usage_error(self) -> None:
        with redirect_stderr(io.StringIO()):
            code = main(["decide", "APR-999", "approve"])
        self.assertEqual(code, 2)

    def test_state_file_survives_a_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "desk" / "state.json")
            office = _load_office(path)
            created = office.handle("Send the Friday building reminder")
            restored = _load_office(path)
            decided = restored.decide(created["proposal"]["id"], "approve", actor="owner")
            self.assertEqual(decided["proposal"]["status"], "executed")
            saved = json.loads(Path(path).read_text(encoding="utf-8"))
            self.assertEqual(saved["world"]["flags"]["reminder"], "sent-simulated")


if __name__ == "__main__":
    unittest.main()
