# Job Alert System - GEMINI.md

이 파일은 본 채용 공고 알림 시스템 프로젝트의 설계, 아키텍처, 데이터베이스 스키마, 기업 분석/적합도 평가 엔진 및 개발 가이드를 담고 있습니다. 사용자 및 개발자가 점진적으로 프로젝트를 이해하고 발전시킬 수 있도록 돕는 기준 문서 역할을 합니다.

---

## 1. 프로젝트 개요 (Overview)

본 프로젝트는 **임베디드 및 시스템 소프트웨어 직무 맞춤형 채용 공고**를 다중 채용 플랫폼에서 주기적으로 수집·분석하여, 사용자에게 맞춤형 요약 정보를 **카카오톡 '나에게 보내기'** 단일 통합 메시지로 정기 제공하는 엔드투엔드 채용 자동화 시스템입니다.

- **핵심 목표**: 대기업 및 핵심 타겟 공고를 최우선 하이라이트하고, 직무 적합도 점수를 산출하여 1개의 깔끔한 카카오톡 메시지로 신규/유효 공고를 한눈에 파악할 수 있도록 지원합니다.
- **지원 플랫폼**: 원티드(Wanted), 잡코리아(JobKorea), 자소설닷컴(Jasoseol.com)
- **실행 방식**: GitHub Actions 기반 매일 18:00 KST (UTC 09:00) 단 1회 스케줄링 실행

---

## 2. 시스템 아키텍처 및 핵심 엔진 (Architecture & Core Engines)

시스템은 데이터 수집(Crawlers) -> 지능형 분석(Analyzer) -> 데이터베이스 저장 및 만료 관리(Database) -> 단일 통합 알림(Notifier)으로 이어지는 파이프라인으로 구성됩니다.

```mermaid
flowchart TD
    A[GitHub Actions / Local CLI] --> B[main.py]
    B --> C[DB 초기화 및 만료 공고 삭제]
    B --> D[JobCrawlerManager]
    D --> D1[WantedCrawler - 태그 658, 900, 817]
    D --> D2[JobKoreaCrawler - 검색 & 카드 파싱]
    D --> D3[JasoseolCrawler - API & 모집분야]
    D1 & D2 & D3 --> E[Analyzer 엔진]
    E --> E1[analyze_company - 기업 규모/하이라이트 판별]
    E --> E2[calculate_fit_score - 직무 적합도 점수 산출]
    E --> E3[parse_deadline - 마감일 표준화]
    E1 & E2 & E3 --> F[통합 정렬 및 중복 제거\n(Highlight > 대기업 > 적합도순)]
    F --> G[Web Generator - 반응형 모바일 대시보드 HTML 생성\n(index.html / docs/index.html)]
    G --> H{드라이 런 여부}
    H -- No --> I[Notifier - 단일 통합 카카오톡 발송\n(1,000자 제한 준수 + 웹 대시보드 바로가기 버튼)]
    I --> J[save_jobs_bulk - DB 일괄 저장]
    H -- Yes --> K[결과 로깅 후 종료]
```

### 2.1 주요 모듈 구성
1. **데이터 소스 (Multi-Platform Crawlers)**:
   - **Wanted (`wanted.py`)**: 임베디드(658), C/C++(900), 제어(817) 태그 기반 API 실시간 조회
   - **JobKorea (`jobkorea.py`)**: 최신 등록순 검색 카드 DOM 파싱, 기업 규모 배지(BadgeItem), 직무 칩, 마감일 정보 추출
   - **Jasoseol (`jasoseol.py`)**: 기업 공고 및 세부 모집분야(field) 분석, 지원 마감일시 연동
2. **지능형 분석 엔진 (`crawlers/analyzer.py`)**:
   - `analyze_company`: 대기업(`MAJOR_CORPS`), 중견기업(`MID_CORPS`), 공기업/외국계 매칭을 통해 기업 규모 코드(1~4) 및 하이라이트 여부 결정
   - `calculate_fit_score`: 임베디드 핵심 키워드 가중치(`FIT_WEIGHTS`)를 적용해 점수 및 적합도 등급(High/Med/Low) 부여
   - `parse_deadline`: ISO 날짜, `D-day`, `~ MM/DD`, 점(.) 구분자 등 다양한 마감일 문자열을 표준 `YYYY-MM-DD HH:MM:SS`로 파싱
3. **웹 대시보드 생성기 (`web_generator.py`)**:
   - 카카오톡 1,000자 제한을 우회하여 전체 공고(수십~수백 건)를 모바일 및 데스크톱에서 완벽하게 열람할 수 있는 정적 HTML([`index.html`](file:///mnt/c/career_searching/index.html), [`docs/index.html`](file:///mnt/c/career_searching/docs/index.html)) 자동 생성
   - **주요 기능**: 실시간 키워드 검색, 플랫폼별 탭(원티드/잡코리아/자소설닷컴), 기업규모/기술키워드 칩 필터, D-Day/적합도/최신순 정렬, 로컬 관심공고(북마크) 저장
4. **데이터베이스 관리 (`database.py`)**:
   - 15개 컬럼의 확장 스키마 지원 및 기존 DB 자동 마이그레이션
   - `delete_expired_jobs`: 현재 시간 기준 마감 공고 및 30일 경과 상시채용 공고 자동 삭제
   - `save_jobs_bulk`: `executemany`를 통한 대량 일괄 저장 (`ON CONFLICT DO UPDATE`)
   - `get_active_jobs`: 유효 공고 조회 및 정렬
5. **스마트 알림 (`notifier.py`)**:
   - 대기업 및 하이라이트 공고 요약과 함께 하단에 GitHub Pages 웹 대시보드 바로가기 버튼(`전체 공고 웹에서 보기 (N건)`)을 포함하여 1개의 단일 메시지로 전송
   - 카카오톡 1,000자 글자수 제한을 철저히 준수 (약 750~820자 이내 유지)

---

## 3. 데이터베이스 스키마 (Database Schema)

### `jobs` 테이블 구조
| 컬럼명 | 데이터 타입 | 설명 |
|---|---|---|
| `job_id` | TEXT (PK) | 고유 공고 ID (`{platform}_{raw_id}`) |
| `platform` | TEXT | 수집 플랫폼 (`원티드`, `잡코리아`, `자소설닷컴`) |
| `title` | TEXT | 채용 공고 제목 |
| `company` | TEXT | 채용 기업명 |
| `duty` | TEXT | 세부 직무 및 모집 분야 |
| `deadline` | TEXT | 표준 마감일시 (`YYYY-MM-DD HH:MM:SS` 또는 `NULL`) |
| `salary` | TEXT | 급여/경력 정보 |
| `company_type` | TEXT | 기업 규모명 (`대기업`, `중견기업`, `공기업/외국계`, `중소/스타트업`) |
| `company_type_code` | INTEGER | 기업 규모 코드 (1: 대기업 ~ 4: 중소/스타트업) |
| `fit_score` | INTEGER | 직무 적합도 점수 |
| `fit_level` | TEXT | 직무 적합도 레벨 (`High`, `Med`, `Low`) |
| `is_highlighted` | INTEGER | 하이라이트 여부 (1: 참, 0: 거짓) |
| `url` | TEXT | 공고 상세 바로가기 URL |
| `created_at` | TIMESTAMP | 레코드 생성 일시 |
| `sent_at` | TIMESTAMP | 알림 발송 일시 |

---

## 4. 디렉토리 구조 (Directory Structure)

```text
/mnt/c/career_searching/
├── .github/workflows/
│   └── job_alert.yaml         # GitHub Actions 워크플로우 (매일 18:00 KST 단일 실행)
├── image/
│   └── icon.jpg               # 서비스 관련 이미지 리소스
├── src/
│   ├── config.py              # 기업군, 가중치, 키워드 중앙 설정
│   ├── database.py            # SQLite3 DB 연동, 만료 삭제, 일괄 저장
│   ├── notifier.py            # 단일 카카오톡 메시지 구성 및 토큰 갱신
│   ├── crawlers/              # 플랫폼별 크롤러 및 분석 패키지
│   │   ├── __init__.py        # 모듈 익스포트
│   │   ├── base.py            # BaseCrawler 추상 클래스 & 표준 아이템 빌더
│   │   ├── analyzer.py        # 기업 규모, 적합도 점수, 마감일 파서
│   │   ├── wanted.py          # 원티드 API 수집기
│   │   ├── jobkorea.py        # 잡코리아 검색 크롤러
│   │   ├── jasoseol.py        # 자소설닷컴 공고 수집기
│   │   └── manager.py         # 전체 공고 수집, 중복제거, 정렬 매니저
│   ├── main.py                # 시스템 메인 엔트리포인트 (CLI 옵션 지원)
│   ├── get_kakao_token.py     # 카카오톡 OAuth 최초 토큰 발급 도구
│   ├── kakao_tokens.json      # 카카오 OAuth 토큰 보관 파일 (자동 갱신)
│   └── jobs.db                # SQLite3 데이터베이스
└── vkent/                     # Python 3.10 가상환경 디렉토리
```

---

## 5. 로컬 실행 및 테스트 가이드 (Testing & Verification Guide)

### 5.1 의존성 패키지 설치
```bash
pip install requests python-dotenv beautifulsoup4
```

### 5.2 실행 명령 옵션
```bash
# 1. 드라이 런 (실제 카카오톡 전송 및 DB 저장 없이 수집/분석 결과 확인)
python src/main.py --dry-run

# 2. 특정 플랫폼만 드라이 런 테스트
python src/main.py --platform jobkorea --dry-run
python src/main.py --platform jasoseol --dry-run
python src/main.py --platform wanted --dry-run

# 3. 실제 라이브 실행 (단일 카카오톡 알림 발송 및 DB 일괄 저장)
python src/main.py
```

---

## 6. 개발 원칙 및 주의 사항 (Engineering Standards)

- **크레덴셜 보안**: `kakao_tokens.json` 및 `KAKAO_REST_API_KEY`는 외부에 노출되지 않도록 안전하게 보호합니다.
- **예외 격리 및 안전성**: 크롤러 개별 실패가 전체 실행에 영향을 미치지 않도록 방어적으로 예외를 처리합니다.
- **메시지 길이 안전성**: 카카오톡 텍스트 템플릿의 1,000자 한도를 초과하지 않도록 메시지 생성기(`build_kakao_message_text`)에서 길이를 동적으로 검증합니다.
- **정밀 키워드 매칭**: `bsp`, `soc`, `arm`, `mcu`, `can`, `dsp` 등 짧은 영문/숫자 약어는 단어 경계 정규식(`\b`)을 적용하여 오탐을 방지합니다.
