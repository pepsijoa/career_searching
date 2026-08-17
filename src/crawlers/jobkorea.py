# src/crawlers/jobkorea.py
import re
import requests
import logging
from typing import Any
from bs4 import BeautifulSoup
from .base import BaseCrawler
from config import DEFAULT_HEADERS, JOBKOREA_SEARCH_KEYWORDS

logger = logging.getLogger(__name__)

class JobKoreaCrawler(BaseCrawler):
    """잡코리아(JobKorea) 채용 공고 크롤러"""

    def __init__(self):
        super().__init__(name="잡코리아")
        self.search_url = "https://www.jobkorea.co.kr/Search/"

    def crawl(self) -> list[dict[str, Any]]:
        found_jobs: dict[str, dict[str, Any]] = {}

        for keyword in JOBKOREA_SEARCH_KEYWORDS:
            params = {
                "stext": keyword,
                "tabType": "recruit",
                "Ord": "2",  # 최신 등록/수정일순 정렬
                "Page_No": "1"
            }

            try:
                response = requests.get(
                    self.search_url,
                    params=params,
                    headers=DEFAULT_HEADERS,
                    timeout=10
                )
                if response.status_code != 200:
                    logger.warning(f"[{self.name}] 키워드 '{keyword}' 수집 실패 (상태코드: {response.status_code})")
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                gi_links = soup.find_all("a", href=re.compile(r"/Recruit/GI_Read/(\d+)"))

                for a_tag in gi_links:
                    href = a_tag.get("href", "")
                    m = re.search(r"/Recruit/GI_Read/(\d+)", href)
                    if not m:
                        continue
                    gino = m.group(1)
                    raw_id = gino
                    job_key = f"jobkorea_{raw_id}"
                    if job_key in found_jobs:
                        continue

                    # 최상위 카드 컨테이너 탐색
                    card = a_tag
                    for _ in range(6):
                        if card.parent:
                            card = card.parent
                            if "shadow-list" in (card.get("class") or []):
                                break

                    # 1. 기업 배지/규모
                    badge = ""
                    badge_el = card.find(attrs={"data-sentry-component": "BadgeItem"})
                    if badge_el:
                        badge = badge_el.get_text(strip=True)

                    # 2. 공고 제목
                    title_el = card.find(attrs={"data-sentry-component": "Title"})
                    title = title_el.get_text(strip=True) if title_el else a_tag.get_text(strip=True)

                    # 3. 회사명
                    comp_span = card.find("span", class_=re.compile(r"text-gray700"))
                    company = comp_span.get_text(strip=True) if comp_span else ""

                    # 회사명이 비어있을 경우 폴백
                    if not company:
                        links = card.find_all("a", href=re.compile(r"/Recruit/GI_Read/"))
                        texts = [l.get_text(strip=True) for l in links if l.get_text(strip=True)]
                        if len(texts) > 1:
                            company = texts[1]

                    if not title or not company:
                        continue

                    # 4. 직무 칩(Duty), 지역, 연봉 정보
                    chips = [chip.get_text(strip=True) for chip in card.find_all(attrs={"data-sentry-component": "GrayChip"})]
                    duty_text = " / ".join(chips) if chips else ""

                    # 5. 경력 및 급여
                    career_el = card.find("span", class_=re.compile(r"text-typo-c1-13"))
                    career_info = career_el.get_text(strip=True) if career_el else ""

                    # 6. 마감일 파싱 (공고 카드 내부 텍스트 탐색)
                    deadline_raw = None
                    for text in card.stripped_strings:
                        if any(term in text for term in ["~", "오늘마감", "D-", "상시", "채용시"]):
                            if not any(exc in text for exc in ["연봉", "시행중", "축하금", "경력", "만원", "지원금"]):
                                deadline_raw = text
                                break

                    if self.matches_filter(title=title, company=company, extra_text=duty_text):
                        job_item = self.build_job_item(
                            raw_id=raw_id,
                            title=title,
                            company=company,
                            url=f"https://www.jobkorea.co.kr/Recruit/GI_Read/{gino}",
                            duty=duty_text,
                            raw_deadline=deadline_raw,
                            salary=career_info,
                            meta_size=badge,
                            extra={
                                "gino": gino,
                                "matched_keyword": keyword,
                                "badge": badge,
                                "chips": chips
                            }
                        )
                        found_jobs[job_key] = job_item

            except Exception as e:
                logger.error(f"[{self.name}] 키워드 '{keyword}' 크롤링 중 오류: {e}")

        matched_list = list(found_jobs.values())
        logger.info(f"[{self.name}] {len(matched_list)}건 공고 수집 완료 (검색 키워드: {', '.join(JOBKOREA_SEARCH_KEYWORDS)})")
        return matched_list
