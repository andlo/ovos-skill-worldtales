"""Shared pytest fixtures for the worldtales skill test suite.

Same approach as ovos-skill-fairytales' conftest: build a bare instance via
Tales.__new__() rather than going through OVOSSkill's normal __init__
(which needs a live messagebus connection).
"""
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_INIT_PATH = Path(__file__).resolve().parents[1] / "__init__.py"
_spec = importlib.util.spec_from_file_location("worldtales_skill", _INIT_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

WorldTales = _module.WorldTales
StoryFetchError = _module.StoryFetchError


@pytest.fixture
def skill(tmp_path, monkeypatch):
    s = WorldTales.__new__(WorldTales)
    s.log = MagicMock()
    s.skill_id = "ovos-skill-worldtales.test"
    s.status = MagicMock()
    s._bus = MagicMock()
    s._settings = {}
    monkeypatch.setattr(WorldTales, "lang", "en-us", raising=False)
    s.index = {}
    s._book_soup_cache = {}
    return s
