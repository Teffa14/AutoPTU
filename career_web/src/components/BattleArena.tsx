import { useEffect, useRef } from "react";
import { Application, Container, Graphics, Rectangle, Sprite, Text, TextStyle, Texture } from "pixi.js";

import type { BattleViewState } from "../battlePresentation";
import type { BattleTranscript } from "../types";

type ActorVisual = { container: Container; sprite?: Sprite; home: boolean };
type ArenaEffect = { display: Container; life: number; maxLife: number };

export function BattleArena({ transcript, eventIndex, view }: { transcript: BattleTranscript; eventIndex: number; view: BattleViewState }) {
  const host = useRef<HTMLDivElement>(null);
  const appRef = useRef<Application | null>(null);
  const visuals = useRef<Map<string, ActorVisual>>(new Map());
  const targets = useRef<Map<string, [number, number]>>(new Map());
  const impulses = useRef<Map<string, [number, number]>>(new Map());
  const effects = useRef<ArenaEffect[]>([]);
  const timers = useRef<number[]>([]);
  const screen = useRef({ width: 900, height: 520 });

  useEffect(() => {
    if (!host.current) return;
    let cancelled = false;
    let app: Application | null = null;
    const mount = host.current;

    async function start() {
      app = new Application();
      await app.init({ resizeTo: mount, antialias: true, backgroundAlpha: 0, resolution: Math.min(2, window.devicePixelRatio || 1) });
      if (cancelled || !app) return;
      appRef.current = app;
      mount.appendChild(app.canvas);
      screen.current = { width: app.screen.width, height: app.screen.height };
      app.stage.addChild(buildStadium(app.screen.width, app.screen.height));
      visuals.current.clear();
      targets.current.clear();
      impulses.current.clear();

      const ordered = [...transcript.initial_state.combatants].sort((left, right) => Number(right.team === "career-home") - Number(left.team === "career-home"));
      for (const combatant of ordered) {
        const home = combatant.team === "career-home";
        const container = new Container();
        const position = combatant.position
          ? stagePosition(combatant.position, app.screen.width, app.screen.height, transcript.initial_state.grid)
          : home ? [app.screen.width * 0.24, app.screen.height * 0.58] : [app.screen.width * 0.76, app.screen.height * 0.38];
        container.position.set(position[0], position[1]);
        targets.current.set(combatant.id, [position[0], position[1]]);
        const shadow = new Graphics().ellipse(0, 42, 82, 22).fill({ color: 0x020706, alpha: 0.48 });
        container.addChild(shadow);
        let sprite: Sprite | undefined;
        try {
          const sheet = await loadPokemonTexture(combatant.species);
          if (cancelled || appRef.current !== app) return;
          const frameSize = Math.min(sheet.width, sheet.height);
          const texture = new Texture({ source: sheet.source, frame: new Rectangle(0, 0, frameSize, frameSize) });
          sprite = new Sprite(texture);
          sprite.anchor.set(0.5, 1);
          const scale = Math.min(1.7, 174 / Math.max(sprite.width, sprite.height));
          sprite.scale.set(home ? scale : -scale, scale);
          container.addChild(sprite);
        } catch {
          if (cancelled || appRef.current !== app) return;
          container.addChild(new Graphics().circle(0, 0, 42).fill({ color: home ? 0xffc86a : 0xff715b }));
        }
        if (cancelled || appRef.current !== app) return;
        const plate = new Graphics().roundRect(-58, 52, 116, 24, 7).fill({ color: 0x07100e, alpha: 0.86 }).stroke({ color: home ? 0xe8b85a : 0xff8066, width: 1, alpha: 0.7 });
        const label = new Text({ text: combatant.species, style: new TextStyle({ fill: 0xfff1c9, fontFamily: "Arial", fontSize: 14, fontWeight: "700" }) });
        label.anchor.set(0.5, 0);
        label.position.set(0, 56);
        container.addChild(plate, label);
        visuals.current.set(combatant.id, { container, sprite, home });
        app.stage.addChild(container);
      }

      let time = 0;
      app.ticker.add((ticker) => {
        time += ticker.deltaTime * 0.045;
        for (const [id, visual] of visuals.current) {
          const target = targets.current.get(id);
          const impulse = impulses.current.get(id) ?? [0, 0];
          if (target) {
            visual.container.x += (target[0] + impulse[0] - visual.container.x) * 0.2;
            visual.container.y += (target[1] + impulse[1] - visual.container.y) * 0.2;
          }
          impulses.current.set(id, [impulse[0] * 0.78, impulse[1] * 0.78]);
          if (visual.sprite) visual.sprite.y = Math.sin(time + (visual.home ? 0 : 2.4)) * 2.5;
        }
        effects.current = effects.current.filter((effect) => {
          effect.life += ticker.deltaTime;
          const progress = effect.life / effect.maxLife;
          effect.display.alpha = Math.max(0, 1 - progress);
          effect.display.y -= ticker.deltaTime * 0.45;
          effect.display.scale.set(0.85 + progress * 0.45);
          if (progress < 1) return true;
          effect.display.destroy({ children: true });
          return false;
        });
      });
    }
    void start();
    return () => {
      cancelled = true;
      appRef.current = null;
      visuals.current.clear();
      effects.current = [];
      timers.current.forEach((timer) => window.clearTimeout(timer));
      timers.current = [];
      if (app) app.destroy(true, { children: true, texture: false, textureSource: false });
      mount.replaceChildren();
    };
  }, [transcript]);

  useEffect(() => {
    const app = appRef.current;
    for (const combatant of view.combatants) {
      if (combatant.position) targets.current.set(combatant.id, stagePosition(combatant.position, screen.current.width, screen.current.height, transcript.initial_state.grid));
    }
    if (!app || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const event = view.event;
    if (!event) {
      for (const combatant of view.combatants) {
        const visual = visuals.current.get(combatant.id);
        if (!visual) continue;
        const winner = combatant.team === transcript.winner_team;
        visual.container.alpha = winner ? 1 : 0.38;
        visual.container.scale.set(winner ? 1.12 : 0.82);
      }
      return;
    }
    const actor = visuals.current.get(view.actorId);
    const target = visuals.current.get(view.targetId);
    if (event.type === "move" && actor) {
      const actorPoint = targets.current.get(view.actorId);
      const targetPoint = targets.current.get(view.targetId);
      if (actorPoint && targetPoint) impulses.current.set(view.actorId, [(targetPoint[0] - actorPoint[0]) * 0.22, (targetPoint[1] - actorPoint[1]) * 0.12]);
      actor.container.scale.set(1.14);
      timers.current.push(window.setTimeout(() => actor.container.scale.set(1), 210));
      if (target && view.hit !== false) {
        impulses.current.set(view.targetId, [view.critical ? 42 : 24, view.critical ? -14 : -7]);
        flashCombatant(target, view.critical ? 0xffdc68 : 0xff795f, timers.current);
        spawnImpact(app, target.container.x, target.container.y - 34, view.damage, view.critical, effects.current);
        if (view.combatants.find((entry) => entry.id === view.targetId)?.hp === 0) {
          timers.current.push(window.setTimeout(() => { target.container.alpha = 0.42; target.container.scale.set(0.78); }, 260));
        }
      }
    } else if ((event.type === "status" || event.type === "ability") && target) {
      spawnStatus(app, target.container.x, target.container.y - 36, String(event.status ?? event.ability ?? "STATUS"), effects.current);
    } else if (event.type === "combat_stage" && target) {
      spawnStatus(app, target.container.x, target.container.y - 36, `${Number(event.amount ?? 0) > 0 ? "+" : ""}${Number(event.amount ?? 0)} ${String(event.stat ?? "STAT").toUpperCase()}`, effects.current, 0x72d9a0);
    }
  }, [eventIndex, transcript, view]);

  return <div ref={host} className="pixi-arena" role="img" aria-label={`${transcript.spec.home_species} versus ${transcript.spec.away_species}`} />;
}

function buildStadium(width: number, height: number): Container {
  const stadium = new Container();
  stadium.addChild(new Graphics().rect(0, 0, width, height).fill({ color: 0x08120f }));
  const crowd = new Graphics().roundRect(width * 0.03, height * 0.035, width * 0.94, height * 0.18, 16).fill({ color: 0x13211d }).stroke({ color: 0x4e665c, width: 2, alpha: 0.5 });
  for (let x = width * 0.055; x < width * 0.95; x += 17) {
    const color = Math.round(x / 17) % 4 === 0 ? 0xe8b85a : 0x82968d;
    crowd.circle(x, height * (0.08 + ((x / 17) % 3) * 0.035), 2.3).fill({ color, alpha: 0.55 });
  }
  stadium.addChild(crowd);
  const field = new Graphics().roundRect(width * 0.035, height * 0.205, width * 0.93, height * 0.75, 24).fill({ color: 0x184f39 }).stroke({ color: 0xe5cf91, width: 4, alpha: 0.85 });
  for (let column = 1; column < 15; column += 1) field.moveTo(width * 0.035 + column * (width * 0.93 / 15), height * 0.205).lineTo(width * 0.035 + column * (width * 0.93 / 15), height * 0.955).stroke({ color: 0xdce6cb, width: 1, alpha: 0.08 });
  for (let row = 1; row < 9; row += 1) field.moveTo(width * 0.035, height * 0.205 + row * (height * 0.75 / 9)).lineTo(width * 0.965, height * 0.205 + row * (height * 0.75 / 9)).stroke({ color: 0xdce6cb, width: 1, alpha: 0.08 });
  field.ellipse(width * 0.25, height * 0.62, width * 0.22, height * 0.22).fill({ color: 0x2d7656, alpha: 0.6 }).stroke({ color: 0xdce6cb, width: 2, alpha: 0.24 });
  field.ellipse(width * 0.75, height * 0.48, width * 0.22, height * 0.22).fill({ color: 0x316c52, alpha: 0.6 }).stroke({ color: 0xdce6cb, width: 2, alpha: 0.24 });
  field.moveTo(width * 0.5, height * 0.205).lineTo(width * 0.5, height * 0.955).stroke({ color: 0xf5e7bd, width: 3, alpha: 0.32 });
  field.circle(width * 0.5, height * 0.58, Math.min(width, height) * 0.11).stroke({ color: 0xf5e7bd, width: 3, alpha: 0.28 });
  stadium.addChild(field);
  const light = new Graphics().poly([width * 0.08, height * 0.2, width * 0.38, height * 0.2, width * 0.5, height, 0, height]).fill({ color: 0xf4e4a6, alpha: 0.035 });
  stadium.addChild(light);
  return stadium;
}

function spawnImpact(app: Application, x: number, y: number, damage: number, critical: boolean, bucket: ArenaEffect[]) {
  const display = new Container();
  display.position.set(x, y);
  const color = critical ? 0xffdf65 : 0xff765d;
  display.addChild(new Graphics().circle(0, 0, critical ? 46 : 34).fill({ color, alpha: 0.18 }).stroke({ color, width: critical ? 7 : 4, alpha: 0.9 }));
  if (damage > 0) {
    const text = new Text({ text: `−${damage}`, style: new TextStyle({ fill: 0xfff2ce, stroke: { color: 0x4b160e, width: 5 }, fontFamily: "Arial", fontSize: critical ? 34 : 27, fontWeight: "900" }) });
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

function flashCombatant(target: ActorVisual, color: number, timers: number[]) {
  const flash = new Graphics().circle(0, -35, 56).fill({ color, alpha: 0.42 });
  target.container.addChild(flash);
  timers.push(window.setTimeout(() => flash.destroy(), 130));
}

async function loadPokemonTexture(species: string): Promise<Texture> {
  const image = new Image();
  image.src = `/api/sprites/pokemon?name=${encodeURIComponent(species)}`;
  await image.decode();
  return Texture.from(image);
}

function stagePosition(position: [number, number], width: number, height: number, grid?: { width: number; height: number }): [number, number] {
  const columns = Math.max(2, grid?.width ?? 15);
  const rows = Math.max(2, grid?.height ?? 9);
  return [width * (0.08 + (position[0] / (columns - 1)) * 0.84), height * (0.29 + (position[1] / (rows - 1)) * 0.59)];
}
