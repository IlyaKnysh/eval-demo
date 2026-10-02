# SubTrack Admin – Automation Framework

Python + pytest + Playwright (sync API) hybrid UI/API test suite for the SubTrack
subscription-billing admin console (accounts, contacts, support tickets, and
subscription plans).

## Stack

- Python 3.11
- pytest 8.x
- Playwright (sync API) for UI tests
- `requests`-based wrapper clients for API tests
- pytest-html for local reports, Allure-style trace capture on retry in CI
- pytest-rerunfailures for CI stability

## Layout

```
src/
  core/            # config, browser/session fixtures helpers, typed auth context
  pages/            # Page Object classes (Playwright)
  api_clients/       # API client wrapper classes (requests)
  factories/         # test-data builder classes
tests/
  ui/                # UI-only Playwright tests
  api/               # API-only tests
  hybrid/            # combined UI+API flows
conftest.py          # fixture composition (browser, page, api clients, auth)
pytest.ini
requirements.txt
.env.example
.github/workflows/ci.yml
```

## Running locally

```
cp .env.example .env
pip install -r requirements.txt
playwright install --with-deps chromium
pytest
```

## Reporting

Every CI run publishes an HTML report (`report.html`) as a build artifact, and
Playwright traces are captured `on-first-retry` so failures can be replayed with
`playwright show-trace trace.zip`.
