# Transcript: eval-3 / without_skill / run-1

Task: review the Playwright/TS framework at `.claude/skills/automation-framework-review-skill-creator/evals/fixtures/clean-framework`, write `review.md`. Baseline run: no skill used, and no SKILL.md, manifest, evals.json or workspace files read (other than my own outputs dir).

## Steps

1. **Inventoried the fixture.** Ran `find . -type f | sort` and `wc -l` in the fixture dir. Result: 30 files, 1,462 lines total. Layout: `src/{core,pages,flows,factories,utils,types}`, `tests/{auth,orders,users}` (5 specs), plus config, CI workflow, README and CONTRIBUTING.
2. **Read config and docs** with `cat -n`: package.json, playwright.config.ts, tsconfig.json, .env.example, .gitignore, README.md, CONTRIBUTING.md, .github/workflows/e2e-tests.yml. What I noted:
   - `retries: 0`, `trace: retain-on-failure`, `fullyParallel`.
   - baseURL falls back to localhost.
   - No `dotenv` in dependencies.
   - CI runs `npm ci` and typecheck in two jobs that duplicate each other.
   - tsconfig `lib: ES2021`.
3. **Read core, utils, types and factories** (8 files). What I noted:
   - `networkidle` in `BasePage.waitForLoad`.
   - Cleanup fixture runs deletes one after another and throws on non-OK responses.
   - `loginAs` in fixtures duplicates the auth flow.
   - `nextSuffix()` is duplicated word for word across both factories.
   - `this.cause` is used under ES2021 lib.
   - `buildOrder` and `buildUser` handle overrides differently.
4. **Read pages, flows and specs** (14 files, 15 tests). What I noted:
   - `fillFromOrderData` ignores `notes` and refills the same SKU/Quantity fields for every item.
   - Several tests only check that a row exists.
   - `loginAs` never confirms the dashboard loaded.
   - The toast locator is page-wide.
   - Unused `expect` imports in the two ModifyPages.
5. **Confirmed with grep** (one command, several patterns, plus `ls` for lock and lint files):
   - `loginPage` fixture: defined but never used by specs.
   - `searchFor`: defined only, never called.
   - `API_BASE_URL`: 0 hits in code (only in .env.example).
   - `dotenv`: 0 hits.
   - `catch`: only in errors.ts (no empty catches).
   - `waitForTimeout|setTimeout`: 0 hits.
   - `networkidle`: 1 definition, 3 call sites.
   - `notes`: no hits in pages or flows.
   - xpath / `locator(`: 0 hits.
   - `standardUser`: used only in login.spec.
   - `cancel(`: never called by tests.
   - `exact:`: 0 hits.
   - No package-lock.json, yarn.lock or pnpm-lock.yaml. No ESLint or Prettier config.
6. **Created the outputs dir** with `mkdir -p` and wrote review.md. Then corrected the severity totals line: on recount it is 23 findings, 5 High, 5 Medium, 1 Low–Medium, 9 Low, 3 Info.

## Subagents
None. The framework is small (about 1.5k lines), so I read every file directly.

## Decisions
- **Verdict "Approve with changes, not as-is".** The user expects a clean bill of health. The architecture really is strong, and section 4 says so with specifics. But F1–F3 are false-green tests, and F4/F5 break local and CI runs, so I didn't rubber-stamp it.
- **Rated F1–F3 High.** The test names claim behavior that the code never exercises. That is a correctness problem in the suite itself, not a style point.
- **F19 (`Error.cause` type) marked "verify", Low.** I couldn't run tsc because there's no node_modules, and some typings packages may declare `cause`.
- **F9, F13 and F2 depend on assumptions about app behavior.** I listed those assumptions in section 6 and kept the severities moderate.
- **Added a Config/CI area** beyond the 8 requested, because two High findings are there.
- **Left out:**
  - `retries: 0` on CI, because it's a documented, deliberate policy.
  - Assertions living in page objects (`expect*` methods), because it's a consistent, documented design choice.
  - The `Page` suffix on panel POs, which is only an Info note since the convention is documented.
- **Did not modify the framework under review.**

## Problems
- The first grep command exited with code 2 only because `ls` on the missing lock and lint files failed. All grep results came back. No other issues.
