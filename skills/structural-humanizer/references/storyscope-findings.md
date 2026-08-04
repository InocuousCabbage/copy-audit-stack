# Storyscope findings, distilled for marketing copy

Source: `jenna-russell/storyscope` (Russell et al., 2026, University of Maryland and Google DeepMind). Verified against `data/taxonomy.json`: **304 features across 10 dimensions**, counts confirmed from `taxonomy_metadata`.

## Read this before using any number below

**Storyscope measures narrative fiction. This stack's scope is marketing and business copy.** Its reported ~93% F1 for human-versus-AI classification is a result about *stories*, not about landing pages.

Every rate here is **directional guidance**, not evidence about our genre. Do not cite these percentages as validating your output, and do not quote them to a client. The mechanism (AI converges structurally, humans disperse) is what transfers. The specific numbers do not.

## The finding that actually matters

**Convergence.** All five AI models tested occupy one tight region of structural space, while human writing is dispersed and irregular.

**Rarity is the human signal.** This has a direct operational consequence: applying every de-AI intervention at once does not make writing human, it just relocates it to a new tight cluster. Pick 1 or 2 interventions per piece and vary them across pieces.

**Aspect-based checking beat one combined pass, 95% versus 68%,** in the study's own pipeline. This is why the audits in SKILL.md run one at a time. Merging them to save effort discards the single largest methodological gain available.

## The 10 dimensions, ranked by transfer to marketing copy

| Dimension | Features | Transfer |
|---|---|---|
| **style** | 39 | **High.** Sentence length bands, clause-combining, parenthetical frequency, register consistency, information density. Directly measurable in copy. |
| **revelation** | 25 | **High.** Information disclosure and withholding maps onto lede placement and delayed-reveal structure. |
| **situatedness** | 25 | **Medium-high.** Concrete grounding in real, named, checkable specifics. This is the evidence-versus-adjectives audit. |
| **perspective** | 17 | **Medium.** Maps to first-person versus second-person choice, which is genre-critical. |
| **temporal_structure** | 24 | **Medium.** Linear versus nonlinear. Mostly relevant to blog and case study. |
| **plot** | 28 | **Low-medium.** Arc and resolution. Applies to case studies and founder stories only. |
| **events** | 26 | **Low.** Escalation and intensity. Narrative-native. |
| **agents** | 54 | **Low.** Character construction. Largely inapplicable. |
| **social_networks** | 39 | **Low.** Inter-character relations. Inapplicable. |
| **setting** | 27 | **Low.** Physical world-building. Inapplicable. |

Roughly 106 of 304 features (style, revelation, situatedness) carry real weight for business copy. The remaining 198 are narrative machinery. **This is why this stack's audits are not a port of storyscope.** Most of the taxonomy does not apply.

## Style features worth borrowing directly

From the `style` dimension, the ones that are measurable in business copy:

- `STY_CPX_002` Predominant sentence length band
- `STY_CPX_010` Mean sentence length category
- `STY_CPX_012` Sentence-structure repertoire (multi-select: is there variety, or one shape repeated)
- `STY_CPX_004` Parataxis versus hypotaxis preference
- `STY_CPX_013` Parenthetical aside frequency
- `STY_CPX_003` Use of sentence fragments
- `STY_ALL_015` Lexical register and consistency
- `STY_ALL_019` Jargon and technical terminology usage
- `STY_TON_029` Information density per sentence
- `STY_TON_020` Evaluative stance intensity
- `STY_FIG_009` Concrete versus abstract lexis balance

`STY_CPX_012` (repertoire) and `STY_CPX_010` (mean length) together capture the strongest machine tell available here: **even, unvaried mid-length cadence.**

## Turning this into numbers you can scan against

The features above are qualitative categories. `scripts/structural_scan.py` needs numeric baselines, and those have to come from your own writer, not from the study and not from this repo.

Measure these on a corpus of at least 5,000 published words from a single register:

| Feature analogue | What to record | Machine default, for contrast |
|---|---|---|
| Mean sentence length | words per sentence, mean | tends to a narrow mid band |
| Sentence length stdev | words per sentence, stdev | notably lower, evenness is the tell |
| Short sentences | % under 8 words | often lower |
| Long sentences | % over 30 words | often lower |
| Parenthetical asides | count per corpus | typically fewer |
| First person | count per corpus | varies |
| Second vs first person plural | you/your vs we/our | varies |
| Exclamations | count per corpus | varies |

**The standard deviation is the number to defend, not the mean.** Variance is the human signal. Copy that lands every sentence within a few words of the mean has failed even when no individual sentence is wrong. A writer whose mean is 22 and stdev is 11 is a different writer from one whose mean is 22 and stdev is 4, and only the first one sounds like a person.

Procedure and file format: repo README, "Calibrate it to your own writer", plus `baselines.example.json`.

## The Claude fingerprint

The study found Claude's structural signature the most distinctive of the models tested:

- **Flat event escalation.** Uniform intensity throughout. Vary stakes and energy across the piece.
- **The epilogue habit.** A wrap-up coda after the natural ending. Cut it and stop earlier.
- **Reverent, quiet endings.** Sometimes end on the spike or leave it unresolved.

If your drafting model and your auditing model are the same model, it carries this signature by default and will not catch it by reading more carefully. Two passes by the same model compound the fingerprint rather than cancelling it. Check for these three on your own output first, not last.
