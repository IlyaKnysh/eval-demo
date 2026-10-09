import { test } from '@core/fixtures';
import type { DashboardPage } from '@pages/DashboardPage';
import type { Role, User } from '@domain/domain';
import { withContext } from '@utils/errors';

/**
 * Business-step layer for user-management actions.
 */

/** Invites (registers) a new user from the dashboard. */
export async function registerUser(dashboard: DashboardPage, userData: User): Promise<void> {
  await withContext(`Registering user ${userData.email}`, async () => {
    await test.step(`Register user ${userData.email}`, async () => {
      const listPage = await dashboard.goToUsers();
      const modifyPage = await listPage.openInviteUserPanel();
      await modifyPage.fillFromUserData(userData);
      await modifyPage.save();
    });
  });
}

/** Locates an existing user by email and changes their role. */
export async function changeUserRole(dashboard: DashboardPage, email: string, role: Role): Promise<void> {
  await withContext(`Changing role for ${email} to ${role}`, async () => {
    await test.step(`Change role for ${email} to "${role}"`, async () => {
      const listPage = await dashboard.goToUsers();
      const modifyPage = await listPage.openUserByEmail(email);
      await modifyPage.setRole(role);
      await modifyPage.save();
    });
  });
}
