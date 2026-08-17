# Gateway verification status

`REVIEWED_FINAL`의 Gateway 항목은 제품 source와 승인된 interface/timing/log contract가
확정되기 전까지 실행 가능한 테스트가 아니라 **Test Specification**으로 관리한다.

현재 `ota-platform`은 direct-device LwM2M OTA platform이며, 전통적인 CAN Gateway/UI와
동일한 제품으로 가정하지 않는다. 다음 테스트는 Jira/RTM에 `READY WHEN ...` 상태로만
등록한다.

- `TC-GA-DECODE-001`
- `TC-GA-STATE-001`
- `TC-GA-STALE-001`
- `TC-GA-INVALID-001`
- `TC-GA-LOG-001`

QA 판정 원칙: Source가 없다는 이유로 mock 구현 자체를 제품 PASS 근거로 사용하지 않는다.
Mock은 계약 리뷰와 harness 검증에만 사용하며, 제품 인수 판정은 실제 parser/service와 링크한
뒤 수행한다.
