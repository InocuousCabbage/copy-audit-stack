#!/usr/bin/env python3
"""
family_check.py: assert the scanners in this repo stay structurally consistent.

WHY THIS EXISTS, because the reason is the whole design.

A bug was found in extract_copy_strings.py: pointed at a repo that vendored it,
the gate fired 83 times on the scanners' own docstrings, failing the very PR
that installed it. It was fixed there. Its sibling copy_scan.py had the
identical defect and was not fixed, because the reported instance was fixed
instead of the class being swept.

"When you fix a bug, sweep for its class before closing" was already a held
rule, written down in prose, and it did not fire. That is the same failure mode
as a scanner rule that lives in a document instead of in code: it depends on
someone remembering, and remembering degrades. The fix for a prose rule that
needs vigilance is to encode it, so this is the encoding.

WHAT IT ASSERTS

  1. Every scanner exposes --self-test, and it passes.
  2. Every scanner declares a FAMILY_CONTRACT.
  3. Every contract answers the questions the family has had to answer, with a
     stated reason rather than a bare boolean.
  4. Every scanner tells the reader that a clean run is not a pass.

Point 2 is the load-bearing one. The check fails on a MISSING declaration, not
on a False one. A sibling is free to opt out of skip-self, and structural_scan
does exactly that, but it cannot opt out by silence. Divergence has to be
argued in the file where someone reading it will see the argument.

Usage:
    python3 scripts/family_check.py
Exit 0 if the family is consistent, 1 if not.
"""

import argparse
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Located by NAME under the repo root, not by a hardcoded path. The skills
# directory sits at skills/ in this repo and at .claude/skills/ when the stack is
# installed into a project, and a check that only works in one layout silently
# reports "missing from the repo" in the other. That is a false divergence, which
# is the failure this tool exists to prevent, so it must not be the tool's own
# behaviour. Verified by running it in both layouts rather than reasoning about
# them: the hardcoded version passed here and failed there.
SCANNER_NAMES = ["copy_scan.py", "extract_copy_strings.py", "structural_scan.py"]
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}


def find_scanners(root):
    found = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in SCANNER_NAMES:
            if name in filenames and name not in found:
                found[name] = os.path.join(dirpath, name)
    return [found.get(n) or n for n in SCANNER_NAMES]


SCANNERS = find_scanners(ROOT)

REQUIRED_CONTRACT_KEYS = {"skip_self", "skip_self_reason", "clean_scan_caveat"}

# Deliberately loose. An earlier version of this check grepped for one exact
# phrasing of the caveat and reported a false divergence on a file that carried
# it in different words. That is the prose-rule-versus-regex-rule mistake, made
# inside the tool built to prevent that mistake. Match the concept.
CAVEAT_MARKERS = ("not a pass", "does not mean", "not mean that", "is not a pass")


def load(path):
    spec = importlib.util.spec_from_file_location(f"_fam_{os.path.basename(path)}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--require-all", action="store_true",
                    help="treat a missing scanner as a failure. Off by default because a "
                         "partial vendor is a legitimate deployment: a project may install "
                         "only the scanners it needs. Use this in the canonical repo, where "
                         "an absent sibling really is a problem.")
    args = ap.parse_args()

    failures = []
    present, absent = [], []
    for path in SCANNERS:
        name = os.path.basename(path)
        if not os.path.exists(path):
            absent.append(name)
            if args.require_all:
                failures.append(f"{name}: missing, and --require-all was passed")
            continue
        present.append(name)

        r = subprocess.run([sys.executable, path, "--self-test"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            failures.append(f"{name}: --self-test exited {r.returncode}")

        try:
            mod = load(path)
        except Exception as exc:
            failures.append(f"{name}: could not import ({exc})")
            continue

        contract = getattr(mod, "FAMILY_CONTRACT", None)
        if contract is None:
            failures.append(
                f"{name}: no FAMILY_CONTRACT. Every scanner must declare where it "
                f"stands on the questions this family has already had to answer, "
                f"so a fix to one sibling cannot silently skip another.")
            continue

        missing = REQUIRED_CONTRACT_KEYS - set(contract)
        if missing:
            failures.append(f"{name}: FAMILY_CONTRACT missing {sorted(missing)}")
        if not str(contract.get("skip_self_reason", "")).strip():
            failures.append(f"{name}: skip_self_reason is empty. State the reason, "
                            f"a bare boolean does not survive the next reader.")

        src = open(path, encoding="utf-8").read().lower()
        if contract.get("clean_scan_caveat") and not any(m in src for m in CAVEAT_MARKERS):
            failures.append(f"{name}: claims clean_scan_caveat but no such caveat "
                            f"appears in the file")

        print(f"  {name}: self-test ok, contract "
              f"skip_self={contract.get('skip_self')} "
              f"({contract.get('skip_self_reason', '')[:60]})")

    if absent and not args.require_all:
        print(f"\n  not installed here, skipped: {', '.join(absent)}")
        print("  (a partial install is fine; this checks consistency among what is present)")
    if not present:
        print("\nFAMILY CHECK FAILED: found none of the scanners at all.")
        return 1
    if failures:
        print("\nFAMILY CHECK FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"\nfamily check PASSED: {len(present)} scanner(s) consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
