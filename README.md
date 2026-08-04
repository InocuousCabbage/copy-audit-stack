# copy-audit-stack

Two-pass editing stack for external-facing copy. Pass 1 removes AI tells at the word level. Pass 2 audits whether the piece actually works: what it claims, what order it says things in, whether every paragraph earns its place, and what it asks the reader to do. Both passes ship with a deterministic scanner for the slice a regex can see, and both are explicit that the scanner is the floor and not the gate.

Built for Claude Code skills, but the two SKILL.md files are plain Markdown and the scanners are dependency-free Python 3. Nothing here needs an agent to be useful.

## Why two passes

Word-level tells decay. Models drop "delve" and "tapestry" as they update, and light fine-tuning collapses stylistic detection quickly. What persists is structure, because structure comes from how a model organizes thought rather than which adjectives it reaches for.

The empirical backing is `jenna-russell/storyscope` (Russell et al., 2026), which built a 304-feature taxonomy of narrative structure and found that five different AI models occupy one tight region of that space while human writing is dispersed across it. **Rarity is the human signal.**

Two consequences run through everything here.

The first is methodological. In storyscope's own pipeline, checking one aspect at a time found 95% of issues where a single combined pass found 68%. So the audits in pass 2 run separately, one at a time, against an extracted skeleton. Merging them to save effort throws away the largest single gain available.

The second is a trap. If you fix AI writing by applying every de-AI intervention at once, every piece now opens mid-scene, names its feeling plainly, and ends unresolved. That is not human writing. That is a new tight cluster wearing different clothes. Pick one or two interventions per piece, vary them across pieces, and be able to say why this piece got this shape.

Storyscope measures narrative fiction. Its percentages are directional guidance for business copy, not evidence about it. They are quoted here as reasons to work this way, not as claims about what this stack achieves.

## Install and use

```bash
git clone https://github.com/<you>/copy-audit-stack.git
cd copy-audit-stack
```

For Claude Code, copy the two skill directories into your project or user skills path:

```bash
cp -r skills/humanizer skills/structural-humanizer ~/.claude/skills/
```

The scanners run standalone on Python 3.8 or later, no dependencies:

```bash
# pass 1: word-level tells
python3 scripts/copy_scan.py --strict draft.md

# pass 2: the measurable slice of structure
python3 skills/structural-humanizer/scripts/structural_scan.py \
  --baselines baselines.json --strict draft.md
```

Copy generated in application source (email subjects, transactional bodies, meta tags, aria labels) never appears on a page you can fetch, so it silently escapes a URL-based audit. Pull it out first:

```bash
python3 scripts/extract_copy_strings.py src/ -o /tmp/copy.txt
python3 scripts/copy_scan.py /tmp/copy.txt
```

Both scanners have a `--self-test` that runs them against known-bad input and confirms they fire. Run it after editing either one. An instrument that cannot distinguish pass from fail is not a check.

The full order of operations, including why pass 1 runs before pass 2 and why you re-run pass 1 afterward, is in [docs/PIPELINE.md](docs/PIPELINE.md).

## Calibrate it to your own writer

**This is the step that makes the stack usable, and skipping it is the most likely way to get bad results from it.**

`structural_scan.py` compares a draft against numeric baselines: mean sentence length, sentence-length standard deviation, the proportion of short and long sentences, and the balance of second person against first. The values it ships with are **placeholders that describe no real writer**, and the scanner says so in its output until you replace them. Numbers borrowed from someone else's corpus will fire on writing that is perfectly good, and a scanner that fires on good writing gets ignored, which is worse than not running one.

The procedure:

1. **Gather at least 5,000 words your target writer actually published.** Published, not drafted, and not edited by someone else afterward.
2. **Separate by register before you measure.** Sales email and published content are different registers from the same person, and averaging them gives you a profile that matches neither. Keep one baselines file per register.
3. **Measure.** Mean and standard deviation of words per sentence; percentage under 8 words and over 30; raw counts of `you/your`, `we/our`, first-person singular, and exclamation marks, along with the corpus word count those counts are per.
4. **Write it to `baselines.json`.** Copy `baselines.example.json` and replace every value.
5. **Run the scanner over the corpus you just measured.** This is a negative control. Your writer's own published work should come back quiet. If it lights up, your thresholds are wrong, not their writing.

The standard deviation is the number to defend, not the mean. A writer at mean 22 with a standard deviation of 11 and a writer at mean 22 with a standard deviation of 4 are different writers, and only the first one sounds like a person.

Two thresholds in the scanner are not baselines and stay put unless you have a reason: `STDEV_FLOOR` (below which cadence reads as machine-even) and `STDEV_CEILING` (above which the input is not prose at all but tables and spec lists parsing as enormous sentences). Both were derived from long-form business prose. Re-derive them if your genre has a very different natural rhythm.

For the qualitative half, build a register table for your writer following `skills/structural-humanizer/references/genre-calibration.md`, and keep client-specific rules there rather than in the scanner. Bans are regex-shaped and belong in `copy_scan.py`. Positive rules ("include specific quantities", "the owner speaks in first person") are judgment-shaped, and forcing them into a pattern matcher raises its false-positive rate until nobody reads its output.

## What is whose

| Component | Source | Status |
|---|---|---|
| Pass 1 skill, 33 AI-writing patterns | [blader/humanizer](https://github.com/blader/humanizer) v2.9.1, MIT, Copyright (c) 2025 Siqi Chen | **Vendored verbatim**, license retained |
| Two-pass architecture, skeleton-first method, aspect-by-aspect passes, convergence trap, intervention menu, model fingerprints | [NulightJens/humanizer-stack](https://github.com/NulightJens/humanizer-stack) by Jens Klose, MIT | **Referenced, not vendored** |
| Empirical base: 304 features, 10 dimensions, the convergence finding, the 95-vs-68 result | [jenna-russell/storyscope](https://github.com/jenna-russell/storyscope), Russell et al. 2026, University of Maryland and Google DeepMind | **Cited** |
| Marketing-native audits A, C, E, F, I, J; both scanners; the calibration interface; the genre and register model | This repo | **Original**, MIT |

Audits B, D, G, H, and K are Jens's, translated out of narrative terms into business copy. Jens recommends building your own stack rather than adopting his, which is what this is, and which is also what we would tell you to do with this one. Full detail in [ATTRIBUTION.md](ATTRIBUTION.md).

## Honest limitations

- **Pass 2 is draft quality.** It has been run on real client work, not on a benchmark, and its audit set has not been validated against a held-out corpus.
- **The landing-page and social calibrations are unvalidated.** Neither reference source covers those genres, so that guidance is reasoned rather than measured, and it is labeled as such in the file.
- **Storyscope's percentages are measured on narrative fiction.** Not marketing copy. They are directional here. Do not quote them as evidence about business writing, including to a client.
- **The shipped baselines are placeholders.** They describe nobody. Until you calibrate, half the pass-2 scanner output is noise, and the scanner will tell you so on every run.
- **A clean scan is not a pass.** This is the one to take seriously. During this stack's own development, copy came back fully green from both scanners twice and was non-compliant with a documented rule both times. The judgment pass caught it, and nothing in either scanner would have. Green means nothing mechanical is left to find. It does not mean the piece is ready.
- **Both scanners had real bugs that only their self-tests caught**, including a fixture so unlike real machine-uniform prose that the check passed vacuously. That is why the self-tests are in the repo rather than in a test directory nobody runs.

## License

MIT. See [LICENSE](LICENSE). The vendored `skills/humanizer/` carries its own MIT license and copyright notice, retained per its terms.
