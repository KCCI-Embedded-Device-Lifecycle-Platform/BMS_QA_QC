# QA/QC Review Notes

## 결론

Reviewed Final은 초기 제안보다 제품 코드와 잘 맞으며 이 저장소의 test baseline으로
채택했다. 단, “자동화 코드 존재”와 “제품 검증 완료”를 분리한다. 현재 산출물은
검증 프레임워크와 실행 가능한 test design이며, 실제 PASS는 고정 artifact를
Ubuntu/Pi에서 실행하고 target 동일성 증거를 얻은 뒤 선언한다.

## 주요 품질 판단

1. BMS MCU를 F446으로, EVSE를 F429로 분리했다. 보드/링커 혼동은 시험 장비와
   flash 주소를 잘못 선택하는 CM 결함으로 이어진다.
2. BMS 온도 기준은 현재 승인 후보 소스의 55.0/50.0°C다. 과거 대화의 40/37°C를
   재사용하면 잘못된 테스트가 된다.
3. OTA canonical은 staging과 backup metadata가 있는 `ota-platform` 복사본으로
   고정했다. standalone 복사본과 섞어 build하지 않는다.
4. BMS fault 3회 confirm과 link timeout 1000 ms가 결합되는 지점은 요구-구현
   불일치 후보다. test tolerance를 1300 ms로 늘려 PASS시키지 않고 deviation으로
   관리한다.
5. CAN 수신 성공은 BEOG-16/48 precondition 진전이지만 E2E safety 증거는 아니다.
   3-node START/STOP, PA8/PE11 및 실제 contactor를 별도 관찰해야 한다.
6. OTA power-loss/rollback, downgrade, wrong-target rejection은 제품 mechanism이
   확인되지 않았다. 이 세 항목은 명시적 GAP test로 유지한다.
7. Gateway는 현재 `ota-platform`과 동일어가 아니다. schema와 source boundary가
   없으므로 구현을 상상해서 PASS하지 않고 contract-waiting test만 제공한다.

## 리뷰 코멘트

좋은 QA는 실패를 많이 찾는 사람이 아니라, 어떤 증거로 무엇까지 말할 수 있는지
경계를 지키는 사람이다. 이 구조는 product failure, test defect, requirement gap,
configuration mismatch, infrastructure blocker를 분리해 개발팀이 올바른 원인을
수정하도록 한다. 특히 물리 안전 출력은 CAN/logical state와 독립된 오라클로
확인하고, 테스트가 target을 바꾸는 순간부터 복구 절차까지 하나의 test case로
관리한다.
