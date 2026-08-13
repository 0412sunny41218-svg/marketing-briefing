"""
fetch_news.py
--------------
구글 뉴스 RSS(검색 기반)로 마케팅/브랜드/콘텐츠 기획 관련 뉴스를 수집한다.
특정 언론사 RSS는 접근이 자주 막히거나 주소가 바뀌기 때문에,
안정적으로 동작하는 구글 뉴스 검색 RSS(news.google.com/rss/search)를 사용한다.

출력: data/raw_YYYY-MM-DD.json
  [
    {"title": ..., "link": ..., "source": ..., "published": ..., "keyword": ...},
    ...
  ]
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

import feedparser
import requests

# ── 검색 키워드: 마케팅/브랜드/콘텐츠 기획 업계 전반 ─────────────────────────
KEYWORDS = [
    "마케팅 트렌드",
    "브랜드 캠페인",
    "콘텐츠 기획",
    "브랜드 전략",
    "광고 업계",
    "디지털 마케팅",
    "소비자 트렌드",
    "브랜드 리브랜딩",
]

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DailyBriefingBot/1.0)"
}


def build_rss_url(keyword: str) -> str:
    q = quote(keyword)
    return f"https://news.google.com/rss/search?q={q}+when:1d&hl=ko&gl=KR&ceid=KR:ko"


def fetch_keyword(keyword: str, max_items: int = 8):
    url = build_rss_url(keyword)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    parsed = feedparser.parse(resp.content)

    items = []
    for entry in parsed.entries[:max_items]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        source = ""
        if "source" in entry and hasattr(entry.source, "title"):
            source = entry.source.title
        published = entry.get("published", "")

        if not title or not link:
            continue

        items.append(
            {
                "title": title,
                "link": link,
                "source": source,
                "published": published,
                "keyword": keyword,
            }
        )
    return items


def dedupe(items):
    seen_titles = set()
    result = []
    for item in items:
        # 제목 앞부분 기준으로 중복 제거 (같은 기사가 여러 키워드에 걸리는 경우 방지)
        key = item["title"][:30]
        if key in seen_titles:
            continue
        seen_titles.add(key)
        result.append(item)
    return result


def main():
    all_items = []
    for kw in KEYWORDS:
        try:
            print(f"[수집중] {kw}")
            items = fetch_keyword(kw)
            all_items.extend(items)
            time.sleep(1)  # 요청 간 텀
        except Exception as e:
            print(f"[경고] '{kw}' 수집 실패: {e}", file=sys.stderr)

    all_items = dedupe(all_items)
    print(f"[완료] 총 {len(all_items)}건 수집")

    os.makedirs("data", exist_ok=True)
    out_path = f"data/raw_{TODAY}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    print(f"[저장] {out_path}")


if __name__ == "__main__":
    main()
