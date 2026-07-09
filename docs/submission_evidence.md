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
| `SECURE=false` | `compromised=true`, `operator_deceived=true`, reported-true 불일치 645.6m 유지 | blue verdict `block`은 기록되지만 집행되지 않음 | 85 (링크 열화, 제어권 유지) |
| `SECURE=true` | `compromised=false`, blue verdict 집행 후 reported-INS 롤백 | action verdict `block`, 후속 telemetry verdict `flag`, `availability_impact=0` | 85 (blue 대응이 가용성 추가 훼손 없음) |

참고: blue 탐지 신호(reported-INS 637.9m)와 정답 라벨(reported-true 645.6m)은 INS 편이 때문에 서로 다른 값이며, secure 롤백 후 잔여 reported-true는 8.0m(모델링된 INS 편이)로 탐지 임계(50m) 미만이다. 다만 현재 INS는 true position의 고정 평행이동이므로 완전히 독립적인 관측원이라고 주장하지 않는다.

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

| 공격 단계 | 관측 신호 | 방어 통제 | 탐지 규칙/임계 | 통제가 실패하는 조건 | AI agent 역할 | 증거 |
|---|---|---|---|---|---|---|
| telemetry 정찰 | state read (`GET /api/telemetry` 의미) | 정상 telemetry 유지 | 상태 관찰 | 해당 없음 | red: 모드/좌표 관측 | red trace 1단계, JSONL telemetry |
| 링크 열화 -> RTL 유도 | `link_quality<0.30`, `failsafe=triggered`, `mode=RTL` | 지속 DoS 아님을 관찰, 페일세이프 정상 처리 | 임계 0.30/3.0s | 링크 열화를 정상 RTL과 구분하기 어려울 때 | red: 재시도 포함 `link_degrade`, blue: telemetry 연속 검사 | `logs/*` inject + telemetry |
| GPS spoof (reported만 편이) | reported-INS 637.9m 발산 | 교차출처 정합성 검사 후 block + 롤백 | `>50m` -> block | INS 드리프트가 임계 근처일 때(현 데모는 무노이즈) | red: `gps_spoof`, blue: divergence 탐지 | insecure/secure log verdict |
| home 재지정 시도 | reported_home-pinned_home 편차 | home-pin 무결성 검사 | `>30m` -> block | pinned_home 자체가 오염된 경우 | blue: home 무결성 판정 | policy 유닛테스트 |
| green-board 유지 | `mode=RTL`, 보안경보 없음, availability 85 | 정상 흐름 차단 없이 악성 신호만 판단 | `availability_impact=0` | "green"이 RTL 배너로 노출될 때(무경보 정의로 한정) | blue: availability 무손실 verdict | demo summary |
| secure 대응 | blue `block` verdict 후 simulator rollback | spoof 무효화 + 후속 telemetry `flag` 기록 | window 5s -> flag | GPS jump가 상관 윈도 밖일 때 미탐 | blue: 판정, simulator: 집행 | secure log verdict sequence |

## 한계 및 본선 확장

- 본 데모는 임계(50m)를 크게 초과하는 gross-spoof(약 645m)에 대한 탐지·복구를 시연한다. 임계 근처 spoof는 policy 유닛테스트에서 45m allow, 55m block으로 경계를 검증하며, 점진 드리프트/probing 시나리오는 본선 확장 항목으로 둔다.
- 현 INS는 true position에 약 8m 고정 편이를 준 모델이다. 이는 `INS=true`였던 초기 순환 구조를 완화하지만, 독립 관측원 모델은 아니다. 시간에 따른 INS 드리프트·센서 노이즈와 임계값 tradeoff는 본선 확장 과제로 관리한다.
- availability는 100/85/40 세 등급으로 모델링한다. 데모는 제어권 유지 상태인 85를 사용하며, 링크 상실 등급(40, `mission_continuity=false`)은 별도 유닛테스트로 검증한다.

## 보고서에 쓸 한 문장

본 프로토타입은 실제 UAV/RF/GNSS 시스템을 대상으로 하지 않고, UAV C2 신뢰 경계를 추상화한 mock testbed에서 Green-Board Hijack 공격과 가용성 보존형 blue 에이전트 대응을 재현한다. 데모는 `SECURE=false`에서 operator deception 기반 임무 오염(reported-true 645.6m)이 유지되고, `SECURE=true`에서 blue verdict가 simulator에 집행되어 GPS spoof가 INS 기준으로 롤백되며(잔여 8.0m, 탐지 임계 미만) 링크 열화 하에서도 제어권과 임무 지속성이 유지됨을 JSONL 로그와 11개 단위·시나리오 테스트로 입증한다. 이때 blue의 탐지 신호(reported-INS)는 정답 라벨(reported-true)과 값이 다르지만, 현 INS는 true position의 고정 편이 모델이므로 완전 독립 관측원은 아니며 드리프트·노이즈 모델링은 본선 확장 과제로 둔다.

## 참고문헌

1. MAVLink Developer Guide, `common.xml` message set: `GPS_RAW_INT`, `GLOBAL_POSITION_INT`, telemetry protocol vocabulary. https://mavlink.io/en/messages/common.html
2. PX4 User Guide, Safety/Failsafe configuration. https://docs.px4.io/main/en/config/safety
3. ArduPilot Copter Documentation, Radio Failsafe. https://ardupilot.org/copter/docs/radio-failsafe.html
4. University of Texas at Austin News, "UT Austin Researchers Successfully Spoof an $80 million Yacht at Sea" (2013). https://news.utexas.edu/2013/07/29/ut-austin-researchers-successfully-spoof-an-80-million-yacht-at-sea/
