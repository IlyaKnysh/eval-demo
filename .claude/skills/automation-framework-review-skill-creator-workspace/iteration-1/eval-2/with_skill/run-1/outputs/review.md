# Automation Framework Issues

**Scope:** SubTrack Admin automation framework at `.claude/skills/automation-framework-review-deepeval/evals/fixtures/medium-framework` (repo-relative to `evals-demo`) — Python 3.11 / pytest 8.3 / Playwright (sync API) hybrid UI+API suite. Reviewed: `conftest.py`, `pytest.ini`, `.github/workflows/ci.yml`, `requirements.txt`, `.env.example`, all of `src/core`, `src/api_clients`, `src/factories`, `src/pages` (9 page-object files), and all 9 test files across `tests/api`, `tests/hybrid`, `tests/ui` (954 lines of Python total).

**Excluded from this review:** Fixture/DI composition (`conftest.py`), the test-data builder pattern (`src/factories/factories.py`), and locator strategy fundamentals (semantic `get_by_role`/`get_by_label`/`get_by_test_id` usage) were called out by the requester as already considered solid. Independent verification confirmed no material defects in these three areas, so per the skill's no-fluff rule they are not written up below — their clean status is recorded only in the FIRST-principles table and the checklist.

**Verdict up front:** The real problems are four near-identical page-object classes that duplicate the same five-method shape across every `*ModifyPage` file, two silent-pass tests on the delete path that assert nothing, inconsistent API-layer usage where two test files bypass the existing client wrappers and reach for raw `requests` calls with raw tokens, and an unconditional 2x retry configured in both `pytest.ini` and the CI invocation that will mask flakiness in green builds. None of these are large architecturally, but together they represent the most common real defects: duplicated domain logic, under-verified happy-path tests, and masked instability.

---

## Duplicated `*ModifyPage` classes across four sibling files

**[Impact: High | Effort: Medium]**

`src/pages/account_modify_page.py:1-21`, `src/pages/contact_modify_page.py:1-21`, `src/pages/subscription_modify_page.py:1-21`, and `src/pages/ticket_modify_page.py:1-21` each declare the identical five-method shape — `wait_until_loaded`, `update_name`, `update_status`, `save_changes`, `cancel_changes` — with near-identical bodies differing only in the label text passed to `get_by_role`/`get_by_label` and the success-message string checked in `save_changes`. All four are 21-22 lines, all four follow the exact same method order. This is the §C same-role cross-file duplication pattern: 4 sibling files, each with 5 matching method names, near-identical bodies modulo one locator/label string. A generic `ModifyPage` base (or a composition helper taking the entity-name, heading text, and field-label map as constructor args) would collapse all four into one implementation plus four thin configurations.

One of the four methods also has a naming-semantics defect that this duplication makes easy to miss: `SubscriptionModifyPage.update_name()` (`src/pages/subscription_modify_page.py:10-11`) fills the "Plan code" label, not a name field — the method name says `update_name` but the other three siblings' `update_name` genuinely map to a name-like field (`account name`, `contact name`, `ticket subject`). Copy-paste-renaming one case missed the actual field semantics.

## Two tests execute a delete and assert nothing

**[Impact: Medium | Effort: Low]**

`tests/api/test_account_api.py:20-26` (`test_delete_account`) calls `account_client.delete_account(account["id"])` and then only executes `account_client.get_account.__self__` — a no-op attribute access, not a call, not an assertion. A broken delete endpoint (account not actually removed) would pass this test. The companion hybrid test `tests/hybrid/test_account_lifecycle.py:53-63` (`test_delete_account_removes_from_list`) has the same shape: it deletes the account, searches for it in the UI, and waits for the search-results container to render — but never asserts the deleted account is absent from the results. Confirmed via AST scan: exactly 2 of 22 test methods in the suite contain zero `assert` statements, and both are on the delete path for the same entity (account), suggesting the gap is systematic to how "delete" is tested rather than a one-off oversight.

## Inconsistent API-layer usage: raw `requests` calls bypass existing client wrappers and the typed auth object

**[Impact: Medium | Effort: Low]**

`tests/api/test_billing_sync_api.py` imports `requests` directly (line 11) and makes two raw HTTP calls (lines 21-26, 35-40) to the billing-sync endpoint, even though `SubscriptionClient` (used correctly elsewhere in `tests/api/test_subscription_api.py` and the hybrid subscription tests) does not yet expose a `trigger_billing_sync` wrapper call at the test layer for this specific flow — the client method exists (`src/api_clients/clients.py:77-84`) but these two tests don't call it, duplicating its URL-building and header logic inline instead. Both raw calls also pull `Config.API_TOKEN` directly and pass it as a literal `Authorization` header (lines 24, 38) instead of going through the typed `AuthContext`/`User` object that `src/core/auth.py` defines and that most of the rest of the suite uses — this is the §C "domain-concept representation consistency" gap: the suite has one typed way to represent an authenticated session, and these two tests reach around it for the same concept.

The same pattern repeats in `tests/api/test_ticket_export_api.py:17-27` (`test_export_ticket_returns_pdf`): it imports `requests` and `os` directly, pulls `SUBTRACK_API_TOKEN` from the environment with `os.getenv` (line 21) rather than through `AuthContext`, and makes a raw GET to the export endpoint — despite `TicketClient.export_ticket()` (`src/api_clients/clients.py:49-54`) already existing and being used correctly two lines later in the same file's other test (`test_export_ticket_has_valid_pdf_header`, line 46) and in `tests/hybrid/test_ticket_lifecycle.py`. Three occurrences across two files, both with an available, already-used wrapper method sitting right next to the bypass.

## Hardcoded fake secret committed as a Python literal

**[Impact: Low | Effort: Low]**

`src/core/config.py:26` — `INVOICING_PROVIDER_API_KEY = "sk-fake1234567890"` — is a literal string assignment, inconsistent with every other credential in the same class (`ADMIN_USERNAME`, `ADMIN_PASSWORD`, `API_TOKEN` are all sourced via `os.getenv`, line 18-21). `.env.example` (line 14) already documents `INVOICING_PROVIDER_API_KEY=changeme` as an environment variable, so the mechanism to source it properly already exists in the same codebase — this one field just doesn't use it. Grep for credential-literal assignment patterns (`password|api_key|token|secret` assigned to a string literal) across the whole repo returns exactly this one hit; no other hardcoded secret exists.

## Silent exception-swallowing in two verification helpers

**[Impact: Medium | Effort: Low]**

Repo-wide grep for `except`/`except:` found 2 bare-except blocks, both wrapping comparison/verification logic — the specific case the skill flags as worst because a swallow there makes "failed to check" look identical to "checked, no difference":
- `tests/api/test_ticket_export_api.py:30-41` — `_content_matches_expected_header()` wraps a slice comparison in `try/except: pass; return False`. Any unexpected error (e.g., `content` being `None`) is silently converted into an ordinary "header didn't match" failure, masking the real cause.
- `tests/ui/test_admin_console_nav.py:18-29` — `_values_are_equivalent()` wraps `actual.strip().lower() == expected.strip().lower()` in the same `try/except: pass` shape, falling back to a plain `==` on error. If `actual` is `None` because a UI field never populated (a real rendering bug), this silently degrades to a different, still-valid-looking comparison instead of surfacing the real defect.

Both are small, isolated helper functions (not a systemic pattern across the suite — only these two matches total), so impact is capped at Medium rather than High, but both sit exactly in the comparison/verification role the skill calls out as highest-risk for this smell.

## Unconditional retry configured twice, masking flakiness

**[Impact: Medium | Effort: Low]**

`pytest.ini:14-15` sets `reruns = 2` / `reruns_delay = 2` globally (via `pytest-rerunfailures`, confirmed current in `requirements.txt`), and `.github/workflows/ci.yml:31` redundantly passes `--reruns 2 --reruns-delay 2` again on the CI invocation (the ini setting already applies; the CLI flags are either dead duplication or an attempt to override that in fact sets identical values). Every CI run gets up to 2 silent re-executions of any failing test before it's reported as a failure, with no flaky-test tracking/quarantine mechanism found anywhere in the repo (no marker, no ticket-link annotation, no separate flaky-suite list) — a genuinely flaky test will simply re-run until green and never surface in the report as having been unstable. `conftest.py:84-93`'s trace-capture logic does at least conditionally capture a Playwright trace when `rerun_count > 1`, so a rerun is diagnosable after the fact, but nothing in the pipeline flags that it happened.

## No smoke/fast-path split in CI despite tagging markers existing

**[Impact: Low | Effort: Low]**

`pytest.ini:17-20` defines `smoke`, `billing`, and `tickets` markers, but `.github/workflows/ci.yml` has a single `test` job that runs plain `pytest --reruns 2 --reruns-delay 2` on every push and PR to `main` — no `-m smoke` fast subset on PR and full-suite-elsewhere split. The tagging convention exists but CI doesn't use it; every run is all-or-nothing regardless of trigger.

## Missing `.gitignore` for generated test output

**[Impact: Low | Effort: Low]**

No `.gitignore` file exists anywhere in the framework directory. The suite generates `report.html` (via `pytest-html`, `pytest.ini:10-11`) and a `traces/` directory (via `conftest.py:91`, consumed by `.github/workflows/ci.yml:40-46`), both of which are exactly the kind of generated artifact a `.gitignore` should exclude, and neither is currently covered by any ignore rule in this project's own directory.

## Minor: unused fixture dependency

**[Impact: Low | Effort: Low]**

`conftest.py:49-52` — the `account_client` fixture declares a dependency on `auth_client` (`def account_client(auth_client):`) but never references the parameter in its body; the returned `AccountClient` is constructed independently and isn't authenticated via `auth_client` at all (actual auth wiring happens later through `AuthContext.login_as`, `src/core/auth.py:26-36`). The unused parameter is misleading about where authentication actually happens and should either be removed or the client should actually be wired with the token it implies.

---

## FIRST principles table

| Letter | Verdict | Evidence |
|---|---|---|
| **Fast** | + | No `Thread.sleep`/`time.sleep`/`waitForTimeout` found anywhere in the suite (0 hits on repo-wide grep); suite relies on Playwright's built-in auto-waiting and explicit `.wait_for()` calls throughout. |
| **Independent** | Fails (isolated) | `tests/hybrid/test_ticket_lifecycle.py:7,31-44` — module-level mutable list `_CREATED_TICKET_IDS` is populated by `test_create_ticket_and_record_id` and consumed by `test_second_test_relies_on_previous_ticket`; running the second test alone raises an unhandled `IndexError` rather than a meaningful failure. This is the only inter-test order dependency found in the suite (1 of 3 hybrid test files). |
| **Repeatable** | + | `AccountBuilder`/`ContactBuilder`/`TicketBuilder` use a shared `itertools.count()` sequence and `SubscriptionBuilder` uses `uuid.uuid4()` for uniqueness (`src/factories/factories.py:12,91`) — no raw timestamps or hardcoded colliding literals found. No parallel-execution config (no `pytest-xdist`, no worker count anywhere) is configured, so the shared counter's collision risk under concurrent workers is currently theoretical, not live. |
| **Self-validating** | Fails | 2 of 22 test methods contain no assert statement (`test_delete_account`, `test_delete_account_removes_from_list` — see finding above), confirmed via AST scan of every `test_*.py` file. |
| **Timely** | N/A statically | No smoke/full split enforced in CI (see finding above) — cannot assess actual wall-clock turnaround statically. |

## Recommended actions, in priority order

1. **Collapse the four `*ModifyPage` classes into one parameterized implementation** — highest-leverage structural fix; removes ~60 lines of duplicated method bodies across 4 files and would have prevented the `SubscriptionModifyPage.update_name` field-semantics bug as a side effect of making the field mapping explicit. `[Impact: High | Effort: Medium]`
2. **Add real assertions to the two delete-path tests** (`test_delete_account`, `test_delete_account_removes_from_list`) — cheap, localized, closes a real self-validation gap. `[Impact: Medium | Effort: Low]`
3. **Route `test_billing_sync_api.py` and `test_export_ticket_returns_pdf` through the existing `SubscriptionClient`/`TicketClient` wrappers and `AuthContext`**, removing the raw `requests` + raw-token calls. `[Impact: Medium | Effort: Low]`
4. **Fix the two bare `except: pass` verification helpers** to re-raise or log the real error instead of silently degrading to a different comparison. `[Impact: Medium | Effort: Low]`
5. **Remove or justify the double-configured retry** (`pytest.ini` + CI CLI flags) and add a flaky-test tracking mechanism if retries are to stay. `[Impact: Medium | Effort: Low]`
6. **Move `INVOICING_PROVIDER_API_KEY` to `os.getenv`**, matching every other credential in `Config`. `[Impact: Low | Effort: Low]`
7. **Add a `.gitignore`** covering `report.html`, `traces/`, `__pycache__/`. `[Impact: Low | Effort: Low]`
8. **Wire CI to run a `-m smoke` subset on PR and the full suite on a separate trigger**, using the markers that already exist. `[Impact: Low | Effort: Low]`
9. **Remove the unused `auth_client` parameter from the `account_client` fixture**, or wire real auth through it. `[Impact: Low | Effort: Low]`
