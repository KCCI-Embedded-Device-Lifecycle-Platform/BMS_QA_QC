# Verification Test Plan

문서 ID: `BEOG-TP-001`
ASPICE focus: SWE.4, SWE.5, SWE.6, SYS.4, SYS.5, SUP.8

## 목적

Reviewed Final의 54개 Jira Test를 제품 요구사항, 독립 오라클, 자동화 코드 및
증거까지 양방향 추적한다. 실행되지 않았거나 오라클이 부족한 항목은 PASS가 아닌
GAP/BLOCKED로 공개한다.

## 시험 계층과 순서

1. 정적/CM gate: full SHA, canonical boot path, target/memory map, credential leak.
2. SWE.4 Host: 제품 C 모듈과 독립 C oracle을 Ubuntu에서 `-Werror`로 빌드/실행.
3. SWE.5 component: FSM, protocol, timeout, GPIO command를 target 또는 HIL에서 확인.
4. SWE.6 integration: BMS↔EVSE CAN state/permit/fault 흐름 확인.
5. SYS.4/5 HIL: 3-node bus, actual GPIO/contactor, fault injection, OTA recovery.
6. Gateway: contract와 source boundary 승인 후 실행 baseline으로 승격.

## 환경

| 환경 | Runner | 용도 | 금지/제약 |
|---|---|---|---|
| Ubuntu Docker | `docker`, `qa-toolchain` | compile, Host unit, static, artifact | 실제 GPIO PASS 주장 금지 |
| Raspberry Pi 4 | protected `raspberrypi`, `hil` | CAN/UART/OpenOCD/fixture HIL | 승인 env gate 없이 actuation/erase 금지 |

## Entry criteria

- `config/product-baseline.json`의 full SHA와 clone HEAD 일치.
- CAN 500 kbit/s, 54–66 Ω, 공통 GND, ECU 전원/비상차단 확인.
- 대상별 artifact SHA-256과 flash verify evidence 생성.
- destructive test는 복구 artifact와 운영자 승인이 있음.
- Gateway는 ICD/schema/expected behavior가 승인됨.

## Exit criteria

- P0의 PASS/FAIL/GAP/BLOCKED가 모두 근거와 함께 기록됨.
- FAIL은 제품/테스트/구성/인프라로 분류됨.
- Jira ID↔SWRS↔자동화↔JUnit↔artifact 링크가 RTM에서 끊기지 않음.
- safety case의 물리 오라클이 충족됨. CAN 또는 로그만으로 대체하지 않음.

## 결과 분류

`PASS`, `FAIL_PRODUCT`, `GAP_REQUIREMENT`, `FAIL_TEST`,
`BLOCKED_INFRA`, `MISMATCH_CONFIGURATION`, `NOT_APPLICABLE`만 사용한다.
공식 증거 필드는 `result-schema.json`을 따른다.

## Safety 운영

BMS demo/relay 및 EVSE actuation 후보를 HIL에서 사용할 때 전류 제한 전원,
독립 fuse, hard interlock, emergency stop, no-load first-run을 적용한다. 버스 오류,
relay actuation, reset, power loss, flash erase는 각각 별도 `HIL_ALLOW_*` 승인으로
분리한다.
