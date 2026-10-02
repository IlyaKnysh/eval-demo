# SubTrack Admin Automation Framework — Review

**Scope reviewed:** `evals/fixtures/medium-framework` (Python/pytest/Playwright hybrid UI+API
framework). Per request, this review does **not** relitigate fixtures (`conftest.py` composition
model), the test-data builders (`src/factories/factories.py`), or locator strategy
(`get_by_role`/`get_by_label`/`get_by_test_id` usage in page objects) — those are solid and not
revisited below except where they intersect with a real defect.

Findings are ordered roughly by severity/impact.

---

## 1. Hardcoded secret committed to source (`src/core/config.py`)

```python
# Hardcoded plaintext-looking fake credential committed directly here
# instead of going through the .env / os.getenv mechanism used by every
# other credential in this class. Inconsistent with the rest of the file.
INVOICING_PROVIDER_API_KEY = "sk-fake1234567890"
```

Every other credential in `Config` (`ADMIN_USERNAME`, `ADMIN_PASSWORD`, `API_TOKEN`) is sourced via
`os.getenv(...)`, and `.env.example` even documents `INVOICING_PROVIDER_API_KEY` as an env var. This
one field breaks that pattern and hardcodes a key literal into source. Even though the value looks
like a placeholder, this is the wrong pattern to normalize in a test framework: it trains the team to
accept secrets-in-source "because it's just a fake one," and the next person who copies this pattern
for a real sandbox key will commit it for real. It also means this one credential can't be rotated or
varied per environment the way every other credential in the same class already can be.

**Fix:** `INVOICING_PROVIDER_API_KEY = os.getenv("INVOICING_PROVIDER_API_KEY")`, consistent with the
rest of the class (the env var is already defined in `.env.example` and already wired into
`.github/workflows/ci.yml`'s secrets — wait, actually it is *not* wired into CI, see Finding 2).

---

## 2. CI workflow never injects `INVOICING_PROVIDER_API_KEY`

`.github/workflows/ci.yml` passes `SUBTRACK_BASE_URL`, `SUBTRACK_API_BASE_URL`,
`SUBTRACK_ADMIN_USERNAME`, `SUBTRACK_ADMIN_PASSWORD`, and `SUBTRACK_API_TOKEN` as env/secrets, but
not `INVOICING_PROVIDER_API_KEY` — because today the code never reads it from the environment (see
Finding 1), so there was nothing to wire up. Once Finding 1 is fixed, this workflow also needs a
`INVOICING_PROVIDER_API_KEY: ${{ secrets.INVOICING_PROVIDER_API_KEY }}` line added, or billing-sync
tests will fail/misbehave in CI with an empty key.

---

## 3. Broken boolean/ternary precedence in the trace-capture autouse fixture (`conftest.py:90`)

```python
rerun_count = getattr(request.node, "execution_count", 1)
if rerun_count > 1 or request.node.rep_call.failed if hasattr(request.node, "rep_call") else False:
    context.tracing.stop(path=f"traces/{request.node.name}.zip")
else:
    context.tracing.stop()
```

This does not parse the way the surrounding docstring claims ("saves the Playwright trace only when
a test is on a retry attempt"). Python's conditional expression binds *looser* than `or`, so this is
actually:

```python
(rerun_count > 1 or request.node.rep_call.failed) if hasattr(request.node, "rep_call") else False
```

Two consequences:

- If `request.node` has no `rep_call` attribute yet at the point this teardown code runs (e.g. a
  fixture/setup error before the test body executes, or ordering differences across pytest/plugin
  versions), the whole condition silently evaluates to `False` and **no trace is saved even though
  the test failed** — the opposite of the stated intent, and the one case (setup failure) where a
  trace is often most valuable for debugging.
- The condition also saves a trace on a first-attempt failure that pytest-rerunfailures hasn't
  retried yet (not just "on retry" as documented), which may be intentional but isn't what the
  docstring says, so the comment and the behavior have drifted apart.

This is also fragile at a design level: it depends on `rep_call` being set by the custom
`pytest_runtest_makereport` hook below it in the same file, and on that hook having already run for
the *call* phase by the time this fixture's teardown executes. That's an implicit, undocumented
ordering dependency between two unrelated pieces of `conftest.py` that would be easy to break with an
unrelated change (e.g. adding another autouse fixture that also does cleanup).

**Fix:** parenthesize explicitly and guard against the missing-attribute case without conflating it
with "trace not needed":

```python
rep_call = getattr(request.node, "rep_call", None)
test_failed = rep_call is not None and rep_call.failed
if rerun_count > 1 or test_failed:
    context.tracing.stop(path=f"traces/{request.node.name}.zip")
else:
    context.tracing.stop()
```

---

## 4. Several tests assert nothing meaningful about the action they just performed

- `tests/api/test_account_api.py::test_delete_account` calls `delete_account`, then does:
  ```python
  account_client.get_account.__self__  # no-op access, not a real assertion
  ```
  This is dead code — a bound-method attribute access with no call and no assertion. The test will
  pass even if the delete endpoint is completely broken (e.g. returns 500, or silently no-ops
  server-side). This is the one test in the file that should be verifying a negative/absence
  (`get_account` 404s, or returns a `deleted`/`inactive` status), and it's the one test that verifies
  nothing.

- `tests/hybrid/test_account_lifecycle.py::test_delete_account_removes_from_list` has the identical
  problem on the UI side:
  ```python
  page.get_by_test_id("search-results").wait_for()
  ```
  waits for the results container to render, but never asserts the deleted account is actually
  absent from it. A regression that leaves deleted accounts visible in search would pass this test
  silently. The test name promises "removes from list" but nothing in the body checks that.

Both should end with a real assertion of absence, e.g. `expect(page.get_by_role("link",
name=account["name"])).not_to_be_visible()` for the UI case, and an assertion on a 404/exception or a
`status == "deleted"` field for the API case.

---

## 5. Exception handlers that swallow real failures and return a default instead

Two near-identical helper functions silently convert any exception into a boolean, masking the
actual cause of failure:

`tests/api/test_ticket_export_api.py`:
```python
def _content_matches_expected_header(content: bytes, expected_magic: bytes) -> bool:
    try:
        return content[: len(expected_magic)] == expected_magic
    except:
        pass
    return False
```

`tests/ui/test_admin_console_nav.py`:
```python
def _values_are_equivalent(actual: str, expected: str) -> bool:
    try:
        return actual.strip().lower() == expected.strip().lower()
    except:
        pass
    return actual == expected
```

Both use a bare `except:` (catches `SystemExit`/`KeyboardInterrupt` too, not just ordinary
exceptions) and both turn an unexpected error — `content` being `None`, a non-string `actual`, an
API contract change — into a plain `False`/fallback-equality result instead of letting it surface.
When the assertion that uses these helpers then fails, the failure message says "expected True, got
False" with zero information about *why* (was it a mismatch, or was it a crash?). This is strictly
worse than letting the real exception propagate: a `TypeError: 'NoneType' object is not subscriptable`
in a test failure log points straight at the bug; `assert False` does not.

**Fix:** remove the try/except entirely (let a genuine type error fail loudly), or catch only the
specific expected exception type and still re-raise/report it rather than silently coercing to
`False`.

---

## 6. Inconsistent API-client usage — some tests bypass the client layer entirely

The repo has a working client layer (`BaseApiClient` → `AccountClient`/`TicketClient`/
`SubscriptionClient`) that most tests use correctly. But:

- `tests/api/test_billing_sync_api.py` (both tests) imports `requests` directly and makes raw HTTP
  calls to the billing-sync endpoint instead of using `SubscriptionClient` — even though
  `SubscriptionClient` is used correctly two lines away for `create_subscription`, and
  `trigger_billing_sync` already exists on `SubscriptionClient` (`src/api_clients/clients.py:77`)
  and is simply never called by these tests.
- `tests/api/test_ticket_export_api.py::test_export_ticket_returns_pdf` does the same thing —
  raw `requests.get(...)` to the export endpoint — despite `TicketClient.export_ticket(...)` existing
  and being used correctly by the *next test in the same file*
  (`test_export_ticket_has_valid_pdf_header`) and by `tests/hybrid/test_ticket_lifecycle.py`.

Both raw-request tests also pull the auth token directly from `Config`/`os.getenv` and set the
`Authorization` header by hand, bypassing the typed `AuthContext`/`User` abstraction
(`src/core/auth.py`) that the rest of the suite goes through. Net effect: if the auth header format,
base URL construction, or timeout/retry policy ever changes, it has to be updated in the client
classes *and* independently in these three call sites, and they will silently drift out of sync
(note `test_billing_sync_api.py` already uses no error-status assertion beyond `status_code == 200`,
where the client-based tests check domain-specific response fields).

**Fix:** route these three tests through `SubscriptionClient.trigger_billing_sync` and
`TicketClient.export_ticket`, and have them pick up auth the same way every other authenticated test
does (via `authenticated_context`/the client's existing session), rather than reading
`Config.API_TOKEN`/`os.getenv` directly.

---

## 7. Test-order dependency via module-level mutable state

`tests/hybrid/test_ticket_lifecycle.py`:
```python
_CREATED_TICKET_IDS = []

def test_create_ticket_and_record_id(ticket_client):
    ticket = ticket_client.create_ticket(TicketBuilder().with_priority("high").build())
    _CREATED_TICKET_IDS.append(ticket["id"])
    assert ticket["priority"] == "high"


def test_second_test_relies_on_previous_ticket(ticket_client):
    # Only passes if test_create_ticket_and_record_id already ran
    ticket_id = _CREATED_TICKET_IDS[-1]
    ...
```

This violates test independence: `test_second_test_relies_on_previous_ticket` has a hard, undeclared
dependency on `test_create_ticket_and_record_id` running first in the same session and mutating
shared module state. Consequences:

- `pytest -k test_second_test_relies_on_previous_ticket` (a completely normal thing to do when
  iterating on a single failing test) raises `IndexError: list index out of range` instead of a
  meaningful assertion message.
- Running tests in parallel (`pytest-xdist`) or in a different order (`pytest-randomly`, or even just
  a future pytest default-order change) breaks this test non-deterministically.
- There is no cleanup of `_CREATED_TICKET_IDS` between runs/sessions — it's process-global, so a
  second `pytest` invocation in the same interpreter (e.g. from a test-runner that imports and calls
  pytest.main() repeatedly) would accumulate stale entries across runs.

**Fix:** the second test should either be folded into the first (it's really one scenario: "create a
high-priority ticket, then fetch it back and confirm the priority stuck"), or `_CREATED_TICKET_IDS`
should become a fixture-provided value (e.g. the first test's ticket returned via a fixture or
`pytest.mark.dependency`), not free-floating module state.

---

## 8. Page-object naming convention broken for two classes, without a corresponding problem in the tests

`src/pages/AdminConsole.py` and `src/pages/SettingsScreen.py` break the `*Page` suffix convention
used by every other page object in the package (`LoginPage`, `DashboardPage`, `AccountModifyPage`,
`ContactModifyPage`, `SubscriptionModifyPage`, `TicketModifyPage`, `TicketListPage`,
`SubscriptionListPage`). Both files even have a docstring acknowledging the inconsistency rather than
fixing it. This is a minor but real consistency gap: a new contributor grepping for `*Page` to find
all page objects, or a lint rule enforcing the naming convention, will miss these two. Since they're
also named like generic UI regions rather than specific screens (`AdminConsole`, `SettingsScreen`),
they read as a different *kind* of object (layout/shell helper vs. page) when nothing about their
actual implementation (constructor takes `page`, wraps `get_by_role` calls) differs from the rest.

**Fix:** rename to `AdminConsolePage` / `SettingsPage` (or equivalent) for consistency, or — if the
intent really is to carve out a distinct "layout component" category from "page" — document that
distinction explicitly (e.g. a `components/` vs `pages/` split) rather than leaving two
unexplained outliers in the same flat `pages/` package.

---

## 9. Misleading method name reused across unrelated page objects (`update_name`)

```python
# SubscriptionModifyPage
def update_name(self, name: str):
    self.page.get_by_label("Plan code").fill(name)

# TicketModifyPage
def update_name(self, name: str):
    self.page.get_by_label("Ticket subject").fill(name)
```

Both methods are called `update_name`, copied from `AccountModifyPage`/`ContactModifyPage` (where
"name" is accurate), but on `SubscriptionModifyPage` it actually fills the **plan code** field, and
on `TicketModifyPage` it fills the **ticket subject** field. The call sites make this worse, not
better — e.g. `tests/hybrid/test_subscription_lifecycle.py`:

```python
modify_page.update_name("PRO-ANNUAL")
...
assert updated["plan_code"] == "PRO-ANNUAL"
```

A reader has to connect "update_name" to "plan_code" via the assertion two lines later; the method
name itself actively misleads. This isn't a cosmetic nitpick — a future maintainer adding an actual
"name" field to subscriptions or tickets has no safe name left to give a method that really does
rename something, and is likely to either collide with this one or add a confusingly-similar
`rename()`/`set_name()`.

**Fix:** rename to `update_plan_code` and `update_subject` respectively, matching what the field
and the domain object actually call it (consistent with `SubscriptionBuilder.with_plan_code` /
`TicketBuilder.with_subject`, which already use the correct domain terms).

---

## 10. No `.gitignore` in the framework root

There is no `.gitignore` anywhere under `medium-framework/`, and the working tree already has a
generated `__pycache__/` directory sitting in the repo root alongside source files. Given
`pytest.ini` configures `--html=report.html --self-contained-html` and `conftest.py` writes trace
zips to `traces/*.zip`, and `.env` is the documented local-secrets file (per `.env.example` and the
README's "Running locally" section), none of `__pycache__/`, `*.pyc`, `.env`, `report.html`, or
`traces/` are excluded. Without a `.gitignore`, it's a matter of time before someone's local `.env`
(real staging credentials) or a `report.html`/trace capture (which can embed response bodies,
screenshots, and request headers — including auth tokens — via the tracing config in `conftest.py`)
gets committed by an unwary `git add .`.

**Fix:** add a `.gitignore` covering at minimum `__pycache__/`, `*.pyc`, `.env`, `report.html`,
`traces/`.

---

## Summary

| # | Finding | Severity |
|---|---|---|
| 1 | Hardcoded secret in `config.py` instead of env-sourced | High |
| 2 | CI never injects `INVOICING_PROVIDER_API_KEY` | Medium (follows from #1) |
| 3 | Broken precedence in autouse trace-capture fixture, contradicts its own docstring | High |
| 4 | Two tests perform an action but assert nothing about its effect | High |
| 5 | Bare `except:` blocks silently coerce real errors into `False` | Medium |
| 6 | Inconsistent API-client usage — raw `requests` calls bypass existing client/auth abstractions in 3 tests | Medium |
| 7 | Cross-test dependency via module-level mutable list, breaks test isolation | Medium |
| 8 | Two page objects break the `*Page` naming convention | Low |
| 9 | `update_name` method name is misleading on 2 of 4 modify-page objects | Low |
| 10 | No `.gitignore`; secrets/generated artifacts are one `git add .` away from being committed | Medium |

10 findings logged (4 high, 4 medium, 2 low). Fixtures, builders, and locator strategy were
intentionally not re-reviewed per scope.
