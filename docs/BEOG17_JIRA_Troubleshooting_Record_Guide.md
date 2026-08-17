# BEOG-17 EVSE Relay Verification
## Jira 기록 · Troubleshooting · ASPICE Evidence 운영 가이드

> 대상 프로젝트: `BEOG — BMS/EVSE/OTA/Gateway Verification`  
> 관련 Epic:
> - `BEOG-9` — EVSE Firmware
> - `BEOG-12` — QA, HIL & CI/CD
>
> 관련 Requirement/Test:
> - `BEOG-16` — EVSE Relay Safe-Off Requirement
> - `BEOG-17` — `TC-EVSE-REL-001`, RELAY_CTRL PE11 GPIO Safe-Off Smoke

---

# 1. Jira Architecture

현재 Jira는 다음 구조로 운영하는 것이 좋다.

```text
BEOG-9 EVSE Firmware
├─ BEOG-16 [REQ][EVSE] Relay Safe-Off Requirement
├─ BEOG-17 [TEST][EVSE] RELAY_CTRL PE11 GPIO Safe-Off Smoke
└─ BEOG-19 [TEST][EVSE] CAN → Relay Safe-Off Timing

BEOG-12 QA, HIL & CI/CD
├─ [BUG][TEST-INFRA] OpenOCD / ST-LINK access failure
├─ [BUG][CI] Ubuntu host verification bootstrap failure
├─ [BUG][CONFIG] EVSE target application baseline mismatch
├─ [TASK][QA-INFRA] Build/HIL evidence baseline
└─ [CR][CI] Deterministic CI bootstrap / retry policy
```

핵심 원칙:

```text
Product Requirement/Test
→ BEOG-9 EVSE Firmware

Runner / Docker / OpenOCD / Artifact / Binary mismatch
→ BEOG-12 QA, HIL & CI/CD
```

---

# 2. 전체 QA/HIL Architecture

```text
DEV-PC / Windows
  └─ VSCode
     ├─ QA Python/C Test
     ├─ .gitlab-ci.yml
     └─ Git branch / commit / MR
            │
            ▼
GitLab QA Repository
  ├─ requirements/tests
  ├─ JUnit
  ├─ artifacts/logs
  └─ pipeline
       ├─ Ubuntu BUILD-VM / Docker Runner
       │   ├─ pytest
       │   ├─ gcc
       │   ├─ mock HAL
       │   ├─ relay.c unit
       │   └─ hw_gpio.c unit
       │
       └─ Raspberry Pi HIL-PI / Shell Runner
           ├─ OpenOCD
           ├─ ST-LINK
           ├─ STM32F429ZI
           ├─ register readback
           └─ PE11 Safe-Off
                    │
                    ▼
             NUCLEO-F429ZI
             0x08000000 Boot/OTA
             0x08020000 EVSE App
             RELAY_CTRL = PE11
```

---

# 3. ASPICE Mapping

| 항목 | Process | 의미 |
|---|---|---|
| BEOG-16 Requirement | SWE.1 | Software Requirement |
| Ubuntu relay.c/hw_gpio.c Host Unit | SWE.4 | Unit Verification |
| BEOG-17 Target GPIO/HIL | SWE.5 | Component/Integration Verification |
| Commit/SHA/ELF/Target image | SUP.8 | Configuration Management |
| CI/OpenOCD/Binary mismatch RCA | SUP.9 | Problem Resolution |
| CI/Test Harness/Config 변경 | SUP.10 | Change Request |
| 이후 CAN→Safety→Relay timing | SWE.6 | Integrated SW Verification |

---

# 4. BEOG-17에는 무엇을 남길까

BEOG-17은 Test Record다.

Description에는 다음을 유지한다.

```text
Test ID
Related Requirement
Objective
Target
Environment
Preconditions
Procedure
Expected
Pass/Fail Criteria
Canonical Artifact Names
Result
Evidence
Limitation
```

긴 Troubleshooting 명령/로그는 BEOG-17 Description에 몰아넣지 않는다.

대신 아래처럼 요약한다.

```markdown
## Troubleshooting Summary

During verification setup, TC-EVSE-REL-001 was blocked by
test-infrastructure/configuration issues before final verification.

Resolved:
- Ubuntu host-test dependency bootstrap
- OpenOCD/ST-LINK access ownership
- Boot/Application execution-target mismatch
- EVSE target application binary baseline mismatch

Detailed problem records:
- <Jira problem key>
- <Jira problem key>
- <Jira problem key>

Final re-verification:
PASS

Evidence:
- GitLab Pipeline: ...
- JUnit: reports/evse-relay-pe11-smoke.xml
- Log: logs/evse-relay-pe11-smoke.log
```

---

# 5. 이번에 별도 Jira Problem으로 남길 항목

## Problem A — 가장 중요

Summary:

```text
[BUG][CONFIG] EVSE HIL target application does not match approved BEOG-17 baseline
```

Parent:

```text
BEOG-12 QA, HIL & CI/CD
```

ASPICE Dropdown:

```text
SUP.9
```

Related:

```text
SUP.8 / SWE.5
```

Description:

```markdown
## Problem ID
PR-EVSE-HIL-001

## Detected By
BEOG-17 / TC-EVSE-REL-001

## Symptom
Initial HIL verification reported:

GPIOE clock disabled
RCC_AHB1ENR = 0x0010008A

## Initial Hypotheses
1. PE11 register mask error
2. MX_GPIO_Init() not executed
3. HardFault / Error_Handler
4. Wrong firmware flashed
5. Boot/Application execution mismatch

## Investigation

### ST-LINK/SWD
OpenOCD detected:
- STLINK V2J47M34
- Target voltage ≈3.24V
- Cortex-M4
- Examination succeed

Conclusion:
Probe/USB path was not the root cause.

### Boot/Application Vector
BOOT:
- Base: 0x08000000
- SP: 0x20030000
- PC: 0x08003471

APP:
- Base: 0x08020000
- SP: 0x20030000
- PC: 0x0802749D / later approved image vector changed

### Exact Product Build
Approved Product Commit:
a133fbf003be722dc1a1d879e5f7e98639e82e11

Commands:
cmake --preset Debug
cmake --build --preset Debug

Result:
PASS

Artifact:
build/Debug/bms_esev.elf

### Binary Verification
OpenOCD:
verify_image /tmp/beog17_bms_esev.elf

Result:
FAIL

More than 128 differences found starting from vector table.

## Root Cause
The EVSE application already programmed on the HIL target
did not match the approved product baseline used by BEOG-17.

The HIL test was therefore not testing the same binary as
the Ubuntu verification jobs.

## Impact
- Test result was not configuration-controlled.
- GPIO result could not be attributed to the approved EVSE commit.
- TC-EVSE-REL-001 was BLOCKED.
- Product defect classification would have been invalid.

## Corrective Action
1. Existing flash backup
2. Exact EVSE commit rebuild
3. ELF/BIN SHA256 record
4. Approved ELF programming
5. verify_image re-run
6. Application vector recheck
7. TC-EVSE-REL-001 re-run

## Preventive Action
Future HIL evidence chain:

Product Commit
→ Firmware Artifact
→ SHA256
→ Flash/verify
→ HIL Test
→ JUnit/Artifact

HIL result is not accepted if firmware identity cannot be established.

## Re-verification
TC-EVSE-REL-001
Pipeline: <URL>
Result: PASS

## Classification
Test Infrastructure / Configuration Management
Not a Product Relay defect.
```

---

# 6. Problem B — Boot/App 실행 컨텍스트 오류

Summary:

```text
[BUG][TEST-INFRA] BEOG-17 HIL observed boot image instead of EVSE application
```

Parent:

```text
BEOG-12
```

ASPICE:

```text
Primary: SUP.9
Related: SUP.8 / SWE.5
```

Description:

```markdown
## Problem ID
PR-EVSE-HIL-002

## Detected By
BEOG-17 / TC-EVSE-REL-001

## Symptom
Initial procedure:

reset run
sleep 1000
halt
GPIOE register read

Observed PC:
0x08000E2A

Expected EVSE Application region:
0x08020000 ~

## Investigation
EVSE linker script:
Application FLASH ORIGIN = 0x08020000

Target reset enters:
0x08000000 Boot/OTA image

Therefore reset-run did not guarantee application entry.

## Root Cause
The HIL test assumed that target reset directly executed
the EVSE application.

Actual memory architecture:
0x08000000 = Boot/OTA
0x08020000 = EVSE Application

The test observed the wrong execution context.

## Corrective Action
Application-only HIL setup:

1. reset halt
2. read APP_SP @0x08020000
3. read APP_PC @0x08020004
4. VTOR = 0x08020000
5. MSP = APP_SP
6. PC = APP_ENTRY
7. resume
8. wait
9. halt
10. verify GPIOE / PE11

## Re-verification
Application running PC = 0x0802xxxx
VTOR = 0x08020000
GPIOE clock = ON
PE11 = Output / Safe-Off LOW
Result = PASS

## Scope
Direct launch is Test Harness setup.
Bootloader → Application handoff is NOT verified here.
It belongs to OTA/System Integration testing.
```

---

# 7. Problem C — Ubuntu Host Verification Bootstrap

Summary:

```text
[BUG][CI] Ubuntu EVSE host verification environment incomplete
```

Parent:

```text
BEOG-12
```

ASPICE:

```text
Primary: SUP.9
Related: SUP.8 / SUP.10
```

Description:

```markdown
## Problem ID
PR-QA-CI-001

## Related Verification
BEOG-17
GitLab Job: evse_relay_host_unit

## Architecture
GitLab
→ Ubuntu 24.04 VirtualBox
→ Docker Runner
→ python:3.11-slim-bookworm
→ pytest
→ host gcc
→ EVSE relay.c / hw_gpio.c

## Incident Timeline

### I-01 pytest missing

Symptom:
No module named pytest

Root Cause:
python:3.11-slim-bookworm did not contain pytest and
CI bootstrap did not install it.

Corrective Action:
python -m pip install --no-cache-dir pytest==8.3.5


### I-02 C standard headers missing

Symptom:
stdio.h / stdint.h / math.h not found

Root Cause:
Compiler executable existed but complete host C development
environment was not provisioned.

Corrective Action:
Install build-essential.


### I-03 apt install syntax failure

Symptom:
Unable to locate package  build-essential
Unable to locate package  git
Unable to locate package  ca-certificates

Observed command:
apt-get install ... \ build-essential \ git \ ca-certificates

Root Cause:
Backslash escaped whitespace instead of continuing a shell line.

Corrective Action:
Use a simple single-line apt command or YAML block with
backslash-newline.

## Final Result
TC-EVSE-REL-U001 PASS
TC-EVSE-REL-U002 PASS

JUnit:
reports/evse-relay-host.xml

Log:
logs/evse-relay-host.log

## Preventive Action
- Pin pytest version
- C compiler/header preflight
- Simple package-install syntax
- Later migrate to versioned QA toolchain image
```

---

# 8. GitLab Source Fetch transient

한 번 발생하고 Retry에서 성공했다면 별도 Bug를 만들지 않아도 된다.

BEOG-12 또는 BEOG-17 Comment:

```markdown
## CI Infrastructure Observation

Initial pipeline failed during GitLab source checkout:

Failed to connect to gitlab.com:443

Failure occurred before `step_script`,
therefore Product/Test execution did not start.

Classification:
CI infrastructure / transient source-fetch failure

Product Test Result:
NOT EXECUTED

Retry:
PASS

Preventive Action:
GET_SOURCES_ATTEMPTS=3

Policy:
Do not automatically retry real script/test assertion failures.
```

반복되면 별도 Jira Bug로 격상한다.

---

# 9. OpenOCD `Error: open failed`

Summary 예:

```text
[BUG][TEST-INFRA] HIL runner could not exclusively open ST-LINK
```

핵심 기록:

```markdown
## Symptom
OpenOCD:
Error: open failed

## Layer
USB / ST-LINK adapter layer

Failure occurred before:
- target examination
- GPIO verification
- firmware verification

## Investigation
Checked:
- competing IDE debugger
- another OpenOCD/st-util
- USB enumeration
- gitlab-runner permissions

## Re-verification
sudo -u gitlab-runner openocd ...

Result:
STLINK detected
SWD DPIDR detected
Cortex-M4 detected
Examination succeed
Target halt PASS

## Classification
Probe ownership / HIL environment
Not Product firmware.
```

---

# 10. Jira와 Markdown 역할 분리

## Markdown 파일

권장 파일:

```text
docs/06_problems/PR-EVSE-BEOG17-Troubleshooting.md
```

여기에 남길 것:

```text
Architecture
전체 Timeline
실행 명령
원인 분석 과정
Before/After
로그 일부
Lessons Learned
```

## Jira

Jira에는:

```text
Symptom
Impact
Root Cause
Corrective Action
Preventive Action
Re-test
Links
Status
```

만 요약한다.

Jira Description 또는 Comment에:

```text
Canonical RCA:
docs/06_problems/PR-EVSE-BEOG17-Troubleshooting.md
```

를 링크한다.

---

# 11. Jira Link 구조

```text
BEOG-16 Requirement
   │
   │ verified by
   ▼
BEOG-17 Test
   │
   ├── blocked by → PR-EVSE-HIL-001
   ├── blocked by → PR-EVSE-HIL-002
   └── relates to → PR-QA-CI-001
                         │
                         │ resolved by
                         ▼
                    Config/Test changes
                         │
                         │ re-tested by
                         ▼
                    BEOG-17 Pipeline PASS
```

Custom Link가 없다면 `blocks / is blocked by / relates to`를 사용한다.

---

# 12. Problem Workflow

```text
Open
→ Analysis
→ Root Cause Confirmed
→ Fix In Progress
→ Re-test
→ Closed
```

각 단계:

```text
Open:
Symptom/Evidence 확보

Analysis:
Hypothesis와 Layer 분리

Root Cause Confirmed:
재현 및 증거 확보

Fix In Progress:
CI/Test/Config 수정

Re-test:
동일 조건 재검증

Closed:
PASS Evidence + Preventive Action 기록
```

---

# 13. BEOG-17 Final Verification Comment

```markdown
## Final Verification Result

Test ID:
TC-EVSE-REL-001

Result:
PASS

## Verification Layers

### Host / SWE.4
TC-EVSE-REL-U001: PASS
TC-EVSE-REL-U002: PASS

### Target / SWE.5
EVSE Application direct launch: PASS
VTOR: 0x08020000
GPIOE clock: PASS
RELAY_CTRL: PE11
PE11 Mode: Output
PE11 Output: LOW / Safe-Off

## Configuration Evidence

Product Commit:
a133fbf003be722dc1a1d879e5f7e98639e82e11

Firmware Artifact:
bms_esev.elf

Firmware SHA256:
<actual>

Target Application Binary:
verified/programmed from approved baseline

## CI Evidence

Pipeline:
<URL>

JUnit Host:
reports/evse-relay-host.xml

JUnit HIL:
reports/evse-relay-pe11-smoke.xml

HIL Log:
logs/evse-relay-pe11-smoke.log

OpenOCD:
logs/openocd-preflight.log

## Problems Resolved

- <PR-EVSE-HIL-001 Jira>
- <PR-EVSE-HIL-002 Jira>
- <PR-QA-CI-001 Jira>

## Limitation

This test does not verify:
- BMS CAN 0x100
- charge_permit=0 transition
- ≤200 ms response timing
- physical contactor opening

These remain for TC-EVSE-REL-002 / system HIL.
```

---

# 14. BEOG-16 상태

BEOG-17 PASS 후에도:

```text
BEOG-16 Verification Status = Partially Covered
```

가 맞다.

미검증:

```text
CAN 0x100
→ charge_permit=0
→ Safety Logic
→ Relay OFF
→ ≤200 ms
```

---

# 15. 포트폴리오에서 보여줄 대표 Troubleshooting 3개

## 1. Firmware Baseline Mismatch

```text
Target binary
≠
Approved Product Artifact
→ verify_image로 검출
→ exact build/flash/verify
```

역량:

```text
SUP.8
Configuration Management
HIL reproducibility
```

## 2. Boot/App Execution Context

```text
Reset → Boot
Test는 App 실행이라고 가정
→ wrong context
→ Vector/VTOR/MSP/PC 분석
→ App direct launch
```

역량:

```text
Embedded memory architecture
Bootloader/Application
HIL test design
SUP.9 RCA
```

## 3. Host CI Toolchain Bring-up

```text
pytest missing
C headers missing
apt syntax issue
→ deterministic bootstrap
```

역량:

```text
Docker
GitLab CI
C Host Unit Test
failure-layer classification
```

---

# 16. 면접용 설명

> EVSE Relay HIL 시험 초기에는 GPIOE clock이 꺼져 있다는 Assertion이 발생했습니다. 처음부터 Product Bug로 판단하지 않고 ST-LINK, CPU 실행 상태, Boot/Application vector, firmware binary identity 순으로 계층을 분리해 조사했습니다. 그 결과 MCU reset은 0x08000000 Boot image를 실행하는 반면 EVSE Application은 0x08020000에 위치했고, Target Application도 승인된 GitHub commit으로 빌드한 ELF와 verify_image가 불일치했습니다. 이를 Configuration Management 문제로 분류하고 exact commit build, artifact hash, flash/verify, application direct-launch 순으로 Test Setup을 정리한 뒤 PE11 Safe-Off를 재검증했습니다. CI 환경 오류와 Product Verification 실패도 분리하여 Jira Problem과 GitLab Evidence를 연결했습니다.

---

# 17. 완료 Checklist

```text
[ ] Ubuntu U001 PASS
[ ] Ubuntu U002 PASS
[ ] Product Commit 기록
[ ] CMake Cross-build PASS
[ ] ELF/BIN 생성
[ ] Firmware SHA 기록
[ ] Target Binary identity 확인
[ ] ST-LINK/OpenOCD PASS
[ ] Application execution context 확인
[ ] VTOR 0x08020000
[ ] GPIOE Clock PASS
[ ] PE11 Output PASS
[ ] PE11 Safe-Off LOW PASS
[ ] GitLab 3 Jobs PASS
[ ] JUnit Host 업로드
[ ] JUnit HIL 업로드
[ ] HIL Log 업로드
[ ] Jira Problem RCA 작성
[ ] Corrective Action 기록
[ ] Preventive Action 기록
[ ] Re-test Pipeline 링크
[ ] BEOG-17 Result PASS
[ ] BEOG-16은 Partially Covered 유지
```
