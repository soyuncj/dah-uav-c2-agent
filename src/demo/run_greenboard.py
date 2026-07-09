"""Run the Green-Board Hijack demo in insecure and secure modes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from blue_agent.agent import BlueAgent
from mock_gcs.simulator import MockGCS
from red_agent.agent import RedAgent


class ObservedTarget:
    def __init__(self, gcs: MockGCS, blue: BlueAgent, enforce_blue: bool) -> None:
        self.gcs = gcs
        self.blue = blue
        self.enforce_blue = enforce_blue
        self.verdicts: list[dict[str, Any]] = []

    def telemetry(self) -> dict[str, Any]:
        full_event = self.gcs.telemetry(include_true=True)
        verdict = self.blue.inspect_telemetry(full_event)
        self.verdicts.append(verdict)
        if self.enforce_blue:
            self.gcs.apply_blue_verdict(verdict)
        red_view = dict(full_event)
        red_view.pop("true_position")
        return red_view

    def inject_link_degrade(self, quality: float, hold_s: float, source: Any) -> Any:
        return self.gcs.inject_link_degrade(quality=quality, hold_s=hold_s, source=source)

    def inject_gps_spoof(
        self,
        offset_m_north: float,
        offset_m_east: float,
        rate_m_s: float,
        source: Any,
    ) -> Any:
        return self.gcs.inject_gps_spoof(
            offset_m_north=offset_m_north,
            offset_m_east=offset_m_east,
            rate_m_s=rate_m_s,
            source=source,
        )


def run_case(secure: bool, log_path: Path) -> dict:
    gcs = MockGCS(secure=secure, log_path=log_path)
    blue = BlueAgent(pinned_home=gcs.state.home, log_path=log_path)
    target = ObservedTarget(gcs=gcs, blue=blue, enforce_blue=secure)
    red = RedAgent(target)
    red_trace = red.run_greenboard_hijack()
    telemetry = gcs.telemetry(include_true=True)
    verdict = blue.inspect_telemetry(telemetry)
    target.verdicts.append(verdict)
    if secure:
        gcs.apply_blue_verdict(verdict)
    action_verdict = _select_action_verdict(target.verdicts)
    return {
        "secure": secure,
        "mission": gcs.mission_result(),
        "blue_verdict": action_verdict,
        "blue_last_verdict": verdict,
        "blue_verdict_count": len(target.verdicts),
        "red_trace_steps": len(red_trace["trace"]),
    }


def _select_action_verdict(verdicts: list[dict[str, Any]]) -> dict[str, Any]:
    for candidate in verdicts:
        if candidate["verdict"] == "block":
            return candidate
    for candidate in verdicts:
        if candidate["verdict"] == "flag":
            return candidate
    return verdicts[-1]


def main() -> None:
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    insecure_log = logs_dir / "greenboard_insecure.jsonl"
    secure_log = logs_dir / "greenboard_secure.jsonl"
    insecure_log.write_text("", encoding="utf-8")
    secure_log.write_text("", encoding="utf-8")

    insecure = run_case(secure=False, log_path=insecure_log)
    secure = run_case(secure=True, log_path=secure_log)
    summary = {"insecure": insecure, "secure": secure}
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
