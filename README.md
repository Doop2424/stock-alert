# 국내주가 기준가 알림 (GitHub Actions + Gmail + 웹 UI)

15분 간격(장중 09:00~15:30, 평일)으로 등록한 종목의 현재가를 확인하고,
기준가에 도달하면 이메일로 알려줍니다. 종목/기준가/알림메일은 웹 페이지에서 관리합니다.

## 1. Gmail 앱 비밀번호 발급 (최초 1회)

1. Google 계정 → 보안 → 2단계 인증 켜기 (필수)
2. https://myaccount.google.com/apppasswords 접속
3. 앱 이름 아무거나 입력 후 생성 → 16자리 비밀번호 복사

## 2. GitHub Secrets 등록 (최초 1회, 발신 계정만)

레포 → Settings → Secrets and variables → Actions → New repository secret

| Name | Value |
|---|---|
| `GMAIL_USER` | 발신용 Gmail 주소 |
| `GMAIL_APP_PASSWORD` | 위에서 발급한 16자리 앱 비밀번호 |

(알림 받을 이메일은 여기 안 넣습니다 — 웹 UI에서 설정합니다.)

## 3. GitHub Pages 켜기 (웹 UI 접속용)

1. 레포 → Settings → Pages
2. Source: **Deploy from a branch**
3. Branch: **main** / **/(root)** 선택 → Save
4. 1~2분 후 `https://Doop2424.github.io/stock-alert/` 로 접속 가능

⚠️ 이 페이지는 링크를 아는 사람이면 누구나 화면 자체는 열어볼 수 있습니다
(GitHub Pages 공개 특성). 다만 아래 토큰이 없으면 종목/이메일을 보거나
수정할 수 없으니 링크를 남에게 공유하지만 않으면 됩니다.

## 4. Personal Access Token 발급 (최초 1회, 웹 UI 저장용)

1. https://github.com/settings/personal-access-tokens/new 접속
2. Repository access: **Only select repositories** → `stock-alert` 선택
3. Permissions → **Repository permissions → Contents → Read and write**
4. Generate token → 생성된 토큰 복사 (`github_pat_...`)

## 5. 웹 UI에서 종목/기준가/이메일 설정

1. `https://Doop2424.github.io/stock-alert/` 접속
2. 상단 "⚙️ 저장소 연결 설정" 펼치기
3. GitHub 아이디/저장소: `Doop2424/stock-alert` (기본값 그대로 두면 됨)
4. Personal Access Token 붙여넣기 → **불러오기**
5. 종목명 검색창에 이름 입력 → 목록에서 클릭하면 코드 자동 입력
6. 조건(이상/이하)과 기준가 입력
7. "환율 목록"에서 통화 선택(달러/엔화/유로/위안/파운드) + 조건 + 기준환율 입력
8. 알림 받을 이메일 입력
9. **저장하기** 클릭 → repo의 config.json이 자동 커밋됨

토큰과 저장소 정보는 브라우저에만 저장되어, 다음 접속 때는 자동으로 불러옵니다.

## 6. 동작 확인

- 레포 → Actions 탭 → "Stock Price Check" → "Run workflow" 버튼으로 수동 테스트
- 로그에 종목별 현재가가 찍히면 정상 동작
- 기준가 도달 종목이 없으면 이메일은 오지 않습니다 (콘솔 로그로만 확인 가능)

## 참고

- 주가는 네이버 증권 모바일 API 기준이며 약간의 지연이 있을 수 있습니다
- 종목 검색 데이터(`stocks.json`)는 2018년 기준 상장사 목록이라, 이후 신규 상장 종목은
  검색되지 않을 수 있습니다. 이 경우 config.json을 직접 수정해 종목코드를 추가하면 됩니다
- GitHub Actions 무료 사용량: private 레포 기준 월 2,000분 (충분함)
