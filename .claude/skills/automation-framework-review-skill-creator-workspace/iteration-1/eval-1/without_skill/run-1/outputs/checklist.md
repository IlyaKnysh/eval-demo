# Checklist Tab — CRM Admin UI Tests Framework Review

Source review: `review.md` (same output directory). 34 findings total.

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

## Severity counts

- Critical: 6
- High: 11
- Medium: 12
- Low: 3
- **Total: 34**
