import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, careerApi } from "./api";

describe("career API request timeout", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("fails a request that never receives a response instead of hanging forever", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn((_input: RequestInfo | URL, init?: RequestInit) => new Promise<Response>((_resolve, reject) => {
      init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")), { once: true });
    })));

    const pending = careerApi.catalog("es");
    const rejection = expect(pending).rejects.toMatchObject<ApiError>({
      name: "ApiError",
      status: 408,
    });

    await vi.advanceTimersByTimeAsync(15_000);
    await rejection;
  });
});
