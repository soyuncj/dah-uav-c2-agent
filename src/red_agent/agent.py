"""Red agent for the Green-Board Hijack scenario.

The red agent imports only common.wire vocabulary. It does not import common.policy.
"""
from __future__ import annotations

from typing import Any

from common.wire import Source, to_wire


class RedAgent:
    def __init__(self, target: Any) -> None:
        self.target = target
        self.trace: list[dict[str, Any]] = []

    def run_greenboard_hijack(self) -> dict[str, Any]:
        self._record("observe", "read telemetry before attack", self.target.telemetry())
        link_response = self.target.inject_link_degrade(
            quality=0.20,
            hold_s=4.0,
            source=Source.RED_AGENT,
        )
        self._record("act", "degrade link to trigger RTL failsafe", link_response)
        self._record("observe", "read RTL state after link degradation", self.target.telemetry())
        gps_response = self.target.inject_gps_spoof(
            offset_m_north=620.0,
            offset_m_east=180.0,
            rate_m_s=5.0,
            source=Source.RED_AGENT,
        )
        self._record("act", "spoof GPS reported position while keeping board green", gps_response)
        self._record("observe", "read telemetry after spoof", self.target.telemetry())
        return {"agent": "red_agent", "trace": self.trace}

    def _record(self, phase: str, thought: str, result: Any) -> None:
        self.trace.append({"phase": phase, "thought": thought, "result": to_wire(result)})
