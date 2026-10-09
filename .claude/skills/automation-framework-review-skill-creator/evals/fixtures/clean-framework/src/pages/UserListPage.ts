import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { BasePage } from '@core/BasePage';
import { getUniqueGridRow } from '@utils/gridUtils';
import { UserModifyPage } from '@pages/UserModifyPage';

/** Page object for the paginated user grid. */
export class UserListPage extends BasePage {
  private static readonly GRID_TESTID = 'users-grid';

  constructor(page: Page) {
    super(page);
  }

  private get grid() {
    return this.page.getByTestId(UserListPage.GRID_TESTID);
  }

  private get inviteUserButton() {
    return this.page.getByRole('button', { name: 'Invite user' });
  }

  async expectGridVisible(): Promise<void> {
    await expect(this.grid).toBeVisible();
  }

  async expectRowWithEmail(email: string): Promise<void> {
    const row = await getUniqueGridRow(this.page, UserListPage.GRID_TESTID, email);
    await expect(row).toBeVisible();
  }

  async openInviteUserPanel(): Promise<UserModifyPage> {
    await this.inviteUserButton.click();
    const modifyPage = new UserModifyPage(this.page);
    await modifyPage.waitForOpen();
    return modifyPage;
  }

  async openUserByEmail(email: string): Promise<UserModifyPage> {
    const row = await getUniqueGridRow(this.page, UserListPage.GRID_TESTID, email);
    await row.getByRole('button', { name: 'Edit' }).click();
    const modifyPage = new UserModifyPage(this.page);
    await modifyPage.waitForOpen();
    return modifyPage;
  }
}
