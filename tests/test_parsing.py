"""Tests for get_story_paragraphs() against a saved HTML fragment shaped
like a real Project Gutenberg book page - deliberately not hitting the
live site in CI."""
import requests
import pytest
from bs4 import BeautifulSoup

from conftest import StoryFetchError

BOOK_HTML = """
<html><body>
<a href="#link2H_4_0006"> An Earlier Tale </a>
<a id="link2H_4_0007">
<!--  H2 anchor --> </a>
<div style="height: 4em;"><br/></div>
<h2>CINDERELLA, OR THE LITTLE GLASS SLIPPER</h2>
<p>Once there was a gentleman who married a proud woman.</p>
<p>She had two daughters of her own humour.</p>
<a id="link2H_4_0008">
<!--  H2 anchor --> </a>
<h2>THE NEXT STORY</h2>
<p>This text belongs to the next story and must not be included.</p>
</body></html>
"""

MISSING_ANCHOR_HTML = "<html><body><p>no anchors here</p></body></html>"


def test_get_story_paragraphs(skill, monkeypatch):
    monkeypatch.setattr(skill, "_get_book_soup", lambda url: BeautifulSoup(BOOK_HTML, "html.parser"))
    entry = {"url": "http://example.test/book.htm", "anchor": "link2H_4_0007", "book": "Blue Fairy Book"}
    paragraphs = skill.get_story_paragraphs(entry)
    assert paragraphs == [
        "Once there was a gentleman who married a proud woman.",
        "She had two daughters of her own humour.",
    ]


def test_get_story_paragraphs_missing_anchor_raises(skill, monkeypatch):
    monkeypatch.setattr(skill, "_get_book_soup", lambda url: BeautifulSoup(MISSING_ANCHOR_HTML, "html.parser"))
    entry = {"url": "http://example.test/book.htm", "anchor": "link2H_4_9999", "book": "Blue Fairy Book"}
    with pytest.raises(StoryFetchError):
        skill.get_story_paragraphs(entry)


def test_get_book_soup_caches_and_wraps_request_exception(skill, monkeypatch):
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(requests, "get", fake_get)
    with pytest.raises(StoryFetchError):
        skill._get_book_soup("http://example.test/down.htm")
    assert len(calls) == 1
