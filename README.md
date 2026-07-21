# World Tales
Classic fairy tales and folklore from around the world, read aloud by OVOS.

[![Tests](https://github.com/andlo/ovos-skill-worldtales/actions/workflows/test.yml/badge.svg)](https://github.com/andlo/ovos-skill-worldtales/actions/workflows/test.yml)
[![PyPI version](https://img.shields.io/pypi/v/ovos-skill-worldtales.svg)](https://pypi.org/project/ovos-skill-worldtales/)

## Install
```bash
pip install ovos-skill-worldtales
```

## About
This skill tells classic fairy tales, folk tales and fables collected from
storytellers around the world - starting with **Andrew Lang's twelve
"Coloured" Fairy Books** (389 stories drawn from French, German, Norse,
Russian, Arabic, Japanese and many other traditions), sourced from
[Project Gutenberg](https://www.gutenberg.org/), the public-domain digital
library.

This is a companion to
[`ovos-skill-fairytales`](https://github.com/andlo/ovos-skill-fairytales)
(H.C. Andersen and the Brothers Grimm) rather than a replacement for it -
`ovos-skill-worldtales` covers everything *outside* those two authors.

## Language support

Currently **English only**. The story index for other languages is a much
bigger undertaking than for `ovos-skill-fairytales` - Project Gutenberg
simply doesn't have a single curated multi-language fairy tale collection
the way andersenstories.com/grimmstories.com do. See
[#1](https://github.com/andlo/ovos-skill-worldtales/issues/1) for the plan
to add German, French, Dutch, Portuguese and Italian, each backed by real
original-language source books already confirmed to exist on Gutenberg
(e.g. original German Grimm, original French Perrault) rather than machine
translation.

## How it works

Unlike `ovos-skill-fairytales`, the story **index** here is bundled with
the skill (`locale/<lang>/index.json`, built by
`scripts/build_lang_index.py`) - no internet is needed to browse or pick a
story. Only the actual story **text** is fetched from Project Gutenberg,
on demand, the first time you ask for a given story - and then cached for
the rest of the session, including for "continue".

Per [Project Gutenberg's robot access policy](https://www.gutenberg.org/policy/robot_access.html),
this skill does not scrape gutenberg.org's website repeatedly - the index
is built once (offline, via the script above) rather than at request time,
and runtime fetches are limited to the specific book file a requested story
lives in.

## Examples
* "Tell me a story about the twelve dancing princesses"
* "Read me a fairy tale"
* "Continue the story"

OVOS will then try to find the story if you told it which one you wanted.
If not, it will ask you.

## Credits
Andreas Lorensen (@andlo)

Stories collected by Andrew Lang, sourced from
[Project Gutenberg](https://www.gutenberg.org/ebooks/30580) (public domain).

## Category
**Entertainment**

## Tags
#stories
#story
#tales
#fairy
#fairytale
#fairytales
#folklore
#gutenberg
#andrewlang
