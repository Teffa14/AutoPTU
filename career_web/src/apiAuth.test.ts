import { describe, expect, it } from "vitest";
import { authModeForPath } from "./api";

describe("career API auth routing", () => {
  it("keeps browser-local career calls on the casual identity", () => {
    expect(authModeForPath("/api/v1/portable/action")).toBe("casual");
    expect(authModeForPath("/api/v1/runs/restore")).toBe("casual");
  });

  it("keeps public catalog, challenge and leaderboard reads unauthenticated", () => {
    expect(authModeForPath("/api/v1/catalog?locale=es")).toBe("public");
    expect(authModeForPath("/api/v1/daily/2026-08-20")).toBe("public");
    expect(authModeForPath("/api/v1/daily/2026-08-20/leaderboards/simple")).toBe("public");
    expect(authModeForPath("/api/v1/shares/example-share")).toBe("public");
  });

  it("requires ranked identity for attempts and authoritative run state", () => {
    expect(authModeForPath("/api/v1/daily/2026-08-20/attempts")).toBe("ranked");
    expect(authModeForPath("/api/v1/runs/run-1")).toBe("ranked");
    expect(authModeForPath("/api/v1/runs/run-1/decisions")).toBe("ranked");
    expect(authModeForPath("/api/v1/runs/run-1/battles/battle-1")).toBe("ranked");
  });
});
