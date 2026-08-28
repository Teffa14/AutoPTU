import { afterEach, describe, expect, it } from "vitest";

import { authHeaders } from "./auth";

const originalStorageDescriptor = Object.getOwnPropertyDescriptor(globalThis, "localStorage");

afterEach(() => {
  if (originalStorageDescriptor) {
    Object.defineProperty(globalThis, "localStorage", originalStorageDescriptor);
  } else {
    delete (globalThis as typeof globalThis & { localStorage?: Storage }).localStorage;
  }
});

describe("casual auth storage fallback", () => {
  it("keeps a stable casual identity when browser storage is unavailable", async () => {
    Object.defineProperty(globalThis, "localStorage", {
      configurable: true,
      get() {
        throw new Error("storage blocked");
      },
    });

    const first = await authHeaders("casual");
    const second = await authHeaders("casual");

    expect(first["X-Career-User"]).toBeTruthy();
    expect(second["X-Career-User"]).toBe(first["X-Career-User"]);
  });
});
