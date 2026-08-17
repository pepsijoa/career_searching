# src/crawlers/analyzer.py
import re
from datetime import datetime, timedelta
from typing import Tuple
from config import MAJOR_CORPS, MID_CORPS, COMPANY_TYPE_NAMES, FIT_WEIGHTS

PUBLIC_FOREIGN_KEYWORDS = [
    "연구원", "공사", "공단", "재단", "진흥원", "외국계",
    "한국전력", "한전", "ETRI", "KIST", "DGIST", "UNIST", "GIST", "KAIST",
    "한국원자력", "한국항공우주연구원", "국방과학연구소", "ADD", "KTL"
]

def analyze_company(company_name: str, meta_size: str = "") -> Tuple[int, str, bool]:
    """
    회사명과 메타 규모 정보를 분석하여 기업 규모 코드(1~4), 명칭, 하이라이트 여부를 반환합니다.
    - 1: 대기업 (is_highlighted = True)
    - 2: 중견기업
    - 3: 공기업/외국계
    - 4: 중소/스타트업
    """
    comp_clean = (company_name or "").strip()
    meta_clean = (meta_size or "").strip().lower()
    comp_lower = comp_clean.lower()

    company_type_code = 4
    is_highlighted = False

    # 1. 메타 데이터(태그/배지) 1차 판별
    if any(k in meta_clean for k in ["대기업", "대기업계열사", "대기업 계열사"]):
        company_type_code = 1
    elif any(k in meta_clean for k in ["중견기업", "중견"]):
        company_type_code = 2
    elif any(k in meta_clean for k in ["공기업", "공공기관", "외국계"]):
        company_type_code = 3

    # 2. 회사명 기반 정밀 매칭 (MAJOR_CORPS 우선 검사)
    for major in MAJOR_CORPS:
        major_l = major.lower()
        # 짧은 영문 약어(SK, LG, KT, CJ, KAI 등)는 단어 경계 검사
        if major_l.isalnum() and len(major_l) <= 3 and major_l.isascii():
            pattern = rf"(?<![a-z0-9]){re.escape(major_l)}(?![a-z0-9])"
            if re.search(pattern, comp_lower):
                company_type_code = 1
                break
        elif major_l in comp_lower:
            company_type_code = 1
            break

    # 3. 중견기업 매칭 (아직 대기업이 아닌 경우)
    if company_type_code != 1:
        for mid in MID_CORPS:
            mid_l = mid.lower()
            if mid_l.isalnum() and len(mid_l) <= 3 and mid_l.isascii():
                pattern = rf"(?<![a-z0-9]){re.escape(mid_l)}(?![a-z0-9])"
                if re.search(pattern, comp_lower):
                    company_type_code = 2
                    break
            elif mid_l in comp_lower:
                company_type_code = 2
                break

    # 4. 공기업 / 공공기관 / 연구원 매칭 (아직 대기업/중견이 아닌 경우)
    if company_type_code not in [1, 2]:
        for pub in PUBLIC_FOREIGN_KEYWORDS:
            pub_l = pub.lower()
            if pub_l.isalnum() and len(pub_l) <= 4 and pub_l.isascii():
                pattern = rf"(?<![a-z0-9]){re.escape(pub_l)}(?![a-z0-9])"
                if re.search(pattern, comp_lower):
                    company_type_code = 3
                    break
            elif pub_l in comp_lower:
                company_type_code = 3
                break

    # 대기업(1)은 하이라이트 공고로 지정
    if company_type_code == 1:
        is_highlighted = True

    company_type_name = COMPANY_TYPE_NAMES.get(company_type_code, "중소/스타트업")
    return company_type_code, company_type_name, is_highlighted

def calculate_fit_score(title: str, description: str = "") -> Tuple[int, str]:
    """
    공고 제목 및 설명 텍스트를 기반으로 임베디드 직무 적합도 점수와 레벨(High/Med/Low)을 계산합니다.
    """
    full_text = f"{title or ''} {description or ''}".lower()
    score = 0

    for keyword, weight in FIT_WEIGHTS.items():
        kw_l = keyword.lower()
        # 짧은 영문/숫자 약어는 단어 경계 정규식 적용
        if kw_l.isalnum() and len(kw_l) <= 4 and kw_l.isascii():
            pattern = rf"(?<![a-z0-9]){re.escape(kw_l)}(?![a-z0-9])"
            if re.search(pattern, full_text):
                score += weight
        elif kw_l in full_text:
            score += weight

    if score >= 5:
        fit_level = "High"
    elif score >= 3:
        fit_level = "Med"
    else:
        fit_level = "Low"

    return score, fit_level

def parse_deadline(deadline_str: str | None) -> str | None:
    """
    다양한 형식의 마감일 문자열을 표준 'YYYY-MM-DD HH:MM:SS' 형식으로 파싱합니다.
    상시채용, 채용시 마감 등 기한이 없거나 파싱 불가능한 경우 None을 반환합니다.
    """
    if not deadline_str:
        return None

    raw = str(deadline_str).strip()
    raw_lower = raw.lower()

    # 상시 / 채용시 마감
    if any(k in raw_lower for k in ["상시", "채용시", "수시", "마감시", "없음", "null", "none"]):
        return None

    now = datetime.now()

    # 1. D-Day 형식: D-7, D-0, D-day, 오늘마감
    if "오늘마감" in raw_lower or "d-0" in raw_lower or "d-day" in raw_lower:
        return now.strftime("%Y-%m-%d 23:59:59")
    
    d_match = re.search(r"d-(\d+)", raw_lower)
    if d_match:
        days = int(d_match.group(1))
        target_date = now + timedelta(days=days)
        return target_date.strftime("%Y-%m-%d 23:59:59")

    # 2. ISO 포맷: 2026-08-31T10:00:00.000+09:00 또는 2026-08-31T23:59:59
    iso_match = re.search(r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2}):(\d{2})", raw)
    if iso_match:
        y, m, d, h, mi, s = iso_match.groups()
        return f"{y}-{m}-{d} {h}:{mi}:{s}"

    # 3. YYYY-MM-DD HH:MM 또는 YYYY.MM.DD HH:MM
    dt_match = re.search(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})\s+(\d{1,2}):(\d{1,2})", raw)
    if dt_match:
        y, m, d, h, mi = dt_match.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d} {int(h):02d}:{int(mi):02d}:00"

    # 4. YYYY-MM-DD 또는 YYYY.MM.DD (시간 없음 -> 당일 23:59:59)
    date_match = re.search(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", raw)
    if date_match:
        y, m, d = date_match.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d} 23:59:59"

    # 5. MM/DD 또는 MM.DD (예: ~ 08/25(일), 08.25)
    md_match = re.search(r"(\d{1,2})[/.](\d{1,2})", raw)
    if md_match:
        m, d = md_match.groups()
        year = now.year
        return f"{year:04d}-{int(m):02d}-{int(d):02d} 23:59:59"

    return None
