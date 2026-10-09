# Checklist tab input: SubTrack Admin automation framework

Secondary deliverable. The same table appears at the end of review.md; finding numbers refer to review.md.


Rows are limited to checks this code review can answer. `Tools`, `Strategy` and `AI Usage` rows, and interview-only `Running` and `Processes` rows, are omitted. The "Tests remain independent under parallel execution" row is omitted because no parallel execution is configured.

| Section | Check | Status (+/-) | Comments |
| --- | --- | --- | --- |
| Framework | Framework is consistent | - | Auth is expressed three ways: `User`/`AuthContext`, `Config.API_TOKEN` and `os.getenv` (finding 11). `update_name` fills a non-name field in 2 of 4 modify pages (finding 7). |
| Framework | Framework follows a layered architecture | - | 3 raw `requests` calls in 2 API test files and 11 raw `page.get_by_*` calls in 3 test files bypass the domain layer. `core/auth.py` holds login-screen locators. No step layer (findings 11, 15, 17, 18). |
| Framework | Framework complies with DRY | - | 4 `*ModifyPage` clones (20 methods, only 3 lines differ per file). 5 hybrid tests repeat one 4-step skeleton. 13 client methods repeat the same body (findings 15, 16, 22). |
| Framework | Framework complies with KISS | - | Hand-rolled tracing fixture and hook re-implement pytest-playwright's built-in `--tracing` and introduce a precedence bug at `conftest.py:90` (finding 9). |
| Framework | Framework complies with YAGNI | - | 0 references to `LoginPage`, `ContactModifyPage`, `ContactBuilder`, `close_ticket` and `DEFAULT_TIMEOUT_MS`. The `auth_client` fixture is unused, and 3 markers are declared but never applied (findings 18, 21). |
| Framework | Framework complies with SOLID | + | No god base class (`BaseApiClient` is 20 lines), no closed switch chains and no LSP or ISP breaks. The one DIP-style inconsistency (raw `requests` in 2 tests) is logged under layering (finding 11). |
| Framework | Framework complies with language standards | - | No linter config; judged against PEP 8. 2 of 9 page modules are PascalCase, and 2 of 10 page classes lack the `Page` suffix (finding 24). |
| Framework | Presetups are implemented at the optimal available level | - | Data presetup is API-based (correct level), but the auth presetup raises `AttributeError` for 15 of 23 tests, ticket and subscription clients are never authenticated, and API tests log in through the UI (findings 1, 2, 10). |
| Framework | Unconditional waits are not a common practice | + | 0 `time.sleep` / `wait_for_timeout` / `setTimeout` hits. Separately, 0 `expect()` web-first assertions, and 2 one-shot reads are racy (finding 19). |
| Framework | Tests are atomic and independent | - | Module-level `_CREATED_TICKET_IDS` order dependency. Shared-config mutation. Cross-run name collisions plus 0 cleanup for 19 creates (findings 3, 4, 5, 8, 14). |
| Framework | Test implementation is done at the optimal level (API, UI...) | - | All 11 API-only tests start a traced browser context, and 3 also do a UI login (finding 10). The hybrid tests' level choice (API setup, UI action, API verify) is appropriate. The overall split needs the questionnaire's stated strategy. |
| Framework | Core libraries/framework/language versions are reasonably current | + | `playwright==1.47.0`, `pytest==8.3.3`, Python 3.11. Playwright is about 2 years old as of this review but has every capability the fixes need (`expect`, tracing, `exact=`). |
| Framework | No hardcoded credentials/secrets in the test codebase | - | 1 hit: `config.py:26` `INVOICING_PROVIDER_API_KEY = "sk-fake1234567890"`, despite `.env.example:14` documenting it as an env var (finding 13). |
| Running | Steps have a sufficient level of documentation for reporting | - | 0 markers applied, so the HTML report is flat. 3 test names misstate what they test (findings 7, 21). |
| Running | When tests fail, there are mechanisms to easily find the cause | - | HTML report and traces are uploaded (`ci.yml:33-46`), but traces are discarded on every setup-phase failure because of the `conftest.py:90` precedence. Swallowing helpers reduce failures to a bare `assert False` (findings 9, 20). |
| Running | Test stability is at a sufficient level | - | `reruns = 2` in both `pytest.ini:14` and `ci.yml:31`, a nonzero retry default that signals known instability. Deterministic failures are retried too (finding 12). |
| Running | There is a way to track run results over time | - | Only a per-run `report.html` artifact. No JUnit XML, Allure history or trend store (`ci.yml:33-38`). |
| Running | Tests are integrated into CI/CD, not run purely manually/on-demand | + | GitHub Actions runs on push and pull request to `main` (`ci.yml:3-7`). |
| Processes | Tests are properly documented | - | Module docstrings exist, but 3 of 23 test names misdescribe their body, and 5 of 23 tests do not validate their stated behavior. Self-validation has no dedicated checklist row, so it is recorded here (findings 6, 7). |
| Processes | A failure-handling strategy is implemented (bug reporting → flaky rerun → failure skipping) | - | Blanket reruns only. 0 `flaky` / `xfail` / `skip(reason=)` markers and no ticket linkage. 2 of 2 catch sites swallow (findings 12, 20, 21). Corroborate with the questionnaire. |
