# Test Automation Framework Review: `crm-admin-ui-tests`

**Repository reviewed:** `.claude/skills/automation-framework-review-skill-creator/evals/fixtures/messy-framework`
**Stack:** Java 8, Selenium 3.141.59, TestNG 6.14.3, Maven Surefire 2.22.2, GitHub Actions
**Scope:** Every file in the repo was read: 11 page objects, 6 utilities, 9 test classes, `pom.xml`, `testng.xml`, `config.properties`, `ci.yml`, `README.md` (about 1,860 lines).
**Review date:** 2026-10-09
**Method:** Static review only. The suite was not compiled or run, because it points at production systems (see C4).

---

## 1. Executive summary

The framework is in poor shape and is not safe to run as it stands. Five problems block everything else:

1. **It probably does not build.** `EmailSenderUtil` imports `javax.mail.*`, and `pom.xml` has no dependency that provides it. `mvn clean test` should fail in the compile phase.
2. **The suite probably cannot start.** `testng.xml` registers `RetryListener` as a `<listener>`, but that class only implements `IRetryAnalyzer`, which is not a TestNG listener type.
3. **Production secrets are committed.** The repo contains the admin UI password and the production DB password, in `config.properties` and hard-coded in Java.
4. **The tests target production.** The base URL is `crm-admin.acmecorp.com` and the DB is `crm_production`. The tests create users and orders, mark invoices paid, send billing emails and archive records. CI runs on every push to every branch.
5. **Passing tests prove little.** Many tests have no assertions or always-true assertions. Several end-to-end tests claim in comments to verify behaviour they never check.

Beyond these, the framework has the usual signs of an unmaintained Selenium suite:
- 38 `Thread.sleep` calls and 36 empty `catch` blocks that swallow `InterruptedException`.
- 12 positional XPaths and 9 auto-generated ExtJS ids (`ext-comp-NNNN`).
- No driver factory or base test class (9 separate `new ChromeDriver()` calls).
- A config file that nothing reads.
- Tests that depend on each other through static fields.
- A "god" `BasePage`.
- Four copy-pasted `*ModifyPage` classes.
- WIP and debug tests included in the CI suite.

**Overall maturity: Low (roughly 1 on a 1-5 scale).** It has a page-object structure, a Maven build and a CI job, but the fundamentals of safety, reliability and test validity are missing.

### Severity counts

| Severity | Count |
|---|---|
| Critical | 5 |
| High | 12 |
| Medium | 10 |
| Low | 9 |
| **Total** | **36** |

---

## 2. What is done reasonably well

- A page-object layer exists (`src/main/java/com/acme/crm/pages`). Locators are `private final By` fields rather than strings scattered through the tests, at least in the page classes.
- Some locators are semantic and stable: `LoginPage` uses `By.id("username")`, `By.id("password")` and `By.id("loginSubmit")`. Several fields use `By.name(...)`.
- Driver cleanup is attempted. Class-level tests use `@AfterClass` with a null check, and the `Full*Tests` classes wrap their work in `try/finally { driver.quit(); }`.
- The project uses a standard Maven layout and a single suite file, has a CI workflow, and has a README that describes the layout.

---

## 3. Full issues list

Each issue gives a severity, the evidence (file:line) and a recommendation. File paths are relative to the framework root.

### Critical

#### C1. Main source does not compile: missing `javax.mail` dependency
- **Evidence:** `src/main/java/com/acme/crm/utils/EmailSenderUtil.java:4-9` imports `javax.mail.Message`, `Session`, `Transport`, `InternetAddress` and `MimeMessage`. `pom.xml:20-36` declares only `selenium-java`, `testng` and `mysql-connector-java`, and none of them supply JavaMail.
- **Impact:** `mvn clean test` (README and `ci.yml:22`) should fail in `compile`, so no tests run. `EmailSenderUtil` is not referenced anywhere (0 usages), so the build is broken by dead code.
- **Recommendation:** Delete `EmailSenderUtil`. If failure notifications are needed, use CI notifications or a reporting tool rather than SMTP calls from test code. If you keep it, add `com.sun.mail:jakarta.mail` (or `javax.mail`) explicitly.

#### C2. `RetryListener` is registered as a listener but is not a listener, and retries would hide flakiness anyway
- **Evidence:** `testng.xml:4-6` contains `<listener class-name="com.acme.crm.utils.RetryListener"/>`. `RetryListener.java:10` is declared `implements IRetryAnalyzer`. `IRetryAnalyzer` does not extend `ITestNGListener`, and TestNG 6.x rejects listener classes that are not `ITestNGListener` implementations when the suite starts.
- **Also:**
  - No `@Test(retryAnalyzer = ...)` or `IAnnotationTransformer` attaches the analyzer, so even if the suite started, nothing would retry (`grep retryAnalyzer` returns 0 hits).
  - The `retryCount` parameter in `testng.xml:8` is never read. `MAX_RETRY_COUNT = 3` is hard-coded at `RetryListener.java:13`.
  - The analyzer keeps per-instance mutable state (`retryCount`) with no reset.
- **Impact:** The suite likely aborts before any test runs. If it were wired correctly, a blanket 3x retry would hide the timing problems described in H3.
- **Recommendation:**
  - Remove the `<listener>` entry.
  - If you want retries, attach the analyzer through an `IAnnotationTransformer`, limit it to 1 retry, read the count from config, and report retried tests as flaky rather than passed.
  - Fix the timing problems first.

#### C3. Production credentials committed to source control
- **Evidence:**
  - `src/test/resources/config.properties:3-4` has `adminUsername=admin@acmecorp.com` and `adminPassword=Admin123!`.
  - `config.properties:5-9` has `dbHost=prod-crm-db.acmecorp.internal`, `dbName=crm_production`, `dbUser=crm_svc` and `dbPassword=Sup3rSecret!`.
  - `DbConnector.java:15-17` hard-codes the same production JDBC URL, user and password.
  - `LoginPage.java:33` hard-codes `login("admin@acmecorp.com", "Admin123!")`.
  - The same admin credentials are hard-coded at `FullAdminWorkflowTests.java:35,123`, `FullInvoiceBillingCycleTests.java:31` and `FullProductLifecycleTests.java:31`.
- **Impact:** Anyone with read access to the repo or its history has production admin and DB credentials.
- **Recommendation:**
  - Rotate both credentials now.
  - Remove them from the code and purge them from git history (`git filter-repo` or BFG).
  - Supply secrets through environment variables or CI secrets (`${{ secrets.* }}`) or a vault, and use a dedicated, low-privilege test account in a non-production environment.

#### C4. The suite runs destructive tests against production on every push
- **Evidence:**
  - Every URL is `https://crm-admin.acmecorp.com/...` (35 hard-coded occurrences in `src`), and `config.properties:1` points to the same host. The DB is `crm_production`.
  - Tests register users (`RegisterUserTests`), create orders (`CreateOrderTests`, `InvoiceLookupTests`), mark invoices paid and send billing emails (`FullInvoiceBillingCycleTests.java:83-121`), and archive invoices and products (`FullInvoiceBillingCycleTests.java:124-127`, `FullProductLifecycleTests.java:124-127`).
  - `ci.yml:3-7` triggers on `push` and `pull_request` for `branches: ["**"]`.
- **Impact:** Each CI run pollutes production data and may send real emails to real addresses. It can also archive real products, because `FullProductLifecycleTests.java:124` archives whatever `.product-row` comes first.
- **Recommendation:**
  - Stop CI runs against production immediately.
  - Introduce environment selection (`-Denv=qa`) with per-environment config.
  - Run against a dedicated QA or staging environment with seeded, disposable data, and add cleanup.

#### C5. `DbConnector`: SQL injection, leaked connections, silent failures
- **Evidence:**
  - `DbConnector.java:32` builds SQL by string concatenation: `"... WHERE customer_email = '" + customerEmail + "'"`.
  - `DbConnector.java:21-23` opens a `Connection` and `Statement` that are never closed and returns a live `ResultSet` to the caller.
  - It returns `null` (`:26`) or `-1` (`:39`) on failure, after printing to `System.err`.
- **Impact:** Combined with C3/C4, test code holds an injectable, leaking connection to the production DB. Failures turn into sentinel values that tests could easily mistake for real data.
- **Recommendation:**
  - Use `PreparedStatement` with try-with-resources, and map results to plain objects inside the helper.
  - Read connection settings from config.
  - Throw on failure.
  - Point it at a test DB with a read-only user.
  - The class currently has 0 usages, so deleting it is also reasonable.

### High

#### H1. No driver management: hard-coded `new ChromeDriver()` everywhere, no base test
- **Evidence:**
  - 9 occurrences of `new ChromeDriver()`: `CreateOrderTests.java:24`, `InvoiceLookupTests.java:24`, `ProductGridTests.java:19`, `RegisterUserTests.java:24`, `FullAdminWorkflowTests.java:23`, `FullInvoiceBillingCycleTests.java:22`, `FullProductLifecycleTests.java:22`, `DebugOrderExportTest.java:16`, `ScratchLoginExperimentTest.java:15`.
  - `browser=chrome` (`config.properties:10`) is never read. There is no `ChromeOptions` or headless mode.
  - Selenium 3 has no Selenium Manager, so a matching chromedriver must already be on PATH.
- **Impact:** You cannot switch browsers, run headless, run remotely (Grid/cloud) or run in parallel. On `ubuntu-latest`, Chrome without `--headless` has no display, so CI runs will likely fail. The setup and teardown code is duplicated in every class.
- **Recommendation:**
  - Add a `DriverFactory` that reads the browser, headless flag and remote URL from config and keeps drivers in a `ThreadLocal<WebDriver>`.
  - Add a `BaseTest` with `@BeforeMethod`/`@AfterMethod(alwaysRun = true)` lifecycle.
  - Upgrade to Selenium 4 so Selenium Manager handles drivers.

#### H2. Configuration is never loaded, and URLs and test data are hard-coded
- **Evidence:**
  - Nothing in `src` loads `config.properties`. A grep for `config.properties` returns 0 hits, and the only `Properties` usage is the SMTP setup in `EmailSenderUtil`.
  - URLs are hard-coded 35 times.
  - `implicitWaitSeconds=10` and `apiUrl` are never used.
  - `README.md:18` says "Configuration (URLs, credentials) lives in `src/test/resources/config.properties`", which is not true.
- **Impact:** You cannot change the environment without editing about 35 lines of Java, and the documentation misleads new contributors.
- **Recommendation:**
  - Add a typed `Config` class that loads `config-{env}.properties`, with system properties and environment variables taking precedence.
  - Build URLs from `baseUrl` plus a path, and expose navigation through page objects (`LoginPage.open()`).
  - Correct the README.

#### H3. Synchronization by `Thread.sleep`; available explicit waits are unused
- **Evidence:**
  - There are 38 `Thread.sleep` calls: 8 in page objects (`BasePage.java:105,112`, `DashboardPage.java:19`, `LoginPage.java:22,35`, `OrderCreatePage.java:63`, `OrderHandler.java:29`, `UserRegisterPage.java:63`) and 30 in tests (`FullAdminWorkflowTests` 9, `FullInvoiceBillingCycleTests` 10, `FullProductLifecycleTests` 10, `ProductGridTests` 1).
  - 36 of them sit in an empty `catch (InterruptedException e) {}`, which swallows the interrupt without restoring it.
  - `BasePage.waitUntilDisplayed` and `waitUntilClickable` (`BasePage.java:55-63`) have **0 call sites**.
  - There are methods literally named `waitForPageLoadHack` and `waitForAjaxSpinnerHack`.
  - A single login sleeps for a fixed 5 s: `LoginPage.login` 2 s, plus `loginAsAdmin` 1 s, plus 2 s in each Full test.
- **Impact:** The tests are both slow (well over 40 s of fixed sleeps per full run) and flaky, because the sleeps are never right for every environment or load.
- **Recommendation:**
  - Remove every `Thread.sleep`.
  - Wait inside page-object actions with `WebDriverWait` and `ExpectedConditions`: clickable before click, visible before read, and invisibility of spinners or toasts after submit.
  - Make the page-object "is shown" checks wait with a timeout (see H4b).

#### H4. Brittle locators: positional XPaths and auto-generated ids
- **Evidence:**
  - 12 positional XPaths:
    - `DashboardPage.java:8` `//div[1]/div[1]/nav/ul/li[3]/a`
    - `OrderCreatePage.java:8-9`
    - `OrderModifyPage.java:12` `//div[3]/div[2]/table/tbody/tr[6]/td[2]/input`
    - `UserManagement.java:12` `.../tr[2]/td[1]`, which hard-codes the second row as the "first result"
    - `UserModifyPage.java:12`
    - `UserRegisterPage.java:8-9`
    - in tests: `FullInvoiceBillingCycleTests.java:60`, `FullProductLifecycleTests.java:108`, `InvoiceLookupTests.java:45`, `ProductGridTests.java:38`
  - 9 ExtJS auto-generated ids (`ext-comp-1023`, `-1047`, `-1188`, `-2091`, `-3312`, `-4108`, `-4109`, `-5021`, `-5033`). These are regenerated on render and change whenever components are added.
  - `OrderCreatePage.customerNameField` and `UserRegisterPage.firstNameField` are the **identical** XPath `//div[2]/div[1]/form/div[1]/input`. That shows the locators describe layout, not meaning.
- **Impact:** Any layout change, or a new ExtJS component, breaks tests or makes them act on the wrong element without failing.
- **Recommendation:**
  - Agree with developers on `data-testid` (or `data-qa`) attributes.
  - Until those exist, prefer `id` or `name`, ARIA roles or labels, or text-anchored relative XPath. Never use ExtJS `ext-comp-*` ids.
  - Locate grid rows by content (for example, the row containing a given email), not by index.

#### H4b. "Instant" presence checks used as test oracles
- **Evidence:**
  - `BasePage.isElementPresentNow` (`BasePage.java:69-75`) does a single `findElement` with no wait and returns `false` on any exception. The Javadoc admits it is "used ... as a substitute for a real wait".
  - It backs `LoginPage.isErrorBannerShown` (`:27-30`), `DashboardPage.isWelcomeBannerVisible` (`:24-26`) and `UserRegisterPage.isSuccessMessageShown` (`:68-70`).
- **Impact:**
  - `Assert.assertFalse(loginPage.isErrorBannerShown())` (`FullAdminWorkflowTests.java:36`, `FullInvoiceBillingCycleTests.java:32`, `FullProductLifecycleTests.java:32`) passes whenever the banner is merely slow, so it is a false positive.
  - `assertTrue(isSuccessMessageShown())` fails whenever the message is slow, so it is a false negative.
- **Recommendation:** Positive checks should wait for visibility with a timeout. Negative checks should assert a positive success signal instead (for example, the dashboard is visible), or wait for invisibility explicitly.

#### H5. Tests with no assertions or with always-true assertions
- **Evidence:**
  - `ProductGridTests.java`: all 3 tests (`testOpenProductGridAndFilter` `:26-33`, `testSortProductGridByPrice` `:36-44`, `testExpandProductDetailsPanel` `:47-53`) contain **no assertion**. `:52` calls `detailsPanel.isDisplayed()` and discards the result.
  - `InvoiceLookupTests.testInvoiceGridLoadsWithoutError` `:51-55` calls `grid.isDisplayed()` and discards the result.
  - `FullProductLifecycleTests.java:87` asserts `rows.size() >= 0`, which is always true. `:94` calls `exportToast.isDisplayed()` and discards the result.
  - `Assert.assertNotNull(orderCreatePage.getConfirmationOrderId())`: `WebElement.getText()` never returns `null`, so this cannot fail once the element exists. It appears at `CreateOrderTests.java:42,57,67,77`, `FullAdminWorkflowTests.java:99`, `FullInvoiceBillingCycleTests.java:51` and `InvoiceLookupTests.java:42`.
  - `RegisterUserTests.testDependsOnPreviouslyRegisteredEmail` `:76-79` asserts a static field that the test class assigned itself (`:43`). It tests the test code, not the application.
  - `CreateOrderTests.testReuseOrderIdFromEarlierTest` `:81-85` types a note, never saves it and asserts nothing about the application.
  - `BasePage.compareElementText` `:164-172` returns **`true`** when an exception is thrown, so a missing element counts as a match. It is unused, but it would produce false passes if anyone adopted it.
  - The scratch and debug tests (`wip/*`) contain no assertions. One prints `"did it work? who knows"`.
- **Impact:** Green builds mean very little. Roughly a third of the `@Test` methods cannot fail on a functional regression.
- **Recommendation:**
  - Every test must assert an observable business outcome. For example, assert that the order id matches a pattern and the order appears in the grid with the expected status, or that the grid is sorted by price.
  - Add a static-analysis rule, or a review checklist item, that bans discarded `isDisplayed()` results and tautological assertions.

#### H6. End-to-end tests whose step comments claim checks they never make
- **Evidence:**
  - `FullAdminWorkflowTests`:
    - "feature 6: verify dashboard reflects the new order count" (`:118-120`) only checks the welcome banner.
    - "feature 7: log back in to verify audit trail persisted" (`:122-130`) never logged out, calls `login` while already logged in, and checks no audit trail.
    - "feature 8: confirm the status stuck" (`:132-134`) only checks that a field is enabled.
    - "feature 10: check the user grid still lists the modified user" (`:146-155`) asserts `isPageLoaded()`.
  - `FullInvoiceBillingCycleTests`:
    - "feature 8: verify dashboard revenue widget updates" (`:106-108`) only checks the banner.
    - "feature 12: confirm the archived invoice no longer appears" (`:145-153`) only asserts `dashboardPage.isPageLoaded()` on the invoices page.
  - `FullProductLifecycleTests`:
    - "feature 9: check invoice was generated for the exported orders" (`:111-120`) only checks that the grid is displayed.
    - "feature 12: confirm the archived product no longer appears" (`:145-153`) asserts `isPageLoaded()`.
  - `isPageLoaded()` (`BasePage.java:214-216`) only checks `document.readyState`, which says nothing about the business state.
- **Impact:** The reported coverage is fiction. Stakeholders reading these tests would believe the audit trail, revenue widget, archiving and invoice generation are verified, and they are not.
- **Recommendation:** Either implement real assertions for each claimed behaviour, or delete the misleading comments and steps. Track real coverage against requirements.

#### H7. Tests depend on each other through static state and priority ordering
- **Evidence:**
  - `CreateOrderTests.java:20` declares `static String orderIdFromFirstTest`, which is set at `:43` and consumed at `:82-84` (`priority = 5` depends on `priority = 1`).
  - `RegisterUserTests.java:20` declares `static String lastRegisteredEmail`, which is set at `:43` and read at `:77`.
  - Class-level `@BeforeClass` logs in once (`CreateOrderTests.java:22-30`, `RegisterUserTests.java:22-30`, `InvoiceLookupTests.java:22-30`, `ProductGridTests.java:17-23`), and every test assumes the browser is left in a usable state by the previous one. Nothing resets state between tests.
- **Impact:** You cannot run a single test in isolation, in a different order or in parallel. One failure cascades through the rest of the class.
- **Recommendation:**
  - Make every test self-contained: create its own preconditions, preferably through the API (`apiUrl` is already configured) or DB fixtures, and use `@BeforeMethod` for a fresh session.
  - If a dependency is truly required, use `dependsOnMethods` explicitly, never shared statics.

#### H8. Monolithic "mega" tests
- **Evidence:** `FullAdminWorkflowTests`, `FullInvoiceBillingCycleTests` and `FullProductLifecycleTests` each contain one `@Test` method of about 140 lines that chains 11-13 numbered "features" across unrelated areas (users, orders, products, invoices, exports).
- **Impact:** The first failure hides all later checks, failures are hard to diagnose, and the tests are slow and fragile. These tests carry most of the suite's assertions, so a single flaky step makes most coverage disappear.
- **Recommendation:**
  - Split them into focused tests, one behaviour each, with API or DB setup and teardown.
  - Keep at most one or two genuine end-to-end smoke journeys, built from page-object flows and with real assertions at the end.

#### H9. Wrong navigation and logic errors in test flows
- **Evidence:**
  - User registration is preceded by `dashboardPage.openOrdersMenu()`, which navigates to **Orders**, not user registration: `RegisterUserTests.java:34,48,84` and `FullAdminWorkflowTests.java:46`.
  - `FullAdminWorkflowTests.java:107-111` navigates to the `/orders` **list** and immediately drives `OrderModifyPage` without opening any order.
  - `FullAdminWorkflowTests.java:123` calls `login(...)` while already logged in. The comment says "log back in", but there was no logout.
  - `UserManagement.getFirstResultRow` selects `tr[2]`, which is the second row, not the first (`UserManagement.java:12`).
  - `RegisterUserTests.registerInline` accepts `state` (`:83`) but never uses it.
  - `testRegisterUserMinimalProfile` (`:68-73`) fills the full profile, just like `testRegisterUserFullProfile`.
- **Impact:** These tests either fail for reasons unrelated to the product or exercise the wrong screens. Either way they are not testing what they claim.
- **Recommendation:**
  - Add explicit navigation methods to page objects, such as `DashboardPage.openUserRegistration()` returning a `UserRegisterPage`.
  - Use fluent page transitions (actions return the next page object) so wrong-page flows cannot compile.
  - Fix the minimal-profile test so it actually omits optional fields.

#### H10. Hard-coded, non-unique test data with no cleanup
- **Evidence:**
  - Fixed emails and names are used on every run, for example `alice.nguyen@acmecorp.com` (`RegisterUserTests.java:37`), `grace.kim@acmecorp.com` (`FullAdminWorkflowTests.java:49`) and `John Doe` / `john.doe@example.com` (`CreateOrderTests.java:35-36`).
  - No teardown deletes the users, orders or products that were created.
  - There is no `@DataProvider` (0 hits), builder or factory.
  - Helper methods take long positional parameter lists: `createOrderInline` has 11 `String` parameters (`CreateOrderTests.java:88-90`) and `registerInline` has 10 (`RegisterUserTests.java:81-83`).
- **Impact:**
  - A second run collides with unique-email rules.
  - Data piles up in the target environment (production, see C4).
  - It is easy to swap arguments in long lists of untyped `String` parameters.
- **Recommendation:**
  - Use test-data builders or factories (`OrderData.builder()...`) with unique suffixes (timestamp or UUID).
  - Use `@DataProvider` for variants.
  - Clean up through the API in `@AfterMethod`.

#### H11. WIP/debug tests are part of the CI suite
- **Evidence:**
  - `testng.xml:13` includes the `com.acme.crm.wip` package.
  - `DebugOrderExportTest.java:22` carries the comment "debugging flaky export button, remove before merge".
  - `ScratchLoginExperimentTest.java:9` carries "TODO: delete this or move it somewhere real - Dave, 2024".
  - Neither test has assertions or `try/finally`, so a failure leaks a Chrome process.
- **Impact:** CI runs noise tests, leaks browser processes, and the experimental login uses real admin credentials against production.
- **Recommendation:** Delete the `wip` package, or move it outside `src/test` and exclude it from the suite. Enforce this through review.

### Medium

#### M1. `BasePage` is a god class (violates SRP)
- **Evidence:** `BasePage.java` (231 lines) mixes navigation, waits, "hack" sleeps, popup handling, **assertions**, file logging, CSV result writing, JS scrolling and highlighting, frames, dropdowns and hover. Its own Javadoc (`:17-20`) says it "bundles navigation, assertions, popup handling, data I/O and logging all in one class".
- **Unused methods:** 14 public methods have 0 call sites: `waitUntilDisplayed`, `waitUntilClickable`, `waitForPageLoadHack`, `waitForAjaxSpinnerHack`, `getRawElement`, `acceptAlertIfPresent`, `dismissCookieBanner`, `closeAnyModal`, `assertTextPresent`, `assertElementVisible`, `assertUrlContains`, `compareElementText`, `writeResultToCsv`, `highlightElement`. In addition, `takeScreenshotPathPlaceholder` (`:228-230`) just returns `null`.
- **Recommendation:**
  - Keep `BasePage` to driver access plus waited interaction primitives.
  - Move waits to a `Waits` helper, logging to SLF4J/Logback, and reporting to a TestNG listener.
  - Move assertions to tests or to dedicated assertion and verification helpers.
  - Delete the dead code.

#### M2. Assertions inside page objects, and a misleading verify method
- **Evidence:**
  - `BasePage.java:147-158` imports `org.testng.Assert` into page code.
  - `verifyFieldIsEditableAndEnabled()` throws `AssertionError` in all four `*ModifyPage` classes (for example, `OrderModifyPage.java:22-27`).
  - Despite its name, that method only checks `isEnabled()`. It does not detect `readonly` fields, so "editable" is not verified.
- **Recommendation:** Page objects should expose state (`isNameFieldEditable()` checking both `isEnabled()` and the absence of `readonly`), and tests should assert on it. Keep TestNG out of `src/main`.

#### M3. Raw Selenium in tests and `WebElement` leaking out of page objects
- **Evidence:**
  - Tests call `driver.findElement(...)` directly 27 times, mostly in `FullProductLifecycleTests`, `FullInvoiceBillingCycleTests`, `InvoiceLookupTests` and `ProductGridTests`.
  - There are no page objects for the product grid, product create, invoice list or toasts.
  - `BasePage.getRawElement(s)` (`:79-85`), `OrderHandler.getAllOrderRows()` (`:35-37`) and `UserManagement.getFirstResultRow()` (`:28-30`) return `WebElement`s to tests.
- **Impact:** Locators and Selenium details spread into tests. A UI change requires edits in many places.
- **Recommendation:**
  - Add the missing page objects and components: `ProductListPage`, `ProductFormPage`, `InvoiceListPage`, `Toast` and a `GridComponent`.
  - Return domain values (`List<OrderRow>`, `String`, `boolean`) or page objects, never `WebElement`.

#### M4. Copy-paste duplication
- **Evidence:**
  - `InvoiceModifyPage`, `OrderModifyPage`, `ProductModifyPage` and `UserModifyPage` are identical (50 lines each) apart from locator values and the error message. Each also re-implements `enterName` by hand instead of using `BasePage.type` (for example, `OrderModifyPage.java:29-33`).
  - The `@BeforeClass` setup and login block is duplicated in 4 test classes.
  - The `try { Thread.sleep } catch {}` block is repeated 38 times.
  - The order-creation steps are duplicated across `CreateOrderTests`, `FullAdminWorkflowTests`, `FullInvoiceBillingCycleTests` and `InvoiceLookupTests`.
- **Recommendation:**
  - Extract an `EntityModifyForm` component or abstract base parameterised by its root locator.
  - Add a `BaseTest`.
  - Add flow methods such as `OrderCreatePage.createOrder(OrderData)`.

#### M5. Error handling swallows failures
- **Evidence:**
  - `catch (Exception e)` that returns false or does nothing: `BasePage.java:72,122,131,140,169`.
  - Empty `InterruptedException` catches (36).
  - `ScreenshotUtil.java:19` writes to `target/screenshots/` without creating the directory and fails if the file already exists. The `IOException` is printed and ignored.
  - `DbConnector` returns `null` or `-1`.
  - `EmailSenderUtil` prints and ignores.
- **Recommendation:**
  - Catch only specific exceptions such as `NoSuchElementException` or `NoAlertPresentException`.
  - Restore the interrupt flag (`Thread.currentThread().interrupt()`).
  - Create directories with `Files.createDirectories`.
  - Let infrastructure failures fail the test with a clear message.

#### M6. No reporting, failure diagnostics or real logging
- **Evidence:**
  - `ScreenshotUtil` has 0 usages, and no `ITestListener` takes screenshots on failure.
  - There is no Allure or ExtentReports.
  - Logging is `System.out` plus a `FileWriter` reopened on every call (`BasePage.java:176-184`).
  - CI only runs `cat target/surefire-reports/*.txt || true` (`ci.yml:24-26`) and uploads no artifacts.
- **Recommendation:**
  - Add a TestNG `ITestListener` that captures a screenshot, page source and browser logs on failure.
  - Add Allure (or Extent) reporting.
  - Use SLF4J.
  - Upload `target/surefire-reports`, screenshots and the report as CI artifacts, and publish JUnit XML to the PR.

#### M7. CI pipeline design
- **Evidence (`ci.yml`):**
  - It runs the full suite, including WIP tests, on every push to every branch and on every PR (`:3-7`).
  - There is no Maven cache, no browser or driver setup, no headless flag and no `secrets` usage.
  - There is no environment parameter, test grouping or parallelism. TestNG `groups` has 0 hits, so smoke and regression cannot be separated.
  - Results are swallowed with `|| true`.
- **Recommendation:**
  - Run a fast smoke group on PRs and the full regression on a schedule or on merges to `main`, against QA or staging.
  - Add `actions/setup-java` `cache: maven`, headless Chrome and secrets.
  - Add artifact upload and a test-report action.

#### M8. Outdated and vulnerable dependencies
- **Evidence:** `pom.xml` pins Java 1.8 (`:13-14`), Selenium 3.141.59 (2018, unmaintained), TestNG 6.14.3, Surefire 2.22.2 and `mysql-connector-java` 8.0.19, which has known CVEs and has since been renamed `com.mysql:mysql-connector-j`.
- **Impact:** No Selenium Manager, no BiDi or CDP features and no relative locators. Driver binaries must be managed by hand, and the dependencies carry known security issues.
- **Recommendation:**
  - Upgrade to Java 17+, Selenium 4.x, TestNG 7.x and Surefire 3.x.
  - Note that `new WebDriverWait(driver, int)` (`BasePage.java:56,61`) must become `Duration.ofSeconds(...)`.
  - Add Dependabot or Renovate.

#### M9. Dead utilities and dead configuration
- **Evidence:**
  - 0 usages each for `DbConnector`, `EmailSenderUtil`, `ScreenshotUtil` and `DateFormatterUtil`.
  - The `retryCount` suite parameter is unused.
  - `implicitWaitSeconds`, `apiUrl` and `browser` in config are unused.
  - 14 `BasePage` methods are unused (see M1).
- **Impact:** This misleads readers about what the framework does, and in the case of C1 it breaks the build.
- **Recommendation:** Delete the dead code, or wire it in deliberately. For example, wire `ScreenshotUtil` into a failure listener and `DateFormatterUtil` into unique-data generation.

#### M10. No test categorisation, traceability or parallel readiness
- **Evidence:**
  - No TestNG `groups`, `description` or requirement and ticket IDs on any `@Test`.
  - `testng.xml` has a single `<test name="AllTests">` with no `parallel` or `thread-count` settings.
  - The shared static state (H7) and the absence of a `ThreadLocal` driver (H1) would block parallel runs anyway.
- **Recommendation:**
  - Tag tests (`smoke`, `regression` and feature area) and link them to requirements.
  - Make drivers thread-local and tests independent, then enable `parallel="methods"` with a modest `thread-count`.

### Low (naming and coding standards)

#### L1. Inconsistent page-object naming
`OrderHandler` (`OrderHandler.java:12`) and `UserManagement` (`UserManagement.java:10`) break the `*Page` convention used everywhere else, and "Handler" suggests a controller rather than a page. **Rename** them `OrderListPage` and `UserListPage`.

#### L2. Misleading class name
`RetryListener` is a retry *analyzer*, not a listener. This naming confusion is likely what caused C2. **Rename** it `RetryAnalyzer` (and add a separate `RetryTransformer` if you need one).

#### L3. Test class and method names
- `Full*Tests` classes each contain a single test.
- `test` prefixes are redundant in TestNG.
- Several names do not state the expected outcome or are inaccurate:
  - `testRegisterUserMinimalProfile` fills a full profile.
  - `testDependsOnPreviouslyRegisteredEmail` describes a dependency, not a behaviour.
  - `testOpenProductGridAndFilter` verifies nothing.
  - `testInvoiceGridLoadsWithoutError` never checks for errors.
- **Adopt** `should<Outcome>_when<Condition>`, or `<action>_<expectedResult>`, consistently.

#### L4. Poor and misleading identifiers
- Parameters named `v` throughout `UserRegisterPage.java:24-58`.
- In `InvoiceModifyPage.java:12`, `nameField` maps to `invoiceRefInput`, and `enterName` is used to type an invoice reference (`FullInvoiceBillingCycleTests.java:72`).
- `emailField` maps to `billingEmail` and `ownerEmail` in different classes.
- `navMenu` in `DashboardPage.java:8` actually means the Orders menu item.

#### L5. "Hack" and other informal names in production framework code
`waitForPageLoadHack` and `waitForAjaxSpinnerHack` (`BasePage.java:103,110`) and `isElementPresentNow`. Utility naming is also inconsistent: `DbConnector` sits alongside `*Util` classes.

#### L6. Fully-qualified names instead of imports
`new org.openqa.selenium.support.ui.Select(...)` (`BasePage.java:220`), `new org.openqa.selenium.interactions.Actions(...)` (`:225`) and `java.util.List<WebElement>` (`FullProductLifecycleTests.java:86`).

#### L7. Stale TODOs and personal notes in committed code
- "TODO: delete this or move it somewhere real - Dave, 2024" (`ScratchLoginExperimentTest.java:9`).
- "remove before merge" (`DebugOrderExportTest.java:22`).
- `System.out.println("did it work? who knows")` (`ScratchLoginExperimentTest.java:20`).

#### L8. Repository hygiene
- There is no `.gitignore`, so `target/`, `target/automation.log` and `results.csv` risk being committed.
- The README lacks prerequisites (chromedriver and browser version), environment selection, how to run a single group or test, and reporting.

#### L9. Comment style and accuracy
- Comments describe intent that the code does not implement (see H6).
- Section banners such as `// ---------- misc utility crammed in ----------` (`BasePage.java:194`) acknowledge the debt instead of fixing it.
- Fixed, unexplained numbers are scattered through the code (sleep durations, `3`, row indexes).

---

## 4. Recommended remediation plan (prioritised)

| Phase | Actions | Addresses |
|---|---|---|
| **0. Stop the bleeding (this week)** | Rotate the admin and DB credentials and purge them from history. Disable CI runs against production. Remove the `wip` package and the invalid `<listener>`. Delete or fix `EmailSenderUtil` so the build compiles. | C1-C5, H11 |
| **1. Foundation (1-2 sprints)** | Add a `Config` loader with per-environment files and env-var secrets. Add `DriverFactory` (ThreadLocal, headless, remote) and `BaseTest`. Upgrade to Java 17, Selenium 4 and TestNG 7. Add a failure listener (screenshot, logs) and Allure. Fix the CI pipeline (cache, headless, artifacts, smoke on PR). | H1, H2, M5-M8 |
| **2. Reliability** | Replace every `Thread.sleep` with explicit waits inside page objects. Replace `isElementPresentNow` oracles. Get `data-testid` attributes from developers and replace positional XPaths and `ext-comp-*` ids. | H3, H4, H4b |
| **3. Test validity** | Give every test a real outcome assertion. Remove the tautologies. Split the mega tests. Remove static inter-test state. Set up data through the API with builders and unique data. Add cleanup. Fix the wrong-navigation flows. | H5-H10 |
| **4. Design and standards** | Slim down `BasePage`. Add the missing page objects and components. Remove the `*ModifyPage` duplication. Stop returning `WebElement`s. Apply naming conventions. Add groups and traceability. Delete dead code. Add `.gitignore` and update the README. | M1-M4, M9, M10, L1-L9 |

---

## 5. Assumptions and limitations

- This was a static review. I did not run `mvn` or the suite, because it targets production hosts and credentials. "Does not compile" (C1) and "suite fails at startup" (C2) are based on the declared dependencies and TestNG 6.x listener-type validation, not on an observed run.
- The team's maturity-assessment spreadsheet format was not provided. The checklist table (section 6 and `checklist.md`) uses a generic layout (Area / Checklist item / Status / Evidence / Recommendation). Status values are **Yes** (met), **Partial**, **No** (not met) and **N/A**. Adjust the column names to match your sheet.
- Counts come from grep over `src/` (for example, `grep -rn "Thread.sleep" src | wc -l` returned 38).

---

## 6. Checklist-tab table

The same table is saved separately as `checklist.md`.

| # | Area | Checklist item | Status | Evidence | Recommendation |
|---|---|---|---|---|---|
| 1 | Build & dependencies | Project builds cleanly from a fresh clone | No | `EmailSenderUtil.java:4-9` imports `javax.mail`; no dependency in `pom.xml` | Remove the class or add the dependency |
| 2 | Build & dependencies | Dependencies are current and free of known vulnerabilities | No | Selenium 3.141.59, TestNG 6.14.3, Java 8, mysql-connector 8.0.19 | Upgrade to Selenium 4, TestNG 7, Java 17+; add Dependabot |
| 3 | Security | No secrets or credentials in source control | No | `config.properties:3-9`, `DbConnector.java:15-17`, `LoginPage.java:33`, 4 test files | Rotate, purge history, use CI secrets or a vault |
| 4 | Environment | Tests run against a non-production environment | No | `baseUrl=https://crm-admin.acmecorp.com`, `dbName=crm_production` | Dedicated QA or staging environment |
| 5 | Configuration | Environment-specific config externalised and actually used | No | `config.properties` never loaded; 35 hard-coded URLs | `Config` loader, per-env files, system-property overrides |
| 6 | Driver management | Central driver factory, browser selectable, headless and remote supported | No | 9 x `new ChromeDriver()`; `browser` config unused | `DriverFactory` + `ThreadLocal` + options |
| 7 | Architecture | Base test class handles setup and teardown consistently | No | Setup duplicated in 4 classes; WIP tests have no `finally` | `BaseTest` with `@BeforeMethod`/`@AfterMethod(alwaysRun=true)` |
| 8 | Architecture | Page Object Model used consistently | Partial | POs exist, but tests call `driver.findElement` 27 times; no product or invoice POs | Add missing POs and components |
| 9 | Architecture | Page objects free of assertions | No | `BasePage.java:147-158`; `verifyFieldIsEditableAndEnabled` throws `AssertionError` | Expose state; assert in tests |
| 10 | Architecture | Page objects do not expose raw `WebElement` | No | `getRawElement(s)`, `getAllOrderRows`, `getFirstResultRow` | Return domain values or page objects |
| 11 | Design principles | Single Responsibility (no god classes) | No | `BasePage` mixes navigation, waits, asserts, logging, CSV, JS | Split into helpers and components |
| 12 | Design principles | DRY: no copy-paste classes or flows | No | 4 identical `*ModifyPage` classes; repeated sleep blocks and setup | Shared form component, flow methods |
| 13 | Code hygiene | No dead code or unused utilities | No | `DbConnector`, `EmailSenderUtil`, `ScreenshotUtil`, `DateFormatterUtil` and 14 `BasePage` methods unused | Delete or wire in |
| 14 | Synchronization | No hard-coded sleeps; explicit waits used | No | 38 `Thread.sleep`; wait helpers have 0 call sites | `WebDriverWait` inside PO actions |
| 15 | Synchronization | Visibility and state checks wait rather than poll once | No | `isElementPresentNow` backs 3 assertion helpers | Waited checks with a timeout |
| 16 | Locators | Stable, semantic locators (`data-testid`, id, name, role) | Partial | Some id and name locators; 12 positional XPaths; 9 `ext-comp-*` ids | Add `data-testid`; remove index XPaths |
| 17 | Test design | Each test has meaningful assertions on business outcomes | No | `ProductGridTests` has 0 asserts; discarded `isDisplayed()`; `size() >= 0`; `assertNotNull(getText())` | Assert real outcomes |
| 18 | Test design | Tests are independent and order-agnostic | No | Static `orderIdFromFirstTest`, `lastRegisteredEmail`; priority chaining | Self-contained tests, API setup |
| 19 | Test design | Tests are small and focused (one behaviour per test) | No | 3 mega tests with 11-13 chained features | Split; keep 1-2 smoke journeys |
| 20 | Test design | Test steps and comments match what is verified | No | FullAdmin features 6, 7, 8, 10; FullInvoice 8, 12; FullProduct 9, 12 | Implement or remove the claims |
| 21 | Test design | Navigation flows are correct | No | `openOrdersMenu()` before user registration; OrderModify used from the list page | Explicit navigation and fluent POs |
| 22 | Test data | Test data externalised, unique per run, data-driven | No | Hard-coded emails; 0 `@DataProvider`; 11-parameter helpers | Builders, unique suffixes, DataProviders |
| 23 | Test data | Created data is cleaned up | No | No teardown of users, orders or products | API cleanup in `@AfterMethod` |
| 24 | Test data | Preconditions set up through API or DB, not UI | No | All setup through UI; `apiUrl` unused | API client for fixtures |
| 25 | Error handling | Exceptions not swallowed; interrupts restored | No | 36 empty catches; `catch (Exception)` in `BasePage`; `compareElementText` returns true on error | Specific catches; fail loudly |
| 26 | Flakiness policy | Retry policy is deliberate, limited and reported | No | Invalid listener registration; hard-coded 3 retries; param ignored | Fix wiring; at most 1 retry; report flaky |
| 27 | Reporting | Rich reports with screenshots and logs on failure | No | `ScreenshotUtil` unused; no Allure or Extent; `System.out` logging | Failure listener + Allure + SLF4J |
| 28 | Suite organisation | Groups or tags (smoke, regression) and traceability | No | 0 `groups`; no descriptions or IDs | Tag tests; link to requirements |
| 29 | Suite organisation | No WIP or debug tests in the executed suite | No | `testng.xml:13` includes the `wip` package | Delete or exclude |
| 30 | Parallelism | Suite is parallel-safe and configured for parallel runs | No | No `parallel` setting; static state; no `ThreadLocal` driver | Fix isolation, then enable parallel |
| 31 | CI/CD | CI runs the right scope at the right time against the right environment | No | Full suite on every push to every branch, against production | Smoke on PR, regression nightly, QA environment |
| 32 | CI/CD | CI publishes test reports and artifacts | No | Only `cat *.txt \|\| true` | Upload artifacts; publish JUnit XML |
| 33 | CI/CD | CI configures browser, headless mode, caching and secrets | No | None present in `ci.yml` | `setup-java` cache, headless, secrets |
| 34 | Naming | Consistent class naming conventions (`*Page`, `*Test`, `*Util`) | Partial | `OrderHandler`, `UserManagement`, `RetryListener` (actually an analyzer), `DbConnector` | Rename |
| 35 | Naming | Descriptive test and method names that state the expected outcome | Partial | `testRegisterUserMinimalProfile` misnamed; `*Hack` methods; parameters named `v` | Naming convention and review |
| 36 | Coding standards | Clean code: imports, no stale TODOs or debug prints, no unexplained numbers | No | FQCNs inline; "Dave, 2024" TODO; "did it work? who knows" | Lint (Checkstyle or PMD) in CI |
| 37 | Documentation | README is accurate and covers setup, run options and environments | Partial | README exists, but its config claim is false and prerequisites and env selection are missing | Update the README |
| 38 | Repository hygiene | `.gitignore` excludes build output and logs | No | No `.gitignore` in the repo | Add a standard Maven `.gitignore` |

**Totals:** Yes 0, Partial 5, No 33.
