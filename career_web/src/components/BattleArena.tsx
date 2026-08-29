import { useEffect, useRef, useState, type CSSProperties } from "react";
import { Application, Container, Graphics, Text, TextStyle } from "pixi.js";

import type { BattleViewState } from "../battlePresentation";
import { battleOutcomeVisualState, battleRenderFrameFactors, battleRenderMaxFps, constrainRequestedBattleVisualQuality, detectBattleVisualQuality, persistBattleVisualQuality, prefersReducedMotion, type BattleVisualQuality } from "../battleQuality";
import { createBattleTimerRegistry, type BattleTimerRegistry } from "../battleTimerRegistry";
import type { BattleCombatant, BattleMove, BattleTranscript, Locale } from "../types";
import { PokemonSprite } from "./PokemonSprite";

type ActorVisual = { container: Container };
type ArenaEffect = {
  display: Container;
  life: number;
  maxLife: number;
  kind?: "float" | "projectile";
  from?: [number, number];
  to?: [number, number];
};

const TYPE_COLORS: Record<string, number> = {
  bug: 0xa8c957, dark: 0x6b6170, dragon: 0x7a79ff, electric: 0xffdf4d,
  fairy: 0xff9fd7, fighting: 0xe86942, fire: 0xff6a32, flying: 0x91c8ee,
  ghost: 0x8c71c5, grass: 0x6fd05c, ground: 0xd6a65a, ice: 0xa7ecff,
  normal: 0xe8dfc4, poison: 0xb968c7, psychic: 0xff62a5, rock: 0xc8aa66,
  steel: 0xb8cad0, water: 0x4ba5ff, typeless: 0xf1e5c5,
};

const QUALITY_TOGGLE_STYLE: CSSProperties = {
  position: "absolute",
  top: 10,
  right: 12,
  zIndex: 8,
  border: "1px solid rgba(245, 226, 168, 0.62)",
  borderRadius: 999,
  padding: "6px 10px",
  background: "rgba(5, 14, 12, 0.84)",
  color: "#f5e2a8",
  font: "700 11px/1 Arial, sans-serif",
  letterSpacing: "0.08em",
  cursor: "pointer",
  backdropFilter: "blur(4px)",
};

export function BattleArena({ transcript, eventIndex, view, locale }: { transcript: BattleTranscript; eventIndex: number; view: BattleViewState; locale: Locale }) {
  const host = useRef<HTMLDivElement>(null);
  const appRef = useRef<Application | null>(null);
  const visuals = useRef<Map<string, ActorVisual>>(new Map());
  const targets = useRef<Map<string, [number, number]>>(new Map());
  const impulses = useRef<Map<string, [number, number]>>(new Map());
  const effects = useRef<ArenaEffect[]>([]);
  const timers = useRef<BattleTimerRegistry | null>(null);
  if (!timers.current) timers.current = createBattleTimerRegistry();
  const screen = useRef({ width: 900, height: 520 });
  const [quality, setQuality] = useState<BattleVisualQuality>(() => detectBattleVisualQuality());
  const [rendererFailed, setRendererFailed] = useState(false);
  const reducedMotion = prefersReducedMotion();
  const effectiveQuality: BattleVisualQuality = reducedMotion ? "light" : quality;

  function toggleQuality() {
    if (reducedMotion) return;
    const requested: BattleVisualQuality = quality === "full" ? "light" : "full";
    const next = constrainRequestedBattleVisualQuality(requested, {
      reducedMotion,
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
      devicePixelRatio: window.devicePixelRatio,
    });
    setRendererFailed(false);
    setQuality(next);
    persistBattleVisualQuality(next);
  }

  useEffect(() => {
    if (effectiveQuality !== "full") return;
    const enforceRasterBudget = () => {
      const next = constrainRequestedBattleVisualQuality("full", {
        reducedMotion,
        viewportWidth: window.innerWidth,
        viewportHeight: window.innerHeight,
        devicePixelRatio: window.devicePixelRatio,
      });
      if (next === "light") {
        setRendererFailed(false);
        persistBattleVisualQuality("light");
        setQuality("light");
      }
    };
    window.addEventListener("resize", enforceRasterBudget, { passive: true });
    return () => window.removeEventListener("resize", enforceRasterBudget);
  }, [effectiveQuality, reducedMotion]);

  useEffect(() => {
    if (!host.current) return;
    let cancelled = false;
    let app: Application | null = null;
    const mount = host.current;
    const syncScreenMetrics = () => {
      const currentApp = appRef.current;
      if (!currentApp) return;
      requestAnimationFrame(() => {
        if (cancelled || appRef.current !== currentApp) return;
        screen.current = { width: currentApp.screen.width, height: currentApp.screen.height };
      });
    };

    async function start() {
      app = new Application();
      const full = effectiveQuality === "full";
      try {
        await app.init({ resizeTo: mount, antialias: full, backgroundAlpha: 0, resolution: full ? Math.min(2, window.devicePixelRatio || 1) : 1 });
      } catch {
        try {
          app?.destroy(true, { children: true, texture: false, textureSource: false });
        } catch {
          // Pixi can reject before a renderer exists; cleanup is best-effort.
        }
        app = null;
        if (cancelled) return;
        if (effectiveQuality === "full") {
          persistBattleVisualQuality("light");
          setQuality("light");
          return;
        }
        setRendererFailed(true);
        return;
      }
      if (cancelled || !app) return;
      setRendererFailed(false);
      app.ticker.maxFPS = battleRenderMaxFps(effectiveQuality);
      appRef.current = app;
      mount.appendChild(app.canvas);
      screen.current = { width: app.screen.width, height: app.screen.height };
      window.addEventListener("resize", syncScreenMetrics, { passive: true });
      app.stage.addChild(buildStadium(app.screen.width, app.screen.height, transcript.initial_state.grid));
      visuals.current.clear();
      targets.current.clear();
      impulses.current.clear();

      const tile = tileMetrics(app.screen.width, app.screen.height, transcript.initial_state.grid);
      const ordered = [...transcript.initial_state.combatants].sort((left, right) => Number(right.team === "career-home") - Number(left.team === "career-home"));
      for (const combatant of ordered) {
        const home = combatant.team === "career-home";
        const container = new Container();
        const position = combatant.position
          ? stagePosition(combatant.position, app.screen.width, app.screen.height, transcript.initial_state.grid, combatant.footprint_side)
          : home ? [app.screen.width * 0.18, app.screen.height * 0.58] : [app.screen.width * 0.82, app.screen.height * 0.58];
        container.position.set(position[0], position[1]);
        container.visible = combatant.active !== false;
        targets.current.set(combatant.id, [position[0], position[1]]);
        const footprint = Math.max(1, combatant.footprint_side ?? 1);
        const visualTiles = visualTileScale(combatant.size, footprint);
        const shadow = new Graphics().ellipse(0, tile.height * 0.18, tile.width * Math.min(2.8, visualTiles * 0.76), tile.height * Math.min(1.2, visualTiles * 0.23)).fill({ color: 0x020706, alpha: 0.52 });
        container.addChild(shadow);
        const footing = new Graphics().circle(0, tile.height * 0.16, tile.width * Math.min(0.9, visualTiles * 0.28)).stroke({ color: home ? 0xf0c760 : 0xff7464, width: 2, alpha: 0.7 });
        container.addChild(footing);
        visuals.current.set(combatant.id, { container });
        app.stage.addChild(container);
      }

      app.ticker.add((ticker) => {
        const { positionBlend, impulseDecay } = battleRenderFrameFactors(ticker.deltaTime);
        for (const [id, visual] of visuals.current) {
          const target = targets.current.get(id);
          const impulse = impulses.current.get(id) ?? [0, 0];
          if (target) {
            visual.container.x += (target[0] + impulse[0] - visual.container.x) * positionBlend;
            visual.container.y += (target[1] + impulse[1] - visual.container.y) * positionBlend;
          }
          impulses.current.set(id, [impulse[0] * impulseDecay, impulse[1] * impulseDecay]);
        }
        effects.current = effects.current.filter((effect) => {
          effect.life += ticker.deltaTime;
          const progress = Math.min(1, effect.life / effect.maxLife);
          if (effect.kind === "projectile" && effect.from && effect.to) {
            const eased = 1 - (1 - progress) ** 3;
            effect.display.position.set(
              effect.from[0] + (effect.to[0] - effect.from[0]) * eased,
              effect.from[1] + (effect.to[1] - effect.from[1]) * eased,
            );
            effect.display.rotation += ticker.deltaTime * 0.18;
            effect.display.alpha = progress < 0.82 ? 1 : Math.max(0, (1 - progress) / 0.18);
          } else {
            effect.display.alpha = Math.max(0, 1 - progress);
            effect.display.y -= ticker.deltaTime * 0.45;
            effect.display.scale.set(0.85 + progress * 0.45);
          }
          if (progress < 1) return true;
          effect.display.destroy({ children: true });
          return false;
        });
      });
    }
    void start();
    return () => {
      cancelled = true;
      window.removeEventListener("resize", syncScreenMetrics);
      appRef.current = null;
      visuals.current.clear();
      effects.current = [];
      timers.current?.clearAll();
      if (app) app.destroy(true, { children: true, texture: false, textureSource: false });
      mount.replaceChildren();
    };
  }, [effectiveQuality, transcript]);

  useEffect(() => {
    timers.current?.clearAll();
    const app = appRef.current;
    for (const combatant of view.combatants) {
      const visual = visuals.current.get(combatant.id);
      if (!visual) continue;
      visual.container.visible = combatant.active !== false;
      if (combatant.position) targets.current.set(combatant.id, stagePosition(combatant.position, screen.current.width, screen.current.height, transcript.initial_state.grid, combatant.footprint_side));
    }
    if (!app) return;
    const event = view.event;
    if (!event) {
      for (const combatant of view.combatants) {
        const visual = visuals.current.get(combatant.id);
        if (!visual || !visual.container.visible) continue;
        const outcome = battleOutcomeVisualState(combatant.team, transcript.winner_team);
        visual.container.alpha = outcome.alpha;
        visual.container.scale.set(outcome.scale);
      }
      return;
    }
    if (effectiveQuality === "light" || reducedMotion) return;
    const actor = visuals.current.get(view.actorId);
    const target = visuals.current.get(view.targetId);
    if (event.type === "switch") {
      const incoming = visuals.current.get(String(event.target ?? ""));
      if (incoming) {
        incoming.container.visible = true;
        incoming.container.alpha = 1;
        incoming.container.scale.set(0.25);
        timers.current?.schedule(() => incoming.container.scale.set(1), 40);
        spawnStatus(app, incoming.container.x, incoming.container.y - 34, locale === "es" ? "¡ENTRA!" : "IN!", effects.current, 0x72d9a0);
      }
      return;
    }
    if (event.type === "shift" && actor) {
      spawnStatus(app, actor.container.x, actor.container.y - 34, locale === "es" ? "POSICIÓN" : "POSITION", effects.current, 0x72d9a0);
      actor.container.scale.set(1.06);
      timers.current?.schedule(() => actor.container.scale.set(1), 220);
      return;
    }
    if ((event.type === "forced_movement" || event.type === "maneuver") && target) {
      const actorPoint = targets.current.get(view.actorId);
      const targetPoint = targets.current.get(view.targetId);
      if (actorPoint && targetPoint) spawnAttack(app, actorPoint, targetPoint, undefined, effects.current, false);
      impulses.current.set(view.targetId, [view.targetId.includes("away") ? 28 : -28, -9]);
      flashCombatant(target, 0xf0c760, timers.current!);
      spawnStatus(app, target.container.x, target.container.y - 34, locale === "es" ? "MANIOBRA" : "MANEUVER", effects.current, 0xf0c760);
      return;
    }
    if (event.type === "move" && actor) {
      const actorPoint = targets.current.get(view.actorId);
      const targetPoint = targets.current.get(view.targetId);
      const move = moveMetadata(view, transcript);
      const melee = String(move?.range ?? "").toLowerCase().includes("melee") || move?.category.toLowerCase() === "physical" && !String(move?.range ?? "").match(/\d/);
      if (actorPoint && targetPoint) {
        impulses.current.set(view.actorId, [(targetPoint[0] - actorPoint[0]) * (melee ? 0.28 : 0.08), (targetPoint[1] - actorPoint[1]) * (melee ? 0.16 : 0.04)]);
        spawnAttack(app, actorPoint, targetPoint, move, effects.current, view.hit === false);
      }
      actor.container.scale.set(1.1);
      timers.current?.schedule(() => actor.container.scale.set(1), 260);
      if (target && view.hit !== false) {
        timers.current?.schedule(() => {
          impulses.current.set(view.targetId, [view.critical ? 34 : 20, view.critical ? -11 : -5]);
          flashCombatant(target, view.critical ? 0xffdc68 : attackColor(move), timers.current!);
          spawnImpact(app, target.container.x, target.container.y - 24, view.damage, view.critical, effects.current, attackColor(move));
          if (view.combatants.find((entry) => entry.id === view.targetId)?.hp === 0) {
            timers.current?.schedule(() => { target.container.alpha = 0.34; target.container.scale.set(0.72); }, 240);
          }
        }, melee ? 170 : 330);
      }
    } else if ((event.type === "status" || event.type === "ability") && target) {
      spawnStatus(app, target.container.x, target.container.y - 30, String(event.status ?? event.ability ?? "STATUS"), effects.current);
    } else if (event.type === "combat_stage" && target) {
      spawnStatus(app, target.container.x, target.container.y - 30, `${Number(event.amount ?? 0) > 0 ? "+" : ""}${Number(event.amount ?? 0)} ${String(event.stat ?? "STAT").toUpperCase()}`, effects.current, 0x72d9a0);
    }
  }, [effectiveQuality, eventIndex, locale, reducedMotion, transcript, view]);

  const parity = eventIndex % 2 === 0 ? "event-even" : "event-odd";
  const qualityLabel = effectiveQuality === "light"
    ? (locale === "es" ? "FX LIGEROS" : "LIGHT FX")
    : (locale === "es" ? "FX COMPLETOS" : "FULL FX");
  const qualityTitle = reducedMotion
    ? (locale === "es" ? "Los efectos ligeros están fijados por la preferencia de movimiento reducido del dispositivo." : "Light effects are locked by the device reduced-motion preference.")
    : (locale === "es" ? "Cambia sólo el costo visual del replay. Las reglas y el resultado no cambian." : "Changes replay rendering cost only. Rules and results do not change.");
  const fallbackCopy = locale === "es"
    ? "El renderer visual no está disponible. El estado táctico y el resultado del combate siguen accesibles."
    : "The visual renderer is unavailable. Tactical state and the battle result remain accessible.";

  return (
    <div style={{ position: "relative" }}>
      <button type="button" style={{ ...QUALITY_TOGGLE_STYLE, cursor: reducedMotion ? "default" : "pointer", opacity: reducedMotion ? 0.72 : 1 }} onClick={toggleQuality} disabled={reducedMotion} title={qualityTitle} aria-label={qualityTitle}>
        {qualityLabel}
      </button>
      <div className="arena-canvas-shell" data-visual-quality={effectiveQuality} role="img" aria-label={`${transcript.spec.home_club} versus ${transcript.spec.away_club}`}>
        <div ref={host} className="pixi-arena" aria-hidden="true" />
        {rendererFailed ? <div className="battle-arena-fallback" role="status">{fallbackCopy}</div> : null}
        <div className="field-pokemon-layer" aria-hidden="true">
          {view.combatants.filter((combatant) => combatant.active !== false).map((combatant) => {
            const isActor = (view.event?.type === "move" || view.event?.type === "forced_movement" || view.event?.type === "maneuver") && combatant.id === view.actorId;
            const isTarget = (view.event?.type === "move" || view.event?.type === "forced_movement" || view.event?.type === "maneuver") && combatant.id === view.targetId && view.hit !== false;
            return (
              <div
                key={combatant.id}
                className={`field-pokemon ${combatant.team === "career-home" ? "home" : "away"} ${isActor ? `attacking ${parity}` : ""} ${isTarget ? `taking-hit ${parity}` : ""} ${combatant.hp <= 0 ? "fainted" : ""}`}
                style={actorFieldStyle(combatant, transcript)}
              >
                <div className="field-model-facing"><PokemonSprite name={combatant.species} className="field-model" /></div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function buildStadium(width: number, height: number, grid?: { width: number; height: number }): Container {
  const stadium = new Container();
  const columns = Math.max(2, grid?.width ?? 15);
  const rows = Math.max(2, grid?.height ?? 9);
  const metrics = tileMetrics(width, height, grid);
  stadium.addChild(new Graphics().rect(0, 0, width, height).fill({ color: 0x06100d, alpha: 0.12 }));
  const crowd = new Graphics().roundRect(width * 0.03, height * 0.035, width * 0.94, height * 0.14, 16).fill({ color: 0x13211d, alpha: 0.24 }).stroke({ color: 0xe8c86f, width: 2, alpha: 0.24 });
  for (let x = width * 0.055; x < width * 0.95; x += 17) {
    const color = Math.round(x / 17) % 4 === 0 ? 0xe8b85a : 0x82968d;
    crowd.circle(x, height * (0.07 + ((x / 17) % 3) * 0.025), 2.3).fill({ color, alpha: 0.55 });
  }
  stadium.addChild(crowd);
  const field = new Graphics().rect(metrics.left, metrics.top, metrics.fieldWidth, metrics.fieldHeight).fill({ color: 0x184f39, alpha: 0.16 }).stroke({ color: 0xf5e2a8, width: 3, alpha: 0.82 });
  for (let column = 1; column < columns; column += 1) field.moveTo(metrics.left + column * metrics.width, metrics.top).lineTo(metrics.left + column * metrics.width, metrics.top + metrics.fieldHeight).stroke({ color: 0xdce6cb, width: 1, alpha: 0.17 });
  for (let row = 1; row < rows; row += 1) field.moveTo(metrics.left, metrics.top + row * metrics.height).lineTo(metrics.left + metrics.fieldWidth, metrics.top + row * metrics.height).stroke({ color: 0xdce6cb, width: 1, alpha: 0.17 });
  field.circle(width * 0.5, metrics.top + metrics.fieldHeight * 0.5, Math.min(width, height) * 0.1).stroke({ color: 0xf5e7bd, width: 3, alpha: 0.28 });
  field.moveTo(width * 0.5, metrics.top).lineTo(width * 0.5, metrics.top + metrics.fieldHeight).stroke({ color: 0xf5e7bd, width: 3, alpha: 0.3 });
  stadium.addChild(field);
  stadium.addChild(new Graphics().poly([metrics.left, metrics.top, width * 0.34, metrics.top, width * 0.48, metrics.top + metrics.fieldHeight, metrics.left, metrics.top + metrics.fieldHeight]).fill({ color: 0xf4e4a6, alpha: 0.035 }));
  return stadium;
}

function spawnAttack(app: Application, from: [number, number], to: [number, number], move: BattleMove | undefined, bucket: ArenaEffect[], missed: boolean) {
  const color = attackColor(move);
  const display = new Container();
  const core = new Graphics();
  const type = move?.type.toLowerCase() ?? "normal";
  if (type === "electric") core.moveTo(-16, 0).lineTo(-4, -9).lineTo(2, 5).lineTo(15, -5).stroke({ color, width: 6 });
  else if (type === "fire") core.poly([-13, 10, -7, -12, 0, -3, 9, -17, 14, 10]).fill({ color, alpha: 0.96 });
  else if (type === "grass") core.poly([0, -15, 11, 0, 0, 15, -11, 0]).fill({ color, alpha: 0.95 }).stroke({ color: 0xeaffc7, width: 2 });
  else if (type === "water" || type === "ice") core.circle(0, 0, 12).fill({ color, alpha: 0.9 }).circle(-4, -4, 4).fill({ color: 0xe9ffff, alpha: 0.75 });
  else if (type === "psychic" || type === "ghost") core.circle(0, 0, 13).stroke({ color, width: 5 }).circle(0, 0, 5).fill({ color, alpha: 0.7 });
  else core.poly([-15, -5, -3, -13, 14, 0, -3, 13, -15, 5]).fill({ color, alpha: 0.92 });
  display.addChild(core);
  display.position.set(from[0], from[1] - 20);
  app.stage.addChild(display);
  const destination: [number, number] = missed ? [to[0] + 45, to[1] - 55] : [to[0], to[1] - 20];
  bucket.push({ display, life: 0, maxLife: 20, kind: "projectile", from: [from[0], from[1] - 20], to: destination });
}

function spawnImpact(app: Application, x: number, y: number, damage: number, critical: boolean, bucket: ArenaEffect[], baseColor: number) {
  const display = new Container();
  display.position.set(x, y);
  const color = critical ? 0xffdf65 : baseColor;
  const burst = new Graphics().circle(0, 0, critical ? 40 : 30).fill({ color, alpha: 0.2 }).stroke({ color, width: critical ? 7 : 4, alpha: 0.95 });
  for (let angle = 0; angle < Math.PI * 2; angle += Math.PI / 4) burst.moveTo(Math.cos(angle) * 18, Math.sin(angle) * 18).lineTo(Math.cos(angle) * 45, Math.sin(angle) * 45).stroke({ color, width: 3, alpha: 0.85 });
  display.addChild(burst);
  if (damage > 0) {
    const text = new Text({ text: `−${damage}`, style: new TextStyle({ fill: 0xfff2ce, stroke: { color: 0x4b160e, width: 5 }, fontFamily: "Arial", fontSize: critical ? 32 : 25, fontWeight: "900" }) });
    text.anchor.set(0.5);
    display.addChild(text);
  }
  app.stage.addChild(display);
  bucket.push({ display, life: 0, maxLife: critical ? 48 : 38 });
}

function spawnStatus(app: Application, x: number, y: number, label: string, bucket: ArenaEffect[], color = 0xf2c35e) {
  const display = new Container();
  display.position.set(x, y);
  display.addChild(new Graphics().roundRect(-54, -16, 108, 32, 9).fill({ color: 0x07100e, alpha: 0.9 }).stroke({ color, width: 2 }));
  const text = new Text({ text: label.toUpperCase(), style: new TextStyle({ fill: color, fontFamily: "Arial", fontSize: 13, fontWeight: "800" }) });
  text.anchor.set(0.5);
  display.addChild(text);
  app.stage.addChild(display);
  bucket.push({ display, life: 0, maxLife: 54 });
}

function flashCombatant(target: ActorVisual, color: number, timers: BattleTimerRegistry) {
  const flash = new Graphics().circle(0, -26, 42).fill({ color, alpha: 0.42 });
  target.container.addChild(flash);
  timers.schedule(() => flash.destroy(), 140);
}

function moveMetadata(view: BattleViewState, transcript: BattleTranscript): BattleMove | undefined {
  const actor = transcript.initial_state.combatants.find((entry) => entry.id === view.actorId);
  return actor?.moves?.find((move) => move.name.toLowerCase() === view.move.toLowerCase());
}

function attackColor(move?: BattleMove): number { return TYPE_COLORS[move?.type.toLowerCase() ?? "normal"] ?? TYPE_COLORS.normal; }

function tileMetrics(width: number, height: number, grid?: { width: number; height: number }) {
  const columns = Math.max(2, grid?.width ?? 15);
  const rows = Math.max(2, grid?.height ?? 9);
  const left = width * 0.035;
  const top = height * 0.19;
  const fieldWidth = width * 0.93;
  const fieldHeight = height * 0.76;
  return { columns, rows, left, top, fieldWidth, fieldHeight, width: fieldWidth / columns, height: fieldHeight / rows };
}

function stagePosition(position: [number, number], width: number, height: number, grid?: { width: number; height: number }, footprintSide = 1): [number, number] {
  const tile = tileMetrics(width, height, grid);
  const centerOffset = Math.max(0, footprintSide - 1) / 2;
  return [tile.left + (position[0] + 0.5 + centerOffset) * tile.width, tile.top + (position[1] + 0.5 + centerOffset) * tile.height];
}

function visualTileScale(size = "Medium", footprintSide = 1): number {
  const bySize: Record<string, number> = { tiny: 0.72, small: 0.95, medium: 1.28, large: 1.85, huge: 2.65, gigantic: 3.35 };
  return Math.max(bySize[String(size).toLowerCase()] ?? 1.28, footprintSide * 0.92);
}

function actorFieldStyle(combatant: BattleCombatant, transcript: BattleTranscript): CSSProperties {
  const columns = Math.max(2, transcript.initial_state.grid?.width ?? 15);
  const rows = Math.max(2, transcript.initial_state.grid?.height ?? 9);
  const position = combatant.position ?? (combatant.team === "career-home" ? [2, Math.floor(rows / 2)] : [columns - 3, Math.floor(rows / 2)]);
  const footprint = Math.max(1, combatant.footprint_side ?? 1);
  const offset = Math.max(0, footprint - 1) / 2;
  const x = 3.5 + (position[0] + 0.5 + offset) * (93 / columns);
  const y = 19 + (position[1] + 0.5 + offset) * (76 / rows);
  const size = Math.max(8.5, (76 / rows) * visualTileScale(combatant.size, footprint));
  return {
    "--field-x": `${x}%`,
    "--field-y": `${y}%`,
    "--field-size": `${size}%`,
  } as CSSProperties;
}
