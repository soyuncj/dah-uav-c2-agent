"""Local mock GCS/UAV simulator for the Green-Board Hijack scenario."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common import geo
from common.wire import (
    ActionResponse,
    FailsafeState,
    InjectType,
    Mode,
    Position,
    Reason,
    Source,
    append_jsonl,
    now_ts,
    to_wire,
)


@dataclass
class SimState:
    seq: int
    home: Position
    true_position: Position
    reported_position: Position
    ins_position: Position
    mode: Mode = Mode.AUTO
    armed: bool = True
    velocity_ms: float = 35.0
    heading_deg: float = 0.0
    battery_pct: int = 91
    gps_fix: bool = True
    gps_jammed: bool = False
    link_quality: float = 1.0
    failsafe_state: FailsafeState = FailsafeState.NOMINAL
    availability: int = 100
    compromised: bool = False
    gps_jump_seq: int | None = None


class MockGCS:
    def __init__(self, secure: bool, log_path: str | Path = "logs/events.jsonl") -> None:
        home = Position(lat=36.350411, lon=127.384548, alt_m=120.0)
        self.secure = secure
        self.log_path = Path(log_path)
        self.state = SimState(
            seq=0,
            home=home,
            true_position=geo.offset_m(home, north_m=420.0, east_m=120.0),
            reported_position=geo.offset_m(home, north_m=420.0, east_m=120.0),
            ins_position=geo.offset_m(home, north_m=420.0, east_m=120.0),
        )

    def telemetry(self, include_true: bool = False) -> dict[str, Any]:
        self._tick()
        event = self._telemetry_event()
        append_jsonl(self.log_path, event)
        if include_true:
            return event
        red_view = dict(event)
        red_view.pop("true_position")
        return red_view

    def inject_link_degrade(self, quality: float, hold_s: float, source: Source = Source.RED_AGENT) -> ActionResponse:
        self._tick()
        accepted = True
        reason = Reason.OK
        self.state.link_quality = max(0.0, min(1.0, quality))
        if self.state.link_quality < 0.30:
            self.state.failsafe_state = FailsafeState.LINK_DEGRADED
        if self.state.link_quality < 0.30 and hold_s >= 3.0:
            self.state.failsafe_state = FailsafeState.TRIGGERED
            self.state.mode = Mode.RTL

        self._log_inject(
            inject_type=InjectType.LINK_DEGRADE,
            params={"quality": quality, "hold_s": hold_s},
            source=source,
            accepted=accepted,
            reason=reason,
        )
        return ActionResponse(
            seq=self.state.seq,
            accepted=accepted,
            reason=reason,
            availability_after=self.state.availability,
        )

    def inject_gps_spoof(
        self,
        offset_m_north: float,
        offset_m_east: float,
        rate_m_s: float,
        source: Source = Source.RED_AGENT,
    ) -> ActionResponse:
        self._tick()
        self.state.reported_position = geo.offset_m(
            self.state.reported_position,
            north_m=offset_m_north,
            east_m=offset_m_east,
        )
        self.state.gps_jump_seq = self.state.seq

        if not self.secure:
            self.state.true_position = geo.offset_m(
                self.state.true_position,
                north_m=offset_m_north,
                east_m=offset_m_east,
            )
            self.state.compromised = True
        else:
            self.state.reported_position = self.state.ins_position
            self.state.compromised = False

        self._log_inject(
            inject_type=InjectType.GPS_SPOOF,
            params={
                "offset_m_north": offset_m_north,
                "offset_m_east": offset_m_east,
                "rate_m_s": rate_m_s,
            },
            source=source,
            accepted=not self.secure,
            reason=Reason.OK if not self.secure else Reason.GPS_INS_DIVERGENCE,
        )
        return ActionResponse(
            seq=self.state.seq,
            accepted=not self.secure,
            reason=Reason.OK if not self.secure else Reason.GPS_INS_DIVERGENCE,
            verdict_by="mock_gcs" if self.secure else None,
            availability_after=self.state.availability,
        )

    def _tick(self) -> None:
        self.state.seq += 1

    def _telemetry_event(self) -> dict[str, Any]:
        return {
            "event": "telemetry",
            "ts": now_ts(),
            "seq": self.state.seq,
            "uav_id": "UAV-01",
            "mode": self.state.mode,
            "reported_position": self.state.reported_position,
            "ins_position": self.state.ins_position,
            "true_position": self.state.true_position,
            "velocity_ms": self.state.velocity_ms,
            "battery_pct": self.state.battery_pct,
            "gps_jammed": self.state.gps_jammed,
            "link_quality": self.state.link_quality,
            "failsafe_state": self.state.failsafe_state,
            "home": self.state.home,
            "availability": self.state.availability,
        }

    def _log_inject(
        self,
        inject_type: InjectType,
        params: dict[str, Any],
        source: Source,
        accepted: bool,
        reason: Reason,
    ) -> None:
        append_jsonl(
            self.log_path,
            {
                "event": "inject",
                "ts": now_ts(),
                "seq": self.state.seq,
                "source": source,
                "uav_id": "UAV-01",
                "type": inject_type,
                "params": params,
                "malicious": True,
                "accepted": accepted,
                "reason": reason,
            },
        )

    def mission_result(self) -> dict[str, Any]:
        return {
            "secure": self.secure,
            "compromised": self.state.compromised,
            "availability": self.state.availability,
            "mode": to_wire(self.state.mode),
            "failsafe_state": to_wire(self.state.failsafe_state),
            "link_quality": self.state.link_quality,
            "distance_true_to_home_m": round(geo.haversine_m(self.state.true_position, self.state.home), 1),
            "distance_reported_to_ins_m": round(geo.haversine_m(self.state.reported_position, self.state.ins_position), 1),
        }
