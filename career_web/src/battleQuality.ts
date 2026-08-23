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

export function chooseBattleVisualQuality(signals: BattleVisualSignals): BattleVisualQuality {
  if (signals.reducedMotion) return "light";
  if (signals.storedPreference === "full" || signals.storedPreference === "light") return signals.storedPreference;
  if (signals.saveData) return "light";
  if (signals.compactTouch) return "light";

  const cores = Number(signals.hardwareConcurrency ?? 0);
  if (Number.isFinite(cores) && cores > 0 && cores <= 4) return "light";

  const memory = Number(signals.deviceMemory ?? 0);
  if (Number.isFinite(memory) && memory > 0 && memory <= 4) return "light";

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

export function prefersReducedMotion(): boolean {
  return typeof window !== "undefined"
    && typeof window.matchMedia === "function"
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function isCompactTouchDevice(): boolean {
  if (typeof window === "undefined") return false;
  const coarsePointer = typeof window.matchMedia === "function"
    && window.matchMedia("(pointer: coarse)").matches;
  const touchPoints = Number(window.navigator.maxTouchPoints ?? 0);
  const shortestViewportEdge = Math.min(
    Number(window.innerWidth || 0),
    Number(window.innerHeight || 0),
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
