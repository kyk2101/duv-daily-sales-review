# DUVETICA Daily Sales Review

폰에서 매일 확인하는 DUVETICA 매출 리뷰 모바일 웹앱.

**📱 폰 접속 URL** (GitHub Pages): https://kyk2101.github.io/duv-daily-sales-review/

기준일: 어제까지 누적 데이터 · 매일 08:00 KST 자동 갱신

---

## 구조 한눈에

```
duv-daily-sales-review/
├── index.html                    # GitHub Pages 진입점 (모바일 최적화 단일 HTML)
├── data/
│   └── duv_review_data.json      # 가공된 시즌/매장/인사이트 데이터
├── src/
│   └── service/sales_review_app/
│       ├── fetch_data.py         # DCS API → %TEMP%/dcs-ai-cli/ 6개 JSON
│       ├── build_app.py          # 6개 JSON → data/duv_review_data.json
│       └── build_html.py         # JSON 임베딩 → index.html
├── scripts/
│   ├── run_daily.bat             # 일일 자동 갱신 wrapper (fetch+build+push)
│   └── setup_scheduler.ps1       # Windows 작업 스케줄러 등록
├── .github/workflows/daily.yml   # Phase 2 클라우드 자동화 (DCS 토큰 발급 후 활성화)
└── README.md
```

## 자동화 동작

```
[Windows 작업 스케줄러]
   매일 08:00 KST + 로그온 직후 + (예약 시간 놓치면 즉시 catch-up)
        ↓
[scripts/run_daily.bat]
   ① fetch_data.py    — dcs-ai-cli로 6개 데이터셋 다운로드 (전일까지)
   ② build_app.py     — 시즌별/컬러별 집계, 인사이트, 매장 TOP15 산출
   ③ build_html.py    — 단일 HTML로 빌드 (JSON 임베드)
   ④ git add/commit/push origin main
        ↓
[GitHub Pages]  자동 배포 (보통 1~2분 내)
        ↓
[폰] 동일 URL → 항상 최신 데이터
```

## 셋업 가이드 (1회)

### 1. 의존성 확인
- Python 3.13 가상환경: `C:\Users\Admin\Desktop\DCSAI\.venv\Scripts\python.exe`
- `dcs-ai-cli` 설치 + OAuth 인증 완료 (Claude Code MCP로 인증 시 영속됨)

### 2. Git 원격 연결 + 첫 push
```bash
cd "C:/Users/Admin/Desktop/DCSAI/project_file/매출리뷰용 어플"
git remote add origin https://github.com/kyk2101/duv-daily-sales-review.git
git add .
git commit -m "init: DUVETICA daily sales review app"
git push -u origin main
```

### 3. GitHub Pages 활성화
1. https://github.com/kyk2101/duv-daily-sales-review/settings/pages
2. Source: **Deploy from a branch**
3. Branch: `main` / `/ (root)` → **Save**
4. 1~2분 후 https://kyk2101.github.io/duv-daily-sales-review/ 접속

### 4. Windows 작업 스케줄러 등록
관리자 PowerShell:
```powershell
cd "C:/Users/Admin/Desktop/DCSAI/project_file/매출리뷰용 어플/scripts"
./setup_scheduler.ps1
```

수동 실행 테스트:
```powershell
Start-ScheduledTask -TaskName DUV_Sales_Review_Daily
```

### 5. 폰에 북마크
홈 화면 추가:
- iOS Safari: 공유 → 홈 화면에 추가
- Android Chrome: 메뉴 → 홈 화면에 추가

## 한계 — 현재 운영의 약점

| 한계 | 영향 | 회피 |
|------|------|------|
| PC가 08:00에 꺼져 있으면 그날 자동 실행 안 됨 | 데이터 갱신 지연 | 켜자마자 catch-up 실행 (StartWhenAvailable=ON) |
| OAuth refresh token 만료 (장기) | 갱신 실패 | DCS팀에서 장기 서비스 토큰 발급 후 GitHub Actions 마이그레이션 |
| GitHub Pages 캐시 | 갱신 직후 1~2분 구버전 보일 수 있음 | 페이지 reload (Ctrl+Shift+R) |

## Phase 2 — 풀 클라우드 자동화 (PC 무관)

DCS팀에서 장기 API 토큰 발급되면:
1. `.github/workflows/daily.yml`의 `if: false` 라인 제거
2. GitHub Secrets에 `DCSAI_TOKEN` 등록
3. `fetch_data.py`를 `dcs-ai-cli` 대신 `requests` 직접 호출로 수정
4. Windows 작업 스케줄러 비활성화 (`Disable-ScheduledTask -TaskName DUV_Sales_Review_Daily`)

이후 PC가 꺼져 있어도 매일 08:00 KST GitHub Actions가 자동 실행.

## 데이터 소스

- DCS 지식그래프 API (`https://dcsai.fnf.co.kr/server/`)
- BRD_CD = `V` (DUVETICA)
- 시즌 SESN: `25F` (FW), `26S` (SS)
- 도구: `get_season_wear_style_order_stor_sale_stock_sale_rt`, `get_channel_product_sale_type`

## 만든 사람

Roybong · DCS AI 프로젝트 · 2026.04
