# The pipeline

Two passes, in order, plus a voice layer. They do different jobs and none substitutes for another.

```
draft
  |
  v
[ pass 1: humanizer ]              words, phrasing, punctuation, copy tells
  |                                scanner: scripts/copy_scan.py
  |                                reference: skills/humanizer/references/copy-tells.md
  v
[ pass 2: structural-humanizer ]   skeleton, claim, order, genre fit
  |                                scanner: skills/structural-humanizer/scripts/structural_scan.py
  |                                references: storyscope-findings.md, genre-calibration.md
  v
[ voice layer ]                    your writer's register for the target genre
  |                                reference: your own voice profile (see README)
  v
deliver
```

## Why this order

Pass 1 is cheap and mechanical. Running it first clears vocabulary noise so the structural audit reads the actual skeleton instead of tripping over adjectives.

Pass 2 rewrites at section level: moving material, cutting codas, deleting restatements. Doing that after a word-level pass means you are not polishing sentences you are about to delete.

The voice layer goes last because it is **additive**. Passes 1 and 2 remove signal that should not be there. The voice layer adds signal that should.

**Then re-run pass 1** on anything pass 2 rewrote. New prose reintroduces AI tells. Iterate until both are clean. That loop is the deliverable standard, not a single sweep.

## What each layer owns

| Layer | Owns | Does not own |
|---|---|---|
| `humanizer` | Vocabulary, punctuation, punctuation policy, hype adjectives, antithesis, rule of three, signposting, sycophancy | Structure, claim order, genre fit |
| `structural-humanizer` | Skeleton, claim clarity, evidence vs adjectives, information order, paragraph necessity, single next action, shape convergence | Word choice, punctuation |
| voice layer | Register per genre, your writer's measured habits, client copy rules | Anything the first two passes handle |

Keeping these separate matters. When one skill tries to do all three, it does the structural work badly, because structural work needs the skeleton extracted and audited on its own.

## Running pass 2 properly

**Audit the outline, not the prose.** Structural tells hide from prose-level reading, which is exactly why they survive pass 1.

1. Extract the skeleton: sections in order, where the claim is stated and how often, what the opening does, what resolves, named vs vague references, where the ask appears.
2. Run the audits **one at a time** against that skeleton. Aspect-based checking found 95% of issues versus 68% for a single combined pass. Merging them discards the largest available gain.
3. Choose 1 or 2 interventions. Genre-appropriate, different from last time.
4. Rewrite structurally.
5. Scan.
6. Check the trap: if the fix looks like yesterday's fix, vary it.

## The trap

AI models converge on one tight region of structural space; humans are dispersed. **Rarity is the human signal.**

So do not replace one default with another. If every piece now opens mid-scene and ends unresolved, that is a new detectable cluster wearing different clothes. Pick 1 or 2 interventions per piece, vary across pieces, and be able to say why this piece got this shape.

## Genre first

**There is no single voice for any writer.** Measure one and you will typically find at least three registers:

- **instructional** (to a team, in chat or briefs): terse, often unpunctuated, unhedged
- **cold-email**: warm, first-person, softeners deliberate and worth defending
- **marketing-content**: second-person dominant, sparse first person, low hedging, longer sentences

Registers 2 and 3 are both external and differ sharply, which is the part that catches people out. Confirm the genre before drafting. If work arrives untagged, ask rather than guessing.

See `skills/structural-humanizer/references/genre-calibration.md`.

## Scanners are a floor, not a gate

Both scanners support `--strict` (exit 1 on hits) so they can gate a pre-delivery check:

```bash
python3 scripts/copy_scan.py --strict draft.md \
  && python3 skills/structural-humanizer/scripts/structural_scan.py \
       --baselines baselines.json --strict draft.md
```

**A clean scan does not mean the piece passed.** They catch only the pattern-matchable slice. Everything requiring judgment stays with the skills.

This is not a disclaimer, it is the operating instruction. Two separate times in this stack's own development, copy that returned a fully green scan turned out to be non-compliant on a documented rule, and the judgment pass is what caught it. Treat a green scan as "nothing mechanical left to find", never as "ready to ship".

Both ship a `--self-test` that runs them against known-bad input and confirms they fire. Run it after editing either scanner. An instrument that cannot distinguish pass from fail is not a check, and both scanners had real bugs that only their self-tests caught.

Also validate against a **negative control**: run the scanner over a corpus of your writer's published work. It should come back quiet. If it lights up on writing you already shipped and were happy with, the thresholds are wrong, not the writing.

## Applies to external-facing copy only

Run this on site copy, landing pages, external email, marketing content, social, and blog posts.

Do not run it on internal messages or team chat. Applied to internal docs it fires constantly on text nobody needs to be human.
