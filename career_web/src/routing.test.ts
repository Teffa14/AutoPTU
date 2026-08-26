import { describe, expect, it } from "vitest";
import { careerNavigationTarget, careerPathFromLocation, normalizeCareerBasePath } from "./routing";

describe("GitHub Pages career routing", () => {
  it("uses hash routes so client navigation never requests a missing Pages document", () => {
    expect(careerNavigationTarget("new", "/AutoPTU/career-game/")).toBe("/AutoPTU/career-game/#/new");
    expect(careerNavigationTarget("run/demo", "/AutoPTU/career-game/")).toBe("/AutoPTU/career-game/#/run/demo");
    expect(careerNavigationTarget("", "/AutoPTU/career-game/")).toBe("/AutoPTU/career-game/");
  });

  it("prefers the hash route while retaining legacy deep-link compatibility", () => {
    expect(careerPathFromLocation("/AutoPTU/career-game/", "/AutoPTU/career-game/", "#/new")).toBe("new");
    expect(careerPathFromLocation("/AutoPTU/career-game/", "/AutoPTU/career-game/", "#/run/demo")).toBe("run/demo");
    expect(careerPathFromLocation("/AutoPTU/career-game/new", "/AutoPTU/career-game/")).toBe("new");
    expect(careerPathFromLocation("/AutoPTU/career-game/", "/AutoPTU/career-game/")).toBe("");
  });

  it("does not mistake unrelated repository paths for Career routes", () => {
    expect(careerPathFromLocation("/AutoPTU/other", "/AutoPTU/career-game/")).toBe("");
    expect(normalizeCareerBasePath("/AutoPTU/career-game///")).toBe("/AutoPTU/career-game");
  });
});
