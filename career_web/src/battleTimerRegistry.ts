export type BattleTimerId = number;

type SetTimer = (callback: () => void, delay: number) => BattleTimerId;
type ClearTimer = (timer: BattleTimerId) => void;

export interface BattleTimerRegistry {
  schedule(callback: () => void, delay: number): BattleTimerId;
  clearAll(): void;
  activeCount(): number;
}

export function createBattleTimerRegistry(
  setTimer: SetTimer = (callback, delay) => window.setTimeout(callback, delay),
  clearTimer: ClearTimer = (timer) => window.clearTimeout(timer),
): BattleTimerRegistry {
  const active = new Set<BattleTimerId>();

  return {
    schedule(callback, delay) {
      let timer = 0;
      timer = setTimer(() => {
        active.delete(timer);
        callback();
      }, delay);
      active.add(timer);
      return timer;
    },
    clearAll() {
      for (const timer of active) clearTimer(timer);
      active.clear();
    },
    activeCount() {
      return active.size;
    },
  };
}
