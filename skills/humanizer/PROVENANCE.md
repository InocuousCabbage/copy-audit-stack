# Provenance

Vendored from https://github.com/blader/humanizer
- Version: 2.9.1 (`metadata.version` in SKILL.md, matches `.claude-plugin/plugin.json`)
- Commit: 523374d "Improve skill packaging and portability (v2.9.1)"
- Retrieved: 2026-08-03
- License: MIT, Copyright (c) 2025 Siqi Chen (LICENSE retained alongside)

Pure-Markdown skill, no build step and no runtime code. The upstream repo's only
script (`scripts/validate-package.py`, 61 lines) is a packaging validator and was
scanned for network and exec calls before install; it has none and was not vendored.

Role in this stack: **pass 1**, line-level AI-tell removal (33 numbered patterns).
Pass 2 (structural audit) is original to this repo and is NOT covered by this skill.

## Local deviations, if any

Record here anything your project overrides in the vendored skill, so a future
upstream sync does not silently revert it.

The one most projects hit: upstream §14 hard-bans em dashes, but the upstream
Voice Calibration section says a user-provided writing sample OUTRANKS that ban.
Whether that carve-out applies is a house-style decision, and it has a real
failure mode in both directions:

- Honor the sample, and a corpus drawn from dictation or from a word processor
  with smart punctuation on will reintroduce em dashes the writer never chose.
- Ignore the sample, and you flatten a writer who genuinely uses them.

Decide once, write the decision here, and note that it survives any sample.

Also worth recording: this file is the seam where a vendored dependency meets a
local policy, and it is the only place a sync conflict will show up as text you
can read. Keep it accurate or the next sync is silent.
