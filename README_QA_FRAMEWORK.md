# BMS–EVSE–OTA QA/QC Verification Framework

이 디렉터리는 제품 코드를 복제하는 곳이 아니라, 승인된 요구사항을 독립적으로
검증하는 QA 저장소다. 제품 저장소는 CI에서 고정 SHA로 가져오고 이 저장소의
오라클, Host harness, Raspberry Pi HIL이 제품 결과를 판정한다.

## 구성

```text
firmware/        독립 BMS/EVSE/CAN 요구사항 오라클(C)
bootloader/      OTA 경계·CRC·벡터 검증 오라클(C)
gateway/         계약 승인 전 테스트 경계와 GAP 설명
tests/host/      실제 제품 C 모듈을 연결하는 SWE.4 Host 테스트
tests/quality/   추적성, 증거 스키마, GAP/BLOCKED 품질 게이트
hil/             Pi 4 CAN/UART/OpenOCD/전원·결함 자극과 HIL 테스트
docs/aspice/     SWRS, ICD, 계획, 명세, RTM, 검증 보고서
docs/jira_export Jira Test import CSV 및 상세 카탈로그
docker/          Ubuntu 재현 가능 도구 체인
ci/              GitLab Host/HIL 확장 파이프라인
```

## 빠른 실행

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-qa.txt
pytest tests/host tests/quality -m "host or gap" --junitxml=reports/host/junit.xml
```

HIL은 `hil/fixtures/config.example.json`을 복사해 장비 포트와 승인된 자극 명령을
입력한 후 실행한다. 파괴적/동작 자극은 `HIL_ALLOW_*` 환경 게이트와 물리적
interlock 확인이 모두 필요하다.

## QA/QC 판정 원칙

- 제품 매크로와 동일한 값을 재사용해 expected를 만들지 않는다. 승인 기준은
  `firmware/common/qa_requirements.h`의 독립 오라클이다.
- UART 로그, CAN 명령, GPIO 레지스터, 실제 접촉기 상태는 서로 다른 증거다.
  요구 오라클이 물리 출력이면 로그만으로 PASS하지 않는다.
- 요구사항 부재는 제품 FAIL이 아니라 `GAP_REQUIREMENT`, 장비 부재는
  `BLOCKED_INFRA`다. 테스트 코드 결함은 `FAIL_TEST`로 분리한다.
- SHA, artifact SHA-256, target verify, 장비 identity가 없으면 결과를 공식
  `PASS`로 승격하지 않는다.
