# Automation Framework Issues

**Scope:** `.claude/skills/automation-framework-review-deepeval/evals/fixtures/clean-framework` — a Playwright + TypeScript UI test framework (27 files: `src/core`, `src/factories`, `src/flows`, `src/pages`, `src/types`, `src/utils`, 5 spec files under `tests/`, plus `playwright.config.ts`, `package.json`, `tsconfig.json`, CI workflow, and docs). All files were read in full.

**Excluded from this review:** Nothing excluded — full scope reviewed.

**Verdict up front:** This framework has one real, concrete issue: the pinned `@playwright/test` version (`^1.47.2`, `package.json:16`) is roughly a year-plus behind current Playwright releases as of this review. Everything else is a genuine, grep-verified clean bill of health — there is no missing business-step/flow layer, no God Base Class, no layer-boundary leakage, no swallowed exceptions, no unconditional sleeps, no fragile locators, and no naming drift. Two trivial nits are worth a one-line mention each (a verbatim-duplicated helper function, and one hardcoded placeholder password for non-privileged synthetic test users) but neither is a defect worth more than a sentence.

---

## Outdated core library: `@playwright/test` pinned to `^1.47.2`

`[Impact: Medium | Effort: Low]`

`package.json:16` pins `"@playwright/test": "^1.47.2"`. Playwright 1.47.2 shipped in September 2024; as of this review (2026-10-01), the project is roughly a year and a half behind current releases. `@types/node` (`package.json:17`, `^20.14.10`) and `typescript` (`package.json:18`, `^5.5.4`) are also behind current lines but less severely. This doesn't block any specific best practice the framework currently follows — the codebase isn't relying on any now-missing Playwright capability — but it's a real currency gap that should be closed with a routine dependency bump rather than left to drift further, since newer Playwright releases carry trace-viewer, auto-waiting, and reporter improvements relevant to §G/§J of this review.

## Duplicated `nextSuffix()` helper across the two factories

`[Impact: Low | Effort: Low]`

`src/factories/orderFactory.ts:11-16` and `src/factories/userFactory.ts:11-16` each define an identical `nextSuffix()` function (same body, same doc comment) instead of importing it from one shared utility module. This is the one piece of literal copy-paste found anywhere in the codebase — everywhere else (grid-row lookup, error wrapping, panel actions) is centralized in a single shared helper. Low impact: the function is small, stable, and independent in both call sites, so the duplication carries negligible maintenance risk, but it's worth collapsing into `src/utils/` the next time either factory is touched.

## Hardcoded placeholder password for synthetic test users

`[Impact: Low | Effort: Low]`

`src/factories/userFactory.ts:31` sets `password: 'Test-Passw0rd!'` as the default for `UserBuilder`-constructed users. This is a literal matching the mandated hardcoded-credential grep pattern, so it's reported here for completeness, but context matters: it is a synthetic, non-privileged value used only for ad-hoc test users built via `buildUser()`, not a real or shared credential. The two "real" seeded identities (`adminUser()`, `standardUser()`, `userFactory.ts:66-72` and `76-83`) correctly read from `process.env.ADMIN_PASSWORD`/`process.env.STANDARD_PASSWORD`, and `.env` itself is gitignored (`.gitignore:12-13`) with only `replace-me` placeholders in `.env.example`. No action needed beyond awareness; flagged only because the grep is mandatory and the pattern matched.

---

## FIRST principles table

| Letter | Verdict | Evidence |
|---|---|---|
| **F**ast | + | No `Thread.sleep`/`time.sleep`/`waitForTimeout`/`setTimeout`/`implicitlyWait` anywhere (0 hits, repo-wide grep). Waits are event-based (`waitForLoadState('networkidle')`, `BasePage.ts:18`) or condition-based (`locator.waitFor({state:'visible'})`, `gridUtils.ts:29`). `fullyParallel: true` (`playwright.config.ts:16`) with worker-safe ID generation (`nextSuffix()` combining worker index, timestamp, and entropy). |
| **I**ndependent | + | 0 module-level shared mutable state across the 5 spec files; each fixture constructs fresh state per test (`fixtures.ts:16-17`). Cross-worker collision risk explicitly mitigated by `nextSuffix()`'s worker-index component rather than bare `Date.now()`/`Math.random()`. |
| **R**epeatable | + | 0 hardcoded date/timestamp literals in assertions; all dynamic data flows through the two factories' suffix generator. Environment switching is fully via env vars (`.env.example`, `playwright.config.ts:30`), so the suite isn't tied to one environment's state. |
| **S**elf-validating | + | 15 of 15 `test()` cases contain at least one assertion (verified per-test, all routed through typed `expect*` page-object methods rather than raw `expect()` calls in test bodies). 0 assertion-free tests. |
| **T**imely | N/A statically | Suite is small (15 tests, 5 spec files) with a working smoke/full split: 6 of 15 tests tagged `@smoke` run on PR (`e2e-tests.yml:14-16`, `package.json:9`), full suite runs on push/schedule/dispatch (`e2e-tests.yml:52-54`). Actual wall-clock runtime isn't determinable from static review. |

---

## Recommended actions, in priority order

1. **Bump `@playwright/test` (and related `@types/node`/`typescript` pins) to a current release.** `[Impact: Medium | Effort: Low]` — `package.json:16`. Routine dependency maintenance; no code changes required beyond the version bump and a regression run.
2. **Extract `nextSuffix()` into a shared utility module.** `[Impact: Low | Effort: Low]` — `orderFactory.ts:11-16`, `userFactory.ts:11-16`. Mechanical, localized refactor: move the function to `src/utils/`, import it from both factories, delete the duplicate.
3. **No action required** on the `userFactory.ts:31` placeholder password beyond awareness — it is a synthetic, non-privileged default, not a real credential. If the team wants zero literal matches on credential-pattern greps going forward, source it from a named constant instead of an inline string, but this is cosmetic.

---

## Checklist tab input

| Section | Check | Status (+/-) | Comments |
|---|---|---|---|
| Framework | Framework is consistent | + | Optional/null idiom uniform (`domain.ts:30`, `?` only, no `null`); chaining methods consistently return typed `this`/next page object (`LoginPage.ts`, `OrderModifyPage.ts`, `UserModifyPage.ts`); doc-comment coverage complete across `src/core`, `src/utils`, `src/pages`, `src/factories`, `src/flows`. |
| Framework | Framework follows a layered architecture | + | 0 raw `page.locator/click/fill` calls or raw `Locator`/`Page` type imports in test files; dedicated `flows/` layer sits between page objects and tests and is used by all 5 spec files; page objects return correctly typed objects for chaining; `BasePage`/`EntityModifyPanel` carry no domain concepts. |
| Framework | Framework complies with DRY | + (minor nit) | `EntityModifyPanel`, `gridUtils`, and both factories are shared abstractions used consistently with 0 inline literals in tests. One verbatim duplication: `nextSuffix()` in `orderFactory.ts:11-16` and `userFactory.ts:11-16` (see finding above). |
| Framework | Framework complies with SOLID | + | `BasePage.ts` is 20 lines / 2 methods, single-responsibility (no God Base Class); no if/switch-based extensibility antipattern; 0 LSP violations across 6 page-object subclasses; `fixtures.ts` uses genuine Playwright fixture composition, not inheritance-based setup. |
| Framework | Framework complies with language standards | + | No ESLint/Prettier/.editorconfig present — judged against language-idiomatic TypeScript conventions (no formal standard found). 6/6 page objects end `Page`, 3/3 flow files end `Flows`, 2/2 factories end `Factory` + builder pattern, consistent `get*`/`expect*` method-naming semantics, 0 mixed-case or mismatched conventions found. |
| Framework | Unconditional waits are not a common practice | + | 0 hits for `Thread.sleep`/`time.sleep`/`waitForTimeout`/`setTimeout`/`implicitlyWait` repo-wide. |
| Framework | Tests are atomic and independent | + | 0 shared mutable state across spec files; fresh fixture state per test. |
| Framework | Tests remain independent under parallel execution | + | `fullyParallel: true` configured, and `nextSuffix()` is specifically engineered (worker index + timestamp + entropy) to avoid cross-worker record collisions. |
| Framework | Core libraries/framework/language versions are reasonably current | - | `@playwright/test` pinned to `^1.47.2`, roughly a year+ behind current releases as of 2026-10-01 (see finding above). |
| Framework | No hardcoded credentials/secrets in the test codebase | + (minor nit) | Only one literal match: a synthetic, non-privileged placeholder password in `userFactory.ts:31` for ad-hoc test users; the two real seeded identities correctly read from env vars, and `.env` is gitignored. |
| Running | Steps have a sufficient level of documentation for reporting | + | Test names and flow-function names read as business scenarios (e.g. "admin can log in and reach the dashboard", `login.spec.ts:6`); `@smoke` tagging used for report/CI navigability. |
| Running | When tests fail, there are mechanisms to easily find the cause | + | `trace: 'retain-on-failure'`, `screenshot: 'only-on-failure'`, `video: 'retain-on-failure'` all configured (`playwright.config.ts:33-35`); HTML report published as a CI artifact on both smoke and full-regression jobs, guarded by `if: always()` so it publishes on failure too. |
| Running | Test stability is at a sufficient level | + | `retries: 0` explicitly configured (`playwright.config.ts:21`) with documented rationale in both the config comment and `CONTRIBUTING.md:40-46` ("flaky tests should be fixed, not hidden by retrying"). This is a stated policy, not independent proof of stability, but it is evidence the team isn't masking flakiness with retries. |
| Running | There is a way to track run results over time | + | Playwright HTML reporter configured and published as a versioned CI artifact (14-day retention for smoke, 30-day for full regression). |
| Running | Tests are integrated into CI/CD, not run purely manually/on-demand | + | `.github/workflows/e2e-tests.yml` runs smoke tests on PR and full regression on push/schedule/dispatch. |
| Processes | Tests are properly documented | + | Business-readable test names, documented naming conventions in `CONTRIBUTING.md`, module- and method-level doc comments throughout `src/`. |
| Processes | A failure-handling strategy is implemented (bug reporting → flaky rerun → failure skipping) | + | No-retry policy is deliberate and documented (`CONTRIBUTING.md:40-46`); no retry/skip-mark mechanism exists because the team's stated strategy is "fix, don't hide" rather than quarantine-and-rerun — consistent with a documented process, not a gap.
