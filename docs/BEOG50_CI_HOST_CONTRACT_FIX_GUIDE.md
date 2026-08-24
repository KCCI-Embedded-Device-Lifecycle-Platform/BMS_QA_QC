# BEOG-50 CI Host Contract 수정 및 실행 가이드

## 1. 수정 목적

이번 수정은 다음 세 가지 실패를 분리해서 해결한다.

1. `qa_static`의 `ModuleNotFoundError: No module named 'hil'`
2. EVSE relay Host test의 `implicit declaration` 컴파일 오류
3. 일반 MR에서 `qa_product_artifacts`가 실행되지 않거나 수동 필수 job으로 남는 문제

브랜치와 커밋은 다음과 같이 관리한다.

```text
branch: fix/BEOG-50-ci-host-contract
commit: [BEOG-50] fix CI import and EVSE host API contract
```

## 2. 원인과 수정 판단

### Python import

이 저장소는 루트의 `hil/`을 직접 import하는 flat layout이다. 따라서 아래 설정은 적절하다.

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

실행 위치 차이도 줄이기 위해 CI에서는 `pytest` 대신 `python -m pytest`를 사용한다. 루트
`hil/__init__.py`가 이미 존재하므로 `tests/hil/__init__.py`는 import 오류 해결에 필요하지 않다.

### EVSE Host header contract

실패한 Host compile 명령은 mock include 경로를 제품 include 경로보다 먼저 두었다. 그러므로
`#include "hw_gpio.h"`는 STM32 제품 헤더가 아니라
`tests/host/evse/mocks/hw_gpio.h`를 선택한다. 이 구조는 HAL 의존성을 차단하기 위해 의도된
것이지만, mock 헤더에 `hw_gpio_relay_write()`와
`hw_gpio_apply_safe_outputs()` 선언이 없어서 `-Werror` 빌드가 중단되었다.

U002는 제품 `hw_gpio.c`를 직접 검증하므로 제품 `MyApp/Hardware/hw_gpio.h`를 mock보다 먼저
검색하도록 include 순서를 수정한다. mock 경로는 `main.h`와 HAL 경계만 계속 제공한다. 또한
다른 Host harness에서 사용하는 mock `hw_gpio.h`에는 필요한 공개 함수 원형을 선언한다. 이
구성은 제품 헤더 변경을 U002 compile 단계에서 바로 감지하며, 테스트가 제품 로직 대신 가짜
relay 로직을 검증하는 것도 방지한다.

### Artifact gate

일반 MR에서는 firmware 전체 cross-build가 선택형 진단이므로 manual/optional로 둔다. 정식
Artifact 또는 HIL 파이프라인은 변수로 명시하여 자동 실행하고 실패를 차단한다.

```text
RUN_PRODUCT_ARTIFACTS=1  # cross-build + manifest 검증
RUN_HIL=1                # HIL 선행 artifact를 자동 필수 실행
```

## 3. `rg`가 없는 Bash에서 검색하기

`ripgrep`은 편리하지만 CI와 수정 절차의 필수 의존성이 아니다. 아래처럼 자동 fallback을
사용한다.

```bash
if command -v rg >/dev/null 2>&1; then
  rg -n --glob '*.[ch]' \
    'hw_gpio_(relay_write|apply_safe_outputs)' \
    tests/host/evse product/EVSE-Application/MyApp
else
  grep -RInE \
    --include='*.c' --include='*.h' \
    'hw_gpio_(relay_write|apply_safe_outputs)' \
    tests/host/evse product/EVSE-Application/MyApp
fi
```

개발 PC에서 원하면 Ubuntu/Debian에 `sudo apt-get install ripgrep`으로 설치할 수 있지만,
설치 권한이 없는 Raspberry Pi runner에서도 `grep` 경로로 진단 가능하다.

## 4. 로컬 및 GitLab 검증 순서

Ubuntu runner 또는 GCC가 설치된 Bash에서 다음 순서로 확인한다.

```bash
python -c 'import hil; import hil.report_junit'
python -m pytest tests/quality -m 'host or gap'
python -m pytest -v -s \
  tests/host/evse/test_evse_relay_host.py
python -m pytest \
  tests/host/bms \
  tests/host/evse/test_evse_core_host.py \
  tests/host/ota \
  -m host
```

GitLab에서는 fix branch push 후 `qa_static`, `qa_host_tests`,
`evse_relay_host_unit`가 모두 생성되는지 확인한다. 정식 firmware 산출물 검증은 Run pipeline
화면에서 `RUN_PRODUCT_ARTIFACTS=1`을 지정한다.

## 5. 실물 CAN 성공 결과의 QA 판정

BMS STM32F446, EVSE STM32F429ZI, CAN Analyzer가 같은 bus에서 송수신한 결과는
`BENCH_COMMUNICATION_PASS`로 기록할 수 있다. 이는 배선, bitrate, transceiver와 기본 CAN
frame 교환이 동작한다는 중요한 통합 증거다.

다만 다음 증거가 없는 상태에서는 BEOG-48/49 전체를 바로 PASS로 닫지 않는다.

- 승인된 BMS/EVSE firmware SHA와 flash 검증 기록
- CAN bitrate, 종단저항, adapter/runner 식별 정보
- BMS `0x100~0x105`, EVSE `0x200~0x202`의 기대 주기와 payload 판정
- START/STOP 이후 CAN 상태 전이와 BMS PA8 relay 물리 출력의 연계 증거
- JUnit, candump/raw log, Pipeline URL

QA 코멘트에는 다음처럼 관찰과 판정을 분리한다.

```markdown
## Bench Verification
- Observation: STM32F446 BMS와 STM32F429ZI EVSE가 CAN Analyzer에서 상호 frame 송수신함
- Verdict: BENCH_COMMUNICATION_PASS
- QA judgment: 물리 계층과 기본 통신 경로는 확인했으나, 승인 SHA 및 START/STOP→PA8
  relay E2E 자동 증거가 없어 요구사항 전체는 Partially Covered로 유지함
- Remaining evidence: firmware SHA, bitrate/termination, candump, JUnit, Pipeline URL
```

이 구분은 장비 연결 성공을 축소하지 않으면서도 제품 기능과 안전 요구사항을 과대 판정하지
않기 위한 것이다.
