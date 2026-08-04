# Attribution

This stack builds on three external sources. Recording what came from where, and what did not.

## blader/humanizer (vendored, MIT)

**Vendored verbatim** at `skills/humanizer/SKILL.md`.

- Repository: https://github.com/blader/humanizer
- Version 2.9.1, commit `523374d`
- License: MIT, Copyright (c) 2025 Siqi Chen
- `LICENSE` retained alongside the skill, per MIT terms
- Verified byte-identical to upstream at install (2026-08-03)

Provides pass 1: 33 numbered AI-writing patterns, based on Wikipedia's "Signs of AI writing" maintained by WikiProject AI Cleanup.

**One documented deviation point.** Upstream §14 bans em dashes, but its Voice Calibration section says a user-provided writing sample outranks that ban. Whether that carve-out applies is a house-style decision, and it is recorded in `skills/humanizer/PROVENANCE.md` so a future upstream sync does not silently change it. This is not a criticism of the upstream skill; it is a local policy that the upstream skill correctly leaves configurable.

## NulightJens/humanizer-stack (architectural inspiration, MIT)

**Not vendored. Referenced for architecture.**

- Repository: https://github.com/NulightJens/humanizer-stack
- Author: Jens Klose
- License: MIT

This repository's **layout and method** are mirrored here: the two-skill split, the `references/` and `scripts/` breakdown, deterministic scanners alongside each skill, and `docs/PIPELINE.md`.

Method borrowed:
- Skeleton-first auditing ("audit the outline, not the prose")
- Aspect-by-aspect passes rather than one combined pass
- The convergence trap, and 1-2 interventions per piece varied across pieces
- The intervention menu
- Model fingerprints, including the Claude signature
- Genre calibration as a separate reference file

**Audit content is original.** Jens's six audits are narrative-tuned. Audits A, C, E, F, I, and J here (job and claim, opening, information order, paragraph necessity, single next action, so-what) are marketing-native and have no counterpart in his set. Audits B, D, G, H, and K are his, translated out of narrative terms into business copy.

Jens explicitly recommends building your own stack rather than adopting his. That is what this is, and it is also what we recommend you do with this one.

## jenna-russell/storyscope (empirical reference)

**Not vendored. Cited as the evidence base.**

- Repository: https://github.com/jenna-russell/storyscope
- Russell et al., 2026, University of Maryland and Google DeepMind
- 304 features across 10 dimensions, verified against `data/taxonomy.json`

Distilled for business-copy scope in `skills/structural-humanizer/references/storyscope-findings.md`.

**Scope caveat, stated wherever the numbers appear:** storyscope measures narrative fiction. Its reported ~93% F1 is a result about stories, not marketing copy. The percentages are directional guidance here, not evidence about this genre, and must not be quoted as validating any output produced with this stack.

## Original to this repo

- All audit content listed above as marketing-native
- The landing-page, site-copy, and social genre calibrations (neither reference covers these; **unvalidated**)
- `scripts/copy_scan.py`, `scripts/extract_copy_strings.py`, and `skills/structural-humanizer/scripts/structural_scan.py`, including their self-tests, guards, and calibration interface
- The genre and register model, and the rule that positive client rules stay in the judgment pass while ban-shaped rules go to the scanner
