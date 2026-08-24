# BEOG-92 Ubuntu / Raspberry Pi QA Evidence Guide

## 목적과 판정 원칙

이 문서는 `TC-INFRA-JUNIT-001`의 실행 증거와 신입 QA/QC 포트폴리오 캡처를 같은 방식으로 남기기 위한 절차다. 좋은 증거는 단순한 초록색 화면이 아니라 **요구사항 → 고정 SHA → 실행 환경 → 명령 → 실제 결과 → 결함/보류 판정**이 이어져야 한다.

다음 항목은 서로 다른 판정으로 기록한다.

- `PASS`: 승인된 사전조건과 oracle을 모두 만족했다.
- `FAIL_PRODUCT`: 시험 인프라는 정상이고 제품 동작이 oracle과 다르다.
- `BLOCKED_INFRA`: 장비, 권한, CAN 채널, fixture 정보 또는 자극기가 없다.
- `GAP_REQUIREMENT`: 수치/계약/복구 정책이 승인되지 않아 합격 기준이 없다.

통신 프레임을 한 번 수신한 것은 bring-up 증거이지만 릴레이 안전 요구사항의 PASS는 아니다. 정식 HIL PASS에는 artifact SHA, 실제 target image, CAN 상태 전이와 물리 출력 oracle이 함께 필요하다.

## 현재 권장 실행 순서

1. `BEOG-50` 기준선과 RTM 일관성을 확인한다.
2. `BEOG-33`, `BEOG-34`, `BEOG-45`의 CAN 판정/구성 결정을 승인한다.
3. `BEOG-51`에서 EVSE app 영역을 `0x08020000..<0x08100000`으로 제한한다.
4. `qa_product_artifacts`를 실행해 `BEOG-89`의 SHA, 크기, vector, checksum gate를 통과한다.
5. Host P0/P1을 실행하고 JUnit을 보존한다.
6. 무자극 Pi 시험 `qa_hil_can_infra`로 `BEOG-37`, `BEOG-48`의 500 kbit/s 3-node acceptance를 확인한다.
7. hard interlock, 무부하, dual OpenOCD, START/STOP 절연 자극기를 확인한 뒤 `qa_hil_can_start_stop`을 실행한다.
8. fault/timeout HIL을 수행한 뒤에만 OTA erase/update 시험으로 이동한다.

`BEOG-51`과 `BEOG-89`는 사진의 Phase 0에 포함해야 한다. 이 gate를 건너뛰면 어떤 ELF/BIN이 보드에 올라갔는지 입증하지 못하므로 이후 HIL 결과는 참고 증거일 뿐 정식 검증 결과가 아니다.

## Ubuntu Runner 증거 수집

저장소 루트에서 실행한다.

```bash
git fetch origin
git status --short --branch
git rev-parse HEAD
python3 tools/generate_jira_catalog.py
git diff --exit-code -- docs/jira_export
python3 -m pytest tests/quality -m "host or gap" \
  --junitxml=reports/portfolio/ubuntu-static/junit.xml
bash tools/capture_qa_evidence.sh reports/portfolio/ubuntu
```

Host C 시험은 GitLab의 `qa_host_tests` Docker job을 정식 증거로 사용한다. 로컬 명령은 빠른 재현용이며, 제품 SHA를 clone하는 CI job의 URL과 JUnit artifact를 Jira에 연결한다.

`rg`가 설치되지 않은 Ubuntu/Pi에서는 다음처럼 대체한다.

```bash
grep -RIn --exclude-dir=.git --exclude-dir=.venv \
  -E 'TC-|BEOG-|0x08020000|0x08100000' docs hil tests tools
```

## Raspberry Pi 4 + Seeed USB-CAN 증거 수집

현재 승인 예시는 SocketCAN `can0`가 아니라 python-can `seeedstudio`와 `/dev/ttyUSB0`을 사용한다. Samba에서 복제된 venv는 재사용하지 말고 Pi에서 새로 만든다.

```bash
cd /srv/samba/stm32-bms-evse-ota-ga-hil
python3 -m venv .qa-hil-venv
.qa-hil-venv/bin/python -m pip install -r requirements-qa.txt
cp hil/fixtures/config.example.json hil/fixtures/config.bench-01.json
```

`config.bench-01.json`에는 전원을 끈 상태에서 측정한 종단저항 값을 `fixture.termination_ohms`에 기록한다. 이 bench 파일은 비밀정보와 장비별 명령을 포함할 수 있으므로 commit하지 않는다.

먼저 읽기 전용 환경 증거를 수집한다.

```bash
CAN_CHANNEL=can0 bash tools/capture_qa_evidence.sh reports/portfolio/pi
ls -l /dev/ttyUSB0
gitlab-runner --version
```

Seeed adapter 기반 무자극 acceptance를 실행한다.

```bash
export HIL_CONFIG="$PWD/hil/fixtures/config.bench-01.json"
.qa-hil-venv/bin/python -m hil.test_orchestrator \
  --config "$HIL_CONFIG" \
  --suite can-infra \
  --reports reports/hil-can-infra \
  --require-all-executed
sha256sum reports/hil-can-infra/junit.xml \
  reports/hil-can-infra/metadata.json
```

SocketCAN 장비를 실제로 쓸 때만 `interface=socketcan`, `channel=can0`으로 바꾸고 다음 상태를 캡처한다. Seeed serial backend에 `can0`가 없다는 이유만으로 제품 결함을 만들지 않는다.

```bash
ip -details -statistics link show can0
```

START/STOP, fault injection, OTA erase는 GitLab manual job의 승인 변수와 fixture 사전조건 없이 터미널에서 직접 실행하지 않는다.

## 효과적인 캡처 7장

1. Jira Test issue: requirement ID, precondition, stimulus, oracle, 결과 분류가 한 화면에 보이게 캡처한다.
2. GitLab pipeline overview: branch, commit SHA, pipeline ID, stage 흐름이 보이게 캡처한다.
3. Ubuntu `qa_host_tests`: pytest 요약과 JUnit Tests 탭을 캡처한다.
4. Artifact manifest: product source SHA, ELF/BIN SHA-256, flash start/end, size 판정을 캡처한다.
5. Bench topology: BMS F446, EVSE F429, Pi 4, CAN Analyzer, 두 종단 위치를 라벨링한 사진을 남긴다.
6. 전원 OFF 종단저항: CAN_H-CAN_L 약 60 ohm 측정과 시험 일시/fixture ID를 함께 남긴다.
7. Pi HIL: metadata의 QA/product SHA와 JUnit 결과, 필요한 경우 PA8/PE11 물리 측정값을 한 test execution에 묶는다.

캡처에는 `/etc/gitlab-runner/config.toml`, CI token, Jira/API token, Wi-Fi SSID/password, 개인 이메일, 전체 USB serial을 노출하지 않는다. 필요한 식별자는 일부 마스킹한다.

## Jira 실행 코멘트 예시

```text
[실행 결과] PASS / FAIL_PRODUCT / BLOCKED_INFRA / GAP_REQUIREMENT

- Test Case: TC-...
- QA commit: <full SHA>
- Product baseline: BMS=<SHA>, EVSE=<SHA>, OTA=<SHA>
- Pipeline / Job: <URL>
- Runner: Ubuntu Docker 또는 Pi4 bench-01
- Fixture: CAN 500 kbit/s, termination=<측정값>, no-load/interlock=<상태>
- Actual: <관측값과 시간>
- Expected: <승인된 oracle>
- Evidence: junit.xml, metadata.json, manifest.json, 사진/로그
- 판단: 수신 성공과 물리 출력 검증을 구분했으며, 미충족 사전조건은 제품 FAIL이 아닌 BLOCKED_INFRA로 분류함.
```

이 형식은 “테스트를 돌렸다”보다 왜 그 결과를 신뢰할 수 있는지 설명한다. 특히 실패를 억지로 PASS로 만들지 않고 제품 결함, 인프라 차단, 요구사항 Gap을 분리하는 것이 QA/QC 핵심 역할이다.
