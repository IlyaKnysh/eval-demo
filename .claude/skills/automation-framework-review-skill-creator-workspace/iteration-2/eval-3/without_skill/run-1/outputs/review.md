# Framework Review: `storefront-admin-e2e` (Playwright + TypeScript)

**Scope:** `.claude/skills/automation-framework-review-skill-creator/evals/fixtures/clean-framework/` (30 files, ~1,460 lines). I read every file: 6 page objects, 3 flow modules, 2 factories, core (BasePage, EntityModifyPanel, fixtures), utils, types, 5 spec files (15 tests), config, CI workflow, README and CONTRIBUTING.
**Checklist areas:** layering, SOLID, DRY, test design, locators, error handling, waits, naming. I also covered config/CI because some of the problems show up there.
**Method:** Static review only. There is no `node_modules` or lockfile, so nothing was compiled or run. The review targets an unknown app, so the UI behavior assumptions are listed in section 6.

---

## 1. Verdict

**Approve with changes. Do not sign off as-is.**

You're right that the architecture is in good shape. The layering (spec → flow → page object → composed helper) is clean, the locator strategy is good, there are no hard sleeps or empty catch blocks, test data is built through factories, and cleanup is handled by fixtures. That is better than most suites I see.

The second opinion still turns up problems you would miss if you only read the README and CONTRIBUTING:

1. **Three tests don't check what their names say they check.** One of them can't pass for the right reason: the notes test never enters the notes, and the multi-item test overwrites the first item with the second. These are false greens. (F1–F3)
2. **Local runs ignore `.env`.** Nothing loads it, so the suite quietly falls back to `localhost:3000` and `replace-me` credentials. (F4)
3. **`npm ci` in CI needs a lockfile, and the repo has none.** (F5)
4. **`waitForLoad()` uses `networkidle`**, which Playwright discourages, and it is the only signal that a login succeeded. (F6, F7)
5. **The cleanup fixture stops at the first failure**, which leaves orphaned data in the shared staging environment. (F8)

Fix F1–F8 before sign-off. Everything else can go to the backlog.

### Scorecard

| Area | Rating | Notes |
|---|---|---|
| Layering | Strong | The spec → flow → PO → helper split is followed. Specs never touch `Locator`. One coupling smell: flows import `test` from fixtures (F12). |
| SOLID | Good | Slim `BasePage`, composition through `EntityModifyPanel`, fixture-based DI. Minor: the API cleanup client lives in `fixtures.ts` (F15), and the panel POs inherit `goto` without needing it (F21). |
| DRY | Good, with gaps | `nextSuffix()` is copied word for word between the two factories (F10). The `loginAs` helper is duplicated between fixtures and flows (F11). The CI jobs are copies of each other (F22). |
| Test design | **Needs work** | AAA structure and isolation are good, but several assertions are too weak to prove the behavior (F1–F3, F9). There are no negative or permission tests for orders and users (F17). |
| Locators | Strong | Only role, label and test-id locators. No XPath or CSS chains. Small risks from substring matching and page-wide toast and alert locators (F13, F14). |
| Error handling | Good | `withContext`/`FrameworkError` is used consistently and there are no empty catches. The issues are cleanup error handling (F8), double wrapping (F16), and possibly a type error on `this.cause` (F19). |
| Waits | Good, with one real issue | No `waitForTimeout`, and web-first assertions are used. But there is `networkidle` (F6), login is never confirmed (F7), and a stale toast can satisfy the save check (F13). |
| Naming | Strong | The `*Page`, verb-phrase flow, `*.spec.ts` and `*Factory.ts` conventions are followed exactly as documented. Nits only (F23). |
| Config / CI | Needs work | `.env` is never loaded (F4), there is no lockfile (F5), there is no linter (F18), and `API_BASE_URL` is never used (F15). |

---

## 2. Findings summary

| ID | Severity | Area | Finding | Location |
|---|---|---|---|---|
| F1 | **High** | Test design | The "custom notes" test never fills in or checks the notes, so it passes whether or not notes work | `tests/orders/createOrder.spec.ts:41-48`, `src/pages/OrderModifyPage.ts:41-48` |
| F2 | **High** | Test design | Multi-item orders: every item is typed into the same `SKU`/`Quantity` fields, so the last item overwrites the earlier ones. The test only checks that a row exists | `src/pages/OrderModifyPage.ts:35-46`, `tests/orders/createOrder.spec.ts:23-30` |
| F3 | **High** | Test design | "Custom initial status" and the "registers admin / read-only user" tests never check the status or role they are named after | `createOrder.spec.ts:32-39`, `registerUser.spec.ts:19-35` |
| F4 | **High** | Config | `.env` is documented but never loaded (no `dotenv`). Local runs silently use `localhost:3000` and `replace-me` credentials | `playwright.config.ts:30`, `userFactory.ts:66-83`, `README.md:31-32`, `package.json` |
| F5 | **High** | CI | `npm ci` fails when there is no `package-lock.json`, and the repo has none | `.github/workflows/e2e-tests.yml:27,65` |
| F6 | Medium | Waits | `waitForLoad()` uses `waitForLoadState('networkidle')`, which Playwright discourages. It flakes or hangs on SPAs that poll or keep sockets open | `src/core/BasePage.ts:17-19`, `DashboardPage.ts:35,42`, `LoginPage.ts:50` |
| F7 | Medium | Waits / test design | `loginAs()` returns a `DashboardPage` without confirming the dashboard loaded, so a failed login shows up later as a misleading locator timeout | `src/pages/LoginPage.ts:44-53` |
| F8 | Medium | Error handling | Cleanup teardown stops at the first failed delete, and a 404 for a record that was never created counts as a failure. Both leave orphaned data or add noise | `src/core/fixtures.ts:60-106` |
| F9 | Medium | Test design | The order and user grids are "paginated", but row lookups never search or filter. On a busy shared staging environment, a new record may not be on page 1 | `OrderListPage.ts:36-39`, `UserListPage.ts:27-30`, `gridUtils.ts:22-36` |
| F10 | Medium | DRY | `nextSuffix()` and its doc comment are copied word for word in both factories | `orderFactory.ts:3-16`, `userFactory.ts:3-16` |
| F11 | Low | DRY | The private `loginAs()` in fixtures copies the `loginAsUser` flow, apparently to avoid a circular import | `fixtures.ts:80-84`, `authFlows.ts:9-17` |
| F12 | Low | Layering | Flows import `test` from `@core/fixtures` only to call `test.step`. That couples the flow layer to the fixture graph and causes F11 | `authFlows.ts:1`, `orderFlows.ts:1`, `userFlows.ts:1` |
| F13 | Low–Med | Waits / locators | The success toast locator is page-wide. A toast left over from a previous save in the same test can satisfy the check, and two visible toasts trigger a strict-mode error | `EntityModifyPanel.ts:32-34,59-65` |
| F14 | Low | Locators | `getByLabel('Password')`, `getByRole('link', {name:'Orders'})` and similar use substring matching by default. Page-wide `getByRole('alert')` can match unrelated alerts | `LoginPage.ts:23,31`, `DashboardPage.ts:17,21` |
| F15 | Low | SOLID / config | The API cleanup client is embedded in `fixtures.ts`. `API_BASE_URL` is documented but never read, and cleanup quietly depends on cookies from `adminSession` | `fixtures.ts:86-106`, `.env.example:13-14` |
| F16 | Low | Error handling | Context is wrapped twice: `withContext` + `test.step` in flows, and `withContext` again in `LoginPage.loginAs`. Messages come out as "Signing in as X: Logging in as X: …" | `authFlows.ts:10-16`, `LoginPage.ts:45` |
| F17 | Low | Coverage | No negative or authorization tests for orders and users (validation, duplicate email, standard-user access). `standardUser()` is only used for login | `tests/**` |
| F18 | Low | Tooling | No ESLint or Prettier. In particular there is no `@typescript-eslint/no-floating-promises`, which is the main guard against missing `await` in Playwright code. CONTRIBUTING rules are enforced "by convention" only | repo root, `package.json` |
| F19 | Low (verify) | Type safety | `this.cause = cause` with `lib: ["ES2021"]`: `Error.cause` is declared in `lib.es2022.error`, so `tsc --noEmit` may fail. Couldn't confirm because no dependencies are installed | `errors.ts:13`, `tsconfig.json:5` |
| F20 | Low | Dead code | The `loginPage` fixture, `OrderListPage.searchFor()`, both `cancel()` methods, and the unused `expect` imports in `OrderModifyPage`/`UserModifyPage` | `fixtures.ts:40-43`, `OrderListPage.ts:31-34`, `*ModifyPage.ts:2` |
| F21 | Info | SOLID | `OrderModifyPage`/`UserModifyPage` are slide-over panels but extend `BasePage` and inherit `goto`/`waitForLoad` they never use | `OrderModifyPage.ts:12`, `UserModifyPage.ts:12` |
| F22 | Info | DRY / CI | The `smoke` and `full-regression` jobs repeat 6 steps and all the env wiring. There is also no npm cache | `e2e-tests.yml` |
| F23 | Info | Naming / docs | The `@domain/*` alias points at `src/types/`. The invalid-login test uses raw credential strings, against the CONTRIBUTING rule. AAA comments appear in some tests but not others | `tsconfig.json:18`, `login.spec.ts:26`, `CONTRIBUTING.md:60-62` |

Totals (23 findings): **5 High, 5 Medium, 1 Low–Medium, 9 Low, 3 Info.**

---

## 3. Detailed findings

### F1 (High): The notes test passes whether notes work or not
`tests/orders/createOrder.spec.ts:41-48` builds `buildOrder({ notes: 'Customer requested gift wrap.' })`, but `OrderModifyPage.fillFromOrderData()` (lines 41-48) only fills customer, status and line items. **`notes` is never written to the UI.** A grep for `notes` across `src/pages` and `src/flows` finds nothing. The only assertion is `expectRowWithCustomer`, so the test passes even if the Notes feature is removed.

**Fix:** Add `fillNotes()` to `OrderModifyPage`, call it from `fillFromOrderData` when `order.notes` is set, and assert the notes after reopening the order (for example `expectFieldValue('Notes', …)`).

### F2 (High): Multi-item orders can't be entered correctly
```ts
// OrderModifyPage.ts:35-46
async addLineItem(sku: string, quantity: number) {
  await this.panel.fillField('SKU', sku);
  await this.panel.fillField('Quantity', String(quantity));
}
...
for (const item of order.items) { await this.addLineItem(item.sku, item.quantity); }
```
Nothing clicks an "add line item" control, so the second item overwrites the first in the same inputs. If the panel does render one SKU input per line, `getByLabel('SKU')` fails with a strict-mode violation instead. Either way the "multi-item order" test (`createOrder.spec.ts:23-30`) only checks that a row exists for the customer, so it doesn't check the line-item rendering and totals that `buildMultiItemOrder`'s doc comment says it covers (`orderFactory.ts:83`). `description` and `unitPriceCents` are never used either.

**Fix:** Model line items properly (an "Add item" button plus row-scoped inputs) and assert the item count and total.

### F3 (High): Status and role variants don't check status or role
- `createOrder.spec.ts:32-39` "creates an order with a custom initial status" only checks that the row exists, not that the status is `processing`.
- `registerUser.spec.ts:19-35` "registers a new admin user" and "… read-only user" only check that the email is in the grid. All three `registerUser` tests are identical apart from the role, and none of them checks the role. Compare `changeUserRole.spec.ts`, which reopens the record and calls `expectRoleFieldValue`. That pattern is right and should be reused here.

**Fix:** Reopen the record and call `expectStatusFieldValue` / `expectRoleFieldValue`, or check the status or role column in the grid row. Consider a data-driven loop (`for (const role of ['standard','admin','read-only'] as const)`) to remove the three near-identical tests.

### F4 (High): `.env` is never loaded
README step 1 and the comment in `playwright.config.ts` say values come from `.env`. Playwright doesn't load `.env` on its own, and there is no `dotenv` dependency or import anywhere (grep for `dotenv` finds nothing). Locally:
- `baseURL` falls back to `http://localhost:3000` (`playwright.config.ts:30`).
- `adminUser()`/`standardUser()` fall back to `admin.qa@example.com` / `replace-me` (`userFactory.ts:68-79`).

The result is a confusing login failure instead of a clear configuration error. CI is fine because it injects env vars directly.

**Fix:** Add `dotenv` and `import 'dotenv/config'` in `playwright.config.ts`. Replace the `?? 'replace-me'` fallbacks with a `requireEnv('ADMIN_PASSWORD')` helper that throws a clear error.

### F5 (High): CI `npm ci` with no lockfile
Both jobs run `npm ci` (`e2e-tests.yml:27,65`), which exits with an error when there is no `package-lock.json`. The repo has no lockfile of any kind. Even if the lockfile was only left out of this snapshot, the `^` ranges in `package.json` mean Playwright and browser versions aren't pinned, so results aren't reproducible.

**Fix:** Commit `package-lock.json`. Optionally add `cache: npm` to `setup-node`.

### F6 (Medium): `networkidle` waits
`BasePage.waitForLoad()` calls `page.waitForLoadState('networkidle')`, and it is the only wait after login (`LoginPage.ts:50`) and after nav-link clicks (`DashboardPage.ts:35,42`). Playwright's documentation marks `networkidle` as discouraged. On an admin SPA with polling, analytics or websockets it can hang until the 10s/30s timeout, or it can resolve before client-side rendering finishes.

**Fix:** Replace it with web-first readiness checks that belong to each page, for example `expect(this.grid).toBeVisible()` in an `OrderListPage.waitForReady()`, or `expect(page).toHaveURL(/\/orders/)`.

### F7 (Medium): Login success is never confirmed
`LoginPage.loginAs()` clicks Sign in, waits for `networkidle`, and returns a `DashboardPage` without checking that the dashboard actually appeared. With bad credentials (see F4), the failure shows up as "link Orders not found" inside a flow, not as "login failed". Only the two login tests call `expectWelcomeVisible()`.

**Fix:** Check the dashboard landmark (`welcomeBanner`) or the URL inside `loginAs()` before returning.

### F8 (Medium): Cleanup fixture is fragile
`fixtures.ts:71-76` runs the deletes one after another with no per-item error isolation. If one delete throws, the remaining orders and users are never deleted. The tests also register records *before* creating them (`createdRecords.order(...)` then `createOrder(...)`). If creation fails early and the API returns 404 for an unknown email, teardown throws a second error on top of the real failure.

**Fix:** Run every delete, collect the failures, then throw one aggregated error (or use `Promise.allSettled`). Treat 404 as success.

### F9 (Medium): Grid lookups assume the new row is on page 1
The README and comments call both grids "paginated", and the suite runs `fullyParallel` against shared staging. `getUniqueGridRow` waits for a matching row on whatever page is currently shown. If the grid isn't sorted newest-first, or other activity pushes the row off page 1, lookups time out. `OrderListPage.searchFor()` already exists but is never called, and there is no search on the user grid.

**Fix:** Search or filter by the unique email or name before looking up the row, and wait for the grid to refresh after the search. Also, `expectRowWithCustomer` calls `toBeVisible()` again after `getUniqueGridRow` has already waited for visibility. That's harmless but redundant.

### F10 (Medium): Duplicated `nextSuffix()`
`orderFactory.ts:3-16` and `userFactory.ts:3-16` are character-for-character identical, including the doc comment. This contradicts the README's "single source of truth" claim, and the uniqueness logic is exactly what will need to change if collisions show up.

**Fix:** Move it to `src/factories/uniqueSuffix.ts` (or `@utils`) and import it in both factories. A related inconsistency: `buildOrder(overrides)` just spreads the overrides, while `buildUser(overrides)` applies them through the builder *and then* spreads them again (`userFactory.ts:57-63`). Pick one pattern.

### F11 / F12 (Low): Flow imports fixtures, which forces a duplicated login helper
The flows import `test` from `@core/fixtures` (which imports the page objects) only to call `test.step`. So `fixtures.ts` can't import `loginAsUser` without a cycle, and it re-implements the same three lines as a private `loginAs()` (`fixtures.ts:80-84`).

**Fix:** In flows, `import { test } from '@playwright/test'`. `test.step` doesn't depend on custom fixtures. Then `adminSession` can call `loginAsUser(page, adminUser())`.

### F13 (Low–Medium): Page-wide toast check
`successToast = page.getByRole('status').filter({ hasText: 'Saved successfully' })` isn't scoped to this save. In `updateOrderStatus` and `changeUserRole` tests, `createOrder`/`registerUser` saves first, and the toast may still be on screen when the second save happens. `toBeVisible()` then passes immediately. If both toasts are visible, it fails with a strict-mode violation. The `toBeHidden()` check on the panel softens the first case but not the second.

**Fix:** Wait for any existing toast to disappear before clicking Save, use `.last()`, or wait on the save network response (`page.waitForResponse`) as the completion signal.

### F14 (Low): Substring matching in locators
`getByLabel` and `getByRole({ name })` match substrings by default. `getByLabel('Password')` also matches a "Forgot password?" or "Confirm password" label. `getByRole('link', { name: 'Orders' })` also matches "Recent orders". `getByRole('alert')` covers the whole page.

**Fix:** Add `{ exact: true }` where the label is a common word, and scope the error banner to the login form.

### F15 (Low): Cleanup API client inside fixtures, and the unused `API_BASE_URL`
`deleteOrder`/`deleteUser` make raw REST calls inside the fixture file, which mixes DI wiring with API-client code. They call relative `/api/...` paths on the UI `baseURL`, while `.env.example` documents an `API_BASE_URL` "for seeding calls used by factories". Nothing reads it. Cleanup also relies on the browser cookies set by `adminSession`. If a test uses `createdRecords` without `adminSession`, teardown gets a 401.

**Fix:** Move these calls to `src/api/adminApi.ts` with an `APIRequestContext` that authenticates itself and uses `API_BASE_URL`, and declare the dependency explicitly in the fixture.

### F16 (Low): Double error wrapping
Every flow wraps both `withContext` and `test.step` around the same action, and `loginAsUser` → `LoginPage.loginAs` adds a third layer with the same meaning. Failure messages come out as `Signing in as a@b: Logging in as a@b: <original>`. That's readable but noisy, and `test.step` already gives the report the same context.

**Fix:** Keep `test.step` in flows and use `withContext` only where no step exists.

### F17 (Low): Coverage gaps
All 15 tests are happy-path apart from one invalid-login test. There are no tests for:
- required-field validation on the order or user panels
- inviting a duplicate email
- invalid status transitions (for example shipped → pending)
- a standard or read-only user trying to reach `/users`

The role model exists in `domain.ts`, and `standardUser()` is already available.

### F18 (Low): No static enforcement of the conventions
CONTRIBUTING says the rules are "enforced by convention and PR review". There is no ESLint or Prettier config. Recommended setup: `@typescript-eslint/no-floating-promises` (a missing `await` is the most common Playwright bug), `eslint-plugin-playwright` (`no-wait-for-timeout`, `no-networkidle`, `no-raw-locators`), `no-restricted-imports` so specs can't import `Locator`, and `noUnusedLocals` in tsconfig (which would catch F20).

### F19 (Low, verify): `Error.cause` under `lib: ES2021`
`FrameworkError` sets `this.cause = cause` (`errors.ts:13`), but `tsconfig.json` sets `lib` to `["ES2021","DOM"]`. `cause` is declared in `lib.es2022.error.d.ts`, so `tsc --noEmit` (run in CI) is likely to report TS2339 unless a dependency's typings add it.

**Fix:** Set `lib`/`target` to `ES2022` and use `super(msg, { cause })`. Run `npm run typecheck` to confirm the error.

### F20 (Low): Dead code
- the `loginPage` fixture (no spec uses it)
- `OrderListPage.searchFor()` (never called; see F9)
- `OrderModifyPage.cancel()` / `UserModifyPage.cancel()` / `EntityModifyPanel.cancel()` (never called)
- the `expect` imports in `OrderModifyPage.ts:2` and `UserModifyPage.ts:2` (unused)

Either cover these with tests (cancel discards changes, search filters the grid) or delete them.

### F21–F23 (Info)
- **F21:** The modify panels extend `BasePage` and inherit `goto`/`waitForLoad` they shouldn't need (a small interface-segregation smell). A `BasePanel` or plain composition would fit better.
- **F22:** The two CI jobs are copies of each other. Use one job with a step that chooses `test:smoke` or `test:full` based on the event, or a reusable workflow.
- **F23:**
  - The `@domain/*` alias maps to `src/types/`. Rename one so they match.
  - `login.spec.ts:26` passes raw strings, which contradicts "Never log in with a raw credential string". Either document the negative-test exception in CONTRIBUTING or build an invalid `User` with the factory.
  - AAA comments appear in 3 of 15 tests. Use them everywhere or nowhere.
  - `OrderModifyPage`/`UserModifyPage` are panels, not pages. The `Page` suffix is a deliberate, documented convention, so this is just a note.

---

## 4. What's done well (keep these)

- **Clear layering:** specs call only flows and page-object methods. No spec imports `Page`/`Locator`, and no public PO method returns a `Locator` (checked across all 6 POs).
- **Composition instead of inheritance:** `EntityModifyPanel` removes the save/cancel/toast duplication between the two modify panels, and `BasePage` really does only navigation.
- **Fixture-based DI** gives each test its own login and creates nothing shared or mutable at module level.
- **Locators:** only `getByRole`/`getByLabel`/`getByTestId`. No XPath, no CSS chains, no `nth()`. Row lookups are centralized in `gridUtils`.
- **Waits:** no `waitForTimeout` or `setTimeout` anywhere. Assertions are web-first `expect`.
- **Error handling:** no empty catches. Errors are wrapped with context, and `cause` is preserved. `getUniqueGridRow` fails fast when a lookup is ambiguous.
- **Test data:** builders plus collision-resistant unique suffixes that are safe under parallel workers, and seeded credentials come from env or secrets.
- **Isolation:** each test registers what it creates for teardown cleanup. `fullyParallel` is on.
- **Config:** `forbidOnly` on CI, trace/screenshot/video kept on failure (correctly paired with `retries: 0`), a documented no-retry policy, `@smoke` tagging, strict TS, typecheck gating in CI, and the report uploaded with `if: always()`.
- **Naming:** consistent and documented. README and CONTRIBUTING describe the code accurately, apart from the exceptions in F4, F10, F15 and F23.

---

## 5. Recommended sign-off conditions

**Must fix before sign-off:** F1, F2, F3, F4, F5, F6, F7, F8.
**Should fix soon:** F9, F10, F13, F18, F19.
**Backlog:** F11, F12, F14–F17, F20–F23.

---

## 6. Assumptions and limits

- Static review only. I couldn't compile or run anything because there's no `node_modules` and no lockfile. F19 needs a `tsc` run to confirm.
- UI behavior is inferred from the page objects. F2 assumes the order panel has no "add line item" control beyond what the PO models. F9 assumes the grid's default sort doesn't guarantee new records appear on page 1. F8 assumes cleanup endpoints may return 404 for unknown records. If the real app behaves differently, adjust the severity of those findings.
- "Our usual best-practices checklist" was read as the eight areas named in the request. I added config and CI because several of the significant issues are there.
- I didn't modify the framework under review.
