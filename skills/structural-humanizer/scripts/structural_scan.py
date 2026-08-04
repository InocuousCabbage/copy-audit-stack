#!/usr/bin/env python3
"""
structural_scan.py: deterministic scanner for pass-2 structural tells.

Pass 2 is mostly judgment work on an extracted skeleton, and no script replaces
that. This catches the measurable slice: sentence-length uniformity, takeaway
restatement, vague-allusion density, embodied-emotion cliches, and first/second
person balance.

A clean scan does NOT mean the piece passed pass 2. Cadence evenness is the one
finding here that is genuinely hard to see by eye, which is the main reason this
script is worth running.

CALIBRATION IS REQUIRED. The baselines below are PLACEHOLDERS, not defaults you
should trust. They describe no real writer. Measure your own target writer and
pass the result with --baselines, or the cadence and person-balance comparisons
are meaningless. See the repo README, "Calibrate it to your own writer".

Usage:
    python3 structural_scan.py FILE [FILE...]
    python3 structural_scan.py --baselines baselines.json FILE
    python3 structural_scan.py --strict FILE
    python3 structural_scan.py --self-test
"""

import argparse
import json
import re
import statistics as st
import sys

# PLACEHOLDER baselines. Round invented numbers, deliberately not measured from
# anyone, so that shipping without calibrating is visible rather than silently
# wrong. Replace via --baselines.
BASE = {
    "label": "PLACEHOLDER (uncalibrated)",
    "mean_sentence": 20.0,
    "stdev_sentence": 10.0,    # variance is the human signal, defend it
    "pct_short": 10,           # <8 words
    "pct_long": 15,            # >30 words
    "you_per_corpus": 80,
    "we_per_corpus": 50,
    "first_person_per_corpus": 10,
    "corpus_words": 7500,      # the corpus size the three counts above are per
}

# Thresholds, as opposed to baselines. These were derived from long-form business
# prose and have held up across several corpora, but they are still empirical
# rather than universal. Re-derive them if you are scanning a genre with a very
# different natural rhythm (technical reference, transcripts, verse).
STDEV_FLOOR = 7.0             # below this, cadence reads as machine-even
STDEV_CEILING = 25.0          # above this, the input is not prose (tables/specs/long lines)
MIN_ROBUST_N = 80             # below this sentence count, cadence calls are noise-dominated
STDEV_MARGIN = 1.0            # within this of the floor, do not assert

# Anchored to SENTENCE start (line start or after terminal punctuation), not line
# start alone: these markers appear mid-paragraph in real prose, and a line-only
# anchor silently misses them.
TAKEAWAY = re.compile(r"(?i)(?:^|(?<=[.!?])\s)\s*(the takeaway|bottom line|in summary|to sum up|"
                      r"in conclusion|what this means for you|key takeaway|the upshot)\b",
                      re.M)
VAGUE = re.compile(r"(?i)\b(a (popular|leading|major|well-known|prominent) \w+|"
                   r"(some|many|most) (experts|observers|critics|analysts)|"
                   r"industry reports|studies (show|suggest)|research (shows|suggests)|"
                   r"it is (widely )?(believed|known|understood))\b")
EMBODIED = re.compile(r"(?i)(chest (tightened|tightens)|breath (caught|hitched)|heart (sank|raced|pounded)|"
                      r"stomach (dropped|churned)|shoulders (slumped|tensed)|throat (tightened|closed))")
HEDGE = re.compile(r"(?i)\b(might|could|perhaps|possibly|potentially|arguably|somewhat|"
                   r"relatively|fairly|it seems|tends to)\b")
CODA = re.compile(r"(?i)(?:^|(?<=[.!?])\s)\s*(in the end|at the end of the day|ultimately|"
                  r"all in all|looking ahead|the future (looks|is)|exciting times)\b",
                  re.M)
INLINE_HEADER = re.compile(r"(?m)^\s*[-*]\s+\*\*[^*]{2,40}\*\*\s*:")


def load_baselines(path):
    """Merge a user baselines file over the placeholders."""
    if not path:
        return dict(BASE)
    with open(path, encoding="utf-8") as fh:
        user = json.load(fh)
    if not isinstance(user, dict):
        raise ValueError("baselines file must contain a JSON object")
    # Keys starting with "_" are comment slots. JSON has no comment syntax and a
    # baselines file people are expected to hand-edit needs one, so treat them as
    # intentional rather than warning about the example file's own annotations.
    unknown = sorted(k for k in set(user) - set(BASE) if not k.startswith("_"))
    if unknown:
        print(f"warning: unknown baseline keys ignored: {unknown}", file=sys.stderr)
    merged = dict(BASE)
    merged.update({k: v for k, v in user.items() if k in BASE})
    if merged["label"] == BASE["label"]:
        merged["label"] = path
    return merged


def sentences(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"(?m)^\s*[#>|].*$", " ", text)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.split()) >= 2]


def analyze(path, base=None):
    base = base or dict(BASE)
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()

    out = []
    if base["label"] == BASE["label"]:
        out.append(("INFO", "UNCALIBRATED: comparing against placeholder baselines that describe "
                            "no real writer. The cadence-floor and person-balance findings below "
                            "are not trustworthy until you pass --baselines. See README."))

    sents = sentences(text)
    if len(sents) < 5:
        out.append(("INFO", f"only {len(sents)} sentences, too short for cadence analysis"))
        return out, sents

    # Fragment-collection guard. Cadence analysis assumes flowing prose. Fed a
    # list of headlines, meta descriptions, CTAs or nav labels it will ALWAYS
    # report uniformity, because those are supposed to be short and even. Found
    # by dogfooding against strings extracted from a live site, where the cadence
    # error was an artifact of the extraction, not a fact about the copy.
    unterminated = sum(1 for s in sents if s.rstrip()[-1:] not in ".!?")
    frag_ratio = unterminated / len(sents)
    mean_len = st.mean(len(s.split()) for s in sents)
    if frag_ratio > 0.4 or mean_len < 12:
        out.append(("INFO", f"FRAGMENT COLLECTION detected ({frag_ratio:.0%} unterminated, "
                            f"mean {mean_len:.1f}w). This looks like headlines/labels/CTAs, "
                            "not flowing prose. Cadence analysis SKIPPED, it would be a "
                            "false positive. Scan the body prose instead."))
        return out, sents

    wl = [len(s.split()) for s in sents]
    mean, sd = st.mean(wl), st.pstdev(wl)
    short = 100 * sum(1 for w in wl if w < 8) / len(wl)
    long_ = 100 * sum(1 for w in wl if w > 30) / len(wl)

    out.append(("STAT", f"sentences {len(sents)} | mean {mean:.1f}w "
                        f"(base {base['mean_sentence']}) | stdev {sd:.1f} "
                        f"(base {base['stdev_sentence']}) | short {short:.0f}% | long {long_:.0f}%"))

    # Structured-content guard, the mirror of the fragment guard above. Tables,
    # spec lists and CSV-ish lines parse as enormous "sentences" and inflate
    # variance far past anything prose produces. Past STDEV_CEILING the document
    # is mixed prose and structure, so cadence is not measuring cadence. Found by
    # dogfooding a brand manuscript at stdev 42.3, which the fragment guard could
    # not catch because it only looked for too-LITTLE variance. Guard both bounds
    # or you have not guarded either.
    if sd > STDEV_CEILING:
        out.append(("INFO", f"MIXED/STRUCTURED CONTENT (stdev {sd:.1f} exceeds {STDEV_CEILING}). "
                            "Tables, spec lists or long unbroken lines are parsing as sentences. "
                            "Cadence analysis is NOT meaningful here. Extract the prose sections "
                            "and rescan them alone."))
        return out, sents

    if sd < STDEV_FLOOR:
        # Downgrade to a non-robust call when the sample is small or the value
        # sits near the threshold. At n=54 a stdev estimate resampled to a
        # 5.7-7.4 spread, i.e. the floor sat INSIDE the noise band, so asserting
        # a finding there would be false precision. Found dogfooding live copy.
        marginal = (len(sents) < MIN_ROBUST_N) or (STDEV_FLOOR - sd) < STDEV_MARGIN
        if marginal:
            out.append(("WARN", f"CADENCE UNIFORMITY (NOT ROBUST): stdev {sd:.1f} vs floor "
                                f"{STDEV_FLOOR}, n={len(sents)}. Too close to the threshold or "
                                "too small a sample to assert. Treat as a prompt to look, not a "
                                "finding. The floor derives from LONG-FORM prose; if this is "
                                "landing-page or short-form copy it is the wrong yardstick."))
        else:
            out.append(("ERROR", f"CADENCE UNIFORMITY: stdev {sd:.1f} is below {STDEV_FLOOR}. "
                                 "Even mid-length rhythm is the strongest machine tell. "
                                 f"Vary sentence length; baseline is {base['stdev_sentence']}."))
    if long_ < 5:
        out.append(("WARN", f"only {long_:.0f}% of sentences exceed 30 words "
                            f"(base {base['pct_long']}%). Prose may be over-chopped."))
    if short < 3:
        out.append(("WARN", f"only {short:.0f}% short sentences (base {base['pct_short']}%). "
                            "No rhythmic contrast."))

    for label, rx, msg in [
        ("TAKEAWAY-MARKER", TAKEAWAY, "Explicit takeaway marker. State the point once, where it lands hardest."),
        ("VAGUE-ALLUSION",  VAGUE,    "Vague attribution. Name the thing or cut the claim."),
        ("EMBODIED-EMOTION", EMBODIED, "Body-performance emotion. Humans more often name the feeling plainly."),
        ("GENERIC-CODA",    CODA,     "Generic wrap-up coda. Common model fingerprint: cut it and end earlier."),
        ("INLINE-HEADER",   INLINE_HEADER, "Bolded inline-header list. Classic AI output shape."),
    ]:
        hits = rx.findall(text)
        if hits:
            out.append(("WARN", f"{label} x{len(hits)}: {msg}"))

    you = len(re.findall(r"(?i)\b(you|your)\b", text))
    we = len(re.findall(r"(?i)\b(we|our)\b", text))
    i = len(re.findall(r"\bI\b", text))
    words = max(1, len(text.split()))
    cw = base["corpus_words"]
    out.append(("STAT", f"you/your {you} | we/our {we} | I {i} "
                        f"(base {base['you_per_corpus']}/{base['we_per_corpus']}/"
                        f"{base['first_person_per_corpus']} per {cw:,}w)"))
    if we > you and words > 300 and base["you_per_corpus"] > base["we_per_corpus"]:
        out.append(("WARN", "we/our outnumbers you/your, which inverts the baseline. "
                            "Most marketing content writes to the reader, not about the company."))
    fp_rate = i / words * cw
    if fp_rate > base["first_person_per_corpus"] * 4 and words > 300:
        out.append(("WARN", f"first-person density high for content genre (~{fp_rate:.0f} "
                            f"per {cw:,}w vs baseline {base['first_person_per_corpus']}). "
                            "Often correct for cold-email, off-voice for marketing content."))

    hedges = len(HEDGE.findall(text))
    out.append(("STAT", f"hedges {hedges}"))
    return out, sents


# Multi-line on purpose: real documents have line breaks, and an earlier
# single-line fixture could not fire the sentence-anchored rules at all, which
# made the self-test pass vacuously. Known-bad input must actually be reachable.
# The fixture must resemble the REAL failure mode. An earlier version used
# 5-word sentences, which is not what machine-uniform prose looks like and also
# tripped the fragment guard, so cadence could never fire. Real AI evenness is
# mid-length sentences (~18-22 words) with low variance. That is what this is:
# every sentence sits in a narrow band, which is exactly the tell.
# Every sentence sits in a narrow mid-length band (measured: mean 15.4, stdev
# 0.9). The narrowness is the point, since that is what machine-uniform prose
# looks like, and the mid length keeps the fixture clear of the fragment guard's
# mean_len < 12 cutoff with room to spare. A shorter fixture trips
# that guard, cadence analysis is skipped entirely, and the self-test passes
# without ever reaching the code it claims to test.
_UNIFORM = [
    "Our platform helps teams manage their daily work with far less friction than they had before.",
    "The system integrates cleanly with all of the tools that your team already uses every day.",
    "Setup takes only a few minutes to complete and requires no technical configuration from your staff.",
    "Reporting gives managers a clear running view of progress across every active project this quarter.",
    "Permissions can be adjusted for each individual member of the team at almost any point in time.",
    "Notifications keep everyone on the project informed without ever flooding their inbox with noise.",
    "Data is stored securely and backed up automatically on a nightly schedule without any supervision.",
    "Support is available whenever your team runs into a problem that is genuinely worth solving.",
]
_TAIL = (
    "\nUltimately, we deliver value to every customer we serve across the region.\n"
    "The bottom line is that many experts agree this is a popular modern choice.\n"
)

# SMALL fixture: n below MIN_ROBUST_N, so cadence must come back as the
# non-robust WARN rather than an ERROR.
SELF_TEST_SMALL = "\n".join(_UNIFORM) + "\n" + _TAIL

# LARGE fixture: n above MIN_ROBUST_N, so the same uniformity must escalate to
# an ERROR. Testing only the small one would let the ERROR branch break silently,
# because both branches emit the string "CADENCE UNIFORMITY". Check both bounds
# or you have checked neither.
SELF_TEST_LARGE = "\n".join(_UNIFORM * 11) + "\n" + _TAIL


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--baselines", metavar="JSON",
                    help="path to your measured baselines (see baselines.example.json). "
                         "Without this, comparisons use placeholders and mean little.")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any ERROR")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        import tempfile, os

        def run(text):
            fd, tmp = tempfile.mkstemp(suffix=".md")
            with os.fdopen(fd, "w") as fh:
                fh.write(text)
            res, _ = analyze(tmp)
            os.unlink(tmp)
            return res

        failures = []

        # Below MIN_ROBUST_N: cadence must be reported, but only as a WARN.
        small = run(SELF_TEST_SMALL)
        print("  small fixture (below MIN_ROBUST_N):")
        for lvl, msg in small:
            print(f"    [{lvl}] {msg}")
        if not any(lvl == "WARN" and "CADENCE UNIFORMITY (NOT ROBUST)" in msg for lvl, msg in small):
            failures.append("small fixture did not produce the non-robust cadence WARN")
        if any(lvl == "ERROR" for lvl, _ in small):
            failures.append("small fixture asserted an ERROR at a sample size too small to support one")
        if not any("GENERIC-CODA" in msg for _, msg in small):
            failures.append("coda rule did not fire")

        # Above MIN_ROBUST_N: the same uniformity must escalate to an ERROR.
        large = run(SELF_TEST_LARGE)
        print("  large fixture (above MIN_ROBUST_N):")
        for lvl, msg in large:
            print(f"    [{lvl}] {msg}")
        if not any(lvl == "ERROR" and "CADENCE UNIFORMITY" in msg for lvl, msg in large):
            failures.append("large fixture did not escalate uniform cadence to an ERROR")

        if failures:
            for f in failures:
                print(f"  SELF-TEST FAILED: {f}")
            return 2
        print("self-test PASSED: cadence warns when the sample is too small to assert, "
              "errors when it is not, and the coda rule fires.")
        return 0

    if not args.files:
        ap.error("need files, or --self-test")

    try:
        base = load_baselines(args.baselines)
    except (OSError, ValueError) as exc:
        print(f"cannot load baselines: {exc}", file=sys.stderr)
        return 2

    errs = 0
    for path in args.files:
        print(f"\n{path}")
        res, _ = analyze(path, base)
        for lvl, msg in res:
            print(f"  [{lvl:<5}] {msg}")
            if lvl == "ERROR":
                errs += 1

    print(f"\nbaselines: {base['label']}")
    print("NOTE: a clean scan does not mean pass 2 passed. Most structural work is")
    print("      judgment on the extracted skeleton. This is the measurable slice only.")
    return 1 if (args.strict and errs) else 0


if __name__ == "__main__":
    sys.exit(main())
