# Interface Contract Review

## Conclusion

The v2 contract is sufficient for a preliminary-round red/blue agent prototype if the implementation stays focused on Green-Board Hijack.

## What Changed

- The main attack is no longer command injection.
- The core attack surface is telemetry/link injection:
  - link degradation triggers RTL failsafe.
  - GPS spoof changes reported position only.
  - INS and true position remain separate so blue can detect internal inconsistency.
- Red can import `wire.py` only.
- Blue/mock GCS can import `policy.py`.

## Minimum Acceptance Mapping

| Requirement | Prototype Evidence |
|---|---|
| SECURE=false attack succeeds | `logs/greenboard_insecure.jsonl`, `compromised=true` |
| SECURE=true or blue blocks spoof | `logs/greenboard_secure.jsonl`, blue verdict |
| Availability preserved | summary `availability=100` |
| Red/blue agent loop exists | red trace and blue verdict events |

## Risk

The supplied `wire.py` uses Pydantic, but this local environment does not have Pydantic installed. The prototype uses dataclasses while preserving enum names and JSON field names.
