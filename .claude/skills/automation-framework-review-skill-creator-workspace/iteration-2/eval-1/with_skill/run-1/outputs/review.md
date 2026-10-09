# Automation Framework Issues

**Scope:** `messy-framework` (Java 8 / Selenium 3.141.59 / TestNG 6.14.3 / Maven). All 30 files were read in full: 11 page objects (`src/main/java/com/acme/crm/pages`), 5 utilities (`src/main/java/com/acme/crm/utils`), 7 test classes (`src/test/java/com/acme/crm/tests`), 2 scratch tests (`src/test/java/com/acme/crm/wip`), plus `pom.xml`, `testng.xml`, `.github/workflows/ci.yml`, `src/test/resources/config.properties` and `README.md`. The suite has 20 `@Test` methods. All paths below are relative to the framework root.
**Excluded from this review:** nothing was excluded. The application UI was not available, so every claim about runtime behaviour comes from reading the code. Claims that need a live run to confirm are marked **(hypothesis)**.

**Verdict up front:** The suite probably cannot run at all right now. `src/main` imports `javax.mail`, but the POM doesn't declare it, so `mvn clean test` should fail at compile time. Even if it compiled, it would give little real signal. The only synchronization is 38 hardcoded `Thread.sleep` calls. 6 of 20 tests assert nothing, and several more assert things that can't fail. Tests share static state and create literal-named records that are never cleaned up. The three largest tests each cram 11-13 "features" into one method, and their step comments promise checks the code never makes. Structurally, there's no business-step layer, no driver/config layer and no data builders: tests compose raw page actions, or raw Selenium calls directly, on top of a 32-method God base class. Credentials and a production database URL are committed in plaintext.

---

## Build and CI

### The project cannot compile: `javax.mail` is used but not declared
`[Impact: High | Effort: Low]`

- `src/main/java/com/acme/crm/utils/EmailSenderUtil.java:4-9` imports `javax.mail.*`. `pom.xml:20-36` declares only `selenium-java`, `testng` and `mysql-connector-java`, and none of them brings JavaMail in transitively. JavaMail has never been part of Java SE 8. The file is under `src/main`, so the `compile` phase of `mvn clean test` (the README's run command, `README.md:15`, and the CI command, `ci.yml:22`) should fail before any test runs. This needs confirming with one `mvn compile`; it wasn't executed here, to avoid writing `target/` into the repo under review.
- `EmailSenderUtil` has **0 references** outside its own definition (repo-wide grep). Deleting it fixes the build just as well as adding the dependency.
- **(hypothesis)** Even after the compile is fixed, all 9 `new ChromeDriver()` calls (listed under "No driver/fixture layer" below) start Chrome with no options. `ci.yml:11` runs on `ubuntu-latest` with no display server and no `--headless` flag (grep for `headless`/`ChromeOptions`: 0 hits). Chrome normally refuses to start in that setup. Check this against a real CI log.

### Scratch/WIP tests are part of the suite that CI runs
`[Impact: Medium | Effort: Low]`

- `testng.xml:13` includes the package `com.acme.crm.wip`. Its two classes are explicitly throwaway: `ScratchLoginExperimentTest.java:9` says "TODO: delete this or move it somewhere real - Dave, 2024", and `:18-20` says "just poking at this, not a real test yet … did it work? who knows". `DebugOrderExportTest.java:10,22` says "Leftover draft test … remove before merge".
- Neither class has an assertion. Both call `driver.quit()` only on the happy path (`DebugOrderExportTest.java:25`, `ScratchLoginExperimentTest.java:21`, with no `finally`), so any failure leaves a Chrome process running. `DebugOrderExportTest` calls `clickExport()` twice (`:23-24`), which adds 8 s of fixed sleep (`OrderHandler.java:29`).
- The README describes the tests as living in `src/test/java/com/acme/crm/tests` (`README.md:24`) and doesn't mention `wip`.

### No test tagging; every push and every PR on every branch runs the full suite
`[Impact: Medium | Effort: Low]`

- There are 0 `groups=` / category annotations anywhere (repo-wide grep). `testng.xml:10-15` defines a single `AllTests` test.
- `ci.yml:3-7` triggers on `push` to `"**"` and on `pull_request` to `"**"`. A push to a branch that has an open PR therefore runs the whole suite twice. There's no fast smoke subset for PRs and no separate nightly or full job.

---

## Secrets and environment

### Plaintext credentials committed in 7 files
`[Impact: High | Effort: Low]`

The credentials grep (`password|api_key|token|secret` assigned to a literal) found **9 hardcoded password occurrences in 7 files**:

| File:line | Value |
|---|---|
| `src/test/resources/config.properties:4` | `adminPassword=Admin123!` |
| `src/test/resources/config.properties:9` | `dbPassword=Sup3rSecret!` |
| `src/main/java/com/acme/crm/utils/DbConnector.java:17` | `PASSWORD = "Sup3rSecret!"` (production DB user `crm_svc`, `:16`) |
| `src/main/java/com/acme/crm/pages/LoginPage.java:33` | `login("admin@acmecorp.com", "Admin123!")` |
| `src/test/java/com/acme/crm/tests/FullAdminWorkflowTests.java:35`, `:123` | same admin literal |
| `src/test/java/com/acme/crm/tests/FullInvoiceBillingCycleTests.java:31` | same admin literal |
| `src/test/java/com/acme/crm/tests/FullProductLifecycleTests.java:31` | same admin literal |
| `src/test/java/com/acme/crm/wip/ScratchLoginExperimentTest.java:19` | `"Admin123!@#$%"` variant |

Nothing reads secrets from the environment or from CI secrets. `ci.yml` has no `env:`/`secrets.` references.

### A test utility points at the production database and builds SQL by string concatenation
`[Impact: Medium | Effort: Low]`

- `DbConnector.java:15` hardcodes `jdbc:mysql://prod-crm-db.acmecorp.internal:3306/crm_production`, and `config.properties:5-6` repeats `prod-crm-db…`/`crm_production`. This is a test framework wired straight to production data, with no switch to a test database.
- `DbConnector.java:32` builds `"… WHERE customer_email = '" + customerEmail + "'"`. That's open to SQL injection, and it also breaks on any email containing an apostrophe. `Statement` is used where `PreparedStatement` belongs. `runQuery` (`:19-28`) never closes the `Connection`/`Statement`, so every call leaks a connection.
- Impact is Medium rather than High only because `DbConnector` currently has **0 callers** (repo-wide grep). It's one import away from being used against production.

### `config.properties` is never read; the environment is hardcoded in 33 places
`[Impact: High | Effort: Medium]`

- `README.md:18` says "Configuration (URLs, credentials) lives in `src/test/resources/config.properties`". The code says otherwise: there are **0** `getProperty`/`Properties.load`/`config.properties` references in `src` (the only `new Properties()` is the SMTP setup in `EmailSenderUtil.java:17`).
- The base URL `https://crm-admin.acmecorp.com` appears as a literal **33 times across all 9 test classes** (FullAdmin 7, FullInvoice 7, FullProduct 7, ProductGrid 4, InvoiceLookup 3, DebugOrderExport 2, CreateOrder 1, RegisterUser 1, ScratchLogin 1).
- `browser=chrome` (`config.properties:10`) and `implicitWaitSeconds=10` (`:11`) are dead settings. `ChromeDriver` is hardcoded and `implicitlyWait` has 0 call sites, which matters for the sync findings below. `apiUrl` (`:2`) is also unused.
- Targeting another environment (staging, local) means editing 9 Java files. There's no profile, system-property or env-var mechanism. The code also doesn't make clear whether `crm-admin.acmecorp.com` is production. Given the `crm_production` DB entry next to it, the team should confirm that the UI suite (which creates users and orders and archives products and invoices) isn't running against production.

---

## Architecture and layering

### Missing business-step/flow layer: every test re-composes raw page actions
`[Impact: High | Effort: High]`

There's no `steps/`, `flows/` or similar package. Tests build each business action out of field-level page calls:

- **Create an order:** the `enterCustomerName → enterCustomerEmail → selectProduct → enterQuantity → … → submit` sequence appears at **6 call sites in 4 files**: `CreateOrderTests.java:35-39`, `:49-54`, `:92-101` (helper); `FullAdminWorkflowTests.java:88-96`; `FullInvoiceBillingCycleTests.java:41-48`; `InvoiceLookupTests.java:35-39`.
- **Register a user:** the `enterFirstName → … → submitRegistration` sequence appears at **4 call sites in 2 files**: `RegisterUserTests.java:35-40`, `:49-54`, `:85-94`; `FullAdminWorkflowTests.java:47-56`.
- **Log in:** `driver.get(".../login")` followed by `login(...)`/`loginAsAdmin()` is repeated in **all 9 test classes**.
- The two attempts at reuse, `createOrderInline` (`CreateOrderTests.java:88`) and `registerInline` (`RegisterUserTests.java:81`), are `private` to one class each, so the other three order-creating classes can't use them.

The same root cause drives the DRY, readability and mega-test findings below. Fixing it won't resolve those on its own, so each keeps its own entry.

### No driver/fixture layer: 9 copies of browser setup, `ChromeDriver` hardcoded
`[Impact: High | Effort: Medium]`

- There are **9 `new ChromeDriver()` calls in 9 classes** (`CreateOrderTests.java:24`, `FullAdminWorkflowTests.java:23`, `FullInvoiceBillingCycleTests.java:22`, `FullProductLifecycleTests.java:22`, `InvoiceLookupTests.java:24`, `ProductGridTests.java:19`, `RegisterUserTests.java:24`, `DebugOrderExportTest.java:16`, `ScratchLoginExperimentTest.java:15`). There's no base test class, no driver factory and no TestNG listener/`@BeforeSuite` fixture.
- Lifecycle is managed three different ways. 4 classes use copy-pasted `@BeforeClass`/`@AfterClass` pairs (8 annotations, identical bodies). 3 classes use inline `try { … } finally { driver.quit(); }`. The 2 wip classes have no teardown at all, so they leak the browser when they fail.
- **OCP/DIP:** switching browser means editing 9 files. The `browser` config key exists but is ignored, and tests depend on the concrete `ChromeDriver` instead of a `WebDriver` supplier.

### Tests bypass page objects and drive Selenium directly
`[Impact: High | Effort: Medium]`

- **4 of 9 test classes** import `org.openqa.selenium.By`/`WebElement` and call `driver.findElement` directly: `FullProductLifecycleTests` (13 calls), `FullInvoiceBillingCycleTests` (7), `ProductGridTests` (5), `InvoiceLookupTests` (2). That's **27 raw `driver.findElement` calls and 27 raw locators** in the test layer. `ProductGridTests` has no page object for its screen at all. Several inline comments acknowledge the bypass ("via raw selenium click", `FullProductLifecycleTests.java:39,48,122`; `FullInvoiceBillingCycleTests.java:110`).
- Locators are duplicated between tests and page objects, or across tests, so they drift independently: `By.id("productNameInput")` (`FullProductLifecycleTests.java:51` and `ProductModifyPage.java:12`); `.crm-form-actions .btn-save` (`FullProductLifecycleTests.java:57` plus all 4 `*ModifyPage`); the invoice-row XPath `//div[4]/div[1]/table/tbody/tr[1]/td[2]` (`FullInvoiceBillingCycleTests.java:60`, `InvoiceLookupTests.java:45`); `productSearchInput`, `.product-toolbar .btn-search`, `invoiceGridContainer` and `.archive-modal .btn-confirm` each appear in 2 test files.
- **DIP inconsistency inside the domain layer too:** `BasePage.type()` (`BasePage.java:91-95`) wraps clear+sendKeys, but all 4 `*ModifyPage.enterName` methods re-implement it with raw `driver.findElement`/`clear`/`sendKeys` (`*ModifyPage.java:29-33`).

### Page objects leak `WebElement`, assert internally, and never return the next page
`[Impact: Medium | Effort: Low]`

- **Raw type leakage:** `OrderHandler.getAllOrderRows()` returns `List<WebElement>` (`OrderHandler.java:35`), `UserManagement.getFirstResultRow()` returns `WebElement` (`UserManagement.java:28`), and `BasePage.getRawElement/getRawElements` (`BasePage.java:79-85`) are public. Tests then act on the raw element (`FullAdminWorkflowTests.java:74` `.click()`, `FullProductLifecycleTests.java:86-87`).
- **Verification inside page objects:** all 4 `*ModifyPage.verifyFieldIsEditableAndEnabled()` methods `throw new AssertionError` (`InvoiceModifyPage.java:25`, `OrderModifyPage.java:25`, `ProductModifyPage.java:25`, `UserModifyPage.java:25`). `BasePage` adds `assertTextPresent`/`assertElementVisible`/`assertUrlContains` (`:147-158`) and imports `org.testng.Assert` into `src/main` (`BasePage.java:9`), which ties the domain layer to the test runner.
- **No navigation return types:** every page action returns `void`; 0 methods return a page object. So tests instantiate 4-7 page objects up front (for example `FullAdminWorkflowTests.java:25-31`), and nothing in the code says which page an action lands on. That's how the navigation mismatch under "`openOrdersMenu()` is used to reach the user-registration form" below went unnoticed.

### God base class: `BasePage` (231 lines, 32 public methods, 9 concerns)
`[Impact: High | Effort: Medium]`

- `BasePage.java:17-19` says so itself: "It bundles navigation, assertions, popup handling, data I/O and logging all in one class." The concerns are navigation (`:32-51`), explicit waits (`:55-63`), instant checks (`:69-75`), raw element access (`:79-99`), sleep hacks (`:103-115`), popup handling (`:119-143`), assertions (`:147-172`), file I/O and logging (`:176-192`), and JS/frame/hover utilities (`:196-230`).
- All 10 page classes inherit it. **SRP/ISP:** `LoginPage` inherits a CSV result writer, an iframe switcher, a hover helper and an element highlighter it never uses.
- **24 of 32 public methods have 0 callers** anywhere in the repo (grep for each bare identifier): `navigateTo`, `goBack`, `getCurrentUrl`, `getPageTitle`, `waitUntilDisplayed`, `waitUntilClickable`, `getRawElement`, `getRawElements`, `waitForPageLoadHack`, `waitForAjaxSpinnerHack`, `acceptAlertIfPresent`, `dismissCookieBanner`, `closeAnyModal`, `assertTextPresent`, `assertElementVisible`, `assertUrlContains`, `compareElementText`, `writeResultToCsv`, `scrollToElement`, `highlightElement`, `switchToFrame`, `switchToDefaultContent`, `hoverOver`, `takeScreenshotPathPlaceholder`. Only 8 are used: `isElementPresentNow`, `click`, `type`, `getText`, `log`, `refreshPage`, `isPageLoaded`, `selectDropdownByVisibleText`.
- Template for the split: the 8 used methods form a small interaction core. Waits, popups, assertions and I/O should move into separate collaborators that are injected only where needed.

### Unused utility classes
`[Impact: Medium | Effort: Low]`

4 of 5 classes in `utils/` have **0 references outside their own definition** (repo-wide grep of the bare class name): `DbConnector`, `EmailSenderUtil`, `ScreenshotUtil`, `DateFormatterUtil`. One of them breaks the build, and one holds production credentials. Together with the 24 dead `BasePage` methods, this is speculative code nobody calls. The fifth class, `RetryListener`, is referenced but miswired (see "Retry policy declared but miswired" below).

### Every precondition is built through the UI
`[Impact: Medium | Effort: High]`

- Login goes through the UI form in **9 of 9** test classes, including classes whose subject isn't login.
- The invoice tests create their prerequisite order through the full UI order form before checking anything about invoices (`FullInvoiceBillingCycleTests.java:40-48`, `InvoiceLookupTests.java:34-39`).
- An API endpoint is configured (`config.properties:2`, `apiUrl=…/api/v2`), but there's no HTTP/API client in the repo (no such dependency in `pom.xml`), and the one DB helper is unused. Whether API seeding is available and preferred depends on the team's stated strategy. Confirm against the questionnaire.

---

## Duplication

### Four near-identical `*ModifyPage` classes
`[Impact: Medium | Effort: Medium]`

`InvoiceModifyPage`, `OrderModifyPage`, `ProductModifyPage` and `UserModifyPage` are each exactly 50 lines and declare the same 6 methods (`verifyFieldIsEditableAndEnabled`, `enterName`, `selectStatus`, `enterEmail`, `clickSave`, `toggleActive`). The bodies are byte-identical apart from the 5 locator values and one word in the error message (`:22-49` in each file). The `saveButton` locator `.crm-form-actions .btn-save` is identical in all 4 (`:15`). That's about 200 lines that could be one parametrized `EntityModifyForm` component taking 4 locator sets. This is separate from the `BasePage` finding: splitting `BasePage` doesn't touch these siblings.

### The admin user is represented three disconnected ways
`[Impact: Medium | Effort: Low]`

- There's a typed entry point, `LoginPage.loginAsAdmin()` (`LoginPage.java:32`), with 5 callers (`CreateOrderTests:29`, `InvoiceLookupTests:29`, `ProductGridTests:22`, `RegisterUserTests:29`, `DebugOrderExportTest:20`).
- The 3 E2E classes reach around it with inline `login("admin@acmecorp.com", "Admin123!")` (4 sites, listed under "Plaintext credentials committed in 7 files" above).
- `config.properties:3-4` defines `adminUsername`/`adminPassword`, which nothing reads.

Rotating the admin password would currently mean editing 6 places, and the config file isn't one of them.

### No test-data builders; 10-11 positional `String` parameters instead
`[Impact: Medium | Effort: Medium]`

- `createOrderInline(...)` takes 11 `String` parameters (`CreateOrderTests.java:88-90`; its own comment at `:87` says it's "not a real builder/factory"). `registerInline(...)` takes 10 (`RegisterUserTests.java:81-83`).
- The shape is already producing defects. `registerInline` accepts `state` but never uses it (`:85-94` has no `enterState`). `testRegisterUserMinimalProfile` (`:68-73`) passes all 10 fields, the same as `testRegisterUserFullProfile` (`:60-65`), so its name claims a scenario it doesn't test.
- Order and user data are otherwise inline literals, repeated in 4 order-creating and 2 user-registering files.

---

## Synchronization

### 38 hardcoded sleeps are the only synchronization mechanism
`[Impact: High | Effort: Medium]`

- The unconditional-waits grep (`Thread.sleep|time.sleep|waitForTimeout|setTimeout|implicitlyWait`) found **38 `Thread.sleep` calls in 10 files**:
  - **8 in 6 page objects:** `BasePage.java:105,112`; `DashboardPage.java:19`; `LoginPage.java:22,35`; `OrderCreatePage.java:63`; `OrderHandler.java:29`; `UserRegisterPage.java:63`.
  - **30 in 4 test classes:** `FullInvoiceBillingCycleTests` 10, `FullProductLifecycleTests` 10, `FullAdminWorkflowTests` 9, `ProductGridTests` 1.
- **0 condition-based waits are actually used.** The only explicit-wait helpers, `BasePage.waitUntilDisplayed/waitUntilClickable` (`:55-63`), have 0 callers. There's no implicit wait: `implicitlyWait` has 0 hits, and `implicitWaitSeconds=10` is in a config file nothing reads. Every `findElement` is therefore an instant lookup, and the fixed sleeps are the only thing between an action and the next lookup.
- Sleeps are built into page actions, so every caller pays them: `login` 2 s, `loginAsAdmin` +1 s, `openOrdersMenu` 1 s, `submit` 2.5 s, `submitRegistration` 2 s, `clickExport` 4 s.
- The inline sleeps in the 3 E2E tests alone add up to 39.8 s per run (11.7 s + 14.3 s + 13.8 s), before counting the page-object sleeps.
- Context: Selenium 3.141.59 still has the deprecated `WebDriverWait(driver, int)` constructor used at `BasePage.java:56,61`. See "Core stack is 2018-era" below.

### Instant, non-retrying presence checks feed 12 assertions
`[Impact: High | Effort: Low]`

- `BasePage.isElementPresentNow()` (`:69-75`) does a single `findElement(...).isDisplayed()` and returns `false` on any exception. Its own Javadoc says it's "used in a few places as a substitute for a real wait".
- Three page predicates rely on it: `DashboardPage.isWelcomeBannerVisible` (`:25`), `LoginPage.isErrorBannerShown` (`:29`, commented "raw non-retrying instant check, no wait"), and `UserRegisterPage.isSuccessMessageShown` (`:69`). Together they're behind **12 assertion call sites in 4 test files**.
- The failure modes point in opposite directions:
  - `assertTrue(isWelcomeBannerVisible())` and `assertTrue(isSuccessMessageShown())` (9 sites) fail spuriously if the element needs one more render tick.
  - `assertFalse(isErrorBannerShown())` (3 sites: `FullAdminWorkflowTests.java:36`, `FullInvoiceBillingCycleTests.java:32`, `FullProductLifecycleTests.java:32`) **passes** whenever the error banner hasn't rendered yet, so a failed login can pass this check.
- On top of those, 6 raw `findElement(...).isDisplayed()` checks in tests have no wait (`FullInvoiceBillingCycleTests.java:94,121`; `FullProductLifecycleTests.java:94,120`; `InvoiceLookupTests.java:54`; `ProductGridTests.java:52`).
- The retrying variant (`waitUntilDisplayed`, `BasePage.java:55`) already exists and is unused.

---

## Error handling

### All 49 catch blocks swallow; none rethrows
`[Impact: High | Effort: Medium]`

The swallowed-exceptions grep (`catch (` across all `.java` files) found **49 catch blocks, and 0 rethrow with context**:

| Classification | Count | Where |
|---|---|---|
| Empty body | 38 | 36 `InterruptedException` catches around sleeps (7 in page objects, 29 in tests); `BasePage.java:131` (`dismissCookieBanner`); `BasePage.java:169` (`compareElementText`) |
| Return a sentinel | 3 | `BasePage.java:72` → `false`; `DbConnector.java:24-26` → `null`; `DbConnector.java:36-39` → `-1` |
| Log and continue | 8 | `OrderHandler.java:30`; `FullAdminWorkflowTests.java:70`; `BasePage.java:122,140,181,189`; `EmailSenderUtil.java:29`; `ScreenshotUtil.java:20` |

Worst offenders:

- **`BasePage.compareElementText` (`:164-172`):** on any exception, the empty catch falls through to `return true`. So "couldn't read either element" reports exactly like "texts match". It has 0 callers today, so the defect is latent.
- **`BasePage.isElementPresentNow` (`:70-74`):** catches `Exception`, so `StaleElementReferenceException`, `WebDriverException` (session dead) and `NoSuchElementException` all become `false`. That feeds the false-pass in "Instant, non-retrying presence checks feed 12 assertions" above.
- **All 38 `InterruptedException` catches** discard the interrupt without calling `Thread.currentThread().interrupt()`, so a TestNG timeout or CI cancellation can't stop a sleeping test cleanly.
- **The DB helpers use two different sentinels** (`null` and `-1`), and the page helpers use a third and fourth (`false` on error in one, `true` on error in the other). Callers can't tell which return values mean "failed to check".

Judged harmless, but only because they're labelled best-effort: `dismissCookieBanner`/`acceptAlertIfPresent`/`closeAnyModal` (`BasePage.java:119-143`) and the log-file writer (`:181`). Even these catch `Exception` rather than the specific `NoSuchElementException`/`NoAlertPresentException`.

### Retry policy declared but miswired; no known-issue/skip mechanism
`[Impact: Medium | Effort: Low]`

- The retry/rerun grep (`retries|rerunFailingTestsCount|flaky|@Retry|retryAnalyzer|retryCount`) shows **the intended policy is 3 automatic retries** (`testng.xml:8` `retryCount=3`; `RetryListener.java:13` `MAX_RETRY_COUNT = 3`). The team already expects flakiness: `DebugOrderExportTest.java:22` says "debugging flaky export button".
- The wiring is broken in three ways:
  1. `RetryListener` implements `IRetryAnalyzer` (`:10`), which isn't a TestNG listener interface. Registering it under `<listeners>` (`testng.xml:5`) doesn't attach it to any test. That needs `@Test(retryAnalyzer=…)` (0 hits) or an `IAnnotationTransformer` (0 hits). **(hypothesis)** Depending on TestNG 6.14.3's listener loading, the registration is either ignored or fails at suite start.
  2. The `retryCount` XML parameter is never read; the value is hardcoded.
  3. The class name says "Listener" for something that isn't one.
- If someone "fixes" the wiring as is, every failure gets silently re-run up to 3 times. Combined with no reporting (see "Failures can't be diagnosed from CI" below), flaky tests would turn green with no record of it.
- There's no skip-with-reason or known-issue mechanism: `SkipException`, `enabled = false`, `@Issue`/`@TmsLink` and `description=` all have 0 hits. A known, tracked failure reports the same way as a new one.

---

## Test design

### Three single-method tests each cover 11-13 unrelated features
`[Impact: High | Effort: Medium]`

- `FullAdminWorkflowTests`, `FullInvoiceBillingCycleTests` and `FullProductLifecycleTests` each have exactly 1 `@Test` method of about 140 lines (`:21-164`, `:20-162`, `:20-162`). They're split into 11, 13 and 13 numbered `// --- feature N ---` blocks covering login, registration, orders, invoices, products, dashboard and logout. That's 3 of the 7 classes in `tests/`.
- Every assertion is a hard `Assert.*` (0 `SoftAssert` hits), so a failure in feature 2 hides features 3-13 from the report.
- Every step depends on the previous step's leftover state: the created user or order, and the current page. The steps are dependent within the test, so one early UI hiccup takes out the whole scenario.
- Template: `CreateOrderTests.testCreateStandardOrder` (`:32-44`) shows the intended shape, one business action and one outcome check. Split the E2E flows into feature-scoped tests that use it as the model (without its static state; see "Tests depend on execution order through static fields and a shared browser" below).

### 6 of 20 tests assert nothing, and many of the remaining assertions can't fail
`[Impact: High | Effort: Low]`

- **Assertion-free `@Test` methods: 6 of 20.** `InvoiceLookupTests.testInvoiceGridLoadsWithoutError` (`:51-55`); all 3 in `ProductGridTests` (`:26`, `:36`, `:47`; the file has 0 `Assert` calls); both `wip` tests. `ProductGridTests.testSortProductGridByPrice` clicks a header and sleeps; it never checks the sort.
- **Discarded results:** `.isDisplayed()` is called and thrown away 3 times (`FullProductLifecycleTests.java:94`, `InvoiceLookupTests.java:54`, `ProductGridTests.java:52`).
- **Vacuous assertions:** 7 `Assert.assertNotNull(orderId)` checks on the result of `getConfirmationOrderId()`, which returns `WebElement.getText()` (`OrderCreatePage.java:69`) and so is never `null` (`CreateOrderTests.java:42,57,67,77`; `FullAdminWorkflowTests.java:99`; `FullInvoiceBillingCycleTests.java:51`; `InvoiceLookupTests.java:42`). A blank or error banner passes all 7.
- **Tautology:** `Assert.assertTrue(rows.size() >= 0, …)` (`FullProductLifecycleTests.java:87`) is always true.
- **Asserts test-internal state, not the app:** `RegisterUserTests.testDependsOnPreviouslyRegisteredEmail` (`:76-79`) asserts a static field the same class set at `:43`. `CreateOrderTests.testReuseOrderIdFromEarlierTest` (`:81-85`) asserts only its precondition, then types a note it never submits or verifies.
- **Weak proxy:** 6 assertions use `isPageLoaded()` (`document.readyState == "complete"`, `BasePage.java:214-216`) as the only check for content-specific claims (`FullAdminWorkflowTests.java:144,155`; `FullInvoiceBillingCycleTests.java:143,153`; `FullProductLifecycleTests.java:143,153`).

### Step comments promise checks the code never makes
`[Impact: High | Effort: Low]`

The E2E tests look readable only because of their comments, and **9 commented business checks have no matching assertion**:

| Location | Comment promises | Code actually checks |
|---|---|---|
| `FullAdminWorkflowTests.java:118-120` | "verify dashboard reflects the new order count" | welcome banner visible |
| `FullAdminWorkflowTests.java:122-130` | "log back in to verify audit trail persisted" | logs in again *without logging out first*; asserts welcome banner, with message "after logout" |
| `FullAdminWorkflowTests.java:132-134` | "re-open the order and confirm the status stuck" | name field is enabled; status never read |
| `FullAdminWorkflowTests.java:146-155` | "check the user grid still lists the modified user" | `isPageLoaded()` |
| `FullInvoiceBillingCycleTests.java:106-108` | "verify dashboard revenue widget updates" | welcome banner visible |
| `FullInvoiceBillingCycleTests.java:145-153` | "confirm the archived invoice no longer appears" | `dashboardPage.isPageLoaded()` on the invoices URL |
| `FullProductLifecycleTests.java:92-94` | "verify export completed" | result discarded |
| `FullProductLifecycleTests.java:111-120` | "check invoice was generated for the exported orders" | invoice grid container displayed |
| `FullProductLifecycleTests.java:145-153` | "confirm the archived product no longer appears" | `isPageLoaded()` |

Also **(hypothesis)**: `FullAdminWorkflowTests.java:107-108` navigates to the orders *list* and calls `orderModifyPage.verifyFieldIsEditableAndEnabled()` without opening the order it just created, so feature 5 may be editing whatever row-6 input exists, or failing.

No test uses `description=` or any report-grouping annotation (0 hits), so these comments are the only statement of business intent, and they're inaccurate.

### Tests depend on execution order through static fields and a shared browser
`[Impact: High | Effort: Medium]`

- `CreateOrderTests.orderIdFromFirstTest` is a `static` field (`:20`) written by test 1 (`:43`) and read by test 5 (`:82`). `RegisterUserTests.lastRegisteredEmail` is also `static` (`:20`), written at `:43` and read at `:77`. Both classes chain on `priority = 1..5` (10 methods), and test 5 in each fails with a misleading message if test 1 fails or runs alone.
- 4 classes share one browser per class through `@BeforeClass`. Each test starts on whatever page the previous test left. For example, `CreateOrderTests.testCreateOrderWithDiscountCode` (`:47`) starts on the post-submit page of test 1.
- Parallel execution isn't configured (`testng.xml` has no `parallel`/`thread-count`; grep: 0 hits), so parallel safety wasn't assessed. The static fields above would collide immediately if it were turned on.

### Hardcoded, non-unique test data and no cleanup
`[Impact: High | Effort: Medium]`

- **No uniqueness utility exists or is used** (grep for `currentTimeMillis|UUID|Random`: 0 hits; `DateFormatterUtil.formatTimestampForFilename` exists but is unused). Every entity has a literal name or email, for example `alice.nguyen@acmecorp.com` (`RegisterUserTests.java:37`) and `grace.kim@acmecorp.com` (`FullAdminWorkflowTests.java:49`). **(hypothesis)** If the app enforces unique emails, every rerun of `RegisterUserTests` and `FullAdminWorkflowTests` fails. With the intended retry=3, the retries would fail the same way.
- **Records created per full run, never deleted:** 7 orders (CreateOrder 4, FullAdmin 1, FullInvoice 1, InvoiceLookup 1), 5 users (RegisterUser 4, FullAdmin 1) and 1 product, 13 in total. The 4 `@AfterClass` methods only call `driver.quit()`, and there are 0 `@AfterMethod` hooks.
- The only "cleanup" is inline archiving at the end of 2 E2E tests (`FullInvoiceBillingCycleTests.java:124-127`, `FullProductLifecycleTests.java:124-127`), which runs only on the happy path.
- **Data-safety bug:** `FullProductLifecycleTests.java:124` archives the *first* `.product-row` in the grid, not the product the test created, so it can archive unrelated data. That matters more given the production-environment question in "`config.properties` is never read" above.

---

## Locators

### 21 of 84 locators are positional XPath or ExtJS auto-generated IDs
`[Impact: Medium | Effort: Medium]`

- **Distribution (repo-wide grep of `By.*(`):** `cssSelector` 37 (44%), `id` 24 (29%), `xpath` 12 (14%), `name` 11 (13%). There are 57 in page objects and 27 in tests.
- **All 12 XPaths are absolute-positional** (`//div[n]/div[n]/…/tr[n]/td[n]`). **9 of 24 IDs are ExtJS auto-generated** (`ext-comp-NNNN`: `DashboardPage.java:9`, `InvoiceModifyPage.java:13`, `OrderCreatePage.java:10`, `OrderHandler.java:15`, `OrderModifyPage.java:13`, `ProductModifyPage.java:13`, `UserModifyPage.java:13`, `UserRegisterPage.java:12,13`), and these renumber when the component tree changes.
- Individual verdicts:
  - `OrderModifyPage.java:12` (`…/tr[6]/td[2]/input`) and `UserModifyPage.java:12` (`…/tr[5]/td[2]/input`) are **bad**. Their sibling pages already prove that a stable ID exists for the same "name" field (`InvoiceModifyPage.java:12` `invoiceRefInput`, `ProductModifyPage.java:12` `productNameInput`).
  - `OrderCreatePage.java:8-9` and `UserRegisterPage.java:8-9` are **bad**. They use the *identical* XPath literals `//div[2]/div[1]/form/div[1]/input` and `…/div[2]/input` for different fields on different pages, while `name`/class-based locators sit a few lines below in the same files.
  - `UserManagement.java:12` is **bad**. "First result row" is hardcoded as `tr[2]/td[1]` with no text-based lookup, so a header-row change or a different sort breaks it silently.
  - `DashboardPage.java:8` (`//div[1]/div[1]/nav/ul/li[3]/a`) is **bad**. It's the third nav item by position (see "`openOrdersMenu()` is used to reach the user-registration form" below).
- **No scoped grid-row helper:** there's no "row containing text X" helper. Tests pick rows by index (`FullInvoiceBillingCycleTests.java:60`, `InvoiceLookupTests.java:45`, `FullProductLifecycleTests.java:108,124`), so in a shared environment they read or archive whatever row happens to be first.

---

## Diagnostics and reporting

### Failures can't be diagnosed from CI: no screenshots, no published report, no artifacts
`[Impact: High | Effort: Low]`

- There's no screenshot-on-failure. `ScreenshotUtil.capture` has 0 callers, there's no `ITestListener`/`onTestFailure` (0 hits), and `BasePage.takeScreenshotPathPlaceholder()` literally `return null;` (`:228-230`). Even if it were called, `ScreenshotUtil.java:19` writes to `target/screenshots/`, which nothing creates, so `Files.copy` would throw, and the catch at `:20` swallows that.
- CI only `cat`s the surefire `.txt` summaries, with `|| true` (`ci.yml:24-26`). There's no `actions/upload-artifact` (0 hits), so the surefire XML/HTML, `target/automation.log` (`BasePage.java:24`) and `results.csv` (`BasePage.java:187`, writer unused) all disappear with the runner.
- The run history isn't kept anywhere, so results can't be tracked over time.

### Report has no grouping by feature area
`[Impact: Low | Effort: Low]`

0 uses of TestNG `groups`/`description` or Allure `@Feature`/`@Story`/`@Epic` across all 9 test classes. The report is a flat list of 20 methods, and the 3 E2E methods each hide 11-13 features under one name. That's manageable at the current size, but it gets worse with every test added.

---

## Naming and coding standards

### `openOrdersMenu()` is used to reach the user-registration form
`[Impact: Medium | Effort: Low]`

`dashboardPage.openOrdersMenu()` is immediately followed by `userRegisterPage.enter…` at 4 call sites (`RegisterUserTests.java:34,48,84`; `FullAdminWorkflowTests.java:46`). Either the method is misnamed (it clicks the positional `li[3]` nav item, `DashboardPage.java:8`, which may not be Orders), or the registration tests navigate to the wrong screen and pass only because of the instant `isSuccessMessageShown` check. Both readings are defects. Which one applies depends on the live UI.

### Naming/style drift
`[Impact: Low | Effort: Low]`

**Baseline:** no explicit standard exists (0 hits for Checkstyle/Spotless/PMD/SpotBugs/`.editorconfig`; the README has no style section), so this is judged against idiomatic Java conventions.

- **Class suffix by role:** 8 of 10 page objects end in `Page`. The outliers are `OrderHandler` and `UserManagement`, both list/grid screens. All 7 classes in `tests/` end in `Tests`, and the 2 wip classes use the singular `Test`. That doesn't affect discovery, since `testng.xml` scans packages.
- **Test method names:** 18 of 20 use the `test…` prefix. The wip methods are `debugExportTimingIssue` and `tryLoginWithWeirdCharsInPassword`.
- **Names that misdescribe behaviour:**
  - `RetryListener` isn't a listener.
  - `isElementPresentNow` checks display, not presence, and swallows errors.
  - `verifyFieldIsEditableAndEnabled` only checks `isEnabled()`, and "Field" always means the name field.
  - `compareElementText` returns `true` on error.
  - `waitForPageLoadHack`/`waitForAjaxSpinnerHack` admit they're hacks.
  - `takeScreenshotPathPlaceholder` returns `null`.
  - `testRegisterUserMinimalProfile` registers a full profile.
- **Parameter names:** 9 parameters named `v` in `UserRegisterPage.java:24-58`.
- **Inline fully qualified names:** 3 (`BasePage.java:220,225`; `FullProductLifecycleTests.java:86`).
- **Constants:** the base URL appears as 33 literals with no constants class. The few constants that do exist (`LOG_FILE`, `MAX_RETRY_COUNT`, DB `URL/USER/PASSWORD`) are scattered across unrelated classes.
- **Package contents:** `utils/` holds a DB client and an SMTP client, which are integration adapters rather than utilities, and 4 of its 5 classes are unused.

---

## Dependencies and repo hygiene

### Core stack is 2018-era: Selenium 3.141.59, TestNG 6.14.3, Java 8
`[Impact: Medium | Effort: Medium]`

`pom.xml:13-17,34` and `ci.yml:15-19`. This explains several of the findings above:

- Selenium 3 has no Selenium Manager, so CI depends on a preinstalled chromedriver matching the runner's Chrome.
- It uses the deprecated `WebDriverWait(driver, int)` API (`BasePage.java:56,61`).
- It has no relative locators.
- Java 8 blocks `var`/records-based builders and current TestNG 7.x.

Plugin and dependency version properties are named correctly (`selenium.version`, `testng.version`). Only currency is the issue.

### No `.gitignore`
`[Impact: Low | Effort: Low]`

The repo root has no `.gitignore` (`find -name .gitignore`: 0 results). The framework writes `target/automation.log` (`BasePage.java:24`), `target/results.csv` (`:187`) and `target/screenshots/` (`ScreenshotUtil.java:19`), all of which could be committed by accident. No generated artifacts are committed yet (0 `.png`/`.html`/`.log`/`.csv`/`target` files found).

---

## FIRST principles table

| Principle | Verdict | Evidence |
|---|---|---|
| **Fast** | Fails | 38 `Thread.sleep` (39.8 s inline in the 3 E2E tests alone, plus per-action page sleeps of 1-4 s); 9 separate browser launches; every UI precondition (login, order) built through the UI. |
| **Independent** | Fails | Static cross-test state in `CreateOrderTests:20` and `RegisterUserTests:20`; 10 methods chained by `priority`; shared per-class browser in 4 classes; 3 E2E tests with 11-13 dependent steps each. Parallel execution isn't configured, so it wasn't assessed. |
| **Repeatable** | Fails | 0 uniqueness helpers, so literal emails and names are reused every run; 13 records created per run and never cleaned up; environment hardcoded in 33 URL literals; 12 assertions depend on render timing through instant checks. No hardcoded dates found. |
| **Self-validating** | Fails | 6 of 20 `@Test` methods have no assertion; 7 vacuous `assertNotNull` on `getText()`; 1 tautology; 3 discarded `isDisplayed()` results; 9 commented checks with no assertion; `compareElementText` returns `true` on error. |
| **Timely** | N/A statically | Can't be judged from code. Related: there's no tagging, so CI runs the full suite on every push and PR (see "No test tagging" above). |

---

## Recommended actions, in priority order

Rollup of the tags above, sorted by Impact (High → Low), then Effort (Low → High).

**High impact / Low effort**
1. Fix the build. Delete the unused `EmailSenderUtil` (or add JavaMail). Run Chrome headless in CI and confirm with a green run. (*The project cannot compile*)
2. Move every credential out of source and `config.properties` into CI secrets and environment variables, then rotate `Admin123!` and `Sup3rSecret!`. (*Plaintext credentials*)
3. Replace `isElementPresentNow` in the 3 page predicates with the existing `waitUntilDisplayed`, and use a wait-for-absence for the error banner. (*Instant presence checks*)
4. Add real assertions to the 6 assertion-free tests. Replace the 7 `assertNotNull(getText())` with an ID-format check, and remove the tautology and the discarded `isDisplayed()` calls. (*Assertion-free/vacuous tests*)
5. Make each step comment true: assert the order count, status, grid row and archived-absent claims, or delete the comment. (*Step comments promise checks*)
6. Add an `ITestListener` that captures a screenshot and page source on failure, and upload `target/surefire-reports`, the screenshots and logs with `actions/upload-artifact`. (*Failures can't be diagnosed from CI*)

**High impact / Medium effort**

7. Load `config.properties`, with environment overrides, through one `Config` class. Replace the 33 URL literals, honour `browser`, and get an explicit answer on whether `crm-admin.acmecorp.com` is production. (*`config.properties` is never read*)
8. Introduce a `BaseTest` plus a `DriverFactory` (config-driven browser, headless flag, `@AfterMethod(alwaysRun=true)` quit) and remove the 9 copies of driver setup. (*No driver/fixture layer*)
9. Move every raw `driver.findElement` in tests (27 calls, 4 classes) into page objects, deduplicate the shared locators, and make `*ModifyPage.enterName` use `type()`. (*Tests bypass page objects*)
10. Split `BasePage` into a small interaction core plus separate wait, popup and logging collaborators, and delete the 24 uncalled methods. (*God base class*)
11. Replace all 38 `Thread.sleep` calls with condition waits centralized in the page layer, and restore the interrupt flag anywhere a sleep has to stay. (*38 hardcoded sleeps*)
12. Make catches rethrow with context. In particular, make `compareElementText` and `isElementPresentNow` stop returning a value that looks like success on error, and settle on one failure idiom instead of `null`/`-1`/`false`/`true`. (*All 49 catch blocks swallow*)
13. Split the 3 E2E mega-tests into feature-scoped tests modelled on `CreateOrderTests.testCreateStandardOrder`. Use `SoftAssert` only where several checks on one screen belong together. (*Three single-method tests*)
14. Remove the static cross-test fields and `priority` chains. Each test should create or look up its own data, and use `@BeforeMethod` navigation so every test starts from a known page. (*Tests depend on execution order*)
15. Add a unique-suffix data generator and `@AfterMethod(alwaysRun=true)` cleanup, ideally via API, and fix `FullProductLifecycleTests:124` so it archives the product it created. (*Hardcoded, non-unique test data*)

**High impact / High effort**

16. Introduce a business-step layer (`OrderSteps.createOrder(order)`, `UserSteps.register(user)`, `AuthSteps.loginAs(user)`) and migrate the 6 order-creation and 4 registration call sites. (*Missing business-step layer*)

**Medium impact / Low effort**

17. Point `DbConnector` at a configurable test database, switch to `PreparedStatement` with try-with-resources, or delete it, since it has 0 callers. (*Production database and string-built SQL*)
18. Make page actions return the next page object. Return typed rows or values instead of `WebElement`, and move `verify*`/`assert*` out of page objects into tests or assertion helpers. (*Page objects leak `WebElement`*)
19. Delete the 4 unused `utils/` classes or wire them in deliberately (`ScreenshotUtil` would be wired by action 6). (*Unused utility classes*)
20. Route every admin login through one `User`/credentials object loaded from config. (*Admin user represented three ways*)
21. Decide on retries explicitly. Either remove `RetryListener`, or wire it through an `IAnnotationTransformer` that reads `retryCount` and logs every retry. Add a skip-with-ticket mechanism for known failures. (*Retry policy miswired*)
22. Remove `com.acme.crm.wip` from `testng.xml` and delete or finish the 2 scratch classes. (*Scratch/WIP tests in CI*)
23. Add `groups` (`smoke`/`regression`). Run smoke on PRs and the full suite on merge or nightly, and drop the duplicate push+PR trigger. (*No test tagging*)
24. Confirm what `li[3]` actually opens, and rename `openOrdersMenu` or fix the registration navigation. (*`openOrdersMenu()` used for registration*)

**Medium impact / Medium effort**

25. Collapse the 4 `*ModifyPage` classes into one parametrized form component. (*Four near-identical `*ModifyPage`*)
26. Replace `createOrderInline`/`registerInline` with `Order`/`User` builders, and fix the unused `state` parameter and the misleading "Minimal" test. (*No test-data builders*)
27. Replace the 12 positional XPaths and 9 `ext-comp-*` IDs with the stable `id`/`name`/class hooks the sibling pages already use, and add a scoped "row containing text" grid helper. (*21 of 84 fragile locators*)
28. Upgrade to Selenium 4 / TestNG 7 / Java 11+. This also unlocks Selenium Manager for CI and `Duration`-based waits. (*2018-era core stack*)

**Medium impact / High effort**

29. Seed preconditions (login session, prerequisite orders) through the API instead of the UI, if the team's strategy supports it. Confirm against the questionnaire. (*Every precondition is built through the UI*)

**Low impact / Low effort**

30. Add feature-area `groups`/`description` to tests for report navigability. (*Report has no grouping*)
31. Fix the naming drift: rename `RetryListener`, `isElementPresentNow`, `verifyFieldIsEditableAndEnabled` and the `*Handler`/`*Management` page objects, replace the `v` parameters, and add a Checkstyle gate. (*Naming/style drift*)
32. Add a `.gitignore` covering `target/` and IDE files. (*No `.gitignore`*)

---

## Checklist tab input

These are only the rows this code review can answer. Rows left out are either for the questionnaire interview (all of Tools, Strategy and AI Usage; Running: remote execution and run time; Processes: coverage, PR review, meaningfulness to QA) or not applicable. "Tests remain independent under parallel execution" is left out because `testng.xml` doesn't configure parallel execution (0 `parallel`/`thread-count` hits). All paths are relative to the framework root; see `review.md` for full evidence.

| Section | Check | Status (+/-) | Comments |
|---|---|---|---|
| Framework | Framework is consistent | - | Selenium wrappers are used in some places and bypassed in others: 4 `*ModifyPage.enterName` re-implement `type()`, and tests make 27 raw `driver.findElement` calls. Failure idioms are mixed (`null`/`-1`/`false`/`true`, `DbConnector.java:26,39`, `BasePage.java:73,171`), and verification mixes `Assert.*` with `throw new AssertionError` (4 pages). |
| Framework | Framework follows a layered architecture | - | There's no step/flow layer: order creation is composed at 6 sites in 4 files. 4 of 9 test classes import `By`/`WebElement`. Page objects return `WebElement` (`OrderHandler.java:35`, `UserManagement.java:28`) and assert internally (4 `verify*`, `BasePage.java:147-158`, `org.testng.Assert` in `src/main`). |
| Framework | Framework complies with DRY | - | 4 `*ModifyPage` classes share 6 identical methods; there are 9 copies of driver setup and 33 base-URL literals. The admin login is expressed 3 ways (`loginAsAdmin`, inline literals, unused config), and positional 10-11-arg helpers stand in for builders. |
| Framework | Framework complies with KISS | - | God base class `BasePage` (231 lines, 32 public methods, 9 concerns; self-described at `BasePage.java:17-19`) is inherited by all 10 page classes. |
| Framework | Framework complies with YAGNI | - | 24 of 32 `BasePage` public methods and 4 of 5 `utils/` classes (`DbConnector`, `EmailSenderUtil`, `ScreenshotUtil`, `DateFormatterUtil`) have 0 callers repo-wide. |
| Framework | Framework complies with SOLID | - | SRP/ISP: `BasePage` God class. OCP/DIP: `new ChromeDriver()` is hardcoded in 9 classes with no factory, and the `browser` config is ignored. DIP: Selenium is sometimes wrapped, sometimes not. LSP: clean (0 overrides). |
| Framework | Framework complies with language standards | - | Judged against idiomatic Java (no linter config found). 2 of 10 page objects lack the `Page` suffix; 9 params are named `v`. Misleading names include `RetryListener`, `isElementPresentNow`, `compareElementText` and `openOrdersMenu` (used 4× to reach registration). |
| Framework | Presetups are implemented at the optimal available level | - | All presetup goes through the UI: login form in 9 of 9 classes, and the invoice tests create orders via the UI form (`FullInvoiceBillingCycleTests.java:40-48`). `apiUrl` is configured but there's no API client. Confirm the "optimal" judgment against the questionnaire. |
| Framework | Unconditional waits are not a common practice | - | 38 `Thread.sleep` in 10 files (8 in page objects, 30 in tests); 0 condition-wait call sites, since `waitUntilDisplayed`/`waitUntilClickable` are unused, and no implicit wait. |
| Framework | Tests are atomic and independent | - | Static cross-test state (`CreateOrderTests.java:20`, `RegisterUserTests.java:20`) with `priority` chains; 3 single-method E2E tests with 11-13 dependent features each; 13 literal-named records created per run with 0 cleanup. |
| Framework | Test implementation is done at the optimal level (API, UI...) | - | UI is used for setup that's only a precondition (orders created via UI to test invoices), and the DB helper is unused. Only partly verifiable from code; needs the questionnaire's stated strategy to complete. |
| Framework | Core libraries/framework/language versions are reasonably current | - | Selenium 3.141.59, TestNG 6.14.3, Java 8 (`pom.xml:13-17`, `ci.yml:19`). No Selenium Manager, deprecated `WebDriverWait(int)`. |
| Framework | No hardcoded credentials/secrets in the test codebase | - | 9 password literals in 7 files, including the prod DB password at `DbConnector.java:17` and `config.properties:4,9`. `DbConnector` also targets `crm_production` with string-concatenated SQL (`:32`), and `config.properties` is never read. |
| Running | Steps have a sufficient level of documentation for reporting | - | 0 `description`/`groups`/Allure annotations. 9 step comments in the E2E tests claim checks the code never makes (e.g. `FullAdminWorkflowTests.java:118-120`). |
| Running | When tests fail, there are mechanisms to easily find the cause | - | No screenshot-on-failure (`ScreenshotUtil` has 0 callers; `takeScreenshotPathPlaceholder` returns `null`). CI only `cat`s the surefire `.txt` files (`ci.yml:24-26`) and uploads no artifacts. |
| Running | Test stability is at a sufficient level | - | The intended 3× retry (`testng.xml:8`) and a "flaky export button" note (`DebugOrderExportTest.java:22`) show known instability. Other signals: 38 sleeps, 12 assertions on instant checks, and 21 of 84 locators positional XPath or `ext-comp-*` IDs. No retry is not proof of stability. |
| Running | There is a way to track run results over time | - | No published or uploaded report (0 `upload-artifact`); the `results.csv` writer is unused. |
| Running | Tests are integrated into CI/CD, not run purely manually/on-demand | - | CI is wired on every push and PR (`ci.yml:3-7`), but the build should fail at compile because `javax.mail` isn't declared for `EmailSenderUtil`. Chrome isn't headless (hypothesis: won't launch on the runner), there's no smoke/full split, and the `wip` package runs too. |
| Processes | Tests are properly documented | - | 6 of 20 tests have no assertion and 7 more assertions are vacuous `assertNotNull(getText())`. Test names and comments misstate behaviour (`testRegisterUserMinimalProfile` sends a full profile), and `README.md:18` says config comes from a file that's never read. |
| Processes | A failure-handling strategy is implemented (bug reporting → flaky rerun → failure skipping) | - | Retry is declared but miswired (`RetryListener` is an `IRetryAnalyzer` registered as a listener; 0 `retryAnalyzer` uses). There's no skip/known-issue mechanism (0 `SkipException`/`enabled=false`/`@Issue`), and all 49 catch blocks swallow. Corroborate against the questionnaire's stated process. |
