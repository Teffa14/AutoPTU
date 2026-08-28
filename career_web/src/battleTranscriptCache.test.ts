import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const apiSource = readFileSync(
  fileURLToPath(new URL("./api.ts", import.meta.url)),
  "utf8",
);

describe("battle transcript cache", () => {
  it("keeps replay retention bounded in long browser careers", () => {
    expect(apiSource).toContain("MAX_BATTLE_CACHE_ENTRIES");
    expect(apiSource).toContain("rememberBattleTranscript");
    expect(apiSource).toContain("battleCache.delete(oldestKey)");
    expect(apiSource.match(/battleCache\.set\(key, safeTranscript\)/g)).toHaveLength(1);
  });

  it("coalesces concurrent loads of the same uncached battle", () => {
    expect(apiSource).toContain("battleRequests");
    expect(apiSource).toContain("battleRequests.get(key)");
    expect(apiSource).toContain("battleRequests.set(key, requestPromise)");
    expect(apiSource).toContain("battleRequests.delete(key)");
  });
});
