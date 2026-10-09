# SubTrack Admin Automation Framework: Review

**Scope:** `medium-framework/` (Python 3.11, pytest 8.3, Playwright sync 1.47, requests, pytest-rerunfailures, pytest-html, GitHub Actions). I read all 29 source/config files (1,091 lines, 23 tests) and grepped for symbol usage. `__pycache__` was ignored. Nothing was executed; there is no live SubTrack environment.

**Assumptions:** "Best practices" means mainstream pytest + Playwright + API-testing practice: isolated and idempotent tests, web-first assertions, layered clients and page objects, secrets kept out of source, and CI that doesn't hide flakiness. Severity reflects impact on the suite's reliability and trustworthiness, not style.

---

## Bottom line

The architecture is reasonable: fixtures handle DI, there are builders, page objects, client wrappers and a ui/api/hybrid split. Most of the problems are in how the pieces are wired and in what the tests actually assert.

- **Critical:** `authenticated_context` is broken. 15 of the 23 tests depend on it, and they cannot pass as written.
- **High:**
  - At least 7 tests assert nothing meaningful, or test something other than what their name says.
  - Global retries hide all of this.
  - Test data is never cleaned up and isn't unique enough to avoid colliding with leftovers.
  - A credential is hardcoded in source.

You said fixtures, builders and locators look solid. The *patterns* are solid and I don't relitigate them. The concrete defects that do live in those areas are listed in their own section (§2), kept short, because two of them are the root cause of the critical and high findings.

---

## 1. Findings by severity

### CRITICAL

**C1. `authenticated_context` raises `AttributeError`, so every test that uses it fails**
- `conftest.py:71-80` builds `AuthContext(page, account_client)`.
- `src/core/auth.py:34` then calls `self._api_client.authenticate(...)`.
- `authenticate` exists only on `AuthClient` (`src/api_clients/base_client.py:23-31`). `AccountClient` (`clients.py:11`) inherits from `BaseApiClient`, which has no such method.
- Result: every test requesting `authenticated_context` errors right after the UI login step. That is 15 of 23 tests, covering all UI, all hybrid and 3 of 4 account API tests.
- Related leftover: `account_client` takes an `auth_client` argument it never uses (`conftest.py:50`). It looks like someone meant to wire `AuthClient` in and didn't finish.
- **Fix:** have `AuthContext` take the `AuthClient` to get the token. Then call `set_auth_token` on every domain client that should be authenticated (see H5).

### HIGH

**H1. Tests that cannot fail, or don't test what they're named for**

| Test | Problem |
|---|---|
| `tests/api/test_account_api.py:20` `test_delete_account` | No assertion. Line 26 `account_client.get_account.__self__` is a no-op. A broken DELETE still passes. |
| `tests/hybrid/test_account_lifecycle.py:53` `test_delete_account_removes_from_list` | Ends at `wait_for()` with no assertion that the deleted account is absent. |
| `tests/hybrid/test_subscription_lifecycle.py:29` `test_cancel_subscription` | Clicks the form's **Cancel** button (discard edits), not "cancel subscription". It then asserts `updated["id"] == subscription["id"]`, which is a tautology. |
| `tests/hybrid/test_subscription_lifecycle.py:8` `test_update_subscription_seats` | Changes **plan code** through the misnamed `update_name` (fills "Plan code"). Seats are never touched, even though `SubscriptionBuilder.with_seats` exists. |
| `tests/hybrid/test_ticket_lifecycle.py:10` `test_update_ticket_priority` | Changes **status**, not priority. |
| `tests/ui/test_admin_console_nav.py:32` `test_billing_settings_saves_provider_key` | Finds the element with `get_by_text("Settings saved")` and then asserts its text equals "Settings saved", which is circular. It never checks that the key was persisted. |
| `tests/ui/test_search.py:35` `test_filter_tickets_by_status` | Waits for the first row, then asserts `row_count() > 0`, which is guaranteed by the wait. It never checks that the rows are actually status "open", so the filter is untested. It also relies on pre-existing data. |
| `tests/ui/test_search.py:18-20, 52-54` | `wait_for()` followed by `assert is_visible()`. The assertion is redundant; the wait already guarantees visibility. |

**Fix:** assert on the outcome:
- For the API delete test, expect a 404 from `get_account`.
- For the UI delete test, use `expect(...).to_have_count(0)`.
- Make each test do what its name says, or rename it.

**H2. Bare `except: pass` in verification helpers hides real failures**
- `tests/api/test_ticket_export_api.py:37-41`: any error becomes `False`, so the failure message loses the real cause.
- `tests/ui/test_admin_console_nav.py:25-29`: errors fall through to a second comparison.
- Bare `except` also catches `KeyboardInterrupt` and `SystemExit`.
- **Fix:** delete both helpers and use plain `assert` or `expect(locator).to_have_text(..., ignore_case=True)`.

**H3. Order-dependent tests share module-level state**
- `tests/hybrid/test_ticket_lifecycle.py:7, 31-44`: `test_second_test_relies_on_previous_ticket` reads `_CREATED_TICKET_IDS[-1]`, which another test fills in.
- Running it alone, under `-k`, under `pytest-xdist`, in random order, or as a rerun after the producer passed gives an `IndexError` or a stale ID.
- **Fix:** create the ticket in a fixture (or in the test itself) and delete the module global.

**H4. Retries are on everywhere and configured twice, which hides the problems above**
- `pytest.ini:14-15` sets `reruns = 2` for **every** run, local included. `ci.yml:31` adds `--reruns 2 --reruns-delay 2` again.
- Every hybrid test creates server-side data. A retry creates duplicates, which feed the locator collisions in §2.
- Nothing reports or fails on flaky passes; consider `--fail-on-flaky` or at least surfacing rerun counts.
- **Fix:**
  - Remove reruns from `pytest.ini`.
  - Keep at most one CI retry, apply it selectively, and track flaky tests explicitly.
  - Fix the root causes (C1, H3, §2-B).

**H5. API auth is inconsistent and mostly absent**
- Only `account_client` would ever get a token, and only through the broken `authenticated_context`.
- `ticket_client` and `subscription_client` (`conftest.py:55-62`) are never authenticated. Every API call they make (create ticket, create subscription, get, cancel) goes out without an `Authorization` header.
- Two test files bypass the clients completely:
  - `test_billing_sync_api.py:21-26` and `35-40` use raw `requests.post` with `Config.API_TOKEN`, duplicated twice. `SubscriptionClient.trigger_billing_sync` exists (`clients.py:77`) and is never used.
  - `test_ticket_export_api.py:21-26` uses raw `requests.get` with `os.getenv("SUBTRACK_API_TOKEN")`, although `TicketClient.export_ticket` exists.
- `test_account_api.py` runs a **full browser UI login** just to authenticate pure API tests. API tests should not need a browser.
- **Fix:**
  - Add a session-scoped `api_token` fixture: either the service token from `Config.API_TOKEN`, or one obtained through `AuthClient`.
  - Have every `*_client` fixture call `set_auth_token`.
  - Route all HTTP through the clients.
  - Remove `authenticated_context` from API tests.

**H6. Hardcoded credential, and a test that writes it into the shared environment**
- `src/core/config.py:26` hardcodes `INVOICING_PROVIDER_API_KEY = "sk-fake1234567890"`. This happens even though `.env.example:14` declares the env var.
- CI (`ci.yml:25-30`) doesn't pass that secret either, so the hardcoded value is what runs.
- `test_billing_settings_saves_provider_key` saves the key into the staging admin's **global billing settings**. That overwrites shared environment configuration on every run and can break billing sync for other tests or users.
- **Fix:**
  - Read the value with `os.getenv` like every other secret, and add it to CI secrets.
  - Restore the original setting in teardown, or run that test against a disposable workspace.
  - Scan git history if the value was ever real.

### MEDIUM

**M1. No test-data cleanup.** Every test creates accounts, tickets or subscriptions on shared staging and nothing deletes them. There are no yield fixtures with teardown, and `close_ticket` is never called. Data builds up across runs and retries, and the next item makes that actively harmful (§2-B). **Fix:** use factory fixtures that record created IDs and delete them in teardown.

**M2. Playwright plumbing duplicates pytest-playwright and fights it.**
- `pytest-playwright==0.5.2` is installed (`requirements.txt:5`), but `conftest.py:15-41` redefines `browser`, `context` and `page` with hardcoded `chromium` and `headless=True`.
- As a result the plugin's `--browser`, `--headed`, `--tracing retain-on-failure`, `--screenshot` and `--video` options silently do nothing.
- **Fix:** either drop the plugin or drop the custom fixtures. Then use `browser_context_args` for `base_url` and use `--tracing=retain-on-failure`.

**M3. Trace capture runs for every test, including API tests, and doesn't match the docs.**
- `_capture_trace_on_retry` is `autouse` and depends on `context` (`conftest.py:83-84`). Every API-only test therefore launches a browser context and starts tracing.
- Tracing starts unconditionally (`conftest.py:33`). The comment says "started selectively on retry", and README:47 says "on-first-retry"; neither is true. Tracing is always recorded and only the decision to save it is conditional.
- The condition at `conftest.py:90` is `A or B if hasattr(...) else False`, which parses as `(A or B) if hasattr(...) else False`. If `rep_call` is missing (for example the test failed in setup), the trace is **not** saved even on a retry.
- **Fix:** use the plugin's `--tracing=retain-on-failure`. Or make the fixture non-autouse and apply it only to tests that use `page`, with explicit parentheses.

**M4. No web-first assertions.**
- `playwright.sync_api.expect` is used nowhere (grep: 0 hits).
- Assertions are snapshots taken after a manual `wait_for()`: `inner_text() ==` (`test_search.py:32`), `is_visible()` and `count()`. A snapshot read like `inner_text()` doesn't retry, so it races any re-render.
- **Fix:** use `expect(locator).to_have_text/to_be_visible/to_have_count`. That also removes most of the hand-written `wait_for()` calls.

**M5. UI login on every test.** `authenticated_context` is function-scoped and drives the login form each time (`auth.py:28-32`). **Fix:** log in once per session (through the API or UI), save `storage_state`, and create contexts from it. That removes a large chunk of runtime and a common source of flakiness.

**M6. Repeated hybrid steps are written out inline in every test.** The "create via API → open in UI → modify → save → verify via API" sequence is copied in `test_account_lifecycle.py:13-50`, `test_subscription_lifecycle.py:8-27` and `test_ticket_lifecycle.py:10-28`. Extract step helpers or fixtures, for example `open_account_in_ui(account)`.

**M7. API clients raise on every non-2xx, so negative tests can't be written.** Every client method calls `raise_for_status()` (`clients.py` throughout). That makes it awkward to assert a 404 after a delete, which probably explains H1's no-op assertion. The same few lines of post, raise and `.json()` are also repeated about 13 times. **Fix:** add a single `_request()` in `BaseApiClient` that returns the response (or offers `expect_status=`) and logs request and response on failure.

**M8. CI gaps.**
- Markers `smoke`, `billing` and `tickets` are declared (`pytest.ini:17-20`) but applied to no test (0 `pytest.mark` hits), and `--strict-markers` is off.
- There is no smoke/regression split, no parallelism (`pytest-xdist`), no JUnit XML for the CI test summary, no `timeout-minutes`, and no pip/browser caching.
- Secrets are unavailable to PRs from forks, so those runs fail at login.

### LOW

- **L1. Naming inconsistencies.**
  - `src/pages/AdminConsole.py` and `SettingsScreen.py` use PascalCase module names (PEP 8) and classes without the `*Page` suffix used everywhere else.
  - `list_pages.py` holds two classes, while everywhere else it's one per file.
  - `factories/factories.py` contains `*Builder` classes.
  - `update_name()` on `SubscriptionModifyPage` and `TicketModifyPage` actually fills "Plan code" and "Ticket subject", a copy-paste name that leads directly to H1's mislabeled test.
- **L2. Duplicate and dead code.**
  - `AuthContext.login_as` re-implements `LoginPage.login` with the same locators. `LoginPage` is never used.
  - `ContactBuilder`, `ContactModifyPage`, `trigger_billing_sync`, `close_ticket`, `with_plan_tier`, `with_seats` and `Config.DEFAULT_TIMEOUT_MS` are unused. Timeouts are hardcoded as 10/15 s in each client method instead.
  - The four `*ModifyPage` classes are near-identical; they could share a parameterized base.
- **L3. Raw locators in tests.** `test_account_lifecycle.py:20,40`, `test_search.py:28` and `test_account_lifecycle.py:63` use `page.get_by_role/get_by_test_id` directly because there is no `AccountListPage` or search-results page object.
- **L4. Config fails late and silently.** `ADMIN_USERNAME`, `ADMIN_PASSWORD` and `API_TOKEN` default to `None`, so a missing `.env` shows up as a confusing login or 401 failure. URLs silently default to staging. Validate required settings once at session start.
- **L5. Documentation drift.**
  - README claims "Allure-style trace capture" and "`on-first-retry`", and says `core/` holds browser fixture helpers; none of that is accurate.
  - `requirements.txt:1-2` calls Playwright 1.47.0 (2024) "current", but it is about two years old as of this review.
  - Several docstrings record known defects ("Does not follow the naming convention", "no-op access, not a real assertion") instead of the defects being fixed or tracked as issues.
- **L6. Misplaced test.** `test_create_ticket_and_record_id` is pure API but lives in `tests/hybrid/`.

---

## 2. Your "solid" areas: only the concrete exceptions

The patterns are fine and need no rework. These are the specific defects inside them.

**A. Fixtures (DI composition is the right approach).** The defects are:
- the broken auth wiring (C1);
- the unused `auth_client` dependency;
- unauthenticated ticket and subscription clients (H5);
- an autouse fixture that forces a browser onto API tests (M3);
- overriding pytest-playwright's fixtures (M2);
- no teardown or cleanup (M1).

**B. Builders (the fluent builder pattern is good).** One real defect: **the data isn't unique across runs.**
- `_seq = itertools.count(1)` (`factories.py:12`) restarts at 1 in every process, so every run creates "Acme Test Account 1", "Test ticket 1" and so on again. It also collides under xdist.
- `SubscriptionBuilder` gives every subscription `plan_code="PRO-MONTHLY"`.
- Tests use fixed names: "Globex Test Corp" and "Cannot access invoices".
- With no cleanup (M1), these names pile up on staging.
- **Fix:** add a run-unique suffix (`uuid4().hex[:8]`) to names, subjects and anything else used as a UI lookup key.

**C. Locators (semantic `get_by_role/label/test_id`, no CSS/XPath; confirmed with 0 hits).** The defect is how they combine with B:
- `get_by_role("link", name=...)` uses **substring** matching by default. "Acme Test Account 1" also matches "Acme Test Account 10" through "…19", plus leftovers from earlier runs.
- `SubscriptionListPage.open_subscription(plan_code)` (`list_pages.py:22-23`) looks up the link by `plan_code`, which is identical for every subscription.
- Both lead to strict-mode violations or opening the wrong record.
- **Fix:** use unique data (B) plus `exact=True`, or address rows by `get_by_test_id` and ID.

---

## 3. What is genuinely fine (not discussed further)

- ui/api/hybrid directory split
- Builder API shape
- Semantic locator strategy
- Page objects that stay free of assertions
- Client-per-domain design
- `timeout=` on every `requests` call
- `.env.example` plus `python-dotenv`
- Most secrets sourced from the environment
- Pinned dependencies
- HTML report and trace artifacts uploaded with `if: always()`
- No `time.sleep` or `wait_for_timeout` anywhere (grep: 0 hits)

---

## 4. Suggested fix order

1. **C1 + H5:** fix auth wiring. Add a session `api_token` fixture, authenticate all clients, and route all HTTP through the clients.
2. **H1 + H2:** make every test assert its outcome, rename mislabeled tests, and delete the bare-`except` helpers.
3. **§2-B + M1:** make test data unique and add cleanup through factory fixtures; use `exact=True` on name-based locators.
4. **H3:** remove the shared module state.
5. **H4:** turn off default reruns and surface flaky tests.
6. **H6:** move the provider key to env/CI secrets and stop mutating global settings, or restore them.
7. **M2–M5:** adopt pytest-playwright properly (tracing, `expect`, `storage_state`), and stop opening a browser for API tests.
8. **M6–M8, then the L items.**
