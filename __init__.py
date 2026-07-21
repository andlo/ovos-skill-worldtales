"""
skill OVOS World Tales
Copyright (C) 2026  Andreas Lorensen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from ovos_bus_client.message import Message
from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill
from ovos_utils.parse import match_one
from ovos_utils import classproperty
from ovos_utils.process_utils import RuntimeRequirements

import requests
from bs4 import BeautifulSoup
import json
import os


class StoryFetchError(Exception):
    """Raised when a story could not be fetched or parsed from
    Project Gutenberg."""


class WorldTales(OVOSSkill):

    @classproperty
    def runtime_requirements(self):
        # unlike ovos-skill-fairytales, the story INDEX here is bundled
        # with the skill package (see locale/<lang>/index.json) - browsing
        # and selecting a story needs no internet at all. Internet is only
        # needed when actually fetching a specific story's text from
        # Project Gutenberg, which is handled per-request with a graceful
        # 'story_unavailable' fallback (see handle_Tales/handle_continue),
        # so the skill never needs to be unloaded for connectivity reasons.
        return RuntimeRequirements(
            internet_before_load=False,
            network_before_load=False,
            requires_internet=False,
            requires_network=False,
            no_internet_fallback=True,
            no_network_fallback=True,
        )

    def initialize(self):
        self.is_reading = False
        self.settings.setdefault('progress', {})
        self.settings.setdefault('last_story', None)
        # in-memory cache of already-fetched Gutenberg book pages (BeautifulSoup),
        # keyed by URL - several stories share the same book file, and
        # 'continue' shouldn't need a fresh fetch either
        self._book_soup_cache = {}
        self.index = self._load_index()
        if not self.index:
            self.log.error("No bundled story index found for this language")

    def _index_path_for_lang(self, lang):
        return os.path.join(os.path.dirname(__file__), "locale", lang, "index.json")

    def _load_index(self):
        lang = self.lang
        path = self._index_path_for_lang(lang)
        if not os.path.isfile(path):
            # this language has no curated story index yet - fall back to
            # the English one rather than leaving the skill with nothing to
            # offer (see README for current per-language coverage)
            self.log.warning(f"no bundled index for '{lang}', falling back to en-us")
            path = self._index_path_for_lang("en-us")
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError) as e:
            self.log.error(f"could not read bundled story index {path}: {e}")
            return {}

    @intent_handler('Tales.intent')
    def handle_Tales(self, message: Message):
        if not self.index:
            self.speak_dialog('story_unavailable')
            return
        if message.data.get("tale", "") is None:
            response = self.get_response('Tales', num_retries=1)
            if not response:
                return
        else:
            response = message.data.get("tale")
        result = match_one(response, list(self.index.keys()))
        if result[1] < 0.8:
            self.speak_dialog('that_would_be', data={"story": result[0]})
            response = self.ask_yesno('is_it_that')
            if not response or response == 'no':
                self.speak_dialog('no_story')
                return
        title = result[0]
        self.speak_dialog('i_know_that', data={"story": title}, wait=True)
        self.settings['last_story'] = title
        try:
            self.tell_story(title, 0)
        except StoryFetchError as e:
            self.log.error(f"Could not fetch story: {e}")
            self.is_reading = False
            self.speak_dialog('story_unavailable')

    @intent_handler('continue.intent')
    def handle_continue(self, message: Message):
        title = self.settings.get('last_story')
        if title is None:
            self.speak_dialog('no_story_to_continue')
            return
        self.speak_dialog('continue', data={"story": title}, wait=True)
        start = self.settings.get('progress', {}).get(title, 0)
        try:
            self.tell_story(title, start)
        except StoryFetchError as e:
            self.log.error(f"Could not fetch story: {e}")
            self.is_reading = False
            self.speak_dialog('story_unavailable')

    def tell_story(self, story_title, bookmark):
        entry = self.index.get(story_title)
        if entry is None:
            raise StoryFetchError(f"unknown story: {story_title}")
        self.is_reading = True
        paragraphs = self.get_story_paragraphs(entry)
        self.speak_dialog('title_by_author', data={'title': story_title, 'book': entry.get('book', '')}, wait=True)
        self.log.info(entry["url"])
        for i, para in enumerate(paragraphs[bookmark:], start=bookmark):
            self.settings['progress'][story_title] = i + 1
            if self.is_reading is False:
                break
            for sentence in para.split('. '):
                if self.is_reading is False:
                    break
                self.speak_dialog(sentence, wait=True)
        if self.is_reading is True:
            self.is_reading = False
            self.settings['progress'].pop(story_title, None)
            if self.settings.get('last_story') == story_title:
                self.settings['last_story'] = None
            self.speak_dialog('from_Tales')

    def stop(self):
        self.log.info('stop is called')
        if self.is_reading is True:
            self.speak_dialog('stop_telling_tales')
            self.speak_dialog('from_Tales')
            self.is_reading = False
            return True
        else:
            return False

    def _get_book_soup(self, url):
        if url in self._book_soup_cache:
            return self._book_soup_cache[url]
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, "html.parser")
        except requests.RequestException as e:
            raise StoryFetchError(f"failed to fetch {url}: {e}") from e
        self._book_soup_cache[url] = soup
        return soup

    def get_story_paragraphs(self, entry):
        """Extract a single story's paragraphs from its Project Gutenberg
        book page, bounded by its own story anchor and the next one in the
        same file. Different Gutenberg transcriptions use either
        '<a id="link...">' (standalone, right before the <h2> title) or
        '<a name="link...">' (nested inside the <h2>) for these anchors -
        we match on either attribute."""
        soup = self._get_book_soup(entry["url"])
        anchor = entry["anchor"]
        anchor_tag = soup.find(id=anchor) or soup.find(attrs={"name": anchor})
        if anchor_tag is None:
            raise StoryFetchError(f"anchor {anchor} not found in {entry['url']}")
        paragraphs = []
        for el in anchor_tag.find_all_next():
            if el.name == "a" and (
                (el.get("id") or "").startswith("link") or (el.get("name") or "").startswith("link")
            ):
                break
            if el.name == "p":
                text = el.get_text(" ", strip=True)
                if text:
                    paragraphs.append(text)
        if not paragraphs:
            raise StoryFetchError(f"no story text found at {entry['url']}#{anchor}")
        return paragraphs

    def _index_path_for_lang(self, lang):
        return os.path.join(os.path.dirname(__file__), "locale", lang, "index.json")

    def _load_index(self):
        lang = self.lang
        path = self._index_path_for_lang(lang)
        if not os.path.isfile(path):
            # this language has no curated index yet - fall back to the
            # bundled English one rather than having an empty skill
            # (see README for current per-language coverage)
            self.log.info(f"No story index for '{lang}', falling back to en-us")
            path = self._index_path_for_lang("en-us")
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError) as e:
            self.log.error(f"Could not read bundled story index: {e}")
            return {}

    @intent_handler('Tales.intent')
    def handle_Tales(self, message: Message):
        if not self.index:
            self.speak_dialog('story_unavailable')
            return
        if message.data.get("tale", "") is None:
            response = self.get_response('Tales', num_retries=1)
            if not response:
                return
        else:
            response = message.data.get("tale")
        result = match_one(response, list(self.index.keys()))
        if result[1] < 0.8:
            self.speak_dialog('that_would_be', data={"story": result[0]})
            response = self.ask_yesno('is_it_that')
            if not response or response == 'no':
                self.speak_dialog('no_story')
                return
        self.speak_dialog('i_know_that', data={"story": result[0]}, wait=True)
        title = result[0]
        self.settings['last_story'] = title
        try:
            self.tell_story(title, 0)
        except StoryFetchError as e:
            self.log.error(f"Could not fetch story: {e}")
            self.is_reading = False
            self.speak_dialog('story_unavailable')

    @intent_handler('continue.intent')
    def handle_continue(self, message: Message):
        title = self.settings.get('last_story')
        if title is None:
            self.speak_dialog('no_story_to_continue')
            return
        self.speak_dialog('continue', data={"story": title}, wait=True)
        start = self.settings.get('progress', {}).get(title, 0)
        try:
            self.tell_story(title, start)
        except StoryFetchError as e:
            self.log.error(f"Could not fetch story: {e}")
            self.is_reading = False
            self.speak_dialog('story_unavailable')

    def tell_story(self, story_title, bookmark):
        entry = self.index.get(story_title)
        if entry is None:
            raise StoryFetchError(f"unknown story: {story_title}")
        self.is_reading = True
        paragraphs = self.get_story_paragraphs(entry)
        self.speak_dialog('title_by_author', data={'title': story_title, 'book': entry.get('book', '')}, wait=True)
        self.log.info(entry["url"])
        for i, para in enumerate(paragraphs[bookmark:], start=bookmark):
            self.settings['progress'][story_title] = i + 1
            if self.is_reading is False:
                break
            sentenses = para.split('. ')
            for sentens in sentenses:
                if self.is_reading is False:
                    sentens = ""
                    break
                else:
                    self.speak_dialog(sentens, wait=True)
        if self.is_reading is True:
            self.is_reading = False
            self.settings['progress'].pop(story_title, None)
            if self.settings.get('last_story') == story_title:
                self.settings['last_story'] = None
            self.speak_dialog('from_Tales')

    def stop(self):
        self.log.info('stop is called')
        if self.is_reading is True:
            self.speak_dialog('stop_telling_tales')
            self.speak_dialog('from_Tales')
            self.is_reading = False
            return True
        else:
            return False

    def _get_book_soup(self, url):
        if url in self._book_soup_cache:
            return self._book_soup_cache[url]
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, "html.parser")
        except requests.RequestException as e:
            raise StoryFetchError(f"failed to fetch {url}: {e}") from e
        self._book_soup_cache[url] = soup
        return soup

    def get_story_paragraphs(self, entry):
        """Extract one story's paragraphs from its Gutenberg book page.

        Each story starts at an <a id="link..."> anchor followed by an <h2>
        title and a run of <p> paragraphs, ending at the next such anchor
        (the next story in the same book file). See scripts/build_lang_index.py
        for how the anchors were harvested.
        """
        soup = self._get_book_soup(entry["url"])
        anchor_tag = soup.find(id=entry["anchor"])
        if anchor_tag is None:
            raise StoryFetchError(f"anchor {entry['anchor']} not found in {entry['url']}")
        paragraphs = []
        for el in anchor_tag.find_all_next():
            if el.name == "a" and (el.get("id") or "").startswith("link"):
                break
            if el.name == "p":
                text = el.get_text(" ", strip=True)
                if text:
                    paragraphs.append(text)
        if not paragraphs:
            raise StoryFetchError(f"no story text found at {entry['url']}#{entry['anchor']}")
        return paragraphs
