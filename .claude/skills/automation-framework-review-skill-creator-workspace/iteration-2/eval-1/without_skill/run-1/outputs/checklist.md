# Checklist Tab: crm-admin-ui-tests Framework Review

Generated from the review in `review.md` (2026-10-09). Status values: Yes = met, Partial = partly met, No = not met. Columns use a generic layout because the team spreadsheet template was not provided; rename them to match your sheet if needed.

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
