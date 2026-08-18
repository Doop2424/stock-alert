"""
config.json에 등록된 국내 종목의 현재가를 조회하여
기준가에 도달한 종목이 있으면 이메일로 알림을 보낸다.
조회 결과는 latest.json으로 저장하여 대시보드에서 읽어간다.

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
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
LATEST_PATH = BASE_DIR / "latest.json"
KST = timezone(timedelta(hours=9))

NAVER_API = "https://m.stock.naver.com/api/stock/{code}/basic"
NAVER_FX_API_PRIMARY = (
    "https://m.stock.naver.com/front-api/v1/marketIndex/prices"
    "?page=1&pageSize=1&category=exchange&reutersCode={code}"
)
NAVER_FX_API_FALLBACK = (
    "https://api.stock.naver.com/marketindex/exchange/{code}/prices"
    "?page=1&pageSize=1"
)

# 조회에 성공한 값을 모아 latest.json으로 내보낸다.
PRICES = {}


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        data = json.load(f)
        return data.get("stocks", []), data.get("currencies", []), data["notify_email"]


def _to_number(value):
    """'70,300' / '-1.23' 같은 문자열을 숫자로. 실패하면 None."""
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def _pick_change(data: dict):
    """응답에서 전일 대비 등락률(%)을 찾는다. 키 이름이 바뀔 수 있어 후보를 순서대로 본다."""
    for key in ("fluctuationsRatio", "changeRate", "fluctuationRatio", "compareRatio"):
        rate = _to_number(data.get(key))
        if rate is not None:
            return rate
    return None


def fetch_price(code: str):
    """네이버 증권 모바일 API에서 현재가(원)와 등락률(%)을 조회한다."""
    resp = requests.get(NAVER_API.format(code=code), timeout=10)
    resp.raise_for_status()
    data = resp.json()
    price = int(str(data["closePrice"]).replace(",", ""))
    return price, _pick_change(data)


def fetch_fx_rate(reuters_code: str):
    """네이버 증권 API에서 환율과 등락률을 조회한다. (예: FX_USDKRW)
    네이버가 비공식 API 경로를 종종 바꾸므로, 알려진 두 가지 방식을 순서대로 시도한다.
    """
    # 방식 1: front-api (category=exchange&reutersCode=...)
    try:
        resp = requests.get(NAVER_FX_API_PRIMARY.format(code=reuters_code), timeout=10)
        if resp.ok:
            row = resp.json()["result"][0]
            return float(str(row["closePrice"]).replace(",", "")), _pick_change(row)
    except Exception:
        pass

    # 방식 2: api.stock.naver.com (경로에 코드 직접 포함, 리스트 형태 응답)
    resp = requests.get(NAVER_FX_API_FALLBACK.format(code=reuters_code), timeout=10)
    resp.raise_for_status()
    row = resp.json()[0]
    return float(str(row["closePrice"]).replace(",", "")), _pick_change(row)


def check_condition(price, target, condition: str) -> bool:
    if condition == "above":
        return price >= target
    if condition == "below":
        return price <= target
    raise ValueError(f"알 수 없는 condition: {condition}")


def write_latest():
    """대시보드가 읽어갈 시세 파일을 만든다. 실패해도 알림 흐름은 막지 않는다."""
    payload = {
        "updated": datetime.now(KST).isoformat(timespec="seconds"),
        "prices": PRICES,
    }
    try:
        with open(LATEST_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
        print(f"latest.json 저장 ({len(PRICES)}건)")
    except Exception as e:
        print(f"latest.json 저장 실패: {e}", file=sys.stderr)


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
    stocks, currencies, notify_email = load_config()
    triggered = []
    errors = []

    for stock in stocks:
        code = stock["code"]
        name = stock.get("name", code)
        target = stock["target_price"]
        condition = stock["condition"]

        try:
            price, change = fetch_price(code)
        except Exception as e:
            errors.append(f"{name}({code}) 조회 실패: {e}")
            continue

        entry = {"name": name, "price": price}
        if change is not None:
            entry["change"] = change
        PRICES[code] = entry

        print(f"{name}({code}) 현재가 {price:,}원 / 기준가 {target:,}원 ({condition})")

        if check_condition(price, target, condition):
            triggered.append((name, price, target, condition, "원"))

    for cur in currencies:
        code = cur["code"]  # 예: FX_USDKRW
        name = cur.get("name", code)
        target = cur["target_rate"]
        condition = cur["condition"]

        try:
            rate, change = fetch_fx_rate(code)
        except Exception as e:
            errors.append(f"{name}({code}) 환율 조회 실패: {e}")
            continue

        entry = {"name": name, "price": rate}
        if change is not None:
            entry["change"] = change
        PRICES[code] = entry

        print(f"{name} 현재 환율 {rate:,.2f}원 / 기준 {target:,.2f}원 ({condition})")

        if check_condition(rate, target, condition):
            triggered.append((name, rate, target, condition, "원"))

    # 알림 여부와 무관하게 시세 파일은 항상 갱신한다.
    write_latest()

    if not triggered and not errors:
        print("기준치 도달 항목 없음.")
        return

    lines = []
    for name, value, target, condition, unit in triggered:
        word = "이상" if condition == "above" else "이하"
        lines.append(f"- {name}: 현재 {value:,.2f}{unit} (기준 {target:,.2f}{unit} {word} 도달)")
    for err in errors:
        lines.append(f"- [오류] {err}")

    body = "\n".join(lines)
    subject_parts = []
    if triggered:
        subject_parts.append(f"기준치 도달 {len(triggered)}건")
    if errors:
        subject_parts.append(f"조회오류 {len(errors)}건")
    subject = "[주가/환율 알림] " + ", ".join(subject_parts)

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
