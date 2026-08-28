import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const app = readFileSync(fileURLToPath(new URL("./App.tsx", import.meta.url)), "utf8");
const home = readFileSync(fileURLToPath(new URL("./components/HomeScreen.tsx", import.meta.url)), "utf8");

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

  it("keeps local career persistence out of the synchronous startup graph", () => {
    expect(app).not.toContain('from "./localCareer"');
    expect(home).not.toContain('from "../localCareer"');
    expect(app).toContain('import("./localCareer")');
    expect(home).toContain('import("../localCareer")');
  });
});
