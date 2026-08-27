export type BattleVisualQuality = "full" | "light";

export type BattleVisualSignals = {
  storedPreference?: string | null;
  reducedMotion?: boolean;
  hardwareConcurrency?: number | null;
  deviceMemory?: number | null;
  saveData?: boolean;
  compactTouch?: boolean;
};

export const BATTLE_VISUAL_QUALITY_KEY = "autoptu:battle-visual-quality";

export function battleRenderMaxFps(quality: BattleVisualQuality): number {
  return quality === "light" ? 30 : 60;
}

export function battleRenderFrameFactors(deltaTime: number): { positionBlend: number; impulseDecay: number } {
  const frameScale = Number.isFinite(deltaTime) && deltaTime >= 0 ? deltaTime : 1;
  return {
    positionBlend: 1 - 0.8 ** frameScale,
    impulseDecay: 0.78 ** frameScale,
  };
}

export function battleOutcomeVisualState(team: string, winnerTeam?: string | null): { alpha: number; scale: number } {
  if (winnerTeam !== "career-home" && winnerTeam !== "career-away") return { alpha: 1, scale: 1 };
  return team === winnerTeam
    ? { alpha: 1, scale: 1.08 }
    : { alpha: 0.38, scale: 0.86 };
}

function finitePositiveHardwareSignal(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) && value > 0 ? value : null;
}

function finiteNonNegativeHostSignal(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 ? value : 0;
}

export function chooseBattleVisualQuality(signals: BattleVisualSignals): BattleVisualQuality {
  if (signals.reducedMotion) return "light";
  if (signals.storedPreference === "full" || signals.storedPreference === "light") return signals.storedPreference;
  if (signals.saveData) return "light";
  if (signals.compactTouch) return "light";

  const cores = finitePositiveHardwareSignal(signals.hardwareConcurrency);
  if (cores !== null && cores <= 4) return "light";

  const memory = finitePositiveHardwareSignal(signals.deviceMemory);
  if (memory !== null && memory <= 4) return "light";

  return "full";
}

export function detectBattleVisualQuality(): BattleVisualQuality {
  if (typeof window === "undefined") return "full";

  let storedPreference: string | null = null;
  try {
    storedPreference = window.localStorage.getItem(BATTLE_VISUAL_QUALITY_KEY);
  } catch {
    storedPreference = null;
  }

  const nav = window.navigator as Navigator & {
    deviceMemory?: number;
    connection?: { saveData?: boolean };
  };
  return chooseBattleVisualQuality({
    storedPreference,
    reducedMotion: prefersReducedMotion(),
    hardwareConcurrency: nav.hardwareConcurrency,
    deviceMemory: nav.deviceMemory,
    saveData: nav.connection?.saveData,
    compactTouch: isCompactTouchDevice(),
  });
}

function mediaQueryMatches(query: string): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return false;
  try {
    return window.matchMedia(query).matches === true;
  } catch {
    return false;
  }
}

export function prefersReducedMotion(): boolean {
  return mediaQueryMatches("(prefers-reduced-motion: reduce)");
}

export function isCompactTouchDevice(): boolean {
  if (typeof window === "undefined") return false;
  const coarsePointer = mediaQueryMatches("(pointer: coarse)");
  const touchPoints = finiteNonNegativeHostSignal(window.navigator.maxTouchPoints);
  const shortestViewportEdge = Math.min(
    finiteNonNegativeHostSignal(window.innerWidth),
    finiteNonNegativeHostSignal(window.innerHeight),
  );
  return (coarsePointer || touchPoints > 0)
    && shortestViewportEdge > 0
    && shortestViewportEdge <= 900;
}

export function persistBattleVisualQuality(value: BattleVisualQuality): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(BATTLE_VISUAL_QUALITY_KEY, value);
  } catch {
    // Storage may be blocked in private or restricted browser contexts.
  }
}
