"""Availability-aware blue agent."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from common import policy
from common.wire import FailsafeState, Position, append_jsonl, now_ts, to_wire


class BlueAgent:
    def __init__(self, pinned_home: Position, log_path: str | Path = "logs/events.jsonl") -> None:
        self.pinned_home = pinned_home
        self.log_path = Path(log_path)

    def inspect_telemetry(self, telemetry_event: dict[str, Any]) -> dict[str, Any]:
        seconds_since_gps_jump = None
        if telemetry_event.get("failsafe_state") == FailsafeState.TRIGGERED.value:
            seconds_since_gps_jump = 1.0

        detection = policy.evaluate_telemetry(
            reported=_position_from_wire(telemetry_event["reported_position"]),
            ins=_position_from_wire(telemetry_event["ins_position"]),
            reported_home=_position_from_wire(telemetry_event["home"]),
            pinned_home=self.pinned_home,
            failsafe=FailsafeState(telemetry_event["failsafe_state"]),
            seconds_since_gps_jump=seconds_since_gps_jump,
        )
        verdict = {
            "event": "verdict",
            "ts": now_ts(),
            "seq": telemetry_event["seq"] + 10_000,
            "ref_seq": telemetry_event["seq"],
            "ref_event": "telemetry",
            "verdict": detection.verdict,
            "rule": detection.rule,
            "reason": detection.reason,
            "confidence": detection.confidence,
            "detected_by": "blue_agent",
            "availability_impact": detection.availability_impact,
            "detail": detection.detail,
        }
        append_jsonl(self.log_path, verdict)
        return to_wire(verdict)


def _position_from_wire(value: Position | dict[str, Any]) -> Position:
    if isinstance(value, Position):
        return value
    return Position(lat=value["lat"], lon=value["lon"], alt_m=value.get("alt_m", 0.0))
