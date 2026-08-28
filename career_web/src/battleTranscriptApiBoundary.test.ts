import { describe, expect, it } from "vitest";

import apiSource from "./api.ts?raw";

describe("battle transcript API boundary", () => {
  it("normalizes malformed legacy event collections before BattleScreen receives them", () => {
    expect(apiSource).toContain("function normalizeBattleTranscriptEvents");
    expect(apiSource).toContain("Array.isArray((transcript as { events?: unknown }).events)");
    expect(apiSource).toContain("events: []");
    expect(apiSource).toContain("const safeTranscript = normalizeBattleTranscriptHash(normalizeBattleTranscriptSpec(normalizeBattleTranscriptInitialState(normalizeBattleTranscriptEvents(transcript))))");
    expect(apiSource).toContain("battleCache.set(key, safeTranscript)");
    expect(apiSource).toContain("return safeTranscript");
  });

  it("normalizes a missing or null legacy initial battle state before BattleArena dereferences it", () => {
    expect(apiSource).toContain("function normalizeBattleTranscriptInitialState");
    expect(apiSource).toContain("const rawInitialState = (transcript as { initial_state?: unknown }).initial_state");
    expect(apiSource).toContain("rawInitialState && typeof rawInitialState === \"object\"");
    expect(apiSource).toContain("initial_state: { grid: { width: 1, height: 1 }, combatants: [] } as BattleTranscript[\"initial_state\"]");
    expect(apiSource).toContain("normalizeBattleTranscriptInitialState(normalizeBattleTranscriptEvents(transcript))");
  });

  it("normalizes a missing or null legacy battle spec before BattleScreen receives it", () => {
    expect(apiSource).toContain("function normalizeBattleTranscriptSpec");
    expect(apiSource).toContain("const rawSpec = (transcript as { spec?: unknown }).spec");
    expect(apiSource).toContain("rawSpec && typeof rawSpec === \"object\"");
    expect(apiSource).toContain("spec: {} as BattleTranscript[\"spec\"]");
    expect(apiSource).toContain("normalizeBattleTranscriptSpec(normalizeBattleTranscriptInitialState(normalizeBattleTranscriptEvents(transcript)))");
  });

  it("normalizes a missing or non-string legacy battle hash before BattleScreen slices it", () => {
    expect(apiSource).toContain("function normalizeBattleTranscriptHash");
    expect(apiSource).toContain("const rawHash = (transcript as { sha256?: unknown }).sha256");
    expect(apiSource).toContain("typeof rawHash === \"string\"");
    expect(apiSource).toContain("sha256: \"legacy\"");
    expect(apiSource).toContain("normalizeBattleTranscriptHash(normalizeBattleTranscriptSpec(normalizeBattleTranscriptInitialState(normalizeBattleTranscriptEvents(transcript))))");
  });
});