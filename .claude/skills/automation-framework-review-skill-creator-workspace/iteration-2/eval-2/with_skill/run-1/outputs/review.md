# Automation Framework Issues: SubTrack Admin (pytest + Playwright + requests)

**Scope:** `medium-framework/` in full: `conftest.py`, `pytest.ini`, `requirements.txt`, `.env.example`, `.github/workflows/ci.yml`, `src/core` (2 files), `src/api_clients` (2), `src/factories` (1), `src/pages` (9 modules, 10 classes), `tests/{api,hybrid,ui}` (9 files, 23 test functions). `__pycache__` ignored.

**Excluded from this review:** Nothing was excluded. You described fixtures, test-data builders and locators as solid, so I did not question the design choices there: pytest fixture DI, the builder pattern, and role/test-id locators. I still checked the code in those areas, and three defects turned up: auth wiring in fixtures, cross-run uniqueness in builders, and one lookup key in locators. Each one comes with its own traced evidence below.

**Baseline for naming:** No linter or formatter config exists (0 of `pyproject.toml`, `setup.cfg`, `.flake8`, `ruff.toml`, `tox.ini`, `.editorconfig`, `.pre-commit-config.yaml`), so naming is judged against PEP 8 and the repo's own stated `*Page` / `*Client` / `test_*.py` conventions.

**Verdict up front:**
- **The authenticated-session fixture cannot work as written.** `AuthContext.login_as` calls `authenticate()` on an `AccountClient`, which has no such method. That breaks setup for 15 of 23 tests. The ticket and subscription API clients are also never given a token at all.
- **The suite cannot be re-run against the same environment.** Builder names restart at 1 in every process, several tests hardcode entity names, subscriptions are looked up by a plan code that every subscription shares, and nothing cleans up the 19 entities the tests create. Playwright strict-mode lookups will collide. `reruns = 2` hides some of this and makes the data buildup worse.
- **Smaller problems:** 5 of 23 tests do not actually verify the behavior they are named for, one test depends on another having run first, and API-only tests bypass the client and auth layer in 3 places.

---

## 1. `authenticated_context` raises `AttributeError` before any test body runs `[Impact: High | Effort: Low]`

- `conftest.py:71-80` builds `AuthContext(page, account_client)`.
- `src/core/auth.py:34` then calls `self._api_client.authenticate(...)`.
- `authenticate` is defined only on `AuthClient` (`src/api_clients/base_client.py:23-31`). `AccountClient(BaseApiClient)` (`src/api_clients/clients.py:11-33`) does not have it, and `BaseApiClient` has no `__getattr__`. A repo-wide grep finds `authenticate` in exactly 2 places: the definition and this call.
- Runtime trace: the UI login at `auth.py:28-32` succeeds, then line 34 raises `AttributeError: 'AccountClient' object has no attribute 'authenticate'` during fixture setup.
- **15 of 23 tests** request `authenticated_context`. All 15 error in setup, and `reruns = 2` retries each one twice more for no benefit.
- The intended wiring is visible but unused. The `auth_client` fixture (`conftest.py:44-46`) is injected into `account_client` (`conftest.py:50`) and then ignored. A grep finds `auth_client` only at those two lines.

**Fix:** Pass `auth_client` into `AuthContext` to obtain the token, then apply the token to the domain clients (see finding 2).

## 2. Ticket and subscription API clients never get an auth token `[Impact: High | Effort: Low]`

- `set_auth_token` is called exactly once in the repo (`auth.py:35`), and only on the `account_client` passed into `AuthContext`.
- `ticket_client` (`conftest.py:55-57`) and `subscription_client` (`conftest.py:60-62`) are built with no token and never pass through `AuthContext`.
- Every `TicketClient` and `SubscriptionClient` call is therefore anonymous. That covers all 6 API tests in `test_subscription_api.py`, `test_billing_sync_api.py` and `test_ticket_export_api.py`, 2 tests in `test_ticket_lifecycle.py`, and the API setup and verification calls in the hybrid ticket and subscription tests.
- The billing tests add `Authorization: Bearer ...` by hand to their raw calls (`test_billing_sync_api.py:24`), which suggests the API does require auth. If it does, `raise_for_status()` fails on every one of these calls.
- Shares a root cause with finding 1 (auth wiring), but it needs its own fix. Making `AuthContext` work does not reach these two fixtures.

## 3. Test data is not unique across runs, so Playwright lookups collide on a persistent environment `[Impact: High | Effort: Low]`

**Builder counter restarts every run.**
- `src/factories/factories.py:12`: `_seq = itertools.count(1)` resets every process.
- Run 2 recreates `Acme Test Account 1..n`, `billing.1@example.com`, `Test ticket n` and so on, while run 1's records are still there (see finding 4).
- Tests then click by name, for example `page.get_by_role("link", name=account["name"]).click()` at `test_account_lifecycle.py:20,40` and `test_search.py:28`. That resolves to 2+ elements, which is a strict-mode violation.
- `get_by_role(name=...)` matches substrings by default, so `Acme Test Account 1` also matches `...10` through `...19` within a single run whenever those rows are visible together.
- If the API enforces unique billing emails, `create_account` fails before the UI is reached.

**Hardcoded literal names.**
- `test_search.py:13` uses `"Globex Test Corp"` and `test_search.py:47` uses `"Cannot access invoices"`.
- On the second run against the same environment, `result.wait_for()` (`:19`, `:53`) hits two matching links and fails deterministically.

**The fix already exists in the same file.** `SubscriptionBuilder` gives `external_ref` a `uuid.uuid4()` (`factories.py:91`). Apply the same per-entity unique suffix to account names and emails, ticket subjects and contact emails, and pass `exact=True` on name-based link lookups.

## 4. No cleanup of test-created data `[Impact: Medium | Effort: Medium]`

- Tests make 19 `create_account` / `create_ticket` / `create_subscription` calls.
- Only 2 deletes exist (`test_account_api.py:22`, `test_account_lifecycle.py:55`), and in both the delete is the behavior under test, not cleanup.
- There are 0 `yield`-based cleanup fixtures and 0 `addfinalizer` calls. `close_ticket` and `cancel_subscription` exist, but neither is used for teardown.
- Each run leaves at least 17 records behind, up to 3x that when tests are rerun (finding 10). This accumulation is what turns finding 3 from theoretical into certain.

**Fix:** Have each `create_*` go through a fixture that yields the entity and deletes it on teardown, so cleanup also runs when the test fails.

## 5. `SubscriptionListPage.open_subscription` looks up by a value every subscription shares `[Impact: Medium | Effort: Low]`

- `src/pages/list_pages.py:22-23` clicks `get_by_role("link", name=plan_code)`.
- `SubscriptionBuilder` gives every subscription `plan_code = "PRO-MONTHLY"` (`factories.py:88`).
- pytest runs `tests/api` before `tests/hybrid`, so by the time `test_subscription_lifecycle.py` runs, 4 `PRO-MONTHLY` subscriptions already exist from `test_subscription_api.py` (2) and `test_billing_sync_api.py` (2). Both hybrid subscription tests (`:16`, `:35`) then hit a strict-mode violation, even on a fresh environment.

**Fix:** Look up by the unique `external_ref` or by `id`.

## 6. Tests that execute steps but verify nothing, or verify a tautology `[Impact: Medium | Effort: Low]`

Mandatory grep result: 2 of 23 test functions contain no `assert` at all, and 3 more assert something that cannot fail for the behavior under test.

| Test | Problem |
| --- | --- |
| `tests/api/test_account_api.py:20` `test_delete_account` | 0 asserts. Line 26 is a no-op attribute access. A broken DELETE passes. |
| `tests/hybrid/test_account_lifecycle.py:53` `test_delete_account_removes_from_list` | 0 asserts. Ends with `wait_for()` on the results container, so a deleted account still listed in search passes. |
| `tests/hybrid/test_subscription_lifecycle.py:29` `test_cancel_subscription` | Asserts `updated["id"] == subscription["id"]` (`:42`), which is true for any GET of that id. |
| `tests/ui/test_admin_console_nav.py:32` `test_billing_settings_saves_provider_key` | Locates the element by the text `"Settings saved"` (`:42`), then asserts the element's text is `"Settings saved"` (`:44`). Circular. It never checks that the key was persisted. |
| `tests/ui/test_search.py:35` `test_filter_tickets_by_status` | Asserts `row_count() > 0` (`:43`). It never checks that the rows have status `open`, so an ignored filter still passes. |

## 7. Test names claim coverage that the body doesn't provide `[Impact: Medium | Effort: Low]`

3 of 23 test names describe a behavior their body does not exercise, which leaves real coverage gaps hidden in the report:

| Test | Named behavior | What it actually does | Coverage gap |
| --- | --- | --- | --- |
| `test_ticket_lifecycle.py:10` `test_update_ticket_priority` | Update priority | Changes **status** (`:23`, `:28`) | No UI test for priority |
| `test_subscription_lifecycle.py:8` `test_update_subscription_seats` | Update seats | Changes **plan code** via `update_name` (`:21`, `:26`) | No UI test for seats |
| `test_subscription_lifecycle.py:29` `test_cancel_subscription` | Cancel the subscription | Clicks the edit form's **Cancel** button (`:39`) | No UI test for cancelling a subscription |

The `update_name` method compounds this. On `SubscriptionModifyPage` it fills "Plan code" (`subscription_modify_page.py:10-11`), and on `TicketModifyPage` it fills "Ticket subject" (`ticket_modify_page.py:10-11`). 2 of 4 `update_name` methods do not update a name.

## 8. Order-dependent test via module-level mutable state `[Impact: Medium | Effort: Low]`

- `tests/hybrid/test_ticket_lifecycle.py:7` declares `_CREATED_TICKET_IDS = []`.
- `test_create_ticket_and_record_id` (`:31`) appends to it, and `test_second_test_relies_on_previous_ticket` (`:37`) reads `[-1]` (`:42`).
- Running the second test on its own (`-k`, `--lf`, IDE single-test run, or any future `pytest-xdist` split) gives `IndexError` instead of an assertion failure.
- This is the only inter-test dependency found (1 module-level mutable list in 9 test modules).
- **Fix:** Have the test create its own ticket using `TicketBuilder().with_priority("high")`.

## 9. Trace capture throws traces away on setup failures, and its own docs don't match it `[Impact: Medium | Effort: Low]`

`conftest.py:90` reads:

```python
if rerun_count > 1 or request.node.rep_call.failed if hasattr(request.node, "rep_call") else False:
```

**How Python parses it.** The conditional expression has the lowest precedence, so this is `(rerun_count > 1 or rep_call.failed) if hasattr(node, "rep_call") else False`.

**Traced values.**
- `rep_call` is set by the hook at `:96-100` only when the call phase runs.
- When a fixture fails in setup, as every `authenticated_context` failure in finding 1 does, `rep_call` never exists. The expression is `False` on every attempt, including retries where `execution_count` is 2 or 3, so `context.tracing.stop()` discards the trace.
- Result: the most common failure class in this suite (login/session setup) never produces a trace, even though the docstring at `:85-87` promises one "for anything pytest-rerunfailures had to retry".

**Docs that don't match the code.**
- The comment at `conftest.py:30-31` says tracing "can be started selectively on retry", but `:33` starts it unconditionally for every test.
- `README.md:13,47` describes "Allure-style" capture `on-first-retry`, but no Allure is installed and the logic is not on-first-retry.

**KISS note.** `pytest-playwright==0.5.2` is installed (`requirements.txt:5`), but `conftest.py` redefines its `browser`, `context` and `page` fixtures, which shadows the plugin's built-in `--tracing retain-on-failure` and `--screenshot` options. This hand-rolled hook rebuilds that feature with a bug.

**Fix:** Delete the custom fixtures and hook, and use the plugin's options.

## 10. Every API-only test pays for a browser context with full tracing `[Impact: Medium | Effort: Low]`

- `_capture_trace_on_retry` is `autouse=True` and depends on `context` (`conftest.py:83-84`). `context` starts tracing with screenshots, snapshots and sources (`:33`).
- So all 9 tests in `tests/api/`, and the 2 API-only tests in `test_ticket_lifecycle.py`, open a Chromium context and record a trace they never use.
- The 3 tests in `tests/api/test_account_api.py` also request `authenticated_context`, which drives a full UI login (`auth.py:28-32`) just to get an API token.
- This works against Fast, and against testing at the lowest level that covers the behavior.

**Fix:** Scope trace capture to tests that use `page`, and give API tests an API-only auth fixture.

## 11. API tests bypass the client layer and the typed auth concept `[Impact: Medium | Effort: Low]`

**Raw HTTP calls.** 2 test files import `requests` directly and make 3 raw HTTP calls:
- `test_billing_sync_api.py:21`, `:35`
- `test_ticket_export_api.py:22`

The matching wrappers already exist. `SubscriptionClient.trigger_billing_sync` (`clients.py:77`) has **0 callers** in the repo. `TicketClient.export_ticket` (`clients.py:49`) is used by the neighboring test in the same file (`test_ticket_export_api.py:46`).

**Credentials expressed three ways.** The auth concept appears in three disconnected forms:
- the typed `User` / `AuthContext` (`auth.py`, `conftest.py:65-80`)
- `Config.API_TOKEN` pasted into a header (`test_billing_sync_api.py:24`, `:38`)
- `os.getenv("SUBTRACK_API_TOKEN")` read inline (`test_ticket_export_api.py:21`), which even bypasses `Config`

**Lost failure context.** The raw calls also skip `raise_for_status()`. `test_billing_sync_records_external_reference` (`:41-42`) never checks the status code, so an error response surfaces as a `KeyError` instead of an HTTP failure.

## 12. Retries mask failures: `reruns = 2` in two places, with no flaky tracking `[Impact: Medium | Effort: Low]`

Mandatory grep result: the configured retry value is **2 reruns with a 2 s delay**, in two places:
- `pytest.ini:14-15`
- `ci.yml:31` (`pytest --reruns 2 --reruns-delay 2`)

What is missing:
- no `--only-rerun` filter, so deterministic failures like findings 1 and 5 also run 3 times
- 0 `@pytest.mark.flaky` or `xfail` markers
- no quarantine list

Each rerun of a data-creating test adds more orphaned records (finding 4), so the retry policy feeds the collisions in finding 3. `README.md:14` gives "CI stability" as the reason, which suggests the team already knows the suite is not reliable.

## 13. Hardcoded credential in `Config`, inconsistent with the env-driven design `[Impact: Medium | Effort: Low]`

Mandatory grep result: **1** credential assigned to a literal, at `src/core/config.py:26`: `INVOICING_PROVIDER_API_KEY = "sk-fake1234567890"`.
- Every other credential in the class comes from `os.getenv` (`:18-21`).
- `.env.example:14` documents `INVOICING_PROVIDER_API_KEY` as an env var, but `Config` never reads it.
- `ci.yml:25-30` does not pass it either.
- The value looks fake, but the `sk-` prefix will trip secret scanners, and the pattern invites a real key to land in the same spot.

The other 3 `changeme` placeholders in `.env.example:8,11,14` are template values and are not counted.

## 14. A UI test overwrites shared environment configuration and never restores it `[Impact: Medium | Effort: Low]`

- `test_admin_console_nav.py:40` saves `Config.INVOICING_PROVIDER_API_KEY` (the fake key from finding 13) into the environment's real Billing settings through `SettingsScreen.set_invoicing_provider_key` (`SettingsScreen.py:15-17`).
- There is no teardown that restores the previous value.
- Anyone else using that staging admin console, including manual QA and any provider integration, inherits the fake key after each run.

## 15. Missing business-step layer: 5 hybrid tests re-compose the same 4-step skeleton inline `[Impact: Medium | Effort: Medium]`

- `test_account_lifecycle.py:13,33`, `test_subscription_lifecycle.py:8,29` and `test_ticket_lifecycle.py:10` each inline the same sequence: create via API, open from the dashboard and list, `wait_until_loaded`, modify, `save_changes`, re-GET and assert. Their own `# step 1..4` comments mark it.
- No `steps/` or `flows/` module exists.
- That is 5 of 8 hybrid tests, and the account file's docstring (`test_account_lifecycle.py:3-6`) already names the missing `create_and_open_account` / `modify_and_save` helpers.
- A step layer would also be the natural home for the missing account-list navigation (finding 17).

## 16. Four `*ModifyPage` classes are copy-paste clones `[Impact: Medium | Effort: Low]`

- `account_modify_page.py`, `contact_modify_page.py`, `ticket_modify_page.py` and `subscription_modify_page.py` each declare the same 5 methods, 20 in total.
- Diffing each against `AccountModifyPage` shows only 3 changed lines per file: the heading text (`:8`), the field label (`:11`) and the success toast text (`:18`).
- `update_status` and `cancel_changes` are byte-identical in all 4 files.

**Fix:** One `EntityModifyPage(page, entity="Ticket", name_field="Ticket subject")`. This would also remove the misleading `update_name` naming from finding 7. It is independent of finding 15: a step layer would still call 4 duplicate classes.

## 17. Tests reach past page objects into raw `page.get_by_*` `[Impact: Low | Effort: Low]`

- There are 11 raw `page.get_by_*` calls across 3 test files: `test_account_lifecycle.py:20,40,63`, `test_admin_console_nav.py:14,15,42` and `test_search.py:18,28,30,42,52`.
- Account-list navigation has no page object, while `TicketListPage` and `SubscriptionListPage` do (`list_pages.py`). So "open account by name" is hand-written in 2 tests and "find search result" in 3.
- **Fix:** Add an `AccountListPage` and a `SearchResults` component, modeled on `TicketListPage`.

## 18. Core auth duplicates the unused `LoginPage`, and other dead or unused abstractions `[Impact: Low | Effort: Low]`

`src/core/auth.py:28-31` re-implements `LoginPage.goto()` and `LoginPage.login()` (`login_page.py:9-15`) line for line, so login-screen locators live in the core layer.

Repo-wide reference counts outside each symbol's own definition (docstring mentions excluded):

| Unused symbol | References |
| --- | --- |
| `LoginPage` | 0 |
| `ContactModifyPage` | 0 |
| `ContactBuilder` | 0 |
| `TicketClient.close_ticket` | 0 |
| `Config.DEFAULT_TIMEOUT_MS` | 0 |
| `auth_client` fixture | injected at `conftest.py:50` and never used |
| `smoke` / `billing` / `tickets` markers | 0 (see finding 21) |

The contact page and builder imply contact coverage that `README.md:4` advertises, but no test exercises contacts.

## 19. UI checks are one-shot reads, not web-first assertions `[Impact: Low | Effort: Low]`

**Mandatory grep result:** 0 unconditional waits (`time.sleep`, `wait_for_timeout`, `setTimeout` and `implicitlyWait` all return 0).

**The problem:** 0 uses of Playwright's retrying `expect(...)`. All 6 UI assertions are single reads: `is_visible()` at `test_admin_console_nav.py:15` and `test_search.py:20,54`, `inner_text()` at `test_admin_console_nav.py:44` and `test_search.py:32`, and `.count()` at `test_search.py:43`. The `is_visible()` calls follow a `wait_for()`, so they are safe but redundant.

**Two reads are real races:**
- `test_search.py:32`: `badge.wait_for()` waits only for visibility, then `inner_text()` reads once. A badge that renders "Loading..." before "Suspended" fails intermittently.
- `test_search.py:42-43`: `.first.wait_for()` succeeds on the pre-filter rows already on screen.

The `test_search.py:3-5` docstring claims the suite relies on Playwright "assertions" for waiting, but no Playwright assertions are used.

**Fix:** Use `expect(badge).to_have_text("Suspended")` and similar web-first assertions.

## 20. Bare `except:` swallows in verification helpers `[Impact: Low | Effort: Low]`

**Mandatory grep result:** 2 catch sites in the repo, and both swallow.

| Site | Helper | What happens |
| --- | --- | --- |
| `tests/api/test_ticket_export_api.py:37-41` | `_content_matches_expected_header` | Any error returns `False` |
| `tests/ui/test_admin_console_nav.py:25-29` | `_values_are_equivalent` | Any error falls through to `actual == expected` |

**Traced runtime values:** neither helper can turn a failure into a pass.
- In `_values_are_equivalent`, the fallback is only reached when `.strip()` raises, for example when `actual` is `None`, and `None == "Settings saved"` is `False`.
- `export_ticket` always returns `bytes` (`clients.py:54`), so the slice in the other helper cannot raise for real inputs.

The docstring at `test_admin_console_nav.py:21-23` claims a false pass is possible; it is not. The real defects are these:
- "Could not check" and "checked, mismatch" both surface as a bare `assert False` with the cause discarded.
- Bare `except:` also catches `KeyboardInterrupt` and `SystemExit`.

**Fix:** Delete both helpers and assert directly. Neither try block guards a reachable error.

## 21. Markers are declared but never applied, so CI has no fast subset and the report is flat `[Impact: Low | Effort: Low]`

- `pytest.ini:17-20` declares `smoke`, `billing` and `tickets`. There are 0 `pytest.mark` usages in `tests/`.
- `ci.yml:3-7,31` runs the entire suite on every push and pull request to `main`. There is no smoke-on-PR / full-on-merge split.
- The pytest-html report cannot be grouped by domain.
- There are 0 `skip(reason=...)` or `xfail(reason=...)` usages, so a known, ticketed failure looks the same as a new one.
- `--strict-markers` is not set, so a typo in a marker name would pass silently.

## 22. API client methods repeat the same send / raise / parse body with literal timeouts `[Impact: Low | Effort: Low]`

- 12 of 12 methods in `clients.py`, plus `AuthClient.authenticate`, repeat the same body: `self.session.<verb>(self._url(...), timeout=N)`, then `raise_for_status()`, then `.json()`.
- `timeout=` literals (10 or 15) appear 13 times in `src/api_clients` and 3 more times in the raw test calls.
- `Config.DEFAULT_TIMEOUT_MS` (0 references) is unused, and is in milliseconds while `requests` expects seconds.

**Fix:** A `BaseApiClient._request(method, path, **kw)` helper with a single timeout default.

## 23. No `.gitignore` for `.env`, reports or traces `[Impact: Medium | Effort: Low]`

- There is no `.gitignore` in the framework root (`find . -name .gitignore` returns 0 hits).
- `.env.example:1` and the README tell users to create a real `.env` holding the admin password and API token, and say "Never commit the real .env file". Nothing enforces that.
- `report.html` (`pytest.ini:10`), `traces/` (`conftest.py:91`) and `__pycache__/` are also unignored. A committed `__pycache__/` is already present.
- Assumption: this directory is the repository root. A parent-repo `.gitignore` was not evaluated.

## 24. Naming outliers against PEP 8 and the repo's own conventions `[Impact: Low | Effort: Low]`

- **Page-object classes:** 8 of 10 end in `Page`. The outliers are `AdminConsole` and `SettingsScreen`.
- **Page modules:** 7 of 9 are `snake_case`. The outliers are `src/pages/AdminConsole.py` and `src/pages/SettingsScreen.py`, which are PascalCase module names and violate PEP 8.
- **Other:** `test_second_test_relies_on_previous_ticket` names an implementation dependency rather than a behavior. `test_admin_console_nav.py:33` has an in-function `import`.
- Misnamed tests and methods that hide coverage gaps are covered separately in finding 7.

---

## FIRST principles

| Principle | Verdict | Evidence |
| --- | --- | --- |
| **Fast** | Fails | All 23 tests create a traced Chromium context through the autouse fixture (`conftest.py:83-84`), including 11 API-only tests. 3 API tests also do a full UI login. Reruns add 2 s delays and retry deterministic failures (findings 10 and 12). No parallel execution is configured (0 `xdist` / `-n` hits). |
| **Independent** | Fails | `_CREATED_TICKET_IDS` order dependency (`test_ticket_lifecycle.py:7,42`). `test_billing_settings_saves_provider_key` mutates shared environment config (findings 8 and 14). |
| **Repeatable** | Fails | Builder sequence resets per process, literal names `Globex Test Corp` and `Cannot access invoices` are reused, the plan code lookup key is shared, and there is 0 cleanup for 19 creates. A second run against the same environment collides (findings 3, 4 and 5). No hardcoded dates or timestamps found. |
| **Self-validating** | Fails | 2 of 23 tests have no assertion. 3 more have tautological or non-discriminating assertions (finding 6). |
| **Timely** | N/A statically | Cannot be judged from the repo. |

## Recommended actions, in priority order

Ordered by Impact (High first), then Effort (Low first).

1. **Fix `AuthContext` wiring.** Authenticate with `auth_client` instead of `account_client` (finding 1). `[High | Low]`
2. **Authenticate `ticket_client` and `subscription_client`.** Apply the session token to every domain client, not just `account_client` (finding 2). `[High | Low]`
3. **Make test data unique across runs.** Use a uuid-based suffix in every builder, remove the literal names in `test_search.py`, and use `exact=True` on name lookups (finding 3). `[High | Low]`
4. **Look up subscriptions by a unique key.** Use `external_ref` or `id`, not `plan_code` (finding 5). `[Medium | Low]`
5. **Give the five non-validating tests real assertions** (finding 6). `[Medium | Low]`
6. **Rename or fix the three misnamed tests**, and add the missing priority, seats and cancel-subscription coverage (finding 7). `[Medium | Low]`
7. **Remove the module-level ticket-id list.** Make the dependent test self-contained (finding 8). `[Medium | Low]`
8. **Replace the hand-rolled tracing** with pytest-playwright's `--tracing retain-on-failure` and `--screenshot only-on-failure`, or at minimum fix the `conftest.py:90` precedence (finding 9). `[Medium | Low]`
9. **Stop API tests from launching a browser or logging in through the UI** (finding 10). `[Medium | Low]`
10. **Route the 3 raw `requests` calls through the existing clients and the typed auth path** (finding 11). `[Medium | Low]`
11. **Reduce retries to 0 by default**, or add `--only-rerun` plus explicit `flaky` markers with a tracked quarantine list (finding 12). `[Medium | Low]`
12. **Read `INVOICING_PROVIDER_API_KEY` from the environment** and add it to the CI secrets (finding 13). `[Medium | Low]`
13. **Restore the billing provider key in teardown**, or move that test to a disposable workspace (finding 14). `[Medium | Low]`
14. **Collapse the four `*ModifyPage` clones** into one parameterized page object (finding 16). `[Medium | Low]`
15. **Add a `.gitignore`** covering `.env`, `report.html`, `traces/` and `__pycache__/` (finding 23). `[Medium | Low]`
16. **Add teardown fixtures that delete or close every created entity** (finding 4). `[Medium | Medium]`
17. **Introduce a `steps/` layer** (`create_and_open_*`, `modify_and_save`) and convert the 5 hybrid tests to use it (finding 15). `[Medium | Medium]`
18. **Add `AccountListPage` and a search-results component**, and remove the 11 raw `page.get_by_*` calls from tests (finding 17). `[Low | Low]`
19. **Remove dead code or put it to use.** Make `AuthContext` use `LoginPage`. Delete or cover `ContactModifyPage`, `ContactBuilder`, `close_ticket` and `DEFAULT_TIMEOUT_MS` (finding 18). `[Low | Low]`
20. **Switch UI assertions to `expect(...)` web-first assertions** (finding 19). `[Low | Low]`
21. **Delete the two bare-`except` helpers** and assert directly (finding 20). `[Low | Low]`
22. **Apply the declared markers**, add `--strict-markers`, run `-m smoke` on pull requests and the full suite on merge, and use `xfail(reason=<ticket>)` for known issues (finding 21). `[Low | Low]`
23. **Add a `BaseApiClient._request` helper** with a single timeout default (finding 22). `[Low | Low]`
24. **Rename `AdminConsole` and `SettingsScreen`** to `admin_console_page.py` / `AdminConsolePage` and `settings_page.py` / `SettingsPage` (finding 24). `[Low | Low]`

---

## Checklist tab input

Rows are limited to checks this code review can answer. `Tools`, `Strategy` and `AI Usage` rows, and interview-only `Running` and `Processes` rows, are omitted. The "Tests remain independent under parallel execution" row is omitted because no parallel execution is configured.

| Section | Check | Status (+/-) | Comments |
| --- | --- | --- | --- |
| Framework | Framework is consistent | - | Auth is expressed three ways: `User`/`AuthContext`, `Config.API_TOKEN` and `os.getenv` (finding 11). `update_name` fills a non-name field in 2 of 4 modify pages (finding 7). |
| Framework | Framework follows a layered architecture | - | 3 raw `requests` calls in 2 API test files and 11 raw `page.get_by_*` calls in 3 test files bypass the domain layer. `core/auth.py` holds login-screen locators. No step layer (findings 11, 15, 17, 18). |
| Framework | Framework complies with DRY | - | 4 `*ModifyPage` clones (20 methods, only 3 lines differ per file). 5 hybrid tests repeat one 4-step skeleton. 13 client methods repeat the same body (findings 15, 16, 22). |
| Framework | Framework complies with KISS | - | Hand-rolled tracing fixture and hook re-implement pytest-playwright's built-in `--tracing` and introduce a precedence bug at `conftest.py:90` (finding 9). |
| Framework | Framework complies with YAGNI | - | 0 references to `LoginPage`, `ContactModifyPage`, `ContactBuilder`, `close_ticket` and `DEFAULT_TIMEOUT_MS`. The `auth_client` fixture is unused, and 3 markers are declared but never applied (findings 18, 21). |
| Framework | Framework complies with SOLID | + | No god base class (`BaseApiClient` is 20 lines), no closed switch chains and no LSP or ISP breaks. The one DIP-style inconsistency (raw `requests` in 2 tests) is logged under layering (finding 11). |
| Framework | Framework complies with language standards | - | No linter config; judged against PEP 8. 2 of 9 page modules are PascalCase, and 2 of 10 page classes lack the `Page` suffix (finding 24). |
| Framework | Presetups are implemented at the optimal available level | - | Data presetup is API-based (correct level), but the auth presetup raises `AttributeError` for 15 of 23 tests, ticket and subscription clients are never authenticated, and API tests log in through the UI (findings 1, 2, 10). |
| Framework | Unconditional waits are not a common practice | + | 0 `time.sleep` / `wait_for_timeout` / `setTimeout` hits. Separately, 0 `expect()` web-first assertions, and 2 one-shot reads are racy (finding 19). |
| Framework | Tests are atomic and independent | - | Module-level `_CREATED_TICKET_IDS` order dependency. Shared-config mutation. Cross-run name collisions plus 0 cleanup for 19 creates (findings 3, 4, 5, 8, 14). |
| Framework | Test implementation is done at the optimal level (API, UI...) | - | All 11 API-only tests start a traced browser context, and 3 also do a UI login (finding 10). The hybrid tests' level choice (API setup, UI action, API verify) is appropriate. The overall split needs the questionnaire's stated strategy. |
| Framework | Core libraries/framework/language versions are reasonably current | + | `playwright==1.47.0`, `pytest==8.3.3`, Python 3.11. Playwright is about 2 years old as of this review but has every capability the fixes need (`expect`, tracing, `exact=`). |
| Framework | No hardcoded credentials/secrets in the test codebase | - | 1 hit: `config.py:26` `INVOICING_PROVIDER_API_KEY = "sk-fake1234567890"`, despite `.env.example:14` documenting it as an env var (finding 13). |
| Running | Steps have a sufficient level of documentation for reporting | - | 0 markers applied, so the HTML report is flat. 3 test names misstate what they test (findings 7, 21). |
| Running | When tests fail, there are mechanisms to easily find the cause | - | HTML report and traces are uploaded (`ci.yml:33-46`), but traces are discarded on every setup-phase failure because of the `conftest.py:90` precedence. Swallowing helpers reduce failures to a bare `assert False` (findings 9, 20). |
| Running | Test stability is at a sufficient level | - | `reruns = 2` in both `pytest.ini:14` and `ci.yml:31`, a nonzero retry default that signals known instability. Deterministic failures are retried too (finding 12). |
| Running | There is a way to track run results over time | - | Only a per-run `report.html` artifact. No JUnit XML, Allure history or trend store (`ci.yml:33-38`). |
| Running | Tests are integrated into CI/CD, not run purely manually/on-demand | + | GitHub Actions runs on push and pull request to `main` (`ci.yml:3-7`). |
| Processes | Tests are properly documented | - | Module docstrings exist, but 3 of 23 test names misdescribe their body, and 5 of 23 tests do not validate their stated behavior. Self-validation has no dedicated checklist row, so it is recorded here (findings 6, 7). |
| Processes | A failure-handling strategy is implemented (bug reporting → flaky rerun → failure skipping) | - | Blanket reruns only. 0 `flaky` / `xfail` / `skip(reason=)` markers and no ticket linkage. 2 of 2 catch sites swallow (findings 12, 20, 21). Corroborate with the questionnaire. |
