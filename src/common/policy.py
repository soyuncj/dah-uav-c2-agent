"""Blue-only detection policy. Red agents must not import this module."""
from __future__ import annotations

from common.geo import haversine_m
from common.wire import Detection, FailsafeState, Position, Reason, Rule, Verdict

# Detection thresholds (blue-only knowledge).
GPS_INS_DIVERGENCE_TOLERANCE_M = 50.0
HOME_PIN_TOLERANCE_M = 30.0

# Failsafe modelling constants shared with the simulator so the magic numbers
# live in exactly one place.
LINK_FAILSAFE_THRESHOLD = 0.30
MIN_FAILSAFE_HOLD_S = 3.0
FAILSAFE_GPS_CORR_WINDOW_S = 5.0


def evaluate_telemetry(
    reported: Position,
    ins: Position,
    reported_home: Position,
    pinned_home: Position,
    failsafe: FailsafeState,
    seconds_since_gps_jump: float | None,
) -> Detection:
    gps_ins_distance = haversine_m(reported, ins)
    if gps_ins_distance > GPS_INS_DIVERGENCE_TOLERANCE_M:
        return Detection(
            verdict=Verdict.BLOCK,
            rule=Rule.CROSS_SOURCE_CONSISTENCY,
            reason=Reason.GPS_INS_DIVERGENCE,
            detail=f"reported/INS divergence {gps_ins_distance:.1f}m exceeds tolerance",
        )

    home_distance = haversine_m(reported_home, pinned_home)
    if home_distance > HOME_PIN_TOLERANCE_M:
        return Detection(
            verdict=Verdict.BLOCK,
            rule=Rule.HOME_PIN,
            reason=Reason.HOME_PIN_MISMATCH,
            detail=f"reported home differs from pinned home by {home_distance:.1f}m",
        )

    if (
        failsafe == FailsafeState.TRIGGERED
        and seconds_since_gps_jump is not None
        and seconds_since_gps_jump <= FAILSAFE_GPS_CORR_WINDOW_S
    ):
        return Detection(
            verdict=Verdict.FLAG,
            rule=Rule.FAILSAFE_GPS_CORRELATION,
            reason=Reason.FAILSAFE_GPS_CORRELATION,
            detail="GPS jump occurred shortly after RTL failsafe trigger",
            confidence=0.85,
        )

    return Detection(
        verdict=Verdict.ALLOW,
        rule=Rule.TELEMETRY_BASELINE,
        reason=Reason.OK,
        detail="telemetry remains internally consistent",
        confidence=0.6,
    )
