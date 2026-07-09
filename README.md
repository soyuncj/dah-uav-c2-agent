# dah-uav-c2-agent

공방 해커톤

DAH 2026 preliminary prototype for the Green-Board Hijack scenario.

This repository is a safe mock testbed. It does not control a real UAV or attack a real RF/GNSS/C2 system. It models the UAV C2 trust boundary with local Python objects and JSONL logs so the report can show executable red/blue agent evidence.

## Scenario

The red agent performs a stealthy availability-preserving attack:

1. Read the current telemetry.
2. Degrade the C2 link just enough to trigger RTL failsafe.
3. Spoof GPS by moving only the reported position while the INS estimate remains stable.
4. Keep the operator board green while the true mission state is compromised.

The blue agent watches telemetry and verdicts:

1. GPS versus INS divergence.
2. Home pin mismatch.
3. Failsafe and GPS jump time correlation.
4. Availability-preserving block/flag actions.

## Run

```bash
PYTHONPATH=src python3 -m demo.run_greenboard
```

Expected summary:

- `SECURE=false`: attack succeeds, availability stays high, and the board appears green.
- `SECURE=true`: blue detects and neutralizes the GPS spoof while preserving normal telemetry availability.

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Structure

```text
src/common/wire.py       shared protocol vocabulary and JSONL helpers
src/common/geo.py        shared geographic math
src/common/policy.py     blue-only detection policy
src/mock_gcs/simulator.py local mock GCS/UAV simulator
src/red_agent/agent.py   red agent tool loop
src/blue_agent/agent.py  blue agent verdict loop
src/demo/run_greenboard.py reproducible scenario runner
docs/agent_section_draft.md report section draft
docs/interface_review.md contract review notes
```

## Limitations

- The prototype uses a local simulator instead of FastAPI endpoints to avoid deadline and dependency risk.
- `POST /api/_inject/link` and `POST /api/_inject/gps` are represented as simulator methods with the same request meaning.
- `wire.py` mirrors the submitted interface fields but uses Python dataclasses instead of Pydantic because the local environment does not have Pydantic installed.
