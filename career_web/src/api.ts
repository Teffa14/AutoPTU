import { authHeaders } from "./auth";
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
}

const base = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";
const battleCache = new Map<string, BattleTranscript>();

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const identity = await authHeaders();
  const response = await fetch(`${base}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...identity, ...(init.headers ?? {}) },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(payload.detail || `Request failed (${response.status})`, response.status);
  return payload as T;
}

async function decide(run: CareerRun, optionId: string): Promise<{ run: CareerRun; battle_ids: string[]; featured_battle?: BattleTranscript }> {
  const originalDecisionId = run.season?.decision?.id;
  const originalSeason = run.season_number;
  let source = run;
  let result;
  try {
    result = await decideOnce(source, optionId);
  } catch (reason) {
    if (!(reason instanceof ApiError) || reason.status !== 409) throw reason;
    const latest = await request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}`);
    if (latest.season?.decision?.id !== originalDecisionId) {
      const completed = [...latest.timeline].reverse().find((entry) => entry.type === "season.completed" && entry.season === originalSeason);
      const hashes = Array.isArray(completed?.battle_hashes) ? completed.battle_hashes as { id?: string }[] : [];
      return { run: latest, battle_ids: hashes.map((entry) => String(entry.id ?? "")).filter(Boolean) };
    }
    if (!latest.season?.decision?.options.some((option) => option.id === optionId)) throw reason;
    source = latest;
    result = await decideOnce(source, optionId);
  }
  if (result.featured_battle) battleCache.set(`${run.id}:${result.featured_battle.battle_id}`, result.featured_battle);
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

async function retryRunMutation(run: CareerRun, path: string, payload: Record<string, unknown>): Promise<CareerRun> {
  try {
    return await request<CareerRun>(path, { method: "POST", body: JSON.stringify({ expected_revision: run.revision, ...payload }) });
  } catch (reason) {
    if (!(reason instanceof ApiError) || reason.status !== 409) throw reason;
    const latest = await request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}`);
    return request<CareerRun>(path, { method: "POST", body: JSON.stringify({ expected_revision: latest.revision, ...payload }) });
  }
}

async function lineup(run: CareerRun, pokemonIds: string[]): Promise<CareerRun> {
  try {
    return await lineupOnce(run, pokemonIds);
  } catch (reason) {
    if (!(reason instanceof ApiError) || reason.status !== 409) throw reason;
    const latest = await request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}`);
    const owned = new Set(latest.pokemon.map((pokemon) => pokemon.id));
    if (pokemonIds.some((id) => !owned.has(id))) return latest;
    return lineupOnce(latest, pokemonIds);
  }
}

function lineupOnce(run: CareerRun, pokemonIds: string[]): Promise<CareerRun> {
  return request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}/lineup`, {
    method: "POST",
    body: JSON.stringify({ expected_revision: run.revision, pokemon_ids: pokemonIds }),
  });
}

async function useItem(run: CareerRun, item: string, pokemonId = "", stat = ""): Promise<CareerRun> {
  try {
    return await useItemOnce(run, item, pokemonId, stat);
  } catch (reason) {
    if (!(reason instanceof ApiError) || reason.status !== 409) throw reason;
    const latest = await request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}`);
    if ((latest.inventory[item] ?? 0) < (run.inventory[item] ?? 0)) return latest;
    return useItemOnce(latest, item, pokemonId, stat);
  }
}

function useItemOnce(run: CareerRun, item: string, pokemonId: string, stat: string): Promise<CareerRun> {
  return request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}/items/use`, {
    method: "POST",
    body: JSON.stringify({ expected_revision: run.revision, item, pokemon_id: pokemonId, stat }),
  });
}

async function train(run: CareerRun, method: string, pokemonId: string): Promise<CareerRun> {
  try {
    return await trainOnce(run, method, pokemonId);
  } catch (reason) {
    if (!(reason instanceof ApiError) || reason.status !== 409) throw reason;
    const latest = await request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}`);
    if (latest.season?.training_completed) return latest;
    return trainOnce(latest, method, pokemonId);
  }
}

function trainOnce(run: CareerRun, method: string, pokemonId: string): Promise<CareerRun> {
  return request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}/training`, {
    method: "POST",
    body: JSON.stringify({ expected_revision: run.revision, method, pokemon_id: pokemonId }),
  });
}

async function purchase(run: CareerRun, productId: string): Promise<CareerRun> {
  try {
    return await purchaseOnce(run, productId);
  } catch (reason) {
    if (!(reason instanceof ApiError) || reason.status !== 409) throw reason;
    const latest = await request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}`);
    return purchaseOnce(latest, productId);
  }
}

function purchaseOnce(run: CareerRun, productId: string): Promise<CareerRun> {
  return request<CareerRun>(`/api/v1/runs/${encodeURIComponent(run.id)}/market/purchases`, {
    method: "POST",
    body: JSON.stringify({ expected_revision: run.revision, product_id: productId }),
  });
}

async function battle(runId: string, battleId: string): Promise<BattleTranscript> {
  const key = `${runId}:${battleId}`;
  const cached = battleCache.get(key);
  if (cached) return cached;
  return request<BattleTranscript>(`/api/v1/runs/${encodeURIComponent(runId)}/battles/${encodeURIComponent(battleId)}`);
}

function finalizeSeason(runId: string, battleId: string): Promise<CareerRun> {
  return request<CareerRun>(
    `/api/v1/runs/${encodeURIComponent(runId)}/battles/${encodeURIComponent(battleId)}/finalize`,
    { method: "POST", body: "{}" },
  );
}

export const careerApi = {
  catalog: (locale: string) => request<CareerCatalog>(`/api/v1/catalog?locale=${encodeURIComponent(locale)}`),
  create: (payload: Record<string, unknown>) => request<CareerRun>("/api/v1/runs", { method: "POST", body: JSON.stringify(payload) }),
  run: (id: string) => request<CareerRun>(`/api/v1/runs/${encodeURIComponent(id)}`),
  preseason: (runId: string) => request<PreseasonSnapshot>(`/api/v1/runs/${encodeURIComponent(runId)}/preseason`),
  chooseClub: (run: CareerRun, offerId: string) => retryRunMutation(run, `/api/v1/runs/${encodeURIComponent(run.id)}/club`, { offer_id: offerId }),
  chooseSponsor: (run: CareerRun, offerId: string) => retryRunMutation(run, `/api/v1/runs/${encodeURIComponent(run.id)}/sponsor`, { offer_id: offerId }),
  capture: (run: CareerRun, candidateId: string) => retryRunMutation(run, `/api/v1/runs/${encodeURIComponent(run.id)}/captures`, { candidate_id: candidateId }),
  lineup,
  useItem,
  train,
  purchase,
  decide,
  battle,
  finalizeSeason,
  retire: (runId: string) => request<CareerRun>(`/api/v1/runs/${encodeURIComponent(runId)}/retire`, { method: "POST", body: JSON.stringify({ reason: "voluntary" }) }),
  share: (runId: string) => request<{ url: string; include_replay: boolean }>(
    `/api/v1/runs/${encodeURIComponent(runId)}/shares`,
    { method: "POST", body: JSON.stringify({ include_replay: false }) },
  ),
  publicShare: (shareId: string) => request<{ share_id: string; summary: Record<string, unknown>; has_replay: boolean }>(`/api/v1/shares/${encodeURIComponent(shareId)}`),
  daily: (day: string) => request<Record<string, unknown>>(`/api/v1/daily/${day}`),
  dailyAttempt: (day: string, payload: Record<string, unknown>) => request<{ run: CareerRun; attempt_no: number }>(
    `/api/v1/daily/${day}/attempts`,
    { method: "POST", body: JSON.stringify(payload) },
  ),
  leaderboard: (day: string, mode: string) => request<Record<string, unknown>>(`/api/v1/daily/${day}/leaderboards/${mode}`),
};
