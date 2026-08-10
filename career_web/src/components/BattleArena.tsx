import { useEffect, useRef } from "react";
import { Application, Container, Graphics, Rectangle, Sprite, Text, TextStyle, Texture } from "pixi.js";
import type { BattleTranscript } from "../types";

export function BattleArena({ transcript, eventIndex, complete }: { transcript: BattleTranscript; eventIndex: number; complete: boolean }) {
  const host = useRef<HTMLDivElement>(null);
  const actors = useRef<Container[]>([]);
  const actorIds = useRef<string[]>([]);
  const targets = useRef<Map<string, [number, number]>>(new Map());
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
      mount.appendChild(app.canvas);
      const field = new Graphics().roundRect(0, 0, 900, 520, 30).fill({ color: 0x173c31 }).stroke({ color: 0xe9c878, width: 5, alpha: 0.8 });
      for (let column = 1; column < 16; column += 1) field.moveTo(column * 56.25, 0).lineTo(column * 56.25, 520).stroke({ color: 0xdce6cb, width: 1, alpha: 0.055 });
      for (let row = 1; row < 9; row += 1) field.moveTo(0, row * 57.78).lineTo(900, row * 57.78).stroke({ color: 0xdce6cb, width: 1, alpha: 0.055 });
      field.roundRect(70, 65, 145, 120, 18).fill({ color: 0x356b55, alpha: 0.22 });
      field.roundRect(690, 330, 145, 120, 18).fill({ color: 0xb88945, alpha: 0.12 });
      field.rect(450, 0, 3, 520).fill({ color: 0xe9e0bd, alpha: 0.24 });
      field.circle(450, 260, 80).stroke({ color: 0xe9e0bd, width: 3, alpha: 0.3 });
      field.scale.set(app.screen.width / 900, app.screen.height / 520);
      app.stage.addChild(field);
      actors.current = [];
      actorIds.current = [];
      targets.current.clear();
      screen.current = { width: app.screen.width, height: app.screen.height };
      const orderedCombatants = [...transcript.initial_state.combatants].sort((left, right) => {
        const home = transcript.spec.home_species;
        return Number(right.species === home) - Number(left.species === home);
      });
      for (const [index, combatant] of orderedCombatants.entries()) {
        const container = new Container();
        const position = combatant.position
          ? stagePosition(combatant.position, app.screen.width, app.screen.height, transcript.initial_state.grid)
          : index === 0 ? [app.screen.width * 0.25, app.screen.height * 0.5] : [app.screen.width * 0.75, app.screen.height * 0.5];
        container.position.set(position[0], position[1]);
        targets.current.set(combatant.id, [position[0], position[1]]);
        const shadow = new Graphics().ellipse(0, 48, 72, 22).fill({ color: 0x020706, alpha: 0.55 });
        container.addChild(shadow);
        try {
          const sheet = await loadPokemonTexture(combatant.species);
          const frameSize = Math.min(sheet.width, sheet.height);
          const texture = new Texture({ source: sheet.source, frame: new Rectangle(0, 0, frameSize, frameSize) });
          const sprite = new Sprite(texture);
          sprite.anchor.set(0.5, 1);
          const scale = Math.min(1.45, 150 / Math.max(sprite.width, sprite.height));
          sprite.scale.set(index === 0 ? scale : -scale, scale);
          container.addChild(sprite);
        } catch {
          container.addChild(new Graphics().circle(0, 0, 42).fill({ color: index === 0 ? 0xffc86a : 0xff715b }));
        }
        const label = new Text({ text: combatant.species, style: new TextStyle({ fill: 0xfff1c9, fontFamily: "Barlow Condensed", fontSize: 22, fontWeight: "600" }) });
        label.anchor.set(0.5, 0);
        label.position.set(0, 58);
        container.addChild(label);
        actors.current.push(container);
        actorIds.current.push(combatant.id);
        app.stage.addChild(container);
      }
      let time = 0;
      app.ticker.add((ticker) => {
        time += ticker.deltaTime * 0.04;
        actors.current.forEach((actor, index) => {
          const target = targets.current.get(actorIds.current[index]);
          if (target) {
            actor.x += (target[0] - actor.x) * 0.14;
            actor.y += (target[1] - actor.y) * 0.14;
          }
          actor.rotation = Math.sin(time + index * 2) * 0.006;
        });
      });
    }
    void start();
    return () => {
      cancelled = true;
      actors.current = [];
      if (app) app.destroy(true, { children: true, texture: false, textureSource: false });
      mount.replaceChildren();
    };
  }, [transcript]);
  useEffect(() => {
    const actingId = String(transcript.events[eventIndex]?.actor ?? "");
    const actingIndex = actorIds.current.indexOf(actingId);
    const target = actors.current[actingIndex >= 0 ? actingIndex : eventIndex % Math.max(1, actors.current.length)];
    const shifts = transcript.events.slice(0, eventIndex + 1).filter((event) => event.type === "shift" && Array.isArray(event.to));
    for (const shift of shifts) {
      const actor = String(shift.actor ?? "");
      const to = shift.to as [number, number];
      targets.current.set(actor, stagePosition(to, screen.current.width, screen.current.height, transcript.initial_state.grid));
    }
    if (!target || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    target.scale.set(complete ? 1.08 : 1.18);
    const timer = window.setTimeout(() => target.scale.set(1), 180);
    return () => window.clearTimeout(timer);
  }, [complete, eventIndex]);
  return <div ref={host} className="pixi-arena" role="img" aria-label={`${transcript.spec.home_species} versus ${transcript.spec.away_species}`} />;
}

async function loadPokemonTexture(species: string): Promise<Texture> {
  const image = new Image();
  image.src = `/api/sprites/pokemon?name=${encodeURIComponent(species)}`;
  await image.decode();
  return Texture.from(image);
}

function stagePosition(position: [number, number], width: number, height: number, grid?: { width: number; height: number }): [number, number] {
  const columns = Math.max(2, grid?.width ?? 16);
  const rows = Math.max(2, grid?.height ?? 9);
  return [width * (0.08 + (position[0] / (columns - 1)) * 0.84), height * (0.12 + (position[1] / (rows - 1)) * 0.72)];
}
