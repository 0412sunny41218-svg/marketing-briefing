# 오늘의 마케팅 브리핑

마케팅·브랜드·콘텐츠 기획 업계 뉴스를 매일 아침 자동으로 수집·요약해서
정적 웹사이트로 발행하는 파이프라인입니다.

작동 방식: 구글 뉴스 RSS 검색 → Claude API 요약/분류 → 정적 HTML 생성 →
GitHub Actions가 매일 자동 실행 → GitHub Pages로 배포

---

## 1. GitHub 저장소 만들기

1. GitHub에서 새 저장소 생성 (예: `marketing-briefing`), Public으로 설정
2. 이 폴더(`marketing-briefing/`) 전체를 저장소에 push

```bash
cd marketing-briefing
git init
git add .
git commit -m "init: 마케팅 브리핑 파이프라인"
git branch -M main
git remote add origin https://github.com/본인아이디/marketing-briefing.git
git push -u origin main
```

## 2. Claude API 키 등록 (Secrets)

1. 저장소 페이지 → **Settings → Secrets and variables → Actions**
2. **New repository secret** 클릭
3. Name: `ANTHROPIC_API_KEY`, Value: 본인의 Anthropic API 키 입력
   - API 키는 https://console.anthropic.com 에서 발급 (Claude.ai 앱 계정과는 별도)

## 3. GitHub Pages 켜기

1. 저장소 **Settings → Pages**
2. Source: `Deploy from a branch`
3. Branch: `main`, 폴더: `/docs` 선택 → Save
4. 잠시 후 `https://본인아이디.github.io/marketing-briefing/` 로 접속 가능

## 4. 자동 실행 확인

- 기본 설정: 매일 한국시간 오전 7시에 자동 실행 (`.github/workflows/daily-briefing.yml`)
- 시간 바꾸고 싶으면 워크플로 파일의 `cron: "0 22 * * *"` 부분 수정
  (UTC 기준이라 한국시간 -9시간으로 계산)
- 지금 바로 테스트하고 싶으면: 저장소 **Actions** 탭 → `Daily Marketing Briefing` →
  **Run workflow** 버튼으로 수동 실행 가능

## 5. 로컬에서 미리 테스트하기 (선택)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=본인의_API_키
python scripts/fetch_news.py
python scripts/generate_briefing.py
open docs/index.html   # 맥 기준, 윈도우는 그냥 더블클릭
```

---

## 커스터마이징 포인트

| 바꾸고 싶은 것 | 어디를 수정 |
|---|---|
| 검색 키워드 | `scripts/fetch_news.py` 의 `KEYWORDS` 리스트 |
| 카테고리/분류 기준 | `scripts/generate_briefing.py` 의 `system_prompt` |
| 디자인(색상, 폰트, 레이아웃) | `scripts/generate_briefing.py` 의 `CSS`, `HTML_TEMPLATE` |
| 실행 시간 | `.github/workflows/daily-briefing.yml` 의 `cron` |
| 기사 개수 | `fetch_news.py`의 `max_items` 값 |

## 폴더 구조

```
marketing-briefing/
├── scripts/
│   ├── fetch_news.py         # 뉴스 수집
│   └── generate_briefing.py  # 요약 + 사이트 생성
├── data/                     # 수집된 원본 데이터 (자동 생성)
├── docs/                     # GitHub Pages로 배포되는 실제 사이트
│   ├── index.html            # 오늘자 브리핑
│   └── archive/              # 지난 브리핑 아카이브
├── .github/workflows/
│   └── daily-briefing.yml    # 매일 자동 실행 설정
└── requirements.txt
```
