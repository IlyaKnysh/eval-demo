# Review transcript — SubTrack Admin automation framework audit

**Skill used:** `automation-framework-review-skill-creator` (`.claude/skills/automation-framework-review-skill-creator/SKILL.md`)
**Target:** `.claude/skills/automation-framework-review-deepeval/evals/fixtures/medium-framework` (repo root: `C:\Users\knysh\source\repos\evals-demo`)
**Mode:** read-only audit — no files under the fixture path were modified.

## Process followed

1. **Read the skill file in full** before starting, to follow its process, dimension list (§A-O), severity-tagging rules, mandatory-greps table, and output structure exactly as specified.
2. **Scoped the review.** Noted the user's exclusion hint (fixtures, test-data builders, locators considered "solid") but treated it as a hint to verify, not a free pass — per the skill's "verify, don't recall" principle.
3. **Surveyed the repo.** Listed all files (`find ... -type f`), got line counts (`wc -l`) — 954 lines of Python across 23 files, small/medium framework. Read `README.md` for stated architecture (layout: `core/`, `pages/`, `api_clients/`, `factories/`, `tests/{ui,api,hybrid}`).
4. **Read every source and test file directly** rather than delegating to subagents, given the small size (faster, preserves exact line-level evidence): `conftest.py`, `src/core/auth.py`, `src/core/config.py`, `src/api_clients/base_client.py`, `src/api_clients/clients.py`, `src/factories/factories.py`, all 9 files in `src/pages/`, and all 9 test files across `tests/api`, `tests/hybrid`, `tests/ui`.
5. **Ran the mandatory greps table verbatim:**
   - Swallowed exceptions (`except`/`except:`) → 2 hits, both bare `except: pass` in verification helpers (`test_ticket_export_api.py:39`, `test_admin_console_nav.py:27`).
   - Unconditional waits (`time.sleep`/`waitForTimeout`/etc.) → 0 hits.
   - Assertion-free tests → ran an AST script parsing every `test_*.py` for `ast.Assert` nodes inside each `test_*` function; found exactly 2 of 22 with no assert (`test_delete_account`, `test_delete_account_removes_from_list`).
   - Hardcoded credentials (`password|api_key|token|secret` = literal) → 1 hit (`config.py:26`, fake invoicing API key).
   - Retry/rerun policy → `pytest.ini` sets `reruns = 2`/`reruns_delay = 2`; CI workflow redundantly re-passes the same flags on the command line.
6. **Ran targeted follow-up greps** for: God Base Class presence (none — no shared page-object base class), steps/flows package (none found), direct Playwright locator calls inside test bodies bypassing page objects (11 lines across 3 files, several using `.click()` directly), method-chaining return-type consistency (no page object returns `self`/next-page — uniformly absent, not inconsistent), OCP switch/if-chains (none found), `.gitignore` presence (none in the fixture directory), committed build artifacts (`__pycache__` exists on disk but the whole fixture dir is untracked/new in the outer repo, so git-hygiene checks were scoped to "no `.gitignore` exists" rather than "something slipped past gitignore").
7. **Verified the user's "solid" claims independently:**
   - Fixtures (`conftest.py`): composition is via pytest DI fixtures, not inheritance chains — confirmed clean, no material finding. One minor issue found and reported anyway (unused `auth_client` param on `account_client` fixture) since it was concrete evidence encountered during verification, not something to suppress just because the broader area was called "solid."
   - Test-data builders (`src/factories/factories.py`): builder pattern used consistently for all 4 entity types, chaining `with_*` methods, `.build()` returns a copy — confirmed clean.
   - Locators (`src/pages/*.py`): consistently `get_by_role`/`get_by_label`/`get_by_test_id`, no CSS/XPath scraping found anywhere — confirmed clean.
   - None of these three areas are written up as findings in review.md, per the skill's no-fluff rule (clean dimensions get zero lines, only reflected in the FIRST-principles table / checklist).
8. **Synthesized findings**, cross-referencing where relevant (e.g., the `SubscriptionModifyPage.update_name` field-semantics bug is a direct consequence of the cross-file duplication, called out together). Tagged every finding with `[Impact | Effort]` per the skill's three-value-only rule.
9. **Drafted `review.md`** following the mandated output structure: Scope / Excluded / Verdict-up-front / per-finding headings / FIRST-principles table / Recommended actions rollup.
10. **Drafted the checklist-tab table**, restricting rows strictly to what code evidence actually answers (per the mapping table in the skill) — left out all `Tools`/`Strategy`/`AI Usage` rows and anything requiring questionnaire-interview data.
11. **Ran the mandated two-directional self-check** before finalizing the checklist:
    - Row→evidence: walked the skill's full mapping table line by line and confirmed each filled row has backing evidence already present in review.md.
    - Finding→row: walked every `[Impact|Effort]`-tagged finding and FIRST-table verdict in review.md and confirmed each either has a corresponding checklist row, or legitimately has no row in the skill's mapping (e.g., assertion-free-tests/Self-validating and exception-swallowing have no direct checklist-row mapping per the skill's own table — confirmed by re-reading the mapping rather than assuming).

## Findings logged (review.md)

9 tagged findings in the issues list, plus the FIRST-principles table (5 letters, 2 failing) and a 9-item Recommended Actions rollup:
1. Duplicated `*ModifyPage` classes across 4 sibling files — Impact: High, Effort: Medium
2. Two delete-path tests with no assertions — Impact: Medium, Effort: Low
3. Inconsistent API-layer usage (raw `requests` bypassing client wrappers, raw tokens bypassing `AuthContext`) — Impact: Medium, Effort: Low
4. Hardcoded fake secret in `config.py` — Impact: Low, Effort: Low
5. Two silent exception-swallowing verification helpers — Impact: Medium, Effort: Low
6. Unconditional retry configured twice (pytest.ini + CI) — Impact: Medium, Effort: Low
7. No smoke/fast-path CI split despite existing markers — Impact: Low, Effort: Low
8. Missing `.gitignore` — Impact: Low, Effort: Low
9. Unused `auth_client` fixture dependency — Impact: Low, Effort: Low

Areas verified and confirmed clean (not written up, per the skill's silence rule): fixtures/DI composition, test-data builders, locator strategy, SOLID (no inheritance hierarchy to violate), KISS, dependency currency (Playwright 1.47.0 / pytest 8.3.3 both current), repo/report publishing mechanism.

## Outputs produced

- `review.md` — main issues-list document
- `checklist.md` — checklist-tab input table (16 rows, scope-disciplined per the skill's mapping)
- `transcript.md` — this file
