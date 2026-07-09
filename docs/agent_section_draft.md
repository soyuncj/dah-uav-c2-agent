# 보고서 §6 초안: 공격·방어 AI 에이전트 설계 및 구현

본 구현은 실제 UAV 또는 실제 RF/GNSS 링크를 대상으로 하지 않고, UAV GCS/C2 신뢰 경계를 추상화한 안전한 mock testbed에서 수행하였다. 목표는 Green-Board Hijack 시나리오에서 red agent와 blue agent가 관측, 판단, 행동, 로그 생성을 수행함을 입증하는 것이다.

## Red Agent

Red agent는 그레이박스 공격자 모델을 따른다. 공용 프로토콜(`wire.py`)의 이벤트 형식과 엔드포인트 의미는 알고 있지만, blue의 탐지 임계값과 정책(`policy.py`)은 알지 못한다. 에이전트 루프는 다음 순서로 동작한다.

1. 현재 telemetry를 관측하여 모드, 링크 품질, home, reported position을 확인한다.
2. 링크 품질을 임계 이하로 낮추는 `link_degrade` 행동을 수행하여 RTL 페일세이프를 유도한다.
3. `gps_spoof` 행동으로 reported position만 편이시켜 오퍼레이터 화면은 정상 복귀 상태처럼 보이게 한다.
4. 각 단계의 관측과 행동 결과를 trace와 JSONL 로그로 저장한다.

## Blue Agent

Blue agent는 가용성 인지 방어를 수행한다. 핵심 원칙은 시스템 전체를 중단하지 않고, 악성 신호만 식별하여 차단하거나 경고하는 것이다. 구현된 탐지 규칙은 다음과 같다.

1. GPS reported position과 INS position의 거리 발산 검사.
2. 보고된 home 좌표와 로컬 pinned home 좌표의 불일치 검사.
3. RTL 페일세이프 직후 GPS 점프가 발생하는 시간 상관 패턴 검사.

Blue agent는 탐지 결과를 `verdict` 이벤트로 기록하며, verdict에는 참조 이벤트 번호, 탐지 규칙, 사유, confidence, availability impact가 포함된다.

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
- `logs/greenboard_secure.jsonl`: 방어 적용 상태에서 spoof가 무효화되고 availability가 유지되는 증거.
