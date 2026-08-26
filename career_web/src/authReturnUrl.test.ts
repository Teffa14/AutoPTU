import { describe, expect, it } from "vitest";

import { authReturnUrlForLocation } from "./auth";

describe("ranked auth return URL", () => {
  it("keeps the GitHub Pages project-site base and daily hash route", () => {
    expect(authReturnUrlForLocation("https://teffa14.github.io", "/AutoPTU/career-game/", "#/daily")).toBe(
      "https://teffa14.github.io/AutoPTU/career-game/#/daily",
    );
  });

  it("normalizes a nested project-site route back to the app root", () => {
    expect(authReturnUrlForLocation("https://teffa14.github.io", "/AutoPTU/career-game/new", "")).toBe(
      "https://teffa14.github.io/AutoPTU/career-game/",
    );
  });

  it("keeps local development on the local career root", () => {
    expect(authReturnUrlForLocation("http://localhost:5173", "/career-game/", "#/daily")).toBe(
      "http://localhost:5173/career-game/#/daily",
    );
  });
});
