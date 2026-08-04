# Genre calibration

The audits in SKILL.md do not apply with equal force everywhere. Calibrate before rewriting.

**Short-text rule:** under roughly 400 words, concentrate on audits B (claim explicitness), D (specificity), G (emotion mode), and K (shape convergence). Structural moves like tangents and delayed reveals need room to work.

## Your writer has more than one register

This is the most important idea in this file, and it is the one most often skipped.

"Write in the founder's voice" implies there is one voice. Measure any real writer across channels and there is not. The same person writing a sales email, a blog post, and a Slack message to their team produces three distinguishable registers, and **two of those three can both be external and still differ sharply**. Carrying the warm first-person email register into published content is as wrong as carrying the impersonal content register into an email.

So do not build one profile. Build a table, one column per register, and measure each from real samples of that register alone.

A worked example of the shape, using invented values. **Do not copy these numbers.** Measure your own:

| | Instructional | Cold-outreach email | Marketing content |
|---|---|---|---|
| **Where** | internal chat, briefs | client sales email | blog and site |
| **Median length** | very short, often fragments | short paragraphs | longer, varied sentences |
| **First person** | heavy | expected, natural | usually sparse |
| **Second person** | rare | present | usually dominant |
| **Hedging** | near zero | often deliberate | low |
| **Terminal punctuation** | frequently absent | normal | normal |
| **Tone** | directive | warm, low-pressure | calm, explanatory |

The pattern that generalizes is the *structure* of the difference: internal writing compresses, outreach writing hedges on purpose, published content removes the author. The magnitudes are writer-specific.

**Tag work with its genre at assignment.** If a genre arrives untagged or is new, flag it and agree the calibration before drafting, not after. A draft written to the wrong register fails an audit that cannot tell you which register it should have been.

## Marketing content (blog, explainers, site body copy)

Usually the genre with the most available ground truth, because it is the one that gets published.

- **Second person tends to dominate.** Write to the reader, not about the company, even in company marketing.
- **Remove yourself.** First person is typically near-absent. No founder voice unless the piece is explicitly that.
- **Defend sentence variance.** Even cadence is the machine tell. Whatever your writer's mean is, the standard deviation around it is the number to protect.
- **Low hedging.** State things.
- **Calm.** Exclamation marks are rare in most published business prose.
- **Do not simplify your writer.** If they use semicolons and parentheses, those are in-voice. A scanner that prefers short declaratives will happily flatten a competent writer.
- Audit B targets re-moralizing only. An explainer is supposed to explain. The tell is a takeaway restated at every section close.
- Skip: nonlinear structure, ambivalent closes.

## Cold-outreach email

- **Open with standing, keep the warmth.** A concrete credential (a named town, a mutual contact, a remembered conversation) is what makes a warm opener land. Generic warmth alone is the tell. Warmth plus standing is not.
- **Keep the softeners.** "No obligation at all", "totally fine", "I'd love to". These lower pressure in cold outreach and are usually deliberate. An editor cutting them for concision is removing the thing that makes the email sendable.
- **Flowing first-person verb chains**, not clipped fragments. "I got the domain, pulled photos from your page, wrote the copy, and launched the site."
- **Accurate self-description.** Neither inflated nor self-deprecating. Both read as performance.
- **One ask, in the first three lines.** Reach the number and state it plainly.
- **Give an easy out, generously worded**, once.
- The PS is a natural oblique-tangent slot, not a second call to action.
- Skip: nonlinear structure. Email scanning punishes it.

## Landing pages and site copy

**This calibration is original to this stack and unvalidated.** Neither of the reference sources behind this method covers the genre. Treat it as provisional and revise it against your own delivered work.

- One action, visible without scrolling, repeated at the close.
- Explicitness is correct here. Audit B targets re-moralizing only, not the plain statement of the offer.
- Named specifics (real prices, real timelines, real service names) are the cheapest credibility available.
- Skip nonlinear structure entirely.
- **Client copy rules outrank general style.** If a client has a house rule, it wins over anything in this file.

## Client rules: where they live, and why not in the scanner

**Bans are regex-shaped. Positive rules are judgment-shaped.** Route them accordingly.

A ban ("never use this hashtag", "capitalize this place name") has a finite surface a scanner can match, and encoding it is cheap and safe. A positive rule ("include specific quantities", "speak in the owner's first person") is a claim about what *should* be present, and testing for absence is noisy in a way that degrades the instrument. Forcing those into `copy_scan.py` raises its false-positive rate until people stop reading its output, and **a scanner nobody trusts is worse than no scanner**: the noise is ignored wholesale, so the one real hit goes with it.

So positive rules live in a reference file like this one, and the judgment pass owns them. That is deliberate, not an oversight, and it should be stated wherever the rules are written down so the next person does not "fix" it.

Keep a per-client section here. The shape that works:

```
### <client>

Judgment-pass rules (NOT scanner-enforced):
1. Voice owner and person. Who speaks, and as "I" or "we"?
   Note this explicitly. The voice owner is often NOT the person
   who commissioned the work, and calibrating a client's copy on
   your own writer's profile is a common and invisible error.
2. Required specifics. Crew size, years in business, service radius,
   equipment count. Absence is the failure. This is audit D with a
   client-specific expectation.
3. Naming conventions. When a category appears, is it named
   specifically or generically?

Scanner-enforced (listed here for completeness, encoded in copy_scan.py):
- <the ban-shaped ones>
```

### Coverage limit, state it plainly

A list like this covers rules that are **written down**. A rule that exists only in a past conversation is unenforced and invisible to both the scanner and this file. When a new client rule surfaces, write it here first and decide second whether it is ban-shaped enough to also encode.

Also worth writing down: a rule that *is* encoded can still be missed if the regex knows one phrasing and the copy uses another. The judgment pass should confirm that a scanner-enforced concept has not crept back in a form the pattern does not recognize. That exact gap produces live compliance misses.

## Social posts

**Original calibration, unvalidated.** No ground truth behind it.

- The first line must survive being read alone, because it often is.
- Insight stated at most once, and roughly a third of posts should not state it at all.
- Rotate skeletons. Never the same shape twice running.
- Named specifics are the cheapest human marker at this length.
- Skip fourth-wall moves beyond one light touch. At this length it reads as a gimmick.

## Everything, always

- **Audit K (shape convergence) applies to every genre.** Check the skeleton against the last two or three pieces in the same channel before publishing.
- **Never deploy the full intervention menu in one piece.** One or two moves, chosen deliberately, varied across pieces.
- **House punctuation policy survives any voice sample.** If you have banned a character, a sample containing it is not a reason to unban it. See `../../humanizer/references/copy-tells.md`.
