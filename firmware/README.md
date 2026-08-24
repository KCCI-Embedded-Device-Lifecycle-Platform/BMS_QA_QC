# Firmware QA seams

이 디렉터리는 제품 펌웨어 복사본이 아니다. BMS, EVSE, Bootloader의 승인 SHA는 CI가
별도 checkout하며, 여기에는 승인 요구사항으로부터 독립적으로 작성한 **test oracle**과
host-test seam만 둔다.

- `common/qa_requirements.h`: SWRS/ICD에서 승인한 수치와 CAN 계약
- `bms/bms_oracle.*`: Fault 경계·permit 판정 oracle
- `evse/evse_oracle.*`: Relay 허용 decision table oracle

제품 매크로를 그대로 expected value로 사용하면 구현 오류를 테스트가 복제할 수 있다.
따라서 제품 값과 QA 요구사항 값은 별도 파일로 유지하고, CI에서 양쪽의 일치 여부와 실제
동작을 각각 검증한다.
