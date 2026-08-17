# main.py
import requests
import json
import sqlite3
import os

# --- 설정 정보 ---
REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "e75f11430fc77443b6582da2d1a4301a")
TOKEN_FILE = "kakao_tokens.json"
DB_FILE = "jobs.db"

# 임베디드 및 시스템 직무 맞춤 키워드
TARGET_KEYWORDS = [
    "임베디드", "embedded", "펌웨어", "firmware", "c++", "c언어",
    "rtos", "freertos", "linux", "리눅스", "kernel", "커널",
    "driver", "드라이버", "mcu", "bsp", "stm32", "esp32", "arm"
]

# 제외할 키워드 (오탐 방지)
EXCLUDE_KEYWORDS = ["웹 프론트엔드", "react", "vue", "spring boot", "마케팅"]

def init_db():
    """이미 발송한 공고를 기록하여 중복 전송을 방지하는 SQLite DB 초기화"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_already_sent(job_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM sent_jobs WHERE job_id = ?", (str(job_id),))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def record_sent_job(job_id, title, company):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO sent_jobs (job_id, title, company) VALUES (?, ?, ?)", 
                   (str(job_id), title, company))
    conn.commit()
    conn.close()

def update_kakao_access_token():
    """Refresh Token을 이용해 만료된 Access Token을 자동으로 갱신"""
    if not os.path.exists(TOKEN_FILE):
        return None

    with open(TOKEN_FILE, "r") as f:
        tokens = json.load(f)

    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": tokens.get("refresh_token")
    }
    response = requests.post(url, data=data)
    new_tokens = response.json()

    if "access_token" in new_tokens:
        tokens["access_token"] = new_tokens["access_token"]
        if "refresh_token" in new_tokens:
            tokens["refresh_token"] = new_tokens["refresh_token"]
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=4)
        return tokens["access_token"]
    return tokens.get("access_token")

def send_kakao_message(job_list):
    """카카오톡 '나에게 보내기' API를 통해 텍스트/링크 발송"""
    access_token = update_kakao_access_token()
    if not access_token:
        print("카카오 토큰이 유효하지 않습니다.")
        return

    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {access_token}"}

    # 메시지 본문 구성
    message_text = f"📢 [신규 임베디드 채용 공고 ({len(job_list)}건)]\n\n"
    for i, job in enumerate(job_list[:5], start=1):  # 한 번에 최대 5개 표시
        message_text += f"{i}. {job['company']} - {job['position']}\n"
        message_text += f"🔗 https://www.wanted.co.kr/wd/{job['id']}\n\n"

    payload = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": message_text.strip(),
            "link": {
                "web_url": f"https://www.wanted.co.kr/wd/{job_list[0]['id']}",
                "mobile_web_url": f"https://www.wanted.co.kr/wd/{job_list[0]['id']}"
            },
            "button_title": "첫 번째 공고 보기"
        })
    }

    res = requests.post(url, headers=headers, data=payload)
    if res.status_code == 200:
        print(f"카카오톡 알림 전송 완료: {len(job_list)}건")
    else:
        print("전송 실패:", res.text)

def fetch_wanted_jobs():
    """원티드 채용 공고 수집 및 임베디드 직무 필터링"""
    # 원티드 개발 카테고리 (임베디드/C/C++/하드웨어) 검색 파라미터
    url = "https://api.wanted.co.kr/v2/jobs"
    params = {
        "country": "kr",
        "tag_type_ids": "677,678",  # C/C++, 임베디드 관련 태그 ID
        "job_sort": "job.latest_order",
        "locations": "all",
        "years": "0",  # 신입 ~ 3년 차 타겟팅 시 조정 가능
        "limit": 30
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        print("공고 수집 실패:", response.status_code)
        return []

    data = response.json().get("data", [])
    matched_jobs = []

    for item in data:
        job_id = str(item.get("id"))
        position = item.get("position", "")
        company = item.get("company", {}).get("name", "")

        # 이미 발송한 공고 건너뛰기
        if is_already_sent(job_id):
            continue

        full_text = f"{position} {company}".lower()

        # 1. 제외 키워드 체크
        if any(exc.lower() in full_text for exc in EXCLUDE_KEYWORDS):
            continue

        # 2. 대상 키워드 매칭
        if any(tgt.lower() in full_text for tgt in TARGET_KEYWORDS):
            matched_jobs.append({
                "id": job_id,
                "position": position,
                "company": company
            })

    return matched_jobs

def main():
    init_db()
    matched = fetch_wanted_jobs()
    
    if matched:
        print(f"새로운 매칭 공고 {len(matched)}건 발견.")
        send_kakao_message(matched)
        for job in matched:
            record_sent_job(job["id"], job["position"], job["company"])
    else:
        print("새로운 조건 일치 공고가 없습니다.")

if __name__ == "__main__":
    main()