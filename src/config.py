# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# 기본 디렉토리 경로
SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent

# .env 파일 로드 (로컬 환경 지원)
load_dotenv(ROOT_DIR / ".env")
load_dotenv(SRC_DIR / ".env")

# 설정 정보 (보안을 위해 환경변수 또는 .env에서만 주입)
REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "")
CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", "")
REFRESH_TOKEN = os.getenv("KAKAO_REFRESH_TOKEN", "")
TOKEN_FILE = os.getenv("KAKAO_TOKEN_FILE", str(SRC_DIR / "kakao_tokens.json"))
DB_FILE = os.getenv("JOB_DB_FILE", str(SRC_DIR / "jobs.db"))

# GitHub Pages 웹 대시보드 URL 및 파일 경로
GITHUB_PAGES_URL = os.getenv("GITHUB_PAGES_URL", "https://pepsijoa.github.io/career_searching/")
DOCS_DIR = ROOT_DIR / "docs"
HTML_OUTPUT_FILES = [ROOT_DIR / "index.html", DOCS_DIR / "index.html"]

# 기업 규모 분류 맵
COMPANY_TYPE_NAMES = {
    1: "대기업",
    2: "중견기업",
    3: "공기업/외국계",
    4: "중소/스타트업"
}

# 대기업 및 주요 계열사 키워드 (하이라이트 대상)
MAJOR_CORPS = [
    # 주요 그룹사 및 계열사
    "삼성", "삼성전자", "삼성SDI", "삼성전기", "삼성SDS", "삼성중공업",
    "현대", "현대차", "현대자동차", "기아", "현대모비스", "현대오토에버", "현대로템",
    "현대케피코", "현대트랜시스", "현대위아", "현대일렉트릭", "HD현대", "HD현대일렉트릭", "HD현대로보틱스",
    "LG", "LG전자", "LG이노텍", "LG디스플레이", "LG에너지솔루션", "LG유플러스", "LG CNS",
    "SK", "SK하이닉스", "SK텔레콤", "SK이노베이션", "SK온", "SK스퀘어",
    "한화", "한화에어로스페이스", "한화시스템", "한화오션", "한화비전", "한화엔진",
    "LIG", "LIG넥스원", "넥스원",
    "만도", "HL만도", "HL클레무브", "HL홀딩스",
    "포스코", "포스코DX", "포스코홀딩스",
    "두산", "두산에너빌리티", "두산로보틱스", "두산밥캣",
    "한국항공우주", "KAI",
    "KT", "네이버", "NAVER", "카카오", "쿠팡", "라인", "CJ", "씨제이"
]

# 주요 중견기업 키워드 (차량부품, 반도체/팹리스, 전장, 제어, 로봇 등)
MID_CORPS = [
    "텔레칩스", "다산네트웍스", "유라코퍼레이션", "경신", "티에이치엔", "SL", "에스엘",
    "동운아나텍", "어보브반도체", "픽셀플러스", "제주반도체", "리벨리온", "퓨리오사AI",
    "딥엑스", "모빌린트", "코스맥스", "루닛", "뷰노", "솔트룩스", "안랩", "알서포트",
    "파수", "한글과컴퓨터", "비츠로셀", "인텔리안테크", "쎄트렉아이", "우리엔",
    "바텍", "레이언스", "엠씨넥스", "파트론", "캠시스", "파워로직스", "슈프리마",
    "에스넷시스템", "오픈엣지테크놀로지", "가온칩스", "에이디테크놀로지", "코아시아",
    "에이직랜드", "세메스", "원익", "한미반도체", "주성엔지니어링", "유진테크",
    "로보티즈", "레인보우로보틱스", "뉴로메카", "에스비비테크", "SPG", "티로보틱스"
]

# 직무 적합도 점수 가중치 (키워드별 가중치 산출)
FIT_WEIGHTS = {
    # 핵심 임베디드 / 펌웨어 (+4)
    "임베디드": 4, "embedded": 4, "펌웨어": 4, "firmware": 4,
    # 핵심 시스템 / OS / 제어기 (+3)
    "rtos": 3, "freertos": 3, "zephyr": 3, "bsp": 3, "driver": 3, "드라이버": 3,
    "mcu": 3, "mpu": 3, "stm32": 3, "esp32": 3, "autosar": 3, "auto-sar": 3,
    "디바이스 드라이버": 3, "device driver": 3, "리눅스 커널": 3, "linux kernel": 3,
    # 프로그래밍 언어 및 하드웨어 제어 (+2)
    "c++": 2, "c언어": 2, "fpga": 2, "verilog": 2, "soc": 2, "arm": 2, "cortex": 2,
    "모터 제어": 2, "로봇 제어": 2, "제어기": 2, "전장": 2, "전장 sw": 2, "제어 sw": 2,
    # 보조 시스템/통신 프로토콜 (+1)
    "linux": 1, "리눅스": 1, "can": 1, "can 통신": 1, "can통신": 1,
    "uart": 1, "i2c": 1, "spi": 1, "modbus": 1, "dsp": 1, "dsp 개발": 1,
    "제어 알고리즘": 1, "하드웨어 제어": 1, "system software": 1, "시스템 sw": 1
}

# 임베디드 및 시스템 직무 탐색 타겟 키워드
TARGET_KEYWORDS = [
    # 기본 직무 키워드
    "임베디드", "embedded", "펌웨어", "firmware", "c++", "c언어",
    # OS / 시스템 / 커널
    "rtos", "freertos", "zephyr", "linux", "리눅스", "kernel", "커널",
    # 드라이버 / BSP / 하드웨어 제어
    "driver", "드라이버", "mcu", "mpu", "bsp", "stm32", "esp32", "arm", "cortex",
    # 하드웨어 / 반도체 / 제어
    "fpga", "verilog", "dsp", "soc", "제어기", "제어 sw", "제어 알고리즘",
    "모터 제어", "로봇 제어", "전장", "전장 sw", "auto-sar", "autosar",
    "can 통신", "can통신", "modbus", "uart", "i2c", "spi", "디바이스 드라이버"
]

# 제외할 키워드 (오탐 방지)
EXCLUDE_KEYWORDS = [
    "웹 프론트엔드", "react", "vue", "spring boot", "마케팅",
    "영업", "인사", "회계", "재무", "법무", "간호", "임상", "디자이너", "ui/ux",
    "행정", "사무", "물리치료", "영양사", "트레이너", "사격장", "선수",
    "웹 퍼블리셔", "학원", "강사", "단순 조립", "단순노무"
]

# 잡코리아 검색 대상 키워드
JOBKOREA_SEARCH_KEYWORDS = [
    "임베디드", "펌웨어", "RTOS", "임베디드 리눅스", "MCU"
]

# 자소설닷컴 탐색 페이지 수
JASOSEOL_PAGE_LIMIT = 3

# HTTP 요청용 기본 헤더
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}
