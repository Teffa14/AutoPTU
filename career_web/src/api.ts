import { authHeaders, type CareerAuthMode } from "./auth";
import { loadLocalRun, saveLocalRun } from "./localCareer";
import type { BattleTranscript, CareerCatalog, CareerRun } from "./types";

export interface ClubOffer {
  id: string;
  club_id: string;
  club_name: string;
  salary: number;
  seasons: number;
  loan_slots: number;
  loan_species: string[];
  renewal: boolean;
  perk: { stat: string; amount: number; label: string };
}

export interface SponsorOffer {
  id: string;
  name: string;
  theme: string;
  upfront: number;
  bonus: number;
  objective: string;
  target: number;
  description_es: string;
  description_en: string;
}

export interface CaptureCandidate {
  id: string;
  species: string;
  rarity: string;
  ball_cost: number;
}

export interface PreseasonSnapshot {
  season: number;
  club_completed: boolean;
  sponsor_completed: boolean;
  capture_completed: boolean;
  club_offers: ClubOffer[];
  sponsor_offers: SponsorOffer[];
  capture_candidates: CaptureCandidate[];
  run?: CareerRun;
}

const base = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";
const MAX_BATTLE_CACHE_ENTRIES = 6;
const battleCache = new Map<string, BattleTranscript>();
const battleRequests = new Map<string, Promise<BattleTranscript>>();
const requestTimeoutMs = 15_000;

function normalizeBattleTranscriptEvents(transcript: BattleTranscript): BattleTranscript {
  if (Array.isArray((transcript as { events?: unknown }).events)) return transcript;
  return { ...transcript, events: [] };
}

function normalizeBattleTranscriptInitialState(transcript: BattleTranscript): BattleTranscript {
  const rawInitialState = (transcript as { initial_state?: unknown }).initial_state;
  if (
    rawInitialState
    && typeof rawInitialState === "object"
    && Array.isArray((rawInitialState as { combatants?: unknown }).combatants)
  ) return transcript;
  return { ...transcript, initial_state: { round: 0, battle_over: false, grid: { width: 1, height: 1 }, combatants: [] } };
}

function normalizeBattleTranscriptSpec(transcript: BattleTranscript): BattleTranscript {
  const rawSpec = (transcript as { spec?: unknown }).spec;
  if (rawSpec && typeof rawSpec === "object") return transcript;
  return { ...transcript, spec: {} as BattleTranscript["spec"] };
}

function normalizeBattleTranscriptHash(transcript: BattleTranscript): BattleTranscript {
  const rawHash = (transcript as { sha256?: unknown }).sha256;
  if (typeof rawHash === "string") return transcript;
  return { ...transcript, sha256: "legacy" };
}

function rememberBattleTranscript(key: string, transcript: BattleTranscript): BattleTranscript {
  const safeTranscript = normalizeBattleTranscriptHash(normalizeBattleTranscriptSpec(normalizeBattleTranscriptInitialState(normalizeBattleTranscriptEvents(transcript))));
  battleCache.delete(key);
  battleCache.set(key, safeTranscript);
  while (battleCache.size > MAX_BATTLE_CACHE_ENTRIES) {
    const oldestKey = battleCache.keys().next().value as string | undefined;
    if (!oldestKey) break;
    battleCache.delete(oldestKey);
  }
  return safeTranscript;
}

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

export function authModeForPath(path: string): CareerAuthMode {
  const pathname = path.split("?", 1)[0];
  if (pathname === "/api/v1/portable/action" || pathname === "/api/v1/runs/restore") return "casual";
  if (/^\/api\/v1\/daily\/[^/]+\/attempts$/.test(pathname)) return "ranked";
  if (pathname.startsWith("/api/v1/runs/")) return "ranked";
  return "public";
}

async function request<T>(path: string, init: RequestInit = {}, authMode: CareerAuthMode = authModeForPath(path)): Promise<T> {
  const identity = await authHeaders(authMode);
  const controller = new AbortController();
  const upstreamSignal = init.signal;
  let timedOut = false;
  const abortFromCaller = () => controller.abort(upstreamSignal?.reason);
  if (upstreamSignal?.aborted) abortFromCaller();
  else upstreamSignal?.addEventListener("abort", abortFromCaller, { once: true });
  const timeout = globalThis.setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, requestTimeoutMs);

  try {
    const response = await fetch(`${base}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...identity, ...(init.headers ?? {}) },
      signal: controller.signal,
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new ApiError(payload.detail || `Request failed (${response.status})`, response.status);
    return payload as T;
  } catch (reason) {
    if (timedOut) throw new ApiError("Request timed out. Check your connection and try again.", 408);
    throw reason;
  } finally {
    globalThis.clearTimeout(timeout);
    upstreamSignal?.removeEventListener("abort", abortFromCaller);
  }
}

function isMissingRun(reason: unknown): reason is ApiError {
  return reason instanceof ApiError && reason.status === 404 && reason.message.includes("Career run not found");
}

function remember(run: CareerRun): CareerRun {
  saveLocalRun(run);
  return run;
}

async function portable<T>(
  action: string,
  run: CareerRun | null,
  payload: Record<string, unknown> = {},
  idempotencyKey = "",
): Promise<T> {
  return request<T>("/api/v1/portable/action", {
    method: "POST",
    body: JSON.stringify({
      action,
      ...(run ? { run } : {}),
      payload,
      ...(idempotencyKey ? { idempotency_key: idempotencyKey } : {}),
    }),
  });
}

async function restoreRun(run: CareerRun): Promise<CareerRun> {
  if (run.ranked) throw new ApiError("Ranked career state cannot be restored from the browser.", 403);
  const restored = await request<CareerRun>("/api/v1/runs/restore", {
    method: "POST",
    body: JSON.stringify({ run }),
  });
  return remember(restored);
}

async function restoreById(runId: string): Promise<CareerRun | null> {
  const local = loadLocalRun(runId);
  if (!local) return null;
  return restoreRun(local);
}

async function decide(run: CareerRun, optionId: string): Promise<{ run: CareerRun; battle_ids: string[]; featured_battle?: BattleTranscript }> {
  if (!run.ranked) {
    const result = await portable<{ run: CareerRun; battle_ids: string[]; featured_battle?: BattleTranscript }>(
      "decide",
      run,
      { expected_revision: run.revision, option_id: optionId },
      `${run.id}:${run.revision}:${optionId}`,
    );
    remember(result.run);
    if (result.featured_battle) rememberBattleTranscript(`${run.id}:${result.featured_battle.battle_id}`, result.featured_battle);
    return result;
  }

  const originalDecisionId = run.season?.decision?.id;
  const originalSeason = run.season_number;
  let source = run;
  let result;
  try {
    result = await decideOnce(source, optionId);
  } catch (reason) {
    if (isMissingRun(reason) && !run.ranked) {
      source = await restoreRun(run);
      result = await decideOnce(source, optionId);
    } else {
      if (!(reason instanceof ApiError) || reason.status !== 409) throw reason;
      const latest = await request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}`);
      if (latest.season?.decision?.id !== originalDecisionId) {
        const completed = [...latest.timeline].reverse().find((entry) => entry.type === "season.completed" && entry.season === originalSeason);
        const hashes = Array.isArray(completed?.battle_hashes) ? completed.battle_hashes as { id?: string }[] : [];
        remember(latest);
        return { run: latest, battle_ids: hashes.map((entry) => String(entry.id ?? "")).filter(Boolean) };
      }
      if (!latest.season?.decision?.options.some((option) => option.id === optionId)) throw reason;
      source = latest;
      result = await decideOnce(source, optionId);
    }
  }
  remember(result.run);
  if (result.featured_battle) rememberBattleTranscript(`${run.id}:${result.featured_battle.battle_id}`, result.featured_battle);
  return result;
}

function decideOnce(run: CareerRun, optionId: string) {
  return request<{ run: CareerRun; battle_ids: string[]; featured_battle?: BattleTranscript }>(
    `/api/v1/runs/${encodeURIComponent(run.id)}/decisions`,
    {
      method: "POST",
      headers: { "Idempotency-Key": `${run.id}:${run.revision}:${optionId}` },
      body: JSON.stringify({ expected_revision: run.revision, option_id: optionId }),
    },
  );
}

async function retryRunMutation(
  run: CareerRun,
  action: string,
  path: string,
  payload: Record<string, unknown>,
): Promise<CareerRun> {
  if (!run.ranked) {
    return remember(await portable<CareerRun>(action, run, { expected_revision: run.revision, ...payload }));
  }
  try {
    return remember(await request<CareerRun>(path, { method: "POST", body: JSON.stringify({ expected_revision: run.revision, ...payload }) }));
  } catch (reason) {
    if (isMissingRun(reason) && !run.ranked) {
      const restored = await restoreRun(run);
      return remember(await request<CareerRun>(path, { method: "POST", body: JSON.stringify({ expected_revision: restored.revision, ...payload }) }));
    }
    if (!(reason instanceof ApiError) || reason.status !== 409) throw reason;
    const latest = await request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}`);
    return remember(await request<CareerRun>(path, { method: "POST", body: JSON.stringify({ expected_revision: latest.revision, ...payload }) }));
  }
}

async function lineup(run: CareerRun, pokemonIds: string[]): Promise<CareerRun> {
  if (!run.ranked) {
    return remember(await portable<CareerRun>("lineup", run, { expected_revision: run.revision, pokemon_ids: pokemonIds }));
  }
  try {
    return remember(await lineupOnce(run, pokemonIds));
  } catch (reason) {
    if (isMissingRun(reason) && !run.ranked) {
      return remember(await lineupOnce(await restoreRun(run), pokemonIds));
    }
    if (!(reason instanceof ApiError) || reason.status !== 409) throw reason;
    const latest = await request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}`);
    const owned = new Set(latest.pokemon.map((pokemon) => pokemon.id));
    if (pokemonIds.some((id) => !owned.has(id))) return remember(latest);
    return remember(await lineupOnce(latest, pokemonIds));
  }
}

function lineupOnce(run: CareerRun, pokemonIds: string[]): Promise<CareerRun> {
  return request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}/lineup`, {
    method: "POST",
    body: JSON.stringify({ expected_revision: run.revision, pokemon_ids: pokemonIds }),
  });
}

async function useItem(run: CareerRun, item: string, pokemonId = "", stat = ""): Promise<CareerRun> {
  if (!run.ranked) {
    return remember(await portable<CareerRun>("item", run, { expected_revision: run.revision, item, pokemon_id: pokemonId, stat }));
  }
  try {
    return remember(await useItemOnce(run, item, pokemonId, stat));
  } catch (reason) {
    if (isMissingRun(reason) && !run.ranked) {
      return remember(await useItemOnce(await restoreRun(run), item, pokemonId, stat));
    }
    if (!(reason instanceof ApiError) || reason.status !== 409) throw reason;
    const latest = await request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}`);
    if ((latest.inventory[item] ?? 0) < (run.inventory[item] ?? 0)) return remember(latest);
    return remember(await useItemOnce(latest, item, pokemonId, stat));
  }
}

function useItemOnce(run: CareerRun, item: string, pokemonId: string, stat: string): Promise<CareerRun> {
  return request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}/items/use`, {
    method: "POST",
    body: JSON.stringify({ expected_revision: run.revision, item, pokemon_id: pokemonId, stat }),
  });
}

async function train(run: CareerRun, method: string, pokemonId: string): Promise<CareerRun> {
  if (!run.ranked) {
    return remember(await portable<CareerRun>("train", run, { expected_revision: run.revision, method, pokemon_id: pokemonId }));
  }
  try {
    return remember(await trainOnce(run, method, pokemonId));
  } catch (reason) {
    if (isMissingRun(reason) && !run.ranked) {
      return remember(await trainOnce(await restoreRun(run), method, pokemonId));
    }
    if (!(reason instanceof ApiError) || reason.status !== 409) throw reason;
    const latest = await request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}`);
    if (latest.season?.training_completed) return remember(latest);
    return remember(await trainOnce(latest, method, pokemonId));
  }
}

function trainOnce(run: CareerRun, method: string, pokemonId: string): Promise<CareerRun> {
  return request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}/training`, {
    method: "POST",
    body: JSON.stringify({ expected_revision: run.revision, method, pokemon_id: pokemonId }),
  });
}

async function purchase(run: CareerRun, productId: string): Promise<CareerRun> {
  if (!run.ranked) {
    return remember(await portable<CareerRun>("purchase", run, { expected_revision: run.revision, product_id: productId }));
  }
  try {
    return remember(await purchaseOnce(run, productId));
  } catch (reason) {
    if (isMissingRun(reason) && !run.ranked) {
      return remember(await purchaseOnce(await restoreRun(run), productId));
    }
    if (!(reason instanceof ApiError) || reason.status !== 409) throw reason;
    const latest = await request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}`);
    return remember(await purchaseOnce(latest, productId));
  }
}

function purchaseOnce(run: CareerRun, productId: string): Promise<CareerRun> {
  return request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}/market/purchases`, {
    method: "POST",
    body: JSON.stringify({ expected_revision: run.revision, product_id: productId }),
  });
}

async function loadBattleTranscript(runId: string, battleId: string, key: string): Promise<BattleTranscript> {
  const local = loadLocalRun(runId);
  if (local && !local.ranked) {
    const transcript = await portable<BattleTranscript>("battle", local, { battle_id: battleId });
    return rememberBattleTranscript(key, transcript);
  }
  const path = `/api/v1/runs/${encodeURIComponent(runId)}/battles/${encodeURIComponent(battleId)}`;
  try {
    const transcript = await request<BattleTranscript>(path);
    return rememberBattleTranscript(key, transcript);
  } catch (reason) {
    if (!isMissingRun(reason)) throw reason;
    const restored = await restoreById(runId);
    if (!restored) throw reason;
    const transcript = await request<BattleTranscript>(path);
    return rememberBattleTranscript(key, transcript);
  }
}

async function battle(runId: string, battleId: string): Promise<BattleTranscript> {
  const key = `${runId}:${battleId}`;
  const cached = battleCache.get(key);
  if (cached) {
    rememberBattleTranscript(key, cached);
    return cached;
  }
  const pending = battleRequests.get(key);
  if (pending) return pending;

  const requestPromise = loadBattleTranscript(runId, battleId, key);
  battleRequests.set(key, requestPromise);
  try {
    return await requestPromise;
  } finally {
    if (battleRequests.get(key) === requestPromise) battleRequests.delete(key);
  }
}

async function finalizeSeason(runId: string, battleId: string): Promise<CareerRun> {
  const local = loadLocalRun(runId);
  if (local && !local.ranked) {
    return remember(await portable<CareerRun>("finalize", local, { battle_id: battleId }));
  }
  const path = `/api/v1/runs/${encodeURIComponent(runId)}/battles/${encodeURIComponent(battleId)}/finalize`;
  try {
    return remember(await request<CareerRun>(path, { method: "POST", body: "{}" }));
  } catch (reason) {
    if (!isMissingRun(reason)) throw reason;
    const restored = await restoreById(runId);
    if (!restored) throw reason;
    return remember(await request<CareerRun>(path, { method: "POST", body: "{}" }));
  }
}

async function preseason(runId: string): Promise<PreseasonSnapshot> {
  const local = loadLocalRun(runId);
  if (local && !local.ranked) {
    const snapshot = await portable<PreseasonSnapshot>("preseason", local);
    if (snapshot.run) remember(snapshot.run);
    return snapshot;
  }
  const path = `/api/v1/runs/${encodeURIComponent(runId)}/preseason`;
  try {
    return await request<PreseasonSnapshot>(path);
  } catch (reason) {
    if (!isMissingRun(reason)) throw reason;
    const restored = await restoreById(runId);
    if (!restored) throw reason;
    return request<PreseasonSnapshot>(path);
  }
}

async function retire(runId: string): Promise<CareerRun> {
  const local = loadLocalRun(runId);
  if (local && !local.ranked) {
    return remember(await portable<CareerRun>("retire", local, { reason: "voluntary" }));
  }
  const path = `/api/v1/runs/${encodeURIComponent(runId)}/retire`;
  try {
    return remember(await request<CareerRun>(path, { method: "POST", body: JSON.stringify({ reason: "voluntary" }) }));
  } catch (reason) {
    if (!isMissingRun(reason)) throw reason;
    const restored = await restoreById(runId);
    if (!restored) throw reason;
    return remember(await request<CareerRun>(path, { method: "POST", body: JSON.stringify({ reason: "voluntary" }) }));
  }
}

async function share(runId: string): Promise<{ url: string; include_replay: boolean }> {
  const path = `/api/v1/runs/${encodeURIComponent(runId)}/shares`;
  const local = loadLocalRun(runId);
  const authMode: CareerAuthMode = local?.ranked ? "ranked" : "casual";
  try {
    return await request(path, { method: "POST", body: JSON.stringify({ include_replay: false }) }, authMode);
  } catch (reason) {
    if (!isMissingRun(reason)) throw reason;
    const restored = await restoreById(runId);
    if (!restored) throw reason;
    return request(path, { method: "POST", body: JSON.stringify({ include_replay: false }) }, authMode);
  }
}

export const careerApi = {
  catalog: (locale: string) => request<CareerCatalog>(`/api/v1/catalog?locale=${encodeURIComponent(locale)}`),
  create: async (payload: Record<string, unknown>) => remember(await portable<CareerRun>("new", null, payload)),
  run: (id: string) => {
    const local = loadLocalRun(id);
    return local ? Promise.resolve(local) : request<CareerRun>(`/api/v1/runs/${encodeURIComponent(id)}`);
  },
  preseason,
  chooseClub: (run: CareerRun, offerId: string) => retryRunMutation(run, "club", `/api/v1/runs/${encodeURIComponent(run.id)}/club`, { offer_id: offerId }),
  chooseSponsor: (run: CareerRun, offerId: string) => retryRunMutation(run, "sponsor", `/api/v1/runs/${encodeURIComponent(run.id)}/sponsor`, { offer_id: offerId }),
  capture: (run: CareerRun, candidateId: string) => retryRunMutation(run, "capture", `/api/v1/runs/${encodeURIComponent(run.id)}/captures`, { candidate_id: candidateId }),
  lineup,
  useItem,
  train,
  purchase,
  decide,
  battle,
  finalizeSeason,
  retire,
  share,
  publicShare: (shareId: string) => request<{ share_id: string; summary: Record<string, unknown>; has_replay: boolean }>(`/api/v1/shares/${encodeURIComponent(shareId)}`),
  daily: (day: string) => request<Record<string, unknown>>(`/api/v1/daily/${day}`),
  dailyAttempt: (day: string, payload: Record<string, unknown>) => request<{ run: CareerRun; attempt_no: number }>(
    `/api/v1/daily/${day}/attempts`,
    { method: "POST", body: JSON.stringify(payload) },
  ),
  leaderboard: (day: string, mode: string) => request<Record<string, unknown>>(`/api/v1/daily/${day}/leaderboards/${mode}`),
};