# dah-uav-c2-agent

DAH 2026 공방 해커톤 예선용 UAV C2 공격·방어 에이전트 프로토타입입니다.

이 저장소는 Green-Board Hijack 시나리오를 안전하게 재현하기 위한 mock testbed입니다.
실제 UAV를 제어하거나 실제 RF/GNSS/C2 시스템을 공격하지 않습니다.
로컬 Python 객체와 JSONL 로그로 UAV C2 신뢰 경계를 모델링하여, 보고서에 넣을 수 있는 red/blue 에이전트 실행 증거를 생성합니다.

에이전트는 관측-판단-행동-로깅 루프를 갖춘 **자율 규칙기반(rule-based) 에이전트**입니다.
현 예선 구현은 결정론적 정책으로 동작하며 머신러닝/LLM 추론은 포함하지 않습니다.
정책 계층은 교체 가능한 triage 모듈로 분리되어 있어 본선에서 LLM 기반 이상 판정으로 확장 가능합니다.

## "Green-Board"의 정의

여기서 "green board(초록불 유지)"는 모든 지표가 완전 정상(nominal)이라는 뜻이 아닙니다.
링크 열화로 RTL 페일세이프가 발동하므로 `mode=RTL`은 오퍼레이터 화면에 보입니다.
핵심은 오퍼레이터에게 보안 침해(위치 위조)를 알리는 신호가 없고, RTL이 정상 복귀로 오인되어 임무가 조용히 오염된다는 점입니다.

## 시나리오

red 에이전트는 가용성을 크게 훼손하지 않으면서 은밀하게 임무를 오염시키는 공격을 수행합니다.

1. 현재 telemetry를 조회합니다.
2. C2 링크 품질을 RTL 페일세이프가 발동될 정도로만 낮춥니다.
3. INS 추정 위치는 유지한 채 reported position만 이동시키는 GPS spoof를 수행합니다.
4. 실제 임무 상태는 오염되지만, 보안 경보 없이 화면은 정상 복귀처럼 보이게 유지합니다.

blue 에이전트는 telemetry와 verdict를 관찰하며 다음 항목을 검사합니다.

1. GPS reported position과 INS position의 발산 여부.
2. home 좌표와 pinned home 좌표의 불일치 여부.
3. 페일세이프 발동과 GPS jump 사이의 시간 상관관계.
4. 가용성을 보존하는 block/flag 대응과 spoof 롤백 집행.

## 신뢰 모델과 탐지 한계

INS는 무오차 기준이 아니라 모델링된 편이(bias, 약 8m)를 가집니다.
따라서 blue가 보는 신호(reported-INS)는 정답 라벨(reported-true)과 다른 값입니다.
이는 `INS=true`였던 초기 순환 구조를 완화하기 위한 설계입니다.
다만 현 INS는 true position의 고정 편이 버전이므로 완전히 독립적인 관측원이라고 주장하지 않습니다.
현 데모는 무노이즈 조건이며, 현실에서는 INS 드리프트 하의 임계값과 노이즈 tradeoff가 핵심 과제입니다.

## 가용성 모델

가용성은 링크 품질의 등급 함수입니다.
`link_quality >= 0.30`이면 100, 열화 구간(0.05~0.30)에서는 85(RTL 발동, 제어권 유지), `link_quality <= 0.05`이면 40(사실상 링크 상실)입니다.
"가용성 보존"은 완전 셧다운 없이 제어권과 임무 지속성(mission continuity)을 유지함을 의미하며, blue의 block 대응은 spoof를 무효화하되 가용성을 추가로 훼손하지 않습니다(`availability_impact=0`).

## 실행

```bash
PYTHONPATH=src python3 -m demo.run_greenboard
```

예상 요약:

- `SECURE=false`: 공격이 성공하고(compromised, operator_deceived), availability는 85로 유지되며 operator deception 상태가 남습니다.
- `SECURE=true`: blue가 GPS spoof를 탐지하고 simulator가 그 verdict를 집행해 reported position을 INS 기준으로 롤백합니다.

## 테스트

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## 구조

```text
src/common/wire.py        공용 프로토콜 어휘와 JSONL 헬퍼
src/common/geo.py         공용 지리 계산 함수
src/common/policy.py      blue 전용 탐지 정책(공유 임계 상수 포함)
src/mock_gcs/simulator.py 로컬 mock GCS/UAV 시뮬레이터
src/red_agent/agent.py    red 에이전트 도구 실행 루프
src/blue_agent/agent.py   blue 에이전트 verdict 생성 루프
src/demo/run_greenboard.py 재현 가능한 시나리오 실행기
docs/agent_section_draft.md 보고서 섹션 초안
docs/interface_review.md    인터페이스 검토 메모
```

## 한계

- 마감일과 의존성 리스크를 줄이기 위해 FastAPI 엔드포인트 대신 로컬 시뮬레이터를 사용합니다.
- `POST /api/_inject/link`, `POST /api/_inject/gps`는 실제 HTTP 엔드포인트가 아니라 동일 계약을 표현한 시뮬레이터 메서드입니다.
- 제출 인터페이스의 필드와 enum 이름은 유지했지만, 로컬 환경에 Pydantic이 설치되어 있지 않아 `wire.py`는 Python dataclass 기반으로 구현했습니다.
- 본 testbed는 MAVLink telemetry stream의 논리적 신뢰 경계만 모델링하며, RF 물리 계층과 수신기 하드웨어 취약점은 범위 밖입니다.
- INS는 고정 편이만 모델링하며 시간에 따른 드리프트/센서 노이즈는 범위 밖입니다.
- 데모 spoof는 임계(50m)를 크게 초과하는 gross-spoof이며, 임계 근처 회피형 spoof는 policy 유닛테스트로 경계만 검증합니다.
- 현재 blue 에이전트는 규칙 기반 탐지와 verdict 집행까지 구현되어 있으며, LLM triage는 본선 확장 항목으로 남겨두었습니다.

## 참고문헌

- MAVLink Developer Guide, `common.xml` message set: `GPS_RAW_INT`, `GLOBAL_POSITION_INT`, telemetry protocol vocabulary. https://mavlink.io/en/messages/common.html
- PX4 User Guide, Safety/Failsafe configuration. https://docs.px4.io/main/en/config/safety
- ArduPilot Copter Documentation, Radio Failsafe. https://ardupilot.org/copter/docs/radio-failsafe.html
- University of Texas at Austin News, "UT Austin Researchers Successfully Spoof an $80 million Yacht at Sea" (2013). https://news.utexas.edu/2013/07/29/ut-austin-researchers-successfully-spoof-an-80-million-yacht-at-sea/
