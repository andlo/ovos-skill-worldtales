#!/usr/bin/env python3
"""Build locale/en-us/index.json from Andrew Lang's Fairy Books master
index (Project Gutenberg ebook #30580, produced by David Widger).

This is a one-time/occasional *build-time* script, not something the skill
runs live - per Project Gutenberg's robot access policy, we fetch this page
once here, not on every user request. See:
https://www.gutenberg.org/policy/robot_access.html

Usage:
    python3 scripts/build_lang_index.py
"""
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

INDEX_URL = "https://www.gutenberg.org/files/30580/30580-h/30580-h.htm"
OUT_PATH = Path(__file__).resolve().parents[1] / "locale" / "en-us" / "index.json"

BOOK_NAMES = [
    "Blue Fairy Book", "Red Fairy Book", "Yellow Fairy Book",
    "Violet Fairy Book", "Crimson Fairy Book", "Orange Fairy Book",
    "Brown Fairy Book", "Lilac Fairy Book", "Pink Fairy Book",
    "Grey Fairy Book", "Green Fairy Book", "Olive Fairy Book",
]

# Olive Fairy Book (Gutenberg id 27826) uses a different, page-number-based
# anchor scheme (#Page_1, #Page_9, ...) instead of the #2H_4_NNNN per-story
# anchors every other book uses - excluded from v1, tracked as a follow-up.
EXCLUDED_BOOK_IDS = {"27826"}

HREF_RE = re.compile(
    r"gutenberg\.org/files/(\d+)/\d+-h/(\d+-h\.htm)#([\w.]+)"
)


def fetch_index_html():
    r = requests.get(INDEX_URL, timeout=30)
    r.raise_for_status()
    return r.text


def parse(html):
    soup = BeautifulSoup(html, "html.parser")

    marker = soup.find(string=re.compile("ALPHABETICAL LISTING"))
    if marker:
        for el in list(marker.find_all_next()):
            el.decompose()
        marker.extract()

    entries = {}
    book_idx = -1
    seen_books = set()

    for el in soup.find_all("a"):
        text = " ".join(el.get_text(strip=True).split())
        href = el.get("href", "")
        m = HREF_RE.search(href)
        if not m:
            continue
        book_id, filename, anchor = m.groups()
        if book_id in EXCLUDED_BOOK_IDS:
            continue
        url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-h/{filename}"

        if book_id not in seen_books:
            seen_books.add(book_id)
            book_idx += 1
        book_name = BOOK_NAMES[book_idx] if book_idx < len(BOOK_NAMES) else f"book_{book_id}"

        if not text or (text.isupper() and len(text) > 20):
            continue

        entries[text] = {"url": url, "anchor": f"link{anchor}", "book": book_name, "author": "Andrew Lang"}

    return entries


def main():
    print(f"Fetching {INDEX_URL} ...")
    html = fetch_index_html()
    entries = parse(html)
    print(f"Parsed {len(entries)} stories")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    sys.exit(main())
