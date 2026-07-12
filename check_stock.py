"""
config.json에 등록된 국내 종목의 현재가를 조회하여
기준가에 도달한 종목이 있으면 이메일로 알림을 보낸다.

필요한 환경변수 (GitHub Secrets로 등록, 최초 1회만):
  GMAIL_USER          - 발신용 Gmail 주소
  GMAIL_APP_PASSWORD  - Gmail 앱 비밀번호 (일반 로그인 비밀번호 아님)

알림 받을 이메일(TO_EMAIL)은 Secrets가 아니라 config.json의
"notify_email" 값을 사용한다. UI(index.html)에서 자유롭게 변경 가능.
"""

import json
import os
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

import requests

CONFIG_PATH = Path(__file__).parent / "config.json"
NAVER_API = "https://m.stock.naver.com/api/stock/{code}/basic"


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        data = json.load(f)
        return data["stocks"], data["notify_email"]


def fetch_price(code: str) -> int:
    """네이버 증권 모바일 API에서 현재가(원)를 조회한다."""
    resp = requests.get(NAVER_API.format(code=code), timeout=10)
    resp.raise_for_status()
    data = resp.json()
    price_str = data["closePrice"]  # 예: "70,300"
    return int(price_str.replace(",", ""))


def check_condition(price: int, target: int, condition: str) -> bool:
    if condition == "above":
        return price >= target
    if condition == "below":
        return price <= target
    raise ValueError(f"알 수 없는 condition: {condition}")


def send_email(subject: str, body: str, to_email: str):
    gmail_user = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, [to_email], msg.as_string())


def main():
    stocks, notify_email = load_config()
    triggered = []
    errors = []

    for stock in stocks:
        code = stock["code"]
        name = stock.get("name", code)
        target = stock["target_price"]
        condition = stock["condition"]

        try:
            price = fetch_price(code)
        except Exception as e:
            errors.append(f"{name}({code}) 조회 실패: {e}")
            continue

        print(f"{name}({code}) 현재가 {price:,}원 / 기준가 {target:,}원 ({condition})")

        if check_condition(price, target, condition):
            triggered.append((name, code, price, target, condition))

    if not triggered and not errors:
        print("기준치 도달 종목 없음.")
        return

    lines = []
    for name, code, price, target, condition in triggered:
        word = "이상" if condition == "above" else "이하"
        lines.append(f"- {name}({code}): 현재가 {price:,}원 (기준가 {target:,}원 {word} 도달)")
    for err in errors:
        lines.append(f"- [오류] {err}")

    body = "\n".join(lines)
    subject_parts = []
    if triggered:
        subject_parts.append(f"기준가 도달 {len(triggered)}건")
    if errors:
        subject_parts.append(f"조회오류 {len(errors)}건")
    subject = "[주가 알림] " + ", ".join(subject_parts)

    print("--- 이메일 발송 ---")
    print(subject)
    print(body)

    send_email(subject, body, notify_email)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"실행 중 오류: {e}", file=sys.stderr)
        sys.exit(1)
