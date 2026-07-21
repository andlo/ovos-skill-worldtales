# OVOS Skills Store submission

`ovos-skill-worldtales-andlo.json` in this folder is a pre-validated
submission file for https://github.com/OpenVoiceOS/OVOS-skills-store
(validated locally with their `scripts/apply_submission.py`).

**Icon**: currently reusing `story-512.png` from `ovos-skill-fairytales`
as a placeholder. TODO: swap the rainbow for a simple globe with
lines of longitude/latitude once there's time to make a proper variant.


**Not submitted yet** - the store requires the skill to be a finished,
installable release, and this skill isn't published to PyPI yet.

Once a release is tagged and published (see `.github/workflows/publish.yml`),
submit it the same way `ovos-skill-fairytales` was:

1. Fork https://github.com/OpenVoiceOS/OVOS-skills-store
2. Copy `ovos-skill-worldtales-andlo.json` into that fork's `raw_jsons/`
   directory (base branch: `master`, not `main` - `main` is stale)
3. Open a PR
