# Transcript — Manual Review of messy-framework (no skill used)

## Task

Review the Java/TestNG/Selenium test automation framework at:
`.claude/skills/automation-framework-review-deepeval/evals/fixtures/messy-framework`
(relative to repo root `C:\Users\knysh\source\repos\evals-demo`)

Constraint: use only general senior-engineer judgment — explicitly do NOT use any
"automation-framework-review" skill or checklist. Produce a full issues list and a
checklist-tab table, saved to `review.md` and `checklist.md` respectively, in:
`.claude/skills/automation-framework-review-skill-creator-workspace/iteration-1/messy-java-full-review/without_skill/outputs/`

Read-only task: nothing under `evals/fixtures/messy-framework` was modified.

## Process

1. **Enumerated the repo.** Listed all files (excluding `target/` and `.git/`) via a
   `find` command to get the full inventory before reading anything:
   - `.github/workflows/ci.yml`, `README.md`, `pom.xml`, `testng.xml`
   - `src/main/java/com/acme/crm/pages/*.java` (10 page objects incl. `BasePage`)
   - `src/main/java/com/acme/crm/utils/*.java` (5 utility classes)
   - `src/test/java/com/acme/crm/tests/*.java` (7 test classes)
   - `src/test/java/com/acme/crm/wip/*.java` (2 scratch/debug test classes)
   - `src/test/resources/config.properties`

2. **Read project metadata first**: `README.md`, `pom.xml`, `testng.xml`,
   `.github/workflows/ci.yml`, `config.properties`. Immediately found hardcoded
   production credentials and a production DB connection string in
   `config.properties`, and confirmed `testng.xml` runs both the real `tests`
   package and a `wip` scratch package in the same suite. Also noted the stack is
   old (Java 8, Selenium 3.141.59, TestNG 6.14.3).

3. **Read all page objects** (`BasePage`, `DashboardPage`, `LoginPage`,
   `InvoiceModifyPage`, `OrderCreatePage`, `OrderHandler`, `OrderModifyPage`,
   `ProductModifyPage`, `UserManagement`, `UserModifyPage`, `UserRegisterPage`).
   Found: `BasePage` is a god object (nav + waits + assertions + logging + CSV
   + JS-executor helpers all in one class); four "modify" page classes
   (`OrderModifyPage`/`ProductModifyPage`/`UserModifyPage`/`InvoiceModifyPage`)
   are near-duplicate copy-paste of each other; locators are dominated by
   auto-generated `ext-comp-NNNN` IDs and absolute positional XPath
   (`//div[N]/div[N]/...`); naming is inconsistent (`OrderHandler`/
   `UserManagement` vs. the `*Page` convention used elsewhere); hardcoded
   admin credentials duplicated again inside `LoginPage.loginAsAdmin()`.

4. **Read all utility classes** (`DateFormatterUtil`, `DbConnector`,
   `EmailSenderUtil`, `RetryListener`, `ScreenshotUtil`). Found: `DbConnector`
   hardcodes the same production DB credentials seen in `config.properties`
   and builds SQL via string concatenation (injection-shaped); `EmailSenderUtil`
   sends real failure-notification emails; `RetryListener` implements
   `IRetryAnalyzer` for the suite-wide `retryCount=3` configured in `testng.xml`.

5. **Read all test classes**, including the two `wip` scratch classes. Found:
   three "god tests" (`FullAdminWorkflowTests`, `FullInvoiceBillingCycleTests`,
   `FullProductLifecycleTests`) each bundling 10-13 unrelated "features" into a
   single `@Test` method with no isolation; `ProductGridTests` has two test
   methods with zero assertions and one with an unasserted `.isDisplayed()`
   call, meaning they can never fail on a real regression; `CreateOrderTests`
   and `RegisterUserTests` use static mutable fields to pass state between
   `@Test(priority=N)` methods, creating ordering dependencies; raw
   `driver.findElement(By...)` calls appear directly inside
   `FullProductLifecycleTests`/`FullInvoiceBillingCycleTests`, bypassing the
   page-object layer; the two `wip` tests instantiate `ChromeDriver` with no
   `try/finally`, so an early exception leaks the browser process; `38`
   occurrences of `Thread.sleep` were found across the whole codebase.

6. **Targeted greps to confirm/quantify suspicions** rather than relying on
   impression alone:
   - `grep -rln "EmailSenderUtil|ScreenshotUtil|..."` across the repo →
     confirmed `EmailSenderUtil` and `ScreenshotUtil` are defined but never
     called anywhere outside their own files (dead code).
   - `grep -rn "Thread.sleep" --include=*.java src | wc -l` → 38 matches,
     used as the quantified basis for the "pervasive sleep usage" finding.
   - `grep -rln 'xpath("//div\['` and `grep -rln "ext-comp-"` across
     `src/main/java` → 6 of 10 page objects use positional XPath, 8 of 10 use
     auto-generated `ext-comp-*` IDs, used to quantify the locator-brittleness
     finding precisely rather than asserting "most" vaguely.
   - Checked for `.gitignore`, `log4j*`/logback config, and any `.git` folder →
     none found, confirming the "no `.gitignore`" and "no real logging
     framework" findings.
   - Searched for any reader of `config.properties` (Properties/ResourceBundle
     usage) → none found, confirming the file is dead/unused configuration
     while credentials are hardcoded directly in Java instead.

7. **Synthesized 34 distinct findings**, grouped into six themes: security &
   secrets management; environment & configuration; architecture & design;
   test design; reliability & wait strategy; code quality & maintainability.
   Assigned a severity (Critical/High/Medium/Low) to each based on real-world
   impact (e.g., committed production credentials and tests hitting
   production = Critical; naming inconsistency = Low).

8. **Wrote `review.md`**: scope, summary, the full 34-item issues list with
   file-level evidence for each, a short "what's working well" section, and
   the checklist-tab table embedded at the end as requested.

9. **Wrote `checklist.md`**: the same 34-row table as its own standalone file
   (area / finding / severity / evidence), plus a severity-count summary
   (6 Critical, 11 High, 12 Medium, 3 Low).

10. **Wrote this `transcript.md`** documenting the steps above.

## Key findings (condensed)

- Plaintext production admin credentials and production database credentials
  committed in `src/test/resources/config.properties`, duplicated again
  verbatim inside `LoginPage.java`, `DbConnector.java`, and three test classes.
- Tests and a raw-JDBC verification utility (`DbConnector`, which also builds
  SQL via string concatenation) run directly against the production CRM
  environment and production MySQL database — no staging/test environment
  exists.
- `BasePage` god object mixes navigation, waits, assertions, logging, CSV
  writing, and JS-executor helpers in one class.
- Four page objects (`OrderModifyPage`, `ProductModifyPage`, `UserModifyPage`,
  `InvoiceModifyPage`) are near-identical copy-paste duplicates.
- Locators are dominated by brittle auto-generated IDs (`ext-comp-NNNN`, 8/10
  page objects) and absolute positional XPath (6/10 page objects).
- Three "god tests" bundle 10-13 unrelated features into one `@Test` method
  each, destroying failure diagnosability; several other tests have no
  assertions at all and can never fail.
- 38 `Thread.sleep` calls substitute for explicit waits; `BasePage` has two
  methods self-labeled `waitForPageLoadHack`/`waitForAjaxSpinnerHack`.
- Cross-test ordering dependencies via static mutable fields
  (`orderIdFromFirstTest`, `lastRegisteredEmail`).
- Scratch/WIP debug test classes are checked into the suite and executed by
  CI (`testng.xml` includes the `com.acme.crm.wip` package).
- `EmailSenderUtil` and `ScreenshotUtil` are fully implemented but dead code
  (never invoked anywhere).
- Outdated stack (Java 8, Selenium 3.141.59, TestNG 6.14.3), no `.gitignore`,
  no real logging framework, no static analysis tooling, CI with no quality
  gate running on every branch.

## Tools used

`Bash` (file enumeration via `find`, targeted `grep` counts/confirmations),
`Read` (full-content read of every source file in the fixture — no file was
read partially or skipped), `Write` (three output files). No destructive or
write operations were performed against the fixture repo itself; it was
treated strictly as read-only per the task instructions.
