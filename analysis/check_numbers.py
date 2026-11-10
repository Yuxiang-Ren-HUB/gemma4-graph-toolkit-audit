"""Deterministic post-hoc check: every numeric token in the final draft must
appear in the material files (material_facts.md / references_for_paper.md /
requirements.md).  Catches invented counts/percentages; cannot catch a
material number used in the wrong place (that is the reviewer's job).

Usage: python check_numbers.py <draft.md>
"""

import re
import sys
import os

MATERIAL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "material")

NUM_RX = re.compile(r"\d+(?:[.,]\d+)*")
# tokens that never need material backing
WHITELIST = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10"}  # section/table/ref numbers


def numbers_in(text: str) -> list[str]:
    return NUM_RX.findall(text)


def main():
    draft_path = sys.argv[1]
    draft = open(draft_path, encoding="utf-8").read()
    material = ""
    for name in os.listdir(MATERIAL_DIR):
        if name.endswith(".md"):
            material += open(os.path.join(MATERIAL_DIR, name), encoding="utf-8").read()
    mat_nums = set(numbers_in(material))
    # also accept comma-less variants of material numbers (452,588 vs 452588)
    mat_nums |= {n.replace(",", "") for n in mat_nums}

    missing = {}
    for n in numbers_in(draft):
        plain = n.replace(",", "")
        if n in WHITELIST or plain in WHITELIST:
            continue
        if n in mat_nums or plain in mat_nums:
            continue
        missing[n] = missing.get(n, 0) + 1

    total = len(numbers_in(draft))
    print(f"draft numeric tokens: {total}; unmatched: {sum(missing.values())}")
    for n, cnt in sorted(missing.items()):
        # show one context line per unmatched number
        for line in draft.splitlines():
            if n in line:
                print(f"  UNMATCHED {n} (x{cnt}): {line.strip()[:140]}")
                break
    if not missing:
        print("OK: every number in the draft is backed by the material files.")


if __name__ == "__main__":
    main()
