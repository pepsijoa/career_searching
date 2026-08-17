# src/database.py
import sqlite3
import logging
from datetime import datetime
from typing import Any
from config import DB_FILE

logger = logging.getLogger(__name__)

def init_db():
    """
    확장된 채용 공고 스키마를 지원하는 SQLite DB 초기화 및 자동 마이그레이션
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. 메인 jobs 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            platform TEXT DEFAULT '',
            title TEXT DEFAULT '',
            company TEXT DEFAULT '',
            duty TEXT DEFAULT '',
            deadline TEXT,
            salary TEXT DEFAULT '',
            company_type TEXT DEFAULT '중소/스타트업',
            company_type_code INTEGER DEFAULT 4,
            fit_score INTEGER DEFAULT 0,
            fit_level TEXT DEFAULT 'Low',
            is_highlighted INTEGER DEFAULT 0,
            url TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. 하위 호환용 sent_jobs 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            platform TEXT DEFAULT '',
            url TEXT DEFAULT '',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. jobs 테이블 컬럼 자동 마이그레이션
    cursor.execute("PRAGMA table_info(jobs)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    
    expected_cols = {
        "platform": "TEXT DEFAULT ''",
        "title": "TEXT DEFAULT ''",
        "company": "TEXT DEFAULT ''",
        "duty": "TEXT DEFAULT ''",
        "deadline": "TEXT",
        "salary": "TEXT DEFAULT ''",
        "company_type": "TEXT DEFAULT '중소/스타트업'",
        "company_type_code": "INTEGER DEFAULT 4",
        "fit_score": "INTEGER DEFAULT 0",
        "fit_level": "TEXT DEFAULT 'Low'",
        "is_highlighted": "INTEGER DEFAULT 0",
        "url": "TEXT DEFAULT ''",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "sent_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    for col, col_type in expected_cols.items():
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col} {col_type}")

    # 4. 기존 sent_jobs 데이터를 jobs 테이블로 동기화 마이그레이션
    cursor.execute("""
        INSERT OR IGNORE INTO jobs (job_id, platform, title, company, url, sent_at)
        SELECT job_id, platform, title, company, url, sent_at FROM sent_jobs
    """)

    conn.commit()
    conn.close()
    logger.info("SQLite 데이터베이스(jobs, sent_jobs) 초기화 및 마이그레이션 완료")

def delete_expired_jobs() -> int:
    """
    현재 시간 기준 마감일이 지난 공고 및 30일이 경과한 상시채용(deadline NULL) 공고 삭제
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. 마감일이 존재하는 공고 중 마감 시간이 지난 공고 삭제
    cursor.execute("""
        DELETE FROM jobs
        WHERE deadline IS NOT NULL AND deadline < ?
    """, (now_str,))
    deleted_deadline = cursor.rowcount

    # 2. deadline이 NULL인 상시 채용 공고 중 30일 경과 공고 삭제
    cursor.execute("""
        DELETE FROM jobs
        WHERE deadline IS NULL AND (
            datetime(created_at) < datetime('now', '-30 days')
            OR datetime(sent_at) < datetime('now', '-30 days')
        )
    """)
    deleted_sangsi = cursor.rowcount

    total_deleted = deleted_deadline + deleted_sangsi
    conn.commit()
    conn.close()

    if total_deleted > 0:
        logger.info(f"만료 공고 정리 완료: 총 {total_deleted}건 삭제 (기한만료 {deleted_deadline}건, 30일경과 상시 {deleted_sangsi}건)")
    else:
        logger.info("만료 공고 정리 완료: 삭제 대상 없음")

    return total_deleted

def save_jobs_bulk(jobs: list[dict[str, Any]]):
    """
    수집된 공고 리스트를 executemany를 활용해 일괄 저장/갱신합니다.
    """
    if not jobs:
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    rows = []
    sent_rows = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for job in jobs:
        job_id = str(job.get("id"))
        platform = job.get("platform", "")
        title = job.get("title", "")
        company = job.get("company", "")
        duty = job.get("duty", "")
        deadline = job.get("deadline")
        salary = job.get("salary", "")
        company_type = job.get("company_type", "중소/스타트업")
        company_type_code = int(job.get("company_type_code", 4))
        fit_score = int(job.get("fit_score", 0))
        fit_level = job.get("fit_level", "Low")
        is_highlighted = 1 if job.get("is_highlighted") else 0
        url = job.get("url", "")

        rows.append((
            job_id, platform, title, company, duty, deadline, salary,
            company_type, company_type_code, fit_score, fit_level,
            is_highlighted, url, now_str, now_str
        ))

        sent_rows.append((
            job_id, title, company, platform, url, now_str
        ))

    cursor.executemany("""
        INSERT INTO jobs (
            job_id, platform, title, company, duty, deadline, salary,
            company_type, company_type_code, fit_score, fit_level,
            is_highlighted, url, created_at, sent_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_id) DO UPDATE SET
            platform = excluded.platform,
            title = excluded.title,
            company = excluded.company,
            duty = excluded.duty,
            deadline = excluded.deadline,
            salary = excluded.salary,
            company_type = excluded.company_type,
            company_type_code = excluded.company_type_code,
            fit_score = excluded.fit_score,
            fit_level = excluded.fit_level,
            is_highlighted = excluded.is_highlighted,
            url = excluded.url,
            sent_at = excluded.sent_at
    """, rows)

    cursor.executemany("""
        INSERT OR REPLACE INTO sent_jobs (job_id, title, company, platform, url, sent_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sent_rows)

    conn.commit()
    conn.close()
    logger.info(f"공고 {len(jobs)}건 DB 일괄 저장 완료")

def get_active_jobs() -> list[dict[str, Any]]:
    """
    마감되지 않은 유효 공고 조회
    정렬 기준: is_highlighted DESC, company_type_code ASC, fit_score DESC, sent_at DESC
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        SELECT job_id, platform, title, company, duty, deadline, salary,
               company_type, company_type_code, fit_score, fit_level,
               is_highlighted, url, created_at, sent_at
        FROM jobs
        WHERE (deadline IS NULL OR deadline >= ?)
        ORDER BY is_highlighted DESC, company_type_code ASC, fit_score DESC, sent_at DESC
    """, (now_str,))

    rows = cursor.fetchall()
    active_jobs = [dict(row) for row in rows]
    conn.close()
    return active_jobs

def is_already_sent(job_id: str) -> bool:
    """공고 ID가 이미 DB에 등록되어 있는지 확인"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM jobs WHERE job_id = ?", (str(job_id),))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def record_sent_job(job_id: str, title: str, company: str, platform: str = "", url: str = ""):
    """단일 공고 저장 (하위 호환용)"""
    save_jobs_bulk([{
        "id": job_id,
        "title": title,
        "company": company,
        "platform": platform,
        "url": url
    }])

def get_sent_jobs_count() -> int:
    """누적 공고 수 조회"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    count = cursor.fetchone()[0]
    conn.close()
    return count
