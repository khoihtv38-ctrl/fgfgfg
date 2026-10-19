#!/usr/bin/env python3
"""Tải các RSS feed và ghi ra news.json (cùng domain với trang -> không bị CORS/proxy chặn)."""
import json, re, sys, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

FEEDS = [
    ("Global News Canada", "https://globalnews.ca/canada/feed/", "canada"),
    ("CBC Canada", "https://www.cbc.ca/webfeed/rss/rss-canada", "canada"),
    ("Google News Canada", "https://news.google.com/rss/search?q=Canada+when:2d&hl=en-CA&gl=CA&ceid=CA:en", "canada"),
    ("Global News Politics", "https://globalnews.ca/politics/feed/", "politics"),
    ("CBC Politics", "https://www.cbc.ca/webfeed/rss/rss-politics", "politics"),
    ("Google News Politics", "https://news.google.com/rss/search?q=Canada+politics+OR+parliament+OR+%22prime+minister%22+when:3d&hl=en-CA&gl=CA&ceid=CA:en", "politics"),
    ("Global News Economy", "https://globalnews.ca/money/feed/", "business"),
    ("BBC Business", "http://feeds.bbci.co.uk/news/business/rss.xml", "business"),
    ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml", "world"),
    ("BBC Culture", "http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml", "culture"),
    ("VnExpress Travel", "https://e.vnexpress.net/rss/travel.rss", "vietnam"),
    ("BBC Tech", "http://feeds.bbci.co.uk/news/technology/rss.xml", "tech"),
]
NS = {"media": "http://search.yahoo.com/mrss/", "content": "http://purl.org/rss/1.0/modules/content/"}


def text(el, tag, ns=None):
    n = el.find(tag, ns) if ns else el.find(tag)
    return (n.text or "").strip() if n is not None and n.text else ""


def fetch(name, url, cat):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; VCNowBot/1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            root = ET.fromstring(r.read())
    except Exception as e:
        print(f"LỖI {name}: {e}", file=sys.stderr)
        return []
    out = []
    for it in root.iter("item"):
        title, link = text(it, "title"), text(it, "link")
        if not title or not link:
            continue
        try:
            dt = parsedate_to_datetime(text(it, "pubDate")).astimezone(timezone.utc)
        except Exception:
            dt = datetime.now(timezone.utc)
        thumb = ""
        for tag in ("media:content", "media:thumbnail", "enclosure"):
            e = it.find(tag, NS)
            if e is not None and e.get("url"):
                thumb = e.get("url")
                break
        out.append({
            "source": name, "category": cat, "title": title, "link": link,
            "pubDate": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "description": text(it, "description"),
            "content": text(it, "content:encoded", NS),
            "thumbnail": thumb,
        })
    print(f"{name}: {len(out)} bài")
    return out


items = []
for f in FEEDS:
    items += fetch(*f)
if not items:
    sys.exit("Không lấy được bài nào, giữ nguyên news.json cũ")
with open("news.json", "w", encoding="utf-8") as fh:
    json.dump({"updated": datetime.now(timezone.utc).isoformat(), "items": items}, fh, ensure_ascii=False)
