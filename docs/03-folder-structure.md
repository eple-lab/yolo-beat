# 03. 폴더 구조

```
yolo-beat/
├── .gitignore            # git에서 뺄 것: .venv, models/, 캐시, 빌드 결과
├── .python-version       # uv가 쓸 Python 버전: 3.14
├── LICENSE               # AGPL-3.0 전문 (Ultralytics 패키지에 들어 있던 파일 복사)
├── README.md             # 쓰는 법: 설치, 실행, 옵션, 라이선스
├── pyproject.toml        # 프로젝트 정보, 의존성, 라이선스, 실행 스크립트
├── uv.lock               # 의존성 65개의 정확한 버전 고정 (uv가 관리)
├── docs/                 # 이 문서들: 만든 과정 전체
│   ├── README.md
│   ├── 01-prd.md
│   ├── 02-architecture.md
│   ├── 03-folder-structure.md
│   ├── 04-getting-started-checklist.md
│   ├── 05-dev-log.md
│   ├── 06-test-log.md
│   ├── 07-decisions.md
│   ├── images/           # README 실행 화면 3장 (영상에서 캡처, 얼굴은 가림)
│   └── videos/           # 시험 영상 YOLO-Beat-test.mp4 (8.5MB)
├── src/
│   └── yolo_beat/        # 파이썬 패키지 (이름에 하이픈을 못 써서 밑줄)
│       ├── __init__.py   # uv init 기본 파일. main()은 인사만 출력 (정리는 남은 일)
│       ├── app.py        # 메인 앱
│       ├── pose_preview.py
│       ├── sounds.py
│       └── zones.py
├── tests/
│   ├── test_zones.py     # 구역·판정 14개
│   └── test_sounds.py    # 합성 소리·손 이름 6개
│
│  ── 아래는 git에 올라가지 않음 ──
├── .venv/                # uv가 만든 가상환경 (torch 등 설치본)
├── models/               # yolo11n-pose.pt (6.0MB, 첫 실행 때 자동 다운로드)
└── .pytest_cache/        # pytest 캐시
```

## 파일별 설명

### 루트

| 파일 | 누가 만듦 | 설명 |
|---|---|---|
| `pyproject.toml` | `uv init` → 수정 | 이름 `yolo-beat`, `requires-python >=3.14`, 의존성 3개(ultralytics, opencv-python, pygame-ce), 개발 의존성 pytest, `license = "AGPL-3.0-only"`. `uv init`이 넣은 `authors`(git 설정의 이름·이메일)는 개인정보라서 지웠다 |
| `uv.lock` | `uv add`, `uv sync` | 손으로 고치지 않는다. 다른 컴퓨터에서 `uv sync`를 하면 같은 버전이 깔린다 |
| `.python-version` | `uv init --python 3.14` | uv가 이 버전의 Python을 준비한다 |
| `.gitignore` | `uv init` → 수정 | 기본값에 `models/`를 추가했다 |
| `LICENSE` | 복사 | 설치된 `ultralytics-8.4.210.dist-info/licenses/LICENSE`를 그대로 복사. 661줄, 34,523바이트 |

### `src/yolo_beat/`

| 파일 | 주요 이름 | 실행 |
|---|---|---|
| `app.py` | `run()`, `draw_zones()`, `main()` | `uv run python -m yolo_beat.app` |
| `pose_preview.py` | `open_camera()`, `load_model()`, `wrists()`, `hand_label()`, `bench()`, `live()` | `uv run python -m yolo_beat.pose_preview` (`--bench 60`이면 창 없이 시간 측정) |
| `zones.py` | `Zone`, `default_drum_layout()`, `Hit`, `HitDetector` | 직접 실행 없음 |
| `sounds.py` | `kick()` 등 6개, `synth_all()`, `to_int16()`, `DrumKit` | 직접 실행 없음 |

### `tests/`

| 파일 | 테스트 수 | 웹캠·스피커 필요 |
|---|---|---|
| `test_zones.py` | 14 | 아니요 |
| `test_sounds.py` | 6 | 아니요 (`pose_preview`를 import해서 Ultralytics 로딩에 약 4초 걸림) |

각 테스트 파일 맨 위 docstring에 **구현 전에 쓴 기대 동작**이 적혀 있다.

## 왜 `src/` 구조인가

`uv init`(uv 0.13.5)이 기본으로 `src/<패키지>/` 구조와 `[build-system]`을 만들었다.
처음 계획(`main.py` 하나)과 달랐지만 그대로 썼다. 장점은 이렇다.

- `uv sync`가 패키지를 편집 가능 모드로 설치해서, 어디서든 `python -m yolo_beat.app`으로 실행된다.
- 테스트가 설치된 패키지를 import하므로 경로 문제가 없다.
- 이름을 바꿀 때 폴더 하나와 import만 바꾸면 된다(실제로 `yolo_detect` → `yolo_beat`로 바꿈).

## git에 넣지 않는 것과 이유

| 대상 | 이유 | 대신 |
|---|---|---|
| `.venv/` | 컴퓨터마다 다르고 크다(torch 포함). 폴더 경로도 박혀 있다 | `uv sync`로 다시 만든다 |
| `models/` | 6MB 바이너리, 공식 배포본 | 첫 실행 때 자동으로 받아진다 |
| `.pytest_cache/`, `__pycache__/` | 실행 캐시 | - |
| 시험 화면 스크린샷 | 얼굴과 방이 찍혀 있다 | 문서에 글로만 설명 |
