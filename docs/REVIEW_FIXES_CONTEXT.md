# 리뷰 반영 변경 컨텍스트

## 변경 요약

| ID | 문제 | 조치 | 파일 |
|---|---|---|---|
| P0-1 | 정답 라벨과 blue 탐지가 같은 계산이라 탐지가 정의상 100% 정확 | INS에 모델링된 편이 약 8m 부여 | `src/mock_gcs/simulator.py`, `tests/` |
| P0-2 | availability가 사실상 상수 | 링크 품질 등급 함수 100/85/40 및 `mission_continuity` 추가 | `src/mock_gcs/simulator.py`, `tests/`, docs |
| P0-3 | "AI 에이전트/OODA" 과장 | "자율 규칙기반 에이전트"로 리프레이밍, LLM 확장 슬롯 명시 | `README.md`, `docs/agent_section_draft.md` |
| P1-1 | "green board"인데 `mode=RTL` 노출 | green을 보안 무경보 상태로 정의 축소 | `README.md`, `docs/agent_section_draft.md` |
| P1-2 | 성공 경로만 테스트 | ALLOW 베이스라인 및 INS 편이 무오탐 테스트 추가 | `tests/test_greenboard.py` |
| P1-3 | adaptive retry가 데모에서 1회만 발동 | 구현과 데모 서술을 분리해 문구 정정 | `docs/agent_section_draft.md` |
| P1-4 | dead 상수와 중복 매직넘버 | `policy`에 `LINK_FAILSAFE_THRESHOLD`, `MIN_FAILSAFE_HOLD_S` 공유 상수화 | `src/common/policy.py`, `src/mock_gcs/simulator.py` |
| 2차 P1-1 | 문서가 "탐지 신호 독립"을 과장 | "고정 편이로 순환 완화, 완전 독립은 아님"으로 문구 수정 | `README.md`, `docs/` |
| 2차 P1-2 | gross-spoof만 검증 | 45m allow / 55m block 경계 테스트 추가 | `tests/test_greenboard.py` |
| 2차 P1-3 | 참고문헌 부족 | MAVLink/PX4/ArduPilot/GNSS spoofing 참고문헌 추가 | `README.md`, `docs/submission_evidence.md` |
| 2차 P1-4 | availability 40 분기 미검증 | link loss tier 유닛테스트 추가 | `tests/test_greenboard.py` |

## 핵심 설계 변경

시뮬레이터는 `reported`, `ins`, `true` 세 위치를 유지한다. `ins_position`은 `true_position`에서 북쪽으로 약 8m 편이를 갖도록 초기화한다. 따라서 blue의 탐지 신호인 `reported`와 `INS`의 발산은 정답 라벨인 `reported`와 `true`의 발산과 다른 값이다. 단, 현 INS는 true position의 고정 평행이동이므로 완전히 독립적인 관측원이라고 주장하지 않는다.

가용성은 링크 품질의 함수다. `link_quality >= 0.30`이면 100, `0.05 < link_quality < 0.30`이면 85, `link_quality <= 0.05`이면 40이다. 데모의 링크 열화는 0.25이므로 RTL은 발동하지만 `mission_continuity`는 유지된다.

blue의 `block` verdict는 simulator가 집행한다. 집행 시 spoof된 `reported_position`을 `ins_position`으로 롤백하고, ground-truth compromise 상태는 `true_position` 기준으로 다시 계산한다.

## 검증 기대값

```text
Ran 11 tests ... OK
```

데모 핵심 수치:

| 지표 | insecure | secure |
|---|---|---|
| compromised | true | false |
| operator_deceived | true | false |
| availability | 85 | 85 |
| mission_continuity | true | true |
| reported-INS | 약 637.9m | 0.0m |
| reported-true | 약 645.6m | 약 8.0m |
| 방어 verdict | block 기록, 미집행 | block 집행 및 후속 flag |

## 남은 TODO

- spoof가 아직 큰 단일 점프라 탐지가 자명하다. ramp-up/probing 공격으로 확장하면 은밀성 서사가 더 강해진다.
- INS는 고정 편이만 모델링한다. 드리프트와 센서 노이즈를 추가하면 방어 임계값 논의가 더 설득력 있어진다.
- 보고서 최종본에는 MITRE ATT&CK for ICS 또는 유사 프레임워크 매핑을 추가하면 공격 시나리오 설명이 강해진다.
