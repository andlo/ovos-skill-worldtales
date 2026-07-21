"""Tests for the bundled locale/en-us/index.json - built by
scripts/build_lang_index.py from Project Gutenberg ebook #30580."""
import json
from pathlib import Path

INDEX_PATH = Path(__file__).resolve().parents[1] / "locale" / "en-us" / "index.json"


def test_index_file_exists_and_is_valid_json():
    assert INDEX_PATH.is_file()
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert len(data) > 300  # 389 at time of writing


def test_index_entries_have_required_fields():
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    for title, entry in data.items():
        assert entry["url"].startswith("https://www.gutenberg.org/files/")
        # most anchors are 'link2H_4_NNNN', but Red/Brown Fairy Book were
        # re-published on Gutenberg with a 'chapNN' scheme and got repaired
        # via their own contents table (see build_lang_index.py) - either
        # is valid, just must be non-empty
        assert entry["anchor"]
        assert entry["book"]
        assert entry["author"] == "Andrew Lang"


def test_index_excludes_olive_fairy_book_page_anchors():
    # Olive Fairy Book (id 27826) uses a different, page-number anchor
    # scheme that isn't compatible with get_story_paragraphs() yet - see
    # README "Language support" / scripts/build_lang_index.py
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    assert not any("27826" in entry["url"] for entry in data.values())


def test_cinderella_is_present():
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    assert "Cinderella, Or The Little Glass Slipper" in data
    entry = data["Cinderella, Or The Little Glass Slipper"]
    assert entry["book"] == "Blue Fairy Book"
