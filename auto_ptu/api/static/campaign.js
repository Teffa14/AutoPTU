const $ = (selector) => document.querySelector(selector);
const gate = $("#campaign-gate");
const workspace = $("#campaign-workspace");
const toastEl = $("#campaign-toast");
const SESSION_KEY = "autoptu_campaign_session";
const AGENT_MODEL_KEY = "autoptu_campaign_agent_models";

let campaign = null;
let campaignId = "";
let participantToken = "";
let campaignSocket = null;
let reconnectTimer = null;
let activeSeatId = "";
let agentBusy = false;
let autoplayEnabled = false;
let autoplayRoundsInScene = 0;
let autoplaySceneId = "";
let sceneChoiceActions = [];
let mapTravelBusy = false;
let selectedExplorationActorId = "";
let selectedExplorationPointId = "";
let explorationMoveBusy = false;

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
}

function formPayload(form) {
  return Object.fromEntries(new FormData(form).entries());
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (participantToken) headers.Authorization = `Bearer ${participantToken}`;
  const response = await fetch(path, { ...options, headers });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`);
  return payload;
}

function toast(message, kind = "ok") {
  toastEl.textContent = message;
  toastEl.className = `campaign-toast ${kind === "error" ? "error" : ""}`;
  clearTimeout(toastEl._timer);
  toastEl._timer = setTimeout(() => toastEl.classList.add("hidden"), 3200);
}

function rememberSession() {
  localStorage.setItem(SESSION_KEY, JSON.stringify({ campaignId, participantToken }));
}

function forgetSession() {
  localStorage.removeItem(SESSION_KEY);
  campaign = null;
  campaignId = "";
  participantToken = "";
  autoplayEnabled = false;
  clearTimeout(reconnectTimer);
  reconnectTimer = null;
  if (campaignSocket) campaignSocket.close();
  campaignSocket = null;
  workspace.classList.add("hidden");
  gate.classList.remove("hidden");
  loadCampaigns().catch(reportError);
}

function reportError(error) {
  toast(String(error?.message || error || "Something went wrong."), "error");
}

function can(commandName) {
  return Array.isArray(campaign?.permissions) && campaign.permissions.includes(commandName);
}

function isAgentHost() {
  return !!campaign?.viewer?.id && campaign.viewer.id === campaign.world?.agent_host_participant_id;
}

function canDirectAgents() {
  return campaign?.viewer?.role === "gm" || isAgentHost();
}

function atActiveSceneLocation() {
  const required = String(campaign?.active_scene?.metadata?.location_id || "");
  return !required || required === String(campaign?.world?.current_location_id || "");
}

function canEnterBattle() {
  return (can("battle.link") || isAgentHost()) && atActiveSceneLocation();
}

async function loadCampaigns() {
  const payload = await api("/api/campaigns");
  const records = payload.campaigns || [];
  const select = $("#join-campaign-id");
  const previous = select.value;
  select.innerHTML = '<option value="">Choose campaign</option>';
  records.forEach((entry) => {
    const option = document.createElement("option");
    option.value = entry.id;
    option.textContent = `${entry.name} · ${entry.participants} in party`;
    select.appendChild(option);
  });
  if (records.some((entry) => entry.id === previous)) select.value = previous;
  const stored = JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
  $("#campaign-list").innerHTML = records.length
    ? records.map((entry) => `<article class="campaign-list-card"><strong>${escapeHtml(entry.name)}</strong><span>${escapeHtml(entry.active_scene || "Adventure not started")} · chapter revision ${entry.revision}</span>${stored?.campaignId === entry.id ? `<button type="button" data-resume="${escapeHtml(entry.id)}">Continue adventure</button>` : `<button type="button" data-join="${escapeHtml(entry.id)}">Join adventure</button>`}</article>`).join("")
    : '<div class="campaign-list-card"><strong>No saved adventures</strong><span>Begin The Prism Trail above.</span></div>';
}

async function enterCampaign(id, token) {
  campaignId = id;
  participantToken = token;
  const payload = await api(`/api/campaigns/${encodeURIComponent(id)}`);
  campaign = payload.campaign;
  rememberSession();
  gate.classList.add("hidden");
  workspace.classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "auto" });
  renderCampaign();
  loadAgentStatus().catch(() => {});
  connectCampaignSocket();
}

function connectCampaignSocket() {
  clearTimeout(reconnectTimer);
  if (!campaignId || !participantToken) return;
  if (campaignSocket) campaignSocket.close();
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${protocol}//${location.host}/api/campaigns/${encodeURIComponent(campaignId)}/ws?token=${encodeURIComponent(participantToken)}`;
  const socket = new WebSocket(url);
  campaignSocket = socket;
  $("#connection-state").textContent = "Connecting to party…";
  socket.addEventListener("open", () => { if (campaignSocket === socket) $("#connection-state").textContent = "Party live"; });
  socket.addEventListener("message", (event) => {
    let message = null;
    try { message = JSON.parse(event.data); } catch (_error) { return; }
    if (message.type === "campaign.snapshot" && message.campaign) {
      campaign = message.campaign;
      renderCampaign();
      return;
    }
    if (message.type === "campaign.updated" && Number(message.seq || 0) > Number(campaign?.revision || 0)) {
      refreshCampaign().catch(reportError);
      return;
    }
    if (message.type === "campaign.event" && Number(message.event?.seq || 0) > Number(campaign?.revision || 0)) {
      refreshCampaign().catch(reportError);
    }
  });
  socket.addEventListener("close", () => {
    if (campaignSocket !== socket || !campaignId || !participantToken) return;
    $("#connection-state").textContent = "Reconnecting…";
    reconnectTimer = setTimeout(connectCampaignSocket, 1500);
  });
  socket.addEventListener("error", () => socket.close());
}

async function refreshCampaign() {
  if (!campaignId || !participantToken || agentBusy) return;
  const payload = await api(`/api/campaigns/${encodeURIComponent(campaignId)}`);
  if (Number(payload.campaign?.revision || 0) === Number(campaign?.revision || 0)) return;
  campaign = payload.campaign;
  renderCampaign();
}

async function command(type, payload = {}) {
  const playerCommands = new Set(["chat.post", "roll.check", "journal.add", "safety.pause", "participant.control", "actor.sheet.update", "starter.select", "location.travel", "exploration.token.move", "exploration.point.interact", "craft.item", "shop.buy", "shop.sell", "downtime.activity", "npc.talk", "builder.sync"]);
  const actingId = campaign?.viewer?.role === "gm" && activeSeatId && playerCommands.has(type) ? activeSeatId : "";
  const response = await api(`/api/campaigns/${encodeURIComponent(campaignId)}/command`, {
    method: "POST",
    body: JSON.stringify({ type, payload, ...(actingId ? { as_participant_id: actingId } : {}) }),
  });
  campaign = response.campaign;
  renderCampaign();
  return response.event;
}

function setFormAccess(selector, allowed) {
  const element = $(selector);
  if (!element) return;
  element.querySelectorAll("input,select,textarea,button").forEach((control) => { control.disabled = !allowed; });
  element.classList.toggle("hidden", !allowed);
}

function activeSceneIndex() {
  return Math.max(0, (campaign?.scenes || []).findIndex((entry) => entry.id === campaign?.active_scene_id));
}

function renderCampaign() {
  if (!campaign) return;
  const viewer = campaign.viewer || {};
  const scenes = campaign.scenes || [];
  const sceneIndex = activeSceneIndex();
  workspace.dataset.sceneKind = String(campaign.active_scene?.kind || "quiet").toLowerCase();
  $("#campaign-name").textContent = campaign.name;
  $("#campaign-system").textContent = campaign.system;
  $("#campaign-time").textContent = campaign.time_label;
  $("#viewer-role").textContent = String(viewer.role || "viewer").toUpperCase();
  $("#connection-state").textContent = `Story ${campaign.revision}`;
  const isGm = viewer.role === "gm";
  $("#chapter-label").textContent = isGm
    ? `Chapter ${sceneIndex + 1} of ${Math.max(1, scenes.length)}`
    : `Chapter ${campaign.active_scene?.order || sceneIndex + 1} · ${scenes.length > 1 ? `${scenes.length} revealed` : "the road ahead is hidden"}`;
  $("#chapter-progress-fill").style.width = isGm
    ? `${Math.min(100, ((sceneIndex + 1) / Math.max(1, scenes.length)) * 100)}%`
    : `${campaign.active_scene?.status === "complete" ? 100 : 58}%`;
  $("#campaign-invite").classList.toggle("hidden", !campaign.invite_code);
  $("#campaign-invite").textContent = campaign.invite_code ? `Invite ${campaign.invite_code}` : "";
  $("#safety-banner").classList.toggle("hidden", !campaign.safety_paused);
  $("#safety-message").textContent = campaign.safety_message || "Check in before play resumes.";
  $("#safety-resume").classList.toggle("hidden", !can("safety.resume"));
  $("#safety-pause").disabled = !can("safety.pause") || campaign.safety_paused;
  $("#scene-new-toggle").classList.toggle("hidden", !can("scene.create"));
  $("#director-tools").classList.toggle("hidden", viewer.role !== "gm");
  $("#agent-party").classList.toggle("hidden", !canDirectAgents());
  setFormAccess("#clock-create-form", can("clock.create"));
  setFormAccess("#quest-create-form", can("quest.create"));
  setFormAccess("#faction-form", can("faction.adjust"));
  setFormAccess("#time-form", can("time.set"));
  setFormAccess("#chat-form", can("chat.post"));
  setFormAccess("#roll-form", can("roll.check"));
  setFormAccess("#journal-form", can("journal.add"));
  renderScenes();
  renderParticipants();
  renderStarterChoice();
  renderWorld();
  renderExploration();
  renderNpcs();
  renderStory();
  renderClocks();
  renderQuests();
  renderFactions();
  renderJournal();
  renderChoices();
  renderContinue();
}

function renderScenes() {
  const scenes = campaign.scenes || [];
  $("#scene-list").innerHTML = scenes.length
    ? scenes.map((scene) => {
      const active = scene.id === campaign.active_scene_id;
      const hidden = !scene.published;
      const gm = campaign.viewer?.role === "gm";
      const stateLabel = active ? "Playing now" : hidden ? "Hidden from players" : scene.available ? "Ready for the table" : "Revealed preview";
      const activateDisabled = !can("scene.activate") || active || !scene.available;
      const controls = gm && !active
        ? `<span class="scene-director-controls">${hidden
          ? `<button type="button" data-scene-visibility="${escapeHtml(scene.id)}" data-published="true" data-available="false">Reveal</button>`
          : `<button type="button" data-scene-visibility="${escapeHtml(scene.id)}" data-published="true" data-available="${scene.available ? "false" : "true"}">${scene.available ? "Hold" : "Make ready"}</button><button type="button" data-scene-visibility="${escapeHtml(scene.id)}" data-published="false" data-available="false">Hide</button>`}</span>`
        : "";
      return `<article class="scene-card scene-card-${escapeHtml(scene.kind)} ${active ? "active" : ""} ${hidden ? "scene-hidden" : ""} ${scene.available ? "scene-available" : ""}" data-kind="${escapeHtml(scene.kind)}"><button type="button" class="scene-card-main" data-scene="${escapeHtml(scene.id)}" ${activateDisabled ? "disabled" : ""}><i aria-hidden="true"></i><strong>${Number(scene.order || 0)}. ${escapeHtml(scene.title)}</strong><span>${escapeHtml(scene.kind)} · ${escapeHtml(scene.location || "Unknown location")}</span><small>${escapeHtml(stateLabel)}</small></button>${controls}</article>`;
    }).join("")
    : '<div class="campaign-list-card"><span>The first chapter has not opened.</span></div>';
  const scene = campaign.active_scene;
  $("#scene-kind").textContent = scene ? scene.kind : "No active scene";
  $("#scene-title").textContent = scene ? scene.title : "The adventure awaits";
  $("#scene-location").textContent = scene?.location || "";
  $("#scene-summary").textContent = scene?.summary || "Choose how your Trainer enters the story.";
  const dangerLabels = { roleplay: "Story scene", exploration: "Exploration", travel: "On the road", combat: "Battle ready", downtime: "Safe moment" };
  $("#scene-danger").textContent = dangerLabels[scene?.kind] || "Adventure";
  $("#open-battle-link").classList.toggle("hidden", !scene || scene.kind !== "combat" || !!scene.metadata?.battle_completed || !atActiveSceneLocation());
}

function initials(name) {
  return String(name || "?").split(/\s+/).slice(0, 2).map((part) => part[0] || "").join("").toUpperCase();
}

function renderParticipants() {
  const scene = campaign.active_scene;
  $("#participant-list").innerHTML = (campaign.participants || []).map((entry) => {
    const color = entry.color || (entry.role === "gm" ? "#f6c453" : "#79aef2");
    const agentBadge = `<i class="agent-seat-badge">${entry.controller === "ai" ? "AI" : entry.id === campaign.viewer?.id ? "YOU" : "HUMAN"}</i>`;
    const stepButton = entry.is_agent && entry.controller === "ai" && canDirectAgents() ? `<button class="agent-seat-turn" type="button" data-agent-step="${escapeHtml(entry.id)}">Let act</button>` : (scene?.spotlight_id === entry.id ? '<i class="spotlight-dot" title="In the spotlight"></i>' : "");
    const mayControl = (campaign.viewer?.role === "gm" && entry.id !== campaign.viewer.id) || entry.id === campaign.viewer?.id || (isAgentHost() && entry.role === "player");
    const control = mayControl && can("participant.control") ? `<button class="seat-control" type="button" data-seat-control="${escapeHtml(entry.id)}" data-controller="${entry.controller === "ai" ? "human" : "ai"}">${entry.controller === "ai" ? "Take control" : "Hand to AI"}</button>` : "";
    return `<article class="participant-card ${activeSeatId === entry.id ? "active-seat" : ""}" style="--participant-color:${escapeHtml(color)}"><span class="participant-avatar">${escapeHtml(initials(entry.name))}</span><div><strong>${escapeHtml(entry.name)}</strong><span class="companion">${escapeHtml(entry.companion || entry.role)}</span><small>${escapeHtml(entry.controller || "human")}-controlled ${escapeHtml(entry.role)}</small></div><div>${agentBadge}${stepButton}${control}</div></article>`;
  }).join("");
  const acting = $("#acting-seat");
  if (campaign.viewer?.role === "gm") {
    const seats = (campaign.participants || []).filter((entry) => entry.role !== "spectator" && entry.controller === "human");
    acting.classList.remove("hidden");
    acting.innerHTML = seats.map((entry) => `<option value="${escapeHtml(entry.id)}">Act as ${escapeHtml(entry.name)}</option>`).join("");
    if (!seats.some((entry) => entry.id === activeSeatId)) activeSeatId = campaign.viewer.id;
    acting.value = activeSeatId;
  } else {
    activeSeatId = campaign.viewer?.id || "";
    acting.classList.add("hidden");
  }
  const spotlight = $("#spotlight-select");
  spotlight.innerHTML = '<option value="">Open party</option>' + (campaign.participants || []).filter((entry) => entry.role !== "spectator").map((entry) => `<option value="${escapeHtml(entry.id)}">${escapeHtml(entry.name)}</option>`).join("");
  spotlight.value = scene?.spotlight_id || "";
  spotlight.disabled = !can("spotlight.set") || !scene;
}

function currentSeatId() {
  return activeSeatId || campaign?.viewer?.id || "";
}

function ownedActors(participantId = currentSeatId()) {
  return (campaign?.actors || []).filter((entry) => entry.owner_participant_id === participantId);
}

function renderStarterChoice() {
  const panel = $("#starter-choice-panel");
  const ownedStarter = ownedActors().find((entry) => entry.kind === "pokemon" && entry.sheet?.starter);
  const candidates = (campaign.actors || []).filter((entry) => entry.kind === "pokemon" && entry.sheet?.starter_candidate && !entry.owner_participant_id);
  const inStarterScene = campaign.active_scene?.id === "scene-starter-day";
  const show = inStarterScene && (!!ownedStarter || (candidates.length && can("starter.select")));
  panel.classList.toggle("hidden", !show);
  panel.classList.toggle("starter-confirmed", !!ownedStarter);
  const kicker = panel.querySelector("header span");
  const heading = panel.querySelector("header h3");
  if (ownedStarter) {
    kicker.textContent = "Your party changed";
    heading.textContent = `${ownedStarter.name || ownedStarter.species} is your partner`;
    $("#starter-choice-list").innerHTML = `<article class="starter-roster-confirmation"><span class="starter-sigil">${escapeHtml(String(ownedStarter.species || "?").slice(0, 1))}</span><div><strong>${escapeHtml(ownedStarter.name || ownedStarter.species)}</strong><small>${escapeHtml(ownedStarter.species)} · Level ${Number(ownedStarter.level || 1)}</small><em>Persistent party ownership confirmed · tactical battle roster synced</em></div></article>`;
  } else {
    kicker.textContent = "Your first real choice";
    heading.textContent = "Which Pokémon chooses you back?";
    $("#starter-choice-list").innerHTML = show ? candidates.map((entry) => `<button type="button" data-starter="${escapeHtml(entry.species)}"><span class="starter-sigil">${escapeHtml(String(entry.species || "?").slice(0, 1))}</span><strong>${escapeHtml(entry.species)}</strong><small>Level ${Number(entry.level || 1)} · choose together</small></button>`).join("") : "";
  }
}

function renderWorldMap(locations, current) {
  const map = $("#campaign-world-map");
  const byId = new Map(locations.map((entry) => [entry.id, entry]));
  const neighbors = new Set(current.neighbors || []);
  const revealed = new Set(campaign.world?.revealed_location_ids || []);
  const gm = campaign.viewer?.role === "gm";
  const lines = [];
  const seenEdges = new Set();
  locations.forEach((entry) => {
    (entry.neighbors || []).forEach((neighborId) => {
      const neighbor = byId.get(neighborId);
      if (!neighbor) return;
      const edgeId = [entry.id, neighbor.id].sort().join("::");
      if (seenEdges.has(edgeId)) return;
      seenEdges.add(edgeId);
      const hidden = gm && (!revealed.has(entry.id) || !revealed.has(neighbor.id));
      lines.push(`<line class="${hidden ? "map-edge-hidden" : ""}" x1="${Number(entry.map_x || 50)}" y1="${Number(entry.map_y || 45)}" x2="${Number(neighbor.map_x || 50)}" y2="${Number(neighbor.map_y || 45)}"></line>`);
    });
  });
  const nodes = locations.map((entry) => {
    const isCurrent = entry.id === current.id;
    const canTravel = !isCurrent && neighbors.has(entry.id) && revealed.has(entry.id) && can("location.travel") && !mapTravelBusy;
    const hidden = gm && !revealed.has(entry.id) && !isCurrent;
    const classes = ["map-node", isCurrent ? "map-node-current" : "", canTravel ? "map-node-travel" : "map-node-locked", hidden ? "map-node-hidden" : ""].filter(Boolean).join(" ");
    const token = isCurrent ? '<span class="party-map-token" data-party-token="true" draggable="true" aria-label="Drag party marker">◆</span>' : "";
    const label = hidden ? "GM only" : canTravel ? "Click or drop to travel" : isCurrent ? "Party location" : "Route not connected";
    return `<button type="button" class="${classes}" style="--map-x:${Number(entry.map_x || 50)}%;--map-y:${Number(entry.map_y || 45)}%" ${canTravel ? `data-travel-map="${escapeHtml(entry.id)}"` : isCurrent ? 'aria-disabled="true"' : "disabled"} aria-label="${escapeHtml(`${entry.name}. ${label}`)}"><i></i>${token}<strong>${escapeHtml(entry.name)}</strong><small>${escapeHtml(label)}</small></button>`;
  }).join("");
  map.innerHTML = `<svg viewBox="0 0 100 90" preserveAspectRatio="none" aria-hidden="true">${lines.join("")}</svg>${nodes}`;
  map.classList.toggle("is-travelling", mapTravelBusy);
  $("#map-help").textContent = gm
    ? "Gold places are published. Dim places remain GM-only until a chapter or location is revealed."
    : "Only places the GM revealed exist on this map. Click a connected place, or drag the party marker onto it.";
}

function renderExploration() {
  const card = $("#exploration-card");
  const board = $("#exploration-board");
  const panel = $("#exploration-interaction-panel");
  const exploration = campaign.exploration;
  card.classList.toggle("hidden", !exploration);
  if (!exploration) {
    selectedExplorationActorId = "";
    selectedExplorationPointId = "";
    board.innerHTML = "";
    panel.innerHTML = "";
    return;
  }
  const gm = campaign.viewer?.role === "gm";
  const tokens = exploration.tokens || [];
  const movableTokens = gm ? tokens : tokens.filter((token) => token.owned);
  if (!movableTokens.some((token) => token.actor_id === selectedExplorationActorId)) {
    selectedExplorationActorId = movableTokens[0]?.actor_id || "";
  }
  const selected = tokens.find((token) => token.actor_id === selectedExplorationActorId);
  const reachable = new Map((selected?.reachable_cells || []).map((cell) => [String(cell.key || `${cell.x},${cell.y}`), cell]));
  const cells = exploration.cells || [];
  const points = exploration.points || [];
  if (!points.some((point) => point.id === selectedExplorationPointId)) selectedExplorationPointId = "";
  const selectedPoint = points.find((point) => point.id === selectedExplorationPointId);
  const pointsByCell = new Map();
  points.forEach((point) => {
    const key = `${point.x},${point.y}`;
    if (!pointsByCell.has(key)) pointsByCell.set(key, []);
    pointsByCell.get(key).push(point);
  });
  const tokensByCell = new Map();
  tokens.forEach((token) => {
    const key = `${token.x},${token.y}`;
    if (!tokensByCell.has(key)) tokensByCell.set(key, []);
    tokensByCell.get(key).push(token);
  });
  const theme = String(exploration.theme || "route").toLowerCase().replace(/[^a-z0-9-]+/g, "-");
  $("#exploration-name").textContent = exploration.name || "Current area";
  $("#exploration-gm-controls").classList.toggle("hidden", !gm);
  $("#exploration-token-picker").innerHTML = movableTokens.length
    ? movableTokens.map((token) => `<span class="exploration-token-control ${token.actor_id === selectedExplorationActorId ? "active" : ""}"><button type="button" data-exploration-select="${escapeHtml(token.actor_id)}"><i style="--token-color:${token.kind === "trainer" ? "#67e8f9" : "#f6c453"}"></i>${escapeHtml(token.name || token.species || "Token")} <small>S${Number(token.speed || 1)}</small></button>${gm ? `<button type="button" class="token-visibility-button" data-exploration-token-visibility="${escapeHtml(token.actor_id)}" data-revealed="${token.revealed ? "false" : "true"}" aria-label="${token.revealed ? "Hide" : "Reveal"} ${escapeHtml(token.name)}">${token.revealed ? "◉" : "○"}</button>` : ""}</span>`).join("")
    : '<span class="empty-action">No owned token is on this floor.</span>';
  board.className = `exploration-board theme-${theme} ${explorationMoveBusy ? "is-moving" : ""}`;
  board.style.setProperty("--exploration-width", Number(exploration.width || 10));
  board.style.setProperty("--exploration-height", Number(exploration.height || 7));
  board.innerHTML = cells.map((cell) => {
    const key = String(cell.key || `${cell.x},${cell.y}`);
    const cellTokens = (tokensByCell.get(key) || []).sort((a, b) => String(a.actor_id).localeCompare(String(b.actor_id)));
    const cellPoints = (pointsByCell.get(key) || []).sort((a, b) => String(a.id).localeCompare(String(b.id)));
    const route = reachable.get(key);
    const legal = !!selected && !!route && can("exploration.token.move") && !explorationMoveBusy;
    const terrain = String(cell.terrain || "floor").toLowerCase().replace(/[^a-z0-9-]+/g, "-");
    const pointMarkup = cellPoints.map((point) => {
      const classes = [point.revealed ? "revealed" : "secret", point.available ? "" : "locked", point.completed ? "completed" : "", point.can_interact ? "interactable" : "", point.id === selectedExplorationPointId ? "selected" : ""].filter(Boolean).join(" ");
      const icon = point.completed ? "✓" : !point.available ? "×" : point.revealed ? "!" : "?";
      const visibility = gm ? (point.revealed ? "visible to players" : "GM hidden") : (point.available ? "select to interact" : "locked by the GM");
      return `<button type="button" class="exploration-point ${classes}" data-exploration-point-select="${escapeHtml(point.id)}" title="${escapeHtml(`${point.label} · ${visibility}`)}"><span>${icon}</span><em>${escapeHtml(point.label)}</em></button>`;
    }).join("");
    const tokenMarkup = cellTokens.map((token) => {
      const canMove = gm || token.owned;
      const initials = String(token.name || token.species || "?").split(/\s+/).map((word) => word[0]).join("").slice(0, 2).toUpperCase();
      return `<button type="button" class="exploration-token token-${escapeHtml(token.kind)} ${token.actor_id === selectedExplorationActorId ? "selected" : ""} ${token.hidden ? "gm-hidden-token" : ""}" data-exploration-select="${escapeHtml(token.actor_id)}" ${canMove ? `draggable="true" data-exploration-drag="${escapeHtml(token.actor_id)}"` : ""} title="${escapeHtml(`${token.name}${token.hidden ? " · hidden from players" : ""}`)}"><span>${escapeHtml(initials)}</span></button>`;
    }).join("");
    const label = cell.state === "hidden" ? "Unexplored tile" : `${cell.terrain}${cell.blocked ? ", blocked" : ""}${legal ? `, ${Number(route.steps)} movement steps` : ""}`;
    return `<div class="exploration-cell state-${escapeHtml(cell.state)} terrain-${terrain} ${cell.blocked ? "blocked" : ""} ${legal ? "legal-move" : ""}" data-cell-key="${escapeHtml(key)}" ${legal ? `data-exploration-x="${Number(cell.x)}" data-exploration-y="${Number(cell.y)}" data-move-steps="${Number(route.steps)}"` : ""} aria-label="${escapeHtml(label)}" role="gridcell">${legal ? `<small class="move-cost">${Number(route.steps)}</small>` : ""}${pointMarkup}${tokenMarkup}</div>`;
  }).join("");
  board.setAttribute("role", "grid");
  if (!selectedPoint) {
    panel.innerHTML = '<div class="interaction-empty"><strong>Explore the scene</strong><span>Select a gold marker to inspect, talk, enter, shop, or uncover a clue.</span></div>';
  } else {
    const check = selectedPoint.check ? `<span class="interaction-check">${escapeHtml(selectedPoint.check.label)} · ${escapeHtml(selectedPoint.check.expression)}${selectedPoint.check.difficulty ? ` vs ${Number(selectedPoint.check.difficulty)}` : ""}</span>` : "";
    const nearbyActorId = selectedPoint.nearby_actor_ids?.includes(selectedExplorationActorId) ? selectedExplorationActorId : selectedPoint.nearby_actor_ids?.[0] || "";
    const status = selectedPoint.completed ? "Completed" : !selectedPoint.available ? "Locked by GM" : selectedPoint.can_interact ? "In range" : "Move closer";
    const playerAction = selectedPoint.completed && selectedPoint.once
      ? `<span class="interaction-result">${escapeHtml(selectedPoint.result || "This discovery is already part of the campaign.")}</span>`
      : `<button type="button" class="interaction-primary" data-exploration-point-interact="${escapeHtml(selectedPoint.id)}" data-actor-id="${escapeHtml(nearbyActorId)}" ${selectedPoint.can_interact ? "" : "disabled"}>${escapeHtml(selectedPoint.interaction || "Investigate")}</button>`;
    const gmActions = `<div class="interaction-gm-actions"><button type="button" data-exploration-point-visibility="${escapeHtml(selectedPoint.id)}" data-revealed="${selectedPoint.revealed ? "false" : "true"}">${selectedPoint.revealed ? "Hide from players" : "Reveal to players"}</button><button type="button" data-exploration-point-available="${escapeHtml(selectedPoint.id)}" data-available="${selectedPoint.available ? "false" : "true"}">${selectedPoint.available ? "Lock interaction" : "Unlock interaction"}</button>${selectedPoint.can_interact ? playerAction : ""}</div>`;
    panel.innerHTML = `<div class="interaction-heading"><span>${escapeHtml(String(selectedPoint.kind || "point").replaceAll("_", " "))}</span><strong>${escapeHtml(selectedPoint.label)}</strong><i class="interaction-status ${selectedPoint.can_interact ? "ready" : ""}">${escapeHtml(status)}</i></div><p>${escapeHtml(selectedPoint.description)}</p>${check}${selectedPoint.result ? `<blockquote>${escapeHtml(selectedPoint.result)}</blockquote>` : ""}${gm ? gmActions : playerAction}`;
  }
  const visibleCount = cells.filter((cell) => cell.state === "visible").length;
  const rememberedCount = cells.filter((cell) => cell.state === "explored").length;
  $("#exploration-help").textContent = gm
    ? `${exploration.fully_revealed ? "Players can see the whole floor." : "Player fog is active."} Select markers to reveal or lock them; drag any token along a glowing path.`
    : selected
      ? `${selected.name} selected · Speed ${Number(selected.speed || 1)} · ${visibleCount} visible · ${rememberedCount} remembered. Numbers show path cost.`
      : "The GM has not placed one of your tokens on this floor yet.";
}

function renderWorld() {
  const world = campaign.world || {};
  const locations = campaign.locations || [];
  const current = locations.find((entry) => entry.id === world.current_location_id) || {};
  const nextLocationId = String(campaign.active_scene?.metadata?.location_id || "");
  const nextLocation = locations.find((entry) => entry.id === nextLocationId);
  $("#world-location").textContent = current.name || "Unknown location";
  $("#world-weather").textContent = `${world.weather || "Clear"} · ${world.lighting || "Daylight"} · fog ${Number(world.fog || 0)}`;
  const progress = campaign.progression || {};
  const badges = progress.gym_badges || [];
  $("#world-progress").textContent = `${badges.length} badges · ${progress.league_rank || "Unranked"}`;
  const revealed = new Set(world.revealed_location_ids || []);
  const neighbors = (current.neighbors || []).map((id) => locations.find((entry) => entry.id === id)).filter((entry) => entry && revealed.has(entry.id));
  renderWorldMap(locations, current);
  const routeHint = nextLocation && nextLocation.id !== current.id ? `<p class="route-hint">Chapter destination: <strong>${escapeHtml(nextLocation.name)}</strong>. Follow connected routes.</p>` : "";
  $("#travel-options").innerHTML = routeHint + (neighbors.length ? neighbors.map((entry) => `<button type="button" data-travel="${escapeHtml(entry.id)}"><strong>Travel to ${escapeHtml(entry.name)}</strong><small>${Number(entry.travel_hours || 1)}h · danger ${Number(entry.danger || 0)}</small></button>`).join("") : '<span class="empty-action">No connected route.</span>');
  const trainer = ownedActors().find((entry) => entry.kind === "trainer");
  const inventory = trainer?.inventory || {};
  $("#inventory-list").innerHTML = `<strong>${escapeHtml(trainer?.name || "Trainer")} · ₽${Number(trainer?.currency || 0)}</strong><div>${Object.keys(inventory).length ? Object.entries(inventory).sort(([a], [b]) => a.localeCompare(b)).map(([name, count]) => `<span>${escapeHtml(name)} ×${Number(count)}</span>`).join("") : "Pack empty"}</div>`;

  const services = new Set(current.services || []);
  const actions = [];
  if (services.has("healing") || services.has("camp") || campaign.active_scene?.kind === "downtime") {
    actions.push('<button type="button" data-downtime="recover">Recover party</button>', '<button type="button" data-downtime="train">Train partner</button>');
  }
  if (services.has("crafting") || services.has("camp")) {
    (campaign.recipes || []).forEach((recipe) => actions.push(`<button type="button" data-craft="${escapeHtml(recipe.id)}">Craft ${escapeHtml(recipe.name)}<small>${Object.entries(recipe.ingredients || {}).map(([name, count]) => `${escapeHtml(name)} ×${Number(count)}`).join(", ")}</small></button>`));
  }
  (campaign.shops || []).filter((shop) => shop.location_id === current.id).forEach((shop) => {
    Object.entries(shop.stock || {}).filter(([, item]) => Number(item.quantity || 0) > 0).forEach(([name, item]) => actions.push(`<button type="button" data-shop="${escapeHtml(shop.id)}" data-item="${escapeHtml(name)}">Buy ${escapeHtml(name)}<small>₽${Number(item.price || 0)} · ${Number(item.quantity || 0)} left</small></button>`));
  });
  if (campaign.viewer?.role === "gm") {
    actions.push('<button type="button" data-environment="fog">Toggle fog</button>', '<button type="button" data-environment="lighting">Toggle lighting</button>');
  }
  $("#world-actions").innerHTML = actions.join("") || '<span class="empty-action">Explore or speak with someone nearby.</span>';
}

function renderNpcs() {
  const locationId = campaign.world?.current_location_id;
  const npcKinds = new Set(["npc", "rival", "gym_leader", "league", "champion"]);
  const npcs = (campaign.actors || []).filter((entry) => npcKinds.has(entry.kind) && entry.location_id === locationId);
  $("#npc-list").innerHTML = npcs.length ? npcs.map((entry) => `<button type="button" data-npc-pick="${escapeHtml(entry.id)}"><strong>${escapeHtml(entry.name)}</strong><small>${escapeHtml(entry.voice || entry.persona || entry.kind)}</small></button>`).join("") : '<span class="empty-action">No one is nearby right now.</span>';
  const select = $("#npc-talk-form select[name='npc_id']");
  const previous = select.value;
  select.innerHTML = npcs.map((entry) => `<option value="${escapeHtml(entry.id)}">${escapeHtml(entry.name)}</option>`).join("");
  if (npcs.some((entry) => entry.id === previous)) select.value = previous;
  $("#npc-talk-form").classList.toggle("hidden", !npcs.length || !can("npc.talk"));
  const visibleDialogue = (campaign.dialogue || []).filter((entry) => entry.participant_id === currentSeatId() || campaign.viewer?.role === "gm").slice(-8);
  $("#dialogue-feed").innerHTML = visibleDialogue.map((entry) => `<article><strong>${escapeHtml(entry.participant_name)} → ${escapeHtml(entry.npc_name)}</strong><p>${escapeHtml(entry.text)}</p>${entry.response ? `<blockquote>${escapeHtml(entry.response)}</blockquote>` : '<small>Thinking in character…</small>'}</article>`).join("");
}

function renderStory() {
  const activity = campaign.activity || [];
  const visibleTypes = new Set(["chat.post", "roll.check", "safety.pause", "safety.resume", "scene.activate", "spotlight.set", "clock.tick", "quest.objective", "battle.link", "starter.select", "location.travel", "exploration.point.interact", "craft.item", "shop.buy", "shop.sell", "downtime.activity", "npc.talk", "npc.reply", "participant.control", "battle.complete", "progression.award"]);
  const visible = activity.filter((entry) => visibleTypes.has(entry.type)).slice(-60);
  const feed = $("#story-feed");
  if (!visible.length) {
    feed.innerHTML = '<div class="story-empty">The world is holding its breath. Choose an action or let the party take a round.</div>';
  } else {
    feed.innerHTML = visible.map((entry) => {
      const detail = entry.detail || {};
      if (entry.type === "chat.post") {
        const mine = entry.actor_id === campaign.viewer?.id ? "mine" : "";
        const narration = detail.kind === "narration" ? "narration" : "";
        return `<article class="story-entry ${mine} ${narration}"><header><span>${escapeHtml(entry.actor_name)}</span><span>${escapeHtml(String(detail.kind || "in character").replaceAll("_", " "))}</span></header><p>${escapeHtml(detail.text)}</p></article>`;
      }
      if (entry.type === "roll.check") {
        return `<article class="story-entry roll-entry"><header><span>${escapeHtml(entry.actor_name)} tests ${escapeHtml(detail.label)}</span><span>${escapeHtml(detail.expression)}</span></header><p>${escapeHtml((detail.rolls || []).join(" + "))}${detail.modifier ? ` ${detail.modifier > 0 ? "+" : "−"} ${Math.abs(detail.modifier)}` : ""} = <strong>${detail.total}</strong></p></article>`;
      }
      if (entry.type === "npc.talk" || entry.type === "npc.reply") {
        const text = entry.type === "npc.talk" ? `${detail.participant_name || entry.actor_name}: ${detail.text || ""}` : `${detail.npc_name || "NPC"}: ${detail.response || ""}`;
        return `<article class="story-entry dialogue-story"><header><span>${escapeHtml(entry.type === "npc.talk" ? entry.actor_name : detail.npc_name || entry.actor_name)}</span><span>conversation</span></header><p>${escapeHtml(text)}</p></article>`;
      }
      if (entry.type === "exploration.point.interact") {
        const check = detail.check ? ` ${detail.check.label}: ${detail.check.total}${detail.difficulty ? ` vs ${detail.difficulty}` : ""}.` : "";
        return `<article class="story-entry discovery-story ${detail.success ? "success" : "setback"}"><header><span>${escapeHtml(detail.actor_name || entry.actor_name)} · ${escapeHtml(detail.interaction)}</span><span>${detail.success ? "discovery" : "setback"}</span></header><p>${escapeHtml(detail.result)}${escapeHtml(check)}</p></article>`;
      }
      const labels = {
        "safety.pause": "The adventure pauses so everyone can check in.",
        "safety.resume": "Everyone is ready. The adventure resumes.",
        "scene.activate": "The party travels into the next chapter.",
        "spotlight.set": "The spotlight shifts to another Trainer.",
        "clock.tick": "Danger moves one step closer.",
        "quest.objective": "A quest objective changes.",
        "battle.link": "A tactical encounter begins.",
        "starter.select": "A Trainer and starter choose one another.",
        "location.travel": "The party follows the route into a new place.",
        "craft.item": "Supplies become something useful.",
        "shop.buy": "The Trainer packs a new item.",
        "shop.sell": "The Trainer trades an item away.",
        "downtime.activity": "Time passes with purpose.",
        "participant.control": "A seat changes between human and AI control.",
        "battle.complete": "The battle changes the campaign permanently.",
        "progression.award": "The Trainer's League record advances.",
      };
      return `<article class="story-entry narration system-story"><header><span>${escapeHtml(entry.actor_name)}</span><span>world changes</span></header><p>${escapeHtml(labels[entry.type] || entry.type)}</p></article>`;
    }).join("");
    requestAnimationFrame(() => { feed.scrollTop = feed.scrollHeight; });
  }
  const lastRoll = [...activity].reverse().find((entry) => entry.type === "roll.check");
  $("#last-roll").innerHTML = lastRoll ? `<span>${escapeHtml(lastRoll.detail?.label)}</span><br><strong>${Number(lastRoll.detail?.total || 0)}</strong> <span>(${escapeHtml(lastRoll.detail?.expression)})</span>` : "No check rolled yet.";
}

function renderClocks() {
  $("#clock-list").innerHTML = (campaign.clocks || []).map((clock) => `<div class="clock-card"><div class="clock-head"><strong>${escapeHtml(clock.name)}</strong><span>${clock.filled}/${clock.segments}</span></div><div class="clock-segments">${Array.from({ length: clock.segments }, (_, index) => `<i class="${index < clock.filled ? "filled" : ""}"></i>`).join("")}</div>${can("clock.tick") ? `<button type="button" data-clock="${escapeHtml(clock.id)}" data-delta="1">Advance</button> <button type="button" data-clock="${escapeHtml(clock.id)}" data-delta="-1">Undo</button>` : ""}</div>`).join("") || '<div class="last-roll">The horizon is clear.</div>';
}

function renderQuests() {
  $("#quest-list").innerHTML = (campaign.quests || []).map((quest) => `<div class="quest-card"><strong>${escapeHtml(quest.name)}</strong>${(quest.objectives || []).map((objective) => `<label class="quest-objective ${objective.complete ? "quest-complete" : ""}"><input type="checkbox" data-quest="${escapeHtml(quest.id)}" data-objective="${escapeHtml(objective.id)}" ${objective.complete ? "checked" : ""} ${can("quest.objective") ? "" : "disabled"} />${escapeHtml(objective.text)}</label>`).join("")}<small>${escapeHtml(quest.reward || quest.status)}</small></div>`).join("") || '<div class="last-roll">No promises yet.</div>';
  const gateRequirements = campaign.scene_gate?.requirements || [];
  const incompleteGate = gateRequirements.find((entry) => !entry.complete);
  const objective = incompleteGate
    ? { quest: "Chapter goal", text: incompleteGate.label, complete: false }
    : gateRequirements.length
      ? { quest: "Chapter goal", text: "Complete — the road ahead is ready", complete: true }
      : (campaign.quests || []).flatMap((quest) => (quest.objectives || []).map((entry) => ({ ...entry, quest: quest.name }))).find((entry) => !entry.complete);
  $("#active-objective").classList.toggle("hidden", !objective);
  $("#active-objective").classList.toggle("objective-complete", !!objective?.complete);
  if (objective) $("#active-objective strong").textContent = `${objective.quest}: ${objective.text}`;
}

function renderFactions() {
  $("#faction-list").innerHTML = (campaign.factions || []).map((faction) => `<div class="faction-card"><strong>${escapeHtml(faction.name)}</strong><span class="faction-score">${Number(faction.score) > 0 ? "+" : ""}${Number(faction.score)}</span>${can("faction.adjust") ? `<span><button type="button" data-faction="${escapeHtml(faction.id)}" data-delta="-1">−</button> <button type="button" data-faction="${escapeHtml(faction.id)}" data-delta="1">+</button></span>` : ""}</div>`).join("") || '<div class="last-roll">No known factions.</div>';
}

function renderJournal() {
  $("#journal-list").innerHTML = (campaign.journal || []).slice(-6).reverse().map((note) => `<article class="journal-card"><strong>${escapeHtml(note.title)}</strong><small>${escapeHtml(note.visibility)} · ${escapeHtml(note.actor_name)}</small><p>${escapeHtml(note.text)}</p></article>`).join("") || '<div class="last-roll">Your field journal is empty.</div>';
}

function sceneChoicesFor(kind) {
  const common = {
    roleplay: [
      { title: "Reach out", hint: "Speak honestly and invite a response.", type: "chat.post", payload: { kind: "in_character", text: "I lower myself to the frightened Pokémon's level, offer an open hand, and ask what it needs from us." } },
      { title: "Read the room", hint: "Perception · 2d6+1", type: "roll.check", payload: { label: "Perception", expression: "2d6+1" } },
      { title: "Win their trust", hint: "Charm · 2d6+2", type: "roll.check", payload: { label: "Charm", expression: "2d6+2" } },
    ],
    exploration: [
      { title: "Follow the trail", hint: "Survival · 3d6+1", type: "roll.check", payload: { label: "Survival", expression: "3d6+1" } },
      { title: "Study the Pokémon", hint: "Pokémon Education · 2d6+2", type: "roll.check", payload: { label: "Pokemon Education", expression: "2d6+2" } },
      { title: "Protect the party", hint: "Describe your approach.", type: "chat.post", payload: { kind: "in_character", text: "I move to the front, keep the smallest Pokémon close, and guide everyone toward shelter without losing the trail." } },
    ],
    travel: [
      { title: "Scout ahead", hint: "Perception · 2d6+1", type: "roll.check", payload: { label: "Perception", expression: "2d6+1" } },
      { title: "Set the pace", hint: "Athletics · 3d6", type: "roll.check", payload: { label: "Athletics", expression: "3d6" } },
      { title: "Talk on the road", hint: "Share a character moment.", type: "chat.post", payload: { kind: "in_character", text: "As we travel, I ask the others what they hope waits for us at the end of this trail." } },
    ],
    combat: [
      { title: "Enter battle", hint: "Open the full tactical board.", type: "battle", payload: {} },
      { title: "Assess the enemy", hint: "Focus · 2d6+1", type: "roll.check", payload: { label: "Focus", expression: "2d6+1" } },
      { title: "Rally the team", hint: "Declare your battle intent.", type: "chat.post", payload: { kind: "in_character", text: "Stay together. Protect the objective first—we win this by trusting our partners." } },
    ],
    downtime: [
      { title: "Record the lesson", hint: "Add a shared field note.", type: "journal.add", payload: { title: "What Changed", text: "Tonight I write down what this journey taught me about my partner and the people beside us.", visibility: "table" } },
      { title: "Share the quiet", hint: "Speak with the party.", type: "chat.post", payload: { kind: "in_character", text: "I watch the lanterns with my partner and ask everyone where they want the trail to lead next." } },
      { title: "Read the future", hint: "Intuition · 2d6+2", type: "roll.check", payload: { label: "Intuition", expression: "2d6+2" } },
    ],
  };
  return common[kind] || common.roleplay;
}

function renderChoices() {
  const scene = campaign.active_scene;
  sceneChoiceActions = sceneChoicesFor(scene?.kind || "roleplay");
  $("#scene-choices").innerHTML = sceneChoiceActions.map((choice, index) => {
    const battleComplete = choice.type === "battle" && !!scene?.metadata?.battle_completed;
    const allowed = choice.type === "battle" ? canEnterBattle() && !battleComplete : can(choice.type);
    const title = battleComplete ? "Battle won" : choice.title;
    const hint = battleComplete ? "Victory is recorded—continue the adventure." : choice.hint;
    return `<button type="button" class="scene-choice" data-number="${index + 1}" data-choice="${index}" ${allowed ? "" : "disabled"}><strong>${escapeHtml(title)}</strong><small>${escapeHtml(hint)}</small></button>`;
  }).join("");
}

function renderContinue() {
  const button = $("#campaign-continue");
  const scene = campaign.active_scene;
  const scenes = campaign.scenes || [];
  const index = activeSceneIndex();
  const next = scenes[index + 1];
  const title = button.querySelector("span");
  const hint = button.querySelector("small");
  const gate = campaign.scene_gate || { ready: true, incomplete_labels: [] };
  const incomplete = gate.incomplete_labels?.[0] || "Finish the chapter goal";
  if (scene?.kind === "combat" && !scene.metadata?.battle_completed) {
    if (!atActiveSceneLocation()) {
      title.textContent = `Travel to ${scene.location || "the encounter"}`;
      hint.textContent = "Use the world map to reach the battle before it can begin";
      button.disabled = true;
    } else {
      title.textContent = "Enter the battle";
      hint.textContent = "Resolve this encounter to continue";
      button.disabled = !canEnterBattle();
    }
  } else if (!gate.ready) {
    title.textContent = incomplete;
    hint.textContent = "Complete the visible chapter goal before the story can advance";
    button.disabled = true;
  } else if (isAgentHost() && campaign.viewer?.role === "player" && campaign.has_next_scene) {
    title.textContent = "Ask the GM to continue";
    hint.textContent = "The AI GM will open exactly the next chapter and frame the scene";
    button.disabled = agentBusy;
  } else if (!campaign.has_next_scene) {
    title.textContent = "Adventure complete";
    hint.textContent = "The Prism Trail will remember your ending";
    button.disabled = true;
  } else if (next && campaign.viewer?.role === "gm") {
    title.textContent = next.published ? `Open ${next.title}` : "Reveal & open the next chapter";
    hint.textContent = next.published ? `${next.kind} · ${next.location || "next chapter"}` : "Players cannot see its title, location, or encounter yet";
    button.disabled = !can("scene.activate");
  } else if (campaign.viewer?.role !== "gm") {
    title.textContent = next?.available ? "The next chapter is ready" : "The GM holds the next chapter";
    hint.textContent = next?.available ? "Waiting for the GM to bring it on screen" : "Explore, roleplay, or finish the current objective";
    button.disabled = true;
  } else {
    title.textContent = "Adventure complete";
    hint.textContent = "The Prism Trail will remember your ending";
    button.disabled = true;
  }
}

async function handleChoice(choice) {
  if (!choice || agentBusy) return;
  if (choice.type === "battle") {
    $("#open-battle-link").click();
    return;
  }
  const button = $("#scene-choices [data-choice]:focus");
  if (button) button.disabled = true;
  try {
    await command(choice.type, choice.payload);
    toast(choice.type === "roll.check" ? "The dice changed the story." : "Your choice is now part of the campaign.");
  } catch (error) {
    reportError(error);
  }
}

async function continueAdventure() {
  const scene = campaign.active_scene;
  if (scene?.kind === "combat" && !scene.metadata?.battle_completed) {
    if (!canEnterBattle()) return;
    $("#open-battle-link").click();
    return;
  }
  if (!campaign.scene_gate?.ready) return;
  if (isAgentHost() && campaign.viewer?.role === "player") {
    if (!campaign.has_next_scene || agentBusy) return;
    setAgentBusy(true, "The AI Game Master is opening and framing the next chapter.");
    try {
      const result = await api(`/api/campaigns/${encodeURIComponent(campaignId)}/agents/advance`, {
        method: "POST",
        body: JSON.stringify({ model: $("#agent-gm-model").value }),
      });
      campaign = result.campaign;
      autoplayRoundsInScene = 0;
      autoplaySceneId = campaign.active_scene_id;
      renderCampaign();
      toast(`Chapter opened: ${campaign.active_scene?.title || "the next chapter"}`);
    } finally {
      setAgentBusy(false);
    }
    return;
  }
  const scenes = campaign.scenes || [];
  const next = scenes[activeSceneIndex() + 1];
  if (!next) return;
  if (!next.published || !next.available) {
    await command("scene.visibility", { scene_id: next.id, published: true, available: true });
  }
  await command("scene.activate", { scene_id: next.id });
  autoplayRoundsInScene = 0;
  autoplaySceneId = next.id;
  toast(`Chapter opened: ${next.title}`);
}

async function travelTo(locationId) {
  if (!locationId || mapTravelBusy) return;
  mapTravelBusy = true;
  renderWorld();
  try {
    await command("location.travel", { location_id: locationId });
    mapTravelBusy = false;
    renderWorld();
    const map = $("#campaign-world-map");
    map.classList.add("has-arrived");
    setTimeout(() => map.classList.remove("has-arrived"), 720);
    toast("The party arrived. The world changed with you.");
  } catch (error) {
    mapTravelBusy = false;
    renderWorld();
    throw error;
  }
}

async function moveExplorationToken(actorId, x, y) {
  if (explorationMoveBusy || !actorId) return;
  explorationMoveBusy = true;
  renderExploration();
  try {
    const event = await command("exploration.token.move", { actor_id: actorId, x: Number(x), y: Number(y) });
    selectedExplorationActorId = actorId;
    explorationMoveBusy = false;
    renderExploration();
    const board = $("#exploration-board");
    (event.detail?.path || []).slice(0, -1).forEach((step, index) => {
      const cell = board.querySelector(`[data-cell-key="${step.x},${step.y}"]`);
      if (cell) {
        cell.style.setProperty("--path-order", index);
        cell.classList.add("path-step");
      }
    });
    board.classList.add("has-moved");
    if (event.detail?.discovered_point_ids?.length) {
      toast(event.detail.discovered_point_ids.length === 1 ? "You discovered something hidden on the scene floor." : `You discovered ${event.detail.discovered_point_ids.length} hidden clues.`);
    }
    setTimeout(() => {
      board.classList.remove("has-moved");
      board.querySelectorAll(".path-step").forEach((cell) => cell.classList.remove("path-step"));
    }, 720);
  } finally {
    if (explorationMoveBusy) {
      explorationMoveBusy = false;
      renderExploration();
    }
  }
}

async function interactExplorationPoint(pointId, actorId) {
  if (!pointId || explorationMoveBusy) return;
  explorationMoveBusy = true;
  renderExploration();
  try {
    const event = await command("exploration.point.interact", { point_id: pointId, ...(actorId ? { actor_id: actorId } : {}) });
    selectedExplorationPointId = pointId;
    toast(event.detail?.result || "The scene answered your action.");
  } finally {
    explorationMoveBusy = false;
    renderExploration();
  }
}

function setAgentBusy(busy, detail = "Ollama is choosing a legal action.") {
  agentBusy = busy;
  $("#agent-thinking").classList.toggle("hidden", !busy);
  $("#agent-thinking-detail").textContent = detail;
  $("#agent-round").disabled = busy;
  $("#agent-step-gm").disabled = busy;
  document.querySelectorAll("[data-agent-step]").forEach((button) => { button.disabled = busy; });
  if (campaign) renderContinue();
}

function populateModelSelect(select, models, preferred) {
  const available = models.map((entry) => entry.name).filter(Boolean);
  if (!available.length) return;
  const current = preferred || select.value;
  select.innerHTML = available.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("");
  select.value = available.includes(current) ? current : available.includes(preferred) ? preferred : available[0];
}

async function loadAgentStatus() {
  const status = await api("/api/agents/ollama");
  $("#agent-party").classList.toggle("online", !!status.online);
  $("#agent-ollama-state").textContent = status.online ? `${status.models.length} models ready` : "Fallback mode ready";
  let stored = {};
  try { stored = JSON.parse(localStorage.getItem(AGENT_MODEL_KEY) || "{}"); } catch (_error) { stored = {}; }
  populateModelSelect($("#agent-gm-model"), status.models || [], stored.gm || status.recommended?.gm || "qwen2.5:3b");
  populateModelSelect($("#agent-player-model"), status.models || [], stored.player || status.recommended?.player || "qwen2.5:3b");
}

function rememberAgentModels() {
  localStorage.setItem(AGENT_MODEL_KEY, JSON.stringify({
    gm: $("#agent-gm-model").value,
    player: $("#agent-player-model").value,
  }));
}

function agentTurnSummary(turn) {
  const name = turn.agent?.name || "Agent";
  const action = String(turn.decision?.action || turn.event?.type || "acts").replaceAll(".", " ");
  return `${name}: ${action}${turn.source === "ollama" ? "" : " (fallback)"}`;
}

async function runAgentStep(agentId) {
  if (agentBusy || !agentId) return;
  const agent = (campaign.participants || []).find((entry) => entry.id === agentId) || {};
  setAgentBusy(true, `${agent.name || "The agent"} is reading the scene and choosing a legal action.`);
  try {
    const model = agent.role === "gm" ? $("#agent-gm-model").value : $("#agent-player-model").value;
    const result = await api(`/api/campaigns/${encodeURIComponent(campaignId)}/agents/step`, { method: "POST", body: JSON.stringify({ agent_id: agentId, model }) });
    campaign = result.campaign;
    renderCampaign();
    $("#agent-turn-log").textContent = agentTurnSummary(result);
    toast(`${result.agent.name} took a real campaign turn.`);
  } catch (error) {
    reportError(error);
  } finally {
    setAgentBusy(false);
  }
}

async function runAgentRound() {
  if (agentBusy) return;
  setAgentBusy(true, "The GM and every Trainer are taking one turn through Ollama.");
  try {
    const result = await api(`/api/campaigns/${encodeURIComponent(campaignId)}/agents/round`, {
      method: "POST",
      body: JSON.stringify({ gm_model: $("#agent-gm-model").value, player_model: $("#agent-player-model").value, include_gm: true }),
    });
    campaign = result.campaign;
    renderCampaign();
    $("#agent-turn-log").textContent = (result.turns || []).map(agentTurnSummary).join(" · ");
    autoplayRoundsInScene += 1;
    autoplaySceneId = campaign.active_scene_id;
    toast(`Party round complete: ${(result.turns || []).length} real turns.`);
  } catch (error) {
    autoplayEnabled = false;
    $("#agent-autoplay").setAttribute("aria-pressed", "false");
    reportError(error);
  } finally {
    setAgentBusy(false);
  }
}

async function autoplayLoop() {
  if (!autoplayEnabled || agentBusy) return;
  const beforeScene = campaign.active_scene_id;
  await runAgentRound();
  if (!autoplayEnabled) return;
  if (campaign.active_scene_id !== beforeScene) autoplayRoundsInScene = 0;
  if (autoplayRoundsInScene >= 2 && campaign.active_scene?.kind !== "combat" && (campaign.scenes || [])[activeSceneIndex() + 1]) {
    await continueAdventure();
  }
  if (autoplayEnabled) setTimeout(autoplayLoop, 1200);
}

$("#campaign-starter-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = $("#campaign-starter");
  button.disabled = true;
  button.classList.add("launching");
  try {
    const result = await api("/api/campaigns/starter", { method: "POST", body: JSON.stringify(formPayload(form)) });
    await enterCampaign(result.campaign.id, result.token);
    toast(result.campaign.viewer?.role === "player" ? "Your Trainer has entered the Prism Trail. Choose the partner who chooses you back." : "The Prism Trail is alive. Direct the first scene.");
  } catch (error) { reportError(error); }
  finally { button.disabled = false; button.classList.remove("launching"); }
});

$("#campaign-create-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const result = await api("/api/campaigns", { method: "POST", body: JSON.stringify(formPayload(event.currentTarget)) });
    await enterCampaign(result.campaign.id, result.token);
    toast("Campaign created.");
  } catch (error) { reportError(error); }
});

$("#campaign-join-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const values = formPayload(event.currentTarget);
    const result = await api(`/api/campaigns/${encodeURIComponent(values.campaign_id)}/join`, { method: "POST", body: JSON.stringify(values) });
    await enterCampaign(result.campaign.id, result.token);
    toast("You joined the adventure.");
  } catch (error) { reportError(error); }
});

$("#campaign-list").addEventListener("click", (event) => {
  const joinId = event.target.dataset.join;
  const resumeId = event.target.dataset.resume;
  if (joinId) { $("#join-campaign-id").value = joinId; document.querySelector(".gate-existing").open = true; $("#campaign-join-form input[name='invite_code']").focus(); }
  if (resumeId) {
    const stored = JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
    if (stored?.campaignId === resumeId) enterCampaign(resumeId, stored.participantToken).catch(reportError);
  }
});

$("#campaign-leave").addEventListener("click", forgetSession);
$("#campaign-guide-open").addEventListener("click", () => { const guide = $("#campaign-guide"); if (typeof guide.showModal === "function") guide.showModal(); else guide.setAttribute("open", ""); });
$("#scene-new-toggle").addEventListener("click", () => $("#scene-create-form").classList.toggle("hidden"));
$("#scene-create-form").addEventListener("submit", (event) => { event.preventDefault(); const form = event.currentTarget; command("scene.create", { ...formPayload(form), activate: true }).then(() => { form.reset(); form.classList.add("hidden"); }).catch(reportError); });
$("#chat-form").addEventListener("submit", (event) => { event.preventDefault(); const form = event.currentTarget; command("chat.post", formPayload(form)).then(() => { form.elements.text.value = ""; }).catch(reportError); });
$("#roll-form").addEventListener("submit", (event) => { event.preventDefault(); command("roll.check", formPayload(event.currentTarget)).catch(reportError); });
$("#clock-create-form").addEventListener("submit", (event) => { event.preventDefault(); const form = event.currentTarget; command("clock.create", formPayload(form)).then(() => form.reset()).catch(reportError); });
$("#quest-create-form").addEventListener("submit", (event) => { event.preventDefault(); const form = event.currentTarget; const values = formPayload(form); values.objectives = String(values.objectives || "").split(/\n+/).filter(Boolean); command("quest.create", values).then(() => form.reset()).catch(reportError); });
$("#faction-form").addEventListener("submit", (event) => { event.preventDefault(); const form = event.currentTarget; command("faction.adjust", formPayload(form)).then(() => form.reset()).catch(reportError); });
$("#time-form").addEventListener("submit", (event) => { event.preventDefault(); const form = event.currentTarget; command("time.set", formPayload(form)).then(() => form.reset()).catch(reportError); });
$("#journal-form").addEventListener("submit", (event) => { event.preventDefault(); const form = event.currentTarget; command("journal.add", formPayload(form)).then(() => form.reset()).catch(reportError); });
$("#safety-pause").addEventListener("click", () => command("safety.pause", {}).catch(reportError));
$("#safety-resume").addEventListener("click", () => command("safety.resume", {}).catch(reportError));
$("#spotlight-select").addEventListener("change", (event) => command("spotlight.set", { participant_id: event.target.value || null }).catch(reportError));
$("#scene-list").addEventListener("click", (event) => {
  const visibility = event.target.closest("[data-scene-visibility]");
  if (visibility) {
    command("scene.visibility", {
      scene_id: visibility.dataset.sceneVisibility,
      published: visibility.dataset.published === "true",
      available: visibility.dataset.available === "true",
    }).then(() => toast(visibility.dataset.published === "true" ? "Chapter visibility updated." : "Chapter returned behind the GM screen.")).catch(reportError);
    return;
  }
  const sceneId = event.target.closest("[data-scene]")?.dataset.scene;
  if (sceneId) command("scene.activate", { scene_id: sceneId }).then(() => toast("The table entered a new scene.")).catch(reportError);
});
$("#clock-list").addEventListener("click", (event) => { if (event.target.dataset.clock) command("clock.tick", { clock_id: event.target.dataset.clock, delta: Number(event.target.dataset.delta) }).catch(reportError); });
$("#quest-list").addEventListener("change", (event) => { if (event.target.dataset.quest) command("quest.objective", { quest_id: event.target.dataset.quest, objective_id: event.target.dataset.objective, complete: event.target.checked }).catch(reportError); });
$("#faction-list").addEventListener("click", (event) => { if (event.target.dataset.faction) command("faction.adjust", { faction_id: event.target.dataset.faction, delta: Number(event.target.dataset.delta) }).catch(reportError); });
$("#scene-choices").addEventListener("click", (event) => { const index = Number(event.target.closest("[data-choice]")?.dataset.choice); if (Number.isInteger(index)) handleChoice(sceneChoiceActions[index]); });
$("#campaign-continue").addEventListener("click", () => continueAdventure().catch(reportError));
$("#acting-seat").addEventListener("change", (event) => { activeSeatId = event.target.value; renderCampaign(); });
$("#participant-list").addEventListener("click", (event) => {
  const agentId = event.target.closest("[data-agent-step]")?.dataset.agentStep;
  if (agentId) { runAgentStep(agentId); return; }
  const control = event.target.closest("[data-seat-control]");
  if (control) {
    command("participant.control", { participant_id: control.dataset.seatControl, controller: control.dataset.controller })
      .then(() => {
        if (control.dataset.controller === "human") activeSeatId = control.dataset.seatControl;
        else if (activeSeatId === control.dataset.seatControl) activeSeatId = campaign.viewer?.id || "";
        renderCampaign();
        toast(`Seat is now ${control.dataset.controller}-controlled.`);
      })
      .catch(reportError);
  }
});
$("#starter-choice-list").addEventListener("click", (event) => {
  const species = event.target.closest("[data-starter]")?.dataset.starter;
  if (species) command("starter.select", { species }).then((eventResult) => toast(`${eventResult.detail.name || species} joined your persistent party and battle roster.`)).catch(reportError);
});
$("#travel-options").addEventListener("click", (event) => {
  const locationId = event.target.closest("[data-travel]")?.dataset.travel;
  if (locationId) travelTo(locationId).catch(reportError);
});
$("#campaign-world-map").addEventListener("click", (event) => {
  const locationId = event.target.closest("[data-travel-map]")?.dataset.travelMap;
  if (locationId) travelTo(locationId).catch(reportError);
});
$("#campaign-world-map").addEventListener("dragstart", (event) => {
  if (!event.target.closest("[data-party-token]") || mapTravelBusy) return;
  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData("text/autoptu-party", campaign.world?.current_location_id || "party");
  $("#campaign-world-map").classList.add("is-dragging");
});
$("#campaign-world-map").addEventListener("dragover", (event) => {
  const target = event.target.closest("[data-travel-map]");
  if (!target || !event.dataTransfer.types.includes("text/autoptu-party")) return;
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  target.classList.add("is-drop-target");
});
$("#campaign-world-map").addEventListener("dragleave", (event) => event.target.closest("[data-travel-map]")?.classList.remove("is-drop-target"));
$("#campaign-world-map").addEventListener("dragend", () => {
  $("#campaign-world-map").classList.remove("is-dragging");
  document.querySelectorAll(".map-node.is-drop-target").forEach((node) => node.classList.remove("is-drop-target"));
});
$("#campaign-world-map").addEventListener("drop", (event) => {
  const target = event.target.closest("[data-travel-map]");
  if (!target) return;
  event.preventDefault();
  $("#campaign-world-map").classList.remove("is-dragging");
  target.classList.remove("is-drop-target");
  travelTo(target.dataset.travelMap).catch(reportError);
});
$("#exploration-token-picker").addEventListener("click", (event) => {
  const visibility = event.target.closest("[data-exploration-token-visibility]");
  if (visibility) {
    command("exploration.token.visibility", {
      actor_id: visibility.dataset.explorationTokenVisibility,
      revealed: visibility.dataset.revealed === "true",
    }).then(() => toast(visibility.dataset.revealed === "true" ? "Token revealed to players." : "Token returned behind the fog.")).catch(reportError);
    return;
  }
  const actorId = event.target.closest("[data-exploration-select]")?.dataset.explorationSelect;
  if (actorId) {
    selectedExplorationActorId = actorId;
    renderExploration();
  }
});
$("#exploration-gm-controls").addEventListener("click", (event) => {
  const mode = event.target.closest("[data-exploration-visibility]")?.dataset.explorationVisibility;
  if (!mode) return;
  command("exploration.visibility", { mode })
    .then(() => toast(mode === "reveal_all" ? "The whole scene floor is visible." : "Unseen areas returned to fog."))
    .catch(reportError);
});
$("#exploration-board").addEventListener("click", (event) => {
  const point = event.target.closest("[data-exploration-point-select]");
  if (point) {
    selectedExplorationPointId = point.dataset.explorationPointSelect;
    renderExploration();
    return;
  }
  const token = event.target.closest("[data-exploration-select]");
  if (token) {
    selectedExplorationActorId = token.dataset.explorationSelect;
    renderExploration();
    return;
  }
  const cell = event.target.closest("[data-exploration-x]");
  if (cell && selectedExplorationActorId) {
    moveExplorationToken(selectedExplorationActorId, cell.dataset.explorationX, cell.dataset.explorationY).catch(reportError);
  }
});
$("#exploration-interaction-panel").addEventListener("click", (event) => {
  const interact = event.target.closest("[data-exploration-point-interact]");
  if (interact) {
    interactExplorationPoint(interact.dataset.explorationPointInteract, interact.dataset.actorId).catch(reportError);
    return;
  }
  const visibility = event.target.closest("[data-exploration-point-visibility]");
  if (visibility) {
    command("exploration.point.visibility", {
      point_id: visibility.dataset.explorationPointVisibility,
      revealed: visibility.dataset.revealed === "true",
    }).then(() => toast(visibility.dataset.revealed === "true" ? "Point of interest revealed." : "Point of interest hidden.")).catch(reportError);
    return;
  }
  const availability = event.target.closest("[data-exploration-point-available]");
  if (availability) {
    command("exploration.point.update", {
      point_id: availability.dataset.explorationPointAvailable,
      available: availability.dataset.available === "true",
    }).then(() => toast(availability.dataset.available === "true" ? "Interaction unlocked." : "Interaction locked until the GM opens it.")).catch(reportError);
  }
});
$("#exploration-board").addEventListener("dragstart", (event) => {
  const token = event.target.closest("[data-exploration-drag]");
  if (!token || explorationMoveBusy) return;
  selectedExplorationActorId = token.dataset.explorationDrag;
  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData("text/autoptu-exploration", selectedExplorationActorId);
  $("#exploration-board").classList.add("is-dragging");
});
$("#exploration-board").addEventListener("dragover", (event) => {
  const cell = event.target.closest("[data-exploration-x]");
  if (!cell || !event.dataTransfer.types.includes("text/autoptu-exploration")) return;
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  cell.classList.add("is-drop-target");
});
$("#exploration-board").addEventListener("dragleave", (event) => event.target.closest("[data-exploration-x]")?.classList.remove("is-drop-target"));
$("#exploration-board").addEventListener("dragend", () => {
  $("#exploration-board").classList.remove("is-dragging");
  document.querySelectorAll(".exploration-cell.is-drop-target").forEach((cell) => cell.classList.remove("is-drop-target"));
});
$("#exploration-board").addEventListener("drop", (event) => {
  const cell = event.target.closest("[data-exploration-x]");
  if (!cell) return;
  event.preventDefault();
  const actorId = event.dataTransfer.getData("text/autoptu-exploration") || selectedExplorationActorId;
  $("#exploration-board").classList.remove("is-dragging");
  cell.classList.remove("is-drop-target");
  moveExplorationToken(actorId, cell.dataset.explorationX, cell.dataset.explorationY).catch(reportError);
});
$("#world-actions").addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  if (button.dataset.downtime) {
    const partner = ownedActors().find((entry) => entry.kind === "pokemon");
    command("downtime.activity", { activity: button.dataset.downtime, ...(partner ? { actor_id: partner.id } : {}) }).catch(reportError);
  } else if (button.dataset.craft) {
    command("craft.item", { recipe_id: button.dataset.craft }).then(() => toast("Crafting complete.")).catch(reportError);
  } else if (button.dataset.shop) {
    command("shop.buy", { shop_id: button.dataset.shop, item: button.dataset.item, quantity: 1 }).then(() => toast(`${button.dataset.item} added to the pack.`)).catch(reportError);
  } else if (button.dataset.environment === "fog") {
    command("world.environment", { fog: Number(campaign.world?.fog || 0) > 0 ? 0 : 3 }).catch(reportError);
  } else if (button.dataset.environment === "lighting") {
    command("world.environment", { lighting: campaign.world?.lighting === "Dark" ? "Daylight" : "Dark" }).catch(reportError);
  }
});
$("#npc-list").addEventListener("click", (event) => {
  const npcId = event.target.closest("[data-npc-pick]")?.dataset.npcPick;
  if (!npcId) return;
  $("#npc-talk-form select[name='npc_id']").value = npcId;
  $("#npc-talk-form textarea").focus();
});
$("#npc-talk-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const exchange = await command("npc.talk", formPayload(form));
    form.elements.text.value = "";
    const result = await api(`/api/campaigns/${encodeURIComponent(campaignId)}/agents/npc/reply`, { method: "POST", body: JSON.stringify({ dialogue_id: exchange.detail.id, model: $("#agent-gm-model").value }) });
    campaign = result.campaign;
    renderCampaign();
    toast(`${result.npc.name} answered in character.`);
  } catch (error) { reportError(error); }
});
$("#agent-step-gm").addEventListener("click", () => { const gm = (campaign.participants || []).find((entry) => entry.is_agent && entry.role === "gm"); if (gm) runAgentStep(gm.id); });
$("#agent-round").addEventListener("click", () => runAgentRound());
$("#agent-gm-model").addEventListener("change", rememberAgentModels);
$("#agent-player-model").addEventListener("change", rememberAgentModels);
$("#agent-autoplay").addEventListener("click", () => { autoplayEnabled = !autoplayEnabled; $("#agent-autoplay").setAttribute("aria-pressed", String(autoplayEnabled)); $("#agent-autoplay").textContent = autoplayEnabled ? "Stop autoplay" : "Autoplay"; if (autoplayEnabled) autoplayLoop(); });
$("#open-battle-link").addEventListener("click", async (event) => {
  if (!canEnterBattle()) return;
  event.preventDefault();
  try {
    await api("/api/battle/new", { method: "POST", body: JSON.stringify({ campaign_id: campaignId }) });
    location.href = "/";
  } catch (error) { reportError(error); }
});

document.addEventListener("keydown", (event) => {
  if (event.target && ["INPUT", "SELECT", "TEXTAREA"].includes(event.target.tagName)) return;
  if (event.key >= "1" && event.key <= "3") {
    const choice = sceneChoiceActions[Number(event.key) - 1];
    if (choice) { event.preventDefault(); handleChoice(choice); }
  } else if (event.key === " ") {
    event.preventDefault();
    runAgentRound();
  }
});

(async function initialize() {
  try {
    await loadCampaigns();
    const stored = JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
    if (stored?.campaignId && stored?.participantToken) await enterCampaign(stored.campaignId, stored.participantToken);
  } catch (error) {
    forgetSession();
    reportError(error);
  }
})();
