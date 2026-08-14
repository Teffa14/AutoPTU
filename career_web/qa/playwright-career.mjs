import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";

const base = "http://127.0.0.1:8010/career-game/";
const output = "test-results/career-qa";
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });

async function metrics(page) {
  return page.evaluate(() => ({
    width: innerWidth,
    height: innerHeight,
    scrollWidth: document.documentElement.scrollWidth,
    scrollHeight: document.documentElement.scrollHeight,
    horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
    canvasCount: document.querySelectorAll("canvas").length,
    navCount: document.querySelectorAll("nav.game-nav").length,
  }));
}

try {
  const desktop = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await desktop.addInitScript(() => localStorage.setItem("autoptu-career-development-user", "career-qa-user"));
  const page = await desktop.newPage();
  const errors = [];
  page.on("console", (message) => message.type() === "error" && errors.push(message.text()));
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(base, { waitUntil: "networkidle" });
  await page.screenshot({ path: `${output}/desktop-create.png` });
  const initial = await metrics(page);
  if (initial.horizontalOverflow || initial.canvasCount !== 0) throw new Error(`Bad creation fit: ${JSON.stringify(initial)}`);

  await page.getByRole("button", { name: "ES", exact: true }).click();
  await page.getByRole("button", { name: "EN", exact: true }).click();
  await page.getByRole("button", { name: /advanced/i }).click();
  await page.getByRole("button", { name: /simple/i }).click();
  await page.getByLabel("Nombre").fill("Ari Vale");
  await page.getByRole("button", { name: /contrato|contract/i }).click();
  await page.waitForURL(/\/career-game\/run\//, { timeout: 20_000 });
  await page.screenshot({ path: `${output}/desktop-season.png` });
  const season = await metrics(page);
  if (season.horizontalOverflow || season.canvasCount !== 0 || season.navCount !== 1) throw new Error(`Bad season state: ${JSON.stringify(season)}`);

  await page.getByRole("button", { name: /Entrenador|Trainer/ }).click();
  await page.waitForURL(/\/profile\//);
  await page.getByRole("button", { name: /Historia|Story/ }).click();
  await page.waitForURL(/\/timeline\//);
  await page.getByRole("button", { name: /Reto diario|Daily challenge/ }).click();
  await page.waitForURL(/\/daily$/);
  await page.getByRole("button", { name: "advanced", exact: true }).click();
  await page.getByRole("button", { name: "simple", exact: true }).click();
  await page.screenshot({ path: `${output}/desktop-daily.png` });
  await page.getByRole("button", { name: /Temporada|Season/ }).click();
  await page.waitForURL(/\/run\//);
  await page.locator(".decision-options button").last().click();
  await page.getByRole("button", { name: /Girar la ruleta|Spin the wheel/ }).click();
  await page.locator(".roulette-overlay.spinning").waitFor({ state: "visible" });
  await page.locator(".roulette-overlay.settling").waitFor({ state: "visible", timeout: 45_000 });
  const rouletteResult = page.getByRole("button", { name: /Entrar al campo de batalla|Enter the battlefield/ });
  await rouletteResult.waitFor({ state: "visible", timeout: 10_000 });
  if (!/\/career-game\/run\//.test(page.url())) throw new Error("Roulette navigated away before the result was accepted.");
  await page.screenshot({ path: `${output}/desktop-roulette-result.png` });
  await rouletteResult.click();
  await page.waitForURL(/\/battle\//, { timeout: 45_000 });
  const battleUrl = page.url();
  await page.locator("canvas").waitFor({ state: "visible", timeout: 15_000 });
  if (await page.locator(".hp-track").count() !== 2) throw new Error("Battle HUD does not expose both HP bars.");
  if (await page.locator(".battle-stats").count() !== 2) throw new Error("Battle HUD does not expose both PTU stat blocks.");
  await page.getByRole("button", { name: "2×" }).click();
  await page.waitForTimeout(900);
  await page.screenshot({ path: `${output}/desktop-battle.png` });
  await page.getByRole("button", { name: /Saltar|Skip/ }).click();
  await page.waitForTimeout(250);
  await page.getByRole("button", { name: /Continuar la carrera|Continue career/ }).waitFor();
  await page.screenshot({ path: `${output}/desktop-battle-result.png` });
  const battle = await metrics(page);
  if (battle.canvasCount !== 1 || battle.navCount !== 0 || battle.horizontalOverflow) throw new Error(`Bad battle isolation: ${JSON.stringify(battle)}`);
  await page.getByRole("button", { name: /Continuar la carrera|Continue career/ }).click();
  await page.waitForURL(/\/run\//);
  if ((await metrics(page)).canvasCount !== 0) throw new Error("Pixi canvas remained mounted after leaving battle.");
  await page.locator(".season-footer .text-action").click();
  await page.locator(".retire-confirm button").first().click();
  await page.getByRole("button", { name: /Compartir resumen|Share summary/ }).click();
  const publicUrl = await page.locator(".share-url").textContent();
  if (!publicUrl) throw new Error("Explicit share action did not create a public URL.");
  const publicPage = await desktop.newPage();
  await publicPage.goto(publicUrl, { waitUntil: "networkidle" });
  await publicPage.getByText(/PUBLIC LEAGUE ARCHIVE/).waitFor();
  await publicPage.screenshot({ path: `${output}/desktop-shared-career.png` });
  await publicPage.close();

  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  await mobile.addInitScript(() => localStorage.setItem("autoptu-career-development-user", "career-qa-user"));
  const mobilePage = await mobile.newPage();
  await mobilePage.goto(battleUrl, { waitUntil: "networkidle" });
  await mobilePage.locator("canvas").waitFor({ state: "visible", timeout: 15_000 });
  await mobilePage.screenshot({ path: `${output}/mobile-battle.png` });
  const mobileBattle = await metrics(mobilePage);
  if (mobileBattle.horizontalOverflow || mobileBattle.canvasCount !== 1 || await mobilePage.locator(".hp-track").count() !== 2) throw new Error(`Bad mobile battle: ${JSON.stringify(mobileBattle)}`);
  await mobilePage.goto(page.url(), { waitUntil: "networkidle" });
  await mobilePage.screenshot({ path: `${output}/mobile-season.png` });
  const mobileState = await metrics(mobilePage);
  if (mobileState.horizontalOverflow || mobileState.canvasCount !== 0 || mobileState.navCount !== 1) throw new Error(`Bad mobile fit: ${JSON.stringify(mobileState)}`);
  await mobilePage.getByRole("button", { name: /Entrenador|Trainer/ }).click();
  await mobilePage.waitForURL(/\/profile\//);
  await mobilePage.screenshot({ path: `${output}/mobile-profile.png` });
  if ((await metrics(mobilePage)).horizontalOverflow) throw new Error("Mobile profile overflows horizontally.");

  if (errors.length) throw new Error(`Browser errors: ${errors.join(" | ")}`);
  console.log(JSON.stringify({ initial, season, battle, mobileBattle, mobileState, status: "passed" }, null, 2));
  await mobile.close();
  await desktop.close();
} finally {
  await browser.close();
}
