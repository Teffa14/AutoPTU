import { describe, expect, it } from "vitest";

import { createBattleTimerRegistry } from "./battleTimerRegistry";

type PendingTimer = { id: number; callback: () => void; delay: number };

function fakeTimers() {
  let nextId = 1;
  const pending = new Map<number, PendingTimer>();
  const cleared: number[] = [];
  return {
    pending,
    cleared,
    setTimer(callback: () => void, delay: number) {
      const id = nextId++;
      pending.set(id, { id, callback, delay });
      return id;
    },
    clearTimer(id: number) {
      cleared.push(id);
      pending.delete(id);
    },
    fire(id: number) {
      const timer = pending.get(id);
      if (!timer) return;
      pending.delete(id);
      timer.callback();
    },
  };
}

describe("createBattleTimerRegistry", () => {
  it("drops fired timer ids instead of retaining one entry per replay event", () => {
    const fake = fakeTimers();
    const registry = createBattleTimerRegistry(fake.setTimer, fake.clearTimer);
    let fired = 0;

    const timer = registry.schedule(() => { fired += 1; }, 330);
    expect(registry.activeCount()).toBe(1);

    fake.fire(timer);

    expect(fired).toBe(1);
    expect(registry.activeCount()).toBe(0);
  });

  it("cancels callbacks from the previous visual event before the next event renders", () => {
    const fake = fakeTimers();
    const registry = createBattleTimerRegistry(fake.setTimer, fake.clearTimer);
    let staleImpact = false;

    const timer = registry.schedule(() => { staleImpact = true; }, 330);
    registry.clearAll();
    fake.fire(timer);

    expect(staleImpact).toBe(false);
    expect(registry.activeCount()).toBe(0);
    expect(fake.cleared).toEqual([timer]);
  });

  it("clears every nested visual timer without leaving retained handles", () => {
    const fake = fakeTimers();
    const registry = createBattleTimerRegistry(fake.setTimer, fake.clearTimer);

    registry.schedule(() => undefined, 140);
    registry.schedule(() => undefined, 240);
    registry.schedule(() => undefined, 330);
    expect(registry.activeCount()).toBe(3);

    registry.clearAll();

    expect(registry.activeCount()).toBe(0);
    expect(fake.pending.size).toBe(0);
    expect(fake.cleared).toHaveLength(3);
  });
});
