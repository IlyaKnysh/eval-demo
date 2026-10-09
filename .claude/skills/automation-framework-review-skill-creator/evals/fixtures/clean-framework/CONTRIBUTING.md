# Contributing

## Naming conventions (enforced by convention and PR review)

| Element | Rule | Examples |
|---|---|---|
| Page object class/file | Must end in `Page` | `LoginPage`, `OrderListPage`, `OrderModifyPage`, `UserListPage`, `UserModifyPage`, `DashboardPage` |
| Shared composed helper (not a page itself) | Descriptive noun, no `Page` suffix | `EntityModifyPanel` |
| Flow/step function | Action-verb phrase describing business intent | `createOrder`, `updateOrderStatus`, `registerUser`, `changeUserRole`, `loginAsUser`, `attemptInvalidLogin` |
| Test file | Must end in `.spec.ts`, grouped under `tests/<feature>/` | `tests/orders/createOrder.spec.ts` |
| Factory module | `<entity>Factory.ts`, exports `<Entity>Builder` + `build<Entity>()` | `orderFactory.ts` → `OrderBuilder`, `buildOrder()` |
| Fixture | camelCase noun describing what it provides | `orderListPage`, `adminSession` |

No exceptions to the `Page` suffix rule exist in this repo — every class in
`src/pages/` and its file name follow it.

## Layering rules

- Tests (`tests/**/*.spec.ts`) call **flow functions** (`src/flows/`) and
  **page-object public methods** (`src/pages/`) only. Tests must not import
  `Page` or `Locator` from `@playwright/test` to perform actions directly.
  A page object may accept `Page` as a typed constructor parameter — that is
  the one expected use of the raw type outside `src/pages/` and `src/core/`.
- Page-object public methods never return a raw `Locator`. They return `this`
  for chaining, a typed value (string, boolean, another page object), or
  `void`/`Promise<void>` for terminal actions.
- Shared logic between similar page objects (e.g. the order/user modify
  panels) is factored into a composed helper (`EntityModifyPanel`), not
  copy-pasted.

## Error handling

- No empty `catch` blocks anywhere in the framework.
- When a try/catch is needed, wrap and rethrow using `withContext()` /
  `FrameworkError` from `src/utils/errors.ts` so failures carry the business
  context (e.g. "Creating order for Jane Doe: <original error>").
- Prefer letting Playwright's own error messages and auto-waiting surface
  failures over adding try/catch where it isn't needed.

## No-retry policy

`playwright.config.ts` sets `retries: 0`. A flaky test is a bug in the test or
the locator strategy, not something to paper over with retries. If a test
proves genuinely flaky due to environment factors outside our control, that
must be discussed and justified in the PR with a comment before a nonzero
retry count is introduced.

## Locators

- Prefer `getByRole`, `getByLabel`, `getByTestId` in that order of
  preference. No positional XPath, no CSS descent chains.
- Any "find the row/item containing X" lookup goes through
  `src/utils/gridUtils.ts` rather than being reimplemented per page object.

## Test data

- Never write inline object literals for `Order`/`User` test data. Use
  `OrderBuilder`/`buildOrder()` and `UserBuilder`/`buildUser()` from
  `src/factories/`.
- Never log in with a raw credential string. Use `LoginPage.loginAs(user)`
  (or the `loginAsUser` flow) with a `User` built from
  `src/factories/userFactory.ts`.
