# BEOG 다음 Pipeline / Jira 작업안

작성 기준: 2026-08-16
대상 브랜치: 각 BEOG 브랜치에서 검증 후 `develop` Merge Request
장비: Ubuntu Docker Runner, Raspberry Pi 4, Seeed USB-CAN Analyzer, BMS F446, EVSE F429ZI

## QA 판단

현재 벤치에서 CAN 수신이 확인된 것은 중요한 진전이지만, 이것만으로 START/STOP 또는
Safe-Off 요구사항을 PASS 처리할 수는 없다. CAN Analyzer가 본 프레임, ECU 상태 전이,
EVSE PE11, BMS PA8의 물리 출력을 서로 다른 증거로 남겨야 한다.

`rasp_samba/test_evse_start_stop_bms_relay.py`는 현장 관찰용으로는 유용하지만 기대 전이가
없어도 종료코드 0을 반환하고 JUnit을 만들지 않는다. 따라서 공식 Pipeline oracle로
사용하지 않고, 재현 가능한 pytest HIL 코드로 승격한다.

## 권장 Jira / Commit 순서

| 순서 | Jira | 제목 | Branch | Squash commit | Pipeline verdict |
|---:|---|---|---|---|---|
| 1 | 기존 `BEOG-48` | `[INFRA][HIL] Raspberry Pi CAN Analyzer 3-node acceptance` | `test/BEOG-48-pi-can-acceptance` | `[BEOG-48] add Pi CAN analyzer bus and heartbeat acceptance` | 인프라 PASS/BLOCKED |
| 2 | `BEOG-50` | `[QA][ASPICE] SWE traceability and Host verification baseline` | `test/BEOG-50-qa-framework` | `[BEOG-50] add ASPICE traceability and QA automation framework` | 제품 로직 Host PASS/FAIL |
| 3 | `BEOG-51` | `[BUG][EVSE] App flash region overlaps OTA staging boundary` | 제품 저장소의 `fix/BEOG-51-evse-flash-layout` | `[BEOG-51] constrain EVSE app below OTA staging region` | 구성 PASS/FAIL |
| 4 | 기존 `BEOG-49` | `[TEST][E2E] EVSE START/STOP to BMS PA8 relay HIL` | `test/BEOG-49-start-stop-relay-e2e` | `[BEOG-49] verify START STOP through BMS relay E2E` | System HIL PASS/FAIL |
| 5 | 기존 `BEOG-19` | `[TEST][SAFETY] BMS timeout to EVSE PE11 Safe-Off timing` | `test/BEOG-19-can-relay-safe-off` | `[BEOG-19] verify CAN timeout drives EVSE relay safe off` | Safety HIL PASS/FAIL |
| 6 | 신규 `BEOG-OO` | `[TEST][SAFETY] Critical BMS fault to dual-ECU Safe-Off HIL` | `test/BEOG-OO-bms-fault-safe-off` | `[BEOG-OO] verify critical BMS fault converges to safe off` | System safety PASS/FAIL |
| 7 | 신규 `BEOG-OO` | `[TEST][EVSE] OLED I2C diagnostic display verification` | `test/BEOG-OO-evse-oled-diagnostic` | `[BEOG-OO] add EVSE OLED diagnostic HIL evidence` | 진단 표시 PASS/FAIL |

남은 `BEOG-OO`는 Jira 생성 후 실제 번호로 교체한다. BEOG-48/49/19가 이미 같은 범위로
존재한다면 새 이슈를 만들지 않고 기존 이슈의 Sub-task 또는 Test로 연결한다.

## 1. BEOG-48 복사/붙여넣기 본문

### 목적

Raspberry Pi 4와 USB-CAN Analyzer가 BMS/EVSE의 500 kbit/s Classic CAN 프레임을
동시에 안정적으로 관찰할 수 있는지 확인한다. 이 시험은 제품 기능 PASS가 아니라 이후
HIL 시험을 수행할 수 있다는 인프라 수용 조건을 증명한다.

### 제가 이 검증을 선택한 이유

처음에는 프레임 한 개를 수신하면 CAN 연결이 완료된 것으로 생각했다. 하지만 QA 관점에서
한 노드의 단발 수신과 두 ECU의 지속 통신은 다른 증거라는 것을 확인했다. 그래서 종단저항,
양쪽 ID 범위, 주기성, error frame을 함께 확인하도록 시험을 구성했다.

### Acceptance criteria

- 전원 OFF 상태의 종단저항 측정값이 54~66 ohm이고 설정 파일에 기록된다.
- BMS `0x100~0x105`와 EVSE `0x200~0x202`가 3초 동안 모두 관찰된다.
- 승인된 100/500/1000 ms 주기가 허용오차 안에 있다.
- 관찰 구간의 CAN error frame은 0개다.
- GitLab JUnit, 설정 SHA-256, QA commit, Runner 정보가 artifact로 남는다.
- 실패는 제품 결함으로 단정하지 않고 `BLOCKED_INFRA` 또는 인프라 FAIL로 분류한다.

### 핵심 역할

이 이슈는 이후 BEOG-49/19에서 발생한 실패를 CAN 배선·Analyzer 문제와 제품 로직 문제로
분리하는 기준점이다. 안전 시험 전에 반드시 통과해야 하는 Entry gate다.

### Commit 대상

- `hil/can_adapter.py`
- `hil/test_orchestrator.py`
- `hil/tests/conftest.py`
- `hil/tests/support.py`
- `hil/tests/test_can_bus_acceptance.py`
- `hil/tests/test_can_timeout.py`의 `TC-CAN-HB-001`
- `hil/fixtures/config.example.json`
- `ci/qa-core.yml`의 `qa_hil_can_infra`

## 2. BEOG-50 Host/ASPICE baseline 본문

### 목적

Ubuntu Docker Runner에서 BMS/EVSE/CAN/OTA의 순수 C 로직과 QA 독립 oracle을 빌드하여
SWE.4 증거를 만들고, SWRS-시험코드-JUnit-Artifact 연결을 RTM으로 관리한다.

### 제가 이 검증을 선택한 이유

HIL만 사용하면 작은 경계값 오류도 실제 보드 상태와 섞여 원인 분석이 늦어진다고 판단했다.
먼저 Host에서 결정표, 경계값, 잘못된 DLC/Endian을 빠르게 검증하고, HIL은 물리 출력과
통합 동작에 집중시키는 편이 신입 엔지니어인 제가 결함을 더 명확하게 설명하는 방법이라고
생각했다.

### Acceptance criteria

- 제품 저장소는 branch 이름이 아니라 승인된 full SHA로 clone된다.
- C harness는 warning을 error로 취급하고 BMS fault/FSM, EVSE FSM/safety/input,
  CAN DLC/endian/unknown ID, OTA CRC/bounds를 검증한다.
- 54개 Test ID의 Requirement, ASPICE level, automation path, disposition이 누락되지 않는다.
- JUnit과 RTM을 Pipeline artifact로 보존한다.
- 미구현 요구사항은 PASS로 숨기지 않고 `GAP_REQUIREMENT`로 공개한다.

### Commit 대상

- `firmware/`, `bootloader/`
- `tests/host/bms`, `tests/host/common`, 선택된 `tests/host/evse`, `tests/host/ota`
- `tests/quality/`
- `docs/aspice/`, `docs/jira_export/`
- `config/product-baseline.json`, `requirements-qa.txt`, `pyproject.toml`
- `docker/Dockerfile.toolchain`, `tools/`, `ci/qa-core.yml`의 static/Host jobs

## 3. BEOG-51 EVSE flash layout Bug 본문

### 관찰

EVSE application은 `0x08020000`에서 시작하지만 현재 linker FLASH 끝이 `0x08200000`이다.
OTA staging 시작 `0x08100000`과 겹치므로, 현재 QA artifact gate는 의도적으로 실패한다.

### Acceptance criteria

- EVSE application 영역은 `0x08020000..<0x08100000`으로 제한된다.
- `.bin` 크기는 최대 `0xE0000`이고 reset vector는 application 영역 안이다.
- bootloader staging/metadata 영역과 겹치지 않는다.
- 수정 SHA로 Ubuntu cross-build와 manifest/size/vector gate가 PASS한다.

### QA 의견

Pipeline을 초록색으로 만들기 위해 checker를 완화하면 OTA erase 시 application 손상 위험을
숨기게 된다. 이 항목은 테스트 실패가 아니라 제품 구성 불일치로 처리하고, 해결 전에는
정식 HIL의 target provenance를 승인하지 않는다.

## 4. BEOG-49 복사/붙여넣기 본문

### 목적

EVSE START/STOP 입력이 CAN `0x201`을 거쳐 BMS 상태와 PA8 relay 물리 출력까지 올바른
순서로 전달되는지 검증한다.

### Acceptance criteria

- 전기적으로 절연된 Pi 제어 actuator가 PE13 START와 PF13 STOP을 재현한다.
- START 후 `0x201=1`, BMS permit/state, EVSE charging/relay command가 순서대로 관찰된다.
- OpenOCD 또는 절연 feedback으로 BMS PA8 HIGH를 확인한다.
- STOP 후 `0x201=0`, EVSE relay OFF, BMS IDLE, PA8 LOW를 확인한다.
- 실행 전 hard interlock, current limit, no-load 조건을 확인한다.
- 대상 BMS/EVSE image는 Pipeline artifact와 `verify_image`로 일치해야 한다.

### 제가 중요하게 본 부분

OLED의 CHARGING 표시나 CAN relay command만으로 실제 relay 동작을 대신 판정하지 않는다.
사용자 입력, 통신, 상태머신, 물리 출력 네 지점을 한 타임라인에 묶는 것이 이 시험의
핵심이라고 생각한다.

### Commit 대상

- `hil/power_fault_controller.py`
- `hil/openocd_client.py`
- `hil/tests/test_can_e2e.py`의 `TC-CAN-E2E-002`
- `ci/qa-core.yml`의 `qa_hil_can_start_stop`

## 5. BEOG-19 / Safe-Off 본문

### 목적

BMS main frame 중단 또는 permit 상실 때 EVSE가 요구 시간 안에 relay command와 PE11을
LOW로 만드는지 검증한다.

### Acceptance criteria

- 승인된 fault fixture로 BMS TX를 중단하고 마지막 정상 frame부터 시간을 측정한다.
- EVSE timeout 기준과 측정 허용범위는 requirement owner의 승인값을 사용한다.
- CAN `0x200` relay OFF와 GPIOE ODR PE11 LOW를 모두 확인한다.
- fault 복구 후 정상 통신 재개 증거를 남긴다.
- CFSR/HFSR가 0인지 assertion하며, 판정 전 target을 resume하지 않는다.

### QA 의견

현재 BMS link timeout은 공통 confirm count 때문에 문서의 1000 ms보다 늦어질 가능성이 있다.
실측 결과가 다르더라도 허용범위를 임의로 넓히지 않고 `FAIL_PRODUCT` 후보와 요구사항
불일치를 분리해 보고한다.

## OLED 시험의 위치

OLED는 운영자 진단과 상태 가시성에는 중요하지만 relay Safe-Off의 독립 oracle은 아니다.
BEOG-49가 끝난 뒤 별도 P2 항목으로 두고, 알려진 상태마다 I2C ACK/driver 상태와 화면 문구를
확인한다. 화면이 맞아도 CAN/PA8/PE11 증거가 없으면 safety PASS로 사용하지 않는다.

## Merge / 실행 규칙

1. 현재 `test/BEOG-17-evse-relay-pe11-smoke` 변경을 먼저 MR로 `develop`에 반영한다.
2. 새 Jira 번호가 확정되면 `develop`에서 각 `test/BEOG-<번호>-...` 브랜치를 만든다.
3. BEOG-48에서는 `qa_static`, `qa_host_tests`, 수동 `qa_hil_can_infra`까지만 실행한다.
4. EVSE flash layout P0가 해결된 뒤 `qa_product_artifacts`를 실행한다.
5. 자동 actuator와 hard interlock가 준비된 뒤에만 `qa_hil_can_start_stop`을 실행한다.
6. OTA/power-loss와 bus-off는 현재 벤치 범위를 넘으므로 이번 CAN Pipeline에 섞지 않는다.
7. 최종 MR은 Jira 번호로 squash하고 JUnit/manifest/raw log 링크를 Jira에 남긴다.

## 이번 Commit에서 제외할 파일

- `rasp_samba/bms-can-venv/`: 장비별 가상환경이며 재현 가능한 dependency가 아니다.
- `rasp_samba/f429_flash_before_beog17.bin`: 2 MiB raw flash backup으로 Git 이력에 넣지 않는다.
- `rasp_samba/send_cantest.py`: 정의되지 않은 `0x300`을 전송하므로 제품 acceptance가 아니다.
- `docs/BEOG17_JIRA_Troubleshooting_Record_Guide.md`: 기존 사용자 작업물이며 별도 검토 없이
  새 BEOG commit에 포함하지 않는다.
