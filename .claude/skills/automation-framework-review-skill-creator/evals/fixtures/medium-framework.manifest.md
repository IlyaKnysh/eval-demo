# medium-framework fixture — ground truth manifest

Fixture root: `.claude/skills/automation-framework-review-deepeval/evals/fixtures/medium-framework/`

This is a MIXED-SIGNAL fixture: 10 deliberately seeded defects mixed with 7
deliberately clean practices, in a Python + pytest + Playwright (sync API)
API+UI hybrid framework for a fictional subscription-billing/support-ticketing
admin system ("SubTrack Admin"). A correct review must catch every defect
below AND must NOT flag any of the clean practices in section 2.

File count: 29 files (12 `src/` modules, 10 test files, `conftest.py`,
`pytest.ini`, `requirements.txt`, `.env.example`, `README.md`,
`.github/workflows/ci.yml`).

---

## 1. Seeded defects (must be caught)

### Defect #1 — Missing business-step/flow layer (§A)
No `steps/` (or equivalent business-flow) package exists anywhere in the repo.
Tests compose page-object + api-client calls directly, inline, repeating the
same ~4-step sequence (create via API → open in UI → modify a field → save +
assert) in **4 test functions across 3 files**:
- `tests/hybrid/test_account_lifecycle.py:18-35` — `test_update_account_name`
- `tests/hybrid/test_account_lifecycle.py:38-55` — `test_update_account_status`
- `tests/hybrid/test_ticket_lifecycle.py:21-39` — `test_update_ticket_priority`
- `tests/hybrid/test_subscription_lifecycle.py:13-31` — `test_update_subscription_seats`

Each repeats: API-client `create_*` call → `DashboardPage.open_*()` +
navigate → `*ModifyPage.wait_until_loaded()` + a field update → `save_changes()`
+ re-fetch-and-assert. No shared step/flow helper exists to express this once.

### Defect #2 — Layer boundary leakage in API tests (DIP-consistency) (§B)
Two test files import `requests` directly and make raw HTTP calls instead of
using the existing `*Client` wrapper classes (`src/api_clients/clients.py`),
while sibling test files in the same `tests/api/` package use the wrappers
correctly:
- `tests/api/test_billing_sync_api.py:12` (`import requests`) — raw calls at
  lines 22-27 (`test_billing_sync_triggers_provider_call`) and lines 36-41
  (`test_billing_sync_records_external_reference`), bypassing
  `SubscriptionClient.trigger_billing_sync` (which exists at
  `src/api_clients/clients.py:77-84` and is unused by this file).
- `tests/api/test_ticket_export_api.py:12` (`import requests`) — raw call at
  lines 23-27 (`test_export_ticket_returns_pdf`), bypassing
  `TicketClient.export_ticket` (which exists at
  `src/api_clients/clients.py:49-54` and IS used correctly by
  `tests/hybrid/test_ticket_lifecycle.py` and by
  `test_export_ticket_has_valid_pdf_header` later in the same file).

Contrast (clean, for comparison): `tests/api/test_account_api.py` and
`tests/api/test_subscription_api.py` use `account_client`/`subscription_client`
wrappers exclusively — no `requests` import. This inconsistency (2 of 4 API
test files bypass the wrapper) is the finding, distinct from Defect #1.

### Defect #3 — Cross-file sibling duplication in page objects (§C)
Four page-object classes in four separate files each implement the same
3-5-method pattern (`wait_until_loaded`, `update_name`, `update_status`,
`save_changes`, `cancel_changes`) with near-identical bodies differing only in
label/heading text:
- `src/pages/account_modify_page.py:1-22` — `AccountModifyPage`
- `src/pages/contact_modify_page.py:1-22` — `ContactModifyPage`
- `src/pages/ticket_modify_page.py:1-22` — `TicketModifyPage`
- `src/pages/subscription_modify_page.py:1-22` — `SubscriptionModifyPage`

Each file is byte-for-byte identical in structure (same method names, same
order, same locator strategy), only the label strings and heading names
differ. No shared base/mixin or generic "ModifyPage" abstraction is used.

### Defect #4 — Domain-concept representation inconsistency (raw token vs. typed AuthContext) (§C)
Most tests obtain credentials through the typed `User`/`AuthContext` object
(`src/core/auth.py`, used via the `authenticated_context` fixture in
`conftest.py:72-82`, which calls `AuthContext.login_as(user)`). Two tests
instead pull a raw token/credential string directly from `Config`/env and pass
it straight to the API layer, bypassing the typed object for the same concept:
- `tests/api/test_billing_sync_api.py:25` — `headers={"Authorization": f"Bearer {Config.API_TOKEN}"}`
  inside `test_billing_sync_triggers_provider_call` (also repeated at line 39
  in the second test in that file, sharing the same raw-token pattern).
- `tests/api/test_ticket_export_api.py:22` — `raw_token = os.getenv("SUBTRACK_API_TOKEN")`
  inside `test_export_ticket_returns_pdf`, then used directly at line 25.

(These are the same two test files as Defect #2 — the raw-`requests` bypass
and the raw-token bypass co-occur in both, but they are distinct findings:
Defect #2 is a layering/DIP violation, Defect #4 is a domain-modeling/
representation-consistency violation.)

### Defect #5 — Test independence violation (shared module-level mutable state) (§D)
`tests/hybrid/test_ticket_lifecycle.py:18` declares module-level list
`_CREATED_TICKET_IDS = []`. Exactly 2 tests share it:
- `test_create_ticket_and_record_id` (lines 42-48) appends to it at line 47.
- `test_second_test_relies_on_previous_ticket` (lines 51-58) reads
  `_CREATED_TICKET_IDS[-1]` at line 56.

Running `test_second_test_relies_on_previous_ticket` in isolation (e.g.
`pytest -k test_second_test_relies_on_previous_ticket`) raises `IndexError`
instead of a meaningful assertion failure — proof of order dependency /
non-parallel-safety.

### Defect #6 — No assertions in 2 tests (§D)
- `tests/hybrid/test_account_lifecycle.py:58-69` —
  `test_delete_account_removes_from_list`: creates and deletes an account,
  searches for it, and waits for the search-results element (line 69), but
  contains no `assert` statement anywhere in the test body.
- `tests/api/test_account_api.py:21-27` — `test_delete_account`: creates and
  deletes an account via `account_client`, then executes a no-op attribute
  access (`account_client.get_account.__self__`, line 27) instead of an
  assertion. Contains no `assert` statement.

### Defect #7 — Empty catch/except (bare `except: pass`) (§F)
Exactly 2 bare `except:` blocks that swallow all exceptions and `pass`:
- `tests/api/test_ticket_export_api.py:41-42` — inside
  `_content_matches_expected_header` (lines 31-43), a comparison/verification
  helper used by `test_export_ticket_has_valid_pdf_header`. The bare
  `except: pass` at lines 41-42 swallows any error and silently returns
  `False`.
- `tests/ui/test_admin_console_nav.py:28-29` — inside
  `_values_are_equivalent` (lines 18-30), a string-comparison helper used by
  `test_billing_settings_saves_provider_key`. The bare `except: pass` at
  lines 28-29 swallows any error and falls back to plain `==`.

### Defect #8 — Nonzero retries with no flaky-test tracking/quarantine mechanism (§F)
- `pytest.ini:17-18` — `reruns = 2` / `reruns_delay = 2` (pytest-rerunfailures).
- `.github/workflows/ci.yml:34` — `run: pytest --reruns 2 --reruns-delay 2`
  (redundant with pytest.ini, confirms the CI path also reruns).

No `@pytest.mark.flaky` quarantine list, no flaky-ticket-linking convention,
no dashboard/tracking reference exists anywhere in the repo (checked
`README.md`, `conftest.py`, `pytest.ini`, and the CI workflow — none mention
flaky-test tracking).

### Defect #9 — Naming outliers among page objects (§O)
Out of 10 page-object classes in `src/pages/`, 2 do not follow the `*Page`
suffix convention used by the other 8
(`LoginPage`, `DashboardPage`, `AccountModifyPage`, `ContactModifyPage`,
`TicketModifyPage`, `SubscriptionModifyPage`, `TicketListPage`,
`SubscriptionListPage`):
- `src/pages/AdminConsole.py:1` — class `AdminConsole` (also: file itself is
  PascalCase, inconsistent with the snake_case filenames used everywhere else
  in `src/pages/`).
- `src/pages/SettingsScreen.py:1` — class `SettingsScreen` (same PascalCase
  filename inconsistency; `Screen` suffix instead of `Page`).

### Defect #10 — Hardcoded plaintext-looking fake credential in committed config (Secrets/Config)
`src/core/config.py:26` — `INVOICING_PROVIDER_API_KEY = "sk-fake1234567890"`
is a literal hardcoded string committed directly in `Config`, even though:
- Every other credential in the same class (`ADMIN_USERNAME`,
  `ADMIN_PASSWORD`, `API_TOKEN`, `BASE_URL`, `API_BASE_URL`) is sourced via
  `os.getenv(...)` (lines 15-21).
- `.env.example` already declares `INVOICING_PROVIDER_API_KEY`'s intended
  env-var name pattern via the sibling `INVOICING_PROVIDER_API_KEY` entry
  (`.env.example:14`), i.e. the env-var mechanism exists and covers this
  exact secret elsewhere, but `config.py` doesn't use it for this one field.
- This value is subsequently read and used live in
  `tests/api/test_billing_sync_api.py:24,38` and
  `tests/ui/test_admin_console_nav.py:41`.

---

## 2. Deliberately clean practices (must NOT be flagged)

1. **Good DI/fixtures, no God Base Class (§B)** — `conftest.py:1-102`. All
   setup (`playwright_instance`, `browser`, `context`, `page`, `auth_client`,
   `account_client`, `ticket_client`, `subscription_client`, `default_user`,
   `authenticated_context`) is composed via `@pytest.fixture`. No test class
   inherits from a shared base-class setup chain anywhere in `tests/`. Called
   out explicitly at `conftest.py:3-6`.

2. **Good test-data builders (builder pattern, used consistently) (§C)** —
   `src/factories/factories.py:1-99`. `AccountBuilder`, `ContactBuilder`,
   `TicketBuilder`, `SubscriptionBuilder` each use chainable `with_*()`
   methods returning `self` and a final `.build()`. Used consistently by
   every test that needs test data (e.g. `tests/api/test_account_api.py:7,11`,
   `tests/hybrid/test_ticket_lifecycle.py:12,23`, `tests/ui/test_search.py:7`)
   — no test constructs a raw dict literal for domain payloads instead.

3. **No hardcoded sleeps; Playwright auto-waiting used correctly (§G)** —
   verified across all page objects (`src/pages/*.py`) and all test files:
   no `time.sleep`, no `page.wait_for_timeout`, no polling loops anywhere in
   the fixture. All waits use Playwright's built-in actionability
   (`.click()`, `.fill()`) or explicit `.wait_for()` on a locator (e.g.
   `src/pages/account_modify_page.py:18`,
   `tests/ui/test_search.py:18,31,44`).

4. **Good locators — consistent semantic locators (§H)** — every page object
   in `src/pages/` (including the 2 naming-outlier files) uses
   `get_by_role`/`get_by_label`/`get_by_test_id`/`get_by_text` exclusively.
   No CSS selector, XPath, or `By.id`/`find_element`-style locator appears
   anywhere in `src/pages/` or in tests that interact with `page` directly
   (e.g. `tests/ui/test_search.py:18,25`, `tests/hybrid/test_account_lifecycle.py:25`).

5. **Current dependency pin (§M)** — `requirements.txt:3` —
   `playwright==1.47.0` (2024 release, supports modern auto-waiting/trace
   viewer). Noted explicitly at `requirements.txt:1-2`.

6. **Good diagnostics — trace-on-retry + published HTML report (§J)** —
   - Trace capture: `conftest.py:30-37` (`context.tracing.start(...)` in the
     `context` fixture) and the `_capture_trace_on_retry` fixture at
     `conftest.py:85-95`, which persists a trace file specifically when a
     test needed a rerun.
   - HTML report: `pytest.ini:10-11` (`--html=report.html --self-contained-html`).
   - CI publishing: `.github/workflows/ci.yml:36-49` — both `report.html`
     (`pytest-html-report` artifact) and `traces/` (`playwright-traces`
     artifact) are uploaded with `if: always()`.

7. **Clean naming conventions (§O)** — consistent `test_*.py` file naming
   across all 10 files in `tests/` (enforced by `pytest.ini:3`,
   `python_files = test_*.py`); consistent `*Page` suffix on 8 of 10 page
   objects (see Defect #9 for the 2 exceptions, which are the deliberately
   seeded outliers, not part of this clean-practice claim); consistent
   `*Client` suffix on all 4 API client classes in
   `src/api_clients/clients.py` and `src/api_clients/base_client.py`
   (`BaseApiClient`, `AuthClient`, `AccountClient`, `TicketClient`,
   `SubscriptionClient`).

---

## Notes for grading

- Defects #2 and #4 deliberately co-occur in the same two files
  (`test_billing_sync_api.py`, `test_ticket_export_api.py`). A review that
  reports only one of the two and misses the other should be marked as
  partially correct, not fully correct — they are distinct root causes (DIP
  layering vs. domain-representation consistency) per the task brief.
- Defect #9's two outlier files (`AdminConsole.py`, `SettingsScreen.py`) are
  also PascalCase filenames, unlike every other snake_case file in
  `src/pages/` — a thorough review may note the filename-casing inconsistency
  as part of the same naming finding; this is acceptable and should not be
  double-counted as a separate defect.
- Good practice #7 (naming) and Defect #9 (naming outliers) are intentionally
  in tension: the review must recognize that the *majority* convention is
  clean and correctly scope the naming finding to only the 2 outliers, not
  flag the whole `pages/` package as inconsistent.
