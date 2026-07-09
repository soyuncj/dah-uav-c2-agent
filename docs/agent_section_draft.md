# 보고서 §6 초안: 공격·방어 AI 에이전트 설계 및 구현

본 구현은 실제 UAV 또는 실제 RF/GNSS 링크를 대상으로 하지 않고, UAV GCS/C2 신뢰 경계를 추상화한 안전한 mock testbed에서 수행하였다. 목표는 Green-Board Hijack 시나리오에서 red agent와 blue agent가 관측, 판단, 행동, 로그 생성을 수행함을 입증하는 것이다.

## Red Agent

Red agent는 그레이박스 공격자 모델을 따른다. 공용 프로토콜(`wire.py`)의 이벤트 형식과 엔드포인트 의미는 알고 있지만, blue의 탐지 임계값과 정책(`policy.py`)은 알지 못한다. 에이전트는 OODA(관측-판단-결정-행동) 루프를 따른다.

1. 현재 telemetry를 관측하여 모드, 링크 품질, home, reported position을 확인한다.
2. `link_degrade` 후 telemetry를 다시 읽어 `failsafe_state`가 실제로 `triggered`되었는지 확인하고, 실패 시 더 강한 링크 열화 파라미터로 재시도한다.
3. RTL 발동 이후 `gps_spoof`를 수행하고, 이후 telemetry를 다시 관측하여 spoof가 유지되었는지 또는 방어 verdict로 롤백되었는지 판단한다.
4. 각 단계의 관측, 계획, 결정, 행동 결과를 trace와 JSONL 로그로 저장한다.

## Blue Agent

Blue agent는 가용성 인지 방어를 수행한다. 핵심 원칙은 시스템 전체를 중단하지 않고, 악성 신호만 식별하여 차단하거나 경고하는 것이다. 구현된 탐지 규칙은 다음과 같다.

1. GPS reported position과 INS position의 거리 발산 검사.
2. 보고된 home 좌표와 로컬 pinned home 좌표의 불일치 검사.
3. RTL 페일세이프 직후 GPS 점프가 발생하는 시간 상관 패턴 검사.

Blue agent는 telemetry 이벤트를 연속적으로 검사하고, 탐지 결과를 `verdict` 이벤트로 기록한다. verdict에는 참조 이벤트 번호, 탐지 규칙, 사유, confidence, availability impact가 포함되며, `block` verdict는 simulator가 집행하여 spoof된 reported position을 INS 기준으로 롤백한다.

## Evidence

실행 명령:

```bash
PYTHONPATH=src python3 -m demo.run_greenboard
```

검증 명령:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

산출 로그:

- `logs/greenboard_insecure.jsonl`: 방어 미적용 상태에서 링크 열화와 GPS spoof가 수용되어 임무 오염이 발생하는 증거.
- `logs/greenboard_secure.jsonl`: blue verdict가 simulator에 집행되어 spoof가 롤백되고 availability가 유지되는 증거.
