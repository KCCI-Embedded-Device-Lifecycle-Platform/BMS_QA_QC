# Jira Test Import Guide

`jira_test_cases.csv`는 Reviewed Final 54개 시험을 Jira CSV importer에서 사용할 수
있도록 생성한 파일이다. 프로젝트에 `Test` issue type(Xray/Zephyr 등)이 없으면 import
화면에서 `Issue Type`을 팀의 `Test Case` 또는 `Task` type으로 매핑한다.

권장 매핑:

| CSV | Jira |
|---|---|
| Issue Type | Issue Type |
| Summary | Summary |
| Description | Description |
| Priority | Priority |
| Labels | Labels |

각 Description에는 Test ID, SWRS, ASPICE level, precondition, stimulus, 독립 expected
oracle, automation 경로와 disposition이 들어 있다. `READY`는 코드 준비 상태일 뿐
실행 결과 PASS가 아니다.

원본은 `test_case_manifest.json`이며 다음 명령으로 CSV/Markdown을 재생성한다.

```bash
python tools/generate_jira_catalog.py
```

이 전달에서는 live Jira를 변경하지 않았다. Import 후 BEOG issue link, assignee,
fix version, 실제 execution/JUnit evidence URL은 프로젝트 권한과 release baseline에
맞춰 추가한다.
