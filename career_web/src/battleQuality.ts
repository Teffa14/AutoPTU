export type BattleVisualQuality = "full" | "light";

export type BattleVisualSignals = {
  storedPreference?: string | null;
  reducedMotion?: boolean;
  hardwareConcurrency?: number | null;
  deviceMemory?: number | null;
};

export const BATTLE_VISUAL_QUALITY_KEY = "autoptu:battle-visual-quality";

export function battleRenderMaxFps(quality: BattleVisualQuality): number {
  return quality === "light" ? 30 : 60;
}

export function chooseBattleVisualQuality(signals: BattleVisualSignals): BattleVisualQuality {
  if (signals.reducedMotion) return "light";
  if (signals.storedPreference === "full" || signals.storedPreference === "light") return signals.storedPreference;

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

  const nav = window.navigator as Navigator & { deviceMemory?: number };
  return chooseBattleVisualQuality({
    storedPreference,
    reducedMotion: prefersReducedMotion(),
    hardwareConcurrency: nav.hardwareConcurrency,
    deviceMemory: nav.deviceMemory,
  });
}

export function prefersReducedMotion(): boolean {
  return typeof window !== "undefined"
    && typeof window.matchMedia === "function"
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function persistBattleVisualQuality(value: BattleVisualQuality): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(BATTLE_VISUAL_QUALITY_KEY, value);
  } catch {
    // Storage may be blocked in private or restricted browser contexts.
  }
}
