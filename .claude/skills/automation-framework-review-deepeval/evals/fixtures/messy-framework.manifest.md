# messy-framework fixture — seeded defect manifest (ground truth)

Fixture root: `.claude/skills/automation-framework-review-deepeval/evals/fixtures/messy-framework/`

All paths below are relative to that root. This is the ground truth for
grading the automation-framework-review -deepeval skill's output against this
fixture. 28 files total. Line numbers reflect the final on-disk state of
the fixture and were re-verified after creation.

---

## 1. God Base Class (SRP violation)

`src/main/java/com/acme/crm/pages/BasePage.java` — 231 lines. Every page
object (`UserModifyPage`, `OrderModifyPage`, `ProductModifyPage`,
`InvoiceModifyPage`, `LoginPage`, `DashboardPage`, `OrderCreatePage`,
`UserRegisterPage`, `UserManagement`, `OrderHandler`) extends it. Bundles
navigation (lines 32-51), wait helpers (55-75), raw element accessors and
generic interaction (79-99), hardcoded-sleep helpers (103-115), popup
handling (119-143), assertions incl. a comparison utility (147-172),
logging/data I/O (176-192), and misc JS/frame/dropdown/hover utilities
(196-230) — 8+ unrelated responsibilities in one class.

## 2. Missing business-step/flow layer

No `steps`/`flows` package exists anywhere in the fixture. At least 5 test
methods each inline the same ~5-6 step "create order" / "register user"
sequence directly via page-object calls instead of a shared step method:

- `src/test/java/com/acme/crm/tests/CreateOrderTests.java:34-39` — `testCreateStandardOrder`
- `src/test/java/com/acme/crm/tests/CreateOrderTests.java:48-54` — `testCreateOrderWithDiscountCode`
- `src/test/java/com/acme/crm/tests/RegisterUserTests.java:34-40` — `testRegisterSalesUser`
- `src/test/java/com/acme/crm/tests/RegisterUserTests.java:48-54` — `testRegisterSupportUser`
- `src/test/java/com/acme/crm/tests/InvoiceLookupTests.java:34-39` — `testCreateOrderThenLookUpInvoice` (5th occurrence)

## 3. Layer-boundary leakage

Test files that import `org.openqa.selenium.WebDriver`/`WebElement` and
call `driver.findElement(...)` directly instead of going through a page
object (4 files, exceeds the required 2):

- `src/test/java/com/acme/crm/tests/ProductGridTests.java` — imports lines 5-6; raw calls lines 28, 31, 38, 49, 51 (3 of 3 test methods use raw Selenium)
- `src/test/java/com/acme/crm/tests/InvoiceLookupTests.java` — imports lines 7-8; raw calls lines 45, 53
- `src/test/java/com/acme/crm/tests/FullProductLifecycleTests.java` — imports lines 7-8; raw calls throughout the single test method
- `src/test/java/com/acme/crm/tests/FullInvoiceBillingCycleTests.java` — imports lines 7-8; raw calls throughout the single test method

## 4. Raw type leakage from domain layer

Public page-object methods returning raw `WebElement` / `List<WebElement>`:

- `src/main/java/com/acme/crm/pages/BasePage.java:79` — `public WebElement getRawElement(By locator)`
- `src/main/java/com/acme/crm/pages/BasePage.java:83` — `public List<WebElement> getRawElements(By locator)`
- `src/main/java/com/acme/crm/pages/UserManagement.java:28` — `public WebElement getFirstResultRow()`
- `src/main/java/com/acme/crm/pages/OrderHandler.java:35` — `public List<WebElement> getAllOrderRows()`

## 5. Cross-file sibling duplication

Four page objects following the identical "Modify" role pattern, each with
the same 6 method names/signatures and near-identical bodies (differing
only by locator/label). Line numbers are identical across all 4 files:

| Method | Line (all 4 files) |
|---|---|
| `verifyFieldIsEditableAndEnabled()` | 22 |
| `enterName(String)` | 29 |
| `selectStatus(String)` | 35 |
| `enterEmail(String)` | 39 |
| `clickSave()` | 43 |
| `toggleActive()` | 47 |

Files: `src/main/java/com/acme/crm/pages/UserModifyPage.java`,
`OrderModifyPage.java`, `ProductModifyPage.java`, `InvoiceModifyPage.java`
(each 50 lines). 24 near-identical method bodies total, genuinely
diffable/greppable with `diff UserModifyPage.java OrderModifyPage.java`.

## 6. No test-data builder

Giant inline literal calls with 10+ raw args, no builder/factory, repeated
with only minor value changes:

- `src/test/java/com/acme/crm/tests/CreateOrderTests.java:62-64` — `testCreateOrderFullDetails` calls `createOrderInline(...)` with 11 raw string args
- `src/test/java/com/acme/crm/tests/CreateOrderTests.java:72-74` — `testCreateOrderNoDiscount` calls `createOrderInline(...)` with 11 raw string args (near-duplicate)
- `src/test/java/com/acme/crm/tests/RegisterUserTests.java:61-62` — `testRegisterUserFullProfile` calls `registerInline(...)` with 10 raw string args
- `src/test/java/com/acme/crm/tests/RegisterUserTests.java:69-70` — `testRegisterUserMinimalProfile` calls `registerInline(...)` with 10 raw string args (near-duplicate)

The `createOrderInline` (`CreateOrderTests.java:88-102`) / `registerInline`
(`RegisterUserTests.java:81-95`) helpers are plain parameter pass-throughs,
not real builders.

## 7. Hardcoded sleeps

38 occurrences of `Thread.sleep(...)` across 10 files (exceeds required 8
across 4 files):

- `src/main/java/com/acme/crm/pages/BasePage.java` — 2 (lines 105, 112)
- `src/main/java/com/acme/crm/pages/DashboardPage.java` — 1 (line 19)
- `src/main/java/com/acme/crm/pages/LoginPage.java` — 2 (lines 22, 35)
- `src/main/java/com/acme/crm/pages/OrderCreatePage.java` — 1 (line 63)
- `src/main/java/com/acme/crm/pages/OrderHandler.java` — 1 (line 29)
- `src/main/java/com/acme/crm/pages/UserRegisterPage.java` — 1 (line 63)
- `src/test/java/com/acme/crm/tests/ProductGridTests.java` — 1 (line 41)
- `src/test/java/com/acme/crm/tests/FullAdminWorkflowTests.java` — 9 (lines 39, 60, 69, 82, 102, 114, 126, 137, 151)
- `src/test/java/com/acme/crm/tests/FullInvoiceBillingCycleTests.java` — 10 (lines 35, 54, 65, 78, 88, 102, 116, 130, 139, 149)
- `src/test/java/com/acme/crm/tests/FullProductLifecycleTests.java` — 10 (lines 35, 44, 61, 73, 82, 104, 116, 130, 139, 149)

Durations vary: 800, 900, 1000, 1200, 1500, 1800, 2000, 2500, 3000, 4000 (ms).

## 8. Mixed raw vs retrying waits

`src/main/java/com/acme/crm/pages/BasePage.java`:
- Line 55-58: `waitUntilDisplayed(By, int)` — proper `WebDriverWait` + `ExpectedConditions.visibilityOfElementLocated` retrying helper.
- Line 60-63: `waitUntilClickable(By, int)` — same pattern, retrying.
- Line 69-75: `isElementPresentNow(By)` — raw, non-retrying instant check (`driver.findElement(locator).isDisplayed()` in a try/catch returning boolean). Used elsewhere in the same domain layer as a substitute for a real wait: `LoginPage.isErrorBannerShown()` (`LoginPage.java:27-29`) and `DashboardPage.isWelcomeBannerVisible()` (`DashboardPage.java:24-25`) and `UserRegisterPage.isSuccessMessageShown()` (`UserRegisterPage.java:68-69`).

## 9. Fragile locators

55 total `By` locator field declarations across
`src/main/java/com/acme/crm/pages/*.java` (verifiable via
`grep -rn "private final By " src/main/java/com/acme/crm/pages`). Distribution:

- **Positional/auto-generated (xpath or `ext-comp-*` IDs): 17/55 ≈ 31%** — e.g. `UserModifyPage.java:12` (`By.xpath("//div[3]/div[2]/table/tbody/tr[5]/td[2]/input")`), `UserModifyPage.java:13` (`By.id("ext-comp-1023")`), `OrderModifyPage.java:12-13`, `DashboardPage.java:8-9`, `OrderCreatePage.java:8-10`, `UserManagement.java:12`, `OrderHandler.java:15`, `ProductModifyPage.java:13`, `InvoiceModifyPage.java:13`, `UserRegisterPage.java:8-9,12-13`.
- **ID/name-based (stable): 17/55 ≈ 31%** — e.g. `LoginPage.java:8-10`, `ProductModifyPage.java:12,14`, `InvoiceModifyPage.java:12,14`, `OrderModifyPage.java:14`, `OrderCreatePage.java:11-14,18`, `UserModifyPage.java:14`, `UserManagement.java:13`, `UserRegisterPage.java:10-11`.
- **CSS class-based: 21/55 ≈ 38%** — e.g. `LoginPage.java:11`, all four `*ModifyPage` `saveButton`/`activeCheckbox` fields (lines 15-16 in each), `OrderCreatePage.java:15-17`, `OrderHandler.java:14,16`, `UserManagement.java:14`, `UserRegisterPage.java:14-18`, `DashboardPage.java:10`.

## 10. Test independence violations

- `src/test/java/com/acme/crm/tests/CreateOrderTests.java:20` — `static String orderIdFromFirstTest;` set in `testCreateStandardOrder` (line 43) and consumed in `testReuseOrderIdFromEarlierTest` (lines 80-85), an explicit `priority`-ordered dependency.
- `src/test/java/com/acme/crm/tests/RegisterUserTests.java:20` — `static String lastRegisteredEmail;` set in `testRegisterSalesUser` (line 43) and consumed in `testDependsOnPreviouslyRegisteredEmail` (lines 75-79).

## 11. Tests with no assertions

- `src/test/java/com/acme/crm/tests/ProductGridTests.java:25-33` — `testOpenProductGridAndFilter` (no `Assert.*` call)
- `src/test/java/com/acme/crm/tests/ProductGridTests.java:35-44` — `testSortProductGridByPrice` (no `Assert.*` call)
- `src/test/java/com/acme/crm/tests/ProductGridTests.java:46-53` — `testExpandProductDetailsPanel` (calls `.isDisplayed()` at line 52 but discards the result)
- `src/test/java/com/acme/crm/tests/InvoiceLookupTests.java:50-55` — `testInvoiceGridLoadsWithoutError` (calls `.isDisplayed()` at line 54 but discards the result)

4 no-assertion test methods total (exceeds required 3).

## 12. Giant multi-feature test methods

Three test classes, each with exactly **one** `@Test` method, 150+ lines,
covering multiple unrelated features in sequence:

- `src/test/java/com/acme/crm/tests/FullAdminWorkflowTests.java` — 165 lines, `testFullAdminWorkflowEndToEnd` (line 22) covers login, user registration, user search+modify, order creation, order modify, dashboard reload, re-login, order re-check, dashboard refresh, user-grid re-check, logout (11 "feature" blocks).
- `src/test/java/com/acme/crm/tests/FullProductLifecycleTests.java` — 163 lines, `testFullProductLifecycleEndToEnd` (line 21) covers login, nav, product creation, product modify, order filter/export, invoice check, product search, archive, dashboard re-check, logout (13 feature blocks).
- `src/test/java/com/acme/crm/tests/FullInvoiceBillingCycleTests.java` — 163 lines, `testFullInvoiceBillingCycleEndToEnd` (line 21) covers login, order creation, invoice lookup, invoice edit, mark-paid, payment toast check, order status check, dashboard check, email send, archive, dashboard re-check, logout (13 feature blocks).

## 13. Empty catch blocks

37 structurally-empty catch blocks (catch clause with no statements in its
body) across 9 files (exceeds required 3):

- `src/main/java/com/acme/crm/pages/BasePage.java` — 3 (lines 106-107, 113-114, 169-170)
- `src/main/java/com/acme/crm/pages/DashboardPage.java` — 1 (lines 20-21)
- `src/main/java/com/acme/crm/pages/LoginPage.java` — 2 (lines 23-24, 36-37)
- `src/main/java/com/acme/crm/pages/OrderCreatePage.java` — 1 (lines 64-65)
- `src/main/java/com/acme/crm/pages/UserRegisterPage.java` — 1 (lines 64-65)
- `src/test/java/com/acme/crm/tests/ProductGridTests.java` — 1 (lines 42-43)
- `src/test/java/com/acme/crm/tests/FullAdminWorkflowTests.java` — 8
- `src/test/java/com/acme/crm/tests/FullInvoiceBillingCycleTests.java` — 10
- `src/test/java/com/acme/crm/tests/FullProductLifecycleTests.java` — 10

Notably: `src/main/java/com/acme/crm/pages/BasePage.java:160-171` —
`compareElementText(By, By)`, a **verification/comparison utility**: its
catch block (lines 169-170) is completely empty and the method falls
through to `return true` on any exception (e.g.
`StaleElementReferenceException`), masking a real failure as a false
"match" instead of surfacing it.

## 14. Nonzero CI retry count

- `testng.xml:4-6` — `<listener class-name="com.acme.crm.utils.RetryListener" />`
- `testng.xml:8` — `<parameter name="retryCount" value="3" />`
- `src/main/java/com/acme/crm/utils/RetryListener.java` — `IRetryAnalyzer` implementation with `MAX_RETRY_COUNT = 3`, retrying any failed test up to 3 times before reporting failure.

## 15. Scratch/WIP code in the tree

`src/test/java/com/acme/crm/wip/` package, **not excluded** from
`testng.xml`'s scan (`testng.xml:13` explicitly includes
`<package name="com.acme.crm.wip" />` alongside the real `com.acme.crm.tests` package):

- `src/test/java/com/acme/crm/wip/ScratchLoginExperimentTest.java` — leftover draft test, `TODO: delete this or move it somewhere real - Dave, 2024` (line 9)
- `src/test/java/com/acme/crm/wip/DebugOrderExportTest.java` — leftover debug test for a "flaky export button" (line 10, 22)

## 16. No smoke/regression tagging

- No `groups = {...}` attribute appears in any `@Test` annotation anywhere in the codebase (verified repo-wide).
- `testng.xml` has no `<groups>` element.
- `.github/workflows/ci.yml:3-7` — triggers on every push/PR to any branch (`branches: [ "**" ]`); `.github/workflows/ci.yml:21-22` runs `mvn -B clean test` (the entire suite) unconditionally — no fast/smoke subset selection exists anywhere.

## 17. Naming convention violations + utils dumping ground

Outliers among `*Page`-suffixed classes:
- `src/main/java/com/acme/crm/pages/UserManagement.java` — handles the User grid screen but doesn't end in `Page`.
- `src/main/java/com/acme/crm/pages/OrderHandler.java` — handles the Order grid screen but doesn't end in `Page`.

(13 of 15 classes in the `pages` package correctly end in `Page`; these 2 are the deliberate outliers.)

`utils` dumping-ground package (`src/main/java/com/acme/crm/utils/`) — 5 unrelated helpers with no cohesive theme:
- `DateFormatterUtil.java` — date/timestamp formatting
- `DbConnector.java` — raw JDBC connection/query helper (lines 15-17 hardcode prod DB credentials, see #19)
- `ScreenshotUtil.java` — screenshot capture (never wired to any failure listener, see #18)
- `EmailSenderUtil.java` — SMTP notification email sender
- `RetryListener.java` — TestNG retry-analyzer logic (5th unrelated concern in the same package)

## 18. No failure diagnostics

- `testng.xml` — bare suite definition; the only listener configured is the retry listener (#14), nothing for screenshots/reporting.
- `pom.xml:38-50` — only `maven-surefire-plugin` is configured; no Allure, no Extent Reports, no HTML/trace reporting plugin.
- `.github/workflows/ci.yml:21-26` — CI just runs `mvn -B clean test` and `cat`s the raw surefire `.txt` output; no artifact upload, no screenshot-on-failure step, no trace capture.
- `src/main/java/com/acme/crm/utils/ScreenshotUtil.java` exists (a `capture(WebDriver, String)` method) but is never invoked from any test, listener, or `@AfterMethod` anywhere in the fixture — the capability exists but isn't wired in.
- No `@Tag`/`@Feature`-equivalent grouping annotations anywhere (see also #16 re: `groups`).

## 19. Hardcoded environment values

`src/test/resources/config.properties`:
- Line 1 — `baseUrl=https://crm-admin.acmecorp.com` (plaintext production-looking URL)
- Line 4 — `adminPassword=Admin123!` (plaintext placeholder-style fake credential)
- Line 5 — `dbHost=prod-crm-db.acmecorp.internal`
- Line 9 — `dbPassword=Sup3rSecret!` (plaintext fake credential)

No profile/env-switching mechanism (no `-Denv=` property, no Maven
profiles, no per-environment resource files) anywhere in `pom.xml` or
`src/test/resources`.

Same credentials duplicated in
`src/main/java/com/acme/crm/utils/DbConnector.java:15-17` (`URL`, `USER`,
`PASSWORD` constants) and hardcoded as literals in test/page code, e.g.
`LoginPage.java:32` (`login("admin@acmecorp.com", "Admin123!")`),
`FullAdminWorkflowTests.java:35`, `FullProductLifecycleTests.java:31`,
`FullInvoiceBillingCycleTests.java:31`.

## 20. Outdated dependency

`pom.xml:16` — `<selenium.version>3.141.59</selenium.version>`, consumed at
`pom.xml:24`. This version predates Selenium 4's relative locators
(`RelativeLocator`) and W3C-standard actionability checks.

---

### Summary counts

| # | Defect | Count |
|---|---|---|
| 1 | God base class | 1 class, 231 lines |
| 2 | Missing steps/flow layer, inline sequences | 5 test methods |
| 3 | Layer-boundary leakage | 4 test files bypass page objects with raw Selenium |
| 4 | Raw type leakage | 4 methods |
| 5 | Cross-file sibling duplication | 4 classes x 6 methods = 24 duplicated methods |
| 6 | No test-data builder | 4 giant inline calls (10-11 args each) |
| 7 | Hardcoded sleeps | 38 occurrences across 10 files |
| 8 | Mixed raw vs retrying waits | 1 file (BasePage.java): 2 retrying helpers + 1 raw helper reused in 3 other page objects |
| 9 | Fragile locators | 55 total: 17 positional (31%) / 17 id-name (31%) / 21 css (38%) |
| 10 | Test independence violations | 2 static fields / order dependencies |
| 11 | Tests with no assertions | 4 test methods |
| 12 | Giant multi-feature test methods | 3 classes, 163-165 lines each, 1 @Test method each |
| 13 | Empty catch blocks | 37 instances across 9 files, incl. 1 in a comparison utility |
| 14 | Nonzero CI retry count | retryCount=3 in testng.xml + RetryListener |
| 15 | Scratch/WIP code in tree | 2 files in wip package, included in testng.xml scan |
| 16 | No smoke/regression tagging | 0 groups usages; CI runs full suite on every trigger |
| 17 | Naming violations + utils dumping ground | 2 outlier classes + 5-helper mixed utils package |
| 18 | No failure diagnostics | no screenshot/Allure/trace wiring anywhere |
| 19 | Hardcoded environment values | config.properties + DbConnector.java, no env switching |
| 20 | Outdated dependency | Selenium 3.141.59 |
