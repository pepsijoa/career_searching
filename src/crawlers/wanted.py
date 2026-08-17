# src/crawlers/wanted.py
import requests
import logging
from typing import Any
from .base import BaseCrawler
from config import DEFAULT_HEADERS

logger = logging.getLogger(__name__)

class WantedCrawler(BaseCrawler):
    """원티드(Wanted) 채용 공고 API 수집기"""

    def __init__(self):
        super().__init__(name="원티드")
        self.api_url = "https://www.wanted.co.kr/api/v4/jobs"

    def crawl(self) -> list[dict[str, Any]]:
        headers = {
            **DEFAULT_HEADERS,
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.wanted.co.kr/wdlist/518"
        }

        # 658: 임베디드 개발자, 900: C/C++ 개발자, 817: 제어 엔지니어
        params = {
            "country": "kr",
            "tag_type_ids": ["658", "900", "817"],
            "job_sort": "job.latest_order",
            "locations": "all",
            "years": "-1",
            "limit": 50
        }

        try:
            response = requests.get(
                self.api_url,
                params=params,
                headers=headers,
                timeout=10
            )
            if response.status_code != 200:
                logger.error(f"[{self.name}] 공고 수집 실패 (상태코드: {response.status_code})")
                return []

            data = response.json().get("data", [])
            matched_jobs = []

            for item in data:
                raw_id = str(item.get("id"))
                position = item.get("position", "")
                company_dict = item.get("company") or {}
                company_name = company_dict.get("name", "")
                industry_name = company_dict.get("industry_name", "")
                due_time = item.get("due_time")
                reward = (item.get("reward") or {}).get("formatted_total", "")
                annual_from = item.get("annual_from")
                annual_to = item.get("annual_to")

                # 경력/급여 표기
                career_str = ""
                if annual_from is not None and annual_to is not None:
                    if annual_from == 0 and annual_to == 0:
                        career_str = "신입/경력무관"
                    else:
                        career_str = f"경력 {annual_from}~{annual_to}년"

                if self.matches_filter(title=position, company=company_name, extra_text=industry_name):
                    job_item = self.build_job_item(
                        raw_id=raw_id,
                        title=position,
                        company=company_name,
                        url=f"https://www.wanted.co.kr/wd/{raw_id}",
                        duty="임베디드/C++ 개발",
                        raw_deadline=due_time,
                        salary=career_str or reward,
                        meta_size="",
                        extra={
                            "reward": reward,
                            "industry": industry_name,
                            "career": career_str,
                            "status": item.get("status")
                        }
                    )
                    matched_jobs.append(job_item)

            logger.info(f"[{self.name}] {len(matched_jobs)}건 공고 수집 완료 (총 {len(data)}건 조회)")
            return matched_jobs

        except Exception as e:
            logger.error(f"[{self.name}] 크롤링 중 오류 발생: {e}")
            return []
