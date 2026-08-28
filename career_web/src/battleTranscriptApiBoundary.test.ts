import { describe, expect, it } from "vitest";

import apiSource from "./api.ts?raw";

describe("battle transcript API boundary", () => {
  it("normalizes malformed legacy event collections before BattleScreen receives them", () => {
    expect(apiSource).toContain("function normalizeBattleTranscriptEvents");
    expect(apiSource).toContain("Array.isArray((transcript as { events?: unknown }).events)");
    expect(apiSource).toContain("events: []");
    expect(apiSource).toContain("const safeTranscript = normalizeBattleTranscriptEvents(transcript)");
    expect(apiSource).toContain("battleCache.set(key, safeTranscript)");
    expect(apiSource).toContain("return safeTranscript");
  });
});
