# dah-uav-c2-agent

DAH 2026 공방 해커톤 예선용 UAV C2 공격·방어 에이전트 프로토타입입니다.

이 저장소는 Green-Board Hijack 시나리오를 안전하게 재현하기 위한 mock testbed입니다.
실제 UAV를 제어하거나 실제 RF/GNSS/C2 시스템을 공격하지 않습니다.
로컬 Python 객체와 JSONL 로그로 UAV C2 신뢰 경계를 모델링하여, 보고서에 넣을 수 있는 red/blue agent 실행 증거를 생성합니다.

## 시나리오

red agent는 가용성을 유지하면서 은밀하게 임무를 오염시키는 공격을 수행합니다.

1. 현재 telemetry를 조회합니다.
2. C2 링크 품질을 RTL 페일세이프가 발동될 정도로만 낮춥니다.
3. INS 추정 위치는 유지한 채 reported position만 이동시키는 GPS spoof를 수행합니다.
4. 실제 임무 상태는 오염되지만, 오퍼레이터 화면은 정상처럼 보이게 유지합니다.

blue agent는 telemetry와 verdict를 관찰하며 다음 항목을 검사합니다.

1. GPS reported position과 INS position의 발산 여부.
2. home 좌표와 pinned home 좌표의 불일치 여부.
3. 페일세이프 발동과 GPS jump 사이의 시간 상관관계.
4. 가용성을 보존하는 block/flag 대응과 spoof 롤백 집행.

## 실행

```bash
PYTHONPATH=src python3 -m demo.run_greenboard
```

예상 요약:

- `SECURE=false`: 공격이 성공하고, availability는 높게 유지되며, operator deception 상태가 남습니다.
- `SECURE=true`: blue가 GPS spoof를 탐지하고 simulator가 그 verdict를 집행해 reported position을 롤백합니다.

## 테스트

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## 구조

```text
src/common/wire.py        공용 프로토콜 어휘와 JSONL 헬퍼
src/common/geo.py         공용 지리 계산 함수
src/common/policy.py      blue 전용 탐지 정책
src/mock_gcs/simulator.py 로컬 mock GCS/UAV 시뮬레이터
src/red_agent/agent.py    red agent 도구 실행 루프
src/blue_agent/agent.py   blue agent verdict 생성 루프
src/demo/run_greenboard.py 재현 가능한 시나리오 실행기
docs/agent_section_draft.md 보고서 섹션 초안
docs/interface_review.md    인터페이스 검토 메모
```

## 한계

- 마감일과 의존성 리스크를 줄이기 위해 FastAPI 엔드포인트 대신 로컬 시뮬레이터를 사용합니다.
- `POST /api/_inject/link`, `POST /api/_inject/gps`는 같은 의미를 가진 시뮬레이터 메서드로 표현했습니다.
- 제출 인터페이스의 필드와 enum 이름은 유지했지만, 로컬 환경에 Pydantic이 설치되어 있지 않아 `wire.py`는 Python dataclass 기반으로 구현했습니다.
- 본 testbed는 MAVLink telemetry stream의 논리적 신뢰 경계만 모델링하며, RF 물리 계층과 수신기 하드웨어 취약점은 범위 밖입니다.
- 현재 blue agent는 규칙 기반 탐지와 verdict 집행까지 구현되어 있으며, LLM triage는 본선 확장 항목으로 남겨두었습니다.
