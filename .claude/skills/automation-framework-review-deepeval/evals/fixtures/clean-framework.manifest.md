# clean-framework fixture — manifest

Purpose: a synthetic, deliberately GOOD TypeScript + Playwright Test framework
for the `automation-framework-review-deepeval` DeepEval suite. Ground truth: the review
should find little to nothing wrong. This manifest lists every deliberate
good practice, with exact file references, so a reviewer run against this
fixture can be checked for false positives.

Domain: Storefront Admin panel (order management, user management, auth) —
27 files total under `fixtures/clean-framework/`.

## A — Clean layering / business-step layer

- No test file imports anything from `@playwright/test` directly — confirmed
  via repo-wide grep (`tests/**/*.spec.ts` only import from `@core/fixtures`,
  `@flows/*`, `@factories/*`). Tests never touch raw `Page`/`Locator`.
- `src/core/fixtures.ts` is the sole place `@playwright/test`'s `test`/`Page`
  are imported for the fixture layer; test files re-import the wrapped
  `test`/`expect` from `@core/fixtures`.
- Flow/business-step layer: `src/flows/orderFlows.ts` (`createOrder`,
  `updateOrderStatus`), `src/flows/userFlows.ts` (`registerUser`,
  `changeUserRole`), `src/flows/authFlows.ts` (`loginAsUser`,
  `attemptInvalidLogin`). Every test calls these instead of chaining
  page-object calls inline.
- Page objects never return a raw `Locator` from a public method. Verified
  across `src/pages/*.ts`: methods return `this`, `void`, a typed page
  object (`LoginPage.loginAs` → `DashboardPage`, `DashboardPage.goToOrders`
  → `OrderListPage`, etc.), or a primitive. Internal `private get` locator
  accessors exist but are never exposed publicly.
- `Page` is imported as a type only, and only ever used as a typed
  constructor parameter in page objects (e.g. `src/pages/LoginPage.ts`
  constructor, `src/core/BasePage.ts` constructor) — exactly the
  fine/expected use called out in the review dimension.

## B — SOLID / no God base class

- `src/core/BasePage.ts` is intentionally slim: `goto()` and `waitForLoad()`
  only. No shared assertion helpers, no grab-bag utility methods.
- `src/core/fixtures.ts` uses Playwright's `test.extend` for DI/composition
  (`loginPage`, `orderListPage`, `userListPage`, `adminSession`,
  `standardSession` fixtures) instead of a deep inheritance chain.
- `src/core/EntityModifyPanel.ts` is a composed helper (used via
  has-a/composition by `OrderModifyPage` and `UserModifyPage`), not a shared
  base class — documented explicitly in its own doc comment as "not a shared
  base class, per the framework's fixture-over-inheritance convention."

## C — DRY (test data + login entry point)

- Single order factory: `src/factories/orderFactory.ts` (`OrderBuilder`
  class, `buildOrder()`, `buildMultiItemOrder()`). Used by every order test
  in `tests/orders/createOrder.spec.ts` and
  `tests/orders/updateOrderStatus.spec.ts` — no inline object literals.
- Single user factory: `src/factories/userFactory.ts` (`UserBuilder` class,
  `buildUser()`, plus environment-driven `adminUser()`/`standardUser()`).
  Used by every user/auth test in `tests/users/*.spec.ts` and
  `tests/auth/login.spec.ts`.
- One typed `User`/`Role` representation (`src/types/domain.ts`) used
  everywhere. Single login entry point: `LoginPage.loginAs(user: User)` in
  `src/pages/LoginPage.ts` — no test constructs a raw credential string and
  bypasses it. (The one negative-path exception,
  `LoginPage.submitLoginAttempt(email, password)`, is a distinct, clearly
  named method for the negative-login test case, not a bypass of
  `loginAs`.)

## C — No sibling duplication

- `OrderModifyPage` (`src/pages/OrderModifyPage.ts`) and `UserModifyPage`
  (`src/pages/UserModifyPage.ts`) are structurally similar (both are
  create/edit slide-over panels) but share their save/cancel/toast/field
  logic via the composed `src/core/EntityModifyPanel.ts` helper instead of
  copy-pasting method bodies. Each page object only adds its own
  entity-specific fields (customer/status/line items vs. email/role).

## D — Test design

- Each `.spec.ts` file has multiple small, focused tests (3–4 each), never
  one multi-feature mega-test:
  - `tests/orders/createOrder.spec.ts` — 4 tests
  - `tests/orders/updateOrderStatus.spec.ts` — 3 tests
  - `tests/users/registerUser.spec.ts` — 3 tests
  - `tests/users/changeUserRole.spec.ts` — 2 tests
  - `tests/auth/login.spec.ts` — 3 tests
- No shared mutable state between tests: every test builds its own fresh
  `Order`/`User` via the factories (unique email/name per call via an
  internal counter + timestamp in `orderFactory.ts`/`userFactory.ts`), and
  `adminSession`/`standardSession` fixtures log in fresh per test.
- Tagging: `test.describe` per feature area, plus `{ tag: '@smoke' }` on the
  representative smoke test in each file (Playwright's native tag object
  syntax, not just a string in the title).
- CI shows the PR-vs-nightly split explicitly:
  `.github/workflows/e2e-tests.yml` — `smoke` job runs `npm run test:smoke`
  on `pull_request`; `full-regression` job runs `npm run test:full` on
  `push` to `main`, a nightly `schedule` cron, and `workflow_dispatch`.
- AAA structure with `// Arrange` / `// Act` / `// Assert` comments in the
  first test of `createOrder.spec.ts`, `registerUser.spec.ts`,
  `login.spec.ts`; step-based readability elsewhere via `test.step(...)`
  calls inside every flow function (`src/flows/orderFlows.ts`,
  `userFlows.ts`, `authFlows.ts`) naming the business intent (e.g. `Create
  order for ${orderData.customerName}`).
- Every test asserts something concrete via `expect(...)` — routed through
  page-object assertion methods (e.g. `expectRowWithCustomer`,
  `expectStatusFieldValue`, `expectRoleFieldValue`, `expectLoginError`,
  `expectWelcomeVisible`), each of which contains a real `expect(locator)...`
  call (see `src/pages/*.ts`).

## F — Error handling

- Zero empty catch blocks anywhere in the repo (verified by grep).
- Single wrap-and-rethrow convention: `src/utils/errors.ts` exports
  `FrameworkError` and `withContext()`. Used consistently in
  `src/core/BasePage.ts` (`goto`), `src/pages/LoginPage.ts` (`loginAs`,
  `submitLoginAttempt`), `src/core/EntityModifyPanel.ts` (`save`),
  `src/utils/gridUtils.ts` (`getUniqueGridRow`), and every flow function in
  `src/flows/*.ts`.
- `playwright.config.ts` sets `retries: 0` with a comment explaining the
  rationale, matching `CONTRIBUTING.md`'s documented "No-retry policy"
  section.

## G — No hardcoded sleeps

- Zero uses of `page.waitForTimeout()` anywhere in the repo (verified by
  grep — this fixture takes the "zero" option, not the one-justified-
  exception option).
- All waits are Playwright auto-waiting plus explicit `expect(locator).
  toBeVisible()` / `toHaveText()` / `toHaveValue()` / `toBeHidden()` style
  condition waits (see `src/pages/*.ts`, `src/core/EntityModifyPanel.ts`).

## H — Stable locators

- Consistent semantic locators throughout: `getByRole` (buttons, links,
  alerts, status regions, table rows), `getByLabel` (form fields),
  `getByTestId` (grids/panels only, where no accessible role/label fits a
  whole-component lookup). No XPath, no CSS descent chains anywhere in the
  repo.
- Centralized dynamic-row lookup: `src/utils/gridUtils.ts`
  (`findGridRowByText`, `getUniqueGridRow`) is the single implementation of
  "find the grid row containing X," reused by both
  `src/pages/OrderListPage.ts` and `src/pages/UserListPage.ts` rather than
  being reimplemented per file.

## J — Diagnostics

- `playwright.config.ts`: `trace: 'on-first-retry'`, `screenshot:
  'only-on-failure'`, `video: 'retain-on-failure'`, HTML reporter
  (`['html', { outputFolder: 'playwright-report', open: 'never' }]`) plus
  `list` and (in CI) `github` reporters.
- Both CI jobs in `.github/workflows/e2e-tests.yml` upload
  `playwright-report/` as a build artifact with `if: always()`, so reports
  are published even on failure.
- Tests are grouped with `test.describe` per feature (`Order creation`,
  `Order status updates`, `User registration`, `User role changes`,
  `Login`), so the HTML report is browsable by area.

## K — Environment management

- `.env.example` documents every required variable (`BASE_URL`,
  `ADMIN_USERNAME`/`ADMIN_PASSWORD`, `STANDARD_USERNAME`/
  `STANDARD_PASSWORD`, `API_BASE_URL`) with placeholder, non-production
  values.
- `playwright.config.ts` reads `baseURL: process.env.BASE_URL` (falling
  back to `http://localhost:3000` for local dev, not a prod URL).
- `src/factories/userFactory.ts`'s `adminUser()`/`standardUser()` read
  credentials from `process.env.*`, falling back to obviously-fake
  placeholder values (`replace-me`) — no real/prod credential is
  committed.
- CI workflow passes secrets via `${{ secrets.* }}`, never inline.

## N — Repo hygiene

- `.gitignore` covers `playwright-report/`, `test-results/`, `.env` (plus
  `node_modules/`, `blob-report/`, `playwright/.cache/`, `.env.local`,
  build/editor artifacts).

## M — Current dependencies

- `package.json`: `@playwright/test: ^1.47.2`, `typescript: ^5.5.4`,
  `@types/node: ^20.14.10` — plausible recent pins as of the fixture's
  authoring date.

## O — Consistent naming

- Every page-object file/class ends in `Page`: `LoginPage`,
  `DashboardPage`, `OrderListPage`, `OrderModifyPage`, `UserListPage`,
  `UserModifyPage` (all in `src/pages/`). No outliers.
- `src/core/EntityModifyPanel.ts` deliberately does NOT end in `Page`
  because it is not a page object — it's a composed helper used by two
  page objects. This is documented explicitly in both `README.md`
  ("Naming conventions") and `CONTRIBUTING.md` so it is not mistaken for
  an inconsistency.
- Every flow-layer function is an action-verb phrase: `createOrder`,
  `updateOrderStatus`, `registerUser`, `changeUserRole`, `loginAsUser`,
  `attemptInvalidLogin`.
- Every test file ends in `.spec.ts`: `createOrder.spec.ts`,
  `updateOrderStatus.spec.ts`, `registerUser.spec.ts`,
  `changeUserRole.spec.ts`, `login.spec.ts`.
- Naming convention is explicitly documented in both `README.md`
  ("Naming conventions" section) and `CONTRIBUTING.md` ("Naming
  conventions" table), so the review can cite it as "documented and
  followed."

## Things that must NOT be flagged (anticipated false positives to watch for)

- `EntityModifyPanel` not ending in `Page` — intentional and documented,
  not a naming inconsistency (see §O above).
- `Page`/`Locator` type imports inside `src/pages/*.ts` and
  `src/core/*.ts` constructors — these are the expected/allowed use
  (typed constructor params), not a layering violation. Only a violation
  if found inside `tests/**` or `src/flows/**`, which it is not.
- `submitLoginAttempt` on `LoginPage` looking like a second login method
  "duplicating" `loginAs` — it is intentionally distinct: `loginAs`
  assumes success and returns `DashboardPage`; `submitLoginAttempt` is for
  the negative-path test and returns `this` (`LoginPage`) without
  assuming navigation succeeded. This is the correct way to model an
  expected-failure login without try/catch or empty catch blocks.
- 27 files vs. the requested "~18-22" — slightly over due to splitting
  tests by feature area (3 subfolders) and separating types/utils/factories
  into their own small modules for clarity; this is normal, realistic
  structure, not bloat, and should not be read as excess ceremony.
- Per-test UI login in the `adminSession`/`standardSession` fixtures
  (`src/core/fixtures.ts`) rather than a cached `storageState` — this is a
  deliberate isolation tradeoff, documented in the comment at the fixture,
  and must not be reported as a defect. Suggesting `storageState` as an
  optional speed optimisation is fair; calling the current design wrong is
  not.
- Test-data cleanup IS present and complete: the `createdRecords` fixture in
  `src/core/fixtures.ts` tracks records created by a test and deletes them in
  teardown. All four data-creating specs register with it — `createOrder`,
  `updateOrderStatus`, `registerUser` and `changeUserRole` — so a "no teardown
  / orphaned data" finding, in whole or for any subset of specs, is a false
  positive.
- The cleanup helpers also CHECK their DELETE responses: `deleteOrder` and
  `deleteUser` wrap the call in `withContext()` and throw on a non-ok status,
  matching the error convention used throughout `src/`. An earlier revision
  fired the DELETE and discarded the result, which meant a 4xx/5xx teardown
  looked identical to a successful one (Playwright's `APIRequestContext` does
  not throw on non-2xx); that is fixed. A "teardown swallows delete failures"
  or "unchecked cleanup response" finding is now a false positive.
- Trace capture works: `trace: 'retain-on-failure'` pairs correctly with the
  deliberate `retries: 0` policy. An earlier revision paired `retries: 0` with
  `'on-first-retry'`, which silently meant no trace was ever captured; that
  interaction is fixed and must not be reported.
- There is no unused `standardSession` fixture. Standard-role login is covered
  directly in `tests/auth/login.spec.ts`.
- The `createdRecords` ledger and the teardown endpoint agree on their key:
  both use `customerEmail` for orders and `email` for users. (An earlier
  revision registered `customerEmail` against a reference-keyed endpoint, so
  teardown silently no-opped; that is fixed.)
- `nextSuffix()` in both factories is safe under `fullyParallel: true`: it
  mixes `TEST_WORKER_INDEX` and random entropy with the counter, so two
  workers cannot collide in the same millisecond.
- The tsconfig path alias for domain types is `@domain/*`, deliberately NOT
  `@types/*`, which would shadow the reserved npm scope that `@types/node`
  occupies. Flagging `@domain` as an inconsistent alias is a false positive.
- `EntityModifyPanel` exposes typed `fillField`/`selectField`/`expectFieldValue`
  operations and keeps its `Locator` private. No page object receives a raw
  Locator, per CONTRIBUTING.md:24-26.
- `tsconfig` strict mode IS enforced in CI: `npm run typecheck`
  (`tsc --noEmit`) runs in both jobs of `.github/workflows/e2e-tests.yml`.
  A "strict configured but never enforced" finding is a false positive.

## Unseeded but genuine bugs (not false positives — a correct review should catch these)

- Several tests assert less than their names claim: `registerUser.spec.ts` "registers a new
  admin user" / "registers a new read-only user" and `createOrder.spec.ts`'s custom-status,
  notes and multi-item tests only check `expectRowWith*` (the row exists), never the
  role/status/notes/items under test — although `expectRoleFieldValue`/`expectStatusFieldValue`
  exist and are used by sibling specs. The §D clean claim above is about every test having a
  real assertion (presence), which still holds; this is about assertion depth.

- `nextSuffix()` (`src/factories/orderFactory.ts:11-16` and `src/factories/userFactory.ts:11-16`)
  is byte-for-byte duplicated across both factory files, including its doc comment. The
  manifest's DRY section above is about page-object/test-data-construction duplication and
  never claimed the two factories share this helper — it's a real, independently-discoverable
  cross-file duplication that should be extracted into one shared module. Flagging it is
  correct, not a false positive, despite `nextSuffix` also being cited elsewhere in this
  manifest as safe under `fullyParallel` (that claim is about correctness, not uniqueness of
  implementation — both can be true at once).
- Two spec files (`tests/orders/updateOrderStatus.spec.ts`, `tests/users/changeUserRole.spec.ts`)
  seed their precondition entity via the full UI-driving flow (`createOrder`/`registerUser`)
  even though `src/core/fixtures.ts:86-105` proves a direct `page.request` API path is already
  available (used there for teardown). A reviewer noting that these tests could seed via API
  instead of UI is a real, legitimate observation, not an invented defect.

- No `package-lock.json`/`npm-shrinkwrap.json` is committed, but both CI jobs run
  `npm ci` (`.github/workflows/e2e-tests.yml:27,64`), which hard-requires a
  committed lockfile. As committed, every CI run fails at dependency install.
  This was not an intentionally seeded defect when this fixture was authored —
  it's a real gap discovered by review — so a reviewer correctly flagging it
  is not a false positive and must not be scored as one.
- `tsconfig.json:5`'s `"lib": ["ES2021", "DOM"]` omits `ES2022`, so
  `src/utils/errors.ts:13`'s `this.cause = cause` assignment inside
  `FrameworkError` (extending `Error`) does not typecheck under `tsc --strict`
  (the `cause` property is declared in `lib.es2022.error.d.ts`). Both CI jobs
  run `npm run typecheck` as a required step. Also not an intentionally seeded
  defect — a real, independently-discoverable build-correctness bug, distinct
  from the deliberate `@domain/*` alias choice documented above. A reviewer
  naming `tsconfig.json` in a finding heading for *this* reason is correct,
  not a false-positive-guard violation.

## Deliberate minor nitpick left in (real, acceptable)

- `playwright.config.ts` runs only two browser projects (`chromium`,
  `firefox`) rather than the full three-engine matrix (no WebKit project).
  This is a reasonable, common real-world scoping choice (not a defect) and
  is the one intentionally-imperfect-but-acceptable detail in this fixture.
  A reviewer noting it as an "optional enhancement" (add WebKit/mobile
  viewport coverage) would be a fair, low-severity observation; a reviewer
  should NOT treat it as a framework-design flaw or count it toward
  layering/SOLID/DRY/error-handling/locator/diagnostics findings.

## File index

```
package.json
tsconfig.json
playwright.config.ts
.env.example
.gitignore
README.md
CONTRIBUTING.md
.github/workflows/e2e-tests.yml
src/types/domain.ts
src/utils/errors.ts
src/utils/gridUtils.ts
src/factories/orderFactory.ts
src/factories/userFactory.ts
src/core/BasePage.ts
src/core/EntityModifyPanel.ts
src/core/fixtures.ts
src/pages/LoginPage.ts
src/pages/DashboardPage.ts
src/pages/OrderListPage.ts
src/pages/OrderModifyPage.ts
src/pages/UserListPage.ts
src/pages/UserModifyPage.ts
src/flows/orderFlows.ts
src/flows/userFlows.ts
src/flows/authFlows.ts
tests/orders/createOrder.spec.ts
tests/orders/updateOrderStatus.spec.ts
tests/users/registerUser.spec.ts
tests/users/changeUserRole.spec.ts
tests/auth/login.spec.ts
```

## Corrections to the claims above (found by later review runs)

- `src/flows/authFlows.ts` does take a `Page` (type-only import): `loginAsUser(page, user)` and
  `attemptInvalidLogin(page, email, password)`. Login is the entry point that runs before any
  page object exists, so this is the expected shape, not leakage. The "only a violation if found
  inside `src/flows/**`" line in the false-positives list is wrong about this file; it should read
  "other flow files" (`orderFlows.ts`, `userFlows.ts` import page-object types only).
- `src/utils/gridUtils.ts` `findGridRowByText` returns a `Locator`. It is an internal helper called
  only by page objects; the "page objects never return a raw Locator" claim is about their public
  methods.
- `EntityModifyPanel.save()` asserting the success toast and panel closing is the action completing
  (a completion wait), not verification of business state.
- The `^1.47.2` Playwright pin is a September-2024 release. It was current when the fixture was
  written; its age is now a fair note in the core-library-currency checklist row, not a finding.
