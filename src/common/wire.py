"""Shared protocol vocabulary and JSONL helpers for the DAH mock testbed."""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "v2-stdlib"


class Source(str, Enum):
    OPERATOR = "operator"
    RED_AGENT = "red_agent"
    BLUE_AGENT = "blue_agent"
    SIM = "sim"


class Mode(str, Enum):
    AUTO = "AUTO"
    RTL = "RTL"
    LOITER = "LOITER"


class FailsafeState(str, Enum):
    NOMINAL = "nominal"
    LINK_DEGRADED = "link_degraded"
    TRIGGERED = "triggered"


class InjectType(str, Enum):
    GPS_SPOOF = "gps_spoof"
    GPS_JAM = "gps_jam"
    LINK_DEGRADE = "link_degrade"


class Reason(str, Enum):
    OK = "ok"
    UNAUTHENTICATED = "unauthenticated"
    GPS_INS_DIVERGENCE = "gps_ins_divergence"
    HOME_PIN_MISMATCH = "home_pin_mismatch"
    FAILSAFE_GPS_CORRELATION = "failsafe_gps_correlation"
    GPS_UNAVAILABLE = "gps_unavailable"


class Verdict(str, Enum):
    ALLOW = "allow"
    FLAG = "flag"
    BLOCK = "block"


class Rule(str, Enum):
    AUTH = "auth"
    CROSS_SOURCE_CONSISTENCY = "cross_source_consistency"
    HOME_PIN = "home_pin"
    FAILSAFE_GPS_CORRELATION = "failsafe_gps_correlation"
    LLM_TRIAGE = "llm_triage"


@dataclass(frozen=True)
class Position:
    lat: float
    lon: float
    alt_m: float = 0.0


@dataclass(frozen=True)
class ActionResponse:
    seq: int
    accepted: bool
    reason: Reason
    verdict_by: str | None = "mock_gcs"
    availability_after: int = 100


@dataclass(frozen=True)
class Detection:
    verdict: Verdict
    rule: Rule
    reason: Reason
    detail: str
    confidence: float = 1.0
    availability_impact: int = 0


def now_ts() -> str:
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def to_wire(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {k: to_wire(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {k: to_wire(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_wire(v) for v in value]
    return value


def append_jsonl(path: str | Path, event: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(to_wire(event), ensure_ascii=False, sort_keys=True) + "\n")
