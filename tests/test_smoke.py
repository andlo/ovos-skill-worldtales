"""Smoke tests: the skill module must import cleanly."""
from conftest import WorldTales, StoryFetchError


def test_imports_cleanly():
    assert WorldTales is not None
    assert issubclass(StoryFetchError, Exception)


def test_worldtales_is_an_ovos_skill():
    from ovos_workshop.skills import OVOSSkill
    assert issubclass(WorldTales, OVOSSkill)
