---
name: automation-framework-review-skill-creator
description: Review a test automation framework (UI/API, any language/stack) against software design principles, test-design best practices, and naming/coding-standards conventions. Use when the user asks to "review the automation framework", "review the test framework", "audit the QA framework/codebase", or asks whether tests/locators/architecture/naming conventions are "good"/"match best practices"/"match requirements for good tests" in a test-automation repo. Produces a structured, evidence-cited Markdown review document, plus a secondary checklist-tab-ready table for the team's maturity-assessment spreadsheet.
---

# Automation Framework Review

Produces a rigorous, evidence-based **issues list** for a test automation framework (Playwright/Selenium/Cypress/RestAssured/etc., any language) against established software design principles and test-design best practices. Output is a Markdown document with concrete `file:line` citations for every claim — never vague impressions.

**This is a defect report, not a review.** The reader wants a punch list of what's wrong and what to do about it — not a guided tour of every dimension considered, and not reassurance about what's fine. A dimension with no defect gets zero lines of output: no heading, no "no violations found," no "verified strength" writeup. If nothing is wrong, that dimension simply does not appear anywhere in the document. The only place a clean-bill-of-health verdict is worth a single line is the FIRST-principles table, because its whole point is being a complete checklist — everywhere else, silence is the correct way to report "nothing here."

## Core principle: verify, don't recall

Every finding must be backed by evidence read *during this review*, not general knowledge about what such frameworks "usually" look like. If a claim can't be tied to a specific file and line, cut it or mark it as a hypothesis to verify. Prefer delegating research to subagents (via the Agent tool) so the main conversation stays free for synthesis and follow-up — each research pass should come back with concrete counts and citations, not prose impressions.

## Process

1. **Scope the review.** Identify modules/layers (e.g. core/driver, page-objects/domain, tests). Note anything the user explicitly excludes (e.g. a specific file already reviewed) and honor that exclusion in every subsequent pass — don't re-include it "for completeness."

2. **Survey first** (one research pass, can run in background while planning). Establish: languages/frameworks in use, module boundaries, build/CI setup, rough file counts. This calibrates how deep later passes need to go.

3. **Run focused, evidence-gathering passes** — as parallel or sequential subagent calls depending on independence — covering the dimensions below. Each pass should return counts, ratios, and `file:line` citations, not summaries.

4. **Synthesize into the review document** using the structure below. Don't just concatenate subagent reports — cross-reference findings (e.g. a DRY violation in page objects often correlates with a missing abstraction layer; note the connection). Tag every individual finding (not just the final Recommended Actions list) with an impact/effort marker — see **Severity/effort tagging** below — so the priority order in the final section is a mechanical rollup of tags already assigned, not a fresh judgment call.

5. **Ask before assuming scope.** If the user's request is ambiguous about depth (e.g. "review the framework" with no further detail), a quick clarifying question is fine, but bias toward doing a full first pass and letting the user redirect — don't stall on the ask.

## Dimensions to cover

Adapt to the stack, but cover all of these unless clearly inapplicable:

### A. Layering / architecture
The relevant model for test automation is usually **driver/core → domain (page objects / API clients) → test**, not classic MVC. Check:
- Do tests reach past the domain layer directly into the underlying tool's raw API (e.g. a test importing the browser-automation library directly instead of going through a page object)? This is the layer-boundary check — grep for the raw library's import in test source directories.
- Does the domain layer leak the underlying tool's types back out through public method signatures (e.g. returning a raw `Locator`/`WebElement` instead of a typed page object or primitive)?
- Does the driver/core layer know about domain-specific business concepts? (Layer inversion — infra should be reusable across projects, not coupled to one feature.)
- **Is there a reusable business-step/flow layer between domain objects and tests**, or does every test re-compose low-level domain actions (clicks, fills) into business scenarios (create X, register Y) from scratch inline? Missing middle layer is a common, high-impact finding — check for a `steps/`/`flows/`/keyword-driven package; if absent, quantify how many tests duplicate the same business-action composition.
- Does the codebase's actual practice match what its own docs/AGENTS.md/README claim about its architecture? Call out any mismatch explicitly.
- **Page Object Model correctness, beyond layer boundaries**: do action methods return `this`/the correct next page-object type for chaining, or an inconsistent/wrong type? Do page objects assert/verify internally (mixing domain responsibility with verification responsibility — a specific, common POM smell distinct from the general SRP check in §B)?

### B. SOLID / design principles in the framework engine and domain layer
- **SRP**: any God Base Class that every domain object inherits, bundling unrelated concerns (navigation + assertions + popups + data I/O)? Cite line-count and responsibility breakdown.
- **OCP**: is extensibility (new selector strategy, new browser/driver, new comparison strategy) done via editing a closed switch/if-chain, or via a genuinely open mechanism (registry, strategy pattern, plugin)?
- **LSP**: do subclasses override base methods in ways that break callers' expectations (throwing where base doesn't, returning null where base implies non-null)? Distinguish public inherited contracts from private helpers — LSP only applies to the former.
- **ISP**: are domain objects forced to inherit/implement methods irrelevant to them because the base class/interface is too fat?
- **DIP**: is the underlying automation tool's concrete API used consistently through the framework, or inconsistently (sometimes wrapped, sometimes not)?
- **Fixture/dependency-injection maturity**: does setup use proper DI/fixture composition (pytest fixtures, JUnit `@ExtendWith`, Playwright fixtures) or is it inheritance-based (base-class setup chains)? This is a distinct axis from the SRP God-Base-Class check above — a base class can have a single responsibility and still be the wrong composition mechanism.

### C. DRY — quantified, not anecdotal
- Grep for repeated method-body shapes (e.g. the same try/catch/assert boilerplate copy-pasted per field), repeated test skeletons (same sequence of steps differing only in entity name), and give a real count of occurrences and files affected. A single example is a data point; a review needs the count.
- **Cross-file duplication within the SAME role, not just within one file.** Duplication inside a single God Base Class is one pattern; a *different* pattern is the same method shape copy-pasted across multiple sibling domain classes of the same kind (e.g. every `*ModifyPage`, every `*ViewPage`, every `*CreatePage`). These do not show up from reading one file in isolation — they require explicitly clustering same-role files and diffing their method-name patterns/bodies. Concretely: grep for a repeated method-name *suffix or prefix pattern* across the domain-object directory (e.g. `verify.*IsEditableAndEnabled`, `enter.*`, `select.*`, `click.*Tab`) and check whether the bodies behind matching names are near-identical modulo one locator/label. If 3+ sibling files each declare 3+ methods matching the same name pattern with near-identical bodies, that is its own DRY finding — distinct from (and don't assume it's subsumed by) any single-file God Base Class or missing-abstraction finding you've already logged. A fix elsewhere (splitting a base class, adding a step layer) does not automatically collapse this — verify it explicitly rather than assuming a related fix covers it.
- **Test-data construction specifically**: is there a builder/factory pattern for constructing test entities, or are giant inline object literals/parameter lists repeated per test? This recurs often enough on its own to call out separately from general method-body duplication.
- **Domain-concept representation consistency**: for a recurring domain concept the suite models explicitly (a logged-in user/role, a test account, an environment) — is there one typed representation used everywhere (e.g. a `User`/`Role` value object with a `.loginAs(user)`-style entry point), or does part of the suite use that representation while another part reaches around it for the same concept (e.g. pulling a raw credential string directly from config/properties and passing it into a lower-level API instead of going through the typed object)? This is a narrower, easy-to-miss case of DRY/consistency — it doesn't show up as duplicated *code shape* (the two paths look different), only as duplicated *concept* with two disconnected representations, so it requires deliberately asking "is there more than one way this codebase expresses X" for each core domain concept, not just diffing method bodies.

### D. Test design quality (excluding anything the user marked out of scope)
- **Test length / responsibility**: are there single-`@Test`-method classes covering many unrelated features in one long method? Quantify across the whole suite (e.g. "13 of 17 files in X have exactly one test method, 150-690 lines"). Identify any file that gets this right and could serve as the template.
- **Test independence**: shared static/mutable state across tests? Order dependency? Distinguish *inter*-test independence (does test B depend on test A having run) from *intra*-test independence (within one long method, does step 40 depend on step 39's leftover state — this is a real but different concern).
- **Parallelization safety**: is the suite actually configured to run in parallel (worker/thread count in CI config, `fullyParallel`, `pytest-xdist`, etc.)? If so, do tests/fixtures share mutable state, files, or test-environment records across workers? This is distinct from ordinary inter-test independence — tests can be order-independent when run serially yet still collide when run concurrently (e.g. two workers both writing to the same named record).
- **Self-validation**: does every test actually assert something about the outcome, or are there tests that execute steps and never call assert/verify (a test that can pass while checking nothing)?
- **Repeatability**: any hardcoded dates/timestamps/environment-specific literals in assertions that will go stale or fail outside the day/environment they were written in?
- **Business-readability**: reading a test method's body, can you tell *what business rule is being validated* without executing the chain mentally or cross-referencing an external spec? Look for: business intent stated via naming/`@DisplayName`/comments vs. only inferable from a sequence of low-level action calls; business-meaningful data expressed as named constants/builders vs. raw string literals; verification interleaved indistinguishably with action calls vs. structurally separated. This is related to but broader than AAA phase-ordering — note both.
- **AAA (or the paradigm that actually fits)**: sample several tests. Is Arrange/Act/Assert cleanly separated, or is it a repeated act→assert→act→assert cycle? For long-running E2E/workflow tests, repeated-cycle can be a legitimate, intentional paradigm (step-based/procedural workflow testing, closer to BDD) rather than an AAA violation — say so explicitly if that's the case, but still flag it if it also fails the business-readability check above (the two are independent: a test can be intentionally step-based *and* still unreadable if it has no business vocabulary layer).
- **Lifecycle hygiene**: is setup/teardown centralized (`@BeforeEach`/base classes) or duplicated per test? Is there any `@AfterEach`/`@AfterAll` cleanup of test-created data, or does cleanup only happen inline on the happy path (meaning an earlier failure skips it)?
- **Scratch/WIP code in the production test tree**: directories with names like `debuggingtests/`, `wip/`, `scratch/`, `presetup/` sitting alongside real suites, not excluded from the CI test-runner scan — flag as a hygiene issue, and check whether any are literal draft/duplicate copies of a "real" finished test elsewhere.
- **Test categorization/tagging**: is there a smoke/regression/full-suite tagging convention (`@Tag`, `@smoke`, pytest markers, JUnit categories)? Does CI actually run a fast tagged subset on PR and the full suite on a separate (nightly/merge) trigger, or is there no distinction (every run is all-or-nothing)? This affects Timely under FIRST and CI turnaround directly.
- **Assertion style consistency**: soft vs. hard assertions — does a failure on assertion N of M in one test method hide assertions N+1..M from ever running/reporting? Is there a consistent custom-matcher/assertion-helper convention, or ad hoc raw comparisons mixed with helper calls?

### E. Test data management
- Is there one consistent ID-generation utility for uniqueness, or do different files bypass it (raw timestamps, `Math.random()`, hardcoded literal names that will collide on rerun)?
- Orphaned data risk: do tests create entities/records they never clean up? Is this bounded or a real accumulation risk against a shared/persistent test environment?

### F. Error handling
- Any empty catch blocks, or catch-and-silently-degrade patterns that mask real failures as false negatives (especially in comparison/verification utilities, where "failed to check" must never look identical to "checked, no difference")? **Grep for this explicitly and report a count, the way §G requires for sleeps — do not answer it from the impression you formed while reading other dimensions.** Search the whole codebase for the language's catch construct (`catch (`, `except:`, `except Exception`, `rescue`, `recover()`) and classify each hit: rethrows with context, handles meaningfully, logs only, or swallows outright. A catch whose body is empty, is a bare `return false`/`return null`, or only logs and continues is a swallow. This check has been observed to go missing entirely from reviews of codebases that had dozens of swallowed exceptions, because nothing forced the grep — so if the review says nothing about exception handling, that is a gap in the review, not evidence the codebase is clean. Report the count and the worst offenders with file:line even when the total is small; report an explicit clean verdict only when the grep genuinely returns no swallows.
- Is checked-exception handling consistent (wrap-with-context-and-rethrow) or does it vary in philosophy across the codebase (fail-fast in some places, swallow-and-continue in others) without a stated reason?
- **Flakiness masking**: does the CI config or test runner silently retry failed tests (`retries: N` in Playwright config, `@RetryOnFailure`, rerun-failed-tests plugins)? A retry mask on a genuinely flaky suite inflates green-build confidence without fixing the underlying nondeterminism — flag any nonzero default retry count and note whether flaky tests are tracked/quarantined or just silently re-run until green.

### G. Synchronization / waiting strategy (UI frameworks specifically)
- Grep for hardcoded sleeps (`Thread.sleep`, `time.sleep`, `page.waitForTimeout`, fixed-duration waits) vs. explicit condition-based waits vs. reliance on the framework's built-in auto-waiting (e.g. Playwright actionability checks). Give a real count and file list, not an impression — this is frequently the single biggest source of flakiness in a UI suite, on par with locator strategy.
- If explicit waits exist, are they centralized in the driver/domain layer or reinvented ad hoc per test/page object?
- Any wait polling on a condition that can never time out cleanly (infinite loop risk) or that swallows the timeout exception silently (masks a real failure as a pass — cross-reference §F).
- **A raw, non-retrying state-check coexisting with a retrying one is its own finding, not a subset of the hardcoded-sleep check above.** Once you find *any* correct retrying/wait-and-poll variant for a check (e.g. `should(isDisplayed())`, `waitFor(...)`, an assertion helper that polls), grep for the raw underlying call it wraps (`.isDisplayed()`, `.isEnabled()`, `.getText()` used as a presence check) across the *whole* domain/steps layer, not just the file where you found the good example — an instant-fail check sitting next to a proper wait is a real, separately-worth-reporting flakiness bug even when it's a minority pattern, because each occurrence fails a test the moment a real users's browser would just need one more render tick. Count occurrences and file list like any other quantified finding; don't fold it into the wrapper-vs-raw-call *consistency* finding in §I — that's about API-choice consistency, this is about correctness under real render timing.

### H. Locator/selector strategy (UI frameworks specifically)
- Get the actual distribution of locator strategies used (grep and count by type/kind), not an impression. Compare against the framework's own documented priority (if any) and check whether that priority is actually followed or just aspirational.
- Sample enough examples to categorize: semantic/attribute-based (stable) vs. positional/structural (fragile) vs. auto-generated-ID-coupled (very fragile, especially in ExtJS/legacy enterprise-widget UIs where IDs encode the entire container hierarchy).
- Check how dynamic lookups (e.g. "find the grid row containing X") are implemented — one centralized, reusable, properly-scoped helper, or ad hoc string-building reinvented per file?
- Check scoping: are locators scoped to their logical parent/component, or page-global (risking wrong-element matches in repeated structures like grids)?
- Give a clear per-example verdict, not just an aggregate — a framework can be "good overall" while having a few standout-bad examples worth calling out individually (e.g. one selector combining an 8-segment auto-generated ID with 4 levels of positional CSS descent when a single class selector already suffices, per the component's own documentation/hints).

### I. Consistency
Optional-vs-null idiom consistency, method-chaining return-type consistency, Javadoc/doc-comment coverage. (Naming-convention drift and coding-standards compliance are covered in depth in §O — don't duplicate that analysis here, just note any consistency issue that isn't specifically about naming/style.)

### J. Failure diagnostics / reporting
- On a CI failure, can a maintainer diagnose the cause without re-running locally? Check for screenshot-on-failure, video/trace capture (e.g. Playwright trace viewer), and whether failure logs include enough context (what step, what data, what environment) or just a bare stack trace.
- Is a human-readable test report generated (HTML report, Allure, JUnit XML consumed by CI) and actually published/accessible from the CI run, or does diagnosing a failure require pulling console logs?
- **Report navigability for a passing/mixed run, not just failure diagnosis**: does the report framework's own grouping/categorization mechanism get used (e.g. Allure `@Feature`/`@Story`/`@Epic`, JUnit `@Tag`/`@DisplayName` used for report grouping, pytest markers surfaced in the HTML report) so a large suite's report is browsable by feature area, or is every test a flat, unstructured list? Sample several test classes across different feature areas — if none use the framework's grouping annotations, that's a real, reportable finding distinct from the failure-diagnostics checks above (this is about finding a *specific* test in a report of hundreds, not about diagnosing *why* one failed).
- **Are known, tracked issues (a linked bug ticket, a "needs update" reason) distinguished in the report from a genuine new failure?** Check for a ticket-link annotation (e.g. Allure `@TmsLink`/`@Issue`) or an explicit skip-with-reason mechanism used when a failure's root cause is already known/tracked, vs. every failure — new or known — reporting identically. This matters most when the questionnaire/interview (if available) states a pass rate below ~90%: at that point, whether the report can separate "known, already-filed" from "new, unexplained" failures directly determines how expensive triage is, so treat this as its own checklet even though it's adjacent to the retry/skip-mechanism check in §F.

### K. Environment/config management
- Is there a clean environment-switching mechanism (profiles, `.env` files, CLI flags) allowing the same suite to target multiple environments without code changes, or are environment values hardcoded/require a code edit to switch?
- Is test data/execution isolated from production data, or is there any risk of a misconfigured run hitting a production endpoint?
- (Secrets handling and plaintext infra values remain covered in §L — this section is about environment-switching mechanics, not secret storage.)

### L. Config/CI (lighter pass, only if in scope)
Hardcoded environment/infra values committed in plaintext, static-analysis gates actually enforced by default in CI vs. opt-in only, secrets handling.
- **Build-file correctness, not just currency**: for each plugin/dependency version driven by a property variable (Maven `${...}`/Gradle version catalog entry), does the variable name actually match what it configures, and does its value correspond to a version that exists for that artifact? A copy-pasted or misnamed version property (e.g. a plugin's version wired to a differently-named sibling property, pointing at a version number that was never published for that artifact) is a real, easy-to-miss build-correctness bug distinct from §M's "is the pinned version merely outdated" question — this one can mean the build is silently falling back to some other resolved version, or breaking, rather than using what the author intended. One targeted read of the build file's version-property block is enough; don't expand this into a full dependency audit.

### M. Dependency currency
Is the core automation library (Selenium/Playwright/Cypress/etc.) pinned to a materially outdated version that's missing key features relevant to the other findings here (e.g. an old Selenium predating built-in relative locators, an old Playwright predating current auto-waiting/trace capabilities)? This affects which best practices are even achievable without an upgrade — note it once as context rather than re-deriving it per dimension.

### N. Repo/artifact hygiene
Committed screenshots/videos/HTML reports bloating the repo, missing `.gitignore` coverage for generated test output (report dirs, trace files, downloaded artifacts).

### O. Naming conventions & coding standards
- **Establish the baseline first.** Check for a formal standard before judging against an assumed one: linter/formatter config (Checkstyle, ESLint, `.editorconfig`, Spotless, PMD, `pyproject.toml` lint sections), a documented style guide (CONTRIBUTING.md, CLAUDE.md, README), or language-idiomatic defaults if none exists (e.g. Java: `UpperCamelCase` classes, `lowerCamelCase` methods/fields, `UPPER_SNAKE_CASE` constants). State explicitly which baseline is being used for the verdict — "no explicit standard found, judged against language-idiomatic Java conventions" is a valid and necessary line, not a gap.
- **Class/file naming by role**: do page objects, step classes, test classes, data providers, and query executors follow one consistent suffix/prefix convention per role (e.g. every page object ends `Page`, every step class ends `Steps`, every test class ends `Tests`)? Grep the relevant directory per role and count outliers, don't sample one file and generalize.
- **Method naming semantics**: do method names accurately describe behavior (a `get*` that mutates state, an `is*`/`has*` that doesn't return boolean, a `verify*`/`assert*` used inconsistently for both soft checks and hard failures)? Cite specific mismatches.
- **Variable/field naming**: single-letter or meaningless names (`x`, `temp`, `data1`) outside trivial loop counters; Hungarian-notation or type-suffix cruft in a language where it's not idiomatic; boolean fields/methods that don't read as a predicate (`status` vs. `isActive`).
- **Constant/enum naming**: are magic strings/numbers that recur across files promoted to named constants, or copy-pasted as literals per call site (this overlaps with §DRY but the naming-specific angle is whether the *existing* constants that do exist follow a consistent case/placement convention, e.g. all in one `constants/` package vs. scattered as ad hoc `static final` fields inside unrelated classes)?
- **Test method / test-case naming**: is there a consistent convention for expressing intent in the test name itself (`should_X_when_Y`, `testX`, `@DisplayName` prose) or a mix of styles across the suite that makes the test report harder to scan?
- **Test-file discovery compliance**: does every test class actually match the naming pattern the runner/build config expects (e.g. `**/*Tests.java` in `testng.xml`/Surefire include pattern)? A file that doesn't match is silently never run — this is a correctness bug wearing a naming-convention costume, tag it accordingly (impact is not cosmetic).
- **Package/directory naming vs. actual contents**: does a package named `utils`/`helpers`/`common` actually hold cohesive utilities, or has it become a dumping ground whose contents don't match what the name promises?
- **Formatting/style mechanics** (only if cheap to check and not already gated by a formatter): indentation consistency, brace style, import ordering/wildcard imports, line-length outliers — report as one aggregated finding with counts, not per-instance.
- Give a clear aggregate verdict with counts/ratios (e.g. "38 of 41 page objects follow `*Page` suffix; 3 outliers: X, Y, Z") — naming findings are exactly the kind of claim that's easy to hand-wave, so hold this dimension to the same evidence bar as locators/DRY.

## Severity/effort tagging

Tag every finding — in every dimension section, not just Recommended Actions — with `[Impact: High/Medium/Low | Effort: High/Medium/Low]` immediately after its heading/bullet. A finding tagged `N/A` or "verified strength" doesn't belong in the document at all — cut it rather than tag it (see Output structure below).

- **Impact**: how much of the codebase it touches or how badly it undermines correctness/maintainability/readability if left alone (use the counts/ratios already gathered as evidence — e.g. "13 of 17 files" is High impact, "one isolated file" is Low).
- **Effort**: rough size of the fix (Low = localized, one file/pattern, mechanical; Medium = a new shared abstraction plus call-site updates; High = structural/architectural change touching many layers or requiring a team decision).
- A missing business-step/flow layer is typically `[Impact: High | Effort: High]`; a single bad locator is typically `[Impact: Low | Effort: Low]`. Let the evidence set the tag, don't default to High everywhere.
- **Exactly three values are legal for each slot: `High`, `Medium`, `Low`.** Nothing else — no `Medium-High`, no `High/Medium`, no `Very High`, no `N/A`, no numeric scores, no qualifiers appended to the word. A finding whose impact feels like it sits between two values still has to pick one, because the tag's whole job is to sort the Recommended actions rollup, and a hyphenated or hedged value has no defined position in that sort. When torn, choose the higher value for Impact and the higher value for Effort, then use the finding's prose to explain the nuance — that is what the prose is for.
- The final **Recommended actions** section is then a straight rollup ordered by Impact first, Effort second (High-impact/Low-effort first) — not a re-judgment from scratch.

## Mandatory greps — run every one before drafting

Most §A–O dimensions are judgement calls you form while reading. The checks below are not:
each one has been observed to vanish from a review of a codebase that visibly had the defect,
because reading the code in dimension order never forced the search. Run all of them as explicit
repo-wide greps, and carry each one's **count** into the document — in a finding when the count is
nonzero, in the FIRST-principles or checklist table when it is zero. A dimension you cannot quote a
number for has not been checked.

| Check | Search for | Report |
| --- | --- | --- |
| Swallowed exceptions (§F) | `catch (`, `except:`, `except Exception`, `rescue`, `recover()` — then classify each hit | Count of swallows (empty body, bare `return false`/`null`, log-and-continue) + worst offenders with `file:line` |
| Unconditional waits (§G) | `Thread.sleep`, `time.sleep`, `waitForTimeout`, `setTimeout`, `implicitlyWait` | Count + files affected |
| Assertion-free tests (FIRST: Self-validating) | test methods with no assert/expect call in the body | `N of M` test methods |
| Hardcoded credentials (§M) | `password`, `api_key`, `token`, `secret` assigned to a literal | Count + `file:line` |
| Retry/rerun policy (§CI) | `retries`, `rerunFailingTestsCount`, `flaky`, `@Retry` | The configured value, even when zero |

Finding zero is a real result and must be reported as such — a clean `+` backed by a grep is worth
something, a clean `+` backed by an impression is not. Conversely, if a grep returns hits you then
judge harmless, say so with the count rather than staying silent; silence here is indistinguishable
from having skipped the check.

## Output structure

Write the review as a single Markdown file (ask where, or infer a sensible repo-root location like `AUTOMATION_FRAMEWORK_REVIEW.md`). This is an issues list: every heading that survives into the final document names a problem, not a dimension. Run the full checklist (§A–O) internally during research, but when a dimension comes back clean, drop it entirely — do not keep its heading as a placeholder, do not write "no violations found," do not describe what was checked. The dimension letters below are the *research* checklist, not a mandatory table of contents.

```
# Automation Framework Issues

**Scope:** ...
**Excluded from this review:** ... (if applicable)
**Verdict up front:** 2-4 sentences naming the real structural issues. If a whole category (e.g. SOLID) turned up nothing worth reporting, don't mention it here either — just don't bring it up. This includes praise: the no-fluff rule is not only about withholding "no violations found" notes, it also rules out complimenting the dimensions that came back clean. Sentences like "the framework's mechanics (locators, fixture DI, waiting strategy, test-data builders) are solid", "the core layers are cleanly separated" or "factories eliminate inline test-data literals" are exactly the fluff to cut here, however true they are — a clean dimension earns its `+` in the FIRST-principles table and the checklist table, and those two tables are the *only* places a clean verdict belongs. The verdict paragraph states what is wrong and how bad it is; if genuinely nothing is wrong, say that in one sentence and stop, rather than touring what went right. The one exception: if a real finding is only intelligible by contrast with a clean part of the codebase (e.g. "two of ten page objects bypass the flow layer the other eight use"), naming the clean part is evidence for the finding, not praise, and is fine.

---
[One heading per actual finding/finding-cluster, grouped by whichever of §A-O dimensions it belongs to — but the section header names the problem ("Missing business-step/flow layer", "God Base Class: InsightBasePOM", "PR pipeline never runs the E2E suite"), not the dimension ("Architecture", "Config/CI"). Skip entirely: layering-boundary checks with zero leakage, SOLID letters with no violation, DIP consistency when it's consistent, hygiene/repo-artifact checks when clean, dependency currency when current, environment/config switching when it's already clean, naming/coding-standards checks with no material drift. Every surviving heading gets its [Impact | Effort] tag and file:line evidence.]

## FIRST principles table — Fast/Independent/Repeatable/Self-validating/Timely, each with a verdict and evidence. This is the one place a clean verdict is worth stating, since the table's value is being exhaustive over the five letters. "N/A statically" is valid for Timely.

## Recommended actions, in priority order — lead with the highest-leverage structural fix, not the easiest one. This is a rollup of the findings above; don't introduce new items here.
```

## Checklist-tab mapping (secondary deliverable)

This review feeds the team's Google Sheets audit workflow, whose **checklist tab** (`Section | Check | Status (+/-) | Comments`) is filled in at the end of the audit alongside the questionnaire tab's interview answers. Producing that checklist input is a **secondary deliverable** of this skill — do it after the main issues-list document, don't let it change how that document is written.

**Scope discipline: fill only what this code review actually answers.** The checklist has six sections — `Tools`, `Strategy`, `Framework`, `Running`, `Processes`, `AI Usage`. Most `Tools`, `Strategy`, and `AI Usage` rows ask about team decisions, investment rationale, and process ownership — that's questionnaire-interview territory, not something a repo/CI read can verify. Do not guess a Status for those from code alone. Only emit a checklist row when this review's dimensions (§A–O) actually produced evidence for it; otherwise leave the row out of the table entirely rather than filling it with a guess or "N/A".

Row-by-row mapping (checklist wording → review dimension → what counts as evidence):

| Checklist section | Check | Backed by | Notes |
|---|---|---|---|
| Framework | Framework is consistent | §I | Optional/null idiom, chaining return types, doc-comment coverage |
| Framework | Framework follows a layered architecture | §A | Layer-boundary leakage, raw-type leakage, missing business-step layer |
| Framework | Framework complies with DRY | §C | Cross-file/same-role duplication counts, test-data builder presence |
| Framework | Framework complies with KISS | §A/§B (indirect) | Only fill if a God Base Class, over-abstracted OCP mechanism, or needless indirection was already found — don't invent a separate KISS pass |
| Framework | Framework complies with YAGNI | — | Not directly covered by any dimension; leave blank unless a finding explicitly shows speculative/unused abstraction |
| Framework | Framework complies with SOLID | §B | Per-letter SRP/OCP/LSP/ISP/DIP verdicts |
| Framework | Framework complies with language standards | §O | Naming/style baseline verdict with counts |
| Framework | Presetups are implemented at the optimal available level | §D (lifecycle hygiene), cross-check questionnaire | Code review can confirm *mechanism* (API vs DB vs UI presetup) if visible; the "optimal" judgment is often already answered in the questionnaire — don't duplicate, just corroborate or flag mismatch |
| Framework | Unconditional waits are not a common practice | §G | Hardcoded-sleep count and file list |
| Framework | Tests are atomic and independent | §D (independence) | Inter-test shared state / order dependency |
| Framework | Tests remain independent under parallel execution | §D (parallelization safety) | Distinct from the row above — only fill if parallel execution is actually configured |
| Framework | Test implementation is done at the optimal level (API, UI...) | §A, §D | Whether UI is used where API/unit would suffice — often only partially code-verifiable; note if judgment needs questionnaire's stated strategy to complete |
| Framework | Core libraries/framework/language versions are reasonably current | §M | Pinned version vs. latest, missing capabilities it explains |
| Framework | No hardcoded credentials/secrets in the test codebase | §L | Plaintext secrets grep result |
| Running | Steps have a sufficient level of documentation for reporting | §D (business-readability), §J | Step naming/labels feeding into reports |
| Running | When tests fail, there are mechanisms to easily find the cause | §J | Screenshot/trace/video-on-failure, log context |
| Running | Test stability is at a sufficient level | §F (retries) | Only a partial signal — nonzero default retry count is evidence of a *known* stability problem; absence of retries is not proof of stability, say so rather than marking a clean `+` |
| Running | There is a way to track run results over time | §J | Published HTML/Allure report, JUnit XML consumed by CI |
| Running | Tests are integrated into CI/CD, not run purely manually/on-demand | §L | CI trigger config presence |
| Processes | Tests are properly documented | §D (business-readability), §O (test-naming) | |
| Processes | A failure-handling strategy is implemented (bug reporting → flaky rerun → failure skipping) | §F | Retry/skip-mark mechanism found in code/CI config; corroborate against questionnaire's stated process, don't contradict it silently |

Everything else on the checklist (`Tools` section entirely; `Strategy` section entirely; `Running`: regular remote execution configured, run time adequate; `Processes`: coverage level calculated, PR-review strategy defined, automation meaningful to whole QA process; `AI Usage` entirely) is **out of scope for this skill** — it's answered by the questionnaire interview, not by reading the repo. Do not fill these rows.

**Output for this deliverable:** a Markdown table with the exact columns `Section | Check | Status (+/-) | Comments`, containing only the rows this review actually answered (per the mapping above), in the same order they appear on the checklist tab. `Status` is `+` (passes) or `-` (fails/violated) — never a bare "partial"; if evidence is mixed, put `-` (or `+` if the violation is minor/isolated) and explain the nuance in `Comments`. `Comments` should cite the same `file:line`/count evidence as the main issues document, kept to 1-2 sentences — this is a summary pointer into the full review, not a duplicate of it. Present this table after the main issues-list document, under its own heading, e.g. `## Checklist tab input` — do not merge it into the issues list itself, and do not attempt to write it into the Google Sheet directly; the user pastes it in manually.

**Self-check before finalizing the table — do not skip this.** This table has been observed to
under-fill itself in practice: a prior run found two God Base Classes (clear KISS-disqualifying
evidence per the mapping's own "fill if a God Base Class... was already found" instruction) and a
clean, current core-library versions verdict (§M) and a clean no-hardcoded-credentials verdict
(§L), yet the first draft of the table omitted all three rows even though the evidence for each
already existed elsewhere in the same document. Prevent this by, after drafting the table, walking
the row-by-row mapping above **line by line** (not just reviewing the table you already drafted)
and for each row asking: "does §[letter] contain a finding, or an explicit clean-verdict statement
(e.g. in the FIRST-principles table or a §M/§L dependency-currency/secrets note), that this row's
`Backed by` column points to?" If yes, the row belongs in the table — go back and add it if it's
missing, don't rely on having caught it the first time. This check applies in both directions: it
catches missing `-` rows (a real finding that didn't get promoted to its checklist row) just as
much as missing `+` rows (a clean dimension that's easy to skip since the output-structure rule
above says clean *findings* get zero lines in the issues list — that "silence" rule governs the
main issues-list document, it does not exempt this checklist table, which is exhaustive-by-mapping
the same way the FIRST-principles table is exhaustive-by-letter).

**Then run the check in the other direction too — this is the one that gets missed.** The walk
above goes row → evidence ("does anything back this row?"). That direction alone has been observed
to still ship a table missing rows, because a finding you wrote as prose never prompts you to look
for its row. So after it, take the finished document and walk your own **findings** list top to
bottom — every `[Impact | Effort]`-tagged heading in the issues list, plus every `Fails`/`-` verdict
in the FIRST-principles table — and for each one ask: "which checklist row does this map to, and is
that row actually in my table?" A finding discussed anywhere in the document with no corresponding
row is a defect in the table, not an acceptable omission. Observed real misses of exactly this kind:
a FIRST `Self-validating: Fails` verdict (assertion-free tests), raw framework-type leakage into
tests, page objects asserting internally, fragile positional/XPath locators, SQL built by string
concatenation, dead utility classes, missing test-data cleanup, and a missing `.gitignore` — each
written up in the issues list, each absent from the table in the same draft. If a finding genuinely
maps to no row in the mapping above, that is fine and expected (the mapping does not cover every
dimension) — but confirm that by checking the mapping, not by assuming it.

## Calibration notes (learned from doing this review)

- **A missing business-step/flow layer is one of the highest-leverage findings** — it explains both duplication (§DRY) and unreadability (§business-readability) as one root cause, so name it as its own section rather than burying it inside DRY or architecture.
- **Business-readability is a distinct axis from AAA-phase-ordering.** A test can legitimately follow a step-based/workflow paradigm (appropriate for long E2E/OQ/compliance scenarios) and still fail readability if there's no vocabulary layer between raw UI actions and business intent. Judge each independently; don't let "this is intentionally not AAA" excuse "this doesn't read as a business scenario."
- **When a locator (or any pattern) looks bad, check whether the codebase's own documentation/hints already prove a simpler alternative was available** (e.g. a component's own hint comment naming a single class selector that would replace an 8-segment ID chain) — this is stronger evidence than an outside opinion that "this could probably be simplified."
- **Always look for the one file/example that gets it right** and name it as the template when recommending a fix for a real finding (e.g. "converge duplicated tests toward the shape of X") — but this is in service of making a fix actionable, not a reason to add standalone praise sections. Don't write up clean dimensions just to "balance" the criticism.
- **The output is an issues list, not a review.** A dimension with no defect gets zero lines — no heading, no "no violations found," no "verified strength" paragraph. Silence is how a clean dimension gets reported. The only exception is the FIRST-principles table, which is exhaustive by design.
- **Distinguish "acceptable trade-off, undocumented" from "actual defect."** E.g. a deterministic IV in encryption for diffable config files, or ThreadLocal-based singletons more defensive than the current execution model needs — these aren't bugs, but they should be called out so a future reader doesn't "fix" them into something worse, or so the team consciously decides whether the trade-off still holds.
- Respect explicit user exclusions strictly across every subagent research prompt — re-state the exclusion in each research prompt rather than assuming a subagent will infer it from prior context it doesn't have.
- **Synchronization/waiting strategy is frequently as high-impact as locator strategy** for UI-framework flakiness — don't let it get buried as a footnote under locators; it earns its own section (§G) precisely because teams fixate on selectors and overlook sleeps.
- **Parallelization safety and inter-test independence are related but not the same finding.** A suite can be fully order-independent under serial execution and still collide under parallel execution (shared fixtures/named records across workers). Check both; don't assume one implies the other.
- **A nonzero default retry count in CI config is itself a finding**, independent of whatever flakiness it's masking — report it even if you haven't separately identified which specific tests are flaky, since the retry policy alone tells you the team already knows the suite isn't fully reliable.
- **Dependency currency is context, not a standalone verdict** — mention an outdated core library version once, near whichever finding it explains (e.g. missing auto-wait capability explaining §G gaps), rather than as an isolated unexplained complaint.
- **Never drop a concrete, separately-verifiable finding because you assume fixing a different, larger finding will incidentally resolve it.** E.g. don't skip searching for cross-file method duplication in domain classes just because you already flagged a God Base Class or a missing business-step layer — those fixes might not touch the sibling classes at all. Each finding needs its own evidence and its own line in the document; "this will probably get fixed as a side effect of #2" is not a substitute for checking, and if a fix doesn't actually cover it, the finding was silently lost. When in doubt, run the check and report it — a fix that turns out to be free (already covered by a bigger refactor) can be noted as such at implementation time, but shouldn't be pre-emptively cut from the report.
- **Before reporting "dead code" / "unused" / "never called", prove it with a repo-wide grep.** An unused-export or unreferenced-class finding is the single easiest false positive to ship, because a symbol looks orphaned the moment you read its definition without searching for its callers. Grep the whole repo for the bare identifier — not just the directory you were reading, and not just import statements, since a symbol can be re-exported through a barrel file, referenced in a config, or used only in tests. If the grep returns any call site, there is no finding. Quote the count in the writeup (`0 references outside its own definition`) so a reader can re-run the same check; if you cannot state that count, you have not done the check and must not report the finding. Observed real false positive: a builder factory reported as "never referenced" and "speculative" while being used by every test that needed test data.
- **Before reporting a logic/operator/precedence bug, trace the actual runtime values.** Claiming a config expression silently misbehaves (e.g. "this `&&` binds wrong, so traces are discarded") is a strong, specific accusation, and it is wrong if you inferred it from the shape of the expression rather than evaluating it. Walk the real values the expression takes under the config as written and state the concrete broken outcome you derived. If the trace shows the code behaving correctly, drop the finding — an expression that merely *looks* confusing is at most a readability note, not a defect.
- **A clean-practice claim in the repo's own docs is evidence, but it is not proof — and neither is its absence.** Two distinct mistakes, and you must avoid both. Do not flag something as broken merely because the docs don't mention it. And do not skip reporting a defect you can actually see in the code merely because a README, CONTRIBUTING file or comment asserts the area is handled: read the code and let it decide. When a doc's claim and the code disagree, the code wins and the discrepancy is itself worth a line.
- **Missing-something ≠ can't-find-it.** If a check in §A-O was skipped, sampled too narrowly, or produced a "probably fine" guess instead of a grep-backed count, say so explicitly rather than letting it silently fall out of the document — an incomplete check reported as incomplete is fine; an incomplete check reported as if it were exhaustive is the actual failure mode to avoid.
- **A finding's `[Impact|Effort]` tag must state an independent verdict, never a cross-reference merge.** Don't write `Effort: High — same root cause as the layer above` or `see finding X`; that phrasing pre-emptively folds this finding into another one *before* rollup, so the "straight rollup, not a re-judgment" rule (above) then silently inherits the merge and the finding never gets its own line in Recommended Actions — even though fixing the other finding may not actually resolve this one (e.g. extracting a business-step layer doesn't force anyone to split an existing giant `@Test` method into several). If two findings share a root cause, say so in prose within each finding's body, but tag each with its own independent `[Impact|Effort]` and give each its own Recommended Actions line — let the rollup step, not the tagging step, decide whether they're presented together.
