# BEOG Jira / Git Branch / Commit 작성 가이드

문서 목적: BMS-EVSE-OTA QA 변경을 Jira 단위로 추적하고, 여러 branch가 같은 CI/HIL
파일을 수정할 때 이력과 merge conflict를 안전하게 관리한다.

## 1. 결론

- 수정 파일이 많다는 이유로 한 번에 commit하지 않는다.
- **한 Jira = 한 검증 목적 = 한 branch/Merge Request**를 기본으로 한다.
- 한 branch 안에서는 1~3개의 논리적 commit을 허용한다.
- 최종 merge 시 GitLab의 Squash를 사용하면 `develop`에는 Jira별 commit 하나가 남는다.
- 같은 파일은 여러 branch에서 반복해서 수정하고 commit할 수 있다. Git은 파일을 잠그지 않는다.
- 문제는 “같은 파일”이 아니라, 공통 기준점 이후 **같은 줄을 서로 다르게 수정했을 때** 생기는
  merge conflict다.

## 2. 이번 저장소의 권장 순서

```text
develop
  └─ test/BEOG-50-qa-framework
       └─ merge to develop
            └─ test/BEOG-48-pi-can-acceptance
                 └─ merge to develop
                      └─ test/BEOG-49-start-stop-relay-e2e
                           └─ merge to develop
                                └─ test/BEOG-19-can-relay-safe-off
```

BEOG-50은 RTM, 54개 카탈로그, Host/HIL scaffold와 CI가 서로 참조하는 최초 기준선이다.
따라서 이 최초 도입은 파일 수가 많아도 하나의 foundation commit으로 관리한다. 이후
BEOG-48/49/19가 `ci/qa-core.yml`, `hil/test_orchestrator.py`, HIL fixture를 공통으로
수정하므로 위처럼 순차적으로 branch를 만들면 conflict가 가장 적다.

병렬 개발이 꼭 필요하면 BEOG-49를 BEOG-48 branch에서 분기하는 stacked branch로 만든다.
BEOG-49 Merge Request의 임시 target을 BEOG-48로 두고, BEOG-48이 `develop`에 merge된 뒤
BEOG-49를 최신 `develop`으로 rebase하여 target을 다시 `develop`으로 바꾼다.

## 3. 같은 파일이 여러 branch에 있을 때

예를 들어 두 Jira가 모두 `ci/qa-core.yml`을 수정해도 commit은 정상적으로 가능하다.

```text
develop:             qa_static + qa_host_tests
BEOG-48 branch:      + qa_hil_can_infra
BEOG-49 branch:      + qa_hil_can_start_stop
```

BEOG-48이 먼저 merge된 후 BEOG-49를 최신 `develop`에서 만들면 최종 파일에는 두 job이 모두
존재한다. 독립된 오래된 `develop`에서 두 branch를 동시에 만든 경우에도 서로 다른 줄을
수정했다면 Git이 자동 병합한다. 같은 YAML 블록이나 같은 Python selector 줄을 다르게
수정했다면 conflict가 발생하며, 최종 의도인 두 기능을 모두 남기도록 사람이 해결해야 한다.

따라서 다음 행동은 피한다.

- 먼저 merge된 branch의 변경을 다른 branch에서 수동으로 다시 복사하기
- `git add .`로 다른 Jira의 파일까지 한꺼번에 staging하기
- conflict 해결을 위해 한쪽 파일 전체를 무조건 선택하기
- 동일한 patch를 두 branch에서 각각 merge한 뒤 다시 cherry-pick하기

## 4. Jira별 권장 commit 구성

### BEOG-48

Branch: `test/BEOG-48-pi-can-acceptance`

```text
[BEOG-48] add CAN analyzer adapter abstraction
[BEOG-48] add three-node and heartbeat HIL tests
[BEOG-48] integrate Pi CAN infrastructure evidence job
```

최종 Squash commit:

```text
[BEOG-48] add Pi CAN analyzer bus and heartbeat acceptance
```

포함 범위:

- `hil/can_adapter.py`
- `hil/test_orchestrator.py`의 `can-infra`
- `hil/tests/test_can_bus_acceptance.py`
- `hil/tests/test_can_timeout.py`의 heartbeat case
- `hil/fixtures/config.example.json`
- `ci/qa-core.yml`의 `qa_hil_can_infra`
- 직접 연관된 Test Specification/RTM 항목

### BEOG-49

Branch: `test/BEOG-49-start-stop-relay-e2e`

```text
[BEOG-49] add isolated START STOP fixture control
[BEOG-49] verify CAN state sequence and BMS PA8 output
[BEOG-49] add formal target provenance and JUnit evidence
```

최종 Squash commit:

```text
[BEOG-49] verify START STOP through BMS relay E2E
```

BEOG-48의 adapter/orchestrator 파일을 다시 새 파일처럼 commit하는 것이 아니다. 최신
`develop`에 이미 있는 내용을 기준으로 `can-start-stop` selector와 E2E job에 필요한 diff만
commit한다.

### BEOG-19

Branch: `test/BEOG-19-can-relay-safe-off`

```text
[BEOG-19] add controlled CAN silence and recovery fixture
[BEOG-19] verify BMS timeout drives EVSE PE11 safe off
[BEOG-19] record timing and fault-register evidence
```

최종 Squash commit:

```text
[BEOG-19] verify CAN timeout drives EVSE relay safe off
```

### ASPICE/Host baseline 신규 Jira

이 변경은 BEOG-48과 목적이 다르므로 별도 Jira/branch로 분리한다.

```text
[BEOG-OO] add ASPICE requirements and test traceability
[BEOG-OO] add native BMS EVSE CAN host verification
[BEOG-OO] add Ubuntu static and host evidence jobs
```

최종 Squash commit:

```text
[BEOG-OO] add ASPICE traceability and native host verification
```

## 5. 안전한 staging 방법

현재 작업 폴더처럼 여러 Jira의 변경이 섞여 있으면 파일을 명시해서 staging한다.

```bash
git status --short
git diff -- ci/qa-core.yml
git diff -- hil/test_orchestrator.py
git add hil/can_adapter.py
git add hil/tests/test_can_bus_acceptance.py
git add hil/tests/test_can_timeout.py
git add hil/fixtures/config.example.json
git add ci/qa-core.yml
git diff --cached --check
git diff --cached --stat
git diff --cached
```

한 파일 안에 여러 Jira 변경이 섞였다면 `git add -p <file>`로 hunk 단위 staging이 가능하다.
다만 YAML job이나 Python selector처럼 서로 의존하는 hunk를 잘못 분리하면 중간 commit이
동작하지 않을 수 있다. 각 commit 자체가 lint/수집/테스트를 통과하는지 확인한다.

`docs/BEOG17_JIRA_Troubleshooting_Record_Guide.md`, firmware backup `.bin`, Pi의 virtualenv는
현재 신규 BEOG commit에 포함하지 않는다.

## 6. Jira Description 작성 구조

### Summary

```text
[TEST][HIL] Raspberry Pi CAN Analyzer 3-node acceptance
```

### Description

```markdown
## 배경
현재 BMS/EVSE 프레임 수신은 확인했지만, 단발 수신만으로 3-node HIL 환경이 안정적이라고
판단하기 어렵다.

## 제가 확인하고 싶은 부분
처음에는 CAN frame이 보이면 연결 검증이 끝났다고 생각했다. 검토 과정에서 종단저항,
두 ECU의 주기 frame, error frame까지 확인해야 이후 제품 결함과 장비 문제를 분리할 수
있다고 판단했다.

## 목적
Pi CAN Analyzer가 승인된 500 kbit/s bus에서 BMS와 EVSE를 동시에 안정적으로 관찰함을
증명한다.

## Traceability
- Requirement: SWRS-CAN-001, SWRS-CAN-005
- Test: TC-CAN-BUS-001, TC-CAN-HB-001
- ASPICE: SYS.4, SWE.5, SUP.8

## 환경/Baseline
- QA commit: <full SHA>
- BMS commit: <full SHA>
- EVSE commit: <full SHA>
- Runner/Adapter: <runner name>, Seeed USB-CAN `/dev/ttyUSB0`
- Bitrate: 500000

## Acceptance Criteria
- 종단저항 54~66 ohm
- BMS 0x100~0x105 및 EVSE 0x200~0x202 관찰
- 승인된 주기 허용오차 만족
- CAN error frame 0개
- JUnit/config SHA/runner evidence 보존

## 결과 분류
PASS / FAIL_PRODUCT / FAIL_TEST / BLOCKED_INFRA / MISMATCH_CONFIGURATION 중 하나로 기록한다.

## Safety
본 시험은 relay actuation이 없는 수동 관찰 시험이다. 전원 OFF에서 종단저항을 먼저
측정하고 공통 GND와 비상 차단 상태를 확인한다.
```

## 7. 2년차 엔지니어다운 작성 방식

좋은 Jira는 경험을 과장하지 않고, 관찰과 판단을 분리한다.

권장 표현:

- “수신은 확인했으나 물리 출력까지 검증되지 않아 Partially Covered로 판단했습니다.”
- “처음 가정과 실제 코드를 비교한 결과 timeout confirm count의 영향 가능성을 발견했습니다.”
- “측정값이 요구사항과 다르면 허용범위를 임의로 변경하지 않고 deviation으로 보고하겠습니다.”
- “재현 가능성을 위해 firmware SHA와 Runner/fixture 정보를 결과에 함께 남겼습니다.”

피할 표현:

- 근거 없이 “완벽히 검증 완료”, “문제없음”이라고 쓰기
- Pipeline URL, SHA, 측정값 없이 PASS만 기록하기
- 장비 미구성을 제품 결함으로 보고하기
- 실제 relay를 보지 않고 OLED 또는 CAN command만으로 물리 동작을 PASS 처리하기

## 8. 시험 실행 후 Jira Comment 양식

```markdown
## Verification Result
- Result: PASS / FAIL_PRODUCT / BLOCKED_INFRA
- Pipeline: <URL>
- QA commit: <full SHA>
- BMS/EVSE SHA: <full SHA>
- Runner / Adapter: <identity>
- Fixture config SHA-256: <hash>
- JUnit / raw log: <artifact URL>

## Observation
- 실제 관찰 frame/state/GPIO 및 측정 시간을 기록합니다.

## QA 판단
- 기대값과 측정값을 비교하고, 제품/테스트 코드/인프라 중 어느 범주인지 근거를 적습니다.

## Remaining scope
- 이번 시험으로 확인하지 못한 물리 출력, fault injection 또는 recovery 범위를 명시합니다.
```

비밀번호, Wi-Fi credential, token, 개인 경로의 민감정보는 Jira comment와 artifact에 기록하지
않는다.

## 9. Merge 전 Checklist

- Jira Summary와 branch/commit key가 일치한다.
- MR target은 `develop`이다.
- `git diff --cached`로 다른 Jira 파일이 섞이지 않았음을 확인했다.
- Host/static test와 HIL collect가 통과했다.
- 실제 HIL을 실행하지 않았다면 문서에 PASS라고 쓰지 않았다.
- 제품 SHA, artifact SHA-256, target verify evidence가 있다.
- conflict 해결 후 전체 Pipeline을 다시 실행했다.
- Jira에 MR, Pipeline, JUnit 링크를 남겼다.

## 10. BEOG-50 최초 Foundation Commit의 실제 staging 범위

이번 최초 commit은 다음 경로를 함께 추가한다. 카탈로그의 automation path가 실제 파일을
가리키고 CI가 같은 commit에서 실행 가능해야 하므로 문서와 코드를 임의로 나누지 않는다.

```text
.gitattributes
.gitignore
.gitlab-ci.yml
README_QA_FRAMEWORK.md
pyproject.toml
requirements-qa.txt
bootloader/
ci/
config/
docker/Dockerfile.toolchain
docs/aspice/
docs/jira_export/
firmware/
gateway/
hil/
tests/host/bms/
tests/host/common/
tests/host/ota/
tests/host/evse/mocks/evse_gpio_mock.c
tests/host/evse/mocks/hw_gpio.h
tests/host/evse/test_evse_core.c
tests/host/evse/test_evse_core_host.py
tests/host/evse/test_evse_input.c
tests/quality/
tools/
tests/host/evse/mocks/hw_def.h  # 기존 파일의 필요한 include 수정
```

명시적으로 제외하는 항목:

- `docs/BEOG17_JIRA_Troubleshooting_Record_Guide.md`: 기존 사용자 작업물
- `rasp_samba/bms-can-venv/`: 장비 종속 virtualenv
- `rasp_samba/f429_flash_before_beog17.bin`: raw flash backup

BEOG-50 merge 뒤 BEOG-48/49/19 branch에서는 같은 파일 전체를 다시 넣는 것이 아니라,
해당 Jira를 수행하기 위해 새로 생긴 diff만 commit한다. 예를 들어 BEOG-48에서
`hil/test_orchestrator.py`를 수정한 뒤 BEOG-49가 최신 develop에서 같은 파일에 selector를
하나 더 추가하는 것은 정상적인 Git 이력이다.
