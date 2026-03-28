const gridEl = document.getElementById("grid");
const gridWrapEl = gridEl?.parentElement;
const combatantListEl = document.getElementById("combatant-list");
const detailsEl = document.getElementById("combatant-details");
const trainerDetailsEl = document.getElementById("trainer-details");
const moveListEl = document.getElementById("move-list");
const logEl = document.getElementById("log");
const partyBarEl = document.getElementById("party-bar");
const turnOrderBarEl = document.getElementById("turn-order-bar");
const roundInfoEl = document.getElementById("round-info");
const terrainInfoEl = document.getElementById("terrain-info");
const weatherInfoEl = document.getElementById("weather-info");
const mapSeedEl = document.getElementById("map-seed");
const sidebarRoundInfoEl = document.getElementById("sidebar-round-info");
const sidebarTerrainInfoEl = document.getElementById("sidebar-terrain-info");
const sidebarWeatherInfoEl = document.getElementById("sidebar-weather-info");
const jsStatusEl = document.getElementById("js-status");
const startButton = document.getElementById("start-battle");
const endTurnButton = document.getElementById("end-turn");
const downloadSpritesButton = document.getElementById("download-sprites");
const spriteStatusEl = document.getElementById("sprite-status");
const modeSelect = document.getElementById("mode-select");
const teamSizeInput = document.getElementById("team-size");
const sideCountInput = document.getElementById("side-count");
const circleIntervalInput = document.getElementById("circle-interval");
const activeSlotsInput = document.getElementById("active-slots");
const minLevelInput = document.getElementById("min-level");
const maxLevelInput = document.getElementById("max-level");
const aiStepButton = document.getElementById("ai-step");
const aiAutoButton = document.getElementById("ai-auto");
const cinematicAutoToggle = document.getElementById("cinematic-auto");
const cinematicProfileSelect = document.getElementById("cinematic-profile");
const cinematicSpeedSelect = document.getElementById("cinematic-speed");
const cinematicExportButton = document.getElementById("cinematic-export");
const cinematicPerfEl = document.getElementById("cinematic-perf");
const aiModelSelect = document.getElementById("ai-model-select");
const aiModelRefreshButton = document.getElementById("ai-model-refresh");
const aiModelMathEl = document.getElementById("ai-model-math");
const autoIntervalInput = document.getElementById("auto-interval");
const undoButton = document.getElementById("undo-action");
const zoomInButton = document.getElementById("zoom-in");
const zoomOutButton = document.getElementById("zoom-out");
const zoomFitButton = document.getElementById("zoom-fit");
const zoomResetButton = document.getElementById("zoom-reset");
const centerCurrentButton = document.getElementById("center-current");
const centerSelectedButton = document.getElementById("center-selected");
const moveTooltip = document.getElementById("move-tooltip");
const logFilterActions = document.getElementById("log-actions");
const logFilterDamage = document.getElementById("log-damage");
const logFilterStatus = document.getElementById("log-status");
const logFilterPhase = document.getElementById("log-phase");
const logAutoScrollToggle = document.getElementById("log-autoscroll");
const logCompactToggle = document.getElementById("log-compact");
const logExportButton = document.getElementById("log-export");
const logClearButton = document.getElementById("log-clear");
const selectedTileInfoEl = document.getElementById("selected-tile-info");
const topbarEl = document.querySelector(".topbar");
const speedButtons = Array.from(document.querySelectorAll(".speed-btn"));
const promptOverlay = document.getElementById("prompt-overlay");
const promptListEl = document.getElementById("prompt-list");
const promptResolveButton = document.getElementById("prompt-resolve");
const hideFaintedToggle = document.getElementById("hide-fainted");
const autoCriesToggle = document.getElementById("auto-cries");
const stepByStepStartToggle = document.getElementById("step-by-step-start");
const useTrainerInput = document.getElementById("use-trainer");
const loadTrainerButton = document.getElementById("load-trainer");
const usefulChartsButton = document.getElementById("open-useful-charts");
const importTrainerButton = document.getElementById("import-trainer");
const clearTrainerButton = document.getElementById("clear-trainer");
const importRosterCsvButton = document.getElementById("import-roster-csv");
const exportRosterCsvButton = document.getElementById("export-roster-csv");
const clearRosterCsvButton = document.getElementById("clear-roster-csv");
const exportRosterMirrorInput = document.getElementById("export-roster-mirror");
const autoUseCreatorRosterInput = document.getElementById("auto-use-creator-roster");
const csvStrictModeInput = document.getElementById("csv-strict-mode");
const rosterCsvStatusEl = document.getElementById("roster-csv-status");
const sideNameEditorEl = document.getElementById("side-name-editor");
const deploymentEditorEl = document.getElementById("deployment-editor");
const infoTabs = Array.from(document.querySelectorAll(".info-tab"));
const infoTabPanels = Array.from(document.querySelectorAll(".info-tab-panel"));
const statusTabsEl = document.querySelector(".status-tabs");
let statusTabs = Array.from(document.querySelectorAll(".status-tab"));
const charStepButtons = Array.from(document.querySelectorAll(".char-step-btn"));
const charContentEl = document.getElementById("char-content");
const charMiniSummaryEl = document.getElementById("char-mini-summary");
const charUndoBtn = document.getElementById("char-undo");
const charRedoBtn = document.getElementById("char-redo");
const charSnapshotBtn = document.getElementById("char-snapshot");
const charSnapshotsOpenBtn = document.getElementById("char-snapshots-open");
const charSnapshotsPanel = document.getElementById("char-snapshots-panel");
const charGuidedToggleBtn = document.getElementById("char-guided-toggle");
const charSaveLocalBtn = document.getElementById("char-save-local");
const charLoadLocalBtn = document.getElementById("char-load-local");
const runtimeErrorEl = document.createElement("div");
runtimeErrorEl.id = "runtime-errors";
document.body.appendChild(runtimeErrorEl);
window.addEventListener("mouseup", () => {
  trapperPaintActive = false;
});
let aiDiagnosticsEl = null;
let _builderRerenderQueued = false;

let combatantTeamFilter = "all";
let battleRosterCsvText = "";
let battleRosterCsvMeta = null;
let sideNameOverrides = {};
let sideNameEditorSignature = "";
let deploymentOverrides = {};
let itemChoiceOverrides = {};
let abilityChoiceOverrides = {};
let usefulChartsDataCache = null;
let usefulChartsDataPromise = null;

const TEAM_PRESETS = {
  player: {
    primary: "#37c998",
    secondary: "#8ff4ca",
    track: "rgba(55, 201, 152, 0.32)",
    warning: "#f2bb57",
    danger: "#f06b6b",
  },
  foe: {
    primary: "#df6767",
    secondary: "#ffadad",
    track: "rgba(223, 103, 103, 0.32)",
    warning: "#efb45b",
    danger: "#f06b6b",
  },
  neutral: {
    primary: "#65a9ff",
    secondary: "#a8cdff",
    track: "rgba(101, 169, 255, 0.3)",
    warning: "#f0be63",
    danger: "#f06b6b",
  },
};

const TEAM_COLOR_WHEEL = [
  { primary: "#5ecbcb", secondary: "#9ef3f3" },
  { primary: "#a78bfa", secondary: "#c9bbff" },
  { primary: "#f59e0b", secondary: "#ffd080" },
  { primary: "#22d3ee", secondary: "#9cefff" },
  { primary: "#a3e635", secondary: "#cef58d" },
  { primary: "#fb7185", secondary: "#ffc0ce" },
];

const TYPE_VFX = {
  normal: { primary: "#d4c7a5", secondary: "#f2e7cb", glyph: "â—‡" },
  fighting: { primary: "#d86767", secondary: "#ffb1ad", glyph: "âœ¦" },
  flying: { primary: "#88b4ff", secondary: "#d4e4ff", glyph: "ðŸœ" },
  poison: { primary: "#aa78dd", secondary: "#dabdff", glyph: "â˜£" },
  ground: { primary: "#b88653", secondary: "#e0bb89", glyph: "â–¦" },
  rock: { primary: "#9f8f6f", secondary: "#d9cfb7", glyph: "â—ˆ" },
  bug: { primary: "#84c661", secondary: "#bff4a2", glyph: "âœ¤" },
  ghost: { primary: "#8f8adb", secondary: "#c7c2ff", glyph: "â˜¾" },
  steel: { primary: "#95a8bf", secondary: "#d9e6f7", glyph: "â¬¡" },
  fire: { primary: "#ff8a5a", secondary: "#ffd0a8", glyph: "âœ¹" },
  water: { primary: "#5db1ff", secondary: "#b3dcff", glyph: "âœ§" },
  grass: { primary: "#5ccf89", secondary: "#a7f0c4", glyph: "â‹" },
  electric: { primary: "#ffe061", secondary: "#fff4bf", glyph: "âš¡" },
  psychic: { primary: "#ff86bc", secondary: "#ffd0e7", glyph: "â—Œ" },
  ice: { primary: "#8fe7ff", secondary: "#d7f8ff", glyph: "â†" },
  dragon: { primary: "#7d9eff", secondary: "#bbcbff", glyph: "ðŸ‰" },
  dark: { primary: "#8d87a3", secondary: "#cbc7dd", glyph: "âœ¥" },
  fairy: { primary: "#f5a6d1", secondary: "#ffe0f2", glyph: "âœ¿" },
};

const TYPE_ANIM_STYLE = {
  normal: "impact",
  fighting: "impact",
  flying: "wind",
  poison: "toxic",
  ground: "quake",
  rock: "shard",
  bug: "vine",
  ghost: "shadow",
  steel: "shard",
  fire: "flame",
  water: "wave",
  grass: "vine",
  electric: "spark",
  psychic: "psy",
  ice: "frost",
  dragon: "draco",
  dark: "shadow",
  fairy: "gleam",
};

const NOISY_NAMED_MOVE_SHEETS = new Set([
  "tackle",
  "dragon pulse",
  "confusion",
  "confuse ray",
  "take down",
  "pound",
]);

const SAFE_NAMED_MOVE_SHEETS = new Set([
  "flamethrower",
  "fire blast",
  "hydro pump",
  "surf",
  "thunderbolt",
  "ice beam",
  "shadow ball",
  "solar beam",
]);

const EXACT_MOVE_STYLE_OVERRIDES = {
  tackle: "impact",
  "quick attack": "impact",
  "feint attack": "impact",
  "take down": "impact",
  pound: "impact",
  slam: "impact",
  stomp: "impact",
  strength: "impact",
  headbutt: "impact",
  "high jump kick": "impact",
  "hi jump kick": "impact",
  "jump kick": "impact",
  "double kick": "impact",
  "triple kick": "impact",
  "steel wing": "slash",
  "wing attack": "slash",
  slash: "slash",
  "night slash": "slash",
  "air slash": "wind",
  confusion: "mind",
  "confuse ray": "mind",
  "dragon pulse": "draco",
  "dark pulse": "shadow",
  "water pulse": "wave",
};

const MOVE_SFX_EXACT = {
  tackle: { impact: "hit.ogg" },
  "dragon pulse": { launch: "PRSFX- Dragon Pulse.wav", impact: "PRSFX- Dragon Pulse.wav" },
  "steel wing": { launch: "PRSFX- Steel Wing.wav", impact: "PRSFX- Steel Wing.wav" },
  "high jump kick": { launch: "PRSFX- Hi Jump Kick1.wav", impact: "PRSFX- Hi Jump Kick1.wav" },
  "hi jump kick": { launch: "PRSFX- Hi Jump Kick1.wav", impact: "PRSFX- Hi Jump Kick1.wav" },
  thunderbolt: { launch: "PRSFX- Thunderbolt1.wav", impact: "PRSFX- Thunderbolt1.wav" },
  "water pulse": { launch: "PRSFX- Water Pulse.wav", impact: "PRSFX- Water Pulse.wav" },
  "shadow ball": { launch: "PRSFX- Shadow Ball1.wav", impact: "PRSFX- Shadow Ball1.wav" },
  psychic: { launch: "PRSFX- Psychic.wav", impact: "PRSFX- Psychic.wav" },
  "fire blast": { launch: "PRSFX- Fire Blast.wav", impact: "PRSFX- Fire Blast.wav" },
  "ice beam": { launch: "PRSFX- Ice Beam.wav", impact: "PRSFX- Ice Beam.wav" },
  "solar beam": { launch: "PRSFX- Solar Beam1.wav", impact: "PRSFX- Solar Beam1.wav" },
};

const MOVE_SFX_STYLE = {
  impact: { launch: "hit.ogg", impact: "hit.ogg" },
  slash: { launch: "Slash.ogg", impact: "Slash.ogg" },
  wind: { launch: "gust.ogg", impact: "gust.ogg" },
  quake: { launch: "Earth1.ogg", impact: "Earth1.ogg" },
  shadow: { launch: "Darkness2.ogg", impact: "Darkness2.ogg" },
  toxic: { launch: "Poison.ogg", impact: "Poison.ogg" },
  wave: { launch: "Water3.ogg", impact: "Water3.ogg" },
  frost: { launch: "Ice2.ogg", impact: "Ice2.ogg" },
  flame: { launch: "Fire3.ogg", impact: "Fire3.ogg" },
  spark: { launch: "PRSFX- Thunderbolt1.wav", impact: "PRSFX- Thunderbolt1.wav" },
  draco: { launch: "PRSFX- Dragon Pulse.wav", impact: "PRSFX- Dragon Pulse.wav" },
  psy: { launch: "PRSFX- Psychic.wav", impact: "PRSFX- Psychic.wav" },
  mind: { launch: "Confuse.ogg", impact: "Confuse.ogg" },
  gleam: { launch: "PRSFX- Psychic.wav", impact: "PRSFX- Psychic.wav" },
};

const LOG_CATEGORY_TAG = {
  actions: "ACT",
  damage: "DMG",
  status: "STS",
  ability: "ABL",
  hazard: "HZD",
  item: "ITM",
  phase: "PHS",
  other: "LOG",
};

const STATUS_KEYWORD_HELP = {
  burned: "Burned: ongoing damage each round from burn ticks.",
  poisoned: "Poisoned: ongoing poison damage each round.",
  badlypoisoned: "Badly Poisoned: poison damage that escalates over time.",
  paralyzed: "Paralyzed: may lose actions from paralysis checks.",
  sleep: "Sleep: cannot act normally until cured or awakened by effects.",
  frozen: "Frozen: cannot act until thawed or cured.",
  confused: "Confused: may hurt itself instead of acting.",
  flinch: "Flinch/Flinched: loses action for the current turn window.",
  flinched: "Flinch/Flinched: loses action for the current turn window.",
  trapped: "Trapped: movement options are restricted.",
  stuck: "Stuck: movement options are restricted.",
  infatuated: "Infatuated: can lose actions due to infatuation checks.",
  slowed: "Slowed: temporary movement/speed penalty from effect source.",
  vulnerable: "Vulnerable: takes increased punishment from relevant follow-up effects.",
  blinded: "Blinded: reduced battlefield awareness and targeting reliability.",
  suppressed: "Suppressed: abilities/passives may be disabled temporarily.",
  enraged: "Enraged: forced/aggressive behavior from the source effect.",
  drowsy: "Drowsy: precursor state that can convert into sleep.",
  cursed: "Cursed: ongoing harmful curse effect from source move/ability.",
  powdered: "Powdered: affected by powder-based trigger penalties.",
  grounded: "Grounded: treated as grounded for terrain and move interactions.",
  leechseed: "Leech Seed: periodic HP drain from seeded target.",
  aquaring: "Aqua Ring: periodic HP recovery each round.",
  vortex: "Vortex: ongoing trap/chip damage from vortex effects.",
  bleed: "Bleed: ongoing bleed damage over time.",
};

const STATUS_LOG_KEYWORDS = [
  "Badly Poisoned",
  "Poisoned",
  "Burned",
  "Paralyzed",
  "Sleep",
  "Frozen",
  "Confused",
  "Flinched",
  "Flinch",
  "Trapped",
  "Stuck",
  "Infatuated",
  "Slowed",
  "Vulnerable",
  "Blinded",
  "Suppressed",
  "Enraged",
  "Drowsy",
  "Cursed",
  "Powdered",
  "Grounded",
  "Leech Seed",
  "Aqua Ring",
  "Vortex",
  "Bleed",
];

const HAZARD_GLYPHS = {
  spikes: "S",
  toxic_spikes: "T",
  sticky_web: "W",
  stealth_rock: "R",
  stealth_rock_fairy: "F",
  fire_hazards: "F",
  dreepy_token: "D",
};

const TRAP_GLYPHS = {
  trap: "!",
  dust_trap: "D",
  tangle_trap: "T",
  slick_trap: "S",
  abrasion_trap: "A",
};

const GRID_CELL_SIZE = 74;
const GRID_GAP = 4;
const MIN_GRID_SCALE = 0.2;
const MAX_GRID_SCALE = 2.0;
const SPRITE_RETRY_MS = 30000;
const ABILITY_BLINK_MS = 520;
const TOOLTIP_HIDE_DELAY_MS = 140;

let state = null;
let aiModelsCache = null;
let selectedId = null;
let _speciesCatalogCache = null;
let _learnsetMoveNameSetCache = null;
let _moveCatalogCache = null;
let _abilityCatalogCache = null;
let _pokeEdgeCatalogCache = null;

function _mergeNamedEntries(sources, mergeFn = null) {
  const merged = new Map();
  (sources || []).forEach((list) => {
    (Array.isArray(list) ? list : []).forEach((raw) => {
      const name = String(raw?.name || "").trim();
      if (!name) return;
      const key = _normalizeSearchText(name);
      if (!key) return;
      const prev = merged.get(key);
      if (!prev) {
        merged.set(key, { ...raw, name });
        return;
      }
      merged.set(key, typeof mergeFn === "function" ? mergeFn(prev, raw) : { ...prev, ...raw, name });
    });
  });
  return Array.from(merged.values());
}

function _mergeStringLists(...lists) {
  const out = [];
  const seen = new Set();
  lists.forEach((list) => {
    (Array.isArray(list) ? list : []).forEach((value) => {
      const text = String(value || "").trim();
      const key = _normalizeSearchText(text);
      if (!text || !key || seen.has(key)) return;
      seen.add(key);
      out.push(text);
    });
  });
  return out;
}
let armedMove = null;
let armedTileAction = null;
let frozenDomainDraftTiles = [];
let trapperDraftTiles = [];
let psionicOverloadBarrierTiles = [];
let trapperPaintActive = false;
let tooltipMode = null;
let tooltipAnchor = null;
let tooltipHideTimer = null;
let tooltipPinned = false;
let selectedTileKey = null;
let promptAnswers = {};
let autoTimer = null;
let resizeFitTimer = null;
let autoSpriteStarted = false;
let lastBattlePayload = null;
let battleResultModal = null;
let lastBattleResultToken = "";
let gimmickState = {
  mega_evolve: false,
  dynamax: false,
  z_move: false,
  teracrystal: false,
  tera_type: "",
};
let itemTargetId = null;
let lastItemActorId = null;
let gridScale = 1.18;
let gridOffset = { x: 0, y: 0 };
let panState = null;
let viewManuallyAdjusted = false;
let lastGridSize = null;
let lastProcessedLogSize = null;
let lastProcessedLogToken = "";
let logClearOffset = 0;
let fxQueue = Promise.resolve();
let spriteMissUntil = new Map();
let lastSpriteCompleted = 0;
let lastSpritePollAt = 0;
let suppressGridClickUntil = 0;
let lastTileMeta = new Map();
let gridCellByKey = new Map();
let lastTurnActorId = null;
let lastCinematicActorId = null;
let lastCinematicPanAt = 0;
let pendingAnimationJobs = 0;
const MAX_ANIMATION_QUEUE = 40;
const MAX_ANIMATION_EVENT_SLICE = 96;
let cinematicCameraBusy = false;
let cinematicCameraJob = Promise.resolve();
let aiStepInFlight = false;
let cinematicPhaseActive = false;
let cinematicShotIndex = 0;
let cinematicReplayCache = [];
let cinematicFrameMsAvg = 16.7;
let lastRenderedPositions = new Map();
let characterData = null;
let masterData = null;
let learnsetData = null;
let moveRecordMap = null;
let characterStep = "profile";
const _navStack = [];
const _navForward = [];
let charHistory = [];
let charRedoHistory = [];
let lastCharacterSnapshot = "";
let snapshotStore = [];
let trainerProfile = null;
let trainerProfileRaw = null;
let _activeSortables = [];

function clearArmedTileAction() {
  armedTileAction = null;
  frozenDomainDraftTiles = [];
  trapperDraftTiles = [];
  psionicOverloadBarrierTiles = [];
  trapperPaintActive = false;
}

function frozenDomainDraftKeySet() {
  return new Set((frozenDomainDraftTiles || []).map((coord) => `${coord[0]},${coord[1]}`));
}

function trapperDraftKeySet() {
  return new Set((trapperDraftTiles || []).map((coord) => `${coord[0]},${coord[1]}`));
}

function trapperTilesAreContiguous(rawTiles) {
  const tiles = Array.isArray(rawTiles) ? rawTiles : [];
  if (!tiles.length) return true;
  const keySet = new Set(tiles.map((coord) => `${coord[0]},${coord[1]}`));
  const queue = [tiles[0]];
  const seen = new Set();
  while (queue.length) {
    const [x, y] = queue.shift();
    const key = `${x},${y}`;
    if (seen.has(key) || !keySet.has(key)) continue;
    seen.add(key);
    [
      [x + 1, y],
      [x - 1, y],
      [x, y + 1],
      [x, y - 1],
    ].forEach((next) => {
      const nextKey = `${next[0]},${next[1]}`;
      if (!seen.has(nextKey) && keySet.has(nextKey)) {
        queue.push(next);
      }
    });
  }
  return seen.size === keySet.size;
}

function trapperDraftCanAdd(coord) {
  if (!Array.isArray(coord) || coord.length < 2) return false;
  if (!trapperDraftTiles.length) return true;
  const [x, y] = coord;
  return trapperDraftTiles.some(([tx, ty]) => Math.abs(tx - x) + Math.abs(ty - y) === 1);
}

function frozenDomainDraftCanAdd(coord) {
  if (!Array.isArray(coord) || coord.length < 2) return false;
  if (!frozenDomainDraftTiles.length) return true;
  const [x, y] = coord;
  return frozenDomainDraftTiles.some(([tx, ty]) => Math.abs(tx - x) + Math.abs(ty - y) === 1);
}

function psionicOverloadBarrierKeySet() {
  return new Set((psionicOverloadBarrierTiles || []).map((coord) => `${coord[0]},${coord[1]}`));
}

let characterState = {
  profile: {
    name: "",
    played_by: "",
    age: "",
    sex: "",
    height: "",
    weight: "",
    concept: "",
    background: "",
    region: "",
    level: 1,
    money: "",
  },
  stats: {
    hp: 10,
    atk: 5,
    def: 5,
    spatk: 5,
    spdef: 5,
    spd: 5,
  },
  class_ids: [],
  class_id: "",
  features: new Set(),
  edges: new Set(),
  feature_order: [],
  edge_order: [],
  skills: {},
  skill_budget: null,
  skill_budget_auto: false,
  skill_edge_non_skill_count: 0,
  skill_background: {
    adept: "",
    novice: "",
    pathetic: [],
  },
  skill_background_edit: false,
  advancement_choices: {
    5: "stats",
    10: "stats",
    20: "stats",
    30: "stats",
    40: "stats",
  },
  step_by_step: false,
  allow_warnings: false,
  guided_mode: false,
  content_scope: "official",
  feature_search: "",
  edge_search: "",
  poke_edge_search: "",
  feature_tag_filter: "",
  feature_class_filter: "",
  edge_class_filter: "",
  feature_status_filter: "all",
  edge_status_filter: "all",
  feature_group_mode: "none",
  edge_group_mode: "none",
  feature_filter_available: true,
  feature_filter_close: true,
  feature_filter_unavailable: true,
  feature_filter_blocked: true,
  edge_filter_available: true,
  edge_filter_close: true,
  edge_filter_unavailable: true,
  edge_filter_blocked: true,
  poke_edge_filter_available: true,
  poke_edge_filter_close: true,
  poke_edge_filter_unavailable: true,
  poke_edge_filter_blocked: true,
  override_prereqs: false,
  feature_slots_override: {},
  list_density: "comfortable",
  planner_collapsed: false,
  planner_targets: [],
  planner_targets_expanded: false,
  training_type: "",
  extras: [],
  pokemon_builds: [],
  inventory: {
    key_items: [],
    pokemon_items: [],
  },
  extras_search: "",
  inventory_search: "",
  extras_catalog_search: "",
  extras_catalog_scope: "class",
  inventory_catalog_search: "",
  inventory_catalog_category: "",
  inventory_catalog_type: "",
  inventory_catalog_kind: "all",
  pokemon_team_search: "",
  pokemon_team_limit: 6,
  pokemon_team_auto_level: false,
  pokemon_team_auto_level_explicit: false,
  pokemon_team_autofill: true,
};
const pokeApiMoveMetaCache = new Map();
const pokeApiAbilityMetaCache = new Map();
const pokeApiItemMetaCache = new Map();
const pokeApiTypeIconCache = new Map();
const pokeApiCryCache = new Map();
const pokeApiPending = new Map();
const cryAudio = new Audio();
let itemFxAudioCtx = null;
let moveFxAudioCtx = null;
const moveFxAudioCache = new Map();
const isBattleUI = !!gridEl && !!startButton;

if (jsStatusEl) {
  jsStatusEl.textContent = "JS: running";
}

function showRuntimeError(message) {
  if (!runtimeErrorEl) return;
  const entry = document.createElement("div");
  entry.className = "runtime-error-entry";
  entry.textContent = message;
  runtimeErrorEl.appendChild(entry);
}

function notifyUI(type, message, timeout = 3200) {
  const text = String(message || "").trim();
  if (!text) return;
  if (window.DSUI && typeof window.DSUI.notify === "function") {
    window.DSUI.notify(type, text, timeout);
    return;
  }
  if (window.DSUI && typeof window.DSUI.toast === "function") {
    window.DSUI.toast(text, timeout);
  }
}

window.addEventListener("error", (event) => {
  if (!event?.message) return;
  showRuntimeError(`JS Error: ${event.message}`);
});

window.addEventListener("unhandledrejection", (event) => {
  const reason = event?.reason?.message || String(event?.reason || "Unknown promise rejection");
  showRuntimeError(`Promise Error: ${reason}`);
});

if (moveTooltip && moveTooltip.parentElement !== document.body) {
  document.body.appendChild(moveTooltip);
}

if (moveTooltip) {
  moveTooltip.addEventListener("mouseenter", () => {
    tooltipPinned = true;
    clearTooltipHideTimer();
  });
  moveTooltip.addEventListener("mouseleave", () => {
    tooltipPinned = false;
    scheduleTooltipHide();
  });
  moveTooltip.addEventListener(
    "wheel",
    (event) => {
      if (!moveTooltip) return;
      if (moveTooltip.scrollHeight <= moveTooltip.clientHeight) return;
      event.preventDefault();
      event.stopPropagation();
      moveTooltip.scrollTop += event.deltaY;
    },
    { passive: false }
  );
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("\r", "").replaceAll("\n", "&#10;");
}

const ALPHA_INDEX = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

function alphaKey(value) {
  const first = String(value || "").trim().charAt(0).toUpperCase();
  if (!first) return "#";
  if (first >= "A" && first <= "Z") return first;
  return "#";
}

function createAlphaIndex() {
  const wrap = document.createElement("div");
  wrap.className = "alpha-index";
  const buttons = new Map();
  let currentMap = new Map();
  const makeButton = (label) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "alpha-index-button";
    btn.textContent = label;
    btn.addEventListener("click", () => {
      const target = currentMap.get(label);
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
    buttons.set(label, btn);
    wrap.appendChild(btn);
  };
  ALPHA_INDEX.forEach((letter) => makeButton(letter));
  makeButton("#");
  return {
    element: wrap,
    update: (map) => {
      currentMap = map || new Map();
      buttons.forEach((btn, key) => {
        btn.disabled = !currentMap.has(key);
      });
    },
  };
}

function applyDensityClass(target) {
  if (!target) return;
  target.classList.toggle("density-compact", characterState.list_density === "compact");
}

function createDensityToggle(onChange) {
  const wrap = document.createElement("div");
  wrap.className = "char-density-toggle";
  const label = document.createElement("div");
  label.className = "char-density-label";
  label.textContent = "Density";
  wrap.appendChild(label);
  const compact = document.createElement("button");
  compact.type = "button";
  compact.textContent = "Compact";
  const comfortable = document.createElement("button");
  comfortable.type = "button";
  comfortable.textContent = "Comfortable";
  const sync = () => {
    compact.classList.toggle("active", characterState.list_density === "compact");
    comfortable.classList.toggle("active", characterState.list_density !== "compact");
  };
  compact.addEventListener("click", () => {
    characterState.list_density = "compact";
    saveCharacterToStorage();
    if (typeof onChange === "function") onChange();
  });
  comfortable.addEventListener("click", () => {
    characterState.list_density = "comfortable";
    saveCharacterToStorage();
    if (typeof onChange === "function") onChange();
  });
  wrap.appendChild(compact);
  wrap.appendChild(comfortable);
  sync();
  return wrap;
}

function createStatusLegend() {
  const legend = document.createElement("div");
  legend.className = "char-legend";
  const items = [
    ["available", "Available"],
    ["close", "Close"],
    ["unavailable", "Unavailable"],
    ["blocked", "Locked"],
  ];
  items.forEach(([id, label]) => {
    const item = document.createElement("div");
    item.className = `char-legend-item ${id}`;
    item.textContent = label;
    legend.appendChild(item);
  });
  return legend;
}

function createSelectedPanel(label, items, onRemove) {
  const panel = document.createElement("div");
  panel.className = "char-selected-panel";
  const title = document.createElement("div");
  title.className = "char-selected-title";
  title.textContent = `${label} (${items.length})`;
  panel.appendChild(title);
  const list = document.createElement("div");
  list.className = "char-selected-list";
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "char-selected-empty";
    empty.textContent = "None selected yet.";
    list.appendChild(empty);
  } else {
    items.forEach((entry) => {
      const pill = document.createElement("button");
      pill.type = "button";
      pill.className = "char-selected-pill";
      pill.textContent = entry;
      pill.title = "Click to remove";
      pill.addEventListener("click", () => onRemove(entry));
      list.appendChild(pill);
    });
  }
  panel.appendChild(list);
  return panel;
}

function _ensureOrder(order, selectedSet) {
  const next = order.filter((name) => selectedSet.has(name));
  selectedSet.forEach((name) => {
    if (!next.includes(name)) next.push(name);
  });
  return next;
}

function _addToOrder(order, name) {
  if (!order.includes(name)) order.push(name);
}

function _removeFromOrder(order, name) {
  const idx = order.indexOf(name);
  if (idx >= 0) order.splice(idx, 1);
}

function _featureRankByName(name) {
  const node = (characterData?.nodes || []).find((n) => n.type === "feature" && n.name === name);
  return Number(node?.rank || 1);
}

function _edgeByName(name) {
  return (characterData?.edges_catalog || []).find((edge) => edge.name === name);
}

function _featureByName(name) {
  return (
    (characterData?.nodes || []).find((node) => node.type === "feature" && node.name === name) ||
    (characterData?.features || []).find((entry) => entry.name === name)
  );
}

function _destroySortables() {
  _activeSortables.forEach((inst) => {
    try {
      inst.destroy();
    } catch {
      // ignore
    }
  });
  _activeSortables = [];
}

function _registerSortable(instance) {
  if (instance) _activeSortables.push(instance);
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (char === "\"") {
      if (inQuotes && text[i + 1] === "\"") {
        field += "\"";
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }
    if (char === "," && !inQuotes) {
      row.push(field);
      field = "";
      continue;
    }
    if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && text[i + 1] === "\n") i += 1;
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
      continue;
    }
    field += char;
  }
  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

function stringifyCsv(rows) {
  const escape = (value) => {
    const str = String(value ?? "");
    if (/[\",\n\r]/.test(str)) {
      return `"${str.replaceAll("\"", "\"\"")}"`;
    }
    return str;
  };
  return rows.map((row) => row.map(escape).join(",")).join("\r\n");
}

function _normalizeRosterSide(value) {
  const raw = String(value || "").trim().toLowerCase();
  if (["player", "players", "ally", "allies", "you", "p1", "left"].includes(raw)) return "player";
  if (["foe", "foes", "enemy", "enemies", "opponent", "opponents", "ai", "p2", "right"].includes(raw)) return "foe";
  return raw.replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

function _defaultSideName(side) {
  const normalized = _normalizeRosterSide(side) || "player";
  if (normalized === "player") return "Player";
  if (normalized === "foe") return "Foe";
  return formatTeamLabel(normalized);
}

function _normalizedSideNameOverrides(value) {
  const out = {};
  if (!value || typeof value !== "object") return out;
  Object.entries(value).forEach(([key, entry]) => {
    const side = _normalizeRosterSide(key);
    const name = String(entry || "").trim();
    if (!side || !name) return;
    out[side] = name;
  });
  return out;
}

function _availableSideLabels() {
  const labels = [];
  const seen = new Set();
  const push = (value) => {
    const side = _normalizeRosterSide(value);
    if (!side || seen.has(side)) return;
    seen.add(side);
    labels.push(side);
  };
  const preview = _currentRosterPreview();
  preview.forEach((entry) => push(entry.side));
  const liveCombatants = Array.isArray(state?.combatants) ? state.combatants : [];
  liveCombatants.forEach((combatant) => push(teamKeyForCombatant(combatant)));
  const trainerSides = Array.isArray(state?.trainers) ? state.trainers : [];
  trainerSides.forEach((trainer) => push(trainer?.team || trainer?.id));
  if (!labels.length) {
    push("player");
    push("foe");
    const requested = Math.max(2, Number(sideCountInput?.value || 2));
    for (let index = 3; index <= requested; index += 1) push(`side_${index}`);
  }
  return labels;
}

function renderSideNameEditor() {
  if (!sideNameEditorEl) return;
  const labels = _availableSideLabels();
  const signature = JSON.stringify({
    labels,
    values: labels.map((side) => [side, String(sideNameOverrides[side] || "")]),
  });
  const active = document.activeElement;
  const editingInside = !!(active && sideNameEditorEl.contains(active));
  if (editingInside && sideNameEditorSignature === signature) {
    return;
  }
  if (!editingInside && sideNameEditorSignature === signature) {
    return;
  }
  sideNameEditorSignature = signature;
  sideNameEditorEl.innerHTML = "";
  const wrap = document.createElement("div");
  wrap.className = "char-stack";
  const note = document.createElement("div");
  note.className = "char-feature-meta";
  note.textContent = "These names are used in battle labels and the winner message.";
  wrap.appendChild(note);
  labels.forEach((side) => {
    const row = document.createElement("label");
    row.className = "field";
    row.style.display = "flex";
    row.style.flexDirection = "column";
    const caption = document.createElement("span");
    caption.textContent = formatTeamLabel(side);
    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = _defaultSideName(side);
    input.value = String(sideNameOverrides[side] || "");
    input.addEventListener("input", () => {
      const value = String(input.value || "");
      if (value.trim()) sideNameOverrides[side] = value;
      else delete sideNameOverrides[side];
      sideNameEditorSignature = "";
    });
    input.addEventListener("change", () => {
      const value = String(input.value || "").trim();
      if (value) sideNameOverrides[side] = value;
      else delete sideNameOverrides[side];
      sideNameEditorSignature = "";
      saveSettings();
      syncStatusTabs();
      renderCombatants();
      renderPartyBar();
    });
    input.addEventListener("blur", () => {
      sideNameEditorSignature = "";
      renderSideNameEditor();
    });
    row.appendChild(caption);
    row.appendChild(input);
    wrap.appendChild(row);
  });
  sideNameEditorEl.appendChild(wrap);
}

function _normalizeStatChoice(value) {
  const raw = String(value || "").trim().toLowerCase();
  const mapping = {
    attack: "atk",
    atk: "atk",
    defense: "def",
    def: "def",
    "special attack": "spatk",
    spatk: "spatk",
    "special defense": "spdef",
    spdef: "spdef",
    speed: "spd",
    spd: "spd",
    accuracy: "accuracy",
    evasion: "evasion",
  };
  return mapping[raw] || "";
}

function _normalizeDeploymentPayload() {
  const out = {};
  Object.entries(deploymentOverrides || {}).forEach(([side, entry]) => {
    const active = Array.isArray(entry?.active)
      ? entry.active.map((value) => String(value || "").trim()).filter(Boolean)
      : [];
    const startPositions = Array.isArray(entry?.start_positions)
      ? entry.start_positions
          .map((coord) => (Array.isArray(coord) && coord.length >= 2 ? [Number(coord[0]), Number(coord[1])] : null))
          .filter((coord) => coord && Number.isFinite(coord[0]) && Number.isFinite(coord[1]))
      : [];
    if (!active.length && !startPositions.length) return;
    out[side] = {};
    if (active.length) out[side].active = active;
    if (startPositions.length) out[side].start_positions = startPositions;
  });
  return out;
}

function _normalizeItemChoicePayload() {
  const out = {};
  Object.entries(itemChoiceOverrides || {}).forEach(([side, mons]) => {
    if (!mons || typeof mons !== "object") return;
    const sideOut = {};
    Object.entries(mons).forEach(([species, items]) => {
      if (!items || typeof items !== "object") return;
      const monOut = {};
      Object.entries(items).forEach(([itemName, choice]) => {
        if (!choice || typeof choice !== "object") return;
        const chosenStat = _normalizeStatChoice(choice.chosen_stat);
        const chosenStats = Array.isArray(choice.chosen_stats)
          ? choice.chosen_stats.map((value) => _normalizeStatChoice(value)).filter(Boolean)
          : [];
        if (!chosenStat && !chosenStats.length) return;
        monOut[itemName] = {};
        if (chosenStat) monOut[itemName].chosen_stat = chosenStat;
        if (chosenStats.length) monOut[itemName].chosen_stats = chosenStats;
      });
      if (Object.keys(monOut).length) sideOut[species] = monOut;
    });
    if (Object.keys(sideOut).length) out[side] = sideOut;
  });
  return out;
}

function _normalizeAbilityChoicePayload() {
  const out = {};
  Object.entries(abilityChoiceOverrides || {}).forEach(([side, mons]) => {
    if (!mons || typeof mons !== "object") return;
    const sideOut = {};
    Object.entries(mons).forEach(([species, abilities]) => {
      if (!abilities || typeof abilities !== "object") return;
      const monOut = {};
      Object.entries(abilities).forEach(([abilityName, choice]) => {
        if (!choice || typeof choice !== "object") return;
        const entry = {};
        if (choice.color_theory_roll !== undefined && choice.color_theory_roll !== null && choice.color_theory_roll !== "") {
          entry.color_theory_roll = Number(choice.color_theory_roll);
        }
        if (choice.color_theory_color) entry.color_theory_color = String(choice.color_theory_color).trim();
        if (choice.serpents_mark_roll !== undefined && choice.serpents_mark_roll !== null && choice.serpents_mark_roll !== "") {
          entry.serpents_mark_roll = Number(choice.serpents_mark_roll);
        }
        if (choice.serpents_mark_pattern) entry.serpents_mark_pattern = String(choice.serpents_mark_pattern).trim();
        if (choice.fabulous_trim_style) entry.fabulous_trim_style = String(choice.fabulous_trim_style).trim();
        if (choice.giver_choice_roll !== undefined && choice.giver_choice_roll !== null && choice.giver_choice_roll !== "") {
          entry.giver_choice_roll = Number(choice.giver_choice_roll);
        }
        if (!Object.keys(entry).length) return;
        monOut[abilityName] = entry;
      });
      if (Object.keys(monOut).length) sideOut[species] = monOut;
    });
    if (Object.keys(sideOut).length) out[side] = sideOut;
  });
  return out;
}

function renderDeploymentEditor() {
  if (!deploymentEditorEl) return;
  const preview = _currentRosterPreview();
  deploymentEditorEl.innerHTML = "";
  if (!preview.length) {
    deploymentEditorEl.textContent = "Load or stage a roster CSV to configure starters, throw tiles, item choices, and visible ability variants.";
    return;
  }
  const activeSlots = Math.max(1, Number(activeSlotsInput?.value || 1));
  const groups = new Map();
  preview.forEach((entry) => {
    const side = _normalizeRosterSide(entry.side) || "player";
    if (!groups.has(side)) groups.set(side, []);
    groups.get(side).push(entry);
  });
  const wrap = document.createElement("div");
  wrap.className = "deployment-editor";
  const note = document.createElement("div");
  note.className = "char-feature-meta";
  note.textContent = "Use the highlighted battlefield tile or enter x,y manually. Throw range is validated on start. Item and ability choices are applied when the encounter begins.";
  wrap.appendChild(note);
  groups.forEach((entries, side) => {
    const card = document.createElement("div");
    card.className = "deployment-card";
    const title = document.createElement("div");
    title.className = "deployment-title";
    title.textContent = `${formatTeamLabel(side)} Deployment`;
    card.appendChild(title);
    for (let index = 0; index < activeSlots; index += 1) {
      const row = document.createElement("div");
      row.className = "deployment-row";
      const picker = document.createElement("select");
      const empty = document.createElement("option");
      empty.value = "";
      empty.textContent = `Starter ${index + 1}`;
      picker.appendChild(empty);
      entries.forEach((entry) => {
        const option = document.createElement("option");
        option.value = entry.species;
        option.textContent = `${entry.slot}. ${entry.species}`;
        picker.appendChild(option);
      });
      picker.value = String(deploymentOverrides?.[side]?.active?.[index] || "");
      picker.addEventListener("change", () => {
        deploymentOverrides[side] = deploymentOverrides[side] || {};
        deploymentOverrides[side].active = deploymentOverrides[side].active || [];
        deploymentOverrides[side].active[index] = String(picker.value || "");
        saveSettings();
      });
      const tileInput = document.createElement("input");
      tileInput.type = "text";
      tileInput.placeholder = "x,y";
      const coord = deploymentOverrides?.[side]?.start_positions?.[index];
      tileInput.value = Array.isArray(coord) ? `${coord[0]},${coord[1]}` : "";
      tileInput.addEventListener("change", () => {
        deploymentOverrides[side] = deploymentOverrides[side] || {};
        deploymentOverrides[side].start_positions = deploymentOverrides[side].start_positions || [];
        const match = String(tileInput.value || "").match(/^\s*(-?\d+)\s*,\s*(-?\d+)\s*$/);
        if (match) deploymentOverrides[side].start_positions[index] = [Number(match[1]), Number(match[2])];
        else deploymentOverrides[side].start_positions[index] = [];
        saveSettings();
      });
      const tileButton = document.createElement("button");
      tileButton.type = "button";
      tileButton.textContent = "Use Tile";
      tileButton.addEventListener("click", () => {
        if (!selectedTileKey) {
          notifyUI("warn", "Select a battlefield tile first.", 1800);
          return;
        }
        const [x, y] = selectedTileKey.split(",").map((value) => Number(value));
        deploymentOverrides[side] = deploymentOverrides[side] || {};
        deploymentOverrides[side].start_positions = deploymentOverrides[side].start_positions || [];
        deploymentOverrides[side].start_positions[index] = [x, y];
        tileInput.value = `${x},${y}`;
        saveSettings();
      });
      row.appendChild(picker);
      row.appendChild(tileInput);
      row.appendChild(tileButton);
      card.appendChild(row);
    }
    entries.forEach((entry) => {
      const itemName = String(entry.item || "").trim();
      if (!itemName) return;
      const normalizedItem = itemName.toLowerCase();
      if (!["stat boosters", "eviolite"].includes(normalizedItem)) return;
      const itemRow = document.createElement("div");
      itemRow.className = "deployment-item-row";
      const label = document.createElement("div");
      label.className = "deployment-item-label";
      label.textContent = `${entry.species}: ${itemName}`;
      itemRow.appendChild(label);
      const stats = [
        ["atk", "Attack"],
        ["def", "Defense"],
        ["spatk", "Special Attack"],
        ["spdef", "Special Defense"],
        ["spd", "Speed"],
        ["accuracy", "Accuracy"],
        ["evasion", "Evasion"],
      ];
      if (normalizedItem === "stat boosters") {
        const select = document.createElement("select");
        const empty = document.createElement("option");
        empty.value = "";
        empty.textContent = "Choose stat";
        select.appendChild(empty);
        stats.forEach(([value, text]) => {
          const option = document.createElement("option");
          option.value = value;
          option.textContent = text;
          select.appendChild(option);
        });
        select.value = String(itemChoiceOverrides?.[side]?.[entry.species]?.[itemName]?.chosen_stat || "");
        select.addEventListener("change", () => {
          itemChoiceOverrides[side] = itemChoiceOverrides[side] || {};
          itemChoiceOverrides[side][entry.species] = itemChoiceOverrides[side][entry.species] || {};
          itemChoiceOverrides[side][entry.species][itemName] = { chosen_stat: select.value };
          saveSettings();
        });
        itemRow.appendChild(select);
      } else if (normalizedItem === "eviolite") {
        for (let slot = 0; slot < 2; slot += 1) {
          const select = document.createElement("select");
          const empty = document.createElement("option");
          empty.value = "";
          empty.textContent = slot === 0 ? "Stat A" : "Stat B";
          select.appendChild(empty);
          stats
            .filter(([value]) => !["accuracy", "evasion"].includes(value))
            .forEach(([value, text]) => {
              const option = document.createElement("option");
              option.value = value;
              option.textContent = text;
              select.appendChild(option);
            });
          select.value = String(itemChoiceOverrides?.[side]?.[entry.species]?.[itemName]?.chosen_stats?.[slot] || "");
          select.addEventListener("change", () => {
            itemChoiceOverrides[side] = itemChoiceOverrides[side] || {};
            itemChoiceOverrides[side][entry.species] = itemChoiceOverrides[side][entry.species] || {};
            const current = itemChoiceOverrides[side][entry.species][itemName] || {};
            const chosenStats = Array.isArray(current.chosen_stats) ? current.chosen_stats.slice(0, 2) : ["", ""];
            chosenStats[slot] = select.value;
            itemChoiceOverrides[side][entry.species][itemName] = { chosen_stats: chosenStats };
            saveSettings();
          });
          itemRow.appendChild(select);
        }
      }
      card.appendChild(itemRow);
    });
    entries.forEach((entry) => {
      const abilityName = String(entry.ability || "").trim();
      if (!abilityName) return;
      const normalizedAbility = _normalizeAbilityChoiceKey(abilityName);
      if (![
        _normalizeAbilityChoiceKey("color theory"),
        _normalizeAbilityChoiceKey("serpent's mark"),
        _normalizeAbilityChoiceKey("serpent's mark [errata]"),
        _normalizeAbilityChoiceKey("fabulous trim"),
        _normalizeAbilityChoiceKey("giver"),
      ].includes(normalizedAbility)) return;
      const abilityRow = document.createElement("div");
      abilityRow.className = "deployment-item-row";
      const label = document.createElement("div");
      label.className = "deployment-item-label";
      label.textContent = `${entry.species}: ${abilityName}`;
      abilityRow.appendChild(label);
      if (normalizedAbility === _normalizeAbilityChoiceKey("color theory")) {
        const colors = ["Red", "Red-Orange", "Orange", "Yellow-Orange", "Yellow", "Yellow-Green", "Green", "Blue-Green", "Blue", "Blue-Violet", "Violet", "Red-Violet"];
        const select = document.createElement("select");
        colors.forEach((color, index) => {
          const option = document.createElement("option");
          option.value = color;
          option.textContent = `${index + 1}. ${color}`;
          select.appendChild(option);
        });
        const currentColor = String(abilityChoiceOverrides?.[side]?.[entry.species]?.[abilityName]?.color_theory_color || "");
        select.value = currentColor || "Red";
        select.addEventListener("change", () => {
          abilityChoiceOverrides[side] = abilityChoiceOverrides[side] || {};
          abilityChoiceOverrides[side][entry.species] = abilityChoiceOverrides[side][entry.species] || {};
          abilityChoiceOverrides[side][entry.species][abilityName] = {
            color_theory_roll: colors.indexOf(select.value) + 1,
            color_theory_color: select.value,
          };
          saveSettings();
        });
        const rollButton = document.createElement("button");
        rollButton.type = "button";
        rollButton.textContent = "Roll";
        rollButton.addEventListener("click", () => {
          const roll = 1 + Math.floor(Math.random() * colors.length);
          select.value = colors[roll - 1];
          select.dispatchEvent(new Event("change"));
        });
        if (!currentColor) {
          abilityChoiceOverrides[side] = abilityChoiceOverrides[side] || {};
          abilityChoiceOverrides[side][entry.species] = abilityChoiceOverrides[side][entry.species] || {};
          abilityChoiceOverrides[side][entry.species][abilityName] = { color_theory_roll: 1, color_theory_color: "Red" };
        }
        abilityRow.appendChild(select);
        abilityRow.appendChild(rollButton);
      } else if (
        normalizedAbility === _normalizeAbilityChoiceKey("serpent's mark")
        || normalizedAbility === _normalizeAbilityChoiceKey("serpent's mark [errata]")
      ) {
        const patterns = ["Attack Pattern", "Crush Pattern", "Fear Pattern", "Life Pattern", "Speed Pattern", "Stealth Pattern"];
        const select = document.createElement("select");
        patterns.forEach((pattern, index) => {
          const option = document.createElement("option");
          option.value = pattern;
          option.textContent = `${index + 1}. ${pattern}`;
          select.appendChild(option);
        });
        const currentPattern = String(abilityChoiceOverrides?.[side]?.[entry.species]?.[abilityName]?.serpents_mark_pattern || "");
        select.value = currentPattern || "Attack Pattern";
        select.addEventListener("change", () => {
          abilityChoiceOverrides[side] = abilityChoiceOverrides[side] || {};
          abilityChoiceOverrides[side][entry.species] = abilityChoiceOverrides[side][entry.species] || {};
          abilityChoiceOverrides[side][entry.species][abilityName] = {
            serpents_mark_roll: patterns.indexOf(select.value) + 1,
            serpents_mark_pattern: select.value,
          };
          saveSettings();
        });
        const rollButton = document.createElement("button");
        rollButton.type = "button";
        rollButton.textContent = "Roll";
        rollButton.addEventListener("click", () => {
          const roll = 1 + Math.floor(Math.random() * patterns.length);
          select.value = patterns[roll - 1];
          select.dispatchEvent(new Event("change"));
        });
        if (!currentPattern) {
          abilityChoiceOverrides[side] = abilityChoiceOverrides[side] || {};
          abilityChoiceOverrides[side][entry.species] = abilityChoiceOverrides[side][entry.species] || {};
          abilityChoiceOverrides[side][entry.species][abilityName] = { serpents_mark_roll: 1, serpents_mark_pattern: "Attack Pattern" };
        }
        abilityRow.appendChild(select);
        abilityRow.appendChild(rollButton);
      } else if (normalizedAbility === _normalizeAbilityChoiceKey("fabulous trim")) {
        const styles = ["Natural", "Debutante Trim", "Diamond Trim", "Heart Trim", "Kabuki Trim", "La Reine Trim", "Matron Trim", "Pharaoh Trim", "Star Trim", "Dandy Trim"];
        const select = document.createElement("select");
        styles.forEach((style) => {
          const option = document.createElement("option");
          option.value = style;
          option.textContent = style;
          select.appendChild(option);
        });
        const currentStyle = String(abilityChoiceOverrides?.[side]?.[entry.species]?.[abilityName]?.fabulous_trim_style || "");
        select.value = currentStyle || "Natural";
        select.addEventListener("change", () => {
          abilityChoiceOverrides[side] = abilityChoiceOverrides[side] || {};
          abilityChoiceOverrides[side][entry.species] = abilityChoiceOverrides[side][entry.species] || {};
          abilityChoiceOverrides[side][entry.species][abilityName] = { fabulous_trim_style: select.value };
          saveSettings();
        });
        if (!currentStyle) {
          abilityChoiceOverrides[side] = abilityChoiceOverrides[side] || {};
          abilityChoiceOverrides[side][entry.species] = abilityChoiceOverrides[side][entry.species] || {};
          abilityChoiceOverrides[side][entry.species][abilityName] = { fabulous_trim_style: "Natural" };
        }
        abilityRow.appendChild(select);
      } else if (normalizedAbility === _normalizeAbilityChoiceKey("giver")) {
        const select = document.createElement("select");
        [
          ["", "Auto"],
          ["5", "Damage Present"],
          ["1", "Healing Present"],
        ].forEach(([value, text]) => {
          const option = document.createElement("option");
          option.value = value;
          option.textContent = text;
          select.appendChild(option);
        });
        select.value = String(abilityChoiceOverrides?.[side]?.[entry.species]?.[abilityName]?.giver_choice_roll || "");
        select.addEventListener("change", () => {
          abilityChoiceOverrides[side] = abilityChoiceOverrides[side] || {};
          abilityChoiceOverrides[side][entry.species] = abilityChoiceOverrides[side][entry.species] || {};
          if (!select.value) {
            delete abilityChoiceOverrides[side][entry.species][abilityName];
          } else {
            abilityChoiceOverrides[side][entry.species][abilityName] = { giver_choice_roll: Number(select.value) };
          }
          saveSettings();
        });
        abilityRow.appendChild(select);
      }
      card.appendChild(abilityRow);
    });
    wrap.appendChild(card);
  });
  deploymentEditorEl.appendChild(wrap);
}

function _mirrorRosterCsvToFoe(csvText) {
  const rows = parseCsv(String(csvText || ""));
  if (!rows.length) throw new Error("Roster CSV is empty.");
  const header = (rows[0] || []).map((cell) => String(cell || ""));
  const normalizedHeader = header.map((cell) => String(cell || "").trim().toLowerCase());
  const speciesIdx = normalizedHeader.findIndex((cell) => ["species", "pokemon", "name"].includes(cell));
  if (speciesIdx < 0) throw new Error("Roster CSV requires a species column.");
  let sideIdx = normalizedHeader.findIndex((cell) => ["side", "team", "faction"].includes(cell));
  let nextRows = rows.map((row) => Array.isArray(row) ? row.slice() : []);
  if (sideIdx < 0) {
    sideIdx = header.length;
    nextRows = nextRows.map((row, idx) => {
      const next = row.slice();
      if (idx === 0) next.push("side");
      else next.push("player");
      return next;
    });
  }
  const slotIdx = normalizedHeader.findIndex((cell) => ["slot", "index", "position"].includes(cell));
  const originals = [];
  for (let i = 1; i < nextRows.length; i += 1) {
    const row = nextRows[i] || [];
    const species = String(row[speciesIdx] || "").trim();
    if (!species) continue;
    const side = _normalizeRosterSide(row[sideIdx] || "player") || "player";
    row[sideIdx] = side;
    if (side !== "foe") originals.push(row.slice());
  }
  let foeSlot = 1;
  originals.forEach((row) => {
    const clone = row.slice();
    clone[sideIdx] = "foe";
    if (slotIdx >= 0) clone[slotIdx] = String(foeSlot++);
    nextRows.push(clone);
  });
  return stringifyCsv(nextRows);
}

function _defaultRosterSideLabels(targetCount) {
  const count = Math.max(1, Number(targetCount || 1));
  const labels = ["player"];
  if (count >= 2) labels.push("foe");
  for (let index = 3; index <= count; index += 1) {
    labels.push(`side_${index}`);
  }
  return labels;
}

function _expandRosterCsvToSideCount(csvText, targetCount) {
  const rows = parseCsv(String(csvText || ""));
  if (!rows.length) throw new Error("Roster CSV is empty.");
  const header = (rows[0] || []).map((cell) => String(cell || ""));
  const normalizedHeader = header.map((cell) => String(cell || "").trim().toLowerCase());
  const speciesIdx = normalizedHeader.findIndex((cell) => ["species", "pokemon", "name"].includes(cell));
  if (speciesIdx < 0) throw new Error("Roster CSV requires a species column.");
  const requestedCount = Math.max(1, Number(targetCount || 1));
  let sideIdx = normalizedHeader.findIndex((cell) => ["side", "team", "faction"].includes(cell));
  let nextRows = rows.map((row) => Array.isArray(row) ? row.slice() : []);
  if (sideIdx < 0) {
    sideIdx = header.length;
    nextRows = nextRows.map((row, idx) => {
      const next = row.slice();
      if (idx === 0) next.push("side");
      else next.push("player");
      return next;
    });
  }
  const slotIdx = normalizedHeader.findIndex((cell) => ["slot", "index", "position"].includes(cell));
  const existingSides = [];
  const seenSides = new Set();
  for (let i = 1; i < nextRows.length; i += 1) {
    const row = nextRows[i] || [];
    const species = String(row[speciesIdx] || "").trim();
    if (!species) continue;
    const side = _normalizeRosterSide(row[sideIdx] || "player") || "player";
    row[sideIdx] = side;
    if (!seenSides.has(side)) {
      seenSides.add(side);
      existingSides.push(side);
    }
  }
  if (!existingSides.length) throw new Error("Roster CSV has no usable rows.");
  if (existingSides.length >= requestedCount) return stringifyCsv(nextRows);
  const desiredSides = existingSides.slice();
  _defaultRosterSideLabels(requestedCount).forEach((label) => {
    if (desiredSides.length >= requestedCount) return;
    if (!desiredSides.includes(label)) desiredSides.push(label);
  });
  while (desiredSides.length < requestedCount) {
    desiredSides.push(`side_${desiredSides.length + 1}`);
  }
  const templateSide = existingSides.includes("player") ? "player" : existingSides[0];
  const templateRows = nextRows.slice(1).filter((row) => {
    const species = String(row[speciesIdx] || "").trim();
    if (!species) return false;
    return (_normalizeRosterSide(row[sideIdx] || "player") || "player") === templateSide;
  });
  let nextSlotBySide = 1;
  desiredSides.slice(existingSides.length).forEach((sideLabel) => {
    templateRows.forEach((template) => {
      const clone = template.slice();
      clone[sideIdx] = sideLabel;
      if (slotIdx >= 0) clone[slotIdx] = String(nextSlotBySide++);
      nextRows.push(clone);
    });
  });
  return stringifyCsv(nextRows);
}

function _assignRosterCsvSide(csvText, targetSide) {
  const rows = parseCsv(String(csvText || ""));
  if (!rows.length) throw new Error("Roster CSV is empty.");
  const header = (rows[0] || []).map((cell) => String(cell || ""));
  const normalizedHeader = header.map((cell) => String(cell || "").trim().toLowerCase());
  const speciesIdx = normalizedHeader.findIndex((cell) => ["species", "pokemon", "name"].includes(cell));
  if (speciesIdx < 0) throw new Error("Roster CSV requires a species column.");
  let sideIdx = normalizedHeader.findIndex((cell) => ["side", "team", "faction"].includes(cell));
  const slotIdx = normalizedHeader.findIndex((cell) => ["slot", "index", "position"].includes(cell));
  let nextRows = rows.map((row) => Array.isArray(row) ? row.slice() : []);
  if (sideIdx < 0) {
    sideIdx = header.length;
    nextRows = nextRows.map((row, idx) => {
      const next = row.slice();
      if (idx === 0) next.push("side");
      else next.push("");
      return next;
    });
  }
  const safeSide = _normalizeRosterSide(targetSide) || "player";
  let slot = 1;
  for (let i = 1; i < nextRows.length; i += 1) {
    const row = nextRows[i] || [];
    const species = String(row[speciesIdx] || "").trim();
    if (!species) continue;
    row[sideIdx] = safeSide;
    if (slotIdx >= 0) row[slotIdx] = String(slot++);
  }
  return stringifyCsv(nextRows);
}

function _mergeRosterCsvBySide(baseCsvText, incomingCsvText) {
  const baseRows = parseCsv(String(baseCsvText || ""));
  if (!baseRows.length) return String(incomingCsvText || "");
  const incomingRows = parseCsv(String(incomingCsvText || ""));
  if (!incomingRows.length) return String(baseCsvText || "");
  const normalizeHeader = (row) => (row || []).map((cell) =>
    String(cell || "")
      .replace(/^\ufeff/, "")
      .trim()
      .replace(/^"+|"+$/g, "")
      .toLowerCase()
  );
  const baseHeader = normalizeHeader(baseRows[0]);
  const incomingHeader = normalizeHeader(incomingRows[0]);
  const baseSpeciesIdx = baseHeader.findIndex((cell) => ["species", "pokemon", "name"].includes(cell));
  const incomingSpeciesIdx = incomingHeader.findIndex((cell) => ["species", "pokemon", "name"].includes(cell));
  if (baseSpeciesIdx < 0 || incomingSpeciesIdx < 0) {
    throw new Error("Roster CSV requires a species column.");
  }
  const baseSideIdx = baseHeader.findIndex((cell) => ["side", "team", "faction"].includes(cell));
  const incomingSideIdx = incomingHeader.findIndex((cell) => ["side", "team", "faction"].includes(cell));
  const baseSlotIdx = baseHeader.findIndex((cell) => ["slot", "index", "position"].includes(cell));
  const incomingSideSet = new Set();
  for (let i = 1; i < incomingRows.length; i += 1) {
    const row = incomingRows[i] || [];
    const species = String(row[incomingSpeciesIdx] || "").trim();
    if (!species) continue;
    incomingSideSet.add(_normalizeRosterSide(incomingSideIdx >= 0 ? row[incomingSideIdx] : "player") || "player");
  }
  const merged = [baseRows[0].slice()];
  for (let i = 1; i < baseRows.length; i += 1) {
    const row = baseRows[i] || [];
    const species = String(row[baseSpeciesIdx] || "").trim();
    if (!species) continue;
    const side = _normalizeRosterSide(baseSideIdx >= 0 ? row[baseSideIdx] : "player") || "player";
    if (!incomingSideSet.has(side)) {
      merged.push(row.slice());
    }
  }
  for (let i = 1; i < incomingRows.length; i += 1) {
    const row = incomingRows[i] || [];
    const species = String(row[incomingSpeciesIdx] || "").trim();
    if (!species) continue;
    const normalized = row.slice();
    if (baseSlotIdx >= 0) {
      while (normalized.length <= baseSlotIdx) normalized.push("");
    }
    merged.push(normalized);
  }
  if (baseSideIdx >= 0 && baseSlotIdx >= 0) {
    const nextSlotBySide = new Map();
    for (let i = 1; i < merged.length; i += 1) {
      const row = merged[i] || [];
      const species = String(row[baseSpeciesIdx] || "").trim();
      if (!species) continue;
      const side = _normalizeRosterSide(row[baseSideIdx] || "player") || "player";
      const nextSlot = Number(nextSlotBySide.get(side) || 0) + 1;
      nextSlotBySide.set(side, nextSlot);
      row[baseSlotIdx] = String(nextSlot);
    }
  }
  return stringifyCsv(merged);
}

function _availableImportSideChoices() {
  const count = Math.max(2, Number(sideCountInput?.value || 2) || 2);
  return _defaultRosterSideLabels(count);
}

function _chooseRosterImportSide(csvText, sourceName = "") {
  return new Promise((resolve) => {
    let summary = null;
    try {
      summary = _extractRosterSummary(csvText, { allowSingleTeam: true });
    } catch (error) {
      resolve({ mode: "keep", csvText });
      return;
    }
    const modal = document.createElement("div");
    modal.className = "char-connection-modal";
    const box = document.createElement("div");
    box.className = "char-connection-box";
    const title = document.createElement("div");
    title.className = "char-section-title";
    title.textContent = "Choose Team Side";
    box.appendChild(title);
    const note = document.createElement("div");
    note.className = "char-feature-meta";
    const sides = Number(summary?.sideCount || 0);
    note.textContent = sides > 1
      ? `This import contains ${sides} side labels. You can keep them, or remap the whole import onto one side.`
      : "This import is a single team. Choose which side it should occupy in PTUWeb.";
    box.appendChild(note);
    if (sourceName) {
      const sourceMeta = document.createElement("div");
      sourceMeta.className = "char-feature-meta";
      sourceMeta.textContent = `Source: ${sourceName}`;
      box.appendChild(sourceMeta);
    }
    const select = document.createElement("select");
    select.className = "char-select";
    const keepOption = document.createElement("option");
    keepOption.value = "__keep__";
    keepOption.textContent = sides > 1 ? "Keep sides from file" : "Keep side from file (defaults to player if missing)";
    select.appendChild(keepOption);
    _availableImportSideChoices().forEach((side) => {
      const option = document.createElement("option");
      option.value = side;
      option.textContent = `Import as ${side}`;
      if (sides <= 1 && side === "player") option.selected = true;
      select.appendChild(option);
    });
    if (sides > 1) select.value = "__keep__";
    box.appendChild(select);
    const actions = document.createElement("div");
    actions.className = "char-action-row";
    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.className = "char-mini-button";
    cancel.textContent = "Cancel";
    cancel.addEventListener("click", () => {
      modal.remove();
      resolve(null);
    });
    const apply = document.createElement("button");
    apply.type = "button";
    apply.textContent = "Load Team";
    apply.addEventListener("click", () => {
      const choice = String(select.value || "__keep__");
      modal.remove();
      if (choice === "__keep__") resolve({ mode: "keep", csvText });
      else resolve({ mode: "assign", side: choice, csvText: _assignRosterCsvSide(csvText, choice) });
    });
    actions.appendChild(cancel);
    actions.appendChild(apply);
    box.appendChild(actions);
    modal.appendChild(box);
    modal.addEventListener("click", (event) => {
      if (event.target === modal) {
        modal.remove();
        resolve(null);
      }
    });
    document.body.appendChild(modal);
  });
}

function _extractRosterSummary(csvText, options = {}) {
  const allowSingleTeam = !!options.allowSingleTeam;
  const rows = parseCsv(String(csvText || ""));
  if (!rows.length) throw new Error("Roster CSV is empty.");
  const header = (rows[0] || []).map((cell) => String(cell || "").trim().toLowerCase());
  const sideIdx = header.findIndex((cell) => ["side", "team", "faction"].includes(cell));
  const speciesIdx = header.findIndex((cell) => ["species", "pokemon", "name"].includes(cell));
  if (speciesIdx < 0) {
    throw new Error("Roster CSV requires a species column.");
  }
  const sideCounts = new Map();
  for (let i = 1; i < rows.length; i += 1) {
    const row = rows[i] || [];
    const species = String(row[speciesIdx] || "").trim();
    if (!species) continue;
    const side = sideIdx >= 0 ? _normalizeRosterSide(row[sideIdx]) : "player";
    if (!side) {
      throw new Error(`Roster CSV row ${i + 1}: invalid side value.`);
    }
    sideCounts.set(side, Number(sideCounts.get(side) || 0) + 1);
  }
  if (!sideCounts.size) {
    throw new Error("Roster CSV has no usable rows.");
  }
  if (!allowSingleTeam && sideCounts.size < 2) {
    throw new Error("Roster CSV must include at least two distinct side labels.");
  }
  const playerCount = Number(sideCounts.get("player") || 0);
  const foeCount = Number(sideCounts.get("foe") || 0);
  const teamSize = Array.from(sideCounts.values()).reduce((best, value) => Math.max(best, Number(value || 0)), 1);
  return {
    players: playerCount,
    foes: foeCount,
    teamSize,
    sideCount: sideCounts.size,
  };
}

function _parseStagedRosterPreview(csvText) {
  const rows = parseCsv(String(csvText || ""));
  if (!rows.length) return [];
  const header = (rows[0] || []).map((cell) =>
    String(cell || "")
      .replace(/^\ufeff/, "")
      .trim()
      .replace(/^"+|"+$/g, "")
      .toLowerCase()
  );
  const speciesIdx = header.findIndex((cell) => ["species", "pokemon", "name"].includes(cell));
  if (speciesIdx < 0) return [];
  const sideIdx = header.findIndex((cell) => ["side", "team", "faction"].includes(cell));
  const slotIdx = header.findIndex((cell) => ["slot", "index", "position"].includes(cell));
  const levelIdx = header.findIndex((cell) => cell === "level");
  const natureIdx = header.findIndex((cell) => cell === "nature");
  const abilityIdx = header.findIndex((cell) => cell === "ability1" || cell === "ability");
  const itemIdx = header.findIndex((cell) => cell === "item1" || cell === "item");
  const hpIdx = header.findIndex((cell) => cell === "hp");
  const atkIdx = header.findIndex((cell) => cell === "atk");
  const defIdx = header.findIndex((cell) => cell === "def");
  const spatkIdx = header.findIndex((cell) => cell === "spatk");
  const spdefIdx = header.findIndex((cell) => cell === "spdef");
  const spdIdx = header.findIndex((cell) => cell === "spd");
  const moveIndexes = header
    .map((cell, index) => (/^move[1-8]$/.test(cell) ? index : -1))
    .filter((index) => index >= 0);
  const sideSlots = new Map();
  const preview = [];
  for (let i = 1; i < rows.length; i += 1) {
    const row = rows[i] || [];
    const species = String(row[speciesIdx] || "").trim();
    if (!species) continue;
    const side = _normalizeRosterSide(sideIdx >= 0 ? row[sideIdx] : "player") || "player";
    const rawSlot = slotIdx >= 0 ? Number(row[slotIdx]) : NaN;
    const nextSlot = Number(sideSlots.get(side) || 0) + 1;
    sideSlots.set(side, nextSlot);
    const slot = Number.isFinite(rawSlot) && rawSlot > 0 ? Math.trunc(rawSlot) : nextSlot;
    const rawLevel = levelIdx >= 0 ? Number(row[levelIdx]) : NaN;
    preview.push({
      id: `staged-${side}-${slot}`,
      side,
      slot,
      name: species,
      species,
      level: Number.isFinite(rawLevel) && rawLevel > 0 ? Math.trunc(rawLevel) : null,
      nature: natureIdx >= 0 ? String(row[natureIdx] || "").trim() : "",
      ability: abilityIdx >= 0 ? String(row[abilityIdx] || "").trim() : "",
      item: itemIdx >= 0 ? String(row[itemIdx] || "").trim() : "",
      sprite_url: `/api/sprites/pokemon?name=${encodeURIComponent(species)}`,
      stats: {
        hp: hpIdx >= 0 ? String(row[hpIdx] || "").trim() : "",
        atk: atkIdx >= 0 ? String(row[atkIdx] || "").trim() : "",
        def: defIdx >= 0 ? String(row[defIdx] || "").trim() : "",
        spatk: spatkIdx >= 0 ? String(row[spatkIdx] || "").trim() : "",
        spdef: spdefIdx >= 0 ? String(row[spdefIdx] || "").trim() : "",
        spd: spdIdx >= 0 ? String(row[spdIdx] || "").trim() : "",
      },
      moves: moveIndexes.map((index) => String(row[index] || "").trim()).filter(Boolean),
    });
  }
  preview.sort((a, b) => {
    if (a.side !== b.side) return formatTeamLabel(a.side).localeCompare(formatTeamLabel(b.side));
    return a.slot - b.slot;
  });
  return preview;
}

function _currentRosterPreview() {
  if (Array.isArray(state?.combatants) && state.combatants.length) return [];
  if (!battleRosterCsvText) return [];
  return _parseStagedRosterPreview(battleRosterCsvText);
}

function _renderRosterCsvStatus() {
  if (!rosterCsvStatusEl) return;
  if (!battleRosterCsvText || !battleRosterCsvMeta) {
    rosterCsvStatusEl.textContent = "Roster CSV: none";
    return;
  }
  const sideCount = Number(battleRosterCsvMeta.sideCount || 0);
  const sideLabel =
    sideCount > 2
      ? `${sideCount} sides`
      : `${battleRosterCsvMeta.players} player / ${battleRosterCsvMeta.foes} foe`;
  rosterCsvStatusEl.textContent = `Roster CSV: loaded (${sideLabel})` + (battleRosterCsvMeta.source ? ` - ${battleRosterCsvMeta.source}` : "");
}

function _setBattleRosterCsv(csvText, source = "") {
  const summary = _extractRosterSummary(csvText, { allowSingleTeam: true });
  battleRosterCsvText = String(csvText || "");
  battleRosterCsvMeta = { ...summary, source: String(source || "") };
  _renderRosterCsvStatus();
  syncStatusTabs();
  renderSideNameEditor();
  renderDeploymentEditor();
  renderCombatants();
  renderPartyBar();
}

function _clearBattleRosterCsv() {
  battleRosterCsvText = "";
  battleRosterCsvMeta = null;
  deploymentOverrides = {};
  itemChoiceOverrides = {};
  abilityChoiceOverrides = {};
  _renderRosterCsvStatus();
  syncStatusTabs();
  renderSideNameEditor();
  renderDeploymentEditor();
  renderCombatants();
  renderPartyBar();
}

function _firstName(value) {
  if (Array.isArray(value)) return _firstName(value[0]);
  if (value && typeof value === "object") {
    return String(value.name || value.id || value.label || "").trim();
  }
  return String(value || "").trim();
}

function _entryNameList(value) {
  if (!Array.isArray(value)) return [];
  return value.map((entry) => _firstName(entry)).filter(Boolean);
}

function _moveNameList(value) {
  if (!Array.isArray(value)) return [];
  return value
    .map((entry) => {
      if (entry && typeof entry === "object") return String(entry.name || "").trim();
      return String(entry || "").trim();
    })
    .filter(Boolean);
}

function _normalizeInteger(value, fallback = 0, min = null, max = null) {
  const num = Number(value);
  let next = Number.isFinite(num) ? Math.trunc(num) : Math.trunc(Number(fallback) || 0);
  if (min !== null && min !== undefined && Number.isFinite(Number(min))) next = Math.max(Number(min), next);
  if (max !== null && max !== undefined && Number.isFinite(Number(max))) next = Math.min(Number(max), next);
  return next;
}

function _normalizeMoveKey(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "");
}

function _normalizePokemonStatMode(value) {
  return String(value || "").trim().toLowerCase() === "post_nature" ? "post_nature" : "pre_nature";
}

function _normalizePokemonMoveSource(value) {
  const mode = String(value || "").trim().toLowerCase();
  if (mode === "sketch") return "sketch";
  if (mode === "egg" || mode === "egg_move" || mode === "egg move") return "egg";
  if (mode === "tutor" || mode === "tutor_tm" || mode === "tm" || mode === "non_natural") return "tutor";
  if (mode === "level" || mode === "level_up" || mode === "natural") return "level_up";
  return "";
}

function _normalizeAbilityChoiceKey(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[’`]/g, "'")
    .replace(/\*/g, "")
    .replace(/[^a-z0-9]+/g, "");
}

function _normalizePokemonMoveSources(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  const out = {};
  Object.entries(value).forEach(([key, entry]) => {
    const moveKey = _normalizeMoveKey(key);
    const source = _normalizePokemonMoveSource(entry);
    if (!moveKey || !source) return;
    out[moveKey] = source;
  });
  return out;
}

function _normalizePokeEdgeChoices(value) {
  const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  const normalizeStringArray = (entry) =>
    Array.isArray(entry)
      ? entry.map((item) => String(item || "").trim()).filter(Boolean)
      : [];
  const underdogLessonsRaw =
    source.underdog_lessons && typeof source.underdog_lessons === "object" && !Array.isArray(source.underdog_lessons)
      ? source.underdog_lessons
      : {};
  return {
    accuracy_training: normalizeStringArray(source.accuracy_training),
    advanced_connection: normalizeStringArray(source.advanced_connection),
    underdog_lessons: {
      evolution: String(underdogLessonsRaw.evolution || "").trim(),
      moves: normalizeStringArray(underdogLessonsRaw.moves).slice(0, 3),
    },
  };
}

function _rosterAbilityHeader() {
  return ["ability1", "ability2", "ability3", "ability4"];
}

function _rosterItemHeader() {
  return ["item1", "item2", "item3", "item4", "item5", "item6", "item7", "item8"];
}

function _rosterMoveLimit() {
  return 8;
}

function _rosterMoveHeader() {
  return Array.from({ length: _rosterMoveLimit() }, (_, idx) => `move${idx + 1}`);
}

function _rosterMoveSourceHeader() {
  return Array.from({ length: _rosterMoveLimit() }, (_, idx) => `move_source${idx + 1}`);
}

function _rosterPokeEdgeHeader() {
  return ["poke_edge1", "poke_edge2", "poke_edge3", "poke_edge4", "poke_edge5", "poke_edge6", "poke_edge7", "poke_edge8"];
}

function _rosterPokeEdgeChoiceHeader() {
  return [
    "poke_edge_accuracy_training",
    "poke_edge_advanced_connection",
    "poke_edge_underdog_evolution",
    "poke_edge_underdog_moves",
  ];
}

function _rosterStatModeHeader() {
  return ["stat_mode"];
}

function _rosterTutorPointHeader() {
  return ["tutor_points"];
}

function _rosterStatHeader() {
  return ["hp", "atk", "def", "spatk", "spdef", "spd"];
}

function _rosterListCells(value, limit) {
  const list = _entryNameList(value).slice(0, Math.max(0, Number(limit || 0)));
  while (list.length < limit) list.push("");
  return list;
}

function _normalizedRosterStats(source) {
  const raw = source && typeof source === "object" ? source : {};
  return {
    hp: _normalizeInteger(raw.hp, 0, 0),
    atk: _normalizeInteger(raw.atk, 0, 0),
    def: _normalizeInteger(raw.def, 0, 0),
    spatk: _normalizeInteger(raw.spatk, 0, 0),
    spdef: _normalizeInteger(raw.spdef, 0, 0),
    spd: _normalizeInteger(raw.spd, 0, 0),
  };
}

function _rosterStatsFromCombatant(entry) {
  const stats = _normalizedRosterStats(entry?.stats);
  return _rosterStatHeader().map((key) => Number(stats[key] || 0));
}

function _rosterStatsFromBuild(build) {
  const stats = _normalizedRosterStats(build?.stats);
  return _rosterStatHeader().map((key) => Number(stats[key] || 0));
}

function _rosterMoveSourcesFromCombatant(entry) {
  const limit = _rosterMoveLimit();
  const moves = _moveNameList(entry?.moves).slice(0, limit);
  const sourceMap = _normalizePokemonMoveSources(entry?.move_sources);
  return moves.map((name) => String(sourceMap[_normalizeMoveKey(name)] || "").trim()).concat(Array(Math.max(0, limit - moves.length)).fill(""));
}

function _rosterMoveSourcesFromBuild(build) {
  const limit = _rosterMoveLimit();
  const moves = _moveNameList(build?.moves).slice(0, limit);
  const sourceMap = _normalizePokemonMoveSources(build?.move_sources);
  return moves.map((name) => String(sourceMap[_normalizeMoveKey(name)] || "").trim()).concat(Array(Math.max(0, limit - moves.length)).fill(""));
}

function _serializePokeEdgeChoiceList(value) {
  if (!Array.isArray(value)) return "";
  return value
    .map((entry) => String(entry || "").trim())
    .filter(Boolean)
    .join(";");
}

function _rosterPokeEdgeChoiceCellsFromCombatant(entry) {
  const choices = _normalizePokeEdgeChoices(entry?.poke_edge_choices);
  return [
    _serializePokeEdgeChoiceList(choices.accuracy_training),
    _serializePokeEdgeChoiceList(choices.advanced_connection),
    String(choices.underdog_lessons?.evolution || "").trim(),
    _serializePokeEdgeChoiceList(choices.underdog_lessons?.moves),
  ];
}

function _rosterPokeEdgeChoiceCellsFromBuild(build) {
  const choices = _normalizePokeEdgeChoices(build?.poke_edge_choices);
  return [
    _serializePokeEdgeChoiceList(choices.accuracy_training),
    _serializePokeEdgeChoiceList(choices.advanced_connection),
    String(choices.underdog_lessons?.evolution || "").trim(),
    _serializePokeEdgeChoiceList(choices.underdog_lessons?.moves),
  ];
}

function _downloadCsvFile(filename, content) {
  const blob = new Blob([String(content || "")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function _downloadTextFile(filename, content, mimeType = "text/plain;charset=utf-8;") {
  const blob = new Blob([String(content || "")], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function _rosterRowsFromCombatants(combatants, includeFoe = true) {
  if (!Array.isArray(combatants) || !combatants.length) return [];
  const rows = [[
    "side",
    "slot",
    "species",
    "level",
    "nickname",
    ..._rosterAbilityHeader(),
    ..._rosterItemHeader(),
    "nature",
    ..._rosterMoveHeader(),
    ..._rosterMoveSourceHeader(),
    ..._rosterPokeEdgeHeader(),
    ..._rosterPokeEdgeChoiceHeader(),
    ..._rosterStatModeHeader(),
    ..._rosterTutorPointHeader(),
    ..._rosterStatHeader(),
  ]];
  const bySide = new Map();
  combatants.forEach((entry) => {
    const side = _normalizeRosterSide(entry?.team) || _normalizeRosterSide(entry?.trainer);
    if (!side) return;
    if (!bySide.has(side)) bySide.set(side, []);
    bySide.get(side).push(entry);
  });
  const sides = includeFoe
    ? Array.from(bySide.keys())
    : Array.from(bySide.keys()).filter((side) => side === "player");
  sides.forEach((side) => {
    const members = bySide.get(side) || [];
    members.forEach((entry, idx) => {
      const moves = _moveNameList(entry?.moves).slice(0, _rosterMoveLimit());
      rows.push([
        side,
        idx + 1,
        String(entry?.species || entry?.name || "").trim(),
        Number(entry?.level || 30),
        String(entry?.name || "").trim(),
        ..._rosterListCells(entry?.abilities, 4),
        ..._rosterListCells(entry?.items, 8),
        String(entry?.nature || "").trim(),
        ...moves.map((move) => String(move || "").trim()).concat(Array(Math.max(0, _rosterMoveLimit() - moves.length)).fill("")),
        ..._rosterMoveSourcesFromCombatant(entry),
        ..._rosterListCells(entry?.poke_edges, 8),
        ..._rosterPokeEdgeChoiceCellsFromCombatant(entry),
        _normalizePokemonStatMode(entry?.stat_mode),
        _normalizeInteger(entry?.tutor_points, 0, 0),
        ..._rosterStatsFromCombatant(entry),
      ]);
    });
  });
  return rows.length > 1 ? rows : [];
}

function _rosterRowsFromTrainerBuilds(payload, includeFoe = true) {
  const builds = Array.isArray(payload?.pokemon_builds) ? payload.pokemon_builds : [];
  if (!builds.length) return [];
  const rows = [[
    "side",
    "slot",
    "species",
    "level",
    "nickname",
    ..._rosterAbilityHeader(),
    ..._rosterItemHeader(),
    "nature",
    ..._rosterMoveHeader(),
    ..._rosterMoveSourceHeader(),
    ..._rosterPokeEdgeHeader(),
    ..._rosterPokeEdgeChoiceHeader(),
    ..._rosterStatModeHeader(),
    ..._rosterTutorPointHeader(),
    ..._rosterStatHeader(),
  ]];
  builds.forEach((build, idx) => {
    const species = String(build?.species || build?.name || "").trim();
    if (!species) return;
    const level = Number(build?.level || 30);
    const nickname = String(build?.name || "").trim();
    const moves = _moveNameList(build?.moves).slice(0, _rosterMoveLimit());
    const sideMode = String(build?.battle_side || "")
      .trim()
      .toLowerCase();
    const explicitMode = sideMode === "player" || sideMode === "foe" || sideMode === "both";
    const addPlayer = explicitMode ? sideMode === "player" || sideMode === "both" : true;
    const addFoe = explicitMode ? sideMode === "foe" || sideMode === "both" : includeFoe;
    if (addPlayer) {
      rows.push([
        "player",
        idx + 1,
        species,
        level,
        nickname,
        ..._rosterListCells(build?.abilities, 4),
        ..._rosterListCells(build?.items, 8),
        String(build?.nature || "").trim(),
        ...moves.map((move) => String(move || "").trim()).concat(Array(Math.max(0, _rosterMoveLimit() - moves.length)).fill("")),
        ..._rosterMoveSourcesFromBuild(build),
        ..._rosterListCells(build?.poke_edges, 8),
        ..._rosterPokeEdgeChoiceCellsFromBuild(build),
        _normalizePokemonStatMode(build?.stat_mode),
        _normalizeInteger(build?.tutor_points, 0, 0),
        ..._rosterStatsFromBuild(build),
      ]);
    }
    if (addFoe) {
      rows.push([
        "foe",
        idx + 1,
        species,
        level,
        nickname ? `${nickname} AI` : "",
        ..._rosterListCells(build?.abilities, 4),
        ..._rosterListCells(build?.items, 8),
        String(build?.nature || "").trim(),
        ...moves.map((move) => String(move || "").trim()).concat(Array(Math.max(0, _rosterMoveLimit() - moves.length)).fill("")),
        ..._rosterMoveSourcesFromBuild(build),
        ..._rosterListCells(build?.poke_edges, 8),
        ..._rosterPokeEdgeChoiceCellsFromBuild(build),
        _normalizePokemonStatMode(build?.stat_mode),
        _normalizeInteger(build?.tutor_points, 0, 0),
        ..._rosterStatsFromBuild(build),
      ]);
    }
  });
  return rows.length > 1 ? rows : [];
}

function _readStoredTrainerPayload() {
  try {
    const raw = localStorage.getItem("autoptu_character");
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

function _buildRosterCsvFromTrainerPayload(payload, includeFoe = true) {
  const rows = _rosterRowsFromTrainerBuilds(payload, includeFoe);
  if (!rows.length) return null;
  const csvText = stringifyCsv(rows);
  const summary = _extractRosterSummary(csvText, { allowSingleTeam: !includeFoe });
  return { csvText, summary };
}

function _trainerCsvListValue(values) {
  return _normalizeStringList(values).join("; ");
}

function _trainerCsvRowsFromPayload(payload) {
  const raw = payload && typeof payload === "object" ? payload : {};
  const profile = raw.profile && typeof raw.profile === "object" ? raw.profile : {};
  const rows = [
    ["field", "value"],
    ["format", "autoptu_trainer_v1"],
    ["name", String(profile.name || "").trim()],
    ["played_by", String(profile.played_by || "").trim()],
    ["age", String(profile.age || "").trim()],
    ["sex", String(profile.sex || "").trim()],
    ["height", String(profile.height || "").trim()],
    ["weight", String(profile.weight || "").trim()],
    ["money", String(profile.money || "").trim()],
    ["region", String(profile.region || "").trim()],
    ["concept", String(profile.concept || "").trim()],
    ["background", String(profile.background || "").trim()],
    ["level", String(_normalizeInteger(profile.level, 1, 1))],
    ["class_ids", _trainerCsvListValue(raw.class_ids || (raw.class_id ? [raw.class_id] : []))],
    ["features", _trainerCsvListValue(raw.features)],
    ["edges", _trainerCsvListValue(raw.edges)],
  ];
  Object.entries(raw.stats && typeof raw.stats === "object" ? raw.stats : {}).forEach(([key, value]) => {
    rows.push([`stat_${key}`, String(_normalizeInteger(value, 0, 0))]);
  });
  Object.entries(raw.skills && typeof raw.skills === "object" ? raw.skills : {}).forEach(([key, value]) => {
    rows.push([`skill_${key}`, String(value == null ? "" : value)]);
  });
  return rows;
}

function _readTextFile(file) {
  return new Promise((resolve, reject) => {
    if (!file) {
      resolve("");
      return;
    }
    try {
      const reader = new FileReader();
      reader.onerror = () => reject(reader.error || new Error("Failed to read file."));
      reader.onload = () => resolve(typeof reader.result === "string" ? reader.result : "");
      reader.readAsText(file);
    } catch (readerError) {
      if (typeof file.text === "function") {
        Promise.resolve(file.text()).then(resolve, reject);
        return;
      }
      reject(readerError);
    }
  });
}

function _buildTrainerCsvFromTrainerPayload(payload) {
  return stringifyCsv(_trainerCsvRowsFromPayload(payload));
}

function _applyTrainerCsvToPayload(csvText, existingPayload = null) {
  const rows = parseCsv(String(csvText || ""));
  if (!rows.length) throw new Error("Trainer CSV is empty.");
  const header = (rows[0] || []).map((cell) => String(cell || "").trim().toLowerCase());
  const fieldIdx = header.findIndex((cell) => cell === "field" || cell === "key");
  const valueIdx = header.findIndex((cell) => cell === "value");
  if (fieldIdx < 0 || valueIdx < 0) throw new Error("Trainer CSV requires field,value headers.");
  const base = existingPayload && typeof existingPayload === "object" ? existingPayload : {};
  const profile = base.profile && typeof base.profile === "object" ? { ...base.profile } : {};
  const patch = {
    ...base,
    profile,
    class_ids: Array.isArray(base.class_ids) ? base.class_ids.slice() : [],
    features: Array.isArray(base.features) ? base.features.slice() : [],
    edges: Array.isArray(base.edges) ? base.edges.slice() : [],
    skills: base.skills && typeof base.skills === "object" ? { ...base.skills } : {},
    stats: base.stats && typeof base.stats === "object" ? { ...base.stats } : {},
  };
  for (let i = 1; i < rows.length; i += 1) {
    const row = rows[i] || [];
    const field = String(row[fieldIdx] || "").trim().toLowerCase();
    const value = String(row[valueIdx] || "").trim();
    if (!field || field === "format") continue;
    if (field === "class_ids") {
      patch.class_ids = value ? value.split(/\s*;\s*/).filter(Boolean) : [];
      patch.class_id = String(patch.class_ids[0] || "").trim();
      continue;
    }
    if (field === "features") {
      patch.features = value ? value.split(/\s*;\s*/).filter(Boolean) : [];
      continue;
    }
    if (field === "edges") {
      patch.edges = value ? value.split(/\s*;\s*/).filter(Boolean) : [];
      continue;
    }
    if (field.startsWith("skill_")) {
      patch.skills[field.slice(6)] = value;
      continue;
    }
    if (field.startsWith("stat_")) {
      patch.stats[field.slice(5)] = _normalizeInteger(value, 0, 0);
      continue;
    }
    patch.profile[field] = field === "level" ? _normalizeInteger(value, 1, 1) : value;
  }
  return patch;
}

function _downloadTournamentSubmissionPack() {
  const payload = {
    profile: characterState.profile,
    pokemon_builds: Array.isArray(characterState.pokemon_builds) ? characterState.pokemon_builds : [],
  };
  if (!payload.pokemon_builds.length) {
    throw new Error("No Pokemon builds found to export.");
  }
  const roster = _buildRosterCsvFromTrainerPayload(payload, false);
  const trainerCsv = _buildTrainerCsvFromTrainerPayload(payload);
  if (!roster?.csvText) {
    throw new Error("Unable to generate tournament roster CSV from current team.");
  }
  const trainerName = String(characterState.profile?.name || "participant").trim() || "participant";
  const safeName = trainerName.replace(/[^a-z0-9]+/gi, "_").replace(/^_+|_+$/g, "") || "participant";
  const files = [
    {
      name: `${safeName}_team_roster.csv`,
      content: roster.csvText,
    },
    {
      name: `${safeName}_trainer.csv`,
      content: trainerCsv,
    },
    {
      name: `${safeName}_team_builder.json`,
      content: JSON.stringify(payload, null, 2),
    },
    {
      name: "README.txt",
      content:
        "AutoPTU tournament submission pack\r\n\r\n" +
        "Use the builder JSON to fully restore the project.\r\n" +
        "Use the team CSV for battle imports or one-team encounter tests.\r\n" +
        "Use the trainer CSV when you want trainer data without the Pokemon roster.\r\n",
    },
  ];
  const blob = buildZip(files);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${safeName}_autoptu_team_pack.zip`;
  link.click();
  URL.revokeObjectURL(url);
}

function _csvCell(row, idx) {
  if (!Array.isArray(row) || idx < 0 || idx >= row.length) return "";
  return String(row[idx] || "").trim();
}

function _builderPokemonImportFromRosterCsv(csvText) {
  const rows = parseCsv(String(csvText || ""));
  if (!rows.length) throw new Error("Roster CSV is empty.");
  const header = (rows[0] || []).map((cell) => String(cell || "").trim().toLowerCase());
  const sideIdx = header.findIndex((cell) => ["side", "team", "faction"].includes(cell));
  const speciesIdx = header.findIndex((cell) => ["species", "pokemon", "name"].includes(cell));
  if (sideIdx < 0 || speciesIdx < 0) {
    throw new Error("Roster CSV requires headers including side and species.");
  }
  const levelIdx = header.findIndex((cell) => ["level", "lvl"].includes(cell));
  const nicknameIdx = header.findIndex((cell) => ["nickname", "alias"].includes(cell));
  const nameIdx = header.findIndex((cell) => cell === "name");
  const natureIdx = header.findIndex((cell) => cell === "nature");
  const slotIdx = header.findIndex((cell) => ["slot", "index", "position"].includes(cell));
  const moveIndices = header.map((cell, idx) => ({ cell, idx })).filter((entry) => /^move(?:_?\d+)?$/.test(entry.cell) || /^moves_?\d+$/.test(entry.cell)).map((entry) => entry.idx).slice(0, _rosterMoveLimit());
  const moveSourceIndices = header.map((cell, idx) => ({ cell, idx })).filter((entry) => /^move_source(?:_?\d+)?$/.test(entry.cell) || /^movesource_?\d+$/.test(entry.cell)).map((entry) => entry.idx).slice(0, _rosterMoveLimit());
  const abilityIndices = header.map((cell, idx) => ({ cell, idx })).filter((entry) => /^ability(?:_?\d+)?$/.test(entry.cell)).map((entry) => entry.idx).slice(0, 4);
  const itemIndices = header.map((cell, idx) => ({ cell, idx })).filter((entry) => /^(?:item|held_item)(?:_?\d+)?$/.test(entry.cell)).map((entry) => entry.idx).slice(0, 8);
  const pokeEdgeIndices = header.map((cell, idx) => ({ cell, idx })).filter((entry) => /^(?:poke_edge|pokeedge)(?:_?\d+)?$/.test(entry.cell)).map((entry) => entry.idx).slice(0, 8);
  const accuracyTrainingIdx = header.findIndex((cell) => ["poke_edge_accuracy_training", "edge_accuracy_training", "accuracy_training"].includes(cell));
  const advancedConnectionIdx = header.findIndex((cell) => ["poke_edge_advanced_connection", "edge_advanced_connection", "advanced_connection"].includes(cell));
  const underdogEvolutionIdx = header.findIndex((cell) => ["poke_edge_underdog_evolution", "edge_underdog_evolution", "underdog_evolution"].includes(cell));
  const underdogMovesIdx = header.findIndex((cell) => ["poke_edge_underdog_moves", "edge_underdog_moves", "underdog_moves"].includes(cell));
  const statModeIdx = header.findIndex((cell) => ["stat_mode", "stats_mode", "statmode"].includes(cell));
  const tutorPointsIdx = header.findIndex((cell) => ["tutor_points", "tutor_point", "tutorpoints", "tp"].includes(cell));
  const statIndices = {
    hp: header.findIndex((cell) => ["hp", "hp_stat", "hpstat"].includes(cell)),
    atk: header.findIndex((cell) => ["atk", "attack"].includes(cell)),
    def: header.findIndex((cell) => ["def", "defense"].includes(cell)),
    spatk: header.findIndex((cell) => ["spatk", "sp_atk", "special_attack", "specialattack", "spa"].includes(cell)),
    spdef: header.findIndex((cell) => ["spdef", "sp_def", "special_defense", "specialdefense", "spdf"].includes(cell)),
    spd: header.findIndex((cell) => ["spd", "speed"].includes(cell)),
  };
  const builds = [];
  for (let i = 1; i < rows.length; i += 1) {
    const row = rows[i] || [];
    const species = _csvCell(row, speciesIdx);
    if (!species) continue;
    const side = _normalizeRosterSide(_csvCell(row, sideIdx));
    if (!side) throw new Error(`Roster CSV row ${i + 1}: invalid side value.`);
    const nickname = _csvCell(row, nicknameIdx) || (nameIdx >= 0 && nameIdx !== speciesIdx ? _csvCell(row, nameIdx) : "");
    const nature = _csvCell(row, natureIdx);
    const level = Math.max(1, Number(_csvCell(row, levelIdx) || 30) || 30);
    const moves = moveIndices.map((idx) => _csvCell(row, idx)).filter(Boolean);
    const moveSources = {};
    moves.forEach((moveName, idx) => {
      const sourceValue = _normalizePokemonMoveSource(_csvCell(row, moveSourceIndices[idx] ?? -1));
      const moveKey = _normalizeMoveKey(moveName);
      if (moveKey && sourceValue) moveSources[moveKey] = sourceValue;
    });
    const abilities = abilityIndices.map((idx) => _csvCell(row, idx)).filter(Boolean);
    const items = itemIndices.map((idx) => _csvCell(row, idx)).filter(Boolean);
    const pokeEdges = pokeEdgeIndices.map((idx) => _csvCell(row, idx)).filter(Boolean);
    const pokeEdgeChoices = _normalizePokeEdgeChoices({
      accuracy_training: _csvCell(row, accuracyTrainingIdx)
        .split(";")
        .map((value) => String(value || "").trim())
        .filter(Boolean),
      advanced_connection: _csvCell(row, advancedConnectionIdx)
        .split(";")
        .map((value) => String(value || "").trim())
        .filter(Boolean),
      underdog_lessons: {
        evolution: _csvCell(row, underdogEvolutionIdx),
        moves: _csvCell(row, underdogMovesIdx)
          .split(";")
          .map((value) => String(value || "").trim())
          .filter(Boolean)
          .slice(0, 3),
      },
    });
    const stats = {
      hp: _normalizeInteger(_csvCell(row, statIndices.hp), 0, 0),
      atk: _normalizeInteger(_csvCell(row, statIndices.atk), 0, 0),
      def: _normalizeInteger(_csvCell(row, statIndices.def), 0, 0),
      spatk: _normalizeInteger(_csvCell(row, statIndices.spatk), 0, 0),
      spdef: _normalizeInteger(_csvCell(row, statIndices.spdef), 0, 0),
      spd: _normalizeInteger(_csvCell(row, statIndices.spd), 0, 0),
    };
    const slot = Math.max(1, Number(_csvCell(row, slotIdx) || builds.length + 1) || builds.length + 1);
    builds.push({
      name: nickname || species,
      species,
      level,
      nature,
      stat_mode: _normalizePokemonStatMode(_csvCell(row, statModeIdx)),
      tutor_points: _normalizeInteger(_csvCell(row, tutorPointsIdx), 0, 0),
      battle_side: side === "player" ? "player" : side === "foe" ? "foe" : side,
      battle_slot: slot,
      moves,
      move_sources: moveSources,
      abilities,
      items,
      poke_edges: pokeEdges,
      poke_edge_choices: pokeEdgeChoices,
      stats,
    });
  }
  if (!builds.length) throw new Error("Roster CSV has no usable rows.");
  builds.sort((a, b) => {
    const sideOrder = { player: 0, foe: 1 };
    const sideA = sideOrder[a.battle_side] ?? 2;
    const sideB = sideOrder[b.battle_side] ?? 2;
    if (sideA !== sideB) return sideA - sideB;
    return Number(a.battle_slot || 0) - Number(b.battle_slot || 0);
  });
  return {
    builds: builds.map((build) => {
      const next = { ...build };
      delete next.battle_slot;
      return next;
    }),
    summary: _extractRosterSummary(csvText, { allowSingleTeam: true }),
    csvText: String(csvText || ""),
  };
}

function _applyCsvModeControls() {
  const strict = !!csvStrictModeInput?.checked;
  if (autoUseCreatorRosterInput) {
    autoUseCreatorRosterInput.disabled = strict;
  }
}

function buildZip(files) {
  const encoder = new TextEncoder();
  const parts = [];
  const central = [];
  let offset = 0;
  const dosTime = 0;
  const dosDate = 0;

  const crcTable = (() => {
    const table = new Uint32Array(256);
    for (let i = 0; i < 256; i += 1) {
      let c = i;
      for (let k = 0; k < 8; k += 1) {
        c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      }
      table[i] = c >>> 0;
    }
    return table;
  })();

  const crc32 = (data) => {
    let crc = 0xffffffff;
    for (let i = 0; i < data.length; i += 1) {
      crc = crcTable[(crc ^ data[i]) & 0xff] ^ (crc >>> 8);
    }
    return (crc ^ 0xffffffff) >>> 0;
  };

  files.forEach((file) => {
    const nameBytes = encoder.encode(file.name);
    const dataBytes = encoder.encode(file.content);
    const crc = crc32(dataBytes);
    const localHeader = new Uint8Array(30 + nameBytes.length);
    const dv = new DataView(localHeader.buffer);
    dv.setUint32(0, 0x04034b50, true);
    dv.setUint16(4, 20, true);
    dv.setUint16(6, 0, true);
    dv.setUint16(8, 0, true);
    dv.setUint16(10, dosTime, true);
    dv.setUint16(12, dosDate, true);
    dv.setUint32(14, crc, true);
    dv.setUint32(18, dataBytes.length, true);
    dv.setUint32(22, dataBytes.length, true);
    dv.setUint16(26, nameBytes.length, true);
    dv.setUint16(28, 0, true);
    localHeader.set(nameBytes, 30);
    parts.push(localHeader, dataBytes);

    const centralHeader = new Uint8Array(46 + nameBytes.length);
    const cdv = new DataView(centralHeader.buffer);
    cdv.setUint32(0, 0x02014b50, true);
    cdv.setUint16(4, 20, true);
    cdv.setUint16(6, 20, true);
    cdv.setUint16(8, 0, true);
    cdv.setUint16(10, 0, true);
    cdv.setUint16(12, dosTime, true);
    cdv.setUint16(14, dosDate, true);
    cdv.setUint32(16, crc, true);
    cdv.setUint32(20, dataBytes.length, true);
    cdv.setUint32(24, dataBytes.length, true);
    cdv.setUint16(28, nameBytes.length, true);
    cdv.setUint16(30, 0, true);
    cdv.setUint16(32, 0, true);
    cdv.setUint16(34, 0, true);
    cdv.setUint16(36, 0, true);
    cdv.setUint32(38, 0, true);
    cdv.setUint32(42, offset, true);
    centralHeader.set(nameBytes, 46);
    central.push(centralHeader);

    offset += localHeader.length + dataBytes.length;
  });

  const centralSize = central.reduce((sum, chunk) => sum + chunk.length, 0);
  const centralOffset = offset;
  const endRecord = new Uint8Array(22);
  const edv = new DataView(endRecord.buffer);
  edv.setUint32(0, 0x06054b50, true);
  edv.setUint16(4, 0, true);
  edv.setUint16(6, 0, true);
  edv.setUint16(8, files.length, true);
  edv.setUint16(10, files.length, true);
  edv.setUint32(12, centralSize, true);
  edv.setUint32(16, centralOffset, true);
  edv.setUint16(20, 0, true);
  parts.push(...central, endRecord);

  return new Blob(parts, { type: "application/zip" });
}

function _readZipEntries(buffer) {
  const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer || new ArrayBuffer(0));
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const decoder = new TextDecoder();
  const files = {};
  let offset = 0;
  while (offset + 30 <= bytes.length) {
    const signature = view.getUint32(offset, true);
    if (signature === 0x02014b50 || signature === 0x06054b50) break;
    if (signature !== 0x04034b50) {
      offset += 1;
      continue;
    }
    const compression = view.getUint16(offset + 8, true);
    const compressedSize = view.getUint32(offset + 18, true);
    const uncompressedSize = view.getUint32(offset + 22, true);
    const fileNameLength = view.getUint16(offset + 26, true);
    const extraLength = view.getUint16(offset + 28, true);
    const nameStart = offset + 30;
    const dataStart = nameStart + fileNameLength + extraLength;
    const dataEnd = dataStart + compressedSize;
    if (dataEnd > bytes.length) break;
    const name = decoder.decode(bytes.slice(nameStart, nameStart + fileNameLength));
    if (!name) break;
    if (compression !== 0) throw new Error("Project ZIP import only supports stored AutoPTU ZIP files.");
    const raw = bytes.slice(dataStart, dataStart + Math.min(compressedSize, uncompressedSize || compressedSize));
    files[name] = decoder.decode(raw);
    offset = dataEnd;
  }
  return files;
}

async function loadFancyTemplate(name) {
  const candidates = [`fancy_templates/${name}`, `/fancy_templates/${name}`];
  for (const path of candidates) {
    try {
      const response = await fetch(path);
      if (response.ok) return response.text();
    } catch {
      // ignore
    }
  }
  return "";
}

let inventoryCatalogCache = null;

async function loadInventoryCatalog() {
  if (inventoryCatalogCache) return inventoryCatalogCache;
  const raw = await loadFancyTemplate("Inv Data.csv");
  if (!raw) {
    inventoryCatalogCache = [];
    return inventoryCatalogCache;
  }
  const rows = parseCsv(raw);
  if (rows.length < 2) {
    inventoryCatalogCache = [];
    return inventoryCatalogCache;
  }
  const catalog = [];
  const categories = [
    { name: rows[0][0], cols: [0, 1, 2], kind: "key" },
    { name: rows[0][3], cols: [3, 4, 5], kind: "key" },
    { name: rows[0][6], cols: [6, 7, 8], kind: "key" },
    { name: rows[0][9], cols: [9, 10, 11], kind: "pokemon" },
    { name: rows[0][12], cols: [12, 13, 14, 15], kind: "key" },
    { name: rows[0][16], cols: [16, 17, 18, 19], kind: "key" },
  ];
  rows.slice(2).forEach((row) => {
    categories.forEach((cat) => {
      const name = (row[cat.cols[0]] || "").trim();
      if (!name) return;
      const cost = row[cat.cols[1]] || "";
      const extra = cat.cols.length > 3 ? row[cat.cols[2]] || "" : "";
      const desc = row[cat.cols[cat.cols.length - 1]] || "";
      const detail = extra ? `${extra}` : "";
      catalog.push({
        name,
        cost,
        desc,
        extra: detail,
        category: cat.name || "",
        kind: cat.kind,
      });
    });
  });
  inventoryCatalogCache = catalog;
  return catalog;
}

function rankValue(rank, rules) {
  if (!rank) return "";
  const ranks = rules?.ranks || [];
  const idx = ranks.indexOf(rank);
  if (idx === -1) return "";
  const mapping = [1, 2, 3, 4, 5, 6];
  return mapping[Math.min(idx, mapping.length - 1)] || "";
}

function computeFancyTrainerRows() {
  const rules = characterData?.skill_rules || {};
  const derived = computeDerivedStats(characterState.stats, characterState.skills, rules, characterState.profile.level);
  const featuresCount = characterState.features.size;
  const edgesCount = characterState.edges.size;
  return { rules, derived, featuresCount, edgesCount };
}

async function exportFancyPtuSheet() {
  const trainerCsv = await loadFancyTemplate("Trainer.csv");
  const featuresCsv = await loadFancyTemplate("Features.csv");
  const edgesCsv = await loadFancyTemplate("Edges.csv");
  const extrasCsv = await loadFancyTemplate("Extras.csv");
  const inventoryCsv = await loadFancyTemplate("Inventory.csv");
  const combatCsv = await loadFancyTemplate("Combat.csv");
  if (!trainerCsv || !featuresCsv || !edgesCsv) {
    alert("Fancy PTU templates missing. Ensure fancy_templates are available.");
    return;
  }
  const { rules, derived, featuresCount, edgesCount } = computeFancyTrainerRows();
  const trainerRows = parseCsv(trainerCsv);
  const featuresRows = parseCsv(featuresCsv);
  const edgesRows = parseCsv(edgesCsv);
  const extrasRows = extrasCsv ? parseCsv(extrasCsv) : [];
  const inventoryRows = inventoryCsv ? parseCsv(inventoryCsv) : [];
  const combatRows = combatCsv ? parseCsv(combatCsv) : [];

  const name = characterState.profile.name || "";
  const playedBy = characterState.profile.played_by || "";
  const age = characterState.profile.age || "";
  const sex = characterState.profile.sex || "";
  const height = characterState.profile.height || "";
  const weight = characterState.profile.weight || "";
  const level = String(characterState.profile.level || 1);
  const maxHp = String(derived.maxHp || "");
  const money = String(characterState.profile.money || "");

  if (trainerRows[0]) {
    trainerRows[0][0] = "Name";
    trainerRows[0][6] = "Level";
    trainerRows[0][7] = "Max HP";
  }
  if (trainerRows[1]) {
    trainerRows[1][0] = name;
    trainerRows[1][1] = playedBy;
    trainerRows[1][2] = age;
    trainerRows[1][3] = sex;
    trainerRows[1][4] = height;
    trainerRows[1][5] = weight;
    trainerRows[1][6] = level;
    trainerRows[1][7] = maxHp;
    trainerRows[1][9] = money;
  }
  const statMap = {
    HP: characterState.stats.hp,
    ATK: characterState.stats.atk,
    DEF: characterState.stats.def,
    SATK: characterState.stats.spatk,
    SDEF: characterState.stats.spdef,
    SPD: characterState.stats.spd,
  };
  trainerRows.forEach((row) => {
    const key = String(row[0] || "").trim().toUpperCase();
    if (statMap[key] !== undefined) {
      row[1] = String(statMap[key]);
      row[6] = String(statMap[key]);
    }
  });
  if (trainerRows[10]) {
    trainerRows[10][6] = String(featuresCount);
    trainerRows[10][8] = String(edgesCount);
  }
  const bg = characterState.skill_background || {};
  if (trainerRows[3]) trainerRows[3][8] = characterState.profile.background || "";
  if (trainerRows[4]) trainerRows[4][8] = characterState.profile.concept || "";
  if (trainerRows[6]) trainerRows[6][7] = bg.adept || "";
  if (trainerRows[6]) trainerRows[6][8] = (bg.pathetic || []).filter(Boolean).join(", ");
  if (trainerRows[8]) trainerRows[8][7] = bg.novice || "";

  trainerRows.forEach((row) => {
    const skillName = String(row[0] || "").trim();
    if (!skillName || !characterState.skills[skillName]) return;
    const rank = characterState.skills[skillName];
    row[2] = rank;
    const value = rankValue(rank, rules);
    if (value !== "") row[4] = String(value);
  });

  const selectedFeatures = Array.from(characterState.features);
  const featureCatalog = (characterData.features || []).slice();
  const featureByName = new Map(featureCatalog.map((f) => [f.name, f]));
  let featureRowIndex = 1;
  selectedFeatures.forEach((name) => {
    const entry = featureByName.get(name);
    if (!entry) return;
    if (!featuresRows[featureRowIndex]) {
      featuresRows[featureRowIndex] = ["", "", "--", "--", "--", "--"];
    }
    featuresRows[featureRowIndex][0] = entry.name || "";
    featuresRows[featureRowIndex][1] = "";
    featuresRows[featureRowIndex][2] = entry.tags || "";
    featuresRows[featureRowIndex][3] = entry.prerequisites || "";
    featuresRows[featureRowIndex][4] = entry.frequency || "";
    featuresRows[featureRowIndex][5] = entry.effects || "";
    featureRowIndex += 1;
  });

  const selectedEdges = Array.from(characterState.edges);
  const edgeCatalog = (characterData.edges_catalog || []).slice();
  const edgeByName = new Map(edgeCatalog.map((e) => [e.name, e]));
  let edgeRowIndex = 1;
  selectedEdges.forEach((name) => {
    const entry = edgeByName.get(name);
    if (!entry) return;
    if (!edgesRows[edgeRowIndex]) {
      edgesRows[edgeRowIndex] = ["", "", "--", "--"];
    }
    edgesRows[edgeRowIndex][0] = entry.name || "";
    edgesRows[edgeRowIndex][1] = "";
    edgesRows[edgeRowIndex][2] = entry.prerequisites || "";
    edgesRows[edgeRowIndex][3] = entry.effects || "";
    edgeRowIndex += 1;
  });

  if (extrasRows.length) {
    const extras = Array.isArray(characterState.extras) ? characterState.extras : [];
    let rowIndex = 2;
    extras.forEach((entry) => {
      if (!extrasRows[rowIndex]) {
        extrasRows[rowIndex] = ["", "--", "--", "", ""];
      }
      extrasRows[rowIndex][0] = entry.className || "";
      extrasRows[rowIndex][1] = entry.mechanic || "";
      extrasRows[rowIndex][2] = entry.effect || "";
      rowIndex += 1;
    });
  }

  if (inventoryRows.length) {
    const keyItems = characterState.inventory?.key_items || [];
    const pokemonItems = characterState.inventory?.pokemon_items || [];
    let rowIndex = 2;
    keyItems.forEach((entry) => {
      if (!inventoryRows[rowIndex]) {
        inventoryRows[rowIndex] = ["", "", "--", "--", "", "", "", "", "", "--", "--", ""];
      }
      inventoryRows[rowIndex][0] = entry.name || "";
      inventoryRows[rowIndex][1] = entry.qty || "";
      inventoryRows[rowIndex][2] = entry.cost || "";
      inventoryRows[rowIndex][3] = entry.desc || "";
      rowIndex += 1;
    });
    rowIndex = 2;
    pokemonItems.forEach((entry) => {
      if (!inventoryRows[rowIndex]) {
        inventoryRows[rowIndex] = ["", "", "--", "--", "", "", "", "", "", "--", "--", ""];
      }
      inventoryRows[rowIndex][7] = entry.name || "";
      inventoryRows[rowIndex][8] = entry.qty || "";
      inventoryRows[rowIndex][9] = entry.cost || "";
      inventoryRows[rowIndex][10] = entry.desc || "";
      rowIndex += 1;
    });
  }

  const files = [
    { name: "Fancy PTU Trainer.csv", content: stringifyCsv(trainerRows) },
    { name: "Fancy PTU Features.csv", content: stringifyCsv(featuresRows) },
    { name: "Fancy PTU Edges.csv", content: stringifyCsv(edgesRows) },
  ];
  if (extrasRows.length) files.push({ name: "Fancy PTU Extras.csv", content: stringifyCsv(extrasRows) });
  if (inventoryRows.length) files.push({ name: "Fancy PTU Inventory.csv", content: stringifyCsv(inventoryRows) });
  if (combatRows.length) files.push({ name: "Fancy PTU Combat.csv", content: stringifyCsv(combatRows) });

  try {
    const zipBlob = buildZip(files);
    const link = document.createElement("a");
    link.href = URL.createObjectURL(zipBlob);
    link.download = "Fancy_PTU_Export.zip";
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch {
    files.forEach((file) => {
      const blob = new Blob([file.content], { type: "text/csv;charset=utf-8;" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = file.name;
      document.body.appendChild(link);
      link.click();
      link.remove();
    });
  }
}

async function importFancyPtuCsvFiles(fileList) {
  if (!fileList || !fileList.length) return;
  const files = Array.from(fileList);
  const skillSet = new Set(characterData?.skills || []);
  const statMap = {
    HP: "hp",
    ATK: "atk",
    DEF: "def",
    SATK: "spatk",
    SDEF: "spdef",
    SPD: "spd",
  };
  for (const file of files) {
    const name = String(file.name || "").toLowerCase();
    const text = await _readTextFile(file);
    const rows = parseCsv(text);
    if (!rows.length) continue;
    if (name.includes("trainer")) {
      if (rows[1]) {
        characterState.profile.name = rows[1][0] || characterState.profile.name;
        characterState.profile.played_by = rows[1][1] || characterState.profile.played_by;
        characterState.profile.age = rows[1][2] || characterState.profile.age;
        characterState.profile.sex = rows[1][3] || characterState.profile.sex;
        characterState.profile.height = rows[1][4] || characterState.profile.height;
        characterState.profile.weight = rows[1][5] || characterState.profile.weight;
        characterState.profile.level = Number(rows[1][6] || characterState.profile.level || 1);
        characterState.profile.money = rows[1][9] || characterState.profile.money;
      }
      rows.forEach((row) => {
        const key = String(row[0] || "").trim().toUpperCase();
        if (statMap[key]) {
          const value = Number(row[1] || row[6] || 0);
          if (Number.isFinite(value) && value > 0) {
            characterState.stats[statMap[key]] = value;
          }
        }
        const skillName = String(row[0] || "").trim();
        if (skillSet.has(skillName)) {
          const rank = row[2] || "";
          if (rank) characterState.skills[skillName] = rank;
        }
      });
      if (rows[3]) characterState.profile.background = rows[3][8] || characterState.profile.background;
      if (rows[4]) characterState.profile.concept = rows[4][8] || characterState.profile.concept;
      const bg = characterState.skill_background || { adept: "", novice: "", pathetic: [] };
      if (rows[6]) {
        bg.adept = rows[6][7] || bg.adept;
        const pat = rows[6][8] || "";
        if (pat) bg.pathetic = pat.split(",").map((s) => s.trim()).filter(Boolean);
      }
      if (rows[8]) {
        bg.novice = rows[8][7] || bg.novice;
      }
      characterState.skill_background = bg;
    } else if (name.includes("features")) {
      const picks = [];
      rows.slice(1).forEach((row) => {
        const nameCell = (row[0] || "").trim();
        if (!nameCell || nameCell === "--") return;
        picks.push(nameCell);
      });
      if (picks.length) characterState.features = new Set(picks);
    } else if (name.includes("edges")) {
      const picks = [];
      rows.slice(1).forEach((row) => {
        const nameCell = (row[0] || "").trim();
        if (!nameCell || nameCell === "--") return;
        picks.push(nameCell);
      });
      if (picks.length) characterState.edges = new Set(picks);
    } else if (name.includes("extras")) {
      const extras = [];
      rows.slice(2).forEach((row) => {
        const className = (row[0] || "").trim();
        const mechanic = (row[1] || "").trim();
        const effect = (row[2] || "").trim();
        if (!className && !mechanic && !effect) return;
        extras.push({ className, mechanic, effect });
      });
      characterState.extras = extras;
    } else if (name.includes("inventory")) {
      const keyItems = [];
      const pokemonItems = [];
      rows.slice(2).forEach((row) => {
        const nameKey = (row[0] || "").trim();
        if (nameKey) {
          keyItems.push({ name: row[0] || "", qty: row[1] || "", cost: row[2] || "", desc: row[3] || "" });
        }
        const namePoke = (row[7] || "").trim();
        if (namePoke) {
          pokemonItems.push({ name: row[7] || "", qty: row[8] || "", cost: row[9] || "", desc: row[10] || "" });
        }
      });
      characterState.inventory = { key_items: keyItems, pokemon_items: pokemonItems };
    }
  }
  saveCharacterToStorage();
  renderCharacterStep();
}

function normalizePokeKey(value) {
  return String(value || "").trim().toLowerCase();
}

function pokeApiCacheGet(cache, key) {
  const normalized = normalizePokeKey(key);
  if (!normalized || !cache.has(normalized)) return null;
  return cache.get(normalized);
}

function pokeApiCacheHas(cache, key) {
  const normalized = normalizePokeKey(key);
  if (!normalized) return false;
  return cache.has(normalized);
}

async function fetchPokeApiMeta(kind, key) {
  const normalized = normalizePokeKey(key);
  if (!normalized) return null;
  const cacheKey = `${kind}:${normalized}`;
  if (pokeApiPending.has(cacheKey)) {
    return pokeApiPending.get(cacheKey);
  }
  const promise = api(`/api/poke/${kind}/${encodeURIComponent(key)}`)
    .then((payload) => (payload && payload.available ? payload : null))
    .catch(() => null)
    .finally(() => pokeApiPending.delete(cacheKey));
  pokeApiPending.set(cacheKey, promise);
  return promise;
}

async function ensureTypeIcon(typeName) {
  const normalized = normalizePokeKey(typeName);
  if (!normalized) return null;
  const cached = pokeApiCacheGet(pokeApiTypeIconCache, normalized);
  if (cached !== null) return cached;
  const payload = await fetchPokeApiMeta("type_icon", normalized);
  const url = payload?.url || null;
  pokeApiTypeIconCache.set(normalized, url);
  return url;
}

async function ensureMoveMeta(moveName) {
  const normalized = normalizePokeKey(moveName);
  if (!normalized) return null;
  const cached = pokeApiCacheGet(pokeApiMoveMetaCache, normalized);
  if (cached !== null) return cached;
  const payload = await fetchPokeApiMeta("move", normalized);
  pokeApiMoveMetaCache.set(normalized, payload || null);
  if (payload?.type && payload?.type_icon_url) {
    pokeApiTypeIconCache.set(normalizePokeKey(payload.type), payload.type_icon_url);
  }
  return payload;
}

async function ensureAbilityMeta(abilityName) {
  const normalized = normalizePokeKey(abilityName);
  if (!normalized) return null;
  const cached = pokeApiCacheGet(pokeApiAbilityMetaCache, normalized);
  if (cached !== null) return cached;
  const payload = await fetchPokeApiMeta("ability", normalized);
  pokeApiAbilityMetaCache.set(normalized, payload || null);
  return payload;
}

async function ensureItemMeta(itemName) {
  const normalized = normalizePokeKey(itemName);
  if (!normalized) return null;
  const cached = pokeApiCacheGet(pokeApiItemMetaCache, normalized);
  if (cached !== null) return cached;
  const payload = await fetchPokeApiMeta("item", normalized);
  pokeApiItemMetaCache.set(normalized, payload || null);
  return payload;
}

async function ensureCryUrl(speciesName) {
  const normalized = normalizePokeKey(speciesName);
  if (!normalized) return null;
  const cached = pokeApiCacheGet(pokeApiCryCache, normalized);
  if (cached !== null) return cached;
  const payload = await fetchPokeApiMeta("cry", speciesName);
  const url = payload?.url || null;
  pokeApiCryCache.set(normalized, url);
  return url;
}

async function ensureMoveAnimAsset(moveName) {
  const normalized = normalizePokeKey(moveName);
  if (!normalized) return null;
  return api(`/api/move_anim/${encodeURIComponent(moveName)}`)
    .then((payload) => {
      return payload && payload.available ? payload.url || null : null;
    })
    .catch(() => {
      return null;
    });
}

function moveAnimUrlFromCache(moveName) {
  return null;
}

function shouldUseNamedMoveAnim(moveMeta, moveAnim) {
  const name = String(moveMeta?.name || "").trim().toLowerCase();
  if (!name) return false;
  if (!SAFE_NAMED_MOVE_SHEETS.has(name)) return false;
  if (NOISY_NAMED_MOVE_SHEETS.has(name)) return false;
  if (moveAnim?.channel === "melee") return false;
  if (name === "confusion" || name === "confuse ray") return false;
  return true;
}

function typeIconFromCache(typeName) {
  return pokeApiCacheGet(pokeApiTypeIconCache, typeName);
}

function statusTypeForIcon(statusName) {
  const value = normalizePokeKey(statusName);
  if (!value) return "";
  if (value.includes("burn")) return "fire";
  if (value.includes("freeze") || value.includes("frost")) return "ice";
  if (value.includes("poison")) return "poison";
  if (value.includes("sleep")) return "psychic";
  if (value.includes("paral")) return "electric";
  if (value.includes("flinch")) return "fighting";
  if (value.includes("confus")) return "psychic";
  if (value.includes("blind")) return "dark";
  if (value.includes("trap") || value.includes("bound")) return "rock";
  return "normal";
}

function statusVisualKey(statusName) {
  const value = normalizePokeKey(statusName);
  if (!value) return "other";
  if (value.includes("burn")) return "burn";
  if (value.includes("freeze") || value.includes("frost")) return "freeze";
  if (value.includes("poison")) return "poison";
  if (value.includes("sleep")) return "sleep";
  if (value.includes("paral")) return "paralyze";
  if (value.includes("confus")) return "confusion";
  if (value.includes("flinch")) return "flinch";
  if (value.includes("blind")) return "blind";
  if (value.includes("trap") || value.includes("bound")) return "trap";
  if (value.includes("vulnerab")) return "vulnerable";
  if (value.includes("trip")) return "tripped";
  if (value.includes("hinder")) return "hindered";
  if (value.includes("grapple")) return "grappled";
  return "other";
}

function _normalizeHazardEntries(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) {
    return raw
      .map((entry) => String(entry || "").trim())
      .filter((entry) => entry)
      .map((name) => ({ name, layers: 1 }));
  }
  if (typeof raw === "object") {
    return Object.entries(raw)
      .map(([name, value]) => {
        const layers = Number(value);
        return { name: String(name || "").trim(), layers: Number.isFinite(layers) ? layers : 1 };
      })
      .filter((entry) => entry.name);
  }
  const name = String(raw || "").trim();
  return name ? [{ name, layers: 1 }] : [];
}

function collectTileHazards(hazards, traps) {
  const entries = [];
  _normalizeHazardEntries(hazards).forEach((entry) => {
    entries.push({ kind: "hazard", name: entry.name, layers: entry.layers });
  });
  _normalizeHazardEntries(traps).forEach((entry) => {
    entries.push({ kind: "trap", name: entry.name, layers: entry.layers });
  });
  return entries;
}

function trapEffectSummary(name) {
  const normalized = normalizePokeKey(name);
  if (normalized === "dust_trap") return "Slowed and Blinded";
  if (normalized === "tangle_trap") return "Stuck";
  if (normalized === "slick_trap") return "Slowed and Vulnerable";
  if (normalized === "abrasion_trap") return "Slowed and -1 Def/-1 SpDef CS";
  if (normalized === "trap") return "Generic trap effect";
  return "";
}

function frozenDomainEntries(meta) {
  return Array.isArray(meta?.frozen_domain) ? meta.frozen_domain : [];
}

function frozenDomainSummary(entry) {
  const dc = Number(entry?.dc || 0);
  const source = String(entry?.source_name || entry?.source_id || "Frozen Domain").trim();
  return `${source}${dc > 0 ? ` (DC ${dc})` : ""}`;
}

function frozenDomainBadgeTitle(entries) {
  const list = Array.isArray(entries) ? entries : [];
  if (!list.length) return "Frozen Domain";
  return `Frozen Domain | ${list.map((entry) => frozenDomainSummary(entry)).join(" | ")} | Effect: Acrobatics check or Tripped. Acts as Hail on this tile. Fire clears it.`;
}

function tileInfoChip(label, value, extraClass = "") {
  return `<span class="tile-info-chip${extraClass ? ` ${extraClass}` : ""}">${escapeHtml(label)}: ${escapeHtml(value)}</span>`;
}

function tileObjectChip(label, titleText = "", extraClass = "") {
  const titleAttr = titleText ? ` title="${escapeAttr(titleText)}"` : "";
  return `<span class="tile-info-chip tile-info-object${extraClass ? ` ${extraClass}` : ""}"${titleAttr}>${escapeHtml(label)}</span>`;
}

function tileGroupHtml(label, chips) {
  const safeChips = Array.isArray(chips) ? chips.filter(Boolean) : [];
  if (!safeChips.length) return "";
  return `
    <div class="tile-info-group">
      <div class="tile-info-group-label">${escapeHtml(label)}</div>
      <div class="tile-info-row">${safeChips.join("")}</div>
    </div>
  `;
}

function scheduleRerender() {
  window.requestAnimationFrame(() => {
    if (!state || state.status !== "ok") return;
    render();
  });
}

function clearTooltipHideTimer() {
  if (tooltipHideTimer) {
    clearTimeout(tooltipHideTimer);
    tooltipHideTimer = null;
  }
}

function hideTooltip() {
  clearTooltipHideTimer();
  tooltipMode = null;
  tooltipAnchor = null;
  tooltipPinned = false;
  if (moveTooltip) {
    moveTooltip.classList.add("hidden");
    moveTooltip.innerHTML = "";
  }
}

function scheduleTooltipHide() {
  clearTooltipHideTimer();
  tooltipHideTimer = setTimeout(() => {
    if (!tooltipPinned) {
      hideTooltip();
    }
  }, TOOLTIP_HIDE_DELAY_MS);
}

function tooltipStatLabel(stat) {
  switch (String(stat || "").toLowerCase()) {
    case "hp_stat":
      return "HP";
    case "atk":
      return "ATK";
    case "defense":
      return "DEF";
    case "spatk":
      return "SpATK";
    case "spdef":
      return "SpDEF";
    case "spd":
      return "SPD";
    default:
      return String(stat || "").toUpperCase();
  }
}

function tooltipHtmlFromText(text) {
  const value = String(text || "").trim();
  if (!value) return "";
  return escapeHtml(value).replaceAll("\n", "<br>");
}

function positionTooltip(anchorEl) {
  if (!moveTooltip || !anchorEl) return;
  if (!anchorEl.isConnected) {
    hideTooltip();
    return;
  }
  const anchorRect = anchorEl.getBoundingClientRect();
  const tipRect = moveTooltip.getBoundingClientRect();
  const gap = 10;
  const edge = 8;
  let left = anchorRect.right + gap;
  if (left + tipRect.width > window.innerWidth - edge) {
    left = anchorRect.left - tipRect.width - gap;
  }
  left = Math.max(edge, Math.min(left, window.innerWidth - tipRect.width - edge));
  let top = anchorRect.top;
  top = Math.max(edge, Math.min(top, window.innerHeight - tipRect.height - edge));
  moveTooltip.style.left = `${Math.round(left)}px`;
  moveTooltip.style.top = `${Math.round(top)}px`;
}

function showTooltipContent(anchorEl, htmlContent, mode = "detail") {
  if (!moveTooltip || !anchorEl || !htmlContent) return;
  clearTooltipHideTimer();
  tooltipPinned = false;
  tooltipMode = mode;
  tooltipAnchor = anchorEl;
  moveTooltip.innerHTML = htmlContent;
  moveTooltip.classList.remove("hidden");
  window.requestAnimationFrame(() => {
    if (!moveTooltip || moveTooltip.classList.contains("hidden")) return;
    positionTooltip(tooltipAnchor);
  });
}

function showDetailTooltip(anchorEl, title, description) {
  const titleText = String(title || "").trim();
  const descriptionHtml = tooltipHtmlFromText(description);
  if (!titleText || !descriptionHtml) {
    return;
  }
  const html = `
    <div class="tooltip-title">${escapeHtml(titleText)}</div>
    <div class="tooltip-section">${descriptionHtml}</div>
  `;
  showTooltipContent(anchorEl, html, "detail");
}

function _setTooltipAttrs(el, title, body) {
  if (!el) return;
  const safeTitle = escapeAttr(title || "");
  const safeBody = escapeAttr(body || "");
  if (!safeTitle || !safeBody) return;
  el.setAttribute("data-tooltip-title", safeTitle);
  el.setAttribute("data-tooltip-body", safeBody);
}

function bindCharacterTooltips() {
  if (!charContentEl) return;
  const targets = charContentEl.querySelectorAll("[data-tooltip-title][data-tooltip-body]");
  targets.forEach((target) => {
    target.addEventListener("mouseenter", () => {
      const title = target.getAttribute("data-tooltip-title") || target.textContent || "Details";
      const body = target.getAttribute("data-tooltip-body") || "";
      showDetailTooltip(target, title, body);
    });
    target.addEventListener("mouseleave", () => {
      scheduleTooltipHide();
    });
  });
}

function escapeRegex(value) {
  return String(value || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function keywordKey(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "");
}

function statusTooltipBody(statusName) {
  const raw = String(statusName || "").trim();
  if (!raw) return "";
  const key = keywordKey(raw);
  if (STATUS_KEYWORD_HELP[key]) return STATUS_KEYWORD_HELP[key];
  if (key.includes("poison")) return STATUS_KEYWORD_HELP.poisoned;
  if (key.includes("burn")) return STATUS_KEYWORD_HELP.burned;
  if (key.includes("paraly")) return STATUS_KEYWORD_HELP.paralyzed;
  if (key.includes("sleep")) return STATUS_KEYWORD_HELP.sleep;
  if (key.includes("freeze") || key.includes("frost")) return STATUS_KEYWORD_HELP.frozen;
  if (key.includes("confus")) return STATUS_KEYWORD_HELP.confused;
  if (key.includes("flinch")) return STATUS_KEYWORD_HELP.flinch;
  return `${raw}: status effect handled by the PTU engine.`;
}

function collectLogTooltipTerms(text, event) {
  const sourceText = String(text || "");
  const lowerText = sourceText.toLowerCase();
  const terms = new Map();
  const addTerm = (label, title, body) => {
    const token = String(label || "").trim();
    const tipBody = String(body || "").trim();
    const tipTitle = String(title || "").trim();
    if (!token || !tipBody || !tipTitle) return;
    if (!lowerText.includes(token.toLowerCase())) return;
    const key = token.toLowerCase();
    if (terms.has(key)) return;
    terms.set(key, { label: token, title: tipTitle, body: tipBody });
  };

  const status = String(event?.status || event?.condition || "").trim();
  if (status) {
    addTerm(status, `Status: ${status}`, statusTooltipBody(status));
  }
  STATUS_LOG_KEYWORDS.forEach((statusLabel) => {
    addTerm(statusLabel, `Status: ${statusLabel}`, statusTooltipBody(statusLabel));
  });

  const ability = String(event?.ability || "").trim();
  if (ability) {
    const meta = pokeApiCacheGet(pokeApiAbilityMetaCache, ability);
    if (!pokeApiCacheHas(pokeApiAbilityMetaCache, ability)) {
      ensureAbilityMeta(ability).then(() => scheduleRerender());
    }
    addTerm(
      ability,
      `Ability: ${ability}`,
      bestEffectDescription(meta, ability, "Ability description unavailable.")
    );
  }

  const move = String(event?.move || event?.move_name || "").trim();
  if (move) {
    const meta = pokeApiCacheGet(pokeApiMoveMetaCache, move);
    if (!pokeApiCacheHas(pokeApiMoveMetaCache, move)) {
      ensureMoveMeta(move).then(() => scheduleRerender());
    }
    const effectText = bestEffectDescription(meta, move, "");
    const summaryText = buildMoveSummary(meta);
    const tooltipBody = effectText || summaryText || "PTU reference text missing. See move details.";
    addTerm(move, `Move: ${move}`, tooltipBody);
  }

  const item = String(event?.item || "").trim();
  if (item) {
    const meta = pokeApiCacheGet(pokeApiItemMetaCache, item);
    if (!pokeApiCacheHas(pokeApiItemMetaCache, item)) {
      ensureItemMeta(item).then(() => scheduleRerender());
    }
    addTerm(item, `Item: ${item}`, meta?.effect || "Item description unavailable.");
  }

  return Array.from(terms.values()).sort((a, b) => b.label.length - a.label.length);
}

function decorateLogText(text, event) {
  const value = String(text || "");
  const terms = collectLogTooltipTerms(value, event);
  if (!terms.length) {
    return formatLogTextSegment(value);
  }
  const lookup = new Map(terms.map((entry) => [entry.label.toLowerCase(), entry]));
  const pattern = new RegExp(terms.map((entry) => escapeRegex(entry.label)).join("|"), "gi");
  let cursor = 0;
  const parts = [];
  for (const match of value.matchAll(pattern)) {
    const offset = Number(match.index ?? 0);
    if (offset > cursor) {
      parts.push(formatLogTextSegment(value.slice(cursor, offset)));
    }
    const token = String(match[0] || "");
    const entry = lookup.get(token.toLowerCase());
    if (entry) {
      parts.push(
        `<span class="log-keyword" data-tooltip-title="${escapeAttr(entry.title)}" data-tooltip-body="${escapeAttr(entry.body)}">${escapeHtml(token)}</span>`
      );
    } else {
      parts.push(formatLogTextSegment(token));
    }
    cursor = offset + token.length;
  }
  if (cursor < value.length) {
    parts.push(formatLogTextSegment(value.slice(cursor)));
  }
  return parts.join("");
}

function formatLogTextSegment(raw) {
  if (!raw) return "";
  const numberPattern = /(\b-?\d+(?:\.\d+)?%?\b|x\d+(?:\.\d+)?)/g;
  const numberToken = /^-?\d+(?:\.\d+)?%?$|^x\d+(?:\.\d+)?$/;
  return String(raw)
    .split(numberPattern)
    .map((part) => {
      if (numberToken.test(part)) {
        return `<span class="log-num">${escapeHtml(part)}</span>`;
      }
      return escapeHtml(part);
    })
    .join("");
}

function bindLogTooltips() {
  const targets = logEl.querySelectorAll(".log-keyword[data-tooltip-title][data-tooltip-body]");
  targets.forEach((target) => {
    target.addEventListener("mouseenter", () => {
      const title = target.getAttribute("data-tooltip-title") || "Log Keyword";
      const body = target.getAttribute("data-tooltip-body") || "";
      showDetailTooltip(target, title, body);
    });
    target.addEventListener("mouseleave", () => {
      scheduleTooltipHide();
    });
  });
}

async function startBattle() {
  if (jsStatusEl) jsStatusEl.textContent = "JS: start click";
  const mode = modeSelect.value;
  const teamSize = Number(teamSizeInput.value || 1);
  const activeSlots = Number(activeSlotsInput.value || 1);
  const sideCount = Math.max(2, Number(sideCountInput?.value || 2));
  const circleInterval = Math.max(1, Number(circleIntervalInput?.value || 3));
  const multiSideRandomMode = mode === "ai-royale" || (mode === "ai-random" && sideCount > 2);
  const minLevel = Number(minLevelInput.value || 20);
  const maxLevel = Number(maxLevelInput.value || 40);
  const payload = {
    team_size: teamSize,
    active_slots: activeSlots,
    min_level: minLevel,
    max_level: maxLevel,
  };
  if (csvStrictModeInput?.checked && !battleRosterCsvText) {
    alertError(new Error("CSV-first strict mode is enabled. Import a roster CSV before starting a battle."));
    return;
  }
  let hasRosterCsv = !!battleRosterCsvText;
  if (!hasRosterCsv && autoUseCreatorRosterInput?.checked) {
    const sourceTrainer = trainerProfileRaw || _readStoredTrainerPayload();
    const modeNeedsTwoSides = mode === "ai" || (mode === "ai-random" && !multiSideRandomMode);
    const includeFoe = modeNeedsTwoSides ? exportRosterMirrorInput?.checked !== false : true;
    const autoRoster = sourceTrainer ? _buildRosterCsvFromTrainerPayload(sourceTrainer, includeFoe) : null;
    if (autoRoster) {
      if (modeNeedsTwoSides && !includeFoe) {
        alertError(new Error("AI vs AI auto-start needs foe rows. Enable 'Mirror to foe on export' or import a full roster CSV."));
        return;
      }
      payload.roster_csv = autoRoster.csvText;
      payload.team_size = Math.max(1, Number(autoRoster.summary.teamSize || teamSize));
      payload.active_slots = Math.max(1, Math.min(Number(payload.active_slots || 1), payload.team_size));
      hasRosterCsv = true;
      notifyUI("info", "Auto-loaded roster from creator team.", 2200);
    }
  }
  if (hasRosterCsv && battleRosterCsvMeta && !payload.roster_csv) {
    payload.team_size = Math.max(1, Number(battleRosterCsvMeta.teamSize || teamSize));
    payload.active_slots = Math.max(1, Math.min(Number(payload.active_slots || 1), payload.team_size));
    payload.roster_csv = battleRosterCsvText;
  }
  if ((mode === "ai" || mode === "ai-random" || mode === "ai-royale") && payload.roster_csv) {
    const stagedSummary = _extractRosterSummary(payload.roster_csv, { allowSingleTeam: true });
    const requiredSides = mode === "ai-royale" ? Math.max(3, sideCount) : mode === "ai-random" ? Math.max(2, sideCount) : 2;
    if (Number(stagedSummary.sideCount || 0) < requiredSides) {
      payload.roster_csv = requiredSides === 2 ? _mirrorRosterCsvToFoe(payload.roster_csv) : _expandRosterCsvToSideCount(payload.roster_csv, requiredSides);
      const mirroredSummary = _extractRosterSummary(payload.roster_csv, { allowSingleTeam: false });
      payload.team_size = Math.max(1, Number(mirroredSummary.teamSize || payload.team_size || teamSize));
      payload.active_slots = Math.max(1, Math.min(Number(payload.active_slots || 1), payload.team_size));
      notifyUI("info", requiredSides === 2 ? "Single-team roster mirrored to foe for AI vs AI." : `Roster expanded to ${requiredSides} sides for AI mode.`, 2400);
    }
  }
  const namedSides = _normalizedSideNameOverrides(sideNameOverrides);
  if (Object.keys(namedSides).length) {
    payload.side_names = namedSides;
  }
  const normalizedDeployment = _normalizeDeploymentPayload();
  if (Object.keys(normalizedDeployment).length) {
    payload.deployment_overrides = normalizedDeployment;
  }
  const normalizedItemChoices = _normalizeItemChoicePayload();
  const normalizedAbilityChoices = _normalizeAbilityChoicePayload();
  if (Object.keys(normalizedItemChoices).length) {
    payload.item_choice_overrides = normalizedItemChoices;
  }
  if (Object.keys(normalizedAbilityChoices).length) {
    payload.ability_choice_overrides = normalizedAbilityChoices;
  }
  if (mode === "random" && !hasRosterCsv) {
    payload.random_battle = true;
  } else if (mode === "ai") {
    payload.ai_mode = "ai";
    payload.step_ai = true;
  } else if (mode === "ai-random") {
    payload.ai_mode = "ai";
    payload.step_ai = true;
    payload.side_count = sideCount;
    payload.random_battle = true;
  } else if (mode === "ai-royale") {
    payload.ai_mode = "ai";
    payload.step_ai = true;
    payload.random_battle = true;
    payload.battle_royale = true;
    payload.side_count = Math.max(3, sideCount);
    payload.circle_interval = circleInterval;
  }
  if (hasRosterCsv && (mode === "random" || mode === "ai-random" || mode === "ai-royale") && !multiSideRandomMode) {
    notifyUI("info", "Roster CSV loaded: random generation disabled for this start.", 2600);
  }
  if (useTrainerInput?.checked) {
    if (!trainerProfileRaw) {
      alertError(new Error("Enable Use Trainer only after loading a trainer profile."));
      return;
    }
    payload.trainer_profile = trainerProfileRaw;
  }
  if (stepByStepStartToggle?.checked) {
    const modeLabel = modeSelect.value;
    const trainerLabel = useTrainerInput?.checked ? "On" : "Off";
    const rosterLabel = hasRosterCsv
      ? `Loaded (${battleRosterCsvMeta?.players || 0}P/${battleRosterCsvMeta?.foes || 0}F)`
      : "Off";
    if (!confirm(`Step 1/3\nMode: ${modeLabel}\nContinue?`)) return;
    if (!confirm(`Step 2/3\nTeam size: ${teamSize}\nActive slots: ${activeSlots}\nContinue?`)) return;
    if (!confirm(`Step 3/3\nMin Level: ${minLevel}\nMax Level: ${maxLevel}\nUse Trainer: ${trainerLabel}\nRoster CSV: ${rosterLabel}\nStart battle?`)) return;
  }
  lastBattlePayload = { ...payload };
  saveSettings();
  state = await api("/api/battle/new", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  selectedId = state.current_actor_id || null;
  armedMove = null;
  clearArmedTileAction();
  viewManuallyAdjusted = false;
  lastGridSize = null;
  lastProcessedLogSize = null;
  lastProcessedLogToken = "";
  lastBattleResultToken = "";
  logClearOffset = 0;
  fxQueue = Promise.resolve();
  closeBattleResultModal();
  hideTooltip();
  render();
}

async function stopBattle() {
  if (autoTimer) {
    clearInterval(autoTimer);
    autoTimer = null;
  }
  const response = await api("/api/battle/stop", { method: "POST", body: JSON.stringify({}) });
  const result = response?.result || null;
  const copy = stoppedBattleResultCopy(result);
  const detailRows = [];
  const teamSummary = result?.team_summary && typeof result.team_summary === "object" ? result.team_summary : {};
  Object.entries(teamSummary).forEach(([team, summary]) => {
    if (!summary || typeof summary !== "object") return;
    detailRows.push(
      `${formatTeamLabel(team)}: ${Number(summary.active || 0)} remaining, ${Number(summary.fainted || 0)} fainted, ${Number(summary.remaining_hp || 0)} HP left`
    );
  });
  state = null;
  selectedId = null;
  armedMove = null;
  clearArmedTileAction();
  viewManuallyAdjusted = false;
  lastGridSize = null;
  lastProcessedLogSize = null;
  lastProcessedLogToken = "";
  lastBattleResultToken = "";
  render();
  openBattleResultModal(copy.title, copy.body, detailRows);
  if (response?.battle_log_path) {
    notifyUI("ok", `Battle stopped. Log saved to ${response.battle_log_path}`, 3200);
  } else {
    notifyUI("ok", "Battle stopped.", 2200);
  }
}

async function refreshState() {
  state = await api("/api/state");
  if (!selectedId && state.current_actor_id) {
    selectedId = state.current_actor_id;
  }
  render();
}

async function commitAction(payload) {
  state = await api("/api/action", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  armedMove = null;
  clearArmedTileAction();
  gimmickState = {
    mega_evolve: false,
    dynamax: false,
    z_move: false,
    teracrystal: false,
    tera_type: "",
  };
  render();
}

async function endTurn() {
  state = await api("/api/end_turn", { method: "POST" });
  armedMove = null;
  clearArmedTileAction();
  render();
}

async function aiStep(silent = false) {
  if (aiStepInFlight) return;
  if (!state || state.mode !== "ai") {
    if (!silent) {
      alertError(new Error("AI Step requires an AI vs AI battle. Start one from the mode selector."));
    }
    if (autoTimer) {
      clearInterval(autoTimer);
      autoTimer = null;
      applyBattleLifecycleControls();
    }
    return;
  }
  aiStepInFlight = true;
  try {
    if (isCinematicAutoActive()) {
      await ensureCinematicActorFocus();
    }
    state = await api("/api/ai/step", { method: "POST" });
    if (state?.warning === "Not in AI vs AI mode.") {
      if (autoTimer) {
        clearInterval(autoTimer);
        autoTimer = null;
        applyBattleLifecycleControls();
      }
      await refreshState();
      if (!silent) {
        alertError(new Error("Battle is no longer in AI vs AI mode."));
      }
      return;
    }
    render();
  } catch (err) {
    const message = String(err?.message || err || "");
    if (message.includes("Not in AI vs AI mode")) {
      if (autoTimer) {
        clearInterval(autoTimer);
        autoTimer = null;
        applyBattleLifecycleControls();
      }
      await refreshState().catch(() => {});
      if (!silent) {
        alertError(new Error("Battle is no longer in AI vs AI mode."));
      }
      return;
    }
    throw err;
  } finally {
    aiStepInFlight = false;
  }
}

async function undoStep() {
  state = await api("/api/undo", { method: "POST" });
  render();
}

function toggleAuto() {
  if (!state || state.mode !== "ai") {
    alertError(new Error("Auto only works in AI vs AI mode. Start an AI vs AI battle first."));
    return;
  }
  if (autoTimer) {
    clearInterval(autoTimer);
    autoTimer = null;
    applyBattleLifecycleControls();
    return;
  }
  const interval = Math.max(250, Number(autoIntervalInput.value || 1000));
  autoTimer = setInterval(() => {
    if (isCinematicAutoActive() && (pendingAnimationJobs > 0 || cinematicCameraBusy || cinematicPhaseActive)) {
      return;
    }
    if (aiStepInFlight) return;
    aiStep(true).catch(() => {});
  }, interval);
  applyBattleLifecycleControls();
}
async function resolvePrompts() {
  state = await api("/api/prompts/resolve", {
    method: "POST",
    body: JSON.stringify({ answers: promptAnswers }),
  });
  promptAnswers = {};
  armedMove = null;
  clearArmedTileAction();
  render();
}

async function downloadSprites() {
  await api("/api/sprites/download_all", { method: "POST" });
  await refreshSpriteStatus();
}

async function refreshSpriteStatus() {
  try {
    const status = await api("/api/sprites/status");
    const done = status.done || 0;
    const total = status.total || 0;
    const errors = status.errors || 0;
    const completed = status.completed ?? done + errors;
    if (completed > lastSpriteCompleted) {
      lastSpriteCompleted = completed;
      spriteMissUntil.clear();
    }
    const stateLabel = status.complete ? "done" : status.state;
    const errorLabel = errors ? ` (errors ${errors})` : "";
    spriteStatusEl.textContent = `Sprites: ${stateLabel} ${completed}/${total}${errorLabel}`;
    if (!autoSpriteStarted && (status.state === "idle" || status.state === "error")) {
      autoSpriteStarted = true;
      await api("/api/sprites/download_all", { method: "POST" });
      const next = await api("/api/sprites/status");
      const nextDone = next.done || 0;
      const nextErrors = next.errors || 0;
      const nextTotal = next.total || 0;
      const nextCompleted = next.completed ?? nextDone + nextErrors;
      const nextState = next.complete ? "done" : next.state;
      const nextErrorLabel = nextErrors ? ` (errors ${nextErrors})` : "";
      spriteStatusEl.textContent = `Sprites: ${nextState} ${nextCompleted}/${nextTotal}${nextErrorLabel}`;
    }
  } catch {
    spriteStatusEl.textContent = "Sprites: error";
  }
}

function normalizeTeamLabel(value) {
  const raw = String(value || "neutral").trim().toLowerCase();
  if (!raw) return "neutral";
  if (raw.includes("player")) return "player";
  if (raw.includes("foe") || raw.includes("enemy") || raw.includes("rival")) return "foe";
  return raw.replace(/[^a-z0-9_-]/g, "");
}

function teamKeyForCombatant(combatant) {
  return normalizeTeamLabel(combatant?.team || combatant?.trainer || "neutral");
}

function trainersForTeam(teamLabel) {
  const normalized = normalizeTeamLabel(teamLabel);
  return Array.isArray(state?.trainers)
    ? state.trainers.filter((trainer) => normalizeTeamLabel(trainer?.team || trainer?.id) === normalized)
    : [];
}

function friendlySideLabel(teamLabel) {
  const normalized = normalizeTeamLabel(teamLabel);
  const trainerNames = trainersForTeam(normalized)
    .map((trainer) => String(trainer?.name || "").trim())
    .filter((name) => {
      if (!name) return false;
      const normalizedName = normalizeTeamLabel(name);
      return normalizedName !== normalized && normalizedName !== "neutral";
    });
  if (trainerNames.length) {
    return trainerNames.join(" / ");
  }
  if (sideNameOverrides[normalized]) {
    return String(sideNameOverrides[normalized]);
  }
  if (normalized === "player") return "Your Team";
  if (normalized === "foe") return "Opposing Team";
  return null;
}

function hashLabel(label) {
  let hash = 0;
  for (let i = 0; i < label.length; i += 1) {
    hash = (hash * 31 + label.charCodeAt(i)) >>> 0;
  }
  return hash;
}

function getTeamVisual(teamLabel) {
  const normalized = normalizeTeamLabel(teamLabel);
  if (TEAM_PRESETS[normalized]) {
    return TEAM_PRESETS[normalized];
  }
  const fallback = TEAM_COLOR_WHEEL[hashLabel(normalized) % TEAM_COLOR_WHEEL.length];
  return {
    ...TEAM_PRESETS.neutral,
    primary: fallback.primary,
    secondary: fallback.secondary,
    track: "rgba(99, 140, 199, 0.28)",
  };
}

function healthGradient(teamVisual, ratio) {
  if (ratio <= 0.25) {
    return `linear-gradient(90deg, ${teamVisual.danger}, #f7a6a6)`;
  }
  if (ratio <= 0.5) {
    return `linear-gradient(90deg, ${teamVisual.warning}, #f6d28d)`;
  }
  return `linear-gradient(90deg, ${teamVisual.primary}, ${teamVisual.secondary})`;
}

function formatTeamLabel(teamLabel) {
  const friendly = friendlySideLabel(teamLabel);
  if (friendly) return friendly;
  return String(teamLabel || "neutral")
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function escapeRegExp(value) {
  return String(value || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function normalizeRefKey(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "");
}

function findCombatantByRef(value) {
  if (!value || !Array.isArray(state?.combatants)) return null;
  const raw = String(value || "").trim();
  if (!raw) return null;
  const exact = state.combatants.find((combatant) => combatant.id === raw);
  if (exact) return exact;
  const normalized = normalizeRefKey(raw);
  if (!normalized) return null;
  return (
    state.combatants.find((combatant) => normalizeRefKey(combatant?.id) === normalized) ||
    state.combatants.find((combatant) => normalizeRefKey(combatant?.name) === normalized) ||
    null
  );
}

function findTrainerByRef(value) {
  if (!value || !Array.isArray(state?.trainers)) return null;
  const raw = String(value || "").trim();
  if (!raw) return null;
  const exact = state.trainers.find((trainer) => trainer.id === raw);
  if (exact) return exact;
  const normalized = normalizeRefKey(raw);
  if (!normalized) return null;
  return (
    state.trainers.find((trainer) => normalizeRefKey(trainer?.id) === normalized) ||
    state.trainers.find((trainer) => normalizeRefKey(trainer?.name) === normalized) ||
    null
  );
}

function prettifyCombatReference(text) {
  let next = String(text || "");
  const combatants = Array.isArray(state?.combatants)
    ? [...state.combatants].sort((a, b) => String(b?.id || "").length - String(a?.id || "").length)
    : [];
  combatants.forEach((combatant) => {
    const id = String(combatant?.id || "").trim();
    const name = String(combatant?.name || "").trim();
    if (!id || !name) return;
    const pattern = id
      .split(/[-_\s]+/)
      .filter(Boolean)
      .map((part) => escapeRegExp(part))
      .join("[-_\\s]*");
    if (!pattern) return;
    next = next.replace(new RegExp(`\\b${pattern}\\b`, "gi"), name);
  });
  next = next.replace(/\bplayer\b/gi, friendlySideLabel("player") || "Your Team");
  next = next.replace(/\bfoe\b/gi, friendlySideLabel("foe") || "Opposing Team");
  return next;
}

function initialsFor(name) {
  const value = String(name || "?").trim();
  if (!value) return "?";
  const parts = value.split(/\s+/).filter(Boolean);
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  return `${parts[0][0] || ""}${parts[1][0] || ""}`.toUpperCase();
}

function syncSpectatorStateChips() {
  if (sidebarRoundInfoEl && roundInfoEl) {
    sidebarRoundInfoEl.textContent = roundInfoEl.textContent || "Round -";
  }
  if (sidebarTerrainInfoEl && terrainInfoEl) {
    sidebarTerrainInfoEl.textContent = terrainInfoEl.textContent || "Terrain: -";
  }
  if (sidebarWeatherInfoEl && weatherInfoEl) {
    sidebarWeatherInfoEl.textContent = weatherInfoEl.textContent || "Weather: -";
  }
}

function normalizeMoveType(typeName) {
  return String(typeName || "").trim().toLowerCase();
}

function moveMetaFromEvent(event) {
  if (!event || typeof event !== "object") return null;
  const moveName = String(event.move || event.move_name || "").trim();
  const actor = combatantFromEventRef(event.actor ?? event.actor_id ?? event.source);
  if (!actor || !moveName) return null;
  const match = (actor.moves || []).find(
    (move) => String(move?.name || "").trim().toLowerCase() === moveName.toLowerCase()
  );
  return match || null;
}

function vfxPaletteForEvent(event, fallbackVisual) {
  const moveMeta = moveMetaFromEvent(event);
  const typeKey = normalizeMoveType(moveMeta?.type);
  const typeVisual = TYPE_VFX[typeKey];
  if (typeVisual) {
    return {
      ...typeVisual,
      category: String(moveMeta?.category || "").trim().toLowerCase(),
      typeKey,
      label: typeKey || "move",
    };
  }
  return {
    primary: fallbackVisual.primary,
    secondary: fallbackVisual.secondary,
    glyph: "â—‡",
    category: String(moveMeta?.category || "").trim().toLowerCase(),
    typeKey: "neutral",
    label: "move",
  };
}

function resolveMoveChannel(moveMeta) {
  const category = String(moveMeta?.category || "").trim().toLowerCase();
  if (category === "status") {
    return "status";
  }
  const raw = `${moveMeta?.range || ""} ${moveMeta?.target || ""}`.toLowerCase();
  if (raw.includes("melee")) {
    return "melee";
  }
  return "ranged";
}

function moveAnimationProfile(moveMeta, palette) {
  const typeKey = normalizeMoveType(moveMeta?.type || palette?.typeKey || "neutral");
  const moveName = String(moveMeta?.name || "").trim().toLowerCase();
  let style = TYPE_ANIM_STYLE[typeKey] || "pulse";
  if (EXACT_MOVE_STYLE_OVERRIDES[moveName]) {
    style = EXACT_MOVE_STYLE_OVERRIDES[moveName];
  } else if (/(kick|punch|tackle|slam|headbutt|stomp|bash|crash)/.test(moveName)) {
    style = "impact";
  } else if (/(slash|claw|cut|wing|rend|scythe|slice|leaf blade|x-scissor)/.test(moveName)) {
    style = "slash";
  } else if (/(beam)/.test(moveName)) {
    style = typeKey === "ice" ? "frost" : typeKey === "electric" ? "spark" : typeKey === "grass" ? "gleam" : typeKey === "psychic" ? "psy" : typeKey === "dragon" ? "draco" : typeKey === "dark" ? "shadow" : typeKey === "water" ? "wave" : typeKey === "fire" ? "flame" : "pulse";
  } else if (/(pulse|ball|orb)/.test(moveName)) {
    style = typeKey === "dragon" ? "draco" : typeKey === "dark" || typeKey === "ghost" ? "shadow" : typeKey === "water" ? "wave" : typeKey === "electric" ? "spark" : typeKey === "psychic" ? "psy" : "pulse";
  } else if (/(confus|psy|telekinesis|hypnosis|dream eater)/.test(moveName)) {
    style = moveName.includes("confus") ? "mind" : "psy";
  }
  return {
    typeKey: typeKey || "neutral",
    style,
    channel: resolveMoveChannel(moveMeta),
  };
}

function shouldRequestSprite(url) {
  if (!url) return false;
  const until = spriteMissUntil.get(url);
  if (!until) return true;
  if (Date.now() >= until) {
    spriteMissUntil.delete(url);
    return true;
  }
  return false;
}

function configureSpriteSheet(wrap, img) {
  const width = Number(img.naturalWidth || 0);
  const height = Number(img.naturalHeight || 0);
  if (!width || !height || width <= height * 1.25) {
    return;
  }
  const frameCount = Math.max(1, Math.round(width / height));
  if (frameCount <= 1) {
    return;
  }
  const durationMs = Math.max(900, Math.min(7000, frameCount * 90));
  wrap.classList.add("sprite-sheet");
  img.classList.add("sprite-sheet-image");
  wrap.style.setProperty("--sheet-frames", String(frameCount));
  wrap.style.setProperty("--sheet-travel", `${((frameCount - 1) / frameCount) * 100}%`);
  img.style.animation = `spriteSheetAdvance ${durationMs}ms steps(${frameCount}) infinite`;
}

function attachSprite(container, url, alt) {
  if (!shouldRequestSprite(url)) {
    return false;
  }
  const wrap = document.createElement("div");
  wrap.className = "token-sprite-wrap";
  const img = document.createElement("img");
  img.className = "token-sprite";
  img.src = url;
  img.alt = alt || "sprite";
  img.addEventListener(
    "load",
    () => {
      configureSpriteSheet(wrap, img);
      wrap.classList.add("loaded");
    },
    { once: true }
  );
  img.addEventListener(
    "error",
    () => {
      spriteMissUntil.set(url, Date.now() + SPRITE_RETRY_MS);
      wrap.remove();
    },
    { once: true }
  );
  wrap.appendChild(img);
  container.appendChild(wrap);
  return true;
}

function attachTurnSprite(container, url, alt) {
  container.classList.add("placeholder");
  if (!url || !shouldRequestSprite(url)) {
    return false;
  }
  const wrap = document.createElement("div");
  wrap.className = "turn-sprite-wrap";
  const img = document.createElement("img");
  img.className = "turn-sprite";
  img.src = url;
  img.alt = alt || "sprite";
  img.addEventListener(
    "error",
    () => {
      spriteMissUntil.set(url, Date.now() + SPRITE_RETRY_MS);
      wrap.remove();
      container.classList.add("placeholder");
    },
    { once: true }
  );
  img.addEventListener(
    "load",
    () => {
      configureSpriteSheet(wrap, img);
      wrap.classList.add("loaded");
      container.classList.remove("placeholder");
    },
    { once: true }
  );
  wrap.appendChild(img);
  container.appendChild(wrap);
  return true;
}

function spawnPokemonMovementGhost(actor, fromCoord, toCoord) {
  if (!actor?.sprite_url || !fromCoord || !toCoord) return 0;
  const fromCell = gridCellByKey.get(coordKey(fromCoord));
  const toCell = gridCellByKey.get(coordKey(toCoord));
  if (!fromCell || !toCell) return 0;
  const fromRect = fromCell.getBoundingClientRect();
  const toRect = toCell.getBoundingClientRect();
  const size = Math.round(Math.max(54, Math.min(92, fromRect.width * 0.9)));
  const ghost = document.createElement("div");
  ghost.className = "fx-pokemon-move";
  ghost.style.width = `${size}px`;
  ghost.style.height = `${size}px`;
  ghost.style.left = `${Math.round(fromRect.left + fromRect.width / 2)}px`;
  ghost.style.top = `${Math.round(fromRect.top + fromRect.height / 2)}px`;
  const wrap = document.createElement("div");
  wrap.className = "token-sprite-wrap loaded";
  const img = document.createElement("img");
  img.className = "token-sprite";
  img.src = actor.sprite_url;
  img.alt = actor.name || actor.species || "sprite";
  img.addEventListener(
    "load",
    () => {
      configureSpriteSheet(wrap, img);
    },
    { once: true }
  );
  wrap.appendChild(img);
  ghost.appendChild(wrap);
  document.body.appendChild(ghost);
  const durationMs = 340;
  const dx = Math.round((toRect.left + toRect.width / 2) - (fromRect.left + fromRect.width / 2));
  const dy = Math.round((toRect.top + toRect.height / 2) - (fromRect.top + fromRect.height / 2));
  requestAnimationFrame(() => {
    ghost.style.setProperty("--move-dx", `${dx}px`);
    ghost.style.setProperty("--move-dy", `${dy}px`);
    ghost.classList.add("active");
  });
  toCell.classList.remove("fx-token-arrive");
  void toCell.offsetWidth;
  toCell.classList.add("fx-token-arrive");
  window.setTimeout(() => {
    ghost.remove();
    toCell.classList.remove("fx-token-arrive");
  }, durationMs + 180);
  return durationMs;
}

function closeBattleResultModal() {
  if (!battleResultModal) return;
  battleResultModal.remove();
  battleResultModal = null;
}

async function clearBattleAndRoster() {
  try {
    await api("/api/battle/clear", { method: "POST", body: JSON.stringify({}) });
  } catch {
    // If the engine is already empty, keep clearing local state.
  }
  state = null;
  selectedId = null;
  armedMove = null;
  clearArmedTileAction();
  closeBattleResultModal();
  lastBattleResultToken = "";
  _clearBattleRosterCsv();
  render();
  saveSettings();
  notifyUI("ok", "Battle and roster cleared.", 2200);
}

function battleResultToken() {
  if (!state?.battle_over) return "";
  const alive = Array.isArray(state?.alive_teams) ? state.alive_teams.join("|") : "";
  return [state.winner_team || "draw", state.round || 0, alive].join("::");
}

function battleResultCopy() {
  if (!state?.battle_over) {
    return { title: "", body: "" };
  }
  if (!state.winner_team) {
    return {
      title: "Battle Finished",
      body: "All remaining teams were knocked out. The battle ends in a draw.",
    };
  }
  const winnerLabel = state.winner_label || formatTeamLabel(state.winner_team);
  return {
    title: state.winner_is_player ? "Victory" : "Battle Finished",
    body: `${winnerLabel} won the battle.`,
  };
}

function stoppedBattleResultCopy(result) {
  if (!result) {
    return {
      title: "Battle Stopped",
      body: "The battle was stopped.",
    };
  }
  const round = Number(result.round || 0);
  const aliveTeams = Array.isArray(result.alive_teams) ? result.alive_teams : [];
  const winnerLabel = result.winner_label || formatTeamLabel(result.winner_team);
  if (result.battle_over) {
    if (winnerLabel) {
      return {
        title: "Battle Finished",
        body: `${winnerLabel} won the battle on round ${round}.`,
      };
    }
    return {
      title: "Battle Finished",
      body: `The battle ended in a draw on round ${round}.`,
    };
  }
  const survivors = aliveTeams.length ? aliveTeams.map((team) => formatTeamLabel(team)).join(", ") : "none";
  return {
    title: "Battle Stopped",
    body: `Stopped on round ${round}. Remaining teams: ${survivors}.`,
  };
}

function openBattleResultModal(title, body, detailRows = []) {
  closeBattleResultModal();
  const modal = document.createElement("div");
  modal.className = "char-connection-modal";
  const box = document.createElement("div");
  box.className = "char-connection-box";
  const heading = document.createElement("div");
  heading.className = "char-section-title";
  heading.textContent = title || "Battle Finished";
  const message = document.createElement("div");
  message.className = "char-feature-meta";
  message.textContent = body || "The battle is over.";
  const actions = document.createElement("div");
  actions.className = "char-action-row";
  const close = document.createElement("button");
  close.type = "button";
  close.textContent = "Close";
  close.addEventListener("click", closeBattleResultModal);
  actions.appendChild(close);
  box.appendChild(heading);
  box.appendChild(message);
  detailRows.forEach((line) => {
    const detail = document.createElement("div");
    detail.className = "char-feature-meta";
    detail.textContent = String(line || "");
    box.appendChild(detail);
  });
  box.appendChild(actions);
  modal.appendChild(box);
  modal.addEventListener("click", (event) => {
    if (event.target === modal) closeBattleResultModal();
  });
  document.body.appendChild(modal);
  battleResultModal = modal;
}

function maybeShowBattleResultModal() {
  if (!state?.battle_over) return;
  const token = battleResultToken();
  if (!token || token === lastBattleResultToken) return;
  lastBattleResultToken = token;
  const { title, body } = battleResultCopy();
  openBattleResultModal(title, body, []);
  if (battleResultModal) {
    const actions = battleResultModal.querySelector(".char-action-row");
    if (actions) {
      const clear = document.createElement("button");
      clear.type = "button";
      clear.textContent = "Clear Battle";
      clear.addEventListener("click", () => clearBattleAndRoster().catch(alertError));
      actions.appendChild(clear);
    }
  }
}

function applyBattleLifecycleControls() {
  const lifecycle = window.PTUBattleUI?.computeLifecycle
    ? window.PTUBattleUI.computeLifecycle(state, { autoActive: !!autoTimer })
    : {
        hasBattle: !!state && state.status === "ok",
        canStartBattle: !autoTimer,
        canEndTurn: !!state?.current_actor_is_player,
        canAiStep: state?.mode === "ai",
        canToggleAuto: state?.mode === "ai",
        canUndo: !!state && state.status === "ok",
        autoActive: !!autoTimer,
      };
  if (window.PTUBattleUI?.applyLifecycleControls) {
    window.PTUBattleUI.applyLifecycleControls(
      { startButton, endTurnButton, aiStepButton, aiAutoButton, undoButton },
      lifecycle
    );
  } else {
    startButton.disabled = lifecycle.hasBattle ? false : !lifecycle.canStartBattle;
    endTurnButton.disabled = !lifecycle.canEndTurn;
    aiStepButton.disabled = !lifecycle.canAiStep;
    aiAutoButton.disabled = !lifecycle.canToggleAuto;
    undoButton.disabled = !lifecycle.canUndo;
    aiAutoButton.textContent = lifecycle.autoActive ? "Auto On" : "Auto Off";
  }
  if (startButton) {
    startButton.textContent = lifecycle.hasBattle ? "Stop Battle" : "Start Battle";
  }
  return lifecycle;
}

function renderAiModelMath(source) {
  if (!aiModelMathEl) return;
  const math = source?.math || source?.ai_model?.math || null;
  const selectedAnalysis = source?.selected_analysis || source?.ai_model?.selected_analysis || null;
  if (!math) {
    aiModelMathEl.textContent = "Model score: -";
    return;
  }
  const score = Number.isFinite(Number(math.score)) ? Number(math.score).toFixed(3) : "-";
  const threshold = Number.isFinite(Number(math.threshold)) ? Number(math.threshold).toFixed(3) : "-";
  const updates = Number.isFinite(Number(math.updates_since_snapshot)) ? Number(math.updates_since_snapshot) : 0;
  const style = Array.isArray(selectedAnalysis?.styles) && selectedAnalysis.styles.length ? ` | ${selectedAnalysis.styles[0]}` : "";
  aiModelMathEl.textContent = `Model score: ${score}/${threshold} | updates ${updates}${style}`;
}

function applyAiModelSelectionFromPayload(payload) {
  if (!aiModelSelect) return;
  const models = Array.isArray(payload?.models) ? payload.models : [];
  const currentId = String(payload?.current_model_id || "");
  aiModelSelect.innerHTML = "";
  models.forEach((model) => {
    const option = document.createElement("option");
    option.value = String(model.id || "");
    const tag = model.auto_created ? "auto" : "manual";
    const conservative = Number.isFinite(Number(model?.rating?.conservative))
      ? ` | ${Number(model.rating.conservative).toFixed(1)}`
      : "";
    option.textContent = `${model.id} (${tag}${conservative})`;
    aiModelSelect.appendChild(option);
  });
  if (models.length) {
    aiModelSelect.value = currentId || String(models[0].id || "");
  } else {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No models";
    aiModelSelect.appendChild(option);
    aiModelSelect.value = "";
  }
  renderAiModelMath(payload);
}

async function refreshAiModels(preferredModelId = "") {
  if (!aiModelSelect) return;
  let payload = null;
  try {
    payload = await api("/api/ai/models");
  } catch (err) {
    const message = String(err?.message || err || "");
    if (message.includes("404")) {
      aiModelSelect.innerHTML = "";
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "Server missing /api/ai/models";
      aiModelSelect.appendChild(option);
      aiModelSelect.value = "";
      if (aiModelMathEl) aiModelMathEl.textContent = "Model score: endpoint unavailable";
      return;
    }
    throw err;
  }
  aiModelsCache = payload;
  applyAiModelSelectionFromPayload(payload);
  if (preferredModelId && Array.isArray(payload?.models) && payload.models.some((entry) => entry.id === preferredModelId)) {
    aiModelSelect.value = preferredModelId;
  }
}

async function selectAiModel(modelId) {
  if (!modelId) return;
  const payload = await api("/api/ai/models/select", {
    method: "POST",
    body: JSON.stringify({ model_id: modelId }),
  });
  aiModelsCache = payload;
  applyAiModelSelectionFromPayload(payload);
  notifyUI("ok", `Selected AI model: ${modelId}`, 1800);
}

function render() {
  renderSideNameEditor();
  if (!state || state.status !== "ok") {
    closeBattleResultModal();
    lastBattleResultToken = "";
    hideTooltip();
    gridEl.innerHTML = "";
    gridCellByKey = new Map();
    detailsEl.textContent = "No battle loaded.";
    renderTrainerDetails();
    renderAIDiagnostics();
    moveListEl.innerHTML = "";
    logEl.innerHTML = "";
    if (turnOrderBarEl) turnOrderBarEl.innerHTML = "";
    lastProcessedLogSize = null;
    lastProcessedLogToken = "";
    fxQueue = Promise.resolve();
    roundInfoEl.textContent = "Round -";
    if (terrainInfoEl) {
      terrainInfoEl.textContent = "Terrain: -";
    }
    if (weatherInfoEl) {
      weatherInfoEl.textContent = "Weather: -";
    }
    if (mapSeedEl) {
      mapSeedEl.textContent = "Seed: -";
    }
    syncSpectatorStateChips();
    applyBattleLifecycleControls();
    if (centerCurrentButton) centerCurrentButton.disabled = true;
    if (centerSelectedButton) centerSelectedButton.disabled = true;
    lastTurnActorId = null;
    lastCinematicActorId = null;
    cinematicCameraBusy = false;
    cinematicCameraJob = Promise.resolve();
    aiStepInFlight = false;
    cinematicPhaseActive = false;
    pendingAnimationJobs = 0;
    lastRenderedPositions = new Map();
    syncStatusTabs();
    renderCombatants();
    renderPartyBar();
    return;
  }
  if (autoTimer && state.mode !== "ai") {
    clearInterval(autoTimer);
    autoTimer = null;
    applyBattleLifecycleControls();
  }
  const lifecycle = applyBattleLifecycleControls();
  updateCinematicPerfLabel();
  if (lifecycle.promptLocked) {
    notifyUI("warn", lifecycle.reason || "Resolve pending prompts before continuing.", 2200);
  }
  if (terrainInfoEl) {
    const terrain = state.terrain;
    const label = normalizeFieldName(terrainNameValue(terrain)) || "None";
    terrainInfoEl.textContent = `Terrain: ${label}`;
    terrainInfoEl.onmouseenter = () => {
      showDetailTooltip(terrainInfoEl, "Terrain", terrainTooltipBody(terrain));
    };
    terrainInfoEl.onmouseleave = () => {
      scheduleTooltipHide();
    };
  }
  if (weatherInfoEl) {
    const weather = normalizeFieldName(state.weather) || "Clear";
    weatherInfoEl.textContent = `Weather: ${weather}`;
    weatherInfoEl.onmouseenter = () => {
      showDetailTooltip(weatherInfoEl, "Weather", weatherTooltipBody(state.weather));
    };
    weatherInfoEl.onmouseleave = () => {
      scheduleTooltipHide();
    };
  }
  if (mapSeedEl) {
    const seedValue = Number.isFinite(Number(state.seed)) ? String(state.seed) : "-";
    mapSeedEl.textContent = `Seed: ${seedValue}`;
  }
  if (centerCurrentButton) {
    const current = (state.combatants || []).find((entry) => entry.id === state.current_actor_id);
    centerCurrentButton.disabled = !current?.position;
  }
  if (centerSelectedButton) {
    const selected = (state.combatants || []).find((entry) => entry.id === selectedId);
    centerSelectedButton.disabled = !selected?.position;
  }
  roundInfoEl.textContent = `Round ${state.round} | ${state.phase || "-"}`;
  syncSpectatorStateChips();
  if (autoCriesToggle?.checked && state.current_actor_id && state.current_actor_id !== lastTurnActorId) {
    const current = (state.combatants || []).find((combatant) => combatant.id === state.current_actor_id);
    if (current) {
      playCryForSpecies(current.species || current.name).catch(() => {});
    }
  }
  lastTurnActorId = state.current_actor_id || null;
  renderGrid();
  applyCinematicTurnCamera();
  renderTurnOrder();
  syncStatusTabs();
  renderCombatants();
  renderDetails();
  renderTrainerDetails();
  renderAIDiagnostics();
  renderPartyBar();
  renderMoves();
  renderLog();
  renderPrompts();
  processMoveAnimations();
  maybeShowBattleResultModal();
  lastRenderedPositions = captureCombatantPositions();
}

function renderGrid() {
  const grid = state.grid;
  if (!grid) {
    gridEl.innerHTML = "<div>No grid</div>";
    gridCellByKey = new Map();
    return;
  }
  const gridSize = `${grid.width}x${grid.height}`;
  if (gridSize !== lastGridSize) {
    lastGridSize = gridSize;
    viewManuallyAdjusted = false;
  }
  const cellSize = GRID_CELL_SIZE;
  gridEl.style.gridTemplateColumns = `repeat(${grid.width}, ${cellSize}px)`;
  gridEl.style.gridTemplateRows = `repeat(${grid.height}, ${cellSize}px)`;
  const expectedCells = grid.width * grid.height;
  if (gridCellByKey.size !== expectedCells) {
    gridEl.innerHTML = "";
    gridCellByKey = new Map();
    for (let y = 0; y < grid.height; y += 1) {
      for (let x = 0; x < grid.width; x += 1) {
        const key = `${x},${y}`;
        const cell = document.createElement("div");
        cell.className = "cell";
        cell.dataset.x = String(x);
        cell.dataset.y = String(y);
        cell.addEventListener("mouseenter", () => {
          if (selectedTileKey !== key) return;
          const meta = lastTileMeta.get(key) || {};
          showDetailTooltip(cell, "Tile Info", buildTileTooltip(meta, x, y));
        });
        cell.addEventListener("mouseleave", () => {
          if (selectedTileKey !== key) return;
          scheduleTooltipHide();
        });
        cell.addEventListener("mousedown", (event) => {
          if (armedTileAction !== "trapper" && armedTileAction !== "frozen_domain") return;
          if (event.button !== 0) return;
          event.preventDefault();
          suppressGridClickUntil = Date.now() + 120;
          trapperPaintActive = true;
          const occupantId = state?.occupants ? state.occupants[key] : null;
          onGridClick(x, y, occupantId, { trapperPaint: true });
        });
        cell.addEventListener("mouseenter", (event) => {
          if ((armedTileAction !== "trapper" && armedTileAction !== "frozen_domain") || !trapperPaintActive) return;
          if (!(event.buttons & 1)) return;
          const occupantId = state?.occupants ? state.occupants[key] : null;
          onGridClick(x, y, occupantId, { trapperPaint: true, trapperAddOnly: true });
        });
        cell.addEventListener("click", () => {
          const occupantId = state?.occupants ? state.occupants[key] : null;
          onGridClick(x, y, occupantId);
        });
        gridEl.appendChild(cell);
        gridCellByKey.set(key, cell);
      }
    }
  }
  const blockers = new Set((grid.blockers || []).map((c) => `${c[0]},${c[1]}`));
  const tileMeta = new Map();
  const rawTiles = grid.tiles || [];
  const ingestTileEntry = (entry, fallbackKey) => {
    if (Array.isArray(entry)) {
      tileMeta.set(`${entry[0]},${entry[1]}`, {
        type: entry[2],
        hazards: entry[3],
        traps: entry[4],
        barriers: entry[5],
        frozen_domain: entry[6],
        trap_sources: entry[7],
      });
      return;
    }
    if (entry && typeof entry === "object") {
      const x = entry.x ?? entry[0];
      const y = entry.y ?? entry[1];
      let coordX = x;
      let coordY = y;
      if (!Number.isFinite(Number(coordX)) || !Number.isFinite(Number(coordY))) {
        const match = String(fallbackKey || "").match(/-?\d+/g) || [];
        if (match.length >= 2) {
          coordX = Number(match[0]);
          coordY = Number(match[1]);
        }
      }
      if (Number.isFinite(Number(coordX)) && Number.isFinite(Number(coordY))) {
        const resolvedType =
          entry.type !== undefined
            ? entry.type
            : entry.terrain !== undefined
              ? entry.terrain
              : entry.tile_type !== undefined
                ? entry.tile_type
                : entry.kind !== undefined
                  ? entry.kind
                  : entry.value;
        tileMeta.set(`${coordX},${coordY}`, {
          type: resolvedType,
          hazards: entry.hazards,
          traps: entry.traps,
          barriers: entry.barriers,
          frozen_domain: entry.frozen_domain,
          trap_sources: entry.trap_sources,
        });
      }
      return;
    }
    if (fallbackKey !== undefined) {
      const match = String(fallbackKey || "").match(/-?\d+/g) || [];
      if (match.length >= 2) {
        tileMeta.set(`${match[0]},${match[1]}`, {
          type: entry,
        });
      }
    }
  };
  if (Array.isArray(rawTiles)) {
    rawTiles.forEach((entry) => ingestTileEntry(entry));
  } else if (rawTiles && typeof rawTiles === "object") {
    Object.entries(rawTiles).forEach(([key, entry]) => ingestTileEntry(entry, key));
  }
  const combatantsById = new Map((state.combatants || []).map((combatant) => [combatant.id, combatant]));
  const occupantMap = state.occupants || {};
  const currentPos = state.current_pos ? `${state.current_pos[0]},${state.current_pos[1]}` : null;
  const legalShift = new Set((state.legal_shifts || []).map((c) => `${c[0]},${c[1]}`));
  const legalLongJump = new Set((state.legal_long_jumps || state.legal_jumps || []).map((c) => `${c[0]},${c[1]}`));
  const legalHighJump = new Set((state.legal_high_jumps || []).map((c) => `${c[0]},${c[1]}`));
  const legalFrozenDomain = new Set((state.legal_frozen_domain_tiles || []).map((c) => `${c[0]},${c[1]}`));
  const legalTrapper = new Set((state.legal_trapper_tiles || []).map((c) => `${c[0]},${c[1]}`));
  const frozenDomainDraft = frozenDomainDraftKeySet();
  const trapperDraft = trapperDraftKeySet();
  const legalPsionicOverloadBarrier = new Set((((state.combatants || []).find((entry) => entry.id === selectedId)?.trainer_action_hints?.psionic_overload_barrier_tiles) || []).map((entry) => `${entry.tile[0]},${entry.tile[1]}`));
  const psionicOverloadBarrierDraft = psionicOverloadBarrierKeySet();
  const rangeTiles = new Set();
  const targetTiles = new Set();
  if (armedMove && selectedId && state.move_targets && state.move_targets[armedMove]) {
    (state.move_targets[armedMove] || []).forEach((targetId) => {
      const target = combatantsById.get(targetId);
      if (target && target.position) {
        rangeTiles.add(`${target.position[0]},${target.position[1]}`);
        targetTiles.add(`${target.position[0]},${target.position[1]}`);
      }
    });
  }
  for (let y = 0; y < grid.height; y += 1) {
    for (let x = 0; x < grid.width; x += 1) {
      const key = `${x},${y}`;
      const cell = gridCellByKey.get(key);
      if (!cell) continue;
      cell.className = "cell";
      cell.style.removeProperty("--team-primary");
      cell.style.removeProperty("--team-secondary");
      cell.textContent = "";
      if (blockers.has(key)) {
        cell.classList.add("blocker");
      }
      const meta = tileMeta.get(key) || {};
      const tileType = meta.type;
      const tileTokens = tileTypeTokens(tileType);
      if (tileTokens.includes("water")) {
        cell.classList.add("water");
      }
      if (tileTokens.includes("difficult") || tileTokens.includes("rough")) {
        cell.classList.add("difficult");
      }
      if (tileTokens.includes("wall") || tileTokens.includes("blocker") || tileTokens.includes("blocking")) {
        cell.classList.add("blocker");
      }
      if (legalShift.has(key)) {
        cell.classList.add("legal");
      }
      if (((armedTileAction === "jump" || armedTileAction === "jump_long") && legalLongJump.has(key))
        || (armedTileAction === "jump_high" && legalHighJump.has(key))
        || (armedTileAction === "frozen_domain" && legalFrozenDomain.has(key))
        || (armedTileAction === "trapper" && legalTrapper.has(key))
        || (armedTileAction === "psionic_overload_barrier" && legalPsionicOverloadBarrier.has(key))) {
        cell.classList.add("in-range");
      }
      if (armedTileAction === "frozen_domain" && frozenDomainDraft.has(key)) {
        cell.classList.add("selected-tile");
      }
      if (armedTileAction === "trapper" && trapperDraft.has(key)) {
        cell.classList.add("selected-tile");
      }
      if (armedTileAction === "psionic_overload_barrier" && psionicOverloadBarrierDraft.has(key)) {
        cell.classList.add("selected-tile");
      }
      if (rangeTiles.has(key)) {
        cell.classList.add("in-range");
      }
      if (selectedTileKey === key) {
        cell.classList.add("selected-tile");
      }
      if (currentPos === key) {
        cell.classList.add("current");
      }
      const hazardEntries = collectTileHazards(meta.hazards, meta.traps);
      const barrierEntries = Array.isArray(meta?.barriers) ? meta.barriers : [];
      const frozenEntries = frozenDomainEntries(meta);
      if (hazardEntries.length || barrierEntries.length || frozenEntries.length) {
        cell.classList.add("has-hazard");
        const hazardWrap = document.createElement("div");
        hazardWrap.className = "hazard-stack";
        hazardEntries.slice(0, 4).forEach((entry) => {
          const badge = document.createElement("div");
          badge.className = `hazard-badge ${entry.kind === "trap" ? "trap" : "hazard"}`;
          const normalized = normalizePokeKey(entry.name);
          const glyph =
            (entry.kind === "trap" ? TRAP_GLYPHS[normalized] : HAZARD_GLYPHS[normalized]) ||
            String(entry.name || "?").charAt(0).toUpperCase();
          badge.textContent = entry.layers > 1 ? `${glyph}${entry.layers}` : glyph;
          badge.title = trapBadgeTitle(entry, meta);
          hazardWrap.appendChild(badge);
        });
      barrierEntries.slice(0, Math.max(0, 4 - hazardEntries.length)).forEach((entry) => {
        const badge = document.createElement("div");
        badge.className = "hazard-badge blocker";
        badge.textContent = "B";
        badge.title = barrierBadgeTitle(entry);
        hazardWrap.appendChild(badge);
      });
      if (frozenEntries.length && hazardWrap.childElementCount < 4) {
        const badge = document.createElement("div");
        badge.className = "hazard-badge frozen";
        badge.textContent = "FD";
        badge.title = frozenDomainBadgeTitle(frozenEntries);
        hazardWrap.appendChild(badge);
      }
      const totalObjects = hazardEntries.length + barrierEntries.length + frozenEntries.length;
      if (totalObjects > hazardWrap.childElementCount) {
        const badge = document.createElement("div");
        badge.className = "hazard-badge counter";
        badge.textContent = `+${totalObjects - hazardWrap.childElementCount}`;
        badge.title = `Tile has ${totalObjects} battlefield objects: ${hazardEntries.filter((entry) => entry.kind !== "trap").length} hazards, ${hazardEntries.filter((entry) => entry.kind === "trap").length} traps, ${barrierEntries.length} barriers, ${frozenEntries.length} Frozen Domain.`;
        hazardWrap.appendChild(badge);
      }
      cell.appendChild(hazardWrap);
      const noteWrap = document.createElement("div");
      noteWrap.className = "hazard-notes";
      const noteSpecs = [];
      hazardEntries.slice(0, 2).forEach((entry) => {
        noteSpecs.push({
          className: `hazard-note ${entry.kind === "trap" ? "trap" : "hazard"}`.trim(),
          text: `${entry.kind === "trap" ? "T" : "H"}:${String(entry.source_name || entry.name || entry.kind || "Hazard").trim().slice(0, 10)}`,
          title: trapBadgeTitle(entry, meta),
        });
      });
      barrierEntries.slice(0, 1).forEach((entry) => {
        noteSpecs.push({
          className: "hazard-note barrier",
          text: `B:${String(entry.source_name || entry.move || "Barrier").trim().slice(0, 10)}`,
          title: barrierBadgeTitle(entry),
        });
      });
      frozenEntries.slice(0, 1).forEach((entry) => {
        noteSpecs.push({
          className: "hazard-note frozen",
          text: `FD:${String(entry.source_name || "Frozen").trim().slice(0, 9)}`,
          title: frozenDomainBadgeTitle([entry]),
        });
      });
      barrierEntries.slice(1, 2).forEach((entry) => {
        noteSpecs.push({
          className: "hazard-note barrier",
          text: `B:${String(entry.source_name || entry.move || "Barrier").trim().slice(0, 10)}`,
          title: barrierBadgeTitle(entry),
        });
      });
      noteSpecs.slice(0, 3).forEach((spec) => {
        const note = document.createElement("div");
        note.className = spec.className;
        note.textContent = spec.text;
        note.title = spec.title;
        noteWrap.appendChild(note);
      });
      if (totalObjects > noteWrap.childElementCount) {
        const note = document.createElement("div");
        note.className = "hazard-note effect";
        note.textContent = `+${totalObjects - noteWrap.childElementCount}`;
        note.title = `Tile has ${totalObjects} battlefield objects with additional sources or effects.`;
        noteWrap.appendChild(note);
      }
      if (noteWrap.childElementCount) cell.appendChild(noteWrap);
    }
      const occupantId = occupantMap[key];
      const combatant = occupantId ? combatantsById.get(occupantId) : null;
      if (occupantId) {
        if (combatant) {
          const teamVisual = getTeamVisual(teamKeyForCombatant(combatant));
          const gimmicks = combatant.gimmicks || {};
          const teraType = gimmicks?.terastallized?.tera_type || "";
          cell.classList.add("occupied");
          cell.style.setProperty("--team-primary", teamVisual.primary);
          cell.style.setProperty("--team-secondary", teamVisual.secondary);
          if (gimmicks.mega_form) {
            cell.classList.add("state-mega");
          }
          if (gimmicks.primal_reversion_ready) {
            cell.classList.add("state-primal");
          }
          if (gimmicks.dynamax_active) {
            cell.classList.add("state-dynamax");
          }
          if (teraType) {
            const teraPalette = gimmickPalette("tera", teraType);
            cell.classList.add("state-tera");
            cell.style.setProperty("--tera-primary", teraPalette.primary);
            cell.style.setProperty("--tera-secondary", teraPalette.secondary);
          }
          const bar = document.createElement("div");
          bar.className = "hp-bar";
          bar.style.background = teamVisual.track;
          const fill = document.createElement("div");
          fill.className = "hp-fill";
          const ratio = combatant.max_hp ? combatant.hp / combatant.max_hp : 0;
          fill.style.width = `${Math.max(0, Math.min(1, ratio)) * 100}%`;
          fill.style.background = healthGradient(teamVisual, ratio);
          bar.appendChild(fill);
          cell.appendChild(bar);
          attachSprite(cell, combatant.sprite_url, combatant.name);
          appendTokenItemIcons(cell, combatant);
          appendTokenGimmickBadges(cell, combatant);
          const marker = document.createElement("div");
          marker.className = "marker";
          marker.textContent = combatant.marker;
          marker.style.background = `linear-gradient(135deg, ${teamVisual.primary}, ${teamVisual.secondary})`;
          cell.appendChild(marker);
          const injuryCount = Number(combatant.injuries || 0);
          if (injuryCount > 0) {
            const injuryWrap = document.createElement("div");
            injuryWrap.className = "injury-stack";
            for (let i = 0; i < injuryCount; i += 1) {
              const injury = document.createElement("div");
              injury.className = "injury-mark";
              injury.textContent = "X";
              injury.title = "Injury";
              injury.style.background = injuryColor(i, injuryCount);
              injury.style.top = `${14 + i * 12}px`;
              injury.style.left = "4px";
              injury.addEventListener("mouseenter", () => {
                showDetailTooltip(
                  injury,
                  `Injuries (${combatant.injuries})`,
                  buildInjuryTooltip(injuryCount)
                );
              });
              injury.addEventListener("mouseleave", () => {
                scheduleTooltipHide();
              });
              injuryWrap.appendChild(injury);
            }
            cell.appendChild(injuryWrap);
          }
        } else {
          const marker = document.createElement("div");
          marker.className = "marker";
          marker.textContent = "?";
          marker.style.background = "linear-gradient(135deg, #7d8ca6, #b7c6dd)";
          cell.appendChild(marker);
        }
        if (occupantId === selectedId) {
          cell.classList.add("selected");
        }
      }
      if (targetTiles.has(key)) {
        cell.classList.add("targetable");
      }
    }
  }
  fitGridToViewport();
  applyGridTransform();
  if (!viewManuallyAdjusted) {
    requestAnimationFrame(() => {
      fitGridToViewport();
      applyGridTransform();
    });
  }
  lastTileMeta = tileMeta;
  updateSelectedTileInfo(tileMeta);
}

function updateSelectedTileInfo(tileMeta) {
  if (!selectedTileInfoEl) return;
  if (!selectedTileKey) {
    selectedTileInfoEl.textContent = "Tile: -";
    selectedTileInfoEl.onmouseenter = null;
    selectedTileInfoEl.onmouseleave = null;
    if (terrainInfoEl) {
      const label = normalizeFieldName(terrainNameValue(state?.terrain)) || "None";
      terrainInfoEl.textContent = `Terrain: ${label}`;
    }
    syncSpectatorStateChips();
    return;
  }
  const meta = tileMeta.get(selectedTileKey) || {};
  const [x, y] = selectedTileKey.split(",");
  const typeLabel = tileTypeLabel(meta?.type);
  const typeDesc = tileTypeDescription(meta?.type);
  const blockers = new Set((state?.grid?.blockers || []).map((c) => `${c[0]},${c[1]}`));
  const isBlocked = blockers.has(selectedTileKey);
  const occupantId = state?.occupants ? state.occupants[selectedTileKey] : null;
  const occupant = occupantId
    ? (state?.combatants || []).find((entry) => entry.id === occupantId)
    : null;
  const hazardEntries = collectTileHazards(meta.hazards, meta.traps);
  const barrierEntries = Array.isArray(meta.barriers) ? meta.barriers : [];
  const frozenEntries = frozenDomainEntries(meta);
  const trapEntries = hazardEntries.filter((entry) => entry.kind === "trap");
  const standardHazards = hazardEntries.filter((entry) => entry.kind !== "trap");
  const objectCount = standardHazards.length + trapEntries.length + barrierEntries.length + frozenEntries.length;
  selectedTileInfoEl.textContent = [
    `Tile ${x},${y}`,
    typeLabel,
    occupant ? occupant.name || occupant.species || occupant.id : isBlocked ? "Blocked" : "",
    objectCount ? `${objectCount} object${objectCount === 1 ? "" : "s"}` : "",
  ].filter(Boolean).join(" | ");
  selectedTileInfoEl.onmouseenter = () => {
    const draftNotes = [];
    if (armedTileAction === "trapper") draftNotes.push(`Trapper draft ${trapperDraftTiles.length}/8`);
    if (armedTileAction === "frozen_domain") draftNotes.push(`Frozen draft ${frozenDomainDraftTiles.length}/6`);
    if (armedTileAction === "psionic_overload_barrier") draftNotes.push(`Overload barrier ${psionicOverloadBarrierTiles.length}/2`);
    const detailBody = [
      buildTileTooltip(meta, x, y),
      typeDesc ? `\n${typeDesc}` : "",
      draftNotes.length ? `\n${draftNotes.join("\n")}` : "",
    ].filter(Boolean).join("\n");
    showDetailTooltip(selectedTileInfoEl, `Tile ${x},${y}`, detailBody);
  };
  selectedTileInfoEl.onmouseleave = () => {
    scheduleTooltipHide();
  };
  if (terrainInfoEl) {
    const label = normalizeFieldName(terrainNameValue(state?.terrain)) || "None";
    terrainInfoEl.textContent = `Terrain: ${label} | Tile: ${typeLabel}`;
  }
  syncSpectatorStateChips();
  if (state?.ai_model) {
    aiModelsCache = state.ai_model;
    applyAiModelSelectionFromPayload(state.ai_model);
  } else if (aiModelsCache) {
    renderAiModelMath(aiModelsCache);
  } else {
    renderAiModelMath(null);
  }
}

function ensureAIDiagnosticsPanel() {
  if (aiDiagnosticsEl && aiDiagnosticsEl.isConnected) {
    return aiDiagnosticsEl;
  }
  if (!partyBarEl || !partyBarEl.parentElement) {
    return null;
  }
  const container = partyBarEl.parentElement;
  const title = document.createElement("div");
  title.className = "panel-title ds-panel-title";
  title.textContent = "Rules-safe AI";
  const panel = document.createElement("div");
  panel.id = "ai-diagnostics";
  panel.className = "combatant-details ai-diagnostics";
  panel.textContent = "Rules-safe AI diagnostics will appear during AI turns.";
  if (partyBarEl.nextSibling) {
    container.insertBefore(title, partyBarEl.nextSibling);
    container.insertBefore(panel, title.nextSibling);
  } else {
    container.appendChild(title);
    container.appendChild(panel);
  }
  aiDiagnosticsEl = panel;
  return aiDiagnosticsEl;
}

function renderAIDiagnostics() {
  const panel = ensureAIDiagnosticsPanel();
  if (!panel) return;
  const diag = state?.ai_diagnostics;
  const learning = state?.ai_learning;
  const model = state?.ai_model;
  const learningBattle = learning?.battle && typeof learning.battle === "object" ? learning.battle : null;
  const currentModelId = String(learning?.current_model_id || model?.current_model_id || "-");
  const updatesSince = Number.isFinite(Number(learning?.updates_since_snapshot)) ? Number(learning.updates_since_snapshot) : 0;
  const totalUpdates = Number.isFinite(Number(learning?.total_updates)) ? Number(learning.total_updates) : 0;
  const battleUpdates = Number.isFinite(Number(learningBattle?.battle_updates)) ? Number(learningBattle.battle_updates) : 0;
  const driftScore = Number.isFinite(Number(learning?.drift_score)) ? Number(learning.drift_score).toFixed(3) : "-";
  const driftThreshold = Number.isFinite(Number(learning?.drift_threshold)) ? Number(learning.drift_threshold).toFixed(3) : "-";
  const lastVersion = learningBattle?.last_model_version && typeof learningBattle.last_model_version === "object" ? learningBattle.last_model_version : null;
  const selectedModelAnalysis = model?.selected_analysis && typeof model.selected_analysis === "object" ? model.selected_analysis : null;
  const selectedModelRating =
    Array.isArray(model?.ratings) && model.ratings.length
      ? model.ratings.find((entry) => String(entry?.model_id || "") === currentModelId) || null
      : null;
  const analysisStyles = Array.isArray(selectedModelAnalysis?.styles) ? selectedModelAnalysis.styles.slice(0, 4).join(", ") : "";
  const analysisStrengths = Array.isArray(selectedModelAnalysis?.strengths) ? selectedModelAnalysis.strengths.slice(0, 2) : [];
  const analysisCautions = Array.isArray(selectedModelAnalysis?.cautions) ? selectedModelAnalysis.cautions.slice(0, 2) : [];
  const analysisChanges = Array.isArray(selectedModelAnalysis?.top_changes) ? selectedModelAnalysis.top_changes.slice(0, 3) : [];
  const summaryHtml = `
    <div class="details-row"><strong>Learning:</strong> model ${escapeHtml(currentModelId)} | battle updates ${escapeHtml(String(battleUpdates))} | snapshot updates ${escapeHtml(String(updatesSince))} | total ${escapeHtml(String(totalUpdates))}</div>
    <div class="details-row"><strong>Drift:</strong> ${escapeHtml(String(driftScore))}/${escapeHtml(String(driftThreshold))}</div>
    ${
      learningBattle?.last_action_label
        ? `<div class="details-row"><strong>Last learned:</strong> ${escapeHtml(String(learningBattle.last_action_label || "-"))} by ${escapeHtml(String(learningBattle.last_actor_id || "-"))}</div>`
        : ""
    }
    ${
      lastVersion
        ? `<div class="details-row ai-learning-version"><strong>Auto-versioned:</strong> ${escapeHtml(String(lastVersion.model_id || "-"))} from ${escapeHtml(String(lastVersion.parent_id || "-"))} at drift ${escapeHtml(String(lastVersion.drift_score ?? "-"))}</div>`
        : ""
    }
    ${
      selectedModelAnalysis
        ? `<div class="details-row"><strong>Model read:</strong> ${escapeHtml(String(selectedModelAnalysis.summary || "No analysis summary."))}</div>`
        : ""
    }
    ${
      analysisStyles
        ? `<div class="details-row"><strong>Style:</strong> ${escapeHtml(analysisStyles)}</div>`
        : ""
    }
    ${
      analysisStrengths.length
        ? `<div class="details-row"><strong>Likely strengths:</strong> ${escapeHtml(analysisStrengths.join(" | "))}</div>`
        : ""
    }
    ${
      analysisCautions.length
        ? `<div class="details-row"><strong>Likely cautions:</strong> ${escapeHtml(analysisCautions.join(" | "))}</div>`
        : ""
    }
    ${
      analysisChanges.length
        ? `<div class="details-row ai-diagnostics-list"><strong>Model deltas:</strong><br />${analysisChanges
            .map((entry, index) => `${index + 1}. ${escapeHtml(String(entry?.label || "Change"))} [${escapeHtml(String(entry?.delta ?? "-"))}]`)
            .join("<br />")}</div>`
        : ""
    }
    ${
      selectedModelRating
        ? `<div class="details-row"><strong>Rating:</strong> mu ${escapeHtml(String(selectedModelRating.mu ?? "-"))} | sigma ${escapeHtml(String(selectedModelRating.sigma ?? "-"))} | conservative ${escapeHtml(String(selectedModelRating.conservative ?? "-"))}</div>`
        : ""
    }
  `;
  if (!diag || typeof diag !== "object") {
    panel.innerHTML = `
      ${summaryHtml}
      <div class="details-row ai-diagnostics-muted">Rules-safe AI diagnostics will appear during AI turns.</div>
    `;
    return;
  }
  const actorId = String(diag.actor_id || "");
  const actor = (state?.combatants || []).find((entry) => entry.id === actorId);
  const actorName = actor ? actor.name || actor.species || actor.id : actorId || "Unknown";
  const selectedScore = Number.isFinite(Number(diag.selected_score)) ? Number(diag.selected_score).toFixed(3) : "-";
  const fallbackReason = String(diag.fallback_reason || "").trim();
  const top = Array.isArray(diag.legal_actions_top) ? diag.legal_actions_top.slice(0, 6) : [];
  const topText = top.length
    ? top
        .map((entry, index) => {
          const score = Number.isFinite(Number(entry?.score)) ? Number(entry.score).toFixed(3) : "-";
          return `${index + 1}. ${String(entry?.label || "Action")} [${score}]`;
        })
        .join("<br />")
    : "None";
  panel.innerHTML = `
    ${summaryHtml}
    <div class="details-row"><strong>Actor:</strong> ${escapeHtml(actorName)}</div>
    <div class="details-row"><strong>Source:</strong> ${escapeHtml(diag.source || "-")} | <strong>Reason:</strong> ${escapeHtml(diag.reason || "-")}</div>
    <div class="details-row"><strong>Selected:</strong> ${escapeHtml(diag.selected_action || "-")} | <strong>Score:</strong> ${escapeHtml(selectedScore)}</div>
    <div class="details-row"><strong>Legal actions:</strong> ${escapeHtml(String(diag.legal_action_count ?? 0))}</div>
    <div class="details-row"><strong>Fallback:</strong> ${fallbackReason ? escapeHtml(fallbackReason) : "None"}</div>
    <div class="details-row ai-diagnostics-list"><strong>Top legal:</strong><br />${topText}</div>
  `;
}

function centerGridOnCoord(coord) {
  if (!gridWrapEl || !state?.grid || !coord || coord.length < 2) return false;
  const width = state.grid.width * GRID_CELL_SIZE + Math.max(0, state.grid.width - 1) * GRID_GAP;
  const height = state.grid.height * GRID_CELL_SIZE + Math.max(0, state.grid.height - 1) * GRID_GAP;
  if (!width || !height) return false;
  const centerX = Number(coord[0]) * (GRID_CELL_SIZE + GRID_GAP) + GRID_CELL_SIZE / 2;
  const centerY = Number(coord[1]) * (GRID_CELL_SIZE + GRID_GAP) + GRID_CELL_SIZE / 2;
  gridOffset = {
    x: gridWrapEl.clientWidth / 2 - centerX * gridScale,
    y: gridWrapEl.clientHeight / 2 - centerY * gridScale,
  };
  viewManuallyAdjusted = true;
  applyGridTransform();
  return true;
}

function centerOnCurrentActor() {
  if (!state?.current_actor_id) return false;
  const combatant = (state.combatants || []).find((entry) => entry.id === state.current_actor_id);
  if (!combatant?.position) return false;
  return centerGridOnCoord(combatant.position);
}

function centerOnSelectedActor() {
  if (!selectedId) return false;
  const combatant = (state.combatants || []).find((entry) => entry.id === selectedId);
  if (!combatant?.position) return false;
  return centerGridOnCoord(combatant.position);
}

function isCinematicAutoActive() {
  return !!(cinematicAutoToggle?.checked && autoTimer && state?.mode === "ai");
}

function cinematicProfile() {
  const profile = String(cinematicProfileSelect?.value || "broadcast").toLowerCase();
  const mode = String(cinematicSpeedSelect?.value || "medium").toLowerCase();
  const base =
    profile === "movie"
      ? { pace: 1.05, fx: 0.68, wideZoomDelta: -0.08, settleMs: 280 }
      : profile === "fastcast"
        ? { pace: 0.8, fx: 0.56, wideZoomDelta: -0.04, settleMs: 90 }
        : { pace: 0.96, fx: 0.62, wideZoomDelta: -0.05, settleMs: 190 };
  if (mode === "slow") {
    return { ...base, profile, panMs: 640, actorLockMs: 420, moveLeadMs: 330, moveFollowFactor: 0.7 };
  }
  if (mode === "fast") {
    return { ...base, profile, panMs: 280, actorLockMs: 160, moveLeadMs: 110, moveFollowFactor: 0.5 };
  }
  return { ...base, profile, panMs: 460, actorLockMs: 280, moveLeadMs: 220, moveFollowFactor: 0.6 };
}

function cinematicFxScale() {
  const profile = cinematicProfile();
  const framePenalty = Math.max(0.45, Math.min(1.0, 22 / Math.max(14, cinematicFrameMsAvg)));
  const queuePenalty = pendingAnimationJobs > 10 ? Math.max(0.5, 1 - (pendingAnimationJobs - 10) * 0.035) : 1.0;
  return Math.max(0.45, Math.min(1.15, profile.fx * framePenalty * queuePenalty));
}

function _directorShotForMove(actor, target) {
  const profile = cinematicProfile().profile;
  const defaultSeq = ["actor", "target", "wide", "impact"];
  const movieSeq = ["wide", "actor", "target", "impact"];
  const fastSeq = ["actor", "target", "impact"];
  const seq = profile === "movie" ? movieSeq : profile === "fastcast" ? fastSeq : defaultSeq;
  const shot = seq[cinematicShotIndex % seq.length];
  cinematicShotIndex += 1;
  const actorPos = actor?.position || null;
  const targetPos = target?.position || actorPos;
  if (shot === "wide" && actorPos && targetPos) {
    return {
      type: "wide",
      coord: [
        Math.round((Number(actorPos[0]) + Number(targetPos[0])) / 2),
        Math.round((Number(actorPos[1]) + Number(targetPos[1])) / 2),
      ],
      zoom: Math.max(0.7, cinematicZoomTarget() + cinematicProfile().wideZoomDelta),
    };
  }
  if (shot === "target" && targetPos) return { type: "target", coord: targetPos, zoom: cinematicZoomTarget() };
  if (shot === "impact" && targetPos) return { type: "impact", coord: targetPos, zoom: cinematicZoomTarget() + 0.06 };
  return { type: "actor", coord: actorPos || targetPos, zoom: cinematicZoomTarget() };
}

function appendCinematicReplay(kind, payload) {
  cinematicReplayCache.push({
    t: Date.now(),
    round: Number(state?.round || 0),
    kind,
    payload,
  });
  if (cinematicReplayCache.length > 2200) {
    cinematicReplayCache = cinematicReplayCache.slice(-2200);
  }
}

function exportCinematicReplayCache() {
  if (!cinematicReplayCache.length) {
    notifyUI("warn", "No replay cache yet.", 1800);
    return;
  }
  const bundle = {
    generated_at_utc: new Date().toISOString(),
    mode: state?.mode || "",
    seed: state?.seed ?? null,
    profile: cinematicProfile(),
    events: cinematicReplayCache,
  };
  const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `autoptu_cinematic_replay_${Date.now()}.json`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function animationEventPriority(event) {
  if (!event || typeof event !== "object") return 0;
  const type = String(event.type || "").toLowerCase();
  if (type === "move" || type === "use_move" || type === "attack" || type === "action_move") {
    const crit = event.crit === true ? 2 : 0;
    const damage = Number(event.damage || 0) > 0 ? 1 : 0;
    return 3 + crit + damage;
  }
  if (type === "shift" || type === "move_tile") return 2;
  if (type === "item") {
    const effect = String(event.effect || "").toLowerCase();
    if (effect === "mega_evolution" || effect === "primal_reversion_ready") return 4;
    if (effect === "teracrystal" || effect === "z_move_activate") return 3;
    return 2;
  }
  if (type === "status") {
    const effect = String(event.effect || "").toLowerCase();
    if (effect === "dynamax" || effect === "dynamax_end") return 3;
  }
  if (type === "ability") return 1;
  return 0;
}

function updateCinematicPerfLabel() {
  if (!cinematicPerfEl) return;
  if (!cinematicAutoToggle?.checked) {
    cinematicPerfEl.textContent = "Cine: idle";
    return;
  }
  cinematicPerfEl.textContent = `Cine: ${cinematicFrameMsAvg.toFixed(1)}ms | q${pendingAnimationJobs}`;
}

function cinematicZoomTarget() {
  const width = Number(state?.grid?.width || 0);
  const height = Number(state?.grid?.height || 0);
  const largest = Math.max(width, height);
  if (largest >= 40) return 1.15;
  if (largest >= 28) return 1.25;
  return 1.35;
}

function _gridCenteredOffsetForCoord(coord, scale) {
  if (!gridWrapEl || !state?.grid || !coord || coord.length < 2) return null;
  const centerX = Number(coord[0]) * (GRID_CELL_SIZE + GRID_GAP) + GRID_CELL_SIZE / 2;
  const centerY = Number(coord[1]) * (GRID_CELL_SIZE + GRID_GAP) + GRID_CELL_SIZE / 2;
  return {
    x: gridWrapEl.clientWidth / 2 - centerX * scale,
    y: gridWrapEl.clientHeight / 2 - centerY * scale,
  };
}

function cinematicFocusCoord(coord, zoom = null, force = false, durationMs = null) {
  if (!coord || coord.length < 2) return false;
  if (!isCinematicAutoActive() && !force) return false;
  const now = Date.now();
  if (!force && now - lastCinematicPanAt < 110) {
    return false;
  }
  const startScale = gridScale;
  const targetScale = Math.max(
    MIN_GRID_SCALE,
    Math.min(MAX_GRID_SCALE, Number.isFinite(Number(zoom)) ? Number(zoom) : cinematicZoomTarget())
  );
  const startOffset = { ...gridOffset };
  const targetOffset = _gridCenteredOffsetForCoord(coord, targetScale);
  if (!targetOffset) return false;
  const deltaX = targetOffset.x - startOffset.x;
  const deltaY = targetOffset.y - startOffset.y;
  const deltaScale = Math.abs(targetScale - startScale);
  const deadzone = 14;
  if (!force && Math.hypot(deltaX, deltaY) < deadzone && deltaScale < 0.02) {
    return false;
  }
  viewManuallyAdjusted = true;
  cinematicCameraBusy = true;
  cinematicCameraJob = cinematicCameraJob.then(
    () =>
      new Promise((resolve) => {
        const begin = performance.now();
        const fallback = cinematicProfile().panMs;
        const dur = Math.max(110, Number(durationMs || fallback));
        const ease = (t) => 1 - Math.pow(1 - t, 3);
        const tick = (ts) => {
          const t = Math.max(0, Math.min(1, (ts - begin) / dur));
          const e = ease(t);
          gridScale = startScale + (targetScale - startScale) * e;
          gridOffset = {
            x: startOffset.x + (targetOffset.x - startOffset.x) * e,
            y: startOffset.y + (targetOffset.y - startOffset.y) * e,
          };
          applyGridTransform();
          if (t < 1) {
            requestAnimationFrame(tick);
            return;
          }
          lastCinematicPanAt = Date.now();
          cinematicCameraBusy = false;
          updateCinematicPerfLabel();
          resolve();
        };
        requestAnimationFrame(tick);
      })
  );
  return true;
}

function applyCinematicTurnCamera() {
  if (!isCinematicAutoActive()) return;
  if (!state?.current_actor_id || state.current_actor_id === lastCinematicActorId) return;
  const current = (state.combatants || []).find((entry) => entry.id === state.current_actor_id);
  if (!current?.position) return;
  appendCinematicReplay("turn_focus", {
    actor: current.id,
    position: current.position,
    round: Number(state?.round || 0),
  });
  cinematicFocusCoord(current.position, cinematicZoomTarget(), true, cinematicProfile().panMs);
  lastCinematicActorId = state.current_actor_id;
}

async function ensureCinematicActorFocus() {
  if (!isCinematicAutoActive()) return;
  const current = (state?.combatants || []).find((entry) => entry.id === state?.current_actor_id);
  if (!current?.position) return;
  const profile = cinematicProfile();
  cinematicFocusCoord(current.position, cinematicZoomTarget(), true, profile.panMs);
  await cinematicCameraJob;
  if (profile.actorLockMs > 0) {
    await new Promise((resolve) => window.setTimeout(resolve, profile.actorLockMs));
  }
}

function processMoveAnimations() {
  const log = Array.isArray(state?.log) ? state.log : [];
  const lastEvent = log.length ? log[log.length - 1] : null;
  const logToken = lastEvent
    ? [
        String(log.length),
        String(lastEvent?.round ?? ""),
        String(lastEvent?.type ?? ""),
        String(lastEvent?.actor ?? lastEvent?.actor_id ?? ""),
        String(lastEvent?.target ?? lastEvent?.target_id ?? ""),
        String(lastEvent?.move ?? lastEvent?.text ?? ""),
      ].join("|")
    : "";
  if (lastProcessedLogSize === null) {
    lastProcessedLogSize = log.length;
    lastProcessedLogToken = logToken;
    return;
  }
  let nextEvents = [];
  if (log.length < lastProcessedLogSize) {
    lastProcessedLogSize = 0;
  }
  if (log.length === lastProcessedLogSize && logToken && logToken !== lastProcessedLogToken) {
    nextEvents = log.slice(-20);
  } else {
    nextEvents = log.slice(lastProcessedLogSize);
  }
  if (nextEvents.length > MAX_ANIMATION_EVENT_SLICE) {
    nextEvents = nextEvents.slice(-MAX_ANIMATION_EVENT_SLICE);
  }
  lastProcessedLogSize = log.length;
  lastProcessedLogToken = logToken;
  if (!nextEvents.length) {
    return;
  }
  const moveEvents = nextEvents.filter((event) => {
    if (!event || typeof event !== "object") return false;
    const type = String(event.type || "").toLowerCase();
    const hasMoveName = typeof event.move === "string" || typeof event.move_name === "string";
    const hasActor = !!(event.actor || event.actor_id || event.source);
    if (type === "move" || type === "use_move" || type === "shift" || type === "move_tile" || type === "attack" || type === "action_move") {
      return true;
    }
    if (!hasMoveName || !hasActor) return false;
    if (
      type === "ability" ||
      type === "status" ||
      type === "hazard" ||
      type === "heal" ||
      type === "healing" ||
      type === "damage" ||
      type === "condition" ||
      type === "switch" ||
      type === "pass" ||
      type === "round_start"
    ) {
      return false;
    }
    return false;
  });
  const abilityEvents = nextEvents.filter((event) => {
    if (!event || typeof event !== "object") return false;
    return String(event.type || "").toLowerCase() === "ability";
  });
  const itemEvents = nextEvents.filter((event) => {
    if (!event || typeof event !== "object") return false;
    return String(event.type || "").toLowerCase() === "item";
  });
  const statusEvents = nextEvents.filter((event) => {
    if (!event || typeof event !== "object") return false;
    if (String(event.type || "").toLowerCase() !== "status") return false;
    const effect = String(event.effect || "").toLowerCase();
    return effect === "dynamax" || effect === "dynamax_end";
  });
  const captureAll = isCinematicAutoActive();
  const overloaded = pendingAnimationJobs > 18;
  const moveBatch = captureAll ? moveEvents : moveEvents.slice(-6);
  let abilityBatch = captureAll ? abilityEvents : abilityEvents.slice(-8);
  let itemBatch = captureAll ? itemEvents : itemEvents.slice(-6);
  let statusBatch = captureAll ? statusEvents : statusEvents.slice(-4);
  if (!captureAll && overloaded) {
    abilityBatch = abilityBatch.filter((event) => animationEventPriority(event) >= 2);
    itemBatch = itemBatch.filter((event) => animationEventPriority(event) >= 2);
    statusBatch = statusBatch.filter((event) => animationEventPriority(event) >= 2);
  }
  const queueAnimation = (factory, priority = 1) => {
    if (pendingAnimationJobs >= MAX_ANIMATION_QUEUE && priority <= 1) {
      return;
    }
    if (pendingAnimationJobs >= MAX_ANIMATION_QUEUE * 2) {
      fxQueue = Promise.resolve();
      pendingAnimationJobs = 0;
    }
    pendingAnimationJobs += 1;
    fxQueue = fxQueue
      .then(() => factory())
      .catch(() => {})
      .finally(() => {
        pendingAnimationJobs = Math.max(0, pendingAnimationJobs - 1);
        updateCinematicPerfLabel();
      });
    updateCinematicPerfLabel();
  };
  moveBatch.forEach((event) => {
    const type = String(event.type || "").toLowerCase();
    const priority = animationEventPriority(event);
    if (type === "shift" || type === "move_tile") {
      queueAnimation(() => animateShiftEvent(event), priority);
      return;
    }
    queueAnimation(() => animateMoveEvent(event), Math.max(2, priority));
  });
  abilityBatch.forEach((event) => {
    queueAnimation(() => animateAbilityEvent(event), animationEventPriority(event));
  });
  itemBatch.forEach((event) => {
    queueAnimation(() => animateItemEvent(event), animationEventPriority(event));
  });
  statusBatch.forEach((event) => {
    queueAnimation(() => animateStatusEvent(event), animationEventPriority(event));
  });
}

function combatantFromEventRef(ref) {
  if (!ref || !state?.combatants?.length) return null;
  if (typeof ref === "object") {
    if (typeof ref.id === "string") {
      return state.combatants.find((combatant) => combatant.id === ref.id) || null;
    }
    if (typeof ref.name === "string") {
      return state.combatants.find((combatant) => combatant.name === ref.name) || null;
    }
  }
  const asString = String(ref);
  return (
    state.combatants.find((combatant) => combatant.id === asString) ||
    state.combatants.find((combatant) => combatant.name === asString) ||
    null
  );
}

function cellForCombatant(combatant) {
  if (!combatant?.position || combatant.position.length < 2) return null;
  const x = combatant.position[0];
  const y = combatant.position[1];
  return gridEl.querySelector(`.cell[data-x="${x}"][data-y="${y}"]`);
}

function coordKey(coord) {
  return coord ? `${coord[0]},${coord[1]}` : "";
}

function parseCoord(value) {
  if (!value && value !== 0) return null;
  if (Array.isArray(value) && value.length >= 2) {
    const x = Number(value[0]);
    const y = Number(value[1]);
    if (Number.isFinite(x) && Number.isFinite(y)) {
      return [Math.trunc(x), Math.trunc(y)];
    }
    return null;
  }
  if (typeof value === "object") {
    const x = Number(value.x ?? value.col ?? value.q);
    const y = Number(value.y ?? value.row ?? value.r);
    if (Number.isFinite(x) && Number.isFinite(y)) {
      return [Math.trunc(x), Math.trunc(y)];
    }
    return null;
  }
  if (typeof value === "string") {
    const matches = value.match(/-?\d+/g);
    if (matches && matches.length >= 2) {
      return [Number(matches[0]), Number(matches[1])];
    }
  }
  return null;
}

function formatCoord(value) {
  const coord = parseCoord(value);
  if (!coord) return String(value ?? "-");
  return `${coord[0]},${coord[1]}`;
}

function cellForCoord(coord) {
  if (!coord || coord.length < 2) return null;
  return gridEl.querySelector(`.cell[data-x="${coord[0]}"][data-y="${coord[1]}"]`);
}

function cellCenterForCoord(coord) {
  const cell = cellForCoord(coord);
  if (!cell) return null;
  const rect = cell.getBoundingClientRect();
  return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2, cell };
}

function captureCombatantPositions() {
  const map = new Map();
  if (!state?.combatants?.length) {
    return map;
  }
  state.combatants.forEach((combatant) => {
    if (combatant?.id && combatant?.position && combatant.position.length >= 2) {
      map.set(combatant.id, [Number(combatant.position[0]), Number(combatant.position[1])]);
    }
  });
  return map;
}

function parseLeadingNumber(text) {
  const match = String(text || "").match(/(\d+)/);
  if (!match) return null;
  const value = Number(match[1]);
  if (!Number.isFinite(value)) return null;
  return Math.trunc(value);
}

function extractRangeMeters(moveMeta) {
  const rangeText = String(moveMeta?.range || "").toLowerCase();
  const targetText = String(moveMeta?.target || "").toLowerCase();
  const raw = `${rangeText} ${targetText}`;
  if (raw.includes("self")) return 0;
  if (raw.includes("melee")) return 1;
  const numeric = parseLeadingNumber(raw);
  if (numeric !== null) return Math.max(1, numeric);
  return 1;
}

function extractAoeRadius(moveMeta) {
  const raw = `${moveMeta?.target || ""} ${moveMeta?.range || ""} ${moveMeta?.effects || ""}`.toLowerCase();
  const match = raw.match(/(?:blast|burst|radius|aoe)\s*([0-9]+)/i);
  if (!match) return 0;
  const value = Number(match[1]);
  if (!Number.isFinite(value) || value < 0) return 0;
  return Math.trunc(value);
}

function coordsWithinDistance(origin, distance) {
  const results = [];
  if (!origin || !state?.grid) return results;
  const limit = Math.max(0, Math.trunc(distance));
  for (let y = 0; y < state.grid.height; y += 1) {
    for (let x = 0; x < state.grid.width; x += 1) {
      const manhattan = Math.abs(x - origin[0]) + Math.abs(y - origin[1]);
      if (manhattan <= limit) {
        results.push([x, y]);
      }
    }
  }
  return results;
}

function coordsAlongLine(fromCoord, toCoord, maxSteps = null) {
  if (!fromCoord || !toCoord) return [];
  const dx = toCoord[0] - fromCoord[0];
  const dy = toCoord[1] - fromCoord[1];
  const steps = Math.max(Math.abs(dx), Math.abs(dy));
  if (!steps) return [toCoord];
  const out = [];
  const cap = Number.isFinite(Number(maxSteps)) ? Math.max(1, Math.trunc(Number(maxSteps))) : steps;
  for (let i = 1; i <= steps && i <= cap; i += 1) {
    const t = i / steps;
    const x = Math.round(fromCoord[0] + dx * t);
    const y = Math.round(fromCoord[1] + dy * t);
    out.push([x, y]);
  }
  return out;
}

function uniqueCoords(coords) {
  const seen = new Set();
  const out = [];
  (coords || []).forEach((coord) => {
    if (!coord || coord.length < 2) return;
    const key = coordKey(coord);
    if (!key || seen.has(key)) return;
    seen.add(key);
    out.push(coord);
  });
  return out;
}

function applyTemporaryCellHighlight(coords, className, durationMs = 900) {
  uniqueCoords(coords).forEach((coord) => {
    const cell = cellForCoord(coord);
    if (!cell) return;
    cell.classList.add(className);
    window.setTimeout(() => {
      cell.classList.remove(className);
    }, durationMs);
  });
}

function drawMovementArrow(fromCoord, toCoord, durationMs = 1100) {
  const fromCenter = cellCenterForCoord(fromCoord);
  const toCenter = cellCenterForCoord(toCoord);
  if (!fromCenter || !toCenter) return;
  const dx = toCenter.x - fromCenter.x;
  const dy = toCenter.y - fromCenter.y;
  const length = Math.hypot(dx, dy);
  if (length < 2) return;
  const angle = Math.atan2(dy, dx);
  const body = document.createElement("div");
  body.className = "fx-move-arrow";
  body.style.left = `${fromCenter.x}px`;
  body.style.top = `${fromCenter.y}px`;
  body.style.width = `${Math.max(8, length - 10)}px`;
  body.style.transform = `rotate(${angle}rad)`;
  const head = document.createElement("div");
  head.className = "fx-move-arrow-head";
  head.style.left = `${toCenter.x - 6}px`;
  head.style.top = `${toCenter.y - 5}px`;
  head.style.transform = `rotate(${angle}rad)`;
  document.body.appendChild(body);
  document.body.appendChild(head);
  window.setTimeout(() => {
    body.remove();
    head.remove();
  }, durationMs);
}

function spawnMovementEchoes(actor, fromCoord, toCoord) {
  if (!actor?.sprite_url || !fromCoord || !toCoord) return;
  const fromCell = gridCellByKey.get(coordKey(fromCoord));
  const toCell = gridCellByKey.get(coordKey(toCoord));
  if (!fromCell || !toCell) return;
  const fromRect = fromCell.getBoundingClientRect();
  const toRect = toCell.getBoundingClientRect();
  const dx = (toRect.left + toRect.width / 2) - (fromRect.left + fromRect.width / 2);
  const dy = (toRect.top + toRect.height / 2) - (fromRect.top + fromRect.height / 2);
  const fractions = [0.32, 0.64];
  fractions.forEach((fraction, index) => {
    const ghost = document.createElement("div");
    ghost.className = "fx-move-echo";
    ghost.style.left = `${Math.round(fromRect.left + fromRect.width / 2 + dx * fraction)}px`;
    ghost.style.top = `${Math.round(fromRect.top + fromRect.height / 2 + dy * fraction)}px`;
    ghost.style.animationDelay = `${index * 40}ms`;
    const wrap = document.createElement("div");
    wrap.className = "token-sprite-wrap loaded";
    const img = document.createElement("img");
    img.className = "token-sprite";
    img.src = actor.sprite_url;
    img.alt = actor.name || actor.species || "sprite";
    img.addEventListener("load", () => configureSpriteSheet(wrap, img), { once: true });
    wrap.appendChild(img);
    ghost.appendChild(wrap);
    document.body.appendChild(ghost);
    window.setTimeout(() => ghost.remove(), 320);
  });
}

function showAttackFootprint(actor, target, moveMeta, durationMs = 900) {
  if (!actor?.position || !state?.grid) return;
  const range = moveMeta ? Math.max(0, Math.min(18, extractRangeMeters(moveMeta))) : 0;
  const rangeTiles = coordsWithinDistance(actor.position, range);
  applyTemporaryCellHighlight(rangeTiles, "fx-range-preview", durationMs);
  const targetCoord = target?.position || actor.position;
  const raw = `${moveMeta?.target || ""} ${moveMeta?.range || ""}`.toLowerCase();
  const lineMatch = raw.match(/line\s*([0-9]+)/i);
  const lineLength = lineMatch ? Number(lineMatch[1]) : null;
  const aoeRadius = extractAoeRadius(moveMeta);
  let affected = [];
  if (lineLength && actor?.position && targetCoord) {
    affected = coordsAlongLine(actor.position, targetCoord, lineLength);
  } else if (aoeRadius > 0) {
    affected = coordsWithinDistance(targetCoord, Math.min(12, aoeRadius));
  } else {
    affected = [targetCoord];
  }
  applyTemporaryCellHighlight(affected, "fx-aoe-preview", durationMs + 100);
}

function animateShiftEvent(event) {
  const actorRef = event.actor ?? event.actor_id ?? event.source;
  const actor = combatantFromEventRef(actorRef);
  const toCoord = parseCoord(event.to ?? event.destination ?? event.end) || actor?.position || null;
  const fromCoord =
    parseCoord(event.from ?? event.start) ||
    (actor?.id && lastRenderedPositions.has(actor.id) ? lastRenderedPositions.get(actor.id) : null);
  if (!toCoord || !fromCoord) {
    return Promise.resolve();
  }
  if (coordKey(toCoord) === coordKey(fromCoord)) {
    return Promise.resolve();
  }
  appendCinematicReplay("shift", {
    actor: actor?.id || actorRef,
    from: fromCoord,
    to: toCoord,
  });
  cinematicPhaseActive = true;
  if (isCinematicAutoActive()) {
    cinematicFocusCoord(fromCoord, Math.max(1.12, cinematicZoomTarget() - 0.08), true, cinematicProfile().panMs);
    window.setTimeout(() => {
      cinematicFocusCoord(toCoord, Math.max(1.12, cinematicZoomTarget() - 0.08), true, cinematicProfile().panMs);
    }, 120);
  }
  applyTemporaryCellHighlight([fromCoord], "fx-shift-origin", 1100);
  applyTemporaryCellHighlight([toCoord], "fx-shift-destination", 1100);
  spawnMovementEchoes(actor, fromCoord, toCoord);
  const moveGhostDuration = spawnPokemonMovementGhost(actor, fromCoord, toCoord);
  return new Promise((resolve) => {
    window.setTimeout(() => {
      cinematicPhaseActive = false;
      resolve();
    }, Math.max(170, moveGhostDuration));
  });
}

function triggerGridShake(intensity = 1) {
  if (!gridWrapEl) return;
  const cinematic = isCinematicAutoActive();
  const scaled = cinematic ? Math.max(0, intensity - 1.1) : intensity;
  if (scaled <= 0) return;
  const amount = cinematic
    ? Math.max(1, Math.min(2, Math.round(scaled * 1.25)))
    : Math.max(1, Math.min(4, Math.round(scaled * 1.9)));
  gridWrapEl.style.setProperty("--shake", `${amount}px`);
  gridWrapEl.classList.remove("fx-grid-shake");
  void gridWrapEl.offsetWidth;
  gridWrapEl.classList.add("fx-grid-shake");
  window.setTimeout(() => {
    gridWrapEl?.classList.remove("fx-grid-shake");
  }, cinematic ? 150 : 190);
}

function blinkCellAbility(cell, durationMs = ABILITY_BLINK_MS) {
  if (!cell) return;
  cell.classList.remove("fx-ability-blink");
  void cell.offsetWidth;
  cell.classList.add("fx-ability-blink");
  window.setTimeout(() => {
    cell.classList.remove("fx-ability-blink");
  }, durationMs);
}

function animateAbilityEvent(event) {
  const actorRef = event.actor ?? event.actor_id ?? event.source;
  const targetRef = event.target ?? event.target_id ?? event.defender;
  const actor = combatantFromEventRef(actorRef);
  const target = combatantFromEventRef(targetRef);
  const actorCell = cellForCombatant(actor);
  const targetCell = cellForCombatant(target);
  appendCinematicReplay("ability", {
    actor: actor?.id || actorRef || "",
    target: target?.id || targetRef || "",
    ability: String(event?.ability || event?.move || ""),
  });
  cinematicPhaseActive = true;
  blinkCellAbility(actorCell);
  if (targetCell && targetCell !== actorCell) {
    blinkCellAbility(targetCell, Math.max(300, ABILITY_BLINK_MS - 140));
  }
  return new Promise((resolve) => {
    window.setTimeout(() => {
      cinematicPhaseActive = false;
      resolve();
    }, 110);
  });
}

function spawnHitStreaks(x, y, palette, intensity = 1, crit = false, moveAnim = null) {
  const fxScale = cinematicFxScale();
  const count = Math.max(2, Math.min(9, Math.round((3 + intensity * 3 + (crit ? 2 : 0)) * fxScale)));
  for (let i = 0; i < count; i += 1) {
    const streak = document.createElement("div");
    streak.className = "fx-hit-streak";
    if (moveAnim?.style) {
      streak.classList.add(`streak-${moveAnim.style}`);
    }
    if (moveAnim?.channel) {
      streak.classList.add(`channel-${moveAnim.channel}`);
    }
    if (moveAnim?.typeKey) {
      streak.classList.add(`type-${moveAnim.typeKey}`);
    }
    const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.6;
    const length = 18 + Math.random() * 24 + intensity * 7;
    const radius = 14 + Math.random() * (14 + intensity * 10);
    const sx = x + Math.cos(angle) * radius;
    const sy = y + Math.sin(angle) * radius;
    streak.style.left = `${sx}px`;
    streak.style.top = `${sy}px`;
    streak.style.width = `${length}px`;
    streak.style.background = `linear-gradient(90deg, ${palette.secondary}, ${palette.primary})`;
    streak.style.transform = `rotate(${angle}rad)`;
    document.body.appendChild(streak);
    window.setTimeout(() => streak.remove(), 620);
  }
}

function inferMoveAnimAtlas(imgW, imgH) {
  const width = Math.max(1, Math.trunc(Number(imgW) || 1));
  const height = Math.max(1, Math.trunc(Number(imgH) || 1));
  const preferred = [
    [192, 192],
    [128, 128],
    [96, 96],
    [64, 64],
    [192, 96],
    [96, 192],
    [160, 160],
    [256, 256],
    [80, 80],
    [48, 48],
    [32, 32],
  ];
  for (const [frameW, frameH] of preferred) {
    if (width % frameW !== 0 || height % frameH !== 0) continue;
    const cols = Math.max(1, Math.floor(width / frameW));
    const rows = Math.max(1, Math.floor(height / frameH));
    const frames = cols * rows;
    if (frames < 2 || frames > 128) continue;
    return { frameW, frameH, cols, rows, frames };
  }
  return { frameW: width, frameH: height, cols: 1, rows: 1, frames: 1 };
}

function startMoveAnimSpritePlayback(el, imageUrl, imgW, imgH, intensity = 1, options = {}) {
  if (!el) return { totalMs: 0, stop: () => {} };
  const atlas = inferMoveAnimAtlas(imgW, imgH);
  const frameBase = Math.max(atlas.frameW, atlas.frameH);
  const sourceRect = options.sourceRect || null;
  const targetRect = options.targetRect || null;
  const startX = Number(options.startX || 0);
  const startY = Number(options.startY || 0);
  const endX = Number(options.endX || startX);
  const endY = Number(options.endY || startY);
  const cellBase = Math.max(
    28,
    Math.round(
      [
        sourceRect?.width,
        sourceRect?.height,
        targetRect?.width,
        targetRect?.height,
      ].filter(Number.isFinite).reduce((sum, value, _, arr) => sum + value / Math.max(1, arr.length), 0) || 64
    )
  );
  const scale = Math.max(1.18, Math.min(2.3, 1.26 + cinematicFxScale() * 0.32 + intensity * 0.12));
  const frameDisplayW = Math.round(
    Math.max(cellBase * 1.05, Math.min(cellBase * 2.9, cellBase * scale * (atlas.frameW / frameBase)))
  );
  const frameDisplayH = Math.round(
    Math.max(cellBase * 1.05, Math.min(cellBase * 2.9, cellBase * scale * (atlas.frameH / frameBase)))
  );
  el.style.width = `${frameDisplayW}px`;
  el.style.height = `${frameDisplayH}px`;
  el.style.marginLeft = `${Math.round(-frameDisplayW / 2)}px`;
  el.style.marginTop = `${Math.round(-frameDisplayH / 2)}px`;
  el.style.backgroundImage = `url("${imageUrl}")`;
  el.style.backgroundRepeat = "no-repeat";
  el.style.backgroundSize = `${atlas.cols * frameDisplayW}px ${atlas.rows * frameDisplayH}px`;
  el.style.backgroundPosition = "0px 0px";
  el.style.setProperty("--sheet-fit", "cover");
  el.classList.add("has-sheet");
  el.style.left = `${startX}px`;
  el.style.top = `${startY}px`;
  const travelMs = Math.max(220, Math.min(620, Math.hypot(endX - startX, endY - startY) * 0.56));
  el.style.transition = `left ${travelMs}ms cubic-bezier(0.22, 1, 0.36, 1), top ${travelMs}ms cubic-bezier(0.22, 1, 0.36, 1), opacity 90ms ease-out`;
  requestAnimationFrame(() => {
    el.style.opacity = "1";
    requestAnimationFrame(() => {
      el.style.left = `${endX}px`;
      el.style.top = `${endY}px`;
    });
  });
  if (atlas.frames <= 1) {
    return { totalMs: Math.max(1600, travelMs + 520), stop: () => {} };
  }
  const frameMs = Math.max(46, Math.round(1000 / 16));
  const settleMs = 520;
  const totalMs = Math.max(atlas.frames * frameMs + settleMs, travelMs + 260);
  let frameIndex = 0;
  const timer = window.setInterval(() => {
    frameIndex += 1;
    if (frameIndex >= atlas.frames) {
      window.clearInterval(timer);
      return;
    }
    const col = frameIndex % atlas.cols;
    const row = Math.floor(frameIndex / atlas.cols);
    el.style.backgroundPosition = `${-col * frameDisplayW}px ${-row * frameDisplayH}px`;
  }, frameMs);
  return {
    totalMs,
    stop: () => {
      window.clearInterval(timer);
    },
  };
}

function spawnImpact(
  fromX,
  fromY,
  toX,
  toY,
  sourceRect,
  targetRect,
  moveAnimUrl = null,
  intensity = 1
) {
  const impact = document.createElement("div");
  impact.className = "fx-impact";
  impact.style.left = `${toX}px`;
  impact.style.top = `${toY}px`;
  document.body.appendChild(impact);
  let moveAnimSprite = null;
  let moveAnimPlayback = null;
  if (moveAnimUrl) {
    moveAnimSprite = document.createElement("div");
    moveAnimSprite.className = "fx-impact-moveanim";
    moveAnimSprite.style.left = `${toX}px`;
    moveAnimSprite.style.top = `${toY}px`;
    if (moveAnimUrl) {
      const test = new Image();
      test.addEventListener(
        "load",
        () => {
          if (!moveAnimSprite) return;
          moveAnimPlayback = startMoveAnimSpritePlayback(
            moveAnimSprite,
            moveAnimUrl,
            Number(test.naturalWidth || 0),
            Number(test.naturalHeight || 0),
            intensity,
            { startX: toX, startY: toY, endX: toX, endY: toY, sourceRect, targetRect }
          );
        },
        { once: true }
      );
      test.addEventListener(
        "error",
        () => {},
        { once: true }
      );
      test.src = moveAnimUrl;
    }
    document.body.appendChild(moveAnimSprite);
  }
  const impactLifetime = moveAnimPlayback ? Math.max(1100, moveAnimPlayback.totalMs + 260) : moveAnimSprite ? 1400 : 900;
  setTimeout(() => {
    impact.remove();
    moveAnimPlayback?.stop?.();
    moveAnimSprite?.remove();
  }, impactLifetime);
}

function spawnTrail(fromX, fromY, dx, dy, duration, palette, moveAnim = null) {
  if (cinematicFxScale() < 0.52) return;
  const trail = document.createElement("div");
  trail.className = "fx-trail";
  if (moveAnim?.style) {
    trail.classList.add(`trail-${moveAnim.style}`);
  }
  if (moveAnim?.channel) {
    trail.classList.add(`channel-${moveAnim.channel}`);
  }
  if (moveAnim?.typeKey) {
    trail.classList.add(`type-${moveAnim.typeKey}`);
  }
  trail.style.left = `${fromX}px`;
  trail.style.top = `${fromY}px`;
  trail.style.width = `${Math.max(14, Math.hypot(dx, dy) * 1.15)}px`;
  trail.style.background = `linear-gradient(90deg, ${palette.secondary}, ${palette.primary}, transparent)`;
  const angle = Math.atan2(dy, dx);
  trail.style.transform = `rotate(${angle}rad)`;
  trail.style.transition = `opacity ${Math.max(340, duration * 1.2)}ms ease-out`;
  document.body.appendChild(trail);
  requestAnimationFrame(() => {
    trail.style.opacity = "0.05";
  });
  setTimeout(() => trail.remove(), Math.max(620, Math.round(duration * 1.8)));
}

function animateMoveEvent(event) {
  const actorRef = event.actor ?? event.actor_id ?? event.source;
  const targetRef = event.target ?? event.target_id ?? event.defender;
  const actor = combatantFromEventRef(actorRef);
  const target = combatantFromEventRef(targetRef) || actor;
  const moveMeta = moveMetaFromEvent(event);
  const sourceCell = cellForCombatant(actor);
  const targetCell = cellForCombatant(target);
  if (!sourceCell) {
    return Promise.resolve();
  }
  const sourceRect = sourceCell.getBoundingClientRect();
  const targetRect = (targetCell || sourceCell).getBoundingClientRect();
  const fromX = sourceRect.left + sourceRect.width / 2;
  const fromY = sourceRect.top + sourceRect.height / 2;
  const toX = targetRect.left + targetRect.width / 2;
  const toY = targetRect.top + targetRect.height / 2;
  const dx = toX - fromX;
  const dy = toY - fromY;
  const dist = Math.hypot(dx, dy);
  const teamVisual = getTeamVisual(teamKeyForCombatant(actor || target));
  const palette = vfxPaletteForEvent(event, teamVisual);
  const moveAnim = moveAnimationProfile(moveMeta, palette);
  const profile = cinematicProfile();
  const speedFactor = moveAnim.channel === "melee" ? 0.76 : moveAnim.channel === "status" ? 1.08 : 0.92;
  const baseDuration = Math.max(220, Math.min(760, dist * 0.95 * speedFactor));
  const rawDamage = Number(event?.damage ?? 0);
  const typeMultiplier = Number(event?.type_multiplier ?? 1);
  const intensity = Math.max(
    0.9,
    Math.min(
      2.0,
      0.95 +
        (Number.isFinite(rawDamage) ? rawDamage / 18 : 0) +
        (event?.crit ? 0.4 : 0) +
        (typeMultiplier >= 2 ? 0.15 : 0)
    )
  );
  const koLikely = Number(event?.target_hp ?? 1) <= 0;
  const narrativeBoost =
    (event?.crit ? 0.2 : 0) + (typeMultiplier >= 2 ? 0.12 : 0) + (koLikely ? 0.18 : 0) - (rawDamage <= 0 ? 0.12 : 0);
  const duration = Math.max(220, Math.min(1400, baseDuration * profile.pace * (1 + narrativeBoost)));
  const typeIconUrl = typeIconFromCache(palette.typeKey);
  if (!typeIconUrl && palette.typeKey && palette.typeKey !== "neutral") {
    ensureTypeIcon(palette.typeKey).then(() => {});
  }
  const moveName = moveMeta?.name || event?.move || "";
  const cachedNamedMoveAnimUrl = moveAnimUrlFromCache(moveName);
  const moveAnimPromise = shouldUseNamedMoveAnim(moveMeta, moveAnim)
    ? (cachedNamedMoveAnimUrl
        ? Promise.resolve(cachedNamedMoveAnimUrl)
        : moveName
          ? ensureMoveAnimAsset(moveName).then((url) => url || null)
          : Promise.resolve(null))
    : Promise.resolve(null);
  const category = palette.category || "";
  const cine = profile;
  const directorShot = _directorShotForMove(actor, target);
  appendCinematicReplay("move", {
    actor: actor?.id || actorRef || "",
    target: target?.id || targetRef || "",
    move: String(moveMeta?.name || event?.move || ""),
    shot: directorShot.type,
    crit: !!event?.crit,
    damage: Number(event?.damage || 0),
  });
  cinematicPhaseActive = true;
  if (isCinematicAutoActive()) {
    if (directorShot.coord) {
      cinematicFocusCoord(directorShot.coord, directorShot.zoom, true, cine.panMs);
    }
    const focusTarget = target?.position || actor?.position || null;
    if (focusTarget) {
      window.setTimeout(() => {
        cinematicFocusCoord(focusTarget, cinematicZoomTarget(), true, cine.panMs);
      }, Math.max(120, Math.min(cine.moveLeadMs, duration * Math.max(0.65, cine.moveFollowFactor))));
    }
  }
  showAttackFootprint(actor, target, moveMeta, Math.max(850, duration + 260));
  const kickoff = isCinematicAutoActive()
    ? cinematicCameraJob.then(
        () =>
          new Promise((resolve) =>
            window.setTimeout(resolve, Math.max(90, Math.min(220, Math.round(cine.actorLockMs * 0.55))))
          )
      )
    : Promise.resolve();

  return new Promise((resolve) => {
    kickoff
      .then(() => {
        sourceCell.classList.add("fx-caster");
        sourceCell.classList.add("fx-caster-cast");
        (targetCell || sourceCell).classList.add("fx-target");
        (targetCell || sourceCell).classList.add("fx-hit-cell");
        return Promise.resolve(moveAnimPromise);
      })
      .catch(() => null)
      .then((resolvedMoveAnimUrl) => {
        const isMelee = moveAnim.channel === "melee";
        const hitDelayMs = isMelee
          ? Math.max(70, Math.min(180, Math.round(duration * 0.45)))
          : Math.max(110, Math.min(520, Math.round(duration * 0.72)));
        const projectile = isMelee ? null : spawnProjectileTravel(fromX, fromY, toX, toY, hitDelayMs, palette, moveAnim, typeIconUrl);
        if (!isMelee) {
          spawnTrail(fromX, fromY, dx, dy, hitDelayMs, palette, moveAnim);
        }
        playMoveImpactCue(palette, moveAnim, intensity, "launch", moveMeta);
        setTimeout(() => {
          projectile?.remove();
          triggerGridShake(intensity);
          playMoveImpactCue(palette, moveAnim, intensity, "impact", moveMeta);
          spawnHitStreaks(toX, toY, palette, intensity, !!event?.crit, moveAnim);
          spawnImpact(
            fromX,
            fromY,
            toX,
            toY,
            sourceRect,
            targetRect,
            resolvedMoveAnimUrl || null,
            intensity
          );
          sourceCell.classList.remove("fx-caster");
          sourceCell.classList.remove("fx-caster-cast");
          (targetCell || sourceCell).classList.remove("fx-target");
          (targetCell || sourceCell).classList.remove("fx-hit-cell");
          cinematicPhaseActive = false;
          if (isCinematicAutoActive() && cine.settleMs > 0) {
            window.setTimeout(resolve, cine.settleMs);
            return;
          }
          resolve();
        }, hitDelayMs);
      });
  });
}

function renderTurnOrder() {
  if (!turnOrderBarEl) return;
  const queue = Array.isArray(state?.turn_order) ? state.turn_order : [];
  turnOrderBarEl.innerHTML = "";
  if (!queue.length) {
    const empty = document.createElement("div");
    empty.className = "turn-empty";
    empty.textContent = "No active queue.";
    turnOrderBarEl.appendChild(empty);
    return;
  }
  queue.forEach((entry, index) => {
    const teamVisual = getTeamVisual(entry.team || "neutral");
    const token = document.createElement("button");
    token.type = "button";
    token.className = "turn-token";
    if (index === 0) token.classList.add("current");
    token.style.setProperty("--team-primary", teamVisual.primary);
    token.style.setProperty("--team-secondary", teamVisual.secondary);
    token.title = `${index === 0 ? "Now" : `Next #${index + 1}`}: ${entry.name} | Priority ${Number(entry.priority || 0)} | Initiative ${Number(entry.initiative_total || 0)}`;
    token.setAttribute("aria-label", token.title);
    token.addEventListener("click", () => {
      selectedId = entry.id;
      armedMove = null;
      render();
    });

    const icon = document.createElement("div");
    icon.className = "turn-icon";
    icon.style.background = `linear-gradient(135deg, ${teamVisual.primary}, ${teamVisual.secondary})`;
    if (!attachTurnSprite(icon, entry.sprite_url, entry.name || "unit")) {
      icon.classList.add("placeholder");
    }
    token.appendChild(icon);

    turnOrderBarEl.appendChild(token);
  });
}

function setCombatantTeamFilter(filter) {
  const next = filter || "all";
  combatantTeamFilter = next;
  statusTabs.forEach((btn) => {
    const isActive = btn.getAttribute("data-team-filter") === next;
    btn.classList.toggle("active", isActive);
    btn.setAttribute("aria-selected", isActive ? "true" : "false");
  });
}

function playItemUseCue(kind = "item") {
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtx) return;
  if (!itemFxAudioCtx) {
    try {
      itemFxAudioCtx = new AudioCtx();
    } catch {
      return;
    }
  }
  const ctx = itemFxAudioCtx;
  if (ctx.state === "suspended") {
    ctx.resume().catch(() => {});
  }
  const now = ctx.currentTime;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = kind === "mega" ? "triangle" : "sine";
  const startFreq = kind === "mega" ? 392 : 740;
  const endFreq = kind === "mega" ? 784 : 988;
  osc.frequency.setValueAtTime(startFreq, now);
  osc.frequency.exponentialRampToValueAtTime(endFreq, now + (kind === "mega" ? 0.24 : 0.12));
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(kind === "mega" ? 0.065 : 0.045, now + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + (kind === "mega" ? 0.3 : 0.16));
  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.start(now);
  osc.stop(now + (kind === "mega" ? 0.32 : 0.18));
}

function resolveMoveSfx(moveMeta, moveAnim, phase = "launch") {
  const moveName = String(moveMeta?.name || "").trim().toLowerCase();
  const exact = MOVE_SFX_EXACT[moveName];
  if (exact?.[phase]) return `/assets/move-sfx/${encodeURIComponent(exact[phase])}`;
  if (exact?.impact) return `/assets/move-sfx/${encodeURIComponent(exact.impact)}`;
  const style = String(moveAnim?.style || "").trim().toLowerCase();
  const byStyle = MOVE_SFX_STYLE[style];
  if (byStyle?.[phase]) return `/assets/move-sfx/${encodeURIComponent(byStyle[phase])}`;
  if (byStyle?.impact) return `/assets/move-sfx/${encodeURIComponent(byStyle.impact)}`;
  return null;
}

function playResolvedMoveSfx(url, volume = 0.42) {
  if (!url) return false;
  let audio = moveFxAudioCache.get(url);
  if (!audio) {
    audio = new Audio(url);
    audio.preload = "auto";
    moveFxAudioCache.set(url, audio);
  }
  try {
    audio.pause();
    audio.currentTime = 0;
    audio.volume = Math.max(0.05, Math.min(1, volume));
    audio.play().catch(() => {});
    return true;
  } catch {
    return false;
  }
}

function spawnFloatingIconFx(centerX, centerY, iconUrl, className = "fx-item-icon") {
  const el = document.createElement("div");
  el.className = className;
  el.style.left = `${centerX}px`;
  el.style.top = `${centerY}px`;
  if (iconUrl) {
    const img = document.createElement("img");
    img.src = iconUrl;
    img.alt = "";
    el.appendChild(img);
  } else {
    el.textContent = "●";
  }
  document.body.appendChild(el);
  return el;
}

function spawnPulseRingFx(centerX, centerY, className = "fx-item-ring", count = 1, gapMs = 90) {
  for (let i = 0; i < count; i += 1) {
    window.setTimeout(() => {
      const ring = document.createElement("div");
      ring.className = className;
      ring.style.left = `${centerX}px`;
      ring.style.top = `${centerY}px`;
      document.body.appendChild(ring);
      const lifetime = ["fx-mega-ring", "fx-primal-ring", "fx-tera-ring", "fx-zmove-ring", "fx-dynamax-ring", "fx-dynamax-break-ring"].includes(className) ? 860 : 520;
      window.setTimeout(() => ring.remove(), lifetime);
    }, i * gapMs);
  }
}

function playMoveImpactCue(palette, moveAnim, intensity = 1, phase = "launch", moveMeta = null) {
  const resolved = resolveMoveSfx(moveMeta, moveAnim, phase);
  const assetVolume = phase === "launch" ? Math.min(0.4, 0.2 + intensity * 0.08) : Math.min(0.62, 0.28 + intensity * 0.12);
  if (playResolvedMoveSfx(resolved, assetVolume)) {
    return;
  }
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtx) return;
  if (!moveFxAudioCtx) {
    try {
      moveFxAudioCtx = new AudioCtx();
    } catch {
      return;
    }
  }
  const ctx = moveFxAudioCtx;
  if (ctx.state === "suspended") {
    ctx.resume().catch(() => {});
  }
  const now = ctx.currentTime;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  const filter = ctx.createBiquadFilter();
  const style = String(moveAnim?.style || "pulse");
  const launch = phase === "launch";
  const baseFreqMap = {
    flame: 220,
    wave: 180,
    spark: 720,
    vine: 260,
    shadow: 160,
    frost: 340,
    psy: 420,
    draco: 250,
    toxic: 210,
    gleam: 560,
    shard: 390,
    quake: 120,
    wind: 310,
    slash: 480,
    pulse: 360,
  };
  const baseFreq = baseFreqMap[style] || 320;
  osc.type = launch ? "triangle" : moveAnim?.channel === "status" ? "sine" : "sawtooth";
  osc.frequency.setValueAtTime(launch ? baseFreq : baseFreq * Math.max(0.72, 1 + intensity * 0.08), now);
  osc.frequency.exponentialRampToValueAtTime(launch ? baseFreq * 1.35 : Math.max(90, baseFreq * 0.72), now + (launch ? 0.08 : 0.12));
  filter.type = launch ? "bandpass" : "lowpass";
  filter.frequency.setValueAtTime(launch ? 1100 : 900, now);
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(launch ? 0.028 : 0.05, now + 0.015);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + (launch ? 0.11 : 0.2));
  osc.connect(filter);
  filter.connect(gain);
  gain.connect(ctx.destination);
  osc.start(now);
  osc.stop(now + (launch ? 0.13 : 0.24));
}

function spawnProjectileTravel(fromX, fromY, toX, toY, duration, palette, moveAnim, typeIconUrl = null) {
  const projectile = document.createElement("div");
  projectile.className = `fx-projectile channel-${moveAnim?.channel || "ranged"} ${moveAnim?.category || ""}`.trim();
  if (moveAnim?.style) projectile.classList.add(`anim-${moveAnim.style}`);
  projectile.style.left = `${fromX}px`;
  projectile.style.top = `${fromY}px`;
  projectile.style.background = `radial-gradient(circle at 35% 35%, ${palette.primary}, ${palette.secondary})`;
  projectile.style.setProperty("--dur", `${Math.max(140, Math.round(duration))}ms`);
  projectile.style.setProperty("--dx", `${Math.round(toX - fromX)}px`);
  projectile.style.setProperty("--dy", `${Math.round(toY - fromY)}px`);
  const iconFriendlyStyles = new Set(["spark", "wave", "frost", "flame"]);
  if (typeIconUrl && iconFriendlyStyles.has(String(moveAnim?.style || "").toLowerCase())) {
    const icon = document.createElement("img");
    icon.className = "fx-projectile-icon";
    icon.src = typeIconUrl;
    icon.alt = "";
    projectile.appendChild(icon);
  }
  document.body.appendChild(projectile);
  requestAnimationFrame(() => {
    projectile.classList.add("run");
  });
  return projectile;
}

function spawnFxBurst(centerX, centerY, className, durationMs) {
  const burst = document.createElement("div");
  burst.className = className;
  burst.style.left = `${centerX}px`;
  burst.style.top = `${centerY}px`;
  document.body.appendChild(burst);
  window.setTimeout(() => burst.remove(), durationMs);
  return burst;
}

function gimmickPalette(kind, detail = "") {
  const normalized = String(detail || "").trim().toLowerCase();
  if (kind === "primal") {
    return normalized.includes("blue")
      ? { primary: "rgba(103, 195, 255, 0.98)", secondary: "rgba(13, 83, 182, 0.94)" }
      : { primary: "rgba(255, 118, 79, 0.98)", secondary: "rgba(165, 33, 9, 0.95)" };
  }
  if (kind === "tera") {
    const palette = TYPE_PALETTE[normalized] || TYPE_PALETTE.normal || TYPE_PALETTE.neutral;
    return {
      primary: palette.primary || "rgba(238, 246, 255, 0.98)",
      secondary: palette.secondary || "rgba(128, 148, 194, 0.95)",
      glow: palette.glow || palette.primary || "rgba(238, 246, 255, 0.98)",
    };
  }
  if (kind === "dynamax") {
    return { primary: "rgba(255, 108, 145, 0.98)", secondary: "rgba(124, 18, 60, 0.95)" };
  }
  if (kind === "zmove") {
    return { primary: "rgba(255, 235, 123, 0.98)", secondary: "rgba(168, 113, 21, 0.95)" };
  }
  return { primary: "rgba(255, 255, 255, 0.98)", secondary: "rgba(135, 152, 173, 0.95)" };
}

function animatePrimalReversionEvent(event) {
  const targetRef = event.target ?? event.target_id ?? event.actor ?? event.actor_id;
  const target = combatantFromEventRef(targetRef);
  const targetCell = cellForCombatant(target);
  if (!targetCell) {
    playItemUseCue("mega");
    return Promise.resolve();
  }
  const itemName = String(event.item || "").trim();
  const palette = gimmickPalette("primal", itemName);
  const targetRect = targetCell.getBoundingClientRect();
  const centerX = targetRect.left + targetRect.width / 2;
  const centerY = targetRect.top + targetRect.height / 2;
  appendCinematicReplay("primal", { actor: target?.id || targetRef || "", item: itemName });
  cinematicPhaseActive = true;
  if (isCinematicAutoActive() && target?.position) {
    cinematicFocusCoord(target.position, Math.max(1.2, cinematicZoomTarget() + 0.08), true, Math.max(220, cinematicProfile().panMs + 40));
  }
  playItemUseCue("mega");
  targetCell.classList.remove("fx-primal-target");
  void targetCell.offsetWidth;
  targetCell.classList.add("fx-primal-target");
  const metaPromise = itemName ? ensureItemMeta(itemName).catch(() => null) : Promise.resolve(null);
  return new Promise((resolve) => {
    Promise.resolve(metaPromise).then((meta) => {
      const orb = spawnFloatingIconFx(centerX, centerY - 28, meta?.icon_url || null, "fx-primal-orb");
      orb.style.setProperty("--fx-primary", palette.primary);
      orb.style.setProperty("--fx-secondary", palette.secondary);
      spawnPulseRingFx(centerX, centerY, "fx-primal-ring", 3, 110);
      const burst = spawnFxBurst(centerX, centerY, "fx-primal-burst", 860);
      burst.style.setProperty("--fx-primary", palette.primary);
      burst.style.setProperty("--fx-secondary", palette.secondary);
      window.setTimeout(() => {
        orb.remove();
        targetCell.classList.remove("fx-primal-target");
        cinematicPhaseActive = false;
        resolve();
      }, 860);
    }).catch(() => {
      targetCell.classList.remove("fx-primal-target");
      cinematicPhaseActive = false;
      resolve();
    });
  });
}

function animateTerastallizeEvent(event) {
  const targetRef = event.target ?? event.target_id ?? event.actor ?? event.actor_id;
  const target = combatantFromEventRef(targetRef);
  const targetCell = cellForCombatant(target);
  if (!targetCell) {
    playItemUseCue("item");
    return Promise.resolve();
  }
  const teraType = String(event.tera_type || "").trim();
  const palette = gimmickPalette("tera", teraType);
  const targetRect = targetCell.getBoundingClientRect();
  const centerX = targetRect.left + targetRect.width / 2;
  const centerY = targetRect.top + targetRect.height / 2;
  appendCinematicReplay("terastal", { actor: target?.id || targetRef || "", tera_type: teraType });
  cinematicPhaseActive = true;
  if (isCinematicAutoActive() && target?.position) {
    cinematicFocusCoord(target.position, Math.max(1.22, cinematicZoomTarget() + 0.1), true, Math.max(220, cinematicProfile().panMs + 50));
  }
  playItemUseCue("item");
  targetCell.classList.remove("fx-tera-target");
  void targetCell.offsetWidth;
  targetCell.classList.add("fx-tera-target");
  const iconPromise = teraType && !typeIconFromCache(teraType) ? ensureTypeIcon(teraType).catch(() => null) : Promise.resolve(null);
  return new Promise((resolve) => {
    Promise.resolve(iconPromise).then(() => {
      const icon = typeIconFromCache(teraType) || null;
      const gem = spawnFloatingIconFx(centerX + 26, centerY - 38, icon, "fx-tera-gem");
      gem.style.setProperty("--fx-primary", palette.primary);
      gem.style.setProperty("--fx-secondary", palette.secondary);
      const trainerGlyph = spawnFloatingIconFx(centerX - 28, centerY - 44, null, "fx-tera-trainer");
      trainerGlyph.textContent = "◈";
      spawnPulseRingFx(centerX, centerY, "fx-tera-ring", 3, 110);
      const burst = spawnFxBurst(centerX, centerY, "fx-tera-burst", 880);
      burst.style.setProperty("--fx-primary", palette.primary);
      burst.style.setProperty("--fx-secondary", palette.secondary);
      window.setTimeout(() => {
        gem.remove();
        trainerGlyph.remove();
        targetCell.classList.remove("fx-tera-target");
        cinematicPhaseActive = false;
        resolve();
      }, 880);
    }).catch(() => {
      targetCell.classList.remove("fx-tera-target");
      cinematicPhaseActive = false;
      resolve();
    });
  });
}

function animateZMoveEvent(event) {
  const actorRef = event.actor ?? event.actor_id ?? event.source;
  const actor = combatantFromEventRef(actorRef);
  const actorCell = cellForCombatant(actor);
  if (!actorCell) {
    playItemUseCue("mega");
    return Promise.resolve();
  }
  const actorRect = actorCell.getBoundingClientRect();
  const centerX = actorRect.left + actorRect.width / 2;
  const centerY = actorRect.top + actorRect.height / 2;
  appendCinematicReplay("zmove", { actor: actor?.id || actorRef || "", move: String(event.move || "") });
  cinematicPhaseActive = true;
  if (isCinematicAutoActive() && actor?.position) {
    cinematicFocusCoord(actor.position, Math.max(1.18, cinematicZoomTarget() + 0.06), true, Math.max(190, cinematicProfile().panMs + 20));
  }
  playItemUseCue("mega");
  actorCell.classList.remove("fx-zmove-target");
  void actorCell.offsetWidth;
  actorCell.classList.add("fx-zmove-target");
  const trainerGlyph = spawnFloatingIconFx(centerX - 24, centerY - 40, null, "fx-zmove-trainer");
  trainerGlyph.textContent = "Z";
  spawnPulseRingFx(centerX, centerY, "fx-zmove-ring", 3, 90);
  spawnFxBurst(centerX, centerY, "fx-zmove-burst", 760);
  return new Promise((resolve) => {
    window.setTimeout(() => {
      trainerGlyph.remove();
      actorCell.classList.remove("fx-zmove-target");
      cinematicPhaseActive = false;
      resolve();
    }, 760);
  });
}

function animateDynamaxEvent(event) {
  const targetRef = event.target ?? event.target_id ?? event.actor ?? event.actor_id;
  const target = combatantFromEventRef(targetRef);
  const targetCell = cellForCombatant(target);
  if (!targetCell) {
    playItemUseCue("mega");
    return Promise.resolve();
  }
  const targetRect = targetCell.getBoundingClientRect();
  const centerX = targetRect.left + targetRect.width / 2;
  const centerY = targetRect.top + targetRect.height / 2;
  const ending = String(event.effect || "").toLowerCase() === "dynamax_end";
  appendCinematicReplay(ending ? "dynamax_end" : "dynamax", { actor: target?.id || targetRef || "" });
  cinematicPhaseActive = true;
  if (isCinematicAutoActive() && target?.position) {
    cinematicFocusCoord(target.position, Math.max(1.2, cinematicZoomTarget() + 0.1), true, Math.max(200, cinematicProfile().panMs + 30));
  }
  playItemUseCue("mega");
  targetCell.classList.remove("fx-dynamax-target");
  void targetCell.offsetWidth;
  targetCell.classList.add("fx-dynamax-target");
  spawnPulseRingFx(centerX, centerY, ending ? "fx-dynamax-break-ring" : "fx-dynamax-ring", 3, 110);
  spawnFxBurst(centerX, centerY, ending ? "fx-dynamax-break" : "fx-dynamax-burst", 860);
  return new Promise((resolve) => {
    window.setTimeout(() => {
      targetCell.classList.remove("fx-dynamax-target");
      cinematicPhaseActive = false;
      resolve();
    }, 860);
  });
}

function animateStatusEvent(event) {
  const effect = String(event?.effect || "").toLowerCase();
  if (effect === "dynamax" || effect === "dynamax_end") {
    return animateDynamaxEvent(event);
  }
  return Promise.resolve();
}

function animateItemEvent(event) {
  const targetRef = event.target ?? event.target_id ?? event.defender ?? event.actor ?? event.actor_id;
  const actorRef = event.actor ?? event.actor_id ?? event.source;
  const target = combatantFromEventRef(targetRef);
  const actor = combatantFromEventRef(actorRef);
  const targetCell = cellForCombatant(target);
  const actorCell = cellForCombatant(actor);
  const itemName = String(event.item || "").trim();
  const effect = String(event.effect || "").trim().toLowerCase();
  if (effect === "mega_evolution") {
    return animateMegaEvolutionEvent(event);
  }
  if (effect === "primal_reversion_ready") {
    return animatePrimalReversionEvent(event);
  }
  if (effect === "teracrystal") {
    return animateTerastallizeEvent(event);
  }
  if (effect === "z_move_activate") {
    return animateZMoveEvent(event);
  }
  if (!targetCell) {
    if (targetRef) {
      playItemUseCue("item");
    }
    return Promise.resolve();
  }
  const targetRect = targetCell.getBoundingClientRect();
  const centerX = targetRect.left + targetRect.width / 2;
  const centerY = targetRect.top + targetRect.height / 2;
  const cachedMeta = itemName ? pokeApiCacheGet(pokeApiItemMetaCache, itemName) : null;
  const itemMetaPromise = itemName ? ensureItemMeta(itemName).catch(() => null) : Promise.resolve(null);
  appendCinematicReplay("item", {
    actor: actor?.id || actorRef || "",
    target: target?.id || targetRef || "",
    item: itemName,
    effect,
  });
  cinematicPhaseActive = true;
  if (isCinematicAutoActive() && target?.position) {
    cinematicFocusCoord(target.position, cinematicZoomTarget(), true, Math.max(160, cinematicProfile().panMs - 40));
  }
  playItemUseCue("item");
  targetCell.classList.remove("fx-item-target");
  void targetCell.offsetWidth;
  targetCell.classList.add("fx-item-target");
  if (actorCell && actorCell !== targetCell) {
    actorCell.classList.remove("fx-item-actor");
    void actorCell.offsetWidth;
    actorCell.classList.add("fx-item-actor");
  }
  return new Promise((resolve) => {
    Promise.resolve(itemMetaPromise)
      .then((meta) => {
        const iconUrl = meta?.icon_url || cachedMeta?.icon_url || null;
        const icon = spawnFloatingIconFx(centerX, centerY - 6, iconUrl, "fx-item-icon");
        spawnPulseRingFx(centerX, centerY, "fx-item-ring", 1, 0);
        window.setTimeout(() => {
          icon.remove();
          targetCell.classList.remove("fx-item-target");
          actorCell?.classList.remove("fx-item-actor");
          cinematicPhaseActive = false;
          resolve();
        }, 440);
      })
      .catch(() => {
        targetCell.classList.remove("fx-item-target");
        actorCell?.classList.remove("fx-item-actor");
        cinematicPhaseActive = false;
        resolve();
      });
  });
}

function animateMegaEvolutionEvent(event) {
  const targetRef = event.target ?? event.target_id ?? event.defender ?? event.actor ?? event.actor_id;
  const actorRef = event.actor ?? event.actor_id ?? event.source;
  const target = combatantFromEventRef(targetRef);
  const actor = combatantFromEventRef(actorRef) || target;
  const targetCell = cellForCombatant(target);
  if (!targetCell) {
    playItemUseCue("mega");
    return Promise.resolve();
  }
  const targetRect = targetCell.getBoundingClientRect();
  const centerX = targetRect.left + targetRect.width / 2;
  const centerY = targetRect.top + targetRect.height / 2;
  const itemName = String(event.item || "").trim();
  appendCinematicReplay("mega", {
    actor: actor?.id || actorRef || "",
    target: target?.id || targetRef || "",
    item: itemName,
    form: String(event.mega_form || ""),
  });
  cinematicPhaseActive = true;
  if (isCinematicAutoActive() && target?.position) {
    cinematicFocusCoord(target.position, Math.max(1.18, cinematicZoomTarget() + 0.08), true, Math.max(220, cinematicProfile().panMs + 40));
  }
  playItemUseCue("mega");
  targetCell.classList.remove("fx-mega-target");
  void targetCell.offsetWidth;
  targetCell.classList.add("fx-mega-target");
  const metaPromise = itemName ? ensureItemMeta(itemName).catch(() => null) : Promise.resolve(null);
  return new Promise((resolve) => {
    Promise.resolve(metaPromise)
      .then((meta) => {
        const stoneIcon = spawnFloatingIconFx(centerX + 26, centerY - 36, meta?.icon_url || null, "fx-mega-stone");
        const trainerGlyph = spawnFloatingIconFx(centerX - 28, centerY - 44, null, "fx-mega-trainer");
        trainerGlyph.textContent = "◇";
        spawnPulseRingFx(centerX, centerY, "fx-mega-ring", 3, 110);
        const burst = document.createElement("div");
        burst.className = "fx-mega-burst";
        burst.style.left = `${centerX}px`;
        burst.style.top = `${centerY}px`;
        document.body.appendChild(burst);
        window.setTimeout(() => {
          stoneIcon.remove();
          trainerGlyph.remove();
          burst.remove();
          targetCell.classList.remove("fx-mega-target");
          cinematicPhaseActive = false;
          resolve();
        }, 820);
      })
      .catch(() => {
        targetCell.classList.remove("fx-mega-target");
        cinematicPhaseActive = false;
        resolve();
      });
  });
}

function _buildStatusTabButton(filter, label) {
  const button = document.createElement("button");
  button.className = "status-tab ds-tab";
  button.type = "button";
  button.setAttribute("data-team-filter", filter);
  button.textContent = label;
  button.addEventListener("click", () => {
    setCombatantTeamFilter(filter);
    render();
  });
  return button;
}

function syncStatusTabs() {
  if (!statusTabsEl) return;
  const liveSideKeys = ((state?.combatants || []).map((combatant) => teamKeyForCombatant(combatant)).filter(Boolean));
  const previewSideKeys = _currentRosterPreview().map((entry) => entry.side).filter(Boolean);
  const sideKeys = Array.from(new Set([...liveSideKeys, ...previewSideKeys]));
  const filters = [{ id: "all", label: "All" }];
  if (!sideKeys.length || sideKeys.includes("player")) filters.push({ id: "player", label: "Player" });
  if (!sideKeys.length || sideKeys.includes("foe")) filters.push({ id: "foe", label: "Foe" });
  sideKeys
    .filter((key) => key !== "player" && key !== "foe")
    .sort((a, b) => formatTeamLabel(a).localeCompare(formatTeamLabel(b)))
    .forEach((key) => {
      filters.push({ id: key, label: formatTeamLabel(key) });
    });
  if (!filters.some((entry) => entry.id === combatantTeamFilter)) {
    combatantTeamFilter = "all";
  }
  statusTabsEl.innerHTML = "";
  statusTabs = filters.map((entry) => {
    const button = _buildStatusTabButton(entry.id, entry.label);
    statusTabsEl.appendChild(button);
    return button;
  });
  setCombatantTeamFilter(combatantTeamFilter);
}

function renderCombatants() {
  combatantListEl.innerHTML = "";
  const appendMiniChip = (row, text, className = "", title = "") => {
    if (!text) return;
    const chip = document.createElement("span");
    chip.className = `combatant-mini-chip${className ? ` ${className}` : ""}`;
    chip.textContent = text;
    if (title) chip.title = title;
    row.appendChild(chip);
  };
  const buildCardShell = (teamKey, spriteUrl, name) => {
    const teamVisual = getTeamVisual(teamKey);
    const card = document.createElement("div");
    card.className = "combatant-card combatant-card-compact";
    card.style.setProperty("--team-primary", teamVisual.primary);
    card.style.setProperty("--team-secondary", teamVisual.secondary);
    attachSprite(card, spriteUrl, name);
    const text = document.createElement("div");
    text.className = "combatant-meta combatant-meta-compact";
    card.appendChild(text);
    return { card, text, teamVisual };
  };
  const appendHpBar = (card, teamVisual, hp, maxHp) => {
    const hpRatio = maxHp ? Math.max(0, Math.min(1, hp / maxHp)) : 0;
    const hpBar = document.createElement("div");
    hpBar.className = "combatant-hpbar";
    const hpFill = document.createElement("div");
    hpFill.className = "combatant-hpfill";
    hpFill.style.width = `${hpRatio * 100}%`;
    hpFill.style.background = healthGradient(teamVisual, hpRatio);
    hpBar.appendChild(hpFill);
    card.appendChild(hpBar);
  };
  const preview = _currentRosterPreview();
  if ((!Array.isArray(state?.combatants) || !state.combatants.length) && preview.length) {
    preview.forEach((entry) => {
      const teamKey = entry.side || "player";
      if (combatantTeamFilter !== "all" && teamKey !== combatantTeamFilter) return;
      const { card, text } = buildCardShell(teamKey, entry.sprite_url, entry.name);
      card.classList.add("staged");
      const head = document.createElement("div");
      head.className = "combatant-head";
      const nameWrap = document.createElement("div");
      nameWrap.className = "combatant-name-wrap";
      const nameLine = document.createElement("div");
      nameLine.className = "combatant-name";
      nameLine.textContent = `${formatTeamLabel(teamKey)} ${entry.slot}: ${entry.name}`;
      nameWrap.appendChild(nameLine);
      const hpLine = document.createElement("div");
      hpLine.className = "combatant-hp";
      hpLine.textContent = [
        entry.level ? `Lv ${entry.level}` : "",
        entry.nature || "",
        entry.ability ? `Ability ${entry.ability}` : "",
      ]
        .filter(Boolean)
        .join(" | ") || "Staged roster entry";
      nameWrap.appendChild(hpLine);
      head.appendChild(nameWrap);
      const hpBadge = document.createElement("div");
      hpBadge.className = "combatant-hp-number";
      hpBadge.textContent = entry.stats?.hp ? `HP ${entry.stats.hp}` : "Preview";
      head.appendChild(hpBadge);
      text.appendChild(head);
      const quickRow = document.createElement("div");
      quickRow.className = "combatant-quick-row";
      [
        entry.stats?.atk ? `Atk ${entry.stats.atk}` : "",
        entry.stats?.def ? `Def ${entry.stats.def}` : "",
        entry.stats?.spatk ? `SpA ${entry.stats.spatk}` : "",
        entry.stats?.spdef ? `SpD ${entry.stats.spdef}` : "",
        entry.stats?.spd ? `Spd ${entry.stats.spd}` : "",
      ].filter(Boolean).forEach((label) => appendMiniChip(quickRow, label));
      if (quickRow.childElementCount) text.appendChild(quickRow);
      if (entry.item || (entry.moves && entry.moves.length)) {
        const itemRow = document.createElement("div");
        itemRow.className = "combatant-item-row";
        if (entry.item) {
          appendMiniChip(itemRow, entry.item, "item", `Item: ${entry.item}`);
        }
        (entry.moves || []).slice(0, 4).forEach((move) => {
          appendMiniChip(itemRow, move, "move");
        });
        text.appendChild(itemRow);
      }
      card.appendChild(text);
      combatantListEl.appendChild(card);
    });
    return;
  }
  if (!Array.isArray(state?.combatants) || !state.combatants.length) {
    return;
  }
  const hideFainted = !!hideFaintedToggle?.checked;
  state.combatants.forEach((combatant) => {
    const teamKey = teamKeyForCombatant(combatant);
    if (combatantTeamFilter !== "all" && teamKey !== combatantTeamFilter) {
      return;
    }
    if (hideFainted && combatant.fainted) {
      return;
    }
    const { card, text, teamVisual } = buildCardShell(teamKey, combatant.sprite_url, combatant.name);
    if (combatant.id === selectedId) {
      card.classList.add("active");
    }
    if (combatant.fainted) {
      card.classList.add("fainted");
    }
    if (combatant.id === state?.current_actor_id) {
      card.classList.add("is-current");
    }
    if (combatant.active && !combatant.fainted) {
      const badge = document.createElement("div");
      badge.className = "combatant-badge";
      badge.textContent = "Active";
      card.appendChild(badge);
    }
    const head = document.createElement("div");
    head.className = "combatant-head";
    const nameWrap = document.createElement("div");
    nameWrap.className = "combatant-name-wrap";
    const nameLine = document.createElement("div");
    nameLine.className = "combatant-name";
    nameLine.textContent = `${combatant.marker} ${combatant.name}`;
    nameWrap.appendChild(nameLine);

    const hpLine = document.createElement("div");
    hpLine.className = "combatant-hp";
    const hpParts = [`${formatTeamLabel(teamKey)} | HP ${combatant.hp}/${combatant.max_hp}`];
    if (Number(combatant.temp_hp || 0) > 0) hpParts.push(`Temp ${Number(combatant.temp_hp || 0)}`);
    if (Number(combatant.injuries || 0) > 0) hpParts.push(`Injuries ${Number(combatant.injuries || 0)}`);
    hpLine.textContent = hpParts.join(" | ");
    nameWrap.appendChild(hpLine);
    head.appendChild(nameWrap);
    const hpBadge = document.createElement("div");
    hpBadge.className = "combatant-hp-number";
    hpBadge.textContent = `${combatant.hp}/${combatant.max_hp}`;
    head.appendChild(hpBadge);
    text.appendChild(head);

    if (combatant.position || combatant.nature || (Array.isArray(combatant.abilities) && combatant.abilities.length)) {
      const quickRow = document.createElement("div");
      quickRow.className = "combatant-quick-row";
      [
        combatant.position ? `Pos ${combatant.position.join(",")}` : "",
        combatant.nature ? combatant.nature : "",
        Array.isArray(combatant.abilities) && combatant.abilities.length ? combatant.abilities[0] : "",
      ]
        .filter(Boolean)
        .forEach((label, index) => appendMiniChip(quickRow, label, index === 0 ? "accent" : ""));
      if (quickRow.childElementCount) text.appendChild(quickRow);
    }

    const statusRow = document.createElement("div");
    statusRow.className = "combatant-status-row";
    (combatant.statuses || []).forEach((status) => {
      const chip = document.createElement("span");
      const visual = statusVisualKey(status);
      chip.className = `combatant-status-chip status-${visual}`;
      chip.setAttribute("data-status", visual);
      chip.textContent = String(status);
      statusRow.appendChild(chip);
    });
    if (statusRow.childElementCount) {
      text.appendChild(statusRow);
    }

    const normalizedItems = normalizeCombatantItems(combatant.items || []);
    if (normalizedItems.length) {
      const itemRow = document.createElement("div");
      itemRow.className = "combatant-item-row";
      normalizedItems.slice(0, 4).forEach((item) => {
        appendMiniChip(
          itemRow,
          item.name,
          "item",
          item.effect_description || item.effect_summary?.join(" | ") || `Item: ${item.name}`
        );
      });
      text.appendChild(itemRow);
    }

    const effectRow = document.createElement("div");
    effectRow.className = "combatant-move-row";
    if (Number(combatant.injuries || 0) > 0) {
      appendMiniChip(effectRow, `Injuries ${Number(combatant.injuries || 0)}`, "warning");
    }
    if (Number(combatant.temp_hp || 0) > 0) {
      appendMiniChip(effectRow, `Temp HP ${Number(combatant.temp_hp || 0)}`, "ready");
    }
    (combatant.passive_item_effects || []).slice(0, 2).forEach((effect) => {
      appendMiniChip(effectRow, effect, "", effect);
    });
    const gimmicks = combatant.gimmicks || {};
    if (gimmicks.mega_form) appendMiniChip(effectRow, `Mega ${gimmicks.mega_form}`, "accent");
    if (gimmicks.primal_reversion_ready) appendMiniChip(effectRow, `Primal ${gimmicks.primal_reversion_ready}`, "accent");
    if (gimmicks.dynamax_active) appendMiniChip(effectRow, "Dynamax", "accent");
    if (gimmicks?.terastallized?.tera_type) appendMiniChip(effectRow, `Tera ${gimmicks.terastallized.tera_type}`, "accent");
    if (effectRow.childElementCount) {
      text.appendChild(effectRow);
    }

    const moveNames = Array.isArray(combatant.moves)
      ? combatant.moves
          .map((moveEntry) => (typeof moveEntry === "string" ? moveEntry : String(moveEntry?.name || "")))
          .filter(Boolean)
          .slice(0, 4)
      : [];
    if (moveNames.length) {
      const moveRow = document.createElement("div");
      moveRow.className = "combatant-move-row";
      moveNames.forEach((moveName) => appendMiniChip(moveRow, moveName, "move"));
      text.appendChild(moveRow);
    }

    appendHpBar(card, teamVisual, combatant.hp, combatant.max_hp);
    card.addEventListener("click", () => {
      selectedId = combatant.id;
      armedMove = null;
      render();
    });
    combatantListEl.appendChild(card);
  });
}

function renderPartyBar() {
  if (!partyBarEl) return;
  const preview = _currentRosterPreview();
  if ((!Array.isArray(state?.combatants) || !state.combatants.length) && preview.length) {
    const teams = {};
    preview.forEach((entry) => {
      if (!teams[entry.side]) {
        teams[entry.side] = { key: entry.side, label: formatTeamLabel(entry.side), members: [] };
      }
      teams[entry.side].members.push(entry);
    });
    const entries = Object.values(teams).sort((a, b) => a.label.localeCompare(b.label));
    partyBarEl.innerHTML = "";
    entries.forEach((entry) => {
      const teamVisual = getTeamVisual(entry.key);
      const row = document.createElement("div");
      row.className = "party-row";
      row.style.setProperty("--team-primary", teamVisual.primary);
      row.style.setProperty("--team-secondary", teamVisual.secondary);
      const label = document.createElement("div");
      label.className = "party-label";
      label.textContent = entry.label;
      const meter = document.createElement("div");
      meter.className = "party-meter";
      entry.members.forEach((member) => {
        const segment = document.createElement("div");
        segment.className = "party-segment";
        const segmentFill = document.createElement("div");
        segmentFill.className = "party-segment-fill";
        segmentFill.style.width = "100%";
        segmentFill.style.background = teamVisual.primary;
        segment.title = `${member.name}${member.level ? `: Lv ${member.level}` : ""}`;
        segment.appendChild(segmentFill);
        meter.appendChild(segment);
      });
      const count = document.createElement("div");
      count.className = "party-count";
      count.textContent = `${entry.members.length} staged`;
      row.appendChild(label);
      row.appendChild(meter);
      row.appendChild(count);
      partyBarEl.appendChild(row);
    });
    return;
  }
  if (!Array.isArray(state?.combatants) || !state.combatants.length) {
    partyBarEl.innerHTML = "";
    return;
  }
  const teams = {};
  (state.combatants || []).forEach((combatant) => {
    const teamKey = teamKeyForCombatant(combatant);
    if (!teams[teamKey]) {
      teams[teamKey] = {
        key: teamKey,
        label: formatTeamLabel(teamKey),
        hp: 0,
        max: 0,
        active: 0,
        members: [],
      };
    }
    teams[teamKey].hp += combatant.hp || 0;
    teams[teamKey].max += combatant.max_hp || 0;
    teams[teamKey].members.push(combatant);
    if (combatant.active && !combatant.fainted) {
      teams[teamKey].active += 1;
    }
  });
  const entries = Object.values(teams);
  entries.sort((a, b) => a.label.localeCompare(b.label));
  partyBarEl.innerHTML = "";
  entries.forEach((entry) => {
    const teamVisual = getTeamVisual(entry.key);
    const row = document.createElement("div");
    row.className = "party-row";
    row.style.setProperty("--team-primary", teamVisual.primary);
    row.style.setProperty("--team-secondary", teamVisual.secondary);
    row.addEventListener("click", () => cycleTeamSelection(entry.key));
    const label = document.createElement("div");
    label.className = "party-label";
    label.textContent = entry.label;
    const meter = document.createElement("div");
    meter.className = "party-meter";
    const sortedMembers = [...entry.members].sort((a, b) => String(a.marker).localeCompare(String(b.marker)));
    sortedMembers.forEach((member) => {
      const segment = document.createElement("div");
      segment.className = "party-segment";
      if (member.fainted) {
        segment.classList.add("fainted");
      }
      segment.style.flexGrow = String(Math.max(1, Number(member.max_hp) || 1));
      const segmentFill = document.createElement("div");
      segmentFill.className = "party-segment-fill";
      const ratio = member.max_hp ? member.hp / member.max_hp : 0;
      segmentFill.style.width = `${Math.max(0, Math.min(1, ratio)) * 100}%`;
      segmentFill.style.background = healthGradient(teamVisual, ratio);
      segment.title = `${member.name}: ${member.hp}/${member.max_hp}`;
      segment.appendChild(segmentFill);
      meter.appendChild(segment);
    });
    const count = document.createElement("div");
    count.className = "party-count";
    const ready = entry.members.filter((member) => !member.fainted).length;
    count.textContent = `${entry.active} active | ${ready}/${entry.members.length} ready | ${entry.hp}/${entry.max}`;
    row.appendChild(label);
    row.appendChild(meter);
    row.appendChild(count);
    partyBarEl.appendChild(row);
  });
}

function cycleTeamSelection(teamKey) {
  const teamMembers = (state.combatants || []).filter(
    (c) => teamKeyForCombatant(c) === teamKey && c.active && !c.fainted
  );
  if (!teamMembers.length) return;
  const currentIndex = teamMembers.findIndex((c) => c.id === selectedId);
  const nextIndex = currentIndex === -1 ? 0 : (currentIndex + 1) % teamMembers.length;
  selectedId = teamMembers[nextIndex].id;
  render();
}

function bindCombatantListTooltips() {
  const targets = combatantListEl?.querySelectorAll("[data-tooltip-title][data-tooltip-body]") || [];
  targets.forEach((target) => {
    target.addEventListener("mouseenter", () => {
      const title = target.getAttribute("data-tooltip-title") || target.textContent || "Details";
      const body = target.getAttribute("data-tooltip-body") || "";
      showDetailTooltip(target, title, body);
    });
    target.addEventListener("mouseleave", () => {
      scheduleTooltipHide();
    });
  });
}

async function playCryForSpecies(speciesName) {
  const url = await ensureCryUrl(speciesName);
  if (!url) return false;
  try {
    cryAudio.pause();
    cryAudio.currentTime = 0;
    cryAudio.src = url;
    await cryAudio.play();
    return true;
  } catch {
    return false;
  }
}

function chipHtml({ text, iconUrl = null, iconBadge = null, tooltipTitle = "", tooltipBody = "", className = "", dataStatus = "" }) {
  const safeText = escapeHtml(text);
  const safeTooltipTitle = escapeAttr(tooltipTitle || "");
  const safeTooltipBody = escapeAttr(tooltipBody || "");
  const safeClass = String(className || "").trim();
  const safeStatus = String(dataStatus || "").trim();
  const tooltipAttrs =
    safeTooltipBody && safeTooltipTitle
      ? ` data-tooltip-title="${safeTooltipTitle}" data-tooltip-body="${safeTooltipBody}"`
      : "";
  const statusAttr = safeStatus ? ` data-status="${escapeAttr(safeStatus)}"` : "";
  const iconPart = iconUrl
    ? `<img class="chip-icon" src="${escapeHtml(iconUrl)}" alt="" />`
    : iconBadge
      ? `<span class="chip-icon badge">${escapeHtml(iconBadge)}</span>`
      : "";
  return `<span class="chip${safeClass ? ` ${escapeAttr(safeClass)}` : ""}"${statusAttr}${tooltipAttrs}>${iconPart}<span>${safeText}</span></span>`;
}

function bestEffectDescription(meta, fallbackName, unavailableText = "Description unavailable.") {
  const value = String(meta?.effect || "").trim();
  if (!value) return unavailableText;
  const normalizedValue = value.toLowerCase();
  const normalizedName = String(fallbackName || "").trim().toLowerCase();
  if (
    !normalizedValue ||
    normalizedValue === normalizedName ||
    normalizedValue === "none" ||
    normalizedValue === "n/a" ||
    normalizedValue === "-" ||
    normalizedValue === "--"
  ) {
    return unavailableText;
  }
  return value;
}

function isPlaceholderRuleText(text, fallbackName = "") {
  const value = String(text || "").trim().toLowerCase();
  if (!value) return true;
  if (value === "--" || value === "-" || value === "n/a" || value === "none") return true;
  if (fallbackName && value === String(fallbackName || "").trim().toLowerCase()) return true;
  return false;
}

function extractRangeKeywords(rangeText) {
  const raw = String(rangeText || "").split(",");
  const ignored = new Set([
    "melee",
    "ranged",
    "self",
    "field",
    "line",
    "cone",
    "burst",
    "blast",
    "close blast",
    "closeblast",
    "target",
    "targets",
    "ally",
    "allies",
    "enemy",
    "enemies",
    "foe",
    "foes",
  ]);
  const keywords = [];
  raw.forEach((part) => {
    const token = String(part || "").trim();
    if (!token) return;
    const lower = token.toLowerCase();
    if (ignored.has(lower)) return;
    if (/^\\d+$/.test(lower)) return;
    if (/^\\d+\\s*(target|targets)$/.test(lower)) return;
    keywords.push(token);
  });
  return keywords;
}

function buildMoveSummary(meta) {
  if (!meta) return "";
  const type = String(meta?.type || "").trim();
  const category = String(meta?.category || meta?.damage_class || "").trim();
  const frequency = String(meta?.frequency || "").trim();
  const range = String(meta?.range || "").trim();
  const ac = Number(meta?.ac);
  const db = Number(meta?.damage_base);
  const parts = [];
  if (type || category) {
    parts.push(`Type: ${type || "Unknown"} | Category: ${category || "Unknown"}`);
  }
  if (Number.isFinite(ac) && ac > 0) {
    parts.push(`Accuracy Check: d20 >= ${ac}`);
  } else {
    parts.push("Accuracy Check: none");
  }
  if (Number.isFinite(db) && db > 0 && String(category).toLowerCase() !== "status") {
    parts.push(`Damage Base: ${db}`);
  } else if (String(category).toLowerCase() === "status") {
    parts.push("Damage Base: status/no direct damage");
  }
  if (range) parts.push(`Range: ${range}`);
  if (frequency) parts.push(`Frequency: ${frequency}`);
  return parts.join("\n");
}

function injuryColor(index, total) {
  const safeTotal = Math.max(1, total);
  const ratio = Math.min(1, Math.max(0, (index + 1) / safeTotal));
  const hue = 5;
  const sat = Math.round(70 + ratio * 10);
  const light = Math.round(64 - ratio * 18);
  return `hsl(${hue}deg ${sat}% ${light}%)`;
}

function buildInjuryTooltip(count) {
  const lines = [];
  for (let i = 0; i < count; i += 1) {
    lines.push(`Injury ${i + 1}: -1 Tick to max HP`);
  }
  if (count >= 5) {
    lines.push("");
    lines.push("At 5+ injuries, Standard actions cause injury backlash equal to injuries.");
  }
  lines.push("");
  lines.push("Optional injury stage loss may apply if enabled.");
  return lines.join("\n");
}

function normalizeFieldName(value) {
  return String(value || "").trim();
}

function terrainNameValue(terrain) {
  if (!terrain) return "";
  if (typeof terrain === "string") return terrain;
  if (terrain.name) return terrain.name;
  if (terrain.terrain) return terrain.terrain;
  if (terrain.type) return terrain.type;
  if (terrain.effect) return terrain.effect;
  return "";
}

function tileTypeTokens(tileType) {
  return String(tileType || "")
    .split(/[,;/|]+/)
    .map((part) => part.trim().toLowerCase())
    .filter(Boolean);
}

function terrainTooltipBody(terrain) {
  if (!terrain) return "Terrain: none.";
  const name = normalizeFieldName(terrainNameValue(terrain));
  if (!name) return "Terrain: none.";
  const lower = name.toLowerCase();
  const lines = [];
  lines.push(`Terrain: ${name}`);
  if (Number.isFinite(Number(terrain.remaining))) {
    lines.push(`Remaining: ${terrain.remaining} rounds`);
  }
  if (lower.startsWith("grassy")) {
    lines.push("Grounded creatures heal 1/16 max HP at end of turn; Grass moves gain +1 DB.");
  } else if (lower.startsWith("electric")) {
    lines.push("Grounded creatures cannot be put to Sleep; Electric moves gain +1 DB.");
  } else if (lower.startsWith("misty")) {
    lines.push("Grounded creatures cannot gain new status conditions; Dragon moves lose 1 DB.");
  } else if (lower.startsWith("psychic")) {
    lines.push("Priority moves fail against grounded targets; Psychic moves gain +1 DB.");
  } else if (lower.includes("gravity") || lower.includes("warped")) {
    lines.push("Flight and Levitate-like effects are suppressed; ranged accuracy becomes harsher.");
  }
  return lines.join("\n");
}

function weatherTooltipBody(weather) {
  const name = normalizeFieldName(weather);
  if (!name || name.toLowerCase() === "clear") return "Weather: clear.";
  const lower = name.toLowerCase();
  const lines = [];
  lines.push(`Weather: ${name}`);
  if (lower.includes("rain") || lower.includes("downpour") || lower.includes("storm")) {
    lines.push("Water moves gain +1 DB; Fire moves lose 1 DB. Some weather abilities may trigger.");
  } else if (lower.includes("sun")) {
    lines.push("Fire moves gain +1 DB; Water moves lose 1 DB. Certain abilities trigger.");
  } else if (lower.includes("sand")) {
    lines.push("Non-ground/rock/steel may take chip damage; Rock gains Sp. Def bonuses.");
  } else if (lower.includes("hail") || lower.includes("snow")) {
    lines.push("Non-ice may take chip damage; Ice-related effects may trigger.");
  }
  return lines.join("\n");
}

function tileTypeLabel(tileType) {
  const tokens = tileTypeTokens(tileType);
  if (!tokens.length) return "Normal";
  const labels = tokens.map((value) => {
    if (value === "water") return "Water";
    if (value === "difficult" || value === "rough") return "Difficult Terrain";
    if (value === "blocker" || value === "blocking" || value === "wall") return "Blocking Terrain";
    return value.replace(/_/g, " ");
  });
  return Array.from(new Set(labels)).join(" / ");
}

function tileTypeDescription(tileType) {
  const tokens = tileTypeTokens(tileType);
  if (!tokens.length) return "Normal ground tile with no special movement rules.";
  const notes = [];
  if (tokens.includes("water")) {
    notes.push("Water tile: swim-capable movement is favored; many grounded effects may be limited.");
  }
  if (tokens.includes("difficult") || tokens.includes("rough")) {
    notes.push("Difficult terrain: movement costs extra, reducing effective shift distance.");
  }
  if (tokens.includes("blocker") || tokens.includes("blocking") || tokens.includes("wall")) {
    notes.push("Blocking terrain: line of sight and movement can be blocked.");
  }
  if (!notes.length) {
    notes.push(`Special tile tags: ${tokens.join(", ")}.`);
  }
  return notes.join(" ");
}

function trapBadgeTitle(entry, meta) {
  const suffix = entry.layers > 1 ? ` x${entry.layers}` : "";
  if (entry.kind !== "trap") return `${entry.name}${suffix}`;
  const trapSource = meta?.trap_sources?.[normalizePokeKey(entry.name)];
  const detail = trapEffectSummary(entry.name);
  const parts = [`${entry.name}${suffix}`];
  if (detail) parts.push(detail);
  if (trapSource?.trap_name) parts.push(`Source: ${trapSource.trap_name}`);
  if (trapSource?.source_id) parts.push(`Owner: ${trapSource.source_id}`);
  return parts.join(" | ");
}

function barrierBadgeTitle(entry) {
  const source = String(entry?.source_name || entry?.move || "Barrier").trim() || "Barrier";
  const owner = String(entry?.source_id || "").trim();
  return owner ? `${source} | Owner: ${owner}` : source;
}

function buildTileTooltip(meta, x, y) {
  const lines = [];
  lines.push(`Tile: ${x},${y}`);
  lines.push(`Type: ${tileTypeLabel(meta?.type)}`);
  lines.push(tileTypeDescription(meta?.type));
  const blockers = new Set((state?.grid?.blockers || []).map((c) => `${c[0]},${c[1]}`));
  const isBlocked = blockers.has(`${x},${y}`);
  const occupantId = state?.occupants ? state.occupants[`${x},${y}`] : null;
  const occupant = occupantId
    ? (state?.combatants || []).find((entry) => entry.id === occupantId)
    : null;
  lines.push(`Blocker: ${isBlocked ? "Yes" : "No"}`);
  lines.push(`Occupant: ${occupant ? occupant.name || occupant.species || occupant.id : "None"}`);
  const hazardEntries = collectTileHazards(meta?.hazards, meta?.traps);
  if (hazardEntries.length) {
    lines.push("");
    lines.push("Hazards:");
    hazardEntries.forEach((entry) => {
      const suffix = entry.layers > 1 ? ` x${entry.layers}` : "";
      lines.push(`- ${entry.name}${suffix}`);
      if (entry.kind === "trap") {
        const trapSource = meta?.trap_sources?.[normalizePokeKey(entry.name)];
        const effect = trapEffectSummary(entry.name);
        if (effect) {
          lines.push(`  Effect: ${effect}`);
        }
        if (trapSource?.trap_name) {
          lines.push(`  Source: ${trapSource.trap_name}`);
        }
      }
    });
  }
  const barriers = Array.isArray(meta?.barriers) ? meta.barriers : [];
  if (barriers.length) {
    lines.push("");
    lines.push("Barriers:");
    barriers.forEach((entry, index) => {
      const source = String(entry?.source_name || entry?.move || "Barrier").trim();
      const owner = String(entry?.source_id || "").trim();
      lines.push(`- Segment ${index + 1}: ${source}${owner ? ` (${owner})` : ""}`);
    });
  }
  const frozen = frozenDomainEntries(meta);
  if (frozen.length) {
    lines.push("");
    lines.push("Frozen Domain:");
    frozen.forEach((entry, index) => {
      lines.push(`- Tile ${index + 1}: ${frozenDomainSummary(entry)}`);
      lines.push("  Effect: Acrobatics check or become Tripped. Acts as Hail while standing here. Fire clears this tile.");
    });
  }
  const terrainName = state?.terrain && typeof state.terrain === "object" ? state.terrain.name : state?.terrain;
  if (terrainName) {
    lines.push("");
    lines.push(terrainTooltipBody(state.terrain));
  }
  return lines.join("\n");
}

function bestMoveDescription(move, moveMeta) {
  const lines = [];
  const moveName = String(move?.name || "").trim() || "Unknown Move";
  const type = String(move?.type || moveMeta?.type || "").trim() || "Unknown";
  const category = String(move?.category || moveMeta?.damage_class || "").trim() || "Unknown";
  const frequency = String(move?.freq || "").trim() || "Unspecified";
  const rangeText = String(move?.range || "").trim() || "Unspecified";
  const target = String(move?.target || moveMeta?.target || "").trim() || "Unspecified";
  const priority = Number(move?.priority);
  const ac = Number(move?.ac);
  const db = Number(move?.db);
  const keywords = Array.isArray(move?.keywords)
    ? move.keywords.map((entry) => String(entry || "").trim()).filter(Boolean)
    : [];

  lines.push(`Type: ${type} | Category: ${category}`);
  if (Number.isFinite(ac) && ac > 0) {
    lines.push(`Accuracy Check: d20 >= ${ac} (before Accuracy/Evasion and other modifiers).`);
  } else {
    lines.push("Accuracy Check: none (move resolves without a normal AC roll).");
  }
  if (Number.isFinite(db) && db > 0 && String(category).toLowerCase() !== "status") {
    lines.push(`Damage Base: ${db} (engine then applies stats, STAB, effectiveness, weather, abilities, and items).`);
  } else {
    lines.push("Damage Base: status/no direct damage unless effect text says otherwise.");
  }
  lines.push(`Range: ${rangeText}`);
  lines.push(`Targeting: ${target}`);
  lines.push(`Frequency: ${frequency}`);
  if (Number.isFinite(priority) && priority !== 0) {
    lines.push(`Priority: ${priority > 0 ? `+${priority}` : String(priority)}`);
  }
  if (keywords.length) {
    lines.push(`Keywords: ${keywords.join(", ")}`);
  }
  const rawRulesText = String(move?.effects || "").trim();
  const rulesIsPlaceholder = isPlaceholderRuleText(rawRulesText, moveName);
  const rulesText = rulesIsPlaceholder ? "" : rawRulesText;
  if (rulesText) {
    lines.push("");
    lines.push("PTU Rule Text:");
    lines.push(rulesText);
  } else if (rawRulesText) {
    lines.push("");
    lines.push("PTU Rule Text:");
    lines.push("None listed (no additional effect beyond standard resolution).");
  } else {
    const rangeKeywords = extractRangeKeywords(move?.range);
    if (rangeKeywords.length) {
      lines.push("");
      lines.push("Range Keywords:");
      lines.push(rangeKeywords.join(", "));
    }
  }
  const externalText = bestEffectDescription(moveMeta, moveName, "");
  if (externalText && externalText !== rulesText) {
    lines.push("");
    lines.push("Reference:");
    lines.push(externalText);
  }
  if (lines.length <= 1) {
    lines.push("No description available.");
  }
  return lines.join("\n");
}

function renderStatusChips(statuses) {
  if (!Array.isArray(statuses) || !statuses.length) return "-";
  const chips = statuses.map((statusName) => {
    const visual = statusVisualKey(statusName);
    return chipHtml({
      text: statusName,
      className: `status-${visual}`,
      dataStatus: visual,
      tooltipTitle: `Status: ${statusName}`,
      tooltipBody: statusName,
    });
  });
  return `<div class="chip-group">${chips.join("")}</div>`;
}

function renderAbilityChips(abilities) {
  if (!Array.isArray(abilities) || !abilities.length) return "-";
  const chips = abilities.map((abilityName) => {
    const meta = pokeApiCacheGet(pokeApiAbilityMetaCache, abilityName);
    if (!pokeApiCacheHas(pokeApiAbilityMetaCache, abilityName)) {
      ensureAbilityMeta(abilityName).then(() => scheduleRerender());
    }
    const badge = meta?.id ? `A${meta.id}` : "A";
    return chipHtml({
      text: abilityName,
      iconBadge: badge,
      tooltipTitle: `Ability: ${abilityName}`,
      tooltipBody: bestEffectDescription(meta, abilityName),
    });
  });
  return `<div class="chip-group">${chips.join("")}</div>`;
}

function renderItemChips(items) {
  if (!Array.isArray(items) || !items.length) return "-";
  const chips = normalizeCombatantItems(items).map((item) => {
    const itemName = item.name;
    const meta = pokeApiCacheGet(pokeApiItemMetaCache, itemName);
    if (!pokeApiCacheHas(pokeApiItemMetaCache, itemName)) {
      ensureItemMeta(itemName).then(() => scheduleRerender());
    }
    const summaryLines = Array.isArray(item.effect_summary) ? item.effect_summary.filter(Boolean) : [];
    const description = String(item.effect_description || "").trim();
    const tooltipParts = [];
    if (summaryLines.length) {
      tooltipParts.push(summaryLines.join("\n"));
    }
    if (description) {
      tooltipParts.push(description);
    } else if (meta?.effect) {
      tooltipParts.push(meta.effect);
    }
    return chipHtml({
      text: itemName,
      iconUrl: meta?.icon_url || null,
      iconBadge: meta?.icon_url ? null : "I",
      tooltipTitle: `Item: ${itemName}`,
      tooltipBody: tooltipParts.join("\n\n") || "Description unavailable.",
      className: item.equipped ? "chip-equipped" : "",
    });
  });
  return `<div class="chip-group">${chips.join("")}</div>`;
}

function normalizeCombatantItems(items) {
  if (!Array.isArray(items)) return [];
  return items
    .map((item) => {
      if (!item) return null;
      if (typeof item === "string") {
        const name = String(item || "").trim();
        return name ? { name, equipped: true, visible_on_token: true, kind: "", slot: "" } : null;
      }
      if (typeof item === "object") {
        const name = String(item.name || "").trim();
        if (!name) return null;
        return {
          name,
          equipped: Boolean(item.equipped),
          visible_on_token: item.visible_on_token !== false,
          kind: String(item.kind || "").trim(),
          slot: String(item.slot || "").trim(),
          effect_summary: Array.isArray(item.effect_summary) ? item.effect_summary : [],
          effect_description: String(item.effect_description || "").trim(),
        };
      }
      const name = String(item || "").trim();
      return name ? { name, equipped: true, visible_on_token: true, kind: "", slot: "" } : null;
    })
    .filter(Boolean);
}

function classifyCombatItem(item) {
  const slot = String(item?.slot || "").trim().toLowerCase();
  const kind = String(item?.kind || "").trim().toLowerCase();
  const name = String(item?.name || "").trim().toLowerCase();
  if (kind === "weapon" || slot.includes("wield") || slot.includes("weapon")) {
    return "weapon";
  }
  if (slot.includes("held") || slot.includes("hand")) {
    return "held";
  }
  if (slot.includes("belt")) {
    return "belt";
  }
  if (slot.includes("accessory") || slot.includes("worn") || slot.includes("wear")) {
    return "worn";
  }
  if (name.includes("berry")) {
    return "held";
  }
  return "gear";
}

function tokenDisplayItems(combatant) {
  const items = normalizeCombatantItems(combatant?.items || []);
  if (!items.length) return [];
  const visible = items.filter((item) => item.visible_on_token);
  const preferred = visible.length ? visible : items;
  const order = { held: 0, worn: 1, weapon: 2, belt: 3, gear: 4 };
  return preferred
    .map((item) => ({ ...item, tokenClass: classifyCombatItem(item) }))
    .sort((a, b) => {
      if (a.equipped !== b.equipped) return a.equipped ? -1 : 1;
      const aRank = order[a.tokenClass] ?? 99;
      const bRank = order[b.tokenClass] ?? 99;
      if (aRank !== bRank) return aRank - bRank;
      return a.name.localeCompare(b.name);
    })
    .slice(0, 4);
}

function appendTokenItemIcons(cell, combatant) {
  const items = tokenDisplayItems(combatant);
  if (!items.length) return;
  const groups = new Map();
  items.forEach((item) => {
    const key = item.tokenClass || "gear";
    if (!groups.has(key)) {
      const group = document.createElement("div");
      group.className = `token-item-group token-item-group-${key}`;
      groups.set(key, group);
    }
    const meta = pokeApiCacheGet(pokeApiItemMetaCache, item.name);
    if (!pokeApiCacheHas(pokeApiItemMetaCache, item.name)) {
      ensureItemMeta(item.name).then(() => scheduleRerender());
    }
    const icon = document.createElement("div");
    icon.className = `token-item token-item-${item.tokenClass || "gear"}${item.equipped ? " equipped" : ""}`;
    if (meta?.icon_url) {
      const img = document.createElement("img");
      img.src = meta.icon_url;
      img.alt = item.name;
      img.loading = "lazy";
      icon.appendChild(img);
    } else {
      icon.textContent = item.name.charAt(0).toUpperCase();
    }
    icon.addEventListener("mouseenter", () => {
      showDetailTooltip(icon, `Item: ${item.name}`, meta?.effect || "Item description unavailable.");
    });
    icon.addEventListener("mouseleave", () => {
      scheduleTooltipHide();
    });
    groups.get(key).appendChild(icon);
  });
  const wrap = document.createElement("div");
  wrap.className = "token-item-stack";
  ["held", "worn", "weapon", "belt", "gear"].forEach((key) => {
    const group = groups.get(key);
    if (group) wrap.appendChild(group);
  });
  cell.appendChild(wrap);
}

function appendTokenGimmickBadges(cell, combatant) {
  const gimmicks = combatant?.gimmicks || {};
  const badges = [];
  if (gimmicks.mega_form) {
    badges.push({ label: "M", title: `Mega Evolution: ${gimmicks.mega_form}`, className: "mega" });
  }
  if (gimmicks.primal_reversion_ready) {
    const orbName = String(gimmicks.primal_reversion_ready || "").trim();
    badges.push({ label: "P", title: `Primal Reversion: ${orbName || "Ready"}`, className: orbName.toLowerCase().includes("blue") ? "primal-blue" : "primal-red" });
  }
  if (gimmicks.dynamax_active) {
    badges.push({ label: "D", title: "Dynamaxed", className: "dynamax" });
  }
  const teraType = gimmicks?.terastallized?.tera_type || "";
  if (teraType) {
    badges.push({ label: String(teraType).slice(0, 2).toUpperCase(), title: `Terastallized: ${teraType}`, className: `tera type-${normalizePokeKey(teraType)}` });
  }
  if (!badges.length) return;
  const wrap = document.createElement("div");
  wrap.className = "token-gimmick-stack";
  badges.slice(0, 3).forEach((badgeSpec) => {
    const badge = document.createElement("div");
    badge.className = `token-gimmick ${badgeSpec.className}`.trim();
    badge.textContent = badgeSpec.label;
    badge.title = badgeSpec.title;
    if (badgeSpec.className.includes("type-")) {
      const typeName = badgeSpec.className.split("type-")[1] || "";
      const palette = gimmickPalette("tera", typeName.replace(/-/g, " "));
      badge.style.setProperty("--gimmick-primary", palette.primary);
      badge.style.setProperty("--gimmick-secondary", palette.secondary);
    }
    wrap.appendChild(badge);
  });
  cell.appendChild(wrap);
}

function buildNatureTooltip(combatant) {
  const nature = String(combatant?.nature || "").trim();
  if (!nature) return "";
  const profile = combatant?.nature_profile;
  if (!profile || typeof profile !== "object") {
    return `Nature assigned: ${nature}.`;
  }
  const raise = tooltipStatLabel(profile.raise);
  const lower = tooltipStatLabel(profile.lower);
  const modifiers = profile.modifiers && typeof profile.modifiers === "object" ? profile.modifiers : {};
  const nonZero = Object.entries(modifiers)
    .filter(([, value]) => Number(value) !== 0)
    .map(([stat, value]) => `${tooltipStatLabel(stat)} ${Number(value) > 0 ? "+" : ""}${Number(value)}`);
  const lines = [];
  if (raise && lower) {
    if (raise === lower) {
      lines.push("Neutral nature.");
    } else {
      lines.push(`Raises ${raise}, lowers ${lower}.`);
    }
  }
  if (nonZero.length) {
    lines.push(`Stat mods: ${nonZero.join(", ")}.`);
  }
  if (!lines.length) {
    lines.push("No stat changes.");
  }
  return lines.join("\n");
}

function bindDetailsTooltips() {
  const targets = detailsEl.querySelectorAll("[data-tooltip-title][data-tooltip-body]");
  targets.forEach((target) => {
    target.addEventListener("mouseenter", () => {
      const title = target.getAttribute("data-tooltip-title") || target.textContent || "Details";
      const body = target.getAttribute("data-tooltip-body") || "";
      showDetailTooltip(target, title, body);
    });
    target.addEventListener("mouseleave", () => {
      scheduleTooltipHide();
    });
  });
}

function renderDetails() {
  const combatant = state.combatants.find((c) => c.id === selectedId);
  if (!combatant) {
    if (tooltipMode === "detail") {
      hideTooltip();
    }
    detailsEl.textContent = "Select a unit.";
    return;
  }
  const statuses = combatant.statuses || [];
  const abilities = combatant.abilities || [];
  const baseAbilities = combatant.base_abilities || abilities;
  const shownAbilities = abilities.length ? abilities : baseAbilities;
  const abilitySuffix = abilities.length ? "" : shownAbilities.length ? " (suppressed)" : "";
  const statusMarkup = renderStatusChips(statuses);
  const abilityMarkup = `${renderAbilityChips(shownAbilities)}${escapeHtml(abilitySuffix)}`;
  const itemMarkup = renderItemChips(combatant.items || []);
  const passiveItemEffectsMarkup = formatPassiveItemEffects(combatant.passive_item_effects || []);
  const colorTheory = combatant.color_theory || null;
  const serpentsMark = combatant.serpents_mark || null;
  const fabulousTrim = combatant.fabulous_trim || null;
  const moodyState = combatant.moody_state || null;
  const truantState = combatant.truant_state || null;
  const giverState = combatant.giver_state || null;
  const colorTheoryMarkup = colorTheory?.color
    ? chipHtml({
        text: `Color Theory: ${colorTheory.color}`,
        iconBadge: "CT",
        tooltipTitle: "Color Theory",
        tooltipBody: `Roll ${colorTheory.roll || "?"}: ${colorTheory.color}`,
        className: "type-normal",
      })
    : "-";
  const serpentsMarkMarkup = serpentsMark?.pattern
    ? chipHtml({
        text: `Serpent's Mark: ${serpentsMark.pattern}`,
        iconBadge: "SM",
        tooltipTitle: "Serpent's Mark",
        tooltipBody: `Roll ${serpentsMark.roll || "?"}: ${serpentsMark.pattern}`,
        className: "type-poison",
      })
    : "-";
  const fabulousTrimMarkup = fabulousTrim?.style
    ? chipHtml({
        text: `Trim: ${fabulousTrim.style}`,
        iconBadge: "FT",
        tooltipTitle: "Fabulous Trim",
        tooltipBody: `Current style: ${fabulousTrim.style}`,
        className: "type-normal",
      })
    : "-";
  const moodyMarkup = moodyState?.up_stat
    ? chipHtml({
        text: `${moodyState.errata ? "Moody*" : "Moody"}: +${String(moodyState.up_stat).toUpperCase()} / ${String(moodyState.down_stat || "").toUpperCase()}`,
        iconBadge: "MO",
        tooltipTitle: moodyState.errata ? "Moody [Errata]" : "Moody",
        tooltipBody: `Round ${moodyState.round || "?"}: +${moodyState.up_delta || 0} ${String(moodyState.up_stat || "").toUpperCase()} (roll ${moodyState.up_roll || "?"}), ${moodyState.down_delta || 0} ${String(moodyState.down_stat || "").toUpperCase()} (roll ${moodyState.down_roll || "?"}).`,
        className: "type-normal",
      })
    : "-";
  const truantMarkup = truantState?.roll
    ? chipHtml({
        text: `Truant: ${truantState.skipped ? "Loafed" : "Acted"}`,
        iconBadge: "TR",
        tooltipTitle: "Truant",
        tooltipBody: `Round ${truantState.round || "?"}: roll ${truantState.roll || "?"}${truantState.skipped ? `, skipped Standard Action and healed ${truantState.heal || 0}.` : "."}`,
        className: truantState.skipped ? "type-normal" : "type-grass",
      })
    : "-";
  const giverMarkup = (giverState?.preference_mode || giverState?.last_mode)
    ? chipHtml({
        text: `Giver: ${giverState.last_mode || giverState.preference_mode}`,
        iconBadge: "GV",
        tooltipTitle: "Giver",
        tooltipBody: `${giverState.preference_mode ? `Preference: ${giverState.preference_mode}${giverState.preference_roll ? ` (roll ${giverState.preference_roll})` : ""}. ` : ""}${giverState.last_mode ? `Last Present: ${giverState.last_mode}${giverState.last_roll ? ` (roll ${giverState.last_roll})` : ""}${giverState.last_effective_db !== null && giverState.last_effective_db !== undefined ? `, DB ${giverState.last_effective_db}` : ""}${giverState.round ? ` on round ${giverState.round}` : ""}.` : "No Present used yet."}`,
        className: "type-normal",
      })
    : "-";
  const natureName = String(combatant.nature || "").trim() || "-";
  const natureTooltip = buildNatureTooltip(combatant);
  const natureTooltipAttrs = natureTooltip
    ? ` data-tooltip-title="${escapeAttr(`Nature: ${natureName}`)}" data-tooltip-body="${escapeAttr(natureTooltip)}"`
    : "";
  const hpRatio = combatant.max_hp ? combatant.hp / combatant.max_hp : 0;
  const tempHp = Number(combatant.temp_hp || 0);
  const injuries = Number(combatant.injuries || 0);
  detailsEl.innerHTML = `
    <div class="details-header">
      <div class="details-title">${escapeHtml(combatant.name)} (${escapeHtml(combatant.marker)})</div>
      <button id="play-cry" class="cry-button" type="button">Cry</button>
    </div>
    <div class="details-hero">
      <div class="details-hpbar">
        <div class="details-hpfill" style="width: ${Math.max(0, Math.min(1, hpRatio)) * 100}%"></div>
      </div>
      <div class="details-badges">
        <span class="details-badge">HP ${combatant.hp}/${combatant.max_hp}</span>
        <span class="details-badge">Temp ${tempHp}</span>
        <span class="details-badge">Injuries ${injuries}</span>
      </div>
    </div>
    <div class="details-row">Team: ${escapeHtml(formatTeamLabel(teamKeyForCombatant(combatant)))}</div>
    <div class="details-row">Nature: <span class="nature-value"${natureTooltipAttrs}>${escapeHtml(natureName)}</span></div>
    <div class="details-row">Pos: ${escapeHtml(combatant.position ? combatant.position.join(",") : "-")}</div>
    <div class="details-row">Status: ${statusMarkup}</div>
    <div class="details-row">Abilities: ${abilityMarkup}</div>
    <div class="details-row">Color Theory: ${colorTheoryMarkup}</div>
    <div class="details-row">Serpent's Mark: ${serpentsMarkMarkup}</div>
    <div class="details-row">Fabulous Trim: ${fabulousTrimMarkup}</div>
    <div class="details-row">Moody: ${moodyMarkup}</div>
    <div class="details-row">Truant: ${truantMarkup}</div>
    <div class="details-row">Giver: ${giverMarkup}</div>
    <div class="details-row">Items: ${itemMarkup}</div>
    <div class="details-row">Item Effects: ${passiveItemEffectsMarkup}</div>
    <div class="details-row">CS: ${escapeHtml(formatCombatStages(combatant.combat_stages))}</div>
    <div class="details-row">Stats: ${escapeHtml(formatStats(combatant.stats))}</div>
    <div class="details-row">Effective: ${escapeHtml(formatStats(combatant.effective_stats || combatant.stats))}</div>
  `;
  const cryButton = detailsEl.querySelector("#play-cry");
  if (cryButton) {
    cryButton.addEventListener("click", () => {
      cryButton.disabled = true;
      playCryForSpecies(combatant.species || combatant.name)
        .catch(() => {})
        .finally(() => {
          cryButton.disabled = false;
        });
    });
  }
  bindDetailsTooltips();
}

function pickTrainerFeatureOption(title, options, onSelect, helpText = "") {
  openListPicker({
    title,
    helpText,
    items: (options || []).map((entry) =>
      typeof entry === "string"
        ? { value: entry, label: entry }
        : {
            value: entry.value ?? entry.id ?? entry.label,
            label: entry.label ?? entry.name ?? String(entry.value ?? entry.id ?? ""),
            meta: entry.meta || "",
            hint: entry.hint || "",
          }
    ),
    onSelect: (value, entry) => {
      if (onSelect) onSelect(value, entry);
    },
  });
}

function enemyTargetPicker(combatant) {
  const actorTeam = combatant?.team;
  return (state?.combatants || [])
    .filter((entry) => entry.id !== combatant.id && entry.team !== actorTeam && !entry.fainted)
    .map((entry) => ({
      value: entry.id,
      label: `${entry.name} (${formatTeamLabel(entry.team)})`,
      meta: entry.position ? `Pos ${entry.position.join(",")}` : "",
    }));
}

function allCombatantTargetOptions() {
  return (state?.combatants || []).map((entry) => ({
    id: entry.id,
    label: `${entry.name} (${formatTeamLabel(entry.team)})`,
  }));
}

function combatantOptionsFromIds(ids) {
  const lookup = new Map((state?.combatants || []).map((entry) => [entry.id, entry]));
  return (ids || []).map((id) => {
    const entry = lookup.get(id);
    return {
      value: id,
      label: entry ? `${entry.name} (${formatTeamLabel(entry.team)})` : String(id),
      meta: entry?.position ? `Pos ${entry.position.join(",")}` : "",
    };
  });
}

function pickMultipleTrainerTargets(title, options, minCount, maxCount, onDone, helpText = "") {
  const normalized = (options || []).filter((entry) => entry && entry.value);
  const selected = [];
  const visit = () => {
    const available = normalized.filter((entry) => !selected.includes(entry.value));
    const items = available.map((entry) => ({
      value: entry.value,
      label: entry.label,
      meta: entry.meta || "",
      hint: entry.hint || "",
    }));
    if (selected.length >= minCount) {
      items.unshift({
        value: "__done__",
        label: `Done (${selected.length})`,
        hint: "Confirm the current target selection.",
      });
    }
    if (!items.length) {
      onDone([...selected]);
      return;
    }
    openListPicker({
      title: `${title}${selected.length ? ` (${selected.length}/${maxCount})` : ""}`,
      helpText,
      items,
      onSelect: (value) => {
        if (value === "__done__") {
          onDone([...selected]);
          return;
        }
        selected.push(value);
        if (selected.length >= maxCount) {
          onDone([...selected]);
          return;
        }
        visit();
      },
    });
  };
  visit();
}

function addTrainerFeatureButton(section, label, enabled, onClick, titleText = "") {
  const btn = document.createElement("button");
  btn.className = "item-button";
  btn.textContent = label;
  if (!enabled) {
    btn.classList.add("inactive");
    btn.setAttribute("aria-disabled", "true");
  }
  if (titleText) btn.title = titleText;
  btn.addEventListener("click", () => {
    if (!enabled) return;
    onClick();
  });
  section.appendChild(btn);
}

function renderTrainerFeatureActions(moveListEl, combatant, canAct) {
  const features = new Set((combatant?.trainer_features || []).map((value) => String(value || "").trim().toLowerCase()));
  const hints = combatant?.trainer_action_hints || {};
  const trainerAp = Number(hints.trainer_ap || 0);
  if (!features.size) return;
  const section = document.createElement("div");
  section.className = "item-section";
  const title = document.createElement("div");
  title.className = "item-title";
  title.textContent = "Trainer Features";
  section.appendChild(title);
  const list = document.createElement("div");
  list.className = "item-list";
  const addDraftPanel = (titleText, tiles, maxTiles, onDeploy, onCancel, deployEnabled, helperText) => {
    const panel = document.createElement("div");
    panel.className = "item-help";
    const header = document.createElement("div");
    header.textContent = `${titleText} ${Math.max(0, (tiles || []).length)}/${maxTiles}`;
    panel.appendChild(header);
    const coords = document.createElement("div");
    coords.textContent = (tiles || []).length
      ? (tiles || []).map((coord) => `${coord[0]},${coord[1]}`).join(" | ")
      : "No tiles selected.";
    panel.appendChild(coords);
    if (helperText) {
      const helper = document.createElement("div");
      helper.textContent = helperText;
      panel.appendChild(helper);
    }
    const actions = document.createElement("div");
    actions.className = "item-list";
    const deployBtn = document.createElement("button");
    deployBtn.className = "item-button";
    deployBtn.textContent = "Deploy";
    if (!deployEnabled) {
      deployBtn.classList.add("inactive");
      deployBtn.setAttribute("aria-disabled", "true");
    }
    deployBtn.addEventListener("click", () => {
      if (!deployEnabled) return;
      onDeploy();
    });
    actions.appendChild(deployBtn);
    const cancelBtn = document.createElement("button");
    cancelBtn.className = "item-button";
    cancelBtn.textContent = "Cancel";
    cancelBtn.addEventListener("click", () => {
      onCancel();
    });
    actions.appendChild(cancelBtn);
    panel.appendChild(actions);
    section.appendChild(panel);
  };
  const targets = enemyTargetPicker(combatant);
  const targetMap = new Map(targets.map((entry) => [entry.value, entry]));
  const quickWitOptionMap = new Map((hints.quick_wit_manipulate_options || []).map((entry) => [entry.target, entry]));
  const tricksterOptionMap = new Map((hints.trickster_options || []).map((entry) => [entry.target, entry]));
  const dirtyFightingOptionMap = new Map((hints.dirty_fighting_options || []).map((entry) => [entry.target, entry]));
  const weaponFinesseOptionMap = new Map((hints.weapon_finesse_target_options || []).map((entry) => [entry.target, entry]));
  const psychicResonanceOptionMap = new Map((hints.psychic_resonance_target_options || []).map((entry) => [entry.target, entry]));
  const quickSwitchOptions = hints.quick_switch_replacements || [];
  const telepathActive = !!hints.telepath_active;
  const orderOptions = hints.target_orders || [];
  const orderTargetOptions = combatantOptionsFromIds((hints.order_targets || []).map((entry) => entry.target || entry));
  const focusTargetOptions = (hints.focused_command_targets || []).map((entry) => ({
    value: entry.target,
    label: entry.target_name || entry.target,
  }));
  const orderSectionFeatures = [
    "mobilize",
    "strike again!",
    "long shot",
    "dazzling dervish",
    "sentinel stance",
    "brace for impact",
    "battle conductor",
    "scheme twist",
    "tip the scales",
    "focused command",
    "complex orders",
    "commander's voice",
    "commander’s voice",
  ];
  const hasOrderSurface = orderSectionFeatures.some((name) => features.has(name));
  const chooseFocusedCommand = () => {
    pickMultipleTrainerTargets(
      "Focused Command Targets",
      focusTargetOptions,
      2,
      2,
      (selectedIds) => {
        if (selectedIds.length !== 2) return;
        pickTrainerFeatureOption(
          "Focused Command AP Option",
          [
            { value: "none", label: "No AP", hint: "Both Pokemon stay At-Will only and take -5 damage rolls." },
            { value: "frequency", label: "Lift Frequency", hint: "Spend 1 AP to remove the At-Will restriction." },
            { value: "damage", label: "Lift Damage", hint: "Spend 1 AP to remove the -5 damage penalty." },
            { value: "both", label: "Lift Both", hint: "Spend 2 AP to remove both restrictions." },
          ],
          (liftOption) => {
            commitAction({
              type: "trainer_feature",
              action_key: "focused_command",
              actor_id: combatant.id,
              primary_target_id: selectedIds[0],
              secondary_target_id: selectedIds[1],
              lift_option: liftOption,
            }).catch(alertError);
          },
          "Choose the two allied Pokemon you want to command this round."
        );
      },
      "Pick the primary acting Pokemon first, then the second Pokemon that gains the extra turn."
    );
  };
  const chooseSingleOrder = (helpText = "Choose an Order, then pick its target.") => {
    if (!orderOptions.length || !orderTargetOptions.length) {
      notifyUI("warn", "No valid Order targets are available.", 2200);
      return;
    }
    pickTrainerFeatureOption(
      "Order",
      orderOptions,
      (orderName) => {
        pickTrainerFeatureOption("Order Target", orderTargetOptions, (targetId) => {
          commitAction({
            type: "trainer_feature",
            action_key: "target_order",
            actor_id: combatant.id,
            order_name: orderName,
            target_id: targetId,
          }).catch(alertError);
        }, helpText);
      },
      helpText
    );
  };
  const chooseCommandersVoice = () => {
    const canFocus = !!hints.focused_command_ready && focusTargetOptions.length >= 2;
    pickTrainerFeatureOption(
      "Commander's Voice Mode",
      [
        { value: "swift", label: "Swift Order", hint: "Use one Order as a Swift Action." },
        { value: "double", label: "Two Orders", hint: "Use two different Orders as one Standard Action." },
        ...(canFocus ? [{ value: "focus", label: "Focus + Order", hint: "Pair Focused Command with one targeted Order." }] : []),
      ],
      (mode) => {
        if (mode === "swift") {
          pickTrainerFeatureOption("Swift Order", orderOptions, (orderName) => {
            pickTrainerFeatureOption("Order Target", orderTargetOptions, (targetId) => {
              commitAction({
                type: "trainer_feature",
                action_key: "commanders_voice",
                actor_id: combatant.id,
                mode: "swift_order",
                order_name: orderName,
                target_id: targetId,
              }).catch(alertError);
            });
          });
          return;
        }
        if (mode === "focus") {
          pickMultipleTrainerTargets(
            "Focused Command Targets",
            focusTargetOptions,
            2,
            2,
            (selectedIds) => {
              if (selectedIds.length !== 2) return;
              pickTrainerFeatureOption(
                "Focused Command AP Option",
                [
                  { value: "none", label: "No AP" },
                  { value: "frequency", label: "Lift Frequency" },
                  { value: "damage", label: "Lift Damage" },
                  { value: "both", label: "Lift Both" },
                ],
                (liftOption) => {
                  pickTrainerFeatureOption(
                    "Second Order",
                    orderOptions.filter((entry) => String(entry.order || entry.value || "").trim().toLowerCase() !== "focused command"),
                    (orderName) => {
                      const allowedTargetOptions = orderTargetOptions.filter((entry) => selectedIds.includes(entry.value));
                      pickTrainerFeatureOption("Second Order Target", allowedTargetOptions, (targetId) => {
                        commitAction({
                          type: "trainer_feature",
                          action_key: "commanders_voice",
                          actor_id: combatant.id,
                          mode: "double_order",
                          order_name: "Focused Command",
                          primary_target_id: selectedIds[0],
                          secondary_target_id: selectedIds[1],
                          lift_option: liftOption,
                          secondary_order_name: orderName,
                          second_target_id: targetId,
                        }).catch(alertError);
                      }, "The second Order must target one of the commanded Pokemon.");
                    }
                  );
                }
              );
            }
          );
          return;
        }
        pickTrainerFeatureOption("First Order", orderOptions, (firstOrder) => {
          const secondOrderOptions = orderOptions.filter((entry) => String(entry.order || entry.value || "").trim().toLowerCase() !== String(firstOrder).trim().toLowerCase());
          pickTrainerFeatureOption("First Target", orderTargetOptions, (firstTarget) => {
            pickTrainerFeatureOption("Second Order", secondOrderOptions, (secondOrder) => {
              pickTrainerFeatureOption("Second Target", orderTargetOptions.filter((entry) => entry.value !== firstTarget), (secondTarget) => {
                commitAction({
                  type: "trainer_feature",
                  action_key: "commanders_voice",
                  actor_id: combatant.id,
                  mode: "double_order",
                  order_name: firstOrder,
                  target_id: firstTarget,
                  secondary_order_name: secondOrder,
                  second_target_id: secondTarget,
                }).catch(alertError);
              });
            });
          });
        });
      },
      "Choose how to bundle your Orders this turn."
    );
  };
  const chooseSpreadOrder = (actionKey, orders, targetPool, minTargets, maxTargets, helpText) => {
    if (!orders.length || !targetPool.length) {
      notifyUI("warn", "No valid spread-order choices are available.", 2200);
      return;
    }
    pickTrainerFeatureOption(
      "Spread Order",
      orders,
      (orderName) => {
        pickMultipleTrainerTargets(
          "Spread Targets",
          targetPool,
          minTargets,
          maxTargets,
          (targetIds) => {
            commitAction({
              type: "trainer_feature",
              action_key: actionKey,
              actor_id: combatant.id,
              order_name: orderName,
              target_ids: targetIds,
            }).catch(alertError);
          },
          helpText
        );
      },
      helpText
    );
  };
  const chooseComplexOrders = () => {
    if ((hints.complex_orders_orders || []).length < 2 || orderTargetOptions.length < 2) {
      notifyUI("warn", "Complex Orders needs at least two Orders and two targets.", 2200);
      return;
    }
    pickTrainerFeatureOption("First Order", hints.complex_orders_orders, (firstOrder) => {
      pickTrainerFeatureOption("First Target", orderTargetOptions, (firstTarget) => {
        pickTrainerFeatureOption(
          "Second Order",
          (hints.complex_orders_orders || []).filter((entry) => String(entry.order || entry.value || "").trim().toLowerCase() !== String(firstOrder).trim().toLowerCase()),
          (secondOrder) => {
            pickTrainerFeatureOption(
              "Second Target",
              orderTargetOptions.filter((entry) => entry.value !== firstTarget),
              (secondTarget) => {
                commitAction({
                  type: "trainer_feature",
                  action_key: "complex_orders",
                  actor_id: combatant.id,
                  target_orders: [
                    { order_name: firstOrder, target_id: firstTarget },
                    { order_name: secondOrder, target_id: secondTarget },
                  ],
                }).catch(alertError);
              }
            );
          }
        );
      });
    });
  };

  if (hasOrderSurface) {
    const orderPanel = document.createElement("div");
    orderPanel.className = "item-help";
    const parts = [];
    if (orderOptions.length) parts.push(`Orders: ${orderOptions.map((entry) => entry.order_name || entry.order).join(", ")}`);
    if (orderTargetOptions.length) parts.push(`Targets: ${orderTargetOptions.map((entry) => entry.label).join(" | ")}`);
    if (hints.focused_command_pairs?.length) {
      parts.push(`Focused: ${hints.focused_command_pairs.map((entry) => `${entry.target_name} + ${entry.partner_name}`).join(" | ")}`);
    }
    orderPanel.textContent = parts.join(" || ") || "Orders decisions are available through this panel.";
    section.appendChild(orderPanel);

    addTrainerFeatureButton(
      list,
      "Order",
      canAct && orderOptions.length > 0 && orderTargetOptions.length > 0,
      () => chooseSingleOrder(),
      "Use a single targeted Order."
    );
    if (features.has("focused command")) {
      addTrainerFeatureButton(
        list,
        "Focused Command",
        canAct && !!hints.focused_command_ready,
        () => chooseFocusedCommand(),
        "Grant a second allied Pokemon a turn this round, with selectable restrictions."
      );
    }
    if (features.has("commander's voice") || features.has("commander’s voice")) {
      addTrainerFeatureButton(
        list,
        "Commander's Voice",
        canAct && !!hints.commanders_voice_ready,
        () => chooseCommandersVoice(),
        "Bundle one or two Orders into a single action."
      );
    }
    if (features.has("battle conductor")) {
      addTrainerFeatureButton(
        list,
        "Battle Conductor",
        canAct && !!hints.battle_conductor_ready,
        () => chooseSpreadOrder("battle_conductor", hints.battle_conductor_orders || [], orderTargetOptions, 2, 3, "Choose up to two additional allies for an At-Will Order."),
        "Spread an At-Will Order to up to two additional allies."
      );
    }
    if (features.has("scheme twist")) {
      addTrainerFeatureButton(
        list,
        "Scheme Twist",
        canAct && !!hints.scheme_twist_ready,
        () => chooseSpreadOrder("scheme_twist", hints.scheme_twist_orders || [], orderTargetOptions, 2, 3, "Choose up to two additional allies for a Scene or Daily Order."),
        "Spread a Scene or Daily Order to up to two additional allies."
      );
    }
    if (features.has("tip the scales")) {
      addTrainerFeatureButton(
        list,
        `Tip the Scales${trainerAp ? ` (${trainerAp} AP)` : ""}`,
        canAct && !!hints.tip_the_scales_ready,
        () => {
          pickTrainerFeatureOption(
            "Tip the Scales Order",
            hints.tip_the_scales_orders || [],
            (orderName) => {
              commitAction({
                type: "trainer_feature",
                action_key: "tip_the_scales",
                actor_id: combatant.id,
                order_name: orderName,
              }).catch(alertError);
            },
            "Apply an At-Will Order to all allies within 10 meters."
          );
        },
        "Spend 2 AP to spread an At-Will Order to all nearby allies."
      );
    }
    if (features.has("complex orders")) {
      addTrainerFeatureButton(
        list,
        "Complex Orders",
        canAct && !!hints.complex_orders_ready,
        () => chooseComplexOrders(),
        "Assign different Orders to different allied targets as one Shift action."
      );
    }
  }

  if (armedTileAction === "frozen_domain" && features.has("frozen domain")) {
    addDraftPanel(
      "Frozen Domain Draft",
      frozenDomainDraftTiles,
      6,
      () => {
        if (frozenDomainDraftTiles.length !== 6) {
          alertError(new Error("Select exactly 6 contiguous Frozen Domain tiles."));
          return;
        }
        if (!trapperTilesAreContiguous(frozenDomainDraftTiles)) {
          alertError(new Error("Frozen Domain draft must remain contiguous."));
          return;
        }
        commitAction({
          type: "trainer_feature",
          action_key: "frozen_domain",
          actor_id: combatant.id,
          target_positions: frozenDomainDraftTiles,
        }).catch(alertError);
      },
      () => {
        clearArmedTileAction();
        render();
      },
      canAct && !!hints.frozen_domain_ap_ready && frozenDomainDraftTiles.length === 6 && trapperTilesAreContiguous(frozenDomainDraftTiles),
      "Drag on legal tiles to paint 6 contiguous Frozen Domain tiles."
    );
  }

  if (armedTileAction === "trapper" && features.has("trapper")) {
    addDraftPanel(
      "Trapper Draft",
      trapperDraftTiles,
      8,
      () => {
        if (trapperDraftTiles.length !== 8) {
          alertError(new Error("Select exactly 8 contiguous trap tiles."));
          return;
        }
        if (!trapperTilesAreContiguous(trapperDraftTiles)) {
          alertError(new Error("Trap draft must remain contiguous."));
          return;
        }
        commitAction({
          type: "trainer_feature",
          action_key: "trapper",
          actor_id: combatant.id,
          target_positions: trapperDraftTiles,
        }).catch(alertError);
      },
      () => {
        clearArmedTileAction();
        render();
      },
      canAct && trapperDraftTiles.length === 8 && trapperTilesAreContiguous(trapperDraftTiles),
      "Drag on legal tiles to paint. Click selected tiles to remove them."
    );
  }

  if (armedTileAction === "psionic_overload_barrier" && features.has("psionic overload")) {
    addDraftPanel(
      "Overload Barrier",
      psionicOverloadBarrierTiles,
      2,
      () => {
        if (psionicOverloadBarrierTiles.length !== 2) {
          alertError(new Error("Select exactly 2 barrier segment tiles."));
          return;
        }
        commitAction({
          type: "trainer_feature",
          action_key: "psionic_overload_follow_up",
          actor_id: combatant.id,
          barrier_tiles: psionicOverloadBarrierTiles,
        }).catch(alertError);
      },
      () => {
        clearArmedTileAction();
        render();
      },
      canAct && psionicOverloadBarrierTiles.length === 2,
      "Select 2 legal tiles for the extra Barrier segments."
    );
  }

  if (features.has("quick switch")) {
    addTrainerFeatureButton(
      list,
      `Quick Switch${trainerAp ? ` (${trainerAp} AP)` : ""}`,
      canAct && !!hints.quick_switch_ap_ready && quickSwitchOptions.length > 0,
      () => {
        pickTrainerFeatureOption(
          "Quick Switch Replacement",
          quickSwitchOptions.map((entry) => ({ value: entry.target, label: entry.target_name || entry.target })),
          (replacementId) => {
            commitAction({ type: "trainer_feature", action_key: "quick_switch", actor_id: combatant.id, replacement_id: replacementId }).catch(alertError);
          },
          "Spend 2 AP to switch to a benched ally without losing a Pokemon turn."
        );
      },
      !hints.quick_switch_ap_ready ? "Requires 2 AP." : (quickSwitchOptions.length ? "" : "No valid Quick Switch replacements.")
    );
  }

  if (features.has("quick wit")) {
    addTrainerFeatureButton(list, "Quick Wit: Social Move", canAct && (hints.social_moves || []).length > 0, () => {
      pickTrainerFeatureOption(
        "Quick Wit Move",
        (hints.social_moves || []).map((name) => ({ value: name, label: name })),
        (moveName) => {
          const validTargets = (((state || {}).move_targets || {})[moveName] || []).filter(Boolean);
          const targetOptions = targets.filter((entry) => validTargets.length === 0 || validTargets.includes(entry.value));
          if (!targetOptions.length) {
            commitAction({ type: "trainer_feature", action_key: "quick_wit_move", actor_id: combatant.id, move_name: moveName, target_id: null }).catch(alertError);
            return;
          }
          pickTrainerFeatureOption("Quick Wit Target", targetOptions, (targetId) => {
            commitAction({ type: "trainer_feature", action_key: "quick_wit_move", actor_id: combatant.id, move_name: moveName, target_id: targetId }).catch(alertError);
          });
        },
        "Use a Social move as a Swift Action."
      );
    });
    const manipulateTargets = (hints.quick_wit_manipulate_targets || []).map((id) => targetMap.get(id)).filter(Boolean);
    addTrainerFeatureButton(list, `Quick Wit: Manipulate (${Math.max(0, Number(hints.quick_wit_uses_left || 0))} left)`, canAct && manipulateTargets.length > 0, () => {
      pickTrainerFeatureOption("Manipulate Target", manipulateTargets, (targetId) => {
        const options = (quickWitOptionMap.get(targetId)?.tricks || []).map((trick) => ({ value: trick, label: trick }));
        if (!options.length) {
          notifyUI("warn", "No Manipulate options remain for that target this scene.", 2200);
          return;
        }
        pickTrainerFeatureOption("Manipulate Maneuver", options, (trick) => {
          commitAction({ type: "trainer_feature", action_key: "quick_wit_manipulate", actor_id: combatant.id, trick, target_id: targetId }).catch(alertError);
        });
      }, "Perform a Manipulate Maneuver as a Swift Action.");
    });
  }

  if (features.has("enchanting gaze")) {
    const anchorTargets = (hints.enchanting_gaze_anchor_options || []).map((entry) => ({
      value: entry.target,
      label: `${entry.target_name || entry.target} (${formatTeamLabel(targetMap.get(entry.target)?.team)})`,
      meta: targetMap.get(entry.target)?.meta || "",
    }));
    addTrainerFeatureButton(list, `Enchanting Gaze${trainerAp ? ` (${trainerAp} AP)` : ""}`, canAct && anchorTargets.length > 0 && !!hints.enchanting_gaze_ap_ready, () => {
      pickTrainerFeatureOption("Enchanting Gaze Maneuver", ["Bon Mot", "Flirt", "Terrorize"], (trick) => {
        pickTrainerFeatureOption("Cone Anchor", anchorTargets, (anchorId) => {
          commitAction({ type: "trainer_feature", action_key: "enchanting_gaze", actor_id: combatant.id, trick, anchor_id: anchorId }).catch(alertError);
        });
      }, "Apply one Manipulate effect to all foes in Cone 2.");
    }, !hints.enchanting_gaze_ap_ready ? "Requires 2 AP." : "Spend 2 AP to affect all foes in Cone 2.");
  }

  if (features.has("flight")) {
    const flightSpeed = Number(hints.flight_speed || 0);
    const flightActive = !!hints.flight_active;
    addTrainerFeatureButton(list, `Flight${flightSpeed > 0 ? `: Sky ${flightSpeed}` : ""}`, canAct && flightSpeed > 0 && !flightActive && !!hints.flight_ap_ready, () => {
      commitAction({ type: "trainer_feature", action_key: "flight", actor_id: combatant.id }).catch(alertError);
    }, flightActive ? "Flight is already active this round." : (!hints.flight_ap_ready ? "Requires 1 AP." : "Spend 1 AP to gain temporary Sky movement for the round."));
  }

  if (features.has("telepath")) {
    addTrainerFeatureButton(list, `Telepath${trainerAp ? ` (${trainerAp} AP)` : ""}`, canAct && !telepathActive && !!hints.telepath_ap_ready, () => {
      commitAction({ type: "trainer_feature", action_key: "telepath", actor_id: combatant.id }).catch(alertError);
    }, telepathActive ? "Telepath is already active for this scene." : (!hints.telepath_ap_ready ? "Requires 2 AP." : "Spend 2 AP to gain the Telepath capability for the scene."));
  }

  if (features.has("ambient aura")) {
    const barrierTargets = (hints.ambient_aura_barrier_targets || []).map((entry) => ({
      value: entry.target,
      label: entry.target_name || entry.target,
    }));
    addTrainerFeatureButton(
      list,
      hints.ambient_aura_blessing_move
        ? `Ambient Aura: ${hints.ambient_aura_blessing_move}`
        : "Ambient Aura",
      canAct && !!hints.ambient_aura_ready,
      () => {
        const options = [
          { value: "barrier", label: "Barrier", hint: "Grant DR to yourself or an ally within 5 meters." },
          { value: "cure", label: "Cure", hint: "Remove your volatile status afflictions." },
          { value: "blindsense", label: "Blindsense", hint: "Gain Blindsense for the scene." },
        ].filter((entry) => entry.value !== "cure" || !!hints.ambient_aura_can_cure);
        pickTrainerFeatureOption(
          "Aura Blessing",
          options,
          (mode) => {
            if (mode === "barrier") {
              pickTrainerFeatureOption(
                "Barrier Target",
                barrierTargets,
                (targetId) => {
                  commitAction({ type: "trainer_feature", action_key: "ambient_aura", actor_id: combatant.id, mode, target_id: targetId }).catch(alertError);
                },
                "Choose yourself or an ally within 5 meters."
              );
              return;
            }
            commitAction({ type: "trainer_feature", action_key: "ambient_aura", actor_id: combatant.id, mode }).catch(alertError);
          },
          "Spend your stored Aura Blessing."
        );
      },
      hints.ambient_aura_ready ? "Spend your stored Aura Blessing." : "Use an Aura move while you have Aura Pulse to store a blessing."
    );
  }

  if (features.has("frozen domain")) {
    const frozenCount = frozenDomainDraftTiles.length;
    const frozenArmed = armedTileAction === "frozen_domain";
    addTrainerFeatureButton(
      list,
      frozenArmed ? `Frozen Domain: ${frozenCount}/6` : `Frozen Domain${trainerAp ? ` (${trainerAp} AP)` : ""}`,
      canAct && !!hints.frozen_domain_ready && !!hints.frozen_domain_ap_ready && ((state.legal_frozen_domain_tiles || []).length > 0),
      () => {
        if (frozenArmed) {
          if (frozenCount !== 6) {
            notifyUI("warn", "Select exactly 6 contiguous Frozen Domain tiles.", 2200);
            return;
          }
          if (!trapperTilesAreContiguous(frozenDomainDraftTiles)) {
            notifyUI("warn", "Frozen Domain tiles must stay contiguous.", 2200);
            return;
          }
          commitAction({
            type: "trainer_feature",
            action_key: "frozen_domain",
            actor_id: combatant.id,
            target_positions: frozenDomainDraftTiles,
          }).catch(alertError);
          return;
        }
        frozenDomainDraftTiles = [];
        armedTileAction = "frozen_domain";
        render();
      },
      !hints.frozen_domain_ap_ready
        ? "Requires 2 AP."
        : "Paint 6 contiguous tiles within 6 meters. Entering creatures must pass Acrobatics or be Tripped."
    );
  }

  if (features.has("arctic zeal")) {
    const targets = (hints.arctic_zeal_targets || []).map((entry) => ({
      value: entry.target,
      label: entry.target_name || entry.target,
    }));
    addTrainerFeatureButton(
      list,
      `Arctic Zeal (${Number(hints.arctic_zeal_charges || 0)})`,
      false,
      () => {},
      hints.arctic_zeal_source_move
        ? `Arctic Zeal stored Mist Blessings from ${hints.arctic_zeal_source_move}.`
        : "Arctic Zeal now triggers from Ice-Type moves and stores Mist Blessing charges."
    );
    addTrainerFeatureButton(
      list,
      "Mist Slow",
      canAct && !!hints.arctic_zeal_ready && targets.length > 0,
      () => {
        pickTrainerFeatureOption(
          "Mist Slow Target",
          targets,
          (targetId) => {
            commitAction({ type: "trainer_feature", action_key: "arctic_zeal", actor_id: combatant.id, mode: "slow", target_id: targetId }).catch(alertError);
          },
          "Spend 1 Mist Blessing to give a foe within 5 Slowed and -5 Damage Rolls for 1 full round."
        );
      },
      !targets.length
        ? "No foe is within 5 for Mist Slow."
        : (!hints.arctic_zeal_ready
          ? "Use an Ice-Type move first to gain Mist Blessing charges."
          : "Spend 1 Mist Blessing to slow a foe and reduce their damage rolls.")
    );
    addTrainerFeatureButton(
      list,
      `Mist Def+${hints.arctic_zeal_hail_active ? " | Hail" : ""}`,
      canAct && !!hints.arctic_zeal_ready,
      () => {
        commitAction({ type: "trainer_feature", action_key: "arctic_zeal", actor_id: combatant.id, mode: "def" }).catch(alertError);
      },
      !hints.arctic_zeal_ready
        ? "Use an Ice-Type move first to gain Mist Blessing charges."
        : "Spend 1 Mist Blessing to raise Defense by 1 Combat Stage."
    );
    addTrainerFeatureButton(
      list,
      "Mist SpDef+",
      canAct && !!hints.arctic_zeal_ready,
      () => {
        commitAction({ type: "trainer_feature", action_key: "arctic_zeal", actor_id: combatant.id, mode: "spdef" }).catch(alertError);
      },
      !hints.arctic_zeal_ready
        ? "Use an Ice-Type move first to gain Mist Blessing charges."
        : "Spend 1 Mist Blessing to raise Special Defense by 1 Combat Stage."
    );
  }

  if (features.has("polar vortex")) {
    const targets = (hints.polar_vortex_targets || []).map((entry) => ({
      value: entry.target,
      label: entry.target_name || entry.target,
    }));
    const boundTargets = (hints.polar_vortex_bound_targets || []).map((entry) => entry.target_name || entry.target).filter(Boolean);
    addTrainerFeatureButton(
      list,
      boundTargets.length ? `Polar Vortex: ${boundTargets.join(", ")}` : (hints.polar_vortex_active ? "Polar Vortex | Hail" : "Polar Vortex"),
      canAct && !!hints.polar_vortex_ready && targets.length > 0,
      () => {
        pickTrainerFeatureOption(
          "Polar Vortex Target",
          targets,
          (targetId) => {
            commitAction({ type: "trainer_feature", action_key: "polar_vortex", actor_id: combatant.id, target_id: targetId }).catch(alertError);
          },
          "Spend 2 AP to let an allied Pokemon act as though it were in Hail."
        );
      },
      !targets.length
        ? "No allied active target is available."
        : "Spend 2 AP to bind Hail to an allied Pokemon for moves and abilities."
    );
    if (hints.polar_vortex_release_ready) {
      addTrainerFeatureButton(
        list,
        "Release Polar Vortex",
        canAct,
        () => {
          commitAction({ type: "trainer_feature", action_key: "release_polar_vortex", actor_id: combatant.id }).catch(alertError);
        },
        "Release the current Polar Vortex binding."
      );
    }
  }

  if (features.has("thought detection")) {
    addTrainerFeatureButton(
      list,
      `Thought Detection (${Math.max(0, Number(hints.thought_detection_uses_left || 0))} left)`,
      canAct && !!hints.thought_detection_ready,
      () => {
        commitAction({ type: "trainer_feature", action_key: "thought_detection", actor_id: combatant.id }).catch(alertError);
      },
      !telepathActive ? "Requires Telepath to be active." : (Number(hints.thought_detection_uses_left || 0) <= 0 ? "Thought Detection is out of uses this scene." : "Sense nearby living minds within Focus Rank x3 meters.")
    );
  }

  if (features.has("suggestion")) {
    const suggestionTargets = (hints.suggestion_targets || []).map((entry) => ({
      value: entry.target,
      label: entry.target_name || entry.target,
    }));
    const boundTarget = hints.suggestion_bound_target_name || hints.suggestion_bound_target;
    const boundText = hints.suggestion_bound_text;
    addTrainerFeatureButton(
      list,
      boundTarget ? `Suggestion: Bound to ${boundTarget}` : `Suggestion${trainerAp ? ` (${trainerAp} AP)` : ""}`,
      canAct && telepathActive && !!hints.suggestion_ap_ready && suggestionTargets.length > 0,
      () => {
        pickTrainerFeatureOption("Suggestion Target", suggestionTargets, (targetId) => {
          const message = window.prompt("Suggestion text", boundText || "");
          if (!message || !String(message).trim()) {
            notifyUI("warn", "Suggestion text is required.", 2200);
            return;
          }
          commitAction({
            type: "trainer_feature",
            action_key: "suggestion",
            actor_id: combatant.id,
            target_id: targetId,
            suggestion_text: String(message).trim(),
          }).catch(alertError);
        }, "Bind a planted thought to the target while Telepath is active.");
      },
      !telepathActive ? "Requires Telepath to be active." : (!hints.suggestion_ap_ready ? "Requires 1 AP." : "Bind a suggestion on a living target.")
    );
    if (hints.suggestion_release_ready) {
      addTrainerFeatureButton(
        list,
        "Release Suggestion",
        canAct,
        () => {
          commitAction({ type: "trainer_feature", action_key: "release_suggestion", actor_id: combatant.id }).catch(alertError);
        },
        "Release the current Suggestion binding."
      );
    }
  }

  if (features.has("psionic sight") || features.has("witch hunter")) {
    const residues = Array.isArray(state?.visible_psychic_residue) ? state.visible_psychic_residue : [];
    const residuePanel = document.createElement("div");
    residuePanel.className = "item-help";
    residuePanel.textContent = residues.length
      ? `Psionic Sight: ${residues.map((entry) => {
          const linked = Array.isArray(entry.linked_targets) && entry.linked_targets.length
            ? ` [linked: ${entry.linked_targets.join(", ")}]`
            : "";
          return `${entry.target_name}: ${((entry.sources || []).join(", ")) || "Unknown"}${linked}`;
        }).join(" | ")}`
      : "Psionic Sight: no visible psychic residue right now.";
    section.appendChild(residuePanel);
  }

  if (hints.effective_weather) {
    const weatherInfo = document.createElement("div");
    weatherInfo.className = "item-help";
    weatherInfo.textContent = hints.effective_weather_source
      ? `Weather State: ${hints.effective_weather} via ${hints.effective_weather_source}.`
      : `Weather State: ${hints.effective_weather}.`;
    section.appendChild(weatherInfo);
  }

  if (features.has("adaptive geography")) {
    const aliases = Array.isArray(hints.adaptive_geography_aliases) ? hints.adaptive_geography_aliases : [];
    const info = document.createElement("div");
    info.className = "item-help";
    info.textContent = aliases.length
      ? `Adaptive Geography: acting as ${aliases.join(", ")} this turn.`
      : `Adaptive Geography: ${Math.max(0, Number(hints.adaptive_geography_uses_left || 0))} uses left this scene.`;
    section.appendChild(info);
  }

  if (features.has("natural fighter")) {
    const terrainLabel = hints.terrain_label || "current terrain";
    const moveName = hints.natural_fighter_move;
    const targetMode = hints.natural_fighter_target_mode;
    const targetOptions = (hints.natural_fighter_targets || []).map((entry) => ({
      value: entry.target,
      label: entry.target_name || entry.target,
    }));
    addTrainerFeatureButton(
      list,
      moveName ? `Natural Fighter: ${moveName}` : "Natural Fighter",
      canAct && !!moveName && !!hints.natural_fighter_ap_ready && (targetMode !== "target" || targetOptions.length > 0),
      () => {
        if (targetMode === "target") {
          pickTrainerFeatureOption(
            `${moveName} Target`,
            targetOptions,
            (targetId) => {
              commitAction({ type: "trainer_feature", action_key: "natural_fighter", actor_id: combatant.id, target_id: targetId }).catch(alertError);
            },
            `Use ${moveName} via Natural Fighter in ${terrainLabel}.`
          );
          return;
        }
        commitAction({ type: "trainer_feature", action_key: "natural_fighter", actor_id: combatant.id }).catch(alertError);
      },
      !moveName ? `Natural Fighter requires a mapped terrain. Current terrain: ${terrainLabel}.` : (!hints.natural_fighter_ap_ready ? "Requires 1 AP." : `Use ${moveName} based on ${terrainLabel}.`)
    );
  }

  if (features.has("wilderness guide")) {
    const terrainLabel = hints.terrain_label || "current terrain";
    addTrainerFeatureButton(
      list,
      `Wilderness Guide (${Math.max(0, Number(hints.wilderness_guide_uses_left || 0))} left)`,
      canAct && !!hints.wilderness_guide_ready,
      () => {
        commitAction({ type: "trainer_feature", action_key: "wilderness_guide", actor_id: combatant.id }).catch(alertError);
      },
      !hints.terrain_label
        ? "Wilderness Guide requires current terrain."
        : (Number(hints.wilderness_guide_uses_left || 0) <= 0 ? "Wilderness Guide is out of uses this scene." : `Grant terrain-based ally buffs for ${terrainLabel}.`)
    );
  }

  if (features.has("psionic analysis")) {
    const residues = Array.isArray(hints.psionic_analysis_targets) ? hints.psionic_analysis_targets : [];
    addTrainerFeatureButton(
      list,
      `Psionic Analysis (${Math.max(0, Number(hints.psionic_analysis_uses_left || 0))} left)`,
      canAct && !!hints.psionic_analysis_ready,
      () => {
        pickTrainerFeatureOption(
          "Analyze Residue",
          residues.map((entry) => ({
            value: entry.target,
            label: entry.target_name || entry.target,
            meta: (() => {
              const base = ((entry.sources || []).join(", ")) || "Unknown source";
              const linked = Array.isArray(entry.linked_targets) && entry.linked_targets.length
                ? ` | linked: ${entry.linked_targets.join(", ")}`
                : "";
              return `${base}${linked}`;
            })(),
          })),
          (targetId) => {
            commitAction({
              type: "trainer_feature",
              action_key: "psionic_analysis",
              actor_id: combatant.id,
              target_id: targetId,
            }).catch(alertError);
          },
          "Analyze visible psychic residue on a target."
        );
      },
      !residues.length
        ? "No visible psychic residue to analyze."
        : (Number(hints.psionic_analysis_uses_left || 0) <= 0 ? "Psionic Analysis is out of uses this scene." : "")
    );
  }

  if (features.has("psionic sponge")) {
    const sources = Array.isArray(hints.psionic_sponge_sources) ? hints.psionic_sponge_sources : [];
    addTrainerFeatureButton(
      list,
      `Psionic Sponge (${Math.max(0, Number(hints.psionic_sponge_uses_left || 0))} left)`,
      canAct && !!hints.psionic_sponge_ready,
      () => {
        pickTrainerFeatureOption(
          "Psionic Sponge Source",
          sources.map((entry) => ({
            value: entry.target,
            label: entry.target_name || entry.target,
            meta: (entry.moves || []).map((move) => move.move_name || move.move).join(", "),
          })),
          (allyId) => {
            const source = sources.find((entry) => entry.target === allyId);
            const moveOptions = (source?.moves || []).map((move) => ({
              value: move.move || move.move_name,
              label: move.move_name || move.move,
            }));
            if (!moveOptions.length) {
              notifyUI("warn", "No Psychic moves remain to borrow from that ally.", 2200);
              return;
            }
            pickTrainerFeatureOption(
              "Borrow Psychic Move",
              moveOptions,
              (moveName) => {
                commitAction({
                  type: "trainer_feature",
                  action_key: "psionic_sponge",
                  actor_id: combatant.id,
                  ally_id: allyId,
                  move_name: moveName,
                }).catch(alertError);
              },
              `Borrow a Psychic move from an ally within ${Math.max(0, Number(hints.psionic_sponge_range || 0))} meters until end of turn.`
            );
          },
          `Choose an allied Psychic move source within ${Math.max(0, Number(hints.psionic_sponge_range || 0))} meters.`
        );
      },
      !sources.length
        ? "No allied Psychic moves are available to borrow right now."
        : (Number(hints.psionic_sponge_uses_left || 0) <= 0
          ? "Psionic Sponge is out of uses for this Pokemon this scene."
          : `Borrow an allied Psychic move within ${Math.max(0, Number(hints.psionic_sponge_range || 0))} meters.`)
    );
  }

  if (features.has("mindbreak")) {
    const targets = (hints.mindbreak_targets || []).map((entry) => ({
      value: entry.target,
      label: entry.target_name || entry.target,
    }));
    const boundTargets = (hints.mindbreak_bound_targets || []).map((entry) => entry.target_name || entry.target).filter(Boolean);
    addTrainerFeatureButton(
      list,
      boundTargets.length ? `Mindbreak: ${boundTargets.join(", ")}` : "Mindbreak",
      canAct && !!hints.mindbreak_ap_ready && targets.length > 0,
      () => {
        pickTrainerFeatureOption(
          "Mindbreak Target",
          targets,
          (targetId) => {
            commitAction({ type: "trainer_feature", action_key: "mindbreak", actor_id: combatant.id, target_id: targetId }).catch(alertError);
          },
          "Bind Mindbreak to an allied Psychic-type Pokemon."
        );
      },
      !targets.length ? "No allied Psychic-type target is available." : (!hints.mindbreak_ap_ready ? "Requires 2 AP." : "Bind Mindbreak to amplify afflicted Psychic attacks.")
    );
    if (hints.mindbreak_release_ready) {
      addTrainerFeatureButton(
        list,
        "Release Mindbreak",
        canAct,
        () => {
          commitAction({ type: "trainer_feature", action_key: "release_mindbreak", actor_id: combatant.id }).catch(alertError);
        },
        "Release the current Mindbreak binding."
      );
    }
  }

  if (features.has("tough as schist")) {
    const targets = (hints.tough_as_schist_targets || []).map((entry) => ({
      value: entry.target,
      label: entry.target_name || entry.target,
    }));
    const boundTargets = (hints.tough_as_schist_bound_targets || []).map((entry) => entry.target_name || entry.target).filter(Boolean);
    addTrainerFeatureButton(
      list,
      boundTargets.length ? `Tough as Schist: ${boundTargets.join(", ")}` : "Tough as Schist",
      canAct && !!hints.tough_as_schist_ap_ready && targets.length > 0,
      () => {
        pickTrainerFeatureOption(
          "Tough as Schist Target",
          targets,
          (targetId) => {
            commitAction({ type: "trainer_feature", action_key: "tough_as_schist", actor_id: combatant.id, target_id: targetId }).catch(alertError);
          },
          "Bind Tough as Schist to an allied Rock-type Pokemon."
        );
      },
      !targets.length ? "No allied Rock-type target is available." : (!hints.tough_as_schist_ap_ready ? "Requires 2 AP." : "Bind Tough as Schist to preserve nearby Stealth Rock and turn it into armor.")
    );
    if (hints.tough_as_schist_release_ready) {
      addTrainerFeatureButton(
        list,
        "Release Tough as Schist",
        canAct,
        () => {
          commitAction({ type: "trainer_feature", action_key: "release_tough_as_schist", actor_id: combatant.id }).catch(alertError);
        },
        "Release the current Tough as Schist binding."
      );
    }
  }

  if (features.has("psionic overload")) {
    const overloadMove = String(hints.psionic_overload_move || "").trim();
    const overloadTarget = String(hints.psionic_overload_target_name || hints.psionic_overload_target || "").trim();
    const barrierCount = psionicOverloadBarrierTiles.length;
    const overloadArmed = armedTileAction === "psionic_overload_barrier";
    addTrainerFeatureButton(
      list,
      overloadArmed
        ? `Psionic Overload: Barrier (${barrierCount}/2)`
        : "Psionic Overload",
      canAct && !!hints.psionic_overload_ready,
      () => {
        if (String(overloadMove).toLowerCase() === "barrier") {
          if (!overloadArmed) {
            clearArmedTileAction();
            armedTileAction = "psionic_overload_barrier";
            render();
            return;
          }
          if (barrierCount !== 2) {
            alertError(new Error("Select exactly 2 barrier segment tiles."));
            return;
          }
          commitAction({
            type: "trainer_feature",
            action_key: "psionic_overload_follow_up",
            actor_id: combatant.id,
            barrier_tiles: psionicOverloadBarrierTiles,
          }).catch(alertError);
          return;
        }
        commitAction({
          type: "trainer_feature",
          action_key: "psionic_overload_follow_up",
          actor_id: combatant.id,
        }).catch(alertError);
      },
      !hints.psionic_overload_ready
        ? "Psionic Overload becomes available after Kinesis, Barrier, Psychic, or Telekinesis."
        : (String(overloadMove).toLowerCase() === "barrier"
            ? `Place 2 extra Barrier segments within 6 meters. Triggered by ${overloadMove}.`
            : `Trigger move: ${overloadMove}${overloadTarget ? ` on ${overloadTarget}` : ""}. Spend 1 AP for the extra rider.`)
    );
  }

  if (features.has("force of will")) {
    const moveOptions = (hints.force_of_will_moves || []).map((entry) => ({
      value: entry.move || entry.move_name,
      label: entry.move_name || entry.move,
    }));
    const triggerMove = hints.force_of_will_trigger_move;
    addTrainerFeatureButton(
      list,
      `Force of Will (${Math.max(0, Number(hints.force_of_will_uses_left || 0))} left)`,
      canAct && !!hints.force_of_will_ready && moveOptions.length > 0,
      () => {
        pickTrainerFeatureOption(
          "Force of Will Move",
          moveOptions,
          (moveName) => {
            commitAction({ type: "trainer_feature", action_key: "force_of_will_follow_up", actor_id: combatant.id, move_name: moveName }).catch(alertError);
          },
          triggerMove ? `Trigger move: ${triggerMove}` : "Use another eligible Psychic status move."
        );
      },
      !hints.force_of_will_ready
        ? "Force of Will becomes available after using an eligible Psychic status move."
        : `Follow ${triggerMove || "the trigger"} with another eligible Psychic status move.`
    );
  }

  if (features.has("trapper")) {
    const usesLeft = Math.max(0, Number(hints.trapper_uses_left || 0));
    const terrainLabel = hints.terrain_label || "current terrain";
    const draftCount = trapperDraftTiles.length;
    const trapperArmed = armedTileAction === "trapper";
    addTrainerFeatureButton(
      list,
      trapperArmed
        ? (draftCount >= 8 ? `Trapper: Deploy (${draftCount}/8)` : `Trapper: Paint (${draftCount}/8)`)
        : `Trapper (${usesLeft} left)`,
      canAct && !!hints.trapper_ready,
      () => {
        if (!trapperArmed) {
          trapperDraftTiles = [];
          armedTileAction = "trapper";
          render();
          return;
        }
        if (draftCount === 8) {
          if (!trapperTilesAreContiguous(trapperDraftTiles)) {
            alertError(new Error("Trap tiles must form a contiguous cluster."));
            return;
          }
          commitAction({
            type: "trainer_feature",
            action_key: "trapper",
            actor_id: combatant.id,
            target_positions: trapperDraftTiles,
          }).catch(alertError);
          return;
        }
        clearArmedTileAction();
        render();
      },
      !hints.terrain_label
        ? "Trapper requires matching terrain."
        : (usesLeft <= 0
            ? "Trapper is out of uses for this battle."
            : (trapperArmed
                ? `Paint exactly 8 contiguous ${terrainLabel}-linked trap tiles within 6 meters. Drag to add tiles; click selected tiles to remove them. Click the button again to cancel before deployment.`
                : `Deploy an exact 8-tile ${terrainLabel}-linked trap layout within 6 meters.`))
    );
  }

  (hints.trickster_targets || []).forEach((targetId) => {
    const target = tricksterOptionMap.get(targetId);
    const label = target?.target_name ? `Trickster: ${target.target_name}` : `Trickster: ${targetId}`;
    addTrainerFeatureButton(list, label, canAct, () => {
      const optionEntry = tricksterOptionMap.get(targetId) || {};
      const options = [
        ...(optionEntry.manipulate || []).map((trick) => ({ value: `manipulate:${trick}`, label: `Manipulate: ${trick}` })),
        ...(optionEntry.dirty_trick || []).map((trick) => ({ value: `dirty_trick:${trick}`, label: `Dirty Trick: ${trick}` })),
      ];
      if (!options.length) {
        notifyUI("warn", "No Trickster maneuver options remain for that target this scene.", 2200);
        return;
      }
      pickTrainerFeatureOption("Trickster Follow-Up", options, (value) => {
        const [maneuver_kind, trick] = String(value || "").split(":");
        commitAction({ type: "trainer_feature", action_key: "trickster_follow_up", actor_id: combatant.id, maneuver_kind, trick, target_id: targetId }).catch(alertError);
      });
    });
  });

  (hints.dirty_fighting_targets || []).forEach((targetId) => {
    const target = dirtyFightingOptionMap.get(targetId);
    addTrainerFeatureButton(list, target?.target_name ? `Dirty Fighting: ${target.target_name}` : `Dirty Fighting: ${targetId}`, canAct && !!hints.dirty_fighting_ap_ready, () => {
      const options = (dirtyFightingOptionMap.get(targetId)?.tricks || []).map((trick) => ({ value: trick, label: trick }));
      if (!options.length) {
        notifyUI("warn", "No Dirty Fighting tricks remain for that target this scene.", 2200);
        return;
      }
      pickTrainerFeatureOption("Dirty Fighting Trick", options, (trick) => {
        commitAction({ type: "trainer_feature", action_key: "dirty_fighting_follow_up", actor_id: combatant.id, trick, target_id: targetId }).catch(alertError);
      });
    }, !hints.dirty_fighting_ap_ready ? "Requires 1 AP." : "Spend 1 AP for a Dirty Trick follow-up.");
  });

  (hints.weapon_finesse_targets || []).forEach((targetId) => {
    const target = weaponFinesseOptionMap.get(targetId);
    addTrainerFeatureButton(list, target?.target_name ? `Weapon Finesse: ${target.target_name}` : `Weapon Finesse: ${targetId}`, canAct && !!hints.weapon_finesse_ap_ready, () => {
      pickTrainerFeatureOption("Weapon Finesse Maneuver", ["Push", "Trip", "Disarm"], (maneuver) => {
        commitAction({ type: "trainer_feature", action_key: "weapon_finesse_follow_up", actor_id: combatant.id, maneuver, target_id: targetId }).catch(alertError);
      });
    }, !hints.weapon_finesse_ap_ready ? "Requires 2 AP." : "Spend 2 AP for a free combat maneuver follow-up.");
  });

  (hints.play_them_like_a_fiddle_ready || []).forEach((entry) => {
    const targetName = entry.target_name || targetMap.get(entry.target)?.label || entry.target;
    const moveName = String(entry.move || "").trim();
    const label = `Play Them Like a Fiddle: ${moveName} -> ${targetName}`;
    const moveKey = moveName.toLowerCase();
    const requiresMoveChoice = moveKey === "confide";
    const requiresAbilityChoice = moveKey === "torment";
    const canResolveChoice = (!requiresMoveChoice || (entry.target_moves || []).length > 0)
      && (!requiresAbilityChoice || (entry.target_abilities || []).length > 0);
    addTrainerFeatureButton(list, `${label} (${Math.max(0, Number(hints.play_them_like_a_fiddle_uses_left || 0))} left)`, canAct && canResolveChoice && Number(hints.play_them_like_a_fiddle_uses_left || 0) > 0, () => {
      const payload = {
        type: "trainer_feature",
        action_key: "play_them_like_a_fiddle_follow_up",
        actor_id: combatant.id,
        target_id: entry.target,
        move_name: moveName,
      };
      if (requiresMoveChoice && (entry.target_moves || []).length) {
        pickTrainerFeatureOption(
          "Disable Move",
          (entry.target_moves || []).map((name) => ({ value: name, label: name })),
          (chosenMove) => {
            commitAction({ ...payload, chosen_move: chosenMove }).catch(alertError);
          },
          "Choose a move the target has used this scene."
        );
        return;
      }
      if (requiresAbilityChoice && (entry.target_abilities || []).length > 1) {
        pickTrainerFeatureOption(
          "Disable Ability",
          (entry.target_abilities || []).map((name) => ({ value: name, label: name })),
          (chosenAbility) => {
            commitAction({ ...payload, chosen_ability: chosenAbility }).catch(alertError);
          },
          "Choose one of the target's abilities to disable."
        );
        return;
      }
      if (!canResolveChoice) {
        notifyUI("warn", `No valid ${requiresMoveChoice ? "moves" : "abilities"} remain for ${moveName}.`, 2200);
        return;
      }
      commitAction(payload).catch(alertError);
    }, !canResolveChoice ? `No valid ${requiresMoveChoice ? "moves" : "abilities"} remain for this rider.` : (Number(hints.play_them_like_a_fiddle_uses_left || 0) <= 0 ? "Play Them Like a Fiddle is out of uses this scene." : ""));
  });

  (hints.psychic_resonance_targets || []).forEach((targetId) => {
    const target = psychicResonanceOptionMap.get(targetId);
    addTrainerFeatureButton(list, target?.target_name ? `Psychic Resonance: ${target.target_name} (${Math.max(0, Number(hints.psychic_resonance_uses_left || 0))} left)` : `Psychic Resonance: ${targetId}`, canAct && Number(hints.psychic_resonance_uses_left || 0) > 0, () => {
      commitAction({ type: "trainer_feature", action_key: "psychic_resonance_follow_up", actor_id: combatant.id, target_id: targetId }).catch(alertError);
    }, Number(hints.psychic_resonance_uses_left || 0) <= 0 ? "Psychic Resonance is out of uses this scene." : "Use Encore as a free follow-up.");
  });

  if (!list.childNodes.length) return;
  section.appendChild(list);
  moveListEl.appendChild(section);
}

function battleTargetOptionsFromIds(targetIds) {
  const byId = new Map((state.combatants || []).map((entry) => [entry.id, entry]));
  return (targetIds || [])
    .map((targetId) => {
      const target = byId.get(targetId);
      if (!target) return null;
      return {
        value: targetId,
        label: `${target.name || target.species || targetId}${target.position ? ` (${target.position[0]},${target.position[1]})` : ""}`,
      };
    })
    .filter(Boolean);
}

function battleTileOptions(coords) {
  return (coords || []).map((coord) => ({
    value: `${coord[0]},${coord[1]}`,
    label: `(${coord[0]}, ${coord[1]})`,
  }));
}

function selectedTileCoord() {
  if (!selectedTileKey) return null;
  const match = String(selectedTileKey || "").match(/-?\d+/g) || [];
  if (match.length < 2) return null;
  return [Number(match[0]), Number(match[1])];
}

function selectedTileOccupantId() {
  if (!selectedTileKey || !state?.occupants) return null;
  return state.occupants[selectedTileKey] || null;
}

function submitManeuverMove(actorId, moveName, targetIds) {
  const allowed = Array.isArray(targetIds) ? targetIds.filter(Boolean) : [];
  const selectedOccupant = selectedTileOccupantId();
  if (selectedOccupant && allowed.includes(selectedOccupant)) {
    commitAction({ type: "move", actor_id: actorId, move: moveName, target_id: selectedOccupant }).catch(alertError);
    return;
  }
  if (!allowed.length) {
    notifyUI("warn", `No legal targets for ${moveName}.`, 2200);
    return;
  }
  if (allowed.length === 1) {
    commitAction({ type: "move", actor_id: actorId, move: moveName, target_id: allowed[0] }).catch(alertError);
    return;
  }
  pickTrainerFeatureOption(`Target for ${moveName}`, battleTargetOptionsFromIds(allowed), (targetId) => {
    commitAction({ type: "move", actor_id: actorId, move: moveName, target_id: targetId }).catch(alertError);
  }, "Select a legal target for this combat maneuver.");
}

function submitTileAction(actionType, actorId, coords, extra = {}, title = "Choose Tile") {
  const selected = selectedTileCoord();
  const key = selected ? `${selected[0]},${selected[1]}` : "";
  const allowed = new Set((coords || []).map((coord) => `${coord[0]},${coord[1]}`));
  if (selected && allowed.has(key)) {
    commitAction({ type: actionType, actor_id: actorId, destination: selected, ...extra }).catch(alertError);
    return;
  }
  const options = battleTileOptions(coords);
  if (!options.length) {
    notifyUI("warn", "No legal destination tiles are available.", 2200);
    return;
  }
  pickTrainerFeatureOption(title, options, (value) => {
    const match = String(value || "").match(/-?\d+/g) || [];
    if (match.length < 2) return;
    commitAction({
      type: actionType,
      actor_id: actorId,
      destination: [Number(match[0]), Number(match[1])],
      ...extra,
    }).catch(alertError);
  }, "Select a destination tile, or click a tile first and then use the action.");
}

function recommendCreativeBattleAction(intentText, capabilityName = "") {
  const text = String(intentText || "").toLowerCase();
  const capability = String(capabilityName || "").toLowerCase();
  let skill = "focus";
  let dc = 12;
  let note = "Standard improvised stunt.";
  if (/(jump|leap|vault|balance|swing|dodge|midair|climb)/.test(text) || /(wallclimber|levitate|guster|threaded)/.test(capability)) {
    skill = "acrobatics";
    dc = 12;
    note = "Mobility or finesse stunt.";
  } else if (/(push|shove|lift|throw|drag|break|rush|slam|grapple|carry)/.test(text) || /(power|burrow|swim|reach)/.test(capability)) {
    skill = "athletics";
    dc = 12;
    note = "Force or exertion stunt.";
  } else if (/(telekin|telepath|phase|teleport|precise|concentrat|mind|psionic)/.test(text) || /(telekinetic|telepath|phasing|teleporter)/.test(capability)) {
    skill = "focus";
    dc = 16;
    note = "Precision or mental-control stunt.";
  } else if (/(taunt|fake|feint|trick|dirty|blind|distract)/.test(text)) {
    skill = "guile";
    dc = 12;
    note = "Dirty trick or deception stunt.";
  } else if (/(scout|spot|track|watch|notice)/.test(text)) {
    skill = "perception";
    dc = 12;
    note = "Perception-led battlefield read.";
  }
  if (/(under attack|while hit|mid[- ]?turn|exact timing|delicate)/.test(text)) {
    dc += 4;
    note = `${note} Focus may also apply.`;
  }
  if (/(extreme|desperate|impossible)/.test(text)) {
    dc = Math.max(dc, 20);
  } else if (/(easy|simple|routine)/.test(text)) {
    dc = Math.min(dc, 8);
  }
  return { skill, dc, note };
}

function creativeConsequenceHelp(value) {
  const map = {
    "": "Roll only. No automatic battlefield effect is applied.",
    self_reposition: "Move the acting combatant to the selected tile on success.",
    forced_reposition: "Move the target combatant to the selected tile on success.",
    push_target: "Win a contest and shove the target to the selected tile on success.",
    trip_target: "Apply Tripped to the target on success.",
    vulnerable_target: "Apply Vulnerable to the target on success.",
    slow_target: "Apply Slowed to the target on success.",
    grant_cover_self: "Grant yourself temporary cover as damage reduction.",
    grant_cover_target: "Grant the target temporary cover as damage reduction.",
    trigger_hazard_self: "Immediately resolve tile hazards/traps on the acting combatant.",
    trigger_hazard_target: "Immediately resolve tile hazards/traps on the target combatant.",
  };
  return map[String(value || "")] || "Creative consequence.";
}

function renderBattleManeuverActions(moveListEl, combatant, canAct) {
  const context = state.maneuver_context || {};
  const maneuvers = Array.isArray(state.maneuvers) ? state.maneuvers : [];
  if (!maneuvers.length && !context.grapple_status) return;
  const section = document.createElement("div");
  section.className = "item-section";
  const title = document.createElement("div");
  title.className = "item-title";
  title.textContent = "Battle Maneuvers";
  section.appendChild(title);
  const info = document.createElement("div");
  info.className = "creative-help";
  info.textContent = "PTU Core p.228 allows combat actions using maneuvers, capabilities, and skill checks.";
  section.appendChild(info);
  const list = document.createElement("div");
  list.className = "item-list";

  maneuvers.forEach((move) => {
    const btn = document.createElement("button");
    btn.className = "item-button";
    btn.textContent = move.name;
    const targetIds = (state.maneuver_targets && state.maneuver_targets[move.name]) || [];
    if (!canAct || !targetIds.length) {
      btn.classList.add("inactive");
      btn.setAttribute("aria-disabled", "true");
    }
    btn.addEventListener("click", () => {
      if (!canAct) return;
      submitManeuverMove(combatant.id, move.name, targetIds);
    });
    btn.addEventListener("mouseenter", () => {
      clearTooltipHideTimer();
      showDetailTooltip(btn, `Maneuver: ${move.name}`, move.effects || "Combat maneuver.");
    });
    btn.addEventListener("mouseleave", () => {
      scheduleTooltipHide();
    });
    list.appendChild(btn);
  });

  const addUtilityButton = (label, enabled, onClick, tooltip) => {
    const btn = document.createElement("button");
    btn.className = "item-button";
    btn.textContent = label;
    if (!canAct || !enabled) {
      btn.classList.add("inactive");
      btn.setAttribute("aria-disabled", "true");
    }
    btn.addEventListener("click", () => {
      if (!canAct || !enabled) return;
      onClick();
    });
    if (tooltip) {
      btn.addEventListener("mouseenter", () => {
        clearTooltipHideTimer();
        showDetailTooltip(btn, label, tooltip);
      });
      btn.addEventListener("mouseleave", () => {
        scheduleTooltipHide();
      });
    }
    list.appendChild(btn);
  };

  addUtilityButton(
    "Disengage",
    Array.isArray(context.disengage_tiles) && context.disengage_tiles.length > 1,
    () => submitTileAction("disengage", combatant.id, context.disengage_tiles || [], {}, "Disengage Tile"),
    "Shift 1 meter without provoking attacks of opportunity."
  );
  addUtilityButton("Sprint", true, () => {
    commitAction({ type: "sprint", actor_id: combatant.id }).catch(alertError);
  }, "Increase movement by 50% for the rest of the turn.");
  addUtilityButton(
    "Wake Ally",
    Array.isArray(context.wake_targets) && context.wake_targets.length > 0,
    () => {
      pickTrainerFeatureOption("Wake Ally", (context.wake_targets || []).map((entry) => ({ value: entry.id, label: entry.name })), (targetId) => {
        commitAction({ type: "wake_ally", actor_id: combatant.id, target_id: targetId }).catch(alertError);
      });
    },
    "Use a Standard Action to wake an adjacent sleeping ally."
  );
  addUtilityButton(
    "Intercept (Melee)",
    Array.isArray(context.intercept_melee_targets) && context.intercept_melee_targets.length > 0,
    () => {
      pickTrainerFeatureOption("Intercept Melee", (context.intercept_melee_targets || []).map((entry) => ({ value: entry.id, label: entry.name })), (allyId) => {
        commitAction({ type: "intercept", actor_id: combatant.id, ally_id: allyId, kind: "melee" }).catch(alertError);
      });
    },
    "Prepare a melee intercept for an ally."
  );
  addUtilityButton(
    "Intercept (Ranged)",
    Array.isArray(context.intercept_ranged_targets) && context.intercept_ranged_targets.length > 0,
    () => {
      pickTrainerFeatureOption("Intercept Ranged", (context.intercept_ranged_targets || []).map((entry) => ({ value: entry.id, label: entry.name })), (allyId) => {
        commitAction({ type: "intercept", actor_id: combatant.id, ally_id: allyId, kind: "ranged" }).catch(alertError);
      });
    },
    "Prepare a ranged intercept for an ally."
  );
  addUtilityButton(
    "Manipulate",
    Array.isArray(context.manipulate_targets) && context.manipulate_targets.length > 0,
    () => {
      pickTrainerFeatureOption("Manipulate Trick", ["Bon Mot", "Flirt", "Terrorize"], (trick) => {
        pickTrainerFeatureOption("Manipulate Target", (context.manipulate_targets || []).map((entry) => ({ value: entry.id, label: entry.name })), (targetId) => {
          commitAction({ type: "manipulate", actor_id: combatant.id, trick, target_id: targetId }).catch(alertError);
        });
      }, "Trainer-only social combat maneuver.");
    },
    "Trainer-only manipulate action within 6 meters."
  );
  addUtilityButton("Pick Up Item", !!context.pickup_available, () => {
    commitAction({ type: "pickup_item", actor_id: combatant.id }).catch(alertError);
  }, "Pick up an item on the current tile.");

  if (context.grapple_status) {
    const grappleTitle = document.createElement("div");
    grappleTitle.className = "creative-subtitle";
    grappleTitle.textContent = "Grapple Actions";
    section.appendChild(grappleTitle);
    const grappleList = document.createElement("div");
    grappleList.className = "item-list";
    const dominant = !!context.grapple_status.dominant;
    const immediateActions = dominant ? ["end", "secure", "attack"] : ["contest", "escape"];
    immediateActions.forEach((kind) => {
      addUtilityButton(
        `Grapple: ${kind[0].toUpperCase()}${kind.slice(1)}`,
        true,
        () => commitAction({ type: "grapple", actor_id: combatant.id, action_kind: kind, target_id: context.grapple_status.other_id }).catch(alertError),
        `Resolve grapple action: ${kind}.`
      );
    });
    if (dominant) {
      const moveBtn = document.createElement("button");
      moveBtn.className = "item-button";
      moveBtn.textContent = "Grapple: Move";
      moveBtn.addEventListener("click", () => {
        if (!canAct) return;
        submitTileAction(
          "grapple",
          combatant.id,
          context.grapple_move_tiles || [],
          { action_kind: "move", target_id: context.grapple_status.other_id },
          "Grapple Move Tile"
        );
      });
      grappleList.appendChild(moveBtn);
    }
    section.appendChild(grappleList);
  }

  section.appendChild(list);
  moveListEl.appendChild(section);
}

function renderCreativeBattleAction(moveListEl, combatant, canAct) {
  const section = document.createElement("div");
  section.className = "item-section creative-section";
  const title = document.createElement("div");
  title.className = "item-title";
  title.textContent = "Creative Action";
  section.appendChild(title);
  const help = document.createElement("div");
  help.className = "creative-help";
  help.textContent = "Use improvised actions, capability stunts, and custom skill checks. The engine will roll and log the result.";
  section.appendChild(help);

  const skills = Object.keys(combatant.skills || {}).sort();
  const capabilities = Array.isArray(combatant.capabilities) ? combatant.capabilities : [];
  const enemies = (state.combatants || []).filter((entry) => entry.id !== combatant.id && entry.active && !entry.fainted);
  const context = state.maneuver_context || {};

  const form = document.createElement("div");
  form.className = "creative-form";
  form.innerHTML = `
    <input class="creative-title" type="text" placeholder="Stunt title" value="Creative Action" ${canAct ? "" : "disabled"} />
    <textarea class="creative-intent" placeholder="Describe the stunt, movement, or clever idea." ${canAct ? "" : "disabled"}></textarea>
    <div class="creative-grid">
      <label>Skill<select class="creative-skill" ${canAct ? "" : "disabled"}>${skills.map((skill) => `<option value="${skill}">${skill}</option>`).join("")}</select></label>
      <label>Capability<select class="creative-capability" ${canAct ? "" : "disabled"}><option value="">None</option>${capabilities.map((cap) => `<option value="${cap}">${cap}</option>`).join("")}</select></label>
      <label>Secondary Skill<select class="creative-secondary" ${canAct ? "" : "disabled"}><option value="">None</option>${skills.map((skill) => `<option value="${skill}">${skill}</option>`).join("")}</select></label>
      <label>Check Mode<select class="creative-check-mode" ${canAct ? "" : "disabled"}><option value="auto">Auto</option><option value="dc">DC Check</option><option value="opposed">Opposed Contest</option></select></label>
      <label>Action Cost<select class="creative-cost" ${canAct ? "" : "disabled"}><option value="standard">Standard</option><option value="shift">Shift</option><option value="swift">Swift</option><option value="full">Full</option><option value="free">Free</option></select></label>
      <label>DC<input class="creative-dc" type="number" min="1" value="12" ${canAct ? "" : "disabled"} /></label>
      <label>Opposed Skill<select class="creative-opposed" ${canAct ? "" : "disabled"}><option value="">None</option>${skills.map((skill) => `<option value="${skill}">${skill}</option>`).join("")}</select></label>
      <label>Target<select class="creative-target" ${canAct ? "" : "disabled"}><option value="">None</option>${enemies.map((entry) => `<option value="${entry.id}">${entry.name || entry.species || entry.id}</option>`).join("")}</select></label>
      <label>Consequence<select class="creative-consequence" ${canAct ? "" : "disabled"}>
        <option value="">Roll Only</option>
        <option value="self_reposition">Self Reposition</option>
        <option value="forced_reposition">Force Reposition Target</option>
        <option value="push_target">Push Target To Tile</option>
        <option value="trip_target">Trip Target</option>
        <option value="vulnerable_target">Make Target Vulnerable</option>
        <option value="slow_target">Slow Target</option>
        <option value="grant_cover_self">Grant Self Cover</option>
        <option value="grant_cover_target">Grant Target Cover</option>
        <option value="trigger_hazard_self">Trigger Hazards On Self</option>
        <option value="trigger_hazard_target">Trigger Hazards On Target</option>
      </select></label>
      <label>Consequence Value<input class="creative-consequence-value" type="number" min="1" value="1" ${canAct ? "" : "disabled"} /></label>
      <label>Use Selected Tile<select class="creative-tile" ${canAct ? "" : "disabled"}><option value="">No</option><option value="selected">Selected Tile</option></select></label>
    </div>
    <div class="creative-consequence-help">Roll only. No automatic battlefield effect is applied.</div>
    <input class="creative-note" type="text" placeholder="Optional GM note or consequence text" ${canAct ? "" : "disabled"} />
    <div class="creative-actions">
      <button type="button" class="item-button creative-recommend" ${canAct ? "" : "disabled"}>Recommend Roll</button>
      <button type="button" class="item-button creative-submit" ${canAct ? "" : "disabled"}>Resolve Creative Action</button>
    </div>
  `;
  const titleInput = form.querySelector(".creative-title");
  const intentInput = form.querySelector(".creative-intent");
  const skillSelect = form.querySelector(".creative-skill");
  const capabilitySelect = form.querySelector(".creative-capability");
  const secondarySelect = form.querySelector(".creative-secondary");
  const checkModeSelect = form.querySelector(".creative-check-mode");
  const costSelect = form.querySelector(".creative-cost");
  const dcInput = form.querySelector(".creative-dc");
  const opposedSelect = form.querySelector(".creative-opposed");
  const targetSelect = form.querySelector(".creative-target");
  const consequenceSelect = form.querySelector(".creative-consequence");
  const consequenceValueInput = form.querySelector(".creative-consequence-value");
  const tileSelect = form.querySelector(".creative-tile");
  const consequenceHelpEl = form.querySelector(".creative-consequence-help");
  const noteInput = form.querySelector(".creative-note");
  const recommendBtn = form.querySelector(".creative-recommend");
  const submitBtn = form.querySelector(".creative-submit");

  recommendBtn?.addEventListener("click", () => {
    const recommendation = recommendCreativeBattleAction(intentInput?.value || "", capabilitySelect?.value || "");
    if (skillSelect) skillSelect.value = recommendation.skill;
    if (dcInput) dcInput.value = recommendation.dc;
    if (checkModeSelect && !(targetSelect?.value && opposedSelect?.value)) checkModeSelect.value = "dc";
    if (noteInput && !noteInput.value) noteInput.value = recommendation.note;
    notifyUI("info", `Recommended ${recommendation.skill} vs DC ${recommendation.dc}.`, 2200);
  });
  const syncCreativeMode = () => {
    const mode = checkModeSelect?.value || "auto";
    if (dcInput) dcInput.disabled = !canAct || mode === "opposed";
    if (opposedSelect) opposedSelect.disabled = !canAct || mode === "dc";
    if (targetSelect) targetSelect.disabled = !canAct ? true : false;
  };
  checkModeSelect?.addEventListener("change", syncCreativeMode);
  consequenceSelect?.addEventListener("change", () => {
    if (consequenceHelpEl) consequenceHelpEl.textContent = creativeConsequenceHelp(consequenceSelect.value);
  });
  syncCreativeMode();
  submitBtn?.addEventListener("click", () => {
    if (!canAct) return;
    const selectedTile = tileSelect?.value === "selected" ? selectedTileCoord() : null;
    commitAction({
      type: "creative_action",
      actor_id: combatant.id,
      title: titleInput?.value || "Creative Action",
      description: intentInput?.value || "",
      skill: skillSelect?.value || "",
      capability: capabilitySelect?.value || "",
      secondary_skill: secondarySelect?.value || "",
      check_mode: checkModeSelect?.value || "auto",
      action_cost: costSelect?.value || "standard",
      dc: dcInput?.value || "",
      opposed_skill: opposedSelect?.value || "",
      target_id: targetSelect?.value || "",
      consequence: consequenceSelect?.value || "",
      consequence_value: consequenceValueInput?.value || "",
      target_position: selectedTile,
      note: noteInput?.value || "",
    }).catch(alertError);
  });

  if (Array.isArray(context.capability_suggestions) && context.capability_suggestions.length) {
    const ideas = document.createElement("div");
    ideas.className = "creative-ideas";
    context.capability_suggestions.forEach((entry) => {
      const row = document.createElement("div");
      row.className = "creative-idea";
      row.textContent = `${entry.capability}: ${(entry.ideas || []).join(" ")}`;
      ideas.appendChild(row);
    });
    section.appendChild(ideas);
  }

  section.appendChild(form);
  moveListEl.appendChild(section);
}

function renderMoves() {
  moveListEl.innerHTML = "";
  const combatant = state.combatants.find((c) => c.id === selectedId);
  if (!combatant) {
    return;
  }
  const canAct = !!state.current_actor_is_player && selectedId === state.current_actor_id;
  if (selectedId && selectedId !== lastItemActorId) {
    itemTargetId = selectedId;
    lastItemActorId = selectedId;
  }

  const gimmickRow = document.createElement("div");
  gimmickRow.className = "gimmick-row";
  gimmickRow.innerHTML = `
    <label class="gimmick-chip"><input type="checkbox" data-gimmick="mega_evolve" ${gimmickState.mega_evolve ? "checked" : ""} ${canAct ? "" : "disabled"} />Mega</label>
    <label class="gimmick-chip"><input type="checkbox" data-gimmick="dynamax" ${gimmickState.dynamax ? "checked" : ""} ${canAct ? "" : "disabled"} />Dynamax</label>
    <label class="gimmick-chip"><input type="checkbox" data-gimmick="z_move" ${gimmickState.z_move ? "checked" : ""} ${canAct ? "" : "disabled"} />Z-Move</label>
    <label class="gimmick-chip"><input type="checkbox" data-gimmick="teracrystal" ${gimmickState.teracrystal ? "checked" : ""} ${canAct ? "" : "disabled"} />Tera</label>
  `;
  gimmickRow.querySelectorAll("input[data-gimmick]").forEach((input) => {
    input.addEventListener("change", () => {
      const key = input.getAttribute("data-gimmick");
      if (!key) return;
      gimmickState[key] = !!input.checked;
      if (key === "mega_evolve" && input.checked) {
        gimmickState.dynamax = false;
        gimmickState.teracrystal = false;
      } else if (key === "dynamax" && input.checked) {
        gimmickState.mega_evolve = false;
        gimmickState.teracrystal = false;
      } else if (key === "teracrystal" && input.checked) {
        gimmickState.mega_evolve = false;
        gimmickState.dynamax = false;
      }
      renderMoves();
    });
  });

  const teraRow = document.createElement("div");
  teraRow.className = "gimmick-tera-row";
  const teraOptions = ["", "Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"];
  teraRow.innerHTML = `
    <label class="gimmick-tera-label">
      Tera Type
      <select class="gimmick-tera-select" ${canAct ? "" : "disabled"}>
        ${teraOptions
          .map((type) => `<option value="${type}" ${gimmickState.tera_type === type ? "selected" : ""}>${type || "Auto"}</option>`)
          .join("")}
      </select>
    </label>
  `;
  const teraSelect = teraRow.querySelector(".gimmick-tera-select");
  if (teraSelect) {
    teraSelect.addEventListener("change", () => {
      gimmickState.tera_type = String(teraSelect.value || "");
    });
  }
  moveListEl.appendChild(gimmickRow);
  moveListEl.appendChild(teraRow);

  const legalLongJumpCount = Math.max(0, ((state.legal_long_jumps || state.legal_jumps || []).length || 0) - 1);
  const legalHighJumpCount = Math.max(0, ((state.legal_high_jumps || []).length || 0) - 1);
  if (legalLongJumpCount > 0 || legalHighJumpCount > 0) {
    const jumpSection = document.createElement("div");
    jumpSection.className = "item-section";
    const jumpList = document.createElement("div");
    jumpList.className = "item-list";
    if (legalLongJumpCount > 0) {
      const longJumpBtn = document.createElement("button");
      longJumpBtn.className = "item-button";
      longJumpBtn.textContent = armedTileAction === "jump_long" ? "Long Jump: Select Tile" : "Long Jump";
      if (!canAct) {
        longJumpBtn.classList.add("inactive");
        longJumpBtn.setAttribute("aria-disabled", "true");
      }
      longJumpBtn.addEventListener("click", () => {
        if (!canAct) return;
        armedMove = null;
        if (armedTileAction === "jump_long") {
          clearArmedTileAction();
        } else {
          clearArmedTileAction();
          armedTileAction = "jump_long";
        }
        render();
      });
      jumpList.appendChild(longJumpBtn);
    }
    if (legalHighJumpCount > 0) {
      const highJumpBtn = document.createElement("button");
      highJumpBtn.className = "item-button";
      highJumpBtn.textContent = armedTileAction === "jump_high" ? "High Jump: Select Tile" : "High Jump";
      if (!canAct) {
        highJumpBtn.classList.add("inactive");
        highJumpBtn.setAttribute("aria-disabled", "true");
      }
      highJumpBtn.addEventListener("click", () => {
        if (!canAct) return;
        armedMove = null;
        if (armedTileAction === "jump_high") {
          clearArmedTileAction();
        } else {
          clearArmedTileAction();
          armedTileAction = "jump_high";
        }
        render();
      });
      jumpList.appendChild(highJumpBtn);
    }
    jumpSection.appendChild(jumpList);
    moveListEl.appendChild(jumpSection);
  }

  const items = normalizeCombatantItems(combatant.items || []);
  if (items.length) {
    const itemSection = document.createElement("div");
    itemSection.className = "item-section";
    const title = document.createElement("div");
    title.className = "item-title";
    title.textContent = "Items";
    itemSection.appendChild(title);

    const targetRow = document.createElement("div");
    targetRow.className = "item-target-row";
    const targetLabel = document.createElement("label");
    targetLabel.className = "item-target-label";
    targetLabel.textContent = "Target";
    const targetSelect = document.createElement("select");
    targetSelect.className = "item-target-select";
    targetSelect.disabled = !canAct;
    const targetOptions = allCombatantTargetOptions();
    if (!itemTargetId || !targetOptions.some((opt) => opt.id === itemTargetId)) {
      itemTargetId = selectedId || (targetOptions[0] ? targetOptions[0].id : null);
    }
    targetOptions.forEach((opt) => {
      const option = document.createElement("option");
      option.value = opt.id;
      option.textContent = opt.label;
      if (opt.id === itemTargetId) {
        option.selected = true;
      }
      targetSelect.appendChild(option);
    });
    targetSelect.addEventListener("change", () => {
      itemTargetId = targetSelect.value || null;
    });
    targetLabel.appendChild(targetSelect);
    targetRow.appendChild(targetLabel);
    itemSection.appendChild(targetRow);

    const itemList = document.createElement("div");
    itemList.className = "item-list";
    items.forEach((itemEntry, idx) => {
      const name = String(itemEntry?.name || "").trim();
      if (!name) return;
      const btn = document.createElement("button");
      btn.className = "item-button";
      btn.textContent = `Use ${name}`;
      if (!canAct) {
        btn.classList.add("inactive");
        btn.setAttribute("aria-disabled", "true");
      }
      const meta = pokeApiCacheGet(pokeApiItemMetaCache, name);
      if (!pokeApiCacheHas(pokeApiItemMetaCache, name)) {
        ensureItemMeta(name).then(() => scheduleRerender());
      }
      const tooltipText = meta?.effect || "Item description unavailable.";
      btn.addEventListener("click", () => {
        if (!canAct) return;
        commitAction({
          type: "item",
          actor_id: selectedId,
          item_index: idx,
          target_id: itemTargetId || selectedId,
        }).catch(alertError);
      });
      btn.addEventListener("mouseenter", () => {
        clearTooltipHideTimer();
        showDetailTooltip(btn, `Item: ${name}`, tooltipText);
      });
      btn.addEventListener("mouseleave", () => {
        scheduleTooltipHide();
      });
      itemList.appendChild(btn);
    });
    itemSection.appendChild(itemList);
    moveListEl.appendChild(itemSection);
  }

  renderTrainerFeatureActions(moveListEl, combatant, canAct);
  renderBattleManeuverActions(moveListEl, combatant, canAct);
  renderCreativeBattleAction(moveListEl, combatant, canAct);

  combatant.moves.forEach((move) => {
    const btn = document.createElement("button");
    btn.className = "move-button";
    btn.dataset.moveName = String(move.name || "");
    if (armedMove === move.name) {
      btn.classList.add("active");
    }
    const targets = (state.move_targets && state.move_targets[move.name]) || [];
    const actionable = !!targets.length && canAct;
    if (!actionable) {
      btn.classList.add("inactive");
      btn.setAttribute("aria-disabled", "true");
    }

    const moveMeta = pokeApiCacheGet(pokeApiMoveMetaCache, move.name);
    if (!pokeApiCacheHas(pokeApiMoveMetaCache, move.name)) {
      ensureMoveMeta(move.name).then(() => scheduleRerender());
    }
    const typeIconUrl = moveMeta?.type_icon_url || typeIconFromCache(move.type);
    if (!typeIconUrl) {
      ensureTypeIcon(move.type).then(() => scheduleRerender());
    }
    const descriptionText = bestMoveDescription(move, moveMeta);

    const main = document.createElement("span");
    main.className = "move-main";
    if (typeIconUrl) {
      const icon = document.createElement("img");
      icon.className = "move-type-icon";
      icon.src = typeIconUrl;
      icon.alt = `${move.type} type`;
      main.appendChild(icon);
    }
    const name = document.createElement("span");
    name.textContent = move.name;
    main.appendChild(name);
    btn.appendChild(main);
    const meta = document.createElement("div");
    meta.className = "move-meta";
    meta.textContent = `[${move.type} ${move.category}]`;
    btn.appendChild(meta);
    const badges = document.createElement("div");
    badges.className = "move-badges";
    if (move.freq) {
      const badge = document.createElement("span");
      badge.className = "move-badge";
      badge.textContent = `Freq ${move.freq}`;
      badges.appendChild(badge);
    }
    if (move.range) {
      const badge = document.createElement("span");
      badge.className = "move-badge";
      badge.textContent = `Range ${move.range}`;
      badges.appendChild(badge);
    }
    if (Number(move.priority) !== 0) {
      const badge = document.createElement("span");
      badge.className = "move-badge";
      badge.textContent = `Priority ${move.priority > 0 ? `+${move.priority}` : move.priority}`;
      badges.appendChild(badge);
    }
    if (badges.children.length) {
      btn.appendChild(badges);
    }

    btn.addEventListener("click", () => {
      if (!actionable) {
        return;
      }
      armedMove = armedMove === move.name ? null : move.name;
      clearArmedTileAction();
      render();
    });
    btn.addEventListener("mouseenter", () => {
      clearTooltipHideTimer();
      showDetailTooltip(btn, `Move: ${move.name}`, descriptionText);
    });
    btn.addEventListener("mouseleave", () => {
      scheduleTooltipHide();
    });
    moveListEl.appendChild(btn);
  });
}

function renderLog() {
  const merged = _buildBattleFeedLines({ filtered: true, limit: Number.MAX_SAFE_INTEGER, applyClearOffset: true });
  const shouldAutoScroll = logAutoScrollToggle?.checked ?? true;
  const maxScrollTop = Math.max(0, logEl.scrollHeight - logEl.clientHeight);
  const wasNearBottom = maxScrollTop - logEl.scrollTop <= 24;
  logEl.classList.toggle("compact", !!logCompactToggle?.checked);
  logEl.innerHTML = "";
  merged.forEach((line) => {
    if (line.isDivider) {
      const divider = document.createElement("div");
      divider.className = "log-divider";
      divider.textContent = line.text;
      logEl.appendChild(divider);
      return;
    }
    const div = document.createElement("div");
    div.className = `log-line log-${line.category || "other"}`;
    if (line.prefix) {
      const prefix = document.createElement("span");
      prefix.className = "log-prefix";
      prefix.textContent = line.prefix;
      div.appendChild(prefix);
    }
    const tag = document.createElement("span");
    const normalizedCategory = line.category || "other";
    tag.className = `log-tag log-tag-${normalizedCategory}`;
    tag.textContent = LOG_CATEGORY_TAG[normalizedCategory] || LOG_CATEGORY_TAG.other;
    const text = document.createElement("span");
    text.className = "log-text";
    text.innerHTML = decorateLogText(line.text, line.event);
    div.appendChild(tag);
    div.appendChild(text);
    if (line.count > 1) {
      const repeat = document.createElement("span");
      repeat.className = "log-repeat";
      repeat.textContent = `x${line.count}`;
      div.appendChild(repeat);
    }
    logEl.appendChild(div);
  });
  bindLogTooltips();
  if (shouldAutoScroll || wasNearBottom) {
    const stickToBottom = () => {
      logEl.scrollTop = logEl.scrollHeight;
    };
    stickToBottom();
    requestAnimationFrame(stickToBottom);
  }
}

function _buildBattleFeedLines({ filtered = true, limit = 520, applyClearOffset = true, logEntries = null } = {}) {
  const log = Array.isArray(logEntries) ? logEntries : state?.log || [];
  if (logClearOffset > log.length) {
    logClearOffset = 0;
  }
  const start = applyClearOffset ? logClearOffset : 0;
  const normalizedLimit = Number.isFinite(Number(limit)) ? Math.max(1, Number(limit)) : Number.MAX_SAFE_INTEGER;
  const rawEvents = log.slice(start).slice(-normalizedLimit);
  const lines = [];
  let lastLine = null;
  let lastRound = null;
  rawEvents.forEach((event) => {
    const { text, category, prefix } = renderEventLine(event);
    if (filtered && !passesLogFilter(category)) return;
    const round = Number(event?.round);
    if (Number.isFinite(round) && round !== lastRound) {
      if (!filtered || (logFilterPhase?.checked ?? true)) {
        lines.push({ text: `Round ${round}`, category: "phase", event, prefix, isDivider: true });
      }
      lastRound = round;
    }
    const cleaned = cleanLogLine(text, lastLine);
    if (!cleaned) return;
    if (cleaned === lastLine) return;
    lines.push({ text: cleaned, category, event, prefix });
    lastLine = cleaned;
  });
  const merged = [];
  lines.forEach((line) => {
    if (line.isDivider) {
      merged.push({ ...line, count: 1 });
      return;
    }
    const previous = merged[merged.length - 1];
    if (previous && previous.text === line.text && previous.category === line.category) {
      previous.count += 1;
      return;
    }
    merged.push({ ...line, count: 1 });
  });
  return merged;
}

async function exportBattleLog() {
  let exportState = state;
  let exportLog = Array.isArray(state?.log) ? state.log : [];
  try {
    const payload = await api("/api/battle/log/export");
    if (Array.isArray(payload?.log) && payload.log.length) {
      exportState = { ...(state || {}), ...payload };
      exportLog = payload.log;
    }
  } catch (_error) {
    // Fall back to the clipped snapshot log if the export endpoint is unavailable.
  }
  if (!Array.isArray(exportLog) || !exportLog.length) {
    notifyUI("warn", "No battle log to export.", 2200);
    return;
  }
  const lines = _buildBattleFeedLines({
    filtered: false,
    limit: Math.max(5000, exportLog.length),
    applyClearOffset: false,
    logEntries: exportLog,
  });
  const header = [];
  header.push("AutoPTU Battle Log");
  header.push(`Generated: ${new Date().toISOString()}`);
  if (Number.isFinite(Number(exportState?.round))) header.push(`Round: ${Number(exportState.round)}`);
  if (exportState?.winner_label || exportState?.winner_team) {
    header.push(`Winner: ${String(exportState.winner_label || formatTeamLabel(exportState.winner_team))}`);
  }
  if (exportState?.battle_log_path) {
    header.push(`Engine JSONL: ${String(exportState.battle_log_path)}`);
  }
  header.push("");
  const body = lines.map((line) => {
    if (line.isDivider) return `== ${line.text} ==`;
    const tag = LOG_CATEGORY_TAG[line.category || "other"] || LOG_CATEGORY_TAG.other;
    const prefix = line.prefix ? `${line.prefix} ` : "";
    const repeat = line.count > 1 ? ` x${line.count}` : "";
    return `[${tag}] ${prefix}${line.text}${repeat}`;
  });
  const winnerSlug = String(exportState?.winner_label || exportState?.winner_team || "battle").replace(/[^a-z0-9_-]+/gi, "_");
  const roundSlug = Number.isFinite(Number(exportState?.round)) ? `r${Number(exportState.round)}` : "r0";
  _downloadTextFile(`battle_log_${winnerSlug}_${roundSlug}.txt`, header.concat(body).join("\r\n"));
  notifyUI("ok", "Battle log exported.", 2200);
}

function renderPrompts() {
  const prompts = state.pending_prompts || [];
  if (!prompts.length) {
    promptOverlay.classList.add("hidden");
    promptListEl.innerHTML = "";
    return;
  }
  promptOverlay.classList.remove("hidden");
  if (autoTimer) {
    clearInterval(autoTimer);
    autoTimer = null;
    applyBattleLifecycleControls();
    notifyUI("warn", "Auto AI paused: resolve pending prompts.", 2600);
  }
  promptListEl.innerHTML = "";
  const combatantLookup = new Map(((state && state.combatants) || []).map((entry) => [entry.id, entry]));
  prompts.forEach((prompt) => {
    const wrapper = document.createElement("div");
    wrapper.className = "prompt-item";
    const actorEntry = combatantLookup.get(prompt.actor_id);
    const targetEntry = combatantLookup.get(prompt.target_id || prompt.defender_id || prompt.trigger_target);
    const actorName = prompt.actor_name || actorEntry?.name || prompt.actor_id || "unknown";
    const targetName =
      prompt.target_name ||
      prompt.defender_name ||
      prompt.trigger_target_name ||
      targetEntry?.name ||
      prompt.target_id ||
      prompt.defender_id ||
      prompt.trigger_target ||
      "?";
    const featureName = String(prompt.feature || "").trim();
    const label = document.createElement("div");
    label.textContent = featureName
      ? `${featureName}: ${prompt.label} | ${actorName} -> ${targetName}`
      : `${prompt.label} | ${actorName} -> ${targetName}`;
    const details = document.createElement("div");
    const detailParts = [];
    if (prompt.detail) detailParts.push(String(prompt.detail || ""));
    if (prompt.trainer_name) detailParts.push(`Trainer: ${prompt.trainer_name}`);
    if (prompt.attacker_name && prompt.attacker_name !== actorName) detailParts.push(`Attacker: ${prompt.attacker_name}`);
    if (prompt.move) detailParts.push(`Move: ${prompt.move}`);
    if (prompt.maneuver) detailParts.push(`Maneuver: ${prompt.maneuver}`);
    if (prompt.trigger_move) detailParts.push(`Trigger: ${prompt.trigger_move}`);
    if (Array.isArray(prompt.allied_targets) && prompt.allied_targets.length) {
      const alliedNames = prompt.allied_targets
        .map((id) => prompt[`allied_target_name_${id}`] || combatantLookup.get(id)?.name || id)
        .join(", ");
      if (alliedNames) detailParts.push(`Allies: ${alliedNames}`);
    }
    if (prompt.ap_cost != null) detailParts.push(`AP: ${prompt.ap_cost}`);
    if (prompt.phase) detailParts.push(`Phase: ${prompt.phase}`);
    details.textContent = detailParts.join(" | ") || `Move: ${prompt.move || "-"} Trigger: ${prompt.trigger_move || "-"}`;
    const choice = document.createElement("div");
    choice.className = "prompt-choice";
    const id = prompt.id;
    let choiceSelect = null;
    const promptOptions = Array.isArray(prompt.options) ? prompt.options : [];
    if (promptOptions.length) {
      choiceSelect = document.createElement("select");
      choiceSelect.className = "item-target-select";
      const blank = document.createElement("option");
      blank.value = "";
      blank.textContent = "Choose...";
      choiceSelect.appendChild(blank);
      promptOptions.forEach((entry) => {
        const option = document.createElement("option");
        option.value = String(entry.value ?? entry.id ?? entry.label ?? "");
        const meta = entry.meta ? ` | ${entry.meta}` : "";
        option.textContent = `${entry.label ?? entry.name ?? option.value}${meta}`;
        choiceSelect.appendChild(option);
      });
      choiceSelect.addEventListener("change", () => {
        const existing = promptAnswers[id];
        if (existing && typeof existing === "object") {
          promptAnswers[id] = { ...existing, choice: choiceSelect.value || "" };
        }
      });
      wrapper.appendChild(choiceSelect);
    }
    const yes = document.createElement("button");
    yes.textContent = prompt.yes_label || "Yes";
    const no = document.createElement("button");
    no.textContent = prompt.no_label || "No";
    const update = () => {
      const value = promptAnswers[id];
      const accepted = value === true || (value && typeof value === "object" && value.accept === true);
      const declined = value === false || (value && typeof value === "object" && value.accept === false);
      yes.classList.toggle("active", accepted);
      no.classList.toggle("active", declined);
    };
    yes.addEventListener("click", () => {
      if (choiceSelect) {
        promptAnswers[id] = { accept: true, choice: choiceSelect.value || "" };
      } else {
        promptAnswers[id] = true;
      }
      update();
    });
    no.addEventListener("click", () => {
      if (choiceSelect) {
        promptAnswers[id] = { accept: false, choice: choiceSelect.value || "" };
      } else {
        promptAnswers[id] = false;
      }
      update();
    });
    update();
    choice.appendChild(yes);
    choice.appendChild(no);
    wrapper.appendChild(label);
    wrapper.appendChild(details);
    wrapper.appendChild(choice);
    promptListEl.appendChild(wrapper);
  });
}

async function loadCharacterData() {
  if (characterData) {
    renderCharacterStep();
    return;
  }
  if (location.protocol !== "file:") {
    try {
      const payload = await api("/api/character_creation");
      const hasClasses = Array.isArray(payload?.classes) && payload.classes.length > 0;
      characterData = hasClasses ? payload : null;
    } catch {
      characterData = null;
    }
  }
  if (!characterData) {
    const embedded = document.getElementById("character-data");
    if (embedded && embedded.textContent) {
      try {
        const parsed = parseEmbeddedJsonSafe(embedded.textContent);
        characterData = parsed;
      } catch {
        characterData = null;
      }
    }
  }
  if (characterData && location.protocol !== "file:") {
    try {
      const response = await fetch("character_creation.json", { cache: "no-store" });
      if (response.ok) {
        const refreshed = await response.json();
        if (Array.isArray(refreshed?.classes) && refreshed.classes.length) {
          characterData = refreshed;
        }
      }
    } catch {
      // keep API/embedded payload when static refresh is unavailable
    }
  }
  if (!characterData) {
    if (location.protocol !== "file:") {
      try {
        const response = await fetch("character_creation.json");
        if (response.ok) {
          characterData = await response.json();
        }
      } catch {
        characterData = { classes: [], nodes: [], edges: [], features: [], edges_catalog: [], poke_edges_catalog: [] };
      }
    } else {
      characterData = { classes: [], nodes: [], edges: [], features: [], edges_catalog: [], poke_edges_catalog: [] };
    }
  }
  if (characterData) {
    if (!Array.isArray(characterData.poke_edges_catalog)) {
      const embeddedPoke = document.getElementById("character-data-poke");
      if (embeddedPoke && embeddedPoke.textContent) {
        try {
          const parsedPoke = parseEmbeddedJsonSafe(embeddedPoke.textContent);
          if (Array.isArray(parsedPoke?.poke_edges_catalog)) {
            characterData.poke_edges_catalog = parsedPoke.poke_edges_catalog.slice();
          }
        } catch {
          // ignore
        }
      }
      if (!Array.isArray(characterData.poke_edges_catalog)) {
        characterData.poke_edges_catalog = [];
      }
    }
    _cachedFeatureClassIndex = null;
    _cachedClassNameByKey = null;
    _cachedClassTierMap = null;
    _skillDescriptionCache = null;
    const skills = characterData.skills || [];
    const rules = characterData.skill_rules || {};
    const defaultRank = (rules.ranks || [])[1] || "Untrained";
    skills.forEach((skill) => {
      if (!(skill in characterState.skills)) {
        characterState.skills[skill] = defaultRank;
      }
    });
    if (characterState.skill_budget === null && typeof rules.budget === "number") {
      characterState.skill_budget = rules.budget;
    }
    const scenario = _scenarioName();
    if (scenario) {
      applyCharacterScenario(scenario);
    } else {
      loadCharacterFromStorage();
    }
  }
  await loadMasterData();
  renderCharacterStep();
}

function parseEmbeddedJsonSafe(text) {
  const source = String(text || "");
  try {
    return JSON.parse(source);
  } catch {
    // Some generated embeds may contain raw control chars inside quoted strings.
    // Escape those chars while preserving valid JSON structure.
    let out = "";
    let inString = false;
    let escaped = false;
    for (let i = 0; i < source.length; i += 1) {
      const ch = source[i];
      const code = ch.charCodeAt(0);
      if (!inString) {
        out += ch;
        if (ch === '"') inString = true;
        continue;
      }
      if (escaped) {
        out += ch;
        escaped = false;
        continue;
      }
      if (ch === "\\") {
        const next = source[i + 1] || "";
        const isSimpleEscape =
          next === '"' ||
          next === "\\" ||
          next === "/" ||
          next === "b" ||
          next === "f" ||
          next === "n" ||
          next === "r" ||
          next === "t";
        const isUnicodeEscape =
          next === "u" && /^[0-9a-fA-F]{4}$/.test(source.slice(i + 2, i + 6));
        if (isSimpleEscape || isUnicodeEscape) {
          out += ch;
          escaped = true;
        } else {
          // Preserve an invalid backslash as a literal character.
          out += "\\\\";
        }
        continue;
      }
      if (ch === '"') {
        out += ch;
        inString = false;
        continue;
      }
      if (code <= 0x1f) {
        if (ch === "\n") out += "\\n";
        else if (ch === "\r") out += "\\r";
        else if (ch === "\t") out += "\\t";
        else out += `\\u${code.toString(16).padStart(4, "0")}`;
        continue;
      }
      out += ch;
    }
    return JSON.parse(out);
  }
}

function _hasDisplayValue(value) {
  if (value === null || value === undefined) return false;
  return String(value).trim() !== "";
}

function _formatCostLabel(value, prefix = "Cost: ") {
  return _hasDisplayValue(value) ? `${prefix}${value}` : "";
}

function _scenarioName() {
  try {
    const raw = new URLSearchParams(location.search).get("scenario");
    const value = String(raw || "").trim().toLowerCase();
    return value || "";
  } catch {
    return "";
  }
}

function _resetScenarioBuildState() {
  characterState.class_ids = [];
  characterState.class_id = "";
  characterState.features = new Set();
  characterState.edges = new Set();
  characterState.feature_order = [];
  characterState.edge_order = [];
  characterState.training_type = "";
  characterState.override_prereqs = false;
  characterState.step_by_step = false;
  characterState.allow_warnings = false;
  const rules = characterData?.skill_rules || { ranks: [] };
  const skills = characterData?.skills || [];
  const defaultRank = (rules.ranks || [])[1] || "Untrained";
  const nextSkills = {};
  skills.forEach((skill) => {
    nextSkills[skill] = defaultRank;
  });
  characterState.skills = nextSkills;
}

function applyCharacterScenario(scenario) {
  const mode = String(scenario || "").trim().toLowerCase();
  _resetScenarioBuildState();
  if (mode === "empty") {
    characterState.profile.level = 1;
    characterState.profile.name = "Scenario: Empty";
    characterStep = "summary";
    return;
  }
  const classes = (characterData?.classes || []).slice();
  const pickClass = classes.find((entry) => inContentScope(entry)) || classes[0];
  if (mode === "partial") {
    characterState.profile.level = 8;
    characterState.profile.name = "Scenario: Partial";
    if (pickClass) {
      characterState.class_ids = [pickClass.id];
      characterState.class_id = pickClass.id;
      const className = pickClass.name;
      const starter = (characterData?.features || []).find(
        (entry) =>
          _normalizeSearchText(entry.prerequisites || "").includes(_normalizeSearchText(className)) &&
          isFeatureAllowed(entry, true)
      );
      if (starter) characterState.features.add(starter.name);
    }
    const firstEdge = (characterData?.edges_catalog || []).find((entry) => isEdgeAllowed(entry, true));
    if (firstEdge) characterState.edges.add(firstEdge.name);
    characterStep = "summary";
    return;
  }
  if (mode === "legal") {
    characterState.profile.level = 20;
    characterState.profile.name = "Scenario: Legal";
    const legalClasses = classes.filter((entry) => {
      const node = (characterData?.nodes || []).find((n) => n.id === entry.id);
      return prereqStatus(node?.prerequisites || "", "class").status === "available";
    });
    const selected = legalClasses.slice(0, 2);
    characterState.class_ids = selected.map((entry) => entry.id);
    characterState.class_id = characterState.class_ids[0] || "";
    (characterData?.features || [])
      .filter((entry) => isFeatureAllowed(entry, false))
      .slice(0, 6)
      .forEach((entry) => characterState.features.add(entry.name));
    (characterData?.edges_catalog || [])
      .filter((entry) => isEdgeAllowed(entry, false))
      .slice(0, 6)
      .forEach((entry) => characterState.edges.add(entry.name));
    characterStep = "summary";
    return;
  }
  if (mode === "invalid") {
    characterState.profile.level = 3;
    characterState.profile.name = "Scenario: Invalid";
    const impossibleFeature =
      (characterData?.features || []).find((entry) => /expert|master|gm permission/i.test(String(entry.prerequisites || ""))) ||
      (characterData?.features || [])[0];
    const impossibleEdge =
      (characterData?.edges_catalog || []).find((entry) => /expert|master|gm permission/i.test(String(entry.prerequisites || ""))) ||
      (characterData?.edges_catalog || [])[0];
    if (impossibleFeature?.name) characterState.features.add(impossibleFeature.name);
    if (impossibleEdge?.name) characterState.edges.add(impossibleEdge.name);
    characterStep = "summary";
  }
}

async function loadMasterData() {
  if (masterData && learnsetData && moveRecordMap) return;
  if (!masterData && characterData && (characterData.pokemon || characterData.items)) {
    masterData = {
      trainer: {
        classes: characterData.classes || [],
        features: characterData.features || [],
        edges: characterData.edges_catalog || [],
        poke_edges: characterData.poke_edges_catalog || [],
        skills: characterData.skills || [],
        skill_rules: characterData.skill_rules || {},
        feature_slots_by_rank: characterData.feature_slots_by_rank || {},
        nodes: characterData.nodes || [],
        edges_graph: characterData.edges || [],
      },
      pokemon: {
        species: characterData?.pokemon?.species || [],
        moves: [],
        abilities: [],
        pokedex_abilities: {},
      },
      items: characterData.items || { food_items: [], held_items: [], weather: [], inventory: [], weapons: [] },
    };
  }
  if (!masterData && window.__AUTO_PTU_MASTER_DATA) {
    masterData = window.__AUTO_PTU_MASTER_DATA;
    _rebuildMoveRecordMap();
  }
  if (!learnsetData && window.__AUTO_PTU_LEARNSET_DATA) {
    learnsetData = window.__AUTO_PTU_LEARNSET_DATA;
  }
  const embeddedMaster = document.getElementById("master-data");
  if (embeddedMaster && embeddedMaster.textContent) {
    try {
      masterData = JSON.parse(embeddedMaster.textContent);
      _rebuildMoveRecordMap();
    } catch {
      masterData = null;
      moveRecordMap = null;
    }
  }
  const embeddedLearnset = document.getElementById("learnset-data");
  if (embeddedLearnset && embeddedLearnset.textContent) {
    try {
      learnsetData = JSON.parse(embeddedLearnset.textContent);
    } catch {
      learnsetData = null;
    }
  }
  if (!masterData) {
    try {
      const response = await fetch("master_dataset.json");
      if (response.ok) {
        masterData = await response.json();
        _rebuildMoveRecordMap();
      }
    } catch {
      // Keep embedded/cached data if present.
    }
  }
  if (!masterData && location.protocol === "file:") {
    try {
      await new Promise((resolve, reject) => {
        const existing = document.querySelector('script[data-fallback-master="true"]');
        if (existing) {
          resolve();
          return;
        }
        const script = document.createElement("script");
        script.src = "master_dataset.embed.js";
        script.dataset.fallbackMaster = "true";
        script.onload = () => resolve();
        script.onerror = () => reject(new Error("Embedded master dataset failed to load."));
        document.head.appendChild(script);
      });
    } catch {
      // ignore fallback failures
    }
    if (window.__AUTO_PTU_MASTER_DATA) {
      masterData = window.__AUTO_PTU_MASTER_DATA;
      _rebuildMoveRecordMap();
    }
  }
  if (!learnsetData) {
    try {
      const learnsetResponse = await fetch("pokedex_learnset.json");
      if (learnsetResponse.ok) {
        learnsetData = await learnsetResponse.json();
      }
    } catch {
      // Keep embedded/cached data if present.
    }
  }
  if (!learnsetData && location.protocol === "file:" && window.__AUTO_PTU_LEARNSET_DATA) {
    learnsetData = window.__AUTO_PTU_LEARNSET_DATA;
  }
  if (!masterData && !characterData?.pokemon?.moves && !learnsetData) moveRecordMap = null;
  else _rebuildMoveRecordMap();
}

function renderCharacterStep() {
  if (!charContentEl) return;
  if (!characterData) {
    charContentEl.textContent = "Loading character data...";
    return;
  }
  _destroySortables();
  if (characterState.guided_mode) {
    const guided = document.createElement("div");
    guided.className = "char-guided-box";
    const warnings = _validationWarnings();
    const next = warnings[0] || "Keep building; all current steps are valid.";
    guided.textContent = `Guided Mode: ${next}`;
    charContentEl.appendChild(guided);
  }
  if (characterStep === "profile") {
    renderCharacterProfile();
  } else if (characterStep === "builder") {
    renderCharacterBuilder();
  } else if (characterStep === "skills") {
    renderCharacterSkills();
  } else if (characterStep === "advancement") {
    renderCharacterAdvancement();
  } else if (characterStep === "class") {
    renderCharacterClass();
  } else if (characterStep === "features") {
    renderCharacterFeatures();
  } else if (characterStep === "edges") {
    renderCharacterEdges();
  } else if (characterStep === "poke-edges") {
    renderCharacterPokemonTeam();
  } else if (characterStep === "extras") {
    renderCharacterExtras();
  } else if (characterStep === "inventory") {
    renderCharacterInventory();
  } else if (characterStep === "pokemon-team") {
    renderCharacterPokemonTeam();
  } else {
    renderCharacterSummary();
  }
  renderStepGuide();
  updateStepButtons();
  renderMiniSummary();
  bindCharacterTooltips();
}

function renderCharacterProfile() {
  charContentEl.innerHTML = "";
  charContentEl.setAttribute("data-step-target", "profile");
  appendNavRow();
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Trainer Profile";
  charContentEl.appendChild(title);
  appendStepModeToggle();

  ensurePlaytestScopeForClass(characterState.edge_class_filter);
  _renderPlannerPanel(charContentEl);
  _renderCloseUnlocks(charContentEl);

  const contentTitle = document.createElement("div");
  contentTitle.className = "char-section-title";
  contentTitle.textContent = "Content Scope";
  charContentEl.appendChild(contentTitle);
  const contentBox = document.createElement("div");
  contentBox.className = "char-summary-box";
  const contentButtons = document.createElement("div");
  contentButtons.className = "char-action-row";
  const officialBtn = document.createElement("button");
  officialBtn.type = "button";
  officialBtn.textContent = "Official Only";
  officialBtn.disabled = (characterState.content_scope || "official") === "official";
  officialBtn.addEventListener("click", () => {
    characterState.content_scope = "official";
    saveCharacterToStorage();
    renderCharacterProfile();
  });
  const allBtn = document.createElement("button");
  allBtn.type = "button";
  allBtn.textContent = "Official + Playtest";
  allBtn.disabled = (characterState.content_scope || "official") === "all";
  allBtn.addEventListener("click", () => {
    characterState.content_scope = "all";
    saveCharacterToStorage();
    renderCharacterProfile();
  });
  contentButtons.appendChild(officialBtn);
  contentButtons.appendChild(allBtn);
  const scopeText =
    (characterState.content_scope || "official") === "all"
      ? "Using official and playtest content."
      : "Using official content only.";
  contentBox.textContent = scopeText;
  contentBox.appendChild(contentButtons);
  charContentEl.appendChild(contentBox);

  const grid = document.createElement("div");
  grid.className = "char-field-grid";
  const profileFieldHelp = {
    name: "Character name.",
    played_by: "Player name or handle.",
    age: "Character age.",
    sex: "Gender or presentation.",
    height: "Height or size descriptor.",
    weight: "Weight or build descriptor.",
    region: "Home region.",
    concept: "Short concept or archetype.",
    level: "Trainer level.",
  };
  const fields = [
    { key: "name", label: "Name" },
    { key: "played_by", label: "Played By" },
    { key: "age", label: "Age" },
    { key: "sex", label: "Sex" },
    { key: "height", label: "Height" },
    { key: "weight", label: "Weight" },
    { key: "region", label: "Region" },
    { key: "concept", label: "Concept" },
    { key: "level", label: "Level" },
  ];
  fields.forEach((field) => {
    const wrap = document.createElement("label");
    wrap.className = "char-field";
    const label = document.createElement("span");
    label.className = "char-field-label";
    label.textContent = field.label;
    _setTooltipAttrs(label, field.label, profileFieldHelp[field.key] || "");
    wrap.appendChild(label);
    const input = document.createElement("input");
    if (field.key === "level") {
      input.type = "number";
      input.min = "1";
    }
    input.value = characterState.profile[field.key] || "";
    input.addEventListener("input", () => {
      if (field.key === "level") {
        const level = Number(input.value || 1);
        characterState.profile[field.key] = level;
        if (characterState.pokemon_team_auto_level) {
          const pokemonLevel = trainerToPokemonLevel(level);
          _ensurePokemonBuilds().forEach((build) => {
            build.level = Number.isFinite(pokemonLevel) ? pokemonLevel : 1;
            _sanitizePokemonBuildForLevel(build);
          });
        }
      } else {
        characterState.profile[field.key] = input.value;
      }
      saveCharacterToStorage();
    });
    wrap.appendChild(input);
    grid.appendChild(wrap);
  });
  charContentEl.appendChild(grid);
  const background = document.createElement("label");
  background.className = "char-field";
  const backgroundLabel = document.createElement("span");
  backgroundLabel.className = "char-field-label";
  backgroundLabel.textContent = "Background";
  _setTooltipAttrs(backgroundLabel, "Background", "Short character background or notes.");
  background.appendChild(backgroundLabel);
  const textarea = document.createElement("textarea");
  textarea.value = characterState.profile.background || "";
  textarea.addEventListener("input", () => {
    characterState.profile.background = textarea.value;
    saveCharacterToStorage();
  });
  background.appendChild(textarea);
  charContentEl.appendChild(background);

  const statsTitle = document.createElement("div");
  statsTitle.className = "char-section-title";
  statsTitle.textContent = "Trainer Combat Stats";
  _setTooltipAttrs(
    statsTitle,
    "Trainer Combat Stats",
    "Base combat statistics for your trainer. These drive derived stats and capability calculations."
  );
  charContentEl.appendChild(statsTitle);

  const statsGrid = document.createElement("div");
  statsGrid.className = "char-field-grid";
  const statsFields = [
    { key: "hp", label: "HP" },
    { key: "atk", label: "Attack" },
    { key: "def", label: "Defense" },
    { key: "spatk", label: "Special Attack" },
    { key: "spdef", label: "Special Defense" },
    { key: "spd", label: "Speed" },
  ];
  const statsHelp = {
    hp: "Base HP before bonuses.",
    atk: "Physical attack bonus.",
    def: "Physical defense bonus.",
    spatk: "Special attack bonus.",
    spdef: "Special defense bonus.",
    spd: "Speed bonus.",
  };
  statsFields.forEach((field) => {
    const wrap = document.createElement("label");
    wrap.className = "char-field";
    const label = document.createElement("span");
    label.className = "char-field-label";
    label.textContent = field.label;
    _setTooltipAttrs(label, field.label, statsHelp[field.key] || "");
    wrap.appendChild(label);
    const input = document.createElement("input");
    input.type = "number";
    input.min = "0";
    input.value = String(characterState.stats[field.key] ?? 0);
    input.addEventListener("input", () => {
      characterState.stats[field.key] = Number(input.value || 0);
      saveCharacterToStorage();
      renderCharacterProfile();
    });
    wrap.appendChild(input);
    statsGrid.appendChild(wrap);
  });
  charContentEl.appendChild(statsGrid);

  const level = Number(characterState.profile.level || 1);
  const choices = characterState.advancement_choices || {};
  const budget = computeStatBudgets(level, choices);
  const spent =
    (characterState.stats.hp - 10) +
    (characterState.stats.atk - 5) +
    (characterState.stats.def - 5) +
    (characterState.stats.spatk - 5) +
    (characterState.stats.spdef - 5) +
    (characterState.stats.spd - 5);
  const spentNonAtk =
    (characterState.stats.hp - 10) +
    (characterState.stats.def - 5) +
    (characterState.stats.spdef - 5) +
    (characterState.stats.spd - 5);
  const statMeta = document.createElement("div");
  statMeta.className = "char-feature-meta";
  const totalBudget = budget.general + budget.restricted;
  statMeta.textContent = `Points: ${spent}/${totalBudget} (General ${budget.general}, Atk/SpAtk ${budget.restricted})`;
  _setTooltipAttrs(
    statMeta,
    "Stat Points",
    "Total points spent vs. budget. Restricted points are only for Attack and Special Attack."
  );
  charContentEl.appendChild(statMeta);

  const derivedTitle = document.createElement("div");
  derivedTitle.className = "char-section-title";
  derivedTitle.textContent = "Derived Stats";
  _setTooltipAttrs(
    derivedTitle,
    "Derived Stats",
    "Calculated values based on stats, skills, and rules."
  );
  charContentEl.appendChild(derivedTitle);

  const rules = characterData?.skill_rules || { ranks: [] };
  const derived = computeDerivedStats(characterState.stats, characterState.skills, rules, level);
  const derivedBox = document.createElement("div");
  derivedBox.className = "char-summary-box";
  derivedBox.textContent = `AP ${derived.ap}\nMax HP ${derived.maxHp}\nPower ${derived.power}\nHigh Jump ${derived.highJump}\nLong Jump ${derived.longJump}\nOverland ${derived.overland}\nSwim ${derived.swim}\nThrowing Range ${derived.throwingRange}`;
  const capParts = [
    `Power ${derived.power}`,
    `High Jump ${derived.highJump}`,
    `Long Jump ${derived.longJump}`,
    `Overland ${derived.overland}`,
    `Swim ${derived.swim}`,
    `Throw ${derived.throwingRange}`,
  ];
  const capabilityHelp = {
    power: "Power represents raw lifting and pushing strength.",
    highJump: "High Jump is vertical leap distance.",
    longJump: "Long Jump is horizontal leap distance.",
    overland: "Overland is ground movement speed.",
    swim: "Swim is water movement speed.",
    throw: "Throw is effective thrown range.",
  };
  _setTooltipAttrs(
    derivedBox,
    "Capabilities",
    [
      capabilityHelp.power,
      capabilityHelp.highJump,
      capabilityHelp.longJump,
      capabilityHelp.overland,
      capabilityHelp.swim,
      capabilityHelp.throw,
    ].join("\n")
  );
  charContentEl.appendChild(derivedBox);
  const capRow = document.createElement("div");
  capRow.className = "char-action-row";
  [
    { key: "power", label: "Related Power" },
    { key: "high_jump", label: "Related High Jump" },
    { key: "long_jump", label: "Related Long Jump" },
    { key: "overland", label: "Related Overland" },
    { key: "swim", label: "Related Swim" },
    { key: "throwing_range", label: "Related Throwing" },
  ].forEach((cap) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = cap.label;
    const capKey = cap.key === "throwing_range" ? "throw" : cap.key;
    const capLabel = cap.label.replace("Related ", "");
    _setTooltipAttrs(btn, capLabel, capabilityHelp[capKey] || "");
    btn.addEventListener("click", () => {
      focusCapabilityConnections(cap.key, "features");
    });
    capRow.appendChild(btn);
  });
  charContentEl.appendChild(capRow);
}

function getSkillRankIndex(rank, ranks) {
  const idx = ranks.indexOf(rank);
  return idx === -1 ? 0 : idx;
}

function skillRankValue(rank, rules) {
  if (typeof rank === "number" && Number.isFinite(rank)) return rank;
  const order = (rules.ranks || []).map((r) => String(r).toLowerCase());
  const label = String(rank || "").trim().toLowerCase();
  const idx = order.indexOf(label);
  if (idx === -1) return 0;
  const mapping = [1, 2, 3, 4, 5, 6];
  return mapping[Math.min(idx, mapping.length - 1)] || 0;
}

function computeStatBudgets(level, choices) {
  const numericLevel = Number(level || 1);
  const baseAllocation = 10;
  const perLevel = Math.max(0, numericLevel - 1);
  const bonusLevel5 = numericLevel >= 5 && choices?.[5] === "stats" ? 2 : 0;
  const restrictedSegments = [
    numericLevel >= 5 && choices?.[5] === "stats" ? 3 : 0, // levels 6,8,10
    numericLevel >= 10 && choices?.[10] === "stats" ? 5 : 0, // levels 12-20 even
    numericLevel >= 20 && choices?.[20] === "stats" ? 5 : 0, // levels 22-30 even
    numericLevel >= 30 && choices?.[30] === "stats" ? 5 : 0, // levels 32-40 even
    numericLevel >= 40 && choices?.[40] === "stats" ? 5 : 0, // levels 42-50 even
  ];
  const restricted = restrictedSegments.reduce((a, b) => a + b, 0);
  const general = baseAllocation + perLevel + bonusLevel5;
  return { general, restricted };
}

function computeDerivedStats(stats, skills, rules, level) {
  const levelNum = Number(level || 1);
  const athl = skillRankValue(skills.Athletics, rules);
  const acro = skillRankValue(skills.Acrobatics, rules);
  const combat = skillRankValue(skills.Combat, rules);
  const hp = Number(stats.hp || 0);
  const powerBase = 4 + (athl >= 3 ? 1 : 0) + (combat >= 4 ? 1 : 0);
  const highJump = (acro >= 4 ? 1 : 0) + (acro >= 6 ? 1 : 0);
  const longJump = Math.floor(acro / 2);
  const overland = 3 + Math.floor((athl + acro) / 2);
  const swim = Math.floor(overland / 2);
  const throwingRange = 4 + athl;
  const ap = 5 + Math.floor(levelNum / 5);
  const maxHp = levelNum * 2 + hp * 3 + 10;
  return {
    ap,
    maxHp,
    power: powerBase,
    highJump,
    longJump,
    overland,
    swim,
    throwingRange,
  };
}

function getMaxRankForLevel(level, rules) {
  const ranks = rules.ranks || [];
  let maxRank = ranks[ranks.length - 1] || "Master";
  const caps = rules.rank_caps_by_level || [];
  caps.forEach((cap) => {
    if (Number(level) >= Number(cap.level)) {
      maxRank = cap.max || maxRank;
    }
  });
  return maxRank;
}

function getAutoSkillBudget(level, rules) {
  const base = Number(rules.edge_budget_level1 ?? 4);
  const perEven = Number(rules.edge_per_even_level ?? 1);
  const evenEdges = Math.floor(Number(level || 1) / 2) * perEven;
  const bonusLevels = Array.isArray(rules.bonus_skill_edge_levels) ? rules.bonus_skill_edge_levels : [];
  const bonusEdges = bonusLevels.filter((lvl) => Number(level || 1) >= Number(lvl)).length;
  return base + evenEdges + bonusEdges;
}

function normalizeBackgroundState(rules, skills) {
  const bgRules = rules.background || {};
  const lockPathetic = bgRules.lock_pathetic_level1 !== false;
  const neededPathetic = Number(bgRules.pathetic ?? 0);
  if (!characterState.skill_background || typeof characterState.skill_background !== "object") {
    characterState.skill_background = { adept: "", novice: "", pathetic: [] };
  }
  if (!Array.isArray(characterState.skill_background.pathetic)) {
    characterState.skill_background.pathetic = [];
  }
  while (characterState.skill_background.pathetic.length < neededPathetic) {
    characterState.skill_background.pathetic.push("");
  }
  if (characterState.skill_background.pathetic.length > neededPathetic) {
    characterState.skill_background.pathetic = characterState.skill_background.pathetic.slice(0, neededPathetic);
  }
  if (!skills.includes(characterState.skill_background.adept)) characterState.skill_background.adept = "";
  if (!skills.includes(characterState.skill_background.novice)) characterState.skill_background.novice = "";
  characterState.skill_background.pathetic = characterState.skill_background.pathetic.map((skill) =>
    skills.includes(skill) ? skill : ""
  );
}

function applySkillBackgroundRules(rules, skills, level) {
  if (characterState.override_prereqs) return;
  if (Number(level) !== 1) return;
  const bgRules = rules.background || {};
  if (!bgRules || !skills.length) return;
  const bg = characterState.skill_background || {};
  if (bg.adept) characterState.skills[bg.adept] = "Adept";
  if (bg.novice) characterState.skills[bg.novice] = "Novice";
  if (Array.isArray(bg.pathetic)) {
    bg.pathetic.forEach((skill) => {
      if (skill) characterState.skills[skill] = "Pathetic";
    });
  }
}

function renderCharacterSkills() {
  charContentEl.innerHTML = "";
  charContentEl.setAttribute("data-step-target", "skills");
  appendNavRow();
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Skill Allocation";
  charContentEl.appendChild(title);
  const subtitle = document.createElement("div");
  subtitle.className = "char-feature-meta";
  subtitle.textContent = "Allocate skill ranks, background picks, and training choices.";
  charContentEl.appendChild(subtitle);
  appendStepModeToggle();

  ensurePlaytestScopeForClass(characterState.edge_class_filter);
  _renderPlannerPanel(charContentEl);
  _renderCloseUnlocks(charContentEl);

  const rules = characterData.skill_rules || { ranks: ["Untrained"] };
  const ranks = rules.ranks || ["Untrained"];
  const rankCosts = rules.rank_costs || {};
  const bgRules = rules.background || {};
  const lockPathetic = bgRules.lock_pathetic_level1 !== false;
  const skills = (characterData.skills || []).slice().sort((a, b) => String(a).localeCompare(String(b)));
  const level = Number(characterState.profile.level || 1);
  const maxRank = getMaxRankForLevel(level, rules);
  const maxRankIndex = getSkillRankIndex(maxRank, ranks);
  const autoBudget = getAutoSkillBudget(level, rules);
  const nonSkillEdges = Math.max(0, Number(characterState.skill_edge_non_skill_count || 0));
  const effectiveAutoBudget = Math.max(0, autoBudget - nonSkillEdges);
  normalizeBackgroundState(rules, skills);
  applySkillBackgroundRules(rules, skills, level);
  if (characterState.training_type) {
    setTrainingType(characterState.training_type);
  }
  if (characterState.skill_budget_auto) {
    characterState.skill_budget = effectiveAutoBudget;
  }
  const budget = characterState.skill_budget;

  const buildSkillPill = (labelText, skillName) => {
    if (!skillName) return null;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "char-pill char-pill-link";
    btn.textContent = `${labelText}: ${skillName}`;
    const desc = _getSkillDescription(skillName);
    _setTooltipAttrs(btn, `Skill: ${skillName}`, desc || "");
    btn.addEventListener("click", () => {
      focusSkillConnections(skillName, "features");
    });
    return btn;
  };
  const metaHelp = {
    "Max Rank": "Highest skill rank allowed at your current level.",
    "Background (L1)": "Your Level 1 background picks (Adept/Novice/Pathetic).",
    Preset: "Optional quick presets for bulk skill ranks.",
    Budget: "Optional limit for total skill points. Leave empty to ignore.",
  };
  const makeMetaRow = (labelText, valueEl) => {
    const row = document.createElement("div");
    row.className = "char-meta-row";
    const label = document.createElement("div");
    label.className = "char-meta-label";
    label.textContent = labelText;
    if (metaHelp[labelText]) {
      _setTooltipAttrs(label, labelText, metaHelp[labelText]);
    }
    const value = document.createElement("div");
    value.className = "char-meta-value";
    if (typeof valueEl === "string") {
      value.textContent = valueEl;
    } else if (valueEl) {
      value.appendChild(valueEl);
    }
    row.appendChild(label);
    row.appendChild(value);
    return row;
  };

  const ruleBox = document.createElement("div");
  ruleBox.className = "char-summary-box char-meta-grid";
  const ruleTitleRow = document.createElement("div");
  ruleTitleRow.className = "char-title-row";
  const ruleTitle = document.createElement("div");
  ruleTitle.className = "char-section-title";
  ruleTitle.textContent = "Skill Rules";
  ruleTitleRow.appendChild(ruleTitle);
  ruleBox.appendChild(ruleTitleRow);
  ruleBox.appendChild(makeMetaRow("Max Rank", `Level ${level}: ${maxRank}`));

  if (bgRules && (bgRules.adept || bgRules.novice || bgRules.pathetic)) {
    const bg = characterState.skill_background || { adept: "", novice: "", pathetic: [] };
    const list = document.createElement("div");
    list.className = "char-pill-list";
    const adeptPill = buildSkillPill("Adept", bg.adept);
    const novicePill = buildSkillPill("Novice", bg.novice);
    if (adeptPill) list.appendChild(adeptPill);
    if (novicePill) list.appendChild(novicePill);
    (bg.pathetic || []).filter(Boolean).forEach((name) => {
      const pill = buildSkillPill("Pathetic", name);
      if (pill) list.appendChild(pill);
    });
    if (!list.children.length) {
      const empty = document.createElement("span");
      empty.className = "char-feature-meta";
      empty.textContent = "-";
      list.appendChild(empty);
    }
    ruleBox.appendChild(makeMetaRow("Background (L1)", list));
  } else {
    ruleBox.appendChild(makeMetaRow("Background (L1)", "None"));
  }
  if (bgRules && (bgRules.adept || bgRules.novice || bgRules.pathetic)) {
    const bgTitle = document.createElement("div");
    bgTitle.className = "char-section-title";
    bgTitle.textContent = "Background Picks (Level 1)";
    charContentEl.appendChild(bgTitle);
    const bgHint = document.createElement("div");
    bgHint.className = "char-feature-meta";
    bgHint.textContent = "Set your Level 1 background ranks. You can adjust these later for record-keeping.";
    charContentEl.appendChild(bgHint);

    const bgWrap = document.createElement("div");
    bgWrap.className = "char-field-grid";

    const makeSelect = (labelText, value, onChange) => {
      const wrap = document.createElement("label");
      wrap.className = "char-field char-field-inline";
      const labelSpan = document.createElement("span");
      labelSpan.className = "char-field-label";
      labelSpan.textContent = labelText;
      wrap.appendChild(labelSpan);
      const select = document.createElement("select");
      select.className = "item-target-select";
      const blank = document.createElement("option");
      blank.value = "";
      blank.textContent = "Select...";
      select.appendChild(blank);
      skills.forEach((skill) => {
        const option = document.createElement("option");
        option.value = skill;
        option.textContent = skill;
        if (skill === value) option.selected = true;
        select.appendChild(option);
      });
      select.addEventListener("change", () => {
        onChange(select.value);
        applySkillBackgroundRules(rules, skills, level);
        saveCharacterToStorage();
        renderCharacterSkills();
      });
      wrap.appendChild(select);
      return wrap;
    };

    if (Number(bgRules.adept || 0) > 0) {
      bgWrap.appendChild(
        makeSelect("Adept Skill", characterState.skill_background.adept, (value) => {
          characterState.skill_background.adept = value;
        })
      );
    }
    if (Number(bgRules.novice || 0) > 0) {
      bgWrap.appendChild(
        makeSelect("Novice Skill", characterState.skill_background.novice, (value) => {
          characterState.skill_background.novice = value;
        })
      );
    }
    const patheticCount = Number(bgRules.pathetic || 0);
    for (let i = 0; i < patheticCount; i += 1) {
      bgWrap.appendChild(
        makeSelect(`Pathetic Skill ${i + 1}`, characterState.skill_background.pathetic[i], (value) => {
          characterState.skill_background.pathetic[i] = value;
        })
      );
    }
    charContentEl.appendChild(bgWrap);
  }

  const trainingTitle = document.createElement("div");
  trainingTitle.className = "char-section-title";
  trainingTitle.textContent = "Training Type";
  charContentEl.appendChild(trainingTitle);
  const trainingHint = document.createElement("div");
  trainingHint.className = "char-feature-meta";
  trainingHint.textContent = "Select a training feature granted by your training choice.";
  charContentEl.appendChild(trainingHint);
  const trainingWrap = document.createElement("div");
  trainingWrap.className = "char-field-grid";
  const trainingField = document.createElement("label");
  trainingField.className = "char-field";
  const trainingLabel = document.createElement("span");
  trainingLabel.className = "char-field-label";
  trainingLabel.textContent = "Training Feature";
  _setTooltipAttrs(
    trainingLabel,
    "Training Feature",
    "Choose one: Agility Training, Brutal Training, Focused Training, or Inspired Training."
  );
  trainingField.appendChild(trainingLabel);
  const trainingSelect = document.createElement("select");
  trainingSelect.className = "item-target-select";
  const trainingBlank = document.createElement("option");
  trainingBlank.value = "";
  trainingBlank.textContent = "Select training...";
  trainingSelect.appendChild(trainingBlank);
  const trainingOptions = [
    "Agility Training",
    "Brutal Training",
    "Focused Training",
    "Inspired Training",
  ];
  trainingOptions.forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    if (characterState.training_type === name) option.selected = true;
    trainingSelect.appendChild(option);
  });
  trainingSelect.addEventListener("change", () => {
    setTrainingType(trainingSelect.value);
    saveCharacterToStorage();
    renderCharacterSkills();
  });
  trainingField.appendChild(trainingSelect);
  trainingWrap.appendChild(trainingField);
  const trainingDesc = document.createElement("div");
  trainingDesc.className = "char-summary-box";
  const selectedTraining = characterState.training_type;
  if (selectedTraining) {
    const entry =
      (characterData?.features || []).find((feat) => feat.name === selectedTraining) ||
      (characterData?.nodes || []).find((node) => node?.type === "feature" && node?.name === selectedTraining);
    const title = document.createElement("div");
    title.className = "char-section-title";
    title.textContent = selectedTraining;
    const body = document.createElement("div");
    body.className = "char-feature-meta";
    body.textContent = entry?.effects || "No description found.";
    trainingDesc.appendChild(title);
    trainingDesc.appendChild(body);
    _attachKeywordTooltip(body, body.textContent);
  } else {
    trainingDesc.className += " char-no-word-links";
    trainingDesc.textContent = "Select a training feature to see its description.";
  }
  charContentEl.appendChild(trainingWrap);
  charContentEl.appendChild(trainingDesc);

  const controlsBox = document.createElement("div");
  controlsBox.className = "char-summary-box char-meta-grid";
  const controlsTitle = document.createElement("div");
  controlsTitle.className = "char-section-title";
  controlsTitle.textContent = "Skill Controls";
  controlsBox.appendChild(controlsTitle);

  const presetSelect = document.createElement("select");
  presetSelect.className = "item-target-select";
  const presets = [
    { id: "none", label: "None" },
    { id: "all_untrained", label: "All Untrained" },
    { id: "novice_3", label: "Novice in 3" },
    { id: "novice_6", label: "Novice in 6" },
    { id: "adept_3", label: "Adept in 3" },
  ];
  presets.forEach((preset) => {
    const option = document.createElement("option");
    option.value = preset.id;
    option.textContent = preset.label;
    presetSelect.appendChild(option);
  });
  presetSelect.addEventListener("change", () => {
    applySkillPreset(presetSelect.value);
    saveCharacterToStorage();
    renderCharacterSkills();
  });
  controlsBox.appendChild(makeMetaRow("Preset", presetSelect));

  const budgetControls = document.createElement("div");
  budgetControls.className = "char-inline-controls";
  const budgetInput = document.createElement("input");
  budgetInput.type = "number";
  budgetInput.placeholder = rules.budget === null ? "No limit" : String(rules.budget);
  budgetInput.value = budget === null ? "" : String(budget);
  budgetInput.disabled = characterState.skill_budget_auto;
  budgetInput.addEventListener("input", () => {
    const raw = budgetInput.value;
    characterState.skill_budget = raw === "" ? null : Number(raw);
    saveCharacterToStorage();
    renderCharacterSkills();
  });
  budgetControls.appendChild(budgetInput);
  const autoWrap = document.createElement("label");
  autoWrap.className = "char-inline-toggle";
  const autoInput = document.createElement("input");
  autoInput.type = "checkbox";
  autoInput.checked = characterState.skill_budget_auto;
  autoInput.addEventListener("change", () => {
    characterState.skill_budget_auto = autoInput.checked;
    if (characterState.skill_budget_auto) {
      characterState.skill_budget = autoBudget;
    }
    saveCharacterToStorage();
    renderCharacterSkills();
  });
  autoWrap.appendChild(autoInput);
  const autoText = document.createElement("span");
  autoText.textContent = `Auto from rules (max edges: ${autoBudget}, non-skill: ${nonSkillEdges})`;
  autoWrap.appendChild(autoText);
  budgetControls.appendChild(autoWrap);
  const nonSkillWrap = document.createElement("label");
  nonSkillWrap.className = "char-inline-toggle";
  const nonSkillInput = document.createElement("input");
  nonSkillInput.type = "number";
  nonSkillInput.min = "0";
  nonSkillInput.value = String(nonSkillEdges);
  nonSkillInput.addEventListener("input", () => {
    characterState.skill_edge_non_skill_count = Math.max(0, Number(nonSkillInput.value || 0));
    saveCharacterToStorage();
    renderCharacterSkills();
  });
  nonSkillWrap.appendChild(nonSkillInput);
  const nonSkillText = document.createElement("span");
  nonSkillText.textContent = "Non-skill edges";
  nonSkillWrap.appendChild(nonSkillText);
  budgetControls.appendChild(nonSkillWrap);
  controlsBox.appendChild(makeMetaRow("Budget", budgetControls));
  charContentEl.appendChild(controlsBox);

  const skillsWrap = document.createElement("div");
  skillsWrap.className = "class-tree-tier-list";
  const headerRow = document.createElement("div");
  headerRow.className = "char-feature-row char-skill-header";
  const headerSkill = document.createElement("div");
  headerSkill.textContent = "Skill";
  const headerDetail = document.createElement("div");
  headerDetail.textContent = "Details";
  const headerRank = document.createElement("div");
  headerRank.textContent = "Rank";
  headerRow.appendChild(headerSkill);
  headerRow.appendChild(headerDetail);
  headerRow.appendChild(headerRank);
  skillsWrap.appendChild(headerRow);
  let totalCost = 0;
  skills.forEach((skill) => {
    const row = document.createElement("div");
    row.className = "char-feature-row char-skill-row";
    const label = document.createElement("button");
    label.type = "button";
    label.className = "class-tree-node-title char-inline-link";
    label.textContent = skill;
    label.addEventListener("click", () => {
      focusSkillConnections(skill, "features");
    });
    const select = document.createElement("select");
    select.className = "item-target-select";
    const currentRank = characterState.skills[skill] || ranks[0] || "Untrained";
    const cost = Number(rankCosts[currentRank] ?? 0);
    const skillDesc = _getSkillDescription(skill);
    const tooltipBody =
      `Rank: ${currentRank}\nCost: ${cost}\nMax Rank: ${maxRank}` +
      (skillDesc ? `\n\n${skillDesc}` : "");
    _setTooltipAttrs(label, `Skill: ${skill}`, tooltipBody);
    const isBackgroundAdept = characterState.skill_background.adept === skill;
    const isBackgroundNovice = characterState.skill_background.novice === skill;
    const isBackgroundPathetic = (characterState.skill_background.pathetic || []).includes(skill);
    ranks.forEach((rank) => {
      const option = document.createElement("option");
      option.value = rank;
      option.textContent = rank;
      const rankIndex = getSkillRankIndex(rank, ranks);
      const overCap = rankIndex > maxRankIndex;
      const lockedPathetic = lockPathetic && level === 1 && isBackgroundPathetic && rank !== "Pathetic";
      const overCapAllowed = level === 1 && isBackgroundAdept && rank === "Adept";
      if (!characterState.override_prereqs) {
        if (lockedPathetic) option.disabled = true;
        if (overCap && !overCapAllowed) option.disabled = true;
      }
      if (characterState.skills[skill] === rank) {
        option.selected = true;
      }
      select.appendChild(option);
    });
    select.addEventListener("change", () => {
      characterState.skills[skill] = select.value;
      saveCharacterToStorage();
      renderCharacterSkills();
    });
    totalCost += cost;
    row.appendChild(label);
    const detailBtn = document.createElement("button");
    detailBtn.type = "button";
    detailBtn.className = "char-mini-button";
    detailBtn.textContent = "Details";
    detailBtn.addEventListener("click", () => showSkillDetail(skill));
    row.appendChild(detailBtn);
    row.appendChild(select);
    skillsWrap.appendChild(row);
  });
  charContentEl.appendChild(skillsWrap);

  const summary = document.createElement("div");
  summary.className = "char-feature-meta";
  const budgetText = budget === null ? "No budget limit" : `Budget ${budget}`;
  summary.textContent = `${budgetText} | Total cost ${totalCost}`;
  if (budget !== null && totalCost > budget) {
    summary.textContent += " (over budget)";
  }
  charContentEl.appendChild(summary);

  const derivedTitle = document.createElement("div");
  derivedTitle.className = "char-section-title";
  derivedTitle.textContent = "Capabilities Preview";
  charContentEl.appendChild(derivedTitle);
  const derived = computeDerivedStats(characterState.stats, characterState.skills, rules, level);
  const derivedBox = document.createElement("div");
  derivedBox.className = "char-summary-box";
  derivedBox.textContent = `Power ${derived.power}\nHigh Jump ${derived.highJump}\nLong Jump ${derived.longJump}\nOverland ${derived.overland}\nSwim ${derived.swim}\nThrowing Range ${derived.throwingRange}`;
  const capabilityHelp = {
    power: "Power represents raw lifting and pushing strength.",
    highJump: "High Jump is vertical leap distance.",
    longJump: "Long Jump is horizontal leap distance.",
    overland: "Overland is ground movement speed.",
    swim: "Swim is water movement speed.",
    throw: "Throw is effective thrown range.",
  };
  _setTooltipAttrs(
    derivedBox,
    "Capabilities",
    [
      capabilityHelp.power,
      capabilityHelp.highJump,
      capabilityHelp.longJump,
      capabilityHelp.overland,
      capabilityHelp.swim,
      capabilityHelp.throw,
    ].join("\n")
  );
  charContentEl.appendChild(derivedBox);
  const capRow = document.createElement("div");
  capRow.className = "char-action-row";
  [
    { key: "power", label: "Related Power" },
    { key: "high_jump", label: "Related High Jump" },
    { key: "long_jump", label: "Related Long Jump" },
    { key: "overland", label: "Related Overland" },
    { key: "swim", label: "Related Swim" },
    { key: "throwing_range", label: "Related Throwing" },
  ].forEach((cap) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = cap.label;
    const capKey = cap.key === "throwing_range" ? "throw" : cap.key;
    const capLabel = cap.label.replace("Related ", "");
    _setTooltipAttrs(btn, capLabel, capabilityHelp[capKey] || "");
    btn.addEventListener("click", () => {
      focusCapabilityConnections(cap.key, "features");
    });
    capRow.appendChild(btn);
  });
  charContentEl.appendChild(capRow);

  charContentEl.appendChild(ruleBox);
}

function applySkillPreset(presetId) {
  const rules = characterData.skill_rules || { ranks: [] };
  const ranks = rules.ranks || [];
  const skills = (characterData.skills || []).slice();
  const level = Number(characterState.profile.level || 1);
  const defaultRank = ranks[1] || "Untrained";
  const novice = ranks[2] || "Novice";
  const adept = ranks[3] || "Adept";
  skills.forEach((skill) => {
    characterState.skills[skill] = defaultRank;
  });
  const pick = (count, rank) => {
    skills.slice(0, count).forEach((skill) => {
      characterState.skills[skill] = rank;
    });
  };
  if (presetId === "all_untrained") {
    return;
  }
  if (presetId === "novice_3") {
    pick(3, novice);
  } else if (presetId === "novice_6") {
    pick(6, novice);
  } else if (presetId === "adept_3") {
    pick(3, adept);
  }
  applySkillBackgroundRules(rules, skills, level);
}

function computeAdvancementTotals(level, choices) {
  const numericLevel = Number(level || 1);
  const oddFeatures = Math.max(0, Math.floor((numericLevel - 1) / 2));
  const evenEdges = Math.floor(numericLevel / 2);
  const bonusSkillEdges = (numericLevel >= 2 ? 1 : 0) + (numericLevel >= 6 ? 1 : 0) + (numericLevel >= 12 ? 1 : 0);
  const choiceFeatures =
    (numericLevel >= 5 && choices?.[5] === "feature" ? 1 : 0) +
    (numericLevel >= 30 && choices?.[30] === "feature" ? 1 : 0);
  const choiceEdges =
    (numericLevel >= 10 && choices?.[10] === "edges" ? 2 : 0) +
    (numericLevel >= 20 && choices?.[20] === "edges" ? 2 : 0) +
    (numericLevel >= 30 && choices?.[30] === "edges" ? 2 : 0) +
    (numericLevel >= 40 && choices?.[40] === "edges" ? 2 : 0);
  const baseFeatures = 4;
  const trainingFeature = 1;
  const baseEdges = 4;
  return {
    level: numericLevel,
    features: baseFeatures + trainingFeature + oddFeatures + choiceFeatures,
    edges: baseEdges + evenEdges + bonusSkillEdges + choiceEdges,
    baseFeatures,
    trainingFeature,
    oddFeatures,
    choiceFeatures,
    baseEdges,
    evenEdges,
    bonusSkillEdges,
    choiceEdges,
  };
}

function shuffleCopy(list) {
  const arr = Array.isArray(list) ? list.slice() : [];
  for (let i = arr.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    const tmp = arr[i];
    arr[i] = arr[j];
    arr[j] = tmp;
  }
  return arr;
}

function _collectSkillTargetsFromFeatures(entries, rules, skills) {
  const targets = new Map();
  const ranks = rules.ranks || [];
  (entries || []).forEach((entry) => {
    const reqs = _parseSkillRequirements(entry?.prerequisites || "", rules, skills);
    reqs.forEach((req) => {
      const current = targets.get(req.skill);
      if (!current || _rankIndex(req.rank, rules) > _rankIndex(current, rules)) {
        targets.set(req.skill, req.rank);
      }
    });
  });
  return targets;
}

function canAddFeatureBySlot(featureName) {
  const nodes = characterData?.nodes || [];
  const feature = nodes.find((node) => node.name === featureName);
  const rank = String(feature?.rank || 1);
  const limits = { ...(characterData?.feature_slots_by_rank || {}), ...characterState.feature_slots_override };
  const limit = Number(limits[rank] || 0);
  if (!limit) return true;
  let used = 0;
  Array.from(characterState.features).forEach((name) => {
    const selected = nodes.find((node) => node.name === name);
    const selectedRank = String(selected?.rank || 1);
    if (selectedRank === rank) used += 1;
  });
  return used < limit;
}

function randomLegalBuild() {
  if (!characterData) return;
  const levelInput = prompt("Random build level (1-50):", String(characterState.profile.level || 1));
  if (levelInput === null) return;
  const parsedLevel = Number(levelInput);
  if (!Number.isFinite(parsedLevel) || parsedLevel < 1) {
    alert("Invalid level. Enter a number from 1 to 50.");
    return;
  }
  const clampedLevel = Math.max(1, Math.min(50, Math.floor(parsedLevel)));
  characterState.profile.level = clampedLevel;
  const rules = characterData.skill_rules || { ranks: [] };
  const ranks = rules.ranks || [];
  const defaultRank = ranks[1] || "Untrained";
  const skills = (characterData.skills || []).slice();
  const level = Number(characterState.profile.level || 1);
  characterState.advancement_choices = _randomizeAdvancementChoices(level, characterState.advancement_choices || {});
  const totals = computeAdvancementTotals(level, characterState.advancement_choices || {});

  characterState.class_ids = [];
  characterState.features = new Set();
  characterState.edges = new Set();
  characterState.extras = [];
  characterState.feature_order = [];
  characterState.edge_order = [];
  _randomizeStats(level, characterState.advancement_choices || {});
  skills.forEach((skill) => {
    characterState.skills[skill] = defaultRank;
  });
  normalizeBackgroundState(rules, skills);
  if (level === 1) {
    const bgRules = rules.background || {};
    const picks = shuffleCopy(skills);
    characterState.skill_background.adept = Number(bgRules.adept || 0) > 0 ? picks.shift() || "" : "";
    characterState.skill_background.novice = Number(bgRules.novice || 0) > 0 ? picks.shift() || "" : "";
    const patheticCount = Number(bgRules.pathetic || 0);
    characterState.skill_background.pathetic = [];
    for (let i = 0; i < patheticCount; i += 1) {
      characterState.skill_background.pathetic.push(picks.shift() || "");
    }
  }
  applySkillBackgroundRules(rules, skills, level);
  _randomizeSkills(level, rules, skills);

  const classes = shuffleCopy(characterData.classes || []);
  const legalClasses = classes.filter((entry) => {
    const classNode = (characterData.nodes || []).find((node) => node.id === entry.id);
    if (!inContentScope({ ...entry, ...(classNode || {}) })) return false;
    return prereqStatus(classNode?.prerequisites || "", "class").status === "available";
  });
  const classPick = legalClasses[0] || classes.find((entry) => inContentScope(entry)) || classes[0];
  if (classPick) {
    characterState.class_id = classPick.id;
    const maxClasses = 4;
    const picks = [];
    if (classPick) picks.push(classPick);
    const remainingClasses = legalClasses.filter((entry) => entry.id !== classPick?.id);
    while (picks.length < maxClasses && remainingClasses.length) {
      const next = remainingClasses.shift();
      if (!next) break;
      if (!picks.some((entry) => entry.id === next.id)) picks.push(next);
    }
    characterState.class_ids = picks.map((entry) => entry.id);
    ensurePlaytestScopeForClass(classPick.name);
  }

  const classEntry = (characterData.classes || []).find((cls) => cls.id === characterState.class_id);
  const classNodeIds = new Set();
  Object.values(_classTierMap(classEntry) || {}).forEach((ids) => {
    (ids || []).forEach((id) => classNodeIds.add(id));
  });
  const classFeatureEntries = (characterData.nodes || []).filter(
    (node) => node?.type === "feature" && classNodeIds.has(node.id)
  );
  const skillTargets = _collectSkillTargetsFromFeatures(classFeatureEntries, rules, skills);
  if (skillTargets.size) {
    _randomizeSkills(level, rules, skills, skillTargets);
  }

  ensurePlaytestScopeForClass(characterState.feature_class_filter);
  const multiClassNodeIds = new Set();
  (characterState.class_ids || []).forEach((clsId) => {
    const entry = (characterData.classes || []).find((cls) => cls.id === clsId);
    Object.values(_classTierMap(entry) || {}).forEach((ids) => {
      (ids || []).forEach((id) => multiClassNodeIds.add(id));
    });
  });
  const classFeatures = shuffleCopy(
    (characterData.features || []).filter((entry) => multiClassNodeIds.has(entry.id) && inContentScope(entry))
  );
  const allFeatures = shuffleCopy((characterData.features || []).filter((entry) => inContentScope(entry)));
  const featurePool = classFeatures.concat(allFeatures);
  const allEdges = shuffleCopy((characterData.edges_catalog || []).filter((entry) => inContentScope(entry)));
  for (const entry of allEdges) {
    if (characterState.edges.size >= totals.edges) break;
    if (characterState.edges.has(entry.name)) continue;
    if (!isEdgeAllowed(entry, false)) continue;
    characterState.edges.add(entry.name);
    _addToOrder(characterState.edge_order, entry.name);
  }

  for (const entry of featurePool) {
    if (characterState.features.size >= totals.features) break;
    if (characterState.features.has(entry.name)) continue;
    if (!isFeatureAllowed(entry, false)) continue;
    if (!canAddFeatureBySlot(entry.name)) continue;
    characterState.features.add(entry.name);
    _addToOrder(characterState.feature_order, entry.name);
  }

  if (characterState.features.size < totals.features) {
    for (const entry of featurePool) {
      if (characterState.features.size >= totals.features) break;
      if (characterState.features.has(entry.name)) continue;
      if (!isFeatureAllowed(entry, false)) continue;
      if (!canAddFeatureBySlot(entry.name)) continue;
      characterState.features.add(entry.name);
      _addToOrder(characterState.feature_order, entry.name);
    }
  }

  saveCharacterToStorage();
  renderCharacterStep();
  const warnings = _validationWarnings();
  if (warnings.length) {
    alert(`Random build generated with ${warnings.length} warning(s). Review Summary for fixes.`);
  }
}

function setTrainingType(nextType) {
  const options = ["Agility Training", "Brutal Training", "Focused Training", "Inspired Training"];
  const previous = characterState.training_type || "";
  if (previous && previous !== nextType && options.includes(previous)) {
    characterState.features.delete(previous);
    _removeFromOrder(characterState.feature_order, previous);
  }
  characterState.training_type = nextType || "";
  if (!nextType) return;
  if (!options.includes(nextType)) return;
  const entry =
    (characterData?.features || []).find((feat) => feat.name === nextType) ||
    (characterData?.nodes || []).find((node) => node?.type === "feature" && node?.name === nextType);
  if (!entry) {
    if (window.DSUI && typeof window.DSUI.toast === "function") {
      window.DSUI.toast(`Training feature not found: ${nextType}`);
    }
    return;
  }
  characterState.features.add(nextType);
  _addToOrder(characterState.feature_order, nextType);
}

function _randomizeAdvancementChoices(level, current) {
  const next = { ...current };
  const options = ["stats", "features", "edges"];
  [5, 10, 20, 30, 40].forEach((lvl) => {
    if (Number(level) >= lvl) {
      next[lvl] = options[Math.floor(Math.random() * options.length)];
    }
  });
  return next;
}

function _randomizeStats(level, choices) {
  const budget = computeStatBudgets(level, choices || {});
  const stats = { hp: 10, atk: 5, def: 5, spatk: 5, spdef: 5, spd: 5 };
  const maxCaps =
    Number(level) === 1
      ? { hp: 15, atk: 10, def: 10, spatk: 10, spdef: 10, spd: 10 }
      : null;
  const generalStats = ["hp", "def", "spdef", "spd"];
  const restrictedStats = ["atk", "spatk"];
  const addPoint = (key) => {
    if (maxCaps && stats[key] >= maxCaps[key]) return false;
    stats[key] += 1;
    return true;
  };
  let safety = 0;
  for (let i = 0; i < Number(budget.general || 0); i += 1) {
    if (safety++ > 1000) break;
    const pool = generalStats.filter((key) => !maxCaps || stats[key] < maxCaps[key]);
    if (!pool.length) break;
    addPoint(pool[Math.floor(Math.random() * pool.length)]);
  }
  safety = 0;
  for (let i = 0; i < Number(budget.restricted || 0); i += 1) {
    if (safety++ > 1000) break;
    const pool = restrictedStats.filter((key) => !maxCaps || stats[key] < maxCaps[key]);
    if (!pool.length) break;
    addPoint(pool[Math.floor(Math.random() * pool.length)]);
  }
  characterState.stats = stats;
}

function _randomizeSkills(level, rules, skills, requiredSkills = null) {
  const ranks = rules.ranks || [];
  if (!ranks.length || !skills.length) return;
  characterState.skill_budget_auto = true;
  characterState.skill_budget = getAutoSkillBudget(level, rules);
  const maxRank = getMaxRankForLevel(level, rules);
  const maxRankIndex = _rankIndex(maxRank, rules);
  const rankCosts = rules.rank_costs || {};
  const lockPathetic = (rules.background || {}).lock_pathetic_level1 !== false;
  const locked = new Set(
    Number(level) === 1 && lockPathetic && Array.isArray(characterState.skill_background?.pathetic)
      ? characterState.skill_background.pathetic.filter(Boolean)
      : []
  );
  const costFor = (rank) => Number(rankCosts?.[rank] ?? 0);
  const totalCost = () =>
    skills.reduce((sum, skill) => sum + costFor(_findSkillRank(skill)), 0);
  let budget = Number(characterState.skill_budget || 0);
  let current = totalCost();
  if (requiredSkills && requiredSkills.size) {
    const ordered = Array.from(requiredSkills.entries()).sort(
      (a, b) => _rankIndex(b[1], rules) - _rankIndex(a[1], rules)
    );
    ordered.forEach(([skill, targetRank]) => {
      if (!skills.includes(skill)) return;
      if (locked.has(skill)) return;
      let currentRank = _findSkillRank(skill);
      while (_rankIndex(currentRank, rules) < _rankIndex(targetRank, rules)) {
        const idx = _rankIndex(currentRank, rules);
        const nextRank = ranks[idx + 1];
        if (!nextRank) break;
        const delta = costFor(nextRank) - costFor(currentRank);
        if (current + delta > budget) break;
        characterState.skills[skill] = nextRank;
        current += delta;
        currentRank = nextRank;
      }
    });
  }
  let safety = 0;
  while (current < budget && safety++ < 10000) {
    const skill = skills[Math.floor(Math.random() * skills.length)];
    if (locked.has(skill)) continue;
    const currentRank = _findSkillRank(skill);
    const idx = _rankIndex(currentRank, rules);
    if (idx >= maxRankIndex) continue;
    const nextRank = ranks[idx + 1];
    if (!nextRank) continue;
    const nextCost = costFor(nextRank);
    const delta = nextCost - costFor(currentRank);
    if (current + delta > budget) continue;
    characterState.skills[skill] = nextRank;
    current += delta;
  }
}

function renderCharacterAdvancement() {
  charContentEl.innerHTML = "";
  charContentEl.setAttribute("data-step-target", "advancement");
  appendNavRow();
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Trainer Advancement";
  _setTooltipAttrs(
    title,
    "Trainer Advancement",
    "Milestone bonuses and total progression at your current level."
  );
  charContentEl.appendChild(title);
  const subtitle = document.createElement("div");
  subtitle.className = "char-feature-meta";
  subtitle.textContent = "Review milestone bonuses and how many total features/edges you should have.";
  charContentEl.appendChild(subtitle);
  appendStepModeToggle();

  ensurePlaytestScopeForClass(characterState.edge_class_filter);
  _renderPlannerPanel(charContentEl);
  _renderCloseUnlocks(charContentEl);

  const level = Number(characterState.profile.level || 1);
  const choices = characterState.advancement_choices || {};
  const summary = computeAdvancementTotals(level, choices);
  const autoBudget = getAutoSkillBudget(level, characterData.skill_rules || {});

  const metaRow = document.createElement("div");
  metaRow.className = "char-pill-list";
  const metaItems = [
    { label: `Level ${level}`, help: "Your current trainer level." },
    { label: `Total Features ${summary.features}`, help: "Total number of features you should have at this level." },
    { label: `Total Edges ${summary.edges}`, help: "Total number of edges you should have at this level." },
    { label: `Max Skill Edges ${autoBudget}`, help: "Maximum number of edges granted by skill ranks." },
  ];
  metaItems.forEach((item) => {
    const pill = document.createElement("span");
    pill.className = "char-pill";
    pill.textContent = item.label;
    _setTooltipAttrs(pill, item.label, item.help);
    metaRow.appendChild(pill);
  });
  charContentEl.appendChild(metaRow);

  const choiceTitle = document.createElement("div");
  choiceTitle.className = "char-section-title";
  choiceTitle.textContent = "Milestone Choices";
  _setTooltipAttrs(
    choiceTitle,
    "Milestone Choices",
    "At certain levels, pick a bonus. These choices affect total features/edges/stats."
  );
  charContentEl.appendChild(choiceTitle);

  const choiceWrap = document.createElement("div");
  choiceWrap.className = "char-adv-grid";
  const choiceDefs = [
    {
      level: 5,
      label: "Level 5 Amateur Bonus",
      options: [
        { value: "stats", label: "Stat Points" },
        { value: "feature", label: "General Feature" },
      ],
    },
    {
      level: 10,
      label: "Level 10 Capable Bonus",
      options: [
        { value: "stats", label: "Stat Points" },
        { value: "edges", label: "Two Edges" },
      ],
    },
    {
      level: 20,
      label: "Level 20 Veteran Bonus",
      options: [
        { value: "stats", label: "Stat Points" },
        { value: "edges", label: "Two Edges" },
      ],
    },
    {
      level: 30,
      label: "Level 30 Elite Bonus",
      options: [
        { value: "stats", label: "Stat Points" },
        { value: "edges", label: "Two Edges" },
        { value: "feature", label: "General Feature" },
      ],
    },
    {
      level: 40,
      label: "Level 40 Champion Bonus",
      options: [
        { value: "stats", label: "Stat Points" },
        { value: "edges", label: "Two Edges" },
      ],
    },
  ];
  const optionHelp = {
    stats: "Gain additional stat points at this milestone.",
    feature: "Gain one general feature at this milestone.",
    edges: "Gain two edges at this milestone.",
  };
  choiceDefs.forEach((choice) => {
    const card = document.createElement("div");
    card.className = "char-summary-box char-adv-block";
    const header = document.createElement("div");
    header.className = "char-title-row";
    const label = document.createElement("div");
    label.className = "char-section-title";
    label.textContent = choice.label;
    _setTooltipAttrs(label, choice.label, `Unlocked at Level ${choice.level}.`);
    header.appendChild(label);
    const status = document.createElement("span");
    status.className = `char-pill ${level >= choice.level ? "" : "is-muted"}`.trim();
    status.textContent = level >= choice.level ? "Available" : `Locked (Lv ${choice.level})`;
    header.appendChild(status);
    card.appendChild(header);

    const optionsRow = document.createElement("div");
    optionsRow.className = "char-pill-list";
    const current = choices[choice.level] || choice.options[0].value;
    choice.options.forEach((opt) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "char-pill char-pill-toggle";
      btn.textContent = opt.label;
      btn.classList.toggle("is-active", opt.value === current);
      btn.setAttribute("aria-pressed", String(opt.value === current));
      _setTooltipAttrs(btn, opt.label, optionHelp[opt.value] || "");
      if (level < choice.level) {
        btn.disabled = true;
        btn.classList.add("is-disabled");
      }
      btn.addEventListener("click", () => {
        if (level < choice.level) return;
        characterState.advancement_choices = { ...characterState.advancement_choices, [choice.level]: opt.value };
        saveCharacterToStorage();
        renderCharacterAdvancement();
      });
      optionsRow.appendChild(btn);
    });
    card.appendChild(optionsRow);
    choiceWrap.appendChild(card);
  });
  charContentEl.appendChild(choiceWrap);

  const breakdownTitle = document.createElement("div");
  breakdownTitle.className = "char-section-title";
  breakdownTitle.textContent = "Breakdown";
  _setTooltipAttrs(
    breakdownTitle,
    "Breakdown",
    "Where your total features and edges are coming from."
  );
  charContentEl.appendChild(breakdownTitle);

  const breakdownRow = document.createElement("div");
  breakdownRow.className = "char-pill-list";
  const featureBreakdown = `Features: Base ${summary.baseFeatures} + Training ${summary.trainingFeature} + Odd Levels ${summary.oddFeatures} + Choice ${summary.choiceFeatures}`;
  const edgeBreakdown = `Edges: Base ${summary.baseEdges} + Even Levels ${summary.evenEdges} + Skill Rank Bonuses ${summary.bonusSkillEdges} + Choice ${summary.choiceEdges}`;
  [featureBreakdown, edgeBreakdown].forEach((text) => {
    const pill = document.createElement("span");
    pill.className = "char-pill";
    pill.textContent = text;
    _setTooltipAttrs(pill, "Breakdown", text);
    breakdownRow.appendChild(pill);
  });
  charContentEl.appendChild(breakdownRow);
}

function appendStepModeToggle() {
  const wrap = document.createElement("div");
  wrap.className = "char-pill-row";
  const makeToggle = (labelText, helpText, stateKey) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "char-pill char-pill-toggle";
    btn.setAttribute("aria-pressed", String(!!characterState[stateKey]));
    btn.textContent = labelText;
    _setTooltipAttrs(btn, labelText, helpText);
    const update = () => {
      btn.classList.toggle("is-active", !!characterState[stateKey]);
      btn.setAttribute("aria-pressed", String(!!characterState[stateKey]));
    };
    update();
    btn.addEventListener("click", () => {
      characterState[stateKey] = !characterState[stateKey];
      saveCharacterToStorage();
      updateStepButtons();
      update();
    });
    return btn;
  };
  wrap.appendChild(
    makeToggle(
      "Step-by-step",
      "Locks navigation until you complete each step in order. Useful for new builds.",
      "step_by_step"
    )
  );
  wrap.appendChild(
    makeToggle(
      "Override Warnings",
      "Allows moving ahead even if validation warnings exist.",
      "allow_warnings"
    )
  );
  charContentEl.appendChild(wrap);
}

function updateStepButtons() {
  if (!charStepButtons.length) return;
  charStepButtons.forEach((btn) => {
    btn.disabled = false;
  });
  return;
  const order = [
    "profile",
    "builder",
    "skills",
    "advancement",
    "class",
    "features",
    "edges",
    "extras",
    "inventory",
    "pokemon-team",
    "summary",
  ];
  const validity = getStepValidity();
  let maxIndex = 0;
  for (let i = 0; i < order.length; i += 1) {
    const step = order[i];
    if (!validity[step]) {
      maxIndex = i;
      break;
    }
    maxIndex = i + 1;
  }
  charStepButtons.forEach((btn) => {
    const step = btn.getAttribute("data-step");
    const index = order.indexOf(step);
    btn.disabled = index > maxIndex;
  });
}

function getStepValidity() {
  const rules = characterData?.skill_rules || { ranks: [] };
  const ranks = rules.ranks || [];
  const skills = characterData?.skills || [];
  const level = Number(characterState.profile.level || 1);
  const classEntry = (characterData?.classes || []).find((cls) => cls.id === characterState.class_id);
  const featureSlots = { ...(characterData?.feature_slots_by_rank || {}), ...characterState.feature_slots_override };
  const advancementTotals = computeAdvancementTotals(level, characterState.advancement_choices || {});

  const profileChecks = [
    { ok: Number.isFinite(level) && level >= 1, text: "Level is at least 1" },
    { ok: !!characterState.profile.name, text: "Name is set" },
  ];

  let skillsValid = true;
  const bgRules = rules.background || {};
  const bg = characterState.skill_background || { adept: "", novice: "", pathetic: [] };
  const picks = [bg.adept, bg.novice, ...(bg.pathetic || [])].filter(Boolean);
  const unique = new Set(picks);
  if (bgRules.adept && !bg.adept) skillsValid = false;
  if (bgRules.novice && !bg.novice) skillsValid = false;
  if (Number(bgRules.pathetic || 0) > 0) {
    if ((bg.pathetic || []).some((s) => !s)) skillsValid = false;
  }
  if (unique.size !== picks.length) skillsValid = false;

  const budget = characterState.skill_budget;
  if (budget !== null) {
    let totalCost = 0;
    Object.entries(characterState.skills).forEach(([skill, rank]) => {
      if (!skills.includes(skill)) return;
      totalCost += Number(rules.rank_costs?.[rank] ?? 0);
    });
    if (totalCost > budget) skillsValid = false;
  }
  if (!characterState.override_prereqs) {
    const maxRank = getMaxRankForLevel(level, rules);
    const maxRankIndex = getSkillRankIndex(maxRank, ranks);
    const lockPathetic = bgRules.lock_pathetic_level1 !== false;
    Object.entries(characterState.skills).forEach(([skill, rank]) => {
      if (!skills.includes(skill)) return;
      const rankIndex = getSkillRankIndex(rank, ranks);
      const isBackgroundAdept = bg.adept === skill;
      const isBackgroundPathetic = Array.isArray(bg.pathetic) && bg.pathetic.includes(skill);
      const overCap = rankIndex > maxRankIndex;
      if (overCap && !(level === 1 && isBackgroundAdept && rank === "Adept")) skillsValid = false;
      if (lockPathetic && level === 1 && isBackgroundPathetic && rank !== "Pathetic") skillsValid = false;
    });
  }

  const classValid = !!characterState.class_id && !!classEntry;

  let featuresValid = true;
  if (classEntry && featureSlots) {
    const countByRank = {};
    const nodes = characterData?.nodes || [];
    Array.from(characterState.features).forEach((name) => {
      const node = nodes.find((n) => n.name === name);
      const rank = node?.rank || 1;
      countByRank[rank] = (countByRank[rank] || 0) + 1;
    });
    Object.entries(featureSlots).forEach(([rank, limit]) => {
      const used = countByRank[rank] || 0;
      if (Number(limit) > 0 && used > Number(limit)) featuresValid = false;
    });
  }

  const edgesValid = true;

  const profileValid = profileChecks.every((entry) => entry.ok);
  const featureCountOk = characterState.features.size === advancementTotals.features;
  const edgeCountOk = characterState.edges.size === advancementTotals.edges;

  return {
    profile: profileValid,
    builder: true,
    skills: skillsValid,
    advancement: true,
    class: classValid,
    features: featuresValid && featureCountOk,
    edges: edgesValid && edgeCountOk,
    extras: true,
    inventory: true,
    "pokemon-team": true,
    summary: profileValid && skillsValid && classValid && featuresValid && edgesValid && featureCountOk && edgeCountOk,
  };
}

function renderStepGuide() {
  if (!characterState.step_by_step) return;
  const order = [
    "profile",
    "builder",
    "skills",
    "advancement",
    "class",
    "features",
    "edges",
    "extras",
    "inventory",
    "pokemon-team",
    "summary",
  ];
  const currentIndex = order.indexOf(characterStep);
  const validity = getStepValidity();
  const allowWarnings = characterState.allow_warnings;
  const warnings = _validationWarnings();

  const guide = document.createElement("div");
  guide.className = "char-summary-box char-no-word-links";
  const guideRow = document.createElement("div");
  guideRow.className = "char-pill-list";
  const stepPill = document.createElement("span");
  stepPill.className = "char-pill";
  stepPill.textContent = `Step ${currentIndex + 1}/${order.length}: ${characterStep}`;
  _setTooltipAttrs(stepPill, "Current Step", "You are currently on this step.");
  guideRow.appendChild(stepPill);
  const statusPill = document.createElement("span");
  statusPill.className = `char-pill ${validity[characterStep] ? "" : "is-muted"}`.trim();
  let statusText = validity[characterStep] ? "Complete" : "Needs attention";
  if (allowWarnings) statusText = "Override enabled";
  statusPill.textContent = `Status: ${statusText}`;
  _setTooltipAttrs(statusPill, "Status", "Determines whether step-by-step allows you to proceed.");
  guideRow.appendChild(statusPill);
  const disableBtn = document.createElement("button");
  disableBtn.type = "button";
  disableBtn.className = "char-mini-button";
  disableBtn.textContent = "Disable Step-by-step";
  _setTooltipAttrs(disableBtn, "Disable Step-by-step", "Unlocks all tabs and steps.");
  disableBtn.addEventListener("click", () => {
    characterState.step_by_step = false;
    saveCharacterToStorage();
    renderCharacterStep();
  });
  guideRow.appendChild(disableBtn);
  guide.appendChild(guideRow);
  charContentEl.appendChild(guide);

  const tutorial = document.createElement("div");
  tutorial.className = "char-summary-box char-no-word-links";
  const stepHelp = {
    profile:
      "Tell us who your trainer is. Set Name and Level first, then fill in Region and Concept for flavor. Add Background notes if your table wants it.",
    builder:
      "Use builder utilities here: randomize/reset progression, track pending picks, and jump directly to class/features/edges.",
    skills:
      "Pick your Background skill ranks. You must choose 1 Adept, 1 Novice, and 3 Pathetic skills at Level 1. Then adjust other skills within your budget. Use the preview to confirm capabilities.",
    advancement:
      "Choose milestone bonuses at Levels 5/10/20/30/40. These change your total Edge/Feature counts and stat budgets.",
    class:
      "Pick your first Class to define your build direction. Use the search box to find a concept, then select a class that matches your skill ranks.",
    features:
      "Select your starting Features. Ranked features count toward slot limits by rank. Use the list to see prerequisites and frequencies.",
    edges:
      "Select Edges next. Skill Edges usually raise ranks, and other edges unlock tricks or crafting. Make sure prerequisites are met unless you override.",
    extras:
      "Add class mechanics or special notes you want exported into the Fancy PTU sheet. These are optional.",
    inventory:
      "Track key items and Pokemon items. These export directly into the Fancy PTU sheet inventory tabs.",
    "pokemon-team":
      "Build your Pokemon team. Add species, set levels, and attach moves, abilities, and items for each Pokemon.",
    summary:
      "Review everything. Download JSON to share or import later, and open the standalone builder if you want an offline copy.",
  };
  const todo = [];
  if (characterStep === "profile") {
    if (!characterState.profile.name) todo.push("Enter a trainer name.");
    if (Number(characterState.profile.level || 1) < 1) todo.push("Set Level to 1 or higher.");
  } else if (characterStep === "skills") {
    const rules = characterData?.skill_rules || {};
    const bgRules = rules.background || {};
    if (bgRules.adept && !characterState.skill_background.adept) todo.push("Pick an Adept background skill.");
    if (bgRules.novice && !characterState.skill_background.novice) todo.push("Pick a Novice background skill.");
    const missingPathetic = (characterState.skill_background.pathetic || []).filter((s) => !s).length;
    if (Number(bgRules.pathetic || 0) > 0 && missingPathetic > 0) {
      todo.push("Pick all Pathetic background skills.");
    }
  } else if (characterStep === "class") {
    if (!characterState.class_id) todo.push("Select a Class.");
  } else if (characterStep === "features") {
    if (characterState.features.size === 0) todo.push("Select at least one Feature.");
  } else if (characterStep === "edges") {
    if (characterState.edges.size === 0) todo.push("Select at least one Edge.");
  }
  const what = document.createElement("div");
  what.className = "char-section-title";
  what.textContent = "What to do";
  tutorial.appendChild(what);
  const helpText = document.createElement("div");
  helpText.className = "char-feature-meta";
  helpText.textContent = stepHelp[characterStep] || "";
  tutorial.appendChild(helpText);
  if (todo.length) {
    const todoRow = document.createElement("div");
    todoRow.className = "char-pill-list";
    todo.forEach((item) => {
      const pill = document.createElement("span");
      pill.className = "char-pill is-muted";
      pill.textContent = item;
      todoRow.appendChild(pill);
    });
    tutorial.appendChild(todoRow);
  }
  charContentEl.appendChild(tutorial);

  const checklist = document.createElement("div");
  checklist.className = "char-summary-box char-no-word-links";
  const items = [];
  if (characterStep === "profile") {
    items.push({ ok: !!characterState.profile.name, text: "Set trainer name" });
    items.push({ ok: Number(characterState.profile.level || 1) >= 1, text: "Level is at least 1" });
  } else if (characterStep === "builder") {
    items.push({ ok: true, text: "Builder utilities are optional" });
  } else if (characterStep === "skills") {
    const rules = characterData?.skill_rules || {};
    const bgRules = rules.background || {};
    if (bgRules.adept) items.push({ ok: !!characterState.skill_background.adept, text: "Pick Adept skill" });
    if (bgRules.novice) items.push({ ok: !!characterState.skill_background.novice, text: "Pick Novice skill" });
    const neededPathetic = Number(bgRules.pathetic || 0);
    if (neededPathetic > 0) {
      const missingPathetic = (characterState.skill_background.pathetic || []).filter((s) => !s).length;
      items.push({ ok: missingPathetic === 0, text: "Pick Pathetic skills" });
    }
    if (characterState.skill_budget !== null) {
      const ruleset = characterData?.skill_rules || {};
      const skills = characterData?.skills || [];
      let totalCost = 0;
      Object.entries(characterState.skills).forEach(([skill, rank]) => {
        if (!skills.includes(skill)) return;
        totalCost += Number(ruleset.rank_costs?.[rank] ?? 0);
      });
      items.push({ ok: totalCost <= characterState.skill_budget, text: "Stay within skill budget" });
    }
  } else if (characterStep === "class") {
    items.push({ ok: !!characterState.class_id, text: "Select a class" });
  } else if (characterStep === "features") {
    const totals = computeAdvancementTotals(Number(characterState.profile.level || 1), characterState.advancement_choices || {});
    items.push({
      ok: characterState.features.size === totals.features,
      text: `Select ${totals.features} features (currently ${characterState.features.size})`,
    });
  } else if (characterStep === "edges") {
    const totals = computeAdvancementTotals(Number(characterState.profile.level || 1), characterState.advancement_choices || {});
    items.push({
      ok: characterState.edges.size === totals.edges,
      text: `Select ${totals.edges} edges (currently ${characterState.edges.size})`,
    });
  } else if (characterStep === "extras") {
    items.push({ ok: true, text: "Extras are optional" });
  } else if (characterStep === "inventory") {
    items.push({ ok: true, text: "Inventory is optional" });
  }
  if (items.length) {
    const list = document.createElement("div");
    list.className = "char-pill-list";
    items.forEach((item) => {
      const pill = document.createElement("span");
      pill.className = `char-pill ${item.ok ? "" : "is-muted"}`.trim();
      pill.textContent = `${item.ok ? "?" : "?"} ${item.text}`;
      list.appendChild(pill);
    });
    checklist.appendChild(list);
    charContentEl.appendChild(checklist);
  }
  if (!validity[characterStep] && warnings.length) {
    const missing = document.createElement("div");
    missing.className = "char-summary-box char-no-word-links";
    missing.textContent = warnings.map((w) => `- ${w}`).join("\n");
    charContentEl.appendChild(missing);
  }
  const nav = document.createElement("div");
  nav.className = "char-action-row";
  const prev = document.createElement("button");
  prev.textContent = "Back";
  prev.disabled = currentIndex <= 0;
  prev.addEventListener("click", () => {
    if (currentIndex <= 0) return;
    characterStep = order[currentIndex - 1];
    charStepButtons.forEach((btn) => btn.classList.toggle("active", btn.getAttribute("data-step") === characterStep));
    renderCharacterStep();
  });
  const next = document.createElement("button");
  next.textContent = currentIndex >= order.length - 1 ? "Finish" : "Next";
  const canAdvance = allowWarnings || validity[characterStep];
  next.disabled = !canAdvance;
  next.addEventListener("click", () => {
    if (!canAdvance) return;
    if (currentIndex >= order.length - 1) return;
    characterStep = order[currentIndex + 1];
    charStepButtons.forEach((btn) => btn.classList.toggle("active", btn.getAttribute("data-step") === characterStep));
    renderCharacterStep();
  });
  nav.appendChild(prev);
  nav.appendChild(next);
  charContentEl.appendChild(nav);
}

function renderCharacterClass() {
  charContentEl.innerHTML = "";
  charContentEl.setAttribute("data-step-target", "class");
  appendNavRow();
  const title = document.createElement("div");
  title.className = "char-section-title";
  const classCount = (characterData.classes || []).length;
  title.textContent = `Choose a Class (${classCount})`;
  charContentEl.appendChild(title);
  appendStepModeToggle();

  ensurePlaytestScopeForClass(characterState.edge_class_filter);
  const randomRow = document.createElement("div");
  randomRow.className = "char-action-row";
  const randomBuildBtn = document.createElement("button");
  randomBuildBtn.type = "button";
  randomBuildBtn.textContent = "Generate Random Legal Build";
  randomBuildBtn.addEventListener("click", () => {
    randomLegalBuild();
  });
  randomRow.appendChild(randomBuildBtn);
  charContentEl.appendChild(randomRow);

  const layout = document.createElement("div");
  layout.className = "char-class-layout";
  const listWrap = document.createElement("div");
  listWrap.className = "char-list-panel";
  const list = document.createElement("div");
  list.className = "char-class-list char-entry-list";
  const hint = document.createElement("div");
  hint.className = "char-feature-meta";
  hint.textContent = "Scroll the list to see more classes.";
  const search = document.createElement("input");
  search.className = "char-search";
  search.placeholder = "Search classes by name, prerequisites, or what they do...";
  const searchRow = document.createElement("div");
  searchRow.className = "char-list-toolbar";
  const clearSearch = document.createElement("button");
  clearSearch.type = "button";
  clearSearch.className = "char-mini-button";
  clearSearch.textContent = "Clear";
  clearSearch.addEventListener("click", () => {
    search.value = "";
    query = "";
    renderList();
  });
  searchRow.appendChild(search);
  searchRow.appendChild(clearSearch);
  const statusRow = document.createElement("div");
  statusRow.className = "char-pill-row";
  const statusDefs = [
    { value: "all", label: "All", help: "Show all classes." },
    { value: "available", label: "Available", help: "All prerequisites satisfied." },
    { value: "close", label: "Close", help: "Missing one prerequisite." },
    { value: "unavailable", label: "Unavailable", help: "Missing multiple prerequisites." },
    { value: "locked", label: "Locked", help: "Manual or blocked prerequisites." },
  ];
  const renderStatusRow = () => {
    statusRow.innerHTML = "";
    statusDefs.forEach((def) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "char-pill char-pill-toggle";
      btn.textContent = def.label;
      btn.classList.toggle("is-active", (characterState.class_status_filter || "all") === def.value);
      btn.setAttribute("aria-pressed", String((characterState.class_status_filter || "all") === def.value));
      _setTooltipAttrs(btn, def.label, def.help);
      btn.addEventListener("click", () => {
        characterState.class_status_filter = def.value;
        renderStatusRow();
        renderList();
      });
      statusRow.appendChild(btn);
    });
  };
  renderStatusRow();
  const countRow = document.createElement("div");
  countRow.className = "char-count";
  const alpha = createAlphaIndex();
  listWrap.appendChild(searchRow);
  listWrap.appendChild(statusRow);
  listWrap.appendChild(hint);
  listWrap.appendChild(countRow);
  listWrap.appendChild(createStatusLegend());
  listWrap.appendChild(alpha.element);
  listWrap.appendChild(list);
  listWrap.appendChild(createDensityToggle(renderList));

  const detail = document.createElement("div");
  detail.className = "class-tree-details-inner";
  layout.appendChild(listWrap);
  layout.appendChild(detail);
  charContentEl.appendChild(layout);

  let query = "";
  let previewId = characterState.class_id || "";
  const classes = (characterData.classes || []).slice().sort((a, b) => String(a.name).localeCompare(String(b.name)));
  const selectedPanel = document.createElement("div");
  selectedPanel.className = "char-summary-box";
  const selectedTitle = document.createElement("div");
  selectedTitle.className = "char-section-title";
  selectedTitle.textContent = "Selected Classes (max 4)";
  selectedPanel.appendChild(selectedTitle);
  const selectedList = document.createElement("div");
  selectedList.className = "char-action-row";
  selectedPanel.appendChild(selectedList);
  charContentEl.appendChild(selectedPanel);

  const renderSelectedClasses = () => {
    selectedList.innerHTML = "";
    const classIds = Array.isArray(characterState.class_ids) ? characterState.class_ids : [];
    if (!classIds.length) {
      const empty = document.createElement("span");
      empty.className = "char-pill is-muted";
      empty.textContent = "No classes selected";
      selectedList.appendChild(empty);
      return;
    }
    classIds.forEach((id) => {
      const entry = (characterData.classes || []).find((cls) => cls.id === id);
      const name = entry?.name || id;
      const pill = document.createElement("button");
      pill.type = "button";
      pill.className = "char-pill char-pill-link pill-removable";
      pill.textContent = name;
      pill.addEventListener("click", () => {
        previewId = id;
        renderList();
        renderDetails(entry || { id, name });
      });
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "pill-remove";
      remove.textContent = "x";
      remove.addEventListener("click", (event) => {
        event.stopPropagation();
        characterState.class_ids = classIds.filter((cid) => cid !== id);
        if (characterState.class_id === id) {
          characterState.class_id = characterState.class_ids[0] || "";
        }
        saveCharacterToStorage();
        renderSelectedClasses();
        renderList();
      });
      pill.appendChild(remove);
      selectedList.appendChild(pill);
    });
  };
  function renderList() {
    list.innerHTML = "";
    const filtered = classes.filter((entry) => {
      const classNode = (characterData.nodes || []).find((node) => node.id === entry.id);
      const merged = { ...entry, ...(classNode || {}) };
      if (!inContentScope(merged) && !isPlaytestEntry(merged)) return false;
      if (!query) return true;
      return String(entry.name || "").toLowerCase().includes(query);
    });
    applyDensityClass(listWrap);
    const letterMap = new Map();
    countRow.textContent = `Showing ${filtered.length} of ${classes.length} classes`;
    filtered.forEach((entry) => {
      const classNode = (characterData.nodes || []).find((node) => node.id === entry.id);
      const statusInfo = prereqStatus(classNode?.prerequisites || "", "class");
      const statusFilterValue = characterState.class_status_filter || "all";
      if (
        statusFilterValue !== "all" &&
        !(
          (statusFilterValue === "available" && statusInfo.status === "available") ||
          (statusFilterValue === "close" && statusInfo.status === "close") ||
          (statusFilterValue === "unavailable" && statusInfo.status === "unavailable") ||
          (statusFilterValue === "locked" && statusInfo.status === "blocked")
        )
      ) {
        return;
      }
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "char-class-item";
      const nameEl = document.createElement("div");
      nameEl.className = "char-class-name";
      nameEl.textContent = entry.name;
      const statusPill = document.createElement("span");
      statusPill.className = `status-pill ${statusInfo.status}`;
      statusPill.textContent =
        statusInfo.status === "available"
          ? "Available"
          : statusInfo.status === "close"
          ? "Close"
          : statusInfo.status === "blocked"
          ? "Locked"
          : "Unavailable";
      btn.appendChild(nameEl);
      btn.appendChild(statusPill);
      const tooltipBody = [classNode?.prerequisites ? `Prerequisites: ${classNode.prerequisites}` : "", classNode?.effects || ""]
        .filter(Boolean)
        .join("\n");
      _setTooltipAttrs(btn, `Class: ${entry.name}`, tooltipBody);
      btn.classList.toggle("status-available", statusInfo.status === "available");
      btn.classList.toggle("status-close", statusInfo.status === "close");
      btn.classList.toggle("status-unavailable", statusInfo.status === "unavailable");
      btn.classList.toggle("status-blocked", statusInfo.status === "blocked");
      btn.classList.toggle("is-playtest", isPlaytestEntry({ ...entry, ...(classNode || {}) }));
      if (previewId === entry.id) {
        btn.classList.add("active");
      }
      if (characterState.class_id === entry.id) {
        btn.classList.add("selected");
      }
      const letter = alphaKey(entry.name);
      if (!letterMap.has(letter)) {
        letterMap.set(letter, btn);
      }
      btn.addEventListener("click", () => {
        previewId = entry.id;
        ensurePlaytestScopeForClass(entry.name);
        renderList();
        renderDetails(entry);
      });
      list.appendChild(btn);
    });
    alpha.update(letterMap);
    if (!filtered.length) {
      const empty = document.createElement("div");
      empty.className = "char-empty";
      empty.textContent = "No classes match your search.";
      list.appendChild(empty);
    }
    if (!previewId && filtered.length) {
      previewId = filtered[0].id;
      renderDetails(filtered[0]);
    }
  }

  const renderDetails = (entry) => {
    const classNode = (characterData.nodes || []).find((node) => node.id === entry.id);
    const statusInfo = prereqStatus(classNode?.prerequisites || "", "class");
    const tiers = _classTierMap(entry) || {};
    detail.innerHTML = "";
    const header = document.createElement("div");
    header.className = "class-tree-header";
    const name = document.createElement("div");
    name.className = "class-tree-title";
    name.textContent = entry.name;
    header.appendChild(name);
    if (classNode?.prerequisites) {
      renderPrereqChecklist(classNode.prerequisites, header);
    }
    const statusPill = document.createElement("span");
    statusPill.className = `status-pill ${statusInfo.status}`;
    statusPill.textContent =
      statusInfo.status === "available"
        ? "Available"
        : statusInfo.status === "close"
        ? "Close"
        : statusInfo.status === "blocked"
        ? "Locked"
        : "Unavailable";
    header.appendChild(statusPill);
    const descText = (classNode?.effects || entry.effects || "").trim();
    _appendDetailBlock(header, "Simple Guide", _eli5ClassSummary(entry, classNode));
    if (descText) {
      const descWrap = document.createElement("div");
      descWrap.className = "char-class-desc";
      const descTitle = document.createElement("div");
      descTitle.className = "char-class-desc-title";
      descTitle.textContent = "Description";
      const descBody = document.createElement("div");
      descBody.className = "char-class-desc-body";
      descBody.textContent = descText;
      _attachKeywordTooltip(descBody, descText);
      descWrap.appendChild(descTitle);
      descWrap.appendChild(descBody);
      header.appendChild(descWrap);
    }
    if (Array.isArray(classNode?.mechanics) && classNode.mechanics.length) {
      const mechTitle = document.createElement("div");
      mechTitle.className = "class-tree-meta";
      mechTitle.textContent = "Mechanics:";
      header.appendChild(mechTitle);
      classNode.mechanics.forEach((mech) => {
        const mechBtn = document.createElement("button");
        mechBtn.type = "button";
        mechBtn.className = "char-inline-link";
        mechBtn.textContent = `${mech?.name || "Mechanic"}: ${mech?.effects || ""}`.trim();
        mechBtn.addEventListener("click", () => {
          focusClassConnections(entry.name, "extras");
        });
        header.appendChild(mechBtn);
      });
    }
    const selectRow = document.createElement("div");
    selectRow.className = "char-action-row";
    const selectBtn = document.createElement("button");
    selectBtn.type = "button";
    selectBtn.textContent = characterState.class_id === entry.id ? "Primary Class" : "Set Primary Class";
    selectBtn.disabled = characterState.class_id === entry.id;
    selectBtn.addEventListener("click", () => {
      if (characterState.class_id === entry.id) return;
      if (!characterState.override_prereqs && statusInfo.status !== "available") {
        alert(buildPrereqDetail(classNode?.prerequisites || ""));
        return;
      }
      if (!confirmChoice("Select", "Class", entry.name)) return;
      ensurePlaytestScopeForClass(entry.name);
      characterState.class_id = entry.id;
      const prereq = classNode?.prerequisites || "";
      const featureMatches = (characterData.features || []).filter((f) => {
        const pattern = _namePattern(f.name);
        return pattern ? pattern.test(prereq) : false;
      });
      const edgeMatches = (characterData.edges_catalog || []).filter((e) => {
        const pattern = _namePattern(e.name);
        return pattern ? pattern.test(prereq) : false;
      });
      const missingFeatures = featureMatches.filter((f) => !characterState.features.has(f.name));
      const missingEdges = edgeMatches.filter((e) => !characterState.edges.has(e.name));
      if (missingFeatures.length || missingEdges.length) {
        const message =
          "This class has missing prerequisites:\n" +
          (missingFeatures.length ? `Features: ${missingFeatures.map((f) => f.name).join(", ")}\n` : "") +
          (missingEdges.length ? `Edges: ${missingEdges.map((e) => e.name).join(", ")}\n` : "") +
          "Add the ones you qualify for now?";
        if (confirm(message)) {
          missingFeatures.forEach((f) => {
            if (isFeatureAllowed(f, characterState.override_prereqs)) {
              characterState.features.add(f.name);
              _addToOrder(characterState.feature_order, f.name);
            }
          });
          missingEdges.forEach((e) => {
            if (isEdgeAllowed(e, characterState.override_prereqs)) {
              characterState.edges.add(e.name);
              _addToOrder(characterState.edge_order, e.name);
            }
          });
        }
      }
      saveCharacterToStorage();
      renderList();
      renderDetails(entry);
    });
    selectRow.appendChild(selectBtn);
    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.textContent = "Add to Class List";
    const classIds = Array.isArray(characterState.class_ids) ? characterState.class_ids : [];
    const already = classIds.includes(entry.id);
    addBtn.disabled = already || classIds.length >= 4;
    addBtn.addEventListener("click", () => {
      const nextIds = Array.isArray(characterState.class_ids) ? characterState.class_ids.slice() : [];
      if (nextIds.includes(entry.id)) return;
      if (nextIds.length >= 4) {
        alert("You can select up to 4 classes.");
        return;
      }
      if (!characterState.override_prereqs && statusInfo.status !== "available") {
        alert(buildPrereqDetail(classNode?.prerequisites || ""));
        return;
      }
      nextIds.push(entry.id);
      characterState.class_ids = nextIds;
      if (!characterState.class_id) characterState.class_id = entry.id;
      saveCharacterToStorage();
      renderSelectedClasses();
      renderList();
      renderDetails(entry);
    });
    selectRow.appendChild(addBtn);
    const relatedFeatures = document.createElement("button");
    relatedFeatures.type = "button";
    relatedFeatures.textContent = "Related Features";
    relatedFeatures.addEventListener("click", () => {
      focusClassConnections(entry.name, "features");
    });
    const relatedEdges = document.createElement("button");
    relatedEdges.type = "button";
    relatedEdges.textContent = "Related Edges";
    relatedEdges.addEventListener("click", () => {
      focusClassConnections(entry.name, "edges");
    });
    const relatedExtras = document.createElement("button");
    relatedExtras.type = "button";
    relatedExtras.textContent = "Related Extras";
    relatedExtras.addEventListener("click", () => {
      focusClassConnections(entry.name, "extras");
    });
    selectRow.appendChild(relatedFeatures);
    selectRow.appendChild(relatedEdges);
    selectRow.appendChild(relatedExtras);
    header.appendChild(selectRow);
    if (statusInfo.missing.length) {
      const missing = document.createElement("div");
      missing.className = "class-tree-meta";
      missing.textContent = `Missing: ${statusInfo.missing.join(", ")}`;
      header.appendChild(missing);
      const jumpRow = document.createElement("div");
      jumpRow.className = "char-action-row";
      const toSkills = document.createElement("button");
      toSkills.textContent = "Go to Skills";
      toSkills.addEventListener("click", () => {
        goToCharacterStep("skills");
      });
      const toEdges = document.createElement("button");
      toEdges.textContent = "Go to Edges";
      toEdges.addEventListener("click", () => {
        goToCharacterStep("edges");
      });
      jumpRow.appendChild(toSkills);
      jumpRow.appendChild(toEdges);
      header.appendChild(jumpRow);
    }
    detail.appendChild(header);
    Object.keys(tiers)
      .map((k) => Number(k))
      .sort((a, b) => a - b)
      .forEach((rank) => {
        const tier = document.createElement("div");
        tier.className = "char-tier-block";
        const label = document.createElement("div");
        label.className = "char-tier-title";
        label.textContent = `Rank ${rank}`;
        tier.appendChild(label);
        const list = document.createElement("div");
        list.className = "class-tree-tier-list";
        (tiers[String(rank)] || []).forEach((nodeId) => {
          const node = (characterData.nodes || []).find((n) => n.id === nodeId);
          if (!node) return;
          const card = document.createElement("div");
          card.className = "class-tree-node";
          const label = document.createElement("button");
          label.type = "button";
          label.className = "class-tree-node-title char-inline-link";
          label.textContent = node.name;
          _setTooltipAttrs(
            label,
            `Feature: ${node.name}`,
            [node.prerequisites ? `Prerequisites: ${node.prerequisites}` : "", node.frequency || "", node.tags || "", node.effects || ""]
              .filter(Boolean)
              .join("\n")
          );
          label.addEventListener("click", () => {
            characterState.feature_search = node.name;
            goToCharacterStep("features");
          });
          card.appendChild(label);
          if (node.prerequisites) {
            renderPrereqChecklist(node.prerequisites, card);
          }
          const actions = document.createElement("div");
          actions.className = "char-action-row";
          const openBtn = document.createElement("button");
          openBtn.type = "button";
          openBtn.textContent = "Open Feature";
          openBtn.addEventListener("click", () => {
            characterState.feature_search = node.name;
            goToCharacterStep("features");
          });
          const connectionsBtn = document.createElement("button");
          connectionsBtn.type = "button";
          connectionsBtn.textContent = "Connections";
          connectionsBtn.addEventListener("click", () => {
            showConnectionsForEntry("feature", node.name);
          });
          actions.appendChild(openBtn);
          actions.appendChild(connectionsBtn);
          card.appendChild(actions);
          list.appendChild(card);
        });
        tier.appendChild(list);
        detail.appendChild(tier);
      });
  };

  search.addEventListener("input", () => {
    query = String(search.value || "").trim().toLowerCase();
    renderList();
  });
  renderSelectedClasses();
  renderList();
}

function renderCharacterFeatures() {
  charContentEl.innerHTML = "";
  charContentEl.setAttribute("data-step-target", "features");
  appendNavRow();
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Select Features";
  charContentEl.appendChild(title);
  appendStepModeToggle();

  ensurePlaytestScopeForClass(characterState.edge_class_filter);

  const hasClass = !!characterState.class_id;


  const totals = computeAdvancementTotals(
    Number(characterState.profile.level || 1),
    characterState.advancement_choices || {}
  );
  const remaining = Math.max(0, totals.features - characterState.features.size);
  const guide = document.createElement("div");
  guide.className = "char-feature-meta";
  guide.textContent = `Pick ${totals.features} features total. Remaining: ${remaining}.`;
  charContentEl.appendChild(guide);

  _renderPlannerPanel(charContentEl);
  _renderCloseUnlocks(charContentEl);

  const quickRow = document.createElement("div");
  quickRow.className = "char-action-row";
  const clearBtn = document.createElement("button");
  clearBtn.type = "button";
  clearBtn.textContent = "Clear Selected Features";
  clearBtn.addEventListener("click", () => {
    if (!confirm("Clear all selected features?")) return;
    characterState.features = new Set();
    characterState.feature_order = [];
    saveCharacterToStorage();
    renderCharacterFeatures();
  });
  quickRow.appendChild(clearBtn);
  charContentEl.appendChild(quickRow);

  const suggestionBlock = document.createElement("div");
  suggestionBlock.className = "char-summary-box";
  const suggestions = suggestEntries(
    (characterData.features || []).filter((f) => inContentScope(f)).map((f) => ({ ...f, name: f.name || "" })),
    characterState.features
  );
  if (suggestions.length) {
    suggestionBlock.textContent =
      "Suggested next picks:\n" +
      suggestions.map((item) => `- ${item.entry.name} (${item.status})`).join("\n");
  } else {
    suggestionBlock.textContent = "Suggested next picks: none yet.";
  }
  charContentEl.appendChild(suggestionBlock);
  charContentEl.appendChild(createStatusLegend());
  charContentEl.appendChild(
    createSelectedPanel("Selected Features", Array.from(characterState.features), (name) => {
      if (!confirmChoice("Remove", "Feature", name)) return;
      characterState.features.delete(name);
      _removeFromOrder(characterState.feature_order, name);
      saveCharacterToStorage();
      renderCharacterFeatures();
    })
  );

  const search = document.createElement("input");
  search.className = "char-search";
  search.placeholder = "Search features by name, tag, prerequisite, or plain-English effect...";
  search.value = characterState.feature_search || "";
  search.addEventListener("input", () => {
    characterState.feature_search = search.value;
    renderCharacterFeatures();
  });
  const searchRow = document.createElement("div");
  searchRow.className = "char-list-toolbar";
  const clearSearch = document.createElement("button");
  clearSearch.type = "button";
  clearSearch.className = "char-mini-button";
  clearSearch.textContent = "Clear";
  clearSearch.addEventListener("click", () => {
    search.value = "";
    characterState.feature_search = "";
    renderCharacterFeatures();
  });
  searchRow.appendChild(search);
  searchRow.appendChild(clearSearch);
  charContentEl.appendChild(searchRow);
  const quickFilterRow = document.createElement("div");
  quickFilterRow.className = "char-list-toolbar";
  const statusFilter = document.createElement("select");
  statusFilter.className = "item-target-select";
  ["all", "available", "close", "unavailable", "locked"].forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value === "all" ? "All Status" : value;
    statusFilter.appendChild(option);
  });
  statusFilter.value = characterState.feature_status_filter || "all";
  statusFilter.addEventListener("change", () => {
    characterState.feature_status_filter = statusFilter.value;
    renderCharacterFeatures();
  });
  const classFilter = document.createElement("select");
  classFilter.className = "item-target-select";
  const anyClass = document.createElement("option");
  anyClass.value = "";
  anyClass.textContent = "All Classes";
  classFilter.appendChild(anyClass);
  (characterData.classes || [])
    .map((cls) => cls.name)
    .sort((a, b) => String(a).localeCompare(String(b)))
    .forEach((name) => {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      classFilter.appendChild(option);
    });
  classFilter.value = characterState.feature_class_filter || "";
  classFilter.addEventListener("change", () => {
    characterState.feature_class_filter = classFilter.value;
    ensurePlaytestScopeForClass(characterState.feature_class_filter);
    renderCharacterFeatures();
  });
  const contentFilter = document.createElement("select");
  contentFilter.className = "item-target-select";
  [
    { id: "official", label: "Official Only" },
    { id: "all", label: "Official + Playtest" },
  ].forEach((opt) => {
    const option = document.createElement("option");
    option.value = opt.id;
    option.textContent = opt.label;
    if ((characterState.content_scope || "official") === opt.id) option.selected = true;
    contentFilter.appendChild(option);
  });
  contentFilter.addEventListener("change", () => {
    characterState.content_scope = contentFilter.value;
    renderCharacterFeatures();
  });
  const clearQuick = document.createElement("button");
  clearQuick.type = "button";
  clearQuick.className = "char-mini-button";
  clearQuick.textContent = "Reset Filters";
  clearQuick.addEventListener("click", () => {
    characterState.feature_class_filter = "";
    characterState.feature_tag_filter = "";
    renderCharacterFeatures();
  });
  quickFilterRow.appendChild(statusFilter);
  quickFilterRow.appendChild(classFilter);
  quickFilterRow.appendChild(contentFilter);
  quickFilterRow.appendChild(clearQuick);
  charContentEl.appendChild(quickFilterRow);
  if (characterState.feature_tag_filter) {
    const tagRow = document.createElement("div");
    tagRow.className = "char-row-meta";
    const label = document.createElement("span");
    label.textContent = `Tag filter: ${characterState.feature_tag_filter}`;
    tagRow.appendChild(label);
    const clearTag = document.createElement("button");
    clearTag.type = "button";
    clearTag.className = "char-mini-button";
    clearTag.textContent = "Clear Tag";
    clearTag.addEventListener("click", () => {
      characterState.feature_tag_filter = "";
      renderCharacterFeatures();
    });
    tagRow.appendChild(clearTag);
    charContentEl.appendChild(tagRow);
  }
  charContentEl.appendChild(createDensityToggle(renderCharacterFeatures));

  const filterRow = document.createElement("div");
  filterRow.className = "char-row-meta";
  const filterConfigs = [
    ["available", "Available", "feature_filter_available"],
    ["close", "Close", "feature_filter_close"],
    ["unavailable", "Unavailable", "feature_filter_unavailable"],
    ["blocked", "Locked", "feature_filter_blocked"],
  ];
  filterConfigs.forEach(([value, label, key]) => {
    const wrap = document.createElement("label");
    wrap.className = "char-inline-toggle";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = !!characterState[key];
    input.addEventListener("change", () => {
      characterState[key] = input.checked;
      renderCharacterFeatures();
    });
    wrap.appendChild(input);
    const text = document.createElement("span");
    text.textContent = label;
    wrap.appendChild(text);
    filterRow.appendChild(wrap);
  });
  const showAll = document.createElement("button");
  showAll.type = "button";
  showAll.textContent = "Show All";
  showAll.addEventListener("click", () => {
    characterState.feature_filter_available = true;
    characterState.feature_filter_close = true;
    characterState.feature_filter_unavailable = true;
    characterState.feature_filter_blocked = true;
    renderCharacterFeatures();
  });
  filterRow.appendChild(showAll);
  const groupSelect = document.createElement("select");
  groupSelect.className = "item-target-select";
  [
    { id: "none", label: "No Grouping" },
    { id: "skill", label: "Group by Skill" },
    { id: "tag", label: "Group by Tag" },
  ].forEach((opt) => {
    const option = document.createElement("option");
    option.value = opt.id;
    option.textContent = opt.label;
    if (characterState.feature_group_mode === opt.id) option.selected = true;
    groupSelect.appendChild(option);
  });
  groupSelect.addEventListener("change", () => {
    characterState.feature_group_mode = groupSelect.value;
    renderCharacterFeatures();
  });
  const groupWrap = document.createElement("label");
  groupWrap.className = "char-inline-toggle";
  groupWrap.appendChild(groupSelect);
  filterRow.appendChild(groupWrap);
  charContentEl.appendChild(filterRow);

  const overrideWrap = document.createElement("label");
  overrideWrap.className = "char-field";
  overrideWrap.textContent = "Override prerequisites";
  const overrideInput = document.createElement("input");
  overrideInput.type = "checkbox";
  overrideInput.checked = characterState.override_prereqs;
  overrideInput.addEventListener("change", () => {
    characterState.override_prereqs = overrideInput.checked;
    saveCharacterToStorage();
    renderCharacterFeatures();
  });
  overrideWrap.appendChild(overrideInput);
  charContentEl.appendChild(overrideWrap);

  const slotConfigTitle = document.createElement("div");
  slotConfigTitle.className = "char-section-title";
  slotConfigTitle.textContent = "Feature Slots (Configurable)";
  charContentEl.appendChild(slotConfigTitle);

  const slotsGrid = document.createElement("div");
  slotsGrid.className = "char-field-grid";
  const slotDefaults = characterData.feature_slots_by_rank || {};
  Object.keys(slotDefaults).forEach((rank) => {
    const wrap = document.createElement("label");
    wrap.className = "char-field";
    wrap.textContent = `Rank ${rank} Slots`;
    const input = document.createElement("input");
    input.type = "number";
    input.min = "0";
    const current = characterState.feature_slots_override[rank];
    input.value = current !== undefined ? String(current) : String(slotDefaults[rank]);
    input.addEventListener("input", () => {
      characterState.feature_slots_override[rank] = Number(input.value || 0);
      saveCharacterToStorage();
    });
    wrap.appendChild(input);
    slotsGrid.appendChild(wrap);
  });
  charContentEl.appendChild(slotsGrid);

  ensurePlaytestScopeForClass(characterState.feature_class_filter);
  if (hasClass) {
    const classEntry = (characterData.classes || []).find((cls) => cls.id === characterState.class_id);
    ensurePlaytestScopeForClass(classEntry?.name || "");
    const tiers = _classTierMap(classEntry) || {};
    const query = String(characterState.feature_search || "").trim().toLowerCase();
    Object.keys(tiers)
      .map((k) => Number(k))
      .sort((a, b) => a - b)
      .forEach((rank) => {
        const tier = document.createElement("div");
        tier.className = "char-tier-block";
        const label = document.createElement("div");
        label.className = "char-tier-title";
        label.textContent = `Rank ${rank} Features`;
        tier.appendChild(label);
        (tiers[String(rank)] || []).forEach((nodeId) => {
          const node = (characterData.nodes || []).find((n) => n.id === nodeId);
          if (!node) return;
          if (!inContentScope(node)) return;
          const classLabels = getFeatureClassLabels(node);
          if (characterState.feature_class_filter && !classLabels.includes(characterState.feature_class_filter)) return;
          const nodeTags = extractFeatureTags(node);
          if (characterState.feature_tag_filter && !nodeTags.includes(characterState.feature_tag_filter)) return;
          const searchText = `${node.name} ${node.tags || ""} ${node.prerequisites || ""} ${node.effects || ""}`.toLowerCase();
          if (query && !searchText.includes(query)) return;
          const statusInfo = prereqStatus(node.prerequisites, "feature");
          const allowed =
            (statusInfo.status === "available" && characterState.feature_filter_available) ||
            (statusInfo.status === "close" && characterState.feature_filter_close) ||
            (statusInfo.status === "unavailable" && characterState.feature_filter_unavailable) ||
            (statusInfo.status === "blocked" && characterState.feature_filter_blocked);
          if (!allowed) return;
          const row = document.createElement("label");
          row.className = `char-feature-row status-${statusInfo.status}`;
          const checkbox = document.createElement("input");
          checkbox.type = "checkbox";
          checkbox.checked = characterState.features.has(node.name);
          const valid = isFeatureAllowed(node, characterState.override_prereqs);
          checkbox.disabled = !valid && !checkbox.checked;
          checkbox.addEventListener("change", () => {
            const action = checkbox.checked ? "Add" : "Remove";
            if (!confirmChoice(action, "Feature", node.name)) {
              checkbox.checked = !checkbox.checked;
              return;
            }
            if (checkbox.checked && !isFeatureAllowed(node, characterState.override_prereqs)) {
              alert(buildPrereqDetail(node.prerequisites || ""));
              checkbox.checked = false;
              return;
            }
            if (checkbox.checked) {
              characterState.features.add(node.name);
              _addToOrder(characterState.feature_order, node.name);
            } else {
              characterState.features.delete(node.name);
              _removeFromOrder(characterState.feature_order, node.name);
            }
            saveCharacterToStorage();
            renderCharacterFeatures();
          });
          const body = document.createElement("div");
          const title = document.createElement("div");
          title.className = "class-tree-node-title";
          title.textContent = node.name;
          _setTooltipAttrs(
            title,
            `Feature: ${node.name}`,
            [node.prerequisites ? `Prerequisites: ${node.prerequisites}` : "", node.frequency || "", node.tags || "", node.effects || ""]
              .filter(Boolean)
              .join("\n")
          );
          const statusPill = document.createElement("span");
          statusPill.className = `status-pill ${statusInfo.status}`;
          statusPill.textContent =
            statusInfo.status === "available"
              ? "Available"
              : statusInfo.status === "close"
              ? "Close"
              : statusInfo.status === "blocked"
              ? "Locked"
              : "Unavailable";
          const meta = document.createElement("div");
          meta.className = "char-row-meta";
          meta.textContent = [node.frequency, node.tags].filter(Boolean).join(" | ");
          const effects = document.createElement("div");
          effects.className = "char-feature-meta";
          effects.textContent = node.effects || "";
          _attachKeywordTooltip(effects, effects.textContent);
          const summary = document.createElement("div");
          summary.className = "char-feature-meta";
          summary.textContent = _eli5FeatureSummary(node);
          const badgeRow = document.createElement("div");
          badgeRow.className = "char-tag-row";
          classLabels.forEach((labelText) => {
            badgeRow.appendChild(
              makeFilterChip(`Class: ${labelText}`, () => {
                characterState.feature_class_filter = labelText;
                renderCharacterFeatures();
              })
            );
          });
          nodeTags
            .filter((tagText) => String(tagText || "").trim().toLowerCase() !== "class")
            .forEach((tagText) => {
              badgeRow.appendChild(
                makeFilterChip(`#${tagText}`, () => {
                  characterState.feature_tag_filter = tagText;
                  renderCharacterFeatures();
                })
              );
            });
          body.appendChild(title);
          body.appendChild(statusPill);
          if (meta.textContent) body.appendChild(meta);
          body.appendChild(summary);
          if (badgeRow.childNodes.length) body.appendChild(badgeRow);
          if (node.prerequisites) {
            renderPrereqChecklist(node.prerequisites, body);
          }
          if (statusInfo.missing.length) {
            const missing = document.createElement("div");
            missing.className = "char-feature-meta";
            missing.textContent = `Missing: ${statusInfo.missing.join(", ")}`;
            body.appendChild(missing);
          }
          if (effects.textContent) body.appendChild(effects);
          row.appendChild(checkbox);
          row.appendChild(body);
          tier.appendChild(row);
        });
        charContentEl.appendChild(tier);
      });
  }

  const extraTitle = document.createElement("div");
  extraTitle.className = "char-section-title";
  extraTitle.textContent = "All Features";
  charContentEl.appendChild(extraTitle);
  const listPanel = document.createElement("div");
  listPanel.className = "char-list-panel";
  const countRow = document.createElement("div");
  countRow.className = "char-count";
  const alpha = createAlphaIndex();
  const list = document.createElement("div");
  list.className = "char-entry-list";
  listPanel.appendChild(countRow);
  listPanel.appendChild(alpha.element);
  listPanel.appendChild(list);
  charContentEl.appendChild(listPanel);
  const allFeatures = (characterData.features || []).slice().sort((a, b) => a.name.localeCompare(b.name));
  const renderList = () => {
    list.innerHTML = "";
    let visibleCount = 0;
    const letterMap = new Map();
    applyDensityClass(listPanel);
    const query = String(characterState.feature_search || "").trim().toLowerCase();
    const filtered = query
      ? allFeatures.filter((entry) => {
          const text = `${entry.name} ${entry.tags || ""} ${entry.prerequisites || ""} ${entry.effects || ""}`;
          return _searchMatchScore(text, query) > 0;
        })
      : allFeatures;
    const groupMode = characterState.feature_group_mode;
    const groups = new Map();
    const addToGroup = (key, entry) => {
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(entry);
    };
    filtered.forEach((entry) => {
      if (!inContentScope(entry)) return;
      const classLabels = getFeatureClassLabels(entry);
      if (characterState.feature_class_filter && !classLabels.includes(characterState.feature_class_filter)) return;
      const tags = extractFeatureTags(entry);
      if (characterState.feature_tag_filter && !tags.includes(characterState.feature_tag_filter)) return;
      const statusInfo = prereqStatus(entry.prerequisites, "feature");
      const statusFilter = characterState.feature_status_filter || "all";
      if (
        statusFilter !== "all" &&
        !(
          (statusFilter === "available" && statusInfo.status === "available") ||
          (statusFilter === "close" && statusInfo.status === "close") ||
          (statusFilter === "unavailable" && statusInfo.status === "unavailable") ||
          (statusFilter === "locked" && statusInfo.status === "blocked")
        )
      ) {
        return;
      }
      const allowed =
        (statusInfo.status === "available" && characterState.feature_filter_available) ||
        (statusInfo.status === "close" && characterState.feature_filter_close) ||
        (statusInfo.status === "unavailable" && characterState.feature_filter_unavailable) ||
        (statusInfo.status === "blocked" && characterState.feature_filter_blocked);
      if (!allowed) return;
      if (groupMode === "skill") {
        const skills = extractPrereqSkills(entry.prerequisites || "");
        if (!skills.length) {
          addToGroup("No Skill", entry);
        } else {
          skills.forEach((skill) => addToGroup(skill, entry));
        }
      } else if (groupMode === "tag") {
        const tags = extractFeatureTags(entry);
        if (!tags.length) {
          addToGroup("No Tag", entry);
        } else {
          tags.forEach((tag) => addToGroup(tag, entry));
        }
      } else {
        addToGroup("All", entry);
      }
    });
    const renderEntry = (entry) => {
      const statusInfo = prereqStatus(entry.prerequisites, "feature");
      const row = document.createElement("label");
      row.className = `char-feature-row status-${statusInfo.status}`;
      if (_isRelatedPrereq(entry.prerequisites)) {
        row.classList.add("is-related");
      }
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = characterState.features.has(entry.name);
      const valid = isFeatureAllowed(entry, characterState.override_prereqs);
      checkbox.disabled = !valid && !checkbox.checked;
      checkbox.addEventListener("change", () => {
        const action = checkbox.checked ? "Add" : "Remove";
        if (!confirmChoice(action, "Feature", entry.name)) {
          checkbox.checked = !checkbox.checked;
          return;
        }
        if (checkbox.checked && !isFeatureAllowed(entry, characterState.override_prereqs)) {
          alert(buildPrereqDetail(entry.prerequisites || ""));
          checkbox.checked = false;
          return;
        }
        if (checkbox.checked) {
          characterState.features.add(entry.name);
          _addToOrder(characterState.feature_order, entry.name);
        } else {
          characterState.features.delete(entry.name);
          _removeFromOrder(characterState.feature_order, entry.name);
        }
        saveCharacterToStorage();
        renderCharacterFeatures();
      });
      const body = document.createElement("div");
      const title = document.createElement("div");
      title.className = "class-tree-node-title";
      title.textContent = entry.name;
      const statusPill = document.createElement("span");
      statusPill.className = `status-pill ${statusInfo.status}`;
      statusPill.textContent =
        statusInfo.status === "available"
          ? "Available"
          : statusInfo.status === "close"
          ? "Close"
          : statusInfo.status === "blocked"
          ? "Locked"
          : "Unavailable";
      const meta = document.createElement("div");
      meta.className = "char-row-meta";
      meta.textContent = [entry.tags].filter(Boolean).join(" | ");
      const effects = document.createElement("div");
      effects.className = "char-feature-meta";
      effects.textContent = entry.effects || "";
      _attachKeywordTooltip(effects, effects.textContent);
      const summary = document.createElement("div");
      summary.className = "char-feature-meta";
      summary.textContent = _eli5FeatureSummary(entry);
      const classLabels = getFeatureClassLabels(entry);
      const tags = extractFeatureTags(entry);
      const badgeRow = document.createElement("div");
      badgeRow.className = "char-tag-row";
      classLabels.forEach((labelText) => {
        badgeRow.appendChild(
          makeFilterChip(`Class: ${labelText}`, () => {
            characterState.feature_class_filter = labelText;
            renderCharacterFeatures();
          })
        );
      });
      tags
        .filter((tagText) => String(tagText || "").trim().toLowerCase() !== "class")
        .forEach((tagText) => {
          badgeRow.appendChild(
            makeFilterChip(`#${tagText}`, () => {
              characterState.feature_tag_filter = tagText;
              renderCharacterFeatures();
            })
          );
        });
      badgeRow.appendChild(
        makeFilterChip("Connections", () => showConnectionsForEntry("feature", entry.name))
      );
      body.appendChild(title);
      body.appendChild(statusPill);
      if (meta.textContent) body.appendChild(meta);
      body.appendChild(summary);
      if (badgeRow.childNodes.length) body.appendChild(badgeRow);
      if (entry.prerequisites) {
        renderPrereqChecklist(entry.prerequisites, body);
      }
      if (statusInfo.missing.length) {
        const missing = document.createElement("div");
        missing.className = "char-feature-meta";
        missing.textContent = `Missing: ${statusInfo.missing.join(", ")}`;
        body.appendChild(missing);
      }
      if (effects.textContent) body.appendChild(effects);
      row.appendChild(checkbox);
      row.appendChild(body);
      const letter = alphaKey(entry.name);
      if (!letterMap.has(letter)) {
        letterMap.set(letter, row);
      }
      visibleCount += 1;
      return row;
    };
    Array.from(groups.keys())
      .sort((a, b) => String(a).localeCompare(String(b)))
      .forEach((key) => {
        if (groupMode !== "none" && key !== "All") {
          const groupTitle = document.createElement("div");
          groupTitle.className = "char-tier-title";
          groupTitle.textContent = key;
          list.appendChild(groupTitle);
        }
        (groups.get(key) || []).forEach((entry) => {
          list.appendChild(renderEntry(entry));
        });
      });
    countRow.textContent = `Showing ${visibleCount} of ${allFeatures.length} features`;
    alpha.update(letterMap);
    if (!visibleCount) {
      const empty = document.createElement("div");
      empty.className = "char-empty";
      empty.textContent = "No features match your search/filters.";
      list.appendChild(empty);
    }
  };
  renderList();
}

function renderCharacterEdges() {
  charContentEl.innerHTML = "";
  charContentEl.setAttribute("data-step-target", "edges");
  appendNavRow();
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Select Edges";
  charContentEl.appendChild(title);
  appendStepModeToggle();

  ensurePlaytestScopeForClass(characterState.edge_class_filter);

  const totals = computeAdvancementTotals(Number(characterState.profile.level || 1), characterState.advancement_choices || {});
  const remaining = Math.max(0, totals.edges - characterState.edges.size);
  const guide = document.createElement("div");
  guide.className = "char-feature-meta";
  guide.textContent = `Pick ${totals.edges} edges total. Remaining: ${remaining}.`;
  charContentEl.appendChild(guide);

  _renderPlannerPanel(charContentEl);
  _renderCloseUnlocks(charContentEl);

  const quickRow = document.createElement("div");
  quickRow.className = "char-action-row";
  const clearBtn = document.createElement("button");
  clearBtn.type = "button";
  clearBtn.textContent = "Clear Selected Edges";
  clearBtn.addEventListener("click", () => {
    if (!confirm("Clear all selected edges?")) return;
    characterState.edges = new Set();
    characterState.edge_order = [];
    saveCharacterToStorage();
    renderCharacterEdges();
  });
  quickRow.appendChild(clearBtn);
  charContentEl.appendChild(quickRow);

  const suggestionBlock = document.createElement("div");
  suggestionBlock.className = "char-summary-box";
  const suggestions = suggestEntries(
    (characterData.edges_catalog || []).filter((e) => inContentScope(e)).map((e) => ({ ...e, name: e.name || "" })),
    characterState.edges
  );
  if (suggestions.length) {
    suggestionBlock.textContent =
      "Suggested next picks:\n" +
      suggestions.map((item) => `- ${item.entry.name} (${item.status})`).join("\n");
  } else {
    suggestionBlock.textContent = "Suggested next picks: none yet.";
  }
  charContentEl.appendChild(suggestionBlock);
  charContentEl.appendChild(createStatusLegend());
  charContentEl.appendChild(
    createSelectedPanel("Selected Edges", Array.from(characterState.edges), (name) => {
      if (!confirmChoice("Remove", "Edge", name)) return;
      characterState.edges.delete(name);
      _removeFromOrder(characterState.edge_order, name);
      saveCharacterToStorage();
      renderCharacterEdges();
    })
  );

  const overrideWrap = document.createElement("label");
  overrideWrap.className = "char-field";
  overrideWrap.textContent = "Override prerequisites";
  const overrideInput = document.createElement("input");
  overrideInput.type = "checkbox";
  overrideInput.checked = characterState.override_prereqs;
  overrideInput.addEventListener("change", () => {
    characterState.override_prereqs = overrideInput.checked;
    saveCharacterToStorage();
    renderCharacterEdges();
  });
  overrideWrap.appendChild(overrideInput);
  charContentEl.appendChild(overrideWrap);
  const search = document.createElement("input");
  search.className = "char-search";
  search.placeholder = "Search edges by name, prerequisite, class, or plain-English effect...";
  search.value = characterState.edge_search || "";
  search.addEventListener("input", () => {
    characterState.edge_search = search.value;
    renderCharacterEdges();
  });
  const searchRow = document.createElement("div");
  searchRow.className = "char-list-toolbar";
  const clearSearch = document.createElement("button");
  clearSearch.type = "button";
  clearSearch.className = "char-mini-button";
  clearSearch.textContent = "Clear";
  clearSearch.addEventListener("click", () => {
    search.value = "";
    characterState.edge_search = "";
    renderCharacterEdges();
  });
  searchRow.appendChild(search);
  searchRow.appendChild(clearSearch);
  charContentEl.appendChild(searchRow);
  const quickFilterRow = document.createElement("div");
  quickFilterRow.className = "char-list-toolbar";
  const statusFilter = document.createElement("select");
  statusFilter.className = "item-target-select";
  ["all", "available", "close", "unavailable", "locked"].forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value === "all" ? "All Status" : value;
    statusFilter.appendChild(option);
  });
  statusFilter.value = characterState.edge_status_filter || "all";
  statusFilter.addEventListener("change", () => {
    characterState.edge_status_filter = statusFilter.value;
    renderCharacterEdges();
  });
  const classFilter = document.createElement("select");
  classFilter.className = "item-target-select";
  const anyClass = document.createElement("option");
  anyClass.value = "";
  anyClass.textContent = "All Classes";
  classFilter.appendChild(anyClass);
  (characterData.classes || [])
    .map((cls) => cls.name)
    .sort((a, b) => String(a).localeCompare(String(b)))
    .forEach((name) => {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      classFilter.appendChild(option);
    });
  classFilter.value = characterState.edge_class_filter || "";
  classFilter.addEventListener("change", () => {
    characterState.edge_class_filter = classFilter.value;
    ensurePlaytestScopeForClass(characterState.edge_class_filter);
    renderCharacterEdges();
  });
  const contentFilter = document.createElement("select");
  contentFilter.className = "item-target-select";
  [
    { id: "official", label: "Official Only" },
    { id: "all", label: "Official + Playtest" },
  ].forEach((opt) => {
    const option = document.createElement("option");
    option.value = opt.id;
    option.textContent = opt.label;
    if ((characterState.content_scope || "official") === opt.id) option.selected = true;
    contentFilter.appendChild(option);
  });
  contentFilter.addEventListener("change", () => {
    characterState.content_scope = contentFilter.value;
    renderCharacterEdges();
  });
  quickFilterRow.appendChild(statusFilter);
  quickFilterRow.appendChild(classFilter);
  quickFilterRow.appendChild(contentFilter);
  charContentEl.appendChild(quickFilterRow);
  const filterRow = document.createElement("div");
  filterRow.className = "char-row-meta";
  const filterConfigs = [
    ["available", "Available", "edge_filter_available"],
    ["close", "Close", "edge_filter_close"],
    ["unavailable", "Unavailable", "edge_filter_unavailable"],
    ["blocked", "Locked", "edge_filter_blocked"],
  ];
  filterConfigs.forEach(([value, label, key]) => {
    const wrap = document.createElement("label");
    wrap.className = "char-inline-toggle";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = !!characterState[key];
    input.addEventListener("change", () => {
      characterState[key] = input.checked;
      renderCharacterEdges();
    });
    wrap.appendChild(input);
    const text = document.createElement("span");
    text.textContent = label;
    wrap.appendChild(text);
    filterRow.appendChild(wrap);
  });
  const showAll = document.createElement("button");
  showAll.type = "button";
  showAll.textContent = "Show All";
  showAll.addEventListener("click", () => {
    characterState.edge_filter_available = true;
    characterState.edge_filter_close = true;
    characterState.edge_filter_unavailable = true;
    characterState.edge_filter_blocked = true;
    renderCharacterEdges();
  });
  filterRow.appendChild(showAll);
  const groupSelect = document.createElement("select");
  groupSelect.className = "item-target-select";
  [
    { id: "none", label: "No Grouping" },
    { id: "skill", label: "Group by Skill" },
  ].forEach((opt) => {
    const option = document.createElement("option");
    option.value = opt.id;
    option.textContent = opt.label;
    if (characterState.edge_group_mode === opt.id) option.selected = true;
    groupSelect.appendChild(option);
  });
  groupSelect.addEventListener("change", () => {
    characterState.edge_group_mode = groupSelect.value;
    renderCharacterEdges();
  });
  const groupWrap = document.createElement("label");
  groupWrap.className = "char-inline-toggle";
  groupWrap.appendChild(groupSelect);
  filterRow.appendChild(groupWrap);
  charContentEl.appendChild(filterRow);
  const list = document.createElement("div");
  const listPanel = document.createElement("div");
  listPanel.className = "char-list-panel";
  const countRow = document.createElement("div");
  countRow.className = "char-count";
  const alpha = createAlphaIndex();
  listPanel.appendChild(countRow);
  listPanel.appendChild(alpha.element);
  listPanel.appendChild(list);
  charContentEl.appendChild(listPanel);
  charContentEl.appendChild(createDensityToggle(renderCharacterEdges));
  const edges = (characterData.edges_catalog || []).slice().sort((a, b) => a.name.localeCompare(b.name));
  const renderList = () => {
    list.innerHTML = "";
    let visibleCount = 0;
    const letterMap = new Map();
    applyDensityClass(listPanel);
    const query = String(characterState.edge_search || "").trim().toLowerCase();
  const filtered = query
    ? edges.filter((entry) => {
        const text = `${entry.name} ${entry.prerequisites || ""} ${entry.effects || ""}`;
        return _searchMatchScore(text, query) > 0;
      })
    : edges;
    const groupMode = characterState.edge_group_mode;
    const groups = new Map();
    const addToGroup = (key, entry) => {
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(entry);
    };
    filtered.forEach((entry) => {
      if (!inContentScope(entry)) return;
      const classLabels = getEdgeClassLabels(entry);
      if (characterState.edge_class_filter && !classLabels.includes(characterState.edge_class_filter)) return;
      const statusInfo = prereqStatus(entry.prerequisites, "edge");
      const statusFilter = characterState.edge_status_filter || "all";
      if (
        statusFilter !== "all" &&
        !(
          (statusFilter === "available" && statusInfo.status === "available") ||
          (statusFilter === "close" && statusInfo.status === "close") ||
          (statusFilter === "unavailable" && statusInfo.status === "unavailable") ||
          (statusFilter === "locked" && statusInfo.status === "blocked")
        )
      ) {
        return;
      }
      const allowed =
        (statusInfo.status === "available" && characterState.edge_filter_available) ||
        (statusInfo.status === "close" && characterState.edge_filter_close) ||
        (statusInfo.status === "unavailable" && characterState.edge_filter_unavailable) ||
        (statusInfo.status === "blocked" && characterState.edge_filter_blocked);
      if (!allowed) return;
      if (groupMode === "skill") {
        const skills = extractPrereqSkills(entry.prerequisites || "");
        if (!skills.length) {
          addToGroup("No Skill", entry);
        } else {
          skills.forEach((skill) => addToGroup(skill, entry));
        }
      } else {
        addToGroup("All", entry);
      }
    });
    const renderEntry = (entry) => {
      const statusInfo = prereqStatus(entry.prerequisites, "edge");
      const row = document.createElement("label");
      row.className = `char-edge-row status-${statusInfo.status}`;
      if (_isRelatedPrereq(entry.prerequisites)) {
        row.classList.add("is-related");
      }
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = characterState.edges.has(entry.name);
      const valid = isEdgeAllowed(entry, characterState.override_prereqs);
      checkbox.disabled = !valid && !checkbox.checked;
      checkbox.addEventListener("change", () => {
        const action = checkbox.checked ? "Add" : "Remove";
        if (!confirmChoice(action, "Edge", entry.name)) {
          checkbox.checked = !checkbox.checked;
          return;
        }
        if (checkbox.checked && !isEdgeAllowed(entry, characterState.override_prereqs)) {
          alert(buildPrereqDetail(entry.prerequisites || ""));
          checkbox.checked = false;
          return;
        }
        if (checkbox.checked) {
          characterState.edges.add(entry.name);
          _addToOrder(characterState.edge_order, entry.name);
        } else {
          characterState.edges.delete(entry.name);
          _removeFromOrder(characterState.edge_order, entry.name);
        }
        saveCharacterToStorage();
        renderCharacterEdges();
      });
      const body = document.createElement("div");
      const title = document.createElement("div");
      title.className = "class-tree-node-title";
      title.textContent = entry.name;
      const statusPill = document.createElement("span");
      statusPill.className = `status-pill ${statusInfo.status}`;
      statusPill.textContent =
        statusInfo.status === "available"
          ? "Available"
          : statusInfo.status === "close"
          ? "Close"
          : statusInfo.status === "blocked"
          ? "Locked"
          : "Unavailable";
      const meta = document.createElement("div");
      meta.className = "char-row-meta";
      meta.textContent = entry.tags || "";
      const effects = document.createElement("div");
      effects.className = "char-edge-meta";
      effects.textContent = entry.effects || "";
      _attachKeywordTooltip(effects, effects.textContent);
      const summary = document.createElement("div");
      summary.className = "char-edge-meta";
      summary.textContent = _eli5EdgeSummary(entry);
      const classLabels = getEdgeClassLabels(entry);
      const badgeRow = document.createElement("div");
      badgeRow.className = "char-tag-row";
      classLabels.forEach((labelText) => {
        badgeRow.appendChild(
          makeFilterChip(`Class: ${labelText}`, () => {
            characterState.edge_class_filter = labelText;
            renderCharacterEdges();
          })
        );
      });
      badgeRow.appendChild(makeFilterChip("Connections", () => showConnectionsForEntry("edge", entry.name)));
      body.appendChild(title);
      body.appendChild(statusPill);
      if (meta.textContent) body.appendChild(meta);
      body.appendChild(summary);
      if (badgeRow.childNodes.length) body.appendChild(badgeRow);
      if (entry.prerequisites) {
        renderPrereqChecklist(entry.prerequisites, body);
      }
      if (statusInfo.missing.length) {
        const missing = document.createElement("div");
        missing.className = "char-edge-meta";
        missing.textContent = `Missing: ${statusInfo.missing.join(", ")}`;
        body.appendChild(missing);
      }
      if (effects.textContent) body.appendChild(effects);
      row.appendChild(checkbox);
      row.appendChild(body);
      const letter = alphaKey(entry.name);
      if (!letterMap.has(letter)) {
        letterMap.set(letter, row);
      }
      visibleCount += 1;
      return row;
    };
    Array.from(groups.keys())
      .sort((a, b) => String(a).localeCompare(String(b)))
      .forEach((key) => {
        if (groupMode !== "none" && key !== "All") {
          const groupTitle = document.createElement("div");
          groupTitle.className = "char-tier-title";
          groupTitle.textContent = key;
          list.appendChild(groupTitle);
        }
        (groups.get(key) || []).forEach((entry) => {
          list.appendChild(renderEntry(entry));
        });
      });
    countRow.textContent = `Showing ${visibleCount} of ${edges.length} edges`;
    alpha.update(letterMap);
    if (!visibleCount) {
      const empty = document.createElement("div");
      empty.className = "char-empty";
      empty.textContent = "No edges match your search/filters.";
      list.appendChild(empty);
    }
  };
  renderList();
}

function renderCharacterPokeEdges() {
  charContentEl.innerHTML = "";
  charContentEl.setAttribute("data-step-target", "poke-edges");
  appendNavRow();
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Poke Edges";
  charContentEl.appendChild(title);
  appendStepModeToggle();

  _renderPlannerPanel(charContentEl);

  const guide = document.createElement("div");
  guide.className = "char-feature-meta";
  guide.textContent = `Optional: assign Poke Edges to your Pokemon. Selected: ${characterState.poke_edges.size}.`;
  charContentEl.appendChild(guide);
  if (window.PTUCharacterState?.ensureOrderedSet) {
    window.PTUCharacterState.ensureOrderedSet(characterState, "poke_edges", "poke_edge_order");
  }

  charContentEl.appendChild(createStatusLegend());
  charContentEl.appendChild(
    createSelectedPanel("Selected Poke Edges", characterState.poke_edge_order?.length ? characterState.poke_edge_order : Array.from(characterState.poke_edges), (name) => {
      if (!confirmChoice("Remove", "Poke Edge", name)) return;
      if (window.PTUCharacterState?.removeOrdered) {
        window.PTUCharacterState.removeOrdered(characterState, "poke_edges", "poke_edge_order", name);
      } else {
        characterState.poke_edges.delete(name);
      }
      saveCharacterToStorage();
      renderCharacterPokeEdges();
    })
  );

  const overrideWrap = document.createElement("label");
  overrideWrap.className = "char-field";
  overrideWrap.textContent = "Override prerequisites";
  const overrideInput = document.createElement("input");
  overrideInput.type = "checkbox";
  overrideInput.checked = characterState.override_prereqs;
  overrideInput.addEventListener("change", () => {
    characterState.override_prereqs = overrideInput.checked;
    saveCharacterToStorage();
    renderCharacterPokeEdges();
  });
  overrideWrap.appendChild(overrideInput);
  charContentEl.appendChild(overrideWrap);

  const search = document.createElement("input");
  search.className = "char-search";
  search.placeholder = "Search Poke Edges by name, prerequisite, cost, or plain-English effect...";
  search.value = characterState.poke_edge_search || "";
  search.addEventListener("input", () => {
    const start = search.selectionStart;
    const end = search.selectionEnd;
    characterState.poke_edge_search = search.value;
    renderList();
    if (document.activeElement !== search) {
      requestAnimationFrame(() => {
        search.focus();
        if (start !== null && end !== null) {
          search.setSelectionRange(start, end);
        }
      });
    }
  });
  const searchRow = document.createElement("div");
  searchRow.className = "char-list-toolbar";
  const clearSearch = document.createElement("button");
  clearSearch.type = "button";
  clearSearch.className = "char-mini-button";
  clearSearch.textContent = "Clear";
  clearSearch.addEventListener("click", () => {
    search.value = "";
    characterState.poke_edge_search = "";
    renderList();
    search.focus();
  });
  searchRow.appendChild(search);
  searchRow.appendChild(clearSearch);
  charContentEl.appendChild(searchRow);

  const filterRow = document.createElement("div");
  filterRow.className = "char-row-meta";
  const filterConfigs = [
    ["available", "Available", "poke_edge_filter_available"],
    ["close", "Close", "poke_edge_filter_close"],
    ["unavailable", "Unavailable", "poke_edge_filter_unavailable"],
    ["blocked", "Locked", "poke_edge_filter_blocked"],
  ];
  filterConfigs.forEach(([value, label, key]) => {
    const wrap = document.createElement("label");
    wrap.className = "char-inline-toggle";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = !!characterState[key];
    input.addEventListener("change", () => {
      characterState[key] = input.checked;
      renderCharacterPokeEdges();
    });
    wrap.appendChild(input);
    const text = document.createElement("span");
    text.textContent = label;
    wrap.appendChild(text);
    filterRow.appendChild(wrap);
  });
  const showAll = document.createElement("button");
  showAll.type = "button";
  showAll.textContent = "Show All";
  showAll.addEventListener("click", () => {
    characterState.poke_edge_filter_available = true;
    characterState.poke_edge_filter_close = true;
    characterState.poke_edge_filter_unavailable = true;
    characterState.poke_edge_filter_blocked = true;
    renderCharacterPokeEdges();
  });
  filterRow.appendChild(showAll);
  charContentEl.appendChild(filterRow);

  const list = document.createElement("div");
  const listPanel = document.createElement("div");
  listPanel.className = "char-list-panel";
  const countRow = document.createElement("div");
  countRow.className = "char-count";
  const alpha = createAlphaIndex();
  listPanel.appendChild(countRow);
  listPanel.appendChild(alpha.element);
  listPanel.appendChild(list);
  charContentEl.appendChild(listPanel);
  charContentEl.appendChild(createDensityToggle(renderCharacterPokeEdges));

  const edges = (characterData.poke_edges_catalog || []).slice().sort((a, b) => a.name.localeCompare(b.name));
  let ghostDropReason = "";
  const evaluatePokeEdgeByName = (name) => {
    const entry = edges.find((item) => String(item?.name || "") === String(name || ""));
    if (!entry) {
      return { status: "unavailable", reason: "Edge not found in catalog.", missing: ["Edge not found"] };
    }
    const evalResult = window.PTUPrereqEval?.evaluatePrereq
      ? window.PTUPrereqEval.evaluatePrereq(entry, "edge", {
          prereqStatus,
          isAllowed: (candidate) => isEdgeAllowed(candidate, characterState.override_prereqs),
        })
      : { status: "available", reason: "", missing: [] };
    return evalResult;
  };
  const renderList = () => {
    list.innerHTML = "";
    let visibleCount = 0;
    const letterMap = new Map();
    applyDensityClass(listPanel);
    const query = String(characterState.poke_edge_search || "").trim().toLowerCase();
    const filtered = query
      ? edges.filter((entry) => {
          const text = `${entry.name} ${entry.prerequisites || ""} ${entry.effects || ""} ${entry.cost || ""}`;
          return _searchMatchScore(text, query) > 0;
        })
      : edges;
    filtered.forEach((entry) => {
      const statusInfo = prereqStatus(entry.prerequisites, "edge");
      const allowed =
        (statusInfo.status === "available" && characterState.poke_edge_filter_available) ||
        (statusInfo.status === "close" && characterState.poke_edge_filter_close) ||
        (statusInfo.status === "unavailable" && characterState.poke_edge_filter_unavailable) ||
        (statusInfo.status === "blocked" && characterState.poke_edge_filter_blocked);
      if (!allowed) return;
      const row = document.createElement("label");
      row.className = `char-edge-row status-${statusInfo.status}`;
      if (_isRelatedPrereq(entry.prerequisites)) {
        row.classList.add("is-related");
      }
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = characterState.poke_edges.has(entry.name);
      const valid = isEdgeAllowed(entry, characterState.override_prereqs);
      checkbox.disabled = !valid && !checkbox.checked;
      checkbox.addEventListener("change", () => {
        const action = checkbox.checked ? "Add" : "Remove";
        if (!confirmChoice(action, "Poke Edge", entry.name)) {
          checkbox.checked = !checkbox.checked;
          return;
        }
        if (checkbox.checked && !isEdgeAllowed(entry, characterState.override_prereqs)) {
          alert(buildPrereqDetail(entry.prerequisites || ""));
          checkbox.checked = false;
          return;
        }
        if (checkbox.checked) {
          if (window.PTUCharacterState?.addOrdered) {
            window.PTUCharacterState.addOrdered(characterState, "poke_edges", "poke_edge_order", entry.name);
          } else {
            characterState.poke_edges.add(entry.name);
          }
        } else {
          if (window.PTUCharacterState?.removeOrdered) {
            window.PTUCharacterState.removeOrdered(characterState, "poke_edges", "poke_edge_order", entry.name);
          } else {
            characterState.poke_edges.delete(entry.name);
          }
        }
        saveCharacterToStorage();
        renderCharacterPokeEdges();
      });
      const body = document.createElement("div");
      const title = document.createElement("div");
      title.className = "class-tree-node-title";
      title.textContent = entry.name;
      _setTooltipAttrs(
        title,
        `Poke Edge: ${entry.name}`,
        [
          entry.prerequisites ? `Prerequisites: ${entry.prerequisites}` : "",
          _formatCostLabel(entry.cost),
          entry.effects || "",
        ]
          .filter(Boolean)
          .join("\n")
      );
      const statusPill = document.createElement("span");
      statusPill.className = `status-pill ${statusInfo.status}`;
      statusPill.textContent =
        statusInfo.status === "available"
          ? "Available"
          : statusInfo.status === "close"
          ? "Close"
          : statusInfo.status === "blocked"
          ? "Locked"
          : "Unavailable";
      const meta = document.createElement("div");
      meta.className = "char-row-meta";
      meta.textContent = _formatCostLabel(entry.cost);
      const effects = document.createElement("div");
      effects.className = "char-edge-meta";
      effects.textContent = entry.effects || "";
      _attachKeywordTooltip(effects, effects.textContent);
      const summary = document.createElement("div");
      summary.className = "char-edge-meta";
      summary.textContent = _eli5EdgeSummary(entry, { forPokemon: true });
      body.appendChild(title);
      body.appendChild(statusPill);
      if (meta.textContent) body.appendChild(meta);
      body.appendChild(summary);
      if (entry.prerequisites) {
        renderPrereqChecklist(entry.prerequisites, body);
      }
      if (statusInfo.missing.length) {
        const missing = document.createElement("div");
        missing.className = "char-edge-meta";
        missing.textContent = `Missing: ${statusInfo.missing.join(", ")}`;
        body.appendChild(missing);
      }
      if (effects.textContent) body.appendChild(effects);
      row.appendChild(checkbox);
      row.appendChild(body);
      const letter = alphaKey(entry.name);
      if (!letterMap.has(letter)) {
        letterMap.set(letter, row);
      }
      visibleCount += 1;
      list.appendChild(row);
    });
    countRow.textContent = `Showing ${visibleCount} of ${edges.length} Poke Edges`;
    alpha.update(letterMap);
    if (!visibleCount) {
      const empty = document.createElement("div");
      empty.className = "char-empty";
      empty.textContent = "No Poke Edges match your search or filters.";
      list.appendChild(empty);
    }
  };
  const board = window.PTUBuilderUI?.renderPokeEdgeBoard
    ? window.PTUBuilderUI.renderPokeEdgeBoard({
        edges,
        selected: (characterState.poke_edge_order || []).slice(),
        evaluate: evaluatePokeEdgeByName,
        sortableEnabled: _sortableEnabled(),
        registerSortable: _registerSortable,
        ghostReason: ghostDropReason,
        setGhostReason: (reason) => {
          ghostDropReason = String(reason || "");
        },
        notify: (reason) => _toastDrop(reason),
        onAdd: (name) => {
          const value = String(name || "").trim();
          if (!value) return false;
          if (characterState.poke_edges.has(value)) return false;
          const evalResult = evaluatePokeEdgeByName(value);
          if (evalResult.reason && !characterState.override_prereqs) {
            _toastDrop(evalResult.reason);
            return false;
          }
          if (window.PTUCharacterState?.addOrdered) {
            window.PTUCharacterState.addOrdered(characterState, "poke_edges", "poke_edge_order", value);
          } else {
            characterState.poke_edges.add(value);
          }
          saveCharacterToStorage();
          renderCharacterPokeEdges();
          return true;
        },
        onRemove: (name) => {
          if (window.PTUCharacterState?.removeOrdered) {
            window.PTUCharacterState.removeOrdered(characterState, "poke_edges", "poke_edge_order", name);
          } else {
            characterState.poke_edges.delete(name);
          }
          saveCharacterToStorage();
          renderCharacterPokeEdges();
        },
        onReorder: (nextOrder) => {
          if (window.PTUCharacterState?.reorder) {
            window.PTUCharacterState.reorder(characterState, "poke_edges", "poke_edge_order", nextOrder);
          } else {
            characterState.poke_edge_order = (nextOrder || []).slice();
          }
          saveCharacterToStorage();
        },
      })
    : null;
  if (board) {
    charContentEl.appendChild(board);
  }
  renderList();
}

function renderCharacterExtras() {
  charContentEl.innerHTML = "";
  charContentEl.setAttribute("data-step-target", "extras");
  appendNavRow();
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Class Mechanics / Extras";
  charContentEl.appendChild(title);
  appendStepModeToggle();

  ensurePlaytestScopeForClass(characterState.edge_class_filter);
  _renderPlannerPanel(charContentEl);
  _renderCloseUnlocks(charContentEl);

  const hint = document.createElement("div");
  hint.className = "char-feature-meta";
  hint.textContent = "Track class mechanics, special bonuses, or notes you want on the Fancy PTU sheet.";
  charContentEl.appendChild(hint);

  const catalogPanel = document.createElement("div");
  catalogPanel.className = "char-list-panel";
  const catalogTitle = document.createElement("div");
  catalogTitle.className = "char-section-title";
  catalogTitle.textContent = "Extras Catalog";
  catalogPanel.appendChild(catalogTitle);
  const catalogToolbar = document.createElement("div");
  catalogToolbar.className = "char-list-toolbar";
  const catalogSearch = document.createElement("input");
  catalogSearch.className = "char-search";
  catalogSearch.placeholder = "Search class features by name or simple effect...";
  catalogSearch.value = characterState.extras_catalog_search || "";
  catalogSearch.addEventListener("input", () => {
    characterState.extras_catalog_search = catalogSearch.value;
    renderCharacterExtras();
  });
  const scopeSelect = document.createElement("select");
  scopeSelect.className = "item-target-select";
  [{ id: "class", label: "Selected Class Only" }, { id: "all", label: "All Classes" }].forEach((opt) => {
    const option = document.createElement("option");
    option.value = opt.id;
    option.textContent = opt.label;
    if (characterState.extras_catalog_scope === opt.id) option.selected = true;
    scopeSelect.appendChild(option);
  });
  scopeSelect.addEventListener("change", () => {
    characterState.extras_catalog_scope = scopeSelect.value;
    renderCharacterExtras();
  });
  catalogToolbar.appendChild(catalogSearch);
  catalogToolbar.appendChild(scopeSelect);
  catalogPanel.appendChild(catalogToolbar);
  const catalogList = document.createElement("div");
  catalogList.className = "char-entry-list";
  ensurePlaytestScopeForClass(characterState.feature_class_filter);
  const classEntry = (characterData.classes || []).find((cls) => cls.id === characterState.class_id);
  const catalogQuery = String(characterState.extras_catalog_search || "").trim();
  const nodes = characterData.nodes || [];
  const allowedNodeIds = new Set();
  if (characterState.extras_catalog_scope === "class") {
    Object.values(_classTierMap(classEntry) || {}).forEach((ids) => {
      (ids || []).forEach((id) => allowedNodeIds.add(id));
    });
  }
  const catalogNodes = nodes.filter((node) => {
    if (node.type !== "feature") return false;
    if (!inContentScope(node)) return false;
    if (characterState.extras_catalog_scope === "class") {
      return allowedNodeIds.has(node.id);
    }
    return true;
  });
  let catalogVisible = 0;
  catalogNodes.forEach((node) => {
    const text = `${node.name} ${node.effects || ""}`;
    if (catalogQuery && _searchMatchScore(text, catalogQuery) <= 0) return;
    catalogVisible += 1;
    const row = document.createElement("div");
    row.className = "char-feature-row status-available";
    const body = document.createElement("div");
    const title = document.createElement("div");
    title.className = "class-tree-node-title";
    title.textContent = node.name;
    const effects = document.createElement("div");
    effects.className = "char-feature-meta";
    effects.textContent = node.effects || "";
    const summary = document.createElement("div");
    summary.className = "char-feature-meta";
    summary.textContent = _eli5FeatureSummary(node);
    body.appendChild(title);
    body.appendChild(summary);
    if (effects.textContent) body.appendChild(effects);
    const add = document.createElement("button");
    add.type = "button";
    add.className = "char-mini-button";
    add.textContent = "Add to Extras";
    add.addEventListener("click", () => {
      const className = classEntry?.name || "";
      characterState.extras.push({ className, mechanic: node.name || "", effect: node.effects || "" });
      saveCharacterToStorage();
      renderCharacterExtras();
    });
    row.appendChild(body);
    row.appendChild(add);
    catalogList.appendChild(row);
  });
  if (!catalogVisible) {
    const empty = document.createElement("div");
    empty.className = "char-empty";
    empty.textContent = "No matching features in catalog.";
    catalogList.appendChild(empty);
  }
  catalogPanel.appendChild(catalogList);
  charContentEl.appendChild(catalogPanel);

  const searchRow = document.createElement("div");
  searchRow.className = "char-list-toolbar";
  const search = document.createElement("input");
  search.className = "char-search";
  search.placeholder = "Search extras by class, mechanic, or simple effect...";
  search.value = characterState.extras_search || "";
  search.addEventListener("input", () => {
    characterState.extras_search = search.value;
    renderCharacterExtras();
  });
  const clearSearch = document.createElement("button");
  clearSearch.type = "button";
  clearSearch.className = "char-mini-button";
  clearSearch.textContent = "Clear";
  clearSearch.addEventListener("click", () => {
    characterState.extras_search = "";
    renderCharacterExtras();
  });
  searchRow.appendChild(search);
  searchRow.appendChild(clearSearch);
  charContentEl.appendChild(searchRow);

  const list = document.createElement("div");
  list.className = "char-list-panel";
  const header = document.createElement("div");
  header.className = "char-row-meta";
  header.textContent = "Class Name | Mechanic | Effect";
  list.appendChild(header);

  const renderRow = (entry, idx) => {
    const row = document.createElement("div");
    row.className = "char-field-grid char-extras-row";
    const classInput = document.createElement("input");
    classInput.placeholder = "Class";
    classInput.value = entry.className || "";
    classInput.addEventListener("input", () => {
      characterState.extras[idx].className = classInput.value;
      saveCharacterToStorage();
    });
    const mechInput = document.createElement("input");
    mechInput.placeholder = "Mechanic";
    mechInput.value = entry.mechanic || "";
    mechInput.addEventListener("input", () => {
      characterState.extras[idx].mechanic = mechInput.value;
      saveCharacterToStorage();
    });
    const effectInput = document.createElement("input");
    effectInput.placeholder = "Effect";
    effectInput.value = entry.effect || "";
    effectInput.addEventListener("input", () => {
      characterState.extras[idx].effect = effectInput.value;
      saveCharacterToStorage();
    });
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "char-mini-button";
    remove.textContent = "Remove";
    remove.addEventListener("click", () => {
      if (!confirm("Remove this mechanic?")) return;
      characterState.extras.splice(idx, 1);
      saveCharacterToStorage();
      renderCharacterExtras();
    });
    row.appendChild(classInput);
    row.appendChild(mechInput);
    row.appendChild(effectInput);
    row.appendChild(remove);
    return row;
  };

  if (!Array.isArray(characterState.extras)) {
    characterState.extras = [];
  }
  const extrasQuery = String(characterState.extras_search || "").trim();
  const rows = characterState.extras.length ? characterState.extras : [];
  let visible = 0;
  rows.forEach((entry, idx) => {
    const text = `${entry.className || ""} ${entry.mechanic || ""} ${entry.effect || ""}`;
    if (extrasQuery && _searchMatchScore(text, extrasQuery) <= 0) return;
    visible += 1;
    list.appendChild(renderRow(entry, idx));
  });
  if (!visible) {
    const empty = document.createElement("div");
    empty.className = "char-empty";
    empty.textContent = "No extras added yet.";
    list.appendChild(empty);
  }
  charContentEl.appendChild(list);

  const add = document.createElement("button");
  add.type = "button";
  add.textContent = "Add Mechanic";
  add.addEventListener("click", () => {
    const className =
      (characterData.classes || []).find((cls) => cls.id === characterState.class_id)?.name || "";
    characterState.extras.push({ className, mechanic: "", effect: "" });
    saveCharacterToStorage();
    renderCharacterExtras();
  });
  charContentEl.appendChild(add);
}

function renderCharacterInventory() {
  charContentEl.innerHTML = "";
  charContentEl.setAttribute("data-step-target", "inventory");
  appendNavRow();
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Inventory";
  charContentEl.appendChild(title);
  appendStepModeToggle();

  ensurePlaytestScopeForClass(characterState.edge_class_filter);
  _renderPlannerPanel(charContentEl);
  _renderCloseUnlocks(charContentEl);

  if (!characterState.inventory || typeof characterState.inventory !== "object") {
    characterState.inventory = { key_items: [], pokemon_items: [] };
  }
  const keyItems = Array.isArray(characterState.inventory.key_items) ? characterState.inventory.key_items : [];
  const pokemonItems = Array.isArray(characterState.inventory.pokemon_items)
    ? characterState.inventory.pokemon_items
    : [];
  const moneyField = document.createElement("label");
  moneyField.className = "char-field";
  moneyField.textContent = "Trainer Funds";
  const moneyInput = document.createElement("input");
  moneyInput.type = "text";
  moneyInput.placeholder = "e.g. 4500";
  moneyInput.value = String(characterState.profile.money || "");
  moneyInput.addEventListener("input", () => {
    characterState.profile.money = moneyInput.value;
    saveCharacterToStorage();
  });
  moneyField.appendChild(moneyInput);
  charContentEl.appendChild(moneyField);

  const catalogPanel = document.createElement("div");
  catalogPanel.className = "char-list-panel";
  const catalogTitle = document.createElement("div");
  catalogTitle.className = "char-section-title";
  catalogTitle.textContent = "Inventory Catalog";
  catalogPanel.appendChild(catalogTitle);
  const catalogToolbar = document.createElement("div");
  catalogToolbar.className = "char-list-toolbar";
  const catalogSearch = document.createElement("input");
  catalogSearch.className = "char-search";
  catalogSearch.placeholder = "Search catalog by item name, category, slot, or simple effect...";
  catalogSearch.value = characterState.inventory_catalog_search || "";
  catalogSearch.addEventListener("input", () => {
    characterState.inventory_catalog_search = catalogSearch.value;
    renderCharacterInventory();
  });
  const categorySelect = document.createElement("select");
  categorySelect.className = "item-target-select";
  const typeSelect = document.createElement("select");
  typeSelect.className = "item-target-select";
  const kindTabs = document.createElement("div");
  kindTabs.className = "char-tab-row";
  const kinds = [
    { id: "all", label: "All" },
    { id: "pokeballs", label: "Poke Balls" },
    { id: "equipment", label: "Equipment" },
    { id: "held", label: "Held Items" },
    { id: "key", label: "Key Items" },
    { id: "med", label: "Med Kits" },
    { id: "food", label: "Food Items" },
  ];
  kinds.forEach((tab) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "char-tab";
    btn.textContent = tab.label;
    btn.classList.toggle("active", (characterState.inventory_catalog_kind || "all") === tab.id);
    btn.addEventListener("click", () => {
      characterState.inventory_catalog_kind = tab.id;
      renderCharacterInventory();
    });
    kindTabs.appendChild(btn);
  });
  catalogToolbar.appendChild(catalogSearch);
  catalogToolbar.appendChild(categorySelect);
  catalogToolbar.appendChild(typeSelect);
  catalogPanel.appendChild(catalogToolbar);
  catalogPanel.appendChild(kindTabs);
  const catalogList = document.createElement("div");
  catalogList.className = "char-entry-list";
  catalogPanel.appendChild(catalogList);
  charContentEl.appendChild(catalogPanel);

  const searchRow = document.createElement("div");
  searchRow.className = "char-list-toolbar";
  const search = document.createElement("input");
  search.className = "char-search";
  search.placeholder = "Search inventory by item name or simple effect...";
  search.value = characterState.inventory_search || "";
  search.addEventListener("input", () => {
    characterState.inventory_search = search.value;
    renderCharacterInventory();
  });
  const clearSearch = document.createElement("button");
  clearSearch.type = "button";
  clearSearch.className = "char-mini-button";
  clearSearch.textContent = "Clear";
  clearSearch.addEventListener("click", () => {
    characterState.inventory_search = "";
    renderCharacterInventory();
  });
  searchRow.appendChild(search);
  searchRow.appendChild(clearSearch);
  charContentEl.appendChild(searchRow);

  const renderItemRow = (entry, idx, listKey) => {
    const row = document.createElement("div");
    row.className = "char-field-grid char-inventory-row";
    const nameInput = document.createElement("input");
    nameInput.placeholder = "Name";
    nameInput.value = entry.name || "";
    nameInput.addEventListener("input", () => {
      entry.name = nameInput.value;
      saveCharacterToStorage();
    });
    const qtyInput = document.createElement("input");
    qtyInput.placeholder = "Qty";
    qtyInput.value = entry.qty || "";
    qtyInput.addEventListener("input", () => {
      entry.qty = qtyInput.value;
      saveCharacterToStorage();
    });
    const costInput = document.createElement("input");
    costInput.placeholder = "Cost";
    costInput.value = entry.cost || "";
    costInput.addEventListener("input", () => {
      entry.cost = costInput.value;
      saveCharacterToStorage();
    });
    const descInput = document.createElement("input");
    descInput.placeholder = "Description";
    descInput.value = entry.desc || "";
    descInput.addEventListener("input", () => {
      entry.desc = descInput.value;
      saveCharacterToStorage();
    });
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "char-mini-button";
    remove.textContent = "Remove";
    remove.addEventListener("click", () => {
      if (!confirm("Remove this item?")) return;
      if (listKey === "key_items") {
        characterState.inventory.key_items.splice(idx, 1);
      } else {
        characterState.inventory.pokemon_items.splice(idx, 1);
      }
      saveCharacterToStorage();
      renderCharacterInventory();
    });
    row.appendChild(nameInput);
    row.appendChild(qtyInput);
    row.appendChild(costInput);
    row.appendChild(descInput);
    row.appendChild(remove);
    return row;
  };

  const invQuery = String(characterState.inventory_search || "").trim();
  const makeSection = (label, listKey, entries) => {
    const section = document.createElement("div");
    section.className = "char-list-panel";
    const header = document.createElement("div");
    header.className = "char-section-title";
    header.textContent = label;
    section.appendChild(header);
    let visible = 0;
    entries.forEach((entry, idx) => {
      const text = `${entry.name || ""} ${entry.desc || ""}`;
      if (invQuery && _searchMatchScore(text, invQuery) <= 0) return;
      visible += 1;
      section.appendChild(renderItemRow(entry, idx, listKey));
    });
    if (!visible) {
      const empty = document.createElement("div");
      empty.className = "char-empty";
      empty.textContent = "No items match your search.";
      section.appendChild(empty);
    }
    const add = document.createElement("button");
    add.type = "button";
    add.textContent = "Add Item";
    add.addEventListener("click", () => {
      const target = listKey === "key_items" ? characterState.inventory.key_items : characterState.inventory.pokemon_items;
      target.push({ name: "", qty: "", cost: "", desc: "" });
      saveCharacterToStorage();
      renderCharacterInventory();
    });
    section.appendChild(add);
    return section;
  };

  charContentEl.appendChild(makeSection("Key Items", "key_items", keyItems));
  charContentEl.appendChild(makeSection("Pokemon Items", "pokemon_items", pokemonItems));

  loadInventoryCatalog().then((catalog) => {
    const categories = Array.from(new Set(catalog.map((entry) => entry.category).filter(Boolean))).sort((a, b) =>
      String(a).localeCompare(String(b))
    );
    const typeValues = Array.from(new Set(catalog.map((entry) => entry.extra).filter(Boolean))).sort((a, b) =>
      String(a).localeCompare(String(b))
    );
    categorySelect.innerHTML = "";
    const allOption = document.createElement("option");
    allOption.value = "";
    allOption.textContent = "All Categories";
    categorySelect.appendChild(allOption);
    categories.forEach((cat) => {
      const opt = document.createElement("option");
      opt.value = cat;
      opt.textContent = cat;
      categorySelect.appendChild(opt);
    });
    typeSelect.innerHTML = "";
    const typeAll = document.createElement("option");
    typeAll.value = "";
    typeAll.textContent = "All Slots/Mods";
    typeSelect.appendChild(typeAll);
    typeValues.forEach((value) => {
      const opt = document.createElement("option");
      opt.value = value;
      opt.textContent = value;
      typeSelect.appendChild(opt);
    });
    const currentCategory = characterState.inventory_catalog_category || "";
    if (currentCategory) categorySelect.value = currentCategory;
    categorySelect.addEventListener("change", () => {
      characterState.inventory_catalog_category = categorySelect.value;
      renderCharacterInventory();
    });
    const currentType = characterState.inventory_catalog_type || "";
    if (currentType) typeSelect.value = currentType;
    typeSelect.addEventListener("change", () => {
      characterState.inventory_catalog_type = typeSelect.value;
      renderCharacterInventory();
    });
    catalogList.innerHTML = "";
    const query = String(characterState.inventory_catalog_search || "").trim();
    const categoryFilter = characterState.inventory_catalog_category || "";
    const typeFilter = characterState.inventory_catalog_type || "";
    const kindFilter = characterState.inventory_catalog_kind || "all";
    let visible = 0;
    catalog.forEach((entry) => {
      if (kindFilter === "pokeballs" && !/^pok.*balls?$/i.test(String(entry.category || ""))) return;
      if (kindFilter === "equipment" && entry.category !== "Equipment") return;
      if (kindFilter === "held" && !/^pok.*mon stuff$/i.test(String(entry.category || ""))) return;
      if (kindFilter === "key" && entry.category !== "Key Items") return;
      if (kindFilter === "med" && entry.category !== "Med Kit") return;
      if (kindFilter === "food" && entry.category !== "Food Items") return;
      if (categoryFilter && entry.category !== categoryFilter) return;
      if (typeFilter && entry.extra !== typeFilter) return;
      const text = `${entry.name} ${entry.desc} ${entry.category} ${entry.extra}`;
      if (query && _searchMatchScore(text, query) <= 0) return;
      visible += 1;
      const row = document.createElement("div");
      row.className = "char-feature-row status-available";
      const body = document.createElement("div");
      const title = document.createElement("div");
      title.className = "class-tree-node-title";
      title.textContent = entry.name;
      _setTooltipAttrs(
        title,
        `Item: ${entry.name}`,
        [entry.prerequisites ? `Prerequisites: ${entry.prerequisites}` : "", entry.effects || ""].filter(Boolean).join("\n")
      );
      const meta = document.createElement("div");
      meta.className = "char-row-meta";
      const badges = document.createElement("div");
      badges.className = "char-tag-row";
      const makeBadge = (text) => {
        const badge = document.createElement("span");
        badge.className = "char-tag";
        badge.textContent = text;
        return badge;
      };
      if (entry.category) badges.appendChild(makeBadge(entry.category));
      if (entry.extra) badges.appendChild(makeBadge(entry.extra));
      if (badges.childNodes.length) meta.appendChild(badges);
      const metaText = [_hasDisplayValue(entry.cost) ? `$${entry.cost}` : ""].filter(Boolean).join(" ");
      if (metaText) {
        const cost = document.createElement("div");
        cost.textContent = metaText;
        meta.appendChild(cost);
      }
      const effects = document.createElement("div");
      effects.className = "char-feature-meta";
      effects.textContent = entry.desc || "";
      const summary = document.createElement("div");
      summary.className = "char-feature-meta";
      summary.textContent = _eli5ItemSummary(entry);
      body.appendChild(title);
      body.appendChild(summary);
      if (meta.textContent) body.appendChild(meta);
      if (effects.textContent) body.appendChild(effects);
      const addKey = document.createElement("button");
      addKey.type = "button";
      addKey.className = "char-mini-button";
      addKey.textContent = "Add Key";
      addKey.addEventListener("click", () => {
        characterState.inventory.key_items.push({
          name: entry.name,
          qty: "1",
          cost: entry.cost,
          desc: entry.desc,
        });
        saveCharacterToStorage();
        renderCharacterInventory();
      });
      const addPoke = document.createElement("button");
      addPoke.type = "button";
      addPoke.className = "char-mini-button";
      addPoke.textContent = "Add Pokemon";
      addPoke.addEventListener("click", () => {
        characterState.inventory.pokemon_items.push({
          name: entry.name,
          qty: "1",
          cost: entry.cost,
          desc: entry.desc,
        });
        saveCharacterToStorage();
        renderCharacterInventory();
      });
      row.appendChild(body);
      row.appendChild(addKey);
      row.appendChild(addPoke);
      catalogList.appendChild(row);
    });
    if (!visible) {
      const empty = document.createElement("div");
      empty.className = "char-empty";
      empty.textContent = "No catalog items match your search.";
      catalogList.appendChild(empty);
    }
  });
}

function renderCharacterPokemonTeam() {
  charContentEl.innerHTML = "";
  charContentEl.setAttribute("data-step-target", "pokemon-team");
  appendNavRow();
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Pokemon Team Builder";
  charContentEl.appendChild(title);
  appendStepModeToggle();

  const builds = _ensurePokemonBuilds();
  let sanitizedBuilds = false;
  builds.forEach((build) => {
    const result = _sanitizePokemonBuildForLevel(build);
    if (result.changed) sanitizedBuilds = true;
  });
  if (sanitizedBuilds) saveCharacterToStorage();
  ensureSpeciesDatalist();
  if (characterState.pokemon_team_auto_level) {
    const level = Number(characterState.profile.level || 1);
    let changed = false;
    builds.forEach((build) => {
      const next = trainerToPokemonLevel(level);
      if (build.level !== next) {
        build.level = next;
        changed = true;
      }
    });
    if (changed) saveCharacterToStorage();
  }
  const teamLimit = Math.max(1, Number(characterState.pokemon_team_limit || 6));
  const summary = document.createElement("div");
  summary.className = "char-summary-box";
  const avgLevel =
    builds.length > 0
      ? Math.round(builds.reduce((acc, b) => acc + Number(b.level || 1), 0) / builds.length)
      : 0;
  summary.textContent = `Team size: ${builds.length}/${teamLimit}${builds.length ? ` | Avg Level ${avgLevel}` : ""}`;
  charContentEl.appendChild(summary);
  const dataset = _builderDatasetStatus();
  const datasetSummary = document.createElement("div");
  datasetSummary.className = "char-feature-meta";
  datasetSummary.textContent = `Datasets synced: Species ${dataset.species} | Moves ${dataset.moves} | Abilities ${dataset.abilities} | Items ${dataset.items} | Poke Edges ${dataset.pokeEdges} | Learnset Species ${dataset.learnsetSpecies}`;
  charContentEl.appendChild(datasetSummary);
  if (builds.length > teamLimit) {
    const warn = document.createElement("div");
    warn.className = "char-summary-box";
    warn.textContent = "Team size exceeds the limit. Increase the limit or remove Pokemon.";
    charContentEl.appendChild(warn);
  }

  const actionRow = document.createElement("div");
  actionRow.className = "char-action-row";
  const limitField = document.createElement("label");
  limitField.className = "char-field";
  limitField.textContent = "Team Limit";
  const limitInput = document.createElement("input");
  limitInput.type = "number";
  limitInput.min = "1";
  limitInput.value = String(teamLimit);
  limitInput.addEventListener("input", () => {
    characterState.pokemon_team_limit = Math.max(1, Number(limitInput.value || 1));
    saveCharacterToStorage();
    renderCharacterPokemonTeam();
  });
  limitField.appendChild(limitInput);
  actionRow.appendChild(limitField);
  const autoLevelLabel = document.createElement("label");
  autoLevelLabel.className = "char-inline-toggle";
  const autoLevelInput = document.createElement("input");
  autoLevelInput.type = "checkbox";
  autoLevelInput.checked = !!characterState.pokemon_team_auto_level;
    autoLevelInput.addEventListener("change", () => {
      characterState.pokemon_team_auto_level = autoLevelInput.checked;
      characterState.pokemon_team_auto_level_explicit = true;
      if (autoLevelInput.checked) {
        const level = _defaultPokemonBuildLevel();
        builds.forEach((build) => {
          build.level = Number.isFinite(level) ? level : 1;
          _sanitizePokemonBuildForLevel(build);
        });
      }
      saveCharacterToStorage();
      renderCharacterPokemonTeam();
  });
  autoLevelLabel.appendChild(autoLevelInput);
  const autoLevelText = document.createElement("span");
  autoLevelText.textContent =
    "Auto-sync levels to trainer (Pokemon level ~2x trainer level)";
  autoLevelLabel.appendChild(autoLevelText);
  actionRow.appendChild(autoLevelLabel);
  const autofillLabel = document.createElement("label");
  autofillLabel.className = "char-inline-toggle";
  const autofillInput = document.createElement("input");
  autofillInput.type = "checkbox";
  autofillInput.checked = !!characterState.pokemon_team_autofill;
  autofillInput.addEventListener("change", () => {
    characterState.pokemon_team_autofill = autofillInput.checked;
    saveCharacterToStorage();
  });
  autofillLabel.appendChild(autofillInput);
  const autofillText = document.createElement("span");
  autofillText.textContent = "Auto-fill from species defaults (if available)";
  autofillLabel.appendChild(autofillText);
  actionRow.appendChild(autofillLabel);
  const addBtn = document.createElement("button");
  addBtn.type = "button";
  addBtn.textContent = "Add Pokemon";
  addBtn.addEventListener("click", () => {
    if (builds.length >= teamLimit) {
      alert(`Team limit reached (${teamLimit}). Increase the limit to add more Pokemon.`);
      return;
    }
    const speciesItems = _speciesPickerItems();
    if (!speciesItems.length) {
      const build = _createPokemonBuildFromPrompt();
      if (!build) return;
      renderCharacterPokemonTeam();
      return;
    }
    openListPicker({
      title: "Add Pokemon",
      helpText: "Search by species name, type, size, or capability.",
      items: speciesItems,
      onSelect: (name) => {
        const speciesEntry = _getPokemonSpeciesEntry(name);
        const display = speciesEntry?.name || name;
        const level = _defaultPokemonBuildLevel();
        _ensurePokemonBuilds().push({
          name: display,
          species: display,
          level,
          battle_side: "",
          moves: [],
          abilities: [],
          items: [],
          poke_edges: [],
        });
        if (characterState.pokemon_team_autofill) {
          _autoFillPokemonBuild(builds[builds.length - 1], speciesEntry, false);
        }
        saveCharacterToStorage();
        renderCharacterPokemonTeam();
      },
    });
  });
  const clearBtn = document.createElement("button");
  clearBtn.type = "button";
  clearBtn.className = "char-mini-button";
  clearBtn.textContent = "Clear Team";
  clearBtn.addEventListener("click", () => {
    if (!builds.length) return;
    if (!confirm("Remove all Pokemon from the team?")) return;
    characterState.pokemon_builds = [];
    saveCharacterToStorage();
    renderCharacterPokemonTeam();
  });
  const importBtn = document.createElement("button");
  importBtn.type = "button";
  importBtn.className = "char-mini-button";
  importBtn.textContent = "Import Roster CSV";
  importBtn.addEventListener("click", () => {
    openPokemonRosterImportModal();
  });
  const battleCsvBtn = document.createElement("button");
  battleCsvBtn.type = "button";
  battleCsvBtn.className = "char-mini-button";
  battleCsvBtn.textContent = "Stage Battle CSV";
  battleCsvBtn.addEventListener("click", () => {
    const rows = _rosterRowsFromTrainerBuilds({ pokemon_builds: builds }, true);
    if (!rows.length) {
      alertError(new Error("No Pokemon builds found to stage for battle."));
      return;
    }
    const csvText = stringifyCsv(rows);
    _setBattleRosterCsv(csvText, "builder-team");
    saveSettings();
    notifyUI("ok", "Builder team staged as battle roster CSV.", 2200);
  });
  const submissionBtn = document.createElement("button");
  submissionBtn.type = "button";
  submissionBtn.className = "char-mini-button";
  submissionBtn.textContent = "Save Project ZIP";
  submissionBtn.addEventListener("click", () => {
    try {
      _downloadTournamentSubmissionPack();
      notifyUI("ok", "Tournament team pack downloaded.", 2200);
    } catch (err) {
      alertError(err);
    }
  });
  const bulkAutoStats = document.createElement("button");
  bulkAutoStats.type = "button";
  bulkAutoStats.className = "char-mini-button";
  bulkAutoStats.textContent = "Auto Stats All";
  bulkAutoStats.addEventListener("click", () => {
    let changed = false;
    builds.forEach((build) => {
      const species = _getPokemonSpeciesEntry(build.species || build.name || "");
      if (_applyAutoPokemonStatPoints(build, species, "weighted")) changed = true;
    });
    if (changed) {
      saveCharacterToStorage();
      renderCharacterPokemonTeam();
      notifyUI("ok", "Applied weighted stat points to all Pokemon.", 2000);
    } else {
      notifyUI("info", "All Pokemon stat points already match auto allocation.", 1800);
    }
  });
  const bulkFillStats = document.createElement("button");
  bulkFillStats.type = "button";
  bulkFillStats.className = "char-mini-button";
  bulkFillStats.textContent = "Fill Missing Stats";
  bulkFillStats.addEventListener("click", () => {
    let changed = false;
    builds.forEach((build) => {
      const species = _getPokemonSpeciesEntry(build.species || build.name || "");
      if (_fillRemainingPokemonStatPoints(build, species, "weighted")) changed = true;
    });
    if (changed) {
      saveCharacterToStorage();
      renderCharacterPokemonTeam();
      notifyUI("ok", "Filled missing stat points for the team.", 2000);
    } else {
      notifyUI("info", "No missing stat points to fill.", 1800);
    }
  });
  const bulkClearStats = document.createElement("button");
  bulkClearStats.type = "button";
  bulkClearStats.className = "char-mini-button";
  bulkClearStats.textContent = "Clear Stats All";
  bulkClearStats.addEventListener("click", () => {
    if (!builds.length) return;
    if (!confirm("Clear added stat points for every Pokemon in the team?")) return;
    let changed = false;
    builds.forEach((build) => {
      if (_clearPokemonStatPoints(build)) changed = true;
    });
    if (changed) {
      saveCharacterToStorage();
      renderCharacterPokemonTeam();
      notifyUI("ok", "Cleared added stat points for all Pokemon.", 2000);
    }
  });
  actionRow.appendChild(addBtn);
  actionRow.appendChild(importBtn);
  actionRow.appendChild(battleCsvBtn);
  actionRow.appendChild(submissionBtn);
  actionRow.appendChild(bulkAutoStats);
  actionRow.appendChild(bulkFillStats);
  actionRow.appendChild(bulkClearStats);
  actionRow.appendChild(clearBtn);
  charContentEl.appendChild(actionRow);

  const catalogPanel = document.createElement("div");
  catalogPanel.className = "char-list-panel";
  const catalogTitle = document.createElement("div");
  catalogTitle.className = "char-section-title";
  catalogTitle.textContent = "Pokemon Catalog";
  catalogPanel.appendChild(catalogTitle);
  const catalogToolbar = document.createElement("div");
  catalogToolbar.className = "char-list-toolbar";
  const catalogSearch = document.createElement("input");
  catalogSearch.className = "char-search";
  catalogSearch.placeholder = "Search species...";
  catalogSearch.value = characterState.pokemon_team_search || "";
  const catalogClear = document.createElement("button");
  catalogClear.type = "button";
  catalogClear.className = "char-mini-button";
  catalogClear.textContent = "Clear";
  catalogToolbar.appendChild(catalogSearch);
  catalogToolbar.appendChild(catalogClear);
  catalogPanel.appendChild(catalogToolbar);
  const catalogList = document.createElement("div");
  catalogList.className = "char-entry-list";
  ensureSpeciesDatalist();
  const speciesList = _pokemonSpeciesCatalog().slice();
  speciesList.sort((a, b) => String(a.name).localeCompare(String(b.name)));
  const renderCatalogEntries = () => {
    catalogList.innerHTML = "";
    const query = String(characterState.pokemon_team_search || "").trim();
    let visible = 0;
    if (!speciesList.length) {
      const emptyData = document.createElement("div");
      emptyData.className = "char-empty";
      emptyData.textContent = "Species dataset unavailable. Use Add Pokemon for manual entry.";
      catalogList.appendChild(emptyData);
      const manualBtn = document.createElement("button");
      manualBtn.type = "button";
      manualBtn.className = "char-mini-button";
      manualBtn.textContent = "Add Manual Pokemon";
      manualBtn.addEventListener("click", () => {
        if (builds.length >= teamLimit) {
          alert(`Team limit reached (${teamLimit}). Increase the limit to add more Pokemon.`);
          return;
        }
        const build = _createPokemonBuildFromPrompt();
        if (!build) return;
        renderCharacterPokemonTeam();
      });
      catalogList.appendChild(manualBtn);
      return;
    }
    speciesList.forEach((entry) => {
      const text = `${entry.name} ${(entry.types || []).join(" ")}`;
      if (query && _searchMatchScore(text, query) <= 0) return;
      if (!query && visible >= 80) return;
      visible += 1;
      const row = document.createElement("button");
      row.type = "button";
      row.className = "char-feature-row status-available char-catalog-row";
      const spriteWrap = document.createElement("span");
      spriteWrap.className = "char-catalog-sprite-wrap";
      const sprite = document.createElement("img");
      sprite.className = "char-catalog-sprite";
      sprite.alt = entry.name;
      sprite.loading = "lazy";
      sprite.src = _speciesSpriteUrl(entry.name);
      const spriteFallback = document.createElement("span");
      spriteFallback.className = "char-catalog-sprite-fallback";
      spriteFallback.textContent = String(entry.name || "?").slice(0, 2).toUpperCase();
      sprite.addEventListener("error", () => {
        sprite.style.display = "none";
        spriteFallback.style.display = "flex";
      });
      sprite.addEventListener("load", () => {
        sprite.style.display = "block";
        spriteFallback.style.display = "none";
      });
      spriteWrap.appendChild(sprite);
      spriteWrap.appendChild(spriteFallback);
      const content = document.createElement("div");
      content.className = "char-catalog-main";
      const name = document.createElement("div");
      name.className = "char-row-title";
      name.textContent = entry.name;
      const meta = document.createElement("div");
      meta.className = "char-row-meta";
      meta.textContent = `Size ${entry.size || "-"}${_hasDisplayValue(entry.weight) ? ` | Weight ${entry.weight}` : ""}`;
      const typeRow = document.createElement("div");
      typeRow.className = "char-poke-type-row";
      (entry.types || []).forEach((typeName) => {
        const token = document.createElement("span");
        token.className = "char-type-token";
        const typeIcon = typeIconFromCache(typeName);
        if (!typeIcon && !pokeApiCacheHas(pokeApiTypeIconCache, typeName)) {
          ensureTypeIcon(typeName).then(() => _queueBuilderRerender());
        }
        if (typeIcon) {
          const img = document.createElement("img");
          img.src = typeIcon;
          img.alt = typeName;
          img.loading = "lazy";
          token.appendChild(img);
        }
        const text = document.createElement("span");
        text.textContent = typeName;
        token.appendChild(text);
        typeRow.appendChild(token);
      });
      content.appendChild(name);
      content.appendChild(meta);
      content.appendChild(typeRow);
      row.appendChild(spriteWrap);
      row.appendChild(content);
      row.addEventListener("click", () => {
        if (builds.length >= teamLimit) {
          alert(`Team limit reached (${teamLimit}). Increase the limit to add more Pokemon.`);
          return;
        }
        const level = _defaultPokemonBuildLevel();
        _ensurePokemonBuilds().push({
          name: entry.name,
          species: entry.name,
          level,
          battle_side: "",
          moves: [],
          abilities: [],
          items: [],
          poke_edges: [],
        });
        if (characterState.pokemon_team_autofill) {
          _autoFillPokemonBuild(builds[builds.length - 1], entry, false);
        }
        saveCharacterToStorage();
        renderCharacterPokemonTeam();
      });
      catalogList.appendChild(row);
    });
    if (!visible) {
      const empty = document.createElement("div");
      empty.className = "char-empty";
      empty.textContent = "No species match your search.";
      catalogList.appendChild(empty);
    }
  };
  catalogSearch.addEventListener("input", () => {
    const start = catalogSearch.selectionStart;
    const end = catalogSearch.selectionEnd;
    characterState.pokemon_team_search = catalogSearch.value;
    renderCatalogEntries();
    if (document.activeElement !== catalogSearch) {
      requestAnimationFrame(() => {
        catalogSearch.focus();
        if (start !== null && end !== null) {
          catalogSearch.setSelectionRange(start, end);
        }
      });
    }
  });
  catalogClear.addEventListener("click", () => {
    characterState.pokemon_team_search = "";
    catalogSearch.value = "";
    renderCatalogEntries();
    catalogSearch.focus();
  });
  renderCatalogEntries();
  catalogPanel.appendChild(catalogList);
  charContentEl.appendChild(catalogPanel);

  const teamPanel = document.createElement("div");
  teamPanel.className = "char-list-panel";
  const teamTitle = document.createElement("div");
  teamTitle.className = "char-section-title";
  teamTitle.textContent = "Team Roster";
  teamPanel.appendChild(teamTitle);

  const rosterToolbar = document.createElement("div");
  rosterToolbar.className = "char-list-toolbar";
  const rosterSearch = document.createElement("input");
  rosterSearch.className = "char-search";
  rosterSearch.placeholder = "Search roster by name, species, or type...";
  rosterSearch.value = characterState.pokemon_team_roster_search || "";
  rosterSearch.addEventListener("input", () => {
    characterState.pokemon_team_roster_search = rosterSearch.value;
    renderCharacterPokemonTeam();
  });
  rosterToolbar.appendChild(rosterSearch);
  teamPanel.appendChild(rosterToolbar);

  const rosterFilterRow = document.createElement("div");
  rosterFilterRow.className = "char-filter-row";
  const currentRosterFilter = String(characterState.pokemon_team_roster_filter || "all").toLowerCase();
  const rosterFilters = [
    { id: "all", label: "All" },
    { id: "invalid", label: "Invalid" },
    { id: "stat-gap", label: "Stat Gap" },
    { id: "missing-species", label: "Missing Species" },
  ];
  rosterFilters.forEach((filter) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `char-mini-button${currentRosterFilter === filter.id ? " is-active" : ""}`;
    btn.textContent = filter.label;
    btn.addEventListener("click", () => {
      characterState.pokemon_team_roster_filter = filter.id;
      renderCharacterPokemonTeam();
    });
    rosterFilterRow.appendChild(btn);
  });
  teamPanel.appendChild(rosterFilterRow);

  if (!builds.length) {
    const empty = document.createElement("div");
    empty.className = "char-empty";
    empty.textContent = "No Pokemon added yet.";
    teamPanel.appendChild(empty);
  }

  let shownCount = 0;
  builds.forEach((build, idx) => {
    const filterQuery = String(characterState.pokemon_team_roster_search || "").trim();
    const filterMode = String(characterState.pokemon_team_roster_filter || "all").toLowerCase();
    const filterSpeciesEntry = _getPokemonSpeciesEntry(build.species || build.name || "");
    const filterLegality = _pokemonBuildLegality(build);
    const filterStatBudget = _pokemonStatPointBudget(build.level || 1);
    const filterStatSpent = _pokemonBuildStatPointsSpent(build);
    const filterHaystack = [
      build.name || "",
      build.species || "",
      ...((filterSpeciesEntry && Array.isArray(filterSpeciesEntry.types)) ? filterSpeciesEntry.types : []),
    ].join(" ");
    if (filterQuery && _searchMatchScore(filterHaystack, filterQuery) <= 0) return;
    if (filterMode === "invalid" && filterLegality.ok) return;
    if (filterMode === "stat-gap" && filterStatSpent === filterStatBudget) return;
    if (filterMode === "missing-species" && !(build.species && !filterSpeciesEntry)) return;
    shownCount += 1;

    const card = document.createElement("div");
    card.className = "char-summary-box";
    const speciesEntry = _getPokemonSpeciesEntry(build.species || build.name || "");

    const hero = document.createElement("div");
    hero.className = "char-poke-hero";
    const spriteWrap = document.createElement("div");
    spriteWrap.className = "char-poke-sprite-wrap";
    const sprite = document.createElement("img");
    sprite.className = "char-poke-sprite";
    sprite.alt = build.species || build.name || "Pokemon";
    sprite.loading = "lazy";
    sprite.src = _speciesSpriteUrl(build.species || build.name || "");
    const spriteFallback = document.createElement("div");
    spriteFallback.className = "char-poke-sprite-fallback";
    spriteFallback.textContent = String(build.species || build.name || "?").slice(0, 2).toUpperCase();
    sprite.addEventListener("error", () => {
      sprite.style.display = "none";
      spriteFallback.style.display = "flex";
    });
    sprite.addEventListener("load", () => {
      sprite.style.display = "block";
      spriteFallback.style.display = "none";
    });
    spriteWrap.appendChild(sprite);
    spriteWrap.appendChild(spriteFallback);
    hero.appendChild(spriteWrap);
    const heroMain = document.createElement("div");
    heroMain.className = "char-poke-hero-main";
    const heroTitle = document.createElement("div");
    heroTitle.className = "char-poke-title";
    heroTitle.textContent = `${build.name || build.species || "Pokemon"}  Lv ${build.level || 1}`;
    heroMain.appendChild(heroTitle);
    const typeRow = document.createElement("div");
    typeRow.className = "char-poke-type-row";
    const types = Array.isArray(speciesEntry?.types) ? speciesEntry.types : [];
    if (types.length) {
      types.forEach((typeName) => {
        const typeToken = document.createElement("span");
        typeToken.className = "char-type-token";
        const hasTypeIcon = pokeApiCacheHas(pokeApiTypeIconCache, typeName);
        const typeIcon = typeIconFromCache(typeName);
        if (!hasTypeIcon) ensureTypeIcon(typeName).then(() => _queueBuilderRerender());
        if (typeIcon) {
          const img = document.createElement("img");
          img.src = typeIcon;
          img.alt = typeName;
          img.loading = "lazy";
          typeToken.appendChild(img);
        }
        const text = document.createElement("span");
        text.textContent = typeName;
        typeToken.appendChild(text);
        typeRow.appendChild(typeToken);
      });
    } else {
      const placeholder = document.createElement("span");
      placeholder.className = "char-feature-meta";
      placeholder.textContent = "Unknown type";
      typeRow.appendChild(placeholder);
    }
    heroMain.appendChild(typeRow);
    hero.appendChild(heroMain);
    card.appendChild(hero);

    const grid = document.createElement("div");
    grid.className = "char-field-grid";
    const nameField = document.createElement("label");
    nameField.className = "char-field";
    nameField.textContent = "Name";
    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.value = build.name || "";
    nameInput.addEventListener("input", () => {
      build.name = nameInput.value;
      saveCharacterToStorage();
    });
    nameField.appendChild(nameInput);
    const levelField = document.createElement("label");
    levelField.className = "char-field";
    levelField.textContent = "Level";
    const levelInput = document.createElement("input");
    levelInput.type = "number";
    levelInput.min = "1";
    levelInput.value = String(build.level || 1);
    levelInput.disabled = !!characterState.pokemon_team_auto_level;
    levelInput.addEventListener("input", () => {
      build.level = _clampPokemonLevel(levelInput.value || 1, build.level || 1);
      _sanitizePokemonBuildForLevel(build);
      saveCharacterToStorage();
      renderCharacterPokemonTeam();
    });
    levelField.appendChild(levelInput);
    const speciesField = document.createElement("label");
    speciesField.className = "char-field";
    speciesField.textContent = "Species";
    const speciesInput = document.createElement("input");
    speciesInput.type = "text";
    speciesInput.setAttribute("list", "pokemon-species-list");
    speciesInput.placeholder = "Species name";
    speciesInput.value = build.species || build.name || "";
    speciesInput.addEventListener("input", () => {
      build.species = speciesInput.value;
      saveCharacterToStorage();
    });
    speciesInput.addEventListener("change", () => {
      const speciesEntry = _getPokemonSpeciesEntry(build.species || build.name || "");
      _sanitizePokemonBuildForLevel(build, speciesEntry);
      if (characterState.pokemon_team_autofill && speciesEntry) {
        _autoFillPokemonBuild(build, speciesEntry, false);
        _sanitizePokemonBuildForLevel(build, speciesEntry);
      }
      saveCharacterToStorage();
      renderCharacterPokemonTeam();
    });
    speciesField.appendChild(speciesInput);
    const sideField = document.createElement("label");
    sideField.className = "char-field";
    sideField.textContent = "Battle Side";
    _setTooltipAttrs(
      sideField,
      "Battle Side",
      "Auto: defaults to Player and optionally mirrors to Foe using the battle toggle. Player/Foe/Both: explicit side assignment with full freedom."
    );
    const sideSelect = document.createElement("select");
    const sideMode = String(build.battle_side || "")
      .trim()
      .toLowerCase();
    const normalizedSideMode = ["player", "foe", "both"].includes(sideMode) ? sideMode : "auto";
    [
      { value: "auto", label: "Auto (Player + Mirror Option)" },
      { value: "player", label: "Player" },
      { value: "foe", label: "Foe" },
      { value: "both", label: "Both" },
    ].forEach((entry) => {
      const option = document.createElement("option");
      option.value = entry.value;
      option.textContent = entry.label;
      sideSelect.appendChild(option);
    });
    sideSelect.value = normalizedSideMode;
    sideSelect.addEventListener("change", () => {
      build.battle_side = sideSelect.value === "auto" ? "" : sideSelect.value;
      saveCharacterToStorage();
    });
    sideField.appendChild(sideSelect);
    const caughtField = document.createElement("label");
    caughtField.className = "char-field";
    caughtField.textContent = "Caught (wild)";
    _setTooltipAttrs(
      caughtField,
      "Caught (wild)",
      "Check if this Pokémon was caught in the wild. Required when the species is evolved but below its normal evolution level (e.g. Venusaur at level 5)."
    );
    const caughtInput = document.createElement("input");
    caughtInput.type = "checkbox";
    caughtInput.checked = !!build.caught;
    caughtInput.addEventListener("change", () => {
      build.caught = caughtInput.checked;
      saveCharacterToStorage();
      renderCharacterPokemonTeam();
    });
    caughtField.appendChild(caughtInput);
    grid.appendChild(nameField);
    grid.appendChild(levelField);
    grid.appendChild(speciesField);
    grid.appendChild(sideField);
    grid.appendChild(caughtField);
    card.appendChild(grid);
    if (speciesEntry) {
      const info = document.createElement("div");
      info.className = "char-feature-meta";
      const types = (speciesEntry.types || []).join(" / ") || "-";
      const stats = speciesEntry.base_stats || {};
      const statLine = `HP ${stats.hp ?? "-"} | Atk ${stats.attack ?? "-"} | Def ${stats.defense ?? "-"} | SpA ${stats.special_attack ?? "-"} | SpD ${stats.special_defense ?? "-"} | Spd ${stats.speed ?? "-"}`;
      info.textContent = `${types} | Size ${speciesEntry.size || "-"} | Weight ${speciesEntry.weight || "-"} | ${statLine}`;
      card.appendChild(info);
      const baseStatsPanel = document.createElement("div");
      baseStatsPanel.className = "char-poke-stat-panel";
      const statKeys = [
        { key: "hp", label: "HP", baseKey: "hp" },
        { key: "atk", label: "Atk", baseKey: "attack" },
        { key: "def", label: "Def", baseKey: "defense" },
        { key: "spatk", label: "SpA", baseKey: "special_attack" },
        { key: "spdef", label: "SpD", baseKey: "special_defense" },
        { key: "spd", label: "Spd", baseKey: "speed" },
      ];
      const added = _ensurePokemonBuildStatPoints(build);
      statKeys.forEach((entry) => {
        const baseValue = Math.max(0, Number(stats[entry.baseKey] || 0));
        const addValue = Math.max(0, Number(added[entry.key] || 0));
        const totalValue = baseValue + addValue;
        const row = document.createElement("div");
        row.className = "char-poke-stat-row";
        const label = document.createElement("span");
        label.className = "char-poke-stat-label";
        label.textContent = entry.label;
        const meter = document.createElement("div");
        meter.className = "char-poke-stat-meter";
        const fill = document.createElement("span");
        fill.className = "char-poke-stat-fill";
        fill.style.width = `${Math.max(4, Math.min(100, (totalValue / 30) * 100))}%`;
        meter.appendChild(fill);
        const value = document.createElement("span");
        value.className = "char-poke-stat-value";
        value.textContent = `${totalValue} (${baseValue}+${addValue})`;
        row.appendChild(label);
        row.appendChild(meter);
        row.appendChild(value);
        baseStatsPanel.appendChild(row);
      });
      card.appendChild(baseStatsPanel);

      if (Array.isArray(speciesEntry.capabilities) && speciesEntry.capabilities.length) {
        const capTitle = document.createElement("div");
        capTitle.className = "char-feature-meta";
        capTitle.textContent = "Capabilities (click one for a plain-English explanation)";
        card.appendChild(capTitle);
        const capList = document.createElement("div");
        capList.className = "char-pill-list";
        speciesEntry.capabilities.forEach((cap) => {
          const pill = document.createElement("button");
          pill.type = "button";
          pill.className = "char-pill char-pill-link";
          const desc = _getCapabilityDescription(cap);
          _setTooltipAttrs(pill, `Capability: ${cap}`, desc || "");
          pill.textContent = cap;
          pill.addEventListener("click", () => showCapabilityDetail(cap));
          capList.appendChild(pill);
        });
        card.appendChild(capList);
      }
    } else if (build.species) {
      const warn = document.createElement("div");
      warn.className = "char-feature-meta";
      warn.textContent = "Species not found in dataset. Check spelling.";
      card.appendChild(warn);
    }

    const statPoints = _ensurePokemonBuildStatPoints(build);
    const statBudget = _pokemonStatPointBudget(build.level || 1);
    const statSpent = _pokemonBuildStatPointsSpent(build);
    const statSummary = document.createElement("div");
    statSummary.className = "char-feature-meta";
    statSummary.textContent = `Added Stat Points: ${statSpent}/${statBudget} (budget = Level + 10)`;
    card.appendChild(statSummary);
    const budgetRow = document.createElement("div");
    budgetRow.className = "char-stat-budget-row";
    const budgetMeter = document.createElement("div");
    budgetMeter.className = "char-stat-budget-meter";
    const budgetFill = document.createElement("span");
    budgetFill.className = "char-stat-budget-fill";
    if (statSpent > statBudget) budgetFill.classList.add("is-over");
    else if (statSpent < statBudget) budgetFill.classList.add("is-under");
    else budgetFill.classList.add("is-exact");
    budgetFill.style.width = `${Math.max(4, Math.min(100, statBudget > 0 ? (statSpent / statBudget) * 100 : 0))}%`;
    budgetMeter.appendChild(budgetFill);
    budgetRow.appendChild(budgetMeter);
    const budgetMeta = document.createElement("span");
    budgetMeta.className = "char-stat-budget-meta";
    const remaining = statBudget - statSpent;
    if (remaining > 0) budgetMeta.textContent = `${remaining} points unspent`;
    else if (remaining < 0) budgetMeta.textContent = `${Math.abs(remaining)} points over budget`;
    else budgetMeta.textContent = "Point budget complete";
    budgetRow.appendChild(budgetMeta);
    card.appendChild(budgetRow);
    const statGrid = document.createElement("div");
    statGrid.className = "char-field-grid";
    const statLabels = {
      hp: "HP +",
      atk: "Atk +",
      def: "Def +",
      spatk: "SpA +",
      spdef: "SpD +",
      spd: "Spd +",
    };
    _POKEMON_STAT_POINT_KEYS.forEach((key) => {
      const field = document.createElement("label");
      field.className = "char-field";
      field.textContent = statLabels[key] || `${key} +`;
      const input = document.createElement("input");
      input.type = "number";
      input.min = "0";
      input.step = "1";
      input.value = String(Number(statPoints[key] || 0));
      input.addEventListener("input", () => {
        const next = Number(input.value || 0);
        statPoints[key] = Number.isFinite(next) ? Math.max(0, Math.floor(next)) : 0;
        build.stat_points = statPoints;
        saveCharacterToStorage();
        renderCharacterPokemonTeam();
      });
      field.appendChild(input);
      statGrid.appendChild(field);
    });
    card.appendChild(statGrid);
    const statQolRow = document.createElement("div");
    statQolRow.className = "char-action-row";
    const autoWeightedBtn = document.createElement("button");
    autoWeightedBtn.type = "button";
    autoWeightedBtn.className = "char-mini-button";
    autoWeightedBtn.textContent = "Auto Stats";
    autoWeightedBtn.addEventListener("click", () => {
      if (_applyAutoPokemonStatPoints(build, speciesEntry, "weighted")) {
        saveCharacterToStorage();
        renderCharacterPokemonTeam();
      }
    });
    const autoEvenBtn = document.createElement("button");
    autoEvenBtn.type = "button";
    autoEvenBtn.className = "char-mini-button";
    autoEvenBtn.textContent = "Even Stats";
    autoEvenBtn.addEventListener("click", () => {
      if (_applyAutoPokemonStatPoints(build, speciesEntry, "even")) {
        saveCharacterToStorage();
        renderCharacterPokemonTeam();
      }
    });
    const fillRemainingBtn = document.createElement("button");
    fillRemainingBtn.type = "button";
    fillRemainingBtn.className = "char-mini-button";
    fillRemainingBtn.textContent = "Fill Missing";
    fillRemainingBtn.addEventListener("click", () => {
      if (_fillRemainingPokemonStatPoints(build, speciesEntry, "weighted")) {
        saveCharacterToStorage();
        renderCharacterPokemonTeam();
      }
    });
    const clearStatsBtn = document.createElement("button");
    clearStatsBtn.type = "button";
    clearStatsBtn.className = "char-mini-button";
    clearStatsBtn.textContent = "Clear Stats";
    clearStatsBtn.addEventListener("click", () => {
      if (_clearPokemonStatPoints(build)) {
        saveCharacterToStorage();
        renderCharacterPokemonTeam();
      }
    });
    statQolRow.appendChild(autoWeightedBtn);
    statQolRow.appendChild(autoEvenBtn);
    statQolRow.appendChild(fillRemainingBtn);
    statQolRow.appendChild(clearStatsBtn);
    card.appendChild(statQolRow);

    if (!Array.isArray(build.poke_edges)) build.poke_edges = [];
    const legality = _pokemonBuildLegality(build);
    const legalityBox = document.createElement("div");
    legalityBox.className = `char-legality-box ${legality.ok ? "is-legal" : "is-invalid"}`;
    const legalityTitle = document.createElement("div");
    legalityTitle.className = "char-legality-title";
    legalityTitle.textContent = legality.ok ? "Legality: valid" : "Legality: invalid";
    legalityBox.appendChild(legalityTitle);
    if (!legality.issues.length) {
      const okNote = document.createElement("div");
      okNote.className = "char-feature-meta";
      okNote.textContent = "All species, level, move, ability, item, and Poke Edge checks passed.";
      legalityBox.appendChild(okNote);
    } else {
      const issueList = document.createElement("div");
      issueList.className = "char-legality-list";
      legality.issues.forEach((issue) => {
        const row = document.createElement("div");
        row.className = `char-legality-item ${issue.severity === "error" ? "is-error" : "is-warn"}`;
        row.textContent = issue.message;
        issueList.appendChild(row);
      });
      legalityBox.appendChild(issueList);
    }
    card.appendChild(legalityBox);

    const lists = document.createElement("div");
    lists.className = "char-list-panel";

    const fillRow = document.createElement("div");
    fillRow.className = "char-action-row";
    const fillInfo = document.createElement("div");
    fillInfo.className = "char-feature-meta";
    fillInfo.textContent = "Auto-fill from this species at the build's current level";
    const fillBtn = document.createElement("button");
    fillBtn.type = "button";
    fillBtn.className = "char-mini-button";
    fillBtn.textContent = "Fill from Species";
    fillBtn.addEventListener("click", () => {
      const entry = _getPokemonSpeciesEntry(build.species || build.name || "");
      if (!entry) {
        alert("Species not found in dataset.");
        return;
      }
      build.level = _clampPokemonLevel(build.level || _defaultPokemonBuildLevel(), _defaultPokemonBuildLevel());
      const result = _autoFillPokemonBuild(build, entry, true);
      _sanitizePokemonBuildForLevel(build, entry);
      if (!result.filled && result.message) {
        alert(result.message);
      }
      saveCharacterToStorage();
      renderCharacterPokemonTeam();
    });
    fillRow.appendChild(fillInfo);
    fillRow.appendChild(fillBtn);
    lists.appendChild(fillRow);

    const moveRow = document.createElement("div");
    moveRow.className = "char-action-row";
    const moveLabel = document.createElement("div");
    moveLabel.className = "char-feature-meta";
    moveLabel.textContent = "Moves (click a selected move for a simple explanation)";
    const addMove = document.createElement("button");
    addMove.type = "button";
    addMove.className = "char-mini-button";
    addMove.textContent = "Add Move";
    addMove.addEventListener("click", () => {
      const speciesForBuild = _getPokemonSpeciesEntry(build.species || build.name || "");
      const items = _movePickerItemsForBuild(build, speciesForBuild);
      openListPicker({
        title: "Add Move",
        helpText: "Search by move name, type, class, range, or simple effect. Learnable moves for this species and level are shown first.",
        items,
        onSelect: (name) => {
          if (!Array.isArray(build.moves)) build.moves = [];
          if (!build.moves.includes(name)) build.moves.push(name);
          saveCharacterToStorage();
          renderCharacterPokemonTeam();
        },
      });
    });
    moveRow.appendChild(moveLabel);
    moveRow.appendChild(addMove);
    lists.appendChild(moveRow);
    const moveList = document.createElement("div");
    moveList.className = "char-visual-token-list";
    (build.moves || []).forEach((name) => {
      const moveEntry = _getMoveDetail(name);
      const cachedMeta = pokeApiCacheGet(pokeApiMoveMetaCache, name);
      if (!pokeApiCacheHas(pokeApiMoveMetaCache, name)) ensureMoveMeta(name).then(() => _queueBuilderRerender());
      const typeName = moveEntry?.type || cachedMeta?.type || "";
      const typeIcon = cachedMeta?.type_icon_url || typeIconFromCache(typeName);
      if (typeName && !typeIcon && !pokeApiCacheHas(pokeApiTypeIconCache, typeName)) {
        ensureTypeIcon(typeName).then(() => _queueBuilderRerender());
      }
      const row = document.createElement("div");
      row.className = "char-visual-token";
      row.addEventListener("click", () => showMoveDetail(name));
      const icon = document.createElement("span");
      icon.className = "char-visual-token-icon";
      if (typeIcon) {
        const img = document.createElement("img");
        img.src = typeIcon;
        img.alt = typeName || "Type";
        img.loading = "lazy";
        icon.appendChild(img);
      } else {
        icon.textContent = "M";
      }
      const body = document.createElement("span");
      body.className = "char-visual-token-body";
      const title = document.createElement("span");
      title.className = "char-visual-token-title";
      title.textContent = name;
      const meta = document.createElement("span");
      meta.className = "char-visual-token-meta";
      meta.textContent = `${typeName || "-"} | ${moveEntry?.category || "-"} | DB ${moveEntry?.damage_base ?? "-"}`;
      body.appendChild(title);
      body.appendChild(meta);
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "char-mini-button";
      remove.textContent = "Remove";
      remove.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        build.moves = (build.moves || []).filter((n) => n !== name);
        saveCharacterToStorage();
        renderCharacterPokemonTeam();
      });
      row.appendChild(icon);
      row.appendChild(body);
      row.appendChild(remove);
      moveList.appendChild(row);
    });
    if (!(build.moves || []).length) {
      const empty = document.createElement("span");
      empty.className = "char-feature-meta";
      empty.textContent = "No moves selected.";
      moveList.appendChild(empty);
    }
    lists.appendChild(moveList);

    const abilityRow = document.createElement("div");
    abilityRow.className = "char-action-row";
    const abilityLabel = document.createElement("div");
    abilityLabel.className = "char-feature-meta";
    abilityLabel.textContent = "Abilities (click a selected ability for a simple explanation)";
    const addAbility = document.createElement("button");
    addAbility.type = "button";
    addAbility.className = "char-mini-button";
    addAbility.textContent = "Add Ability";
    addAbility.addEventListener("click", () => {
      const speciesForBuild = _getPokemonSpeciesEntry(build.species || build.name || "");
      const items = _abilityPickerItemsForBuild(build, speciesForBuild);
      openListPicker({
        title: "Add Ability",
        helpText: "Search by ability name, pool, trigger, or plain-English summary. Species-legal abilities for this build are shown first.",
        items,
        onSelect: (name) => {
          if (!Array.isArray(build.abilities)) build.abilities = [];
          if (!build.abilities.includes(name)) build.abilities.push(name);
          saveCharacterToStorage();
          renderCharacterPokemonTeam();
        },
      });
    });
    abilityRow.appendChild(abilityLabel);
    abilityRow.appendChild(addAbility);
    lists.appendChild(abilityRow);
    const abilityList = document.createElement("div");
    abilityList.className = "char-visual-token-list";
    (build.abilities || []).forEach((name) => {
      const cachedMeta = pokeApiCacheGet(pokeApiAbilityMetaCache, name);
      if (!pokeApiCacheHas(pokeApiAbilityMetaCache, name)) ensureAbilityMeta(name).then(() => _queueBuilderRerender());
      const row = document.createElement("div");
      row.className = "char-visual-token";
      row.addEventListener("click", () => showAbilityDetail(name));
      const icon = document.createElement("span");
      icon.className = "char-visual-token-icon";
      icon.textContent = "A";
      const body = document.createElement("span");
      body.className = "char-visual-token-body";
      const title = document.createElement("span");
      title.className = "char-visual-token-title";
      title.textContent = name;
      const meta = document.createElement("span");
      meta.className = "char-visual-token-meta";
      meta.textContent = _firstSentence(cachedMeta?.effect || cachedMeta?.description || "Ability details");
      body.appendChild(title);
      body.appendChild(meta);
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "char-mini-button";
      remove.textContent = "Remove";
      remove.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        build.abilities = (build.abilities || []).filter((n) => n !== name);
        saveCharacterToStorage();
        renderCharacterPokemonTeam();
      });
      row.appendChild(icon);
      row.appendChild(body);
      row.appendChild(remove);
      abilityList.appendChild(row);
    });
    if (!(build.abilities || []).length) {
      const empty = document.createElement("span");
      empty.className = "char-feature-meta";
      empty.textContent = "No abilities selected.";
      abilityList.appendChild(empty);
    }
    lists.appendChild(abilityList);

    const itemRow = document.createElement("div");
    itemRow.className = "char-action-row";
    const itemLabel = document.createElement("div");
    itemLabel.className = "char-feature-meta";
    itemLabel.textContent = "Items";
    const addItem = document.createElement("button");
    addItem.type = "button";
    addItem.className = "char-mini-button";
    addItem.textContent = "Add Item";
    addItem.addEventListener("click", () => {
      const items = _itemPickerItems();
      openListPicker({
        title: "Add Item",
        helpText: "Search by item name, category, slot, cost, or simple effect.",
        items,
        onSelect: (name) => {
          if (!Array.isArray(build.items)) build.items = [];
          if (!build.items.includes(name)) build.items.push(name);
          saveCharacterToStorage();
          renderCharacterPokemonTeam();
        },
      });
    });
    itemRow.appendChild(itemLabel);
    itemRow.appendChild(addItem);
    lists.appendChild(itemRow);
    const itemList = document.createElement("div");
    itemList.className = "char-visual-token-list";
    (build.items || []).forEach((name) => {
      const cachedMeta = pokeApiCacheGet(pokeApiItemMetaCache, name);
      if (!pokeApiCacheHas(pokeApiItemMetaCache, name)) ensureItemMeta(name).then(() => _queueBuilderRerender());
      const entry = _findItemByName(name);
      const row = document.createElement("div");
      row.className = "char-visual-token";
      row.addEventListener("click", () => showItemDetail(name));
      const icon = document.createElement("span");
      icon.className = "char-visual-token-icon";
      if (cachedMeta?.icon_url) {
        const img = document.createElement("img");
        img.src = cachedMeta.icon_url;
        img.alt = name;
        img.loading = "lazy";
        icon.appendChild(img);
      } else {
        icon.textContent = "I";
      }
      const body = document.createElement("span");
      body.className = "char-visual-token-body";
      const title = document.createElement("span");
      title.className = "char-visual-token-title";
      title.textContent = _pokemonBuildItemLabel(name);
      const meta = document.createElement("span");
      meta.className = "char-visual-token-meta";
      meta.textContent = `${entry?.category || "Item"}${_hasDisplayValue(entry?.cost) ? ` | $${entry.cost}` : ""}`;
      body.appendChild(title);
      body.appendChild(meta);
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "char-mini-button";
      remove.textContent = "Remove";
      remove.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        build.items = (build.items || []).filter((n) => n !== name);
        saveCharacterToStorage();
        renderCharacterPokemonTeam();
      });
      row.appendChild(icon);
      row.appendChild(body);
      row.appendChild(remove);
      itemList.appendChild(row);
    });
    if (!(build.items || []).length) {
      const empty = document.createElement("span");
      empty.className = "char-feature-meta";
      empty.textContent = "No items selected.";
      itemList.appendChild(empty);
    }
    lists.appendChild(itemList);

    const pokeEdgeRow = document.createElement("div");
    pokeEdgeRow.className = "char-action-row";
    const pokeEdgeLabel = document.createElement("div");
    pokeEdgeLabel.className = "char-feature-meta";
    pokeEdgeLabel.textContent = "Poke Edges";
    const addPokeEdge = document.createElement("button");
    addPokeEdge.type = "button";
    addPokeEdge.className = "char-mini-button";
    addPokeEdge.textContent = "Add Poke Edge";
    addPokeEdge.addEventListener("click", () => {
      const names = _pokeEdgePickerItems();
      openListPicker({
        title: "Add Poke Edge",
        helpText: "Search by Poke Edge name, prerequisite, cost, or simple effect.",
        items: names,
        onSelect: (name) => {
          if (!Array.isArray(build.poke_edges)) build.poke_edges = [];
          if (!build.poke_edges.includes(name)) build.poke_edges.push(name);
          saveCharacterToStorage();
          renderCharacterPokemonTeam();
        },
      });
    });
    pokeEdgeRow.appendChild(pokeEdgeLabel);
    pokeEdgeRow.appendChild(addPokeEdge);
    lists.appendChild(pokeEdgeRow);
    const pokeEdgeList = document.createElement("div");
    pokeEdgeList.className = "char-visual-token-list";
    (build.poke_edges || []).forEach((name) => {
      const row = document.createElement("div");
      row.className = "char-visual-token";
      const icon = document.createElement("span");
      icon.className = "char-visual-token-icon";
      icon.textContent = "E";
      const body = document.createElement("span");
      body.className = "char-visual-token-body";
      const title = document.createElement("span");
      title.className = "char-visual-token-title";
      title.textContent = name;
      const meta = document.createElement("span");
      meta.className = "char-visual-token-meta";
      meta.textContent = "Poke Edge";
      body.appendChild(title);
      body.appendChild(meta);
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "char-mini-button";
      remove.textContent = "Remove";
      remove.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        build.poke_edges = (build.poke_edges || []).filter((n) => n !== name);
        saveCharacterToStorage();
        renderCharacterPokemonTeam();
      });
      row.appendChild(icon);
      row.appendChild(body);
      row.appendChild(remove);
      pokeEdgeList.appendChild(row);
    });
    if (!(build.poke_edges || []).length) {
      const empty = document.createElement("span");
      empty.className = "char-feature-meta";
      empty.textContent = "No Poke Edges selected.";
      pokeEdgeList.appendChild(empty);
    }
    lists.appendChild(pokeEdgeList);
    card.appendChild(lists);

    const removeRow = document.createElement("div");
    removeRow.className = "char-action-row";
    const moveUp = document.createElement("button");
    moveUp.type = "button";
    moveUp.className = "char-mini-button";
    moveUp.textContent = "Move Up";
    moveUp.disabled = idx <= 0;
    moveUp.addEventListener("click", () => {
      if (idx <= 0) return;
      const [entry] = builds.splice(idx, 1);
      builds.splice(idx - 1, 0, entry);
      saveCharacterToStorage();
      renderCharacterPokemonTeam();
    });
    const moveDown = document.createElement("button");
    moveDown.type = "button";
    moveDown.className = "char-mini-button";
    moveDown.textContent = "Move Down";
    moveDown.disabled = idx >= builds.length - 1;
    moveDown.addEventListener("click", () => {
      if (idx >= builds.length - 1) return;
      const [entry] = builds.splice(idx, 1);
      builds.splice(idx + 1, 0, entry);
      saveCharacterToStorage();
      renderCharacterPokemonTeam();
    });
    const duplicate = document.createElement("button");
    duplicate.type = "button";
    duplicate.className = "char-mini-button";
    duplicate.textContent = "Duplicate";
    duplicate.addEventListener("click", () => {
      if (builds.length >= teamLimit) {
        alert(`Team limit reached (${teamLimit}). Increase the limit to duplicate this Pokemon.`);
        return;
      }
      builds.splice(idx + 1, 0, _duplicatePokemonBuild(build));
      saveCharacterToStorage();
      renderCharacterPokemonTeam();
    });
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "char-mini-button";
    remove.textContent = "Remove Pokemon";
    remove.addEventListener("click", () => {
      if (!confirm(`Remove ${build.name || build.species || "this Pokemon"}?`)) return;
      builds.splice(idx, 1);
      saveCharacterToStorage();
      renderCharacterPokemonTeam();
    });
    removeRow.appendChild(moveUp);
    removeRow.appendChild(moveDown);
    removeRow.appendChild(duplicate);
    removeRow.appendChild(remove);
    card.appendChild(removeRow);

    teamPanel.appendChild(card);
  });

  if (!shownCount && builds.length) {
    const empty = document.createElement("div");
    empty.className = "char-empty";
    empty.textContent = "No Pokemon match current roster search/filter.";
    teamPanel.appendChild(empty);
  }

  charContentEl.appendChild(teamPanel);
}

function _findSkillRank(skillName) {
  return characterState.skills[skillName] || "Untrained";
}

function _rankIndex(rank, rules) {
  const ranks = rules.ranks || [];
  const idx = ranks.indexOf(rank);
  return idx >= 0 ? idx : 0;
}

function _parseSkillRequirements(prereq, rules, skills) {
  const out = [];
  if (!prereq) return out;
  const ranks = rules.ranks || [];
  const rankPattern = ranks.join("|");
  const skillNamePattern = "([A-Za-z][A-Za-z.'\\s-]*)";
  const rankRegex = new RegExp(`(${rankPattern})\\s+${skillNamePattern}`, "gi");
  let match;
  while ((match = rankRegex.exec(prereq)) !== null) {
    const rank = match[1];
    const raw = match[2].trim();
    const skill = skills.find((s) => raw.toLowerCase().includes(String(s).toLowerCase()));
    if (skill) {
      out.push({ skill, rank });
    }
  }
  const atRegex = new RegExp(`${skillNamePattern}\\s+at\\s+(${rankPattern})`, "gi");
  while ((match = atRegex.exec(prereq)) !== null) {
    const raw = match[1].trim();
    const rank = match[2];
    const skill = skills.find((s) => raw.toLowerCase().includes(String(s).toLowerCase()));
    if (skill) {
      out.push({ skill, rank });
    }
  }
  return out;
}

function _escapeRegex(text) {
  return String(text || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function _toastDrop(reason) {
  if (reason) notifyUI("warn", reason);
}

function _sortableEnabled() {
  return typeof window.Sortable !== "undefined";
}

function _buildDeckCard(entry, statusInfo, kind, rank) {
  const card = document.createElement("div");
  card.className = `char-deck-card status-${statusInfo.status}`;
  card.dataset.entryName = entry.name;
  card.dataset.entryKind = kind;
  if (rank) card.dataset.entryRank = String(rank);
  const title = document.createElement("div");
  title.className = "char-deck-title";
  title.textContent = entry.name;
  const status = document.createElement("span");
  status.className = `status-pill ${statusInfo.status}`;
  status.textContent = statusInfo.status;
  card.appendChild(title);
  card.appendChild(status);
  return card;
}

function _buildShelfCard(name, kind, rank) {
  const card = document.createElement("div");
  card.className = "char-shelf-card";
  card.dataset.entryName = name;
  card.dataset.entryKind = kind;
  if (rank) card.dataset.entryRank = String(rank);
  const title = document.createElement("div");
  title.className = "char-shelf-title";
  title.textContent = name;
  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "char-shelf-remove";
  remove.textContent = "Remove";
  remove.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (kind === "feature") {
      characterState.features.delete(name);
      _removeFromOrder(characterState.feature_order, name);
      saveCharacterToStorage();
      renderCharacterFeatures();
    } else if (kind === "edge") {
      characterState.edges.delete(name);
      _removeFromOrder(characterState.edge_order, name);
      saveCharacterToStorage();
      renderCharacterEdges();
    }
  });
  card.appendChild(title);
  card.appendChild(remove);
  return card;
}

function _initDeckSortable(deckEl, kind) {
  if (!_sortableEnabled() || !deckEl) return;
  const sortable = new Sortable(deckEl, {
    group: { name: kind, pull: "clone", put: false },
    sort: false,
    animation: 120,
    ghostClass: "char-ghost",
    draggable: ".char-deck-card",
  });
  _registerSortable(sortable);
}

function _initShelfSortable(shelfEl, kind, getReason, onAccept, onReorder) {
  if (!_sortableEnabled() || !shelfEl) return;
  let lastReason = "";
  const sortable = new Sortable(shelfEl, {
    group: { name: kind, pull: true, put: true },
    animation: 140,
    ghostClass: "char-ghost",
    draggable: ".char-shelf-card, .char-deck-card",
    onMove: (evt) => {
      const item = evt.dragged || evt.related;
      const name = item?.dataset?.entryName;
      const rank = Number(item?.dataset?.entryRank || 0) || null;
      lastReason = getReason ? getReason(name, rank, evt.to, evt) : "";
      evt.to.classList.toggle("slot-invalid", !!lastReason);
      return true;
    },
    onAdd: (evt) => {
      evt.to.classList.remove("slot-invalid");
      const item = evt.item;
      const name = item?.dataset?.entryName;
      const rank = Number(item?.dataset?.entryRank || 0) || null;
      const reason = getReason ? getReason(name, rank, evt.to, evt) : "";
      if (reason) {
        item.remove();
        _toastDrop(reason);
        lastReason = "";
        return;
      }
      if (typeof onAccept === "function") {
        onAccept(name, rank, evt.to);
      }
    },
    onUpdate: () => {
      if (typeof onReorder === "function") onReorder();
    },
    onEnd: () => {
      if (lastReason) {
        _toastDrop(lastReason);
        lastReason = "";
      }
    },
  });
  _registerSortable(sortable);
}

function _namePattern(name) {
  const trimmed = String(name || "").trim();
  if (!trimmed) return null;
  return new RegExp(`(?:^|[^\\w])${_escapeRegex(trimmed)}(?:$|[^\\w])`, "i");
}

function _matchNamesInPrereq(prereq, names) {
  if (!prereq) return [];
  const matches = [];
  const text = String(prereq);
  names.forEach((name) => {
    const trimmed = String(name || "").trim();
    if (trimmed.length < 3) return;
    const pattern = _namePattern(trimmed);
    if (pattern && pattern.test(text)) {
      matches.push(trimmed);
    }
  });
  return matches;
}

function _prereqHasOr(prereq) {
  return /\bor\b/i.test(String(prereq || ""));
}

function _isPermissionLocked(prereq) {
  const text = String(prereq || "").toLowerCase();
  return text.includes("gm permission") || text.includes("gm approval") || text.includes("gm only");
}

function _isUnparsedStrict(prereq, parsedCount) {
  if (!prereq) return false;
  if (parsedCount > 0) return false;
  return true;
}

const PREREQ_AST_VERSION = 1;
const _prereqAstCache = new Map();

function _splitByOr(text) {
  return String(text || "")
    .split(/\s+or\s+/i)
    .map((part) => part.trim())
    .filter(Boolean);
}

function _splitByAnd(text) {
  return String(text || "")
    .split(/\s+and\s+|,\s*/i)
    .map((part) => part.trim())
    .filter(Boolean);
}

function _parseTagCountRule(segment) {
  const match =
    segment.match(/(\d+)\s+features?.*?\[([^\]]+)\].*?tag/i) ||
    segment.match(/feature\s+with\s+the\s+\[([^\]]+)\]\s+tag/i);
  if (!match) return null;
  if (match.length === 3) {
    return { type: "countFeaturesWithTag", tag: match[2], op: ">=", value: Number(match[1]) || 1 };
  }
  return { type: "countFeaturesWithTag", tag: match[1], op: ">=", value: 1 };
}

function _parsePrereqSegment(segment) {
  const rules = characterData?.skill_rules || { ranks: [] };
  const skills = characterData?.skills || [];
  const items = [];
  const levelMatch = segment.match(/Level\s*(\d+)/i);
  if (levelMatch) {
    items.push({ type: "level", op: ">=", value: Number(levelMatch[1]) });
  }
  const tagRule = _parseTagCountRule(segment);
  if (tagRule) items.push(tagRule);

  const reqs = _parseSkillRequirements(segment, rules, skills);
  reqs.forEach((req) => {
    items.push({ type: "skill", skillId: req.skill, op: ">=", value: req.rank });
  });

  const classNames = (characterData?.classes || []).map((c) => c.name);
  const mentionedClasses = _matchNamesInPrereq(segment, classNames);
  mentionedClasses.forEach((name) => {
    items.push({ type: "hasClass", classId: name });
  });

  const featureNames = (characterData?.features || []).map((f) => f.name);
  const edgeNames = (characterData?.edges_catalog || []).map((e) => e.name);
  const mentionedFeatures = _matchNamesInPrereq(segment, featureNames);
  const mentionedEdges = _matchNamesInPrereq(segment, edgeNames);
  mentionedFeatures.forEach((name) => items.push({ type: "hasFeature", featureId: name }));
  mentionedEdges.forEach((name) => items.push({ type: "hasFeature", featureId: name }));

  if (_isPermissionLocked(segment)) {
    items.push({ type: "manual", label: "GM Permission" });
  }

  if (!items.length) {
    items.push({ type: "note", label: segment });
  }
  return items;
}

function buildPrereqAst(prereq) {
  if (!prereq) return null;
  const text = String(prereq || "").trim();
  if (!text) return null;
  const cached = _prereqAstCache.get(text);
  if (cached) return cached;
  const orParts = _splitByOr(text);
  const rules = [];
  orParts.forEach((part) => {
    const andParts = _splitByAnd(part);
    const andRules = [];
    andParts.forEach((seg) => {
      andRules.push(..._parsePrereqSegment(seg));
    });
    if (andRules.length === 1) {
      rules.push(andRules[0]);
    } else {
      rules.push({ type: "and", rules: andRules });
    }
  });
  let ast = null;
  if (rules.length === 1) {
    ast = rules[0];
  } else {
    ast = { type: "or", rules };
  }
  _prereqAstCache.set(text, ast);
  return ast;
}

function _featureTagMap() {
  const map = new Map();
  (characterData?.nodes || []).forEach((node) => {
    if (!node || node.type !== "feature") return;
    if (!node.name) return;
    map.set(node.name, extractFeatureTags(node));
  });
  (characterData?.features || []).forEach((entry) => {
    if (!entry?.name) return;
    if (!map.has(entry.name)) {
      map.set(entry.name, extractFeatureTags(entry));
    }
  });
  return map;
}

function _buildPrereqContext() {
  const rules = characterData?.skill_rules || { ranks: [] };
  const level = Number(characterState.profile.level || 1);
  const className = _currentClassName();
  const tagMap = _featureTagMap();
  return {
    level,
    rules,
    className,
    skills: characterState.skills || {},
    features: characterState.features || new Set(),
    edges: characterState.edges || new Set(),
    tagMap,
  };
}

function _ruleLabel(rule) {
  if (!rule) return "";
  if (rule.type === "level") return `Level ${rule.value}`;
  if (rule.type === "skill") return `${rule.value} ${rule.skillId}`;
  if (rule.type === "hasClass") return `Class ${rule.classId}`;
  if (rule.type === "hasFeature") return rule.featureId;
  if (rule.type === "countFeaturesWithTag") return `${rule.value} feature(s) with [${rule.tag}] tag`;
  if (rule.type === "manual") return rule.label || "Manual requirement";
  if (rule.type === "note") return rule.label || "Requirement";
  return "Requirement";
}

const KEYWORD_HELP = {
  "at-will": "At-Will: can be used any time without per-scene or per-day limits.",
  eot: "EOT: usable once each turn.",
  scene: "Scene: usable once per scene unless otherwise stated.",
  daily: "Daily: usable once per day unless otherwise stated.",
  bind: "Bind: costs AP to maintain; remains active while bound.",
  drain: "Drain: AP is spent and only refreshes on Extended Rest.",
  ap: "AP: Action Points used to fuel features and boosts.",
  "swift action": "Swift Action: a quick action taken alongside a Standard Action.",
  "shift action": "Shift Action: repositioning or minor action.",
  "standard action": "Standard Action: main action for your turn.",
  "free action": "Free Action: minor action that does not consume your main action.",
  interrupt: "Interrupt: can be used out of turn when the trigger occurs.",
  priority: "Priority: resolves before normal actions at the same timing.",
  "set-up": "Set-Up: requires a preparation phase before resolution.",
  burst: "Burst: area of effect centered on the target square.",
  blast: "Blast: area of effect at range.",
  cone: "Cone: area of effect in a cone shape.",
  line: "Line: area of effect in a straight line.",
  melee: "Melee: short range, adjacent target.",
  ranged: "Ranged: attacks from distance.",
  groundsource: "Groundsource: originates from the ground; special terrain interactions.",
  smite: "Smite: enhanced damage/resolution effect on hit.",
  friendly: "Friendly: does not harm allies.",
  social: "Social: uses social-move interactions and defenses.",
  sonic: "Sonic: sound-based move; interacts with sonic effects.",
  powder: "Powder: powder-based move; interacts with powder effects.",
  illusion: "Illusion: interacts with illusion detection and counters.",
  weather: "Weather: interacts with weather effects and conditions.",
  hazard: "Hazard: creates persistent battlefield effects.",
  cs: "CS: Combat Stage; temporary stat stage changes.",
  db: "DB: Damage Base; used to compute damage.",
};

function _keywordHelpList(text) {
  const source = String(text || "");
  if (!source) return [];
  const found = new Map();
  const lower = source.toLowerCase();
  Object.keys(STATUS_KEYWORD_HELP).forEach((key) => {
    if (lower.includes(key)) found.set(key, STATUS_KEYWORD_HELP[key]);
  });
  Object.entries(KEYWORD_HELP).forEach(([key, desc]) => {
    if (lower.includes(key)) found.set(key, desc);
  });
  return Array.from(found.entries()).map(([key, desc]) => `${key}: ${desc}`);
}

function _attachKeywordTooltip(target, text) {
  if (!target) return;
  const lines = _keywordHelpList(text);
  if (!lines.length) return;
  _setTooltipAttrs(target, "Keywords", lines.join("\n"));
}

function _evaluateRule(rule, context) {
  const { rules, skills, level, className, features, edges, tagMap } = context;
  if (rule.type === "level") {
    return level >= Number(rule.value || 0);
  }
  if (rule.type === "skill") {
    const current = skills[rule.skillId] || "Untrained";
    return _rankIndex(current, rules) >= _rankIndex(rule.value, rules);
  }
  if (rule.type === "hasClass") {
    if (!className) return false;
    const pattern = _namePattern(rule.classId);
    return pattern ? pattern.test(className) : false;
  }
  if (rule.type === "hasFeature") {
    return features.has(rule.featureId) || edges.has(rule.featureId);
  }
  if (rule.type === "countFeaturesWithTag") {
    const needed = Number(rule.value || 0);
    let count = 0;
    features.forEach((name) => {
      const tags = tagMap.get(name) || [];
      if (tags.some((tag) => String(tag).toLowerCase() === String(rule.tag).toLowerCase())) {
        count += 1;
      }
    });
    return count >= needed;
  }
  if (rule.type === "manual") {
    return false;
  }
  if (rule.type === "note") {
    return false;
  }
  return false;
}

function evaluatePrereqTree(ast, context) {
  if (!ast) return { ok: true, type: "and", label: "", children: [] };
  if (ast.type === "and" || ast.type === "or") {
    const children = (ast.rules || []).map((rule) => evaluatePrereqTree(rule, context));
    const ok = ast.type === "and" ? children.every((c) => c.ok) : children.some((c) => c.ok);
    return { ok, type: ast.type, label: ast.type === "and" ? "All of:" : "Any of:", children };
  }
  const ok = _evaluateRule(ast, context);
  return { ok, type: ast.type, label: _ruleLabel(ast), children: [] };
}

function _collectMissing(tree, out = []) {
  if (!tree) return out;
  if (!tree.children || !tree.children.length) {
    if (!tree.ok && tree.label) out.push(tree.label);
    return out;
  }
  tree.children.forEach((child) => _collectMissing(child, out));
  return out;
}

function _collectManual(tree) {
  if (!tree) return false;
  if (tree.type === "manual" || tree.type === "note") return true;
  return (tree.children || []).some((child) => _collectManual(child));
}

function getPrereqEvaluation(prereq) {
  if (!prereq) return { ok: true, missing: [], tree: null, hasManual: false };
  const ast = buildPrereqAst(prereq);
  const context = _buildPrereqContext();
  const tree = evaluatePrereqTree(ast, context);
  const missing = _collectMissing(tree, []);
  const hasManual = _collectManual(tree);
  return { ok: tree.ok, missing, tree, hasManual };
}

function _currentClassName() {
  ensurePlaytestScopeForClass(characterState.feature_class_filter);
  const classEntry = (characterData.classes || []).find((cls) => cls.id === characterState.class_id);
  return classEntry?.name || "";
}

function _prereqBreakdown(prereq) {
  const rules = characterData.skill_rules || { ranks: [] };
  const skills = characterData.skills || [];
  const level = Number(characterState.profile.level || 1);
  const className = _currentClassName();
  const lines = [];
  if (!prereq) return lines;

  if (_isPermissionLocked(prereq)) {
    lines.push("[MISS] GM Permission required");
  }

  const levelMatches = prereq.match(/Level\s*(\d+)/gi) || [];
  levelMatches.forEach((match) => {
    const num = Number(match.replace(/\D+/g, ""));
    if (!Number.isFinite(num)) return;
    const ok = level >= num;
    lines.push(`${ok ? "[OK]" : "[MISS]"} Level ${num} (current ${level})`);
  });

  const classNames = (characterData.classes || []).map((c) => c.name);
  const mentionedClasses = _matchNamesInPrereq(prereq, classNames);
  if (mentionedClasses.length) {
    const ok =
      className &&
      mentionedClasses.some((name) => {
        const pattern = _namePattern(name);
        return pattern ? pattern.test(className) : false;
      });
    lines.push(`${ok ? "[OK]" : "[MISS]"} Class ${mentionedClasses[0]} (current ${className || "none"})`);
    if (className) {
      const classRankMatch = prereq.match(new RegExp(`${_escapeRegex(className)}\\s*(\\d+)`, "i"));
      if (classRankMatch) {
        const neededLevel = Number(classRankMatch[1] || 0);
        if (Number.isFinite(neededLevel)) {
          const okRank = level >= neededLevel;
          lines.push(`${okRank ? "[OK]" : "[MISS]"} Class level ${neededLevel} (current ${level})`);
        }
      }
    }
  }

  const featureNames = (characterData.features || []).map((f) => f.name);
  const edgeNames = (characterData.edges_catalog || []).map((e) => e.name);
  const mentionedFeatures = _matchNamesInPrereq(prereq, featureNames);
  const mentionedEdges = _matchNamesInPrereq(prereq, edgeNames);
  const hasOr = _prereqHasOr(prereq);
  if (mentionedFeatures.length) {
    if (hasOr) {
      lines.push("Any of:");
      mentionedFeatures.forEach((name) => {
        lines.push(`${characterState.features.has(name) ? "[OK]" : "[MISS]"} Feature ${name}`);
      });
    } else {
      mentionedFeatures.forEach((name) => {
        lines.push(`${characterState.features.has(name) ? "[OK]" : "[MISS]"} Feature ${name}`);
      });
    }
  }
  if (mentionedEdges.length) {
    if (hasOr) {
      lines.push("Any of:");
      mentionedEdges.forEach((name) => {
        lines.push(`${characterState.edges.has(name) ? "[OK]" : "[MISS]"} Edge ${name}`);
      });
    } else {
      mentionedEdges.forEach((name) => {
        lines.push(`${characterState.edges.has(name) ? "[OK]" : "[MISS]"} Edge ${name}`);
      });
    }
  }

  const reqs = _parseSkillRequirements(prereq, rules, skills);
  reqs.forEach((req) => {
    const haveRank = _findSkillRank(req.skill);
    const ok = _rankIndex(haveRank, rules) >= _rankIndex(req.rank, rules);
    lines.push(`${ok ? "[OK]" : "[MISS]"} ${req.rank} ${req.skill} (current ${haveRank})`);
  });

  return lines;
}

function buildPrereqDetail(prereq) {
  if (!prereq) return "Prerequisites: none.";
  const info = getPrereqEvaluation(prereq);
  if (info.ok) return "Prerequisites: met.";
  if (!info.missing.length) return "Prerequisites: check required.";
  return `Missing: ${info.missing.join(", ")}`;
}

function isFeatureAllowed(node, override) {
  if (override) return true;
  if (!node) return false;
  const prereq = node.prerequisites || "";
  if (!prereq) return true;
  const info = getPrereqEvaluation(prereq);
  if (info.hasManual) return false;
  return info.ok;
}

function isEdgeAllowed(entry, override) {
  if (override) return true;
  if (!entry) return false;
  const prereq = entry.prerequisites || "";
  if (!prereq) return true;
  const info = getPrereqEvaluation(prereq);
  if (info.hasManual) return false;
  return info.ok;
}

function prereqStatus(prereq, type = "feature") {
  if (!prereq) {
    return { status: "available", missing: [], impossible: false, tree: null };
  }
  if (characterState.override_prereqs) {
    return { status: "available", missing: [], impossible: false, tree: null };
  }
  const info = getPrereqEvaluation(prereq);
  if (info.hasManual) return { status: "blocked", missing: info.missing, impossible: true, tree: info.tree };
  if (info.ok) return { status: "available", missing: [], impossible: false, tree: info.tree };
  if (info.missing.length <= 1) return { status: "close", missing: info.missing, impossible: false, tree: info.tree };
  return { status: "unavailable", missing: info.missing, impossible: false, tree: info.tree };
}

function renderPrereqChecklist(prereq, target) {
  if (!prereq || !target) return;
  const info = getPrereqEvaluation(prereq);
  const wrap = document.createElement("div");
  wrap.className = "prereq-box";
  const title = document.createElement("div");
  title.className = "prereq-title";
  title.textContent = "Prerequisites";
  wrap.appendChild(title);
  const list = document.createElement("div");
  list.className = "prereq-list";

  const renderNode = (node) => {
    if (!node) return;
    if (node.children && node.children.length) {
      const group = document.createElement("div");
      group.className = "prereq-group";
      const label = document.createElement("div");
      label.className = "prereq-item";
      label.textContent = `${node.ok ? "[OK]" : "[NO]"} ${node.label}`;
      group.appendChild(label);
      node.children.forEach((child) => {
        const childWrap = document.createElement("div");
        childWrap.className = "prereq-child";
        const childNode = renderNode(child);
        if (childNode) childWrap.appendChild(childNode);
        group.appendChild(childWrap);
      });
      return group;
    }
    const item = document.createElement("div");
    item.className = `prereq-item ${node.ok ? "ok" : "miss"}`;
    item.textContent = `${node.ok ? "[OK]" : "[NO]"} ${node.label}`;
    return item;
  };

  if (info.tree) {
    const node = renderNode(info.tree);
    if (node) list.appendChild(node);
  } else {
    const item = document.createElement("div");
    item.className = "prereq-item ok";
    item.textContent = "[OK] None";
    list.appendChild(item);
  }
  wrap.appendChild(list);
  target.appendChild(wrap);
}

function extractPrereqSkills(prereq) {
  const rules = characterData?.skill_rules || { ranks: [] };
  const skills = characterData?.skills || [];
  const reqs = _parseSkillRequirements(prereq || "", rules, skills);
  return reqs.map((r) => r.skill);
}

function extractFeatureTags(entry) {
  if (!entry?.tags) return [];
  return String(entry.tags)
    .split(/[\[\],]/g)
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function isPlaytestText(text) {
  return /playtest/i.test(String(text || ""));
}

function isPlaytestEntry(entry) {
  if (!entry) return false;
  return isPlaytestText(
    [entry.name, entry.id, entry.tags, entry.prerequisites, entry.frequency, entry.effects].filter(Boolean).join(" ")
  );
}

function inContentScope(entry) {
  const scope = characterState.content_scope || "official";
  if (scope === "all") return true;
  return !isPlaytestEntry(entry);
}

function _isPlaytestName(name) {
  return /playtest/i.test(String(name || ""));
}

function ensurePlaytestScopeForClass(className) {
  if (_isPlaytestName(className) && (characterState.content_scope || "official") !== "all") {
    characterState.content_scope = "all";
  }
}

function getClassNamesFromPrereq(prereq) {
  const classNames = (characterData?.classes || []).map((c) => c.name);
  const matches = _matchNamesInPrereq(prereq || "", classNames);
  const normalizedText = _normalizeMatchKey(prereq || "");
  if (!normalizedText) return matches;
  classNames.forEach((name) => {
    const key = _normalizeMatchKey(name);
    if (key && normalizedText.includes(key)) {
      matches.push(name);
    }
    if (_isPlaytestName(name)) {
      const stripped = _normalizeMatchKey(String(name || "").replace(/playtest/gi, ""));
      if (stripped && normalizedText.includes(stripped)) {
        matches.push(name);
      }
    }
  });
  return Array.from(new Set(matches));
}

function getFeatureClassLabels(entry) {
  const labels = new Set(getClassNamesFromPrereq(entry?.prerequisites || ""));
  const entryId = String(entry?.id || "");
  if (entryId) {
    (characterData?.classes || []).forEach((cls) => {
      const tiers = cls?.tiers || {};
      const found = Object.values(tiers).some((nodeIds) => (nodeIds || []).includes(entryId));
      if (found) labels.add(cls.name);
    });
  }
  const nameKey = _normalizeMatchKey(entry?.name || "");
  if (nameKey) {
    const index = _featureClassIndex();
    const nameMatches = index.get(nameKey) || [];
    nameMatches.forEach((name) => labels.add(name));
  }
  if (nameKey) {
    const direct = _classNameByKey().get(nameKey);
    if (direct) labels.add(direct);
  }
  if (!labels.size && Array.isArray(entry?.tags)) {
    const hasClassTag = entry.tags.some((tag) => String(tag).toLowerCase().includes("class"));
    if (hasClassTag && nameKey) {
      const direct = _classNameByKey().get(nameKey);
      if (direct) labels.add(direct);
    }
  }
  return Array.from(labels).sort((a, b) => String(a).localeCompare(String(b)));
}

function getEdgeClassLabels(entry) {
  return getClassNamesFromPrereq(entry?.prerequisites || "").sort((a, b) => String(a).localeCompare(String(b)));
}

let _cachedFeatureClassIndex = null;
let _cachedClassNameByKey = null;
let _cachedClassTierMap = null;
let _skillDescriptionCache = null;

function _normalizeMatchKey(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "");
}

function _getSkillDescription(skillName) {
  if (!_skillDescriptionCache) {
    _skillDescriptionCache = new Map();
    const catalog = characterData?.skills_catalog || [];
    catalog.forEach((entry) => {
      if (!entry || !entry.name) return;
      const key = _normalizeSearchText(entry.name);
      if (!key) return;
      _skillDescriptionCache.set(key, entry.description || "");
    });
  }
  const key = _normalizeSearchText(skillName);
  return _skillDescriptionCache.get(key) || "";
}

function _featureClassIndex() {
  if (_cachedFeatureClassIndex) return _cachedFeatureClassIndex;
  const index = new Map();
  const nodes = characterData?.nodes || [];
  const nameById = new Map();
  nodes.forEach((node) => {
    if (!node || node.type !== "feature") return;
    const nameKey = _normalizeMatchKey(node.name);
    if (nameKey) nameById.set(node.id, { key: nameKey, name: node.name });
  });
  (characterData?.classes || []).forEach((cls) => {
    const tiers = _classTierMap(cls);
    Object.values(tiers || {}).forEach((nodeIds) => {
      (nodeIds || []).forEach((nodeId) => {
        const entry = nameById.get(nodeId);
        if (!entry) return;
        if (!index.has(entry.key)) index.set(entry.key, new Set());
        index.get(entry.key).add(cls.name);
      });
    });
  });
  const finalized = new Map();
  index.forEach((set, key) => finalized.set(key, Array.from(set)));
  _cachedFeatureClassIndex = finalized;
  return finalized;
}

function _classNameByKey() {
  if (_cachedClassNameByKey) return _cachedClassNameByKey;
  const map = new Map();
  (characterData?.classes || []).forEach((cls) => {
    const key = _normalizeMatchKey(cls?.name || "");
    if (key) map.set(key, cls.name);
  });
  _cachedClassNameByKey = map;
  return map;
}

function _classTierMap(entry) {
  if (!entry) return {};
  if (!_cachedClassTierMap) _cachedClassTierMap = new Map();
  const cacheKey = entry.id || entry.name || "";
  if (_cachedClassTierMap.has(cacheKey)) return _cachedClassTierMap.get(cacheKey);
  const tiers = entry.tiers || {};
  if (tiers && Object.keys(tiers).length) {
    _cachedClassTierMap.set(cacheKey, tiers);
    return tiers;
  }
  const className = entry.name;
  const inferred = {};
  if (className) {
    (characterData?.nodes || []).forEach((node) => {
      if (!node || node.type !== "feature") return;
      if (!inContentScope(node)) return;
      const labels = getClassNamesFromPrereq(node.prerequisites || "");
      const stripped =
        _isPlaytestName(className) ? String(className).replace(/\\s*\\[?playtest\\]?/gi, "").trim() : "";
      const hasMatch = labels.includes(className) || (stripped && labels.includes(stripped));
      if (!hasMatch) return;
      const rank = Number(node.rank || 1);
      if (!inferred[rank]) inferred[rank] = [];
      inferred[rank].push(node.id);
    });
  }
  if (!Object.keys(inferred).length && _isPlaytestName(className)) {
    const stripped = String(className).replace(/\\s*\\[?playtest\\]?/gi, "").trim();
    const base = (characterData?.classes || []).find((cls) => cls?.name === stripped);
    if (base?.tiers && Object.keys(base.tiers).length) {
      _cachedClassTierMap.set(cacheKey, base.tiers);
      return base.tiers;
    }
  }
  _cachedClassTierMap.set(cacheKey, inferred);
  return inferred;
}

function makeFilterChip(text, onClick, className = "char-filter-chip") {
  const chip = document.createElement("button");
  chip.type = "button";
  chip.className = className;
  chip.textContent = text;
  chip.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    onClick();
  });
  return chip;
}

const WORD_LINK_SKIP_TAGS = new Set([
  "BUTTON",
  "INPUT",
  "SELECT",
  "TEXTAREA",
  "OPTION",
  "SCRIPT",
  "STYLE",
]);

function _normalizeWordToken(value) {
  return String(value || "").replace(/^[^\w]+|[^\w]+$/g, "");
}

function _wordTargetSets() {
  const skills = new Map();
  (characterData?.skills || []).forEach((name) => {
    const key = String(name || "").trim().toLowerCase();
    if (key) skills.set(key, name);
  });
  const classes = new Map();
  (characterData?.classes || []).forEach((entry) => {
    const name = String(entry?.name || "").trim();
    if (name) classes.set(name.toLowerCase(), name);
  });
  const features = new Map();
  (characterData?.features || []).forEach((entry) => {
    const name = String(entry?.name || "").trim();
    if (name) features.set(name.toLowerCase(), name);
  });
  const edges = new Map();
  (characterData?.edges_catalog || []).forEach((entry) => {
    const name = String(entry?.name || "").trim();
    if (name) edges.set(name.toLowerCase(), name);
  });
  const pokeEdges = new Map();
  _pokemonPokeEdgeCatalog().forEach((entry) => {
    const name = String(entry?.name || "").trim();
    if (name) pokeEdges.set(name.toLowerCase(), name);
  });
  const inventory = new Map();
  const inv = characterState?.inventory || {};
  const invLists = [inv.key_items, inv.pokemon_items, inv.consumables, inv.gear, inv.misc];
  invLists.forEach((list) => {
    (Array.isArray(list) ? list : []).forEach((entry) => {
      const name = String(entry?.name || entry || "").trim();
      if (name) inventory.set(name.toLowerCase(), name);
    });
  });
  return { skills, classes, features, edges, pokeEdges, inventory };
}

function routeCharacterWordClick(word, fallbackStep) {
  const cleaned = _normalizeWordToken(word);
  if (!cleaned) return;
  const key = cleaned.toLowerCase();
  const targets = _wordTargetSets();
  if (targets.skills.has(key)) {
    focusSkillConnections(targets.skills.get(key), "features");
    return;
  }
  if (targets.features.has(key)) {
    characterState.feature_search = targets.features.get(key);
    goToCharacterStep("features");
    return;
  }
  if (targets.edges.has(key)) {
    characterState.edge_search = targets.edges.get(key);
    goToCharacterStep("edges");
    return;
  }
  if (targets.pokeEdges.has(key)) {
    goToCharacterStep("pokemon-team");
    return;
  }
  if (targets.classes.has(key)) {
    focusClassConnections(targets.classes.get(key), "class");
    return;
  }
  if (targets.inventory.has(key)) {
    characterState.inventory_search = targets.inventory.get(key);
    goToCharacterStep("inventory");
    return;
  }
  goToCharacterStep(fallbackStep || "summary");
}

function makeCharacterWordsClickable(container) {
  if (!container) return;
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
    acceptNode: (node) => {
      if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
      let parent = node.parentElement;
      while (parent) {
        if (WORD_LINK_SKIP_TAGS.has(parent.tagName)) return NodeFilter.FILTER_REJECT;
        if (parent.classList.contains("char-no-word-links")) return NodeFilter.FILTER_REJECT;
        parent = parent.parentElement;
      }
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  const nodes = [];
  while (walker.nextNode()) {
    nodes.push(walker.currentNode);
  }
  nodes.forEach((node) => {
    const text = node.nodeValue || "";
    const frag = document.createDocumentFragment();
    text.split(/(\s+)/).forEach((part) => {
      if (!part) return;
      if (/^\s+$/.test(part)) {
        frag.appendChild(document.createTextNode(part));
        return;
      }
      const cleaned = _normalizeWordToken(part).toLowerCase();
      const targets = _wordTargetSets();
      const isLinkable =
        targets.skills.has(cleaned) ||
        targets.classes.has(cleaned) ||
        targets.features.has(cleaned) ||
        targets.edges.has(cleaned) ||
        targets.pokeEdges.has(cleaned) ||
        targets.inventory.has(cleaned);
      if (!isLinkable) {
        frag.appendChild(document.createTextNode(part));
        return;
      }
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "char-word-link";
      btn.textContent = part;
      const stepTarget =
        node.parentElement?.closest("[data-step-target]")?.getAttribute("data-step-target") || characterStep;
      btn.dataset.word = part;
      btn.dataset.step = stepTarget;
      frag.appendChild(btn);
    });
    node.parentNode?.replaceChild(frag, node);
  });
}

function warningTargetStep(warning) {
  const text = String(warning || "").toLowerCase();
  if (text.includes("poke edge")) return "pokemon-team";
  if (text.includes("no class selected")) return "class";
  if (text.includes("class prerequisite")) return "class";
  if (text.startsWith("class ")) return "class";
  if (text.includes("skill points")) return "skills";
  if (text.includes("background")) return "skills";
  if (text.includes("requires") && /(pathetic|untrained|novice|adept|expert|master)\s+/.test(text)) return "skills";
  if (text.includes("stat points")) return "advancement";
  if (text.includes("level")) return "advancement";
  if (text.includes("feature") && text.includes("exceed")) return "features";
  if (text.includes("edge") && text.includes("exceed")) return "edges";
  if (text.includes("class")) return "class";
  if (text.includes("skill")) return "skills";
  if (text.includes("edge")) return "edges";
  if (text.includes("feature")) return "features";
  if (text.includes("stat")) return "advancement";
  return "summary";
}

function goToCharacterStep(step) {
  const normalizedTarget = step === "poke-edges" ? "pokemon-team" : step;
  const normalizedCurrent = characterStep === "poke-edges" ? "pokemon-team" : characterStep;
  if (characterStep !== normalizedCurrent) characterStep = normalizedCurrent;
  const target = normalizedTarget || characterStep;
  if (target !== characterStep) {
    _navStack.push(_snapshotNavState());
    _navForward.length = 0;
  }
  characterStep = target;
  charStepButtons.forEach((btn) => btn.classList.toggle("active", btn.getAttribute("data-step") === characterStep));
  renderCharacterStep();
}

function _snapshotNavState() {
  return {
    step: characterStep,
    class_id: characterState.class_id,
    class_ids: Array.isArray(characterState.class_ids) ? characterState.class_ids.slice() : [],
    feature_search: characterState.feature_search,
    edge_search: characterState.edge_search,
    poke_edge_search: characterState.poke_edge_search,
    feature_tag_filter: characterState.feature_tag_filter,
    feature_class_filter: characterState.feature_class_filter,
    edge_class_filter: characterState.edge_class_filter,
    class_status_filter: characterState.class_status_filter,
    feature_group_mode: characterState.feature_group_mode,
    edge_group_mode: characterState.edge_group_mode,
    feature_status_filter: characterState.feature_status_filter,
    edge_status_filter: characterState.edge_status_filter,
    feature_filter_available: characterState.feature_filter_available,
    feature_filter_close: characterState.feature_filter_close,
    feature_filter_unavailable: characterState.feature_filter_unavailable,
    feature_filter_blocked: characterState.feature_filter_blocked,
    edge_filter_available: characterState.edge_filter_available,
    edge_filter_close: characterState.edge_filter_close,
    edge_filter_unavailable: characterState.edge_filter_unavailable,
    edge_filter_blocked: characterState.edge_filter_blocked,
    poke_edge_filter_available: characterState.poke_edge_filter_available,
    poke_edge_filter_close: characterState.poke_edge_filter_close,
    poke_edge_filter_unavailable: characterState.poke_edge_filter_unavailable,
    poke_edge_filter_blocked: characterState.poke_edge_filter_blocked,
    list_density: characterState.list_density,
  };
}

function _applyNavState(state) {
  if (!state) return;
  characterState.class_id = state.class_id || characterState.class_id;
  if (Array.isArray(state.class_ids)) characterState.class_ids = state.class_ids.slice();
  if (state.feature_search !== undefined) characterState.feature_search = state.feature_search;
  if (state.edge_search !== undefined) characterState.edge_search = state.edge_search;
  if (state.poke_edge_search !== undefined) characterState.poke_edge_search = state.poke_edge_search;
  if (state.feature_tag_filter !== undefined) characterState.feature_tag_filter = state.feature_tag_filter;
  if (state.feature_class_filter !== undefined) characterState.feature_class_filter = state.feature_class_filter;
  if (state.edge_class_filter !== undefined) characterState.edge_class_filter = state.edge_class_filter;
  if (state.class_status_filter !== undefined) characterState.class_status_filter = state.class_status_filter;
  if (state.feature_group_mode !== undefined) characterState.feature_group_mode = state.feature_group_mode;
  if (state.edge_group_mode !== undefined) characterState.edge_group_mode = state.edge_group_mode;
  if (state.feature_status_filter !== undefined) characterState.feature_status_filter = state.feature_status_filter;
  if (state.edge_status_filter !== undefined) characterState.edge_status_filter = state.edge_status_filter;
  if (state.feature_filter_available !== undefined) characterState.feature_filter_available = state.feature_filter_available;
  if (state.feature_filter_close !== undefined) characterState.feature_filter_close = state.feature_filter_close;
  if (state.feature_filter_unavailable !== undefined) characterState.feature_filter_unavailable = state.feature_filter_unavailable;
  if (state.feature_filter_blocked !== undefined) characterState.feature_filter_blocked = state.feature_filter_blocked;
  if (state.edge_filter_available !== undefined) characterState.edge_filter_available = state.edge_filter_available;
  if (state.edge_filter_close !== undefined) characterState.edge_filter_close = state.edge_filter_close;
  if (state.edge_filter_unavailable !== undefined) characterState.edge_filter_unavailable = state.edge_filter_unavailable;
  if (state.edge_filter_blocked !== undefined) characterState.edge_filter_blocked = state.edge_filter_blocked;
  if (state.poke_edge_filter_available !== undefined) characterState.poke_edge_filter_available = state.poke_edge_filter_available;
  if (state.poke_edge_filter_close !== undefined) characterState.poke_edge_filter_close = state.poke_edge_filter_close;
  if (state.poke_edge_filter_unavailable !== undefined) characterState.poke_edge_filter_unavailable = state.poke_edge_filter_unavailable;
  if (state.poke_edge_filter_blocked !== undefined) characterState.poke_edge_filter_blocked = state.poke_edge_filter_blocked;
  if (state.list_density !== undefined) characterState.list_density = state.list_density;
}

function goBackNav() {
  if (!_navStack.length) return;
  const current = _snapshotNavState();
  _navForward.push(current);
  const prev = _navStack.pop();
  characterStep = prev.step || characterStep;
  _applyNavState(prev);
  charStepButtons.forEach((btn) => btn.classList.toggle("active", btn.getAttribute("data-step") === characterStep));
  renderCharacterStep();
}

function goForwardNav() {
  if (!_navForward.length) return;
  const current = _snapshotNavState();
  _navStack.push(current);
  const next = _navForward.pop();
  characterStep = next.step || characterStep;
  _applyNavState(next);
  charStepButtons.forEach((btn) => btn.classList.toggle("active", btn.getAttribute("data-step") === characterStep));
  renderCharacterStep();
}

function appendNavRow() {
  const row = document.createElement("div");
  row.className = "char-action-row";
  const back = document.createElement("button");
  back.type = "button";
  back.textContent = "Back";
  back.disabled = !_navStack.length;
  back.addEventListener("click", goBackNav);
  const forward = document.createElement("button");
  forward.type = "button";
  forward.textContent = "Forward";
  forward.disabled = !_navForward.length;
  forward.addEventListener("click", goForwardNav);
  const jump = document.createElement("button");
  jump.type = "button";
  jump.textContent = "Jump";
  jump.addEventListener("click", () => openJumpPalette());
  row.appendChild(back);
  row.appendChild(forward);
  row.appendChild(jump);
  charContentEl.appendChild(row);
}

let _jumpOverlay = null;
let _jumpInput = null;
let _jumpList = null;
let _jumpIndex = null;
let _jumpResults = [];
let _jumpActiveIndex = -1;
const _jumpFilterState = {
  Class: true,
  Feature: true,
  Edge: true,
  "Poke Edge": true,
  Skill: true,
  Capability: true,
  Move: true,
  Ability: true,
  Item: true,
  "Held Item": true,
  Food: true,
};

function _buildJumpIndex() {
  const entries = [];
  (characterData?.classes || []).forEach((cls) => {
    if (!cls?.name) return;
    entries.push({
      kind: "Class",
      name: cls.name,
      detail: "Trainer class",
      action: () => focusClassConnections(cls.name, "class"),
    });
  });
  (characterData?.features || []).forEach((entry) => {
    if (!entry?.name) return;
    entries.push({
      kind: "Feature",
      name: entry.name,
      detail: entry.tags || entry.prerequisites || "",
      action: () => focusFeature(entry.name),
    });
  });
  (characterData?.edges_catalog || []).forEach((entry) => {
    if (!entry?.name) return;
    entries.push({
      kind: "Edge",
      name: entry.name,
      detail: entry.prerequisites || "",
      action: () => focusEdge(entry.name),
    });
  });
  _pokemonPokeEdgeCatalog().forEach((entry) => {
    if (!entry?.name) return;
    entries.push({
      kind: "Poke Edge",
      name: entry.name,
      detail: entry.prerequisites || "",
      action: () => {
        goToCharacterStep("pokemon-team");
      },
    });
  });
  (characterData?.skills || []).forEach((skill) => {
    entries.push({
      kind: "Skill",
      name: skill,
      detail: _getSkillDescription(skill),
      action: () => showSkillDetail(skill),
    });
  });
  _mergeNamedEntries([
    masterData?.pokemon?.capabilities || [],
    _pokemonSpeciesCatalog().flatMap((entry) => (entry?.capabilities || []).map((name) => ({ name }))),
  ]).forEach((cap) => {
    if (!cap?.name) return;
    entries.push({
      kind: "Capability",
      name: cap.name,
      detail: cap.description || "",
      action: () => showCapabilityDetail(cap.name),
    });
  });
  _pokemonMoveCatalog().forEach((move) => {
    if (!move?.name) return;
    entries.push({
      kind: "Move",
      name: move.name,
      detail: [move.type, move.category, move.frequency, move.effect].filter(Boolean).join(" | "),
      action: () => showMoveDetail(move.name),
    });
  });
  _pokemonAbilityCatalog().forEach((ability) => {
    if (!ability?.name) return;
    entries.push({
      kind: "Ability",
      name: ability.name,
      detail: [ability.frequency, ability.effect].filter(Boolean).join(" | "),
      action: () => showAbilityDetail(ability.name),
    });
  });
  const itemSets = [
    { list: masterData?.items?.inventory || [], kind: "Item" },
    { list: masterData?.items?.held_items || [], kind: "Held Item" },
    { list: masterData?.items?.food_items || [], kind: "Food" },
  ];
  itemSets.forEach((set) => {
    (set.list || []).forEach((item) => {
      if (!item?.name) return;
      entries.push({
        kind: set.kind,
        name: item.name,
        detail: item.description || item.buff || item.category || "",
        action: () => showItemDetail(item, set.kind.toLowerCase()),
      });
    });
  });
  return entries;
}

function _ensureJumpOverlay() {
  if (_jumpOverlay) return;
  _jumpOverlay = document.createElement("div");
  _jumpOverlay.className = "jump-overlay";
  const box = document.createElement("div");
  box.className = "jump-box";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Jump To";
  const filters = document.createElement("div");
  filters.className = "jump-filters";
  Object.keys(_jumpFilterState).forEach((key) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "jump-filter";
    btn.textContent = key;
    btn.classList.toggle("active", _jumpFilterState[key]);
    btn.addEventListener("click", () => {
      _jumpFilterState[key] = !_jumpFilterState[key];
      btn.classList.toggle("active", _jumpFilterState[key]);
      _renderJumpResults(_jumpInput.value);
    });
    filters.appendChild(btn);
  });
  _jumpInput = document.createElement("input");
  _jumpInput.type = "text";
  _jumpInput.placeholder = "Type to search classes, features, edges, skills, capabilities...";
  _jumpInput.className = "item-target-input";
  _jumpList = document.createElement("div");
  _jumpList.className = "jump-list";
  box.appendChild(title);
  box.appendChild(filters);
  box.appendChild(_jumpInput);
  box.appendChild(_jumpList);
  _jumpOverlay.appendChild(box);
  document.body.appendChild(_jumpOverlay);

  _jumpOverlay.addEventListener("click", (evt) => {
    if (evt.target === _jumpOverlay) closeJumpPalette();
  });
  _jumpInput.addEventListener("input", () => {
    _renderJumpResults(_jumpInput.value);
  });
  _jumpInput.addEventListener("keydown", (evt) => {
    if (evt.key === "ArrowDown") {
      evt.preventDefault();
      _setJumpActive(Math.min(_jumpResults.length - 1, _jumpActiveIndex + 1));
      return;
    }
    if (evt.key === "ArrowUp") {
      evt.preventDefault();
      _setJumpActive(Math.max(0, _jumpActiveIndex - 1));
      return;
    }
    if (evt.key === "Enter" && _jumpResults[_jumpActiveIndex]) {
      evt.preventDefault();
      const entry = _jumpResults[_jumpActiveIndex];
      closeJumpPalette();
      entry.action();
      return;
    }
    if (evt.key === "Escape") {
      evt.preventDefault();
      closeJumpPalette();
    }
  });
}

function _renderJumpResults(query) {
  if (!_jumpList) return;
  if (!_jumpIndex) _jumpIndex = _buildJumpIndex();
  const needle = String(query || "").trim();
  const filtered = needle
    ? _jumpIndex
        .map((entry) => ({
          entry,
          score: _searchMatchScore(`${entry.name} ${entry.kind} ${entry.detail || ""}`, needle),
        }))
        .filter((item) => item.score >= 0.6)
        .sort((a, b) => b.score - a.score)
        .map((item) => item.entry)
    : _jumpIndex.slice(0, 80);
  const scoped = filtered.filter((entry) => _jumpFilterState[entry.kind] !== false);
  _jumpResults = scoped.slice(0, 120);
  _jumpActiveIndex = _jumpResults.length ? 0 : -1;
  _jumpList.innerHTML = "";
  if (!_jumpResults.length) {
    const empty = document.createElement("div");
    empty.className = "char-empty";
    empty.textContent = "No matches.";
    _jumpList.appendChild(empty);
    return;
  }
  _jumpResults.forEach((entry, idx) => {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "jump-row";
    if (idx === _jumpActiveIndex) row.classList.add("is-active");
    row.innerHTML = `<span class="jump-kind">${escapeHtml(entry.kind)}</span><span class="jump-name">${escapeHtml(
      entry.name
    )}</span>`;
    row.addEventListener("click", () => {
      closeJumpPalette();
      entry.action();
    });
    if (entry.detail) {
      row.setAttribute("data-tooltip-title", entry.name);
      row.setAttribute("data-tooltip-body", entry.detail);
    }
    _jumpList.appendChild(row);
  });
  bindCharacterTooltips();
}

function _setJumpActive(idx) {
  if (!_jumpList || !_jumpResults.length) return;
  const next = Math.max(0, Math.min(_jumpResults.length - 1, idx));
  _jumpActiveIndex = next;
  Array.from(_jumpList.children).forEach((child, i) => {
    if (!(child instanceof HTMLElement)) return;
    child.classList.toggle("is-active", i === _jumpActiveIndex);
  });
  const active = _jumpList.children[_jumpActiveIndex];
  if (active && active.scrollIntoView) {
    active.scrollIntoView({ block: "nearest" });
  }
}

function openJumpPalette() {
  _ensureJumpOverlay();
  _jumpIndex = null;
  _jumpOverlay.classList.add("open");
  _jumpInput.value = "";
  _renderJumpResults("");
  setTimeout(() => _jumpInput.focus(), 0);
}

function closeJumpPalette() {
  if (!_jumpOverlay) return;
  _jumpOverlay.classList.remove("open");
}

function _isEditingInput(target) {
  if (!target) return false;
  const tag = target.tagName || "";
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  if (target.isContentEditable) return true;
  return false;
}

document.addEventListener("keydown", (evt) => {
  if (evt.key === "/" && !_isEditingInput(evt.target)) {
    evt.preventDefault();
    openJumpPalette();
  }
  if (evt.key === "Escape" && _jumpOverlay?.classList.contains("open")) {
    evt.preventDefault();
    closeJumpPalette();
  }
});

function focusClassConnections(className, targetStep = "features") {
  if (!className) return;
  characterState.feature_class_filter = className;
  characterState.edge_class_filter = className;
  characterState.feature_search = className;
  characterState.edge_search = className;
  characterState.feature_tag_filter = "";
  characterState.edge_tag_filter = "";
  ensurePlaytestScopeForClass(className);
  if (targetStep === "features" || targetStep === "edges" || targetStep === "extras" || targetStep === "class") {
    goToCharacterStep(targetStep);
    return;
  }
  renderCharacterStep();
}

function _setRelatedSearch(query) {
  const text = String(query || "").trim();
  characterState.feature_search = text;
  characterState.edge_search = text;
}

function focusSkillConnections(skillName, targetStep = "features") {
  if (!skillName) return;
  _setRelatedSearch(skillName);
  goToCharacterStep(targetStep);
}

function _statSearchQuery(statKey) {
  const key = String(statKey || "").toLowerCase();
  const map = {
    hp: "+HP",
    atk: "+Attack",
    def: "+Defense",
    spatk: "+Special Attack",
    spdef: "+Special Defense",
    spd: "+Speed",
  };
  return map[key] || statKey || "";
}

function focusStatConnections(statKey, targetStep = "features") {
  const query = _statSearchQuery(statKey);
  if (!query) return;
  _setRelatedSearch(query);
  goToCharacterStep(targetStep);
}

function _capabilitySearchQuery(capabilityKey) {
  const key = String(capabilityKey || "").toLowerCase();
  const map = {
    power: "Power Capability",
    high_jump: "High Jump",
    long_jump: "Long Jump",
    overland: "Overland",
    swim: "Swim",
    throwing_range: "Throwing Range",
  };
  return map[key] || capabilityKey || "";
}

function _capabilityMatchCounts(query) {
  const text = String(query || "").trim();
  if (!text) return { featureCount: 0, edgeCount: 0 };
  const scoreMatch = (haystack) => _searchMatchScore(haystack, text) > 0;
  const features = (characterData?.features || []).filter((entry) => {
    if (!inContentScope(entry)) return false;
    const haystack = `${entry.name} ${entry.tags || ""} ${entry.prerequisites || ""} ${
      entry.effects || ""
    } ${entry.description || ""}`;
    return scoreMatch(haystack);
  });
  const edges = (characterData?.edges_catalog || []).filter((entry) => {
    if (!inContentScope(entry)) return false;
    const haystack = `${entry.name} ${entry.prerequisites || ""} ${entry.effects || ""} ${entry.description || ""}`;
    return scoreMatch(haystack);
  });
  return { featureCount: features.length, edgeCount: edges.length };
}

function focusCapabilityConnections(capabilityKey, targetStep = "features") {
  const query = _capabilitySearchQuery(capabilityKey);
  if (!query) return;
  const counts = _capabilityMatchCounts(query);
  characterState.feature_class_filter = "";
  characterState.feature_tag_filter = "";
  characterState.edge_class_filter = "";
  characterState.edge_status_filter = "all";
  characterState.feature_filter_available = true;
  characterState.feature_filter_close = true;
  characterState.feature_filter_unavailable = true;
  characterState.feature_filter_blocked = true;
  characterState.edge_filter_available = true;
  characterState.edge_filter_close = true;
  characterState.edge_filter_unavailable = true;
  characterState.edge_filter_blocked = true;
  _setRelatedSearch(query);
  let step = targetStep;
  if (targetStep === "features" && counts.featureCount === 0 && counts.edgeCount > 0) {
    step = "edges";
  }
  if (counts.featureCount === 0 && counts.edgeCount === 0 && window.DSUI && typeof window.DSUI.toast === "function") {
    window.DSUI.toast(`No related features or edges found for ${query}.`);
  }
  goToCharacterStep(step);
}

function focusFeature(name) {
  if (!name) return;
  characterState.feature_search = name;
  goToCharacterStep("features");
}

function focusEdge(name) {
  if (!name) return;
  characterState.edge_search = name;
  goToCharacterStep("edges");
}

function _connectionIndex() {
  const nodes = new Map();
  (characterData?.nodes || []).forEach((node) => {
    if (node?.id) nodes.set(node.id, node.name || node.id);
  });
  const edges = (characterData?.edges || []).filter((edge) => edge?.type);
  return { nodes, edges };
}

function showConnectionsForEntry(kind, name) {
  if (!kind || !name) return;
  const { nodes, edges } = _connectionIndex();
  const entryId = `${kind}:${name}`;
  const prereqs = edges
    .filter((edge) => edge.type === "prereq" && edge.to === entryId)
    .map((edge) => nodes.get(edge.from) || edge.from);
  const unlocks = edges
    .filter((edge) => edge.from === entryId)
    .map((edge) => nodes.get(edge.to) || edge.to);
  const modal = document.createElement("div");
  modal.className = "char-connection-modal";
  const box = document.createElement("div");
  box.className = "char-connection-box";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = `Connections: ${name}`;
  const prereqTitle = document.createElement("div");
  prereqTitle.className = "char-feature-meta";
  prereqTitle.textContent = `Prerequisites: ${prereqs.length ? prereqs.join(", ") : "none"}`;
  const unlockTitle = document.createElement("div");
  unlockTitle.className = "char-feature-meta";
  unlockTitle.textContent = `Unlocks: ${unlocks.length ? unlocks.join(", ") : "none"}`;
  const close = document.createElement("button");
  close.type = "button";
  close.textContent = "Close";
  close.addEventListener("click", () => modal.remove());
  box.appendChild(title);
  box.appendChild(prereqTitle);
  box.appendChild(unlockTitle);
  box.appendChild(close);
  modal.appendChild(box);
  document.body.appendChild(modal);
}

function _relatedEntriesForSkill(skillName) {
  const target = _normalizeSearchText(skillName);
  const features = (characterData?.features || []).filter((entry) => {
    const skills = extractPrereqSkills(entry.prerequisites || "");
    return skills.some((s) => _normalizeSearchText(s) === target);
  });
  const edges = (characterData?.edges_catalog || []).filter((entry) => {
    const skills = extractPrereqSkills(entry.prerequisites || "");
    return skills.some((s) => _normalizeSearchText(s) === target);
  });
  const classes = (characterData?.classes || []).filter((cls) => {
    const node = (characterData?.nodes || []).find((n) => n.id === cls.id);
    const prereq = node?.prerequisites || "";
    return _normalizeSearchText(prereq).includes(target);
  });
  return { features, edges, classes };
}

function _getCapabilityDescription(name) {
  const caps = _mergeNamedEntries([
    masterData?.pokemon?.capabilities || [],
    _pokemonSpeciesCatalog().flatMap((entry) => (entry?.capabilities || []).map((capName) => ({ name: capName }))),
  ]);
  const key = _normalizeSearchText(name);
  const match = caps.find((cap) => _normalizeSearchText(cap.name) === key);
  return match?.description || "";
}

function _cleanDetailText(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .replace(/\s*:\s*/g, ": ")
    .trim();
}

function _firstSentence(value, fallback = "") {
  const text = _cleanDetailText(value);
  if (!text) return fallback;
  const parts = text.split(/(?<=[.!?])\s+/);
  return parts[0] || text;
}

function _plainFrequencyText(value) {
  const text = String(value || "").trim();
  const lower = text.toLowerCase();
  if (!text) return "Use timing is not listed.";
  if (lower.includes("at-will")) return "You can use this whenever you want.";
  if (lower.includes("scene")) return "You can use this a few times each battle scene.";
  if (lower.includes("daily")) return "This is limited and meant to be used sparingly.";
  if (lower.includes("static")) return "This is always on once the Pokemon has it.";
  if (lower.includes("eot")) return "This can trigger at the end of a turn.";
  return `Use timing: ${text}.`;
}

function _plainRangeText(value) {
  const text = String(value || "").trim();
  const lower = text.toLowerCase();
  if (!text) return "Range is not listed.";
  if (lower.includes("melee")) return "You need to be right next to the target.";
  if (lower.includes("burst")) return `It hits an area around a point or target (${text}).`;
  if (lower.includes("line")) return `It travels in a straight line (${text}).`;
  if (lower.includes("cone")) return `It spreads out in a cone (${text}).`;
  const meters = text.match(/\b(\d+)\b/);
  if (meters) return `It can reach about ${meters[1]} spaces away.`;
  return `Range: ${text}.`;
}

function _plainAcText(value) {
  const ac = Number(value);
  if (!Number.isFinite(ac) || ac <= 0) return "It does not use a normal accuracy check.";
  return `It needs an AC ${ac} hit check. Lower AC is easier to land.`;
}

function _plainDbText(value, category = "") {
  const db = Number(value);
  const lowerCategory = String(category || "").trim().toLowerCase();
  if (!Number.isFinite(db) || db <= 0 || lowerCategory === "status") {
    return "This is mostly for utility, setup, or status instead of raw damage.";
  }
  return `Its base power is DB ${db}, so it is mainly a damaging move.`;
}

function _eli5MoveSummary(entry) {
  if (!entry) return "No move details available.";
  const type = String(entry.type || "Unknown").trim();
  const category = String(entry.category || "Unknown").trim();
  const effectText = _moveRulesText(entry);
  const lines = [
    `${entry.name || "This move"} is a ${type} ${String(category || "move").toLowerCase()} move.`,
    _plainDbText(entry.damage_base ?? entry.db, category),
    _plainAcText(entry.ac),
    _plainRangeText(entry.range),
    _plainFrequencyText(entry.frequency),
  ];
  const effectLine = _firstSentence(effectText);
  if (effectLine) lines.push(`Main effect: ${effectLine}`);
  return lines.filter(Boolean).join(" ");
}

function _moveRulesText(entry) {
  if (!entry) return "";
  return entry.effects || entry.effect || entry.effect_text || entry.rules || "";
}

function _eli5AbilitySummary(entry) {
  if (!entry) return "No ability details available.";
  const lines = [];
  const frequency = String(entry.frequency || "").trim();
  if (!frequency || frequency.toLowerCase() === "static") {
    lines.push("This is a passive ability. It is usually just on.");
  } else {
    lines.push(_plainFrequencyText(frequency));
  }
  if (entry.trigger) {
    lines.push(`It matters when this happens: ${_cleanDetailText(entry.trigger)}`);
  }
  const target = _cleanDetailText(entry.target);
  if (target) lines.push(`It usually affects: ${target}`);
  const effectLine = _firstSentence(entry.effect || entry.effect_2 || entry.description || "");
  if (effectLine) lines.push(`What it does: ${effectLine}`);
  return lines.filter(Boolean).join(" ");
}

function _eli5CapabilitySummary(name, description = "") {
  const desc = _cleanDetailText(description);
  if (!desc) return `${name} is a built-in Pokemon trait, but no description is loaded for it yet.`;
  return `${name} is a built-in Pokemon trait. In plain English: ${_firstSentence(desc, desc)}`;
}

function _eli5SkillSummary(skillName, description = "") {
  const desc = _cleanDetailText(description);
  if (!desc) return `${skillName} is a trainer skill used for common checks in that area.`;
  return `${skillName} is the skill you use for this kind of task. In plain English: ${_firstSentence(desc, desc)}`;
}

function _eli5ClassSummary(entry, classNode = null) {
  const name = String(classNode?.name || entry?.name || "This class").trim();
  const effect = _firstSentence(classNode?.effects || entry?.effects || "");
  const prereq = _cleanDetailText(classNode?.prerequisites || entry?.prerequisites || "");
  const lines = [`${name} is a trainer class that gives your character a focused playstyle.`];
  if (effect) lines.push(`Main job: ${effect}`);
  if (prereq) lines.push(`Before taking it: ${_firstSentence(prereq, prereq)}`);
  return lines.join(" ");
}

function _eli5FeatureSummary(entry) {
  if (!entry) return "No feature details available.";
  const effect = _firstSentence(entry.effects || entry.description || "");
  const prereq = _cleanDetailText(entry.prerequisites);
  const lines = ["This is a trainer feature, which is a special rule or perk you can pick."];
  if (effect) lines.push(`Main benefit: ${effect}`);
  if (entry.frequency) lines.push(_plainFrequencyText(entry.frequency));
  if (prereq) lines.push(`Before taking it: ${_firstSentence(prereq, prereq)}`);
  return lines.join(" ");
}

function _eli5EdgeSummary(entry, options = {}) {
  if (!entry) return "No edge details available.";
  const forPokemon = !!options.forPokemon;
  const effect = _firstSentence(entry.effects || entry.description || "");
  const prereq = _cleanDetailText(entry.prerequisites);
  const cost = _cleanDetailText(entry.cost);
  const lines = [
    forPokemon
      ? "This is a Poke Edge, which is a special upgrade for a Pokemon build."
      : "This is an Edge, which is a smaller trainer upgrade or specialty pick.",
  ];
  if (effect) lines.push(`Main benefit: ${effect}`);
  if (cost) lines.push(`Cost: ${cost}`);
  if (prereq) lines.push(`Before taking it: ${_firstSentence(prereq, prereq)}`);
  return lines.join(" ");
}

function _eli5ItemSummary(entry) {
  if (!entry) return "No item details available.";
  const desc = _firstSentence(entry.description || entry.buff || entry.desc || "");
  const category = String(entry.category || "").trim();
  const slot = String(entry.slot || entry.extra || "").trim();
  const lines = ["This is an item you can carry, use, or give to a Pokemon."];
  if (category) lines.push(`Type of item: ${category}.`);
  if (slot) lines.push(`It fits this slot or group: ${slot}.`);
  if (desc) lines.push(`What it does: ${desc}`);
  return lines.join(" ");
}

function _appendInlinePlainSummary(parent, bodyText, className = "char-feature-meta") {
  if (!parent || !bodyText) return;
  const body = document.createElement("div");
  body.className = className;
  body.textContent = bodyText;
  parent.appendChild(body);
}

function _appendDetailBlock(parent, titleText, bodyText) {
  if (!parent || !bodyText) return;
  const title = document.createElement("div");
  title.className = "char-feature-meta";
  title.textContent = titleText;
  parent.appendChild(title);
  const body = document.createElement("div");
  body.className = "char-summary-box char-no-word-links";
  body.textContent = bodyText;
  parent.appendChild(body);
}

function _allPokedexAbilityPools() {
  return {
    ...(characterData?.pokemon?.pokedex_abilities || {}),
    ...(masterData?.pokemon?.pokedex_abilities || {}),
  };
}

function _pokemonSpeciesCatalog() {
  const masterSpecies = masterData?.pokemon?.species || [];
  const characterSpecies = characterData?.pokemon?.species || [];
  if (
    _speciesCatalogCache &&
    _speciesCatalogCache.masterSpecies === masterSpecies &&
    _speciesCatalogCache.characterSpecies === characterSpecies
  ) {
    return _speciesCatalogCache.value;
  }
  const value = _mergeNamedEntries(
    [masterSpecies, characterSpecies],
    (prev, raw) => {
      const next = { ...prev };
      if (!Array.isArray(next.types) || !next.types.length) next.types = Array.isArray(raw?.types) ? raw.types.slice() : [];
      else next.types = _mergeStringLists(next.types, raw?.types);
      if (!Array.isArray(next.capabilities) || !next.capabilities.length) next.capabilities = Array.isArray(raw?.capabilities) ? raw.capabilities.slice() : [];
      else next.capabilities = _mergeStringLists(next.capabilities, raw?.capabilities);
      if (!_hasDisplayValue(next.size) && _hasDisplayValue(raw?.size)) next.size = raw.size;
      if (!_hasDisplayValue(next.weight) && _hasDisplayValue(raw?.weight)) next.weight = raw.weight;
      if (!next.base_stats && raw?.base_stats) next.base_stats = { ...raw.base_stats };
      return next;
    }
  );
  _speciesCatalogCache = { masterSpecies, characterSpecies, value };
  return value;
}

function _learnsetMoveNameSet() {
  if (_learnsetMoveNameSetCache && _learnsetMoveNameSetCache.learnsetRef === learnsetData) {
    return _learnsetMoveNameSetCache.value;
  }
  const names = new Set();
  const index = learnsetData && typeof learnsetData === "object" ? learnsetData : {};
  Object.values(index).forEach((entries) => {
    (Array.isArray(entries) ? entries : []).forEach((entry) => {
      const name = String(entry?.move || "").trim();
      const key = _normalizeSearchText(name);
      if (name && key) names.add(name);
    });
  });
  _learnsetMoveNameSetCache = { learnsetRef: learnsetData, value: names };
  return names;
}

function _pokemonMoveCatalog() {
  const masterMoves = masterData?.pokemon?.moves || [];
  const characterMoves = characterData?.pokemon?.moves || [];
  if (
    _moveCatalogCache &&
    _moveCatalogCache.masterMoves === masterMoves &&
    _moveCatalogCache.characterMoves === characterMoves &&
    _moveCatalogCache.learnsetRef === learnsetData
  ) {
    return _moveCatalogCache.value;
  }
  const merged = _mergeNamedEntries([masterMoves, characterMoves], (prev, raw) => {
    const next = { ...prev };
    if (!_hasDisplayValue(next.type) && _hasDisplayValue(raw?.type)) next.type = raw.type;
    if (!_hasDisplayValue(next.category) && _hasDisplayValue(raw?.category)) next.category = raw.category;
    if (!_hasDisplayValue(next.damage_base) && _hasDisplayValue(raw?.damage_base)) next.damage_base = raw.damage_base;
    if (!_hasDisplayValue(next.range) && _hasDisplayValue(raw?.range)) next.range = raw.range;
    if (!_hasDisplayValue(next.frequency) && _hasDisplayValue(raw?.frequency)) next.frequency = raw.frequency;
    if (!_hasDisplayValue(next.effects) && _hasDisplayValue(raw?.effects)) next.effects = raw.effects;
    if (!_hasDisplayValue(next.ac) && _hasDisplayValue(raw?.ac)) next.ac = raw.ac;
    return next;
  });
  const map = new Map(merged.map((entry) => [_normalizeSearchText(entry.name), entry]));
  _learnsetMoveNameSet().forEach((name) => {
    const key = _normalizeSearchText(name);
    if (!key || map.has(key)) return;
    map.set(key, { name, type: "", category: "", damage_base: "", range: "", frequency: "", effects: "" });
  });
  const value = Array.from(map.values());
  _moveCatalogCache = { masterMoves, characterMoves, learnsetRef: learnsetData, value };
  return value;
}

function _pokemonAbilityCatalog() {
  const masterAbilities = masterData?.pokemon?.abilities || [];
  const characterAbilities = characterData?.pokemon?.abilities || [];
  const masterPoolsRef = masterData?.pokemon?.pokedex_abilities || null;
  const characterPoolsRef = characterData?.pokemon?.pokedex_abilities || null;
  const pools = _allPokedexAbilityPools();
  if (
    _abilityCatalogCache &&
    _abilityCatalogCache.masterAbilities === masterAbilities &&
    _abilityCatalogCache.characterAbilities === characterAbilities &&
    _abilityCatalogCache.masterPoolsRef === masterPoolsRef &&
    _abilityCatalogCache.characterPoolsRef === characterPoolsRef
  ) {
    return _abilityCatalogCache.value;
  }
  const merged = _mergeNamedEntries([masterAbilities, characterAbilities], (prev, raw) => {
    const next = { ...prev };
    if (!_hasDisplayValue(next.effect) && _hasDisplayValue(raw?.effect)) next.effect = raw.effect;
    if (!_hasDisplayValue(next.description) && _hasDisplayValue(raw?.description)) next.description = raw.description;
    if (!_hasDisplayValue(next.frequency) && _hasDisplayValue(raw?.frequency)) next.frequency = raw.frequency;
    return next;
  });
  const map = new Map(merged.map((entry) => [_normalizeSearchText(entry.name), entry]));
  Object.entries(pools || {}).forEach(([abilityName, value]) => {
    const key = _normalizeSearchText(abilityName);
    if (!key) return;
    if (!map.has(key)) {
      map.set(key, { name: abilityName, effect: value?.effect || value?.description || "" });
      return;
    }
    const prev = map.get(key) || {};
    if (!_hasDisplayValue(prev.effect) && _hasDisplayValue(value?.effect)) prev.effect = value.effect;
    if (!_hasDisplayValue(prev.description) && _hasDisplayValue(value?.description)) prev.description = value.description;
    map.set(key, prev);
  });
  const value = Array.from(map.values());
  _abilityCatalogCache = { masterAbilities, characterAbilities, masterPoolsRef, characterPoolsRef, value };
  return value;
}

function _pokemonPokeEdgeCatalog() {
  const characterPokeEdges = characterData?.poke_edges_catalog || [];
  const trainerPokeEdges = masterData?.trainer?.poke_edges || [];
  if (
    _pokeEdgeCatalogCache &&
    _pokeEdgeCatalogCache.characterPokeEdges === characterPokeEdges &&
    _pokeEdgeCatalogCache.trainerPokeEdges === trainerPokeEdges
  ) {
    return _pokeEdgeCatalogCache.value;
  }
  const value = _mergeNamedEntries([characterPokeEdges, trainerPokeEdges], (prev, raw) => {
    const next = { ...prev };
    if (!_hasDisplayValue(next.prerequisites) && _hasDisplayValue(raw?.prerequisites)) next.prerequisites = raw.prerequisites;
    if (!_hasDisplayValue(next.cost) && _hasDisplayValue(raw?.cost)) next.cost = raw.cost;
    if (!_hasDisplayValue(next.effects) && _hasDisplayValue(raw?.effects)) next.effects = raw.effects;
    return next;
  });
  _pokeEdgeCatalogCache = { characterPokeEdges, trainerPokeEdges, value };
  return value;
}

function _findPokeEdgeByName(name) {
  const key = _normalizeSearchText(name);
  return _pokemonPokeEdgeCatalog().find((entry) => _normalizeSearchText(entry.name) === key) || null;
}

function _builderDatasetStatus() {
  return {
    species: _pokemonSpeciesCatalog().length,
    moves: _pokemonMoveCatalog().length,
    abilities: _pokemonAbilityCatalog().length,
    items: _allItemCatalogEntries().length,
    pokeEdges: _pokemonPokeEdgeCatalog().length,
    learnsetSpecies: learnsetData ? Object.keys(learnsetData).length : 0,
  };
}

function _rebuildMoveRecordMap() {
  const list = _pokemonMoveCatalog();
  moveRecordMap = new Map(list.map((entry) => [_normalizeSearchText(entry.name), entry]));
}

function _getMoveDetail(name) {
  const moves = _pokemonMoveCatalog();
  const key = _normalizeSearchText(name);
  return moves.find((move) => _normalizeSearchText(move.name) === key) || null;
}

function _getAbilityDetail(name) {
  const abilities = _pokemonAbilityCatalog();
  const key = _normalizeSearchText(name);
  return abilities.find((ab) => _normalizeSearchText(ab.name) === key) || null;
}

function renderCharacterBuilder() {
  charContentEl.innerHTML = "";
  charContentEl.setAttribute("data-step-target", "builder");
  appendNavRow();
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Builder";
  charContentEl.appendChild(title);
  appendStepModeToggle();
  ensurePlaytestScopeForClass(characterState.edge_class_filter);
  _renderBuilderPanel(charContentEl);
  _renderPlannerPanel(charContentEl);
  _renderCloseUnlocks(charContentEl);
}

function _allItemCatalogEntries() {
  const buckets = ["inventory", "held_items", "food_items", "weather", "weapons"];
  const sources = [characterData?.items || {}, masterData?.items || {}];
  const merged = new Map();
  sources.forEach((items) => {
    buckets.forEach((bucket) => {
      const list = Array.isArray(items?.[bucket]) ? items[bucket] : [];
      list.forEach((raw) => {
        if (!raw?.name) return;
        const key = _normalizeSearchText(raw.name);
        if (!key) return;
        const prev = merged.get(key);
        if (!prev) {
          merged.set(key, { ...raw });
          return;
        }
        const next = { ...prev };
        if (!_hasDisplayValue(next.cost) && _hasDisplayValue(raw.cost)) next.cost = raw.cost;
        if (!_hasDisplayValue(next.description) && _hasDisplayValue(raw.description)) next.description = raw.description;
        if (!_hasDisplayValue(next.buff) && _hasDisplayValue(raw.buff)) next.buff = raw.buff;
        if (!_hasDisplayValue(next.category) && _hasDisplayValue(raw.category)) next.category = raw.category;
        if (!_hasDisplayValue(next.slot) && _hasDisplayValue(raw.slot)) next.slot = raw.slot;
        if (!_hasDisplayValue(next.extra) && _hasDisplayValue(raw.extra)) next.extra = raw.extra;
        merged.set(key, next);
      });
    });
  });
  return Array.from(merged.values());
}

function _findItemByName(name) {
  const key = _normalizeSearchText(name);
  const lists = _allItemCatalogEntries();
  return lists.find((entry) => _normalizeSearchText(entry.name) === key) || null;
}

function _pokemonBuildItemLabel(name) {
  const itemName = String(name || "").trim();
  if (!itemName) return "";
  const entry = _findItemByName(itemName);
  const cost = entry?.cost;
  if (!_hasDisplayValue(cost)) return itemName;
  return `${itemName} ($${cost})`;
}

function _queueBuilderRerender() {
  if (_builderRerenderQueued) return;
  _builderRerenderQueued = true;
  setTimeout(() => {
    _builderRerenderQueued = false;
    if (characterStep === "pokemon-team") renderCharacterPokemonTeam();
  }, 0);
}

function _speciesSpriteSlug(name) {
  const raw = String(name || "").trim().toLowerCase();
  if (!raw) return "";
  return raw
    .replace(/\u2640/g, "f")
    .replace(/\u2642/g, "m")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function _speciesSpriteUrl(name) {
  const slug = _speciesSpriteSlug(name);
  if (!slug) return "";
  return `/sprites/${slug}.png`;
}

function _knownPokemonTypes() {
  return [
    "Normal",
    "Fire",
    "Water",
    "Electric",
    "Grass",
    "Ice",
    "Fighting",
    "Poison",
    "Ground",
    "Flying",
    "Psychic",
    "Bug",
    "Rock",
    "Ghost",
    "Dragon",
    "Dark",
    "Steel",
    "Fairy",
  ];
}

function _requiredTypesFromPrereq(prereqText) {
  const out = [];
  const text = String(prereqText || "");
  const pattern = /\b(Normal|Fire|Water|Electric|Grass|Ice|Fighting|Poison|Ground|Flying|Psychic|Bug|Rock|Ghost|Dragon|Dark|Steel|Fairy)\s*[- ]?Type\b/gi;
  let match;
  while ((match = pattern.exec(text)) !== null) {
    const typeName = String(match[1] || "").trim();
    if (typeName && !out.includes(typeName)) out.push(typeName);
  }
  return out;
}

function _requiredCapabilitiesFromPrereq(prereqText) {
  const caps = _mergeNamedEntries([
    masterData?.pokemon?.capabilities || [],
    _pokemonSpeciesCatalog().flatMap((entry) => (entry?.capabilities || []).map((name) => ({ name }))),
  ]);
  const text = String(prereqText || "");
  if (!text) return [];
  const out = [];
  caps.forEach((entry) => {
    const capName = String(entry?.name || "").trim();
    if (!capName) return;
    const pattern = _namePattern(capName);
    if (pattern && pattern.test(text) && !out.includes(capName)) {
      out.push(capName);
    }
  });
  return out;
}

function _abilityAllowedByLevel(pools, level) {
  const allowed = new Set();
  const safeLevel = Number(level || 1);
  const include = (list) => (list || []).forEach((name) => allowed.add(_normalizeSearchText(name)));
  include(pools?.starting);
  include(pools?.basic);
  if (safeLevel >= 20) include(pools?.advanced);
  if (safeLevel >= 40) include(pools?.high);
  return allowed;
}

function _prereqAllowsPokeEdgeForBuild(edgeEntry, speciesEntry, safeLevel) {
  if (!edgeEntry) return false;
  const prereq = String(edgeEntry.prerequisites || "").trim();
  if (!prereq) return true;
  const levelMatches = prereq.match(/Level\s*(\d+)/gi) || [];
  for (const raw of levelMatches) {
    const reqLevel = Number(String(raw).replace(/[^0-9]/g, ""));
    if (Number.isFinite(reqLevel) && safeLevel < reqLevel) return false;
  }
  if (!speciesEntry) return true;
  const speciesTypes = new Set((speciesEntry.types || []).map((t) => _normalizeSearchText(t)));
  for (const typeName of _requiredTypesFromPrereq(prereq)) {
    if (!speciesTypes.has(_normalizeSearchText(typeName))) return false;
  }
  const speciesCaps = new Set((speciesEntry.capabilities || []).map((cap) => _normalizeSearchText(cap)));
  for (const capName of _requiredCapabilitiesFromPrereq(prereq)) {
    if (!speciesCaps.has(_normalizeSearchText(capName))) return false;
  }
  return true;
}

function _sanitizePokemonBuildForLevel(build, speciesEntry = null) {
  if (!build) return { changed: false, removed: { moves: 0, abilities: 0, poke_edges: 0 } };
  const resolvedSpecies = speciesEntry || _getPokemonSpeciesEntry(build.species || build.name || "");
  const safeLevel = _clampPokemonLevel(build.level || 1, 1);
  let changed = false;
  const removed = { moves: 0, abilities: 0, poke_edges: 0 };
  if (Number(build.level || 1) !== safeLevel) {
    build.level = safeLevel;
    changed = true;
  }
  const statPointState = _sanitizePokemonBuildStatPoints(build);
  if (statPointState.changed) changed = true;

  const learnset = resolvedSpecies ? _getLearnsetForSpecies(resolvedSpecies.name) : [];
  const learnableByLevel = new Set(
    (learnset || [])
      .filter((entry) => Number(entry.level || 0) <= safeLevel)
      .map((entry) => _normalizeSearchText(entry.move))
  );
  if (Array.isArray(build.moves)) {
    const nextMoves = build.moves.filter((name) => {
      const moveName = String(name || "").trim();
      if (!moveName || !_getMoveDetail(moveName)) return false;
      if (resolvedSpecies && learnsetData && learnset.length) {
        return learnableByLevel.has(_normalizeSearchText(moveName));
      }
      return true;
    });
    removed.moves = build.moves.length - nextMoves.length;
    if (removed.moves > 0) {
      build.moves = nextMoves;
      changed = true;
    }
  }

  const abilityPools = resolvedSpecies ? _getAbilityPoolsForSpecies(resolvedSpecies.name) : null;
  const allowedAbilities = _abilityAllowedByLevel(abilityPools, safeLevel);
  if (Array.isArray(build.abilities)) {
    const nextAbilities = build.abilities.filter((name) => {
      const abilityName = String(name || "").trim();
      if (!abilityName || !_getAbilityDetail(abilityName)) return false;
      if (resolvedSpecies && abilityPools && allowedAbilities.size) {
        return allowedAbilities.has(_normalizeSearchText(abilityName));
      }
      return true;
    });
    removed.abilities = build.abilities.length - nextAbilities.length;
    if (removed.abilities > 0) {
      build.abilities = nextAbilities;
      changed = true;
    }
  }

  if (Array.isArray(build.poke_edges)) {
    const nextEdges = build.poke_edges.filter((name) => {
      const edgeName = String(name || "").trim();
      if (!edgeName) return false;
      const edgeEntry = _findPokeEdgeByName(edgeName);
      return _prereqAllowsPokeEdgeForBuild(edgeEntry, resolvedSpecies, safeLevel);
    });
    removed.poke_edges = build.poke_edges.length - nextEdges.length;
    if (removed.poke_edges > 0) {
      build.poke_edges = nextEdges;
      changed = true;
    }
  }

  return { changed, removed };
}

function _pokemonBuildLegality(build) {
  const issues = [];
  const pushDuplicateIssues = (values, label) => {
    const seen = new Set();
    const duplicates = [];
    (values || []).forEach((name) => {
      const raw = String(name || "").trim();
      if (!raw) return;
      const key = _normalizeSearchText(raw);
      if (!key) return;
      if (seen.has(key)) {
        if (!duplicates.includes(raw)) duplicates.push(raw);
        return;
      }
      seen.add(key);
    });
    if (duplicates.length) {
      issues.push({
        severity: "error",
        message: `Duplicate ${label}: ${duplicates.join(", ")}.`,
      });
    }
  };
  const level = Number(build?.level || 1);
  if (!Number.isFinite(level) || level < 1 || level > 100) {
    issues.push({ severity: "error", message: "Level must be between 1 and 100." });
  }
  const speciesName = String(build?.species || build?.name || "").trim();
  if (!speciesName) {
    issues.push({ severity: "error", message: "Species is required." });
  }
  const speciesEntry = _getPokemonSpeciesEntry(speciesName);
  if (!speciesEntry && speciesName) {
    issues.push({ severity: "error", message: `Species not found: ${speciesName}.` });
  }
  const safeLevel = Number.isFinite(level) ? Math.max(1, Math.min(100, level)) : 1;
  const statBudget = _pokemonStatPointBudget(safeLevel);
  const statSpent = _pokemonBuildStatPointsSpent(build);
  if (statSpent > statBudget) {
    issues.push({
      severity: "error",
      message: `Added stat points exceed budget (${statSpent}/${statBudget}).`,
    });
  } else if (statSpent < statBudget) {
    issues.push({
      severity: "warn",
      message: `Unassigned stat points (${statSpent}/${statBudget}).`,
    });
  }
  const learnset = speciesEntry ? _getLearnsetForSpecies(speciesEntry.name) : [];
  const learnableByLevel = new Set(
    (learnset || [])
      .filter((entry) => Number(entry.level || 0) <= safeLevel)
      .map((entry) => _normalizeSearchText(entry.move))
  );
  const moves = Array.isArray(build?.moves) ? build.moves : [];
  const abilities = Array.isArray(build?.abilities) ? build.abilities : [];
  const items = Array.isArray(build?.items) ? build.items : [];
  const pokeEdges = Array.isArray(build?.poke_edges) ? build.poke_edges : [];
  const MAX_ACTIVE_MOVES = 6;
  if (moves.length > MAX_ACTIVE_MOVES) {
    issues.push({
      severity: "error",
      message: `Move list exceeds limit (${moves.length}/${MAX_ACTIVE_MOVES}).`,
    });
  }
  pushDuplicateIssues(moves, "moves");
  pushDuplicateIssues(abilities, "abilities");
  pushDuplicateIssues(items, "items");
  pushDuplicateIssues(pokeEdges, "Poke Edges");
  moves.forEach((name) => {
    const moveName = String(name || "").trim();
    if (!moveName) return;
    const moveEntry = _getMoveDetail(moveName);
    if (!moveEntry) {
      issues.push({ severity: "error", message: `Move not found: ${moveName}.` });
      return;
    }
    if (speciesEntry && learnsetData && learnset.length && !learnableByLevel.has(_normalizeSearchText(moveName))) {
      issues.push({
        severity: "error",
        message: `Move "${moveName}" is not in ${speciesEntry.name}'s learnset at level ${safeLevel}.`,
      });
    }
  });
  const abilityPools = speciesEntry ? _getAbilityPoolsForSpecies(speciesEntry.name) : null;
  const allowedAbilities = _abilityAllowedByLevel(abilityPools, safeLevel);
  const maxAbilitySlots =
    speciesEntry && abilityPools && allowedAbilities.size ? allowedAbilities.size : 3;
  if (abilities.length > maxAbilitySlots) {
    issues.push({
      severity: "error",
      message: `Ability list exceeds limit (${abilities.length}/${maxAbilitySlots}) at level ${safeLevel}.`,
    });
  }
  abilities.forEach((name) => {
    const abilityName = String(name || "").trim();
    if (!abilityName) return;
    const abilityEntry = _getAbilityDetail(abilityName);
    if (!abilityEntry) {
      issues.push({ severity: "error", message: `Ability not found: ${abilityName}.` });
      return;
    }
    if (speciesEntry && abilityPools && allowedAbilities.size && !allowedAbilities.has(_normalizeSearchText(abilityName))) {
      issues.push({
        severity: "error",
        message: `Ability "${abilityName}" is not available for ${speciesEntry.name} at level ${safeLevel}.`,
      });
    }
  });
  items.forEach((name) => {
    const itemName = String(name || "").trim();
    if (!itemName) return;
    if (!_findItemByName(itemName)) {
      issues.push({ severity: "error", message: `Item not found: ${itemName}.` });
    }
  });
  pokeEdges.forEach((name) => {
    const edgeName = String(name || "").trim();
    if (!edgeName) return;
    const edgeEntry = _findPokeEdgeByName(edgeName);
    if (!edgeEntry) {
      issues.push({ severity: "error", message: `Poke Edge not found: ${edgeName}.` });
      return;
    }
    const prereq = String(edgeEntry.prerequisites || "").trim();
    if (!prereq) return;
    const levelMatches = prereq.match(/Level\s*(\d+)/gi) || [];
    levelMatches.forEach((raw) => {
      const reqLevel = Number(String(raw).replace(/[^0-9]/g, ""));
      if (Number.isFinite(reqLevel) && safeLevel < reqLevel) {
        issues.push({
          severity: "error",
          message: `Poke Edge "${edgeName}" requires level ${reqLevel} (current ${safeLevel}).`,
        });
      }
    });
    if (speciesEntry) {
      const speciesTypes = new Set((speciesEntry.types || []).map((t) => _normalizeSearchText(t)));
      _requiredTypesFromPrereq(prereq).forEach((typeName) => {
        if (!speciesTypes.has(_normalizeSearchText(typeName))) {
          issues.push({
            severity: "error",
            message: `Poke Edge "${edgeName}" requires ${typeName}-Type Pokemon.`,
          });
        }
      });
      const speciesCaps = new Set((speciesEntry.capabilities || []).map((cap) => _normalizeSearchText(cap)));
      _requiredCapabilitiesFromPrereq(prereq).forEach((capName) => {
        if (!speciesCaps.has(_normalizeSearchText(capName))) {
          issues.push({
            severity: "error",
            message: `Poke Edge "${edgeName}" requires capability "${capName}".`,
          });
        }
      });
    }
  });
  const evolutionMinLevel = characterData?.pokemon?.evolution_min_level || {};
  const speciesKey = _normalizeSearchText(speciesName);
  const minEvoLevel = evolutionMinLevel[speciesKey];
  if (
    speciesEntry &&
    Number.isFinite(minEvoLevel) &&
    minEvoLevel > 1 &&
    safeLevel < minEvoLevel &&
    !build.caught
  ) {
    issues.push({
      severity: "error",
      message: `${speciesEntry.name} is normally obtained by evolution at level ${minEvoLevel}. At level ${safeLevel} it must be marked as Caught (wild).`,
    });
  }
  return {
    ok: !issues.some((entry) => entry.severity === "error"),
    issues,
    species: speciesEntry,
  };
}

function _addExtraEntry(kind, name, detail) {
  if (!name) return;
  if (!Array.isArray(characterState.extras)) characterState.extras = [];
  characterState.extras.push({
    className: kind,
    mechanic: name,
    effect: detail || "",
  });
  saveCharacterToStorage();
}

function _addInventoryItem(entry, kindHint = "") {
  if (!entry || !entry.name) return;
  if (!characterState.inventory || typeof characterState.inventory !== "object") {
    characterState.inventory = { key_items: [], pokemon_items: [] };
  }
  const qty = Number(prompt("Quantity:", "1") || 1);
  const listKey =
    kindHint === "pokemon" ||
    /pokemon|pokÃ©|poke/i.test(String(entry.category || "")) ||
    /held|food/i.test(String(kindHint || ""))
      ? "pokemon_items"
      : "key_items";
  characterState.inventory[listKey].push({
    name: entry.name,
    qty: Number.isFinite(qty) ? qty : 1,
    cost: entry.cost || "",
    desc: entry.description || entry.buff || "",
  });
  saveCharacterToStorage();
}

function _getPokemonSpeciesEntry(name) {
  const list = _pokemonSpeciesCatalog();
  const key = _normalizeSearchText(name);
  return list.find((entry) => _normalizeSearchText(entry.name) === key) || null;
}

function _normalizeSpeciesKey(name) {
  let text = String(name || "").trim().toLowerCase();
  if (!text) return "";
  text = text.replace("\u2640", "f").replace("\u2642", "m");
  text = text.replace("â™€", "f").replace("â™‚", "m");
  text = text.replace("(", " ").replace(")", " ");
  text = text.replace("-", " ");
  text = text.replace(/\s+/g, " ").trim();
  return text;
}

const _POKEMON_STAT_POINT_KEYS = ["hp", "atk", "def", "spatk", "spdef", "spd"];

function _pokemonStatPointBudget(level) {
  return _clampPokemonLevel(level || 1, 1) + 10;
}

function _normalizePokemonStatPointsShape(raw) {
  const out = {};
  _POKEMON_STAT_POINT_KEYS.forEach((key) => {
    const value = Number(raw?.[key] ?? 0);
    out[key] = Number.isFinite(value) ? Math.max(0, Math.floor(value)) : 0;
  });
  return out;
}

function _ensurePokemonBuildStatPoints(build) {
  if (!build || typeof build !== "object") return _normalizePokemonStatPointsShape({});
  const normalized = _normalizePokemonStatPointsShape(build.stat_points || {});
  build.stat_points = normalized;
  return normalized;
}

function _pokemonBuildStatPointsSpent(build) {
  const points = _ensurePokemonBuildStatPoints(build);
  return _POKEMON_STAT_POINT_KEYS.reduce((total, key) => total + Number(points[key] || 0), 0);
}

function _sanitizePokemonBuildStatPoints(build) {
  if (!build || typeof build !== "object") return { changed: false, spent: 0, budget: _pokemonStatPointBudget(1) };
  const points = _ensurePokemonBuildStatPoints(build);
  const budget = _pokemonStatPointBudget(build.level || 1);
  let changed = false;
  let spent = _POKEMON_STAT_POINT_KEYS.reduce((total, key) => total + Number(points[key] || 0), 0);
  if (spent <= budget) return { changed, spent, budget };
  // Trim excess points deterministically from the end of the stat key order.
  let overflow = spent - budget;
  for (let idx = _POKEMON_STAT_POINT_KEYS.length - 1; idx >= 0 && overflow > 0; idx -= 1) {
    const key = _POKEMON_STAT_POINT_KEYS[idx];
    const current = Number(points[key] || 0);
    if (current <= 0) continue;
    const reduceBy = Math.min(current, overflow);
    points[key] = current - reduceBy;
    overflow -= reduceBy;
    changed = true;
  }
  spent = _POKEMON_STAT_POINT_KEYS.reduce((total, key) => total + Number(points[key] || 0), 0);
  return { changed, spent, budget };
}

function _pokemonStatWeightMap(speciesEntry) {
  const base = speciesEntry?.base_stats || {};
  return {
    hp: Math.max(1, Number(base.hp || 1)),
    atk: Math.max(1, Number(base.attack || 1)),
    def: Math.max(1, Number(base.defense || 1)),
    spatk: Math.max(1, Number(base.special_attack || 1)),
    spdef: Math.max(1, Number(base.special_defense || 1)),
    spd: Math.max(1, Number(base.speed || 1)),
  };
}

function _autoPokemonStatPointsEven(budget) {
  const safeBudget = Math.max(0, Number(budget || 0));
  const out = _normalizePokemonStatPointsShape({});
  const base = Math.floor(safeBudget / _POKEMON_STAT_POINT_KEYS.length);
  let remaining = safeBudget - base * _POKEMON_STAT_POINT_KEYS.length;
  _POKEMON_STAT_POINT_KEYS.forEach((key) => {
    out[key] = base + (remaining > 0 ? 1 : 0);
    if (remaining > 0) remaining -= 1;
  });
  return out;
}

function _autoPokemonStatPointsWeighted(budget, speciesEntry) {
  const safeBudget = Math.max(0, Number(budget || 0));
  const out = _normalizePokemonStatPointsShape({});
  const weights = _pokemonStatWeightMap(speciesEntry);
  const totalWeight = _POKEMON_STAT_POINT_KEYS.reduce((sum, key) => sum + Number(weights[key] || 1), 0) || 1;
  let spent = 0;
  _POKEMON_STAT_POINT_KEYS.forEach((key) => {
    const value = Math.floor((safeBudget * Number(weights[key] || 1)) / totalWeight);
    out[key] = Math.max(0, value);
    spent += out[key];
  });
  let remaining = safeBudget - spent;
  const order = _POKEMON_STAT_POINT_KEYS.slice().sort((a, b) => Number(weights[b] || 1) - Number(weights[a] || 1));
  let idx = 0;
  while (remaining > 0 && order.length) {
    out[order[idx % order.length]] += 1;
    remaining -= 1;
    idx += 1;
  }
  return out;
}

function _applyAutoPokemonStatPoints(build, speciesEntry, mode = "weighted") {
  if (!build) return false;
  const budget = _pokemonStatPointBudget(build.level || 1);
  const next =
    mode === "even" ? _autoPokemonStatPointsEven(budget) : _autoPokemonStatPointsWeighted(budget, speciesEntry);
  const current = _ensurePokemonBuildStatPoints(build);
  let changed = false;
  _POKEMON_STAT_POINT_KEYS.forEach((key) => {
    if (Number(current[key] || 0) !== Number(next[key] || 0)) changed = true;
    current[key] = Number(next[key] || 0);
  });
  build.stat_points = current;
  return changed;
}

function _fillRemainingPokemonStatPoints(build, speciesEntry, mode = "weighted") {
  if (!build) return false;
  const current = _ensurePokemonBuildStatPoints(build);
  const budget = _pokemonStatPointBudget(build.level || 1);
  const spent = _pokemonBuildStatPointsSpent(build);
  if (spent >= budget) return false;
  const targetAll =
    mode === "even" ? _autoPokemonStatPointsEven(budget) : _autoPokemonStatPointsWeighted(budget, speciesEntry);
  let remaining = budget - spent;
  const order = _POKEMON_STAT_POINT_KEYS.slice().sort((a, b) => Number(targetAll[b] || 0) - Number(targetAll[a] || 0));
  order.forEach((key) => {
    if (remaining <= 0) return;
    const desired = Math.max(0, Number(targetAll[key] || 0) - Number(current[key] || 0));
    if (desired <= 0) return;
    const add = Math.min(desired, remaining);
    current[key] = Number(current[key] || 0) + add;
    remaining -= add;
  });
  let idx = 0;
  while (remaining > 0 && order.length) {
    const key = order[idx % order.length];
    current[key] = Number(current[key] || 0) + 1;
    remaining -= 1;
    idx += 1;
  }
  build.stat_points = current;
  return true;
}

function _clearPokemonStatPoints(build) {
  if (!build) return false;
  const current = _ensurePokemonBuildStatPoints(build);
  let changed = false;
  _POKEMON_STAT_POINT_KEYS.forEach((key) => {
    if (Number(current[key] || 0) !== 0) changed = true;
    current[key] = 0;
  });
  build.stat_points = current;
  return changed;
}

function _duplicatePokemonBuild(build) {
  const cloned = _normalizePokemonBuild(JSON.parse(JSON.stringify(build || {})));
  const name = String(cloned.name || cloned.species || "Pokemon").trim();
  cloned.name = `${name} Copy`;
  return cloned;
}

function trainerToPokemonLevel(trainerLevel) {
  const base = Number(trainerLevel || 1);
  const scaled = Math.round(base * 2);
  if (!Number.isFinite(scaled)) return 1;
  return Math.max(1, Math.min(100, scaled));
}

function _clampPokemonLevel(value, fallback = 1) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return Math.max(1, Math.min(100, Number(fallback) || 1));
  return Math.max(1, Math.min(100, Math.round(numeric)));
}

function _defaultPokemonBuildLevel() {
  const trainerLevel = _clampPokemonLevel(characterState.profile.level || 1, 1);
  return characterState.pokemon_team_auto_level ? trainerToPokemonLevel(trainerLevel) : trainerLevel;
}

function _applyPokemonTeamAutoLevelPreference(parsed) {
  if (!parsed || parsed.pokemon_team_auto_level === undefined) return;
  if (parsed.pokemon_team_auto_level_explicit === undefined) {
    characterState.pokemon_team_auto_level = false;
    characterState.pokemon_team_auto_level_explicit = false;
    return;
  }
  characterState.pokemon_team_auto_level = !!parsed.pokemon_team_auto_level;
  characterState.pokemon_team_auto_level_explicit = !!parsed.pokemon_team_auto_level_explicit;
}

function _learnsetKeyCandidates(speciesName) {
  const raw = _normalizeSpeciesKey(speciesName);
  if (!raw) return [];
  const candidates = [];
  const add = (value) => {
    const key = _normalizeSpeciesKey(value);
    if (key && !candidates.includes(key)) candidates.push(key);
  };
  add(raw);
  add(raw.replace(/%/g, "").trim());
  const tokens = raw.replace(/%/g, "").split(" ").filter(Boolean);
  if (!tokens.length) return candidates;
  const base = tokens[0];
  add(base);
  if (base === "deoxys" && tokens.length > 1) {
    const formToken = tokens[1];
    const deoxysMap = { a: "attack", attack: "attack", d: "defense", defense: "defense", s: "speed", speed: "speed", n: "normal", normal: "normal" };
    const form = deoxysMap[formToken];
    if (form) add(`deoxys ${form}`);
  }
  if (base === "darmanitan") {
    const hasGalar = tokens.includes("galar") || tokens.includes("galarian");
    const formMap = { s: "standard", standard: "standard", z: "zen", zen: "zen" };
    const formToken = tokens.find((token) => formMap[token]);
    const form = formToken ? formMap[formToken] : "";
    if (form) {
      add(`darmanitan ${form}`);
      if (hasGalar) {
        add(`darmanitan ${form} galar`);
        add(`darmanitan ${form}, galar`);
      }
    }
    if (hasGalar) add("darmanitan galar");
  }
  const tokenAliases = {
    female: "f",
    male: "m",
    galarian: "galar",
    hisuian: "hisui",
    alolan: "alola",
    paldean: "paldea",
    incarnate: "i",
    therian: "t",
    average: "average",
    av: "average",
    a: "average",
    small: "small",
    sm: "small",
    s: "small",
    large: "large",
    la: "large",
    l: "large",
    super: "super",
    su: "super",
    da: "day",
    day: "day",
    night: "night",
    midday: "day",
    midnight: "night",
    po: "pom pom",
    pau: "pau",
    pa: "pau",
  };
  const mappedTokens = tokens.map((token) => tokenAliases[token] || token);
  add(mappedTokens.join(" "));
  if (base === "nidoran" && tokens.length > 1) {
    if (["f", "female"].includes(tokens[1])) add("nidoran f");
    if (["m", "male"].includes(tokens[1])) add("nidoran m");
  }
  if (base === "stunfisk" && tokens.length > 1 && ["g", "galar", "galarian"].includes(tokens[1])) {
    add("stunfisk galar");
  }
  if (["pumpkaboo", "gourgeist"].includes(base) && tokens.length > 1) {
    const sizeAlias = { a: "average", av: "average", sm: "small", la: "large", su: "super" };
    const size = sizeAlias[tokens[1]] || tokens[1];
    add(`${base} ${size}`);
  }
  if (base === "rotom") {
    if (tokens.length > 1) {
      const rotomAlias = { n: "normal", fn: "fan", fr: "frost", h: "heat", m: "mow", w: "wash" };
      const form = rotomAlias[tokens[1]] || tokens[1];
      add(`rotom ${form}`);
    }
    add("rotom");
  }
  if (base === "lycanroc" && tokens.length > 1) {
    const lycanrocAlias = { midday: "day", midnight: "night", da: "day", n: "night", d: "dusk" };
    const form = lycanrocAlias[tokens[1]] || tokens[1];
    add(`lycanroc ${form}`);
  }
  const evolutionFallbacks = { basculegion: "basculin" };
  if (evolutionFallbacks[base]) add(evolutionFallbacks[base]);
  return candidates;
}

function _abilityKeyCandidates(speciesName) {
  const raw = _normalizeSpeciesKey(speciesName);
  if (!raw) return [];
  const candidates = [];
  const add = (value) => {
    const key = (value || "").trim();
    if (key && !candidates.includes(key)) candidates.push(key);
  };
  add(raw);
  const rawNoPercent = raw.replace(/%/g, "").trim();
  add(rawNoPercent);
  let rawTokens = rawNoPercent.split(" ").map((token) => token.replace(/[^a-z0-9]+/g, ""));
  rawTokens = rawTokens.filter(Boolean);
  if (rawTokens.length && ["alolan", "galarian", "hisuian", "paldean"].includes(rawTokens[0]) && rawTokens.length > 1) {
    add(`${rawTokens[1]} ${rawTokens[0]}`);
  }
  const shortMap = {
    su: "super",
    la: "large",
    sm: "small",
    av: "average",
    b: "baile",
    po: "pompom",
    pa: "pau",
    i: "incarnate",
    da: "day",
    du: "dusk",
    n: "normal",
    a: "alola",
    g: "galar",
    h: "hisui",
    p: "paldea",
  };
  const expanded = rawTokens.map((token) => shortMap[token] || token);
  add(expanded.join(" "));
  if (expanded.length > 2) add(`${expanded[0]} ${expanded.slice(1).join("")}`);
  if (expanded.length && expanded[0] === "mega" && expanded.length > 1) {
    add(expanded[1]);
    if (expanded.length > 2) add(`${expanded[1]} ${expanded[2]}`);
  }
  const head = expanded[0] || "";
  const tail = expanded.length > 1 ? expanded.slice(1) : [];
  if (head.startsWith("flab")) add("flabebe");
  if (head === "hakamoo") add("hakamo o");
  if (head === "jangmoo") add("jangmo o");
  if (head === "kommoo") add("kommo o");
  if (["darmanitan", "deoxys", "eiscue"].includes(head)) {
    add(head);
    if (head === "darmanitan" && (expanded.includes("galarian") || expanded.includes("galar"))) {
      add("darmanitan galarian");
    }
  }
  if (head === "darmanitan") {
    const hasGalar = tail.some((token) => ["galar", "galarian"].includes(token));
    const formToken = tail.find((token) => ["s", "standard", "z", "zen"].includes(token));
    const formMap = { s: "standard", standard: "standard", z: "zen", zen: "zen" };
    const form = formToken ? formMap[formToken] : "";
    if (form && hasGalar) {
      add(`darmanitan galar, ${form} mode`);
      add(`darmanitan galarian, ${form} mode`);
    }
  }
  if (head === "deoxys") {
    const formToken = tail.find((token) => ["a", "attack", "d", "defense", "s", "speed", "n", "normal"].includes(token));
    const formMap = { a: "attack", attack: "attack", d: "defense", defense: "defense", s: "speed", speed: "speed", n: "normal", normal: "normal" };
    const form = formToken ? formMap[formToken] : "";
    if (form) add(`deoxys ${form} forme`);
  }
  if (["dialga", "giratina", "palkia"].includes(head)) {
    add(head);
    if (tail.some((token) => ["o", "origin"].includes(token))) add(`${head} origin`);
  }
  if (head === "calyrex") {
    add("calyrex");
    if (tail.includes("shadow")) add("calyrex shadow rider");
    if (tail.includes("ice")) add("calyrex ice rider");
  }
  if (head === "hoopa") {
    if (tail.some((token) => ["u", "un", "unbound"].includes(token))) add("hoopa unbound");
    else add("hoopa");
  }
  if (head === "kyurem") {
    add("kyurem");
    if (tail.some((token) => ["r", "reshiram", "white"].includes(token))) add("kyurem white");
    if (tail.some((token) => ["z", "zekrom", "black"].includes(token))) add("kyurem black");
  }
  if (head === "meloetta") {
    add("meloetta");
    if (tail.some((token) => ["step", "pirouette"].includes(token))) add("meloetta pirouette");
  }
  if (head === "shaymin") {
    add("shaymin");
    if (tail.some((token) => ["s", "sky"].includes(token))) add("shaymin sky");
  }
  if (head === "urshifu") {
    if (tail.some((token) => ["r", "rapid", "rapidstrike"].includes(token))) add("urshifu rapidstrike");
    if (tail.some((token) => ["s", "single", "singlestrike"].includes(token))) add("urshifu singlestrike");
  }
  if (head === "wormadam") {
    if (tail.some((token) => ["p", "plant", "paldea"].includes(token))) add("wormadam plant");
    if (tail.some((token) => ["s", "sand", "sandy"].includes(token))) add("wormadam sandy");
    if (tail.some((token) => ["t", "trash"].includes(token))) add("wormadam trash");
  }
  if (["enamorus", "landorus", "thundurus", "tornadus"].includes(head)) {
    add(head);
    if (tail.some((token) => ["t", "therian"].includes(token))) add(`${head} therian`);
  }
  if (["basculegion", "indeedee"].includes(head)) {
    if (tail.some((token) => ["f", "female"].includes(token))) add(`${head} female`);
    if (tail.some((token) => ["m", "male"].includes(token))) add(`${head} male`);
    if (!tail.length) {
      add(`${head} male`);
      add(`${head} female`);
    }
  }
  if (head === "lycanroc") {
    if (tail.some((token) => ["night", "midnight"].includes(token))) add("lycanroc midnight");
    if (tail.some((token) => ["n", "normal", "day", "midday"].includes(token))) add("lycanroc midday");
    if (tail.some((token) => ["dusk"].includes(token))) add("lycanroc dusk");
  }
  if (["zacian", "zamazenta"].includes(head) && tail.some((token) => ["c", "crowned"].includes(token))) {
    add(head);
  }
  if (head === "nidoran") {
    if (tail.some((token) => ["female", "f"].includes(token))) add("nidoran f");
    if (tail.some((token) => ["male", "m"].includes(token))) add("nidoran m");
  }
  if (["pyroar", "meowstic"].includes(head) && !tail.length) {
    add(`${head} male`);
    add(`${head} female`);
  }
  if (head === "zygarde") {
    if (expanded.includes("complete")) add("zygarde complete");
    else if (expanded.some((token) => token.startsWith("10"))) add("zygarde 10");
    else if (expanded.some((token) => token.startsWith("50"))) add("zygarde 50");
    else add("zygarde 50");
  }
  if (head === "oricorio") {
    if (rawTokens.includes("s")) add("oricorio sensu");
    if (rawTokens.includes("b")) add("oricorio baile");
    if (rawTokens.includes("po")) add("oricorio pompom");
    if (rawTokens.includes("pa")) add("oricorio pau");
  }
  const formSuffixes = new Set([
    "alola",
    "galar",
    "hisui",
    "paldea",
    "super",
    "large",
    "small",
    "average",
    "origin",
    "altered",
    "incarnate",
    "therian",
    "core",
    "meteor",
    "crowned",
    "hero",
    "dusk",
    "dawn",
    "ultra",
    "male",
    "female",
    "baile",
    "pom",
    "pom-pom",
    "pau",
    "sensu",
    "red",
    "midday",
    "midnight",
    "day",
    "night",
    "school",
    "solo",
    "amped",
    "low",
    "key",
    "hangry",
    "noice",
    "ice",
  ]);
  let trimmed = expanded.slice();
  while (trimmed.length > 1 && formSuffixes.has(trimmed[trimmed.length - 1])) {
    trimmed = trimmed.slice(0, -1);
    add(trimmed.join(" "));
  }
  if (expanded.length && ["mega", "primal", "gmax", "gigantamax"].includes(expanded[0]) && expanded.length > 1) {
    add(expanded.slice(1).join(" "));
  }
  if (expanded.length > 1 && /^[0-9]+$/.test(expanded[expanded.length - 1])) {
    add(expanded.slice(0, -1).join(" "));
  }
  if (
    expanded.length &&
    ["gourgeist", "pumpkaboo", "oricorio", "rotom", "minior", "wishiwashi", "toxtricity", "meowstic", "indeedee"].includes(
      expanded[0]
    )
  ) {
    add(expanded[0]);
  }
  if (expanded.length) {
    const officialEons = new Set([
      "eevee",
      "vaporeon",
      "jolteon",
      "flareon",
      "espeon",
      "umbreon",
      "leafeon",
      "glaceon",
      "sylveon",
    ]);
    const headName = expanded[0];
    if (headName.endsWith("eon") && !officialEons.has(headName)) add("eevee");
  }
  return candidates;
}

function _getLearnsetForSpecies(name) {
  const learnsetSources = [
    learnsetData,
    masterData?.pokemon?.learnset,
    characterData?.pokemon?.learnset,
  ].filter((entry) => entry && typeof entry === "object");
  if (!learnsetSources.length) return [];
  const candidates = _learnsetKeyCandidates(name);
  for (const source of learnsetSources) {
    for (const key of candidates) {
      const list = source[key];
      if (list && list.length) return list;
    }
  }
  return [];
}

function _getAbilityPoolsForSpecies(name) {
  const pools = _allPokedexAbilityPools();
  const candidates = _abilityKeyCandidates(name);
  for (const key of candidates) {
    if (pools[key]) return pools[key];
  }
  return null;
}

function _pickAbilitiesForLevel(pools, level) {
  if (!pools) return [];
  const starting = Array.from(new Set(pools.starting || []));
  const basic = Array.from(new Set(pools.basic || []));
  const advanced = Array.from(new Set(pools.advanced || []));
  const high = Array.from(new Set(pools.high || []));
  const basePool = starting.length ? starting : basic;
  const basicPool = Array.from(new Set([...starting, ...basic]));
  const advancedPool = Array.from(new Set([...advanced]));
  const highPool = Array.from(new Set([...high]));
  const desired = level < 20 ? 1 : level < 40 ? 2 : 3;
  const current = [];
  const pick = (pool) => {
    const choices = pool.filter((name) => !current.some((existing) => existing.toLowerCase() === name.toLowerCase()));
    if (!choices.length) return null;
    return choices[Math.floor(Math.random() * choices.length)];
  };
  if (current.length < 1) {
    const chosen = pick(basePool) || pick(basicPool) || pick(advancedPool) || pick(highPool);
    if (chosen) current.push(chosen);
  }
  if (desired >= 2 && current.length < 2) {
    const chosen = pick([...basicPool, ...advancedPool]);
    if (chosen) current.push(chosen);
  }
  if (desired >= 3 && current.length < 3) {
    const chosen = pick([...basicPool, ...advancedPool, ...highPool]);
    if (chosen) current.push(chosen);
  }
  return current;
}

function _isRepeatableFrequency(frequency) {
  const text = String(frequency || "").trim().toLowerCase();
  if (text.includes("at-will") || text.includes("eot")) return true;
  return ["standard", "free", "shift", "action"].includes(text);
}

function _frequencyScore(frequency) {
  const text = String(frequency || "").trim().toLowerCase();
  if (text.includes("at-will")) return 40;
  if (text.includes("eot")) return 32;
  if (text.includes("scene x3")) return 20;
  if (text.includes("scene x2")) return 12;
  if (text.includes("scene")) return 8;
  if (text.includes("daily x3")) return -6;
  if (text.includes("daily x2")) return -12;
  if (text.includes("daily")) return -18;
  if (text.includes("standard")) return 16;
  if (["free", "shift", "action"].includes(text)) return 12;
  return 0;
}

function _isSelfDestructiveMove(record) {
  const name = String(record.name || "").trim().toLowerCase();
  if (
    [
      "explosion",
      "self-destruct",
      "mind blown",
      "steel beam",
      "memento",
      "healing wish",
      "lunar dance",
      "misty explosion",
      "final gambit",
    ].includes(name)
  ) {
    return true;
  }
  const text = String(record.effects || "").trim().toLowerCase();
  return [
    "hp is set to -50%",
    "hit points are reduced by 50%",
    "the user faints",
    "user faints",
    "faints after",
    "faints, even if this attack misses",
  ].some((token) => text.includes(token));
}

function _isDamagingMove(record) {
  return String(record.category || "").trim().toLowerCase() !== "status" && Number(record.damage_base || 0) > 0;
}

function _categoryMatchesMode(record, mode) {
  const category = String(record.category || "").trim().toLowerCase();
  if (mode === "physical") return category === "physical";
  if (mode === "special") return category === "special";
  return ["physical", "special"].includes(category);
}

function _genericUtilityStatus(record) {
  const text = `${record.name || ""} ${record.effects || ""}`.toLowerCase();
  return [
    "protect",
    "detect",
    "endure",
    "substitute",
    "screen",
    "recover",
    "heal",
    "restore",
    "roost",
    "wish",
    "taunt",
    "disable",
    "paraly",
    "poison",
    "burn",
    "sleep",
    "drowsy",
    "confus",
    "speed",
    "accuracy",
    "attack",
    "spatk",
    "defense",
    "spdef",
  ].some((token) => text.includes(token));
}

function _movePoolKey(name) {
  const normalized = String(name || "").trim().toLowerCase();
  if (normalized === "hidden power" || normalized.startsWith("hidden power ")) return "hidden power [type]";
  return normalized;
}

function _isMoveFamilyBase(name) {
  return String(name || "").trim().toLowerCase() === "hidden power";
}

function _resolveMoveVariant(record) {
  if (_movePoolKey(record?.name) !== "hidden power [type]") return record;
  const typed = _pokemonMoveCatalog().filter(
    (entry) => _movePoolKey(entry?.name) === "hidden power [type]" && !_isMoveFamilyBase(entry?.name)
  );
  if (!typed.length) return record;
  return typed[Math.floor(Math.random() * typed.length)];
}

function _inferOffenseMode(speciesEntry, candidates) {
  const atk = Number(speciesEntry?.base_stats?.attack || 10);
  const spatk = Number(speciesEntry?.base_stats?.special_attack || 10);
  const physicalHits = candidates.filter(
    (record) => _isDamagingMove(record) && String(record.category || "").trim().toLowerCase() === "physical"
  ).length;
  const specialHits = candidates.filter(
    (record) => _isDamagingMove(record) && String(record.category || "").trim().toLowerCase() === "special"
  ).length;
  const physicalScore = atk * 3 + physicalHits * 6;
  const specialScore = spatk * 3 + specialHits * 6;
  if (Math.abs(physicalScore - specialScore) <= 8) return "mixed";
  return physicalScore > specialScore ? "physical" : "special";
}

function _damageMoveScore(speciesEntry, record, mode) {
  const speciesTypes = new Set((speciesEntry?.types || []).map((t) => String(t || "").trim().toLowerCase()).filter(Boolean));
  const category = String(record.category || "").trim().toLowerCase();
  const db = Number(record.damage_base || 0);
  let score = db * 2.75;
  if (mode === "physical") {
    if (category === "physical") score += 16.0;
    else if (category === "special") score -= 14.0;
  } else if (mode === "special") {
    if (category === "special") score += 16.0;
    else if (category === "physical") score -= 14.0;
  } else if (["physical", "special"].includes(category)) {
    score += 8.0;
  }
  const moveType = String(record.type || "").trim().toLowerCase();
  if (moveType && speciesTypes.has(moveType)) score += 20.0;
  else if (moveType) score -= 4.0;
  score += _frequencyScore(record.frequency);
  const ac = record.ac;
  if (ac === null || ac === undefined) {
    score += 6.0;
  } else {
    score += Math.max(0, 7 - Number(ac)) * 2.2;
    if (Number(ac) >= 5) score -= (Number(ac) - 4) * 4.0;
  }
  const text = String(record.effects || "").trim().toLowerCase();
  if (text.includes("priority")) score += 6.0;
  if (text.includes("high crit") || text.includes("critical hit")) score += 3.0;
  if (text.includes("recoil")) score -= 10.0;
  if (text.includes("set-up effect")) score -= 8.0;
  if (text.includes("must use struggle") || text.includes("must recharge")) score -= 22.0;
  if (text.includes("causes the target to lose") && !text.includes("damage")) score -= 20.0;
  if (_isSelfDestructiveMove(record)) score -= 120.0;
  if (String(record.name || "").trim().toLowerCase() === "struggle") score -= 1000.0;
  return score;
}

function _statusMoveScore(speciesEntry, record, mode) {
  const text = `${record.name || ""} ${record.effects || ""}`.toLowerCase();
  let score = _frequencyScore(record.frequency) * 0.6;
  if (mode === "physical") {
    if (text.includes("attack") || text.includes("atk") || text.includes("physical")) score += 10.0;
  } else if (mode === "special") {
    if (text.includes("special attack") || text.includes("spatk") || text.includes("special")) score += 10.0;
  } else if (text.includes("attack") || text.includes("special attack")) {
    score += 7.0;
  }
  if (text.includes("speed")) score += 8.0;
  if (text.includes("accuracy")) score += 6.0;
  if (["heal", "recover", "restore", "roost", "wish", "drain"].some((token) => text.includes(token))) score += 7.0;
  if (["protect", "detect", "endure", "substitute", "screen"].some((token) => text.includes(token))) score += 6.0;
  if (
    ["sleep", "drowsy", "paraly", "poison", "burn", "confus", "taunt", "fear", "flinch", "stun", "trap", "disable", "suppressed"].some(
      (token) => text.includes(token)
    )
  ) {
    score += 7.0;
  }
  const speciesTypes = new Set((speciesEntry?.types || []).map((t) => String(t || "").trim().toLowerCase()).filter(Boolean));
  const moveType = String(record.type || "").trim().toLowerCase();
  if (moveType && speciesTypes.has(moveType)) score += 2.0;
  if (_isSelfDestructiveMove(record)) score -= 100.0;
  return score;
}

function _recordsFromLearnset(eligibleLearnset) {
  if (!eligibleLearnset || !eligibleLearnset.length) return [];
  const grouped = new Map();
  const sorted = [...eligibleLearnset].sort((a, b) => b.level - a.level);
  sorted.forEach((entry) => {
    const record = moveRecordMap?.get(_normalizeSearchText(entry.move));
    if (!record) return;
    const key = _movePoolKey(record.name);
    const existing = grouped.get(key);
    if (!existing || (_isMoveFamilyBase(record.name) && !_isMoveFamilyBase(existing.name))) {
      grouped.set(key, record);
    }
  });
  return Array.from(grouped.values());
}

function _buildMinMaxMoveset(speciesEntry, candidates) {
  if (!candidates || !candidates.length) return [];
  const offensiveMode = _inferOffenseMode(speciesEntry, candidates);
  const damaging = candidates.filter((record) => _isDamagingMove(record));
  const status = candidates.filter((record) => !_isDamagingMove(record));
  damaging.sort((a, b) => _damageMoveScore(speciesEntry, b, offensiveMode) - _damageMoveScore(speciesEntry, a, offensiveMode));
  const repeatable = damaging.filter((record) => _isRepeatableFrequency(record.frequency));
  const burst = damaging.filter((record) => !repeatable.includes(record));
  const selected = [];
  const usedNames = new Set();
  const usedTypes = new Set();
  const targetDamaging = Math.min(status.length ? 3 : 4, damaging.length);
  const damagingCount = () => selected.filter((record) => _isDamagingMove(record)).length;
  const tryAdd = (record, enforceDiversity = true) => {
    const key = _movePoolKey(record.name);
    if (usedNames.has(key)) return false;
    const moveType = String(record.type || "").trim().toLowerCase();
    if (enforceDiversity && moveType && usedTypes.has(moveType) && damagingCount() >= 2) return false;
    if (!_isDamagingMove(record)) {
      const statusCount = selected.filter(
        (chosen) => String(chosen.category || "").trim().toLowerCase() === "status" || Number(chosen.damage_base || 0) <= 0
      ).length;
      if (statusCount >= 2) return false;
    }
    selected.push(record);
    usedNames.add(key);
    if (moveType) usedTypes.add(moveType);
    return true;
  };
  if (repeatable.length) {
    for (const record of repeatable) {
      if (tryAdd(record)) break;
    }
  }
  for (const record of repeatable) {
    if (damagingCount() >= targetDamaging) break;
    tryAdd(record);
  }
  const maxBurst = repeatable.length ? 1 : targetDamaging;
  let burstAdded = 0;
  for (const record of burst) {
    if (damagingCount() >= targetDamaging) break;
    if (repeatable.length && burstAdded >= maxBurst) continue;
    if (tryAdd(record)) burstAdded += 1;
  }
  for (const record of damaging) {
    if (damagingCount() >= targetDamaging) break;
    tryAdd(record);
  }
  let statusSlots = Math.max(0, Math.min(2, 4 - selected.length));
  if (statusSlots > 0 && status.length) {
    status.sort((a, b) => _statusMoveScore(speciesEntry, b, offensiveMode) - _statusMoveScore(speciesEntry, a, offensiveMode));
    for (const record of status) {
      if (selected.length >= 4 || statusSlots <= 0) break;
      if (tryAdd(record, false)) statusSlots -= 1;
    }
  }
  if (selected.length < 4) {
    for (const record of damaging.concat(status)) {
      if (selected.length >= 4) break;
      tryAdd(record, false);
    }
  }
  return selected.slice(0, 4).map((record) => _resolveMoveVariant(record));
}

function _augmentMovePool(speciesEntry, basePool) {
  const seen = new Set(basePool.map((record) => _movePoolKey(record.name)));
  const pool = basePool.slice();
  const speciesTypes = new Set((speciesEntry?.types || []).map((t) => String(t || "").trim().toLowerCase()).filter(Boolean));
  const offensiveMode = _inferOffenseMode(speciesEntry, basePool);
  const stabDamaging = [];
  const repeatableOfftype = [];
  const fallbackDamaging = [];
  const utilityStatus = [];
  const allMoves = _pokemonMoveCatalog();
  allMoves.forEach((record) => {
    const key = _movePoolKey(record.name);
    if (seen.has(key)) return;
    const moveType = String(record.type || "").trim().toLowerCase();
    if (_isDamagingMove(record)) {
      if (_isSelfDestructiveMove(record)) return;
      if (moveType && speciesTypes.has(moveType)) {
        stabDamaging.push(record);
        return;
      }
      if (_isRepeatableFrequency(record.frequency)) {
        if (offensiveMode === "mixed" || _categoryMatchesMode(record, offensiveMode)) {
          repeatableOfftype.push(record);
        }
        return;
      }
      if (offensiveMode === "mixed" || _categoryMatchesMode(record, offensiveMode)) {
        fallbackDamaging.push(record);
      }
      return;
    }
    if (moveType && speciesTypes.has(moveType)) {
      utilityStatus.push(record);
      return;
    }
    if (_genericUtilityStatus(record)) utilityStatus.push(record);
  });
  stabDamaging.sort((a, b) => _damageMoveScore(speciesEntry, b, offensiveMode) - _damageMoveScore(speciesEntry, a, offensiveMode));
  repeatableOfftype.sort(
    (a, b) => _damageMoveScore(speciesEntry, b, offensiveMode) - _damageMoveScore(speciesEntry, a, offensiveMode)
  );
  fallbackDamaging.sort(
    (a, b) => _damageMoveScore(speciesEntry, b, offensiveMode) - _damageMoveScore(speciesEntry, a, offensiveMode)
  );
  utilityStatus.sort((a, b) => _statusMoveScore(speciesEntry, b, offensiveMode) - _statusMoveScore(speciesEntry, a, offensiveMode));
  const buckets = [
    [stabDamaging, 18],
    [repeatableOfftype, 10],
    [utilityStatus, 8],
    [fallbackDamaging, 12],
  ];
  for (const [bucket, limit] of buckets) {
    let added = 0;
    for (const record of bucket) {
      const key = _movePoolKey(record.name);
      if (seen.has(key)) continue;
      pool.push(record);
      seen.add(key);
      added += 1;
      if (pool.length >= 48 || added >= limit) break;
    }
    if (pool.length >= 48) break;
  }
  return pool;
}

function _selectMovesForSpecies(speciesEntry, level) {
  if (!speciesEntry || !moveRecordMap || !learnsetData) return [];
  const learnset = _getLearnsetForSpecies(speciesEntry.name);
  const eligible = learnset.filter((entry) => Number(entry.level || 0) <= Number(level || 1));
  const candidateRecords = _recordsFromLearnset(eligible);
  let moves = _buildMinMaxMoveset(speciesEntry, candidateRecords);
  const damagingCount = moves.filter((record) => _isDamagingMove(record)).length;
  const repeatableCount = moves.filter((record) => _isDamagingMove(record) && _isRepeatableFrequency(record.frequency)).length;
  if (moves.length < 4 || damagingCount < 2 || repeatableCount === 0) {
    const augmented = _augmentMovePool(speciesEntry, candidateRecords);
    moves = _buildMinMaxMoveset(speciesEntry, augmented);
  }
  if (moves.length && (damagingCount < 2 || repeatableCount === 0)) {
    const offensiveMode = _inferOffenseMode(speciesEntry, candidateRecords);
    const damagingPool = _pokemonMoveCatalog()
      .filter((record) => _isDamagingMove(record) && !_isSelfDestructiveMove(record))
      .sort((a, b) => {
        const scoreA = _damageMoveScore(speciesEntry, a, offensiveMode);
        const scoreB = _damageMoveScore(speciesEntry, b, offensiveMode);
        const repA = _isRepeatableFrequency(a.frequency) ? 1 : 0;
        const repB = _isRepeatableFrequency(b.frequency) ? 1 : 0;
        return repB - repA || scoreB - scoreA;
      });
    for (const record of damagingPool) {
      if (moves.some((existing) => existing.name === record.name)) continue;
      if (moves.length < 4) {
        moves.push(record);
      } else {
        let replaced = false;
        for (let i = moves.length - 1; i >= 0; i -= 1) {
          const move = moves[i];
          if (String(move.category || "").trim().toLowerCase() === "status" || Number(move.damage_base || 0) <= 0) {
            moves[i] = record;
            replaced = true;
            break;
          }
        }
        if (!replaced) moves[moves.length - 1] = record;
      }
      const currentDamaging = moves.filter((entry) => _isDamagingMove(entry)).length;
      const currentRepeatable = moves.filter((entry) => _isDamagingMove(entry) && _isRepeatableFrequency(entry.frequency)).length;
      if (currentDamaging >= 2 && currentRepeatable >= 1) break;
    }
  }
  const allMoves = _pokemonMoveCatalog();
  if (!moves.length && allMoves.length) {
    const fallback = allMoves.find((record) => _isDamagingMove(record)) || allMoves[0];
    if (fallback) moves.push(fallback);
  }
  return moves.slice(0, 4).map((record) => record.name);
}

function _autoFillPokemonBuild(build, speciesEntry, overwrite = false) {
  if (!build || !speciesEntry) return { filled: false, message: "" };
  let filled = false;
  const messageParts = [];
  const level = Number(build.level || characterState.profile.level || 1);
  const pools = _getAbilityPoolsForSpecies(build.species || build.name || speciesEntry.name);
  const abilityList = pools ? _pickAbilitiesForLevel(pools, level) : [];
  const moveList = _selectMovesForSpecies(speciesEntry, level);
  if (abilityList.length) {
    if (overwrite || !Array.isArray(build.abilities) || build.abilities.length === 0) {
      build.abilities = abilityList.slice();
      filled = true;
    }
  } else {
    messageParts.push("No default abilities for this species.");
  }
  if (moveList.length) {
    if (overwrite || !Array.isArray(build.moves) || build.moves.length === 0) {
      build.moves = moveList.slice();
      filled = true;
    }
  } else {
    messageParts.push("No default moves for this species.");
  }
  return { filled, message: messageParts.join(" ") };
}

function _movePickerItemsForBuild(build, speciesEntry) {
  const buildLevel = _clampPokemonLevel(build?.level || 1, 1);
  const learnset = speciesEntry ? _getLearnsetForSpecies(speciesEntry.name) : [];
  const learnableByLevel = new Set(
    (learnset || [])
      .filter((entry) => Number(entry.level || 0) <= buildLevel)
      .map((entry) => _normalizeSearchText(entry.move))
  );
  const allMoves = _pokemonMoveCatalog().slice();
  return allMoves
    .map((entry) => {
      const learnableNow = speciesEntry && learnset.length ? learnableByLevel.has(_normalizeSearchText(entry.name)) : null;
      const meta = [
        entry.type || "",
        entry.category || "",
        entry.damage_base ? `DB ${entry.damage_base}` : "Status",
        entry.range ? `Range ${entry.range}` : "",
        learnableNow === true ? "Learnable now" : learnableNow === false ? `Not learnable at Lv ${buildLevel}` : "",
      ]
        .filter(Boolean)
        .join(" | ");
      return {
        name: entry.name,
        meta,
        hint: _eli5MoveSummary(entry),
        sortWeight: learnableNow === true ? 0 : learnableNow === false ? 2 : 1,
      };
    })
    .sort((a, b) => a.sortWeight - b.sortWeight || a.name.localeCompare(b.name));
}

function _abilityPickerItemsForBuild(build, speciesEntry) {
  const buildLevel = _clampPokemonLevel(build?.level || 1, 1);
  const pools = speciesEntry ? _getAbilityPoolsForSpecies(speciesEntry.name) : null;
  const allowedAbilities = _abilityAllowedByLevel(pools, buildLevel);
  const poolMap = new Map();
  const pushPool = (list, label) =>
    (list || []).forEach((name) => {
      const key = _normalizeSearchText(name);
      if (key && !poolMap.has(key)) poolMap.set(key, label);
    });
  pushPool(pools?.starting, "Starting");
  pushPool(pools?.basic, "Basic");
  pushPool(pools?.advanced, "Advanced");
  pushPool(pools?.high, "High");
  const allAbilities = _pokemonAbilityCatalog().slice();
  return allAbilities
    .map((entry) => {
      const key = _normalizeSearchText(entry.name);
      const pool = poolMap.get(key) || "";
      const usableNow = pool ? allowedAbilities.has(key) : null;
      const meta = [
        pool ? `Pool: ${pool}` : "Not listed for this species",
        usableNow === true ? "Available now" : usableNow === false ? `Locked at Lv ${buildLevel}` : "",
        entry.frequency ? `Freq: ${entry.frequency}` : "",
      ]
        .filter(Boolean)
        .join(" | ");
      return {
        name: entry.name,
        meta,
        hint: _eli5AbilitySummary(entry),
        sortWeight: usableNow === true ? 0 : pool ? 1 : 2,
      };
    })
    .sort((a, b) => a.sortWeight - b.sortWeight || a.name.localeCompare(b.name));
}

function _itemPickerItems() {
  const items = _allItemCatalogEntries().filter(
    (entry) =>
      String(entry.category || "").trim().length > 0 ||
      _hasDisplayValue(entry.slot) ||
      _hasDisplayValue(entry.cost)
  );
  return items
    .slice()
    .sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")))
    .map((entry) => ({
      name: entry.name,
      meta: [entry.category || "", entry.slot || entry.extra || "", _formatCostLabel(entry.cost, "Cost ")]
        .filter(Boolean)
        .join(" | "),
      hint: _eli5ItemSummary(entry),
      sortWeight: 0,
    }));
}

function _pokeEdgePickerItems() {
  return _pokemonPokeEdgeCatalog()
    .slice()
    .sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")))
    .map((entry) => ({
      name: entry.name,
      meta: [entry.prerequisites ? `Prereq: ${entry.prerequisites}` : "", _formatCostLabel(entry.cost)]
        .filter(Boolean)
        .join(" | "),
      hint: _eli5EdgeSummary(entry, { forPokemon: true }),
      sortWeight: 0,
    }));
}

function _speciesPickerItems() {
  const species = _pokemonSpeciesCatalog().slice();
  return species
    .sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")))
    .map((entry) => {
      const types = (entry.types || []).join(" / ");
      const meta = [
        types,
        entry.size ? `Size ${entry.size}` : "",
        entry.weight ? `Weight ${entry.weight}` : "",
      ]
        .filter(Boolean)
        .join(" | ");
      const caps = Array.isArray(entry.capabilities) ? entry.capabilities.filter(Boolean) : [];
      const hint = caps.length
        ? `Capabilities: ${caps.slice(0, 4).join(", ")}${caps.length > 4 ? ", ..." : ""}`
        : "";
      return {
        name: entry.name,
        meta,
        hint,
        sortWeight: 0,
      };
    });
}

function ensureSpeciesDatalist() {
  let list = document.getElementById("pokemon-species-list");
  if (!list) {
    list = document.createElement("datalist");
    list.id = "pokemon-species-list";
    document.body.appendChild(list);
  }
  list.innerHTML = "";
  const speciesList = _pokemonSpeciesCatalog().slice();
  speciesList.sort((a, b) => String(a.name).localeCompare(String(b.name)));
  speciesList.forEach((entry) => {
    const option = document.createElement("option");
    option.value = entry.name;
    list.appendChild(option);
  });
}

function _ensurePokemonBuilds() {
  if (!Array.isArray(characterState.pokemon_builds)) characterState.pokemon_builds = [];
  characterState.pokemon_builds = characterState.pokemon_builds.map((build) => _normalizePokemonBuild(build));
  return characterState.pokemon_builds;
}

function _normalizePokemonBuild(build) {
  const raw = build && typeof build === "object" ? build : {};
  const normalized = { ...raw };
  normalized.name = String(raw.name || raw.species || "").trim();
  normalized.species = String(raw.species || raw.name || "").trim();
  normalized.level = _clampPokemonLevel(raw.level || 1, 1);
  normalized.nature = String(raw.nature || "").trim();
  normalized.battle_side = String(raw.battle_side || "").trim();
  normalized.moves = _moveNameList(raw.moves).slice(0, _rosterMoveLimit());
  normalized.abilities = _entryNameList(raw.abilities).slice(0, 4);
  normalized.items = _entryNameList(raw.items).slice(0, 8);
  normalized.poke_edges = _entryNameList(raw.poke_edges).slice(0, 8);
  normalized.move_sources = _normalizePokemonMoveSources(raw.move_sources);
  normalized.poke_edge_choices = _normalizePokeEdgeChoices(raw.poke_edge_choices);
  normalized.stat_mode = _normalizePokemonStatMode(raw.stat_mode);
  normalized.tutor_points = _normalizeInteger(raw.tutor_points, 0, 0);
  normalized.stats = _normalizedRosterStats(raw.stats);
  normalized.stat_points = _normalizePokemonStatPointsShape(raw.stat_points || {});
  return normalized;
}

function _normalizePokemonBuildPokeEdges(build) {
  if (!build || typeof build !== "object") return;
  const seen = new Set();
  const next = (Array.isArray(build.poke_edges) ? build.poke_edges : [])
    .map((name) => String(name || "").trim())
    .filter((name) => {
      if (!name) return false;
      const key = _normalizeSearchText(name);
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  build.poke_edges = next;
}

function _normalizeAllPokemonBuildPokeEdges() {
  _ensurePokemonBuilds().forEach((build) => _normalizePokemonBuildPokeEdges(build));
}

function _countPokemonBuildPokeEdges() {
  _normalizeAllPokemonBuildPokeEdges();
  return _ensurePokemonBuilds().reduce((total, build) => total + (Array.isArray(build.poke_edges) ? build.poke_edges.length : 0), 0);
}

function _migrateLegacyGlobalPokeEdges(parsed) {
  const legacyNames = [];
  (parsed?.poke_edge_order || []).forEach((name) => legacyNames.push(name));
  (parsed?.poke_edges || []).forEach((name) => legacyNames.push(name));
  if (!legacyNames.length) return false;
  const builds = _ensurePokemonBuilds();
  if (!builds.length) return false;
  const target = builds[0];
  _normalizePokemonBuildPokeEdges(target);
  const existing = new Set((target.poke_edges || []).map((name) => _normalizeSearchText(name)));
  legacyNames.forEach((name) => {
    const trimmed = String(name || "").trim();
    const key = _normalizeSearchText(trimmed);
    if (!trimmed || !key || existing.has(key)) return;
    existing.add(key);
    target.poke_edges.push(trimmed);
  });
  return true;
}

function _buildRemovablePill(label, onRemove, onClick) {
  const pill = document.createElement("span");
  pill.className = "char-pill pill-removable";
  const link = document.createElement("button");
  link.type = "button";
  link.className = "char-pill-link";
  link.textContent = label;
  link.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (onClick) onClick();
  });
  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "pill-remove";
      remove.textContent = "x";
  remove.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (onRemove) onRemove();
  });
  pill.appendChild(link);
  pill.appendChild(remove);
  return pill;
}

function openListPicker({ title, items, onSelect, helpText = "" }) {
  const modal = document.createElement("div");
  modal.className = "char-connection-modal";
  const box = document.createElement("div");
  box.className = "char-connection-box";
  const header = document.createElement("div");
  header.className = "char-section-title";
  header.textContent = title || "Select";
  box.appendChild(header);
  if (helpText) {
    const help = document.createElement("div");
    help.className = "char-feature-meta";
    help.textContent = helpText;
    box.appendChild(help);
  }
  const search = document.createElement("input");
  search.className = "char-search";
  search.placeholder = "Type to filter...";
  box.appendChild(search);
  const list = document.createElement("div");
  list.className = "char-entry-list";
  box.appendChild(list);
  const actions = document.createElement("div");
  actions.className = "char-action-row";
  const close = document.createElement("button");
  close.type = "button";
  close.textContent = "Close";
  close.addEventListener("click", () => modal.remove());
  actions.appendChild(close);
  box.appendChild(actions);
  modal.appendChild(box);
  document.body.appendChild(modal);

  const normalizedItems = (items || []).map((entry, index) => {
    if (typeof entry === "string") {
      return { value: entry, label: entry, meta: "", hint: "", sortWeight: 0, order: index };
    }
    const label = String(entry?.name || entry?.label || entry?.value || "").trim();
    const value = entry?.value !== undefined ? entry.value : label;
    const meta = String(entry?.meta || entry?.description || entry?.effects || entry?.prerequisites || "").trim();
    const hint = String(entry?.hint || entry?.summary || "").trim();
    return {
      value,
      label,
      meta,
      hint,
      sortWeight: Number.isFinite(Number(entry?.sortWeight)) ? Number(entry.sortWeight) : 0,
      order: index,
    };
  });

  const renderList = () => {
    const query = String(search.value || "").trim();
    list.innerHTML = "";
    const ranked = normalizedItems
      .map((entry) => {
        const searchText = `${entry.label} ${entry.meta} ${entry.hint}`.trim();
        const score = query ? _searchMatchScore(searchText, query) : 1;
        return { ...entry, score };
      })
      .filter((entry) => entry.score > 0)
      .sort((a, b) => {
        if (query) {
          return b.score - a.score || a.sortWeight - b.sortWeight || a.label.localeCompare(b.label);
        }
        return a.sortWeight - b.sortWeight || a.order - b.order;
      });
    let visible = 0;
    ranked.forEach((entry) => {
      if (!query && visible >= 200) return;
      visible += 1;
      const row = document.createElement("button");
      row.type = "button";
      row.className = "char-feature-row status-available";
      const label = document.createElement("div");
      label.className = "char-row-title";
      label.textContent = entry.label;
      row.appendChild(label);
      if (entry.meta) {
        const meta = document.createElement("div");
        meta.className = "char-row-meta";
        meta.textContent = entry.meta;
        row.appendChild(meta);
      }
      if (entry.hint) {
        const hint = document.createElement("div");
        hint.className = "char-feature-meta";
        hint.textContent = entry.hint;
        row.appendChild(hint);
      }
      row.addEventListener("click", () => {
        if (onSelect) onSelect(entry.value, entry);
        modal.remove();
      });
      list.appendChild(row);
    });
    if (!visible) {
      const empty = document.createElement("div");
      empty.className = "char-empty";
      empty.textContent = "No matches.";
      list.appendChild(empty);
    }
  };
  search.addEventListener("input", renderList);
  renderList();
  search.focus();
  modal.addEventListener("click", (event) => {
    if (event.target === modal) modal.remove();
  });
}

function _createPokemonBuildFromPrompt() {
  const rawName = prompt("Pokemon name/species:", "");
  if (!rawName) return null;
  const defaultLevel = _defaultPokemonBuildLevel();
  const level = Number(prompt("Pokemon level:", String(defaultLevel)) || defaultLevel);
  const build = {
    name: rawName,
    species: rawName,
    level: _clampPokemonLevel(level, defaultLevel),
    battle_side: "",
    caught: false,
    moves: [],
    abilities: [],
    items: [],
    poke_edges: [],
  };
  _ensurePokemonBuilds().push(build);
  saveCharacterToStorage();
  return build;
}

async function _ensureUsefulChartsData(urls = ["useful_charts.json"]) {
  if (usefulChartsDataCache) return usefulChartsDataCache;
  if (usefulChartsDataPromise) return usefulChartsDataPromise;
  usefulChartsDataPromise = (async () => {
    for (const url of urls) {
      try {
        const response = await fetch(url, { cache: "no-store" });
        if (!response.ok) continue;
        const payload = await response.json();
        if (payload && typeof payload === "object") {
          usefulChartsDataCache = payload;
          return usefulChartsDataCache;
        }
      } catch (error) {
      }
    }
    return null;
  })();
  const result = await usefulChartsDataPromise;
  usefulChartsDataPromise = null;
  return result;
}

function _formatUsefulChartNumber(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toLocaleString("en-US") : String(value ?? "");
}

function _buildUsefulChartSections(data) {
  if (!data || typeof data !== "object") return [];
  return [
    { id: "experience", title: "Experience", type: "table", columns: ["Level", "Exp Needed"], rows: (data.experience_chart || []).map((entry) => [entry.level, _formatUsefulChartNumber(entry.exp_needed)]) },
    { id: "damage-rolled", title: "Rolled Damage", type: "table", columns: ["DB", "Actual Damage"], rows: (data.damage_rolled_chart || []).map((entry) => [entry.damage_base, entry.actual_damage]) },
    { id: "damage-set", title: "Set Damage", type: "table", columns: ["DB", "Actual Damage"], rows: (data.damage_set_chart || []).map((entry) => [entry.damage_base, entry.actual_damage]) },
    { id: "type-chart", title: "Type Effectiveness", type: "table", columns: ["Tier", "Multiplier", "Meaning"], rows: (data.type_effectiveness || []).map((entry) => [entry.label, entry.multiplier, entry.detail]) },
    { id: "type-quirks", title: "Type Quirks", type: "list", items: data.type_quirks || [] },
    { id: "maneuvers", title: "Combat Maneuvers", type: "records", items: data.combat_maneuvers || [] },
    { id: "natures", title: "Nature Chart", type: "table", columns: ["Value", "Nature", "Raise", "Lower"], rows: (data.nature_chart || []).map((entry) => [entry.value, entry.nature, entry.raise, entry.lower]) },
    { id: "capture", title: "Capture Rates", type: "capture", data: data.capture_rate || {} },
    { id: "status", title: "Status Afflictions", type: "status", data: data.status_afflictions || {} },
    { id: "power", title: "Power Chart", type: "table", columns: ["Value", "Heavy Lifting", "Staggering Limit", "Drag Limit"], rows: (data.power_chart || []).map((entry) => [entry.value, entry.heavy_lifting, entry.staggering_weight_limit, entry.drag_weight_limit]) },
    { id: "weight", title: "Weight Classes", type: "table", columns: ["Weight Class", "Rule"], rows: (data.weight_classes || []).map((entry) => [entry.weight_class, entry.rule]) },
    { id: "contest-effects", title: "Contest Effects", type: "name-list", items: data.contest_effects || [] },
    { id: "contest-mechanics", title: "Contest Mechanics", type: "list", items: data.contest_mechanics || [] }
  ];
}

function _appendUsefulChartTable(parent, columns, rows) {
  const wrap = document.createElement("div");
  wrap.className = "char-chart-table-wrap";
  const table = document.createElement("table");
  table.className = "char-chart-table";
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  columns.forEach((label) => {
    const th = document.createElement("th");
    th.textContent = label;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);
  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    row.forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value === null || value === undefined || value === "" ? "-" : String(value);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  wrap.appendChild(table);
  parent.appendChild(wrap);
}

function _appendUsefulChartList(parent, items) {
  const list = document.createElement("ul");
  list.className = "char-chart-list";
  (items || []).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = String(item || "");
    list.appendChild(li);
  });
  parent.appendChild(list);
}

function _appendUsefulChartRecords(parent, items) {
  const list = document.createElement("div");
  list.className = "char-chart-records";
  (items || []).forEach((item) => {
    const card = document.createElement("div");
    card.className = "char-summary-box char-chart-record";
    const title = document.createElement("div");
    title.className = "char-section-title";
    title.textContent = item.name || "Rule";
    card.appendChild(title);
    const metaBits = [item.action ? `Action: ${item.action}` : "", item.ac ? `AC ${item.ac}` : "", item.move_class ? `Class: ${item.move_class}` : "", item.range ? `Range: ${item.range}` : "", item.trigger ? `Trigger: ${item.trigger}` : ""].filter(Boolean);
    if (metaBits.length) {
      const meta = document.createElement("div");
      meta.className = "char-feature-meta";
      meta.textContent = metaBits.join(" | ");
      card.appendChild(meta);
    }
    if (item.effect) {
      const effect = document.createElement("div");
      effect.className = "char-feature-meta";
      effect.textContent = item.effect;
      card.appendChild(effect);
    }
    if (Array.isArray(item.details) && item.details.length) _appendUsefulChartList(card, item.details);
    list.appendChild(card);
  });
  parent.appendChild(list);
}

function _appendUsefulChartCapture(parent, capture) {
  const note = document.createElement("div");
  note.className = "char-feature-meta";
  note.textContent = `Start from ${_formatUsefulChartNumber(capture.base || 100)} and apply each modifier in order.`;
  parent.appendChild(note);
  if (Array.isArray(capture.steps) && capture.steps.length) _appendUsefulChartList(parent, capture.steps);
  [["HP Brackets", capture.hp_brackets], ["Evolution Stage", capture.evolution_stage], ["Rarity", capture.rarity], ["Conditions", capture.conditions]].forEach(([title, rows]) => {
    if (!Array.isArray(rows) || !rows.length) return;
    const label = document.createElement("div");
    label.className = "char-field-note";
    label.textContent = title;
    parent.appendChild(label);
    _appendUsefulChartTable(parent, ["Condition", "Modifier"], rows.map((entry) => [entry.condition, entry.modifier]));
  });
}

function _appendUsefulChartStatus(parent, status) {
  [["Persistent Afflictions", status.persistent], ["Volatile Afflictions", status.volatile]].forEach(([title, items]) => {
    if (!Array.isArray(items) || !items.length) return;
    const label = document.createElement("div");
    label.className = "char-field-note";
    label.textContent = title;
    parent.appendChild(label);
    _appendUsefulChartTable(parent, ["Affliction", "Effect"], items.map((entry) => [entry.name, entry.effect]));
  });
}

function _appendUsefulChartNameList(parent, items) {
  const list = document.createElement("div");
  list.className = "char-chart-records";
  (items || []).forEach((item) => {
    const card = document.createElement("div");
    card.className = "char-summary-box char-chart-record";
    const title = document.createElement("div");
    title.className = "char-section-title";
    title.textContent = item.name || "Rule";
    card.appendChild(title);
    if (item.effect) {
      const body = document.createElement("div");
      body.className = "char-feature-meta";
      body.textContent = item.effect;
      card.appendChild(body);
    }
    list.appendChild(card);
  });
  parent.appendChild(list);
}

function _renderUsefulChartsInto(container, data) {
  const sections = _buildUsefulChartSections(data);
  const tabs = document.createElement("div");
  tabs.className = "char-pill-list char-chart-tabs";
  const content = document.createElement("div");
  content.className = "char-chart-sections";
  sections.forEach((section) => {
    const jump = document.createElement("button");
    jump.type = "button";
    jump.className = "char-pill is-muted";
    jump.textContent = section.title;
    jump.addEventListener("click", () => {
      const target = content.querySelector(`[data-chart-section="${section.id}"]`);
      target?.scrollIntoView({ block: "start", behavior: "smooth" });
    });
    tabs.appendChild(jump);

    const block = document.createElement("section");
    block.className = "char-summary-box char-chart-section";
    block.dataset.chartSection = section.id;
    const title = document.createElement("div");
    title.className = "char-section-title";
    title.textContent = section.title;
    block.appendChild(title);
    if (section.type === "table") _appendUsefulChartTable(block, section.columns || [], section.rows || []);
    if (section.type === "list") _appendUsefulChartList(block, section.items || []);
    if (section.type === "records") _appendUsefulChartRecords(block, section.items || []);
    if (section.type === "capture") _appendUsefulChartCapture(block, section.data || {});
    if (section.type === "status") _appendUsefulChartStatus(block, section.data || {});
    if (section.type === "name-list") _appendUsefulChartNameList(block, section.items || []);
    content.appendChild(block);
  });
  container.appendChild(tabs);
  container.appendChild(content);
}

async function openUsefulChartsModal() {
  const modal = document.createElement("div");
  modal.className = "char-connection-modal";
  const box = document.createElement("div");
  box.className = "char-connection-box char-chart-modal-box";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Useful Charts";
  box.appendChild(title);
  const intro = document.createElement("div");
  intro.className = "char-feature-meta";
  intro.textContent = "Shared quick-reference charts for XP, damage, type matchups, maneuvers, natures, capture, statuses, power, weight, and contests.";
  box.appendChild(intro);
  const loading = document.createElement("div");
  loading.className = "char-feature-meta";
  loading.textContent = "Loading charts...";
  box.appendChild(loading);
  const actions = document.createElement("div");
  actions.className = "char-action-row";
  const close = document.createElement("button");
  close.type = "button";
  close.textContent = "Close";
  close.addEventListener("click", () => modal.remove());
  actions.appendChild(close);
  box.appendChild(actions);
  modal.appendChild(box);
  modal.addEventListener("click", (event) => {
    if (event.target === modal) modal.remove();
  });
  document.body.appendChild(modal);

  const data = await _ensureUsefulChartsData();
  loading.remove();
  if (!data) {
    const error = document.createElement("div");
    error.className = "char-feature-meta";
    error.textContent = "Useful Charts could not be loaded in this build.";
    box.insertBefore(error, actions);
    return;
  }
  _renderUsefulChartsInto(box, data);
}

function openPokemonRosterImportModal() {
  const modal = document.createElement("div");
  modal.className = "char-connection-modal";
  const box = document.createElement("div");
  box.className = "char-connection-box";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Import Tournament Roster CSV";
  box.appendChild(title);
  const note = document.createElement("div");
  note.className = "char-feature-meta";
  note.textContent =
    "Paste roster CSV with headers like side,slot,species,level,nickname,ability,item,move1..move8. Imported rows become Pokemon builds with side assignment.";
  box.appendChild(note);
  const textarea = document.createElement("textarea");
  textarea.className = "char-search";
  textarea.style.minHeight = "260px";
  textarea.placeholder =
    "side,slot,species,level,nickname,ability,item,move1,move2,move3,move4,move5,move6,move7,move8\nplayer,1,Pikachu,50,Sparky,Static,Light Ball,Thunderbolt,Volt Tackle,Fake Out,Protect,Quick Attack,Iron Tail,,\nfoe,1,Garchomp,50,,Rough Skin,Yache Berry,Earthquake,Dragon Claw,Rock Slide,Protect,Swords Dance,Crunch,,";
  box.appendChild(textarea);
  const status = document.createElement("div");
  status.className = "char-feature-meta";
  box.appendChild(status);
  const actions = document.createElement("div");
  actions.className = "char-action-row";
  const fileBtn = document.createElement("button");
  fileBtn.type = "button";
  fileBtn.className = "char-mini-button";
  fileBtn.textContent = "Load CSV File";
  fileBtn.addEventListener("click", () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".csv,text/csv";
    input.addEventListener("change", async () => {
      const file = input.files && input.files[0];
      if (!file) return;
      try {
        textarea.value = await _readTextFile(file);
        status.textContent = `Loaded ${file.name}`;
      } catch (err) {
        alertError(err);
      }
    });
    input.click();
  });
  const replaceBtn = document.createElement("button");
  replaceBtn.type = "button";
  replaceBtn.textContent = "Replace Team";
  replaceBtn.addEventListener("click", () => {
    try {
      const imported = _builderPokemonImportFromRosterCsv(textarea.value);
      characterState.pokemon_builds = imported.builds;
      saveCharacterToStorage();
      _setBattleRosterCsv(imported.csvText, "builder-import");
      renderCharacterPokemonTeam();
      notifyUI("ok", `Imported ${imported.builds.length} Pokemon from roster CSV.`, 2400);
      modal.remove();
    } catch (err) {
      alertError(err);
    }
  });
  const appendBtn = document.createElement("button");
  appendBtn.type = "button";
  appendBtn.className = "char-mini-button";
  appendBtn.textContent = "Append Team";
  appendBtn.addEventListener("click", () => {
    try {
      const imported = _builderPokemonImportFromRosterCsv(textarea.value);
      const builds = _ensurePokemonBuilds();
      imported.builds.forEach((build) => builds.push(build));
      saveCharacterToStorage();
      _setBattleRosterCsv(imported.csvText, "builder-import");
      renderCharacterPokemonTeam();
      notifyUI("ok", `Appended ${imported.builds.length} Pokemon from roster CSV.`, 2400);
      modal.remove();
    } catch (err) {
      alertError(err);
    }
  });
  const close = document.createElement("button");
  close.type = "button";
  close.className = "char-mini-button";
  close.textContent = "Close";
  close.addEventListener("click", () => modal.remove());
  actions.appendChild(fileBtn);
  actions.appendChild(replaceBtn);
  actions.appendChild(appendBtn);
  actions.appendChild(close);
  box.appendChild(actions);
  modal.appendChild(box);
  document.body.appendChild(modal);
  textarea.focus();
  modal.addEventListener("click", (event) => {
    if (event.target === modal) modal.remove();
  });
}

function openPokemonBuildPicker(onSelect) {
  const builds = _ensurePokemonBuilds();
  const modal = document.createElement("div");
  modal.className = "char-connection-modal";
  const box = document.createElement("div");
  box.className = "char-connection-box";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Choose Pokemon Build";
  box.appendChild(title);
  const list = document.createElement("div");
  list.className = "char-pill-list";
  if (!builds.length) {
    const empty = document.createElement("div");
    empty.className = "char-feature-meta";
    empty.textContent = "No Pokemon builds yet.";
    box.appendChild(empty);
  } else {
    builds.forEach((build, idx) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "char-pill char-pill-link";
      btn.textContent = `${build.name} (Lv ${build.level || 1})`;
      btn.addEventListener("click", () => {
        modal.remove();
        if (onSelect) onSelect(build, idx);
      });
      list.appendChild(btn);
    });
    box.appendChild(list);
  }
  const actions = document.createElement("div");
  actions.className = "char-action-row";
  const create = document.createElement("button");
  create.type = "button";
  create.textContent = "New Pokemon Build";
  create.addEventListener("click", () => {
    const build = _createPokemonBuildFromPrompt();
    if (!build) return;
    modal.remove();
    if (onSelect) onSelect(build, builds.length - 1);
  });
  const close = document.createElement("button");
  close.type = "button";
  close.textContent = "Close";
  close.addEventListener("click", () => modal.remove());
  actions.appendChild(create);
  actions.appendChild(close);
  box.appendChild(actions);
  modal.appendChild(box);
  document.body.appendChild(modal);
}

function showSkillDetail(skillName) {
  if (!skillName) return;
  const desc = _getSkillDescription(skillName);
  const related = _relatedEntriesForSkill(skillName);
  const modal = document.createElement("div");
  modal.className = "char-connection-modal";
  const box = document.createElement("div");
  box.className = "char-connection-box";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = `Skill: ${skillName}`;
  box.appendChild(title);
  _appendDetailBlock(box, "Simple Guide", _eli5SkillSummary(skillName, desc));
  _appendDetailBlock(box, "Rules Text", desc || "No description available.");
  const actions = document.createElement("div");
  actions.className = "char-action-row";
  const toFeatures = document.createElement("button");
  toFeatures.type = "button";
  toFeatures.textContent = "Related Features";
  toFeatures.addEventListener("click", () => {
    focusSkillConnections(skillName, "features");
    modal.remove();
  });
  const toEdges = document.createElement("button");
  toEdges.type = "button";
  toEdges.textContent = "Related Edges";
  toEdges.addEventListener("click", () => {
    focusSkillConnections(skillName, "edges");
    modal.remove();
  });
  actions.appendChild(toFeatures);
  actions.appendChild(toEdges);
  box.appendChild(actions);
  const listWrap = document.createElement("div");
  listWrap.className = "char-sheet-section";
  const listTitle = document.createElement("div");
  listTitle.className = "char-feature-meta";
  listTitle.textContent = "Related (top 8)";
  listWrap.appendChild(listTitle);
  const list = document.createElement("div");
  list.className = "char-pill-list";
  const items = [
    ...related.classes.slice(0, 3).map((c) => ({ kind: "class", name: c.name })),
    ...related.features.slice(0, 3).map((f) => ({ kind: "feature", name: f.name })),
    ...related.edges.slice(0, 2).map((e) => ({ kind: "edge", name: e.name })),
  ];
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "char-feature-meta";
    empty.textContent = "No related entries found.";
    listWrap.appendChild(empty);
  } else {
    items.forEach((item) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "char-pill char-pill-link";
      btn.textContent = `${item.kind}: ${item.name}`;
      btn.addEventListener("click", () => {
        if (item.kind === "class") {
          focusClassConnections(item.name, "class");
        } else if (item.kind === "feature") {
          focusFeature(item.name);
        } else if (item.kind === "edge") {
          focusEdge(item.name);
        }
        modal.remove();
      });
      list.appendChild(btn);
    });
    listWrap.appendChild(list);
  }
  box.appendChild(listWrap);
  const close = document.createElement("button");
  close.type = "button";
  close.textContent = "Close";
  close.addEventListener("click", () => modal.remove());
  box.appendChild(close);
  modal.appendChild(box);
  document.body.appendChild(modal);
}

function showCapabilityDetail(name) {
  if (!name) return;
  const desc = _getCapabilityDescription(name);
  const modal = document.createElement("div");
  modal.className = "char-connection-modal";
  const box = document.createElement("div");
  box.className = "char-connection-box";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = `Capability: ${name}`;
  box.appendChild(title);
  _appendDetailBlock(box, "Simple Guide", _eli5CapabilitySummary(name, desc));
  _appendDetailBlock(box, "Rules Text", desc || "No description available.");
  const actions = document.createElement("div");
  actions.className = "char-action-row";
  const toFeatures = document.createElement("button");
  toFeatures.type = "button";
  toFeatures.textContent = "Related Features";
  toFeatures.addEventListener("click", () => {
    focusCapabilityConnections(name, "features");
    modal.remove();
  });
  actions.appendChild(toFeatures);
  box.appendChild(actions);
  const close = document.createElement("button");
  close.type = "button";
  close.textContent = "Close";
  close.addEventListener("click", () => modal.remove());
  box.appendChild(close);
  modal.appendChild(box);
  document.body.appendChild(modal);
}

function showMoveDetail(name) {
  if (!name) return;
  const entry = _getMoveDetail(name);
  const modal = document.createElement("div");
  modal.className = "char-connection-modal";
  const box = document.createElement("div");
  box.className = "char-connection-box";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = `Move: ${name}`;
  box.appendChild(title);
  if (entry) {
    _appendDetailBlock(box, "Rules Text", _moveRulesText(entry));
    const meta = document.createElement("div");
    meta.className = "char-feature-meta";
    meta.textContent = [
      entry.type ? `Type: ${entry.type}` : "",
      entry.category ? `Class: ${entry.category}` : "",
      entry.frequency ? `Frequency: ${entry.frequency}` : "",
      entry.ac ? `AC: ${entry.ac}` : "",
      entry.range ? `Range: ${entry.range}` : "",
    ]
      .filter(Boolean)
      .join(" | ");
    box.appendChild(meta);
    _appendDetailBlock(box, "Simple Guide", _eli5MoveSummary(entry));
  }
  const actions = document.createElement("div");
  actions.className = "char-action-row";
  const add = document.createElement("button");
  add.type = "button";
  add.textContent = "Add to Extras";
  add.addEventListener("click", () => {
    const summary = entry ? `${entry.type || ""} ${entry.category || ""} ${entry.frequency || ""}`.trim() : "";
    _addExtraEntry("Move", name, summary);
    modal.remove();
  });
  const addBuild = document.createElement("button");
  addBuild.type = "button";
  addBuild.textContent = "Add to Pokemon Build";
  addBuild.addEventListener("click", () => {
    openPokemonBuildPicker((build) => {
      if (!Array.isArray(build.moves)) build.moves = [];
      if (!build.moves.includes(name)) build.moves.push(name);
      saveCharacterToStorage();
    });
    modal.remove();
  });
  actions.appendChild(add);
  actions.appendChild(addBuild);
  box.appendChild(actions);
  const close = document.createElement("button");
  close.type = "button";
  close.textContent = "Close";
  close.addEventListener("click", () => modal.remove());
  box.appendChild(close);
  modal.appendChild(box);
  document.body.appendChild(modal);
}

function showAbilityDetail(name) {
  if (!name) return;
  const entry = _getAbilityDetail(name);
  const modal = document.createElement("div");
  modal.className = "char-connection-modal";
  const box = document.createElement("div");
  box.className = "char-connection-box";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = `Ability: ${name}`;
  box.appendChild(title);
  if (entry) {
    _appendDetailBlock(box, "Simple Guide", _eli5AbilitySummary(entry));
    const meta = document.createElement("div");
    meta.className = "char-feature-meta";
    meta.textContent = [
      entry.frequency ? `Frequency: ${entry.frequency}` : "",
      entry.trigger ? `Trigger: ${entry.trigger}` : "",
      entry.target ? `Target: ${entry.target}` : "",
      entry.keywords ? `Keywords: ${entry.keywords}` : "",
    ]
      .filter(Boolean)
      .join(" | ");
    if (meta.textContent) box.appendChild(meta);
    _appendDetailBlock(box, "Rules Text", entry.effect || entry.effect_2 || "");
  }
  const actions = document.createElement("div");
  actions.className = "char-action-row";
  const add = document.createElement("button");
  add.type = "button";
  add.textContent = "Add to Extras";
  add.addEventListener("click", () => {
    const summary = entry ? `${entry.frequency || ""} ${entry.effect || ""}`.trim() : "";
    _addExtraEntry("Ability", name, summary);
    modal.remove();
  });
  const addBuild = document.createElement("button");
  addBuild.type = "button";
  addBuild.textContent = "Add to Pokemon Build";
  addBuild.addEventListener("click", () => {
    openPokemonBuildPicker((build) => {
      if (!Array.isArray(build.abilities)) build.abilities = [];
      if (!build.abilities.includes(name)) build.abilities.push(name);
      saveCharacterToStorage();
    });
    modal.remove();
  });
  actions.appendChild(add);
  actions.appendChild(addBuild);
  box.appendChild(actions);
  const close = document.createElement("button");
  close.type = "button";
  close.textContent = "Close";
  close.addEventListener("click", () => modal.remove());
  box.appendChild(close);
  modal.appendChild(box);
  document.body.appendChild(modal);
}

function showItemDetail(entry, kindHint = "") {
  if (typeof entry === "string") {
    entry = _findItemByName(entry) || { name: entry };
  }
  if (!entry || !entry.name) return;
  const modal = document.createElement("div");
  modal.className = "char-connection-modal";
  const box = document.createElement("div");
  box.className = "char-connection-box";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = `Item: ${entry.name}`;
  box.appendChild(title);
  _appendDetailBlock(box, "Simple Guide", _eli5ItemSummary(entry));
  const meta = document.createElement("div");
  meta.className = "char-feature-meta";
  meta.textContent = [entry.category, entry.slot, _formatCostLabel(entry.cost)].filter(Boolean).join(" | ");
  if (meta.textContent) box.appendChild(meta);
  _appendDetailBlock(box, "Rules Text", entry.description || entry.buff || entry.desc || "No description available.");
  const actions = document.createElement("div");
  actions.className = "char-action-row";
  const add = document.createElement("button");
  add.type = "button";
  add.textContent = "Add to Inventory";
  add.addEventListener("click", () => {
    _addInventoryItem(entry, kindHint);
    modal.remove();
  });
  const addBuild = document.createElement("button");
  addBuild.type = "button";
  addBuild.textContent = "Add to Pokemon Build";
  addBuild.addEventListener("click", () => {
    openPokemonBuildPicker((build) => {
      if (!Array.isArray(build.items)) build.items = [];
      if (!build.items.includes(entry.name)) build.items.push(entry.name);
      saveCharacterToStorage();
    });
    modal.remove();
  });
  actions.appendChild(add);
  actions.appendChild(addBuild);
  box.appendChild(actions);
  const close = document.createElement("button");
  close.type = "button";
  close.textContent = "Close";
  close.addEventListener("click", () => modal.remove());
  box.appendChild(close);
  modal.appendChild(box);
  document.body.appendChild(modal);
}

function _isRelatedPrereq(prereq) {
  if (!prereq) return false;
  const text = _normalizeSearchText(prereq);
  const className =
    (characterData?.classes || []).find((cls) => cls.id === characterState.class_id)?.name ||
    characterState.class_id ||
    "";
  const selected = [
    ...Array.from(characterState.features),
    ...Array.from(characterState.edges),
    ...(characterData?.skills || []),
    className,
  ].map(_normalizeSearchText);
  return selected.some((name) => name && text.includes(name));
}

function _getClassNodeByName(name) {
  if (!name) return null;
  const targetId = `class:${name}`;
  return (characterData?.nodes || []).find((node) => node.id === targetId) || null;
}

function _plannerTargets() {
  const targets = [];
  (characterData?.classes || []).forEach((cls) => {
    if (!cls?.name) return;
    const node = _getClassNodeByName(cls.name);
    targets.push({
      kind: "class",
      name: cls.name,
      prereq: node?.prerequisites || "",
      label: `Class: ${cls.name}`,
    });
  });
  (characterData?.features || []).forEach((entry) => {
    if (!entry?.name) return;
    targets.push({
      kind: "feature",
      name: entry.name,
      prereq: entry.prerequisites || "",
      label: `Feature: ${entry.name}`,
    });
  });
  (characterData?.edges_catalog || []).forEach((entry) => {
    if (!entry?.name) return;
    targets.push({
      kind: "edge",
      name: entry.name,
      prereq: entry.prerequisites || "",
      label: `Edge: ${entry.name}`,
    });
  });
  return targets;
}

function _plannerMissingActions(missing) {
  if (!missing) return null;
  const text = String(missing);
  if (text.startsWith("Level")) {
    return { label: text, step: "advancement" };
  }
  if (text.startsWith("Class ")) {
    return { label: text, step: "class" };
  }
  const skillMatch = text.match(/(Pathetic|Untrained|Novice|Adept|Expert|Master)\s+(.+)/i);
  if (skillMatch) {
    return { label: text, step: "skills" };
  }
  const featureNames = (characterData?.features || []).map((f) => f.name);
  const edgeNames = (characterData?.edges_catalog || []).map((e) => e.name);
  if (featureNames.includes(text)) {
    return { label: `Feature: ${text}`, step: "features", search: text };
  }
  if (edgeNames.includes(text)) {
    return { label: `Edge: ${text}`, step: "edges", search: text };
  }
  return { label: text, step: "summary" };
}

function _renderPlannerPanel(container) {
  const plannerBox = document.createElement("div");
  plannerBox.className = "char-summary-box char-planner";
  if (characterState.planner_collapsed) {
    plannerBox.classList.add("is-collapsed");
  }
  const titleRow = document.createElement("div");
  titleRow.className = "char-planner-title";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Build Planner";
  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.className = "char-mini-button";
  toggle.textContent = characterState.planner_collapsed ? "Expand" : "Collapse";
  toggle.addEventListener("click", () => {
    characterState.planner_collapsed = !characterState.planner_collapsed;
    saveCharacterToStorage();
    renderCharacterStep();
  });
  const reset = document.createElement("button");
  reset.type = "button";
  reset.className = "char-mini-button";
  reset.textContent = "Reset";
  titleRow.appendChild(title);
  titleRow.appendChild(reset);
  titleRow.appendChild(toggle);
  plannerBox.appendChild(titleRow);
  const targets = _plannerTargets();
  const selected = new Set(Array.isArray(characterState.planner_targets) ? characterState.planner_targets : []);
  const selectedRow = document.createElement("div");
  selectedRow.className = "char-pill-list char-planner-selected";
  const targetWrap = document.createElement("div");
  targetWrap.className = "char-list-panel char-planner-list";
  if (!targets.length) {
    const empty = document.createElement("span");
    empty.className = "char-pill is-muted";
    empty.textContent = "No planner targets available";
    selectedRow.appendChild(empty);
  } else {
    targets.forEach((target) => {
      const key = `${target.kind}:${target.name}`;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "char-pill char-pill-toggle";
      btn.textContent = target.label;
      btn.dataset.value = key;
      btn.classList.toggle("is-active", selected.has(key));
      btn.setAttribute("aria-pressed", String(selected.has(key)));
      btn.addEventListener("click", () => {
        if (selected.has(key)) selected.delete(key);
        else selected.add(key);
        characterState.planner_targets = Array.from(selected);
        saveCharacterToStorage();
        btn.classList.toggle("is-active", selected.has(key));
        btn.setAttribute("aria-pressed", String(selected.has(key)));
        renderPlannerDetail();
      });
      targetWrap.appendChild(btn);
    });
    if (!selected.size) {
      const hint = document.createElement("span");
      hint.className = "char-pill is-muted char-planner-hint";
      hint.textContent = "No targets selected";
      selectedRow.appendChild(hint);
    }
  }

  const detail = document.createElement("div");
  detail.className = "char-planner-detail";

  const renderPlannerDetail = () => {
    detail.innerHTML = "";
    selectedRow.innerHTML = "";
    if (!selected.size) {
      const hint = document.createElement("span");
      hint.className = "char-pill is-muted char-planner-hint";
      hint.textContent = "No targets selected";
      selectedRow.appendChild(hint);
    } else {
      Array.from(selected).forEach((value) => {
        const target = targets.find((entry) => `${entry.kind}:${entry.name}` === value);
        if (!target) return;
        const pill = document.createElement("button");
        pill.type = "button";
        pill.className = "char-pill char-pill-link";
        pill.textContent = target.label;
        pill.addEventListener("click", () => {
          selected.delete(value);
          characterState.planner_targets = Array.from(selected);
          saveCharacterToStorage();
          const toggle = targetWrap.querySelector(`[data-value="${CSS.escape(value)}"]`);
          if (toggle) {
            toggle.classList.remove("is-active");
            toggle.setAttribute("aria-pressed", "false");
          }
          renderPlannerDetail();
        });
        selectedRow.appendChild(pill);
      });
    }
    if (!selected.size) {
      return;
    }
    Array.from(selected).forEach((value) => {
      const target = targets.find((entry) => `${entry.kind}:${entry.name}` === value);
      if (!target) return;
      const block = document.createElement("div");
      block.className = "char-planner-block";
      const header = document.createElement("div");
      header.className = "char-planner-label";
      header.textContent = target.label;
      block.appendChild(header);
      const statusInfo = prereqStatus(target.prereq || "", target.kind);
      if (!statusInfo.missing.length) {
        const ok = document.createElement("div");
        ok.className = "char-feature-meta";
        ok.textContent = "All prerequisites satisfied.";
        block.appendChild(ok);
      } else {
        const list = document.createElement("div");
        list.className = "char-pill-list";
        statusInfo.missing.forEach((missing) => {
          const action = _plannerMissingActions(missing);
          const row = document.createElement("button");
          row.type = "button";
          row.className = "char-pill char-pill-link";
          row.textContent = action?.label || String(missing);
          row.addEventListener("click", () => {
            if (action?.search) {
              if (action.step === "features") characterState.feature_search = action.search;
              if (action.step === "edges") characterState.edge_search = action.search;
            }
            goToCharacterStep(action?.step || "summary");
          });
          list.appendChild(row);
        });
        block.appendChild(list);
      }
      detail.appendChild(block);
    });
  };

  const resetPlanner = () => {
    selected.clear();
    characterState.planner_targets = [];
    saveCharacterToStorage();
    renderPlannerDetail();
    Array.from(targetWrap.querySelectorAll(".char-pill-toggle")).forEach((btn) => {
      btn.classList.remove("is-active");
      btn.setAttribute("aria-pressed", "false");
    });
  };
  reset.addEventListener("click", resetPlanner);

  renderPlannerDetail();

  const body = document.createElement("div");
  body.className = "char-planner-body";
  body.appendChild(selectedRow);
  const targetHeader = document.createElement("div");
  targetHeader.className = "char-planner-header";
  const targetTitle = document.createElement("div");
  targetTitle.className = "char-feature-meta";
  targetTitle.textContent = "Target list";
  const expand = document.createElement("button");
  expand.type = "button";
  expand.className = "char-mini-button";
  expand.textContent = characterState.planner_targets_expanded ? "Hide" : "Show";
  expand.addEventListener("click", () => {
    characterState.planner_targets_expanded = !characterState.planner_targets_expanded;
    saveCharacterToStorage();
    targetWrap.classList.toggle("is-collapsed", !characterState.planner_targets_expanded);
    expand.textContent = characterState.planner_targets_expanded ? "Hide" : "Show";
  });
  targetHeader.appendChild(targetTitle);
  targetHeader.appendChild(expand);
  body.appendChild(targetHeader);
  targetWrap.classList.toggle("is-collapsed", !characterState.planner_targets_expanded);
  body.appendChild(targetWrap);
  body.appendChild(detail);
  plannerBox.appendChild(body);
  container.appendChild(plannerBox);
}

function _renderBuilderPanel(container) {
  const box = document.createElement("div");
  box.className = "char-summary-box char-builder";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Builder";
  box.appendChild(title);

  const row = document.createElement("div");
  row.className = "char-action-row";

  const levelWrap = document.createElement("label");
  levelWrap.className = "char-field";
  levelWrap.textContent = "Level";
  const levelInput = document.createElement("input");
  levelInput.type = "number";
  levelInput.min = "1";
  levelInput.value = String(characterState.profile.level || 1);
  levelInput.addEventListener("input", () => {
    characterState.profile.level = Number(levelInput.value || 1);
    saveCharacterToStorage();
    renderCharacterStep();
  });
  levelWrap.appendChild(levelInput);
  row.appendChild(levelWrap);

  const randomBtn = document.createElement("button");
  randomBtn.type = "button";
  randomBtn.textContent = "Random Build";
  randomBtn.addEventListener("click", () => {
    randomLegalBuild();
  });
  row.appendChild(randomBtn);

  const resetBtn = document.createElement("button");
  resetBtn.type = "button";
  resetBtn.textContent = "Reset Build";
  resetBtn.addEventListener("click", () => {
    if (!confirm("Reset build? This clears classes, features, edges, skills, and choices.")) return;
    characterState.class_ids = [];
    characterState.class_id = "";
    characterState.features = new Set();
    characterState.edges = new Set();
    characterState.feature_order = [];
    characterState.edge_order = [];
    characterState.skill_background = { adept: "", novice: "", pathetic: [] };
    characterState.training_type = "";
    characterState.skills = {};
    const rules = characterData?.skill_rules || { ranks: [] };
    const skills = characterData?.skills || [];
    const defaultRank = (rules.ranks || [])[1] || "Untrained";
    skills.forEach((skill) => {
      characterState.skills[skill] = defaultRank;
    });
    characterState.advancement_choices = {
      5: "stats",
      10: "stats",
      20: "stats",
      30: "stats",
      40: "stats",
    };
    characterState.override_prereqs = false;
    characterState.step_by_step = false;
    characterState.allow_warnings = false;
    saveCharacterToStorage();
    renderCharacterStep();
  });
  row.appendChild(resetBtn);

  const classCount = Array.isArray(characterState.class_ids) ? characterState.class_ids.length : 0;
  const classBtn = document.createElement("button");
  classBtn.type = "button";
  classBtn.textContent = `Classes: ${classCount}/4`;
  classBtn.addEventListener("click", () => goToCharacterStep("class"));
  row.appendChild(classBtn);

  box.appendChild(row);

  const level = Number(characterState.profile.level || 1);
  const choices = characterState.advancement_choices || {};
  const budgets = computeStatBudgets(level, choices);
  const totalBudget = budgets.general + budgets.restricted;
  const stats = characterState.stats || {};
  const statSpent =
    (Number(stats.hp || 0) - 10) +
    (Number(stats.atk || 0) - 5) +
    (Number(stats.def || 0) - 5) +
    (Number(stats.spatk || 0) - 5) +
    (Number(stats.spdef || 0) - 5) +
    (Number(stats.spd || 0) - 5);
  const pendingStats = totalBudget - statSpent;

  const totals = computeAdvancementTotals(level, choices);
  const pendingFeatures = Math.max(0, totals.features - characterState.features.size);
  const pendingEdges = Math.max(0, totals.edges - characterState.edges.size);

  const pendingRow = document.createElement("div");
  pendingRow.className = "char-action-row";
  const statsBtn = document.createElement("button");
  statsBtn.type = "button";
  statsBtn.textContent = `Pending Stat Points: ${pendingStats}`;
  statsBtn.addEventListener("click", () => goToCharacterStep("profile"));
  const featuresBtn = document.createElement("button");
  featuresBtn.type = "button";
  featuresBtn.textContent = `Pending Features: ${pendingFeatures}`;
  featuresBtn.addEventListener("click", () => goToCharacterStep("features"));
  const edgesBtn = document.createElement("button");
  edgesBtn.type = "button";
  edgesBtn.textContent = `Pending Edges: ${pendingEdges}`;
  edgesBtn.addEventListener("click", () => goToCharacterStep("edges"));
  pendingRow.appendChild(statsBtn);
  pendingRow.appendChild(featuresBtn);
  pendingRow.appendChild(edgesBtn);
  box.appendChild(pendingRow);

  container.appendChild(box);
}

function _renderCloseUnlocks(container) {
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Near Unlocks";
  container.appendChild(title);

  const box = document.createElement("div");
  box.className = "char-summary-box char-no-word-links";
  const list = document.createElement("div");
  list.className = "char-pill-list";
  const entries = [];
  (characterData?.features || []).forEach((entry) => {
    const statusInfo = prereqStatus(entry.prerequisites || "", "feature");
    if (statusInfo.status === "close") entries.push({ ...entry, kind: "feature" });
  });
  (characterData?.edges_catalog || []).forEach((entry) => {
    const statusInfo = prereqStatus(entry.prerequisites || "", "edge");
    if (statusInfo.status === "close") entries.push({ ...entry, kind: "edge" });
  });
  if (!entries.length) {
    const empty = document.createElement("span");
    empty.className = "char-pill is-muted";
    empty.textContent = "No near unlocks";
    _setTooltipAttrs(
      empty,
      "No near unlocks",
      "Nothing is close right now. Adjust prerequisites or add skills/features to unlock more."
    );
    list.appendChild(empty);
    box.appendChild(list);
    container.appendChild(box);
    return;
  }
  entries.slice(0, 12).forEach((entry) => {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "char-pill char-pill-link";
    row.textContent = `${entry.kind === "feature" ? "Feature" : "Edge"}: ${entry.name}`;
    const descParts = [
      entry.prerequisites ? `Prerequisites: ${entry.prerequisites}` : "",
      entry.tags ? `Tags: ${entry.tags}` : "",
      entry.effects || entry.description || "",
    ].filter(Boolean);
    if (descParts.length) {
      _setTooltipAttrs(row, entry.name, descParts.join("\n"));
    }
    row.addEventListener("click", () => {
      if (entry.kind === "feature") {
        characterState.feature_search = entry.name;
        goToCharacterStep("features");
      } else {
        characterState.edge_search = entry.name;
        goToCharacterStep("edges");
      }
    });
    list.appendChild(row);
  });
  box.appendChild(list);
  container.appendChild(box);
}

function suggestEntries(entries, selectedSet) {
  const rules = characterData?.skill_rules || { ranks: [] };
  const skills = characterData?.skills || [];
  const rankedSkills = skills
    .map((s) => ({ skill: s, rank: _rankIndex(_findSkillRank(s), rules) }))
    .sort((a, b) => b.rank - a.rank);
  const topSkills = new Set(rankedSkills.slice(0, 3).map((s) => s.skill));
  const scored = entries
    .filter((entry) => !selectedSet.has(entry.name))
    .map((entry) => {
      const statusInfo = prereqStatus(entry.prerequisites || "");
      const base =
        statusInfo.status === "available"
          ? 3
          : statusInfo.status === "close"
          ? 2
          : statusInfo.status === "unavailable"
          ? 1
          : 0;
      const prereqSkills = extractPrereqSkills(entry.prerequisites || "");
      const skillBonus = prereqSkills.some((s) => topSkills.has(s)) ? 1 : 0;
      return { entry, score: base + skillBonus, status: statusInfo.status };
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score);
  return scored.slice(0, 5);
}

function confirmChoice(action, type, name) {
  const label = `${action} ${type}: ${name}?`;
  return confirm(label);
}

function _validationWarnings() {
  const warnings = [];
  const rules = characterData.skill_rules || { ranks: [] };
  const skills = characterData.skills || [];
  const level = Number(characterState.profile.level || 1);
  if (!characterState.class_id) {
    warnings.push("No class selected.");
  }
  if (Array.isArray(characterState.class_ids) && characterState.class_ids.length > 4) {
    warnings.push("More than 4 classes selected.");
  }
  const budget = characterState.skill_budget;
  if (budget !== null) {
    let totalCost = 0;
    Object.entries(characterState.skills).forEach(([skill, rank]) => {
      if (!skills.includes(skill)) return;
      totalCost += Number(rules.rank_costs?.[rank] ?? 0);
    });
    if (totalCost > budget) {
      warnings.push(`Skill points exceed budget (${totalCost}/${budget}).`);
    }
  }
  const statChoices = characterState.advancement_choices || {};
  const statBudget = computeStatBudgets(level, statChoices);
  const stats = characterState.stats || {};
  const statSpent =
    (Number(stats.hp || 0) - 10) +
    (Number(stats.atk || 0) - 5) +
    (Number(stats.def || 0) - 5) +
    (Number(stats.spatk || 0) - 5) +
    (Number(stats.spdef || 0) - 5) +
    (Number(stats.spd || 0) - 5);
  const nonAtkSpent =
    (Number(stats.hp || 0) - 10) +
    (Number(stats.def || 0) - 5) +
    (Number(stats.spdef || 0) - 5) +
    (Number(stats.spd || 0) - 5);
  const totalStatBudget = statBudget.general + statBudget.restricted;
  if (statSpent > totalStatBudget) {
    warnings.push(`Stat points exceed budget (${statSpent}/${totalStatBudget}).`);
  }
  if (nonAtkSpent > statBudget.general) {
    warnings.push("Stat points for non-Atk/SpAtk exceed general budget.");
  }
  if (level === 1) {
    if (Number(stats.hp || 0) > 15) warnings.push("HP exceeds Level 1 cap (+5).");
    if (Number(stats.atk || 0) > 10) warnings.push("Attack exceeds Level 1 cap (+5).");
    if (Number(stats.def || 0) > 10) warnings.push("Defense exceeds Level 1 cap (+5).");
    if (Number(stats.spatk || 0) > 10) warnings.push("Special Attack exceeds Level 1 cap (+5).");
    if (Number(stats.spdef || 0) > 10) warnings.push("Special Defense exceeds Level 1 cap (+5).");
    if (Number(stats.spd || 0) > 10) warnings.push("Speed exceeds Level 1 cap (+5).");
  }
  const autoBudget = getAutoSkillBudget(level, rules);
  const nonSkillEdges = Math.max(0, Number(characterState.skill_edge_non_skill_count || 0));
  if (characterState.skill_budget_auto && nonSkillEdges > autoBudget) {
    warnings.push(`Non-skill edges exceed total edges (${nonSkillEdges}/${autoBudget}).`);
  }
  if (!characterState.override_prereqs) {
    const maxRank = getMaxRankForLevel(level, rules);
    const maxRankIndex = getSkillRankIndex(maxRank, rules.ranks || []);
    const bgRules = rules.background || {};
    const lockPathetic = bgRules.lock_pathetic_level1 !== false;
    const bg = characterState.skill_background || { adept: "", novice: "", pathetic: [] };
    Object.entries(characterState.skills).forEach(([skill, rank]) => {
      if (!skills.includes(skill)) return;
      const rankIndex = getSkillRankIndex(rank, rules.ranks || []);
      const isBackgroundAdept = bg.adept === skill;
      const isBackgroundPathetic = Array.isArray(bg.pathetic) && bg.pathetic.includes(skill);
      const overCap = rankIndex > maxRankIndex;
      if (overCap && !(level === 1 && isBackgroundAdept && rank === "Adept")) {
        warnings.push(`${skill}: exceeds max rank (${maxRank}) for Level ${level}.`);
      }
      if (lockPathetic && level === 1 && isBackgroundPathetic && rank !== "Pathetic") {
        warnings.push(`${skill}: background Pathetic must stay Pathetic at Level 1.`);
      }
    });
    if (bgRules && (bgRules.adept || bgRules.novice || bgRules.pathetic)) {
      const picks = [bg.adept, bg.novice, ...(bg.pathetic || [])].filter(Boolean);
      const unique = new Set(picks);
      if (bgRules.adept && !bg.adept) warnings.push("Background: select an Adept skill.");
      if (bgRules.novice && !bg.novice) warnings.push("Background: select a Novice skill.");
      if (Number(bgRules.pathetic || 0) > 0) {
        const missing = (bg.pathetic || []).filter((s) => !s).length;
        if (missing > 0) warnings.push("Background: select all Pathetic skills.");
      }
      if (unique.size !== picks.length) {
        warnings.push("Background: skill selections must be distinct.");
      }
    }
  }

  ensurePlaytestScopeForClass(characterState.feature_class_filter);
  const classEntry = (characterData.classes || []).find((cls) => cls.id === characterState.class_id);
  const featureSlots = { ...characterData.feature_slots_by_rank, ...characterState.feature_slots_override };
  const selectedFeatures = Array.from(characterState.features);
  const selectedEdges = Array.from(characterState.edges);
  const nodes = characterData.nodes || [];

  if (classEntry && featureSlots) {
    const countByRank = {};
    selectedFeatures.forEach((name) => {
      const node = nodes.find((n) => n.name === name);
      const rank = node?.rank || 1;
      countByRank[rank] = (countByRank[rank] || 0) + 1;
    });
    Object.entries(featureSlots).forEach(([rank, limit]) => {
      const used = countByRank[rank] || 0;
      if (Number(limit) > 0 && used > Number(limit)) {
        warnings.push(`Rank ${rank} features exceed slot limit (${used}/${limit}).`);
      }
    });
  }

  const checkPrereq = (name, prereq) => {
    if (!prereq) return;
    if (level > 0) {
      const levelMatches = prereq.match(/Level\\s*(\\d+)/gi) || [];
      levelMatches.forEach((match) => {
        const num = Number(match.replace(/\\D+/g, ""));
        if (Number.isFinite(num) && level < num) {
          warnings.push(`${name}: requires Level ${num}.`);
        }
      });
    }
    const className = classEntry?.name;
    if (className && new RegExp(_escapeRegex(className), "i").test(prereq) === false) {
      // no class check
    }
    if (className && /\\bClass\\b/i.test(prereq) && !new RegExp(_escapeRegex(className), "i").test(prereq)) {
      warnings.push(`${name}: class prerequisite may not match selected class.`);
    }
    const skillReqs = _parseSkillRequirements(prereq, rules, skills);
    skillReqs.forEach((req) => {
      const haveRank = _findSkillRank(req.skill);
      if (_rankIndex(haveRank, rules) < _rankIndex(req.rank, rules)) {
        warnings.push(`${name}: requires ${req.rank} ${req.skill}.`);
      }
    });
  };

  selectedFeatures.forEach((feat) => {
    const entry = (characterData.features || []).find((f) => f.name === feat);
    if (entry) {
      checkPrereq(feat, entry.prerequisites);
    }
  });
  selectedEdges.forEach((edge) => {
    const entry = (characterData.edges_catalog || []).find((e) => e.name === edge);
    if (entry) {
      checkPrereq(edge, entry.prerequisites);
    }
  });
  return warnings;
}

function renderMiniSummary() {
  if (!charMiniSummaryEl) return;
  if (charGuidedToggleBtn) {
    charGuidedToggleBtn.textContent = characterState.guided_mode ? "Guided: On" : "Guided Mode";
  }
  const level = Number(characterState.profile.level || 1);
  const rules = characterData?.skill_rules || { ranks: [] };
  const ranks = rules.ranks || [];
  const className =
    (characterData.classes || []).find((cls) => cls.id === characterState.class_id)?.name ||
    characterState.class_id ||
    "-";
  const stats = characterState.stats || { hp: 10, atk: 10, def: 10, spatk: 10, spdef: 10, spd: 10 };
  const summary = computeAdvancementTotals(level, characterState.advancement_choices || {});
  const featureUsed = characterState.features.size;
  const edgeUsed = characterState.edges.size;
  const warnings = _validationWarnings();
  const skills = (characterData.skills || [])
    .map((name) => ({ name, rank: characterState.skills[name] || ranks[1] || "Untrained" }))
    .sort((a, b) => {
      const rankDiff = _rankIndex(b.rank, rules) - _rankIndex(a.rank, rules);
      if (rankDiff !== 0) return rankDiff;
      return String(a.name).localeCompare(String(b.name));
    })
    .slice(0, 5);
  const skillLines = skills.length
    ? skills
        .map(
          (entry) =>
            `<li><button type="button" class="mini-link" data-mini-action="skill" data-skill="${escapeAttr(entry.name)}">${escapeHtml(entry.name)}: ${escapeHtml(entry.rank)}</button></li>`
        )
        .join("")
    : "<li>-</li>";
  charMiniSummaryEl.innerHTML = `
    <div class="mini-header">
      <button type="button" class="mini-link mini-name" data-mini-action="profile">${escapeHtml(characterState.profile.name || "New Trainer")}</button>
      <div class="mini-class">
        <button type="button" class="mini-link" data-mini-action="class">Lv ${escapeHtml(level)} - ${escapeHtml(className)}</button>
      </div>
    </div>
    <div class="mini-section">
      <div class="mini-title">Stats</div>
      <div class="mini-stat-grid">
        <button type="button" class="mini-link" data-mini-action="stats" data-stat="hp">HP ${escapeHtml(stats.hp)}</button>
        <button type="button" class="mini-link" data-mini-action="stats" data-stat="atk">Atk ${escapeHtml(stats.atk)}</button>
        <button type="button" class="mini-link" data-mini-action="stats" data-stat="def">Def ${escapeHtml(stats.def)}</button>
        <button type="button" class="mini-link" data-mini-action="stats" data-stat="spatk">SpA ${escapeHtml(stats.spatk)}</button>
        <button type="button" class="mini-link" data-mini-action="stats" data-stat="spdef">SpD ${escapeHtml(stats.spdef)}</button>
        <button type="button" class="mini-link" data-mini-action="stats" data-stat="spd">Spd ${escapeHtml(stats.spd)}</button>
      </div>
    </div>
    <div class="mini-section">
      <div class="mini-title">Skills</div>
      <ul class="mini-skill-list">${skillLines}</ul>
    </div>
    <div class="mini-section">
      <div class="mini-title">Slots</div>
      <div class="mini-slots">
        <button type="button" class="mini-link" data-mini-action="features">Features: ${featureUsed} / ${summary.features}</button>
        <button type="button" class="mini-link" data-mini-action="edges">Edges: ${edgeUsed} / ${summary.edges}</button>
        <button type="button" class="mini-link" data-mini-action="pokemon-team">Poke Edges: ${_countPokemonBuildPokeEdges()}</button>
      </div>
    </div>
    <div class="mini-section">
      <div class="mini-title">Warnings</div>
      <button type="button" class="mini-warn mini-link ${warnings.length ? "has-warn" : "no-warn"}" data-mini-action="warnings">
        ${warnings.length ? `${warnings.length} issue(s)` : "All clear"}
      </button>
    </div>
  `;
  charMiniSummaryEl.querySelectorAll("[data-mini-action]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const action = btn.getAttribute("data-mini-action");
      if (action === "class") {
        focusClassConnections(className, "features");
      } else if (action === "profile") {
        goToCharacterStep("profile");
      } else if (action === "stats") {
        focusStatConnections(btn.getAttribute("data-stat") || "", "features");
      } else if (action === "skill") {
        focusSkillConnections(btn.getAttribute("data-skill") || "", "features");
      } else if (action === "features") {
        goToCharacterStep("features");
      } else if (action === "edges") {
        goToCharacterStep("edges");
      } else if (action === "pokemon-team" || action === "poke-edges") {
        goToCharacterStep("pokemon-team");
      } else if (action === "warnings") {
        goToCharacterStep("summary");
      }
    });
  });
}

function renderCharacterSummary() {
  charContentEl.innerHTML = "";
  charContentEl.setAttribute("data-step-target", "summary");
  appendNavRow();
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Summary";
  charContentEl.appendChild(title);
  appendStepModeToggle();

  ensurePlaytestScopeForClass(characterState.edge_class_filter);
  const payload = {
    profile: characterState.profile,
    class_ids: Array.isArray(characterState.class_ids) ? characterState.class_ids : [],
    class_id: characterState.class_id,
    class_name: (characterData.classes || []).find((cls) => cls.id === characterState.class_id)?.name || "",
    features: Array.from(characterState.features).sort(),
    edges: Array.from(characterState.edges).sort(),
    skills: characterState.skills,
    stats: characterState.stats,
    skill_budget: characterState.skill_budget,
    skill_budget_auto: characterState.skill_budget_auto,
    skill_edge_non_skill_count: characterState.skill_edge_non_skill_count,
    skill_background: characterState.skill_background,
    advancement_choices: characterState.advancement_choices,
    step_by_step: characterState.step_by_step,
    allow_warnings: characterState.allow_warnings,
    content_scope: characterState.content_scope,
    feature_search: characterState.feature_search,
    edge_search: characterState.edge_search,
    poke_edge_search: characterState.poke_edge_search,
    feature_tag_filter: characterState.feature_tag_filter,
    feature_class_filter: characterState.feature_class_filter,
    edge_class_filter: characterState.edge_class_filter,
    feature_group_mode: characterState.feature_group_mode,
    edge_group_mode: characterState.edge_group_mode,
    feature_filter_available: characterState.feature_filter_available,
    feature_filter_close: characterState.feature_filter_close,
    feature_filter_unavailable: characterState.feature_filter_unavailable,
    feature_filter_blocked: characterState.feature_filter_blocked,
    edge_filter_available: characterState.edge_filter_available,
    edge_filter_close: characterState.edge_filter_close,
    edge_filter_unavailable: characterState.edge_filter_unavailable,
    edge_filter_blocked: characterState.edge_filter_blocked,
    poke_edge_filter_available: characterState.poke_edge_filter_available,
    poke_edge_filter_close: characterState.poke_edge_filter_close,
    poke_edge_filter_unavailable: characterState.poke_edge_filter_unavailable,
    poke_edge_filter_blocked: characterState.poke_edge_filter_blocked,
    extras: characterState.extras,
    pokemon_builds: characterState.pokemon_builds,
    inventory: characterState.inventory,
  };
  const box = document.createElement("div");
  box.className = "char-summary-box";
  const summaryClass =
    (characterData.classes || []).find((cls) => cls.id === characterState.class_id)?.name ||
    characterState.class_id ||
    "Unassigned";
  box.innerHTML = `
    <button type="button" class="char-inline-link" data-summary-action="profile">Name: ${escapeHtml(
      characterState.profile.name || "New Trainer"
    )}</button>
    <button type="button" class="char-inline-link" data-summary-action="class">Class: ${escapeHtml(summaryClass)}</button>
    <button type="button" class="char-inline-link" data-summary-action="profile">Region: ${escapeHtml(
      characterState.profile.region || "Unknown Region"
    )}</button>
    <button type="button" class="char-inline-link" data-summary-action="profile">Concept: ${escapeHtml(
      characterState.profile.concept || "No concept set."
    )}</button>
    <button type="button" class="char-inline-link" data-summary-action="profile">Background: ${escapeHtml(
      characterState.profile.background || "No background entered."
    )}</button>
  `;
  charContentEl.appendChild(box);
  box.querySelectorAll("[data-summary-action]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const action = btn.getAttribute("data-summary-action");
      if (action === "class") {
        focusClassConnections(summaryClass, "class");
      } else if (action === "profile") {
        goToCharacterStep("profile");
      } else {
        goToCharacterStep("summary");
      }
    });
  });
  const warnings = _validationWarnings();
  if (warnings.length) {
    const warnTitle = document.createElement("div");
    warnTitle.className = "char-section-title";
    warnTitle.textContent = "Build Issues";
    charContentEl.appendChild(warnTitle);
    const warnList = document.createElement("div");
    warnList.className = "char-list-panel";
    warnings.forEach((warning) => {
      const row = document.createElement("div");
      row.className = "char-issue-row";
      const text = document.createElement("button");
      text.type = "button";
      text.className = "char-inline-link";
      text.textContent = warning;
      const targetStep = warningTargetStep(warning);
      text.addEventListener("click", () => {
        goToCharacterStep(targetStep);
      });
      const action = document.createElement("button");
      action.type = "button";
      action.className = "char-mini-button";
      action.textContent = `Fix in ${targetStep}`;
      action.addEventListener("click", () => {
        goToCharacterStep(targetStep);
      });
      row.appendChild(text);
      row.appendChild(action);
      warnList.appendChild(row);
    });
    charContentEl.appendChild(warnList);
  }

  _renderPlannerPanel(charContentEl);
  _renderCloseUnlocks(charContentEl);

  const dollTitle = document.createElement("div");
  dollTitle.className = "char-section-title";
  dollTitle.textContent = "Visual Sheet";
  charContentEl.appendChild(dollTitle);
  const doll = document.createElement("div");
  doll.className = "char-paperdoll";
  const paperExtras = Array.isArray(characterState.extras) ? characterState.extras : [];
  const paperInventory = characterState.inventory || { key_items: [], pokemon_items: [] };
  const paperKeyItems = Array.isArray(paperInventory.key_items) ? paperInventory.key_items : [];
  const outfitSlots = ["Hat", "Jacket", "Accessory", "Boots"];
  const gearSlots = ["Satchel", "Device", "Key Item", "Consumable"];
  const outfitNames = outfitSlots.map((label, idx) => {
    const entry = paperExtras[idx];
    return entry?.className || entry?.mechanic || "-";
  });
  const gearNames = gearSlots.map((label, idx) => paperKeyItems[idx]?.name || "-");
  doll.innerHTML = `
    <div class="paperdoll-column">
      ${outfitSlots
        .map(
          (label, idx) => `
        <div class="paperdoll-slot">
          <div class="slot-label">${escapeHtml(label)}</div>
          <div class="slot-value">${escapeHtml(outfitNames[idx])}</div>
        </div>`
        )
        .join("")}
    </div>
    <div class="paperdoll-center">
      <div class="paperdoll-avatar"></div>
      <div class="paperdoll-name">${escapeHtml(characterState.profile.name || "New Trainer")}</div>
      <div class="paperdoll-class">${escapeHtml(summaryClass)}</div>
    </div>
    <div class="paperdoll-column">
      ${gearSlots
        .map(
          (label, idx) => `
        <div class="paperdoll-slot">
          <div class="slot-label">${escapeHtml(label)}</div>
          <div class="slot-value">${escapeHtml(gearNames[idx])}</div>
        </div>`
        )
        .join("")}
    </div>
  `;
  charContentEl.appendChild(doll);

  const sheetTitle = document.createElement("div");
  sheetTitle.className = "char-section-title";
  sheetTitle.textContent = "Character Sheet";
  charContentEl.appendChild(sheetTitle);

  const sheet = document.createElement("div");
  sheet.className = "char-sheet";
  const className =
    (characterData.classes || []).find((cls) => cls.id === characterState.class_id)?.name ||
    characterState.class_id ||
    "-";
  const classIds = Array.isArray(characterState.class_ids) ? characterState.class_ids : [];
  const classButtons = classIds.length
    ? classIds
        .map((id) => {
          const entry = (characterData.classes || []).find((cls) => cls.id === id);
          const name = entry?.name || id;
          return `<button type="button" class="char-pill char-pill-link" data-sheet-action="class" data-class="${escapeAttr(
            name
          )}">${escapeHtml(name)}</button>`;
        })
        .join("")
    : `<button type="button" class="char-pill char-pill-link" data-sheet-action="class" data-class="${escapeAttr(
        className
      )}">${escapeHtml(className)}</button>`;
  const featureList = Array.from(characterState.features).sort();
  const edgeList = Array.from(characterState.edges).sort();
  const skills = characterData.skills || [];
  const skillLines = skills
    .slice()
    .sort((a, b) => String(a).localeCompare(String(b)))
    .map((skill) => ({ name: skill, rank: characterState.skills[skill] || "Untrained" }));
  const profileBlock = `
    <div class="char-sheet-section">
      <div class="char-sheet-title">Profile</div>
      <div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="profile">Name: ${escapeHtml(
        characterState.profile.name || "-"
      )}</button></div>
      <div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="profile">Played By: ${escapeHtml(
        characterState.profile.played_by || "-"
      )}</button></div>
      <div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="profile">Age/Sex: ${escapeHtml(
        characterState.profile.age || "-"
      )} / ${escapeHtml(characterState.profile.sex || "-")}</button></div>
      <div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="profile">Height/Weight: ${escapeHtml(
        characterState.profile.height || "-"
      )} / ${escapeHtml(characterState.profile.weight || "-")}</button></div>
      <div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="profile">Region: ${escapeHtml(
        characterState.profile.region || "-"
      )}</button></div>
      <div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="profile">Concept: ${escapeHtml(
        characterState.profile.concept || "-"
      )}</button></div>
      <div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="profile">Background: ${escapeHtml(
        characterState.profile.background || "-"
      )}</button></div>
    </div>`;
  const classBlock = `
    <div class="char-sheet-section">
      <div class="char-sheet-title">Class</div>
      <div class="char-pill-list">${classButtons}</div>
    </div>`;
  const featurePills = featureList.length
    ? featureList
        .map(
          (name) =>
            `<button type="button" class="char-pill char-pill-link" data-sheet-action="feature" data-name="${escapeAttr(name)}">${escapeHtml(name)}</button>`
        )
        .join("")
    : "<button type=\"button\" class=\"char-pill char-pill-link\" data-sheet-action=\"open-step\" data-step=\"features\">Open Features</button>";
  const edgePills = edgeList.length
    ? edgeList
        .map(
          (name) =>
            `<button type="button" class="char-pill char-pill-link" data-sheet-action="edge" data-name="${escapeAttr(name)}">${escapeHtml(name)}</button>`
        )
        .join("")
    : "<button type=\"button\" class=\"char-pill char-pill-link\" data-sheet-action=\"open-step\" data-step=\"edges\">Open Edges</button>";
  const extras = Array.isArray(characterState.extras) ? characterState.extras : [];
  const extrasList = extras.length
    ? extras
        .map(
          (entry) =>
            `<div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="extra" data-class="${escapeAttr(
              entry.className || ""
            )}">${escapeHtml(entry.className || "")}: ${escapeHtml(entry.mechanic || "")} - ${escapeHtml(entry.effect || "")}</button></div>`
        )
        .join("")
    : "<div class=\"char-sheet-row\"><button type=\"button\" class=\"char-inline-link\" data-sheet-action=\"open-step\" data-step=\"extras\">Open Extras</button></div>";
  const inventory = characterState.inventory || { key_items: [], pokemon_items: [] };
  const keyItems = Array.isArray(inventory.key_items) ? inventory.key_items : [];
  const pokemonItems = Array.isArray(inventory.pokemon_items) ? inventory.pokemon_items : [];
  const keyList = keyItems.length
    ? keyItems
        .map(
          (entry) =>
            `<div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="inventory-item">${escapeHtml(
              entry.name || ""
            )} x${escapeHtml(entry.qty || "")} (${escapeHtml(entry.cost || "")}) ${escapeHtml(entry.desc || "")}</button></div>`
        )
        .join("")
    : "<div class=\"char-sheet-row\"><button type=\"button\" class=\"char-inline-link\" data-sheet-action=\"open-step\" data-step=\"inventory\">Open Inventory</button></div>";
  const pokemonList = pokemonItems.length
    ? pokemonItems
        .map(
          (entry) =>
            `<div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="inventory-item">${escapeHtml(
              entry.name || ""
            )} x${escapeHtml(entry.qty || "")} (${escapeHtml(entry.cost || "")}) ${escapeHtml(entry.desc || "")}</button></div>`
        )
        .join("")
    : "<div class=\"char-sheet-row\"><button type=\"button\" class=\"char-inline-link\" data-sheet-action=\"open-step\" data-step=\"inventory\">Open Inventory</button></div>";
  const pokemonBuilds = Array.isArray(characterState.pokemon_builds) ? characterState.pokemon_builds : [];
  const buildBlocks = pokemonBuilds.length
    ? pokemonBuilds
        .map((build, idx) => {
          const moves = Array.isArray(build.moves) ? build.moves : [];
          const abilities = Array.isArray(build.abilities) ? build.abilities : [];
          const items = Array.isArray(build.items) ? build.items : [];
          const pokeEdges = Array.isArray(build.poke_edges) ? build.poke_edges : [];
          const movePills = moves
            .map(
              (name) =>
                `<button type="button" class="char-pill char-pill-link" data-sheet-action="move" data-name="${escapeAttr(
                  name
                )}">${escapeHtml(name)}</button>`
            )
            .join("");
          const abilityPills = abilities
            .map(
              (name) =>
                `<button type="button" class="char-pill char-pill-link" data-sheet-action="ability" data-name="${escapeAttr(
                  name
                )}">${escapeHtml(name)}</button>`
            )
            .join("");
          const itemPills = items
            .map(
              (name) =>
                `<button type="button" class="char-pill char-pill-link" data-sheet-action="item" data-name="${escapeAttr(
                  name
                )}">${escapeHtml(_pokemonBuildItemLabel(name))}</button>`
            )
            .join("");
          const pokeEdgePills = pokeEdges.map((name) => `<span class="char-pill">${escapeHtml(name)}</span>`).join("");
          return `
            <div class="char-sheet-section">
              <div class="char-sheet-title">${escapeHtml(build.name || build.species || "Pokemon")} (Lv ${escapeHtml(
            build.level || 1
          )})</div>
              <div class="char-sheet-row">${escapeHtml(build.species || build.name || "-")}</div>
              <div class="char-pill-list">${movePills || "<span class=\"char-feature-meta\">No moves</span>"}</div>
              <div class="char-pill-list">${abilityPills || "<span class=\"char-feature-meta\">No abilities</span>"}</div>
              <div class="char-pill-list">${itemPills || "<span class=\"char-feature-meta\">No items</span>"}</div>
              <div class="char-pill-list">${pokeEdgePills || "<span class=\"char-feature-meta\">No Poke Edges</span>"}</div>
              <div class="char-action-row"><button type="button" class="char-mini-button" data-sheet-action="build-remove" data-index="${idx}">Remove Build</button></div>
            </div>
          `;
        })
        .join("")
    : "<div class=\"char-sheet-row\"><button type=\"button\" class=\"char-inline-link\" data-sheet-action=\"open-step\" data-step=\"pokemon-team\">Add Pokemon Build</button></div>";
  const rules = characterData?.skill_rules || { ranks: [] };
  const rankCosts = rules.rank_costs || {};
  const skillsGrid = skillLines
    .map((entry) => {
      const cost = Number(rankCosts[entry.rank] ?? 0);
      const skillDesc = _getSkillDescription(entry.name);
      const body = `Rank: ${entry.rank}\nCost: ${cost}` + (skillDesc ? `\n\n${skillDesc}` : "");
      return `<button type="button" class="char-skill-chip char-pill-link" data-sheet-action="skill" data-skill="${escapeAttr(
        entry.name
      )}" data-tooltip-title="${escapeAttr(`Skill: ${entry.name}`)}" data-tooltip-body="${escapeAttr(
        body
      )}">${escapeHtml(entry.name)}: ${escapeHtml(entry.rank)}</button>`;
    })
    .join("");
  const derived = computeDerivedStats(characterState.stats, characterState.skills, rules, characterState.profile.level);
  const statsBlock = `
    <div class="char-sheet-section">
      <div class="char-sheet-title">Stats</div>
      <div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="profile">HP ${escapeHtml(
        characterState.stats.hp
      )} | Atk ${escapeHtml(characterState.stats.atk)} | Def ${escapeHtml(characterState.stats.def)}</button></div>
      <div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="profile">SpA ${escapeHtml(
        characterState.stats.spatk
      )} | SpD ${escapeHtml(characterState.stats.spdef)} | Spd ${escapeHtml(characterState.stats.spd)}</button></div>
    </div>`;
  const derivedBlock = `
    <div class="char-sheet-section">
      <div class="char-sheet-title">Derived</div>
      <div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="profile">AP ${derived.ap} | Max HP ${derived.maxHp}</button></div>
      <div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="profile">Power ${derived.power} | High Jump ${derived.highJump} | Long Jump ${derived.longJump}</button></div>
      <div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="profile">Overland ${derived.overland} | Swim ${derived.swim} | Throw ${derived.throwingRange}</button></div>
    </div>`;
  sheet.innerHTML = `
    <div class="char-sheet-grid">
      ${profileBlock}
      ${classBlock}
    </div>
    <div class="char-sheet-section">
      <div class="char-sheet-title">Features (${featureList.length})</div>
      <div class="char-pill-list">${featurePills}</div>
    </div>
    <div class="char-sheet-section">
      <div class="char-sheet-title">Edges (${edgeList.length})</div>
      <div class="char-pill-list">${edgePills}</div>
    </div>
    <div class="char-sheet-section">
      <div class="char-sheet-title">Extras (${extras.length})</div>
      ${extrasList}
    </div>
    <div class="char-sheet-section">
      <div class="char-sheet-title">Inventory - Key Items (${keyItems.length})</div>
      <div class="char-sheet-row"><button type="button" class="char-inline-link" data-sheet-action="inventory-item">Funds: ${escapeHtml(characterState.profile.money || "-")}</button></div>
      ${keyList}
    </div>
    <div class="char-sheet-section">
      <div class="char-sheet-title">Inventory - Pokemon Items (${pokemonItems.length})</div>
      ${pokemonList}
    </div>
    <div class="char-sheet-section">
      <div class="char-sheet-title">Pokemon Builds (${pokemonBuilds.length})</div>
      ${buildBlocks}
    </div>
    <div class="char-sheet-section">
      <div class="char-sheet-title">Skills</div>
      <div class="char-sheet-skills">${skillsGrid}</div>
    </div>
  `;
  charContentEl.appendChild(sheet);
  sheet.querySelectorAll("[data-sheet-action]").forEach((btn) => {
    btn.addEventListener("click", (evt) => {
      const action = btn.getAttribute("data-sheet-action");
      if (action === "class") {
        const classText = btn.getAttribute("data-class") || className;
        focusClassConnections(classText, "class");
      } else if (action === "feature") {
        focusFeature(btn.getAttribute("data-name") || "");
      } else if (action === "edge") {
        focusEdge(btn.getAttribute("data-name") || "");
      } else if (action === "profile") {
        goToCharacterStep("profile");
      } else if (action === "skill") {
        if (evt && (evt.shiftKey || evt.altKey)) {
          showSkillDetail(btn.getAttribute("data-skill") || "");
        } else {
          goToCharacterStep("skills");
        }
      } else if (action === "move") {
        showMoveDetail(btn.getAttribute("data-name") || "");
      } else if (action === "ability") {
        showAbilityDetail(btn.getAttribute("data-name") || "");
      } else if (action === "item") {
        const item = _findItemByName(btn.getAttribute("data-name") || "");
        if (item) showItemDetail(item, "item");
      } else if (action === "build-remove") {
        const idx = Number(btn.getAttribute("data-index") || -1);
        if (idx >= 0) {
          characterState.pokemon_builds.splice(idx, 1);
          saveCharacterToStorage();
          renderCharacterSummary();
        }
      } else if (action === "inventory-item") {
        goToCharacterStep("inventory");
      } else if (action === "extra") {
        const sourceClass = btn.getAttribute("data-class") || "";
        if (sourceClass) {
          focusClassConnections(sourceClass, "extras");
        } else {
          goToCharacterStep("extras");
        }
      } else if (action === "open-step") {
        goToCharacterStep(btn.getAttribute("data-step") || "summary");
      }
    });
  });
  const actions = document.createElement("div");
  actions.className = "char-action-row";
  const download = document.createElement("button");
  download.textContent = "Download JSON";
  download.addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "trainer_character.json";
    link.click();
    URL.revokeObjectURL(url);
  });
  actions.appendChild(download);
  const fancyExport = document.createElement("button");
  fancyExport.textContent = "Export Fancy PTU CSVs";
  fancyExport.addEventListener("click", () => {
    exportFancyPtuSheet().catch(alertError);
  });
  actions.appendChild(fancyExport);
  const fancyImport = document.createElement("button");
  fancyImport.textContent = "Import Fancy PTU CSVs";
  const fancyInput = document.createElement("input");
  fancyInput.type = "file";
  fancyInput.accept = ".csv";
  fancyInput.multiple = true;
  fancyInput.style.display = "none";
  fancyImport.addEventListener("click", () => fancyInput.click());
  fancyInput.addEventListener("change", async () => {
    if (!fancyInput.files || !fancyInput.files.length) return;
    try {
      await importFancyPtuCsvFiles(fancyInput.files);
    } catch (err) {
      alertError(err);
    }
  });
  actions.appendChild(fancyImport);
  actions.appendChild(fancyInput);
  const upload = document.createElement("button");
  upload.textContent = "Import JSON";
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = "application/json";
  fileInput.style.display = "none";
  upload.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", async () => {
    const file = fileInput.files && fileInput.files[0];
    if (!file) return;
    try {
      const text = await _readTextFile(file);
      const parsed = JSON.parse(text);
      if (parsed.profile) characterState.profile = { ...characterState.profile, ...parsed.profile };
      if (parsed.class_id) characterState.class_id = parsed.class_id;
      if (Array.isArray(parsed.features)) characterState.features = new Set(parsed.features);
      if (Array.isArray(parsed.edges)) characterState.edges = new Set(parsed.edges);
      if (parsed.skills && typeof parsed.skills === "object") {
        characterState.skills = { ...characterState.skills, ...parsed.skills };
      }
      if (parsed.stats && typeof parsed.stats === "object") {
        characterState.stats = { ...characterState.stats, ...parsed.stats };
      }
      if (parsed.skill_budget !== undefined) {
        characterState.skill_budget = parsed.skill_budget;
      }
      if (parsed.skill_budget_auto !== undefined) {
        characterState.skill_budget_auto = parsed.skill_budget_auto;
      }
      if (parsed.skill_edge_non_skill_count !== undefined) {
        characterState.skill_edge_non_skill_count = parsed.skill_edge_non_skill_count;
      }
      if (parsed.skill_background && typeof parsed.skill_background === "object") {
        characterState.skill_background = { ...characterState.skill_background, ...parsed.skill_background };
      }
      if (parsed.advancement_choices && typeof parsed.advancement_choices === "object") {
        characterState.advancement_choices = { ...characterState.advancement_choices, ...parsed.advancement_choices };
      }
      if (parsed.step_by_step !== undefined) {
        characterState.step_by_step = parsed.step_by_step;
      }
      if (parsed.allow_warnings !== undefined) {
        characterState.allow_warnings = parsed.allow_warnings;
      }
      if (parsed.content_scope !== undefined) characterState.content_scope = parsed.content_scope;
      if (parsed.feature_search !== undefined) characterState.feature_search = parsed.feature_search;
      if (parsed.edge_search !== undefined) characterState.edge_search = parsed.edge_search;
      if (parsed.feature_tag_filter !== undefined) characterState.feature_tag_filter = parsed.feature_tag_filter;
      if (parsed.feature_class_filter !== undefined) characterState.feature_class_filter = parsed.feature_class_filter;
      if (parsed.edge_class_filter !== undefined) characterState.edge_class_filter = parsed.edge_class_filter;
      if (parsed.feature_group_mode !== undefined) characterState.feature_group_mode = parsed.feature_group_mode;
      if (parsed.edge_group_mode !== undefined) characterState.edge_group_mode = parsed.edge_group_mode;
      if (parsed.feature_filter_available !== undefined) characterState.feature_filter_available = parsed.feature_filter_available;
      if (parsed.feature_filter_close !== undefined) characterState.feature_filter_close = parsed.feature_filter_close;
      if (parsed.feature_filter_unavailable !== undefined) characterState.feature_filter_unavailable = parsed.feature_filter_unavailable;
      if (parsed.feature_filter_blocked !== undefined) characterState.feature_filter_blocked = parsed.feature_filter_blocked;
      if (parsed.edge_filter_available !== undefined) characterState.edge_filter_available = parsed.edge_filter_available;
      if (parsed.edge_filter_close !== undefined) characterState.edge_filter_close = parsed.edge_filter_close;
      if (parsed.edge_filter_unavailable !== undefined) characterState.edge_filter_unavailable = parsed.edge_filter_unavailable;
      if (parsed.edge_filter_blocked !== undefined) characterState.edge_filter_blocked = parsed.edge_filter_blocked;
      if (parsed.list_density !== undefined) characterState.list_density = parsed.list_density;
      if (Array.isArray(parsed.extras)) characterState.extras = parsed.extras;
      if (Array.isArray(parsed.pokemon_builds)) characterState.pokemon_builds = parsed.pokemon_builds.map((build) => _normalizePokemonBuild(build));
      _normalizeAllPokemonBuildPokeEdges();
      _migrateLegacyGlobalPokeEdges(parsed);
      if (parsed.inventory && typeof parsed.inventory === "object") characterState.inventory = parsed.inventory;
      if (parsed.extras_search !== undefined) characterState.extras_search = parsed.extras_search;
      if (parsed.inventory_search !== undefined) characterState.inventory_search = parsed.inventory_search;
      if (parsed.extras_catalog_search !== undefined) characterState.extras_catalog_search = parsed.extras_catalog_search;
      if (parsed.extras_catalog_scope !== undefined) characterState.extras_catalog_scope = parsed.extras_catalog_scope;
      if (parsed.inventory_catalog_search !== undefined) characterState.inventory_catalog_search = parsed.inventory_catalog_search;
      if (parsed.inventory_catalog_category !== undefined) characterState.inventory_catalog_category = parsed.inventory_catalog_category;
      if (parsed.inventory_catalog_type !== undefined) characterState.inventory_catalog_type = parsed.inventory_catalog_type;
      if (parsed.inventory_catalog_kind !== undefined) characterState.inventory_catalog_kind = parsed.inventory_catalog_kind;
      if (parsed.pokemon_team_search !== undefined) characterState.pokemon_team_search = parsed.pokemon_team_search;
      if (parsed.pokemon_team_limit !== undefined) characterState.pokemon_team_limit = parsed.pokemon_team_limit;
      _applyPokemonTeamAutoLevelPreference(parsed);
      if (parsed.pokemon_team_autofill !== undefined) characterState.pokemon_team_autofill = parsed.pokemon_team_autofill;
      renderCharacterStep();
    } catch (err) {
      alertError(err);
    }
  });
  actions.appendChild(upload);
  actions.appendChild(fileInput);
  const saveLocal = document.createElement("button");
  saveLocal.textContent = "Save Local";
  saveLocal.addEventListener("click", () => {
    saveCharacterToStorage();
  });
  const loadLocal = document.createElement("button");
  loadLocal.textContent = "Load Local";
  loadLocal.addEventListener("click", () => {
    loadCharacterFromStorage();
    renderCharacterStep();
  });
  actions.appendChild(saveLocal);
  actions.appendChild(loadLocal);
  const openStandalone = document.createElement("button");
  openStandalone.textContent = "Open Standalone";
  openStandalone.addEventListener("click", () => {
    const target = location.protocol === "file:" ? "create.html" : "/create";
    window.open(target, "_blank");
  });
  actions.appendChild(openStandalone);
  const teamPack = document.createElement("button");
  teamPack.textContent = "Save Project ZIP";
  teamPack.addEventListener("click", () => {
    try {
      _downloadTournamentSubmissionPack();
      notifyUI("ok", "Tournament team pack downloaded.", 2200);
    } catch (err) {
      alertError(err);
    }
  });
  actions.appendChild(teamPack);
  charContentEl.appendChild(actions);
}

function saveCharacterToStorage() {
  try {
    const payload = {
      profile: characterState.profile,
      class_ids: Array.isArray(characterState.class_ids) ? characterState.class_ids : [],
      class_id: characterState.class_id,
      features: Array.from(characterState.features),
      edges: Array.from(characterState.edges),
      feature_order: characterState.feature_order,
      edge_order: characterState.edge_order,
      skills: characterState.skills,
      stats: characterState.stats,
      skill_budget: characterState.skill_budget,
      skill_budget_auto: characterState.skill_budget_auto,
      skill_edge_non_skill_count: characterState.skill_edge_non_skill_count,
      skill_background: characterState.skill_background,
      skill_background_edit: characterState.skill_background_edit,
      advancement_choices: characterState.advancement_choices,
      step_by_step: characterState.step_by_step,
      allow_warnings: characterState.allow_warnings,
      guided_mode: characterState.guided_mode,
      content_scope: characterState.content_scope,
      feature_search: characterState.feature_search,
      edge_search: characterState.edge_search,
      poke_edge_search: characterState.poke_edge_search,
      feature_tag_filter: characterState.feature_tag_filter,
      feature_class_filter: characterState.feature_class_filter,
      edge_class_filter: characterState.edge_class_filter,
      class_status_filter: characterState.class_status_filter,
      feature_group_mode: characterState.feature_group_mode,
      edge_group_mode: characterState.edge_group_mode,
      feature_status_filter: characterState.feature_status_filter,
      edge_status_filter: characterState.edge_status_filter,
      feature_filter_available: characterState.feature_filter_available,
      feature_filter_close: characterState.feature_filter_close,
      feature_filter_unavailable: characterState.feature_filter_unavailable,
      feature_filter_blocked: characterState.feature_filter_blocked,
      edge_filter_available: characterState.edge_filter_available,
      edge_filter_close: characterState.edge_filter_close,
      edge_filter_unavailable: characterState.edge_filter_unavailable,
      edge_filter_blocked: characterState.edge_filter_blocked,
      poke_edge_filter_available: characterState.poke_edge_filter_available,
      poke_edge_filter_close: characterState.poke_edge_filter_close,
      poke_edge_filter_unavailable: characterState.poke_edge_filter_unavailable,
      poke_edge_filter_blocked: characterState.poke_edge_filter_blocked,
      planner_collapsed: characterState.planner_collapsed,
      planner_targets: characterState.planner_targets,
      planner_targets_expanded: characterState.planner_targets_expanded,
      training_type: characterState.training_type,
      override_prereqs: characterState.override_prereqs,
      feature_slots_override: characterState.feature_slots_override,
      list_density: characterState.list_density,
      extras: characterState.extras,
      pokemon_builds: characterState.pokemon_builds,
      inventory: characterState.inventory,
      extras_search: characterState.extras_search,
      inventory_search: characterState.inventory_search,
      extras_catalog_search: characterState.extras_catalog_search,
      extras_catalog_scope: characterState.extras_catalog_scope,
      inventory_catalog_search: characterState.inventory_catalog_search,
      inventory_catalog_category: characterState.inventory_catalog_category,
      inventory_catalog_type: characterState.inventory_catalog_type,
      inventory_catalog_kind: characterState.inventory_catalog_kind,
      pokemon_team_search: characterState.pokemon_team_search,
      pokemon_team_limit: characterState.pokemon_team_limit,
      pokemon_team_auto_level: characterState.pokemon_team_auto_level,
      pokemon_team_auto_level_explicit: characterState.pokemon_team_auto_level_explicit,
      pokemon_team_autofill: characterState.pokemon_team_autofill,
    };
    const serialized = JSON.stringify(payload);
    localStorage.setItem("autoptu_character", serialized);
    _pushCharacterHistory(serialized);
  } catch {
    // ignore
  }
}

function setCharacterFromPayload(parsed) {
  if (!parsed || typeof parsed !== "object") return;
  if (parsed.profile) characterState.profile = { ...characterState.profile, ...parsed.profile };
  if (Array.isArray(parsed.class_ids)) characterState.class_ids = parsed.class_ids.slice();
  if (parsed.class_id) characterState.class_id = parsed.class_id;
  if ((!characterState.class_ids || !characterState.class_ids.length) && characterState.class_id) {
    characterState.class_ids = [characterState.class_id];
  }
  if (Array.isArray(parsed.features)) characterState.features = new Set(parsed.features);
  if (Array.isArray(parsed.edges)) characterState.edges = new Set(parsed.edges);
  if (Array.isArray(parsed.feature_order)) characterState.feature_order = parsed.feature_order.slice();
  if (Array.isArray(parsed.edge_order)) characterState.edge_order = parsed.edge_order.slice();
  if (parsed.skills && typeof parsed.skills === "object") {
    characterState.skills = { ...characterState.skills, ...parsed.skills };
  }
  if (parsed.stats && typeof parsed.stats === "object") {
    characterState.stats = { ...characterState.stats, ...parsed.stats };
  }
  if (parsed.skill_budget !== undefined) characterState.skill_budget = parsed.skill_budget;
  if (parsed.skill_budget_auto !== undefined) characterState.skill_budget_auto = parsed.skill_budget_auto;
  if (parsed.skill_edge_non_skill_count !== undefined) {
    characterState.skill_edge_non_skill_count = parsed.skill_edge_non_skill_count;
  }
  if (parsed.skill_background && typeof parsed.skill_background === "object") {
    characterState.skill_background = { ...characterState.skill_background, ...parsed.skill_background };
  }
  if (parsed.skill_background_edit !== undefined) {
    characterState.skill_background_edit = parsed.skill_background_edit;
  }
  if (parsed.advancement_choices && typeof parsed.advancement_choices === "object") {
    characterState.advancement_choices = { ...characterState.advancement_choices, ...parsed.advancement_choices };
  }
  if (parsed.step_by_step !== undefined) characterState.step_by_step = parsed.step_by_step;
  if (parsed.allow_warnings !== undefined) characterState.allow_warnings = parsed.allow_warnings;
  if (parsed.guided_mode !== undefined) characterState.guided_mode = parsed.guided_mode;
  if (parsed.content_scope !== undefined) characterState.content_scope = parsed.content_scope;
  if (parsed.feature_search !== undefined) characterState.feature_search = parsed.feature_search;
  if (parsed.edge_search !== undefined) characterState.edge_search = parsed.edge_search;
  if (parsed.poke_edge_search !== undefined) characterState.poke_edge_search = parsed.poke_edge_search;
  if (parsed.feature_tag_filter !== undefined) characterState.feature_tag_filter = parsed.feature_tag_filter;
  if (parsed.feature_class_filter !== undefined) characterState.feature_class_filter = parsed.feature_class_filter;
  if (parsed.edge_class_filter !== undefined) characterState.edge_class_filter = parsed.edge_class_filter;
  if (parsed.class_status_filter !== undefined) characterState.class_status_filter = parsed.class_status_filter;
  if (parsed.feature_group_mode !== undefined) characterState.feature_group_mode = parsed.feature_group_mode;
  if (parsed.edge_group_mode !== undefined) characterState.edge_group_mode = parsed.edge_group_mode;
  if (parsed.feature_status_filter !== undefined) characterState.feature_status_filter = parsed.feature_status_filter;
  if (parsed.edge_status_filter !== undefined) characterState.edge_status_filter = parsed.edge_status_filter;
  if (parsed.feature_filter_available !== undefined) characterState.feature_filter_available = parsed.feature_filter_available;
  if (parsed.feature_filter_close !== undefined) characterState.feature_filter_close = parsed.feature_filter_close;
  if (parsed.feature_filter_unavailable !== undefined) characterState.feature_filter_unavailable = parsed.feature_filter_unavailable;
  if (parsed.feature_filter_blocked !== undefined) characterState.feature_filter_blocked = parsed.feature_filter_blocked;
  if (parsed.edge_filter_available !== undefined) characterState.edge_filter_available = parsed.edge_filter_available;
  if (parsed.edge_filter_close !== undefined) characterState.edge_filter_close = parsed.edge_filter_close;
  if (parsed.edge_filter_unavailable !== undefined) characterState.edge_filter_unavailable = parsed.edge_filter_unavailable;
  if (parsed.edge_filter_blocked !== undefined) characterState.edge_filter_blocked = parsed.edge_filter_blocked;
  if (parsed.poke_edge_filter_available !== undefined) characterState.poke_edge_filter_available = parsed.poke_edge_filter_available;
  if (parsed.poke_edge_filter_close !== undefined) characterState.poke_edge_filter_close = parsed.poke_edge_filter_close;
  if (parsed.poke_edge_filter_unavailable !== undefined) characterState.poke_edge_filter_unavailable = parsed.poke_edge_filter_unavailable;
  if (parsed.poke_edge_filter_blocked !== undefined) characterState.poke_edge_filter_blocked = parsed.poke_edge_filter_blocked;
  if (parsed.list_density !== undefined) characterState.list_density = parsed.list_density;
  if (Array.isArray(parsed.planner_targets)) characterState.planner_targets = parsed.planner_targets.slice();
  if (parsed.planner_targets_expanded !== undefined) {
    characterState.planner_targets_expanded = parsed.planner_targets_expanded;
  }
  if (parsed.training_type !== undefined) characterState.training_type = parsed.training_type;
  if (Array.isArray(parsed.extras)) characterState.extras = parsed.extras;
      if (Array.isArray(parsed.pokemon_builds)) characterState.pokemon_builds = parsed.pokemon_builds.map((build) => _normalizePokemonBuild(build));
  _normalizeAllPokemonBuildPokeEdges();
  _migrateLegacyGlobalPokeEdges(parsed);
  if (parsed.inventory && typeof parsed.inventory === "object") characterState.inventory = parsed.inventory;
  if (parsed.extras_search !== undefined) characterState.extras_search = parsed.extras_search;
  if (parsed.inventory_search !== undefined) characterState.inventory_search = parsed.inventory_search;
  if (parsed.extras_catalog_search !== undefined) characterState.extras_catalog_search = parsed.extras_catalog_search;
  if (parsed.extras_catalog_scope !== undefined) characterState.extras_catalog_scope = parsed.extras_catalog_scope;
  if (parsed.inventory_catalog_search !== undefined) characterState.inventory_catalog_search = parsed.inventory_catalog_search;
  if (parsed.inventory_catalog_category !== undefined) characterState.inventory_catalog_category = parsed.inventory_catalog_category;
  if (parsed.inventory_catalog_type !== undefined) characterState.inventory_catalog_type = parsed.inventory_catalog_type;
  if (parsed.inventory_catalog_kind !== undefined) characterState.inventory_catalog_kind = parsed.inventory_catalog_kind;
  if (parsed.pokemon_team_search !== undefined) characterState.pokemon_team_search = parsed.pokemon_team_search;
  if (parsed.pokemon_team_limit !== undefined) characterState.pokemon_team_limit = parsed.pokemon_team_limit;
  _applyPokemonTeamAutoLevelPreference(parsed);
  if (parsed.pokemon_team_autofill !== undefined) characterState.pokemon_team_autofill = parsed.pokemon_team_autofill;
  if (parsed.override_prereqs !== undefined) characterState.override_prereqs = parsed.override_prereqs;
  if (parsed.feature_slots_override) {
    characterState.feature_slots_override = { ...parsed.feature_slots_override };
  }
}

function _pushCharacterHistory(serialized) {
  if (!serialized || serialized === lastCharacterSnapshot) return;
  charHistory.push(serialized);
  if (charHistory.length > 100) charHistory.shift();
  charRedoHistory = [];
  lastCharacterSnapshot = serialized;
  _syncHistoryButtons();
}

function _syncHistoryButtons() {
  if (charUndoBtn) charUndoBtn.disabled = charHistory.length <= 1;
  if (charRedoBtn) charRedoBtn.disabled = charRedoHistory.length === 0;
}

function _applyCharacterSnapshot(raw) {
  if (!raw) return;
  try {
    const parsed = JSON.parse(raw);
    setCharacterFromPayload(parsed);
    renderCharacterStep();
  } catch (err) {
    console.error(err);
  }
}

function undoCharacterStep() {
  if (charHistory.length <= 1) return;
  const current = charHistory.pop();
  if (current) charRedoHistory.push(current);
  const prev = charHistory[charHistory.length - 1];
  lastCharacterSnapshot = prev || "";
  _applyCharacterSnapshot(prev);
  _syncHistoryButtons();
}

function redoCharacterStep() {
  const next = charRedoHistory.pop();
  if (!next) return;
  charHistory.push(next);
  lastCharacterSnapshot = next;
  _applyCharacterSnapshot(next);
  _syncHistoryButtons();
}

function loadCharacterFromStorage() {
  try {
    const raw = localStorage.getItem("autoptu_character");
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (parsed.profile) characterState.profile = { ...characterState.profile, ...parsed.profile };
    if (Array.isArray(parsed.class_ids)) characterState.class_ids = parsed.class_ids.slice();
    if (parsed.class_id) characterState.class_id = parsed.class_id;
    if ((!characterState.class_ids || !characterState.class_ids.length) && characterState.class_id) {
      characterState.class_ids = [characterState.class_id];
    }
    if (Array.isArray(parsed.features)) characterState.features = new Set(parsed.features);
    if (Array.isArray(parsed.edges)) characterState.edges = new Set(parsed.edges);
    if (parsed.skills && typeof parsed.skills === "object") {
      characterState.skills = { ...characterState.skills, ...parsed.skills };
    }
    if (parsed.stats && typeof parsed.stats === "object") {
      characterState.stats = { ...characterState.stats, ...parsed.stats };
    }
    if (parsed.skill_budget !== undefined) characterState.skill_budget = parsed.skill_budget;
    if (parsed.skill_budget_auto !== undefined) characterState.skill_budget_auto = parsed.skill_budget_auto;
    if (parsed.skill_edge_non_skill_count !== undefined) {
      characterState.skill_edge_non_skill_count = parsed.skill_edge_non_skill_count;
    }
    if (parsed.skill_background && typeof parsed.skill_background === "object") {
      characterState.skill_background = { ...characterState.skill_background, ...parsed.skill_background };
    }
    if (parsed.skill_background_edit !== undefined) {
      characterState.skill_background_edit = parsed.skill_background_edit;
    }
    if (parsed.advancement_choices && typeof parsed.advancement_choices === "object") {
      characterState.advancement_choices = { ...characterState.advancement_choices, ...parsed.advancement_choices };
    }
    if (parsed.step_by_step !== undefined) {
      characterState.step_by_step = parsed.step_by_step;
    }
    if (parsed.allow_warnings !== undefined) {
      characterState.allow_warnings = parsed.allow_warnings;
    }
    if (parsed.guided_mode !== undefined) {
      characterState.guided_mode = parsed.guided_mode;
    }
    if (parsed.content_scope !== undefined) characterState.content_scope = parsed.content_scope;
    if (parsed.feature_search !== undefined) characterState.feature_search = parsed.feature_search;
    if (parsed.edge_search !== undefined) characterState.edge_search = parsed.edge_search;
    if (parsed.poke_edge_search !== undefined) characterState.poke_edge_search = parsed.poke_edge_search;
    if (parsed.feature_tag_filter !== undefined) characterState.feature_tag_filter = parsed.feature_tag_filter;
    if (parsed.feature_class_filter !== undefined) characterState.feature_class_filter = parsed.feature_class_filter;
    if (parsed.edge_class_filter !== undefined) characterState.edge_class_filter = parsed.edge_class_filter;
    if (parsed.feature_group_mode !== undefined) characterState.feature_group_mode = parsed.feature_group_mode;
    if (parsed.edge_group_mode !== undefined) characterState.edge_group_mode = parsed.edge_group_mode;
    if (parsed.feature_status_filter !== undefined) characterState.feature_status_filter = parsed.feature_status_filter;
    if (parsed.edge_status_filter !== undefined) characterState.edge_status_filter = parsed.edge_status_filter;
    if (parsed.feature_filter_available !== undefined) characterState.feature_filter_available = parsed.feature_filter_available;
    if (parsed.feature_filter_close !== undefined) characterState.feature_filter_close = parsed.feature_filter_close;
    if (parsed.feature_filter_unavailable !== undefined) characterState.feature_filter_unavailable = parsed.feature_filter_unavailable;
    if (parsed.feature_filter_blocked !== undefined) characterState.feature_filter_blocked = parsed.feature_filter_blocked;
    if (parsed.edge_filter_available !== undefined) characterState.edge_filter_available = parsed.edge_filter_available;
    if (parsed.edge_filter_close !== undefined) characterState.edge_filter_close = parsed.edge_filter_close;
    if (parsed.edge_filter_unavailable !== undefined) characterState.edge_filter_unavailable = parsed.edge_filter_unavailable;
    if (parsed.edge_filter_blocked !== undefined) characterState.edge_filter_blocked = parsed.edge_filter_blocked;
    if (parsed.poke_edge_filter_available !== undefined) characterState.poke_edge_filter_available = parsed.poke_edge_filter_available;
    if (parsed.poke_edge_filter_close !== undefined) characterState.poke_edge_filter_close = parsed.poke_edge_filter_close;
    if (parsed.poke_edge_filter_unavailable !== undefined) characterState.poke_edge_filter_unavailable = parsed.poke_edge_filter_unavailable;
    if (parsed.poke_edge_filter_blocked !== undefined) characterState.poke_edge_filter_blocked = parsed.poke_edge_filter_blocked;
    if (parsed.planner_collapsed !== undefined) characterState.planner_collapsed = parsed.planner_collapsed;
    if (parsed.list_density !== undefined) characterState.list_density = parsed.list_density;
    if (Array.isArray(parsed.planner_targets)) characterState.planner_targets = parsed.planner_targets.slice();
    if (parsed.planner_targets_expanded !== undefined) {
      characterState.planner_targets_expanded = parsed.planner_targets_expanded;
    }
    if (parsed.training_type !== undefined) characterState.training_type = parsed.training_type;
    if (Array.isArray(parsed.extras)) characterState.extras = parsed.extras;
    if (Array.isArray(parsed.pokemon_builds)) characterState.pokemon_builds = parsed.pokemon_builds.map((build) => _normalizePokemonBuild(build));
    if (parsed.inventory && typeof parsed.inventory === "object") characterState.inventory = parsed.inventory;
    if (parsed.extras_search !== undefined) characterState.extras_search = parsed.extras_search;
    if (parsed.inventory_search !== undefined) characterState.inventory_search = parsed.inventory_search;
    if (parsed.extras_catalog_search !== undefined) characterState.extras_catalog_search = parsed.extras_catalog_search;
    if (parsed.extras_catalog_scope !== undefined) characterState.extras_catalog_scope = parsed.extras_catalog_scope;
    if (parsed.inventory_catalog_search !== undefined) characterState.inventory_catalog_search = parsed.inventory_catalog_search;
    if (parsed.inventory_catalog_category !== undefined) characterState.inventory_catalog_category = parsed.inventory_catalog_category;
    if (parsed.inventory_catalog_type !== undefined) characterState.inventory_catalog_type = parsed.inventory_catalog_type;
    if (parsed.inventory_catalog_kind !== undefined) characterState.inventory_catalog_kind = parsed.inventory_catalog_kind;
    if (parsed.pokemon_team_search !== undefined) characterState.pokemon_team_search = parsed.pokemon_team_search;
    if (parsed.pokemon_team_limit !== undefined) characterState.pokemon_team_limit = parsed.pokemon_team_limit;
    _applyPokemonTeamAutoLevelPreference(parsed);
    if (parsed.pokemon_team_autofill !== undefined) characterState.pokemon_team_autofill = parsed.pokemon_team_autofill;
    if (parsed.override_prereqs !== undefined) characterState.override_prereqs = parsed.override_prereqs;
    if (parsed.feature_slots_override) {
      characterState.feature_slots_override = { ...parsed.feature_slots_override };
    }
    _pushCharacterHistory(raw);
  } catch {
    // ignore
  }
}

function loadSnapshotsFromStorage() {
  try {
    const raw = localStorage.getItem("autoptu_character_snapshots");
    snapshotStore = raw ? JSON.parse(raw) : [];
  } catch {
    snapshotStore = [];
  }
}

function saveSnapshotsToStorage() {
  try {
    localStorage.setItem("autoptu_character_snapshots", JSON.stringify(snapshotStore));
  } catch {
    // ignore
  }
}

function takeSnapshot() {
  const raw = localStorage.getItem("autoptu_character");
  if (!raw) return;
  const stamp = new Date().toISOString().replace("T", " ").replace("Z", " UTC");
  snapshotStore.unshift({ id: `snap-${Date.now()}`, label: stamp, payload: raw });
  snapshotStore = snapshotStore.slice(0, 50);
  saveSnapshotsToStorage();
  renderSnapshotPanel();
}

function renderSnapshotPanel() {
  if (!charSnapshotsPanel) return;
  charSnapshotsPanel.innerHTML = "";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Snapshots";
  charSnapshotsPanel.appendChild(title);
  if (!snapshotStore.length) {
    const empty = document.createElement("div");
    empty.className = "char-feature-meta";
    empty.textContent = "No snapshots yet.";
    charSnapshotsPanel.appendChild(empty);
    return;
  }
  snapshotStore.forEach((snap) => {
    const row = document.createElement("div");
    row.className = "char-snapshot-row";
    const label = document.createElement("div");
    label.textContent = snap.label;
    const actions = document.createElement("div");
    actions.className = "char-snapshot-actions";
    const loadBtn = document.createElement("button");
    loadBtn.type = "button";
    loadBtn.textContent = "Load";
    loadBtn.addEventListener("click", () => _applyCharacterSnapshot(snap.payload));
    const delBtn = document.createElement("button");
    delBtn.type = "button";
    delBtn.textContent = "Delete";
    delBtn.addEventListener("click", () => {
      snapshotStore = snapshotStore.filter((item) => item.id !== snap.id);
      saveSnapshotsToStorage();
      renderSnapshotPanel();
    });
    actions.appendChild(loadBtn);
    actions.appendChild(delBtn);
    row.appendChild(label);
    row.appendChild(actions);
    charSnapshotsPanel.appendChild(row);
  });
}

function extractTrainerProfile(payload) {
  if (!payload || typeof payload !== "object") return null;
  const profile = payload.profile || {};
  return {
    name: String(profile.name || "Trainer"),
    level: Number(profile.level || 1),
    region: String(profile.region || ""),
    concept: String(profile.concept || ""),
    class_id: String(payload.class_id || ""),
    class_name: String(payload.class_name || payload.class_id || "").replace(/^class:/i, ""),
    features: Array.isArray(payload.features) ? payload.features : [],
    edges: Array.isArray(payload.edges) ? payload.edges : [],
    skills: payload.skills && typeof payload.skills === "object" ? payload.skills : {},
    stats: payload.stats && typeof payload.stats === "object" ? payload.stats : {},
  };
}

function setTrainerProfile(payload) {
  trainerProfileRaw = payload;
  trainerProfile = extractTrainerProfile(payload);
  if (useTrainerInput) {
    useTrainerInput.checked = !!trainerProfile;
  }
  renderTrainerDetails();
}

function _tryStageRosterFromTrainerPayload(payload, source = "builder-import") {
  const includeFoe = exportRosterMirrorInput?.checked !== false;
  const roster = _buildRosterCsvFromTrainerPayload(payload, includeFoe);
  if (!roster?.csvText) return false;
  _setBattleRosterCsv(roster.csvText, source);
  return true;
}

function loadTrainerFromStorage() {
  try {
    const raw = localStorage.getItem("autoptu_character");
    if (!raw) return;
    const parsed = JSON.parse(raw);
    setTrainerProfile(parsed);
  } catch {
    // ignore
  }
}

function renderTrainerDetails() {
  if (!trainerDetailsEl) return;
  if (!trainerProfile) {
    trainerDetailsEl.textContent = "No trainer loaded.";
    return;
  }
  const classLabel = trainerProfile.class_name || trainerProfile.class_id || "Unassigned";
  const featureCount = trainerProfile.features?.length || 0;
  const edgeCount = trainerProfile.edges?.length || 0;
  const stats = trainerProfile.stats || {};
  const statsLine =
    Object.keys(stats).length > 0
      ? `HP ${stats.hp ?? "-"} | Atk ${stats.atk ?? "-"} | Def ${stats.def ?? "-"} | SpA ${stats.spatk ?? "-"} | SpD ${
          stats.spdef ?? "-"
        } | Spd ${stats.spd ?? "-"}`
      : "-";
  trainerDetailsEl.innerHTML = `
    <div class="details-header">
      <div class="details-title">${escapeHtml(trainerProfile.name)}</div>
    </div>
    <div class="details-row">Level: ${escapeHtml(trainerProfile.level)}</div>
    <div class="details-row">Class: ${escapeHtml(classLabel)}</div>
    <div class="details-row">Region: ${escapeHtml(trainerProfile.region || "-")}</div>
    <div class="details-row">Concept: ${escapeHtml(trainerProfile.concept || "-")}</div>
    <div class="details-row">Stats: ${escapeHtml(statsLine)}</div>
    <div class="details-row">Features: ${escapeHtml(featureCount)}</div>
    <div class="details-row">Edges: ${escapeHtml(edgeCount)}</div>
  `;
}

function effectMultiplierText(multiplier) {
  const numeric = Number(multiplier);
  if (!Number.isFinite(numeric)) return "";
  if (numeric <= 0) return "no effect";
  if (numeric >= 2) return "super effective";
  if (numeric > 1) return "effective";
  if (numeric < 1) return "not very effective";
  return "";
}

function stageDeltaLabel(value) {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric) || numeric === 0) return "0";
  return numeric > 0 ? `+${numeric}` : String(numeric);
}

function formatEventPrefix(event) {
  if (!event || typeof event !== "object") return "";
  const parts = [];
  if (Number.isFinite(Number(event.round))) {
    parts.push(`R${Number(event.round)}`);
  }
  if (event.phase) {
    const phase = String(event.phase).replace(/_/g, " ");
    parts.push(phase.toUpperCase());
  }
  return parts.join(" ");
}

function resolveCombatantEntry(value) {
  if (!value) return null;
  return findCombatantByRef(value);
}

function formatHpAmount(current, maxHp) {
  const hp = Number(current);
  if (!Number.isFinite(hp)) return "";
  const maxValue = Number(maxHp);
  if (Number.isFinite(maxValue) && maxValue > 0) {
    const pct = Math.round((hp / maxValue) * 100);
    return `HP ${hp}/${maxValue} (${pct}%)`;
  }
  return `HP ${hp}`;
}

function hpSuffix(event, ref = null) {
  const targetHp = Number(event?.target_hp);
  if (!Number.isFinite(targetHp)) return "";
  const explicitMax =
    Number(event?.target_max_hp ?? event?.max_hp ?? event?.defender_max_hp ?? event?.recipient_max_hp);
  const combatant = resolveCombatantEntry(ref ?? event?.target ?? event?.target_id ?? event?.defender ?? event?.actor);
  const maxHp = Number.isFinite(explicitMax) ? explicitMax : Number(combatant?.max_hp);
  return formatHpAmount(targetHp, maxHp);
}

function formatMoveEventLine(event, actor, target, moveName) {
  const move = moveName || "a move";
  const targetText = target ? ` targeting ${target}` : "";
  const roll = Number(event.roll);
  const needed = Number(event.needed);
  const damageRoll = Number(event.damage_roll);
  const effectiveDb = Number(event.effective_db);
  const preTypeDamage = Number(event.pre_type_damage);
  const attackValue = Number(event.attack_value);
  const defenseValue = Number(event.defense_value);
  const stabDb = Number(event.stab_db);
  const weatherDb = Number(event.weather_db);
  const critExtraRoll = Number(event.crit_extra_roll);
  const strikeHits = Number(event.strike_hits);
  const strikeMax = Number(event.strike_max);
  const multiplier = Number(event.type_multiplier);
  const rollText =
    Number.isFinite(roll) && Number.isFinite(needed) && needed > 0 ? ` AC ${roll}/${needed}` : "";
  if (event.hit === false) {
    const missTags = [];
    if (rollText) missTags.push(rollText.trim());
    if (Number.isFinite(roll) && (!Number.isFinite(needed) || needed <= 0)) {
      missTags.push(`roll ${roll}`);
    }
    if (Number.isFinite(effectiveDb) && effectiveDb > 0) {
      missTags.push(`DB ${effectiveDb}`);
    }
    if (event.reason) {
      missTags.push(String(event.reason).replace(/_/g, " "));
    }
    const hpText = hpSuffix(event, event.target ?? event.target_id ?? event.defender);
    if (hpText) missTags.push(hpText);
    return missTags.length
      ? `${actor || "A unit"} used ${move}${targetText}, but it failed to connect. ${missTags.join(" | ")}.`
      : `${actor || "A unit"} used ${move}${targetText}, but it failed to connect.`;
  }
  const tags = [];
  const damage = Number(event.damage);
  if (Number.isFinite(damage)) {
    if (damage > 0) {
      tags.push(`damage ${damage}`);
    } else if (Number(event.type_multiplier) === 0) {
      tags.push("no damage (immune)");
    } else {
      tags.push("no damage");
    }
  }
  if (Number.isFinite(multiplier)) {
    tags.push(`x${Number(multiplier.toFixed(2))}`);
  }
  if (Number.isFinite(effectiveDb) && effectiveDb > 0) {
    tags.push(`DB ${effectiveDb}`);
  }
  if (Number.isFinite(damageRoll) && damageRoll > 0) {
    tags.push(`roll ${damageRoll}`);
  }
  if (Number.isFinite(preTypeDamage) && preTypeDamage > 0) {
    tags.push(`base ${preTypeDamage}`);
  }
  if (Number.isFinite(attackValue) && Number.isFinite(defenseValue) && (attackValue !== 0 || defenseValue !== 0)) {
    tags.push(`Atk ${attackValue} vs Def ${defenseValue}`);
  }
  if (Number.isFinite(stabDb) && stabDb !== 0) {
    tags.push(`STAB ${stabDb > 0 ? `+${stabDb}` : String(stabDb)} DB`);
  }
  if (Number.isFinite(weatherDb) && weatherDb !== 0) {
    tags.push(`Weather ${weatherDb > 0 ? `+${weatherDb}` : String(weatherDb)} DB`);
  }
  if (Number.isFinite(critExtraRoll) && critExtraRoll > 0) {
    tags.push(`crit roll +${critExtraRoll}`);
  }
  if (Number.isFinite(strikeHits) && strikeHits > 1) {
    if (Number.isFinite(strikeMax) && strikeMax >= strikeHits) {
      tags.push(`hits ${strikeHits}/${strikeMax}`);
    } else {
      tags.push(`hits ${strikeHits}`);
    }
  }
  if (event.crit === true) {
    tags.push("critical hit");
  }
  const effectiveness = effectMultiplierText(multiplier);
  if (effectiveness) {
    tags.push(effectiveness);
  }
  if (rollText) {
    tags.push(rollText.trim());
  }
  const hpText = hpSuffix(event, event.target ?? event.target_id ?? event.defender);
  if (hpText) {
    tags.push(hpText);
  }
  if (tags.length) {
    return `${actor || "A unit"} used ${move}${targetText}. ${tags.join(" | ")}.`;
  }
  return `${actor || "A unit"} used ${move}${targetText}.`;
}

function formatAbilityEventLine(event, actor, target) {
  const ability = String(event.ability || event.move || "Ability").trim();
  if (ability && !pokeApiCacheHas(pokeApiAbilityMetaCache, ability)) {
    ensureAbilityMeta(ability).then(() => scheduleRerender());
  }
  const abilityMeta = pokeApiCacheGet(pokeApiAbilityMetaCache, ability);
  const description = String(event.description || "").trim();
  const effect = String(event.effect || "").trim().toLowerCase();
  const status = String(event.status || event.condition || "").trim();
  const amount = Number(event.amount ?? event.damage ?? event.value ?? event.hp_delta ?? event.heal);
  const roll = Number(event.roll);
  const needed = Number(event.needed ?? event.dc ?? event.threshold ?? event.chance);
  const chance = Number(event.chance);
  const rollText = Number.isFinite(roll)
    ? Number.isFinite(needed)
      ? ` (roll ${roll}/${needed})`
      : ` (roll ${roll})`
    : "";
  const chanceText = Number.isFinite(chance) && chance > 0 ? ` (${chance}% chance)` : "";
  const owner = actor ? `${actor}'s ${ability}` : ability;
  const failed = event.triggered === false || event.success === false || effect === "failed";
  const context = [];
  if (target) context.push(`target ${target}`);
  if (event.move && String(event.move).trim().toLowerCase() !== ability.toLowerCase()) {
    context.push(`after ${event.move}`);
  }
  if (event.item) {
    context.push(`item ${event.item}`);
  }
  if (event.weather) {
    context.push(`weather ${event.weather}`);
  }
  if (event.terrain) {
    context.push(`terrain ${event.terrain}`);
  }
  if (event.stat && Number.isFinite(Number(event.amount))) {
    context.push(`${String(event.stat).toUpperCase()} ${stageDeltaLabel(event.amount)}`);
  }
  const hpText = hpSuffix(event, event.target ?? event.target_id ?? event.defender ?? event.actor ?? event.actor_id);
  if (hpText) {
    context.push(hpText);
  }
  if (failed) {
    return `${owner} did not trigger${rollText || chanceText}.`;
  }
  if (description) {
    const suffix = context.length ? ` (${context.join(" | ")})` : "";
    if (description.toLowerCase().includes(ability.toLowerCase())) {
      return `${description}${suffix}${rollText}`;
    }
    return `${owner}: ${description}${suffix}${rollText}`;
  }
  if (effect === "status" && target && status) {
    return `${owner} afflicted ${target} with ${status}.${rollText || chanceText}`;
  }
  if ((effect === "heal" || effect === "healing") && Number.isFinite(amount)) {
    return target
      ? `${owner} restored ${amount} HP to ${target}.${rollText || chanceText}`
      : `${owner} restored ${amount} HP.${rollText || chanceText}`;
  }
  if (effect === "damage" && Number.isFinite(amount)) {
    return target
      ? `${owner} dealt ${amount} damage to ${target}.${rollText || chanceText}`
      : `${owner} dealt ${amount} damage.${rollText || chanceText}`;
  }
  if (event.stat && Number.isFinite(Number(event.amount))) {
    const stat = String(event.stat).toUpperCase();
    const delta = stageDeltaLabel(event.amount);
    return target
      ? `${owner} changed ${target}'s ${stat} by ${delta}.${rollText || chanceText}`
      : `${owner} changed ${stat} by ${delta}.${rollText || chanceText}`;
  }
  if (effect === "immunity" || effect === "blocked") {
    return target
      ? `${owner} blocked the effect on ${target}.${rollText || chanceText}`
      : `${owner} blocked an effect.${rollText || chanceText}`;
  }
  if (Number.isFinite(amount) && amount !== 0) {
    return target
      ? `${owner} changed ${target}'s HP by ${amount}.${rollText || chanceText}`
      : `${owner} changed HP by ${amount}.${rollText || chanceText}`;
  }
  const contextText = context.length ? ` (${context.join(" | ")})` : "";
  if (target) {
    return `${owner} triggered on ${target}${contextText}.${rollText || chanceText}`;
  }
  if (!context.length && abilityMeta?.effect) {
    return `${owner} triggered. ${abilityMeta.effect}${rollText || chanceText}`;
  }
  return `${owner} triggered${contextText}.${rollText || chanceText}`;
}

function renderEventLine(event) {
  let category = "other";
  if (!event || typeof event !== "object") {
    if (typeof event === "string") {
      const trimmed = event.trim();
      if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
        try {
          return renderEventLine(JSON.parse(trimmed));
        } catch {
          // Keep raw string fallback when not valid JSON.
        }
      }
    }
    return { text: String(event), category, prefix: "" };
  }
  const prefix = formatEventPrefix(event);
  const eventType = String(event.type || "").trim().toLowerCase();
  if (eventType === "round_start") {
    const weather = event.weather ? ` Weather: ${event.weather}.` : "";
    const lead = Array.isArray(event.initiative) && event.initiative.length
      ? ` Initiative lead: ${resolveName(event.initiative[0]?.actor) || event.initiative[0]?.actor} (${event.initiative[0]?.total ?? "?"}).`
      : "";
    return { text: `Round ${event.round} begins.${weather}${lead}`, category: "phase", prefix };
  }
  const actor = resolveName(event.actor ?? event.actor_id ?? event.source);
  const target = resolveName(event.target ?? event.target_id ?? event.defender);
  const move = event.move ?? event.move_name;
  const amount = event.amount ?? event.damage ?? event.value ?? event.hp_delta;
  const status = event.status ?? event.condition;
  switch (eventType) {
    case "shift":
    case "move_tile":
      category = "actions";
      if (event.from || event.to) {
        const fromText = formatCoord(event.from);
        const toText = formatCoord(event.to ?? event.destination ?? event.end);
        return { text: `${actor || "A unit"} repositioned from ${fromText} to ${toText}.`, category, prefix };
      }
      return { text: actor ? `${actor} repositioned.` : "A unit repositioned.", category, prefix };
    case "jump":
      category = "actions";
      const jumpKind = String(event.jump_kind || "").trim().toLowerCase();
      if (event.from || event.to) {
        const fromText = formatCoord(event.from);
        const toText = formatCoord(event.to ?? event.destination ?? event.end);
        return { text: `${actor || "A unit"} ${jumpKind === "high" ? "high jumped" : "long jumped"} from ${fromText} to ${toText}.`, category, prefix };
      }
      return { text: actor ? `${actor} ${jumpKind === "high" ? "high jumped" : "long jumped"}.` : "A unit jumped.", category, prefix };
    case "action":
      category = "actions";
      if (actor && event.detail) {
        return { text: `${actor} declared: ${event.detail}.`, category, prefix };
      }
      return { text: event.detail || "Action declared.", category, prefix };
    case "pass":
      category = "actions";
      return { text: actor ? `${actor} passed.` : "Turn passed.", category, prefix };
    case "switch":
      category = "actions";
      return {
        text: actor
          ? `${actor} entered the field${event.replacing ? ` for ${resolveName(event.replacing) || event.replacing}` : ""}.`
          : "A switch occurred.",
        category,
        prefix,
      };
    case "move":
    case "use_move":
      category = "actions";
      return { text: formatMoveEventLine(event, actor, target, move), category, prefix };
    case "damage":
      category = "damage";
      if (event.description) {
        const hpText = hpSuffix(event, event.target ?? event.target_id ?? event.defender);
        return { text: `${event.description}${hpText ? ` (${hpText})` : ""}`, category, prefix };
      }
      if (actor && target && move && typeof amount === "number") {
        return {
          text: `${move} from ${actor} hit ${target} for ${amount} damage.${hpSuffix(event, event.target ?? event.target_id ?? event.defender) ? ` ${hpSuffix(event, event.target ?? event.target_id ?? event.defender)}.` : ""}`.trim(),
          category,
          prefix,
        };
      }
      if (actor && target && typeof amount === "number") {
        return {
          text: `${actor} dealt ${amount} damage to ${target}.${hpSuffix(event, event.target ?? event.target_id ?? event.defender) ? ` ${hpSuffix(event, event.target ?? event.target_id ?? event.defender)}.` : ""}`.trim(),
          category,
          prefix,
        };
      }
      if (target && typeof amount === "number") {
        return {
          text: `${target} took ${amount} damage.${hpSuffix(event, event.target ?? event.target_id ?? event.defender) ? ` ${hpSuffix(event, event.target ?? event.target_id ?? event.defender)}.` : ""}`.trim(),
          category,
          prefix,
        };
      }
      if (target) {
        return {
          text: `${target} took damage.${hpSuffix(event, event.target ?? event.target_id ?? event.defender) ? ` ${hpSuffix(event, event.target ?? event.target_id ?? event.defender)}.` : ""}`.trim(),
          category,
          prefix,
        };
      }
      return { text: "Damage dealt.", category, prefix };
    case "heal":
    case "healing":
      category = "status";
      if (event.description) {
        const hpText = hpSuffix(event, event.target ?? event.target_id ?? event.defender ?? event.actor ?? event.actor_id);
        return { text: `${event.description}${hpText ? ` (${hpText})` : ""}`, category, prefix };
      }
      if (actor && target && typeof amount === "number") {
        return {
          text: `${actor} restored ${amount} HP to ${target}.${hpSuffix(event, event.target ?? event.target_id ?? event.defender) ? ` ${hpSuffix(event, event.target ?? event.target_id ?? event.defender)}.` : ""}`.trim(),
          category,
          prefix,
        };
      }
      if (target && typeof amount === "number") {
        return {
          text: `${target} healed ${amount} HP.${hpSuffix(event, event.target ?? event.target_id ?? event.defender ?? event.actor ?? event.actor_id) ? ` ${hpSuffix(event, event.target ?? event.target_id ?? event.defender ?? event.actor ?? event.actor_id)}.` : ""}`.trim(),
          category,
          prefix,
        };
      }
      if (target) {
        return {
          text: `${target} recovered HP.${hpSuffix(event, event.target ?? event.target_id ?? event.defender ?? event.actor ?? event.actor_id) ? ` ${hpSuffix(event, event.target ?? event.target_id ?? event.defender ?? event.actor ?? event.actor_id)}.` : ""}`.trim(),
          category,
          prefix,
        };
      }
      return { text: "Healing applied.", category, prefix };
    case "hazard": {
      category = "hazard";
      const hazard = String(event.hazard || "hazard").replace(/_/g, " ");
      const effect = String(event.effect || "").replace(/_/g, " ");
      const amountText = Number.isFinite(Number(amount)) ? ` ${amount}` : "";
      const hpText = hpSuffix(event);
      const effectText = effect ? ` (${effect}${amountText})` : amountText ? ` (${amountText.trim()})` : "";
      const targetName = actor || target || "a unit";
      return {
        text: `${targetName} triggered ${hazard}${effectText}.${hpText ? ` ${hpText}.` : ""}`.trim(),
        category,
        prefix,
      };
    }
    case "status":
    case "condition":
      category = "status";
      if (String(event.effect || "").toLowerCase() === "dynamax" && (target || actor)) {
        return { text: `${target || actor} Dynamaxed.`, category, prefix };
      }
      if (String(event.effect || "").toLowerCase() === "dynamax_end" && (target || actor)) {
        return { text: `${target || actor} returned to normal size.`, category, prefix };
      }
      if (event.description) {
        if (status && !String(event.description).toLowerCase().includes(String(status).toLowerCase())) {
          return { text: `${event.description} (${status})`, category, prefix };
        }
        return { text: event.description, category, prefix };
      }
      if (event.skip_turn === true && actor) {
        return { text: `${actor} is ${status || "affected"} and loses the turn.`, category, prefix };
      }
      if (actor && target && status && move) {
        return { text: `${actor}'s ${move} inflicted ${status} on ${target}.`, category, prefix };
      }
      if (actor && target && status) {
        return { text: `${actor} inflicted ${status} on ${target}.`, category, prefix };
      }
      if (actor && status) {
        return { text: `${actor} is now ${status}.`, category, prefix };
      }
      if (target && status) {
        return { text: `${target} is now ${status}.`, category, prefix };
      }
      if (status) {
        return { text: `Status applied: ${status}.`, category, prefix };
      }
      if (event.effect) {
        return { text: `Status event: ${String(event.effect).replace(/_/g, " ")}.`, category, prefix };
      }
      return { text: "Status applied.", category, prefix };
    case "combat_stage":
      category = "status";
      if (event.description) {
        return { text: event.description, category, prefix };
      }
      if (target && event.stat && Number.isFinite(Number(event.amount))) {
        return {
          text: `${target}'s ${String(event.stat).toUpperCase()} stage changed by ${stageDeltaLabel(event.amount)}.`,
          category,
          prefix,
        };
      }
      return { text: "Combat stage changed.", category, prefix };
    case "ability":
      category = "ability";
      return { text: formatAbilityEventLine(event, actor, target), category, prefix };
    case "trainer_feature":
      category = "status";
      if (String(event.feature || "").trim() === "Thought Detection" && Array.isArray(event.blocked_targets) && event.blocked_targets.length) {
        const blocked = event.blocked_targets.map((entry) => resolveName(entry) || entry).join(", ");
        const base = String(event.description || "Thought Detection senses nearby minds.").trim();
        return { text: `${base} Blocked by Mindlock: ${blocked}.`, category, prefix };
      }
      if (event.description) {
        return { text: String(event.description), category, prefix };
      }
      break;
    case "item":
      category = "item";
      if (event.description) {
        const hpText = hpSuffix(event, event.target ?? event.target_id ?? event.defender ?? event.actor ?? event.actor_id);
        return { text: `${event.description}${hpText ? ` (${hpText})` : ""}`, category, prefix };
      }
      if (String(event.effect || "").toLowerCase() === "mega_evolution") {
        const formName = String(event.mega_form || "").trim();
        if (target && formName) {
          return { text: `${target} Mega Evolved into ${formName}.`, category, prefix };
        }
        if (target) {
          return { text: `${target} Mega Evolved.`, category, prefix };
        }
      }
      if (String(event.effect || "").toLowerCase() === "primal_reversion_ready") {
        if (target || actor) {
          return { text: `${target || actor} began Primal Reversion.`, category, prefix };
        }
      }
      if (String(event.effect || "").toLowerCase() === "teracrystal") {
        if (target && event.tera_type) {
          return { text: `${target} Terastallized into ${event.tera_type}.`, category, prefix };
        }
        if (target) {
          return { text: `${target} Terastallized.`, category, prefix };
        }
      }
      if (String(event.effect || "").toLowerCase() === "z_move_activate") {
        if (actor && event.move) {
          return { text: `${actor} unleashed Z-Power through ${event.move}.`, category, prefix };
        }
        if (actor) {
          return { text: `${actor} unleashed Z-Power.`, category, prefix };
        }
      }
      if (String(event.effect || "").toLowerCase() === "form_change" && target && event.form) {
        return { text: `${target} changed form to ${event.form}.`, category, prefix };
      }
      if (actor && event.item && target && actor !== target) {
        return { text: `${actor} used ${event.item} on ${target}.`, category, prefix };
      }
      if (actor && event.item) {
        return { text: `${actor} used ${event.item}.`, category, prefix };
      }
      return { text: "Item effect resolved.", category, prefix };
    case "blocked":
    case "protect":
      category = "status";
      if (target && actor && move) {
        return { text: `${target} blocked ${actor}'s ${move}.`, category, prefix };
      }
      return { text: target ? `${target} blocked the attack.` : "An attack was blocked.", category, prefix };
    case "faint":
      category = "status";
      return { text: target ? `${target} fainted and is out of the battle.` : "A unit fainted.", category, prefix };
    case "phase":
      category = "phase";
      return { text: event.phase ? `${String(event.phase)} phase.` : "Phase changed.", category, prefix };
    case "turn_start":
      category = "phase";
      if (actor && Number.isFinite(Number(event.initiative?.total))) {
        return { text: `${actor}'s turn begins at initiative ${Number(event.initiative.total)}.`, category, prefix };
      }
      return { text: actor ? `${actor}'s turn begins.` : "Turn started.", category, prefix };
    case "turn_end":
      category = "phase";
      return { text: actor ? `${actor}'s turn ends.` : "Turn ended.", category, prefix };
    default:
      break;
  }
  if (event.description) {
    if (eventType === "move") {
      category = "actions";
    } else if (eventType === "damage") {
      category = "damage";
    } else if (eventType === "ability" || eventType === "status") {
      category = "status";
    }
    return { text: event.description, category, prefix };
  }
  const parts = [];
  if (actor) parts.push(actor);
  if (move) parts.push(`used ${move}`);
  if (target) parts.push(`on ${target}`);
  if (typeof amount === "number") parts.push(`(${amount})`);
  if (parts.length) {
    return { text: `${parts.join(" ")}.`, category, prefix };
  }
  if (event.type) {
    return {
      text: `${String(event.type).replace(/_/g, " ")}.`,
      category,
      prefix,
    };
  }
  return { text: "Event recorded.", category, prefix };
}

function resolveName(value) {
  if (!value) return null;
  const combatant = findCombatantByRef(value);
  if (combatant) return combatant.name;
  const trainer = findTrainerByRef(value);
  if (trainer) return trainer.name || trainer.id;
  if (normalizeTeamLabel(value) === "player") return friendlySideLabel("player") || "Your Team";
  if (normalizeTeamLabel(value) === "foe") return friendlySideLabel("foe") || "Opposing Team";
  if (typeof value === "string") return value;
  return String(value);
}

function cleanLogLine(line, previous) {
  if (!line) return null;
  const trimmed = prettifyCombatReference(String(line).trim());
  if (!trimmed) return null;
  const lower = trimmed.toLowerCase();
  const playerLabel = (friendlySideLabel("player") || "Your Team").toLowerCase();
  const foeLabel = (friendlySideLabel("foe") || "Opposing Team").toLowerCase();
  if (lower === `${playerLabel}.`) return null;
  if (lower === `${foeLabel}.`) return null;
  if (lower === `${playerLabel} is up.`) return `${friendlySideLabel("player") || "Your Team"} is up.`;
  if (lower === `${foeLabel} is up.`) return `${friendlySideLabel("foe") || "Opposing Team"} is up.`;
  if (lower === "phase: command.") return "Command phase.";
  if (lower === "phase: action." || lower === "phase: end.") return null;
  const genericMove = trimmed.match(/^(.+?) used (.+?)\.$/i);
  const previousDetailed = previous ? previous.match(/^(.+?) used (.+?) on .+\.$/i) : null;
  if (
    genericMove &&
    previousDetailed &&
    genericMove[1] === previousDetailed[1] &&
    genericMove[2] === previousDetailed[2]
  ) {
    return null;
  }
  if (previous && trimmed === previous) return null;
  return trimmed;
}

function passesLogFilter(category) {
  const filters = {
    actions: logFilterActions?.checked ?? true,
    damage: logFilterDamage?.checked ?? true,
    status: logFilterStatus?.checked ?? true,
    phase: logFilterPhase?.checked ?? true,
  };
  if (category === "actions") return filters.actions;
  if (category === "damage") return filters.damage;
  if (category === "hazard") return filters.damage;
  if (category === "item") return filters.status;
  if (category === "ability") return filters.status;
  if (category === "status") return filters.status;
  if (category === "phase") return filters.phase;
  return true;
}

function formatCombatStages(stages) {
  if (!stages) return "-";
  return `Atk ${stages.atk ?? 0}, Def ${stages.def ?? 0}, SpA ${stages.spatk ?? 0}, SpD ${stages.spdef ?? 0}, Spd ${stages.spd ?? 0}, Acc ${stages.accuracy ?? 0}`;
}

function formatStats(stats) {
  if (!stats) return "-";
  return `HP ${stats.hp}, Atk ${stats.atk}, Def ${stats.def}, SpA ${stats.spatk}, SpD ${stats.spdef}, Spd ${stats.spd}`;
}

function formatPassiveItemEffects(effects) {
  if (!Array.isArray(effects) || !effects.length) return "-";
  return `<div class="chip-group">${effects.map((effect) => chipHtml({
    text: effect,
    iconBadge: "I",
    tooltipTitle: "Passive Item Effect",
    tooltipBody: effect,
    className: "chip-equipped",
  })).join("")}</div>`;
}

function onGridClick(x, y, occupantId, options = {}) {
  if (Date.now() < suppressGridClickUntil) return;
  if (!state || state.status !== "ok") return;
  if ((state.pending_prompts || []).length) {
    notifyUI("warn", "Resolve pending prompts before acting.");
    return;
  }
  const clickedKey = `${x},${y}`;
  if (!state.current_actor_is_player) {
    selectedTileKey = clickedKey;
    if (occupantId) {
      selectedId = occupantId;
    }
    render();
    return;
  }
  if (armedMove && selectedId) {
    const allowed = (state.move_targets && state.move_targets[armedMove]) || [];
    if (occupantId && !allowed.includes(occupantId)) {
      alertError(new Error("Invalid target."));
      return;
    }
    if (!occupantId && !allowed.includes(null)) {
      alertError(new Error("Move requires a target in range."));
      return;
    }
    if (occupantId) {
      commitAction({
        type: "move",
        actor_id: selectedId,
        move: armedMove,
        target_id: occupantId,
        mega_evolve: !!gimmickState.mega_evolve,
        dynamax: !!gimmickState.dynamax,
        z_move: !!gimmickState.z_move,
        teracrystal: !!gimmickState.teracrystal,
        tera_type: gimmickState.tera_type || null,
      }).catch(alertError);
      return;
    }
    commitAction({
      type: "move",
      actor_id: selectedId,
      move: armedMove,
      target_id: null,
      mega_evolve: !!gimmickState.mega_evolve,
      dynamax: !!gimmickState.dynamax,
      z_move: !!gimmickState.z_move,
      teracrystal: !!gimmickState.teracrystal,
      tera_type: gimmickState.tera_type || null,
    }).catch(alertError);
    return;
  }
  if ((armedTileAction === "jump_long" || armedTileAction === "jump_high") && selectedId) {
    if (occupantId) {
      alertError(new Error("Jump destination must be an empty tile."));
      return;
    }
    const legalJump = new Set(((armedTileAction === "jump_high" ? state.legal_high_jumps : (state.legal_long_jumps || state.legal_jumps)) || []).map((c) => `${c[0]},${c[1]}`));
    if (!legalJump.has(`${x},${y}`)) {
      alertError(new Error("Invalid jump destination."));
      return;
    }
    commitAction({
      type: "jump",
      actor_id: selectedId,
      jump_kind: armedTileAction === "jump_high" ? "high" : "long",
      x,
      y,
    }).catch(alertError);
    selectedTileKey = clickedKey;
    clearArmedTileAction();
    render();
    return;
  }
  if (armedTileAction === "frozen_domain" && selectedId) {
    const legalTiles = new Set((state.legal_frozen_domain_tiles || []).map((c) => `${c[0]},${c[1]}`));
    if (!legalTiles.has(`${x},${y}`)) {
      alertError(new Error("Invalid Frozen Domain tile."));
      return;
    }
    const key = `${x},${y}`;
    const draftSet = frozenDomainDraftKeySet();
    if (draftSet.has(key)) {
      if (options.trapperAddOnly) {
        return;
      }
      frozenDomainDraftTiles = frozenDomainDraftTiles.filter((coord) => `${coord[0]},${coord[1]}` !== key);
      selectedTileKey = clickedKey;
      render();
      return;
    }
    if (frozenDomainDraftTiles.length >= 6) {
      alertError(new Error("Frozen Domain already has 6 selected tiles. Click Deploy or unselect one tile."));
      return;
    }
    if (!frozenDomainDraftCanAdd([x, y])) {
      alertError(new Error("New Frozen Domain tiles must connect orthogonally to the current draft."));
      return;
    }
    frozenDomainDraftTiles = [...frozenDomainDraftTiles, [x, y]];
    selectedTileKey = clickedKey;
    render();
    return;
  }
  if (armedTileAction === "trapper" && selectedId) {
    const legalTiles = new Set((state.legal_trapper_tiles || []).map((c) => `${c[0]},${c[1]}`));
    if (!legalTiles.has(`${x},${y}`)) {
      alertError(new Error("Invalid trap tile."));
      return;
    }
    const key = `${x},${y}`;
    const draftSet = trapperDraftKeySet();
    if (draftSet.has(key)) {
      if (options.trapperAddOnly) {
        return;
      }
      trapperDraftTiles = trapperDraftTiles.filter((coord) => `${coord[0]},${coord[1]}` !== key);
      selectedTileKey = clickedKey;
      render();
      return;
    }
    if (trapperDraftTiles.length >= 8) {
      alertError(new Error("Trapper already has 8 selected tiles. Click Deploy or unselect one tile."));
      return;
    }
    if (!trapperDraftCanAdd([x, y])) {
      alertError(new Error("New trap tiles must connect orthogonally to the current trap draft."));
      return;
    }
    trapperDraftTiles = [...trapperDraftTiles, [x, y]];
    selectedTileKey = clickedKey;
    render();
    return;
  }
  if (armedTileAction === "psionic_overload_barrier" && selectedId) {
    const combatant = (state.combatants || []).find((entry) => entry.id === selectedId) || {};
    const hints = combatant.trainer_action_hints || {};
    const legalTiles = new Set((hints.psionic_overload_barrier_tiles || []).map((entry) => `${entry.tile[0]},${entry.tile[1]}`));
    if (!legalTiles.has(`${x},${y}`)) {
      alertError(new Error("Invalid Psionic Overload barrier tile."));
      return;
    }
    const key = `${x},${y}`;
    const current = psionicOverloadBarrierKeySet();
    if (current.has(key)) {
      psionicOverloadBarrierTiles = psionicOverloadBarrierTiles.filter((coord) => `${coord[0]},${coord[1]}` !== key);
    } else if (psionicOverloadBarrierTiles.length < 2) {
      psionicOverloadBarrierTiles = [...psionicOverloadBarrierTiles, [x, y]];
    } else {
      alertError(new Error("Psionic Overload Barrier needs exactly 2 extra segments."));
      return;
    }
    selectedTileKey = clickedKey;
    render();
    return;
  }
  if (occupantId) {
    selectedId = occupantId;
    selectedTileKey = clickedKey;
    render();
    return;
  }
  if (selectedId) {
    const legalShift = new Set((state.legal_shifts || []).map((c) => `${c[0]},${c[1]}`));
    if (!legalShift.has(`${x},${y}`)) {
      alertError(new Error("Invalid destination."));
      return;
    }
    commitAction({
      type: "shift",
      actor_id: selectedId,
      x,
      y,
    }).catch(alertError);
    selectedTileKey = clickedKey;
    clearArmedTileAction();
    render();
    return;
  }
  selectedTileKey = clickedKey;
  render();
}

function alertError(err) {
  console.error(err);
  const message = err?.message || String(err);
  showRuntimeError(message);
  notifyUI("error", message, 4500);
}

startButton?.addEventListener("click", () => {
  const hasBattle = !!state && state.status === "ok";
  const action = hasBattle ? stopBattle : startBattle;
  action().catch(alertError);
});
endTurnButton?.addEventListener("click", () => endTurn().catch(alertError));
promptResolveButton?.addEventListener("click", () => resolvePrompts().catch(alertError));
downloadSpritesButton?.addEventListener("click", () => downloadSprites().catch(alertError));
aiStepButton?.addEventListener("click", () => aiStep().catch(alertError));
aiAutoButton?.addEventListener("click", () => toggleAuto());
aiModelRefreshButton?.addEventListener("click", () => refreshAiModels().catch(alertError));
aiModelSelect?.addEventListener("change", () => {
  const value = String(aiModelSelect.value || "");
  if (!value) return;
  selectAiModel(value).catch(alertError);
});
undoButton?.addEventListener("click", () => undoStep().catch(alertError));
hideFaintedToggle?.addEventListener("change", () => render());
logFilterActions?.addEventListener("change", () => render());
logFilterDamage?.addEventListener("change", () => render());
logFilterStatus?.addEventListener("change", () => render());
logFilterPhase?.addEventListener("change", () => render());
logAutoScrollToggle?.addEventListener("change", () => render());
moveListEl?.addEventListener("mouseleave", () => {
  if (tooltipAnchor && moveListEl.contains(tooltipAnchor)) {
    scheduleTooltipHide();
  }
});
charContentEl?.addEventListener("click", (event) => {
  const btn = event.target.closest(".char-word-link");
  if (!btn) return;
  event.preventDefault();
  event.stopPropagation();
  routeCharacterWordClick(btn.getAttribute("data-word") || "", btn.getAttribute("data-step") || "");
});
stepByStepStartToggle?.addEventListener("change", () => saveSettings());
useTrainerInput?.addEventListener("change", () => saveSettings());
async function _importBattleProjectZip(file) {
  const entries = _readZipEntries(await file.arrayBuffer());
  const builderJsonName = Object.keys(entries).find((name) => /team_builder\.json$/i.test(name) || /builder\.json$/i.test(name));
  const trainerCsvName = Object.keys(entries).find((name) => /trainer\.csv$/i.test(name));
  const teamCsvName = Object.keys(entries).find((name) => /team_roster\.csv$/i.test(name) || /team\.csv$/i.test(name));
  let parsed = null;
  if (builderJsonName && entries[builderJsonName]) {
    parsed = JSON.parse(entries[builderJsonName]);
  } else if (trainerCsvName && entries[trainerCsvName]) {
    parsed = _applyTrainerCsvToPayload(entries[trainerCsvName], trainerProfileRaw || _readStoredTrainerPayload());
  }
  if (parsed) {
    localStorage.setItem("autoptu_character", JSON.stringify(parsed));
    setTrainerProfile(parsed);
  }
  if (teamCsvName && entries[teamCsvName]) {
    const chosen = await _chooseRosterImportSide(entries[teamCsvName], file.name || "project-zip");
    if (chosen) {
      const nextCsv = chosen.mode === "assign" && battleRosterCsvText
        ? _mergeRosterCsvBySide(battleRosterCsvText, chosen.csvText)
        : chosen.csvText;
      _setBattleRosterCsv(nextCsv, file.name || "project-zip");
    }
  }
  if (!parsed && !(teamCsvName && entries[teamCsvName])) {
    throw new Error("Project ZIP did not contain a supported builder JSON, trainer CSV, or team CSV.");
  }
}

loadTrainerButton?.addEventListener("click", () => {
  loadTrainerFromStorage();
  if (_tryStageRosterFromTrainerPayload(trainerProfileRaw || _readStoredTrainerPayload(), "builder-local")) {
    notifyUI("info", "Local builder team staged as roster CSV.", 2200);
  }
  saveSettings();
});
usefulChartsButton?.addEventListener("click", () => openUsefulChartsModal().catch(alertError));
importTrainerButton?.addEventListener("click", () => {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "application/json,.json,.csv,text/csv,.zip,application/zip";
  input.addEventListener("change", async () => {
    const file = input.files && input.files[0];
    if (!file) return;
    try {
      const lowerName = String(file.name || "").toLowerCase();
      if (lowerName.endsWith(".zip")) {
        await _importBattleProjectZip(file);
        notifyUI("ok", "Project ZIP imported.", 2400);
      } else {
        const text = await _readTextFile(file);
        const isCsv = lowerName.endsWith(".csv");
        const parsed = isCsv
          ? _applyTrainerCsvToPayload(text, trainerProfileRaw || _readStoredTrainerPayload())
          : JSON.parse(text);
        localStorage.setItem("autoptu_character", JSON.stringify(parsed));
        setTrainerProfile(parsed);
        if (_tryStageRosterFromTrainerPayload(parsed, file.name || "builder-import")) {
          notifyUI("ok", "Builder team imported and staged as roster CSV.", 2400);
        } else {
          notifyUI("info", isCsv ? "Trainer CSV imported." : "Trainer JSON imported (no Pokemon builds found for roster staging).", 2800);
        }
      }
      saveSettings();
    } catch (err) {
      alertError(err);
    }
  });
  input.click();
});
importRosterCsvButton?.addEventListener("click", () => {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".csv,text/csv,.zip,application/zip";
  input.addEventListener("change", async () => {
    const file = input.files && input.files[0];
    if (!file) return;
    try {
      const lowerName = String(file.name || "").toLowerCase();
      if (lowerName.endsWith(".zip")) {
        const entries = _readZipEntries(await file.arrayBuffer());
        const teamCsvName = Object.keys(entries).find((name) => /team_roster\.csv$/i.test(name) || /team\.csv$/i.test(name));
        if (!teamCsvName || !entries[teamCsvName]) throw new Error("Project ZIP did not contain a team CSV.");
        const chosen = await _chooseRosterImportSide(entries[teamCsvName], file.name || "imported");
        if (!chosen) return;
        const nextCsv = chosen.mode === "assign" && battleRosterCsvText
          ? _mergeRosterCsvBySide(battleRosterCsvText, chosen.csvText)
          : chosen.csvText;
        _setBattleRosterCsv(nextCsv, file.name || "imported");
        notifyUI("ok", chosen.mode === "assign" ? `Project ZIP team loaded as ${chosen.side}.` : "Project ZIP team CSV loaded.", 2200);
      } else {
        const text = await _readTextFile(file);
        const chosen = await _chooseRosterImportSide(text, file.name || "imported");
        if (!chosen) return;
        const nextCsv = chosen.mode === "assign" && battleRosterCsvText
          ? _mergeRosterCsvBySide(battleRosterCsvText, chosen.csvText)
          : chosen.csvText;
        _setBattleRosterCsv(nextCsv, file.name || "imported");
        notifyUI("ok", chosen.mode === "assign" ? `Roster CSV loaded as ${chosen.side}.` : "Roster CSV loaded.", 2200);
      }
      saveSettings();
    } catch (err) {
      alertError(err);
    }
  });
  input.click();
});
exportRosterCsvButton?.addEventListener("click", () => {
  const includeFoe = exportRosterMirrorInput?.checked !== false;
  const battleRows = _rosterRowsFromCombatants(state?.combatants || [], includeFoe);
  if (battleRows.length) {
    _downloadCsvFile("autoptu_roster_from_battle.csv", stringifyCsv(battleRows));
    notifyUI("ok", includeFoe ? "Exported full roster CSV from current battle." : "Exported player-only roster CSV from battle.", 2200);
    return;
  }
  const sourceTrainer = trainerProfileRaw || _readStoredTrainerPayload();
  const trainerRows = _rosterRowsFromTrainerBuilds(sourceTrainer, includeFoe);
  if (trainerRows.length) {
    _downloadCsvFile("autoptu_roster_from_builder.csv", stringifyCsv(trainerRows));
    notifyUI("info", includeFoe ? "Exported mirrored builder roster CSV for AI vs AI." : "Exported player-only builder roster CSV.", 2400);
    return;
  }
  alertError(new Error("No battle teams or trainer Pokemon builds found to export."));
});
clearRosterCsvButton?.addEventListener("click", () => clearBattleAndRoster().catch(alertError));
clearTrainerButton?.addEventListener("click", () => {
  trainerProfile = null;
  trainerProfileRaw = null;
  if (useTrainerInput) useTrainerInput.checked = false;
  renderTrainerDetails();
  saveSettings();
});
syncStatusTabs();
infoTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.getAttribute("data-tab");
    infoTabs.forEach((btn) => btn.classList.toggle("active", btn === tab));
    infoTabPanels.forEach((panel) => {
      panel.classList.toggle("active", panel.getAttribute("data-tab-panel") === target);
    });
    if (target === "classes") {
      loadCharacterData().catch(() => {});
    }
  });
});
charStepButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    const step = btn.getAttribute("data-step");
    if (!step) return;
    characterStep = step;
    charStepButtons.forEach((other) => other.classList.toggle("active", other === btn));
    renderCharacterStep();
  });
});
charSaveLocalBtn?.addEventListener("click", () => {
  saveCharacterToStorage();
  renderMiniSummary();
});
charLoadLocalBtn?.addEventListener("click", () => {
  loadCharacterFromStorage();
  renderCharacterStep();
});
charUndoBtn?.addEventListener("click", () => undoCharacterStep());
charRedoBtn?.addEventListener("click", () => redoCharacterStep());
charSnapshotBtn?.addEventListener("click", () => takeSnapshot());
charSnapshotsOpenBtn?.addEventListener("click", () => {
  if (!charSnapshotsPanel) return;
  charSnapshotsPanel.classList.toggle("hidden");
  renderSnapshotPanel();
});
charGuidedToggleBtn?.addEventListener("click", () => {
  characterState.guided_mode = !characterState.guided_mode;
  saveCharacterToStorage();
  renderCharacterStep();
});

speedButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    const value = Number(btn.dataset.speed || 1000);
    autoIntervalInput.value = String(value);
    if (autoTimer) {
      toggleAuto();
      toggleAuto();
    }
    saveSettings();
  });
});

zoomInButton?.addEventListener("click", () => setGridScale(gridScale + 0.1));
zoomOutButton?.addEventListener("click", () => setGridScale(gridScale - 0.1));
zoomFitButton?.addEventListener("click", () => {
  viewManuallyAdjusted = false;
  fitGridToViewport(true);
});
zoomResetButton?.addEventListener("click", () => {
  viewManuallyAdjusted = false;
  fitGridToViewport(false);
  applyGridTransform();
});
centerCurrentButton?.addEventListener("click", () => centerOnCurrentActor());
centerSelectedButton?.addEventListener("click", () => centerOnSelectedActor());

window.addEventListener("resize", () => {
  fitGridToViewport();
  applyGridTransform();
  if (resizeFitTimer) clearTimeout(resizeFitTimer);
  resizeFitTimer = setTimeout(() => {
    fitGridToViewport(true);
    applyGridTransform();
  }, 140);
  if (moveTooltip && !moveTooltip.classList.contains("hidden") && tooltipAnchor) {
    positionTooltip(tooltipAnchor);
  }
});

window.addEventListener("scroll", () => {
  if (moveTooltip && !moveTooltip.classList.contains("hidden") && tooltipAnchor) {
    positionTooltip(tooltipAnchor);
  }
});

document.addEventListener("keydown", (event) => {
  if (window.DSUI?.isTypingContext ? window.DSUI.isTypingContext(event) : event.target && ["INPUT", "SELECT", "TEXTAREA"].includes(event.target.tagName)) {
    return;
  }
  if (event.code === "Space") {
    event.preventDefault();
    if (state?.mode === "ai") {
      aiStep().catch(() => {});
    }
  } else if (event.code === "Enter") {
    event.preventDefault();
    if (state?.current_actor_is_player) {
      endTurn().catch(() => {});
    }
  } else if (event.code === "KeyR") {
    event.preventDefault();
    if (lastBattlePayload) {
      api("/api/battle/new", {
        method: "POST",
        body: JSON.stringify(lastBattlePayload),
      })
        .then((next) => {
          state = next;
          selectedId = state.current_actor_id || null;
          armedMove = null;
          viewManuallyAdjusted = false;
          lastGridSize = null;
          render();
        })
        .catch(() => {});
    } else {
      startBattle().catch(() => {});
    }
  } else if (event.code === "KeyC") {
    event.preventDefault();
    centerOnSelectedActor();
  } else if (event.code === "KeyT") {
    event.preventDefault();
    centerOnCurrentActor();
  } else if (event.code === "KeyL") {
    event.preventDefault();
    if (logAutoScrollToggle) {
      logAutoScrollToggle.checked = !logAutoScrollToggle.checked;
      saveSettings();
    }
  }
});

gridEl?.addEventListener("mousedown", (event) => {
  if (event.button === 1 || event.button === 2 || event.shiftKey) {
    event.preventDefault();
    viewManuallyAdjusted = true;
    panState = { x: event.clientX, y: event.clientY, origin: { ...gridOffset }, moved: false };
    gridEl.style.cursor = "grabbing";
  }
});

window.addEventListener("mousemove", (event) => {
  if (!panState) return;
  const dx = event.clientX - panState.x;
  const dy = event.clientY - panState.y;
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
    panState.moved = true;
  }
  gridOffset = { x: panState.origin.x + dx, y: panState.origin.y + dy };
  applyGridTransform();
});

window.addEventListener("mouseup", () => {
  if (!panState) return;
  if (panState.moved) {
    suppressGridClickUntil = Date.now() + 150;
  }
  panState = null;
  gridEl.style.cursor = "default";
});

gridEl?.addEventListener("contextmenu", (event) => {
  event.preventDefault();
});

gridWrapEl?.addEventListener(
  "wheel",
  (event) => {
    if (!state?.grid) return;
    if (!event.ctrlKey && !event.metaKey) {
      event.preventDefault();
      const panX = event.deltaX + (event.shiftKey ? event.deltaY : 0);
      const panY = event.shiftKey ? 0 : event.deltaY;
      gridOffset = {
        x: gridOffset.x - panX,
        y: gridOffset.y - panY,
      };
      viewManuallyAdjusted = true;
      applyGridTransform();
      return;
    }
    event.preventDefault();
    const rect = gridWrapEl.getBoundingClientRect();
    const cursorX = event.clientX - rect.left;
    const cursorY = event.clientY - rect.top;
    const zoomDelta = event.deltaY < 0 ? 0.12 : -0.12;
    const nextScale = Math.max(MIN_GRID_SCALE, Math.min(MAX_GRID_SCALE, gridScale + zoomDelta));
    if (Math.abs(nextScale - gridScale) < 0.0001) {
      return;
    }
    const worldX = (cursorX - gridOffset.x) / gridScale;
    const worldY = (cursorY - gridOffset.y) / gridScale;
    gridScale = nextScale;
    gridOffset = {
      x: cursorX - worldX * gridScale,
      y: cursorY - worldY * gridScale,
    };
    viewManuallyAdjusted = true;
    applyGridTransform();
  },
  { passive: false }
);

function setGridScale(next) {
  gridScale = Math.max(MIN_GRID_SCALE, Math.min(MAX_GRID_SCALE, next));
  viewManuallyAdjusted = true;
  applyGridTransform();
}

function fitGridToViewport(force = false) {
  if (!gridEl || !state?.grid) return;
  if (!force && viewManuallyAdjusted) return;
  const wrap = gridEl.parentElement;
  if (!wrap) return;
  if (wrap.clientWidth < 140 || wrap.clientHeight < 140) return;
  const width = state.grid.width * GRID_CELL_SIZE + Math.max(0, state.grid.width - 1) * GRID_GAP;
  const height = state.grid.height * GRID_CELL_SIZE + Math.max(0, state.grid.height - 1) * GRID_GAP;
  if (!width || !height) return;
  const pad = 16;
  const fitX = (wrap.clientWidth - pad) / width;
  const fitY = (wrap.clientHeight - pad) / height;
  const fitScale = Math.min(fitX, fitY);
  if (!Number.isFinite(fitScale) || fitScale <= 0) return;
  const nextScale = force ? fitScale : Math.min(1.1, fitScale);
  const adaptiveFloor = window.innerWidth >= 1200 ? 0.45 : MIN_GRID_SCALE;
  gridScale = Math.max(adaptiveFloor, Math.min(MAX_GRID_SCALE, nextScale));
  const scaledWidth = width * gridScale;
  const scaledHeight = height * gridScale;
  const centeredX = (wrap.clientWidth - scaledWidth) / 2;
  const centeredY = (wrap.clientHeight - scaledHeight) / 2;
  gridOffset = {
    x: force ? Math.max(0, centeredX) : Math.max(8, centeredX),
    y: force ? Math.max(0, centeredY) : Math.max(8, centeredY),
  };
}

function applyGridTransform() {
  if (!gridEl) return;
  gridEl.style.transform = `translate(${gridOffset.x}px, ${gridOffset.y}px) scale(${gridScale})`;
}

function saveSettings() {
  const settings = {
    mode: modeSelect.value,
    teamSize: teamSizeInput.value,
    sideCount: sideCountInput?.value || "2",
    circleInterval: circleIntervalInput?.value || "3",
    activeSlots: activeSlotsInput.value,
    minLevel: minLevelInput.value,
    maxLevel: maxLevelInput.value,
    autoInterval: autoIntervalInput.value,
    cinematicAuto: cinematicAutoToggle?.checked ?? false,
    cinematicProfile: cinematicProfileSelect?.value || "broadcast",
    cinematicSpeed: cinematicSpeedSelect?.value || "medium",
    autoCries: autoCriesToggle?.checked ?? false,
    hideFainted: hideFaintedToggle?.checked ?? false,
    logFilters: {
      actions: logFilterActions?.checked ?? true,
      damage: logFilterDamage?.checked ?? true,
      status: logFilterStatus?.checked ?? true,
      phase: logFilterPhase?.checked ?? true,
    },
    logAutoScroll: logAutoScrollToggle?.checked ?? true,
    logCompact: logCompactToggle?.checked ?? false,
    useTrainer: useTrainerInput?.checked ?? false,
    stepByStepStart: stepByStepStartToggle?.checked ?? false,
    combatantTeamFilter,
    rosterCsvText: battleRosterCsvText || "",
    exportRosterMirror: exportRosterMirrorInput?.checked ?? true,
    autoUseCreatorRoster: autoUseCreatorRosterInput?.checked ?? true,
    csvStrictMode: csvStrictModeInput?.checked ?? false,
    sideNameOverrides: _normalizedSideNameOverrides(sideNameOverrides),
    deploymentOverrides: _normalizeDeploymentPayload(),
    itemChoiceOverrides: _normalizeItemChoicePayload(),
    abilityChoiceOverrides: _normalizeAbilityChoicePayload(),
  };
  localStorage.setItem("autoptu_settings", JSON.stringify(settings));
}

function _normalizeSearchText(value) {
  const text = String(value || "")
    .toLowerCase()
    .replace(/pok(?:e|\\u00e9)mon/g, "pokemon")
    .replace(/special attack/g, "spatk")
    .replace(/special defense/g, "spdef")
    .replace(/sp\.?\s*atk/g, "spatk")
    .replace(/sp\.?\s*def/g, "spdef")
    .replace(/\battack\b/g, "atk")
    .replace(/\bdefense\b/g, "def")
    .replace(/\bspeed\b/g, "spd")
    .replace(/education/g, "ed")
    .replace(/[^a-z0-9\s]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return text;
}

function _searchMatchScore(haystack, query) {
  const normalizedQuery = _normalizeSearchText(query);
  if (!normalizedQuery) return 1;
  const normalizedHaystack = _normalizeSearchText(haystack);
  if (normalizedQuery.length <= 2) {
    return normalizedHaystack.includes(normalizedQuery) ? 1 : 0;
  }
  const tokens = normalizedQuery.split(" ").filter(Boolean);
  if (!tokens.length) return 1;
  let score = 0;
  tokens.forEach((token) => {
    if (normalizedHaystack.includes(token)) score += 1;
  });
  return score / tokens.length;
}

function loadSettings() {
  try {
    const raw = localStorage.getItem("autoptu_settings");
    if (!raw) return;
    const settings = JSON.parse(raw);
    if (settings.mode) modeSelect.value = settings.mode;
    if (settings.teamSize) teamSizeInput.value = settings.teamSize;
    if (settings.sideCount && sideCountInput) sideCountInput.value = settings.sideCount;
    if (settings.circleInterval && circleIntervalInput) circleIntervalInput.value = settings.circleInterval;
    if (settings.activeSlots) activeSlotsInput.value = settings.activeSlots;
    if (settings.minLevel) minLevelInput.value = settings.minLevel;
    if (settings.maxLevel) maxLevelInput.value = settings.maxLevel;
    if (settings.autoInterval) autoIntervalInput.value = settings.autoInterval;
    if (typeof settings.cinematicAuto === "boolean" && cinematicAutoToggle) {
      cinematicAutoToggle.checked = settings.cinematicAuto;
    }
    if (typeof settings.cinematicProfile === "string" && cinematicProfileSelect) {
      cinematicProfileSelect.value = settings.cinematicProfile;
    }
    if (typeof settings.cinematicSpeed === "string" && cinematicSpeedSelect) {
      cinematicSpeedSelect.value = settings.cinematicSpeed;
    }
    if (typeof settings.autoCries === "boolean" && autoCriesToggle) {
      autoCriesToggle.checked = settings.autoCries;
    }
    if (typeof settings.hideFainted === "boolean" && hideFaintedToggle) {
      hideFaintedToggle.checked = settings.hideFainted;
    }
    if (settings.logFilters) {
      if (logFilterActions) logFilterActions.checked = !!settings.logFilters.actions;
      if (logFilterDamage) logFilterDamage.checked = !!settings.logFilters.damage;
      if (logFilterStatus) logFilterStatus.checked = !!settings.logFilters.status;
      if (logFilterPhase) logFilterPhase.checked = !!settings.logFilters.phase;
    }
    if (typeof settings.logAutoScroll === "boolean" && logAutoScrollToggle) {
      logAutoScrollToggle.checked = settings.logAutoScroll;
    }
    if (typeof settings.logCompact === "boolean" && logCompactToggle) {
      logCompactToggle.checked = settings.logCompact;
    }
    if (typeof settings.useTrainer === "boolean" && useTrainerInput) {
      useTrainerInput.checked = settings.useTrainer;
    }
    if (typeof settings.stepByStepStart === "boolean" && stepByStepStartToggle) {
      stepByStepStartToggle.checked = settings.stepByStepStart;
    }
    if (typeof settings.combatantTeamFilter === "string") {
      setCombatantTeamFilter(settings.combatantTeamFilter);
    }
    sideNameOverrides = _normalizedSideNameOverrides(settings.sideNameOverrides);
    deploymentOverrides = settings.deploymentOverrides && typeof settings.deploymentOverrides === "object" ? settings.deploymentOverrides : {};
    itemChoiceOverrides = settings.itemChoiceOverrides && typeof settings.itemChoiceOverrides === "object" ? settings.itemChoiceOverrides : {};
    abilityChoiceOverrides = settings.abilityChoiceOverrides && typeof settings.abilityChoiceOverrides === "object" ? settings.abilityChoiceOverrides : {};
    if (settings.rosterCsvText) {
      _setBattleRosterCsv(settings.rosterCsvText, "saved");
    } else {
      _clearBattleRosterCsv();
    }
    if (typeof settings.exportRosterMirror === "boolean" && exportRosterMirrorInput) {
      exportRosterMirrorInput.checked = settings.exportRosterMirror;
    }
    if (typeof settings.autoUseCreatorRoster === "boolean" && autoUseCreatorRosterInput) {
      autoUseCreatorRosterInput.checked = settings.autoUseCreatorRoster;
    }
    if (typeof settings.csvStrictMode === "boolean" && csvStrictModeInput) {
      csvStrictModeInput.checked = settings.csvStrictMode;
    }
    document.body.classList.remove("topbar-collapsed", "left-drawer-collapsed", "right-drawer-collapsed");
    _applyCsvModeControls();
    renderSideNameEditor();
    renderDeploymentEditor();
  } catch {
    // ignore invalid settings
  }
}

function applyModeFieldVisibility() {
  const mode = String(modeSelect?.value || "");
  const circleWrap = circleIntervalInput?.closest(".field") || null;
  const sideWrap = sideCountInput?.closest(".field") || null;
  const isAiRandom = mode === "ai-random";
  const isAiRoyale = mode === "ai-royale";
  if (sideWrap) {
    const showSides = isAiRandom || isAiRoyale;
    sideWrap.style.display = showSides ? "" : "none";
    sideCountInput.disabled = !showSides;
  }
  if (circleWrap) {
    circleWrap.style.display = isAiRoyale ? "" : "none";
    circleIntervalInput.disabled = !isAiRoyale;
  }
}

[modeSelect, teamSizeInput, sideCountInput, circleIntervalInput, activeSlotsInput, minLevelInput, maxLevelInput, autoIntervalInput].forEach(
  (input) => {
    input?.addEventListener("change", () => {
      saveSettings();
      renderDeploymentEditor();
    });
  }
);
modeSelect?.addEventListener("change", () => {
  applyModeFieldVisibility();
  renderSideNameEditor();
  renderDeploymentEditor();
});
sideCountInput?.addEventListener("change", () => {
  renderSideNameEditor();
  renderDeploymentEditor();
});
exportRosterMirrorInput?.addEventListener("change", () => saveSettings());
autoUseCreatorRosterInput?.addEventListener("change", () => saveSettings());
csvStrictModeInput?.addEventListener("change", () => {
  _applyCsvModeControls();
  saveSettings();
});
cinematicAutoToggle?.addEventListener("change", () => saveSettings());
cinematicProfileSelect?.addEventListener("change", () => saveSettings());
cinematicSpeedSelect?.addEventListener("change", () => saveSettings());
cinematicExportButton?.addEventListener("click", () => exportCinematicReplayCache());
autoCriesToggle?.addEventListener("change", () => saveSettings());
hideFaintedToggle?.addEventListener("change", () => saveSettings());
logFilterActions?.addEventListener("change", () => saveSettings());
logFilterDamage?.addEventListener("change", () => saveSettings());
logFilterStatus?.addEventListener("change", () => saveSettings());
logFilterPhase?.addEventListener("change", () => saveSettings());
logAutoScrollToggle?.addEventListener("change", () => saveSettings());
logCompactToggle?.addEventListener("change", () => {
  saveSettings();
  renderLog();
});
logExportButton?.addEventListener("click", () => exportBattleLog().catch(alertError));
logClearButton?.addEventListener("click", () => {
  logClearOffset = (state?.log || []).length;
  renderLog();
});
window.addEventListener("scroll", () => {
  if (!topbarEl) return;
  topbarEl.classList.toggle("scrolled", window.scrollY > 4);
});

function startCinematicPerfMonitor() {
  let prev = performance.now();
  const tick = (ts) => {
    const frame = Math.max(1, ts - prev);
    prev = ts;
    cinematicFrameMsAvg = cinematicFrameMsAvg * 0.92 + frame * 0.08;
    if (cinematicPerfEl && (cinematicAutoToggle?.checked || pendingAnimationJobs > 0)) {
      updateCinematicPerfLabel();
    }
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

if (isBattleUI) {
  startCinematicPerfMonitor();
  setInterval(() => {
    if (document.hidden) return;
    const battleBusy =
      !!autoTimer || aiStepInFlight || pendingAnimationJobs > 0 || cinematicCameraBusy || cinematicPhaseActive;
    if (!battleBusy) {
      refreshState().catch(() => {});
    }
    const now = Date.now();
    if (now - lastSpritePollAt >= (battleBusy ? 12000 : 7000)) {
      lastSpritePollAt = now;
      refreshSpriteStatus().catch(() => {});
    }
  }, 5000);
  loadSettings();
  applyModeFieldVisibility();
  _applyCsvModeControls();
  renderSideNameEditor();
  setCombatantTeamFilter(combatantTeamFilter);
  loadTrainerFromStorage();
  refreshState().catch(() => {});
  refreshAiModels().catch(() => {});
  refreshSpriteStatus().catch(() => {});
} else if (charContentEl) {
  loadSnapshotsFromStorage();
  loadCharacterData()
    .then(() => {
      renderSnapshotPanel();
      _syncHistoryButtons();
    })
    .catch(() => {});
}
if (topbarEl) {
  topbarEl.classList.toggle("scrolled", window.scrollY > 4);
}







