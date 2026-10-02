# Automation Framework Issues

**Scope:** Full `medium-framework` fixture repo: `conftest.py`, `pytest.ini`, `requirements.txt`, `.env.example`, `.github/workflows/ci.yml`, `src/core/`, `src/pages/`, `src/api_clients/`, `src/factories/`, and all files under `tests/ui/`, `tests/api/`, `tests/hybrid/` (21 test functions across 9 files, 10 page-object classes, 3 API-client classes, 4 builder classes).
**Not verified:** actual flakiness/runtime stability of the suite (no execution data available in a static review); whether `pytest-rerunfailures`' retry semantics interact with the `_capture_trace_on_retry` conditional in `conftest.py:90` under every retry ordering.

**Verdict up front:** The highest-leverage problem is architectural: every hybrid test re-composes the same create→navigate→modify→save→assert sequence inline instead of calling a shared business-step layer, and this duplication is compounded by four sibling `*ModifyPage` classes that each re-declare the same five methods almost verbatim. Two API test files step around the existing `*Client` wrappers with raw `requests` calls and raw credentials pulled straight from `Config`/env instead of the typed `AuthContext`, two verification helpers swallow exceptions with a bare `except:`, two of 21 tests contain no assertion at all, and one test is order-dependent on another via module-level mutable state.

---

## Missing business-step/flow layer
[Impact: High | Effort: High]

There is no `steps/`/`flows/` package. Five tests across three hybrid files manually re-compose the same ~4-step sequence (create entity via API client → navigate to it via `DashboardPage`/`*ListPage` → modify a field via `*ModifyPage` → save and re-fetch via the API client to assert): `tests/hybrid/test_account_lifecycle.py:13-30` (`test_update_account_name`) and `:33-50` (`test_update_account_status`), `tests/hybrid/test_ticket_lifecycle.py:10-28` (`test_update_ticket_priority`), `tests/hybrid/test_subscription_lifecycle.py:8-26` (`test_update_subscription_seats`) and `:29-42` (`test_cancel_subscription`). The duplication is acknowledged directly in `tests/hybrid/test_account_lifecycle.py:1-7`, which states every test in the file "re-composes the same ~4-step sequence inline ... instead of calling a shared `create_and_open_account(...)` / `modify_and_save(...)` style step function."

**Fix:** introduce a `steps/` module exposing one business-level call per lifecycle action (e.g. `create_and_open_account(...)`, `modify_and_save(page_obj, **fields)`) and route the five tests above through it.

## Cross-file duplication across sibling `*ModifyPage` classes
[Impact: Medium | Effort: Medium]

`src/pages/account_modify_page.py:7-21`, `src/pages/contact_modify_page.py:7-21`, `src/pages/ticket_modify_page.py:7-21`, and `src/pages/subscription_modify_page.py:7-21` each declare the identical method set — `wait_until_loaded`, `update_name`, `update_status`, `save_changes`, `cancel_changes` — with near-identical bodies differing only in the label/heading/success-text string passed to `get_by_label`/`get_by_role`/`get_by_text` (20 method occurrences across the 4 files, confirmed by grepping `wait_until_loaded|update_name|update_status|save_changes|cancel_changes` under `src/pages/`).

**Fix:** extract a generic `EntityModifyPage` (parameterized by heading text, name-field label, and success-message text) that the four classes compose or inherit from, replacing the 20 duplicated method bodies with one shared implementation.

## Dead code: `ContactModifyPage` and `ContactBuilder` are never referenced
[Impact: Low | Effort: Low]

`src/pages/contact_modify_page.py:1-21` (`ContactModifyPage`) and `src/factories/factories.py:41-60` (`ContactBuilder`) have 0 references outside their own definitions — a repo-wide grep for `ContactModifyPage|ContactBuilder` returns only the two definition sites, no import or instantiation anywhere in `tests/`.

**Fix:** either wire a contact-lifecycle test into `tests/hybrid/` that uses both, or delete both classes until a contact test is written.

## Tests bypass the API-client layer via raw `requests` calls
[Impact: Medium | Effort: Low]

`tests/api/test_billing_sync_api.py:21-27` and `:35-41` (2 tests) and `tests/api/test_ticket_export_api.py:17-28` (1 test) `import requests` directly and call the SubTrack API over HTTP, bypassing `SubscriptionClient.trigger_billing_sync` and `TicketClient.export_ticket` in `src/api_clients/clients.py:49-54,77-84`, both of which already exist and are used by `tests/hybrid/test_ticket_lifecycle.py` and `tests/api/test_subscription_api.py` respectively. This is inconsistent use of the underlying HTTP library across the suite (3 of the suite's test files reach past the domain layer; the rest go through the typed `*Client` wrappers).

**Fix:** replace the three raw `requests.get`/`requests.post` calls with `ticket_client.export_ticket(...)` and `subscription_client.trigger_billing_sync(...)`.

## Raw auth token pulled from Config/env instead of the typed `AuthContext`
[Impact: Medium | Effort: Medium]

The same two files read the admin API token directly rather than through `src/core/auth.py`'s `AuthContext`/`User`: `tests/api/test_billing_sync_api.py:24,38` use `Config.API_TOKEN` directly as a header value, and `tests/api/test_ticket_export_api.py:21` calls `os.getenv("SUBTRACK_API_TOKEN")` directly (3 raw-token call sites across 2 files). Elsewhere the suite consistently authenticates through `AuthContext.login_as` (`conftest.py:70-80`), so this is a second, disconnected way of expressing "the current admin credential" rather than a duplicated code shape.

**Fix:** expose the authenticated token through `AuthContext`/the `*Client` instance (e.g. `account_client.session.headers["Authorization"]`) and have these tests read it from there instead of `Config`/`os.getenv`.

## Hardcoded secret literal in `Config`
[Impact: Low | Effort: Low]

`src/core/config.py:26` sets `INVOICING_PROVIDER_API_KEY = "sk-fake1234567890"` as a literal, while every other credential in the same class (`ADMIN_USERNAME`, `ADMIN_PASSWORD`, `API_TOKEN` at lines 18-21) is sourced via `os.getenv(...)`, and `.env.example:14` documents `INVOICING_PROVIDER_API_KEY` as an environment variable that is never actually read. The literal is consumed at 3 call sites: `tests/api/test_billing_sync_api.py:23,37` and `tests/ui/test_admin_console_nav.py:40`.

**Fix:** change line 26 to `os.getenv("INVOICING_PROVIDER_API_KEY")`, matching the other three fields in the class.

## Swallowed exceptions in verification helpers
[Impact: Medium | Effort: Low]

Two bare `except:` blocks mask real failures as negatives in comparison helpers: `tests/ui/test_admin_console_nav.py:25-29` (`_values_are_equivalent`) swallows any error and falls back to a plain `==` check, and `tests/api/test_ticket_export_api.py:37-41` (`_content_matches_expected_header`) swallows any error and returns `False`. Both are confirmed by their own docstrings as intentionally masking the underlying cause. A repo-wide grep for `except:`/`except Exception` across `*.py` returns exactly these 2 hits (no other catch blocks in the codebase).

**Fix:** remove the bare `except:` in both helpers and let the underlying error (e.g. `AttributeError` on `None`) propagate, or replace the helper with an explicit `None`/empty check that fails loudly.

## Assertion-free tests
[Impact: Medium | Effort: Low]

2 of 21 test methods contain no real assertion: `tests/hybrid/test_account_lifecycle.py:53-64` (`test_delete_account_removes_from_list`) only calls `.wait_for()` on the search-results locator and never asserts the account is absent (confirmed by its own comment at lines 61-63), and `tests/api/test_account_api.py:20-26` (`test_delete_account`) ends with `account_client.get_account.__self__`, a no-op attribute access rather than an assertion (confirmed by the comment at lines 23-26).

**Fix:** assert on the actual deletion outcome — e.g. `assert account["name"] not in [r.text for r in page.get_by_test_id("search-results").all()]` and a 404/exception check on `account_client.get_account(account["id"])`.

## Inter-test order dependency via module-level state
[Impact: Low | Effort: Low]

`tests/hybrid/test_ticket_lifecycle.py:7` declares a module-level `_CREATED_TICKET_IDS = []`; `test_create_ticket_and_record_id` (lines 31-34) appends to it, and `test_second_test_relies_on_previous_ticket` (lines 37-44) reads `_CREATED_TICKET_IDS[-1]`, raising `IndexError` instead of a meaningful assertion failure if run alone (e.g. `pytest -k test_second_test_relies_on_previous_ticket`) — both confirmed by the file's own comments.

**Fix:** have the second test create its own ticket (or depend on the first via an explicit fixture), removing the module-level list.

## Naming-convention outliers in the page-object directory
[Impact: Low | Effort: Low]

8 of 10 page-object classes follow the repo's `*Page` suffix and matching snake_case module-filename convention (`login_page.py`→`LoginPage`, `dashboard_page.py`→`DashboardPage`, the four `*_modify_page.py` files, `list_pages.py`'s two classes). 2 outliers break both conventions at once: `src/pages/SettingsScreen.py:1-8` (`SettingsScreen`, PascalCase filename) and `src/pages/AdminConsole.py:1-8` (`AdminConsole`, PascalCase filename) — each file's own docstring explicitly flags the naming-convention break.

**Fix:** rename to `settings_screen.py`/`SettingsPage` and `admin_console.py`/`AdminConsolePage` (or an equivalent `*Page` suffix) and update the two importing test files (`tests/ui/test_admin_console_nav.py`).

## Pytest markers declared but never applied; CI runs a single undifferentiated job
[Impact: Medium | Effort: Low]

`pytest.ini:17-20` declares `smoke`, `billing`, and `tickets` markers, but a repo-wide grep for `@pytest.mark.` across `tests/` returns 0 hits — none of the 21 tests carry any marker. `.github/workflows/ci.yml:3-31` defines exactly one `test` job triggered on every push/PR to `main`, running the full `pytest --reruns 2 --reruns-delay 2` suite with no marker-based subset selection. The same absence of markers means the `pytest-html` report (`pytest.ini:10-11`) has no feature/area grouping — every one of the 21 tests appears as a flat list.

**Fix:** tag tests with the existing markers and add a `pytest -m smoke` job on PR plus the full suite on a separate (merge/nightly) trigger.

## Nonzero default retry with no flaky-test tracking
[Impact: Low | Effort: Low]

`pytest.ini:14-15` sets `reruns = 2` / `reruns_delay = 2`, and `.github/workflows/ci.yml:31` passes `--reruns 2 --reruns-delay 2` again explicitly. No `@pytest.mark.skip(reason=...)`, `xfail`, or ticket-link annotation exists anywhere in `tests/` to distinguish a known-flaky test from a newly broken one — every failure is retried up to twice and reported identically either way.

**Fix:** add a skip/xfail-with-reason convention for tracked-flaky tests, and treat the retry count itself as a stability signal to monitor, not just a pass/fail smoother.

## Orphaned test data; two API clients expose no delete method
[Impact: Medium | Effort: Medium]

`conftest.py` has no teardown fixture that deletes any entity created during a test. Of the 19 of 21 tests that create an account, ticket, or subscription via a `*Client`/`*Builder`, only 2 (`test_delete_account_removes_from_list`, `test_delete_account`) remove the entity they created, and in both cases deletion is the behavior under test, not cleanup — the remaining 17 leave data behind against the staging environment declared in `.env.example:3-4`. `src/api_clients/clients.py:36-60` (`TicketClient`) exposes `create_ticket`/`get_ticket`/`export_ticket`/`close_ticket` but no `delete_ticket`, and `:62-91` (`SubscriptionClient`) exposes `create_subscription`/`get_subscription`/`trigger_billing_sync`/`cancel_subscription` but no `delete_subscription` — so ticket and subscription test data cannot be cleaned up programmatically even if a teardown fixture were added.

**Fix:** add `delete_ticket`/`delete_subscription` to the respective clients and an autouse or per-test teardown fixture that deletes whatever the test created.

## No `.gitignore`; compiled bytecode present in the tree
[Impact: Low | Effort: Low]

The repository contains zero `.gitignore` files (confirmed by glob), and `__pycache__/conftest.cpython-312-pytest-9.1.1.pyc` sits in the repo root alongside source files. Without a `.gitignore`, this bytecode artifact (and future `report.html`, `traces/`, and other generated output) has no standing exclusion from version control.

**Fix:** add a `.gitignore` covering `__pycache__/`, `*.pyc`, `report.html`, and `traces/`, and remove the already-present `__pycache__` directory from the tree.

## FIRST principles table

| Letter | Verdict | Evidence |
| --- | --- | --- |
| Fast | Not independently measured | 0 occurrences of `Thread.sleep`/`time.sleep`/`waitForTimeout`/`implicitlyWait` repo-wide; waiting relies on Playwright's built-in auto-waiting and explicit `.wait_for()` calls, so no fixed-delay overhead is inflating runtime. |
| Independent | Fails | `tests/hybrid/test_ticket_lifecycle.py:7,31-44` — `test_second_test_relies_on_previous_ticket` depends on `test_create_ticket_and_record_id` having already run via a module-level list; fails or errors if run in isolation. |
| Repeatable | Passes | All test-data builders (`src/factories/factories.py`) generate unique values via `itertools.count`/`uuid.uuid4()`, avoiding name/email collisions on rerun; no hardcoded dates/timestamps found in any assertion. |
| Self-validating | Fails | 2 of 21 test methods contain no real assertion: `test_delete_account_removes_from_list` (`tests/hybrid/test_account_lifecycle.py:53-64`) and `test_delete_account` (`tests/api/test_account_api.py:20-26`). |
| Timely | N/A statically | Cannot be assessed from a static code review. |

## Recommended actions

1. Introduce a business-step/flow layer and route the 5 hybrid tests that re-compose the create→navigate→modify→save→assert sequence through it. `[Impact: High | Effort: High]`
2. Replace the raw `requests` calls in `tests/api/test_billing_sync_api.py` (2 tests) and `tests/api/test_ticket_export_api.py` (1 test) with the existing `SubscriptionClient`/`TicketClient` methods. `[Impact: Medium | Effort: Low]`
3. Remove the bare `except:` in `_values_are_equivalent` (`tests/ui/test_admin_console_nav.py:25-29`) and `_content_matches_expected_header` (`tests/api/test_ticket_export_api.py:37-41`). `[Impact: Medium | Effort: Low]`
4. Add real assertions to `test_delete_account_removes_from_list` and `test_delete_account`. `[Impact: Medium | Effort: Low]`
5. Apply the existing `smoke`/`billing`/`tickets` pytest markers to the suite and add a marker-filtered fast job to CI alongside the full-suite job. `[Impact: Medium | Effort: Low]`
6. Extract a shared `EntityModifyPage` to collapse the 20 duplicated methods across the 4 `*ModifyPage` classes. `[Impact: Medium | Effort: Medium]`
7. Route the 3 raw-token call sites in `test_billing_sync_api.py`/`test_ticket_export_api.py` through `AuthContext` instead of `Config`/`os.getenv`. `[Impact: Medium | Effort: Medium]`
8. Add `delete_ticket`/`delete_subscription` to the respective API clients and a teardown fixture to clean up the 17 of 19 entity-creating tests that currently leave data behind. `[Impact: Medium | Effort: Medium]`
9. Wire `ContactModifyPage`/`ContactBuilder` into a real test or delete them. `[Impact: Low | Effort: Low]`
10. Source `INVOICING_PROVIDER_API_KEY` via `os.getenv` in `src/core/config.py:26`, matching the other three credentials in the class. `[Impact: Low | Effort: Low]`
11. Fix `test_second_test_relies_on_previous_ticket`'s dependency on module-level state in `tests/hybrid/test_ticket_lifecycle.py`. `[Impact: Low | Effort: Low]`
12. Rename `SettingsScreen.py`/`AdminConsole.py` (and their classes) to match the `*Page` / snake_case-filename convention used by the other 8 page objects. `[Impact: Low | Effort: Low]`
13. Add a skip/xfail-with-reason convention for known-flaky tests rather than relying solely on the blanket `reruns=2` retry. `[Impact: Low | Effort: Low]`
14. Add a `.gitignore` covering `__pycache__/`, `*.pyc`, `report.html`, `traces/`, and remove the committed `__pycache__` directory. `[Impact: Low | Effort: Low]`

## Checklist tab input

| Section | Check | Status (+/-) | Comments |
|---|---|---|---|
| Framework | Framework is consistent | + | Builder chaining (`src/factories/factories.py`) and page-object method signatures are uniform; no mixed optional/null idiom found. |
| Framework | Framework follows a layered architecture | - | 3 tests bypass `*Client` wrappers with raw `requests` (`test_billing_sync_api.py`, `test_ticket_export_api.py`); no business-step layer exists above the 10 page objects. |
| Framework | Framework complies with DRY | - | 4 sibling `*ModifyPage` classes duplicate the same 5 methods (20 occurrences); `ContactModifyPage`/`ContactBuilder` are unused dead code. |
| Framework | Framework complies with YAGNI | - | `ContactModifyPage` and `ContactBuilder` (`src/pages/contact_modify_page.py`, `src/factories/factories.py:41-60`) are speculative/unused — 0 references outside their own definitions. |
| Framework | Framework complies with SOLID | - | DIP inconsistency: `requests` used directly in 2 test files instead of through `SubscriptionClient`/`TicketClient`, while the rest of the suite wraps it consistently. |
| Framework | Framework complies with language standards | - | 8 of 10 page-object files follow the `*Page` suffix/snake_case-filename convention (no linter config found; judged against idiomatic Python); 2 outliers: `SettingsScreen.py`, `AdminConsole.py`. |
| Framework | Presetups are implemented at the optimal available level | + | All hybrid tests create entities via API clients (`account_client.create_account`, etc.) before touching the UI, rather than creating data through the UI. |
| Framework | Unconditional waits are not a common practice | + | 0 occurrences of `Thread.sleep`/`time.sleep`/`waitForTimeout`/`implicitlyWait` repo-wide; suite relies on Playwright auto-waiting and explicit `.wait_for()`. |
| Framework | Tests are atomic and independent | - | `test_second_test_relies_on_previous_ticket` (`tests/hybrid/test_ticket_lifecycle.py:37-44`) depends on a prior test's module-level state. |
| Framework | Test implementation is done at the optimal level (API, UI...) | + | Hybrid tests use API clients for setup/verification and UI only for the feature under test. |
| Framework | Core libraries/framework/language versions are reasonably current | + | `playwright==1.47.0` (2024 release) supports the auto-waiting/trace-capture features the suite relies on (`requirements.txt:3`). |
| Framework | No hardcoded credentials/secrets in the test codebase | - | `src/core/config.py:26` hardcodes `INVOICING_PROVIDER_API_KEY = "sk-fake1234567890"` as a literal instead of reading it via `os.getenv`, unlike every other credential in the same class. |
| Running | Steps have a sufficient level of documentation for reporting | + | Test names are descriptive (`test_update_account_status`, etc.) and hybrid tests carry inline `# step N:` comments. |
| Running | When tests fail, there are mechanisms to easily find the cause | + | Playwright tracing with screenshots/snapshots/sources is captured on retry/failure (`conftest.py:30-33,83-93`) and published as a CI artifact (`.github/workflows/ci.yml:40-46`). |
| Running | Test stability is at a sufficient level | - | `reruns=2` is configured in both `pytest.ini:14-15` and `.github/workflows/ci.yml:31` with no flaky-test quarantine mechanism — a nonzero default retry is evidence of a known stability gap, not proof of a stable suite. |
| Running | There is a way to track run results over time | + | `pytest-html` report (`pytest.ini:10-11`) is published as a build artifact on every CI run (`.github/workflows/ci.yml:33-38`). |
| Running | Tests are integrated into CI/CD, not run purely manually/on-demand | + | `.github/workflows/ci.yml:3-7` triggers on every push/PR to `main`. |
| Processes | Tests are properly documented | + | Descriptive snake_case test names and per-file module docstrings throughout `tests/`. |
| Processes | A failure-handling strategy is implemented (bug reporting → flaky rerun → failure skipping) | - | `reruns=2` provides the rerun step, but no `skip`/`xfail`-with-reason or ticket-link mechanism exists anywhere in `tests/` to distinguish known-tracked failures from new ones. |