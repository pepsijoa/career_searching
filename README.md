# 🚀 임베디드 & 시스템 SW 채용 레이더 (Job Alert & Dashboard System)

원티드(Wanted), 잡코리아(JobKorea), 자소설닷컴(Jasoseol.com)에서 **임베디드, 펌웨어, 시스템 엔지니어 공고**를 실시간으로 크롤링하고 직무 적합도를 분석하여, **카카오톡 1일 1회 맞춤 알림**과 **반응형 웹 대시보드(GitHub Pages)**를 자동 제공하는 엔드투엔드 채용 자동화 시스템입니다.

---

## 🌟 주요 기능 (Key Features)

1. **다중 채용 플랫폼 통합 크롤링**:
   - **원티드 (Wanted)**: 임베디드(658), C/C++(900), 제어(817) 등 직무 태그 기반 API 실시간 조회
   - **잡코리아 (JobKorea)**: 키워드 검색(임베디드, 펌웨어, RTOS, MCU 등) 및 기업 규모 뱃지 파싱
   - **자소설닷컴 (Jasoseol.com)**: 최신 채용 공고 및 직무 분야 실시간 추출

2. **지능형 기업 및 적합도 분석 엔진**:
   - **기업 규모 자동 분류**: 대기업(삼성, 현대, LG, SK, 한화, LIG, 네이버 등 그룹사) / 중견기업(팹리스, 전장부품, 로봇) / 공기업 / 기타
   - **직무 적합도 점수 산출**: BSP, RTOS, MCU, Linux Kernel, C/C++, AUTOSAR, CAN 등 핵심 키워드 가중치 기반 적합도 레벨(High / Med / Low) 부여

3. **반응형 모바일 웹 대시보드 (GitHub Pages)**:
   - 카카오톡 글자 수(1,000자) 제한을 극복하고 전체 공고(수십~수백 건)를 열람할 수 있는 웹 대시보드 자동 생성
   - **실시간 검색 및 필터**: 키워드 검색, 플랫폼별 탭, 기업 규모 칩, 기술스택 태그
   - **다양한 정렬**: 추천순(대기업 우선) / 마감 임박순(D-Day) / 적합도순 / 최신순
   - **로컬 관심 공고(북마크)**: 브라우저에 저장하여 지원 대상 공고만 모아보기 가능

4. **스마트 카카오톡 단일 통합 알림**:
   - 매일 오후 6시(18:00 KST), 주요 하이라이트 공고 요약과 함께 **`전체 공고 웹에서 보기`** 버튼을 포함한 단 1개의 메시지로 통합 발송

---

## 🛠️ 기술 스택 (Tech Stack)

- **Language & Runtime**: Python 3.10+
- **Automation & Hosting**: GitHub Actions, GitHub Pages
- **Web Frontend**: HTML5, Vanilla CSS, Vanilla JavaScript (Zero Dependencies, Ultra Fast)
- **Database**: SQLite3 (중복 공고 관리 및 만료 공고 자동 정리)
- **Notification**: Kakao Open API (나에게 보내기 템플릿)

---

## ⚙️ 설정 및 설치 가이드 (Setup Guide)

### 1. 로컬 환경 설정
```bash
# 1. 저장소 클론
git clone https://github.com/pepsijoa/career_searching.git
cd career_searching

# 2. 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 패키지 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정 (`.env`)
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래 내용을 입력합니다 (`.env.example` 참조):
```env
# 카카오 REST API 키
KAKAO_REST_API_KEY=your_kakao_rest_api_key_here

# 카카오 Refresh Token (최초 1회 발급 필요)
KAKAO_REFRESH_TOKEN=your_kakao_refresh_token_here

# GitHub Pages 웹 대시보드 주소
GITHUB_PAGES_URL=https://pepsijoa.github.io/career_searching/
```

### 3. 카카오 토큰 최초 발급 (1회)
```bash
python src/get_kakao_token.py
```
콘솔에 안내되는 URL로 접속하여 카카오 로그인 후, 발급받은 인가 코드(`code`)를 입력하면 Refresh Token이 정상 발급됩니다.

---

## 🚀 로컬 실행 방법 (Running Locally)

```bash
# 1. 드라이 런 (카카오톡 발송 및 DB 저장 없이 크롤링 및 웹 대시보드 HTML 생성 테스트)
python src/main.py --dry-run

# 2. 특정 플랫폼만 드라이 런
python src/main.py --platform wanted --dry-run

# 3. 라이브 실행 (카카오톡 알림 발송 + DB 저장 + 웹 대시보드 빌드)
python src/main.py
```

---

## 🤖 GitHub Actions & Pages 배포 설정

### 1. GitHub Repository Secrets 등록
GitHub 저장소의 **[Settings] -> [Secrets and variables] -> [Actions]** 에서 `New repository secret`을 클릭하여 아래 시크릿들을 등록합니다:
- `KAKAO_REST_API_KEY`: 본인의 카카오 REST API 키
- `KAKAO_CLIENT_SECRET`: 카카오 Client Secret (보안 코드가 활성화된 경우)
- `KAKAO_REFRESH_TOKEN`: 발급받은 카카오 Refresh Token

### 2. GitHub Pages 활성화
1. 저장소 **[Settings] -> [Pages]** 이동
2. **Build and deployment** > **Source**: `Deploy from a branch` 선택
3. **Branch**: `main` / `/ (root)` (또는 `/docs`) 선택 후 **[Save]** 클릭
4. 매일 오후 6시 KST에 자동으로 크롤링이 진행되며 대시보드가 갱신됩니다.

---

## 📂 디렉토리 구조 (Directory Structure)

```text
career_searching/
├── .github/workflows/
│   └── job_alert.yaml        # 매일 18:00 KST 자동 실행 워크플로우
├── docs/
│   └── index.html            # GitHub Pages 호스팅용 웹 대시보드
├── index.html                # 루트 웹 대시보드
├── requirements.txt          # 의존성 패키지 목록
├── .env.example              # 환경변수 템플릿
├── GEMINI.md                 # 상세 개발/아키텍처 가이드
└── src/
    ├── config.py             # 중앙 설정 (키워드, 가중치, 기업군)
    ├── database.py           # SQLite DB 관리 (만료 공고 자동 삭제)
    ├── notifier.py           # 카카오톡 단일 알림 메시지 발송기
    ├── web_generator.py      # 반응형 웹 대시보드 HTML 빌더
    ├── crawlers/             # 채용 플랫폼 크롤러 패키지
    │   ├── wanted.py         # 원티드 수집기
    │   ├── jobkorea.py       # 잡코리아 수집기
    │   ├── jasoseol.py       # 자소설닷컴 수집기
    │   ├── analyzer.py       # 기업 규모 및 직무 적합도 엔진
    │   └── manager.py        # 통합 수집 매니저
    └── main.py               # 엔트리포인트 CLI
```

---

## 🔒 보안 및 개인정보 보호 (Security)
- 모든 API 키와 OAuth 토큰은 `.gitignore`에 의해 로컬에만 보관되며, GitHub Public 저장소에 절대 업로드되지 않습니다.
- GitHub Actions는 Repository Secrets를 통해 메모리 상에서만 안전하게 토큰을 처리합니다.
