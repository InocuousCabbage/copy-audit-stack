#!/usr/bin/env python3
"""
extract_copy_strings.py: pull external-facing text out of SOURCE files.

Why this exists: the audit surface was originally defined by what is convenient
to FETCH (HTTP pages). That silently excluded external-facing text that is
GENERATED rather than served: outbound email subject lines and bodies,
transactional copy, OG/meta/aria strings, autoresponders, PDF generators.

Those are often the highest-stakes copy a project produces. A bad email subject
line lands in a prospect's inbox with your client's name on it and cannot be
quietly redeployed the way a web page can.

The general rule this encodes: scope an audit by RENDERED SURFACE, not by
transport. If a human reads it, it is in scope, whether it arrives over HTTP,
SMTP, or a PDF generator. Scoping by "what I can fetch" draws the boundary
where your tooling happens to stop rather than where the risk does.

Pipe the output into copy_scan.py:

    python3 scripts/extract_copy_strings.py src/ -o /tmp/copy.txt
    python3 scripts/copy_scan.py /tmp/copy.txt

Usage:
    python3 extract_copy_strings.py PATH [PATH...] [-o OUT] [--by-genre]
    python3 extract_copy_strings.py --self-test
"""

import argparse
import os
import re
import sys

SOURCE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".py", ".html"}
SKIP_DIR = {"node_modules", ".next", ".git", "dist", "build", ".vercel", "__pycache__",
            "__tests__", "tests", "test", "e2e", "cypress", "playwright"}
# Test files describe() and it() names read exactly like copy ("Audit API: Rate
# Limiting") and inflated a real scan by ~15 phantom hits. They never ship, so
# a hit in one is an instrument bug, not a finding. Found by dogfooding, where
# the count looked implausibly high until the hits were classified by file.
SKIP_FILE = re.compile(r"\.(test|spec)\.[jt]sx?$|\.stories\.[jt]sx?$")

# Keys whose values are external-facing text, grouped by genre. Genre matters:
# an email subject line is neither landing copy nor body prose and should not be
# audited against either baseline.
GENRE_KEYS = {
    "email-subject": r"subject",
    "email-body":    r"(html|text|body|message|template|greeting|signoff)",
    "meta":          r"(title|description|ogTitle|ogDescription|og:title|og:description|alt|ariaLabel|aria-label|placeholder)",
    "ui-copy":       r"(headline|subtitle|blurb|cta|label|heading|caption|tagline|copy)",
}

# A string is copy if it reads like a sentence or phrase, not an identifier,
# path, class list, or config value.
CODEISH = re.compile(
    r"^(?:[a-z0-9_-]+/|https?://|[.#][\w-]+$|[A-Z_]{3,}$|\d+(\.\d+)?(px|rem|em|%|s|ms)?$"
    r"|[\w-]+\.(ts|tsx|js|jsx|css|json|png|jpg|svg|webp)$|#[0-9a-fA-F]{3,8}$)"
)
# Utility-class strings. Two tests: starts-with a known prefix, OR is composed
# ENTIRELY of hyphenated utility tokens (catches "size-5 shrink-0 text-primary",
# which starts with a prefix that was not on the list). Enumerating prefixes is
# the same mistake as encoding one phrasing of a concept in copy_scan.py: the
# enumeration is always incomplete, so test the SHAPE as well as the members.
TAILWINDISH = re.compile(r"^(?:[a-z-]+:)?(?:flex|grid|text-|bg-|p[xytblr]?-|m[xytblr]?-|w-|h-|size-|border|rounded|gap-|font-|items-|justify-|shrink|grow|inline|absolute|relative|space-|leading-|tracking-)")
ALL_UTILITY = re.compile(r"^(?:[a-z0-9]+(?:[-:/][a-z0-9.\[\]%#]+)+\s*)+$", re.I)


def looks_like_copy(s):
    s = s.strip()
    if len(s) < 12 or len(s) > 600:
        return False
    if CODEISH.match(s) or TAILWINDISH.match(s) or ALL_UTILITY.match(s):
        return False
    if CODEY.search(s):        # slab of JSX/TS that slipped through
        return False
    if " " not in s:
        return False
    # needs at least a few word-ish tokens
    words = [w for w in re.split(r"\s+", s) if re.search(r"[A-Za-z]", w)]
    if len(words) < 3:
        return False
    # reject strings that are mostly symbols/markup
    letters = sum(c.isalpha() or c.isspace() for c in s)
    return letters / len(s) > 0.65


def genre_for(key, path):
    k = (key or "").lower()
    for genre, pat in GENRE_KEYS.items():
        if re.search(pat, k, re.I):
            return genre
    if re.search(r"(mail|contact|audit|notify|send)", os.path.basename(path), re.I):
        return "email-body"
    return "ui-copy"


# NO re.S. With DOTALL the value class spans newlines and happily swallows the
# code BETWEEN two strings, so on real TSX every match was a slab of JSX. My
# self-test fixture was clean single-line code and never exposed it. Same shape
# as the copy_scan skip-heuristic bug: the assumption held across the test data
# and failed across the real input. Quoted strings stay on one line here;
# template literals are handled separately below.
STRING_RE = re.compile(
    r"""(?:(?P<key>[A-Za-z_][\w.\-]*)\s*[:=]\s*)?"""      # optional key
    # (?!(?P=q)) not (?!\3): \3 is `val`, the group being defined, still open.
    r"""(?P<q>["'])(?P<val>(?:\\.|(?!(?P=q))[^\n]){12,600}?)(?P=q)"""
)
# Template literals may legitimately wrap, so newlines are allowed inside them,
# but the CODEY filter still rejects any capture that ran past the literal.
TEMPLATE_RE = re.compile(r"`(?P<val>(?:\\.|[^`]){12,600}?)`")

# Hard markers that a captured string is code, not copy.
CODEY = re.compile(r"(?:</|/>|=>|className|useState|useRef|useEffect|import |export |"
                   r"function |return \(|\{\s*\}|\bconst \b|\blet \b|;\s*$|\)\s*;|"
                   r"aria-hidden|tabIndex|onClick|\bprops\b|=\{)")


def walk(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIR]
            for f in files:
                if os.path.splitext(f)[1] in SOURCE_EXT and not SKIP_FILE.search(f):
                    yield os.path.join(root, f)


def extract(paths):
    found = []
    for path in walk(paths):
        try:
            src = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        # drop import lines and comments, which carry non-copy strings
        src = re.sub(r"(?m)^\s*import .*$", "", src)
        src = re.sub(r"//[^\n]*", "", src)
        src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
        matches = list(STRING_RE.finditer(src)) + list(TEMPLATE_RE.finditer(src))
        for m in matches:
            val = m.group("val")
            # unescape the common cases only
            val = val.replace("\\n", " ").replace('\\"', '"').replace("\\'", "'")
            val = re.sub(r"\$\{[^}]*\}", "…", val)   # template interpolations
            val = " ".join(val.split())
            if looks_like_copy(val):
                line = src[: m.start()].count("\n") + 1
                key = m.groupdict().get("key")
                found.append((genre_for(key, path), path, line, val))
    # dedupe on (genre, text)
    seen, out = set(), []
    for g, p, l, v in found:
        if (g, v) in seen:
            continue
        seen.add((g, v))
        out.append((g, p, l, v))
    return out


SELF_TEST_SRC = '''
import { x } from "./y";
const subject = "Your marketing audit is ready to review";
const meta = { title: "Northwind: inventory software for small manufacturers" };
const cls = "flex items-center justify-between rounded-lg";
const path = "components/site-header.tsx";
const body = `Hi ${name}, we finished the audit and here is what we found.`;
const short = "OK";
const hex = "#1a2b3c";
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*")
    ap.add_argument("-o", "--out")
    ap.add_argument("--by-genre", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        import tempfile
        d = tempfile.mkdtemp()
        f = os.path.join(d, "route.ts")
        open(f, "w").write(SELF_TEST_SRC)
        res = extract([f])
        vals = {v for _, _, _, v in res}
        genres = {g for g, _, _, _ in res}
        want_in = ["Your marketing audit is ready to review",
                   "Northwind: inventory software for small manufacturers"]
        want_out = ["flex items-center justify-between rounded-lg",
                    "components/site-header.tsx", "OK", "#1a2b3c"]
        missing = [w for w in want_in if w not in vals]
        leaked = [w for w in want_out if w in vals]
        for g, _, l, v in res:
            print(f"  [{g}] L{l} {v[:70]}")
        if missing or leaked:
            print(f"\nSELF-TEST FAILED. missing={missing} leaked={leaked}")
            return 2
        if "email-subject" not in genres:
            print("\nSELF-TEST FAILED: subject line not genre-tagged")
            return 2
        print("\nself-test PASSED: extracts copy, rejects code, tags genre.")
        return 0

    if not args.paths:
        ap.error("need paths, or --self-test")

    res = extract(args.paths)
    lines = []
    if args.by_genre:
        for genre in sorted({g for g, _, _, _ in res}):
            lines.append(f"\n===== {genre} =====")
            for g, p, l, v in res:
                if g == genre:
                    lines.append(v)
    else:
        lines = [v for _, _, _, v in res]

    text = "\n".join(lines)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text + "\n")
        print(f"wrote {args.out}")
    else:
        print(text)

    from collections import Counter
    c = Counter(g for g, _, _, _ in res)
    print(f"\n{len(res)} copy strings across {len(set(p for _, p, _, _ in res))} files", file=sys.stderr)
    for g, n in c.most_common():
        print(f"  {g}: {n}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
