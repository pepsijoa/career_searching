# src/crawlers/jasoseol.py
import requests
import logging
from typing import Any
from .base import BaseCrawler
from config import DEFAULT_HEADERS, JASOSEOL_PAGE_LIMIT

logger = logging.getLogger(__name__)

class JasoseolCrawler(BaseCrawler):
    """자소설닷컴(Jasoseol.com) 채용 공고 크롤러"""

    def __init__(self):
        super().__init__(name="자소설닷컴")
        self.api_url = "https://jasoseol.com/api/v1/employment_companies"

    def crawl(self) -> list[dict[str, Any]]:
        matched_jobs: dict[str, dict[str, Any]] = {}

        for page in range(1, JASOSEOL_PAGE_LIMIT + 1):
            try:
                response = requests.get(
                    self.api_url,
                    params={"page": page},
                    headers=DEFAULT_HEADERS,
                    timeout=10
                )
                if response.status_code != 200:
                    logger.warning(f"[{self.name}] 페이지 {page} 수집 실패 (상태코드: {response.status_code})")
                    break

                companies = response.json()
                if not isinstance(companies, list) or not companies:
                    break

                for comp in companies:
                    comp_id = comp.get("id")
                    comp_name = comp.get("name", "")
                    comp_title = comp.get("title", "")
                    comp_end_time = comp.get("end_time")
                    company_group = comp.get("company_group") or {}
                    group_type = company_group.get("company_type", "")
                    employments = comp.get("employments", [])

                    # 세부 모집분야(employments)가 있는 경우
                    if employments:
                        for emp in employments:
                            emp_id = emp.get("id")
                            field = emp.get("field", "")
                            emp_end_time = emp.get("end_time") or comp_end_time
                            raw_id = f"{comp_id}_{emp_id}"
                            job_key = f"jasoseol_{raw_id}"

                            if job_key in matched_jobs:
                                continue

                            display_title = f"{comp_title} - {field}" if field else comp_title
                            if self.matches_filter(title=display_title, company=comp_name, extra_text=field):
                                job_item = self.build_job_item(
                                    raw_id=raw_id,
                                    title=display_title,
                                    company=comp_name,
                                    url=f"https://jasoseol.com/recruit/{comp_id}",
                                    duty=field or "공개채용",
                                    raw_deadline=emp_end_time,
                                    salary="",
                                    meta_size=group_type or "",
                                    extra={
                                        "company_id": comp_id,
                                        "employment_id": emp_id,
                                        "field": field,
                                        "group_name": company_group.get("name")
                                    }
                                )
                                matched_jobs[job_key] = job_item
                    else:
                        # 세부 분야가 없는 단일 공고인 경우
                        raw_id = str(comp_id)
                        job_key = f"jasoseol_{raw_id}"
                        if job_key not in matched_jobs and self.matches_filter(title=comp_title, company=comp_name):
                            job_item = self.build_job_item(
                                raw_id=raw_id,
                                title=comp_title,
                                company=comp_name,
                                url=f"https://jasoseol.com/recruit/{comp_id}",
                                duty="공개채용",
                                raw_deadline=comp_end_time,
                                salary="",
                                meta_size=group_type or "",
                                extra={
                                    "company_id": comp_id,
                                    "group_name": company_group.get("name")
                                }
                            )
                            matched_jobs[job_key] = job_item

            except Exception as e:
                logger.error(f"[{self.name}] 페이지 {page} 수집 중 오류: {e}")

        matched_list = list(matched_jobs.values())
        logger.info(f"[{self.name}] {len(matched_list)}건 공고 수집 완료 (총 {JASOSEOL_PAGE_LIMIT}페이지 조회)")
        return matched_list
