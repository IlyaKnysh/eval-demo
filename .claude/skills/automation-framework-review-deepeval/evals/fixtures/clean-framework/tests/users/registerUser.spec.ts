import { test } from '@core/fixtures';
import { registerUser } from '@flows/userFlows';
import { buildUser } from '@factories/userFactory';

test.describe('User registration', () => {
  test('registers a new standard user', { tag: '@smoke' }, async ({ adminSession, userListPage, createdRecords }) => {
    // Arrange
    const user = buildUser({ role: 'standard' });

    // Act
    createdRecords.user(user.email);
    await registerUser(adminSession, user);

    // Assert
    await userListPage.expectGridVisible();
    await userListPage.expectRowWithEmail(user.email);
  });

  test('registers a new admin user', async ({ adminSession, userListPage, createdRecords }) => {
    const user = buildUser({ role: 'admin' });

    createdRecords.user(user.email);
    await registerUser(adminSession, user);

    await userListPage.expectRowWithEmail(user.email);
  });

  test('registers a new read-only user', async ({ adminSession, userListPage, createdRecords }) => {
    const user = buildUser({ role: 'read-only' });

    createdRecords.user(user.email);
    await registerUser(adminSession, user);

    await userListPage.expectRowWithEmail(user.email);
  });
});
