"""Run the Green-Board Hijack demo in insecure and secure modes."""
from __future__ import annotations

import json
from pathlib import Path

from blue_agent.agent import BlueAgent
from mock_gcs.simulator import MockGCS
from red_agent.agent import RedAgent


def run_case(secure: bool, log_path: Path) -> dict:
    gcs = MockGCS(secure=secure, log_path=log_path)
    red = RedAgent(gcs)
    red_trace = red.run_greenboard_hijack()
    telemetry = gcs.telemetry(include_true=True)
    blue = BlueAgent(pinned_home=gcs.state.home, log_path=log_path)
    verdict = blue.inspect_telemetry(telemetry)
    return {
        "secure": secure,
        "mission": gcs.mission_result(),
        "blue_verdict": verdict,
        "red_trace_steps": len(red_trace["trace"]),
    }


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
