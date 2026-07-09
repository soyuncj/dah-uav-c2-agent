# 제출 증거 정리

## GitHub

- Repository: https://github.com/soyuncj/dah-uav-c2-agent
- Branch: `main`

## 실행 명령

```bash
PYTHONPATH=src python3 -m demo.run_greenboard
```

## 테스트 명령

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## 데모 결과 요약

| 모드 | 공격 결과 | 방어 결과 | 가용성 |
|---|---|---|---|
| `SECURE=false` | `compromised=true`, `operator_deceived=true`, reported/true 불일치 645.6m 유지 | blue verdict `block`은 기록되지만 집행되지 않음 | 100 |
| `SECURE=true` | `compromised=false`, blue verdict 집행 후 reported position 롤백 | action verdict는 `block`, 후속 telemetry verdict는 `flag` | 100 |

## 로그 증거

- `logs/greenboard_insecure.jsonl`
  - `link_degrade` injection accepted.
  - `gps_spoof` injection accepted.
  - `mode=RTL`, `failsafe_state=triggered`.
  - `reported_position`과 `true_position`의 괴리가 유지되어 operator deception이 발생.
  - blue verdict는 기록되지만 방어 집행이 비활성화되어 mission이 계속 오염됨.

- `logs/greenboard_secure.jsonl`
  - `link_degrade`로 RTL 페일세이프 조건 재현.
  - `gps_spoof` injection 자체는 수행되지만, blue verdict가 `block`을 내리고 simulator가 이를 집행한다.
  - `reported_position`과 `ins_position` 발산이 롤백 후 0.0m가 된다.
  - 페일세이프 직후 GPS jump 상관관계도 후속 telemetry verdict `flag`로 기록된다.

## 공격-방어 추적 매트릭스

| 공격 단계 | 관측 신호 | 방어 통제 | AI agent 역할 | 증거 |
|---|---|---|---|---|
| telemetry 정찰 | `GET /api/telemetry` 의미의 state read | 정상 telemetry 유지 | red: 현재 모드/좌표 관측 | red trace 1단계, JSONL telemetry |
| 링크 열화 | `link_quality<0.30`, `failsafe_state=triggered` | 지속 DoS가 아닌 RTL 상태 관찰 | red: 재시도 포함 `link_degrade` 수행, blue: telemetry 연속 검사 | `logs/*` inject + telemetry |
| GPS spoof | reported position만 편이 | GPS-INS 교차출처 정합성 검사 | red: `gps_spoof`, blue: divergence 탐지 | insecure/secure log verdict |
| green-board 유지 | `availability=100`, `mode=RTL` | 정상 흐름 차단 없이 악성 신호만 판단 | blue: availability impact 0 verdict | demo summary |
| secure 대응 | blue `block` verdict 후 simulator rollback | spoof 무효화 + 후속 telemetry `flag` 기록 | blue: 판정, simulator: 집행 | secure log verdict sequence |

## 보고서에 쓸 한 문장

본 프로토타입은 실제 UAV/RF/GNSS 시스템을 대상으로 하지 않고, UAV C2 신뢰 경계를 추상화한 mock testbed에서 Green-Board Hijack 공격과 가용성 보존형 blue agent 대응을 재현한다. 데모는 `SECURE=false`에서 operator deception 기반 임무 오염이 유지되고, `SECURE=true`에서 blue verdict가 simulator에 집행되어 GPS spoof가 롤백되며 availability가 100으로 유지됨을 JSONL 로그와 테스트로 입증한다.
