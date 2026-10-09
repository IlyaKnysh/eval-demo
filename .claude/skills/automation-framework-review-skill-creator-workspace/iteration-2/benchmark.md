# Skill Benchmark: automation-framework-review-skill-creator

**Model**: claude-opus-5-5
**Date**: 2026-10-09T07:18:51Z
**Evals**: 1, 2, 3 (1 runs each per configuration)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 90% ± 9% | 67% ± 10% | +0.23 |
| Time | 425.4s ± 107.7s | 226.2s ± 64.4s | +199.2s |
| Tokens | 139073 ± 21677 | 90767 ± 15301 | +48306 |

## Notes

- Single run per configuration per eval: the ± figures are spread ACROSS the 3 evals, not run-to-run variance. Treat per-eval deltas as indicative, not statistically robust.
- The skill wins on all three fixtures, and the margin scales with defect density: messy-Java 100% vs 56% (+44 pts), medium-Python 88% vs 69% (+19), clean-TypeScript 82% vs 76% (+6). Same shape as iteration-1 (81% vs 62%), with the with-skill rate up 9 pts.
- About half the raw gap comes from format assertions (Impact/Effort tags, FIRST table, exact checklist columns) that a no-skill run cannot pass. On content assertions only (45 of 51), the score is skill 40/45 (89%) vs baseline 34/45 (76%), so the real content edge is about 13 pts. On clean-TypeScript the content score is a tie (13/16 each).
- Where the content edge comes from: the baseline missed the missing business-step/flow layer, gave no quantified assertion-free count or locator distribution (messy-Java), and both baselines added a 'what's done well' praise section that the user (eval 2) and the eval (eval 3) explicitly reject. The no-fluff rule works: both with-skill verdicts were issues-only.
- Two iteration-1 failures are now fixed: the empty-catch count is reported (38 across 9 files), and the flow-layer finding is written up on medium-Python.
- Still failing, same as iteration-1: on medium-Python the skill merged the raw-token/domain-representation issue into the raw-requests layering finding (one tag, one fix), even though its own calibration notes say to keep them separate. Neither run named the clean sibling API files (test_account_api.py, test_subscription_api.py) as the contrast case.
- Clean-fixture over-reporting: on clean-TypeScript the with-skill run produced 11 tagged findings against an expected 0-5. Only 4 map to the manifest's genuine bugs; the rest are speculative (pagination 'to be verified', ESLint gate, dead code). The baseline padded more (23 findings, 5 'High'). The skill's issues-only framing removes praise but does not stop padding with low-value findings.
- Both configurations missed the tsconfig lib/ES2022 `cause` typecheck bug on clean-TypeScript in iteration-1. This time the baseline caught it and the skill run did not. Bugs that only show up when two files are read together remain hit-or-miss.
- Cost: the skill takes about 1.9x the wall-clock time (425s vs 226s) and about 1.5x the tokens (139k vs 91k). The mandatory grep checklist runs in full even on the clean fixture.
- Answer-key issues the graders found (fix before trusting future deltas). (a) eval-3 assertion #11 says trace is 'on-first-retry', but the fixture uses 'retain-on-failure'. (b) medium-framework.manifest.md lists conftest.py as deliberately clean, yet both runs found a real bug there (AuthContext calls .authenticate() on AccountClient, breaking 15/23 tests); its line numbers are also stale and its header still points at the deepeval fixture path. (c) The messy-Java assertion-free expectation (4) ignores 2 WIP tests that testng.xml actually runs (6 is defensible). (d) Fixture comments in medium-framework give away the defects (e.g. 'never asserts anything'), which makes several detection assertions easy for the baseline too.