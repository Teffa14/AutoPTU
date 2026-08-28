import { afterEach, describe, expect, it } from "vitest";

import { readLocalStorage, writeLocalStorage } from "./browserStorage";

const originalWindow = globalThis.window;

afterEach(() => {
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    writable: true,
    value: originalWindow,
  });
});

describe("browser storage guard", () => {
  it("falls back when the localStorage getter is blocked", () => {
    Object.defineProperty(globalThis, "window", {
      configurable: true,
      value: Object.defineProperty({}, "localStorage", {
        configurable: true,
        get() {
          throw new Error("storage blocked");
        },
      }),
    });

    expect(readLocalStorage("career-locale")).toBeNull();
    expect(writeLocalStorage("career-locale", "en")).toBe(false);
  });

  it("reads and writes normally when storage is available", () => {
    const values = new Map<string, string>();
    Object.defineProperty(globalThis, "window", {
      configurable: true,
      value: {
        localStorage: {
          getItem: (key: string) => values.get(key) ?? null,
          setItem: (key: string, value: string) => { values.set(key, value); },
        },
      },
    });

    expect(readLocalStorage("career-locale")).toBeNull();
    expect(writeLocalStorage("career-locale", "en")).toBe(true);
    expect(readLocalStorage("career-locale")).toBe("en");
  });
});
