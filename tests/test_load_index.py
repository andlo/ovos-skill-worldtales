"""Tests for _load_index()'s per-language fallback behaviour."""
import json


def test_load_index_uses_bundled_en_us(skill):
    index = skill._load_index()
    assert len(index) > 300
    assert "Cinderella, Or The Little Glass Slipper" in index


def test_load_index_falls_back_to_en_us_for_unsupported_language(skill, monkeypatch):
    monkeypatch.setattr(type(skill), "lang", "xx-xx", raising=False)
    index = skill._load_index()
    # xx-xx has no locale/xx-xx/index.json, so this should silently fall
    # back to the bundled English index rather than returning {}
    assert len(index) > 300
