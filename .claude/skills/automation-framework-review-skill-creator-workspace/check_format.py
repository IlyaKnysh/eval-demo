"""Structural checks for a framework-review output dir.

Usage: python check_format.py <outputs_dir>
Prints JSON with: impact/effort tag stats, FIRST table presence, checklist table columns/rows.
"""
import json
import re
import sys
from pathlib import Path

LEGAL = {"High", "Medium", "Low"}
TAG_RE = re.compile(r"\[Impact:\s*([^|\]]+?)\s*\|\s*Effort:\s*([^\]]+?)\s*\]")
NON_FINDING = re.compile(
    r"(?i)verdict|FIRST|recommended|checklist|summary|scope|method|appendix|assumption|overview|contents"
)
FIRST_LETTERS = ["Fast", "Independent", "Repeatable", "Self-validating", "Timely"]


def heading_findings(text):
    """Level-2+ headings that look like individual findings, with whether a tag follows within 2 lines."""
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines):
        if re.match(r"^#{2,5}\s+\S", line) and not NON_FINDING.search(line):
            window = "\n".join(lines[i:i + 3])
            out.append({"line": i + 1, "heading": line.strip()[:120], "tagged": bool(TAG_RE.search(window))})
    return out


def first_letters(text):
    table_lines = [l.replace("*", "") for l in text.splitlines() if l.lstrip().startswith("|")]
    found = []
    for letter in FIRST_LETTERS:
        pat = re.compile(r"\b" + re.escape(letter) + r"\b", re.I)
        if any(pat.search(l) for l in table_lines):
            found.append(letter)
    return found


def check(outputs_dir):
    d = Path(outputs_dir)
    review = d / "review.md"
    res = {"outputs_dir": str(d), "files": sorted(p.name for p in d.iterdir())}
    if not review.exists():
        res["error"] = "review.md missing"
        return res
    text = review.read_text(encoding="utf-8", errors="replace")
    tags = TAG_RE.findall(text)
    illegal = [f"{i}|{e}" for i, e in tags if i not in LEGAL or e not in LEGAL]
    heads = heading_findings(text)
    res["review_lines"] = len(text.splitlines())
    res["impact_effort_tags"] = len(tags)
    res["illegal_tag_values"] = illegal
    res["finding_headings"] = len(heads)
    res["untagged_finding_headings"] = [h["heading"] for h in heads if not h["tagged"]]
    res["first_table_letters_found"] = first_letters(text)
    res["placeholder_phrases"] = re.findall(r"(?i)no (?:violations|issues) found|verified strength", text)

    combined = text
    cl = d / "checklist.md"
    if cl.exists():
        combined = cl.read_text(encoding="utf-8", errors="replace") + "\n" + text
    hdr = re.search(r"^\|\s*Section\s*\|\s*Check\s*\|\s*Status[^|]*\|\s*Comments\s*\|", combined, re.M)
    res["checklist_header_found"] = bool(hdr)
    if hdr:
        rows = []
        for line in combined[hdr.end():].splitlines()[1:]:
            if not line.startswith("|"):
                if rows:
                    break
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3 and not set(cells[0]) <= set("-: "):
                rows.append({"section": cells[0], "check": cells[1][:90], "status": cells[2]})
        res["checklist_rows"] = len(rows)
        res["checklist_status_values"] = sorted({r["status"] for r in rows})
        res["checklist_minus_rows"] = [r["check"] for r in rows if r["status"].strip("`* ") == "-"]
    return res


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(check(sys.argv[1]), indent=2, ensure_ascii=False))
