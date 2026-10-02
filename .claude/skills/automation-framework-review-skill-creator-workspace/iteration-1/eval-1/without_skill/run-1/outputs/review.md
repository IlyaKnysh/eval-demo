# Test Automation Framework Review — CRM Admin UI Tests (Java/TestNG/Selenium)

**Reviewed path:** `.claude/skills/automation-framework-review-deepeval/evals/fixtures/messy-framework`
**Reviewer:** Senior engineer review (manual, no checklist/skill used)
**Date:** 2026-10-01

## Scope

Reviewed all production and test sources: 1 base page class, 10 page objects, 5 utility classes, 7 test classes (plus 2 "wip" scratch test classes), `pom.xml`, `testng.xml`, CI workflow, and `config.properties`. Read every file in full; no file was skipped.

## Summary

This framework has the shape of a page-object-based Selenium/TestNG suite, but most of the engineering practices that make such a framework maintainable are missing. The most serious problems are: production credentials and a production database connection string committed to source control, tests that execute directly against a live production environment, reliance on `Thread.sleep` instead of explicit waits (38 occurrences), brittle auto-generated/positional locators throughout, a "god object" `BasePage`, heavy copy-paste duplication across four near-identical "modify" page objects, oversized multi-feature "god tests" with no isolation, assertion-free tests that can never fail, and dead/unused utility code. Below is the full list of issues found, roughly grouped by theme, followed by a severity-rated checklist table.

---

## Issues

### Security & secrets management

1. **Plaintext production credentials committed to the repo.** `src/test/resources/config.properties` contains a live-looking admin username/password (`admin@acmecorp.com` / `Admin123!`) and a production database user/password (`crm_svc` / `Sup3rSecret!`), committed in cleartext with no `.gitignore` exclusion or secrets manager.
2. **Hardcoded credentials duplicated across source files**, not just config. The same admin credentials are hardcoded literally in `LoginPage.loginAsAdmin()`, and again inline in `FullAdminWorkflowTests`, `FullInvoiceBillingCycleTests`, `FullProductLifecycleTests`, and `ScratchLoginExperimentTest`. Changing the password requires a multi-file find-and-replace.
3. **Hardcoded production database connection in `DbConnector`.** The JDBC URL, user, and password (`prod-crm-db.acmecorp.internal`, `crm_svc`, `Sup3rSecret!`) are hardcoded constants, duplicating the same production credentials found in `config.properties`.
4. **Tests and verification utilities target the production environment directly**, not a dedicated test/staging environment. `config.properties`'s `baseUrl`/`apiUrl` point at `crm-admin.acmecorp.com`, and `DbConnector` points at `prod-crm-db.acmecorp.internal` / `crm_production`. Running this suite executes real create/modify/archive workflows (and installs committed test data) against production.
5. **SQL built via raw string concatenation.** `DbConnector.getOrderCountForCustomer()` concatenates a `customerEmail` parameter directly into a SQL string instead of using a `PreparedStatement`. This is a SQL-injection-shaped anti-pattern, and especially risky paired with finding 4 (it runs against the production DB).
6. **No `.gitignore` anywhere in the repo.** Build output (`target/`), the automation log file, result CSVs, and screenshots (all written under `target/`) have no exclusion rule and risk being committed, alongside the already-committed secrets above.

### Environment & configuration

7. **Single hardcoded environment, no environment abstraction.** There is no profile/parameterization for dev/staging/prod — `config.properties` has one `baseUrl`, and it is production. There's no evidence the properties file is even read by the tests (see finding 19); most classes hardcode the URL directly instead.
8. **Outdated, unsupported dependency stack.** Java 8, Selenium 3.141.59 (last released 2019, unmaintained, built on the deprecated JSON Wire Protocol rather than W3C WebDriver), and TestNG 6.14.3 (2018-era, several majors behind current 7.x). No dependency-update process is evident (no Dependabot/Renovate config).
9. **CI runs on every branch with no gating.** `.github/workflows/ci.yml` triggers on push/PR to `branches: ["**"]` (literally every branch) but has no artifact upload for screenshots/reports, no caching, no failure threshold/quality gate, and no separation between smoke/regression suites — it just runs the entire suite every time and `cat`s raw surefire text output.
10. **No secrets handling in CI.** The workflow doesn't reference secrets or environment injection at all, implying the credentials are read straight out of the committed `config.properties` even in CI.

### Architecture & design (page objects / base classes)

11. **`BasePage` is a god object.** It mixes unrelated responsibilities in one class: navigation, explicit waits, raw element access, click/type helpers, two different sleep-based "wait hacks," alert/modal/cookie-banner handling, TestNG assertions, text-comparison "verification" logic, file logging, CSV result writing, JS-executor scroll/highlight/page-ready checks, frame switching, dropdown selection, and hover. A page object base should provide navigation/wait primitives; assertions, logging, and reporting belong in separate, composable collaborators.
12. **Assertions live inside the page-object base class.** `assertTextPresent`, `assertElementVisible`, `assertUrlContains`, and `compareElementText` are defined on `BasePage`, meaning every page object (whose job is to model a page) also inherits assertion/verification responsibility. This blurs the separation between "how to interact with the page" and "what the test expects," making both harder to reuse and test independently.
13. **Massive copy-paste duplication across "modify" page objects.** `OrderModifyPage`, `ProductModifyPage`, `UserModifyPage`, and `InvoiceModifyPage` are near character-for-character identical (same method names: `verifyFieldIsEditableAndEnabled`, `enterName`, `selectStatus`, `enterEmail`, `clickSave`, `toggleActive`; same save/active-checkbox locator patterns), differing only in field locators and a hardcoded error message string. This should be a single generic/parameterized "entity modify panel" component instead of four hand-copied classes — any shared bug fix (e.g., to the save/activation flow) now has to be applied four times.
14. **Inconsistent page-object naming convention.** Every class is suffixed `*Page` except `OrderHandler` and `UserManagement`, which model grid/list screens exactly like the `*Page` classes but break the naming convention for no apparent reason, making it harder to predict a class name from its screen.
15. **Brittle, unmaintainable locators throughout.** Nearly every page object uses one or both of: (a) framework/tool auto-generated IDs like `ext-comp-2091`, `ext-comp-1047`, `ext-comp-5021`, `ext-comp-1023`, `ext-comp-4108/4109`, `ext-comp-3312`, `ext-comp-1188`, `ext-comp-5033` (8 of 10 page objects), which look copy-pasted straight from a browser inspector and will silently drift/break on any front-end rebuild; or (b) absolute positional XPath like `//div[1]/div[1]/nav/ul/li[3]/a`, `//div[3]/div[2]/table/tbody/tr[6]/td[2]/input`, `//div[2]/div[1]/form/div[1]/input` (6 of 10 page objects), which breaks the instant the DOM structure shifts by one element and gives no semantic signal about what it targets. No stable `data-testid`/`data-qa` locator strategy is used anywhere.
16. **Raw element/locator leakage via `getRawElement`/`getRawElements`.** `BasePage` exposes raw `WebElement` escape hatches, and several test classes (see findings 20-21) use raw `driver.findElement(By...)` calls directly instead of going through page objects at all — defeating the purpose of the page-object layer.
17. **Dead/unused utility classes.** `EmailSenderUtil` (sends real SMTP emails on test failure) and `ScreenshotUtil` (captures and writes screenshots to disk) are fully implemented but never called from any test, listener, or page object in the codebase. Either they're leftover scaffolding that should be removed, or they were intended to be wired into failure handling (e.g., via an `ITestListener`) and that wiring was never finished — either way it's dead code that costs maintenance attention for zero benefit today.
18. **No real logging framework.** `BasePage.log()` hand-rolls timestamps and writes to both `System.out` and a manually-opened `FileWriter` on every call (re-opening/closing the file handle each time), instead of using SLF4J/Logback/Log4j2, which would give configurable log levels, rotation, and structured output for free.
19. **`config.properties` appears to be unused by the code.** No class in `src/main` or `src/test` was found reading `config.properties` via `Properties`/`ResourceBundle` — URLs and credentials are hardcoded directly in Java instead, making the properties file actively misleading (it looks like the source of truth but isn't).

### Test design

20. **"God tests" covering 10-13 unrelated features in a single `@Test` method.** `FullAdminWorkflowTests.testFullAdminWorkflowEndToEnd()`, `FullInvoiceBillingCycleTests.testFullInvoiceBillingCycleEndToEnd()`, and `FullProductLifecycleTests.testFullProductLifecycleEndToEnd()` each chain 10+ numbered "feature" blocks (login, register, search, modify, create order, archive, logout, etc.) inside one test method. If feature 3 fails, TestNG reports one failing test with no way to tell, from the report alone, which of the 10+ steps broke — defeating the diagnostic value of having a test suite at all. These should be decomposed into independent, single-responsibility test methods.
21. **Raw Selenium calls embedded directly in test classes, bypassing page objects.** `FullProductLifecycleTests` and `FullInvoiceBillingCycleTests` call `driver.findElement(By...)` directly (e.g., `.nav-products`, `#productNameInput`, `.toast-success`, `.btn-archive`, `.archive-modal .btn-confirm`) instead of going through a page object. This means locators are duplicated/scattered across both the page-object layer and the test layer, so the earlier "only maintain locators in one place" benefit of page objects is partially lost.
22. **Tests with no assertions — cannot ever fail on a real regression.** `ProductGridTests.testOpenProductGridAndFilter()` and `testSortProductGridByPrice()` perform UI actions and assert nothing at all. `testExpandProductDetailsPanel()` calls `detailsPanel.isDisplayed()` but never asserts on the result (same pattern in `FullProductLifecycleTests`'s `exportToast.isDisplayed();` call). These tests will pass even if the underlying feature is completely broken, as long as no uncaught exception/`NoSuchElementException` is thrown first.
23. **Cross-test ordering dependencies via shared static mutable state.** `CreateOrderTests.orderIdFromFirstTest` and `RegisterUserTests.lastRegisteredEmail` are static fields set by one `@Test(priority=N)` method and read by a later one. `RegisterUserTests.testDependsOnPreviouslyRegisteredEmail` exists purely to assert that earlier test state "stuck" — this makes tests order-dependent and non-parallelizable, and a single early failure cascades into unrelated-looking failures downstream.
24. **Driver lifecycle managed inconsistently, with leak risk.** Some classes use `@BeforeClass`/`@AfterClass` for setup/teardown (`CreateOrderTests`, `InvoiceLookupTests`, `ProductGridTests`, `RegisterUserTests`); others instantiate the driver inline inside the `@Test` method itself wrapped in `try/finally` (`FullAdminWorkflowTests`, `FullInvoiceBillingCycleTests`, `FullProductLifecycleTests`); and the two `wip` scratch tests (`DebugOrderExportTest`, `ScratchLoginExperimentTest`) instantiate a `ChromeDriver` with no `try/finally` at all, so any exception before the explicit `driver.quit()` call leaks a live browser/driver process. There's no shared base test class or driver-factory abstraction, so every test class re-implements its own setup.
25. **Scratch/WIP/debug test classes are checked into the main suite and actively executed in CI.** `testng.xml` includes the `com.acme.crm.wip` package alongside the real `com.acme.crm.tests` package, so `DebugOrderExportTest` ("remove before merge") and `ScratchLoginExperimentTest` ("TODO: delete this or move it somewhere real - Dave, 2024") run on every CI build. Neither asserts anything meaningful (`ScratchLoginExperimentTest` literally logs `"did it work? who knows"` to stdout), so they add execution time and noise without adding verification value, and their presence in the default suite signals no code-review gate on what gets merged into the test run.
26. **No test categorization/tagging (smoke vs. regression vs. slow).** `testng.xml` has a single `<test>` block running every package with no TestNG `<groups>`/`groups.include` usage, so there's no way to run a fast smoke subset in CI versus a full regression pass elsewhere; every change pays the cost of the entire (slow, sleep-laden) suite.
27. **Retry masking flaky tests instead of fixing root causes.** `testng.xml` configures `retryCount=3` via `RetryListener`, silently retrying any failing test up to 3 times. Combined with the extensive `Thread.sleep` usage (finding 28) and tests hitting production, this is very likely compensating for timing-based flakiness rather than the team fixing the underlying wait strategy. Blanket suite-wide retries also hide genuinely broken tests behind "eventually passed."

### Reliability & wait strategy

28. **Pervasive `Thread.sleep` instead of explicit/fluent waits — 38 occurrences across the codebase.** Nearly every navigation or state-changing action is followed by a fixed sleep (ranging 800ms-4000ms): e.g., `DashboardPage.openOrdersMenu()`, `LoginPage.login()`/`loginAsAdmin()`, `OrderCreatePage.submit()`, `OrderHandler.clickExport()`, `UserRegisterPage.submitRegistration()`, and dozens more inline in the "god tests." `BasePage` even names two of its own methods `waitForPageLoadHack()` and `waitForAjaxSpinnerHack()` — the "Hack" suffix is the code acknowledging its own anti-pattern. This makes the suite both slow (seconds of pure waiting per test) and still flaky (a slow environment can still exceed the fixed sleep). `BasePage` does have proper `waitUntilDisplayed`/`waitUntilClickable` (`WebDriverWait`/`ExpectedConditions`) available, but it's barely used anywhere compared to the sleep calls.
29. **`isElementPresentNow()` is a non-waiting, throwaway-exception presence check used as the primary "did this show up" mechanism.** `LoginPage.isErrorBannerShown()`, `DashboardPage.isWelcomeBannerVisible()`, and `UserRegisterPage.isSuccessMessageShown()` all delegate to this instant, no-retry check (comment even says "raw non-retrying instant check, no wait" in `LoginPage`), meaning it depends entirely on being called after a `Thread.sleep` happened to be "long enough" elsewhere — two unreliable mechanisms compounding each other.
30. **`compareElementText()` silently swallows all exceptions and defaults to `true`.** `BasePage.compareElementText(locatorA, locatorB)` catches every `Exception` and, on failure to even locate the elements, returns `true` (not `false`) — meaning a broken locator or missing element is interpreted as a successful comparison match. Any test relying on this method for verification could pass when it should fail.

### Code quality / maintainability

31. **Massive logic duplication in test "inline helper" methods.** `CreateOrderTests.createOrderInline()` and `RegisterUserTests.registerInline()` are private helpers that just forward a long parameter list into a sequence of page-object calls — described in the code's own comment as "not a real builder/factory." This is a sign the team recognized the need for a test-data builder pattern but didn't implement one, so adding one more field to the form requires touching every call site's positional argument list.
32. **Magic strings/numbers throughout instead of named constants or test-data builders.** Credentials, URLs, sleep durations, and expected UI strings ("Paid", "Processing", "Widget Pro") are all inlined as literals directly in test bodies rather than centralized as constants or produced by a test-data factory.
33. **Inconsistent exception handling style.** Some empty catch blocks silently swallow `InterruptedException` with no comment or log (`DashboardPage.openOrdersMenu()`, most of the "god tests"); others log on the same exception type (`OrderHandler.clickExport()`); `compareElementText` swallows all exceptions (finding 30); `DbConnector`/`EmailSenderUtil` print to `System.err`. There's no consistent policy for what gets logged, rethrown, or silently ignored.
34. **No code style/static analysis tooling configured.** No Checkstyle, PMD, SpotBugs, or Spotless plugin in `pom.xml`, and no `.editorconfig` — nothing in the build enforces consistent formatting or catches the kinds of issues listed above automatically.

---

## Notes on what's working reasonably well

- The suite does use the page-object pattern as its overall structure (even though execution is inconsistent — see findings 13, 16, 21).
- `BasePage` does provide proper explicit-wait helpers (`waitUntilDisplayed`, `waitUntilClickable`) built on `WebDriverWait`/`ExpectedConditions` — the right primitive exists, it's just underused relative to `Thread.sleep`.
- A retry-analyzer and `@Listeners` mechanism is wired up for TestNG (even though, per finding 27, it's likely being used to mask flakiness rather than as a deliberate, narrow retry policy).
- CI does exist and runs on every push/PR (even though it has no gating or environment separation — finding 9).

---

## Checklist-tab table

| # | Area | Finding | Severity | Evidence (file) |
|---|------|---------|----------|------------------|
| 1 | Security | Plaintext prod admin + DB credentials committed in config | Critical | `src/test/resources/config.properties` |
| 2 | Security | Hardcoded credentials duplicated across 5+ source files | Critical | `LoginPage.java`, `FullAdminWorkflowTests.java`, `FullInvoiceBillingCycleTests.java`, `FullProductLifecycleTests.java`, `ScratchLoginExperimentTest.java` |
| 3 | Security | Hardcoded production DB connection string/credentials | Critical | `utils/DbConnector.java` |
| 4 | Environment | Tests and DB utility run directly against production, no test/staging env | Critical | `config.properties`, `DbConnector.java` |
| 5 | Security | SQL built by string concatenation (injection-shaped) against prod DB | High | `utils/DbConnector.java:32` |
| 6 | Repo hygiene | No `.gitignore`; build output/logs/screenshots/CSVs can be committed | Medium | repo root |
| 7 | Environment | No environment abstraction/profiles; single hardcoded env | High | `config.properties`, all page/test classes |
| 8 | Dependencies | Outdated/unsupported stack: Java 8, Selenium 3.141.59, TestNG 6.14.3 | High | `pom.xml` |
| 9 | CI/CD | CI runs on every branch, no quality gate, no artifact upload, no caching | Medium | `.github/workflows/ci.yml` |
| 10 | CI/CD | No secrets management in CI; reads credentials from committed file | High | `.github/workflows/ci.yml`, `config.properties` |
| 11 | Architecture | `BasePage` god object mixing nav/wait/assert/log/CSV/JS-exec responsibilities | High | `pages/BasePage.java` |
| 12 | Architecture | Assertions defined inside page-object base class | Medium | `pages/BasePage.java` |
| 13 | Duplication | 4 near-identical "modify" page objects, copy-pasted | High | `OrderModifyPage.java`, `ProductModifyPage.java`, `UserModifyPage.java`, `InvoiceModifyPage.java` |
| 14 | Naming | Inconsistent page-object naming convention (`*Handler`/`*Management` vs `*Page`) | Low | `OrderHandler.java`, `UserManagement.java` |
| 15 | Locators | Brittle auto-generated (`ext-comp-NNNN`) and positional XPath locators | Critical | 8 of 10 page objects (`ext-comp-*`); 6 of 10 (positional XPath) |
| 16 | Architecture | Raw element/locator access leaking out of page objects | Medium | `BasePage.getRawElement/getRawElements` |
| 17 | Dead code | `EmailSenderUtil` and `ScreenshotUtil` fully implemented but never invoked | Medium | `utils/EmailSenderUtil.java`, `utils/ScreenshotUtil.java` |
| 18 | Logging | No real logging framework; hand-rolled timestamp + manual file I/O per call | Medium | `pages/BasePage.java` (`log()`) |
| 19 | Configuration | `config.properties` not read anywhere; values hardcoded instead | Medium | `config.properties` vs. all page/test classes |
| 20 | Test design | "God tests" bundling 10-13 unrelated features per `@Test` method | Critical | `FullAdminWorkflowTests.java`, `FullInvoiceBillingCycleTests.java`, `FullProductLifecycleTests.java` |
| 21 | Test design | Raw Selenium calls embedded in test classes, bypassing page objects | Medium | `FullProductLifecycleTests.java`, `FullInvoiceBillingCycleTests.java` |
| 22 | Test design | Tests with no assertions / unasserted `isDisplayed()` calls — cannot fail | Critical | `ProductGridTests.java`, `FullProductLifecycleTests.java` |
| 23 | Test design | Cross-test ordering dependency via shared static mutable fields | High | `CreateOrderTests.java` (`orderIdFromFirstTest`), `RegisterUserTests.java` (`lastRegisteredEmail`) |
| 24 | Test design | Inconsistent/leak-prone driver lifecycle management | High | `DebugOrderExportTest.java`, `ScratchLoginExperimentTest.java`, vs. `@BeforeClass`/`@AfterClass` classes |
| 25 | Test hygiene | Scratch/WIP debug tests checked in and executed by CI | High | `wip/DebugOrderExportTest.java`, `wip/ScratchLoginExperimentTest.java`, `testng.xml` |
| 26 | Test design | No smoke/regression tagging via TestNG groups | Medium | `testng.xml` |
| 27 | Reliability | Suite-wide retry (3x) likely masking flaky/timing-based failures | High | `testng.xml`, `utils/RetryListener.java` |
| 28 | Reliability | 38 `Thread.sleep` calls used instead of explicit waits; self-labeled "Hack" methods | Critical | `pages/BasePage.java` (`waitForPageLoadHack`, `waitForAjaxSpinnerHack`), pervasive across pages/tests |
| 29 | Reliability | Non-waiting instant presence check used as primary visibility verification | High | `BasePage.isElementPresentNow`, `LoginPage.isErrorBannerShown`, `DashboardPage.isWelcomeBannerVisible` |
| 30 | Correctness | `compareElementText()` swallows exceptions and defaults to `true` (false positive) | High | `pages/BasePage.java` (`compareElementText`) |
| 31 | Maintainability | Ad hoc "inline helper" methods instead of test-data builder pattern | Medium | `CreateOrderTests.createOrderInline`, `RegisterUserTests.registerInline` |
| 32 | Maintainability | Magic strings/numbers instead of constants or data builders | Medium | Pervasive across test classes |
| 33 | Maintainability | Inconsistent exception-handling policy (swallow/log/rethrow mixed) | Low | Pervasive |
| 34 | Tooling | No static analysis/style enforcement (Checkstyle/PMD/SpotBugs) configured | Low | `pom.xml` |
