# 04. 처음 하는 사람 체크리스트

> 이 프로젝트를 처음부터 다시 만든다고 생각하고, **실제로 부딪힌 것**과 **미리 확인했으면 좋았을 것**을 순서대로 적었어요.
> 각 항목의 "우리 경우"는 2026-11 개발 때 실제로 나온 값이에요.

## 0. 시작 전에 정할 것

- [ ] **무엇을 만들지** 후보를 여러 개 놓고 고른다. 사전학습 모델만으로 되는지, 데이터를 직접 만들어야 하는지가 제일 큰 갈림길이다.
  - 우리 경우: 요가 자세 가이드는 "동작마다 목표 각도 정의"라는 데이터 작업이 커서 접었다([01-prd.md](01-prd.md) 2-2).
- [ ] **라이선스를 먼저 본다.** Ultralytics YOLO는 **AGPL-3.0**이다.

  | 상황 | 소스 공개 의무 |
  |---|---|
  | 내 컴퓨터에서 혼자 씀 | 없음 |
  | 프로그램을 남에게 배포 | 이 프로젝트 소스를 AGPL-3.0으로 공개 |
  | 웹 서비스로 남이 쓰게 함 | 공개 (일반 GPL과 다른 AGPL의 핵심) |
  | 소스 비공개 상업 서비스 | Ultralytics 상용 라이선스 필요 |

  (일반적인 해석이며 법률 자문은 아님)

## 1. 컴퓨터 환경 확인

먼저 **확인만** 하고, 설치는 그다음에 한다.

- [ ] Python 위치와 버전
  ```powershell
  python --version
  (Get-Command python).Source
  ```
  - 우리 경우: 기본 Python이 miniconda base의 **3.14.7**이었다. conda 환경 `myenv`(3.11.16)에는 numpy만 있었다.
- [ ] 필요한 패키지가 이미 있는지
  ```powershell
  python -m pip list | Select-String "ultralytics|torch|opencv|pygame"
  ```
  - 우리 경우: 아무것도 없었다.
- [ ] CPU와 GPU
  ```powershell
  (Get-CimInstance Win32_Processor).Name
  Get-CimInstance Win32_VideoController | Select-Object Name
  nvidia-smi    # 없으면 NVIDIA GPU 없음
  ```
  - 우리 경우: Intel i5-1035G7, Intel Iris Plus(내장), NVIDIA 없음 → **CPU로 추론**해야 한다. 그래서 가장 작은 모델(nano)과 작은 입력 크기를 쓰게 된다.
- [ ] 웹캠 장치
  ```powershell
  Get-PnpDevice -Class Camera -PresentOnly
  ```
  - 우리 경우: 노트북 내장 카메라, 상태 OK. **장치 인식과 실제 영상 수신은 다르다.** OpenCV를 설치한 뒤 프레임 한 장을 꼭 읽어 본다(2-4).
- [ ] RAM과 디스크 여유: 설치가 수백 MB라서 확인한다. 우리 경우 RAM 15.7GB, 여유 공간 71GB.

## 2. Python 버전 호환 확인 (중요)

### 2-1. "최신 Python은 PyTorch가 안 될 것"이라는 짐작을 그대로 믿지 않는다

개발 중에 "Python 3.14는 PyTorch 호환이 불확실하다"고 말했다가, eple이 **"이거 검토부터 먼저 해줘"**라고 했다.
실제로 조회해 보니 **전부 지원됐다. 우려가 틀렸다.**

### 2-2. 확인 방법 ①: pip로 설치 가능한 버전 보기

```powershell
python -m pip index versions torch
```

pip는 **지금 Python에 맞는 설치 파일이 있는 버전만** 보여 준다. torch가 나오면 설치할 수 있다는 뜻이다.
(torch는 PyPI에 소스 배포본이 없어서, 나온다면 wheel이 있다는 뜻이다.)

### 2-3. 확인 방법 ②: PyPI에서 wheel 파일 이름 직접 보기

```powershell
$j = Invoke-RestMethod "https://pypi.org/pypi/torch/json"
$j.urls | ForEach-Object filename | Where-Object { $_ -match 'cp314.*win_amd64' }
```

wheel 파일 이름 읽는 법:

| 파일 이름 조각 | 뜻 |
|---|---|
| `cp314-cp314-win_amd64` | CPython 3.14 전용, Windows 64비트 |
| `cp314-cp314t-...` | 3.14 free-threaded(GIL 없는) 빌드용. 보통 Python에는 안 씀 |
| `cp37-abi3-win_amd64` | 3.7 이상 **모든 버전 공용** (opencv-python이 이 방식) |
| `py3-none-any` | 순수 Python, 어디서나 됨 (ultralytics) |
| `py3-none-win_amd64` | Python 3 공용, Windows 64비트 (torchvision 0.29.2) |

우리 경우(2026-11-11 조회):

| 패키지 | 버전 | 3.14 Windows |
|---|---|---|
| torch | 2.15.0 | ✅ `cp314-cp314-win_amd64` |
| torchvision | 0.29.2 | ✅ `py3-none-win_amd64` (단, `requires_python`에 `!=3.14.1` 제외 조건. 우리는 3.14.7이라 해당 없음) |
| ultralytics | 8.4.208 | ✅ 순수 Python |
| opencv-python | 5.0.0.93 | ✅ abi3 |
| pygame-ce | 2.5.8 | ✅ cp314 |
| numpy, scipy, matplotlib, pillow, pyyaml, psutil, polars | 최신 | ✅ |

**체크 포인트:**
- [ ] 직접 쓰는 패키지만이 아니라 **의존성(scipy, matplotlib, polars 등)**까지 본다. 하나라도 wheel이 없으면 소스 빌드를 시도하다 실패한다.
- [ ] `requires_python`의 제외 조건(`!=3.14.1` 같은 것)을 본다.
- [ ] wheel이 있다는 것과 **실제로 돌아간다는 것은 다르다.** 설치한 뒤 import와 추론까지 해 본다(우리는 2-4에서 확인).

### 2-4. 설치 직후 확인 스크립트 (기대 결과를 먼저 적고 돌린다)

| # | 확인 | 기대 | 실제 |
|---|---|---|---|
| 1 | Python | 3.14.x | 3.14.7 ✅ |
| 2 | torch | 2.15.0, CPU 전용 | 2.15.0+cpu, CUDA False ✅ |
| 3 | ultralytics import | 오류 없음 | 8.4.210 ✅ |
| 4 | OpenCV | 5.0.x | 5.0.0 ✅ |
| 5 | pygame 오디오 | mixer 초기화 성공 | 성공 ✅ (모노로 요청했는데 스테레오로 열림) |
| 6 | 웹캠 0번 | 열림, 한 프레임 읽힘 | 640x480 프레임, 1.37초 ✅ |
| 7 | **일부러 실패:** 웹캠 9번 | 안 열림 | 안 열림 ✅ |

7번처럼 **일부러 실패하는 경우**를 넣으면, 확인 코드가 항상 "성공"만 말하는 가짜가 아님을 알 수 있다.
웹캠 프레임은 디스크에 저장하지 않았다.

## 3. 패키지 관리: conda와 uv

- [ ] 프로젝트 전용 환경을 만든다. base나 다른 프로젝트 환경에 섞지 않는다.
- 우리는 miniconda도 있었지만 **uv**를 골랐다(eple의 선택).

| | conda 새 환경 | uv |
|---|---|---|
| 환경 위치 | miniconda 아래 공용 폴더 | **프로젝트 폴더 안 `.venv`** |
| 버전 고정 | 따로 export 필요 | `uv.lock` 자동 |
| 속도 | 보통 | 빠름 |
| Python 준비 | conda가 설치 | uv가 설치·관리 (`uv python list`) |

명령:

```bash
uv init --python 3.14
uv add ultralytics opencv-python pygame-ce
uv add --dev pytest
```

- 다운로드는 약 260MB였다(torch 121MB, polars 51MB, opencv 42MB, numpy 12MB 등). 준비 1분 51초, 설치 29초.
- Windows의 PyPI torch는 **CPU 버전**이다. GPU 없는 노트북에는 그대로 맞다.

### `uv init`이 자동으로 만드는 것 (놀라지 말 것)

- [ ] **`.git` 저장소**가 생긴다(커밋은 없음).
- [ ] **`src/<패키지>/` 구조**와 `[build-system]`이 생긴다(uv 0.13.5 기준).
- [ ] **`pyproject.toml`의 `authors`에 git 설정의 이름과 이메일**이 들어간다. → **개인정보.** 공개할 거면 지운다.
  - 지워도 되는지 복사본에서 먼저 확인했다: `uv lock --check` 통과, `uv build` 성공, 테스트 20개 통과([06-test-log.md](06-test-log.md) T-19).
- [ ] `README.md`는 **빈 파일**이다.

## 4. 웹캠: OpenCV 백엔드 (중요)

- [ ] **FPS가 15에서 안 오르면 카메라 백엔드를 의심한다.**
- 우리 경우: 입력 크기를 640 → 416 → 320으로 줄여도 FPS가 **정확히 15.0**에서 멈췄다. 카메라만 따로 재 보니:

  | 백엔드 | 카메라가 말한 FPS | 실제 측정 |
  |---|---|---|
  | `cv2.CAP_DSHOW` (DirectShow) | 30.0 | **15.3** |
  | `cv2.CAP_MSMF` (Media Foundation) | 30.0 | **30.0** |

- → `cv2.VideoCapture(0, cv2.CAP_MSMF)` + `CAP_PROP_FPS=30`으로 바꾸자 320에서 17.6 FPS가 나왔다.
- [ ] `cap.get(CAP_PROP_FPS)` 값은 믿지 말고 **직접 3초 동안 읽어서 센다.**
- 참고: `cap.release()`(카메라 닫기)는 MSMF·DSHOW 모두 약 0.3초 걸린다(T-25). 처음에 "MSMF가 느리다"고 추측했다가 재 보고 정정했다. **추측은 재 보고 적는다.**

## 5. 모델과 Ultralytics

- [ ] **모델은 첫 실행 때 자동으로 받아진다.** `YOLO("models/yolo11n-pose.pt")`처럼 경로를 주면 그 경로에 저장된다(6.0MB, 1초 이내). 인터넷이 필요하다.
  - 출처: `https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n-pose.pt`
- [ ] `models/`는 `.gitignore`에 넣는다. 대신 README에 "자동으로 받아진다"고 적는다.
- [ ] **Ultralytics 설정 파일**이 처음 import할 때 사용자 설정 폴더에 생긴다(`Creating new Ultralytics Settings v0.0.8 file` 메시지). 기본값으로 **익명 사용 통계(`sync`)가 켜져 있는 것으로 알고 있다**(직접 열어 보지는 않음). 끄려면 `yolo settings sync=False`. 설정 변경이라 우리는 아직 하지 않았다.
- [ ] **입력 크기(`imgsz`)가 속도를 결정한다.** CPU에서:

  | imgsz | 추론 평균 | FPS |
  |---|---|---|
  | 640 | 140~190ms | 5~7 |
  | 416 | 48ms | 15 (카메라 한계) |
  | 320 | 39~53ms | 15 → 17.6 (MSMF 후) |

- [ ] 측정은 **여러 번** 한다. 같은 설정에서도 320 추론이 39ms → 53ms로 흔들렸다(발열이나 전원 모드로 추정, 확인 안 함).

## 6. 포즈 모델의 한계 (기능을 정하기 전에)

- [ ] COCO 키포인트 17개: 코, 눈 2, 귀 2, 어깨 2, 팔꿈치 2, **손목 2**, 엉덩이 2, 무릎 2, 발목 2. **손가락은 없다.**
  - eple의 질문: "손끝은 안 돼? 손목만 체크돼서." → 손끝은 팔꿈치→손목 방향으로 연장해서 **추정**하는 것이 가장 빠른 방법([01-prd.md](01-prd.md) 10).
- [ ] **화면을 뒤집으면 왼손/오른손 이름도 뒤집힌다.** 모델의 left_wrist = 사용자의 오른손. 우리는 첫 실기 시험 로그를 보고서야 알았다.

## 7. 소리

- [ ] 처음엔 **소리가 안 나는 단계가 있다는 걸 크게 알린다.** 2단계(판정)까지 끝났을 때 eple이 소리를 기다렸다("난 소리를 못 들었어"). 보고 중간에 "아직 소리 없음"이라고만 적어서 놓치기 쉬웠다.
- [ ] pygame은 `pygame-ce`(커뮤니티 판)를 썼다. 3.14 wheel이 있다.
- [ ] mixer 버퍼를 작게(256) 잡아야 지연이 준다. 채널 수를 늘려야(16) 소리가 겹쳐도 안 끊긴다.
- [ ] `pygame.sndarray.make_sound`에는 mixer 채널 수와 같은 모양의 int16 **C-연속** 배열을 넘긴다. 모노로 요청해도 스테레오로 열릴 수 있으니 `mixer.get_init()`으로 실제 채널 수를 읽는다.

## 8. 테스트

- [ ] 판정과 합성은 **순수 함수**로 빼서 웹캠·스피커 없이 테스트한다.
- [ ] 테스트를 **먼저** 쓰고, 구현 전에 돌려서 **실패(Red)**를 본다.
- [ ] 다 통과하면, 코드를 **일부러 망가뜨린 복사본**에 테스트를 돌려 실패하는지 본다(뮤테이션 시험). 테스트가 진짜 버그를 잡는지 확인하는 방법이다.
  - 주의: 망가뜨리는 방식이 실제로는 동작을 안 바꾸는 경우(등가 뮤턴트)도 있다. 우리 경우 8개 중 1개가 그랬다(T-10).
- [ ] 실기 시험은 **터미널 로그에 시간을 찍어서** 분석한다. 스크린샷 한 장으로는 몇 번 울렸는지 모른다.

## 9. Windows·PowerShell에서 헷갈린 것

- [ ] **PowerShell 5.1에서 정상 메시지가 빨간 에러처럼 보인다.** uv는 안내 메시지를 stderr로 내보내는데, PowerShell이 이를 `NativeCommandError`로 감싼다. 예: `uv lock --check`의 `Resolved 65 packages`. **종료 코드로 판단한다.**
- [ ] git 커밋 때 `LF will be replaced by CRLF` 경고: Windows git의 줄바꿈 자동 변환 안내다. 내용에는 영향이 없다.
- [ ] `py` 런처가 없을 수 있다(miniconda만 있는 경우). `python`이나 `uv run`을 쓴다.

## 10. 공개 저장소에 올리기 전

- [ ] 개인정보 검색: 이메일, 실명·아이디, **컴퓨터 경로(`C:\Users\...`)**, 키·토큰
  - 검색 패턴은 **샘플 문자열로 먼저 시험한다.** 처음 패턴이 `https://`의 `s:/`까지 잡아서 고쳤다(T-18).
- [ ] `pyproject.toml`의 `authors` 확인 (3장)
- [ ] 커밋 작성자 정보: 파일과 별개로 커밋 기록에 남는다. 공개 저장소면 같이 공개된다.
- [ ] 얼굴이 나온 스크린샷은 넣지 않는다.
- [ ] `LICENSE` 파일을 둔다. AGPL 전문은 설치된 `ultralytics-*.dist-info/licenses/LICENSE`에 있다(인터넷에서 새로 받을 필요 없음).
- [ ] 브랜치 이름: git 기본이 `master`일 수 있다. GitHub 관례인 `main`으로 바꿨다(`git branch -m master main`).
