import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const app = readFileSync(fileURLToPath(new URL("./App.tsx", import.meta.url)), "utf8");
const home = readFileSync(fileURLToPath(new URL("./components/HomeScreen.tsx", import.meta.url)), "utf8");
const shell = readFileSync(fileURLToPath(new URL("./components/GameShell.tsx", import.meta.url)), "utf8");

describe("career route bundle splitting", () => {
  it("keeps secondary screens out of the initial app bundle", () => {
    for (const screen of ["CreateScreen", "DailyScreen", "ProfileScreen", "ShareScreen", "TimelineScreen"]) {
      expect(app).not.toContain(`import { ${screen} } from \"./components/${screen}\";`);
      expect(app).toContain(`lazy(() => import(\"./components/${screen}\")`);
    }
  });

  it("keeps the career API out of the home startup path", () => {
    expect(app).not.toContain('import { careerApi } from "./api";');
    expect(app).toContain('import("./api")');
  });

  it("keeps account auth out of the synchronous shell startup graph", () => {
    expect(shell).not.toContain('from "../auth"');
    expect(shell).toContain('import("../auth")');
  });

  it("does not start the auth chunk before the page load settles", () => {
    expect(shell).toContain('window.addEventListener("load", loadAuth, { once: true })');
    expect(shell).toContain('window.setTimeout(() => {');
    expect(shell.indexOf('window.setTimeout(() => {')).toBeLessThan(shell.indexOf('void import("../auth")'));
  });

  it("keeps trainer sprite persistence out of the home startup path", () => {
    expect(app).not.toContain('import { trainerSpriteStorageEntry } from "./trainerSprites";');
    expect(app).toContain('import("./trainerSprites")');
  });

  it("keeps local career persistence out of the synchronous home startup graph", () => {
    expect(app).not.toContain('from "./localCareer"');
    expect(home).not.toContain('from "../localCareer"');
    expect(app).toContain('import("./localCareer")');
    expect(home).toContain('import("../localCareer")');
  });

  it("prefetches the two home destination chunks only after user intent", () => {
    expect(home).toContain('new: () => import("./CreateScreen")');
    expect(home).toContain('daily: () => import("./DailyScreen")');
    expect(home).toContain('leaderboard: () => import("./DailyScreen")');
    expect(home).toContain('onPointerEnter={() => warmHomeRoute("new")}');
    expect(home).toContain('onFocus={() => warmHomeRoute("new")}');
    expect(home).not.toContain('useEffect(() => {\n    warmHomeRoute');
  });

  it("gives lazy route failures a visible recovery path", () => {
    expect(app).toContain('import { RouteErrorBoundary } from "./components/RouteErrorBoundary";');
    expect(app).toContain('<RouteErrorBoundary locale={locale} resetKey={path}>');
    expect(app).toContain('</RouteErrorBoundary>');
  });

  it("routes locale persistence through guarded browser storage", () => {
    expect(app).toContain('readLocalStorage("career-locale")');
    expect(app).toContain('writeLocalStorage("career-locale", locale)');
  });
});
