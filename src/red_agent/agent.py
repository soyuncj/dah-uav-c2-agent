"""Red agent for the Green-Board Hijack scenario.

The red agent imports only common.wire vocabulary. It does not import common.policy.
"""
from __future__ import annotations

from typing import Any, Protocol

from common.wire import Source, to_wire


class TargetSurface(Protocol):
    def telemetry(self) -> dict[str, Any]:
        ...

    def inject_link_degrade(self, quality: float, hold_s: float, source: Source = Source.RED_AGENT) -> Any:
        ...

    def inject_gps_spoof(
        self,
        offset_m_north: float,
        offset_m_east: float,
        rate_m_s: float,
        source: Source = Source.RED_AGENT,
    ) -> Any:
        ...


class RedAgent:
    def __init__(self, target: TargetSurface) -> None:
        self.target = target
        self.trace: list[dict[str, Any]] = []

    def run_greenboard_hijack(self) -> dict[str, Any]:
        initial = self.target.telemetry()
        self._record("observe", "read telemetry before attack", initial)

        link_plan = {"quality": 0.25, "hold_s": 3.0}
        self._record("plan", "start with minimal link degradation to trigger failsafe without dropping availability", link_plan)
        for attempt in range(2):
            link_response = self.target.inject_link_degrade(
                quality=link_plan["quality"],
                hold_s=link_plan["hold_s"],
                source=Source.RED_AGENT,
            )
            self._record("act", f"link degrade attempt {attempt + 1}", link_response)
            rtl_state = self.target.telemetry()
            self._record("observe", "read state after link degradation", rtl_state)
            if rtl_state["failsafe_state"] == "triggered":
                self._record("decide", "failsafe triggered, proceed to GPS spoof", rtl_state["failsafe_state"])
                break
            link_plan["quality"] = 0.20
            link_plan["hold_s"] = 4.0
            self._record("decide", "failsafe not triggered, increase hold time and lower link quality", link_plan)

        spoof_plan = {"offset_m_north": 620.0, "offset_m_east": 180.0, "rate_m_s": 5.0}
        self._record("plan", "use a moderate GPS drift after RTL begins", spoof_plan)
        gps_response = self.target.inject_gps_spoof(source=Source.RED_AGENT, **spoof_plan)
        self._record("act", "spoof GPS reported position while keeping board green", gps_response)
        spoof_state = self.target.telemetry()
        self._record("observe", "read telemetry after spoof", spoof_state)
        if spoof_state["reported_position"] == spoof_state["ins_position"]:
            self._record("decide", "reported position was rolled back by defense, stop escalation", "spoof neutralized")
        else:
            self._record("decide", "reported position still diverges from INS, keep mission deception active", "spoof active")
        return {"agent": "red_agent", "trace": self.trace}

    def _record(self, phase: str, thought: str, result: Any) -> None:
        self.trace.append({"phase": phase, "thought": thought, "result": to_wire(result)})
