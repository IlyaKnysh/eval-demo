# Automation Framework Issues

**Scope:** Full review of the Selenium 3 + TestNG 6 "CRM Admin UI Tests" fixture at `messy-framework/` — `src/main/java/com/acme/crm/pages` (11 page objects + `BasePage`), `src/main/java/com/acme/crm/utils` (5 utility classes), `src/test/java/com/acme/crm/tests` (7 test classes), `src/test/java/com/acme/crm/wip` (2 draft test classes), `pom.xml`, `testng.xml`, `.github/workflows/ci.yml`, `src/test/resources/config.properties`.
**Not verified:** actual CI pass/flake rate (static read only, suite was not executed); the exact runtime failure mode of the misregistered `RetryListener` (startup error vs. silent no-op) — only the registration mismatch itself is verified; whether UI-level presetup vs. API/DB-level presetup is a deliberate team choice (no presetup helpers of any kind exist to judge against).

**Verdict up front:** The suite is configured against what reads as a live production target — `config.properties` points at `prod-crm-db.acmecorp.internal`/`crm_production` with plaintext admin and DB passwords — and that file is never actually loaded by any Java code (`grep` for `Properties`/`FileInputStream` usage returns nothing for it); every credential and URL is instead hardcoded redundantly in source (`LoginPage.java:33`, `DbConnector.java:15-17`, three `Full*Tests` classes). On top of that, tests reach past the page-object layer into raw Selenium in 4 of 9 test classes (27 `driver.findElement` calls), `BasePage` is a 232-line God Class of which 24 of its 32 public methods have zero callers anywhere in the repo, 38 `Thread.sleep` calls stand in for real waits while the class's own `WebDriverWait` helpers are among the dead methods, and the suite's only safety net — a TestNG retry listener — is wired through a mechanism TestNG doesn't actually invoke for `IRetryAnalyzer` implementations.

---

## Plaintext credentials and production-named target committed to source
[Impact: High | Effort: Low]

`src/test/resources/config.properties:4,9` stores `adminPassword=Admin123!` and `dbPassword=Sup3rSecret!` in plaintext, alongside `dbHost=prod-crm-db.acmecorp.internal` and `dbName=crm_production` (lines 5,7). `DbConnector.java:15-17` hardcodes the same host/user/password as `static final` fields rather than reading the properties file, and `LoginPage.java:33` (`loginAsAdmin()`) plus `CreateOrderTests`/`RegisterUserTests`/all three `Full*Tests` classes hardcode `"admin@acmecorp.com"`/`"Admin123!"` directly in Java. The credential is duplicated in at least 3 independent places in source control, and the DB name/host read as production, not a dedicated test environment.
**Fix:** externalize all of this to env vars/CI secrets; point the DB host/name at a dedicated test instance.

## No environment-switching mechanism; `config.properties` is dead
[Impact: High | Effort: Medium]

`config.properties` exists but has zero load sites in the codebase (`grep -r "new Properties()\|FileInputStream\|config.properties"` matches only `EmailSenderUtil`'s unrelated SMTP `Properties` object and the README). There is no profile/CLI-flag/`.env` mechanism anywhere — `pom.xml` has no Maven profiles, `testng.xml` has no parameterized environment. Every URL (`"https://crm-admin.acmecorp.com/..."`) and credential pair is a literal string baked into 7+ files, so switching environments requires editing Java source throughout the suite.
**Fix:** wire an actual config loader (e.g. `Properties` + `-Denv=` system property) and delete the now-redundant hardcoded literals it replaces.

## Tests bypass the domain layer via raw Selenium calls
[Impact: High | Effort: Medium]

27 `driver.findElement` calls occur directly inside test classes (`FullInvoiceBillingCycleTests.java` ×7, `ProductGridTests.java` ×5, `InvoiceLookupTests.java` ×2, `FullProductLifecycleTests.java` ×13), bypassing page objects entirely. `ProductGridTests.java` (lines 28-52) and the product-grid section of `FullProductLifecycleTests.java` (lines 40-57, 93, 108, 113, 124-127) build and save a product via raw `WebElement` calls because **no page object exists for the product grid/create screens at all** — only `ProductModifyPage` exists, for the edit screen.
**Fix:** add the missing grid/create page objects and route these 27 call sites through them.

## 4 near-identical `*ModifyPage` classes with duplicated, AssertionError-throwing domain logic
[Impact: High | Effort: Medium]

`InvoiceModifyPage.java`, `OrderModifyPage.java`, `ProductModifyPage.java`, `UserModifyPage.java` each declare the identical method set — `verifyFieldIsEditableAndEnabled`, `enterName`, `selectStatus`, `enterEmail`, `clickSave`, `toggleActive` — with bodies identical modulo one locator and one string literal (e.g. `InvoiceModifyPage.java:22-27` vs. `OrderModifyPage.java:22-27` vs. `ProductModifyPage.java:22-27` vs. `UserModifyPage.java:22-27`). In every one of the 4, `verifyFieldIsEditableAndEnabled()` throws a raw `AssertionError` from inside the page object rather than exposing a boolean/state check for the test to assert on — business-state verification embedded in domain logic, replicated 4 times.
**Fix:** collapse the 4 classes into one generic/parameterized modify-page abstraction (or a shared `steps` helper) and move the editable/enabled check to a return value the test asserts.

## Unconditional waits: 38 `Thread.sleep` calls, and the real wait helpers are unused
[Impact: High | Effort: Medium]

`Thread.sleep` occurs 38 times across 10 files (`FullAdminWorkflowTests.java` ×9, `FullProductLifecycleTests.java` ×10, `FullInvoiceBillingCycleTests.java` ×10, `BasePage.java` ×2, `ProductGridTests.java`/`DashboardPage.java`/`OrderCreatePage.java`/`OrderHandler.java`/`UserRegisterPage.java` ×1 each, `LoginPage.java` ×2). `FullAdminWorkflowTests.java` alone sums to ≈11.7s of blocking sleep across lines 39,60,69,82,102,114,126,137,150, on top of further sleeps inside the page-object methods it calls. Meanwhile `BasePage.waitUntilDisplayed`/`waitUntilClickable` (`BasePage.java:55,60`, real `WebDriverWait`-based waits) and `waitForPageLoadHack`/`waitForAjaxSpinnerHack` (`BasePage.java:103,110`) have zero callers anywhere in the repo — nothing centralizes waiting at all.
**Fix:** replace the 38 fixed sleeps with `waitUntilDisplayed`/`waitUntilClickable` once those are actually wired to real call sites.

## No test-data uniqueness or cleanup; literal values reused across runs
[Impact: High | Effort: Medium]

No ID-generation utility exists anywhere in the codebase (the only candidate, `DateFormatterUtil.formatTimestampForFilename`, is never called — see dead-code finding below), and no builder/factory constructs test entities. `RegisterUserTests.java:37,43,51` registers the literal email `"alice.nguyen@acmecorp.com"` every run; `FullProductLifecycleTests.java:52,56` creates a product with the literal SKU `"WU-1001"`. None of the 9 test classes has an `@AfterMethod`/`@AfterClass` that deletes created orders/users/products — every `@AfterClass` (`CreateOrderTests.java:104-109`, `RegisterUserTests.java:97-102`, etc.) only calls `driver.quit()`. Rerunning the suite against a stateful backend will hit duplicate-record collisions with no cleanup to prevent it.
**Fix:** add a test-data builder with a shared unique-ID generator, and add teardown that deletes what each test created.

## Missing business-step/flow layer
[Impact: High | Effort: High]

There is no `steps`/`flows` package. Every test recomposes low-level page-object calls inline: `CreateOrderTests.createOrderInline` (lines 88-102) and `RegisterUserTests.registerInline` (lines 81-95) are private, per-class helpers duplicating the same compose-a-business-action pattern rather than a shared reusable layer, and the three `Full*Tests` classes (150-166 lines each, one `@Test` method apiece) interleave raw Selenium, page-object calls, and `Thread.sleep` inline with only `// --- feature N: ... ---` comments as narrative — comments that never appear in a TestNG/Surefire report.
**Fix:** extract a shared steps/flow layer that both the single-action tests and the `Full*Tests` workflows call into.

## God Base Class `BasePage`, 75% of it dead
[Impact: High | Effort: High]

`BasePage.java` (232 lines) is the superclass of all 11 page objects and bundles navigation, explicit waits, raw-type element access, click/type/getText primitives, sleep-hack waits, popup/modal/alert handling, assertions, a text-comparison utility, file logging, CSV result writing, JS scroll/highlight, frame switching, dropdown selection, hover, and a screenshot placeholder — 8+ unrelated responsibilities in one class. Of its 32 public methods, 24 have zero callers anywhere in the repo (verified individually): `navigateTo`, `goBack`, `getCurrentUrl`, `getPageTitle`, `waitUntilDisplayed`, `waitUntilClickable`, `getRawElement`, `getRawElements`, `waitForPageLoadHack`, `waitForAjaxSpinnerHack`, `acceptAlertIfPresent`, `dismissCookieBanner`, `closeAnyModal`, `assertTextPresent`, `assertElementVisible`, `assertUrlContains`, `compareElementText`, `writeResultToCsv`, `scrollToElement`, `highlightElement`, `switchToFrame`, `switchToDefaultContent`, `hoverOver`, `takeScreenshotPathPlaceholder`. Only 8 methods are actually exercised (`click`, `type`, `getText`, `isElementPresentNow`, `log`, `refreshPage`, `isPageLoaded`, `selectDropdownByVisibleText`).
**Fix:** split by responsibility (driver/wait, popup, logging) and delete the 24 unused methods during the split rather than carrying them forward.

## Unused utility surface, including a comparison helper that reports false matches on failure
[Impact: Medium | Effort: Low]

`DbConnector.java`, `EmailSenderUtil.java`, `ScreenshotUtil.java`, and `DateFormatterUtil.java` each have 0 references outside their own class declaration anywhere in the repo. Among the 24 dead `BasePage` methods listed above, `compareElementText` (`BasePage.java:164-171`) catches `Exception` with an empty body and then falls through to `return true` — i.e. a failed element lookup is reported identically to a genuine text match. It is currently unreachable, but it is a landmine for whoever next wires it up.
**Fix:** delete the 4 unused classes and the unused `BasePage` methods; if `compareElementText` is kept, make lookup failure return `false` (or throw), never `true`.

## `isElementPresentNow` swallows all exceptions and is used as the suite's only verification signal
[Impact: Medium | Effort: Low]

`BasePage.java:69-75` catches generic `Exception` (not just `NoSuchElementException`) and returns `false` unconditionally — a `WebDriverException` or stale-element error looks identical to "not present." It backs `DashboardPage.isWelcomeBannerVisible()` (`DashboardPage.java:24-26`), `LoginPage.isErrorBannerShown()` (`LoginPage.java:27-30`), and `UserRegisterPage.isSuccessMessageShown()` (`UserRegisterPage.java:68-70`) — all three asserted on directly in tests — with a single instant check and no retry/poll, while `BasePage.waitUntilDisplayed` (a real `WebDriverWait`) exists in the same class and is never used for this purpose.
**Fix:** scope the catch to `NoSuchElementException`, and back these three checks with `waitUntilDisplayed`/a short poll instead of a single immediate check.

## Retry mechanism is wired incorrectly and does not run
[Impact: Medium | Effort: Low]

`RetryListener` implements `IRetryAnalyzer` (`RetryListener.java:10`) but is registered via `testng.xml:5`'s `<listeners>` block, which TestNG only invokes for `ITestNGListener` implementations (`ITestListener`, `ISuiteListener`, `IAnnotationTransformer`, etc.) — `IRetryAnalyzer` is not part of that hierarchy. No `@Test` annotation in any of the 9 test classes sets `retryAnalyzer = RetryListener.class`, and no `IAnnotationTransformer` wires it in either. Separately, `RetryListener` itself never reads the `retryCount` parameter declared in `testng.xml:8` — it hardcodes `MAX_RETRY_COUNT = 3` (`RetryListener.java:13`). The suite's only flakiness safety net is non-functional as configured.
**Fix:** set `retryAnalyzer = RetryListener.class` on each `@Test` (or add a proper `IAnnotationTransformer`), and read `retryCount` from the TestNG parameter instead of hardcoding it.

## Inter-test order dependency via shared static state
[Impact: Medium | Effort: Low]

`CreateOrderTests.java:20` declares `static String orderIdFromFirstTest`, set by `testCreateStandardOrder` (`priority = 1`) and read by `testReuseOrderIdFromEarlierTest` (`priority = 5`, lines 80-85). `RegisterUserTests.java:20` declares `static String lastRegisteredEmail`, set by `testRegisterSalesUser` (`priority = 1`) and asserted by `testDependsOnPreviouslyRegisteredEmail` (`priority = 5`, lines 75-79). Both classes enforce execution order through shared mutable static fields rather than fixture composition.
**Fix:** pass the needed value explicitly (return it, or set it up directly in the dependent test) instead of relying on static state + priority ordering.

## Assertion-free and vacuous tests
[Impact: Medium | Effort: Low]

6 of 20 `@Test` methods in the suite contain no `Assert` call: `InvoiceLookupTests.testInvoiceGridLoadsWithoutError` (line 54, discards `grid.isDisplayed()`), `ProductGridTests.testOpenProductGridAndFilter`, `.testSortProductGridByPrice`, `.testExpandProductDetailsPanel` (line 52, discards `detailsPanel.isDisplayed()`), `DebugOrderExportTest.debugExportTimingIssue`, and `ScratchLoginExperimentTest.tryLoginWithWeirdCharsInPassword` (prints `"did it work? who knows"` instead of asserting, line 20). Separately, `FullProductLifecycleTests.java:87` asserts `rows.size() >= 0`, which is always true for a `List.size()` result and can never fail.
**Fix:** add real assertions to the 6 methods and replace the tautological assertion with a meaningful bound/content check.

## Locator strategy: ExtJS auto-generated IDs and positional XPath used where a stable alternative is proven available
[Impact: Medium | Effort: Medium]

Of ~57 locators in `src/main/java/com/acme/crm/pages`: 9 are auto-generated `By.id("ext-comp-NNNN")` (`DashboardPage.java:9`, `OrderCreatePage.java:10`, `OrderHandler.java:15`, `OrderModifyPage.java:13`, `InvoiceModifyPage.java:13`, `ProductModifyPage.java:13`, `UserModifyPage.java:13`, `UserRegisterPage.java:12,13`), 12 are positional `By.xpath` (8 in page objects, 4 more directly in tests), and 40 use stable `By.id`/`By.name`/`By.cssSelector`. Among the 4 sibling `*ModifyPage` classes, the identical "name field" role is located by stable `By.id` in `InvoiceModifyPage.java:12` and `ProductModifyPage.java:12`, but by a 6-level positional table XPath in `OrderModifyPage.java:12` and `UserModifyPage.java:12` — proving a stable alternative was available for that exact field. Similarly, `OrderCreatePage.java:8-9` uses 4-level positional XPath for `customerNameField`/`customerEmailField` right next to `quantityField = By.name("quantity")` (line 11) on the same form.
**Fix:** replace the `ext-comp-*` and positional-XPath locators with `By.id`/`By.name` equivalents following the pattern already used by the sibling fields/classes cited above.

## No failure diagnostics beyond raw console text
[Impact: Medium | Effort: Medium]

`ScreenshotUtil.capture()` exists but has 0 callers anywhere in the repo. `.github/workflows/ci.yml:24-26`'s only failure-diagnostic step is `cat target/surefire-reports/*.txt` — no screenshot, video, or trace is ever captured on failure, and no HTML/Allure report is generated or published from the CI run.
**Fix:** call `ScreenshotUtil.capture` from an `@AfterMethod` on failure (or add Selenium's built-in failure listener), and publish a structured report (Surefire HTML, Allure) as a CI artifact.

## Draft/debug tests run as part of every CI build
[Impact: Low | Effort: Low]

`com.acme.crm.wip` (containing `DebugOrderExportTest`, whose own Javadoc calls it a "Leftover draft test," and `ScratchLoginExperimentTest`, commented `// TODO: delete this or move it somewhere real - Dave, 2024`) is explicitly listed in `testng.xml:13` alongside `com.acme.crm.tests`, so both run in every CI invocation, not just locally.
**Fix:** remove the `com.acme.crm.wip` package from `testng.xml`'s suite definition (or delete the files).

## No `.gitignore`; generated test artifacts are uncovered
[Impact: Low | Effort: Low]

No `.gitignore` file exists anywhere in the repository. `BasePage.log()`/`writeResultToCsv()` write to `target/automation.log`/`target/results.csv`, `ScreenshotUtil` targets `target/screenshots/`, and Surefire writes `target/surefire-reports/` — none of this generated output has any ignore coverage.
**Fix:** add a `.gitignore` covering `target/`.

## Page-object naming convention drift
[Impact: Low | Effort: Low]

9 of 11 page-object classes follow a `*Page` suffix. `OrderHandler.java` and `UserManagement.java` — both grid/list page objects for the same role as `DashboardPage`/`*ModifyPage` — don't follow it (no documented naming standard exists in README/CLAUDE.md, so this is judged against the codebase's own dominant convention).
**Fix:** rename `OrderHandler`→`OrderListPage` and `UserManagement`→`UserListPage` (or equivalent) for consistency.

## No test categorization and no fast/full CI split
[Impact: Low | Effort: Medium]

`testng.xml:11-14` includes entire packages with no TestNG `groups`/`@Tag` distinction anywhere in the 9 test classes. `.github/workflows/ci.yml:4-7` triggers the identical full `mvn clean test` on every push and every PR to every branch (`branches: [ "**" ]`), with no separate fast-subset-on-PR vs. full-suite-on-merge split.
**Fix:** tag a smoke subset via TestNG `groups` and split the CI trigger into a fast PR check plus a full nightly/merge run.

---

## FIRST principles table

| Letter | Verdict | Evidence |
|---|---|---|
| **Fast** | Fails | 38 `Thread.sleep` calls across 10 files; one test method (`FullAdminWorkflowTests.testFullAdminWorkflowEndToEnd`) alone blocks ≈11.7s on sleeps, excluding sleeps inside the page-object calls it makes. |
| **Independent** | Fails | `CreateOrderTests.java:20` and `RegisterUserTests.java:20` use static fields read by a later `@Test(priority=N)`, enforcing cross-test order dependency. |
| **Repeatable** | Fails | No unique-ID generation utility or test-data builder exists anywhere; literal emails/SKUs (`RegisterUserTests.java:37`, `FullProductLifecycleTests.java:52,56`) are reused verbatim with no cleanup (`@AfterClass` only calls `driver.quit()`), risking rerun collisions against the DB named in `config.properties:7` (`crm_production`). |
| **Self-validating** | Fails | 6 of 20 `@Test` methods contain no `Assert` call (`InvoiceLookupTests.testInvoiceGridLoadsWithoutError`, 3 in `ProductGridTests`, `DebugOrderExportTest`, `ScratchLoginExperimentTest`); `FullProductLifecycleTests.java:87` asserts a tautology (`rows.size() >= 0`). |
| **Timely** | N/A statically | Not determinable from a repo read. |

## Recommended actions

1. Externalize all plaintext credentials and the production-named DB target out of source control. `[Impact: High | Effort: Low]`
2. Wire `config.properties` into an actual config loader and remove the hardcoded URLs/credentials it should replace. `[Impact: High | Effort: Medium]`
3. Add the missing page objects (product grid/create) and route the 27 raw `driver.findElement` test call sites through the domain layer. `[Impact: High | Effort: Medium]`
4. Collapse the 4 duplicated `*ModifyPage` classes into one shared abstraction and move their embedded `AssertionError` checks out of domain logic. `[Impact: High | Effort: Medium]`
5. Replace the 38 `Thread.sleep` calls with the existing-but-unused `waitUntilDisplayed`/`waitUntilClickable` helpers. `[Impact: High | Effort: Medium]`
6. Add a test-data builder with a shared unique-ID generator and real cleanup/teardown for created entities. `[Impact: High | Effort: Medium]`
7. Introduce a reusable business-step/flow layer so tests and the `Full*Tests` workflows stop recomposing low-level actions inline. `[Impact: High | Effort: High]`
8. Split `BasePage` by responsibility and delete its 24 unused public methods in the process. `[Impact: High | Effort: High]`
9. Delete the 4 zero-reference utility classes and the remaining unused `BasePage` methods; fix or remove `compareElementText`'s false-positive-on-failure behavior. `[Impact: Medium | Effort: Low]`
10. Narrow `isElementPresentNow`'s caught exception type and back it with a real wait/retry instead of a single instant check. `[Impact: Medium | Effort: Low]`
11. Fix the `RetryListener` wiring (`retryAnalyzer` on `@Test` or a proper `IAnnotationTransformer`) and have it read the `retryCount` parameter instead of hardcoding it. `[Impact: Medium | Effort: Low]`
12. Remove the static-field order dependency between tests in `CreateOrderTests` and `RegisterUserTests`. `[Impact: Medium | Effort: Low]`
13. Add missing assertions to the 6 assertion-free tests and replace the tautological assertion in `FullProductLifecycleTests`. `[Impact: Medium | Effort: Low]`
14. Replace the `ext-comp-*` and positional-XPath locators with the stable `By.id`/`By.name` pattern already used by sibling classes/fields. `[Impact: Medium | Effort: Medium]`
15. Wire up `ScreenshotUtil` on failure and publish a structured HTML/Allure report from CI instead of catting raw Surefire text. `[Impact: Medium | Effort: Medium]`
16. Remove the `com.acme.crm.wip` package from the `testng.xml` suite run. `[Impact: Low | Effort: Low]`
17. Add a `.gitignore` covering `target/`. `[Impact: Low | Effort: Low]`
18. Rename `OrderHandler`/`UserManagement` to follow the dominant `*Page` suffix convention. `[Impact: Low | Effort: Low]`
19. Add TestNG group tagging and split CI into a fast PR subset plus a full merge/nightly run. `[Impact: Low | Effort: Medium]`

## Checklist tab input

| Section | Check | Status (+/-) | Comments |
|---|---|---|---|
| Framework | Framework follows a layered architecture | - | 27 raw `driver.findElement` calls in 4 test classes bypass page objects; no business-step layer exists (see findings #3, #7). |
| Framework | Framework complies with DRY | - | 4 near-identical `*ModifyPage` classes (`InvoiceModifyPage.java:22-27` etc.); no test-data builder/factory anywhere. |
| Framework | Framework complies with KISS | - | `BasePage.java` is a 232-line God Class bundling 8+ unrelated responsibilities. |
| Framework | Framework complies with YAGNI | - | 24 of 32 `BasePage` public methods and 4 whole utility classes (`DbConnector`, `EmailSenderUtil`, `ScreenshotUtil`, `DateFormatterUtil`) have 0 references anywhere. |
| Framework | Framework complies with SOLID | - | SRP: God Base Class (`BasePage.java`); AssertionError thrown from domain logic duplicated across 4 sibling page objects. |
| Framework | Framework complies with language standards | + | Minor drift only: 2 of 11 page objects (`OrderHandler`, `UserManagement`) don't follow the dominant `*Page` suffix. |
| Framework | Unconditional waits are not a common practice | - | 38 `Thread.sleep` calls across 10 files; the class's own `WebDriverWait` helpers are unused. |
| Framework | Tests are atomic and independent | - | `CreateOrderTests.java:20` and `RegisterUserTests.java:20` share static state read across `@Test(priority=N)` boundaries. |
| Framework | Core libraries/framework/language versions are reasonably current | - | Selenium 3.141.59 and TestNG 6.14.3 (`pom.xml:16-17`), both multi-year-old pins, missing modern wait/locator capabilities relevant to the `Thread.sleep` finding. |
| Framework | No hardcoded credentials/secrets in the test codebase | - | `config.properties:4,9` and `DbConnector.java:15-17` store plaintext admin/DB passwords; never loaded via any config layer. |
| Running | Steps have a sufficient level of documentation for reporting | - | `Full*Tests` narrative exists only as Java comments (`// --- feature N: ... ---`), which never appear in a TestNG/Surefire report; no business-step layer or `@DisplayName` use. |
| Running | When tests fail, there are mechanisms to easily find the cause | - | `ScreenshotUtil.capture` has 0 callers; CI's only diagnostic step is `cat target/surefire-reports/*.txt` (`ci.yml:24-26`). |
| Running | Test stability is at a sufficient level | - | 38 `Thread.sleep` calls and a declared `retryCount=3` (`testng.xml:8`) signal known instability, but the retry listener is misregistered and does not actually run. |
| Running | There is a way to track run results over time | - | No HTML/Allure report is published; CI only dumps raw Surefire text (`ci.yml:24-26`). |
| Running | Tests are integrated into CI/CD, not run purely manually/on-demand | + | `.github/workflows/ci.yml` runs `mvn clean test` on every push and PR to all branches. |
| Processes | Tests are properly documented | - | Test method names are consistent, but business intent beyond that exists only in source comments, not in any report-visible form (see business-step-layer finding). |
| Processes | A failure-handling strategy is implemented (bug reporting → flaky rerun → failure skipping) | - | `RetryListener` is registered incorrectly via `testng.xml`'s `<listeners>` and never actually retries; no skip-with-reason or ticket-link mechanism exists anywhere. |