import { beforeEach, describe, expect, it, vi } from "vitest";

const authMocks = vi.hoisted(() => ({
  signInWithPassword: vi.fn(),
  signUp: vi.fn(),
}));

vi.mock("@supabase/supabase-js", () => ({
  createClient: () => ({
    auth: {
      signInWithPassword: authMocks.signInWithPassword,
      signUp: authMocks.signUp,
    },
  }),
}));

describe("ranked password auth", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.stubEnv("VITE_SUPABASE_URL", "https://example.supabase.co");
    vi.stubEnv("VITE_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test");
    authMocks.signInWithPassword.mockReset();
    authMocks.signUp.mockReset();
  });

  it("signs in on-page without a redirect URL", async () => {
    authMocks.signInWithPassword.mockResolvedValue({ data: { session: {} }, error: null });
    const { signInWithPassword } = await import("./auth");

    await signInWithPassword(" trainer@example.com ", "secret12");

    expect(authMocks.signInWithPassword).toHaveBeenCalledWith({
      email: "trainer@example.com",
      password: "secret12",
    });
  });

  it("creates a permanent account and reports an immediate session", async () => {
    authMocks.signUp.mockResolvedValue({
      data: { session: { access_token: "token", user: { is_anonymous: false } } },
      error: null,
    });
    const { signUpWithPassword } = await import("./auth");

    await expect(signUpWithPassword("new@example.com", "secret12")).resolves.toEqual({ signedIn: true });
    expect(authMocks.signUp).toHaveBeenCalledWith({ email: "new@example.com", password: "secret12" });
  });

  it("reports when signup did not create a browser session", async () => {
    authMocks.signUp.mockResolvedValue({ data: { session: null }, error: null });
    const { signUpWithPassword } = await import("./auth");

    await expect(signUpWithPassword("new@example.com", "secret12")).resolves.toEqual({ signedIn: false });
  });
});
