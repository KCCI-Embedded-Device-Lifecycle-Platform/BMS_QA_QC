# Jira Test Case Catalog — Reviewed Final Implementation

총 54개. GPT Reviewed Final을 기준으로 제품 요구사항, 독립 오라클, 자동화 코드를 연결했다.

> QA/QC: READY는 코드 준비 상태이지 시험 PASS가 아니다. 실제 결과는 고정 SHA/artifact/target 증거로만 승격한다.

## BMS

### TC-BMS-OV-001 — Cell OV detection boundary

- Trace: `SWRS-BMS-001` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Boundary / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Apply 4199, 4200 and 4201 mV candidates.
- Expected oracle: 4199/4200 are normal and 4201 is an OV candidate.
- Automation: `tests/host/bms/test_bms_safety_host.py`

### TC-BMS-OV-002 — Cell OV confirmation count N-1/N

- Trace: `SWRS-BMS-007` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: State transition / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Apply an OV candidate for two then three 100 ms evaluations.
- Expected oracle: Two samples do not latch; the third latches OV.
- Automation: `tests/host/bms/test_bms_safety_host.py`

### TC-BMS-OV-003 — Cell OV clear hysteresis boundary

- Trace: `SWRS-BMS-001,SWRS-BMS-008` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Boundary / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: From OV fault apply 4150 then 4149 mV.
- Expected oracle: 4150 is not a clear candidate; all cells below 4150 start clear hold.
- Automation: `tests/host/bms/test_bms_safety_host.py`

### TC-BMS-OV-004 — Cell OV clear hold time

- Trace: `SWRS-BMS-008` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Timing boundary / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Hold all clear values just below then at 3000 ms.
- Expected oracle: Fault remains before the hold and clears at the approved hold.
- Automation: `tests/host/bms/test_bms_safety_host.py`

### TC-BMS-UV-001 — Cell UV detect and clear

- Trace: `SWRS-BMS-002,SWRS-BMS-007` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Boundary / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Exercise 3000/2999 mV and 3100/3101 mV boundaries.
- Expected oracle: Strict detect/clear comparisons and confirmation are observed.
- Automation: `tests/host/bms/test_bms_safety_host.py`

### TC-BMS-PACKOV-001 — Pack over-voltage detect and clear

- Trace: `SWRS-BMS-003,SWRS-BMS-007` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Boundary / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Exercise 16800/16801 and 16600/16599 mV.
- Expected oracle: Strict detect/clear comparisons are observed.
- Automation: `tests/host/bms/test_bms_safety_host.py`

### TC-BMS-OC-001 — Signed over-current absolute threshold

- Trace: `SWRS-BMS-004` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Boundary / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Apply +1000/+1001 and -1000/-1001 current values.
- Expected oracle: Detection uses absolute signed current and strict threshold.
- Automation: `tests/host/bms/test_bms_safety_host.py`

### TC-BMS-OT-001 — Over-temperature detect and clear

- Trace: `SWRS-BMS-005` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Boundary / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Exercise 550/551 and 500/499 in 0.1 C units.
- Expected oracle: 55.0 C is normal, 55.1 C detects; 50.0 C does not clear, 49.9 C does.
- Automation: `tests/host/bms/test_bms_safety_host.py`

### TC-BMS-SENSOR-001 — Sensor readiness and current cross-check

- Trace: `SWRS-BMS-006` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Boundary / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Set sensor_ready false, then apply shunt/hall difference 500 and 501 mA.
- Expected oracle: Not-ready or difference greater than 500 mA sets SENSOR_ERR.
- Automation: `tests/host/bms/test_bms_safety_host.py`

### TC-BMS-PERMIT-001 — Critical fault denies charge permit

- Trace: `SWRS-BMS-009` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Decision table / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Apply every critical fault bit and representative combinations.
- Expected oracle: Any critical fault forces permit false.
- Automation: `tests/host/bms/test_bms_safety_host.py`

### TC-BMS-FSM-001 — BMS fault-state transition matrix

- Trace: `SWRS-BMS-010` / `SWE.5` / `Component` / `P0`
- Method / disposition: State transition / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Request charge across IDLE/READY/CHARGING/FAULT and clear fault.
- Expected oracle: FAULT cannot charge; accepted clear returns to IDLE.
- Automation: `tests/host/bms/test_bms_safety_host.py`

### TC-BMS-LINK-001 — EVSE link timeout and recovery timing

- Trace: `SWRS-BMS-011` / `SWE.5` / `Component/HIL` / `P0`
- Method / disposition: Fault injection / `READY_HIL_CONDITIONAL`
- Precondition: Isolated EVSE TX silence/restore control is configured.
- Stimulus: Silence EVSE frames, then restore them.
- Expected oracle: LINK_TIMEOUT occurs at 1000 ms requirement and clears after 300 ms stable reception.
- Automation: `hil/tests/test_can_timeout.py`

### TC-BMS-RELAY-001 — EVSE request and permit control PA8

- Trace: `SWRS-BMS-012` / `SWE.5` / `Component/HIL` / `P1`
- Method / disposition: State/output / `READY_HIL_CONDITIONAL`
- Precondition: Current-limited, hard-interlocked BMS relay fixture is connected.
- Stimulus: Apply valid request+permit, then cancel and critical fault.
- Expected oracle: PA8 is ON only for valid request+permit and LOW for cancel/fault.
- Automation: `hil/tests/test_can_e2e.py;hil/tests/test_safe_state.py`

### TC-BMS-MULTI-001 — Multi-fault safety convergence

- Trace: `SWRS-BMS-009` / `SWE.4` / `Host Unit` / `P1`
- Method / disposition: Combinatorial / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Apply representative simultaneous fault masks and clear subsets.
- Expected oracle: Permit remains false while any critical fault remains.
- Automation: `tests/host/bms/test_bms_safety_host.py`

## EVSE

### TC-EVSE-SAFE-001 — Power and reset Safe-Off

- Trace: `SWRS-EVSE-001` / `SWE.5` / `Target Component` / `P0`
- Method / disposition: Reset/output / `READY_HIL_CONDITIONAL`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Initialize and reset the target.
- Expected oracle: Relay command and PE11 are LOW after init/reset.
- Automation: `tests/host/evse/test_evse_core_host.py;hil/tests/test_safe_state.py`

### TC-EVSE-IN-001 — START and STOP 30 ms debounce

- Trace: `SWRS-EVSE-002` / `SWE.4` / `Host Unit` / `P1`
- Method / disposition: Timing boundary / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Apply less than 30 ms then three stable 10 ms samples.
- Expected oracle: Short input is ignored; stable input generates one event.
- Automation: `tests/host/evse/test_evse_core_host.py`

### TC-EVSE-SAFE-002 — Permit false forces relay off

- Trace: `SWRS-EVSE-004` / `SWE.5` / `Component` / `P0`
- Method / disposition: Decision / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Start in CHARGING with relay ON, then remove charge permit.
- Expected oracle: Relay command turns OFF and the FSM enters FAULT.
- Automation: `tests/host/evse/test_evse_core_host.py`

### TC-EVSE-SAFE-003 — Charge-condition decision table

- Trace: `SWRS-EVSE-003` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Decision table / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Evaluate all 64 combinations of six safety inputs.
- Expected oracle: Charging is allowed only for the single approved conjunction.
- Automation: `tests/host/evse/test_evse_core_host.py`

### TC-EVSE-SAFE-004 — BMS timeout drives Safe-Off

- Trace: `SWRS-EVSE-005` / `SWE.5` / `Target/HIL` / `P0`
- Method / disposition: Fault injection / `READY_HIL_CONDITIONAL`
- Precondition: EVSE is in charging state; isolated BMS TX silence control is configured.
- Stimulus: While charging, stop BMS MAIN frames for more than 500 ms.
- Expected oracle: BMS becomes offline and PE11 is LOW within approved task tolerance.
- Automation: `tests/host/evse/test_evse_core_host.py;hil/tests/test_can_timeout.py`

### TC-EVSE-SAFE-005 — Fault or permit-loss response latency

- Trace: `SWRS-EVSE-006` / `SWE.6` / `Integration` / `P0`
- Method / disposition: Timing measurement / `READY_HIL_CONDITIONAL`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Inject an approved critical BMS fault while charging.
- Expected oracle: Relay converges OFF; measured latency is recorded without an unapproved upper-limit verdict.
- Automation: `tests/host/evse/test_evse_core_host.py;hil/tests/test_can_e2e.py`

### TC-EVSE-SAFE-006 — Arbitrary reset robustness

- Trace: `SWRS-EVSE-001` / `SWE.5` / `Target/HIL` / `P0`
- Method / disposition: Robustness / `READY_HIL_CONDITIONAL`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Repeat target reset three times from arbitrary prior RAM state.
- Expected oracle: Every restart begins with relay command and PE11 LOW.
- Automation: `tests/host/evse/test_evse_core_host.py;hil/tests/test_safe_state.py`

### TC-EVSE-FAULT-001 — EVSE fault bitmask mapping

- Trace: `SWRS-EVSE-007` / `SWE.4` / `Host Unit` / `P1`
- Method / disposition: Equivalence / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Encode each EVSE fault bit independently.
- Expected oracle: 0x202 data[0] maps exactly to 01/02/04/08/10/20/40/80.
- Automation: `tests/host/evse/test_evse_core_host.py`

### TC-EVSE-CAN-REQ-001 — START and STOP charge request

- Trace: `SWRS-EVSE-008` / `SWE.5` / `Component/HIL` / `P1`
- Method / disposition: State transition / `READY_HIL_CONDITIONAL`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Issue START then STOP and observe the next fresh BMS response.
- Expected oracle: 0x201 transmits 1/0; cached BMS data cannot acknowledge START.
- Automation: `tests/host/evse/test_evse_core_host.py;hil/tests/test_can_e2e.py`

## CAN

### TC-CAN-PROTO-001 — All defined CAN ID and DLC contracts

- Trace: `SWRS-CAN-001,SWRS-CAN-002` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Interface / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Enumerate all approved IDs and exact DLC values.
- Expected oracle: All frames are unique 11-bit IDs with ICD DLC.
- Automation: `tests/host/evse/test_evse_core_host.py`

### TC-CAN-ENDIAN-001 — Little-endian and signed-current decoding

- Trace: `SWRS-CAN-003` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Data representation / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Decode known byte patterns including negative current.
- Expected oracle: Decoded values exactly match independent LE/signed oracle.
- Automation: `tests/host/evse/test_evse_core_host.py`

### TC-CAN-NEG-001 — Reject wrong DLC Extended and RTR frames

- Trace: `SWRS-CAN-004` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Negative partition / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Pass wrong DLC, extended and RTR variants of a known ID.
- Expected oracle: Each is INVALID and leaves prior snapshot byte-identical.
- Automation: `tests/host/evse/test_evse_core_host.py`

### TC-CAN-UNKID-001 — Ignore unknown CAN ID

- Trace: `SWRS-CAN-004` / `SWE.4` / `Host Unit` / `P1`
- Method / disposition: Negative partition / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Pass a well-formed unassigned standard ID.
- Expected oracle: Result is IGNORED and prior snapshot is unchanged.
- Automation: `tests/host/evse/test_evse_core_host.py`

### TC-CAN-BUS-001 — Three-node 500 kbit/s bus acceptance

- Trace: `SWRS-CAN-001` / `SYS.4` / `HIL` / `P0`
- Method / disposition: Physical acceptance / `READY_HIL_CONDITIONAL`
- Precondition: BMS, EVSE and Pi are connected with power off resistance evidence.
- Stimulus: Measure termination and observe BMS+EVSE from Pi for 3 s.
- Expected oracle: 54–66 ohm, both node frame ranges visible, zero observed error frames.
- Automation: `hil/tests/test_can_bus_acceptance.py`

### TC-CAN-HB-001 — CAN periodicity schedule

- Trace: `SWRS-CAN-005` / `SWE.5` / `HIL` / `P0`
- Method / disposition: Timing / `READY_HIL_CONDITIONAL`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Capture at least 4 seconds of approved periodic IDs.
- Expected oracle: Median periods match 100/500/1000 ms within configured tolerance.
- Automation: `hil/tests/test_can_timeout.py`

### TC-CAN-E2E-001 — BMS MAIN updates EVSE snapshot

- Trace: `SWRS-CAN-002,SWRS-CAN-003` / `SWE.6` / `Integration` / `P0`
- Method / disposition: Back-to-back / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Decode a known 0x100 payload.
- Expected oracle: permit/state/fault/current and RX sequence update exactly.
- Automation: `tests/host/evse/test_evse_core_host.py`

### TC-CAN-E2E-002 — START STOP through BMS state and PA8

- Trace: `SWRS-BMS-012,SWRS-EVSE-008,SWRS-CAN-006` / `SYS.4` / `System HIL` / `P0`
- Method / disposition: End-to-end / `READY_HIL_CONDITIONAL`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Electrically issue START then STOP.
- Expected oracle: 0x201 1/0, BMS state, EVSE state and relay outputs follow the approved sequence.
- Automation: `hil/tests/test_can_e2e.py`

### TC-CAN-E2E-003 — Critical BMS fault drives EVSE Safe-Off

- Trace: `SWRS-BMS-009,SWRS-EVSE-006,SWRS-CAN-006` / `SYS.5` / `System HIL` / `P0`
- Method / disposition: End-to-end fault / `READY_HIL_CONDITIONAL`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Inject one approved critical BMS fault while charging.
- Expected oracle: Fault then permit=0 then EVSE relay command/PE11 OFF are observed in order.
- Automation: `hil/tests/test_can_e2e.py`

### TC-CAN-BUSOFF-001 — Bus-off detect and recovery

- Trace: `SWRS-CAN-007` / `SWE.5` / `HIL Fault Injection` / `P2`
- Method / disposition: Fault injection / `READY_HIL_CONDITIONAL`
- Precondition: Bus fault fixture and recovery policy are approved.
- Stimulus: Use the reviewed fixture to enter then restore bus fault.
- Expected oracle: Bus-off is detected and approved recovery behavior occurs.
- Automation: `hil/tests/test_bus_off_recovery.py`

## OTA

### TC-OTA-BOOT-001 — Valid application reset jump

- Trace: `SWRS-OTA-001` / `SWE.5` / `Target/HIL` / `P0`
- Method / disposition: State/output / `READY_HIL_CONDITIONAL`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Reset a target containing a verified valid app.
- Expected oracle: PC enters 0x08020000–0x08100000.
- Automation: `hil/tests/test_ota_boot.py`

### TC-OTA-BOOT-002 — Invalid app or user button keeps boot mode

- Trace: `SWRS-OTA-001` / `SWE.5` / `Target/HIL` / `P0`
- Method / disposition: State/output / `READY_HIL_CONDITIONAL`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Hold the fixture-controlled user button during reset and issue HELLO.
- Expected oracle: Application jump is prevented and boot command loop returns ACK.
- Automation: `hil/tests/test_ota_boot.py`

### TC-OTA-PROTO-001 — Text and binary boot protocol commands

- Trace: `SWRS-OTA-002` / `SWE.4` / `Host/Target` / `P1`
- Method / disposition: Interface / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Issue HELLO, VERSION, PROTO, RUN and a binary round trip.
- Expected oracle: Exact response/action and framing are returned.
- Automation: `tests/host/ota/test_ota_host.py`

### TC-OTA-PROTO-002 — Binary packet CRC16 rejection

- Trace: `SWRS-OTA-003` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Negative / `READY_HIL_CONDITIONAL`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Corrupt one CRC bit in a valid START_UPDATE packet.
- Expected oracle: Parser reports CRC error or target NACK and performs no update action.
- Automation: `tests/host/ota/test_ota_host.py;hil/tests/test_ota_crc_failure.py`

### TC-OTA-SIZE-001 — Image size boundaries

- Trace: `SWRS-OTA-004` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Boundary / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Try size 0, 7, 8, capacity and capacity+1.
- Expected oracle: Invalid/oversize image is rejected before flash write.
- Automation: `tests/host/ota/test_ota_host.py`

### TC-OTA-OFFSET-001 — Data offset and length sequence

- Trace: `SWRS-OTA-004` / `SWE.4` / `Host Unit` / `P0`
- Method / disposition: Boundary/sequence / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Send out-of-order offset and invalid intermediate length.
- Expected oracle: Request is rejected and expected next offset is unchanged.
- Automation: `tests/host/ota/test_ota_host.py`

### TC-OTA-CRC-001 — Whole-image CRC32 mismatch

- Trace: `SWRS-OTA-005` / `SWE.4` / `Host/Target` / `P0`
- Method / disposition: Negative / `READY_HIL_CONDITIONAL`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Transfer a valid-vector image with one-bit wrong expected CRC32.
- Expected oracle: END_UPDATE returns CRC_MISMATCH and app vector remains erased.
- Automation: `tests/host/ota/test_ota_host.py;hil/tests/test_ota_crc_failure.py`

### TC-OTA-UPDATE-001 — Valid image end-to-end update

- Trace: `SWRS-OTA-005` / `SWE.5` / `Target/HIL` / `P0`
- Method / disposition: End-to-end / `READY_HIL_CONDITIONAL`
- Precondition: Manual approval, verified recovery image and target power control are available.
- Stimulus: Erase, sequentially write, verify and end a known recovery image.
- Expected oracle: CRC/vector valid image completes and boots; recovery evidence is retained.
- Automation: `tests/host/ota/test_ota_host.py;hil/tests/test_ota_update.py`

### TC-OTA-GATE-001 — Manual approval before target update

- Trace: `SWRS-OTA-006` / `SUP.8` / `Process` / `P1`
- Method / disposition: Pipeline inspection / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Evaluate pipeline rules for branch/pipeline sources.
- Expected oracle: No target erase/write job starts automatically; protected manual gate is required.
- Automation: `tests/quality/test_infrastructure.py`

### TC-OTA-VERSION-001 — Firmware downgrade policy

- Trace: `SWRS-OTA-007` / `—` / `GAP` / `GAP`
- Method / disposition: Requirement analysis / `GAP_REQUIREMENT`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Attempt no product update until version contract exists.
- Expected oracle: JUnit records GAP_REQUIREMENT, never PASS.
- Automation: `tests/quality/test_declared_gaps.py`

### TC-OTA-ROLLBACK-001 — Boot failure rollback

- Trace: `SWRS-OTA-008` / `—` / `GAP/HIL` / `GAP`
- Method / disposition: Requirement analysis / `GAP_REQUIREMENT`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Attempt no power-cut update until rollback mechanism/recovery is approved.
- Expected oracle: JUnit records GAP_REQUIREMENT, never PASS.
- Automation: `tests/quality/test_declared_gaps.py;hil/tests/test_ota_power_loss.py`

### TC-OTA-XTARGET-001 — Wrong ECU image rejection

- Trace: `SWRS-OTA-009` / `—` / `GAP` / `GAP`
- Method / disposition: Requirement analysis / `GAP_REQUIREMENT`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Attempt no cross-target assertion without signed target identity.
- Expected oracle: JUnit records GAP_REQUIREMENT, never PASS.
- Automation: `tests/quality/test_declared_gaps.py`

## Infra

### TC-INFRA-CM-001 — Product SHA artifact and target identity

- Trace: `SWRS-INFRA-001` / `SUP.8` / `Process` / `P0`
- Method / disposition: Static/evidence / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Validate full refs then build/hash/verify target image.
- Expected oracle: Source SHA, ELF/BIN SHA256 and target verification agree.
- Automation: `tests/quality/test_infrastructure.py`

### TC-INFRA-PIPE-001 — Ubuntu to Raspberry Pi pipeline topology

- Trace: `SWRS-INFRA-002` / `SUP.8` / `Process` / `P0`
- Method / disposition: Pipeline / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Lint CI and run Host then protected HIL stages.
- Expected oracle: Jobs use intended runner tags and artifacts flow forward.
- Automation: `tests/quality/test_infrastructure.py`

### TC-INFRA-RES-001 — Result classification integrity

- Trace: `SWRS-INFRA-003` / `SUP.9` / `Process` / `P0`
- Method / disposition: Schema / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Validate every result against the classification enum.
- Expected oracle: Product/test/gap/config/infra outcomes remain distinguishable.
- Automation: `tests/quality/test_infrastructure.py`

### TC-INFRA-JUNIT-001 — JUnit and evidence artifact generation

- Trace: `SWRS-INFRA-003` / `SUP.8` / `Process` / `P1`
- Method / disposition: Self-test / `READY`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: Write PASS, FAIL and GAP sample results and parse XML.
- Expected oracle: Counts, failure and skipped nodes are machine-readable.
- Automation: `tests/quality/test_infrastructure.py`

## Gateway

### TC-GA-DECODE-001 — Gateway input decoding

- Trace: `SWRS-GA-001` / `SWE.4` / `Contract waiting` / `P2`
- Method / disposition: Contract / `CONTRACT_WAITING`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: No decode stimulus until input schema is approved.
- Expected oracle: BLOCKED_INFRA is recorded, not PASS.
- Automation: `tests/quality/test_gateway_contract.py`

### TC-GA-STATE-001 — Gateway state normalization

- Trace: `SWRS-GA-001` / `SWE.5` / `Contract waiting` / `P2`
- Method / disposition: Contract / `CONTRACT_WAITING`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: No state vectors until normalized schema is approved.
- Expected oracle: BLOCKED_INFRA is recorded, not PASS.
- Automation: `tests/quality/test_gateway_contract.py`

### TC-GA-STALE-001 — Gateway stale-data handling

- Trace: `SWRS-GA-001` / `SWE.5` / `Contract waiting` / `P2`
- Method / disposition: Contract / `CONTRACT_WAITING`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: No stale timeout is asserted until freshness policy is approved.
- Expected oracle: BLOCKED_INFRA is recorded, not PASS.
- Automation: `tests/quality/test_gateway_contract.py`

### TC-GA-INVALID-001 — Gateway invalid-input handling

- Trace: `SWRS-GA-001` / `SWE.4` / `Contract waiting` / `P2`
- Method / disposition: Contract / `CONTRACT_WAITING`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: No malformed vectors until validation rules are approved.
- Expected oracle: BLOCKED_INFRA is recorded, not PASS.
- Automation: `tests/quality/test_gateway_contract.py`

### TC-GA-LOG-001 — Gateway diagnostic logging

- Trace: `SWRS-GA-001` / `SWE.5` / `Contract waiting` / `P2`
- Method / disposition: Contract / `CONTRACT_WAITING`
- Precondition: Pinned product SHA and independent QA oracle are available.
- Stimulus: No log assertion until event and redaction policy is approved.
- Expected oracle: BLOCKED_INFRA is recorded, not PASS.
- Automation: `tests/quality/test_gateway_contract.py`
