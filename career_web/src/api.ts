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

async function requestRun(path: string, init: RequestInit = {}, authMode: CareerAuthMode = authModeForPath(path)): Promise<CareerRun> {
  try {
    return remember(await request<CareerRun>(path, init, authMode));
  } catch (reason) {
    if (isMissingRun(reason)) {
      const runId = path.match(/^\/api\/v1\/runs\/([^/]+)/)?.[1];
      if (runId) {
        const local = loadLocalRun(runId);
        if (local) return local;
      }
    }
    throw reason;
  }
}

export const careerApi = {
  catalog: (locale: string) => request<CareerCatalog>(`/api/v1/catalog?locale=${locale}`),
  start: (payload: Record<string, unknown>) => requestRun("/api/v1/runs", { method: "POST", body: JSON.stringify(payload) }),
  getRun: (runId: string) => requestRun(`/api/v1/runs/${runId}`),
  deleteRun: (runId: string) => request<void>(`/api/v1/runs/${runId}`, { method: "DELETE" }),
  restoreRun: (payload: Record<string, unknown>) => requestRun("/api/v1/runs/restore", { method: "POST", body: JSON.stringify(payload) }, "casual"),
  portableAction: (payload: Record<string, unknown>) => requestRun("/api/v1/portable/action", { method: "POST", body: JSON.stringify(payload) }, "casual"),
  clubOffers: (runId: string) => request<ClubOffer[]>(`/api/v1/runs/${runId}/club-offers`),
  chooseClub: (runId: string, offerId: string) => requestRun(`/api/v1/runs/${runId}/club`, { method: "POST", body: JSON.stringify({ offer_id: offerId }) }),
  sponsorOffers: (runId: string) => request<SponsorOffer[]>(`/api/v1/runs/${runId}/sponsor-offers`),
  chooseSponsor: (runId: string, offerId: string) => requestRun(`/api/v1/runs/${runId}/sponsor`, { method: "POST", body: JSON.stringify({ offer_id: offerId }) }),
  captureCandidates: (runId: string) => request<CaptureCandidate[]>(`/api/v1/runs/${runId}/capture-candidates`),
  capture: (runId: string, candidateId: string) => requestRun(`/api/v1/runs/${runId}/capture`, { method: "POST", body: JSON.stringify({ candidate_id: candidateId }) }),
  skipCapture: (runId: string) => requestRun(`/api/v1/runs/${runId}/capture/skip`, { method: "POST" }),
  preseason: (runId: string) => request<PreseasonSnapshot>(`/api/v1/runs/${runId}/preseason`),
  startSeason: (runId: string) => requestRun(`/api/v1/runs/${runId}/season`, { method: "POST" }),
  train: (runId: string, pokemonId: string, method: string) => requestRun(`/api/v1/runs/${runId}/train`, { method: "POST", body: JSON.stringify({ pokemon_id: pokemonId, method }) }),
  trainAuto: (runId: string, payload: Record<string, unknown>) => requestRun(`/api/v1/runs/${runId}/train/auto`, { method: "POST", body: JSON.stringify(payload) }),
  decision: (runId: string, optionId: string) => requestRun(`/api/v1/runs/${runId}/decision`, { method: "POST", body: JSON.stringify({ option_id: optionId }) }),
  battle: async (runId: string, battleId: string) => {
    const key = `${runId}:${battleId}`;
    const cached = battleCache.get(key);
    if (cached) return cached;
    const pending = battleRequests.get(key);
    if (pending) return pending;
    const requestPromise = request<BattleTranscript>(`/api/v1/runs/${runId}/battles/${battleId}`)
      .then((transcript) => rememberBattleTranscript(key, transcript))
      .finally(() => battleRequests.delete(key));
    battleRequests.set(key, requestPromise);
    return requestPromise;
  },
  playBattle: (runId: string, battleId: string) => requestRun(`/api/v1/runs/${runId}/battles/${battleId}/play`, { method: "POST" }),
  finishSeason: (runId: string) => requestRun(`/api/v1/runs/${runId}/season/finish`, { method: "POST" }),
  retire: (runId: string) => requestRun(`/api/v1/runs/${runId}/retire`, { method: "POST" }),
  leaderboard: (day: string, mode: string) => request<Record<string, unknown>>(`/api/v1/daily/${day}/leaderboards/${mode}`),
};