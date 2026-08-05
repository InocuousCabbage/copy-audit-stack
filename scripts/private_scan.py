#!/usr/bin/env python3
"""
private_scan.py: gate for content moving from a private repo into a public one.

Copy-up is the dangerous direction. Publishing is hard to unring, and the
mistake is nearly always incidental rather than careless: a provenance note
naming a client directory, an example placeholder using a real first name, a
comment crediting a colleague by handle. None of it looks like a secret while
you are writing it.

This runs on the ADDED LINES OF A DIFF, not on whole files. Pre-existing
exposure in an old repo would drown a first run and train you to skip it. A
clean result therefore means "you are not making it worse", NOT "this repo is
clean". Those are different claims and only the first one is checked here.

THE TERM LIST IS NOT IN THIS FILE, and cannot be. An enumeration of the things
you must not publish is itself the thing you must not publish. So this ships
with data/private-terms.example.txt, which describes nobody, and says so on
every run until you point it at your own list with --terms. Same arrangement as
structural_scan.py's placeholder baselines, for the same reason: shipping
uncalibrated has to be visible rather than silently wrong.

MENTIONS ARE NOT USES. A document that DESCRIBES the gate, or a test fixture
that must contain a dirty string to prove the gate fires, is not a leak. An
early hand-run version of this had no such notion and fired on the very file
documenting the procedure, which is the fastest way to teach someone to ignore
a check. Hits inside a fenced code block, or on a line carrying an explicit
`private-scan-allow:` marker with a stated reason, are DOWNGRADED and printed.
They are never silently dropped: a real use does live inside quotes and fences
routinely, and suppression there would rebuild the failure this file exists to
prevent.

Usage:
    python3 scripts/private_scan.py --terms data/private-terms.txt
    python3 scripts/private_scan.py --terms FILE --diff origin/main...HEAD
    python3 scripts/private_scan.py --terms FILE --paths some/file.md other/
    python3 scripts/private_scan.py --self-test

Exit codes. Read the exit code of THIS command, not of anything you pipe it
into: a pipeline reports the status of its last element, so `private_scan | tail`
returns tail's success and will report a run that found leaks as clean.

    0  no errors on the added lines
    1  at least one error-level hit. Do not commit.
    2  --self-test failed. The gate itself is broken; fix it before trusting a 0.
    3  timed out. NOT a clean result and NOT a dirty one. It means the run could
       not be completed, which is a third thing, and treating non-zero as dirty
       here would report a stalled filesystem as a private-data leak.

Keep this script, the term list, and the repository on local disk. Every stall
observed so far has been a cloud-sync or network mount, not this code.
"""

import argparse
import os
import re
import signal
import subprocess
import sys
import time

# BOUNDED FAILURE.
#
# The first person to adopt this tool who was not its author hit a 120-second
# stall that produced no output at all, and could not tell from the outside
# whether it was slow, wedged, or blocked on a filesystem. They waited, killed
# it, and went back to running the checks by hand. That is the worst outcome
# available: a gate that hangs is more damaging than a gate that is missing,
# because a missing gate is visible and a hanging one teaches its operator to
# route around it permanently after a single encounter.
#
# The scanning itself was never the problem, and was measured at roughly four
# orders of magnitude faster than the observed stall. What was wrong is that
# every blocking operation here was unbounded and the tool said nothing until
# it had finished. Reading the term list, shelling out to git, and walking a
# tree can each block forever, and on a network or file-provider mount they
# genuinely do.
#
# So silence had to carry the explanation, and silence cannot: an absence
# cannot report its own cause. The report has to come from something that
# OUTLIVES or PRECEDES the thing being described, which is what a startup line
# and a watchdog are. Same rule as the run manifest that records unrun steps,
# one layer down and aimed at this tool's own behaviour.
#
# KNOWN LIMIT, stated because the fix reads more complete than it is: this
# bounds everything from process start onward. It cannot bound getting to
# process start. If the interpreter stalls READING THIS FILE, because the
# script itself sits on a stalled mount, nothing below has run yet and nothing
# below can help. Keep the scanner on local disk.


class StageTimeout(Exception):
    """Raised when the watchdog fires. Carries the stage that was in flight."""


_STAGE = "starting up"
_ARMED = False


def set_stage(what):
    """Name the operation in flight, so a timeout can say WHICH one blocked.

    'timed out' on its own sends the reader back to guessing, which is the
    state this whole change exists to remove.
    """
    global _STAGE
    _STAGE = what


def install_watchdog(seconds):
    """Bound the whole run rather than each call we happened to predict.

    Deliberately a single SIGALRM around everything instead of a timeout
    argument on each blocking call. The stall that prompted this was in
    open(), which takes no timeout, and the next one will be somewhere nobody
    listed either. A watchdog covers operations that have not been thought of;
    a per-call timeout only covers the ones that have.
    """
    global _ARMED
    if not seconds or seconds <= 0 or not hasattr(signal, "SIGALRM"):
        return False

    def _fire(_signum, _frame):
        raise StageTimeout(_STAGE)

    signal.signal(signal.SIGALRM, _fire)
    signal.alarm(int(seconds))
    _ARMED = True
    return True


def cancel_watchdog():
    """Disarm. Leaving an alarm armed past the work it was guarding would fire
    into unrelated code later and report the wrong stage, which is worse than
    not guarding at all."""
    global _ARMED
    if _ARMED and hasattr(signal, "SIGALRM"):
        signal.alarm(0)
        _ARMED = False

# Family contract. Asserted by scripts/family_check.py.
# Corrected during dogfooding, and the correction is worth keeping. This first
# declared skip_self=False, reasoning that the term list lives in an external
# data file so the source has nothing to fire on. Then the gate was pointed at
# its own diff and fired five times, because SELF_DIFF below is a fixture of
# deliberately dirty strings that exists to prove the gate works. The reasoning
# was about the term LIST and the fixture is a separate surface I had not
# thought about. Same shape as the defect that created family_check.
FAMILY_CONTRACT = {
    "skip_self": True,
    "skip_self_reason": (
        "its self-test fixture is made of deliberately dirty strings, so pointed "
        "at its own source it reports its own test data as leaks"
    ),
    "clean_scan_caveat": True,
}

# Files that ARE this tooling. Same rule the siblings use, extended to cover a
# vendored copy of this scanner.
SELF_FILES = re.compile(r"(?:^|/)(?:private_scan|copy_scan|extract_copy_strings|structural_scan)\.py$")


def is_self(path):
    """True if path is a copy of this tooling rather than something to gate."""
    return bool(SELF_FILES.search((path or "").replace(os.sep, "/")))

# Pattern gates. Unlike the term list these are structural and safe to ship,
# because they describe a SHAPE rather than naming anything.
PATTERN_GATES = [
    ("ABS-PATH", re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+"),
     "Absolute path containing a username."),
    ("PRIVATE-URL", re.compile(r"(?i)\b(?:localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+)\b"),
     "Local or private-network address. Rarely meaningful to a reader outside."),
    ("CREDENTIAL", re.compile(r"\b(?:sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|"
                              r"\d{8,10}:[A-Za-z0-9_-]{30,})"),
     "Credential-shaped string. Rotate first, then decide whether it was real."),
]

# A line may exempt itself, but it has to say why. A bare marker would let
# anything through with no argument recorded, which is how an exemption path
# becomes the way the gate is routinely defeated.
ALLOW = re.compile(r"private-scan-allow:\s*(?P<reason>\S.*?)\s*(?:-->|\*/|$)")

FENCE = re.compile(r"^\s*(?:```|~~~)")


def load_terms(path):
    """Read the operator's term list. Blank lines and # comments ignored.

    Lines starting with '~' are OUT-OF-DOMAIN GUARDS: a term that would
    otherwise collide with ordinary vocabulary. 'lever' is a client name and
    also half of 'revenue levers', so the guard suppresses the match when the
    surrounding text looks like the innocent sense.
    """
    terms, guards = [], []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith("~"):
                guards.append(re.compile(line[1:].strip(), re.I))
            else:
                terms.append(line)
    if not terms:
        raise ValueError(f"{path}: no terms found. An empty term list makes this gate vacuous.")
    return terms, guards


def build_term_rx(terms):
    """Word-boundary alternation.

    Word boundaries are not optional here: a substring match on a three-letter
    first name fires inside 'benchmark', and an instrument that cries wolf on
    ordinary prose gets switched off within a day.
    """
    return re.compile(r"\b(" + "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) + r")\b", re.I)


def added_lines(diff_ref=None, paths=None, timeout=None):
    """Added lines as (path, lineno_in_new_file, text)."""
    if paths:
        out = []
        set_stage(f"walking {len(paths)} path(s) on disk: {', '.join(paths[:3])}")
        for p in paths:
            for root, _, files in os.walk(p) if os.path.isdir(p) else [(None, None, None)]:
                if root is None:
                    with open(p, encoding="utf-8", errors="replace") as fh:
                        out += [(p, i, l) for i, l in enumerate(fh, 1)]
                    break
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, encoding="utf-8", errors="replace") as fh:
                            out += [(fp, i, l) for i, l in enumerate(fh, 1)]
                    except OSError:
                        pass
        return out

    cmd = ["git", "diff", "--unified=0"]
    cmd += [diff_ref] if diff_ref else ["--cached"]
    set_stage(f"running: {' '.join(cmd)}")
    # Popen rather than run(), specifically so the child is killed on EITHER
    # timeout path. This was written first as run(timeout=...) with a comment
    # claiming nothing would be left running, and testing it showed the
    # watchdog usually wins the race, raises through run(), and leaves git
    # alive. A scanner that leaks a stuck process every time it gives up would
    # make a stalled mount progressively worse each time someone retried.
    def _kill(p):
        # The whole process GROUP, not the process. Killing only the direct
        # child was tried and tested: git's own children survive it, so a
        # timed-out run left a stuck process behind every time. start_new_session
        # puts git in its own group so the group can be killed as a unit, and
        # has the side benefit of detaching it from the terminal, so it cannot
        # sit waiting on a prompt nobody is there to answer.
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            p.kill()
        try:
            p.communicate(timeout=5)
        except Exception:
            pass

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True,
                                start_new_session=True)
    except FileNotFoundError as exc:
        raise SystemExit(f"cannot read diff: {exc}")
    try:
        raw, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill(proc)
        raise StageTimeout(f"running: {' '.join(cmd)}")
    except StageTimeout:
        _kill(proc)
        raise
    if proc.returncode != 0:
        raise SystemExit(f"cannot read diff: git exited {proc.returncode}: {err.strip()}")

    out, path, lineno = [], None, 0
    for line in raw.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            lineno = int(m.group(1)) if m else 0
        elif line.startswith("+") and not line.startswith("+++"):
            out.append((path, lineno, line[1:]))
            lineno += 1
    return out


def scan(lines, term_rx, guards, include_self=True):
    """Return (path, lineno, gate, matched, severity, note)."""
    hits, in_fence = [], False
    for path, lineno, text in lines:
        if not include_self and is_self(path):
            continue
        if FENCE.match(text):
            in_fence = not in_fence
            continue

        allow = ALLOW.search(text)
        downgrade = None
        if allow:
            downgrade = f"allowed on this line: {allow.group('reason')}"
        elif in_fence:
            downgrade = "inside a fenced block, so probably an example rather than a use"

        checks = [("PRIVATE-TERM", term_rx, "Term from your private list.")] if term_rx else []
        checks += [(gid, rx, why) for gid, rx, why in PATTERN_GATES]

        for gid, rx, why in checks:
            for m in rx.finditer(text):
                if gid == "PRIVATE-TERM" and any(g.search(text) for g in guards):
                    continue
                hits.append((path, lineno, gid, m.group(0)[:48],
                             "info" if downgrade else "error",
                             downgrade or why))
    return hits


SELF_TERMS = "Acmecorp\nWidgetInc\n~widget factory\n"
SELF_DIFF = [
    ("a.md", 1, "Extracted from acmecorp/orgs/internal/."),          # 1 term, error
    ("a.md", 2, "The widget factory produces widgets."),             # guard suppresses WidgetInc
    ("a.md", 3, "WidgetInc is our client."),                         # 1 term, error
    ("a.md", 4, "See /Users/someone/notes.txt"),                     # abs path, error
    ("a.md", 5, "Token sk-AAAAAAAAAAAAAAAAAAAA here"),               # credential, error
    ("a.md", 6, "Nothing sensitive on this line at all."),           # clean
    ("a.md", 7, "grep Acmecorp  <!-- private-scan-allow: documents the gate -->"),  # downgraded
    ("a.md", 8, "```"),
    ("a.md", 9, "Acmecorp appears inside a fence"),                  # downgraded
    ("a.md", 10, "```"),
]


def self_test():
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as fh:
        fh.write(SELF_TERMS)
    terms, guards = load_terms(tmp)
    os.unlink(tmp)
    rx = build_term_rx(terms)
    hits = scan(SELF_DIFF, rx, guards)

    fail = []
    by_line = {}
    for _, ln, gid, _, sev, _ in hits:
        by_line.setdefault(ln, []).append((gid, sev))

    # BOTH BOUNDS. The gate must fire where it should AND stay quiet where it
    # should not. A gate proven only on dirty input can be one that fires on
    # everything, which is the same uselessness wearing the opposite face.
    expect = [
        (1, "error", "a private term must fire"),
        (3, "error", "a second private term must fire"),
        (4, "error", "an absolute path must fire"),
        (5, "error", "a credential-shaped string must fire"),
        (7, "info", "an allowed line downgrades, and is still reported"),
        (9, "info", "a fenced example downgrades, and is still reported"),
    ]
    for ln, sev, what in expect:
        got = by_line.get(ln, [])
        if not any(s == sev for _, s in got):
            fail.append(f"line {ln}: expected a {sev} hit ({what}), got {got or 'nothing'}")

    for ln, what in [(2, "an out-of-domain guard must suppress the innocent sense"),
                     (6, "a clean line must produce nothing")]:
        if by_line.get(ln):
            fail.append(f"line {ln}: expected no hit ({what}), got {by_line[ln]}")

    # Positive control on the term list itself: an empty list must be refused
    # rather than quietly scanning for nothing and reporting clean.
    fd, tmp = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as fh:
        fh.write("# only a comment\n")
    try:
        load_terms(tmp)
        fail.append("an empty term list was accepted, which would make the gate vacuous")
    except ValueError:
        pass
    finally:
        os.unlink(tmp)

    if fail:
        for f in fail:
            print(f"SELF-TEST FAILED: {f}")
        return 2
    errors = sum(1 for h in hits if h[4] == "error")
    print(f"self-test PASSED: {errors} error(s) and {len(hits) - errors} downgraded hit(s) "
          f"on the fixture, guard and clean lines silent, empty term list refused.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--terms", help="path to YOUR private term list. Without it only the "
                                    "pattern gates run, which is a partial check.")
    ap.add_argument("--diff", metavar="REF", help="diff ref, e.g. origin/main...HEAD. "
                                                  "Default: staged changes.")
    ap.add_argument("--paths", nargs="*", help="scan whole files instead of a diff. Expect "
                                               "pre-existing hits; this is not the gate mode.")
    ap.add_argument("--include-self", action="store_true",
                    help="gate copies of these scanners too. Off by default: their "
                         "self-test fixtures are made of deliberately dirty strings.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--timeout", type=int, default=30, metavar="SECONDS",
                    help="give up after this long and say which stage was in "
                         "flight. 0 disables. Default 30, which is about 300x "
                         "the slowest legitimate run measured.")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    started = time.time()
    # FIRST, before anything that can block. On a stalled mount this line is
    # the only thing the operator will ever see, and it is the difference
    # between "it is wedged reading the term list" and 120 seconds of nothing.
    where = args.diff or ("the working tree" if args.paths else "staged changes")
    print(f"private_scan: terms={args.terms or 'NONE'} target={where} "
          f"timeout={args.timeout or 'off'}s", flush=True)

    if not install_watchdog(args.timeout):
        if args.timeout:
            print("NOTE: no SIGALRM on this platform, so the run is NOT time-bounded.",
                  flush=True)

    term_rx, guards = None, []
    if args.terms:
        set_stage(f"reading the term list at {args.terms}")
        terms, guards = load_terms(args.terms)
        term_rx = build_term_rx(terms)
        if "example" in os.path.basename(args.terms):
            print("NOTE: running against the EXAMPLE term list, which names nobody. "
                  "Point --terms at your own list or the term gate is theatre.\n")
    else:
        print("NOTE: no --terms given, so only the pattern gates ran. The term gate "
              "is the one that catches client and colleague names.\n")

    t_terms = time.time()
    lines = added_lines(args.diff, args.paths, timeout=args.timeout or None)
    t_diff = time.time()
    set_stage(f"scanning {len(lines)} added line(s)")
    hits = scan(lines, term_rx, guards, include_self=args.include_self)
    t_scan = time.time()
    cancel_watchdog()
    errors = 0
    for path, lineno, gid, txt, sev, note in hits:
        if sev == "error":
            errors += 1
        print(f"  {path}:{lineno}: [{sev.upper():<5}] {gid:<14} {txt!r}")
        print(f"         {note}")

    if not hits:
        print("no hits.")
    print(f"\n{errors} error(s), {len(hits) - errors} downgraded, across {len(lines)} added line(s).")
    # Timings, so the next person who thinks this is slow reports WHERE rather
    # than that it hung. The archaeology this replaces took an hour.
    print(f"timing: terms {t_terms - started:.2f}s, diff {t_diff - t_terms:.2f}s, "
          f"scan {t_scan - t_diff:.2f}s")
    print("NOTE: this scans ADDED LINES ONLY. A clean run means you are not making")
    print("      it worse. It does not mean the repository is clean.")
    return 1 if errors else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except StageTimeout as exc:
        cancel_watchdog()
        # Exit 3, distinct from 1. "Found leaks" and "could not tell whether
        # there are leaks" are opposite results and must not share a code: a
        # caller that treats non-zero as dirty would report a stalled mount as
        # a private-data leak, and one that treats only 1 as dirty would let a
        # timed-out run pass for clean.
        print(f"\nTIMED OUT while: {exc}", file=sys.stderr)
        print("This is almost never the scanning, which is fast. It is a blocked read.\n"
              "Check whether the term list, the scanner itself, or the repository sits\n"
              "on a network or cloud-sync mount, which can stall for minutes on a cold\n"
              "open. Keep all three on local disk. Raise --timeout only after you know\n"
              "what was slow, never to make this message go away.", file=sys.stderr)
        sys.exit(3)
