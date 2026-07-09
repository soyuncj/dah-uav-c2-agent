from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.policy import evaluate_telemetry
from common.wire import FailsafeState, Reason, Rule, Verdict, Position
from demo.run_greenboard import run_case


class GreenboardScenarioTest(unittest.TestCase):
    def test_insecure_case_is_compromised_but_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_case(secure=False, log_path=Path(tmp) / "insecure.jsonl")
        self.assertTrue(result["mission"]["compromised"])
        self.assertTrue(result["mission"]["operator_deceived"])
        self.assertEqual(result["mission"]["availability"], 85)
        self.assertTrue(result["mission"]["mission_continuity"])
        self.assertEqual(result["mission"]["mode"], "RTL")
        self.assertGreater(result["mission"]["distance_reported_to_true_m"], 50.0)
        self.assertGreater(result["blue_verdict_count"], 1)

    def test_secure_case_blocks_spoof_and_preserves_availability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_case(secure=True, log_path=Path(tmp) / "secure.jsonl")
        self.assertFalse(result["mission"]["compromised"])
        self.assertFalse(result["mission"]["operator_deceived"])
        self.assertEqual(result["mission"]["availability"], 85)
        self.assertTrue(result["mission"]["mission_continuity"])
        self.assertEqual(result["blue_verdict"]["verdict"], "block")
        self.assertEqual(result["blue_verdict"]["availability_impact"], 0)
        self.assertLess(result["mission"]["distance_reported_to_true_m"], 50.0)
        self.assertGreater(result["blue_verdict_count"], 1)
        self.assertTrue(
            any(
                step["phase"] == "decide" and step["result"] == "spoof neutralized"
                for step in result["red_trace"]
            )
        )

    def test_red_view_does_not_include_ground_truth_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_case(secure=True, log_path=Path(tmp) / "secure.jsonl")
        observed_events = [step["result"] for step in result["red_trace"] if step["phase"] == "observe"]
        self.assertTrue(observed_events)
        for event in observed_events:
            self.assertNotIn("true_position", event)
            self.assertNotIn("operator_deceived", event)


class PolicyUnitTest(unittest.TestCase):
    def test_clean_telemetry_allows(self) -> None:
        detection = evaluate_telemetry(
            reported=Position(lat=36.0, lon=127.0),
            ins=Position(lat=36.0, lon=127.0),
            reported_home=Position(lat=36.0, lon=127.0),
            pinned_home=Position(lat=36.0, lon=127.0),
            failsafe=FailsafeState.NOMINAL,
            seconds_since_gps_jump=None,
        )
        self.assertEqual(detection.verdict, Verdict.ALLOW)
        self.assertEqual(detection.rule, Rule.TELEMETRY_BASELINE)
        self.assertEqual(detection.reason, Reason.OK)

    def test_small_ins_bias_does_not_false_positive(self) -> None:
        detection = evaluate_telemetry(
            reported=Position(lat=36.0, lon=127.0),
            ins=Position(lat=36.0000719, lon=127.0),
            reported_home=Position(lat=36.0, lon=127.0),
            pinned_home=Position(lat=36.0, lon=127.0),
            failsafe=FailsafeState.NOMINAL,
            seconds_since_gps_jump=None,
        )
        self.assertEqual(detection.verdict, Verdict.ALLOW)

    def test_divergence_blocks(self) -> None:
        detection = evaluate_telemetry(
            reported=Position(lat=36.0, lon=127.0),
            ins=Position(lat=36.0009, lon=127.0),
            reported_home=Position(lat=36.0, lon=127.0),
            pinned_home=Position(lat=36.0, lon=127.0),
            failsafe=FailsafeState.TRIGGERED,
            seconds_since_gps_jump=1.0,
        )
        self.assertEqual(detection.verdict, Verdict.BLOCK)
        self.assertEqual(detection.rule, Rule.CROSS_SOURCE_CONSISTENCY)
        self.assertEqual(detection.reason, Reason.GPS_INS_DIVERGENCE)

    def test_home_pin_mismatch_blocks(self) -> None:
        detection = evaluate_telemetry(
            reported=Position(lat=36.0, lon=127.0),
            ins=Position(lat=36.0, lon=127.0),
            reported_home=Position(lat=36.0005, lon=127.0),
            pinned_home=Position(lat=36.0, lon=127.0),
            failsafe=FailsafeState.NOMINAL,
            seconds_since_gps_jump=None,
        )
        self.assertEqual(detection.verdict, Verdict.BLOCK)
        self.assertEqual(detection.rule, Rule.HOME_PIN)
        self.assertEqual(detection.reason, Reason.HOME_PIN_MISMATCH)

    def test_failsafe_gps_correlation_flags(self) -> None:
        detection = evaluate_telemetry(
            reported=Position(lat=36.0, lon=127.0),
            ins=Position(lat=36.0, lon=127.0),
            reported_home=Position(lat=36.0, lon=127.0),
            pinned_home=Position(lat=36.0, lon=127.0),
            failsafe=FailsafeState.TRIGGERED,
            seconds_since_gps_jump=1.5,
        )
        self.assertEqual(detection.verdict, Verdict.FLAG)
        self.assertEqual(detection.rule, Rule.FAILSAFE_GPS_CORRELATION)
        self.assertEqual(detection.reason, Reason.FAILSAFE_GPS_CORRELATION)


if __name__ == "__main__":
    unittest.main()
