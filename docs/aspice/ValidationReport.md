# Validation Report Template

문서 ID: `BEOG-VR-001`
실행 상태: NOT EXECUTED — framework delivery

## Baseline

| 항목 | 값 |
|---|---|
| QA commit | `<CI_COMMIT_SHA>` |
| BMS commit | `<full SHA>` |
| EVSE commit | `<full SHA>` |
| OTA commit | `<full SHA>` |
| Artifact SHA-256 | `<per target>` |
| Target identity | `<MCU ID / probe serial / flash verify>` |
| Runner | `<description / tags / image digest>` |

## Summary

| 분류 | 수량 |
|---|---:|
| PASS | 0 |
| FAIL_PRODUCT | 0 |
| GAP_REQUIREMENT | 0 |
| FAIL_TEST | 0 |
| BLOCKED_INFRA | 0 |
| MISMATCH_CONFIGURATION | 0 |
| NOT_APPLICABLE | 54 |

이 표의 초기값은 코드가 생성되었다는 사실을 시험 PASS로 오해하지 않기 위한
것이다. 파이프라인/HIL 결과를 import한 뒤에만 갱신한다.

## Deviations / findings

| ID | 관찰 | 예상 분류 | 조치 |
|---|---|---|---|
| DEV-BMS-LINK-001 | 현재 구현은 1000 ms timeout 판정 뒤 공통 3회 confirm을 적용할 가능성이 있어 1000 ms 요구보다 늦을 수 있음 | FAIL_PRODUCT 후보 | HIL timestamp로 판정, 요구 변경으로 숨기지 않음 |
| DEV-OTA-CANON-001 | standalone EVSE_BOOT와 ota-platform 복사본의 기능/flash layout이 다름 | MISMATCH_CONFIGURATION | canonical을 ota-platform 경로로 고정 |
| DEV-EVSE-ACT-001 | EVSE 후보 SHA는 relay/CAN actuation이 활성화될 수 있음 | BLOCKED_INFRA | hard interlock 및 승인 전 flash 금지 |
| DEV-SEC-001 | EVSE source configuration에 자격증명 평문 저장 위험 | FAIL_PRODUCT 후보 | secret rotation/CI secret scan; 값은 보고서에 재출력 금지 |
| DEV-OTA-GAP-001 | signature, version/anti-rollback, target binding, rollback 미완 | GAP_REQUIREMENT | SWRS-OTA-007..009 승인/구현 |

## Per-test evidence

각 행에는 Test ID, Requirement ID, result classification, duration, measured value,
product/QA SHA, artifact SHA, target identity, raw log/JUnit 링크와 deviation ID를
기록한다. 자동 생성 RTM의 실행 열을 공식 결과와 함께 갱신한다.

## QA approval

- Prepared by: `<QA/QC>`
- Requirement owner approval: `<name/date>`
- Safety/HIL approval: `<name/date>`
- Release recommendation: `<GO / CONDITIONAL / NO-GO>`
