"""Metrics for the automation-framework-review-deepeval skill eval suite.

The skill under test is a Claude Code skill (SKILL.md), not a live service:
its input is a target repo and its output is a Markdown findings document
(plus a secondary checklist-tab table). There is no tracing/tool-call data to
grade, so every metric here is a single-turn GEval scored on the saved
Markdown document as `actual_output`, with the fixture's seeded-defect
manifest folded into `input`/`expected_output` as the reference.

**Each judge grades one question, and only what a regex cannot decide.**
Everything mechanical — required headings, checklist columns, `+`/`-` status
values, out-of-scope checklist sections, tag presence, tag vocabulary, tag
placement, finding counts, numbered actions — now lives in
`test_automation_framework_review_deterministic.py`, where it is exact, free
and instant. A judge asked to check a regex-decidable rule alongside a
subjective one tends to average the two into a middling score that names the
mechanical miss and buries the interesting one, which is the opposite of what
the suite is for. So the criteria below deliberately say nothing about format.

The judge model is the local Claude Code CLI (see `claude_code_model.py`)
rather than a metered provider API key, so grading rides on the existing
Claude Code session/subscription. Swap `JUDGE_MODEL` for a `deepeval
set-anthropic`-configured default (pass `model=None` to each GEval below) if
CLI-based grading proves too slow/fragile for a given run.
"""

from deepeval.metrics import GEval
from deepeval.test_case import SingleTurnParams

from claude_code_model import ClaudeCodeModel

JUDGE_MODEL = ClaudeCodeModel(model="sonnet")

EVIDENCE_QUALITY = GEval(
    name="EvidenceQuality",
    criteria=(
        "Judge only whether each finding's evidence actually supports its claim. "
        "A finding should cite concrete `file:line` locations and real counts or "
        "ratios (e.g. '13 of 17 files', '24 duplicated methods') rather than vague "
        "impressions like 'some tests are hard to read'. Beyond mere presence, "
        "check that the cited evidence is specific enough for a reader to verify "
        "the claim without re-auditing the repo, and that a quantitative claim is "
        "backed by a real count rather than an unsupported number. A number that "
        "contradicts another number for the same quantity elsewhere in the "
        "document (e.g. '13 of 15' in one place, '12 of 15' in another) is a "
        "serious evidence failure. The FIRST-principles and checklist-tab rows "
        "are one-line summary pointers by design: do not penalise them for "
        "omitting the file list behind a ratio or a zero-match grep, only for a "
        "figure that conflicts with the findings. "
        "Headings, tags and ordering are graded elsewhere — ignore them."
    ),
    evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT],
    model=JUDGE_MODEL,
    threshold=0.7,
)

DEFECT_RECALL = GEval(
    name="SeededDefectRecall",
    criteria=(
        "The input lists the defects deliberately seeded into the target repo "
        "(ground truth). Judge only whether the review surfaces each one in "
        "substance, under any heading or wording. Penalize heavily for a seeded "
        "defect that is entirely absent. Do not penalize extra findings, do not "
        "require matching wording, and do not grade formatting."
    ),
    evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
    model=JUDGE_MODEL,
    threshold=0.7,
)

FALSE_POSITIVE_DISCIPLINE = GEval(
    name="FalsePositiveDiscipline",
    criteria=(
        "The input lists practices the target repo deliberately got right, which "
        "must NOT be reported as problems. Judge two things and nothing else.\n"
        "(1) Invented findings: does the review flag, as a defect, any dimension "
        "the input declares clean? Read the input's clean claim precisely and "
        "compare it to what the finding actually asserts — if the review reports "
        "a real, separate defect the clean claim does not cover, that is correct "
        "behaviour and must not be penalized.\n"
        "(2) Clean-verdict fluff: the skill's no-fluff rule allows a clean verdict "
        "in exactly two places, the FIRST-principles table and the checklist-tab "
        "table. Anywhere else — a heading, a 'no violations found' note, a "
        "'verified strength' writeup, or praise in the opening verdict paragraph "
        "such as 'the layering and waiting strategy all hold up' — is a violation, "
        "however true the statement is. One exception, which the skill allows "
        "explicitly: naming the clean part of the codebase as the denominator or "
        "contrast for a defect in the same sentence or the one right after it, "
        "with no evaluative adjective (e.g. '4 of 9 test classes import raw "
        "WebElement; the other 5 do not, which is what makes the 4 a violation "
        "rather than the established pattern'). That is evidence for the "
        "finding, not a clean verdict, and must not be penalized. It becomes "
        "fluff once it praises (calls the clean part correct, proper, solid, "
        "legitimate, a template) or once it stands alone without a defect it "
        "explains.\n"
        "Ignore headings, tags, ordering and table formatting."
    ),
    evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
    model=JUDGE_MODEL,
    threshold=0.7,
)

AUTOMATION_FRAMEWORK_REVIEW_METRICS = [
    EVIDENCE_QUALITY,
    DEFECT_RECALL,
    FALSE_POSITIVE_DISCIPLINE,
]


def metrics_for(ground_truth_type: str):
    """The metric set that actually applies to a fixture.

    `SeededDefectRecall` grades "did the review find the planted defects",
    which is meaningless on an all-clean fixture: there are none to find, and
    its golden carries no `must_mention_any`. Left in, the judge hunts the
    prose input for something defect-shaped, latches onto the manifest's one
    explicitly-optional enhancement note (the missing WebKit project), and
    scores the skill down for omitting a finding the ground truth says is
    *not* required. The deterministic suite already skips this case; mirror
    that here instead of grading against an invented requirement.
    """
    if ground_truth_type == "all-clean":
        return [m for m in AUTOMATION_FRAMEWORK_REVIEW_METRICS if m is not DEFECT_RECALL]
    return AUTOMATION_FRAMEWORK_REVIEW_METRICS
