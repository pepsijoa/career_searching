# src/main.py
import argparse
import logging
import sys
from pathlib import Path

# src 디렉토리를 sys.path에 추가
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from database import init_db, delete_expired_jobs, save_jobs_bulk, get_sent_jobs_count, get_active_jobs
from notifier import send_kakao_message
from crawlers import WantedCrawler, JobKoreaCrawler, JasoseolCrawler, JobCrawlerManager
from web_generator import generate_dashboard_html

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="임베디드 및 시스템 직무 채용 공고 자동 알림 시스템")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 카카오톡 전송 및 DB 저장을 하지 않고 수집 결과만 확인합니다."
    )
    parser.add_argument(
        "--platform",
        choices=["all", "wanted", "jobkorea", "jasoseol"],
        default="all",
        help="수집할 채용 플랫폼 선택 (기본값: all)"
    )
    return parser.parse_args()

def get_crawler_instances(platform_choice: str):
    if platform_choice == "wanted":
        return [WantedCrawler()]
    elif platform_choice == "jobkorea":
        return [JobKoreaCrawler()]
    elif platform_choice == "jasoseol":
        return [JasoseolCrawler()]
    else:
        return [WantedCrawler(), JobKoreaCrawler(), JasoseolCrawler()]

def main():
    args = parse_args()
    logger.info("==========================================")
    logger.info("  임베디드 채용 공고 수집 및 알림 시스템 시작  ")
    logger.info(f"  실행 모드: {'[드라이런 (Dry Run)]' if args.dry_run else '[실제 발송 (Live)]'}, 플랫폼: {args.platform}")
    logger.info("==========================================")

    # 1. SQLite DB 초기화 및 만료 공고 정리
    init_db()
    deleted_count = delete_expired_jobs()
    total_stored = get_sent_jobs_count()
    logger.info(f"DB 상태: 기존 저장 공고 {total_stored}건, 만료 정리 {deleted_count}건")

    # 2. 크롤러 설정 및 전체 공고 수집
    crawlers = get_crawler_instances(args.platform)
    manager = JobCrawlerManager(crawlers=crawlers)
    active_jobs = manager.fetch_all_jobs()

    if not active_jobs:
        logger.info("수집된 조건 일치 공고가 없습니다.")
        return

    highlight_count = sum(1 for j in active_jobs if j.get("is_highlighted"))
    logger.info(f"✨ 매칭 공고 총 {len(active_jobs)}건 수집 완료! (주요/대기업 공고: {highlight_count}건)")

    for idx, job in enumerate(active_jobs[:15], start=1):
        star = "⭐ " if job.get("is_highlighted") else "   "
        logger.info(
            f"{star}[{idx:02d}] [{job.get('platform')}] [{job.get('company_type')}] {job.get('company')} - "
            f"{job.get('title')} (적합도: {job.get('fit_score')}점/{job.get('fit_level')}, 마감: {job.get('deadline') or '상시'})"
        )
    if len(active_jobs) > 15:
        logger.info(f"   ... 외 {len(active_jobs) - 15}건 생략")

    # 3. 웹 대시보드 HTML 자동 생성 (GitHub Pages 연동용)
    generate_dashboard_html(active_jobs)

    # 4. 드라이 런 확인
    if args.dry_run:
        logger.info("ℹ️ [드라이 런 모드] 카카오톡 전송 및 DB 저장을 생략합니다.")
        return

    # 5. DB 일괄 저장
    save_jobs_bulk(active_jobs)
    logger.info(f"✅ 유효 공고 {len(active_jobs)}건 DB 일괄 저장/갱신 완료")

    # 6. 카카오톡 단일 통합 메시지 발송 (웹 대시보드 링크 포함)
    logger.info("카카오톡 통합 알림 메시지 발송을 시도합니다...")
    success = send_kakao_message(active_jobs)

    if success:
        logger.info("🎉 전체 작업(크롤링 -> DB 저장 -> 웹 대시보드 생성 -> 카카오톡 발송)이 성공적으로 완료되었습니다.")
    else:
        logger.warning("⚠️ 카카오톡 전송에 실패했습니다.")

if __name__ == "__main__":
    main()