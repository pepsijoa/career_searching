# src/notifier.py
import os
import json
import requests
import logging
from datetime import datetime
from config import REST_API_KEY, CLIENT_SECRET, REFRESH_TOKEN, TOKEN_FILE, GITHUB_PAGES_URL

logger = logging.getLogger(__name__)

def update_kakao_access_token() -> str | None:
    """
    Refresh Token을 이용해 만료된 Access Token을 자동으로 갱신합니다.
    1. KAKAO_REFRESH_TOKEN 환경변수 (GitHub Secrets) 우선 사용
    2. 로컬 kakao_tokens.json 파일 참조 (개발 환경)
    """
    if not REST_API_KEY:
        logger.error("KAKAO_REST_API_KEY 환경변수가 설정되지 않았습니다. .env 또는 GitHub Secrets를 확인하세요.")
        return None

    refresh_token = REFRESH_TOKEN
    tokens_from_file = {}

    # 환경변수에 없으면 파일에서 읽기 시도
    if not refresh_token and os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                tokens_from_file = json.load(f)
            refresh_token = tokens_from_file.get("refresh_token")
        except Exception as e:
            logger.warning(f"토큰 파일 읽기 실패 ({TOKEN_FILE}): {e}")

    if not refresh_token:
        logger.error("유효한 KAKAO_REFRESH_TOKEN 또는 kakao_tokens.json 파일이 존재하지 않습니다.")
        return None

    try:
        url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": REST_API_KEY,
            "refresh_token": refresh_token
        }
        if CLIENT_SECRET:
            data["client_secret"] = CLIENT_SECRET
        response = requests.post(url, data=data, timeout=10)
        new_tokens = response.json()

        if "access_token" in new_tokens:
            new_access_token = new_tokens["access_token"]
            
            # 로컬 파일이 있거나 쓰기 가능하면 파일 업데이트
            if tokens_from_file or os.path.exists(TOKEN_FILE):
                tokens_from_file["access_token"] = new_access_token
                if "refresh_token" in new_tokens:
                    tokens_from_file["refresh_token"] = new_tokens["refresh_token"]
                try:
                    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                        json.dump(tokens_from_file, f, indent=4, ensure_ascii=False)
                except Exception:
                    pass
            
            logger.info("카카오 Access Token 갱신 성공")
            return new_access_token
        else:
            logger.error(f"카카오 토큰 갱신 응답 오류: {new_tokens}")
            return None
    except Exception as e:
        logger.error(f"카카오 토큰 갱신 중 오류 발생: {e}")
        return None

def format_deadline_label(deadline_str: str | None) -> str:
    """공고 마감일을 보기 좋은 축약 레이블로 포맷팅"""
    if not deadline_str:
        return "상시"

    try:
        dl_dt = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        delta_days = (dl_dt.date() - now.date()).days

        if delta_days == 0:
            return "오늘마감"
        elif 0 < delta_days <= 30:
            return f"D-{delta_days} (~{dl_dt.strftime('%m/%d')})"
        else:
            return f"~{dl_dt.strftime('%m/%d')}"
    except Exception:
        return "~" + deadline_str[:10]

def build_kakao_message_text(job_list: list[dict], max_length: int = 800) -> str:
    """
    단일 카카오톡 메시지 본문 생성 (최대 글자 수 안전 제한 준수)
    1. 하이라이트/대기업 공고 (상세 링크 포함)
    2. 일반 추천 공고 (간결 요약)
    3. 초과 시 '...외 N건' 요약 + 웹 대시보드 링크 직접 노출
    """
    total_count = len(job_list)
    today_str = datetime.now().strftime("%m/%d")
    
    header = f"📢 [임베디드/시스템 채용 알림 ({today_str})]\n오늘의 맞춤 공고: 총 {total_count}건\n"
    dashboard_url = GITHUB_PAGES_URL.rstrip('/')
    footer_guide = f"\n\n👉 [전체 공고 {total_count}건 웹 대시보드]\n🔗 {dashboard_url}"
    
    highlighted_jobs = [j for j in job_list if j.get("is_highlighted")]
    standard_jobs = [j for j in job_list if not j.get("is_highlighted")]

    message_parts = [header]
    included_count = 0

    # 1. 하이라이트 / 주요 대기업 공고 섹션 (URL 포함)
    if highlighted_jobs:
        high_section_lines = ["\n⭐ [주요 기업 / 추천 공고]"]
        for job in highlighted_jobs:
            company = job.get("company", "기업명")
            title = job.get("title", "직무")
            dl_label = format_deadline_label(job.get("deadline"))
            url = job.get("url", "")
            
            item_text = f"• [{company}] {title} ({dl_label})\n  🔗 {url}"
            
            # 길이 검사 (뒤의 접미사 및 웹 대시보드 안내 공간 고려)
            test_content = "\n".join(message_parts + high_section_lines + [item_text]) + f"\n\n...외 {total_count - (included_count + 1)}건 (전체 {total_count}건)" + footer_guide
            if len(test_content) > max_length and included_count > 0:
                break
            high_section_lines.append(item_text)
            included_count += 1

        message_parts.append("\n".join(high_section_lines))

    # 2. 일반 추천 공고 섹션 (간결 요약)
    if standard_jobs and included_count < total_count:
        std_section_lines = ["\n📋 [기타 추천 공고]"]
        for job in standard_jobs:
            company = job.get("company", "기업명")
            title = job.get("title", "직무")
            platform = job.get("platform", "")
            dl_label = format_deadline_label(job.get("deadline"))
            
            item_text = f"• [{platform}] {company} - {title} ({dl_label})"
            
            test_content = "\n".join(message_parts + std_section_lines + [item_text]) + f"\n\n...외 {total_count - (included_count + 1)}건 (전체 {total_count}건)" + footer_guide
            if len(test_content) > max_length and included_count > 0:
                break
            std_section_lines.append(item_text)
            included_count += 1

        message_parts.append("\n".join(std_section_lines))

    # 3. 미포함 공고 수 요약 푸터 및 전체보기 안내
    remaining_count = total_count - included_count
    if remaining_count > 0:
        message_parts.append(f"\n...외 {remaining_count}건 (전체 {total_count}건)")
    
    message_parts.append(footer_guide)

    final_text = "\n".join(message_parts).strip()
    return final_text

def send_kakao_message(job_list: list[dict]) -> bool:
    """
    카카오톡 '나에게 보내기' API를 통해 채용 공고를 1개의 단일 메시지로 통합 발송합니다.
    버튼 클릭 시 GitHub Pages 전체 공고 대시보드로 이동합니다.
    """
    if not job_list:
        logger.info("발송할 공고가 없습니다.")
        return True

    access_token = update_kakao_access_token()
    if not access_token:
        logger.error("유효한 카카오 액세스 토큰을 얻지 못했습니다.")
        return False

    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {access_token}"}

    message_text = build_kakao_message_text(job_list)
    logger.info(f"카카오톡 전송 메시지 생성 (글자 수: {len(message_text)}자 / 최대 1000자)\n{message_text}")

    # 버튼 링크: GitHub Pages 웹 대시보드 URL
    dashboard_url = GITHUB_PAGES_URL or (job_list[0].get("url") if job_list else "https://www.wanted.co.kr")
    button_title = f"전체 공고 웹에서 보기 ({len(job_list)}건)"

    payload = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": message_text,
            "link": {
                "web_url": dashboard_url,
                "mobile_web_url": dashboard_url
            },
            "button_title": button_title
        }, ensure_ascii=False)
    }

    try:
        res = requests.post(url, headers=headers, data=payload, timeout=10)
        if res.status_code == 200:
            logger.info("✅ 카카오톡 단일 통합 알림 메시지 전송 성공!")
            return True
        else:
            logger.error(f"카카오톡 전송 실패: {res.status_code} - {res.text}")
            return False
    except Exception as e:
        logger.error(f"카카오톡 전송 중 예외 발생: {e}")
        return False
