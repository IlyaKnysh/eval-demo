"""Eval suite for the automation-framework-review-deepeval skill.

The skill (.claude/skills/automation-framework-review-deepeval/SKILL.md) is not a live
service — it's a Claude Code skill that an agent loads to review a target
repo and write a Markdown findings document. There is no traceable app
entry point to call live during `deepeval test run`, so this suite grades
review documents in `evals/outputs/<scenario>.md` against each fixture's
seeded-defect manifest (ground truth for what must/must not be found).

If an output file is missing or blank, `conftest.py`'s
`pytest_collection_modifyitems` hook generates it automatically before tests
run, via a one-shot non-interactive `claude -p` call (tools: Read/Grep/Glob,
no subagents, see `_generate_output`) — this is a best-effort stand-in for a
real interactive skill session, not an equivalent replacement, since it has
no subagent delegation and runs the whole review in one pass. For a review
that matches what an actual Claude Code session would produce, run the skill
yourself against `evals/fixtures/<scenario>/` and save the Markdown to
`evals/outputs/<scenario>.md` before running pytest — an existing file is
graded as-is and never regenerated or deleted automatically.
"""

import json
import os

import pytest

from deepeval import assert_test
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.test_case import LLMTestCase

from metrics import metrics_for

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_EVALS_DIR = os.path.normpath(os.path.join(HERE, ".."))
OUTPUTS_DIR = os.path.join(SKILL_EVALS_DIR, "outputs")

dataset = EvaluationDataset()
dataset.add_goldens_from_json_file(file_path=os.path.join(HERE, ".dataset.json"))


def _load_actual_output(golden: Golden) -> str:
    scenario = golden.additional_metadata["scenario"]
    output_path = os.path.join(OUTPUTS_DIR, "%s.md" % scenario)
    if not os.path.exists(output_path):
        pytest.skip(
            "No review found at %s and auto-generation didn't produce one "
            "(conftest.py's pytest_collection_modifyitems hook skips "
            "silently if the `claude` CLI isn't on PATH or the subprocess "
            "call failed/timed out — check GENERATION_TIMEOUT_SECONDS and "
            "that `claude` is installed/authenticated). To get a review "
            "that matches a real interactive session, run the "
            "automation-framework-review-deepeval skill yourself against "
            "evals/fixtures/%s/ and save its output there."
            % (output_path, scenario)
        )
    with open(output_path, encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize("golden", dataset.goldens)
def test_automation_framework_review(golden: Golden):
    actual_output = _load_actual_output(golden)
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=actual_output,
        expected_output=golden.expected_output,
    )
    assert_test(
        test_case=test_case,
        metrics=metrics_for(golden.additional_metadata.get("ground_truth_type")),
    )
