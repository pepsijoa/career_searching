# src/crawlers/base.py
from abc import ABC, abstractmethod
import logging
import re
from typing import Any
from config import TARGET_KEYWORDS, EXCLUDE_KEYWORDS
from .analyzer import analyze_company, calculate_fit_score, parse_deadline

logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    """채용 공고 크롤러 기본 인터페이스"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def crawl(self) -> list[dict[str, Any]]:
        """
        플랫폼별 채용 공고를 수집하여 표준 딕셔너리 리스트로 반환합니다.
        
        반환 규격:
        [
            {
                "id": "wanted_12345",
                "platform": "원티드",
                "title": "임베디드 리눅스 BSP 엔지니어",
                "company": "현대오토에버",
                "duty": "임베디드 SW",
                "deadline": "2026-08-31 23:59:59",
                "salary": "회사내규",
                "company_type": "대기업",
                "company_type_code": 1,
                "fit_score": 12,
                "fit_level": "High",
                "is_highlighted": True,
                "url": "https://www.wanted.co.kr/wd/12345",
                "extra": {...}
            }, ...
        ]
        """
        pass

    def matches_filter(self, title: str, company: str = "", extra_text: str = "") -> bool:
        """
        공고 제목, 회사명, 상세 텍스트를 검사하여 타겟 키워드와 매칭되고 제외 키워드에 걸리지 않는지 판단
        - 영문 약어(예: arm, mcu, soc, bsp 등)는 단어 경계를 고려하여 오탐 방지
        """
        full_text = f"{title or ''} {company or ''} {extra_text or ''}".lower()

        # 1. 제외 키워드 체크
        if any(exc.lower() in full_text for exc in EXCLUDE_KEYWORDS):
            return False

        # 2. 대상 키워드 매칭
        for tgt in TARGET_KEYWORDS:
            tgt_l = tgt.lower()
            # 영문/숫자 전용 4글자 이하 짧은 단어(soc, bsp, arm, mcu 등)는 앞뒤 단어 경계 검사
            if tgt_l.isalnum() and len(tgt_l) <= 4 and tgt_l.isascii():
                pattern = rf"(?<![a-z0-9]){re.escape(tgt_l)}(?![a-z0-9])"
                if re.search(pattern, full_text):
                    return True
            elif tgt_l in full_text:
                return True

        return False

    def build_job_item(
        self,
        raw_id: str,
        title: str,
        company: str,
        url: str,
        duty: str = "",
        raw_deadline: str | None = None,
        salary: str = "",
        meta_size: str = "",
        extra: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        수집된 데이터를 표준 규격의 공고 딕셔너리로 조립합니다.
        """
        company_type_code, company_type, is_highlighted = analyze_company(
            company_name=company,
            meta_size=meta_size
        )
        
        fit_score, fit_level = calculate_fit_score(
            title=title,
            description=f"{duty} {company} {' '.join(str(v) for v in (extra or {}).values())}"
        )
        
        parsed_dl = parse_deadline(raw_deadline)

        return {
            "id": f"{self.name_prefix}_{raw_id}",
            "platform": self.name,
            "title": title.strip(),
            "company": company.strip(),
            "duty": duty.strip(),
            "deadline": parsed_dl,
            "salary": salary.strip(),
            "company_type": company_type,
            "company_type_code": company_type_code,
            "fit_score": fit_score,
            "fit_level": fit_level,
            "is_highlighted": is_highlighted,
            "url": url.strip(),
            "extra": extra or {}
        }

    @property
    def name_prefix(self) -> str:
        """ID 생성용 플랫폼 영문 prefix"""
        prefixes = {
            "원티드": "wanted",
            "잡코리아": "jobkorea",
            "자소설닷컴": "jasoseol"
        }
        return prefixes.get(self.name, self.name.lower())
