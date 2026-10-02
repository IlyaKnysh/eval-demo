# Skill Benchmark: automation-framework-review-skill-creator

**Model**: claude-sonnet-5
**Date**: 2026-10-01T16:23:53Z
**Evals**: 1, 2, 3 (3 runs each per configuration)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 81% ± 3% | 62% ± 17% | +0.19 |
| Time | 341.6s ± 69.0s | 194.3s ± 44.8s | +147.3s |
| Tokens | 114081 ± 22673 | 86680 ± 10428 | +27401 |

## Notes

- Skill advantage is largest on the messy-Java fixture (78% vs 44%, +34 points) and near zero on the clean-TypeScript fixture (83% vs 78%, +5 points) — the skill's edge comes almost entirely from structured, grep-backed thoroughness on messy/mixed-signal codebases, not from avoiding false positives on clean ones (both configurations avoided false positives equally well across all three fixtures).
- On messy-Java and medium-Python, the baseline's failures cluster specifically around 'absence of appropriate abstraction' findings (missing business-step/flow layer, cross-file sibling duplication, flakiness-masking retry config) rather than 'bug visibly present in code' findings (hardcoded secrets, assertion-free tests, swallowed exceptions) — the baseline reliably catches the latter category unprompted but needs the skill's explicit checklist to catch the former.
- The skill's most consistent failure mode across all 3 with-skill runs is NOT missing evidence but failing to surface evidence it already gathered: the messy-Java transcript shows the executor ran the empty-catch-block grep (49 hits) and explicitly decided not to report it, reasoning it was 'already captured' elsewhere (it wasn't); the medium-Python transcript shows a flow-layer grep came back empty-handed for an existing steps/ package and the resulting finding was simply never written up despite being gathered. This is a synthesis/write-up gap, not a research gap — the skill's instructions may need a stronger guard against silently dropping a gathered finding.
- A second recurring failure: findings the skill's own calibration notes say must be kept distinct are getting merged into one bullet anyway. Both the messy-Java and medium-Python with-skill runs merged two deliberately co-occurring-but-distinct defects (raw-type-leakage vs God-Base-Class in one case; raw-requests layering vs raw-token domain-representation in the other) despite explicit warnings against exactly this pattern.
- The clean-TypeScript with-skill run's verdict-up-front paragraph recited 7 'no X' clauses in a row ('no missing business-step/flow layer, no God Base Class, no layer-boundary leakage...') — negated phrasing that functions as the same 'tour of strengths' the skill's no-fluff rule forbids for positive phrasing. The instruction may need to explicitly call out that negated enumeration is an equally-prohibited loophole, not just positive praise.
- Both with-skill and baseline missed 2 of the 3 genuine (non-seeded) bugs on the clean-TypeScript fixture (missing package-lock.json vs npm-ci mismatch, tsconfig lib omission breaking a typecheck). Both require cross-referencing two separate files (CI config + lockfile presence; tsconfig + a specific property usage) rather than single-file pattern-matching, suggesting a gap in both approaches for build-correctness bugs that only manifest as an interaction between files.
- Locator-distribution percentage reporting (the specific 31%/31%/38% fragility-based split) failed in both with-skill and baseline runs on messy-Java — both produced real grep-backed counts but bucketed by locator syntax (By.id/By.xpath/By.cssSelector) rather than by fragility category (positional vs stable vs css-class), a different and less useful taxonomy for a reader deciding what to fix first. Worth tightening the skill's §H wording to name the required bucketing explicitly rather than leaving the taxonomy implicit.
- Time and token cost scale with fixture size/defect density more than with skill-vs-baseline: messy-Java (most defects, most files) took the skill 376s/139k tokens vs. medium-Python's 262s/107k and clean-TypeScript's 387s/95k — the clean fixture actually took the longest wall-clock time despite having the fewest findings, likely reflecting the skill's full mandatory-grep checklist running regardless of how little it turns up.
- Grading-infrastructure note (not a skill defect): several grader subagents wrote grading.json to the eval root instead of the run-specific with_skill/without_skill subdirectory specified in their instructions, and one grading.json had a null total_duration_seconds that crashed the stock aggregate_benchmark.py script until patched locally. Future iterations should tighten the grader prompt's output-path phrasing and consider making the aggregation script null-safe upstream.