import { beforeEach, describe, expect, it, vi } from "vitest";

const authMocks = vi.hoisted(() => ({
  signInWithPassword: vi.fn(),
}));

vi.mock("@supabase/supabase-js", () => ({
  createClient: () => ({
    auth: {
      signInWithPassword: authMocks.signInWithPassword,
    },
  }),
}));

describe("ranked ID auth", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.stubEnv("VITE_SUPABASE_URL", "https://example.supabase.co");
    vi.stubEnv("VITE_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test");
    vi.stubEnv("VITE_API_URL", "https://api.example/functions/v1/career-api");
    authMocks.signInWithPassword.mockReset();
    vi.unstubAllGlobals();
  });

  it("normalizes a public ranked ID into an internal Supabase login", async () => {
    const { normalizeRankedId, rankedEmailForId } = await import("./auth");

    expect(normalizeRankedId(" Stefano_14 ")).toBe("stefano_14");
    expect(rankedEmailForId("Stefano_14")).toBe("stefano_14@ranked.autoptu.app");
    expect(() => normalizeRankedId("no spaces allowed")).toThrow(/Ranked ID/);
  });

  it("signs in directly without OAuth, email or redirect options", async () => {
    authMocks.signInWithPassword.mockResolvedValue({ data: { session: {} }, error: null });
    const { signInWithRankedId } = await import("./auth");

    await signInWithRankedId("trainer-7", "secret123");

    expect(authMocks.signInWithPassword).toHaveBeenCalledWith({
      email: "trainer-7@ranked.autoptu.app",
      password: "secret123",
    });
  });

  it("registers through the edge function then signs in on-page", async () => {
    authMocks.signInWithPassword.mockResolvedValue({ data: { session: {} }, error: null });
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 201, json: vi.fn() });
    vi.stubGlobal("fetch", fetchMock);
    const { registerRankedAccount } = await import("./auth");

    await registerRankedAccount("trainer-7", "secret123");

    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.example/functions/v1/career-api/auth/register",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ranked_id: "trainer-7", password: "secret123" }),
      }),
    );
    expect(authMocks.signInWithPassword).toHaveBeenCalledWith({
      email: "trainer-7@ranked.autoptu.app",
      password: "secret123",
    });
  });
});
