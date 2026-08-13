"""
generate_briefing.py (무료 버전 - AI 호출 없음)
--------------------------------------------
1) data/raw_YYYY-MM-DD.json 을 읽어서
2) 검색에 사용된 키워드를 기준으로 카테고리를 나누고 (규칙 기반, AI 아님)
3) docs/index.html (오늘자) + docs/archive/YYYY-MM-DD.html (아카이브)를 생성한다.

AI API를 전혀 쓰지 않아서 비용이 0원이지만, 대신 "왜 눈여겨볼만한지" 같은
요약 문장은 만들지 않고 기사 제목과 출처만 정리해서 보여준다.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST)
TODAY_STR = TODAY.strftime("%Y-%m-%d")
TODAY_LABEL = TODAY.strftime("%Y년 %m월 %d일")

# 검색 키워드 → 카테고리 매핑 (규칙 기반 분류)
KEYWORD_TO_CATEGORY = {
    "브랜드 캠페인": "브랜드·캠페인",
    "브랜드 전략": "브랜드·캠페인",
    "브랜드 리브랜딩": "브랜드·캠페인",
    "콘텐츠 기획": "콘텐츠·미디어",
    "소비자 트렌드": "소비자·트렌드",
    "마케팅 트렌드": "업계·비즈니스",
    "디지털 마케팅": "업계·비즈니스",
    "광고 업계": "업계·비즈니스",
}

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


def categorize(items):
    """AI 없이, 검색 키워드를 기준으로 카테고리를 붙인다."""
    articles = []
    for it in items:
        category = KEYWORD_TO_CATEGORY.get(it.get("keyword", ""), "기타")
        articles.append(
            {
                "category": category,
                "headline": it["title"],
                "source": it.get("source") or "출처 미상",
                "link": it["link"],
                "keyword": it.get("keyword", ""),
            }
        )
    return articles


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
  font-size:12px;
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
  padding:14px 18px;margin-bottom:8px;
  border-radius:0 3px 3px 0;
}
.card h3{
  font-family:'Noto Serif KR',serif;
  font-size:16.5px;margin:0 0 6px;font-weight:600;
}
.card h3 a{color:var(--ink);text-decoration:none;}
.card h3 a:hover{text-decoration:underline;}
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
    <span>매일 자동 생성 (규칙 기반, AI 요약 없음)</span>
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
  <div class="meta">{source} · #{keyword}</div>
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
                source=a["source"],
                keyword=a["keyword"],
            )
            for a in grouped[cat]
        )
        sections_html += SECTION_TEMPLATE.format(category=cat, color=color, cards=cards)

    return HTML_TEMPLATE.format(date_label=TODAY_LABEL, css=CSS, sections=sections_html)


def update_archive_index():
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
    raw_items = load_raw()
    if not raw_items:
        print("[경고] 수집된 기사가 없습니다.")
        sys.exit(0)

    print(f"[정리중] {len(raw_items)}건 카테고리 분류 (규칙 기반, AI 미사용)")
    articles = categorize(raw_items)
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
