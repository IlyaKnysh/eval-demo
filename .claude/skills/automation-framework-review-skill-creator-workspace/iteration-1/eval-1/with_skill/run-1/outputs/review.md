# Automation Framework Issues

**Scope:** `evals/fixtures/messy-framework` — a Java 8 / Selenium 3.141.59 / TestNG 6.14.3 UI automation suite for the Acme CRM admin console (users, orders, products, invoices). 27 Java files, 1,729 lines total: 11 page objects + `BasePage` (`src/main/java/com/acme/crm/pages`), 5 utility classes (`src/main/java/com/acme/crm/utils`), 9 test classes across `src/test/java/com/acme/crm/tests` (7 files) and `src/test/java/com/acme/crm/wip` (2 files), plus `pom.xml`, `testng.xml`, `.github/workflows/ci.yml`, `README.md`, `src/test/resources/config.properties`. All files were read in full; every mandatory grep below was run repo-wide.

**Excluded from this review:** nothing — no exclusions were requested.

**Verdict up front:** The suite has no business-step/flow layer, so every multi-feature workflow test hand-composes the same low-level domain calls inline, and that absence directly explains two of the largest findings below (duplication and unreadability). Four page objects (`InvoiceModifyPage`, `OrderModifyPage`, `ProductModifyPage`, `UserModifyPage`) are near-identical copies of each other. `BasePage` is a 231-line God Base Class mixing navigation, waiting, raw-type leakage, popup handling, assertions, CSV/log file I/O, and JS hacks, and every page object inherits all of it regardless of relevance. Synchronization relies almost entirely on `Thread.sleep` (38 hits across 10 files) instead of explicit waits, four tests reach past page objects straight into raw Selenium (`driver.findElement`), a scratch/WIP package with a non-asserting draft test and a duplicate-click debug test ships in the same CI run as real tests, and `src/test/resources/config.properties` commits a live-looking production DB host/credentials and admin password in plaintext that is also never actually read by any code path.

---

## Missing business-step/flow layer

[Impact: High | Effort: High]

There is no `steps/`/`flows`/keyword-driven package anywhere in the repo (`find`/directory listing confirms only `pages` and `utils` under `src/main/java`). Every multi-feature workflow test re-composes the same business actions from raw page-object calls inline instead of calling a reusable step like `registerUser(...)` or `createOrderFor(user)`:

- `FullAdminWorkflowTests.testFullAdminWorkflowEndToEnd` (`src/test/java/com/acme/crm/tests/FullAdminWorkflowTests.java:21-164`) composes login → register user → modify user → create order → modify order → logout as one 143-line method, recomposing the same user-registration and order-creation call sequences already duplicated in `RegisterUserTests.java` and `CreateOrderTests.java`.
- `FullInvoiceBillingCycleTests.testFullInvoiceBillingCycleEndToEnd` (`src/test/java/com/acme/crm/tests/FullInvoiceBillingCycleTests.java:21-163`) and `FullProductLifecycleTests.testFullProductLifecycleEndToEnd` (`src/test/java/com/acme/crm/tests/FullProductLifecycleTests.java:21-162`) each independently re-derive the "create order" business action instead of sharing one.

This single missing abstraction is the root cause behind both the cross-file DRY duplication (below) and the business-readability failures (below) — a dedicated step layer (e.g. `AdminWorkflowSteps.registerAndModifyUser(...)`) would collapse both at once, which is why it is called out as its own finding rather than folded into either.

## God Base Class: `BasePage`

[Impact: High | Effort: High]

`src/main/java/com/acme/crm/pages/BasePage.java` is 231 lines and every one of the 11 page objects extends it. It bundles at least seven unrelated responsibilities in one class: navigation (`navigateTo`, `refreshPage`, `goBack`, lines 32-51), waiting (`waitUntilDisplayed`, `waitUntilClickable`, `isElementPresentNow`, lines 55-75), raw element access that leaks the underlying Selenium types (`getRawElement`/`getRawElements` returning `WebElement`/`List<WebElement>`, lines 79-85), ad hoc `Thread.sleep` hacks (`waitForPageLoadHack`, `waitForAjaxSpinnerHack`, lines 103-115), popup/modal handling (lines 119-143), assertions bundled into the page layer (`assertTextPresent`, `assertElementVisible`, `assertUrlContains`, `compareElementText`, lines 147-172), log/CSV file I/O (`log`, `writeResultToCsv`, lines 176-192), and misc JS/driver utilities (`scrollToElement`, `highlightElement`, `switchToFrame`, `isPageLoaded`, `selectDropdownByVisibleText`, `hoverOver`, lines 196-230). Every page object — including trivial ones like `DashboardPage` (31 lines, uses 3 of these) and `LoginPage` (39 lines, uses 2 of these) — inherits the entire surface, which is also an ISP violation distinct from the SRP framing: thin page objects are forced to carry CSV-writing, JS-highlighting, and frame-switching capabilities they never use. Composition via a driver/wait/log helper object would resolve both the SRP and ISP angles at once.

## Page objects assert/verify internally (POM smell)

[Impact: Medium | Effort: Medium]

`verifyFieldIsEditableAndEnabled()` is declared identically in all four `*ModifyPage` classes (`InvoiceModifyPage.java:22-27`, `OrderModifyPage.java:22-27`, `ProductModifyPage.java:22-27`, `UserModifyPage.java:22-27`) and throws `new AssertionError(...)` directly from inside the page object rather than returning state for the test to assert on. `BasePage` itself also bundles assertion methods (`assertTextPresent`, `assertElementVisible`, `assertUrlContains`, `BasePage.java:147-158`) that every page object inherits. This is a specific, common POM correctness smell distinct from the general God Base Class/SRP finding above: the domain layer is making pass/fail verdicts instead of just reporting state, which means a test calling `verifyFieldIsEditableAndEnabled()` cannot distinguish "this failed because the field wasn't editable" from any other failure mode in its own assertion output, and the page object's responsibility (model the page) is mixed with the test's responsibility (judge the outcome).

## Naming-convention outliers in page-object and test-class roles

[Impact: Low | Effort: Low]

No formal naming standard exists in the repo — no Checkstyle/PMD/Spotless config, no `.editorconfig`, no CONTRIBUTING.md/style guide — so this is judged against the convention the codebase's own majority already establishes (language-idiomatic Java defaults plus the suite's own de facto per-role suffix). 9 of 11 page objects follow a `*Page` suffix convention; 2 outliers break it: `OrderHandler` (`src/main/java/com/acme/crm/pages/OrderHandler.java`) and `UserManagement` (`src/main/java/com/acme/crm/pages/UserManagement.java`) — both are grid/list-screen page objects functionally equivalent in role to the `*Page` classes but named differently, which also makes them easy to miss when grepping the directory by suffix. Separately, 7 of 9 test classes follow a `*Tests` suffix; the 2 outliers are exactly the two WIP/scratch files (`DebugOrderExportTest.java`, `ScratchLoginExperimentTest.java`, singular `*Test`), which here is more symptomatic of their scratch status (see "Scratch/WIP code ships in CI" finding above) than an independent naming defect — `testng.xml` scans by package rather than Surefire's file-pattern, so this naming drift does not itself cause a discovery miss the way a file-pattern mismatch would in a Surefire-include-driven setup.

## Raw-type leakage: `BasePage.getRawElement`/`getRawElements`

[Impact: Medium | Effort: Medium]

`BasePage.getRawElement(By locator)` and `getRawElements(By locator)` (`src/main/java/com/acme/crm/pages/BasePage.java:79-85`) return `WebElement`/`List<WebElement>` directly from a public page-object method instead of a typed wrapper or primitive, and `OrderHandler.getAllOrderRows()` (`src/main/java/com/acme/crm/pages/OrderHandler.java:35-37`) and `UserManagement.getFirstResultRow()` (`src/main/java/com/acme/crm/pages/UserManagement.java:28-30`) do the same at the domain-object level. Callers in test code receive raw Selenium objects they can call arbitrary WebDriver API on (see layer-boundary finding below), defeating the purpose of a typed domain layer.

## Tests reach past the domain layer into raw Selenium

[Impact: High | Effort: Medium]

9 of 9 test files import `org.openqa.selenium.*` directly (`grep -rl "import org.openqa.selenium" src/test/java/com/acme/crm/tests/ src/test/java/com/acme/crm/wip/` → 9/9 files), and 4 of those files go further and call `driver.findElement`/`driver.findElements` directly in test code, bypassing page objects entirely (27 call sites total):

- `FullInvoiceBillingCycleTests.java:60,93,98,112,120,124,126` — locates and clicks invoice/order/toast elements via raw `By.xpath`/`By.cssSelector` instead of through `InvoiceModifyPage`.
- `FullProductLifecycleTests.java:40,49,51,53,55,57,93,98,100,108,113,124,126` — creates and searches products entirely via raw `driver.findElement` calls (there is no `ProductCreatePage`; the test fabricates the form interaction inline).
- `InvoiceLookupTests.java:45,53` and `ProductGridTests.java:28,31,38,49,51` — same pattern for invoice/product grid lookups.

This is a direct layer-boundary violation: the domain layer exists but roughly half the test suite routes around it, which also means any locator change to these screens requires editing test files instead of one page object.

## Cross-file DRY: four near-identical `*ModifyPage` classes

[Impact: High | Effort: Medium]

`InvoiceModifyPage`, `OrderModifyPage`, `ProductModifyPage`, and `UserModifyPage` (`src/main/java/com/acme/crm/pages/{Invoice,Order,Product,User}ModifyPage.java`, 50 lines each) each declare the same 6 methods with near-identical bodies, differing only in the field/locator and an error-message string: `verifyFieldIsEditableAndEnabled()` (lines 22-27 in each), `enterName(String)` (lines 29-33), `selectStatus(String)` (lines 35-37), `enterEmail(String)` (lines 39-41), `clickSave()` (lines 43-45), `toggleActive()` (lines 47-49). This is a distinct finding from the `BasePage` God Base Class above — it is duplication *across four sibling files*, not inside one shared class, and fixing the base class does not collapse it. A generic `EditableRecordModifyPage` (or a shared composition helper parameterized by locator set) would collapse all four into one implementation plus four locator declarations.

## Missing domain-concept representation for the authenticated user/credentials

[Impact: Medium | Effort: Medium]

There is no typed `User`/`Role`/credentials object. The admin credential pair is hardcoded as a literal string pair in `LoginPage.loginAsAdmin()` (`src/main/java/com/acme/crm/pages/LoginPage.java:32-33`, `"admin@acmecorp.com"`/`"Admin123!"`), and separately re-typed as literals in 5 test files' calls to `loginPage.login("admin@acmecorp.com", "Admin123!")` (`FullAdminWorkflowTests.java:35,123`, `FullInvoiceBillingCycleTests.java:31`, `FullProductLifecycleTests.java:31`, and again in `ScratchLoginExperimentTest.java:19`), while `DbConnector` (`src/main/java/com/acme/crm/utils/DbConnector.java:16-17`) and `config.properties` (`src/test/resources/config.properties:4,9`) each separately hardcode a *different* credential pair (DB service account, admin password) for conceptually the same "who is this test running as" question. No single typed entry point exists; each file re-expresses the concept independently.

## No test-data builder/factory — inline literal argument lists repeated per test

[Impact: Medium | Effort: Low]

`grep -rl "Builder\|Factory"` across the whole repo returns zero files. Test data is constructed as long positional-parameter inline literal lists repeated per test method: `CreateOrderTests.createOrderInline(...)` (`src/test/java/com/acme/crm/tests/CreateOrderTests.java:88-102`, 11 positional `String` parameters, explicitly commented "helper that just packs args into calls - not a real builder/factory") and `RegisterUserTests.registerInline(...)` (`src/test/java/com/acme/crm/tests/RegisterUserTests.java:81-95`, 10 positional `String` parameters) both reimplement the same pattern independently with no shared builder.

## Hardcoded production credentials committed in plaintext

[Impact: High | Effort: Low]

`src/test/resources/config.properties:4-9` commits a live-looking production endpoint and two credential pairs in plaintext: `adminPassword=Admin123!`, `dbHost=prod-crm-db.acmecorp.internal`, `dbUser=crm_svc`, `dbPassword=Sup3rSecret!` against `dbName=crm_production`. The identical DB credential pair is independently hardcoded again as Java string literals in `DbConnector.java:16-17` (`URL`/`USER`/`PASSWORD` constants pointing at the same `prod-crm-db.acmecorp.internal`/`crm_production`). Separately, `config.properties` itself is never read by any code path in the repo (`grep -rn "getProperty\|new Properties"` finds only an unrelated SMTP `Properties` object in `EmailSenderUtil.java:17`, not a reader of this file) — the committed secrets are dead weight as well as a live exposure risk, and the `dbHost`/`dbName` naming strongly suggests this is a production system, not a sandboxed test environment (see also the no-environment-switching finding below).

## SQL built by string concatenation (injection risk) in `DbConnector`

[Impact: Medium | Effort: Low]

`DbConnector.getOrderCountForCustomer(String customerEmail)` (`src/main/java/com/acme/crm/utils/DbConnector.java:30-40`) builds its query via direct string concatenation — `"SELECT COUNT(*) FROM orders WHERE customer_email = '" + customerEmail + "'"` — instead of a parameterized `PreparedStatement`. `DbConnector` has zero call sites anywhere in the repo (confirmed by `grep -rn "DbConnector"` outside its own file), so this is not currently exercised, but it is a real defect in checked-in code that would need fixing before any future caller relies on it with untrusted input.

## Unconditional sleeps used as the primary synchronization strategy

[Impact: High | Effort: High]

`grep -rn "Thread.sleep"` across the repo returns 38 hits across 10 files (`BasePage.java`, `DashboardPage.java`, `LoginPage.java`, `OrderCreatePage.java`, `OrderHandler.java`, `UserRegisterPage.java`, `FullAdminWorkflowTests.java`, `FullInvoiceBillingCycleTests.java`, `FullProductLifecycleTests.java`, `ProductGridTests.java`), with durations ranging from 800ms to 4000ms. Two of these are explicitly named hacks in the base class itself: `waitForPageLoadHack()` and `waitForAjaxSpinnerHack()` (`BasePage.java:103-115`). `BasePage` does separately provide real explicit waits (`waitUntilDisplayed`, `waitUntilClickable`, `BasePage.java:55-63`), but no page object or test actually calls them (zero call sites found for either method outside their own declarations) — the explicit-wait mechanism exists but is unused in favor of sleeps everywhere. Selenium 3.141.59 (pinned in `pom.xml:16`) also predates Selenium 4's richer relative-locator and auto-wait support, which compounds this (see Dependency currency below).

## Raw, non-retrying presence checks coexisting with the real wait mechanism

[Impact: Medium | Effort: Low]

Independent of the sleep-based waiting above: `BasePage.isElementPresentNow(By locator)` (`BasePage.java:69-75`) wraps a single non-retrying `driver.findElement(locator).isDisplayed()` in a try/catch and returns `false` immediately on any exception — no polling, no retry. It is used as the *only* success/failure signal in `LoginPage.isErrorBannerShown()` (`LoginPage.java:27-30`, comment at line 28 explicitly says "raw non-retrying instant check, no wait"), `DashboardPage.isWelcomeBannerVisible()` (`DashboardPage.java:24-26`), and `UserRegisterPage.isSuccessMessageShown()` (`UserRegisterPage.java:68-70`) — all three are asserted on directly in test code (e.g. `FullAdminWorkflowTests.java:36,43,57,120,130`). Each of these checks will instant-fail a real test the moment the page needs one more render tick, which is a distinct, separately-reportable flakiness bug from the sleep-based waiting above — it is a correctness gap in the wait mechanism itself, not merely "sleeps instead of waits."

## Hardcoded auto-generated ExtJS IDs and positional XPath locators

[Impact: Medium | Effort: Medium]

Locator distribution across page objects and tests (`grep -c`): `By.id` 24, `By.cssSelector` 37, `By.xpath` 12, `By.name` 11. Within that: 9 locators hardcode an auto-generated `ext-comp-NNNN` ID that encodes container-build-order rather than any stable semantic (`DashboardPage.java:9`, `InvoiceModifyPage.java:13`, `OrderCreatePage.java:10`, `OrderHandler.java:15`, `OrderModifyPage.java:13`, `ProductModifyPage.java:13`, `UserModifyPage.java:13`, `UserRegisterPage.java:12-13`) — these will break on any ExtJS component re-render that changes build order, independent of any markup change a developer intends. Separately, 8 locators use pure positional XPath (`//div[2]/div[1]/form/div[1]/input` style) with no semantic anchor (`DashboardPage.java:8`, `OrderCreatePage.java:8-9`, `OrderModifyPage.java:12`, `UserManagement.java:12`, `UserModifyPage.java:12`, `UserRegisterPage.java:8-9`), plus 4 more of the same positional-XPath pattern duplicated directly in test code where there's no page object at all (`FullInvoiceBillingCycleTests.java:60`, `FullProductLifecycleTests.java:108`, `InvoiceLookupTests.java:45`, `ProductGridTests.java:38`) — a table-row lookup pattern reinvented ad hoc per call site rather than one centralized, reusable "find grid row containing X" helper.

## Business-readability: workflow tests read as UI action logs, not business scenarios

[Impact: High | Effort: Medium]

`FullAdminWorkflowTests.testFullAdminWorkflowEndToEnd`, `FullInvoiceBillingCycleTests.testFullInvoiceBillingCycleEndToEnd`, and `FullProductLifecycleTests.testFullProductLifecycleEndToEnd` are each explicitly step-based/procedural (comment-delimited `// --- feature N: ... ---` blocks), which is a legitimate paradigm for long E2E workflows and not itself an AAA violation. But within that paradigm there is no business-vocabulary layer: business intent is only inferable from inline comments and low-level call sequences (`userRegisterPage.enterFirstName("Grace"); ...enterZip("89501"); submitRegistration();`, `FullAdminWorkflowTests.java:47-57`), there is no `@DisplayName`/`@Story`/business-named step method, and literal test data (`"Grace Kim-Anderson"`, `"89501"`) is inlined rather than expressed through named constants or a builder. This is independent of the missing-step-layer finding above in cause (that finding is about code reuse; this one is about readability) even though both would be improved by the same fix.

## Test independence: static mutable state shared across tests

[Impact: Medium | Effort: Low]

`CreateOrderTests.orderIdFromFirstTest` (`src/test/java/com/acme/crm/tests/CreateOrderTests.java:20`) is set by `testCreateStandardOrder` (priority 1) and read by `testReuseOrderIdFromEarlierTest` (priority 5, line 82), and `RegisterUserTests.lastRegisteredEmail` (`src/test/java/com/acme/crm/tests/RegisterUserTests.java:20`) is set by `testRegisterSalesUser` (priority 1) and asserted by `testDependsOnPreviouslyRegisteredEmail` (priority 5, line 77). Both are real inter-test order dependencies (test B depends on test A having already run), relying on `priority` to enforce ordering rather than making each test independently runnable.

## Parallelization safety cannot be assessed — not configured, but the shared `static` state above would collide if it were

[Impact: Medium | Effort: Low]

`pom.xml`'s Surefire configuration (`pom.xml:38-47`) sets no `parallel`/thread-count attribute, and `testng.xml` sets no `parallel` attribute on `<suite>` — the suite is not currently configured to run in parallel, so this is `N/A` as an active defect. It is flagged here because the static mutable fields above (`orderIdFromFirstTest`, `lastRegisteredEmail`) would collide across workers the moment parallel execution is turned on, which is worth knowing before anyone flips that switch for CI speed.

## Scratch/WIP code ships in the same CI run as real tests

[Impact: High | Effort: Low]

`src/test/java/com/acme/crm/wip/` contains two draft files, and `testng.xml:11-13` scans both `com.acme.crm.tests` and `com.acme.crm.wip` packages — there is no exclusion, so both run on every `mvn test` and in CI (`.github/workflows/ci.yml:17`, "Run full TestNG suite").
- `ScratchLoginExperimentTest.tryLoginWithWeirdCharsInPassword()` (`src/test/java/com/acme/crm/wip/ScratchLoginExperimentTest.java:13-22`) contains zero `Assert` calls — it logs `"did it work? who knows"` (line 20) and passes regardless of outcome. The class comment itself reads `"TODO: delete this or move it somewhere real - Dave, 2024"` (line 9).
- `DebugOrderExportTest.debugExportTimingIssue()` (`src/test/java/com/acme/crm/wip/DebugOrderExportTest.java:14-26`) also has zero assertions and is explicitly commented `"debugging flaky export button, remove before merge"` (line 22) while calling `orderHandler.clickExport()` twice in a row with no apparent justification in the test logic — a literal leftover debug artifact, not a duplicate of a finished real test (no equivalent "export twice" test exists elsewhere).

## Assertion-free tests (FIRST: Self-validating failure)

[Impact: Medium | Effort: Low]

3 of 9 test files/test-bearing classes contain at least one `@Test` method with zero `Assert.*` calls in its body: `ProductGridTests.testSortProductGridByPrice` and `testExpandProductDetailsPanel` (`src/test/java/com/acme/crm/tests/ProductGridTests.java:35-53`, call `.isDisplayed()`/`.click()` and discard the result without asserting), `DebugOrderExportTest.debugExportTimingIssue` (`wip/DebugOrderExportTest.java:14-26`), and `ScratchLoginExperimentTest.tryLoginWithWeirdCharsInPassword` (`wip/ScratchLoginExperimentTest.java:13-22`). These tests can execute their full action sequence against a broken UI and still report green.

## No test categorization/tagging and no report-grouping annotations

[Impact: Medium | Effort: Medium]

`grep -rn "@Tag|@DisplayName|@Feature|@Story|@Epic|smoke|regression|Allure|TmsLink|@Issue"` across all Java and XML files returns zero hits. There is no smoke/regression/full-suite distinction anywhere, `testng.xml` defines a single `<test name="AllTests">` that runs every package unconditionally (`testng.xml:10-15`), and `.github/workflows/ci.yml` runs `mvn -B clean test` on every push and PR to every branch (`ci.yml:4-6,17`) with no fast-subset-on-PR / full-suite-on-merge distinction. This also means there is no mechanism to group a failure report by feature area in a growing suite, and no ticket-link/skip-with-reason annotation to distinguish a known, already-filed failure from a genuinely new one.

## Failure diagnostics: no screenshot/trace/video capture is ever invoked; report is raw console text only

[Impact: Medium | Effort: Medium]

`ScreenshotUtil.capture(WebDriver, String)` (`src/main/java/com/acme/crm/utils/ScreenshotUtil.java:16-23`) exists but has zero call sites anywhere in the repo outside its own declaration (`grep -rn "ScreenshotUtil"` confirms this) — it is dead code, never wired into a listener or `@AfterMethod`. There is no `ITestListener`/`@Listeners` registration anywhere except `RetryListener` (`testng.xml:5`), so no screenshot-on-failure, no trace, no video capture ever runs. CI's own diagnostic step is `cat target/surefire-reports/*.txt` (`.github/workflows/ci.yml:19-21`) — a bare console dump, not a published HTML/Allure report — so diagnosing a CI failure requires reading raw Surefire text output with no visual artifact and no structured, browsable report.

## Retry policy masks flakiness suite-wide with no quarantine mechanism

[Impact: Medium | Effort: Low]

`testng.xml:8` sets `<parameter name="retryCount" value="3" />`, consumed by `RetryListener` (`src/main/java/com/acme/crm/utils/RetryListener.java:10-23`), which retries any failing test up to 3 times before reporting failure, suite-wide, with no per-test opt-out and no tracking of which tests actually needed a retry to pass. Combined with the "no report-grouping/known-issue annotation" finding above, a green CI run on this suite could be masking a test that failed twice and passed on attempt three, with no visibility into that happening.

## Dead utility classes (zero callers across the whole repo)

[Impact: Low | Effort: Low]

Repo-wide grep for each class name outside its own file returns 0 references for: `ScreenshotUtil` (`src/main/java/com/acme/crm/utils/ScreenshotUtil.java`), `EmailSenderUtil` (`src/main/java/com/acme/crm/utils/EmailSenderUtil.java`), `DbConnector` (`src/main/java/com/acme/crm/utils/DbConnector.java`), and `DateFormatterUtil` (`src/main/java/com/acme/crm/utils/DateFormatterUtil.java`). All four are fully implemented, compiled utility classes with no call site anywhere in `src/main` or `src/test`.

## No environment-switching mechanism — single hardcoded endpoint throughout

[Impact: Medium | Effort: Medium]

Every test hardcodes the full `https://crm-admin.acmecorp.com/...` URL inline (e.g. `CreateOrderTests.java:28`, `FullAdminWorkflowTests.java:34,65,107,119,133,142,147`, and 8 more identical literals across other test files) rather than reading a base URL from `config.properties`'s own `baseUrl`/`apiUrl` keys (`config.properties:1-2`), which — per the dead-config finding above — are never read by any code. There is no profile/`.env`/CLI-flag mechanism to point the same suite at a different environment without editing every test file, and the one config file that models environment values is wired to nothing.

## No `.gitignore`

[Impact: Low | Effort: Low]

The repo root has no `.gitignore` file at all (directory listing of repo root confirms only `.github/`, `README.md`, `pom.xml`, `src/`, `testng.xml`). No generated-output artifacts (`target/`, screenshots, reports) are currently committed, so there is no existing bloat, but there is also no guard against someone's local `target/` or `target/screenshots/` (the path `ScreenshotUtil.java:19` would write to, if it were ever called) being committed by accident.

## Build-file: Selenium version pinned via a correctly-wired property

[Impact: Low | Effort: Low]

One targeted read of `pom.xml`'s property block (`pom.xml:12-18`) found the version properties correctly wired — `${selenium.version}` (3.141.59) and `${testng.version}` (6.14.3) both resolve to versions that exist and match their artifact names. No misnamed/miswired version property was found. (Noted briefly per the skill's build-correctness check; not a finding, included only because the check was performed.)

## FIRST principles table

| Letter | Verdict | Evidence |
|---|---|---|
| **F**ast | Fails | 38 `Thread.sleep` calls (800ms-4000ms) across 10 files add unconditional delay on top of real page-render time; see "Unconditional sleeps" finding above. |
| **I**ndependent | Fails | `CreateOrderTests.orderIdFromFirstTest` and `RegisterUserTests.lastRegisteredEmail` create explicit inter-test order dependencies enforced only by `priority`; see "Test independence" finding above. |
| **R**epeatable | Passes | No hardcoded dates/timestamps found in assertions (`DateFormatterUtil` generates dynamic timestamps, unused elsewhere); test data uses realistic but non-environment-coupled literal names. No repeatability-breaking literal was found. |
| **S**elf-validating | Fails | 3 of 9 test-bearing files contain at least one assertion-free `@Test` method (`ProductGridTests` x2, `DebugOrderExportTest`, `ScratchLoginExperimentTest`); see "Assertion-free tests" finding above. |
| **T**imely | N/A statically | No tagging/fast-subset mechanism exists to evaluate turnaround against (see "No test categorization" finding); cannot be assessed from static code alone. |

## Recommended actions, in priority order

1. **Introduce a business-step/flow layer** (`steps/` package) between page objects and tests — `[Impact: High | Effort: High]`. Highest leverage: collapses both the cross-workflow-test duplication and the business-readability gap at once.
2. **Replace `Thread.sleep` with the already-present explicit-wait methods** (`waitUntilDisplayed`/`waitUntilClickable`) everywhere, and wire them into one centralized driver/domain wait helper — `[Impact: High | Effort: High]`. Single biggest flakiness and runtime-cost source in the suite.
3. **Remove the `com.acme.crm.wip` package from `testng.xml`'s scanned packages**, or delete/finish the two draft tests it contains — `[Impact: High | Effort: Low]`. High-impact (assertion-free tests silently pass in every CI run) for a one-line config fix.
4. **Rotate the committed production credentials in `config.properties` and `DbConnector.java`, and move them out of source control** — `[Impact: High | Effort: Low]`. Live-looking production secrets committed in plaintext; cheap to fix immediately regardless of the dead-config-reader question.
5. **Collapse the four `*ModifyPage` classes into one generic/parameterized implementation** — `[Impact: High | Effort: Medium]`.
6. **Pull the raw `driver.findElement` calls out of the 4 test files that bypass page objects**, and build the missing `ProductCreatePage`/invoice-row-lookup page objects they're standing in for — `[Impact: High | Effort: Medium]`.
7. **Fix the raw non-retrying presence checks** (`isElementPresentNow` call sites in `LoginPage`, `DashboardPage`, `UserRegisterPage`) to use the existing explicit-wait methods instead — `[Impact: Medium | Effort: Low]`.
8. **Wire `ScreenshotUtil.capture` into an `ITestListener`'s `onTestFailure`** so failure diagnostics stop depending on re-running locally — `[Impact: Medium | Effort: Medium]`.
9. **Add a smoke/regression tagging convention** (`@Test(groups=...)`) and split CI into a fast PR subset vs. full nightly run — `[Impact: Medium | Effort: Medium]`.
10. **Replace hardcoded `ext-comp-NNNN` IDs and positional XPath locators** with semantic/attribute-based selectors where the underlying markup supports it — `[Impact: Medium | Effort: Medium]`.
11. **Introduce a test-data builder** to replace the two independent `*Inline(...)` positional-parameter helpers — `[Impact: Medium | Effort: Low]`.
12. **Add real `@AfterMethod`/`@AfterClass` cleanup of created test entities** (orders, users, products, invoices), not just `driver.quit()` — `[Impact: Medium | Effort: Medium]`.
13. **Wire `config.properties`'s `baseUrl`/`apiUrl` into an actual environment-switching mechanism**, or delete it if it's genuinely unused — `[Impact: Medium | Effort: Medium]`.
14. **Delete the four dead utility classes** (`ScreenshotUtil` only after wiring it in per #8; `EmailSenderUtil`, `DbConnector`, `DateFormatterUtil` if truly unneeded) or document why they're intentionally kept for future use — `[Impact: Low | Effort: Low]`.
15. **Add a `.gitignore`** covering `target/`, screenshots, and report output before any of that gets generated and committed by accident — `[Impact: Low | Effort: Low]`.
16. **Upgrade Selenium past 3.141.59** to unlock relative locators and modern auto-waiting, which would make several of the above fixes cheaper — `[Impact: Low | Effort: High]`.
17. **Move the internal assertions out of the four `*ModifyPage` classes** (and out of `BasePage`) so page objects report state and tests make the verdict — `[Impact: Medium | Effort: Medium]`.
18. **Rename `OrderHandler`→`OrderGridPage` and `UserManagement`→`UserGridPage`** (or equivalent) to match the suite's own `*Page` convention — `[Impact: Low | Effort: Low]`.
