# get_kakao_token.py
import requests
import json

REST_API_KEY = "e75f11430fc77443b6582da2d1a4301a"
REDIRECT_URI = "http://localhost:5000"
AUTHORIZE_CODE = "4b1vWo4evdZnthRoDeqmuD51kRMAxTGLisEUW7R4_3TReZm6b2ZafQAAAAQKDQ1fAAABoA9d_xLmTYKY7N6ACw"
CLIENT_SECRET = "gO230Jsiwo1eN0RnkK4vxi1DVBkmi6mC"

url = "https://kauth.kakao.com/oauth/token"
headers = {
    "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
}

data = {
    "grant_type": "authorization_code",
    "client_id": REST_API_KEY.strip(),
    "redirect_uri": REDIRECT_URI,
    "code": AUTHORIZE_CODE.strip(),
}

if CLIENT_SECRET.strip():
    data["client_secret"] = CLIENT_SECRET.strip()

response = requests.post(url, headers=headers, data=data)
tokens = response.json()

if "access_token" in tokens:
    with open("kakao_tokens.json", "w") as f:
        json.dump(tokens, f, indent=4)
    print("성공: kakao_tokens.json 파일이 정상 생성되었습니다.")
else:
    print("토큰 발급 실패:", tokens)