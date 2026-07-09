from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from demo.run_greenboard import run_case


class GreenboardScenarioTest(unittest.TestCase):
    def test_insecure_case_is_compromised_but_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_case(secure=False, log_path=Path(tmp) / "insecure.jsonl")
        self.assertTrue(result["mission"]["compromised"])
        self.assertEqual(result["mission"]["availability"], 100)
        self.assertEqual(result["mission"]["mode"], "RTL")

    def test_secure_case_blocks_spoof_and_preserves_availability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_case(secure=True, log_path=Path(tmp) / "secure.jsonl")
        self.assertFalse(result["mission"]["compromised"])
        self.assertEqual(result["mission"]["availability"], 100)
        self.assertIn(result["blue_verdict"]["verdict"], {"allow", "flag"})


if __name__ == "__main__":
    unittest.main()
