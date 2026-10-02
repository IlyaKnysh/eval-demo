import type { Locator, Page } from '@playwright/test';
import { withContext } from './errors';

/**
 * Centralized helper for the "find the grid row containing X" pattern used
 * across OrderModifyPage, UserModifyPage and any future grid-backed page.
 * Implemented once here instead of being reinvented per page object.
 *
 * Relies on semantic roles (table/row/cell via getByRole) rather than
 * positional CSS/XPath descent, so it stays stable as markup evolves.
 */
export function findGridRowByText(page: Page, gridTestId: string, rowText: string): Locator {
  const grid = page.getByTestId(gridTestId);
  return grid.getByRole('row').filter({ hasText: rowText });
}

/**
 * Resolves a single grid row and asserts exactly one match was found,
 * failing fast with useful context instead of silently returning an
 * ambiguous multi-element locator.
 */
export async function getUniqueGridRow(
  page: Page,
  gridTestId: string,
  rowText: string,
): Promise<Locator> {
  return withContext(`Locating unique row containing "${rowText}" in grid "${gridTestId}"`, async () => {
    const row = findGridRowByText(page, gridTestId, rowText);
    await row.first().waitFor({ state: 'visible' });
    const count = await row.count();
    if (count !== 1) {
      throw new Error(`Expected exactly 1 matching row, found ${count}`);
    }
    return row;
  });
}
