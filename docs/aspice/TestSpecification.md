# Test Specification

문서 ID: `BEOG-TS-001`

상세 54개 절차와 Jira import 필드는 `docs/jira_export`의 생성 결과를 기준으로
한다. 이 문서는 공통 시험 설계와 오라클 규칙을 정의한다.

## 공통 설계 기법

- Boundary value: threshold-1, threshold, threshold+1 및 clear 경계.
- Equivalence partition: valid standard CAN과 DLC/Extended/RTR/unknown 분리.
- Decision table: EVSE charge 조건 6개 boolean의 64조합 전수.
- State transition: BMS/EVSE/OTA의 invalid transition과 fault convergence.
- Fault injection: link silence, bus-off, CRC corruption, reset, 승인된 power loss.
- Back-to-back: 제품 C 함수 결과와 독립 oracle 결과를 동일 vector로 비교.

## 공통 절차

1. 제품/QA SHA, tool version, target ID와 config hash를 기록한다.
2. precondition을 독립 측정하고 충족되지 않으면 `BLOCKED_INFRA`로 종료한다.
3. 단일 제어 자극을 인가하고 timestamp를 기록한다.
4. expected를 제품 로그가 아닌 SWRS/ICD 오라클로 계산한다.
5. logical command, MCU GPIO, 실제 output 중 요구된 계층을 관찰한다.
6. target을 안전상태로 복원하고 raw log/JUnit/metadata를 artifact로 보존한다.

## P0 대표 안전 시험

| Test | 자극 | 독립 오라클 | 필수 증거 |
|---|---|---|---|
| TC-BMS-OV-001..004 | cell 4200/4201 및 clear 4150/4149 | strict 비교 + 3회 confirm/3000 ms clear | sample trace, fault bits, permit |
| TC-BMS-PERMIT-001 | critical mask 각 bit/조합 | any critical → permit false | input mask/output |
| TC-EVSE-SAFE-004 | charging 중 0x100 중단 | last RX+>500 ms → PE11 LOW | raw CAN timestamps, GPIOE ODR |
| TC-CAN-E2E-003 | approved critical fault | fault→permit0→EVSE OFF 순서 | dual ECU log + PE11/fixture |
| TC-OTA-CRC-001 | valid-format image, wrong CRC32 | END_UPDATE reject, vector remains erased | UART frames, flash readback |

## False-PASS 방지 규칙

- `0x200 data[1]=0`은 relay command일 뿐 PE11/contactor OFF의 증명이 아니다.
- HIL metadata에 SHA 문자열만 기록하는 것은 target 동일성 검증이 아니다.
  ELF/BIN hash와 flash verify가 있어야 한다.
- HardFault CFSR/HFSR를 출력만 하고 0인지 assertion하지 않으면 PASS할 수 없다.
- 결과 판정 전에 target을 resume하거나 증거 레지스터를 덮어쓰지 않는다.
- 요구사항 GAP test는 skip/GAP으로 가시화하고 예상 PASS로 취급하지 않는다.

## Test code mapping

- BMS: `tests/host/bms`, `hil/tests/test_can_timeout.py`, `test_safe_state.py`
- EVSE/CAN: `tests/host/evse`, `hil/tests/test_can_*.py`
- OTA: `tests/host/ota`, `hil/tests/test_ota_*.py`
- Infra/Gateway/GAP: `tests/quality`
