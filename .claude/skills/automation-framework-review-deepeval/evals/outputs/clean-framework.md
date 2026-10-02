# Automation Framework Issues

**Scope:** Full repository at `clean-framework` — `src/core`, `src/pages`, `src/flows`, `src/factories`, `src/utils`, `src/types`, all 5 files under `tests/`, `playwright.config.ts`, `package.json`, `tsconfig.json`, `.env.example`, `.gitignore`, `README.md`, `CONTRIBUTING.md`, `.github/workflows/e2e-tests.yml`.
**Not verified:** actual CI pass/fail history and suite runtime (not executed in this review); the npm-resolved `@playwright/test` version at install time (indeterminate without a lockfile — see finding below); whether a failure-skip/known-issue process exists outside the code (questionnaire territory).

**Verdict up front:** CI cannot currently complete a run: both jobs in `.github/workflows/e2e-tests.yml` invoke `npm ci`, but no `package-lock.json` exists anywhere in the repository, so the install step fails before any test executes. Beyond that, there are three low-impact issues: an identical `nextSuffix()` helper duplicated verbatim across the two factory files, Arrange/Act/Assert comments present in only 3 of 15 test methods, and one unused `expect` re-export in `src/core/fixtures.ts:108`.

---

## CI install step fails — no package-lock.json committed
[Impact: High | Effort: Low]

`.github/workflows/e2e-tests.yml:27` (`smoke` job) and `:65` (`full-regression` job) both run `npm ci`. No `package-lock.json` or `npm-shrinkwrap.json` exists anywhere in the repository (confirmed by a repository-wide file search). `npm ci` requires one of these lockfiles to be present and exits with an error when it is missing, so the "Install dependencies" step fails in both jobs before `npx playwright install` or any test runs — on every PR, every push to `main`, every nightly run, and every manual dispatch.

**Fix:** commit a `package-lock.json` generated from the current `package.json`, or change both `npm ci` steps to `npm install` if a committed lockfile is not intended.

## Duplicated `nextSuffix()` helper across factories
[Impact: Low | Effort: Low]

`src/factories/orderFactory.ts:11-16` and `src/factories/userFactory.ts:11-16` define a byte-identical `nextSuffix()` function, including the same doc comment, as a private module-level helper in each file rather than a shared import.

**Fix:** move `nextSuffix()` into a shared module (e.g. `src/utils/testIdentity.ts`) and import it from both factories.

## Inconsistent Arrange/Act/Assert comment usage across tests
[Impact: Low | Effort: Low]

3 of 15 test methods carry explicit `// Arrange` / `// Act` / `// Assert` comments; the other 12 follow the same blank-line-separated phase structure without the labels. Commented: `tests/auth/login.spec.ts:6-15`, `tests/orders/createOrder.spec.ts:6-21`, `tests/users/registerUser.spec.ts:6-17`. Uncommented with the identical structure: `tests/auth/login.spec.ts:17-23,25-29`, `tests/orders/createOrder.spec.ts:23-30,32-39,41-48`, `tests/orders/updateOrderStatus.spec.ts:6-42` (all three tests), `tests/users/registerUser.spec.ts:19-26,28-35`, `tests/users/changeUserRole.spec.ts:6-31` (both tests).

**Fix:** either add the comments to the remaining 12 tests or remove them from the 3 that have them, so the convention is applied the same way everywhere.

## Unused `expect` re-export in fixtures.ts
[Impact: Low | Effort: Low]

`src/core/fixtures.ts:108` re-exports `expect` from `@playwright/test`. A repository-wide search for `from '@core/fixtures'` returns 8 import sites (5 test files, 3 flow files); none of them import `expect` — every assertion in the suite goes through page-object verify methods (`expectLoginError`, `expectRowWithEmail`, `expectStatusFieldValue`, etc.) instead. 0 references to this re-export outside its own declaration.

**Fix:** delete the re-export, or keep it only if it's intended as a deliberate public API for future direct-assertion tests.

---

## FIRST principles table

| Letter | Verdict | Evidence |
|---|---|---|
| Fast | Pass | 0 occurrences of `Thread.sleep`/`time.sleep`/`waitForTimeout`/`setTimeout`/`implicitlyWait` anywhere in the repo; `fullyParallel: true` (`playwright.config.ts:16`); PRs run only the `@smoke`-tagged subset (6 of 15 tests tagged, `e2e-tests.yml:14-16`). |
| Independent | Pass | Every test builds its own entity via `OrderBuilder`/`UserBuilder` with a worker-index + timestamp + random suffix (`src/factories/orderFactory.ts:11-16`, `userFactory.ts:11-16`); the `createdRecords` fixture (`src/core/fixtures.ts:60-77`) tears down created orders/users after each test, including on failure. |
| Repeatable | Pass | No hardcoded dates/environment-specific literals found in any assertion across the 5 spec files; every entity gets a freshly generated unique suffix per `build()` call. |
| Self-validating | Pass | 15 of 15 test methods call at least one page-object verify/expect method (`tests/auth/login.spec.ts`, `tests/orders/createOrder.spec.ts`, `tests/orders/updateOrderStatus.spec.ts`, `tests/users/registerUser.spec.ts`, `tests/users/changeUserRole.spec.ts`). |
| Timely | N/A statically | Actual suite runtime wasn't executed in this review; CI caps the smoke job at 20 minutes and the full-regression job at 60 minutes (`e2e-tests.yml:18,56`). |

## Recommended actions

1. Commit a `package-lock.json` (or switch both CI jobs to `npm install`) so `npm ci` in `.github/workflows/e2e-tests.yml:27,65` stops failing before any test runs. [Impact: High | Effort: Low]
2. Extract the duplicated `nextSuffix()` helper in `src/factories/orderFactory.ts:11-16` and `src/factories/userFactory.ts:11-16` into one shared module. [Impact: Low | Effort: Low]
3. Apply the Arrange/Act/Assert comment convention uniformly across all 15 test methods (currently present in 3 of 15). [Impact: Low | Effort: Low]
4. Remove or document the unused `expect` re-export in `src/core/fixtures.ts:108`. [Impact: Low | Effort: Low]

## Checklist tab input

| Section | Check | Status (+/-) | Comments |
|---|---|---|---|
| Framework | Framework is consistent | - | 3 of 15 test methods carry explicit Arrange/Act/Assert comments, the other 12 don't (`tests/auth/login.spec.ts:6-29`, `tests/orders/createOrder.spec.ts:6-48`); page-object method-chaining return types are consistent across all 6 page-object files. |
| Framework | Framework follows a layered architecture | + | 0 occurrences of `Page`/`Locator` imported from `@playwright/test` in `tests/`; every page-object public method returns `this`, a typed page object, or `void`/`Promise<void>`; the `src/flows/` business-step layer is used by all 5 spec files. |
| Framework | Framework complies with DRY | - | `nextSuffix()` is duplicated verbatim in `src/factories/orderFactory.ts:11-16` and `src/factories/userFactory.ts:11-16`; otherwise `OrderBuilder`/`UserBuilder` are the only entity-construction path used (0 inline `Order`/`User` object literals found in any test). |
| Framework | Framework complies with SOLID | + | No God base class — `BasePage` provides only `goto`/`waitForLoad` (`src/core/BasePage.ts:10-20`); the Playwright `Page`/`Locator` API is used consistently through page objects rather than inconsistently wrapped. |
| Framework | Framework complies with language standards | + | 6 of 6 page-object files/classes end in `Page`; all 5 test files end in `.spec.ts`; both factory modules follow `<entity>Factory.ts` exporting `<Entity>Builder`/`build<Entity>()`, with no outliers against CONTRIBUTING.md's documented convention. |
| Framework | Unconditional waits are not a common practice | + | 0 occurrences of `Thread.sleep`/`time.sleep`/`waitForTimeout`/`setTimeout`/`implicitlyWait` repo-wide. |
| Framework | Tests are atomic and independent | + | Every test constructs its own uniquely-suffixed order/user and registers it with the `createdRecords` fixture (`src/core/fixtures.ts:60-77`) for teardown; no shared mutable state across test bodies. |
| Framework | Tests remain independent under parallel execution | + | `fullyParallel: true` (`playwright.config.ts:16`); `nextSuffix()` combines `TEST_WORKER_INDEX`, `Date.now()`, and `Math.random()` specifically to avoid cross-worker collisions (`orderFactory.ts:11-16`, `userFactory.ts:11-16`). |
| Framework | Core libraries/framework/language versions are reasonably current | + | `@playwright/test` is declared as `^1.47.2` (`package.json:16`), a caret range npm resolves to the latest compatible 1.x release; no missing capability elsewhere in this review was traced to this version. The actual resolved version isn't reproducible without a lockfile — see the missing `package-lock.json` finding above. |
| Framework | No hardcoded credentials/secrets in the test codebase | + | `.env.example:9,11` only contains the placeholder `replace-me`, mirrored by the same fallback in `src/factories/userFactory.ts:69,79`; CI supplies real credentials via GitHub Actions secrets (`e2e-tests.yml:38-42,76-80`). |
| Running | Steps have a sufficient level of documentation for reporting | + | Every flow function wraps its steps in `test.step()` with a business-readable label (e.g. `src/flows/orderFlows.ts:19,37`); test titles describe the business scenario under test. |
| Running | When tests fail, there are mechanisms to easily find the cause | + | `trace: 'retain-on-failure'`, `screenshot: 'only-on-failure'`, `video: 'retain-on-failure'` (`playwright.config.ts:33-35`); `withContext()` wraps actions in business-context error messages (`src/utils/errors.ts:23-29`). |
| Running | Test stability is at a sufficient level | + | `retries: 0` (`playwright.config.ts:21`), so no default retry masks flakiness; this shows the team isn't hiding failures behind retries, not that the suite is stable under real execution (not run in this review). |
| Running | There is a way to track run results over time | + | HTML report published as a build artifact on every run including failures (`e2e-tests.yml:44-50,82-88`), plus the `github` reporter in CI (`playwright.config.ts:26`). |
| Running | Tests are integrated into CI/CD, not run purely manually/on-demand | - | Triggers are configured for PR (smoke), push to `main`, a nightly schedule, and manual dispatch (`e2e-tests.yml:3-11`), but both jobs run `npm ci` with no `package-lock.json` in the repo, so the install step fails before any test executes (`e2e-tests.yml:27,65`). |
| Processes | Tests are properly documented | + | `test.step()` labels and test titles describe business intent throughout; CONTRIBUTING.md's documented naming/layering conventions match the actual file and class names with no outliers found. |
| Processes | A failure-handling strategy is implemented (bug reporting → flaky rerun → failure skipping) | - | No skip-with-reason or known-issue-link annotation mechanism exists in the test code; `CONTRIBUTING.md:40-46` states a flaky test "must be discussed and justified in the PR" before a retry is added, but this is a written review-process policy, not an automated mechanism. |