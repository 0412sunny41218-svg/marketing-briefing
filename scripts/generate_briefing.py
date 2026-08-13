"""
generate_briefing.py
---------------------
1) data/raw_YYYY-MM-DD.json 을 읽어서
2) Claude API로 카테고리 분류 + 2~3문장 요약을 만들고
3) docs/index.html (오늘자) + docs/archive/YYYY-MM-DD.html (아카이브)를 생성한다.

환경변수 ANTHROPIC_API_KEY 필요 (GitHub Actions Secrets로 주입).
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

import requests

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST)
TODAY_STR = TODAY.strftime("%Y-%m-%d")
TODAY_LABEL = TODAY.strftime("%Y년 %m월 %d일")

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-5"

CATEGORY_COLOR = {
    "브랜드·캠페인": "#3E6E64",
    "콘텐츠·미디어": "#6B4C6B",
    "소비자·트렌드": "#45566B",
    "업계·비즈니스": "#8A6A2F",
    "기타": "#5B665F",
}
CATEGORY_ORDER = ["브랜드·캠페인", "콘텐츠·미디어", "소비자·트렌드", "업계·비즈니스", "기타"]


def load_raw():
    path = f"data/raw_{TODAY_STR}.json"
    if not os.path.exists(path):
        print(f"[에러] {path} 없음. fetch_news.py를 먼저 실행하세요.", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def call_claude(items):
    """수집된 기사 목록을 Claude에게 보내 분류+요약된 JSON을 받는다."""
    listing = "\n".join(
        f"{i+1}. [{it['source']}] {it['title']} ({it['link']})"
        for i, it in enumerate(items)
    )

    system_prompt = (
        "너는 마케팅/브랜드/콘텐츠 기획 취업 준비생을 위한 뉴스 브리핑 편집자야. "
        "아래 기사 목록에서 실제로 마케팅, 브랜드 전략, 콘텐츠 기획, 광고, 소비자 트렌드와 "
        "관련이 있는 기사만 골라 정리해. 중복되거나 같은 사안을 다루는 기사는 하나로 합쳐. "
        "관련성이 낮은 기사(단순 주가, 스포츠, 정치성 기사 등)는 제외해.\n\n"
        "각 기사는 다음 카테고리 중 하나로 분류: 브랜드·캠페인, 콘텐츠·미디어, 소비자·트렌드, 업계·비즈니스, 기타\n\n"
        "반드시 아래 JSON 형식으로만 응답해. 다른 텍스트나 코드블록 표시(```) 없이 순수 JSON 배열만:\n"
        '[{"category": "...", "headline": "간결한 한국어 헤드라인 (원제목 다듬어도 됨)", '
        '"summary": "2~3문장 한국어 요약, 취업준비생 관점에서 왜 눈여겨볼만한지 포함", '
        '"source": "...", "link": "..."}]'
    )

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 4000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": listing}],
        },
        timeout=120,
    )
    if resp.status_code >= 400:
        print(f"[API 에러 상세] status={resp.status_code} body={resp.text}", file=sys.stderr)
    resp.raise_for_status()
    data = resp.json()
    text = "".join(
        block["text"] for block in data["content"] if block.get("type") == "text"
    )
    text = re.sub(r"^```json|```$", "", text.strip(), flags=re.MULTILINE).strip()
    return json.loads(text)


CSS = """
:root{
  --paper:#E4E7DE;
  --paper-raised:#EEF0E8;
  --ink:#22312A;
  --ink-soft:#4B5A50;
  --accent:#C99A3B;
  --rule:#C7CBB9;
  --mono:#5B665F;
}
*{box-sizing:border-box;}
body{
  margin:0;
  background:var(--paper);
  color:var(--ink);
  font-family:'Pretendard',-apple-system,sans-serif;
  line-height:1.55;
}
.wrap{max-width:760px;margin:0 auto;padding:48px 24px 96px;}
.masthead{
  display:flex;justify-content:space-between;align-items:flex-end;
  border-bottom:3px solid var(--ink);
  padding-bottom:18px;margin-bottom:8px;
}
.masthead h1{
  font-family:'Noto Serif KR',serif;
  font-size:34px;font-weight:700;margin:0;letter-spacing:-0.5px;
}
.stamp{
  font-family:'IBM Plex Mono',monospace;
  font-size:12px;color:var(--mono);
  border:1.5px solid var(--accent);
  color:var(--accent);
  padding:6px 12px;border-radius:2px;
  transform:rotate(2deg);
  white-space:nowrap;
}
.dateline{
  font-family:'IBM Plex Mono',monospace;
  font-size:13px;color:var(--mono);
  margin:10px 0 40px;
  display:flex;justify-content:space-between;
}
.section{margin-bottom:36px;}
.section-title{
  font-family:'IBM Plex Mono',monospace;
  font-size:13px;letter-spacing:1px;text-transform:uppercase;
  color:#fff;display:inline-block;padding:3px 10px;margin-bottom:14px;
}
.card{
  background:var(--paper-raised);
  border-left:4px solid var(--rule);
  padding:16px 18px;margin-bottom:10px;
  border-radius:0 3px 3px 0;
}
.card h3{
  font-family:'Noto Serif KR',serif;
  font-size:18px;margin:0 0 8px;font-weight:600;
}
.card h3 a{color:var(--ink);text-decoration:none;}
.card h3 a:hover{text-decoration:underline;}
.card p{margin:0 0 10px;font-size:14.5px;color:var(--ink-soft);}
.card .meta{
  font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--mono);
}
footer{
  margin-top:60px;padding-top:20px;border-top:1px solid var(--rule);
  font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--mono);
  display:flex;justify-content:space-between;
}
footer a{color:var(--mono);}
@media (max-width:600px){
  .masthead{flex-direction:column;align-items:flex-start;gap:12px;}
  .masthead h1{font-size:26px;}
}
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>오늘의 마케팅 브리핑 · {date_label}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{css}</style>
</head>
<body>
<div class="wrap">
  <div class="masthead">
    <h1>오늘의 마케팅 브리핑</h1>
    <div class="stamp">DAILY BRIEF</div>
  </div>
  <div class="dateline">
    <span>{date_label}</span>
    <span><a href="archive/index.html" style="color:inherit">지난 브리핑 →</a></span>
  </div>
  {sections}
  <footer>
    <span>마케팅·브랜드·콘텐츠 기획 뉴스 자동 브리핑</span>
    <span>매일 자동 생성</span>
  </footer>
</div>
</body>
</html>
"""

SECTION_TEMPLATE = """
<div class="section">
  <span class="section-title" style="background:{color}">{category}</span>
  {cards}
</div>
"""

CARD_TEMPLATE = """
<div class="card" style="border-left-color:{color}">
  <h3><a href="{link}" target="_blank" rel="noopener">{headline}</a></h3>
  <p>{summary}</p>
  <div class="meta">{source}</div>
</div>
"""


def render_html(articles):
    grouped = {}
    for a in articles:
        grouped.setdefault(a.get("category", "기타"), []).append(a)

    sections_html = ""
    for cat in CATEGORY_ORDER:
        if cat not in grouped:
            continue
        color = CATEGORY_COLOR.get(cat, "#5B665F")
        cards = "".join(
            CARD_TEMPLATE.format(
                color=color,
                link=a["link"],
                headline=a["headline"],
                summary=a["summary"],
                source=a["source"],
            )
            for a in grouped[cat]
        )
        sections_html += SECTION_TEMPLATE.format(category=cat, color=color, cards=cards)

    return HTML_TEMPLATE.format(date_label=TODAY_LABEL, css=CSS, sections=sections_html)


def update_archive_index():
    """docs/archive 안의 파일 목록을 읽어 archive/index.html 목록 페이지를 갱신"""
    arch_dir = "docs/archive"
    os.makedirs(arch_dir, exist_ok=True)
    files = sorted(
        [f for f in os.listdir(arch_dir) if re.match(r"\d{4}-\d{2}-\d{2}\.html", f)],
        reverse=True,
    )
    items = "\n".join(
        f'<li><a href="{f}">{f.replace(".html","")}</a></li>' for f in files
    )
    page = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<title>지난 브리핑 목록</title>
<style>{CSS}
ul{{list-style:none;padding:0;}}
li{{padding:8px 0;border-bottom:1px solid var(--rule);font-family:'IBM Plex Mono',monospace;}}
li a{{color:var(--ink);text-decoration:none;}}
</style></head>
<body><div class="wrap">
<div class="masthead"><h1>지난 브리핑</h1></div>
<ul>{items}</ul>
<p><a href="../index.html">← 오늘 브리핑으로</a></p>
</div></body></html>"""
    with open(f"{arch_dir}/index.html", "w", encoding="utf-8") as f:
        f.write(page)


def main():
    if not API_KEY:
        print("[에러] ANTHROPIC_API_KEY 환경변수가 없습니다.", file=sys.stderr)
        sys.exit(1)

    raw_items = load_raw()
    if not raw_items:
        print("[경고] 수집된 기사가 없습니다.")
        sys.exit(0)

    print(f"[요약중] Claude API 호출 ({len(raw_items)}건)")
    articles = call_claude(raw_items)
    print(f"[완료] {len(articles)}건 정리됨")

    html = render_html(articles)

    os.makedirs("docs/archive", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    with open(f"docs/archive/{TODAY_STR}.html", "w", encoding="utf-8") as f:
        f.write(html)

    update_archive_index()
    print("[저장] docs/index.html, docs/archive/*.html")


if __name__ == "__main__":
    main()
