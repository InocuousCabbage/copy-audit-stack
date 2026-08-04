---
name: structural-humanizer
description: Pass 2 of the copy-audit stack. Audit whether external-facing copy actually does its job, at the skeleton level. Use after the humanizer pass on any site copy, landing page, external email, marketing content, social post, or blog post, before delivery.
metadata:
  version: "0.3.0"
---

# structural-humanizer (pass 2)

Pass 1 (`humanizer`) works at word and sentence level. It will hand back prose that reads naturally and is still structurally broken: opens with who we are instead of what the reader came for, buries the ask, restates one claim in five places, ends with a coda nobody needed.

Pass 1 makes it sound human. Pass 2 makes it work.

Run pass 2 AFTER pass 1. Then re-run pass 1 on anything you rewrote, because new prose reintroduces AI tells. Iterate until both are clean.

## Why structure matters more than vocabulary

Word-level tells decay. Models drop them as they update, and light fine-tuning collapses stylistic detection. Structural fingerprints are durable, because they come from how the model organizes thought, not which adjectives it reaches for.

The deeper finding: AI models converge on one tight region of structural space while human writing is dispersed. **Rarity is the human signal.** That has a direct consequence, below.

## The trap

Do not replace one default with another. If every piece now opens mid-scene, names its feeling plainly, and ends unresolved, that is just a new detectable cluster wearing different clothes.

**Pick 1 or 2 interventions per piece. Vary them across pieces. Be able to say why this piece got this shape.** Never run the whole menu at once.

## Method

**Audit the outline, not the prose.** Structural tells hide from prose-level reading, which is exactly why they survive pass 1.

1. **Extract the skeleton.** Write it out: sections in order, where the central claim is stated and how many times, what the opening actually does, what resolves, named vs vague references, where the ask appears, tangent count.
2. **Run the audits one at a time, against the skeleton.** Separate aspect-based passes found 95% of issues versus 68% for a single combined pass. Do not merge them to save time, that is the whole finding.
3. **Choose 1 or 2 interventions.** Genre-appropriate, different from the last piece.
4. **Rewrite structurally.** Move sections, cut codas, delete restatements. Do not just polish sentences, that is pass 1's job.
5. **Re-run pass 1** on the rewritten material.
6. **Check the trap.** If this fix looks like yesterday's fix, vary it.

## The audits

Run each separately. State PASS or FAIL, and on FAIL quote the specific line and say what to do. If you cannot quote a line, you do not have a finding.

### A. Job and claim
- What is this piece for, in one sentence? Two sentences means two jobs, so split it or cut one.
- State the central claim in under ten words. If you cannot, the piece has a topic, not a claim. Topics do not persuade.
- Is the claim argued, or just asserted more loudly in more places? Repetition is not evidence.

### B. Claim explicitness
The strongest single tell. AI states its lesson, then restates it: a takeaway line per section, every example dutifully interpreted, the thesis re-derived at each close.

**Fix:** state the point once, where it lands hardest. Cut every restatement. Let at least one example sit uninterpreted.

Note the genre exception: a landing page or a course lesson is *supposed* to be explicit. The tell is not that the point is stated, it is that it gets re-moralized at the end of every section.

### C. Opening
Does the first sentence speak to what the reader wants, or describe the writer? "We are a full-service landscaping company" fails.

**Hard fail:** any opening that could be swapped onto a competitor's page without changing a word.

### D. Evidence and reference specificity
Count load-bearing specifics (numbers, names, dates, prices, versions, quantities) against adjectives doing persuasive work ("quality", "professional", "trusted", "reliable").

Adjectives outnumbering specifics means the piece asks to be believed instead of giving a reason. Humans name real things; AI stays at vague allusion.

**Fix:** "a popular productivity book" becomes the actual title. "An expert" gets a name. "Recently" gets a date. Add the price, the model, the town.

**Never invent a specific to fill the gap.** If it does not exist, ask for it or write the plain version. A fabricated detail is a defect even when it improves the sentence.

### E. Information order
Is the most important thing first? Readers leave. Anything requiring three paragraphs of setup is lost. Check specifically whether the best fact in the piece is sitting in paragraph four.

### F. Every paragraph earns its place
Per paragraph: if I delete this, what does the reader lose? If the answer is nothing, or "flow", delete it. Paragraphs that only announce the next paragraph are the most common offenders.

### G. Emotion mode
Where the copy carries feeling (testimonials, founder story, case studies), check how. AI performs emotion through body and atmosphere ("chest tightened", "breath caught"). Humans more often just name it.

**Fix:** say it plainly ("honestly, that one stung"). Reserve embodied detail for the one moment that earns it. This inverts "show, don't tell" on purpose. That advice is now a machine signature.

### H. Reader acknowledgment
Marketing already overuses "you", so that is not the move. The transferable one is acknowledging the writing itself: "skip this if you already run ads", "you're probably skimming, so here's the number".

Use sparingly. It is a spice, and at short lengths it reads as a gimmick.

### I. Single next action
What should the reader do? Stated, singular, easy? Two competing calls to action means neither happens.

### J. So what
Walk each claim and ask "so what?" once. If the answer is not in the text, add it or cut the claim. Highest-yield check on marketing copy.

### K. Shape convergence
Does this piece have the same skeleton as the last two or three in the same channel? Same opener type, same arc, same closer? That is the cluster forming. Break it before publishing.

Applies to every genre, every time.

## Genre calibration

Audits do not apply with equal force everywhere. Under roughly 400 words, concentrate on B, D, G, and K.

**Assume your writer has more than one register, and that two of them can both be external and still differ sharply.** Confirm which one you are writing before drafting, not after.

Full breakdown, including how to build a register table for your own writer: [references/genre-calibration.md](references/genre-calibration.md)

## Intervention menu (rotate, never all at once)

- **Outcome first.** Open at the end state, then rewind.
- **Delayed reveal.** Withhold the number the piece is built on until two-thirds through.
- **Recontextualization callback.** Make an earlier detail mean something new.
- **The oblique tangent.** One paragraph that parallels the theme without serving it. Do not tie it back.
- **The open thread.** Name a question you cannot answer and leave it standing.
- **Genuine ambivalence.** End with both feelings intact.
- **The named thing.** Swap every vague allusion for a real, checkable specific.
- **Plain emotion.** Replace body-performance with the stated feeling.
- **Acknowledged reader.** One moment that admits someone is reading.
- **End hot.** Stop at the spike instead of the quiet coda.

## Know what drafted the text

Check the fingerprint of whichever model produced the draft. Claude's is the most distinctive of the major models, and since this skill is usually run by Claude on Claude output, it is the one to check first:

- **Flat event escalation.** Uniform intensity throughout. Fix by varying stakes across the piece.
- **The epilogue habit.** A wrap-up coda after the natural ending. Cut it and end earlier.
- **Reverent, quiet endings.** Occasionally end on the spike or unresolved instead.

If the same model both drafts and audits, it carries this fingerprint by default and will not find it by looking harder. Check for it explicitly and first, not last. Two passes by the same model compound the signature rather than cancelling it.

## House constraints

Fill these in for your own project. They override anything the source material or a voice sample suggests, and stating them here is what keeps a later contributor from quietly relaxing them:

- **Punctuation policy.** If you ban a character, say so here and note that the ban survives any voice sample. Pass 1's §14 bans em dashes, but its Voice Calibration says a writing sample outranks that ban. Decide explicitly which wins for you.
- **Emoji policy** in external copy.
- **Client-specific copy rules win** over general style. Check the client reference before writing.

## Output

1. The audited copy
2. Audit results, letter by letter, with quoted lines on each FAIL
3. Which 1 or 2 interventions were applied, and why this piece got that shape
4. What changed

If a FAIL needs a fact you do not have, say so and name what is missing. Do not paper over it.

## Provenance

Drafted from first principles (v0.1.0), then revised against two references (v0.2.0):

- **`NulightJens/humanizer-stack`** (Jens Klose, MIT). Source of the method: skeleton-first auditing, aspect-by-aspect passes, the convergence trap, the intervention menu, model fingerprints, and genre calibration. Jens explicitly recommends building your own rather than adopting his, which is what this is. Not vendored, referenced.
- **`jenna-russell/storyscope`** (Russell et al., 2026, University of Maryland and Google DeepMind). The empirical base underneath Jens's audits: 304 features across 10 dimensions of narrative structure, ~93% F1 human-vs-AI. `data/taxonomy.json` is the feature reference. Its trained model is a possible future post-check ("did I successfully humanize"), not part of this loop.

**Adaptation note.** Both references are tuned for narrative and story. This skill's scope is external-facing business copy. Audits A, C, E, F, I, and J are marketing-native and have no counterpart in Jens's six. Audits B, D, G, H, and K are his, translated out of narrative terms.

Neither reference has a landing-page or site-copy genre, so that calibration is original and unvalidated.

Storyscope's percentages are measured on *narrative fiction*, not marketing copy. They are directionally useful here, not evidence about this genre. Do not quote them as though they were.

## References and tooling

- [references/storyscope-findings.md](references/storyscope-findings.md): the empirical base, 304 features distilled to what transfers to marketing copy, plus the model fingerprint
- [references/genre-calibration.md](references/genre-calibration.md): which audits apply per genre, and how to build a register table
- [scripts/structural_scan.py](scripts/structural_scan.py): deterministic scanner for the measurable slice (cadence uniformity, takeaway markers, vague allusions, person balance)
- [../humanizer/references/copy-tells.md](../humanizer/references/copy-tells.md): pass-1 marketing tells
- [../../docs/PIPELINE.md](../../docs/PIPELINE.md): how the passes chain

Run the scanner after rewriting:

```bash
python3 skills/structural-humanizer/scripts/structural_scan.py \
  --baselines baselines.json --strict draft.md
```

A clean scan does not mean the piece passed. The scanner catches only what regex can see; the audits above are the actual work.
