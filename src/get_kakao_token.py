# src/get_kakao_token.py
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# .env 로드
SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent
load_dotenv(ROOT_DIR / ".env")
load_dotenv(SRC_DIR / ".env")

REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:5000")
CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", "")

if not REST_API_KEY:
    print("⚠️ KAKAO_REST_API_KEY가 설정되지 않았습니다.")
    REST_API_KEY = input("카카오 REST API 키를 입력하세요: ").strip()

print(f"\n[1] 브라우저에서 아래 URL로 접속하여 로그인하고 카카오 인가 코드를 발급받으세요:")
print(f"https://kauth.kakao.com/oauth/authorize?client_id={REST_API_KEY}&redirect_uri={REDIRECT_URI}&response_type=code&scope=talk_message\n")

authorize_code = input("발급받은 인가 코드(code)를 입력하세요: ").strip()

if not authorize_code:
    print("❌ 인가 코드가 입력되지 않았습니다.")
    exit(1)

url = "https://kauth.kakao.com/oauth/token"
headers = {
    "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
}

data = {
    "grant_type": "authorization_code",
    "client_id": REST_API_KEY,
    "redirect_uri": REDIRECT_URI,
    "code": authorize_code,
}

if CLIENT_SECRET:
    data["client_secret"] = CLIENT_SECRET

response = requests.post(url, headers=headers, data=data)
tokens = response.json()

if "access_token" in tokens:
    token_file = SRC_DIR / "kakao_tokens.json"
    with open(token_file, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=4, ensure_ascii=False)
    print(f"\n🎉 성공: {token_file} 파일이 정상 생성되었습니다!")
    print(f"🔑 Refresh Token: {tokens.get('refresh_token')}")
    print("\n👉 GitHub Actions에서 사용하려면 GitHub 저장소의 Settings > Secrets and variables > Actions에 다음 Secrets를 추가하세요:")
    print(f"   - KAKAO_REST_API_KEY: {REST_API_KEY}")
    print(f"   - KAKAO_REFRESH_TOKEN: {tokens.get('refresh_token')}")
else:
    print("❌ 토큰 발급 실패:", tokens)