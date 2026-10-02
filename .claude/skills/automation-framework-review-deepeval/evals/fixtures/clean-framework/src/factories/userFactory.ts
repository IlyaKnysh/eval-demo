import type { Role, User } from '@domain/domain';

let sequence = 0;

/**
 * Returns a suffix unique across parallel workers. `fullyParallel: true` runs
 * specs in separate worker processes, so a per-process counter plus Date.now()
 * can collide when two workers tick in the same millisecond; the worker index
 * and a random block make the value unique per process as well as within one.
 */
function nextSuffix(): string {
  sequence += 1;
  const worker = process.env.TEST_WORKER_INDEX ?? '0';
  const entropy = Math.random().toString(36).slice(2, 8);
  return `${worker}-${Date.now()}-${sequence}-${entropy}`;
}

/**
 * Builder-style factory for User entities. Every test that needs a user
 * goes through this factory (or the preconfigured role helpers below)
 * instead of writing inline object literals, so shape/defaults stay in
 * exactly one place.
 */
export class UserBuilder {
  private user: User;

  constructor() {
    const suffix = nextSuffix();
    this.user = {
      email: `qa.user.${suffix}@example.com`,
      password: 'Test-Passw0rd!',
      displayName: `QA User ${suffix}`,
      role: 'standard',
    };
  }

  withRole(role: Role): this {
    this.user.role = role;
    return this;
  }

  withEmail(email: string): this {
    this.user.email = email;
    return this;
  }

  withDisplayName(displayName: string): this {
    this.user.displayName = displayName;
    return this;
  }

  build(): User {
    return { ...this.user };
  }
}

export function buildUser(overrides: Partial<User> = {}): User {
  const builder = new UserBuilder();
  if (overrides.role) builder.withRole(overrides.role);
  if (overrides.email) builder.withEmail(overrides.email);
  if (overrides.displayName) builder.withDisplayName(overrides.displayName);
  return { ...builder.build(), ...overrides };
}

/** Seeded, environment-driven admin credentials — never a raw inline string. */
export function adminUser(): User {
  return {
    email: process.env.ADMIN_USERNAME ?? 'admin.qa@example.com',
    password: process.env.ADMIN_PASSWORD ?? 'replace-me',
    displayName: 'Admin QA',
    role: 'admin',
  };
}

/** Seeded, environment-driven standard-agent credentials. */
export function standardUser(): User {
  return {
    email: process.env.STANDARD_USERNAME ?? 'agent.qa@example.com',
    password: process.env.STANDARD_PASSWORD ?? 'replace-me',
    displayName: 'Standard Agent',
    role: 'standard',
  };
}
