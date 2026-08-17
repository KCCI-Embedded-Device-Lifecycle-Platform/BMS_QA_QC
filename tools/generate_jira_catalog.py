#!/usr/bin/env python3
"""Generate the reviewed 54-case Jira catalog from one controlled manifest."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/jira_export"


@dataclass(frozen=True)
class TestCase:
    test_id: str
    area: str
    summary: str
    requirement_id: str
    aspice: str
    level: str
    priority: str
    method: str
    precondition: str
    stimulus: str
    expected: str
    automation: str
    disposition: str = "READY"


def tc(
    test_id: str,
    area: str,
    summary: str,
    requirement: str,
    aspice: str,
    level: str,
    priority: str,
    method: str,
    stimulus: str,
    expected: str,
    automation: str,
    disposition: str = "READY",
    precondition: str = "Pinned product SHA and independent QA oracle are available.",
) -> TestCase:
    return TestCase(
        test_id,
        area,
        summary,
        requirement,
        aspice,
        level,
        priority,
        method,
        precondition,
        stimulus,
        expected,
        automation,
        disposition,
    )


CASES = [
    tc("TC-BMS-OV-001", "BMS", "Cell OV detection boundary", "SWRS-BMS-001", "SWE.4", "Host Unit", "P0", "Boundary", "Apply 4199, 4200 and 4201 mV candidates.", "4199/4200 are normal and 4201 is an OV candidate.", "tests/host/bms/test_bms_safety_host.py"),
    tc("TC-BMS-OV-002", "BMS", "Cell OV confirmation count N-1/N", "SWRS-BMS-007", "SWE.4", "Host Unit", "P0", "State transition", "Apply an OV candidate for two then three 100 ms evaluations.", "Two samples do not latch; the third latches OV.", "tests/host/bms/test_bms_safety_host.py"),
    tc("TC-BMS-OV-003", "BMS", "Cell OV clear hysteresis boundary", "SWRS-BMS-001,SWRS-BMS-008", "SWE.4", "Host Unit", "P0", "Boundary", "From OV fault apply 4150 then 4149 mV.", "4150 is not a clear candidate; all cells below 4150 start clear hold.", "tests/host/bms/test_bms_safety_host.py"),
    tc("TC-BMS-OV-004", "BMS", "Cell OV clear hold time", "SWRS-BMS-008", "SWE.4", "Host Unit", "P0", "Timing boundary", "Hold all clear values just below then at 3000 ms.", "Fault remains before the hold and clears at the approved hold.", "tests/host/bms/test_bms_safety_host.py"),
    tc("TC-BMS-UV-001", "BMS", "Cell UV detect and clear", "SWRS-BMS-002,SWRS-BMS-007", "SWE.4", "Host Unit", "P0", "Boundary", "Exercise 3000/2999 mV and 3100/3101 mV boundaries.", "Strict detect/clear comparisons and confirmation are observed.", "tests/host/bms/test_bms_safety_host.py"),
    tc("TC-BMS-PACKOV-001", "BMS", "Pack over-voltage detect and clear", "SWRS-BMS-003,SWRS-BMS-007", "SWE.4", "Host Unit", "P0", "Boundary", "Exercise 16800/16801 and 16600/16599 mV.", "Strict detect/clear comparisons are observed.", "tests/host/bms/test_bms_safety_host.py"),
    tc("TC-BMS-OC-001", "BMS", "Signed over-current absolute threshold", "SWRS-BMS-004", "SWE.4", "Host Unit", "P0", "Boundary", "Apply +1000/+1001 and -1000/-1001 current values.", "Detection uses absolute signed current and strict threshold.", "tests/host/bms/test_bms_safety_host.py"),
    tc("TC-BMS-OT-001", "BMS", "Over-temperature detect and clear", "SWRS-BMS-005", "SWE.4", "Host Unit", "P0", "Boundary", "Exercise 550/551 and 500/499 in 0.1 C units.", "55.0 C is normal, 55.1 C detects; 50.0 C does not clear, 49.9 C does.", "tests/host/bms/test_bms_safety_host.py"),
    tc("TC-BMS-SENSOR-001", "BMS", "Sensor readiness and current cross-check", "SWRS-BMS-006", "SWE.4", "Host Unit", "P0", "Boundary", "Set sensor_ready false, then apply shunt/hall difference 500 and 501 mA.", "Not-ready or difference greater than 500 mA sets SENSOR_ERR.", "tests/host/bms/test_bms_safety_host.py"),
    tc("TC-BMS-PERMIT-001", "BMS", "Critical fault denies charge permit", "SWRS-BMS-009", "SWE.4", "Host Unit", "P0", "Decision table", "Apply every critical fault bit and representative combinations.", "Any critical fault forces permit false.", "tests/host/bms/test_bms_safety_host.py"),
    tc("TC-BMS-FSM-001", "BMS", "BMS fault-state transition matrix", "SWRS-BMS-010", "SWE.5", "Component", "P0", "State transition", "Request charge across IDLE/READY/CHARGING/FAULT and clear fault.", "FAULT cannot charge; accepted clear returns to IDLE.", "tests/host/bms/test_bms_safety_host.py"),
    tc("TC-BMS-LINK-001", "BMS", "EVSE link timeout and recovery timing", "SWRS-BMS-011", "SWE.5", "Component/HIL", "P0", "Fault injection", "Silence EVSE frames, then restore them.", "LINK_TIMEOUT occurs at 1000 ms requirement and clears after 300 ms stable reception.", "hil/tests/test_can_timeout.py", "READY_HIL_CONDITIONAL", "Isolated EVSE TX silence/restore control is configured."),
    tc("TC-BMS-RELAY-001", "BMS", "EVSE request and permit control PA8", "SWRS-BMS-012", "SWE.5", "Component/HIL", "P1", "State/output", "Apply valid request+permit, then cancel and critical fault.", "PA8 is ON only for valid request+permit and LOW for cancel/fault.", "hil/tests/test_can_e2e.py;hil/tests/test_safe_state.py", "READY_HIL_CONDITIONAL", "Current-limited, hard-interlocked BMS relay fixture is connected."),
    tc("TC-BMS-MULTI-001", "BMS", "Multi-fault safety convergence", "SWRS-BMS-009", "SWE.4", "Host Unit", "P1", "Combinatorial", "Apply representative simultaneous fault masks and clear subsets.", "Permit remains false while any critical fault remains.", "tests/host/bms/test_bms_safety_host.py"),

    tc("TC-EVSE-SAFE-001", "EVSE", "Power and reset Safe-Off", "SWRS-EVSE-001", "SWE.5", "Target Component", "P0", "Reset/output", "Initialize and reset the target.", "Relay command and PE11 are LOW after init/reset.", "tests/host/evse/test_evse_core_host.py;hil/tests/test_safe_state.py", "READY_HIL_CONDITIONAL"),
    tc("TC-EVSE-IN-001", "EVSE", "START and STOP 30 ms debounce", "SWRS-EVSE-002", "SWE.4", "Host Unit", "P1", "Timing boundary", "Apply less than 30 ms then three stable 10 ms samples.", "Short input is ignored; stable input generates one event.", "tests/host/evse/test_evse_core_host.py"),
    tc("TC-EVSE-SAFE-002", "EVSE", "Permit false forces relay off", "SWRS-EVSE-004", "SWE.5", "Component", "P0", "Decision", "Set charge-ready/relay request with permit false.", "Relay command remains OFF and CHARGING is not entered.", "tests/host/evse/test_evse_core_host.py"),
    tc("TC-EVSE-SAFE-003", "EVSE", "Charge-condition decision table", "SWRS-EVSE-003", "SWE.4", "Host Unit", "P0", "Decision table", "Evaluate all 64 combinations of six safety inputs.", "Charging is allowed only for the single approved conjunction.", "tests/host/evse/test_evse_core_host.py"),
    tc("TC-EVSE-SAFE-004", "EVSE", "BMS timeout drives Safe-Off", "SWRS-EVSE-005", "SWE.5", "Target/HIL", "P0", "Fault injection", "While charging, stop BMS MAIN frames for more than 500 ms.", "BMS becomes offline and PE11 is LOW within approved task tolerance.", "tests/host/evse/test_evse_core_host.py;hil/tests/test_can_timeout.py", "READY_HIL_CONDITIONAL", "EVSE is in charging state; isolated BMS TX silence control is configured."),
    tc("TC-EVSE-SAFE-005", "EVSE", "Fault or permit-loss response latency", "SWRS-EVSE-006", "SWE.6", "Integration", "P0", "Timing measurement", "Inject an approved critical BMS fault while charging.", "Relay converges OFF; measured latency is recorded without an unapproved upper-limit verdict.", "tests/host/evse/test_evse_core_host.py;hil/tests/test_can_e2e.py", "READY_HIL_CONDITIONAL"),
    tc("TC-EVSE-SAFE-006", "EVSE", "Arbitrary reset robustness", "SWRS-EVSE-001", "SWE.5", "Target/HIL", "P0", "Robustness", "Repeat target reset three times from arbitrary prior RAM state.", "Every restart begins with relay command and PE11 LOW.", "tests/host/evse/test_evse_core_host.py;hil/tests/test_safe_state.py", "READY_HIL_CONDITIONAL"),
    tc("TC-EVSE-FAULT-001", "EVSE", "EVSE fault bitmask mapping", "SWRS-EVSE-007", "SWE.4", "Host Unit", "P1", "Equivalence", "Encode each EVSE fault bit independently.", "0x202 data[0] maps exactly to 01/02/04/08/10/20/40/80.", "tests/host/evse/test_evse_core_host.py"),
    tc("TC-EVSE-CAN-REQ-001", "EVSE", "START and STOP charge request", "SWRS-EVSE-008", "SWE.5", "Component/HIL", "P1", "State transition", "Issue START then STOP and observe the next fresh BMS response.", "0x201 transmits 1/0; cached BMS data cannot acknowledge START.", "tests/host/evse/test_evse_core_host.py;hil/tests/test_can_e2e.py", "READY_HIL_CONDITIONAL"),

    tc("TC-CAN-PROTO-001", "CAN", "All defined CAN ID and DLC contracts", "SWRS-CAN-001,SWRS-CAN-002", "SWE.4", "Host Unit", "P0", "Interface", "Enumerate all approved IDs and exact DLC values.", "All frames are unique 11-bit IDs with ICD DLC.", "tests/host/evse/test_evse_core_host.py"),
    tc("TC-CAN-ENDIAN-001", "CAN", "Little-endian and signed-current decoding", "SWRS-CAN-003", "SWE.4", "Host Unit", "P0", "Data representation", "Decode known byte patterns including negative current.", "Decoded values exactly match independent LE/signed oracle.", "tests/host/evse/test_evse_core_host.py"),
    tc("TC-CAN-NEG-001", "CAN", "Reject wrong DLC Extended and RTR frames", "SWRS-CAN-004", "SWE.4", "Host Unit", "P0", "Negative partition", "Pass wrong DLC, extended and RTR variants of a known ID.", "Each is INVALID and leaves prior snapshot byte-identical.", "tests/host/evse/test_evse_core_host.py"),
    tc("TC-CAN-UNKID-001", "CAN", "Ignore unknown CAN ID", "SWRS-CAN-004", "SWE.4", "Host Unit", "P1", "Negative partition", "Pass a well-formed unassigned standard ID.", "Result is IGNORED and prior snapshot is unchanged.", "tests/host/evse/test_evse_core_host.py"),
    tc("TC-CAN-BUS-001", "CAN", "Three-node 500 kbit/s bus acceptance", "SWRS-CAN-001", "SYS.4", "HIL", "P0", "Physical acceptance", "Measure termination and observe BMS+EVSE from Pi for 3 s.", "54–66 ohm, both node frame ranges visible, zero observed error frames.", "hil/tests/test_can_bus_acceptance.py", "READY_HIL_CONDITIONAL", "BMS, EVSE and Pi are connected with power off resistance evidence."),
    tc("TC-CAN-HB-001", "CAN", "CAN periodicity schedule", "SWRS-CAN-005", "SWE.5", "HIL", "P0", "Timing", "Capture at least 4 seconds of approved periodic IDs.", "Median periods match 100/500/1000 ms within configured tolerance.", "hil/tests/test_can_timeout.py", "READY_HIL_CONDITIONAL"),
    tc("TC-CAN-E2E-001", "CAN", "BMS MAIN updates EVSE snapshot", "SWRS-CAN-002,SWRS-CAN-003", "SWE.6", "Integration", "P0", "Back-to-back", "Decode a known 0x100 payload.", "permit/state/fault/current and RX sequence update exactly.", "tests/host/evse/test_evse_core_host.py"),
    tc("TC-CAN-E2E-002", "CAN", "START STOP through BMS state and PA8", "SWRS-BMS-012,SWRS-EVSE-008,SWRS-CAN-006", "SYS.4", "System HIL", "P0", "End-to-end", "Electrically issue START then STOP.", "0x201 1/0, BMS state, EVSE state and relay outputs follow the approved sequence.", "hil/tests/test_can_e2e.py", "READY_HIL_CONDITIONAL"),
    tc("TC-CAN-E2E-003", "CAN", "Critical BMS fault drives EVSE Safe-Off", "SWRS-BMS-009,SWRS-EVSE-006,SWRS-CAN-006", "SYS.5", "System HIL", "P0", "End-to-end fault", "Inject one approved critical BMS fault while charging.", "Fault then permit=0 then EVSE relay command/PE11 OFF are observed in order.", "hil/tests/test_can_e2e.py", "READY_HIL_CONDITIONAL"),
    tc("TC-CAN-BUSOFF-001", "CAN", "Bus-off detect and recovery", "SWRS-CAN-007", "SWE.5", "HIL Fault Injection", "P2", "Fault injection", "Use the reviewed fixture to enter then restore bus fault.", "Bus-off is detected and approved recovery behavior occurs.", "hil/tests/test_bus_off_recovery.py", "READY_HIL_CONDITIONAL", "Bus fault fixture and recovery policy are approved."),

    tc("TC-OTA-BOOT-001", "OTA", "Valid application reset jump", "SWRS-OTA-001", "SWE.5", "Target/HIL", "P0", "State/output", "Reset a target containing a verified valid app.", "PC enters 0x08020000–0x08100000.", "hil/tests/test_ota_boot.py", "READY_HIL_CONDITIONAL"),
    tc("TC-OTA-BOOT-002", "OTA", "Invalid app or user button keeps boot mode", "SWRS-OTA-001", "SWE.5", "Target/HIL", "P0", "State/output", "Hold the fixture-controlled user button during reset and issue HELLO.", "Application jump is prevented and boot command loop returns ACK.", "hil/tests/test_ota_boot.py", "READY_HIL_CONDITIONAL"),
    tc("TC-OTA-PROTO-001", "OTA", "Text and binary boot protocol commands", "SWRS-OTA-002", "SWE.4", "Host/Target", "P1", "Interface", "Issue HELLO, VERSION, PROTO, RUN and a binary round trip.", "Exact response/action and framing are returned.", "tests/host/ota/test_ota_host.py"),
    tc("TC-OTA-PROTO-002", "OTA", "Binary packet CRC16 rejection", "SWRS-OTA-003", "SWE.4", "Host Unit", "P0", "Negative", "Corrupt one CRC bit in a valid START_UPDATE packet.", "Parser reports CRC error or target NACK and performs no update action.", "tests/host/ota/test_ota_host.py;hil/tests/test_ota_crc_failure.py", "READY_HIL_CONDITIONAL"),
    tc("TC-OTA-SIZE-001", "OTA", "Image size boundaries", "SWRS-OTA-004", "SWE.4", "Host Unit", "P0", "Boundary", "Try size 0, 7, 8, capacity and capacity+1.", "Invalid/oversize image is rejected before flash write.", "tests/host/ota/test_ota_host.py"),
    tc("TC-OTA-OFFSET-001", "OTA", "Data offset and length sequence", "SWRS-OTA-004", "SWE.4", "Host Unit", "P0", "Boundary/sequence", "Send out-of-order offset and invalid intermediate length.", "Request is rejected and expected next offset is unchanged.", "tests/host/ota/test_ota_host.py"),
    tc("TC-OTA-CRC-001", "OTA", "Whole-image CRC32 mismatch", "SWRS-OTA-005", "SWE.4", "Host/Target", "P0", "Negative", "Transfer a valid-vector image with one-bit wrong expected CRC32.", "END_UPDATE returns CRC_MISMATCH and app vector remains erased.", "tests/host/ota/test_ota_host.py;hil/tests/test_ota_crc_failure.py", "READY_HIL_CONDITIONAL"),
    tc("TC-OTA-UPDATE-001", "OTA", "Valid image end-to-end update", "SWRS-OTA-005", "SWE.5", "Target/HIL", "P0", "End-to-end", "Erase, sequentially write, verify and end a known recovery image.", "CRC/vector valid image completes and boots; recovery evidence is retained.", "tests/host/ota/test_ota_host.py;hil/tests/test_ota_update.py", "READY_HIL_CONDITIONAL", "Manual approval, verified recovery image and target power control are available."),
    tc("TC-OTA-GATE-001", "OTA", "Manual approval before target update", "SWRS-OTA-006", "SUP.8", "Process", "P1", "Pipeline inspection", "Evaluate pipeline rules for branch/pipeline sources.", "No target erase/write job starts automatically; protected manual gate is required.", "tests/quality/test_infrastructure.py"),
    tc("TC-OTA-VERSION-001", "OTA", "Firmware downgrade policy", "SWRS-OTA-007", "—", "GAP", "GAP", "Requirement analysis", "Attempt no product update until version contract exists.", "JUnit records GAP_REQUIREMENT, never PASS.", "tests/quality/test_declared_gaps.py", "GAP_REQUIREMENT"),
    tc("TC-OTA-ROLLBACK-001", "OTA", "Boot failure rollback", "SWRS-OTA-008", "—", "GAP/HIL", "GAP", "Requirement analysis", "Attempt no power-cut update until rollback mechanism/recovery is approved.", "JUnit records GAP_REQUIREMENT, never PASS.", "tests/quality/test_declared_gaps.py;hil/tests/test_ota_power_loss.py", "GAP_REQUIREMENT"),
    tc("TC-OTA-XTARGET-001", "OTA", "Wrong ECU image rejection", "SWRS-OTA-009", "—", "GAP", "GAP", "Requirement analysis", "Attempt no cross-target assertion without signed target identity.", "JUnit records GAP_REQUIREMENT, never PASS.", "tests/quality/test_declared_gaps.py", "GAP_REQUIREMENT"),

    tc("TC-INFRA-CM-001", "Infra", "Product SHA artifact and target identity", "SWRS-INFRA-001", "SUP.8", "Process", "P0", "Static/evidence", "Validate full refs then build/hash/verify target image.", "Source SHA, ELF/BIN SHA256 and target verification agree.", "tests/quality/test_infrastructure.py"),
    tc("TC-INFRA-PIPE-001", "Infra", "Ubuntu to Raspberry Pi pipeline topology", "SWRS-INFRA-002", "SUP.8", "Process", "P0", "Pipeline", "Lint CI and run Host then protected HIL stages.", "Jobs use intended runner tags and artifacts flow forward.", "tests/quality/test_infrastructure.py"),
    tc("TC-INFRA-RES-001", "Infra", "Result classification integrity", "SWRS-INFRA-003", "SUP.9", "Process", "P0", "Schema", "Validate every result against the classification enum.", "Product/test/gap/config/infra outcomes remain distinguishable.", "tests/quality/test_infrastructure.py"),
    tc("TC-INFRA-JUNIT-001", "Infra", "JUnit and evidence artifact generation", "SWRS-INFRA-003", "SUP.8", "Process", "P1", "Self-test", "Write PASS, FAIL and GAP sample results and parse XML.", "Counts, failure and skipped nodes are machine-readable.", "tests/quality/test_infrastructure.py"),

    tc("TC-GA-DECODE-001", "Gateway", "Gateway input decoding", "SWRS-GA-001", "SWE.4", "Contract waiting", "P2", "Contract", "No decode stimulus until input schema is approved.", "BLOCKED_INFRA is recorded, not PASS.", "tests/quality/test_gateway_contract.py", "CONTRACT_WAITING"),
    tc("TC-GA-STATE-001", "Gateway", "Gateway state normalization", "SWRS-GA-001", "SWE.5", "Contract waiting", "P2", "Contract", "No state vectors until normalized schema is approved.", "BLOCKED_INFRA is recorded, not PASS.", "tests/quality/test_gateway_contract.py", "CONTRACT_WAITING"),
    tc("TC-GA-STALE-001", "Gateway", "Gateway stale-data handling", "SWRS-GA-001", "SWE.5", "Contract waiting", "P2", "Contract", "No stale timeout is asserted until freshness policy is approved.", "BLOCKED_INFRA is recorded, not PASS.", "tests/quality/test_gateway_contract.py", "CONTRACT_WAITING"),
    tc("TC-GA-INVALID-001", "Gateway", "Gateway invalid-input handling", "SWRS-GA-001", "SWE.4", "Contract waiting", "P2", "Contract", "No malformed vectors until validation rules are approved.", "BLOCKED_INFRA is recorded, not PASS.", "tests/quality/test_gateway_contract.py", "CONTRACT_WAITING"),
    tc("TC-GA-LOG-001", "Gateway", "Gateway diagnostic logging", "SWRS-GA-001", "SWE.5", "Contract waiting", "P2", "Contract", "No log assertion until event and redaction policy is approved.", "BLOCKED_INFRA is recorded, not PASS.", "tests/quality/test_gateway_contract.py", "CONTRACT_WAITING"),
]


def jira_description(case: TestCase) -> str:
    return "\n".join(
        [
            f"Test ID: {case.test_id}",
            f"Requirement: {case.requirement_id}",
            f"ASPICE: {case.aspice} / {case.level}",
            f"Method: {case.method}",
            f"Disposition: {case.disposition}",
            "",
            f"Precondition: {case.precondition}",
            f"Stimulus/Steps: {case.stimulus}",
            f"Expected independent oracle: {case.expected}",
            f"Automation: {case.automation}",
            "",
            "QA/QC: A log or CAN command is not physical-output evidence. Record the required observation layer and classify gaps/blockers explicitly.",
        ]
    )


def write_outputs() -> None:
    if len(CASES) != 54:
        raise RuntimeError(f"reviewed catalog must contain 54 cases, got {len(CASES)}")
    if len({case.test_id for case in CASES}) != len(CASES):
        raise RuntimeError("duplicate test ID")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "source": "Jira_Test_Case_Catalog_BMS_EVSE_OTA_GA_REVIEWED_FINAL.md",
        "test_count": len(CASES),
        "cases": [asdict(case) for case in CASES],
    }
    (OUTPUT / "test_case_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    with (OUTPUT / "jira_test_cases.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["Issue Type", "Summary", "Description", "Priority", "Labels"],
        )
        writer.writeheader()
        for case in CASES:
            writer.writerow(
                {
                    "Issue Type": "Test",
                    "Summary": f"[{case.test_id}] {case.summary}",
                    "Description": jira_description(case),
                    "Priority": {"P0": "Highest", "P1": "High", "P2": "Medium"}.get(case.priority, "Medium"),
                    "Labels": ",".join(
                        ["qa", "aspice", case.area.lower(), case.aspice.lower().replace(".", "-")]
                    ),
                }
            )

    lines = [
        "# Jira Test Case Catalog — Reviewed Final Implementation",
        "",
        f"총 {len(CASES)}개. GPT Reviewed Final을 기준으로 제품 요구사항, 독립 오라클, 자동화 코드를 연결했다.",
        "",
        "> QA/QC: READY는 코드 준비 상태이지 시험 PASS가 아니다. 실제 결과는 고정 SHA/artifact/target 증거로만 승격한다.",
        "",
    ]
    for area in ("BMS", "EVSE", "CAN", "OTA", "Infra", "Gateway"):
        lines.extend([f"## {area}", ""])
        for case in [item for item in CASES if item.area == area]:
            lines.extend(
                [
                    f"### {case.test_id} — {case.summary}",
                    "",
                    f"- Trace: `{case.requirement_id}` / `{case.aspice}` / `{case.level}` / `{case.priority}`",
                    f"- Method / disposition: {case.method} / `{case.disposition}`",
                    f"- Precondition: {case.precondition}",
                    f"- Stimulus: {case.stimulus}",
                    f"- Expected oracle: {case.expected}",
                    f"- Automation: `{case.automation}`",
                    "",
                ]
            )
    (OUTPUT / "Jira_Test_Case_Catalog_IMPLEMENTED_FINAL.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


if __name__ == "__main__":
    write_outputs()
