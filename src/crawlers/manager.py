# src/crawlers/manager.py
import logging
from typing import Any
from .base import BaseCrawler
from .wanted import WantedCrawler
from .jobkorea import JobKoreaCrawler
from .jasoseol import JasoseolCrawler

logger = logging.getLogger(__name__)

class JobCrawlerManager:
    """모든 채용 플랫폼 크롤러를 통합 관리하고 공고를 수집/병합/정렬하는 매니저"""

    def __init__(self, crawlers: list[BaseCrawler] | None = None):
        if crawlers is None:
            self.crawlers: list[BaseCrawler] = [
                WantedCrawler(),
                JobKoreaCrawler(),
                JasoseolCrawler()
            ]
        else:
            self.crawlers = crawlers

    def fetch_all_jobs(self) -> list[dict[str, Any]]:
        """
        모든 플랫폼에서 공고를 수집하여 중복을 제거하고
        (is_highlighted DESC, company_type_code ASC, fit_score DESC) 기준으로 정렬하여 반환합니다.
        """
        all_matched_jobs: list[dict[str, Any]] = []

        for crawler in self.crawlers:
            logger.info(f"=== [{crawler.name}] 공고 수집 시작 ===")
            try:
                jobs = crawler.crawl()
                all_matched_jobs.extend(jobs)
            except Exception as e:
                logger.error(f"[{crawler.name}] 수집 중 예외 발생: {e}", exc_info=True)

        # ID 기준 중복 제거
        unique_jobs: list[dict[str, Any]] = []
        seen_ids = set()

        for job in all_matched_jobs:
            job_id = job.get("id")
            if not job_id or job_id in seen_ids:
                continue
            seen_ids.add(job_id)
            unique_jobs.append(job)

        # 정렬: 하이라이트 우선 -> 기업 규모(대기업 1 -> 중견 2...) -> 적합도 점수 높은 순
        unique_jobs.sort(
            key=lambda x: (
                1 if x.get("is_highlighted") else 0,
                -int(x.get("company_type_code", 4)),  # 아래에서 reverse=True 할 때 code 1이 먼저 오도록 처리하거나 튜플 구성
                int(x.get("fit_score", 0))
            ),
            reverse=False
        )
        
        # 더 직관적인 정렬 키:
        # 1. is_highlighted: True (1) 우선 -> -1 if is_highlighted else 0
        # 2. company_type_code: 1 -> 2 -> 3 -> 4 (오름차순)
        # 3. fit_score: 높은 점수 우선 -> -fit_score
        unique_jobs.sort(
            key=lambda x: (
                0 if x.get("is_highlighted") else 1,
                int(x.get("company_type_code", 4)),
                -int(x.get("fit_score", 0))
            )
        )

        logger.info(f"전체 플랫폼 수집 완료: 총 {len(all_matched_jobs)}건 조회 중 고유 공고 {len(unique_jobs)}건 정렬 완료")
        return unique_jobs

    def fetch_all_new_jobs(self) -> list[dict[str, Any]]:
        """fetch_all_jobs와 동일하게 전체 유효 수집 공고를 반환 (하위 호환성 유지)"""
        return self.fetch_all_jobs()
