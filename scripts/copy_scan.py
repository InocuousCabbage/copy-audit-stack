#!/usr/bin/env python3
"""
copy_scan.py: deterministic scanner for pass-1 copy tells.

Catches only the pattern-matchable slice of the humanizer skill: punctuation,
hype vocabulary, fixed constructions. Everything requiring judgment stays with
the skill itself. A clean scan does NOT mean the copy passed pass 1.

Complements skills/humanizer/ and its references/copy-tells.md.

SCOPE: run this on EXTERNAL-FACING COPY. Running it on the stack's own
documentation will fire on the example lists that enumerate banned phrases.
Those are mentions, not uses, and the hits are expected. Do not "fix" them by
re-broadening the skip heuristic: an earlier version skipped any line containing
"never", which silently suppressed 1,479 words of live site copy hiding 4 real
em-dash violations. Noise on your own docs is a far cheaper failure than silence
on a client deliverable.

HOUSE RULES: the em dash and en dash rules below encode one house style. If
yours differs, change the severity rather than deleting the rule, so the
decision stays visible in the diff. Client-specific rules do NOT belong here
unless they are ban-shaped; see skills/structural-humanizer/references/
genre-calibration.md for why positive rules stay in the judgment pass.

Usage:
    python3 scripts/copy_scan.py FILE [FILE...]
    python3 scripts/copy_scan.py --strict content/*.md    # exit 1 on any hit
    python3 scripts/copy_scan.py --self-test              # verify the scanner works
"""

import argparse
import re
import sys

# (id, severity, compiled pattern, human explanation)
RULES = [
    ("EM-DASH",     "error", re.compile(r"—"),
     "Em dash. Banned by house style. Replace with a period, comma, or colon."),
    ("DOUBLE-HYPH", "error", re.compile(r"\s--\s"),
     "Double hyphen doing em-dash duty. Same ban."),
    ("EN-DASH",     "warn",  re.compile(r"–"),
     "En dash. Correct in numeric ranges (1-12, $1M-$50M), a tell when it is a "
     "spaced parenthetical aside doing em-dash duty. Check which one this is."),
    ("HYPE-ADJ",    "warn",  re.compile(r"(?i)\b(seamless|robust|cutting-edge|best-in-class|world-class|"
                                        r"industry-leading|unparalleled|premier|top-notch|unmatched|"
                                        r"state-of-the-art|bespoke|elevate your)\b"),
     "Hype adjective. Replace with the specific that earned it, or cut."),
    ("SERVICE-CLICHE", "warn", re.compile(r"(?i)(full-service|one-stop shop|satisfaction guaranteed|"
                                          r"attention to detail|we pride ourselves|dedicated team|"
                                          r"peace of mind|go(ing)? above and beyond|customer-focused)"),
     "Service-business cliche. Could be pasted onto any competitor's site."),
    ("AI-VOCAB",    "warn",  re.compile(r"(?i)\b(delve|tapestry|testament|pivotal|showcase|underscore[sd]?|"
                                        r"vibrant|intricate|interplay|garner|foster(ing)?|"
                                        r"landscape of|realm of)\b"),
     "High-frequency AI vocabulary."),
    ("ANTITHESIS",  "error", re.compile(r"(?i)(it'?s not just\b|not only\b[^.]{0,60}\bbut also\b|"
                                        r"we don'?t just\b|isn'?t just about\b)"),
     "Negative parallelism / antithesis. Endemic in agency copy."),
    ("SIGNPOST",    "error", re.compile(r"(?i)(let'?s dive in|let'?s explore|let'?s break (this|it) down|"
                                        r"here'?s what you need to know|without further ado|"
                                        r"in this article,? we)"),
     "Signposting. Announces the writing instead of doing it."),
    ("SYCOPHANT",   "warn",  re.compile(r"(?i)(hope this (email )?finds you well|i hope you'?re doing well|"
                                        r"great question|absolutely right|happy to help!)"),
     "Sycophantic or generic-warm filler. Warmth needs concrete standing beside it."),
    # Scarcity framing is a FAMILY of phrasings, not a phrase, and encoding one
    # member of the family produces a false negative that reads as a pass. A rule
    # written against a single remembered wording will return 0 hits while the
    # copy says the same thing three other ways. Match the ROOT of the concept.
    # This is the general failure: a prose rule is a concept, a regex rule is one
    # phrasing, and the gap between them is silent. Test any new rule against
    # real copy you know is dirty, not against the example that inspired it.
    ("FAKE-URGENCY", "error", re.compile(r"(?i)(limited spots|act now|don'?t miss out|while supplies last|"
                                         r"only \d+ (spots|seats) left|limited time only|"
                                         r"founding (member|client|customer|spot|rate|price|partner)s?|"
                                         r"\b\d+ (more )?(spaces?|spots?) (available|left|remaining)|"
                                         r"rates? (will )?increase|spots? (are )?filling)"),
     "Fake urgency/scarcity. If a launch offer was retired, this is how it creeps back."),
    ("PRICE-ANCHOR", "error", re.compile(r"(?i)(was \$[\d,]+.{0,15}now \$[\d,]+|\$[\d,]+\s*→\s*\$[\d,]+)"),
     "Was/now price anchoring."),
    ("EMOJI",       "warn",  re.compile(r"[\U0001F300-\U0001FAFF✀-➿☀-⛿]"),
     "Emoji. Not in external copy unless the client's brand voice uses them."),
    ("EXCLAM",      "warn",  re.compile(r"!"),
     "Exclamation mark. Rare in most published business prose; measure your "
     "writer's rate before deciding what counts as too many."),
]

# Lines where a term is discussed rather than used. Both the humanizer and
# structural-humanizer exempt these, so the scanner must too or it fires on its
# own documentation and gets ignored as noise.
SKIP_MAX_CHARS = 400        # past this a "line" is a content blob, not a doc line
SKIP_LINE = re.compile(r"(?i)^\s*(?:>|\||#{1,6}\s|<!--)|"
                       r"(?:banned|do not|never|tell:|avoid|e\.g\.|pattern|scanner|rule\b|example)")


def scan(path, skip_meta=True):
    hits = []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as exc:
        print(f"{path}: cannot read: {exc}", file=sys.stderr)
        return hits, 1

    in_fence = False
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # SKIP_LINE exists to avoid firing on documentation that DISCUSSES a tell
        # ("never use em dashes"). It assumes one line is roughly one sentence.
        # On input where a whole page is a single line (scraped site text), one
        # stray "never" anywhere suppressed 1,479 words of live copy containing
        # 4 real em-dash violations. Cap it: past SKIP_MAX_CHARS the line is a
        # content blob, not a doc line, so scan it regardless.
        if skip_meta and len(line) <= SKIP_MAX_CHARS and SKIP_LINE.search(line):
            continue
        for rid, sev, rx, why in RULES:
            for m in rx.finditer(line):
                hits.append((n, rid, sev, m.group(0)[:40].strip(), why))
    return hits, 0


SELF_TEST = """This is a seamless, world-class solution.
We don't just build websites, we build relationships.
Let's dive in! Limited spots available.
An em dash — right here.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any hit")
    ap.add_argument("--errors-only", action="store_true")
    ap.add_argument("--self-test", action="store_true",
                    help="run against known-bad text and confirm the scanner fires")
    args = ap.parse_args()

    if args.self_test:
        import tempfile, os
        fd, tmp = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w") as fh:
            fh.write(SELF_TEST)
        hits, _ = scan(tmp, skip_meta=False)
        os.unlink(tmp)
        found = {h[1] for h in hits}
        expect = {"HYPE-ADJ", "ANTITHESIS", "SIGNPOST", "FAKE-URGENCY", "EM-DASH", "EXCLAM"}
        missing = expect - found
        print(f"self-test: {len(hits)} hits, rules fired: {sorted(found)}")
        if missing:
            print(f"SELF-TEST FAILED, these rules did not fire: {sorted(missing)}")
            return 2
        print("self-test PASSED: scanner fires on known-bad input.")
        return 0

    if not args.files:
        ap.error("need files, or --self-test")

    total = 0
    for path in args.files:
        hits, err = scan(path)
        if err:
            continue
        if args.errors_only:
            hits = [h for h in hits if h[2] == "error"]
        if hits:
            print(f"\n{path}")
            for n, rid, sev, txt, why in hits:
                print(f"  {n:>5}: [{sev.upper():<5}] {rid:<14} {txt!r}")
                print(f"         {why}")
            total += len(hits)

    print(f"\n{total} hit(s) across {len(args.files)} file(s)")
    print("NOTE: a clean scan does not mean pass 1 passed. This catches only the")
    print("      pattern-matchable slice; judgment-level tells stay with the skill.")
    return 1 if (args.strict and total) else 0


if __name__ == "__main__":
    sys.exit(main())
