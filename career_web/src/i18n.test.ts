import { describe, expect, it } from "vitest";

import { t } from "./i18n";

describe("career copy", () => {
  it("keeps complete and distinct Spanish and English navigation labels", () => {
    const spanish = t("es");
    const english = t("en");

    for (const key of ["season", "trainer", "timeline", "daily"] as const) {
      expect(spanish[key]).toBeTruthy();
      expect(english[key]).toBeTruthy();
      expect(spanish[key]).not.toBe(english[key]);
    }
  });

  it("preserves the fixed opening resources in both languages", () => {
    expect(t("es").createBody).toContain("Diez Poké Balls");
    expect(t("en").createBody).toContain("Ten Poké Balls");
  });
});
