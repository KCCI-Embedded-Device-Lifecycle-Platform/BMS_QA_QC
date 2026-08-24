# Software Requirements Specification (SWRS)

문서 ID: `BEOG-SWRS-001`
기준: Jira Test Case Catalog Reviewed Final
상태: QA baseline candidate / requirement-owner approval pending

## 1. 범위와 해석 규칙

이 문서는 BMS(STM32F446), EVSE(STM32F429), canonical OTA bootloader
(`ota-platform/EVSE_BOOT/EVSE_BOOT`) 및 향후 Gateway 계약의 검증 가능한
소프트웨어 요구사항을 정의한다. “측정한다”와 “상한 이내여야 한다”는 다르다.
승인되지 않은 응답시간에는 임의 상한을 만들지 않고 측정값만 기록한다.

비교 연산자는 명시적으로 유지한다. 예를 들어 cell OV는 `> 4200 mV`에서
진입하고 모든 cell이 `< 4150 mV`일 때만 clear 후보가 된다. 경계값과 경계
바깥값을 각각 시험한다.

## 2. BMS 요구사항

| ID | SHALL 요구사항 | 검증 기준 |
|---|---|---|
| SWRS-BMS-001 | BMS는 cell 전압이 4200 mV를 초과하면 OV 후보로, 모든 cell이 4150 mV 미만이면 clear 후보로 판정해야 한다. | strict `>`/`<`, 4개 경계 시험 |
| SWRS-BMS-002 | BMS는 cell 전압이 3000 mV 미만이면 UV, 모두 3100 mV 초과이면 clear 후보로 판정해야 한다. | 경계/비경계 |
| SWRS-BMS-003 | BMS는 pack 전압이 16800 mV 초과이면 PACK_OV, 16600 mV 미만이면 clear 후보로 판정해야 한다. | 경계/비경계 |
| SWRS-BMS-004 | Demo 정책에서 절대 전류가 1000(10 mA 단위)을 초과하면 OC, 900 미만이면 clear 후보로 판정해야 한다. | 양/음 전류, 절대값 |
| SWRS-BMS-005 | 최고 온도가 55.0°C를 초과하면 OT, 모든 온도가 50.0°C 미만이면 clear 후보로 판정해야 한다. | 0.1°C 단위, strict 비교 |
| SWRS-BMS-006 | sensor가 ready가 아니거나 shunt/hall current 차이가 500 mA를 초과하면 sensor fault를 설정해야 한다. | ready false 및 독립 절대차 계산 |
| SWRS-BMS-007 | fault 진입은 100 ms 평가 3회 연속 확인 후 확정되어야 한다. | 2회 no fault, 3회 fault |
| SWRS-BMS-008 | fault clear 조건은 3000 ms 연속 유지되어야 한다. | clear hold 이전/이후 |
| SWRS-BMS-009 | 하나 이상의 critical fault가 있으면 charge permit은 false여야 한다. | 전체 critical mask 및 조합 |
| SWRS-BMS-010 | FAULT 상태에서는 charge/relay ON 전이가 금지되고 fault clear 후 IDLE로 복귀해야 한다. | FSM transition matrix |
| SWRS-BMS-011 | EVSE link가 1000 ms 동안 없으면 LINK_TIMEOUT, 정상 수신이 300 ms 유지되면 clear되어야 한다. | HIL 시간축; 현재 소스의 추가 confirm 지연은 deviation으로 판정 |
| SWRS-BMS-012 | 유효한 EVSE request와 permit이 동시에 true일 때만 PA8 relay command를 ON하고 cancel/fault에서 OFF해야 한다. | 명령+PA8 물리 오라클 |

## 3. EVSE 요구사항

| ID | SHALL 요구사항 | 검증 기준 |
|---|---|---|
| SWRS-EVSE-001 | init, reset 및 임의 reset 반복 후 PE11은 LOW여야 한다. | OpenOCD GPIOE ODR + fixture output |
| SWRS-EVSE-002 | START/STOP은 30 ms 안정 입력 후 이벤트를 정확히 1회 생성해야 한다. | 10 ms sampling Host test |
| SWRS-EVSE-003 | connector, BMS online, permit이 true이고 E-stop/fault/OTA가 모두 false일 때만 충전을 허용해야 한다. | 64-combination decision table |
| SWRS-EVSE-004 | permit false 또는 critical fault 수신 시 relay command를 OFF해야 한다. | component 및 HIL |
| SWRS-EVSE-005 | 마지막 정상 BMS MAIN(0x100) 후 500 ms를 초과하면 offline 및 PE11 LOW로 전이해야 한다. | 마지막 RX timestamp→PE11 |
| SWRS-EVSE-006 | fault/permit 손실부터 Safe-Off까지 latency를 기록해야 한다. | 승인 상한 없음; 측정값 보존 |
| SWRS-EVSE-007 | EVSE fault bits는 CAN 0x202 data[0]의 01/02/04/08/10/20/40/80에 정확히 매핑되어야 한다. | bit 단독 자극 |
| SWRS-EVSE-008 | START/STOP 상태 전이는 0x201 data[0] 1/0을 송신해야 하며 cached BMS frame을 새 ACK로 사용하지 않아야 한다. | state/sequence gate |

## 4. CAN 요구사항

| ID | SHALL 요구사항 | 검증 기준 |
|---|---|---|
| SWRS-CAN-001 | 네트워크는 500 kbit/s, 11-bit standard data frame을 사용해야 한다. | 구성 및 3-node HIL |
| SWRS-CAN-002 | 0x100–0x105와 0x200–0x202의 ID/DLC/payload는 ICD와 일치해야 한다. | Host contract test |
| SWRS-CAN-003 | multi-byte 값은 little-endian이고 pack current는 signed 16-bit여야 한다. | round trip |
| SWRS-CAN-004 | wrong DLC, Extended, RTR은 INVALID, unknown ID는 IGNORED이며 이전 snapshot을 바꾸지 않아야 한다. | negative partition |
| SWRS-CAN-005 | 주기 프레임은 ICD schedule 허용오차 내에 있어야 한다. | timestamp median |
| SWRS-CAN-006 | BMS fault→permit false→EVSE Safe-Off의 순서와 물리 출력을 관찰해야 한다. | system HIL |
| SWRS-CAN-007 | bus-off를 검출하고 승인된 recovery 정책에 따라 회복해야 한다. | fault injection; 정책 승인 필요 |

## 5. OTA 요구사항

| ID | SHALL 요구사항 | 검증 기준 |
|---|---|---|
| SWRS-OTA-001 | 유효 app vector이면 0x08020000–0x08100000 범위로 jump하고 invalid vector/user button이면 boot command loop에 남아야 한다. | PC range/UART |
| SWRS-OTA-002 | text HELLO/VERSION/PROTO/RUN 및 binary AA55 protocol은 정의된 ACK/NACK/action을 반환해야 한다. | Host/target |
| SWRS-OTA-003 | binary frame의 CRC16 오류는 side effect 없이 NACK되어야 한다. | corrupted frame |
| SWRS-OTA-004 | image size는 8..896 KiB이고 data offset은 순차적이어야 하며 범위 밖 write를 거부해야 한다. | boundary partitions |
| SWRS-OTA-005 | END_UPDATE는 whole-image CRC32가 일치하고 vector가 유효할 때만 vector 8 byte를 최종 기록해야 한다. | withheld-vector oracle |
| SWRS-OTA-006 | target update HIL job은 GitLab manual approval 없이는 실행되지 않아야 한다. | pipeline rule |
| SWRS-OTA-007 | downgrade 정책은 요구사항 소유자가 version source와 비교 규칙을 승인한 뒤 구현해야 한다. | `GAP_REQUIREMENT` |
| SWRS-OTA-008 | 전원 손실 후 rollback/dual-bank recovery 요구사항은 제품 mechanism 승인 후 정의해야 한다. | `GAP_REQUIREMENT` |
| SWRS-OTA-009 | 다른 ECU image 차단은 signed target identity 계약 승인 후 정의해야 한다. | `GAP_REQUIREMENT` |

## 6. QA Infrastructure / Gateway

| ID | SHALL 요구사항 | 검증 기준 |
|---|---|---|
| SWRS-INFRA-001 | 모든 공식 결과는 제품 SHA, artifact hash, target identity와 환경 identity를 포함해야 한다. | evidence schema |
| SWRS-INFRA-002 | Host test는 Ubuntu Docker runner, HIL은 보호된 Raspberry Pi runner에서 분리 실행되어야 한다. | CI topology |
| SWRS-INFRA-003 | 결과는 승인된 분류와 JUnit/artifact로 보존되어야 한다. | schema/JUnit self-test |
| SWRS-GA-001 | Gateway decoder/state/stale/invalid/log 요구사항은 입력 schema와 source boundary 승인 후 baseline한다. | 현재 `CONTRACT_WAITING` |

## 7. 비기능 안전 제약

- BMS의 `CFG_DEMO_MODE=1`, relay bring-up 활성 및 EVSE actuation 활성 후보는 실제
  부하에서 사용하지 않는다. HIL fixture에는 독립 hard interlock과 비상 차단을 둔다.
- OTA erase/update 시험은 복구 이미지, 전원 차단 절차, 명시적 운영자 승인이 없으면
  실행하지 않는다.
- 제품 저장소의 Wi-Fi 자격증명은 비밀 관리 대상으로 분리하고 로그/보고서에 값을
  재출력하지 않는다.
