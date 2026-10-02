"""Deterministic (non-LLM) checks for the automation-framework-review-deepeval skill.

These complement the GEval-based suite in `test_automation_framework_review.py`
with plain string/regex/structure assertions against each fixture's ground
truth (`additional_metadata` in `.dataset.json`). No model call, no judge —
same input always gives the same pass/fail, so this is the fast, free,
CI-safe layer to run on every commit. The GEval suite stays for the
subjective judgments (evidence quality, tone, prose discipline) that can't be
reduced to a keyword check.
"""

import json
import os
import re

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.normpath(os.path.join(HERE, "..", "outputs"))

# Deliberately looser than REQUIRED_STRUCTURE_HEADINGS: these only decide where
# the findings section ends. A shortened title ("## FIRST principles") should
# fail the one structure test that names it, not also turn the FIRST table into
# an untagged "finding" and cascade into the tag-count/placement tests.
FIXED_TRAILING_HEADINGS = (
    "FIRST principles",
    "Recommended actions",
    "Checklist tab input",
)

REQUIRED_STRUCTURE_HEADINGS = [
    "FIRST principles table",
    "Recommended actions",
    "Checklist tab input",
]

CHECKLIST_HEADER_RE = re.compile(
    r"\|\s*Section\s*\|\s*Check\s*\|\s*Status\s*\(\+/-\)\s*\|\s*Comments\s*\|"
)

# The findings section ends at the FIRST-principles *heading*. Anchoring on the
# bare phrase instead matches the heading text three characters late, leaving an
# orphaned "## " fragment at the slice boundary that then reads as an untitled
# heading. Match the heading line itself.
FIRST_TABLE_HEADING_RE = re.compile(
    r"^#{2,3}\s+.*FIRST principles\b", re.MULTILINE | re.IGNORECASE
)


def _findings_section(review: str) -> str:
    """Everything before the FIRST-principles table heading."""
    match = FIRST_TABLE_HEADING_RE.search(review)
    return review[: match.start()] if match else review


# Only the three values SKILL.md defines are legal.
IMPACT_EFFORT_TAG_RE = re.compile(
    r"\[Impact:\s*(High|Medium|Low)\s*\|\s*Effort:\s*(High|Medium|Low)\]", re.IGNORECASE
)

# Any tag at all, whatever it puts in the value slots. Matching this but not
# IMPACT_EFFORT_TAG_RE means the finding *is* tagged but used a value outside
# the High/Medium/Low vocabulary (observed: "Medium-High"). That is a real
# rubric violation and should be reported as such, not silently counted as a
# missing tag — the two failures have completely different fixes.
ANY_IMPACT_EFFORT_TAG_RE = re.compile(
    r"\[Impact:\s*([^|\]]+?)\s*\|\s*Effort:\s*([^\]]+?)\]", re.IGNORECASE
)


def _load_goldens():
    with open(os.path.join(HERE, ".dataset.json"), encoding="utf-8") as f:
        return json.load(f)


def _load_review(scenario: str) -> str:
    path = os.path.join(OUTPUTS_DIR, "%s.md" % scenario)
    if not os.path.exists(path):
        pytest.skip("No generated review at %s" % path)
    with open(path, encoding="utf-8") as f:
        return f.read()


def _finding_headings(review: str):
    """Headings between the verdict block and the fixed trailing sections."""
    headings = re.findall(r"^#{2,3}\s+(.+)$", review, flags=re.MULTILINE)
    return [
        h for h in headings
        if not any(fixed.lower() in h.lower() for fixed in FIXED_TRAILING_HEADINGS)
    ]


GOLDENS = _load_goldens()


@pytest.mark.parametrize("golden", GOLDENS, ids=[g["name"] for g in GOLDENS])
def test_required_document_structure(golden):
    review = _load_review(golden["additional_metadata"]["scenario"])
    headings = [h.strip().lower() for h in re.findall(r"^#{2,3}\s+(.+)$", review, flags=re.MULTILINE)]
    missing = [
        name for name in REQUIRED_STRUCTURE_HEADINGS
        if not any(h.startswith(name.lower()) for h in headings)
    ]
    assert not missing, (
        "Missing required section heading(s) %s — SKILL.md requires these titles "
        "verbatim. Headings found: %s" % (missing, headings)
    )


@pytest.mark.parametrize("golden", GOLDENS, ids=[g["name"] for g in GOLDENS])
def test_checklist_table_has_required_columns(golden):
    review = _load_review(golden["additional_metadata"]["scenario"])
    assert CHECKLIST_HEADER_RE.search(review), (
        "Checklist tab input table missing or missing the exact "
        "'Section | Check | Status (+/-) | Comments' header"
    )


@pytest.mark.parametrize("golden", GOLDENS, ids=[g["name"] for g in GOLDENS])
def test_every_finding_has_impact_effort_tag(golden):
    review = _load_review(golden["additional_metadata"]["scenario"])
    findings = _finding_headings(review)
    if not findings:
        pytest.skip("No findings in this review (expected for an all-clean fixture)")

    # A tag should appear once per finding; count tags found anywhere in the
    # findings section (before the FIRST-principles table) rather than tying
    # each to its exact heading, since prose wrapping varies.
    findings_section = _findings_section(review)
    tags = IMPACT_EFFORT_TAG_RE.findall(findings_section)
    all_tags = ANY_IMPACT_EFFORT_TAG_RE.findall(findings_section)

    # Separate "no tag" from "tag with an off-vocabulary value" — same symptom
    # under a strict-only regex, different defects.
    legal = {"high", "medium", "low"}
    bad_values = [
        "[Impact: %s | Effort: %s]" % (impact, effort)
        for impact, effort in all_tags
        if impact.strip().lower() not in legal or effort.strip().lower() not in legal
    ]
    assert not bad_values, (
        "Impact/Effort tag(s) use values outside the High/Medium/Low vocabulary "
        "SKILL.md defines: %s" % bad_values
    )

    assert len(tags) >= len(findings), (
        "Found %d finding heading(s) but only %d [Impact|Effort] tag(s) — "
        "every finding must carry one" % (len(findings), len(tags))
    )


@pytest.mark.parametrize("golden", GOLDENS, ids=[g["name"] for g in GOLDENS])
def test_seeded_defects_are_mentioned(golden):
    meta = golden["additional_metadata"]
    must_mention_any = meta.get("must_mention_any")
    if not must_mention_any:
        pytest.skip("No seeded defects to check for this fixture")

    review = _load_review(meta["scenario"])
    review_lower = review.lower()

    missing = []
    for keyword_group in must_mention_any:
        if not any(re.search(kw, review_lower, re.IGNORECASE) for kw in keyword_group):
            missing.append(keyword_group)

    assert not missing, (
        "Review is missing mention of %d/%d seeded defect(s), none of these "
        "keyword groups matched: %s"
        % (len(missing), len(must_mention_any), missing)
    )


@pytest.mark.parametrize("golden", GOLDENS, ids=[g["name"] for g in GOLDENS])
def test_clean_practice_files_not_named_in_findings(golden):
    meta = golden["additional_metadata"]
    must_not_mention = meta.get("must_not_mention_as_finding")
    if not must_not_mention:
        pytest.skip("No clean-practice guardrails to check for this fixture")

    review = _load_review(meta["scenario"])
    findings_section = _findings_section(review)

    # Heuristic false-positive guard: a clean-practice filename should not
    # appear as the subject of a finding heading. It's fine for the name to
    # appear in prose elsewhere (e.g. cited as the *good* example to follow).
    finding_headings_text = "\n".join(_finding_headings(findings_section))
    hits = [name for name in must_not_mention if name.lower() in finding_headings_text.lower()]
    assert not hits, (
        "Clean-practice file(s) named directly in a finding heading — likely "
        "a false positive: %s" % hits
    )


@pytest.mark.parametrize("golden", GOLDENS, ids=[g["name"] for g in GOLDENS])
def test_finding_count_within_expected_bounds(golden):
    meta = golden["additional_metadata"]
    review = _load_review(meta["scenario"])
    count = len(_finding_headings(review))

    max_findings = meta.get("max_findings")
    min_findings = meta.get("min_findings")

    if max_findings is not None:
        assert count <= max_findings, (
            "Expected at most %d finding(s) for a deliberately clean fixture, "
            "got %d — likely inventing findings on clean dimensions"
            % (max_findings, count)
        )
    if min_findings is not None:
        assert count >= min_findings, (
            "Expected at least %d finding(s) given the seeded defect count, "
            "got %d — likely under-reporting" % (min_findings, count)
        )


@pytest.mark.parametrize("golden", GOLDENS, ids=[g["name"] for g in GOLDENS])
def test_recommended_actions_reference_tagged_findings(golden):
    review = _load_review(golden["additional_metadata"]["scenario"])
    actions_match = re.search(
        r"##\s*Recommended actions(.*?)(?=\n##\s|\Z)", review, re.DOTALL | re.IGNORECASE
    )
    if actions_match is None:
        pytest.skip("No Recommended actions section found (covered by structure test)")

    actions_section = actions_match.group(1)
    findings = _finding_headings(review)
    if not findings:
        pytest.skip("No findings to roll up (expected for an all-clean fixture)")

    # The rollup should be non-trivial (not just a restatement of the verdict)
    # and should carry its own [Impact|Effort] tags per the skill's rule that
    # it's a mechanical rollup of already-tagged findings, not a fresh list.
    action_items = re.findall(r"^\s*\d+\.\s", actions_section, re.MULTILINE)
    assert action_items, "Recommended actions section has no numbered items"


# --- Checks pulled down from the GEval suite -------------------------------
# These were previously graded by a judge as part of DocumentStructure,
# ChecklistTableFidelity and SeverityTagging. They are mechanical, so a regex
# decides them exactly and for free; the judge now only grades the genuinely
# subjective remainder (heading specificity, tag plausibility, evidence
# quality). Each check below replaces one bullet of a GEval criteria string.


def _checklist_rows(review: str):
    """Body rows of the 'Checklist tab input' table, as split cell lists."""
    pos = review.lower().find("checklist tab input")
    if pos == -1:
        return []
    rows = []
    for line in review[pos:].splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0].lower() == "section" or set(cells[0]) <= {"-", ":", " "}:
            continue
        rows.append(cells)
    return rows


@pytest.mark.parametrize("golden", GOLDENS, ids=[g["name"] for g in GOLDENS])
def test_checklist_status_is_bare_plus_or_minus(golden):
    review = _load_review(golden["additional_metadata"]["scenario"])
    rows = _checklist_rows(review)
    if not rows:
        pytest.skip("No checklist rows found (covered by the header test)")

    bad = [
        "%s / %s -> %r" % (r[0], r[1], r[2])
        for r in rows
        if r[2].strip().strip("`") not in {"+", "-"}
    ]
    assert not bad, (
        "Checklist Status must be a bare '+' or '-' (never 'partial', 'N/A' "
        "or prose): %s" % bad
    )


@pytest.mark.parametrize("golden", GOLDENS, ids=[g["name"] for g in GOLDENS])
def test_checklist_omits_out_of_scope_sections(golden):
    review = _load_review(golden["additional_metadata"]["scenario"])
    rows = _checklist_rows(review)
    if not rows:
        pytest.skip("No checklist rows found (covered by the header test)")

    # SKILL.md: Tools / Strategy / AI Usage are questionnaire territory and a
    # code review must not guess a Status for them.
    out_of_scope = {"tools", "strategy", "ai usage"}
    hits = sorted({r[0] for r in rows if r[0].strip().lower() in out_of_scope})
    assert not hits, (
        "Checklist contains rows from section(s) a code review cannot answer: "
        "%s" % hits
    )


@pytest.mark.parametrize("golden", GOLDENS, ids=[g["name"] for g in GOLDENS])
def test_impact_effort_tag_follows_its_heading(golden):
    """The tag must sit immediately after the heading, not after the body.

    SKILL.md puts the tag 'immediately after its heading/bullet' so a reader
    scanning headings sees the severity without reading the finding. A tag
    parked at the end of a multi-paragraph body is a different document.
    """
    review = _load_review(golden["additional_metadata"]["scenario"])
    section = _findings_section(review)

    lines = section.splitlines()
    heading_idx = [
        i for i, ln in enumerate(lines)
        if re.match(r"^#{2,3}\s+", ln)
        and not any(f.lower() in ln.lower() for f in FIXED_TRAILING_HEADINGS)
    ]
    if not heading_idx:
        pytest.skip("No findings in this review")

    # Allow a blank line and a short lead-in, but not a whole finding body. The
    # heading line itself counts: a tag at the end of the heading is even more
    # visible to a reader scanning headings than one on the next line.
    MAX_LINES_AFTER_HEADING = 3
    late = []
    for i in heading_idx:
        window = lines[i : i + 1 + MAX_LINES_AFTER_HEADING]
        if not any(IMPACT_EFFORT_TAG_RE.search(ln) for ln in window):
            late.append(lines[i].lstrip("# ").strip())

    assert not late, (
        "%d finding(s) place their [Impact|Effort] tag more than %d lines "
        "after the heading, instead of immediately after it: %s"
        % (len(late), MAX_LINES_AFTER_HEADING, late)
    )


# The checklist rows a code review may answer, copied from SKILL.md's
# "Checklist-tab mapping" table. The Tools/Strategy/AI Usage sections are
# covered by test_checklist_omits_out_of_scope_sections; this guards the other
# direction: a row that isn't on the checklist at all.
CHECKLIST_ROWS = {
    "framework": [
        "Framework is consistent",
        "Framework follows a layered architecture",
        "Framework complies with DRY",
        "Framework complies with KISS",
        "Framework complies with YAGNI",
        "Framework complies with SOLID",
        "Framework complies with language standards",
        "Presetups are implemented at the optimal available level",
        "Unconditional waits are not a common practice",
        "Tests are atomic and independent",
        "Tests remain independent under parallel execution",
        "Test implementation is done at the optimal level (API, UI...)",
        "Core libraries/framework/language versions are reasonably current",
        "No hardcoded credentials/secrets in the test codebase",
    ],
    "running": [
        "Steps have a sufficient level of documentation for reporting",
        "When tests fail, there are mechanisms to easily find the cause",
        "Test stability is at a sufficient level",
        "There is a way to track run results over time",
        "Tests are integrated into CI/CD, not run purely manually/on-demand",
    ],
    "processes": [
        "Tests are properly documented",
        "A failure-handling strategy is implemented",
    ],
}


@pytest.mark.parametrize("golden", GOLDENS, ids=[g["name"] for g in GOLDENS])
def test_checklist_rows_exist_on_the_checklist(golden):
    review = _load_review(golden["additional_metadata"]["scenario"])
    rows = _checklist_rows(review)
    if not rows:
        pytest.skip("No checklist rows found (covered by the header test)")

    def known(section: str, check: str) -> bool:
        check = check.strip().lower()
        # Prefix match either way: the long failure-handling row may be
        # shortened, and a longer comment-style wording still starts with the row.
        return any(
            check.startswith(c.lower()) or c.lower().startswith(check)
            for c in CHECKLIST_ROWS.get(section.strip().lower(), [])
        )

    invented = ["%s / %s" % (r[0], r[1]) for r in rows if not known(r[0], r[1])]
    assert not invented, (
        "Checklist row(s) that are not on the checklist (invented section or "
        "reworded check; SKILL.md says to copy them from its mapping table): %s"
        % invented
    )
