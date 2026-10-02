# Storefront Admin E2E

End-to-end UI test automation for the Storefront Admin panel (order management,
user management, authentication), built with TypeScript, Playwright and
Playwright Test.

## Stack

- TypeScript
- Playwright Test (`@playwright/test`)
- GitHub Actions for CI

## Layout

```
src/
  core/         Slim BasePage, shared EntityModifyPanel helper, fixtures.ts (DI)
  pages/        Page objects (one class per screen/panel)
  flows/        Business-step layer composing page objects for tests
  factories/    Test-data builders (OrderBuilder, UserBuilder)
  utils/        Cross-cutting helpers (grid lookups, error wrapping)
  types/        Shared domain types (User, Role, OrderData, ...)
tests/
  auth/         Login tests
  orders/       Order creation / status update tests
  users/        User registration / role change tests
```

## Getting started

1. Copy `.env.example` to `.env` and fill in your environment's base URL and
   seeded credentials.
2. `npm ci`
3. `npx playwright install`
4. `npm test` (full suite) or `npm run test:smoke` (`@smoke`-tagged subset).

## Architecture

- **Page objects** (`src/pages/`) wrap a single screen or panel. Every public
  method returns either a primitive/typed value, `this` (for chaining), or the
  next page object — never a raw Playwright `Locator`.
- **Flows** (`src/flows/`) compose page-object calls into reusable business
  actions (`createOrder`, `registerUser`, `changeUserRole`, ...). Tests call
  flows and page-object public methods; they never import `Page`/`Locator`
  from `@playwright/test` to perform actions directly (only page objects take
  a `Page` as a typed constructor parameter).
- **Fixtures** (`src/core/fixtures.ts`) provide page objects and authenticated
  sessions via Playwright's `test.extend`. There is no shared God base class;
  `BasePage` only provides navigation, and cross-cutting setup is composed via
  fixtures instead of inheritance.
- **Factories** (`src/factories/`) are the single source of truth for test
  data shape. `OrderBuilder` / `UserBuilder` are used by every test that needs
  an order or user — no inline object literals are duplicated per test.

## Naming conventions

These are followed consistently across the repo:

- Every page-object file and class name ends in `Page` (`LoginPage`,
  `OrderListPage`, `OrderModifyPage`, `UserListPage`, `UserModifyPage`,
  `DashboardPage`). Shared, non-page helpers composed *into* page objects
  (e.g. `EntityModifyPanel`) intentionally do not use the `Page` suffix,
  since they are not page objects themselves.
- Every flow-layer function is an action-verb phrase describing business
  intent: `createOrder`, `updateOrderStatus`, `registerUser`,
  `changeUserRole`, `loginAsUser`, `attemptInvalidLogin`.
- Every test file ends in `.spec.ts`.
- Factories are named `<entity>Factory.ts` and export a `<Entity>Builder`
  class plus `build<Entity>()` convenience functions.
- See `CONTRIBUTING.md` for the full convention list and rationale.

## CI

- Pull requests run the `@smoke`-tagged subset only (`e2e-tests.yml`,
  `smoke` job).
- Merges to `main`, a nightly schedule, and manual dispatch run the full
  suite (`full-regression` job).
- Both jobs publish the Playwright HTML report as a build artifact on every
  run (including failures).
