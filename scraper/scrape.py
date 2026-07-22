#!/usr/bin/env python3
"""
Scrapes caravanmagazine.in's homepage (which has no native RSS feed) and
produces a valid RSS 2.0 feed at docs/feed.xml.
"""

import json
import re
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

import requests
from bs4 import BeautifulSoup

HOMEPAGE = "https://caravanmagazine.in/"
SITE_TITLE = "The Caravan"
SITE_LINK = "https://caravanmagazine.in/"
SITE_DESCRIPTION = "Unofficial feed generated from caravanmagazine.in (no official RSS is published by the site)"

# IMPORTANT: set this to your actual GitHub Pages feed URL
FEED_SELF_URL = "https://githb-man.github.io/Caravan-Feed/feed.xml"

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "data" / "seen.json"
FEED_FILE = ROOT / "docs" / "feed.xml"

MAX_AGE_DAYS = 30
MAX_ITEMS = 60

EXCLUDE_PREFIXES = {
    "pages", "tag", "magazine", "archives", "author", "subscribe",
    "masthead", "contact-us", "sponsored-feature", "search",
}

ARTICLE_RE = re.compile(
    r"^https?://(?:www\.)?caravanmagazine\.in/([a-z0-9-]+)/([^/?#]+)/?$",
    re.IGNORECASE,
)


def fetch_homepage_articles():
    resp = requests.get(
        HOMEPAGE,
        headers={"User-Agent": "Mozilla/5.0 (compatible; PersonalRSSBot/1.0)"},
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    found = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("/"):
            href = "https://caravanmagazine.in" + href
        match = ARTICLE_RE.match(href)
        if not match:
            continue
        section = match.group(1).lower()
        if section in EXCLUDE_PREFIXES:
            continue

        title = None
        img = a.find("img")
        if img and img.get("alt"):
            title = img["alt"].strip()
        if not title:
            text = a.get_text(" ", strip=True)
            if text:
                title = text
        if not title:
            continue

        href = href.rstrip("/")
        existing = found.get(href)
        if existing is None or len(title) > len(existing["title"]):
            found[href] = {
                "title": title,
                "category": section.replace("-", " ").title(),
            }

    return found


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def build_feed(state):
    now = datetime.now(timezone.utc)
    items_xml = []

    ordered = sorted(state.items(), key=lambda kv: kv[1]["first_seen"], reverse=True)[:MAX_ITEMS]

    for url, meta in ordered:
        pub_dt = datetime.fromisoformat(meta["first_seen"])
        pub_date = format_datetime(pub_dt)
        title = escape(meta["title"])
        items_xml.append(f"""    <item>
      <title>{title}</title>
      <link>{escape(url)}</link>
      <guid isPermaLink="true">{escape(url)}</guid>
      <category>{escape(meta.get('category', ''))}</category>
      <description>{title}</description>
      <pubDate>{pub_date}</pubDate>
    </item>""")

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(SITE_TITLE)}</title>
    <link>{escape(SITE_LINK)}</link>
    <atom:link href="{escape(FEED_SELF_URL)}" rel="self" type="application/rss+xml" />
    <description>{escape(SITE_DESCRIPTION)}</description>
    <language>en</language>
    <lastBuildDate>{format_datetime(now)}</lastBuildDate>
{chr(10).join(items_xml)}
  </channel>
</rss>
"""
    FEED_FILE.parent.mkdir(parents=True, exist_ok=True)
    FEED_FILE.write_text(feed, encoding="utf-8")


def main():
    state = load_state()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=MAX_AGE_DAYS)

    articles = fetch_homepage_articles()
    if not articles:
        raise SystemExit(
            "No articles found on the homepage. The site's markup probably "
            "changed -- inspect the HTML and update ARTICLE_RE / the link "
            "selection logic in fetch_homepage_articles()."
        )

    for url, meta in articles.items():
        if url in state:
            state[url]["title"] = meta["title"]
            state[url]["category"] = meta["category"]
        else:
            state[url] = {
                "title": meta["title"],
                "category": meta["category"],
                "first_seen": now.isoformat(),
            }

    state = {
        url: meta
        for url, meta in state.items()
        if datetime.fromisoformat(meta["first_seen"]) > cutoff
    }

    save_state(state)
    build_feed(state)
    print(f"Wrote {len(state)} items to {FEED_FILE}")


if __name__ == "__main__":
    main()
