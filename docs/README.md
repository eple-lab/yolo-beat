# YOLO-Beat 문서

프로젝트 README는 "쓰는 법"이고, 여기 docs는 **"어떻게 만들었는지"**예요.
처음부터 따라 만들어 보거나, 왜 이렇게 됐는지 궁금할 때 읽어요.

## 목차

| 문서 | 내용 | 이럴 때 읽어요 |
|---|---|---|
| [01-prd.md](01-prd.md) | 아이디어를 고른 과정, 목표, 기능, 비기능, 보안, 범위 밖, 다음 기능 | 무엇을 왜 만들었는지 |
| [02-architecture.md](02-architecture.md) | 데이터 흐름, 모듈, 좌표계, 판정 규칙, 소리 합성, 성능 예산 | 코드를 고치기 전에 |
| [03-folder-structure.md](03-folder-structure.md) | 파일 하나하나의 역할, git에 넣는 것과 빼는 것 | 파일을 찾을 때 |
| [04-getting-started-checklist.md](04-getting-started-checklist.md) | **처음 하는 사람 체크리스트.** 환경 확인, Python 버전 호환, uv, 웹캠 백엔드, 모델, 테스트, 공개 전 점검 | 비슷한 프로젝트를 시작할 때 |
| [05-dev-log.md](05-dev-log.md) | 대화 순서대로 쓴 개발 일지 (11-10 ~ 11-14) | 흐름을 처음부터 보고 싶을 때 |
| [06-test-log.md](06-test-log.md) | 모든 시험의 "기대 결과 → 실제" (T-01 ~ T-24) | 숫자와 근거가 필요할 때 |
| [07-decisions.md](07-decisions.md) | 결정 기록 (D-01 ~ D-23): 대안, 이유, 상태 | "왜 이렇게 했지?"가 궁금할 때 |

## 처음이라면 이 순서로

1. [01-prd.md](01-prd.md)의 1~3장
2. [04-getting-started-checklist.md](04-getting-started-checklist.md) 전체
3. [02-architecture.md](02-architecture.md)의 1, 5장
4. 궁금한 결정이나 숫자는 [07](07-decisions.md), [06](06-test-log.md)에서 ID로 찾기

## 표기

- **T-xx**: 시험 번호 ([06-test-log.md](06-test-log.md))
- **D-xx**: 결정 번호 ([07-decisions.md](07-decisions.md))
- **추정, 추측**: 측정하거나 확인하지 않은 내용
- **eple**: 프로젝트를 기획하고 직접 시험한 사람. **Claude**: 함께 코드를 짠 AI(Claude Code)
