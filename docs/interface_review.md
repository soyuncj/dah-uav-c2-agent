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

## Note on Injection Endpoints

`POST /api/_inject/link` 및 `POST /api/_inject/gps`는 실제 HTTP 엔드포인트가 아니라 동일 계약(필드/enum 이름)을 표현한 시뮬레이터 메서드(`inject_link_degrade`, `inject_gps_spoof`)이다. 실제 네트워크 공격을 수행하지 않는다.
