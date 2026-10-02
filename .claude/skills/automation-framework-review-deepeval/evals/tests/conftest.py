"""Shared pytest config for the eval suite.

The judge model (ClaudeCodeModel) shells out to the `claude` CLI per metric
call (up to 180s each, see claude_code_model.py). deepeval's own outer
per-test-case gather budget defaults to ~180s + a ~27s buffer, which is too
tight even with metrics running concurrently (asyncio.to_thread) if a CLI
cold start is slow. Widen both before any test collects.

A review is generated only when its `outputs/<scenario>.md` is missing or
blank; an existing one is graded as-is and never deleted. A saved review
records nothing about the SKILL.md or fixture revision that produced it, so
after changing either, delete the affected `.md` yourself to get a fresh one.
"""

import os
import shutil
import subprocess


os.environ.setdefault("DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE", "600")
os.environ.setdefault("DEEPEVAL_TASK_GATHER_BUFFER_SECONDS_OVERRIDE", "60")

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_EVALS_DIR = os.path.normpath(os.path.join(HERE, ".."))
SKILL_DIR = os.path.normpath(os.path.join(SKILL_EVALS_DIR, ".."))
# .claude/skills/<skill> -> repo root. The review subprocess runs from here so
# the repo-relative fixture paths in .dataset.json stay valid.
REPO_ROOT = os.path.normpath(os.path.join(SKILL_DIR, "..", "..", ".."))
SKILL_MD_PATH = os.path.join(SKILL_DIR, "SKILL.md")
FIXTURES_DIR = os.path.join(SKILL_EVALS_DIR, "fixtures")
OUTPUTS_DIR = os.path.join(SKILL_EVALS_DIR, "outputs")

# Generous: this is a full agentic review pass (multi-dimension file reading
# and synthesis) crammed into a single non-interactive `claude -p` call with
# no subagent delegation, so it runs slower and shallower than an interactive
# skill invocation would. Treat auto-generated outputs as a best-effort stand
# -in for a real session-run review, not an equivalent replacement.
GENERATION_TIMEOUT_SECONDS = 1200

SCENARIOS = ("clean-framework", "messy-framework", "medium-framework")


def _generate_output(scenario: str) -> None:
    output_path = os.path.join(OUTPUTS_DIR, "%s.md" % scenario)
    fixture_path = os.path.join(FIXTURES_DIR, scenario)
    if not os.path.isdir(fixture_path):
        return  # nothing to review; the test itself will skip

    cli_path = shutil.which("claude")
    if cli_path is None:
        return  # no CLI on PATH; fall back to the test's own skip behavior

    with open(SKILL_MD_PATH, encoding="utf-8") as f:
        skill_instructions = f.read()

    prompt = (
        "Follow these skill instructions to review the target repo below, "
        "then output ONLY the final Markdown review document (the issues "
        "list plus its FIRST-principles table, Recommended actions, and "
        "Checklist tab input sections) with no other commentary before or "
        "after it.\n\n"
        "--- SKILL INSTRUCTIONS ---\n%s\n--- END SKILL INSTRUCTIONS ---\n\n"
        "Target repo to review: %s\n"
        "(This is a one-shot non-interactive run: read the files under that "
        "path directly and synthesize the review yourself; there are no "
        "subagents available in this call.)"
        % (skill_instructions, fixture_path)
    )

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    result = subprocess.run(
        [
            cli_path,
            "-p",
            "--output-format",
            "text",
            "--model",
            "sonnet",
            "--tools",
            "Read,Grep,Glob",
            "--add-dir",
            fixture_path,
        ],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=GENERATION_TIMEOUT_SECONDS,
        encoding="utf-8",
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        # Don't fail collection over a generation hiccup; the graded tests
        # will skip cleanly if the file still doesn't exist.
        return

    review_text = result.stdout.strip()
    if review_text:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(review_text)


def _has_output(scenario: str) -> bool:
    output_path = os.path.join(OUTPUTS_DIR, "%s.md" % scenario)
    try:
        with open(output_path, encoding="utf-8") as f:
            return bool(f.read().strip())
    except FileNotFoundError:
        return False


def pytest_collection_modifyitems(config, items):
    if not any("evals" in str(item.fspath).replace("\\", "/") for item in items):
        return
    for scenario in SCENARIOS:
        if not _has_output(scenario):
            _generate_output(scenario)
