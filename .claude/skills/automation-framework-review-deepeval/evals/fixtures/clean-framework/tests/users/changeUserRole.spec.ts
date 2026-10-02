import { test } from '@core/fixtures';
import { registerUser, changeUserRole } from '@flows/userFlows';
import { buildUser } from '@factories/userFactory';

test.describe('User role changes', () => {
  test(
    'promotes a standard user to admin',
    { tag: '@smoke' },
    async ({ adminSession, userListPage, createdRecords }) => {
      const user = buildUser({ role: 'standard' });
      createdRecords.user(user.email);
      await registerUser(adminSession, user);

      await changeUserRole(adminSession, user.email, 'admin');

      const modifyPage = await userListPage.openUserByEmail(user.email);
      await modifyPage.expectRoleFieldValue('admin');
    },
  );

  test('demotes an admin user to read-only', async ({ adminSession, userListPage, createdRecords }) => {
    const user = buildUser({ role: 'admin' });
    createdRecords.user(user.email);
    await registerUser(adminSession, user);

    await changeUserRole(adminSession, user.email, 'read-only');

    const modifyPage = await userListPage.openUserByEmail(user.email);
    await modifyPage.expectRoleFieldValue('read-only');
  });
});
