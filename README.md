# 국내주가 기준가 알림 (GitHub Actions + Gmail)

15분 간격(장중 09:00~15:30, 평일)으로 `config.json`에 등록한 종목의 현재가를 확인하고,
기준가에 도달하면 이메일로 알려줍니다.

## 1. GitHub 레포 만들기

1. GitHub에서 새 저장소 생성 (private 권장)
2. 이 폴더의 파일들을 그대로 업로드/푸시

## 2. Gmail 앱 비밀번호 발급 (1회만)

1. Google 계정 → 보안 → 2단계 인증 켜기 (필수)
2. https://myaccount.google.com/apppasswords 접속
3. 앱 이름 아무거나 입력 후 생성 → 16자리 비밀번호 복사
   (일반 Gmail 로그인 비밀번호와 다릅니다)

## 3. GitHub Secrets 등록

레포 → Settings → Secrets and variables → Actions → New repository secret

| Name | Value |
|---|---|
| `GMAIL_USER` | 발신용 Gmail 주소 (예: yourname@gmail.com) |
| `GMAIL_APP_PASSWORD` | 위에서 발급한 16자리 앱 비밀번호 |
| `TO_EMAIL` | 알림 받을 이메일 (본인 Gmail도 가능) |

## 4. 종목/기준가 설정

`config.json`을 직접 수정합니다.

```json
{
  "stocks": [
    {
      "code": "005930",       // 네이버 증권 종목코드
      "name": "삼성전자",
      "condition": "above",   // "above"=이상, "below"=이하
      "target_price": 70000
    }
  ]
}
```

종목코드는 네이버 증권(https://finance.naver.com) 에서 종목 검색 시
URL의 `code=` 뒤 6자리 숫자입니다.

수정 후 그냥 커밋/푸시만 하면 다음 실행부터 바로 반영됩니다.

## 5. 동작 확인

- 레포 → Actions 탭 → "Stock Price Check" → "Run workflow" 버튼으로 수동 테스트 가능
- 정상 동작하면 매 15분마다 자동 실행되고, 기준가 도달 시에만 메일이 옵니다
  (도달 종목 없으면 메일 없음, 콘솔 로그로만 확인 가능)

## 참고

- 주가는 네이버 증권 모바일 API 기준이며 약간의 지연이 있을 수 있습니다
- GitHub Actions 무료 사용량: private 레포 기준 월 2,000분 (이 작업은 1회 실행에 1분 이내라 충분)
- cron 스케줄은 UTC 기준이라 서머타임 등 영향 없이 항상 KST 09:00~15:30에 맞춰 동작합니다
