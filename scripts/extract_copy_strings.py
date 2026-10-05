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
    python3 extract_copy_strings.py --diff origin/main...HEAD [PATH...] [--exclude REGEX]
    python3 extract_copy_strings.py --self-test

Using --diff as a CI gate, notes from wiring it into a real Node pipeline:

  - Check out with fetch-depth 0. The default shallow clone has no origin/main
    to diff against, and the step fails for a reason unrelated to copy.
  - Use three-dot (origin/main...HEAD), not two-dot. Two-dot includes changes
    that landed on main since the branch point and blames them on this PR.
  - Run it on pull_request events only. On a push-to-main event the diff is
    empty by construction, so every step passes while checking nothing. That
    is a green tick standing in for coverage, which is worse than no gate.
  - Scope it: pass src/ (or whatever your product tree is) so the gate does not
    fire on tooling. Vendored copies of these scanners are skipped by default.
"""

import argparse
import os
import re
import sys

# Family contract. See scripts/family_check.py.
FAMILY_CONTRACT = {
    "skip_self": True,
    "skip_self_reason": "its docstrings classify as ui-copy and fired 83 times on a vendor-install PR",
    "clean_scan_caveat": True,
}

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
# which starts with a prefix I had not listed). Enumerating prefixes is the same
# mistake as encoding one phrasing of a concept in copy_scan.py: the
# enumeration is always incomplete, so test the SHAPE as well as the members.
TAILWINDISH = re.compile(r"^(?:[a-z-]+:)?(?:flex|grid|text-|bg-|p[xytblr]?-|m[xytblr]?-|w-|h-|size-|border|rounded|gap-|font-|items-|justify-|shrink|grow|inline|absolute|relative|space-|leading-|tracking-)")
_UTIL_TOKEN = re.compile(r"^[a-z0-9]+(?:[-:/][a-z0-9.\[\]%#]+)*$")   # lowercase on purpose


def looks_like_utility_classes(s):
    """True for a Tailwind-style class list, false for prose.

    Not a regex, and the reason is a bug I shipped into this very function.
    The original required every token to contain a hyphen, so one bare token
    ("flex") was enough to break the match and "min-h-full flex flex-col" got
    reported as copy against a real dashboard tree. Relaxing the hyphen
    requirement then over-corrected: with bare tokens allowed, the pattern
    matched "Your marketing audit is ready to review" and suppressed real copy.
    My own self-test caught that, which is the only reason it is not shipped.

    Both bounds need to hold at once, and expressing that as one regex is how
    the first version went wrong. So state it plainly:
      - at least two tokens
      - every token is lowercase and utility-shaped (prose has capitals)
      - at least half the tokens are actually hyphenated
    A prose line containing one hyphenated word fails the last condition, which
    is the case a hyphen-anywhere lookahead would have wrongly suppressed.
    """
    tokens = s.split()
    if len(tokens) < 2:
        return False
    if not all(_UTIL_TOKEN.match(t) for t in tokens):
        return False
    hyphenated = sum(1 for t in tokens if re.search(r"[-:/]", t))
    return hyphenated * 2 >= len(tokens)

# Machine-language strings that read as prose to the extractor: SQL, HTTP verb
# lists, viewport/meta directives, MIME and header values. Found by scanning a
# real Next.js dashboard tree, where SELECT statements and
# "width=device-width, initial-scale=1" were being reported as ui-copy.
MACHINEISH = re.compile(
    r"^\s*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|WITH|PRAGMA)\s|"
    r"^\s*\(?\s*(?:title|assignee|project|status|id)\s+(?:LIKE|IN|=)\s|"
    r"\bwidth=device-width|initial-scale=|user-scalable=|"
    r"^(?:GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)(?:\s*,\s*(?:GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD))+$|"
    r"^[a-z]+/[a-z0-9.+-]+(?:;\s*\w+=|$)",
    re.I)


def looks_like_copy(s):
    s = s.strip()
    if len(s) < 12 or len(s) > 600:
        return False
    if CODEISH.match(s) or TAILWINDISH.match(s) or looks_like_utility_classes(s):
        return False
    if MACHINEISH.search(s):
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

# DEVELOPER-facing strings, which are not the rendered surface this gate exists
# to protect. Found by running diff mode against a real backend commit: it
# flagged two console.warn messages out of a scheduling module as "ui-copy",
# because genre_for() defaults anything unrecognised to ui-copy. Nobody outside
# the repo ever reads those. Left in, the gate fires on ordinary backend work,
# reviewers learn the noise is safe to skip, and the one real hit goes with it.
# That is the untrustworthy-check failure, and it is worse than no gate.
# Matched against the source immediately BEFORE the string, not the string
# itself, because the tell is the call site rather than the wording.
LOGGISH = re.compile(
    r"(?:console\.(?:log|warn|error|info|debug|trace)|"
    r"logger?\.(?:log|warn|error|info|debug|trace)|"
    r"\bthrow\s+new\s+\w*Error|new\s+\w*Error|"
    r"\bassert\w*|process\.(?:stdout|stderr)\.write|"
    r"\bdebug\(|\bwarn\(|\bpanic\(|\bfatal\()"
    r"\s*\(?\s*(?:`|\"|')?\s*$")
LOG_LOOKBEHIND = 80   # chars of preceding source to inspect


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


def strings_in(src, path, keep_lines=None):
    """Pull copy-shaped strings out of one blob of source. Shared by tree mode
    and diff mode so the two can never drift in what counts as copy.

    keep_lines: diff mode passes the 1-based line numbers that the diff
    actually changed. The rest of src is unchanged context, present only so
    the LOGGISH lookbehind can see a call site on an untouched line. A string
    is reported only if its span touches a changed line."""
    found = []
    # drop import lines and comments, which carry non-copy strings. Block
    # comments keep their newlines so line numbers stay exact for keep_lines.
    src = re.sub(r"(?m)^\s*import .*$", "", src)
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r"/\*.*?\*/", lambda c: "\n" * c.group(0).count("\n"), src, flags=re.S)
    matches = list(STRING_RE.finditer(src)) + list(TEMPLATE_RE.finditer(src))
    for m in matches:
        val = m.group("val")
        # unescape the common cases only
        val = val.replace("\\n", " ").replace('\\"', '"').replace("\\'", "'")
        val = re.sub(r"\$\{[^}]*\}", "…", val)   # template interpolations
        val = " ".join(val.split())
        if not looks_like_copy(val):
            continue
        # Skip developer-facing strings (log lines, thrown errors). See LOGGISH.
        before = src[max(0, m.start() - LOG_LOOKBEHIND):m.start()]
        if LOGGISH.search(before):
            continue
        line = src[: m.start()].count("\n") + 1
        if keep_lines is not None:
            span = range(line, line + m.group(0).count("\n") + 1)
            if not any(n in keep_lines for n in span):
                continue
        key = m.groupdict().get("key")
        found.append((genre_for(key, path), path, line, val))
    return found


def dedupe(found):
    seen, out = set(), []
    for g, p, l, v in found:
        if (g, v) in seen:
            continue
        seen.add((g, v))
        out.append((g, p, l, v))
    return out


def extract(paths):
    found = []
    for path in walk(paths):
        try:
            src = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        found.extend(strings_in(src, path))
    return dedupe(found)


# Files that ARE this tooling. A repo that vendors these scripts will otherwise
# have the gate fire on the scanners' own docstrings: 83 hits on the very PR
# that installs them, none of it product copy. copy_scan.py has carried a SCOPE
# note about exactly this since it was written, and diff mode shipped without
# applying it. A gate that fails the PR installing it, then fires on every later
# PR touching tools/, teaches people to ignore it on day one. That is the
# untrustworthy-check failure arriving before the check has ever been useful.
SELF_FILES = re.compile(r"(?:^|/)(?:extract_copy_strings|copy_scan|structural_scan)\.py$")


def _path_allowed(path, include=None, exclude=None, skip_self=True):
    if skip_self and SELF_FILES.search(path):
        return False
    if exclude and any(re.search(pat, path) for pat in exclude):
        return False
    if include:
        # match tree mode: a path argument scopes the run
        return any(path == inc or path.startswith(inc.rstrip("/") + "/") for inc in include)
    return True


def extract_from_diff(ref, repo=".", include=None, exclude=None, skip_self=True):
    """Return copy strings that this diff ADDS.

    Why added-lines-only rather than diffing the extraction of two trees: the
    routing gate asks 'does this PR introduce new user-facing prose', and a
    whole-tree comparison answers a slower, different question. Reconstructing
    a pseudo-source from '+' lines does break constructs that span lines, but
    it breaks them in the safe direction: a partially-added template literal
    still surfaces its added text.

    A pure MOVE shows up as an identical string on both a '-' and a '+' line.
    That is not new copy and is suppressed. An EDIT produces different text on
    the '+' side and does fire, which is the 'or substantially rewritten' half
    of the trigger.
    """
    import subprocess
    try:
        out = subprocess.run(
            # 3 lines of context, not 0: a log call whose `console.warn(` line is
            # unchanged must still be visible to the LOGGISH lookbehind.
            ["git", "-C", repo, "diff", "--unified=3", "--no-color", ref],
            capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError(f"git diff failed: {exc}") from exc
    return copy_in_diff_text(out, include=include, exclude=exclude, skip_self=skip_self)


def copy_in_diff_text(diff, include=None, exclude=None, skip_self=True):
    """Split out from extract_from_diff so it can be tested on diff text
    directly, without needing a subprocess."""
    # Each side is rebuilt as context + its own changed lines, in order, so a
    # call site on an unchanged line still precedes its string. The changed
    # line numbers are tracked so only strings touching them are reported.
    # Hunks are separated by a blank line so one hunk cannot bleed into the next.
    new_side, old_side, new_keep, old_keep, path = {}, {}, {}, {}, None
    for line in diff.split("\n"):
        if line.startswith("+++ b/"):
            p = line[6:].strip()
            path = p if (os.path.splitext(p)[1] in SOURCE_EXT
                         and not SKIP_FILE.search(os.path.basename(p))
                         and not any(d in p.split("/") for d in SKIP_DIR)
                         and _path_allowed(p, include, exclude, skip_self)) else None
            continue
        if line.startswith("@@"):
            if path is not None:
                for side in (new_side, old_side):
                    side.setdefault(path, []).append("")
            continue
        if line.startswith(("--- ", "+++ ", "diff --git", "index ", "\\ No newline")):
            continue
        if path is None:
            continue
        if line.startswith("+"):
            new_side.setdefault(path, []).append(line[1:])
            new_keep.setdefault(path, set()).add(len(new_side[path]))
        elif line.startswith("-"):
            old_side.setdefault(path, []).append(line[1:])
            old_keep.setdefault(path, set()).add(len(old_side[path]))
        elif line.startswith(" "):
            for side in (new_side, old_side):
                side.setdefault(path, []).append(line[1:])

    # Report ADDED, REMOVED and MODIFIED. An earlier version reported only
    # additions; review corrected the rule to any diff touching a
    # classified-genre string, because "was this substantially rewritten" is a
    # taste judgment and a rule that needs one erodes to nothing. Deleting
    # user-facing copy is a copy decision too, so removals are in scope.
    #
    # Pure MOVES are still suppressed, and that is not a judgment call: it is an
    # exact text match on both sides of the diff. The string did not change, so
    # there is nothing to review.
    found = []
    for p in set(new_keep) | set(old_keep):
        new = strings_in("\n".join(new_side.get(p, [])), p, keep_lines=new_keep.get(p, set()))
        old = strings_in("\n".join(old_side.get(p, [])), p, keep_lines=old_keep.get(p, set()))
        new_v = {f[3] for f in new}
        old_v = {f[3] for f in old}
        found.extend([("+", ) + f for f in new if f[3] not in old_v])
        found.extend([("-", ) + f for f in old if f[3] not in new_v])
    # dedupe on (sign, genre, text)
    seen, out = set(), []
    for sign, g, p, l, v in found:
        if (sign, g, v) in seen:
            continue
        seen.add((sign, g, v))
        out.append((sign, g, p, l, v))
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
    ap.add_argument("paths", nargs="*",
                    help="paths to scan. In --diff mode these SCOPE the diff, the same "
                         "way they scope a tree walk.")
    ap.add_argument("-o", "--out")
    ap.add_argument("--by-genre", action="store_true")
    ap.add_argument("--diff", metavar="REF",
                    help="report only copy strings this diff ADDS, versus REF "
                         "(e.g. origin/main, HEAD~1). Exits 1 if any are found, "
                         "so it can gate a mixed code+copy PR.")
    ap.add_argument("--repo", default=".", help="repo root for --diff (default: cwd)")
    ap.add_argument("--exclude", action="append", metavar="REGEX", default=[],
                    help="skip paths matching REGEX in --diff mode; repeatable")
    ap.add_argument("--include-self", action="store_true",
                    help="do NOT skip vendored copies of these scanners (default is to skip "
                         "them, so a repo vendoring this tool is not gated on its own docstrings)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.diff:
        try:
            res = extract_from_diff(args.diff, args.repo,
                                    include=args.paths or None,
                                    exclude=args.exclude,
                                    skip_self=not args.include_self)
        except RuntimeError as exc:
            print(exc, file=sys.stderr)
            return 2
        if not res:
            print(f"no user-facing copy changed versus {args.diff}.")
            return 0
        print(f"{len(res)} user-facing string change(s) versus {args.diff}.")
        print("Route to the copy pass before merge.\n")
        for sign, g, p, l, v in res:
            what = "added" if sign == "+" else "removed"
            print(f"  {sign} [{g}] {p}: {v}   ({what})")
        print("\nNOTE: this flags that copy changed, not that it is wrong. Triage is")
        print("      expected to be fast on trivial ones. A clean result is not a pass:")
        print("      it means no classified-genre string moved, nothing more.")
        return 1

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
        print("  tree mode PASSED: extracts copy, rejects code, tags genre.")

        # --- diff mode, on a REAL git repo and a REAL diff ---
        # Not a hand-written diff fixture. A hand-written one would encode my
        # assumptions about git's output format, and the whole point is to
        # verify against what git actually emits.
        import subprocess
        rd = tempfile.mkdtemp()

        def g(*a):
            return subprocess.run(["git", "-C", rd, *a], capture_output=True,
                                  text=True, check=True).stdout

        g("init", "-q")
        g("config", "user.email", "t@t"); g("config", "user.name", "t")
        base = ('const subject = "Your quarterly impact report is ready";\n'
                'const blurb = "We help small teams ship better software faster";\n'
                'const cls = "flex items-center gap-4 rounded-lg";\n')
        open(os.path.join(rd, "app.ts"), "w").write(base)
        g("add", "-A"); g("commit", "-qm", "base")

        after = ('const cls = "flex items-center gap-4 rounded-lg";\n'          # MOVED
                 'const subject = "Your quarterly impact report is ready";\n'   # MOVED
                 'const blurb = "We help small teams ship software with less friction";\n'  # EDITED
                 'const cta = "Book a walkthrough with our team today";\n'      # ADDED
                 'const pad = "px-4 py-2 text-sm font-medium";\n'               # ADDED, utility
                 # ADDED, developer-facing. Real instance: diff mode flagged two
                 # console.warn lines out of a live backend commit as ui-copy.
                 'console.warn("computeStaleThreshold: config is unparseable, falling back");\n'
                 'throw new Error("Could not resolve the requested agent identifier");\n')
        open(os.path.join(rd, "app.ts"), "w").write(after)
        g("add", "-A"); g("commit", "-qm", "change")

        dres = extract_from_diff("HEAD~1", rd)
        dvals = {v for _, _, _, _, v in dres}
        dadded = {v for sg, _, _, _, v in dres if sg == "+"}
        for sg, g_, p_, l_, v_ in dres:
            print(f"  [diff] {sg} [{g_}] {v_[:70]}")

        must_fire = {
            "Book a walkthrough with our team today":                  "newly added string",
            "We help small teams ship software with less friction":    "edited string (rewritten)",
        }
        must_not_fire = {
            "Your quarterly impact report is ready":  "moved verbatim, not new copy",
            "px-4 py-2 text-sm font-medium":          "added utility classes, not copy",
            "flex items-center gap-4 rounded-lg":     "moved utility classes",
            "computeStaleThreshold: config is unparseable, falling back":
                "console.warn line, developer-facing not user-facing",
            "Could not resolve the requested agent identifier":
                "thrown Error message, developer-facing; note it reads like copy",
        }
        fails = [f"did not fire on {d}: {s!r}" for s, d in must_fire.items() if s not in dvals]
        fails += [f"wrongly fired on {d}: {s!r}" for s, d in must_not_fire.items() if s in dvals]

        # positive control: the checker must be capable of failing at all
        if not copy_in_diff_text("+++ b/x.ts\n+const h = \"A brand new headline for the page\";\n"):
            fails.append("positive control failed: checker did not fire on known-dirty diff text")

        if fails:
            for f in fails:
                print(f"  SELF-TEST FAILED: {f}")
            return 2
        print("  diff mode PASSED: fires on added and rewritten copy, silent on moves and utilities.")

        # Call site on an UNCHANGED line. Real instance: a PR that rewrote three
        # log messages, each on its own line under an untouched `console.warn(`,
        # had all three flagged as ui-copy, because diff mode saw only the
        # changed lines and the call site was context. Both bounds asserted:
        # context must silence a log line, and must NOT silence real copy whose
        # neighbour merely happens to be context.
        cd = ('+++ b/src/app/api/contact/route.ts\n'
              '@@ -10,3 +10,3 @@\n'
              '     console.warn(\n'
              '-      "[contact] Mail key not set. Logging submission instead of sending email."\n'
              '+      `[contact] Mail key not set; inquiry not emailed (lead still routed onward) at ${t}`\n'
              '     );\n'
              '@@ -40,3 +40,3 @@\n'
              '   /* layout note that\n'
              '      spans two lines */\n'
              '   const props = {\n'
              '     subtitle: "An unchanged subtitle that must stay quiet here",\n'
              '-    headline: "Ship the site your customers already expect",\n'
              '+    headline: "Ship the website your customers already expect",\n'
              '   };\n'
              '@@ -80,2 +81,3 @@\n'
              '   cta: "Book a free intro call this week",\n'
              '+  footerCta: "Book a free intro call this week",\n'
              ' };\n')
        cres = {v for _, _, _, _, v in copy_in_diff_text(cd)}
        cfails = []
        for s in ("[contact] Mail key not set; inquiry not emailed (lead still routed onward) at …",
                  "[contact] Mail key not set. Logging submission instead of sending email."):
            if s in cres:
                cfails.append(f"wrongly fired on a log line whose console call is context: {s!r}")
        if "An unchanged subtitle that must stay quiet here" in cres:
            cfails.append("reported a string on an UNCHANGED context line")
        # Same text newly placed beside an unchanged copy of itself is a new
        # placement and must still fire, as it did before context was read.
        if "Book a free intro call this week" not in cres:
            cfails.append("context copy of a string masked its newly added duplicate")
        for s in ("Ship the website your customers already expect",
                  "Ship the site your customers already expect"):
            if s not in cres:
                cfails.append(f"did not fire on copy next to unchanged context: {s!r}")
        if cfails:
            for f in cfails:
                print(f"  SELF-TEST FAILED: {f}")
            return 2
        print("  diff context PASSED: a console call on an unchanged line silences its log text; copy still fires.")

        # Scoping. A repo that vendors these scanners must not be gated on the
        # scanners' own docstrings: that fired 83 times on a real vendor-install
        # PR, none of it product copy. Both bounds are asserted, because a skip
        # rule that also swallows product copy is the mirror failure.
        sd = ('+++ b/tools/extract_copy_strings.py\n'
              '+"""Pull external-facing text out of source files for review."""\n'
              '+++ b/src/app/page.tsx\n'
              '+const h = "Book a walkthrough with our team today";\n'
              '+++ b/docs/notes.ts\n'
              '+const n = "An internal note that should be excludable here";\n')
        prod = "Book a walkthrough with our team today"
        selfdoc = "Pull external-facing text out of source files for review."
        vals = lambda **kw: {v for *_, v in copy_in_diff_text(sd, **kw)}
        sfail = []
        if selfdoc in vals():
            sfail.append("default did not skip a vendored copy of this scanner")
        if prod not in vals():
            sfail.append("default skipped real product copy")
        if selfdoc not in vals(skip_self=False):
            sfail.append("--include-self did not restore the vendored copy")
        if vals(include=["src/"]) != {prod}:
            sfail.append("path scoping in diff mode did not restrict to src/")
        if "An internal note that should be excludable here" in vals(exclude=[r"^docs/"]):
            sfail.append("--exclude did not drop the excluded path")
        if sfail:
            for f in sfail:
                print(f"  SELF-TEST FAILED: {f}")
            return 2
        print("  scoping PASSED: skips vendored self, honors paths and --exclude, keeps product copy.")
        print("\nself-test PASSED (tree + diff).")
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
