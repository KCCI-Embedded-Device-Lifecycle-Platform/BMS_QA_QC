# BMS / EVSE / OTA QA Compact Handoff

Updated: 2026-08-18 KST. Use this file as the first context in a new chat.

## Objective

QA repository: `stm32-bms-evse-ota-ga-hil`. Ubuntu Docker Runner performs static/Host/artifact gates; Raspberry Pi 4 + Seeed USB-CAN performs HIL. Gateway work starts after BMS/EVSE/OTA. Evidence follows ASPICE SWE.4/SWE.5 and SUP.8/SUP.9 traceability.

## Pinned product baselines

| Product | SHA / canonical path |
|---|---|
| BMS F446 | `83b1fdf98fa8c5eef792533446826498c36ff030` |
| EVSE F429 CAN | `06f6111e2a4072350ae73af28b3a54e3b6a95a8d` |
| EVSE bench-safe | `a133fbf003be722dc1a1d879e5f7e98639e82e11` |
| OTA platform | `b810605e2a0e610270d4727d95eb108f7eda6a65`; boot path `EVSE_BOOT/EVSE_BOOT` |

Source repos have no authoritative GitLab CI; this QA repo pins, clones, builds, tests and records provenance.

## Decisions that must not drift

- Order: requirements/baseline → Host → artifact identity/layout → passive HIL → actuating HIL → OTA destructive HIL → System.
- A received CAN frame proves bring-up only, not relay/safety PASS.
- Formal HIL requires pinned source SHA, ELF/BIN manifest, target-image verification and physical oracle.
- Result classes: `PASS`, `FAIL_PRODUCT`, `BLOCKED_INFRA`, `GAP_REQUIREMENT`, `MISMATCH_CONFIGURATION`.
- Seeed Analyzer uses python-can `seeedstudio` at `/dev/ttyUSB0`; lack of `can0` is not a product fault. Use `can0` only for an explicitly configured SocketCAN adapter.
- Never run START/STOP, fault injection or OTA erase without fixture interlock and matching `HIL_ALLOW_*` gate.
- Keep Jira-scoped commits separate even when one MR contains several commits.

## Implemented and verified

- MR !1 merged into `develop`; merge SHA `508724afeffc142b599b0dfa306a6359e826f7ec`.
- Merge pipeline `2767778315`: all automatic Host/static/infra jobs PASS; artifact/HIL jobs remain manual by design.
- Fixed: QA imports/API mocks, BMS empty debug macro `-Werror`, OTA app-start requirement constant, EVSE permit-loss setup, JUnit/evidence capture, transient GitLab `get_sources` retry.
- Evidence collector avoids remote URLs/tokens: `tools/capture_qa_evidence.sh`.
- Local quality gate: 7 PASS; 8 expected skips (3 OTA requirement gaps, 5 Gateway contract-waiting). HIL: 15 cases collect successfully; collection is not execution PASS.

## Current blockers / Jira

- `BEOG-50`, `BEOG-90`, `BEOG-92`: Review; complete after MR merge evidence is recorded.
- `BEOG-51` P0: EVSE linker ends at `0x08200000`, overlapping OTA staging at `0x08100000`. Fix product linker before formal artifact/HIL qualification.
- `BEOG-33`, `BEOG-34`, `BEOG-45`: CAN feedback/reject/config decisions remain open.
- `BEOG-37` reception succeeded as bench evidence; `BEOG-48/49` remain open until formal JUnit + target/physical evidence.
- `BEOG-93..97`: Gateway contract waiting; do not fabricate tests.
- EVSE BEOG-67 product-hardening candidate exists only locally at `D:/final_project/.worktrees/evse-beog-67`, commit `ec55e2a`; upstream GitHub push was denied. Do not claim it is in the product baseline.

## Core code and artifacts

- CI: `.gitlab-ci.yml`, `ci/qa-core.yml`
- Baseline: `config/product-baseline.json`, `tools/clone_products.sh`
- Host: `tests/host/{bms,evse,ota}`
- HIL orchestration/adapters: `hil/test_orchestrator.py`, `hil/can_adapter.py`, `hil/openocd_client.py`
- HIL cases: `hil/tests/`
- Artifact gates: `tools/check_linker_layout.py`, `tools/verify_firmware_artifact.py`, `tools/verify_target_image.py`
- Requirements/evidence: `docs/aspice/`, `docs/jira_export/`, `docs/QA_PORTFOLIO_EVIDENCE_GUIDE.md`
- Pipeline artifacts: `junit.xml`, `metadata.json`, product `manifest.json`, ELF/BIN SHA-256.

## Next actions

1. Add merge SHA/pipeline evidence to BEOG-50/90/92; close only after reviewer acceptance.
2. Fix `BEOG-51` in EVSE product repo; update approved SHA deliberately; run `qa_product_artifacts` and close `BEOG-89` only on manifest PASS.
3. On Pi, recreate venv from `requirements-qa.txt`, copy `hil/fixtures/config.example.json` to an untracked bench config, record power-off termination resistance, then run manual `qa_hil_can_infra` on `develop`.
4. After artifact/target identity PASS, run `qa_hil_can_start_stop` for `0x201 → BMS PA8` and then timeout/fault safe-off. OTA erase/update is last.

Do not commit cloned Samba venvs, bench secrets/config, Wi-Fi credentials, Runner tokens or raw USB serials.
