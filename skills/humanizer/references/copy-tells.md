# Copy tells (marketing and site-copy scope)

Companion to the vendored `humanizer` SKILL.md. That skill is written against Wikipedia's "Signs of AI writing" and is encyclopedic and narrative in emphasis. This file covers the tells that show up specifically in **marketing, site copy, and client email**.

Pass 1 owns everything here: words, phrasing, punctuation. Structure belongs to pass 2.

## Punctuation

**Em dash (—).** Ban it if your house style bans it. Whether you do is a policy call, not a fact about writing, and this stack is agnostic. What matters is that you decide once and then enforce it consistently, because a half-enforced ban is worse than none.

If you do ban it, note that the parent skill's Voice Calibration section says a user-provided writing sample outranks the em dash rule. **Decide explicitly whether that carve-out applies to you.** A sample drawn from dictation or from a word processor with smart punctuation on will be full of em dashes the writer never chose, so honoring the sample can reintroduce exactly what the policy exists to prevent. Record the decision in `PROVENANCE.md` so a future upstream sync does not silently flip it back.

**En dash (–): two different things wearing one character. Do not treat them as one rule.**

An em dash in prose is a stylistic tic. An en dash in `Days 1-12` or `$1M-$50M` is correct typography carrying meaning. A blanket find-and-replace destroys the second while fixing the first.

Split by function, not by character:

- **Numeric-range en dash** (`Days 1–12`, `$1M–$50M`, `9–5`): correct typography. **Preserve it.** Replacing it with a hyphen or a comma degrades the copy. This is never a tell.
- **Spaced parenthetical-aside en dash** (`word – clause`): this is doing **em-dash duty** and carries the same rhetorical move the em dash ban exists to stop. Treat it as an em dash and replace with a period, comma, or colon.

The function split is worth the extra rule because it settles a question that otherwise needs the author. "Are these en dashes intentional or is it Word autocorrect?" cannot be answered from the text. It also does not need to be: numeric ranges stay regardless of intent, spaced asides go regardless of intent.

Never introduce an en dash of either kind into copy that did not have one.

**Curly quotes and apostrophes:** not a tell on their own. Word, Google Docs, and macOS all autocorrect by default, so human-written source files are full of them.

**Exclamation marks:** rare in most business prose. Measure your own writer's rate before setting a threshold. See [calibration](#calibrate-before-you-enforce).

## Vocabulary

Hype adjectives that ask to be believed instead of giving a reason. Cut or replace with the specific that earned them:

> quality, professional, trusted, reliable, seamless, robust, cutting-edge, best-in-class, world-class, industry-leading, unparalleled, premier, top-notch, unmatched, comprehensive solution

Service-business flavor of the same problem:

> full-service, one-stop shop, satisfaction guaranteed, attention to detail, we pride ourselves, dedicated team, customer-focused, going above and beyond, peace of mind

The general AI vocabulary from the parent skill §7 still applies (delve, tapestry, testament, landscape, pivotal, showcase, underscore, vibrant, crucial, robust).

## Constructions

**Empty opener.** Any first sentence that could be pasted onto a competitor's site unchanged. "We are a full-service X company serving Y since Z" is the canonical failure. This is a pass-1 catch when it is phrasing and a pass-2 catch when the whole piece is ordered wrong.

**Antithesis / negative parallelism.** "It's not just X, it's Y." "We don't just build websites, we build relationships." Endemic in agency copy.

**Rule of three.** "Fast, affordable, and reliable." AI forces triads to sound comprehensive. Break the pattern or cut to the one that is true.

**Fake urgency and scarcity.** "Limited spots", "act now", "don't miss out", "only 3 seats left", "founding member pricing".

A note on how this one fails in practice. Scarcity framing tends to be a **family** of phrasings, not a phrase. If your product once ran a launch offer and later dropped it, the copy will keep resurfacing in variants the original rule never listed. Match the root, not one wording: `founding (member|client|customer|spot|rate|price|partner)s?` rather than `founding member`. A rule that matches one phrasing of a concept will report zero hits on the other five and read as a pass.

**Was/now price anchoring.** "Was $2,000, now $500". Usually banned alongside scarcity, and for the same reason.

**Sycophantic openers in email.** "Hope this finds you well", "Hope your season's going well." Generic warmth *alone* is the tell, not warmth itself. Warmth paired with concrete standing (a named place, a remembered conversation, a specific credential) is how real people open a cold email.

**Signposting.** "Let's dive in", "here's what you need to know", "without further ado".

**Filler intensifiers.** "very", "really", "truly", "extremely", "incredibly". This one is genre-sensitive. Softeners like "no obligation at all" and "totally fine" lower pressure in cold outreach and are often deliberate. Cut intensifiers in published content, respect them in outreach.

## Register-sensitive, do not over-apply

The same construction is right in one genre and wrong in another. Check the genre before cutting. The shape of the difference typically looks like this, though **the specific values are yours to measure, not ours to assert**:

| Construction | cold-email | marketing-content |
|---|---|---|
| First person "I" | expected | usually sparse |
| Softeners and hedges | often deliberate, keep | usually minimal |
| Second person "you" | present | usually dominant |
| Short sentences | fine | depends entirely on the writer |

See `../../structural-humanizer/references/genre-calibration.md` for how to build this table for your own writer.

## Calibrate before you enforce

Several rules above are only useful once you have a number to compare against. Exclamation rate, first-person density, and the you/we balance are all writer-specific, and a threshold copied from someone else's corpus is a threshold that will fire on correct writing.

The procedure is in the repo README under "Calibrate it to your own writer". In short: gather 5,000 or more words your target writer actually published, measure, and write the results to `baselines.json`. Until you do, treat every numeric threshold in this stack as a placeholder.

## What NOT to flag

Carried from the parent skill's detection guidance, all of it applies here:

- Polish and correct grammar. Clean prose is not evidence of a machine.
- Curly quotes alone.
- A single "however" or "additionally".
- Semicolons and parentheses. Plenty of competent writers use both freely. Do not simplify a writer into short declaratives because a scanner prefers them.
- Long sentences. Length variance is a human signal, not a defect.
- Watched phrases inside quotations, titles, or examples where the phrase is being discussed rather than used.

Look for **clusters**, never isolated hits.
