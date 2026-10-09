/**
 * Consistent error-wrapping convention for the framework.
 *
 * Any code that catches an error and needs to add context re-throws a
 * `FrameworkError` that preserves the original error as `cause`. Empty
 * catch blocks are never used — see CONTRIBUTING.md "Error handling".
 */
export class FrameworkError extends Error {
  constructor(message: string, cause?: unknown) {
    super(cause instanceof Error ? `${message}: ${cause.message}` : message);
    this.name = 'FrameworkError';
    if (cause !== undefined) {
      this.cause = cause;
    }
  }
}

/**
 * Wraps a promise-returning action, rethrowing any failure as a
 * FrameworkError annotated with the supplied context. Use this instead of
 * bare try/catch blocks scattered through page objects and flows.
 */
export async function withContext<T>(context: string, action: () => Promise<T>): Promise<T> {
  try {
    return await action();
  } catch (error) {
    throw new FrameworkError(context, error);
  }
}
