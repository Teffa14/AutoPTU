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



const importTrainerButton = document.getElementById("import-trainer");



const clearTrainerButton = document.getElementById("clear-trainer");



const importRosterCsvButton = document.getElementById("import-roster-csv");



const exportRosterCsvButton = document.getElementById("export-roster-csv");



const clearRosterCsvButton = document.getElementById("clear-roster-csv");



const exportRosterMirrorInput = document.getElementById("export-roster-mirror");



const autoUseCreatorRosterInput = document.getElementById("auto-use-creator-roster");



const csvStrictModeInput = document.getElementById("csv-strict-mode");



const rosterCsvStatusEl = document.getElementById("roster-csv-status");



const infoTabs = Array.from(document.querySelectorAll(".info-tab"));



const infoTabPanels = Array.from(document.querySelectorAll(".info-tab-panel"));



const statusTabs = Array.from(document.querySelectorAll(".status-tab"));



const charStepButtons = Array.from(document.querySelectorAll(".char-step-btn"));



const charContentEl = document.getElementById("char-content");



const charMiniSummaryEl = document.getElementById("char-mini-summary");



const charUndoBtn = document.getElementById("char-undo");



const charRedoBtn = document.getElementById("char-redo");



const charSnapshotBtn = document.getElementById("char-snapshot");



const charSnapshotsOpenBtn = document.getElementById("char-snapshots-open");

const charSnapshotsPanel = document.getElementById("char-snapshots-panel");

const charGuidedToggleBtn = document.getElementById("char-guided-toggle");

const CHARACTER_STEP_SEQUENCE = [
  "profile",
  "skills",
  "advancement",
  "class",
  "features",
  "edges",
  "extras",
  "inventory",
  "pokemon-team",
  "poke-edges",
  "summary",
];

const CHARACTER_STEP_META = {
  profile: { label: "Profile" },
  skills: { label: "Skills" },
  advancement: { label: "Advancement" },
  class: { label: "Classes" },
  features: { label: "Features" },
  edges: { label: "Edges" },
  extras: { label: "Extras" },
  inventory: { label: "Inventory" },
  "pokemon-team": { label: "Pokemon Team" },
  "poke-edges": { label: "Poke Edges" },
  summary: { label: "Summary" },
};

const EXPORT_SIGNATURE = "OurosPTU";

const POKEMON_NATURES = [
  ["Cuddly", { hp: 1, atk: -2, def: 0, spatk: 0, spdef: 0, spd: 0 }, "hp", "atk"],
  ["Distracted", { hp: 1, atk: 0, def: -2, spatk: 0, spdef: 0, spd: 0 }, "hp", "def"],
  ["Proud", { hp: 1, atk: 0, def: 0, spatk: -2, spdef: 0, spd: 0 }, "hp", "spatk"],
  ["Decisive", { hp: 1, atk: 0, def: 0, spatk: 0, spdef: -2, spd: 0 }, "hp", "spdef"],
  ["Patient", { hp: 1, atk: 0, def: 0, spatk: 0, spdef: 0, spd: -2 }, "hp", "spd"],
  ["Desperate", { hp: -1, atk: 2, def: 0, spatk: 0, spdef: 0, spd: 0 }, "atk", "hp"],
  ["Lonely", { hp: 0, atk: 2, def: -2, spatk: 0, spdef: 0, spd: 0 }, "atk", "def"],
  ["Adamant", { hp: 0, atk: 2, def: 0, spatk: -2, spdef: 0, spd: 0 }, "atk", "spatk"],
  ["Naughty", { hp: 0, atk: 2, def: 0, spatk: 0, spdef: -2, spd: 0 }, "atk", "spdef"],
  ["Brave", { hp: 0, atk: 2, def: 0, spatk: 0, spdef: 0, spd: -2 }, "atk", "spd"],
  ["Stark", { hp: -1, atk: 0, def: 2, spatk: 0, spdef: 0, spd: 0 }, "def", "hp"],
  ["Bold", { hp: 0, atk: -2, def: 2, spatk: 0, spdef: 0, spd: 0 }, "def", "atk"],
  ["Impish", { hp: 0, atk: 0, def: 2, spatk: -2, spdef: 0, spd: 0 }, "def", "spatk"],
  ["Lax", { hp: 0, atk: 0, def: 2, spatk: 0, spdef: -2, spd: 0 }, "def", "spdef"],
  ["Relaxed", { hp: 0, atk: 0, def: 2, spatk: 0, spdef: 0, spd: -2 }, "def", "spd"],
  ["Curious", { hp: -1, atk: 0, def: 0, spatk: 2, spdef: 0, spd: 0 }, "spatk", "hp"],
  ["Modest", { hp: 0, atk: -2, def: 0, spatk: 2, spdef: 0, spd: 0 }, "spatk", "atk"],
  ["Mild", { hp: 0, atk: 0, def: -2, spatk: 2, spdef: 0, spd: 0 }, "spatk", "def"],
  ["Rash", { hp: 0, atk: 0, def: 0, spatk: 2, spdef: -2, spd: 0 }, "spatk", "spdef"],
  ["Quiet", { hp: 0, atk: 0, def: 0, spatk: 2, spdef: 0, spd: -2 }, "spatk", "spd"],
  ["Dreamy", { hp: -1, atk: 0, def: 0, spatk: 0, spdef: 2, spd: 0 }, "spdef", "hp"],
  ["Calm", { hp: 0, atk: -2, def: 0, spatk: 0, spdef: 2, spd: 0 }, "spdef", "atk"],
  ["Gentle", { hp: 0, atk: 0, def: -2, spatk: 0, spdef: 2, spd: 0 }, "spdef", "def"],
  ["Careful", { hp: 0, atk: 0, def: 0, spatk: -2, spdef: 2, spd: 0 }, "spdef", "spatk"],
  ["Sassy", { hp: 0, atk: 0, def: 0, spatk: 0, spdef: 2, spd: -2 }, "spdef", "spd"],
  ["Skittish", { hp: -1, atk: 0, def: 0, spatk: 0, spdef: 0, spd: 2 }, "spd", "hp"],
  ["Timid", { hp: 0, atk: -2, def: 0, spatk: 0, spdef: 0, spd: 2 }, "spd", "atk"],
  ["Hasty", { hp: 0, atk: 0, def: -2, spatk: 0, spdef: 0, spd: 2 }, "spd", "def"],
  ["Jolly", { hp: 0, atk: 0, def: 0, spatk: -2, spdef: 0, spd: 2 }, "spd", "spatk"],
  ["Naive", { hp: 0, atk: 0, def: 0, spatk: 0, spdef: -2, spd: 2 }, "spd", "spdef"],
  ["Hardy", { hp: 0, atk: 0, def: 0, spatk: 0, spdef: 0, spd: 0 }, "atk", "atk"],
  ["Docile", { hp: 0, atk: 0, def: 0, spatk: 0, spdef: 0, spd: 0 }, "def", "def"],
  ["Bashful", { hp: 0, atk: 0, def: 0, spatk: 0, spdef: 0, spd: 0 }, "spatk", "spatk"],
  ["Quirky", { hp: 0, atk: 0, def: 0, spatk: 0, spdef: 0, spd: 0 }, "spdef", "spdef"],
  ["Serious", { hp: 0, atk: 0, def: 0, spatk: 0, spdef: 0, spd: 0 }, "spd", "spd"],
  ["Composed", { hp: 0, atk: 0, def: 0, spatk: 0, spdef: 0, spd: 0 }, "hp", "hp"],
];


const charSaveLocalBtn = document.getElementById("char-save-local");



const charLoadLocalBtn = document.getElementById("char-load-local");
const builderUsefulChartsButton = document.getElementById("open-useful-charts");



const runtimeErrorEl = document.createElement("div");



runtimeErrorEl.id = "runtime-errors";



document.body.appendChild(runtimeErrorEl);



let aiDiagnosticsEl = null;







let combatantTeamFilter = "all";



let battleRosterCsvText = "";



let battleRosterCsvMeta = null;







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



  normal: "pulse",



  fighting: "slash",



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







const DEFAULT_MOVE_ANIM_FILES = {



  slash: "003-Attack01.png",



  pulse: "023-Burst01.png",



  wind: "023-Burst01.png",



  quake: "Earth1.png",



  shard: "023-Burst01.png",



  vine: "DustandGrass.png",



  shadow: "022-Darkness01.png",



  toxic: "028-State01.png",



  spark: "017-Thunder01.png",



  wave: "018-Water01.png",



  frost: "016-Ice01.png",



  flame: "015-Fire01.png",



  draco: "023-Burst01.png",



  psy: "Cosmo-01.png",



  gleam: "Anima (1).png",



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



let armedMove = null;



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



let gimmickState = {



  mega_evolve: false,



  dynamax: false,



  z_move: false,



  teracrystal: false,



  tera_type: "",



};



let itemTargetId = null;



let lastItemActorId = null;



let gridScale = 1;



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



let evolutionMinLevelData = null;



let moveRecordMap = null;



let pokemonMoveSourceData = null;



let rulebookGlossaryIndexCache = null;
let usefulChartsDataCache = null;
let usefulChartsDataPromise = null;



const DATA_POLICY_DEFAULTS = Object.freeze({
  evolution_profile: "ptu_builder_105",
  move_source_mode: "dataset_only",
});

const POKEMON_MOVE_SOURCE_OVERRIDES = {
  scyther: {
    tutor: ["Bug Bite"],
    egg: ["Baton Pass"],
  },
  scizor: {
    tutor: ["Bug Bite"],
  },
  "mega scizor": {
    tutor: ["Bug Bite"],
  },
  weavile: {
    natural: ["Assurance"],
    tutor: ["Dynamic Punch", "Dark Pulse"],
    tm: ["Dark Pulse"],
    level_up: {
      "Dark Pulse": 47,
    },
  },
};

const POKEMON_LEARNSET_BLACKLIST = {
  absol: ["Feint Attack"],
  "mega absol": ["Feint Attack"],
};



const POKEMON_EGG_MOVE_PARENT_FALLBACKS = {
  scizor: "scyther",
  "mega scizor": "scyther",
  kleavor: "scyther",
};



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



  poke_edges: new Set(),



  feature_order: [],



  edge_order: [],



  poke_edge_order: [],



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



  feature_sort_mode: "progressive",



  edge_sort_mode: "progressive",



  poke_edge_sort_mode: "progressive",



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



  glossary_query: "",



  glossary_category: "all",



  glossary_open: false,



  pokemon_team_search: "",



  pokemon_team_limit: 6,



  pokemon_team_auto_level: false,


  pokemon_team_autofill: true,



  data_policy: { ...DATA_POLICY_DEFAULTS },



};



const pokeApiMoveMetaCache = new Map();



const pokeApiAbilityMetaCache = new Map();



const pokeApiItemMetaCache = new Map();



const pokeApiTypeIconCache = new Map();



const pokeApiCryCache = new Map();



const pokeApiPending = new Map();



const cryAudio = new Audio();



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







function _extractRosterSummary(csvText, options = {}) {



  const rows = _coerceRosterCsvRows(csvText);



  if (!rows.length) throw new Error("Roster CSV is empty.");



  const allowSingleTeam = !!options.allowSingleTeam;



  const headerRowIndex = rows.findIndex((row) => Array.isArray(row) && row.some((cell) => String(cell || "").trim()));



  if (headerRowIndex < 0) throw new Error("Roster CSV is empty.");



  let header = (rows[headerRowIndex] || []).map((cell) => _normalizeCsvHeaderCell(cell));



  if (!header.includes("species") && !header.includes("pokemon") && !header.includes("name")) {



    const fallbackHeader = _fallbackCsvHeaderCells(csvText);



    if (fallbackHeader.length) header = fallbackHeader;



  }



  const sideIdx = header.findIndex((cell) => ["side", "team", "faction"].includes(cell));



  const speciesIdx = header.findIndex((cell) => ["species", "pokemon", "name"].includes(cell));



  if (speciesIdx < 0) throw new Error("Roster CSV requires a species column.");



  if (sideIdx < 0 && !allowSingleTeam) throw new Error("Roster CSV requires headers including side and species.");



  const sideCounts = new Map();



  for (let i = headerRowIndex + 1; i < rows.length; i += 1) {



    const row = rows[i] || [];



    const species = String(row[speciesIdx] || "").trim();



    if (!species) continue;



    const side = sideIdx >= 0 ? _normalizeRosterSide(row[sideIdx]) : "player";



    if (!side) {



      throw new Error(`Roster CSV row ${i + 1}: invalid side value.`);



    }



    sideCounts.set(side, Number(sideCounts.get(side) || 0) + 1);



  }



  if (sideCounts.size < 2 && !allowSingleTeam) {



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



}







function _clearBattleRosterCsv() {



  battleRosterCsvText = "";



  battleRosterCsvMeta = null;



  _renderRosterCsvStatus();



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



function _downloadBlobFile(filename, blob) {

  const safeName = String(filename || "").trim() || "download.bin";

  const link = document.createElement("a");

  const url = URL.createObjectURL(blob);

  link.href = url;

  link.download = safeName;

  document.body.appendChild(link);

  link.click();

  window.setTimeout(() => {

    link.remove();

    URL.revokeObjectURL(url);

  }, 0);

}



function _downloadCsvFile(filename, content) {

  const blob = new Blob([String(content || "")], { type: "text/csv;charset=utf-8;" });

  _downloadBlobFile(filename, blob);

}



function _rosterStatHeader() {

  return ["hp", "atk", "def", "spatk", "spdef", "spd"];

}



function _rosterStatModeHeader() {

  return ["stat_mode"];

}


function _rosterTutorPointHeader() {

  return ["tutor_points"];

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



function _rosterAbilityHeader() {

  return ["ability1", "ability2", "ability3", "ability4"];

}



function _rosterItemHeader() {

  return ["item1", "item2", "item3", "item4", "item5", "item6", "item7", "item8"];

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



function _rosterStatsFromBuild(build) {

  const stats = _normalizedRosterStats(build?.stats);

  return _rosterStatHeader().map((key) => Number(stats[key] || 0));

}



function _rosterStatsFromCombatant(entry) {

  const stats = _normalizedRosterStats(entry?.stats);

  return _rosterStatHeader().map((key) => Number(stats[key] || 0));

}



function _rosterMoveSourcesFromBuild(build) {

  const limit = _rosterMoveLimit();

  const moves = Array.isArray(build?.moves) ? build.moves.slice(0, limit) : [];

  const speciesEntry = _getPokemonSpeciesEntry(build?.species || build?.name || "");

  const sources = _effectivePokemonMoveSourceMap(build, speciesEntry);

  return moves.map((name) => String(sources[_normalizeMoveKey(name)] || "").trim()).concat(Array(Math.max(0, limit - moves.length)).fill(""));

}



function _rosterMoveSourcesFromCombatant(entry) {

  const limit = _rosterMoveLimit();

  const moves = _moveNameList(entry?.moves).slice(0, limit);

  const sourceMap = _normalizePokemonMoveSources(entry?.move_sources);

  return moves.map((name) => String(sourceMap[_normalizeMoveKey(name)] || "").trim()).concat(Array(Math.max(0, limit - moves.length)).fill(""));

}


function _serializePokeEdgeChoiceList(value) {

  if (!Array.isArray(value)) return "";
  return value
    .map((entry) => String(entry || "").trim())
    .filter(Boolean)
    .join(";");

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


function _rosterPokeEdgeChoiceCellsFromCombatant(entry) {

  const choices = _normalizePokeEdgeChoices(entry?.poke_edge_choices);
  return [
    _serializePokeEdgeChoiceList(choices.accuracy_training),
    _serializePokeEdgeChoiceList(choices.advanced_connection),
    String(choices.underdog_lessons?.evolution || "").trim(),
    _serializePokeEdgeChoiceList(choices.underdog_lessons?.moves),
  ];

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



    const moves = Array.isArray(build?.moves) ? build.moves.slice(0, _rosterMoveLimit()) : [];



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



        _pokemonEffectiveTutorPoints(build),



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



        _pokemonEffectiveTutorPoints(build),



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

    return parsed && typeof parsed === "object" ? _normalizeCharacterPayload(parsed) : null;


  } catch {



    return null;



  }



}







function _buildRosterCsvFromTrainerPayload(payload, includeFoe = true, requireBattleSummary = true) {

  const rows = _rosterRowsFromTrainerBuilds(_normalizeCharacterPayload(payload), includeFoe);


  if (!rows.length) return null;



  const csvText = stringifyCsv(rows);



  const summary = requireBattleSummary
    ? _extractRosterSummary(csvText)
    : {
        row_count: rows.length,
        distinct_sides: Array.from(new Set(rows.map((row) => String(row.side || "").trim()).filter(Boolean))),
      };



  return { csvText, summary };

}

function _trainerCsvListValue(values) {
  return _normalizeStringList(values).join("; ");
}

function _trainerCsvRowsFromPayload(payload) {
  const normalized = _normalizeCharacterPayload(payload);
  const rows = [
    ["field", "value"],
    ["format", "autoptu_trainer_v1"],
    ["name", String(normalized.profile?.name || "").trim()],
    ["played_by", String(normalized.profile?.played_by || "").trim()],
    ["age", String(normalized.profile?.age || "").trim()],
    ["sex", String(normalized.profile?.sex || "").trim()],
    ["height", String(normalized.profile?.height || "").trim()],
    ["weight", String(normalized.profile?.weight || "").trim()],
    ["money", String(normalized.profile?.money || "").trim()],
    ["region", String(normalized.profile?.region || "").trim()],
    ["concept", String(normalized.profile?.concept || "").trim()],
    ["background", String(normalized.profile?.background || "").trim()],
    ["level", String(_normalizeInteger(normalized.profile?.level, 1, 1, 50))],
    ["class_ids", _trainerCsvListValue(normalized.class_ids)],
    ["features", _trainerCsvListValue(normalized.features)],
    ["edges", _trainerCsvListValue(normalized.edges)],
  ];
  Object.entries(normalized.stats || {}).forEach(([key, value]) => {
    rows.push([`stat_${key}`, String(_normalizeInteger(value, 0, 0))]);
  });
  Object.entries(normalized.skills || {}).forEach(([key, value]) => {
    rows.push([`skill_${key}`, String(value == null ? "" : value)]);
  });
  return rows;
}

function _buildTrainerCsvFromTrainerPayload(payload) {
  return stringifyCsv(_trainerCsvRowsFromPayload(payload));
}

function _applyTrainerCsvToPayload(csvText, existingPayload) {
  const rows = parseCsv(String(csvText || ""));
  if (!rows.length) throw new Error("Trainer CSV is empty.");
  const header = (rows[0] || []).map((cell) => _normalizeCsvHeaderCell(cell));
  const fieldIdx = header.findIndex((cell) => cell === "field" || cell === "key");
  const valueIdx = header.findIndex((cell) => cell === "value");
  if (fieldIdx < 0 || valueIdx < 0) {
    throw new Error("Trainer CSV requires field,value headers.");
  }
  const base = _normalizeCharacterPayload(existingPayload || _snapshotCharacterState());
  const patch = {
    profile: { ...(base.profile || {}) },
    class_ids: Array.isArray(base.class_ids) ? base.class_ids.slice() : [],
    features: Array.isArray(base.features) ? base.features.slice() : [],
    edges: Array.isArray(base.edges) ? base.edges.slice() : [],
    skills: { ...(base.skills || {}) },
    stats: { ...(base.stats || {}) },
    pokemon_builds: Array.isArray(base.pokemon_builds) ? base.pokemon_builds.slice() : [],
    inventory: base.inventory,
  };
  for (let i = 1; i < rows.length; i += 1) {
    const row = rows[i] || [];
    const field = String(row[fieldIdx] || "").trim().toLowerCase();
    const value = String(row[valueIdx] || "").trim();
    if (!field || field === "format") continue;
    if (field === "class_ids") {
      patch.class_ids = value ? value.split(/\s*;\s*/).filter(Boolean) : [];
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
    if (Object.prototype.hasOwnProperty.call(patch.profile, field)) {
      patch.profile[field] = field === "level" ? _normalizeInteger(value, 1, 1, 50) : value;
    }
  }
  patch.class_id = String(patch.class_ids[0] || "").trim();
  return _normalizeCharacterPayload({ ...base, ...patch, pokemon_builds: base.pokemon_builds });
}







function _downloadTournamentSubmissionPack() {

  const normalized = _normalizeCharacterPayload(_snapshotCharacterState());

  const payload = {

    profile: normalized.profile,

    pokemon_builds: normalized.pokemon_builds,

    signed_by: EXPORT_SIGNATURE,

  };


  if (!payload.pokemon_builds.length) {



    throw new Error("No Pokemon builds found to export.");



  }



  const roster = _buildRosterCsvFromTrainerPayload(payload, false, false);
  const trainerCsv = _buildTrainerCsvFromTrainerPayload(normalized);



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



      content: JSON.stringify(normalized, null, 2),



    },



    {

      name: "README.txt",


      content:



        "AutoPTU project export\r\n\r\n" +
        "Use the builder JSON to fully restore the project.\r\n" +
        "Use the team roster CSV for battle imports or one-team engine tests.\r\n" +
        "Use the trainer CSV when you want trainer data without the Pokemon roster.\r\n" +
        "If only a team CSV is loaded, AutoPTU creates an empty trainer shell automatically.\r\n",

    },

    {

      name: "OurosPTU-signature.txt",

      content: `Digitally signed by ${EXPORT_SIGNATURE}\r\nGenerated by AutoPTU Character Builder\r\n`,

    },

  ];


  const blob = buildZip(files);

  _downloadBlobFile(`${safeName}_autoptu_team_pack.zip`, blob);

}






function _csvCell(row, idx) {



  if (!Array.isArray(row) || idx < 0 || idx >= row.length) return "";



  return String(row[idx] || "").trim();



}







function _builderPokemonImportFromRosterCsv(csvText) {



  const rows = parseCsv(String(csvText || ""));



  if (!rows.length) throw new Error("Roster CSV is empty.");



  const headerRowIndex = rows.findIndex((row) => Array.isArray(row) && row.some((cell) => String(cell || "").trim()));
  if (headerRowIndex < 0) throw new Error("Roster CSV is empty.");
  let header = (rows[headerRowIndex] || []).map((cell) => _normalizeCsvHeaderCell(cell));
  if (!header.includes("species") && !header.includes("pokemon") && !header.includes("name")) {
    const fallbackHeader = _fallbackCsvHeaderCells(csvText);
    if (fallbackHeader.length) header = fallbackHeader;
  }



  const sideIdx = header.findIndex((cell) => ["side", "team", "faction"].includes(cell));



  const speciesIdx = header.findIndex((cell) => ["species", "pokemon", "name"].includes(cell));



  if (speciesIdx < 0) {



    throw new Error("Roster CSV requires a species column.");



  }



  const levelIdx = header.findIndex((cell) => ["level", "lvl"].includes(cell));



  const nicknameIdx = header.findIndex((cell) => ["nickname", "alias"].includes(cell));



  const nameIdx = header.findIndex((cell) => cell === "name");



  const abilityIdx = header.findIndex((cell) => cell === "ability");

  const itemIdx = header.findIndex((cell) => ["item", "held_item"].includes(cell));



  const natureIdx = header.findIndex((cell) => cell === "nature");



  const slotIdx = header.findIndex((cell) => ["slot", "index", "position"].includes(cell));



  const abilityIndices = header
    .map((cell, idx) => ({ cell, idx }))
    .filter((entry) => /^ability(?:_?\d+)?$/.test(entry.cell))
    .map((entry) => entry.idx)
    .slice(0, 4);



  const itemIndices = header
    .map((cell, idx) => ({ cell, idx }))
    .filter((entry) => /^(?:item|held_item)(?:_?\d+)?$/.test(entry.cell))
    .map((entry) => entry.idx)
    .slice(0, 8);



  const pokeEdgeIndices = header
    .map((cell, idx) => ({ cell, idx }))
    .filter((entry) => /^(?:poke_edge|pokeedge)(?:_?\d+)?$/.test(entry.cell))
    .map((entry) => entry.idx)
    .slice(0, 8);

  const accuracyTrainingIdx = header.findIndex((cell) => ["poke_edge_accuracy_training", "edge_accuracy_training", "accuracy_training"].includes(cell));
  const advancedConnectionIdx = header.findIndex((cell) => ["poke_edge_advanced_connection", "edge_advanced_connection", "advanced_connection"].includes(cell));
  const underdogEvolutionIdx = header.findIndex((cell) => ["poke_edge_underdog_evolution", "edge_underdog_evolution", "underdog_evolution"].includes(cell));
  const underdogMovesIdx = header.findIndex((cell) => ["poke_edge_underdog_moves", "edge_underdog_moves", "underdog_moves"].includes(cell));



  const statIndices = {
    hp: header.findIndex((cell) => ["hp", "hp_stat", "hpstat"].includes(cell)),
    atk: header.findIndex((cell) => ["atk", "attack"].includes(cell)),
    def: header.findIndex((cell) => ["def", "defense"].includes(cell)),
    spatk: header.findIndex((cell) => ["spatk", "sp_atk", "special_attack", "specialattack", "spa"].includes(cell)),
    spdef: header.findIndex((cell) => ["spdef", "sp_def", "special_defense", "specialdefense", "spdf"].includes(cell)),
    spd: header.findIndex((cell) => ["spd", "speed"].includes(cell)),
  };



  const statModeIdx = header.findIndex((cell) => ["stat_mode", "stats_mode", "statmode"].includes(cell));



  const tutorPointsIdx = header.findIndex((cell) => ["tutor_points", "tutor_point", "tutorpoints", "tp"].includes(cell));



  const moveIndices = header



    .map((cell, idx) => ({ cell, idx }))



    .filter((entry) => /^move(?:_?\d+)?$/.test(entry.cell) || /^moves_?\d+$/.test(entry.cell))



    .map((entry) => entry.idx)



    .slice(0, _rosterMoveLimit());



  const moveSourceIndices = header



    .map((cell, idx) => ({ cell, idx }))



    .filter((entry) => /^move_source(?:_?\d+)?$/.test(entry.cell) || /^movesource_?\d+$/.test(entry.cell))



    .map((entry) => entry.idx)



    .slice(0, _rosterMoveLimit());



  const builds = [];



  for (let i = headerRowIndex + 1; i < rows.length; i += 1) {



    const row = rows[i] || [];



    const species = _csvCell(row, speciesIdx);



    if (!species) continue;



    const side = sideIdx >= 0 ? _normalizeRosterSide(_csvCell(row, sideIdx)) : "player";



    if (!side) throw new Error(`Roster CSV row ${i + 1}: invalid side value.`);



    const nickname = _csvCell(row, nicknameIdx) || (nameIdx >= 0 && nameIdx !== speciesIdx ? _csvCell(row, nameIdx) : "");



    const abilities = [
      ...abilityIndices.map((idx) => _csvCell(row, idx)).filter(Boolean),
      ...(!abilityIndices.length && abilityIdx >= 0 ? [_csvCell(row, abilityIdx)] : []),
    ].filter(Boolean);



    const items = [
      ...itemIndices.map((idx) => _csvCell(row, idx)).filter(Boolean),
      ...(!itemIndices.length && itemIdx >= 0 ? [_csvCell(row, itemIdx)] : []),
    ].filter(Boolean);



    const nature = _csvCell(row, natureIdx);



    const level = Math.max(1, Number(_csvCell(row, levelIdx) || 30) || 30);



    const moves = moveIndices.map((idx) => _csvCell(row, idx)).filter(Boolean);



    const moveSources = {};



    moves.forEach((moveName, moveIdx) => {
      const sourceValue = _normalizePokemonMoveSource(moveSourceIndices[moveIdx] >= 0 ? _csvCell(row, moveSourceIndices[moveIdx]) : "");
      if (!moveName || !sourceValue) return;
      moveSources[_normalizeMoveKey(moveName)] = sourceValue;
    });



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



    const slot = Math.max(1, Number(_csvCell(row, slotIdx) || builds.length + 1) || builds.length + 1);



    const speciesEntry = _getPokemonSpeciesEntry(species);



    const stats = _normalizePokemonStatOverrides({
      hp: _normalizeInteger(_csvCell(row, statIndices.hp), speciesEntry?.base_stats?.hp ?? 0, speciesEntry?.base_stats?.hp ?? 0),
      atk: _normalizeInteger(_csvCell(row, statIndices.atk), speciesEntry?.base_stats?.attack ?? 0, speciesEntry?.base_stats?.attack ?? 0),
      def: _normalizeInteger(_csvCell(row, statIndices.def), speciesEntry?.base_stats?.defense ?? 0, speciesEntry?.base_stats?.defense ?? 0),
      spatk: _normalizeInteger(
        _csvCell(row, statIndices.spatk),
        speciesEntry?.base_stats?.special_attack ?? 0,
        speciesEntry?.base_stats?.special_attack ?? 0
      ),
      spdef: _normalizeInteger(
        _csvCell(row, statIndices.spdef),
        speciesEntry?.base_stats?.special_defense ?? 0,
        speciesEntry?.base_stats?.special_defense ?? 0
      ),
      spd: _normalizeInteger(_csvCell(row, statIndices.spd), speciesEntry?.base_stats?.speed ?? 0, speciesEntry?.base_stats?.speed ?? 0),
    });



    builds.push({



      name: nickname || species,



      species,



      level,



      nature,



      stat_mode: _normalizePokemonStatMode(_csvCell(row, statModeIdx)),

      tutor_points: _normalizeInteger(_csvCell(row, tutorPointsIdx), 0, 0),

      move_sources: moveSources,



      battle_side: side === "player" ? "player" : side === "foe" ? "foe" : side,



      battle_slot: slot,



      moves,



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

function _normalizeCsvHeaderCell(cell) {
  return String(cell || "")
    .replace(/^\ufeff/, "")
    .trim()
    .replace(/^"+|"+$/g, "")
    .toLowerCase();
}

function _fallbackCsvHeaderCells(text) {
  const lines = String(text || "").split(/\r\n|\n|\r/);
  const first = lines.find((line) => String(line || "").trim());
  if (!first) return [];
  const delimiter = first.includes("\t") ? "\t" : first.includes(";") && !first.includes(",") ? ";" : ",";
  return first.split(delimiter).map((cell) => _normalizeCsvHeaderCell(cell));
}

function _coerceRosterCsvRows(csvText) {
  const rawText = String(csvText || "").replace(/\u0000/g, "");
  const parsed = parseCsv(rawText);
  const headerRowIndex = parsed.findIndex((row) => Array.isArray(row) && row.some((cell) => String(cell || "").trim()));
  if (headerRowIndex < 0) return parsed;
  const header = (parsed[headerRowIndex] || []).map((cell) => _normalizeCsvHeaderCell(cell));
  const hasExpectedHeader = header.includes("species") || header.includes("pokemon") || header.includes("name");
  const looksCollapsed = (parsed[headerRowIndex] || []).length <= 1;
  if (hasExpectedHeader && !looksCollapsed) return parsed;
  const lines = rawText.split(/\r\n|\n|\r/).filter((line) => String(line || "").trim());
  if (!lines.length) return parsed;
  const first = lines[0];
  const delimiter = first.includes("\t") ? "\t" : first.includes(";") && !first.includes(",") ? ";" : ",";
  const reparsed = lines.map((line) =>
    line
      .split(delimiter)
      .map((cell) => String(cell || "").replace(/^\ufeff/, "").trim().replace(/^"+|"+$/g, ""))
  );
  return reparsed.length ? reparsed : parsed;
}

function _speciesAncestorNames(name) {
  const lineage = evolutionMinLevelData?.lineage && typeof evolutionMinLevelData.lineage === "object" ? evolutionMinLevelData.lineage : null;
  if (!lineage) return [];
  const candidates = _learnsetKeyCandidates(name);
  const comparable = candidates.flatMap((key) => _speciesLookupComparableKeys(key));
  for (const candidate of candidates) {
    const direct = lineage[candidate];
    if (Array.isArray(direct) && direct.length) return direct.slice();
  }
  for (const [key, ancestors] of Object.entries(lineage)) {
    if (!Array.isArray(ancestors) || !ancestors.length) continue;
    if (_keysIntersect(_speciesLookupComparableKeys(key), comparable)) return ancestors.slice();
  }
  return [];
}




function _speciesDescendantNames(name) {
  const lineage = evolutionMinLevelData?.lineage && typeof evolutionMinLevelData.lineage === "object" ? evolutionMinLevelData.lineage : null;
  if (!lineage) return [];
  const candidates = _learnsetKeyCandidates(name);
  const comparable = candidates.flatMap((key) => _speciesLookupComparableKeys(key));
  return Object.entries(lineage)
    .filter(([, ancestors]) => Array.isArray(ancestors) && ancestors.length)
    .filter(([, ancestors]) =>
      ancestors.some((ancestor) => _keysIntersect(_speciesLookupComparableKeys(ancestor), comparable))
    )
    .map(([speciesName]) => speciesName);
}




function _speciesFinalEvolutionNames(name) {
  const descendants = _speciesDescendantNames(name);
  if (!descendants.length) return [];
  const descendantSet = new Set(descendants.map((entry) => _normalizeSearchText(entry)));
  return descendants.filter((candidate) => {
    const childDescendants = _speciesDescendantNames(candidate);
    return !childDescendants.some((child) => descendantSet.has(_normalizeSearchText(child)));
  });
}

function _looksLikeTrainerCsv(text) {
  const rows = parseCsv(String(text || ""));
  if (!rows.length) return false;
  const headerRow = rows.find((row) => Array.isArray(row) && row.some((cell) => String(cell || "").trim())) || [];
  const header = headerRow.map((cell) => _normalizeCsvHeaderCell(cell));
  return header.includes("field") && header.includes("value");
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



function _asStringArray(value) {

  if (value instanceof Set) return Array.from(value);

  if (!Array.isArray(value)) return [];

  return value.map((entry) => String(entry || "").trim()).filter(Boolean);

}



function _normalizeInteger(value, fallback, min = null, max = null) {

  const num = Number(value);

  let next = Number.isFinite(num) ? Math.trunc(num) : Math.trunc(Number(fallback) || 0);

  if (min !== null && min !== undefined && Number.isFinite(Number(min))) next = Math.max(Number(min), next);

  if (max !== null && max !== undefined && Number.isFinite(Number(max))) next = Math.min(Number(max), next);

  return next;

}



function _normalizeTextMap(value) {

  if (!value || typeof value !== "object" || Array.isArray(value)) return {};

  const out = {};

  Object.entries(value).forEach(([key, entry]) => {

    out[String(key || "")] = String(entry || "");

  });

  return out;

}



function _normalizeStringList(value) {

  return _asStringArray(value);

}



function _normalizePokemonStatOverrides(value) {



  const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};



  const out = {};



  ["hp", "atk", "def", "spatk", "spdef", "spd"].forEach((key) => {



    if (source[key] === undefined || source[key] === null || source[key] === "") return;



    out[key] = _normalizeInteger(source[key], source[key], 0);



  });



  return out;



}



function _normalizePokemonStatMode(value) {

  const mode = String(value || "").trim().toLowerCase();

  return mode === "post_nature" ? "post_nature" : "pre_nature";

}



function _normalizePokemonMoveSource(value) {

  const mode = String(value || "").trim().toLowerCase();

  if (mode === "sketch") return "sketch";
  if (mode === "egg" || mode === "egg_move" || mode === "egg move") return "egg";

  if (mode === "tm" || mode === "machine") return "tm";

  if (mode === "tutor" || mode === "tutor_tm" || mode === "non_natural") return "tutor";

  if (mode === "level" || mode === "level_up" || mode === "natural") return "level_up";

  return "";

}



function _normalizePokemonMoveSources(value) {

  if (!value || typeof value !== "object" || Array.isArray(value)) return {};

  const out = {};

  Object.entries(value).forEach(([key, entry]) => {
    const normalizedKey = _normalizeMoveKey(key);
    const normalizedValue = _normalizePokemonMoveSource(entry);
    if (!normalizedKey || !normalizedValue) return;
    out[normalizedKey] = normalizedValue;
  });

  return out;

}



function _pokemonMoveSourceAvailability(speciesEntry, level, build = null) {

  const natural = new Set();
  const sketch = new Set();
  const tm = new Set();
  const tutor = new Set();
  const egg = new Set();
  const tutorFallback = new Set();
  const learnset = speciesEntry ? _getLearnsetForSpecies(speciesEntry.name) : [];
  const inheritedLearnsets = speciesEntry
    ? _speciesAncestorNames(speciesEntry.name).map((ancestorName) => _getLearnsetForSpecies(ancestorName)).filter((list) => Array.isArray(list) && list.length)
    : [];
  const safeLevel = Math.max(1, Math.min(100, Number(level || 1)));
  const normalizedSpeciesKey = _normalizeSearchText(speciesEntry?.name || "");
  const sourceEntries = pokemonMoveSourceData?.entries && typeof pokemonMoveSourceData.entries === "object" ? pokemonMoveSourceData.entries : {};
  const sourceRecord =
    sourceEntries[speciesEntry?.name || ""] ||
    sourceEntries[normalizedSpeciesKey] ||
    Object.entries(sourceEntries).find(([name]) => _normalizeSearchText(name) === normalizedSpeciesKey)?.[1] ||
    null;
  const sourceNatural = new Set(_normalizeStringList(sourceRecord?.natural).map((moveName) => _normalizeMoveKey(moveName)));
  const sourceTm = new Set(_normalizeStringList(sourceRecord?.tm).map((moveName) => _normalizeMoveKey(moveName)));
  const sourceTutor = new Set(_normalizeStringList(sourceRecord?.tutor).map((moveName) => _normalizeMoveKey(moveName)));
  const sourceEgg = new Set(_normalizeStringList(sourceRecord?.egg).map((moveName) => _normalizeMoveKey(moveName)));
  const moveSourceMode = _currentDataPolicy().move_source_mode;

  if (normalizedSpeciesKey === "smeargle") {
    (masterData?.pokemon?.moves || []).forEach((entry) => {
      const key = _normalizeMoveKey(entry?.name || "");
      if (key && key !== "struggle" && key !== "sketch") sketch.add(key);
    });
  }

  (learnset || []).forEach((entry) => {
    const moveName = String(entry?.move || entry?.name || "").trim();
    const key = _normalizeMoveKey(moveName);
    const moveLevel = Number(entry?.level || 0);
    if (!key || !Number.isFinite(moveLevel)) return;
    if (moveLevel > 0 && moveLevel <= safeLevel) {
      natural.add(key);
      return;
    }
    if (moveLevel <= 0) {
      const inNatural = sourceNatural.has(key);
      const inEgg = sourceEgg.has(key);
      const inTm = sourceTm.has(key);
      const inTutor = sourceTutor.has(key);
      if (inNatural) natural.add(key);
      if (inEgg) egg.add(key);
      if (inTm) tm.add(key);
      if (inTutor) tutor.add(key);
      if (!inNatural && !inEgg && !inTm && !inTutor && moveSourceMode === "legacy_level0_tutor") {
        tutor.add(key);
        tutorFallback.add(key);
      }
    }
  });

  inheritedLearnsets.forEach((list) => {
    (list || []).forEach((entry) => {
      const moveName = String(entry?.move || entry?.name || "").trim();
      const key = _normalizeMoveKey(moveName);
      const moveLevel = Number(entry?.level || 0);
      if (!key || !Number.isFinite(moveLevel) || moveLevel <= 0 || moveLevel > safeLevel) return;
      natural.add(key);
    });
  });

  const directOverrides = POKEMON_MOVE_SOURCE_OVERRIDES[normalizedSpeciesKey] || {};
  _normalizeStringList(directOverrides.natural).forEach((moveName) => natural.add(_normalizeMoveKey(moveName)));
  const levelUpOverrides = directOverrides.level_up && typeof directOverrides.level_up === "object" ? directOverrides.level_up : {};
  Object.entries(levelUpOverrides).forEach(([moveName, moveLevel]) => {
    const key = _normalizeMoveKey(moveName);
    const requiredLevel = Number(moveLevel || 0);
    if (key && Number.isFinite(requiredLevel) && requiredLevel > 0 && requiredLevel <= safeLevel) natural.add(key);
  });
  _normalizeStringList(directOverrides.tm).forEach((moveName) => tm.add(_normalizeMoveKey(moveName)));
  _normalizeStringList(directOverrides.tutor).forEach((moveName) => tutor.add(_normalizeMoveKey(moveName)));
  _normalizeStringList(directOverrides.egg).forEach((moveName) => egg.add(_normalizeMoveKey(moveName)));
  sourceNatural.forEach((moveKey) => natural.add(moveKey));
  sourceTm.forEach((moveKey) => tm.add(moveKey));
  sourceTutor.forEach((moveKey) => tutor.add(moveKey));
  sourceEgg.forEach((moveKey) => egg.add(moveKey));

  const visited = new Set();
  let parentKey = POKEMON_EGG_MOVE_PARENT_FALLBACKS[normalizedSpeciesKey] || "";
  while (parentKey && !visited.has(parentKey)) {
    visited.add(parentKey);
    const parentOverrides = POKEMON_MOVE_SOURCE_OVERRIDES[parentKey] || {};
    _normalizeStringList(parentOverrides.egg).forEach((moveName) => egg.add(_normalizeMoveKey(moveName)));
    parentKey = POKEMON_EGG_MOVE_PARENT_FALLBACKS[parentKey] || "";
  }

  const underdogLessons = _pokemonHasPokeEdge(build, "Underdog's Lessons")
    ? _pokemonUnderdogLessonOptions(speciesEntry, build)
    : null;
  if (underdogLessons) {
    underdogLessons.natural.forEach((moveKey) => natural.add(moveKey));
    underdogLessons.tm.forEach((moveKey) => tm.add(moveKey));
    underdogLessons.tutor.forEach((moveKey) => tutor.add(moveKey));
  }

  return { natural, sketch, tm, tutor, egg, tutorFallback, learnset };

}


function _pokemonSketchSlotLimit(speciesEntry, level) {

  if (_normalizeSearchText(speciesEntry?.name || "") !== "smeargle") return 0;
  const safeLevel = Math.max(1, Math.min(100, Number(level || 1)));
  const learnset = speciesEntry ? _getLearnsetForSpecies(speciesEntry.name) : [];
  const explicitSlots = (learnset || []).filter((entry) => _normalizeMoveKey(entry?.move || entry?.name || "") === "sketch" && Number(entry?.level || 0) > 0 && Number(entry?.level || 0) <= safeLevel).length;
  return Math.max(1, explicitSlots);

}


function _pokemonSketchMovesUsed(build, speciesEntry) {

  if (_normalizeSearchText(speciesEntry?.name || build?.species || "") !== "smeargle") return 0;
  const moveSources = _normalizePokemonMoveSources(build?.move_sources);
  const moves = Array.isArray(build?.moves) ? build.moves : [];
  return moves.filter((moveName) => {
    const key = _normalizeMoveKey(moveName);
    if (!key) return false;
    if (key === "sketch") return true;
    return moveSources[key] === "sketch";
  }).length;

}



function _effectivePokemonMoveSourceMap(build, speciesEntry) {

  const stored = _normalizePokemonMoveSources(build?.move_sources);
  const moves = Array.isArray(build?.moves) ? build.moves : [];
  const availability = _pokemonMoveSourceAvailability(speciesEntry, build?.level || 1, build);
  const out = {};

  moves.forEach((moveName) => {
    const key = _normalizeMoveKey(moveName);
    if (!key) return;
    const normalizedSpeciesKey = _normalizeSearchText(speciesEntry?.name || "");
    const explicit = stored[key];
    if (explicit) {
      out[key] = explicit;
      return;
    }
    if (availability.natural.has(key)) {
      out[key] = "level_up";
      return;
    }
    if (availability.sketch?.has(key)) {
      out[key] = "sketch";
      return;
    }
    if (availability.egg.has(key)) {
      out[key] = "egg";
      return;
    }
    if (availability.tm.has(key)) {
      out[key] = "tm";
      return;
    }
    if (availability.tutor.has(key)) {
      out[key] = "tutor";
    }
  });

  return out;

}



function _pokemonTutorMoveLimit() {

  return (Array.isArray(characterState?.features) ? characterState.features : []).some((name) => _normalizeSearchText(name) === _normalizeSearchText("Lifelong Learning"))
    ? 4
    : 3;

}



function _pokemonMoveSourceLabel(value) {

  const normalized = _normalizePokemonMoveSource(value);
  if (normalized === "sketch") return "Sketch";
  if (normalized === "egg") return "Egg";
  if (normalized === "tm") return "TM";
  if (normalized === "tutor") return "Tutor";
  return "Level-Up";

}




function _pokemonMoveSourceCost(value) {



  const normalized = _normalizePokemonMoveSource(value);



  if (normalized === "sketch") return 0;
  if (normalized === "tm") return 1;



  if (normalized === "tutor" || normalized === "egg") return 2;



  return 0;



}



function _normalizeDataPolicy(source) {

  const raw = source && typeof source === "object" ? source : {};
  const evolutionProfile = String(raw.evolution_profile || DATA_POLICY_DEFAULTS.evolution_profile).trim();
  const moveSourceMode = String(raw.move_source_mode || DATA_POLICY_DEFAULTS.move_source_mode).trim();

  return {
    evolution_profile: evolutionProfile || DATA_POLICY_DEFAULTS.evolution_profile,
    move_source_mode:
      moveSourceMode === "legacy_level0_tutor" ? "legacy_level0_tutor" : DATA_POLICY_DEFAULTS.move_source_mode,
  };

}



function _currentDataPolicy() {

  return _normalizeDataPolicy(characterState?.data_policy);

}



function _evolutionProfileCatalog() {

  const profiles =
    evolutionMinLevelData?.profiles && typeof evolutionMinLevelData.profiles === "object" ? evolutionMinLevelData.profiles : null;
  if (profiles && Object.keys(profiles).length) {
    const preferredOrder = [DATA_POLICY_DEFAULTS.evolution_profile, "foundry_default"];
    const ordered = {};
    preferredOrder.forEach((key) => {
      if (profiles[key]) ordered[key] = profiles[key];
    });
    Object.entries(profiles).forEach(([key, value]) => {
      if (!(key in ordered)) ordered[key] = value;
    });
    return ordered;
  }
  return {
    legacy_flat: {
      label: "Official PTU Core Rules",
      source: "Packaged builder evolution map",
      version: "Fallback packaged evolution map",
      notes: "This build only has one packaged evolution minimum-level map, and it is treated as the official default.",
      levels: evolutionMinLevelData || characterData?.pokemon?.evolution_min_level || {},
    },
  };

}



function _activeEvolutionProfileId() {

  const catalog = _evolutionProfileCatalog();
  const policy = _currentDataPolicy();
  if (catalog[policy.evolution_profile]) return policy.evolution_profile;
  if (catalog[DATA_POLICY_DEFAULTS.evolution_profile]) return DATA_POLICY_DEFAULTS.evolution_profile;
  return Object.keys(catalog)[0] || "legacy_flat";

}



function _activeEvolutionProfile() {

  const catalog = _evolutionProfileCatalog();
  return catalog[_activeEvolutionProfileId()] || null;

}



function _activeEvolutionLevelMap() {

  const profile = _activeEvolutionProfile();
  if (profile?.levels && typeof profile.levels === "object") return profile.levels;
  return evolutionMinLevelData || characterData?.pokemon?.evolution_min_level || {};

}



function _moveSourcePolicyNote() {

  const policy = _currentDataPolicy();
  if (policy.move_source_mode === "legacy_level0_tutor") {
    return {
      label: "Legacy Level-0 Fallback",
      source: pokemonMoveSourceData?.generated_from || "Local learnset + source dataset",
      version: "Treat unlabeled level 0 learnset entries as Tutor/TM-style",
      notes: "Compatibility mode. This may surface extra Tutor/TM moves that are not explicitly tagged in the packaged move-source dataset.",
    };
  }
  return {
    label: "Tagged Source Dataset",
    source: pokemonMoveSourceData?.generated_from || "Packaged move-source dataset",
    version: "Explicit Egg/Tutor tags only",
    notes: "Recommended. The builder only treats moves as Egg or Tutor/TM when they are tagged in the packaged move-source dataset or explicit local overrides.",
  };

}



function _pokemonMoveSourceOriginNote(availability, moveKey, selectedSource = "") {

  const normalizedSource = _normalizePokemonMoveSource(selectedSource);
  if (normalizedSource === "sketch") {
    return "Origin: learned via Sketch rather than a normal species learnset source.";
  }
  if (normalizedSource === "egg" && availability?.egg?.has(moveKey)) {
    return "Origin: explicit Egg tag from the packaged move-source dataset.";
  }
  if (normalizedSource === "tm" && availability?.tm?.has(moveKey)) {
    return "Origin: TM-style move from a packaged source tag, learnset row, or local builder override.";
  }
  if (normalizedSource === "tutor" && availability?.tutorFallback?.has(moveKey)) {
    return "Origin: Legacy Level-0 Fallback from unlabeled learnset data, not an explicit Tutor/TM tag.";
  }
  if (normalizedSource === "tutor" && availability?.tutor?.has(moveKey)) {
    return "Origin: explicit Tutor tag from the packaged move-source dataset or local builder override.";
  }
  if (!normalizedSource && availability?.tutorFallback?.has(moveKey)) {
    return "Origin: Legacy Level-0 Fallback from unlabeled learnset data, not an explicit Tutor/TM tag.";
  }
  if (!normalizedSource && availability?.egg?.has(moveKey)) {
    return "Origin: explicit Egg tag from the packaged move-source dataset.";
  }
  if (!normalizedSource && availability?.sketch?.has(moveKey)) {
    return "Origin: legal Sketch replacement for Smeargle.";
  }
  if (!normalizedSource && availability?.tm?.has(moveKey)) {
    return "Origin: TM-style move from a packaged source tag, learnset row, or local builder override.";
  }
  if (!normalizedSource && availability?.tutor?.has(moveKey)) {
    return "Origin: explicit Tutor tag from the packaged move-source dataset or local builder override.";
  }
  if (availability?.natural?.has(moveKey)) {
    return "Origin: level-up learnset entry for the current species and level.";
  }
  return "";

}



function _basenamePath(value) {

  const text = String(value || "").trim();
  if (!text) return "";
  const parts = text.split(/[\\/]/);
  return parts[parts.length - 1] || text;

}



function _builderDataSourceRows() {

  const masterSources = masterData?.sources && typeof masterData.sources === "object" ? masterData.sources : {};
  const evolutionProfile = _activeEvolutionProfile();
  const moveSourcePolicy = _moveSourcePolicyNote();

  return [
    {
      key: "evolution_profile",
      label: "Evolution Legality",
      source: evolutionProfile?.source || "Packaged evolution legality dataset",
      version: evolutionProfile?.version || "Current builder profile",
      notes: evolutionProfile?.notes || "Official PTU Core Rules are the default. Foundry compatibility is optional.",
      options: Object.entries(_evolutionProfileCatalog()).map(([value, profile]) => ({
        value,
        label: profile?.label || value,
      })),
      value: _activeEvolutionProfileId(),
    },
    {
      key: "move_source_mode",
      label: "Egg / Tutor Move Sources",
      source: moveSourcePolicy.source,
      version: moveSourcePolicy.version,
      notes: moveSourcePolicy.notes,
      options: [
        { value: "dataset_only", label: "Tagged Source Dataset" },
        { value: "legacy_level0_tutor", label: "Legacy Level-0 Fallback" },
      ],
      value: _currentDataPolicy().move_source_mode,
    },
    {
      label: "Moves / Stats / Capabilities",
      source: _basenamePath(masterSources.moves) || "master_dataset.json + compiled species data",
      version: "Packaged master dataset",
      notes: "Pokemon move records, species stats, abilities, and capabilities currently come from the packaged master dataset and compiled species sources.",
    },
    {
      label: "Trainer Classes / Features / Edges",
      source: _basenamePath(masterSources.character_creation) || "character_creation.json",
      version: "Packaged character creation dataset",
      notes: "Trainer-side classes, features, edges, and prerequisite graph currently use the packaged character creation dataset.",
    },
    {
      label: "Items",
      source: _basenamePath(masterSources.items_csv || masterSources.inventory_csv) || "Packaged item data",
      version: "Fancy PTU item/inventory CSV import",
      notes: "Item descriptions and inventory catalog entries currently come from the packaged item and inventory CSV sources.",
    },
  ];

}



function _normalizePokemonBuild(build, trainerLevel, autoLevel) {

  const source = build && typeof build === "object" ? build : {};

  const trainerScaled = trainerToPokemonLevel(trainerLevel);
  const level = autoLevel
    ? trainerScaled
    : _normalizeInteger(source.level, trainerScaled, 1, 100);
  const normalized = {
    name: String(source.name || source.species || "").trim(),
    species: String(source.species || source.name || "").trim(),
    level,
    battle_side: String(source.battle_side || "").trim(),
    moves: _normalizeStringList(source.moves).slice(0, _rosterMoveLimit()),
    abilities: _normalizeStringList(source.abilities).slice(0, 4),
    items: _normalizeStringList(source.items).slice(0, 8),
    poke_edges: _normalizeStringList(source.poke_edges),
    nature: String(source.nature || "").trim(),
    stat_mode: _normalizePokemonStatMode(source.stat_mode),
    tutor_points: 0,
    tutor_points_mode: "adjustment",
    move_sources: _normalizePokemonMoveSources(source.move_sources),
    stats: _normalizePokemonStatOverrides(source.stats),
    poke_edge_choices: _normalizePokeEdgeChoices(source.poke_edge_choices),
  };
  const tutorMode = String(source.tutor_points_mode || "").trim().toLowerCase();
  const rawTutorPoints = _normalizeInteger(source.tutor_points, 0, -999, 999);
  if (tutorMode === "adjustment") {
    normalized.tutor_points = rawTutorPoints;
  } else {
    const legacyTotal = Math.max(0, rawTutorPoints);
    normalized.tutor_points = legacyTotal - (_pokemonBaseTutorPoints(level) + _pokemonBonusTutorPoints(normalized));
  }

  return normalized;

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




function _ensurePokemonBuildChoiceState(build) {

  if (!build || typeof build !== "object") return;
  build.poke_edge_choices = _normalizePokeEdgeChoices(build.poke_edge_choices);

}


function _pokemonPokeEdgeVariantMap() {

  return {
    "Skill Improvement": [
      "Skill Improvement (Acrobatics)",
      "Skill Improvement (Athletics)",
      "Skill Improvement (Charm)",
      "Skill Improvement (Combat)",
      "Skill Improvement (Command)",
      "Skill Improvement (Focus)",
      "Skill Improvement (General Ed)",
      "Skill Improvement (Guile)",
      "Skill Improvement (Intimidate)",
      "Skill Improvement (Intuition)",
      "Skill Improvement (Medicine Ed)",
      "Skill Improvement (Occult Ed)",
      "Skill Improvement (Perception)",
      "Skill Improvement (Pokémon Ed)",
      "Skill Improvement (Stealth)",
      "Skill Improvement (Survival)",
      "Skill Improvement (Technology Ed)",
    ],
    "Capability Training": [
      "Capability Training (Power)",
      "Capability Training (High Jump)",
      "Capability Training (Long Jump)",
    ],
    "Advanced Mobility": [
      "Advanced Mobility (Overland)",
      "Advanced Mobility (Sky)",
      "Advanced Mobility (Swim)",
      "Advanced Mobility (Levitate)",
      "Advanced Mobility (Burrow)",
      "Advanced Mobility (Teleporter)",
    ],
    "Basic Ranged Attacks": [
      "Basic Ranged Attacks (Firestarter)",
      "Basic Ranged Attacks (Fountain)",
      "Basic Ranged Attacks (Freezer)",
      "Basic Ranged Attacks (Guster)",
      "Basic Ranged Attacks (Materializer)",
      "Basic Ranged Attacks (Zapper)",
    ],
  };

}


function _pokemonPokeEdgeVariants(baseName) {

  return _pokemonPokeEdgeVariantMap()[String(baseName || "").trim()] || [];

}


function _pokemonConnectedAbilityChoices(build) {

  const names = Array.isArray(build?.abilities) ? build.abilities : [];
  return names
    .map((abilityName) => {
      const moveName = _pokemonConnectedMoveNameForAbility(abilityName);
      return moveName ? { abilityName, moveName } : null;
    })
    .filter(Boolean);

}


function _pokemonConnectedMoveNameForAbility(abilityName) {

  const entry = _getAbilityDetail(abilityName);
  const text = [entry?.effect, entry?.effect_2, entry?.rules, entry?.description]
    .map((value) => _cleanDetailText(value))
    .filter(Boolean)
    .join(" ");
  if (!text) return "";
  const match = text.match(/Connection\s*-\s*[“"]?([^.”"\n]+?)[”"]?(?:\.|\s|$)/i);
  return match ? String(match[1] || "").replace(/\s+/g, " ").trim() : "";

}


function _pokemonAdvancedConnectionFreeMoves(build) {

  _ensurePokemonBuildChoiceState(build);
  const configured = new Set((build?.poke_edge_choices?.advanced_connection || []).map((name) => _normalizeSearchText(name)));
  const connectedAbilities = _pokemonConnectedAbilityChoices(build);
  const selectedMoves = new Set((Array.isArray(build?.moves) ? build.moves : []).map((name) => _normalizeMoveKey(name)));
  const freeMoves = new Set();
  connectedAbilities.forEach(({ abilityName, moveName }) => {
    if (!configured.has(_normalizeSearchText(abilityName))) return;
    const moveKey = _normalizeMoveKey(moveName);
    if (moveKey && selectedMoves.has(moveKey)) freeMoves.add(moveKey);
  });
  return freeMoves;

}


function _pokemonMoveSlotLimit(build) {

  const abilities = Array.isArray(build?.abilities) ? build.abilities : [];
  const hasClusterMind = abilities.some((name) => _normalizeSearchText(name) === "cluster mind");
  return hasClusterMind ? 8 : 6;

}


function _pokemonEffectiveMoveCount(build) {

  const moves = Array.isArray(build?.moves) ? build.moves : [];
  return Math.max(0, moves.length - _pokemonAdvancedConnectionFreeMoves(build).size);

}


function _pokemonUnderdogLessonOptions(speciesEntry, build) {

  _ensurePokemonBuildChoiceState(build);
  const evolutionName = String(build?.poke_edge_choices?.underdog_lessons?.evolution || "").trim();
  const evolutionEntry = _getPokemonSpeciesEntry(evolutionName);
  if (!speciesEntry || !evolutionEntry) {
    return { evolutionEntry: null, natural: new Set(), tm: new Set(), tutor: new Set() };
  }
  const availability = _pokemonMoveSourceAvailability(evolutionEntry, build?.level || 1);
  const selectedMoves = _normalizeStringList(build?.poke_edge_choices?.underdog_lessons?.moves);
  const natural = new Set();
  const tm = new Set();
  const tutor = new Set();
  selectedMoves.forEach((moveName) => {
    const moveKey = _normalizeMoveKey(moveName);
    if (!moveKey) return;
    if (availability.natural.has(moveKey)) natural.add(moveKey);
    if (availability.tm.has(moveKey)) tm.add(moveKey);
    if (availability.tutor.has(moveKey)) tutor.add(moveKey);
  });
  return { evolutionEntry, natural, tm, tutor };

}



function _normalizeNatureKey(name) {

  return String(name || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");

}



function _natureProfile(name) {

  const key = _normalizeNatureKey(name);

  if (!key) return null;

  const match = POKEMON_NATURES.find((entry) => _normalizeNatureKey(entry[0]) === key);

  if (!match) return null;

  return {
    name: match[0],
    modifiers: { ...match[1] },
    raise: match[2],
    lower: match[3],
  };

}



function _pokemonNatureAdjustedStats(speciesEntry, build) {

  const stored = _pokemonBuildStatMap(speciesEntry, build);

  const profile = _natureProfile(build?.nature);

  const statMode = _normalizePokemonStatMode(build?.stat_mode);

  const preNature = { ...stored };

  const effective = { ...stored };

  if (profile?.modifiers) {
    if (statMode === "post_nature") {
      Object.entries(profile.modifiers).forEach(([key, amount]) => {
        preNature[key] = Math.max(1, Number(stored[key] || 0) - Number(amount || 0));
      });
    } else {
      Object.entries(profile.modifiers).forEach(([key, amount]) => {
        effective[key] = Math.max(1, Number(stored[key] || 0) + Number(amount || 0));
      });
    }
  }

  return {
    stored,
    preNature,
    effective,
    profile,
    statMode,
  };

}



function _normalizeInventoryPayload(inventory) {

  const source = inventory && typeof inventory === "object" ? inventory : {};
  const normalizeItems = (items) =>
    Array.isArray(items)
      ? items.map((entry) => ({
          name: String(entry?.name || "").trim(),
          qty: String(entry?.qty || "").trim(),
          cost: String(entry?.cost || "").trim(),
          desc: String(entry?.desc || "").trim(),
        }))
      : [];

  return {
    key_items: normalizeItems(source.key_items),
    pokemon_items: normalizeItems(source.pokemon_items),
  };

}



function _normalizeAdvancementChoices(choices) {

  const source = choices && typeof choices === "object" ? choices : {};
  const allowed = new Set(["stats", "feature", "edges"]);
  const out = { 5: "stats", 10: "stats", 20: "stats", 30: "stats", 40: "stats" };

  Object.keys(out).forEach((key) => {

    const value = String(source[key] || out[key]).trim().toLowerCase();

    out[key] = allowed.has(value) ? value : out[key];

  });

  return out;

}



function _snapshotCharacterState(source = characterState) {

  return {
    profile: source.profile,
    class_ids: Array.isArray(source.class_ids) ? source.class_ids : [],
    class_id: source.class_id,
    features: _asStringArray(source.features),
    edges: _asStringArray(source.edges),
    poke_edges: _asStringArray(source.poke_edges),
    poke_edge_order: Array.isArray(source.poke_edge_order) ? source.poke_edge_order.slice() : [],
    feature_order: Array.isArray(source.feature_order) ? source.feature_order.slice() : [],
    edge_order: Array.isArray(source.edge_order) ? source.edge_order.slice() : [],
    skills: source.skills,
    stats: source.stats,
    skill_budget: source.skill_budget,
    skill_budget_auto: source.skill_budget_auto,
    skill_edge_non_skill_count: source.skill_edge_non_skill_count,
    skill_background: source.skill_background,
    skill_background_edit: source.skill_background_edit,
    advancement_choices: source.advancement_choices,
    step_by_step: source.step_by_step,
    allow_warnings: source.allow_warnings,
    guided_mode: source.guided_mode,
    content_scope: source.content_scope,
    feature_search: source.feature_search,
    edge_search: source.edge_search,
    poke_edge_search: source.poke_edge_search,
    feature_tag_filter: source.feature_tag_filter,
    feature_class_filter: source.feature_class_filter,
    edge_class_filter: source.edge_class_filter,
    class_status_filter: source.class_status_filter,
    feature_group_mode: source.feature_group_mode,
    edge_group_mode: source.edge_group_mode,
    poke_edge_group_mode: source.poke_edge_group_mode,
    feature_sort_mode: source.feature_sort_mode,
    edge_sort_mode: source.edge_sort_mode,
    poke_edge_sort_mode: source.poke_edge_sort_mode,
    feature_status_filter: source.feature_status_filter,
    edge_status_filter: source.edge_status_filter,
    poke_edge_status_filter: source.poke_edge_status_filter,
    feature_filter_available: source.feature_filter_available,
    feature_filter_close: source.feature_filter_close,
    feature_filter_unavailable: source.feature_filter_unavailable,
    feature_filter_blocked: source.feature_filter_blocked,
    edge_filter_available: source.edge_filter_available,
    edge_filter_close: source.edge_filter_close,
    edge_filter_unavailable: source.edge_filter_unavailable,
    edge_filter_blocked: source.edge_filter_blocked,
    poke_edge_filter_available: source.poke_edge_filter_available,
    poke_edge_filter_close: source.poke_edge_filter_close,
    poke_edge_filter_unavailable: source.poke_edge_filter_unavailable,
    poke_edge_filter_blocked: source.poke_edge_filter_blocked,
    override_prereqs: source.override_prereqs,
    feature_slots_override: source.feature_slots_override,
    list_density: source.list_density,
    planner_collapsed: source.planner_collapsed,
    planner_targets: Array.isArray(source.planner_targets) ? source.planner_targets : [],
    planner_targets_expanded: source.planner_targets_expanded,
    training_type: source.training_type,
    extras: Array.isArray(source.extras) ? source.extras : [],
    pokemon_builds: Array.isArray(source.pokemon_builds) ? source.pokemon_builds : [],
    inventory: source.inventory,
    extras_search: source.extras_search,
    inventory_search: source.inventory_search,
    extras_catalog_search: source.extras_catalog_search,
    extras_catalog_scope: source.extras_catalog_scope,
    inventory_catalog_search: source.inventory_catalog_search,
    inventory_catalog_category: source.inventory_catalog_category,
    inventory_catalog_type: source.inventory_catalog_type,
    inventory_catalog_kind: source.inventory_catalog_kind,
    glossary_query: source.glossary_query,
    glossary_category: source.glossary_category,
    glossary_open: source.glossary_open,
    pokemon_team_search: source.pokemon_team_search,
    pokemon_team_limit: source.pokemon_team_limit,
    pokemon_team_auto_level: source.pokemon_team_auto_level,
    pokemon_team_autofill: source.pokemon_team_autofill,
    data_policy: _normalizeDataPolicy(source.data_policy),
  };

}



function _normalizeCharacterPayload(source) {

  const raw = source && typeof source === "object" ? source : {};
  const profileSource = raw.profile && typeof raw.profile === "object" ? raw.profile : {};
  const trainerLevel = _normalizeInteger(profileSource.level, 1, 1, 50);
  const autoLevel = raw.pokemon_team_auto_level !== undefined ? !!raw.pokemon_team_auto_level : false;

  const classIds = _normalizeStringList(raw.class_ids);
  const primaryClass = String(raw.class_id || classIds[0] || "").trim();
  if (primaryClass && !classIds.includes(primaryClass)) classIds.unshift(primaryClass);

  const payload = {
    profile: {
      name: String(profileSource.name || "").trim(),
      played_by: String(profileSource.played_by || "").trim(),
      age: String(profileSource.age || "").trim(),
      sex: String(profileSource.sex || "").trim(),
      height: String(profileSource.height || "").trim(),
      weight: String(profileSource.weight || "").trim(),
      money: String(profileSource.money || "").trim(),
      region: String(profileSource.region || "").trim(),
      concept: String(profileSource.concept || "").trim(),
      background: String(profileSource.background || "").trim(),
      level: trainerLevel,
    },
    class_ids: classIds.slice(0, 4),
    class_id: primaryClass,
    features: _normalizeStringList(raw.features),
    edges: _normalizeStringList(raw.edges),
    poke_edges: _normalizeStringList(raw.poke_edges),
    poke_edge_order: _normalizeStringList(raw.poke_edge_order),
    feature_order: _normalizeStringList(raw.feature_order),
    edge_order: _normalizeStringList(raw.edge_order),
    skills: _normalizeTextMap(raw.skills),
    stats: {
      hp: _normalizeInteger(raw.stats?.hp, 10, 0),
      atk: _normalizeInteger(raw.stats?.atk, 5, 0),
      def: _normalizeInteger(raw.stats?.def, 5, 0),
      spatk: _normalizeInteger(raw.stats?.spatk, 5, 0),
      spdef: _normalizeInteger(raw.stats?.spdef, 5, 0),
      spd: _normalizeInteger(raw.stats?.spd, 5, 0),
    },
    skill_budget: raw.skill_budget === null ? null : _normalizeInteger(raw.skill_budget, 0, 0),
    skill_budget_auto: !!raw.skill_budget_auto,
    skill_edge_non_skill_count: _normalizeInteger(raw.skill_edge_non_skill_count, 0, 0),
    skill_background:
      raw.skill_background && typeof raw.skill_background === "object"
        ? {
            adept: String(raw.skill_background.adept || "").trim(),
            novice: String(raw.skill_background.novice || "").trim(),
            pathetic: _normalizeStringList(raw.skill_background.pathetic),
          }
        : { adept: "", novice: "", pathetic: [] },
    skill_background_edit: !!raw.skill_background_edit,
    advancement_choices: _normalizeAdvancementChoices(raw.advancement_choices),
    step_by_step: !!raw.step_by_step,
    allow_warnings: !!raw.allow_warnings,
    guided_mode: !!raw.guided_mode,
    content_scope: raw.content_scope === "all" ? "all" : "official",
    feature_search: String(raw.feature_search || ""),
    edge_search: String(raw.edge_search || ""),
    poke_edge_search: String(raw.poke_edge_search || ""),
    feature_tag_filter: String(raw.feature_tag_filter || ""),
    feature_class_filter: String(raw.feature_class_filter || ""),
    edge_class_filter: String(raw.edge_class_filter || ""),
    class_status_filter: String(raw.class_status_filter || "all"),
    feature_group_mode: String(raw.feature_group_mode || "none"),
    edge_group_mode: String(raw.edge_group_mode || "none"),
    poke_edge_group_mode: String(raw.poke_edge_group_mode || "none"),
    feature_sort_mode: String(raw.feature_sort_mode || "progressive"),
    edge_sort_mode: String(raw.edge_sort_mode || "progressive"),
    poke_edge_sort_mode: String(raw.poke_edge_sort_mode || "progressive"),
    feature_status_filter: String(raw.feature_status_filter || "all"),
    edge_status_filter: String(raw.edge_status_filter || "all"),
    poke_edge_status_filter: String(raw.poke_edge_status_filter || "all"),
    feature_filter_available: raw.feature_filter_available !== false,
    feature_filter_close: raw.feature_filter_close !== false,
    feature_filter_unavailable: raw.feature_filter_unavailable !== false,
    feature_filter_blocked: raw.feature_filter_blocked !== false,
    edge_filter_available: raw.edge_filter_available !== false,
    edge_filter_close: raw.edge_filter_close !== false,
    edge_filter_unavailable: raw.edge_filter_unavailable !== false,
    edge_filter_blocked: raw.edge_filter_blocked !== false,
    poke_edge_filter_available: raw.poke_edge_filter_available !== false,
    poke_edge_filter_close: raw.poke_edge_filter_close !== false,
    poke_edge_filter_unavailable: raw.poke_edge_filter_unavailable !== false,
    poke_edge_filter_blocked: raw.poke_edge_filter_blocked !== false,
    override_prereqs: !!raw.override_prereqs,
    feature_slots_override:
      raw.feature_slots_override && typeof raw.feature_slots_override === "object" ? { ...raw.feature_slots_override } : {},
    list_density: raw.list_density === "compact" ? "compact" : "comfortable",
    planner_collapsed: !!raw.planner_collapsed,
    planner_targets: Array.isArray(raw.planner_targets) ? raw.planner_targets.slice() : [],
    planner_targets_expanded: !!raw.planner_targets_expanded,
    training_type: String(raw.training_type || "").trim(),
    extras: Array.isArray(raw.extras) ? raw.extras.slice() : [],
    pokemon_builds: Array.isArray(raw.pokemon_builds)
      ? raw.pokemon_builds
          .map((build) => _normalizePokemonBuild(build, trainerLevel, autoLevel))
          .filter((build) => build.species || build.name)
      : [],
    inventory: _normalizeInventoryPayload(raw.inventory),
    extras_search: String(raw.extras_search || ""),
    inventory_search: String(raw.inventory_search || ""),
    extras_catalog_search: String(raw.extras_catalog_search || ""),
    extras_catalog_scope: String(raw.extras_catalog_scope || "class"),
    inventory_catalog_search: String(raw.inventory_catalog_search || ""),
    inventory_catalog_category: String(raw.inventory_catalog_category || ""),
    inventory_catalog_type: String(raw.inventory_catalog_type || ""),
    inventory_catalog_kind: String(raw.inventory_catalog_kind || "all"),
    glossary_query: String(raw.glossary_query || ""),
    glossary_category: String(raw.glossary_category || "all"),
    glossary_open: !!raw.glossary_open,
    pokemon_team_search: String(raw.pokemon_team_search || ""),
    pokemon_team_limit: _normalizeInteger(raw.pokemon_team_limit, 6, 1, 12),
    pokemon_team_auto_level: autoLevel,
    pokemon_team_autofill: raw.pokemon_team_autofill !== false,
    data_policy: _normalizeDataPolicy(raw.data_policy),
  };

  const orderedFeatures = payload.feature_order.filter((name) => payload.features.includes(name));
  payload.features.forEach((name) => {
    if (!orderedFeatures.includes(name)) orderedFeatures.push(name);
  });
  payload.feature_order = orderedFeatures;

  const orderedEdges = payload.edge_order.filter((name) => payload.edges.includes(name));
  payload.edges.forEach((name) => {
    if (!orderedEdges.includes(name)) orderedEdges.push(name);
  });
  payload.edge_order = orderedEdges;

  const orderedPokeEdges = payload.poke_edge_order.filter((name) => payload.poke_edges.includes(name));
  payload.poke_edges.forEach((name) => {
    if (!orderedPokeEdges.includes(name)) orderedPokeEdges.push(name);
  });
  payload.poke_edge_order = orderedPokeEdges;

  return payload;

}



function _applyNormalizedCharacterPayload(payload) {

  const parsed = _normalizeCharacterPayload(payload);

  characterState.profile = { ...characterState.profile, ...parsed.profile };
  characterState.class_ids = parsed.class_ids.slice();
  characterState.class_id = parsed.class_id;
  characterState.features = new Set(parsed.features);
  characterState.edges = new Set(parsed.edges);
  characterState.poke_edges = new Set(parsed.poke_edges);
  characterState.poke_edge_order = parsed.poke_edge_order.slice();
  characterState.feature_order = parsed.feature_order.slice();
  characterState.edge_order = parsed.edge_order.slice();
  characterState.skills = { ...characterState.skills, ...parsed.skills };
  characterState.stats = { ...characterState.stats, ...parsed.stats };
  characterState.skill_budget = parsed.skill_budget;
  characterState.skill_budget_auto = parsed.skill_budget_auto;
  characterState.skill_edge_non_skill_count = parsed.skill_edge_non_skill_count;
  characterState.skill_background = { ...characterState.skill_background, ...parsed.skill_background };
  characterState.skill_background_edit = parsed.skill_background_edit;
  characterState.advancement_choices = { ...parsed.advancement_choices };
  characterState.step_by_step = parsed.step_by_step;
  characterState.allow_warnings = parsed.allow_warnings;
  characterState.guided_mode = parsed.guided_mode;
  characterState.content_scope = parsed.content_scope;
  characterState.feature_search = parsed.feature_search;
  characterState.edge_search = parsed.edge_search;
  characterState.poke_edge_search = parsed.poke_edge_search;
  characterState.feature_tag_filter = parsed.feature_tag_filter;
  characterState.feature_class_filter = parsed.feature_class_filter;
  characterState.edge_class_filter = parsed.edge_class_filter;
  characterState.class_status_filter = parsed.class_status_filter;
  characterState.feature_group_mode = parsed.feature_group_mode;
  characterState.edge_group_mode = parsed.edge_group_mode;
  characterState.poke_edge_group_mode = parsed.poke_edge_group_mode;
  characterState.feature_sort_mode = parsed.feature_sort_mode;
  characterState.edge_sort_mode = parsed.edge_sort_mode;
  characterState.poke_edge_sort_mode = parsed.poke_edge_sort_mode;
  characterState.feature_status_filter = parsed.feature_status_filter;
  characterState.edge_status_filter = parsed.edge_status_filter;
  characterState.poke_edge_status_filter = parsed.poke_edge_status_filter;
  characterState.feature_filter_available = parsed.feature_filter_available;
  characterState.feature_filter_close = parsed.feature_filter_close;
  characterState.feature_filter_unavailable = parsed.feature_filter_unavailable;
  characterState.feature_filter_blocked = parsed.feature_filter_blocked;
  characterState.edge_filter_available = parsed.edge_filter_available;
  characterState.edge_filter_close = parsed.edge_filter_close;
  characterState.edge_filter_unavailable = parsed.edge_filter_unavailable;
  characterState.edge_filter_blocked = parsed.edge_filter_blocked;
  characterState.poke_edge_filter_available = parsed.poke_edge_filter_available;
  characterState.poke_edge_filter_close = parsed.poke_edge_filter_close;
  characterState.poke_edge_filter_unavailable = parsed.poke_edge_filter_unavailable;
  characterState.poke_edge_filter_blocked = parsed.poke_edge_filter_blocked;
  characterState.override_prereqs = parsed.override_prereqs;
  characterState.feature_slots_override = { ...parsed.feature_slots_override };
  characterState.list_density = parsed.list_density;
  characterState.planner_collapsed = parsed.planner_collapsed;
  characterState.planner_targets = parsed.planner_targets.slice();
  characterState.planner_targets_expanded = parsed.planner_targets_expanded;
  characterState.training_type = parsed.training_type;
  characterState.extras = parsed.extras.slice();
  characterState.pokemon_builds = parsed.pokemon_builds.slice();
  characterState.inventory = _normalizeInventoryPayload(parsed.inventory);
  characterState.extras_search = parsed.extras_search;
  characterState.inventory_search = parsed.inventory_search;
  characterState.extras_catalog_search = parsed.extras_catalog_search;
  characterState.extras_catalog_scope = parsed.extras_catalog_scope;
  characterState.inventory_catalog_search = parsed.inventory_catalog_search;
  characterState.inventory_catalog_category = parsed.inventory_catalog_category;
  characterState.inventory_catalog_type = parsed.inventory_catalog_type;
  characterState.inventory_catalog_kind = parsed.inventory_catalog_kind;
  characterState.glossary_query = parsed.glossary_query;
  characterState.glossary_category = parsed.glossary_category;
  characterState.glossary_open = parsed.glossary_open;
  characterState.pokemon_team_search = parsed.pokemon_team_search;
  characterState.pokemon_team_limit = parsed.pokemon_team_limit;
  characterState.pokemon_team_auto_level = parsed.pokemon_team_auto_level;
  characterState.pokemon_team_autofill = parsed.pokemon_team_autofill;
  characterState.data_policy = _normalizeDataPolicy(parsed.data_policy);

  if (!getCharacterStepOrder().includes(characterStep)) {
    characterStep = "profile";
  }

  if (window.PTUCharacterState?.ensureOrderedSet) {
    window.PTUCharacterState.ensureOrderedSet(characterState, "poke_edges", "poke_edge_order");
  }

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

  _applyNormalizedCharacterPayload(_snapshotCharacterState());

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

    {
      name: "OurosPTU-signature.txt",
      content: `Digitally signed by ${EXPORT_SIGNATURE}\r\nGenerated by AutoPTU Character Builder\r\n`,
    },

  ];


  if (extrasRows.length) files.push({ name: "Fancy PTU Extras.csv", content: stringifyCsv(extrasRows) });



  if (inventoryRows.length) files.push({ name: "Fancy PTU Inventory.csv", content: stringifyCsv(inventoryRows) });



  if (combatRows.length) files.push({ name: "Fancy PTU Combat.csv", content: stringifyCsv(combatRows) });







  try {

    const zipBlob = buildZip(files);

    _downloadBlobFile("Fancy_PTU_Export.zip", zipBlob);

  } catch {

    files.forEach((file) => {

      const blob = new Blob([file.content], {
        type: file.name.toLowerCase().endsWith(".txt") ? "text/plain;charset=utf-8;" : "text/csv;charset=utf-8;",
      });

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







function fallbackMoveAnimUrl(moveAnim) {



  return null;



}







function typeIconFromCache(typeName) {



  return pokeApiCacheGet(pokeApiTypeIconCache, typeName);



}

let _pokemonTeamRerenderQueued = false;

function _queuePokemonTeamRerender() {
  if (_pokemonTeamRerenderQueued) return;
  _pokemonTeamRerenderQueued = true;
  requestAnimationFrame(() => {
    _pokemonTeamRerenderQueued = false;
    if (characterStep === "pokemon-team") {
      renderCharacterPokemonTeam();
    }
  });
}

function _speciesSpriteUrl(name) {
  const value = String(name || "").trim();
  if (!value) return "";
  return `/api/sprites/pokemon?name=${encodeURIComponent(value)}`;
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







function showDetailTooltip(anchorEl, title, description, note = "") {



  const titleText = String(title || "").trim();



  const descriptionHtml = tooltipHtmlFromText(description);



  if (!titleText || !descriptionHtml) {



    return;



  }



  const html = `



    <div class="tooltip-title">${escapeHtml(titleText)}</div>



    <div class="tooltip-section">${descriptionHtml}</div>

    ${note ? `<div class="tooltip-note">${escapeHtml(note)}</div>` : ""}



  `;



  showTooltipContent(anchorEl, html, "detail");



}







function _setTooltipAttrs(el, title, body, note = "") {



  if (!el) return;



  const safeTitle = escapeAttr(title || "");



  const safeBody = escapeAttr(body || "");

  const safeNote = escapeAttr(note || "");



  if (!safeTitle || !safeBody) return;



  el.setAttribute("data-tooltip-title", safeTitle);



  el.setAttribute("data-tooltip-body", safeBody);



  if (safeNote) el.setAttribute("data-tooltip-note", safeNote);



}







function bindCharacterTooltips() {



  if (!charContentEl) return;



  const targets = charContentEl.querySelectorAll("[data-tooltip-title][data-tooltip-body]");



  targets.forEach((target) => {



    target.addEventListener("mouseenter", () => {



      const title = target.getAttribute("data-tooltip-title") || target.textContent || "Details";



      const body = target.getAttribute("data-tooltip-body") || "";



      const note = target.getAttribute("data-tooltip-note") || "";



      showDetailTooltip(target, title, body, note);



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



      `${bestEffectDescription(meta, ability, "Ability description unavailable.")}\n\n${_builderSourceNote("ability", meta)}`



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



    addTerm(move, `Move: ${move}`, `${tooltipBody}\n\n${_builderSourceNote("move", meta)}`);



  }







  const item = String(event?.item || "").trim();



  if (item) {



    const meta = pokeApiCacheGet(pokeApiItemMetaCache, item);



    if (!pokeApiCacheHas(pokeApiItemMetaCache, item)) {



      ensureItemMeta(item).then(() => scheduleRerender());



    }



    addTerm(item, `Item: ${item}`, `${meta?.effect || "Item description unavailable."}\n\n${_builderSourceNote("item", meta)}`);



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



      const note = target.getAttribute("data-tooltip-note") || "";



      showDetailTooltip(target, title, body, note);



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



  if (multiSideRandomMode && hasRosterCsv) {



    delete payload.roster_csv;



    hasRosterCsv = false;



    notifyUI("warn", "Ignoring roster CSV for multi-side random mode; generating all sides procedurally.", 2800);



  }



  if (hasRosterCsv && battleRosterCsvMeta && !payload.roster_csv) {



    payload.team_size = Math.max(1, Number(battleRosterCsvMeta.teamSize || teamSize));



    payload.active_slots = Math.max(1, Math.min(Number(payload.active_slots || 1), payload.team_size));



    payload.roster_csv = battleRosterCsvText;



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



  if (hasRosterCsv && (mode === "random" || mode === "ai-random") && !multiSideRandomMode) {



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



  viewManuallyAdjusted = false;



  lastGridSize = null;



  lastProcessedLogSize = null;



  lastProcessedLogToken = "";



  logClearOffset = 0;



  fxQueue = Promise.resolve();



  hideTooltip();



  render();



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



  return String(teamLabel || "neutral")



    .replace(/[_-]+/g, " ")



    .replace(/\b\w/g, (match) => match.toUpperCase());



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



  return {



    typeKey: typeKey || "neutral",



    style: TYPE_ANIM_STYLE[typeKey] || "pulse",



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







function attachSprite(container, url, alt) {



  if (!shouldRequestSprite(url)) {



    return false;



  }



  const img = document.createElement("img");



  img.src = url;



  img.alt = alt || "sprite";



  img.addEventListener(



    "error",



    () => {



      spriteMissUntil.set(url, Date.now() + SPRITE_RETRY_MS);



      img.remove();



    },



    { once: true }



  );



  container.appendChild(img);



  return true;



}







function attachTurnSprite(container, url, alt) {



  container.classList.add("placeholder");



  if (!url || !shouldRequestSprite(url)) {



    return false;



  }



  const img = document.createElement("img");



  img.src = url;



  img.alt = alt || "sprite";



  img.addEventListener(



    "error",



    () => {



      spriteMissUntil.set(url, Date.now() + SPRITE_RETRY_MS);



      img.remove();



      container.classList.add("placeholder");



    },



    { once: true }



  );



  img.addEventListener(



    "load",



    () => {



      container.classList.remove("placeholder");



    },



    { once: true }



  );



  container.appendChild(img);



  return true;



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



    startButton.disabled = !lifecycle.canStartBattle;



    endTurnButton.disabled = !lifecycle.canEndTurn;



    aiStepButton.disabled = !lifecycle.canAiStep;



    aiAutoButton.disabled = !lifecycle.canToggleAuto;



    undoButton.disabled = !lifecycle.canUndo;



    aiAutoButton.textContent = lifecycle.autoActive ? "Auto On" : "Auto Off";



  }



  return lifecycle;



}







function renderAiModelMath(source) {



  if (!aiModelMathEl) return;



  const math = source?.math || source?.ai_model?.math || null;



  if (!math) {



    aiModelMathEl.textContent = "Model score: -";



    return;



  }



  const score = Number.isFinite(Number(math.score)) ? Number(math.score).toFixed(3) : "-";



  const threshold = Number.isFinite(Number(math.threshold)) ? Number(math.threshold).toFixed(3) : "-";



  const updates = Number.isFinite(Number(math.updates_since_snapshot)) ? Number(math.updates_since_snapshot) : 0;



  aiModelMathEl.textContent = `Model score: ${score}/${threshold} | updates ${updates}`;



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



    option.textContent = `${model.id} (${tag})`;



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



  if (!state || state.status !== "ok") {



    hideTooltip();



    gridEl.innerHTML = "";



    gridCellByKey = new Map();



    combatantListEl.innerHTML = "";



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



  renderCombatants();



  renderDetails();



  renderTrainerDetails();



  renderAIDiagnostics();



  renderPartyBar();



  renderMoves();



  renderLog();



  renderPrompts();



  processMoveAnimations();



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



      if (hazardEntries.length) {



        cell.classList.add("has-hazard");



        const hazardWrap = document.createElement("div");



        hazardWrap.className = "hazard-stack";



        hazardEntries.slice(0, 4).forEach((entry) => {



          const badge = document.createElement("div");



          badge.className = `hazard-badge ${entry.kind}`;



          const normalized = normalizePokeKey(entry.name);



          const glyph =



            (entry.kind === "trap" ? TRAP_GLYPHS[normalized] : HAZARD_GLYPHS[normalized]) ||



            String(entry.name || "?").charAt(0).toUpperCase();



          badge.textContent = entry.layers > 1 ? `${glyph}${entry.layers}` : glyph;



          badge.title = `${entry.name}${entry.layers > 1 ? ` x${entry.layers}` : ""}`;



          hazardWrap.appendChild(badge);



        });



        cell.appendChild(hazardWrap);



      }



      const occupantId = occupantMap[key];



      const combatant = occupantId ? combatantsById.get(occupantId) : null;



      if (occupantId) {



        if (combatant) {



          const teamVisual = getTeamVisual(teamKeyForCombatant(combatant));



          cell.classList.add("occupied");



          cell.style.setProperty("--team-primary", teamVisual.primary);



          cell.style.setProperty("--team-secondary", teamVisual.secondary);



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



  const hazardText = hazardEntries.length



    ? hazardEntries



        .map((entry) => `${entry.name}${entry.layers > 1 ? ` x${entry.layers}` : ""}`)



        .join(", ")



    : "None";



  const parts = [



    `Tile ${x},${y}`,



    `Type: ${typeLabel}`,



    `Effect: ${typeDesc}`,



    `Blocker: ${isBlocked ? "Yes" : "No"}`,



    `Occupant: ${occupant ? occupant.name || occupant.species || occupant.id : "None"}`,



    `Hazards: ${hazardText}`,



  ];



  selectedTileInfoEl.textContent = parts.join(" | ");



  selectedTileInfoEl.onmouseenter = () => {



    showDetailTooltip(selectedTileInfoEl, `Tile ${x},${y}`, buildTileTooltip(meta, x, y));



  };



  selectedTileInfoEl.onmouseleave = () => {



    scheduleTooltipHide();



  };



  if (terrainInfoEl) {



    const label = normalizeFieldName(terrainNameValue(state?.terrain)) || "None";



    terrainInfoEl.textContent = `Terrain: ${label} | Tile: ${typeLabel}`;



  }



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



  if (!diag || typeof diag !== "object") {



    panel.textContent = "Rules-safe AI diagnostics will appear during AI turns.";



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



      ? { pace: 1.16, fx: 1.15, wideZoomDelta: -0.12, settleMs: 220 }



      : profile === "fastcast"



        ? { pace: 0.82, fx: 0.78, wideZoomDelta: -0.05, settleMs: 80 }



        : { pace: 1.0, fx: 1.0, wideZoomDelta: -0.08, settleMs: 140 };



  if (mode === "slow") {



    return { ...base, profile, panMs: 420, actorLockMs: 260, moveLeadMs: 250, moveFollowFactor: 0.62 };



  }



  if (mode === "fast") {



    return { ...base, profile, panMs: 180, actorLockMs: 90, moveLeadMs: 90, moveFollowFactor: 0.42 };



  }



  return { ...base, profile, panMs: 300, actorLockMs: 170, moveLeadMs: 150, moveFollowFactor: 0.52 };



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



  const captureAll = isCinematicAutoActive();



  const overloaded = pendingAnimationJobs > 18;



  const moveBatch = captureAll ? moveEvents : moveEvents.slice(-6);



  let abilityBatch = captureAll ? abilityEvents : abilityEvents.slice(-8);



  if (!captureAll && overloaded) {



    abilityBatch = abilityBatch.filter((event) => animationEventPriority(event) >= 2);



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



  drawMovementArrow(fromCoord, toCoord, 1100);



  return new Promise((resolve) => {



    window.setTimeout(() => {



      cinematicPhaseActive = false;



      resolve();



    }, 170);



  });



}







function triggerGridShake(intensity = 1) {



  if (!gridWrapEl) return;



  const amount = Math.max(1, Math.min(6, Math.round(intensity * 2.6)));



  gridWrapEl.style.setProperty("--shake", `${amount}px`);



  gridWrapEl.classList.remove("fx-grid-shake");



  void gridWrapEl.offsetWidth;



  gridWrapEl.classList.add("fx-grid-shake");



  window.setTimeout(() => {



    gridWrapEl?.classList.remove("fx-grid-shake");



  }, 230);



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



  const scale = Math.max(0.95, Math.min(1.75, 1.04 + cinematicFxScale() * 0.22 + intensity * 0.08));



  const frameDisplayW = Math.round(



    Math.max(cellBase * 0.85, Math.min(cellBase * 2.15, cellBase * scale * (atlas.frameW / frameBase)))



  );



  const frameDisplayH = Math.round(



    Math.max(cellBase * 0.85, Math.min(cellBase * 2.15, cellBase * scale * (atlas.frameH / frameBase)))



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



  const travelMs = Math.max(160, Math.min(420, Math.hypot(endX - startX, endY - startY) * 0.42));



  el.style.transition = `left ${travelMs}ms cubic-bezier(0.22, 1, 0.36, 1), top ${travelMs}ms cubic-bezier(0.22, 1, 0.36, 1), opacity 90ms ease-out`;



  requestAnimationFrame(() => {



    el.style.opacity = "1";



    requestAnimationFrame(() => {



      el.style.left = `${endX}px`;



      el.style.top = `${endY}px`;



    });



  });



  if (atlas.frames <= 1) {



    return { totalMs: Math.max(1200, travelMs + 320), stop: () => {} };



  }



  const frameMs = Math.max(24, Math.round(1000 / 28));



  const settleMs = 260;



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



  const usingMoveSheet = !!moveAnimUrl;



  if (!usingMoveSheet) {



    return;



  }



  let moveAnimSprite = null;



  let moveAnimPlayback = null;



  if (moveAnimUrl) {



    moveAnimSprite = document.createElement("div");



    moveAnimSprite.className = "fx-impact-moveanim";



    moveAnimSprite.style.left = `${fromX}px`;



    moveAnimSprite.style.top = `${fromY}px`;



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



            { startX: fromX, startY: fromY, endX: toX, endY: toY, sourceRect, targetRect }



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



  const defaultMoveAnimUrl = null;



  const moveAnimUrl = moveAnimUrlFromCache(moveName);



  const moveAnimPromise = moveAnimUrl



    ? Promise.resolve(moveAnimUrl)



    : moveName



      ? ensureMoveAnimAsset(moveName).then((url) => url || null)



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



      }, Math.max(50, Math.min(cine.moveLeadMs, duration * cine.moveFollowFactor)));



    }



  }



  showAttackFootprint(actor, target, moveMeta, Math.max(850, duration + 260));



  sourceCell.classList.add("fx-caster");



  sourceCell.classList.add("fx-caster-cast");



  (targetCell || sourceCell).classList.add("fx-target");



  (targetCell || sourceCell).classList.add("fx-hit-cell");



  triggerGridShake(intensity);







  return new Promise((resolve) => {



    Promise.resolve(moveAnimPromise)



      .catch(() => null)



      .then((resolvedMoveAnimUrl) => {



        const usingMoveSheet = !!resolvedMoveAnimUrl;



        if (!usingMoveSheet) {



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



          return;



        }



        let projectile = null;



        const delayMs = Math.max(110, Math.min(260, duration * 0.35));



        setTimeout(() => {



          projectile?.remove();



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



        }, delayMs);



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







function renderCombatants() {



  combatantListEl.innerHTML = "";



  const hideFainted = !!hideFaintedToggle?.checked;



  state.combatants.forEach((combatant) => {



    const teamKey = teamKeyForCombatant(combatant);



    if (combatantTeamFilter !== "all" && teamKey !== combatantTeamFilter) {



      return;



    }



    if (hideFainted && combatant.fainted) {



      return;



    }



    const teamVisual = getTeamVisual(teamKey);



    const card = document.createElement("div");



    card.className = "combatant-card";



    card.style.setProperty("--team-primary", teamVisual.primary);



    card.style.setProperty("--team-secondary", teamVisual.secondary);



    if (combatant.id === selectedId) {



      card.classList.add("active");



    }



    if (combatant.fainted) {



      card.classList.add("fainted");



    }



    attachSprite(card, combatant.sprite_url, combatant.name);



    if (combatant.active && !combatant.fainted) {



      const badge = document.createElement("div");



      badge.className = "combatant-badge";



      badge.textContent = "Active";



      card.appendChild(badge);



    }



    const text = document.createElement("div");



    text.className = "combatant-meta";



    const nameLine = document.createElement("div");



    nameLine.className = "combatant-name";



    nameLine.textContent = `${combatant.marker} ${combatant.name}`;



    const hpLine = document.createElement("div");



    hpLine.className = "combatant-hp";



    hpLine.textContent = `${formatTeamLabel(teamKeyForCombatant(combatant))} | HP ${combatant.hp}/${combatant.max_hp}`;



    text.appendChild(nameLine);



    text.appendChild(hpLine);



    const statusRow = document.createElement("div");



    statusRow.className = "combatant-status-row";



    const statusEntries = (combatant.statuses || []).slice(0, 3);



    statusEntries.forEach((status) => {



      const chip = document.createElement("span");



      const visual = statusVisualKey(status);



      chip.className = `combatant-status-chip status-${visual}`;



      chip.setAttribute("data-status", visual);



      chip.textContent = String(status);



      statusRow.appendChild(chip);



    });



    if (statusEntries.length) {



      text.appendChild(statusRow);



    }



    card.appendChild(text);



    const hpBar = document.createElement("div");



    hpBar.className = "combatant-hpbar";



    const hpFill = document.createElement("div");



    hpFill.className = "combatant-hpfill";



    const ratio = combatant.max_hp ? combatant.hp / combatant.max_hp : 0;



    hpFill.style.width = `${Math.max(0, Math.min(1, ratio)) * 100}%`;



    hpBar.appendChild(hpFill);



    card.appendChild(hpBar);



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







function chipHtml({ text, iconUrl = null, iconBadge = null, tooltipTitle = "", tooltipBody = "", tooltipNote = "", className = "", dataStatus = "" }) {



  const safeText = escapeHtml(text);



  const safeTooltipTitle = escapeAttr(tooltipTitle || "");



  const safeTooltipBody = escapeAttr(tooltipBody || "");

  const safeTooltipNote = escapeAttr(tooltipNote || "");



  const safeClass = String(className || "").trim();



  const safeStatus = String(dataStatus || "").trim();



  const tooltipAttrs =



    safeTooltipBody && safeTooltipTitle



      ? ` data-tooltip-title="${safeTooltipTitle}" data-tooltip-body="${safeTooltipBody}"${safeTooltipNote ? ` data-tooltip-note="${safeTooltipNote}"` : ""}`



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



      tooltipNote: _builderSourceNote("ability", meta),



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



    return chipHtml({



      text: itemName,



      iconUrl: meta?.icon_url || null,



      iconBadge: meta?.icon_url ? null : "I",



      tooltipTitle: `Item: ${itemName}`,



      tooltipBody: meta?.effect || "Description unavailable.",



      tooltipNote: _builderSourceNote("item", meta),



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



      showDetailTooltip(icon, `Item: ${item.name}`, meta?.effect || "Item description unavailable.", _builderSourceNote("item", meta));



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



      const note = target.getAttribute("data-tooltip-note") || "";



      showDetailTooltip(target, title, body, note);



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



    <div class="details-row">Items: ${itemMarkup}</div>



    <div class="details-row">CS: ${escapeHtml(formatCombatStages(combatant.combat_stages))}</div>



    <div class="details-row">Stats: ${escapeHtml(formatStats(combatant.stats))}</div>



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







function renderMoves() {



  moveListEl.innerHTML = "";



  const combatant = state.combatants.find((c) => c.id === selectedId);



  if (!combatant) {



    return;



  }



  const canAct = !!state.current_actor_is_player;



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



    const targetOptions = (state.combatants || []).map((entry) => ({



      id: entry.id,



      label: `${entry.name} (${formatTeamLabel(entry.team)})`,



    }));



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



        showDetailTooltip(btn, `Item: ${name}`, tooltipText, _builderSourceNote("item", meta));



      });



      btn.addEventListener("mouseleave", () => {



        scheduleTooltipHide();



      });



      itemList.appendChild(btn);



    });



    itemSection.appendChild(itemList);



    moveListEl.appendChild(itemSection);



  }







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



      render();



    });



    btn.addEventListener("mouseenter", () => {



      clearTooltipHideTimer();



      showDetailTooltip(btn, `Move: ${move.name}`, descriptionText, _builderSourceNote("move", move));



    });



    btn.addEventListener("mouseleave", () => {



      scheduleTooltipHide();



    });



    moveListEl.appendChild(btn);



  });



}







function renderLog() {



  const log = state.log || [];



  if (logClearOffset > log.length) {



    logClearOffset = 0;



  }



  const rawEvents = log.slice(logClearOffset).slice(-520);



  const lines = [];



  let lastLine = null;



  let lastRound = null;



  rawEvents.forEach((event) => {



    const { text, category, prefix } = renderEventLine(event);



    if (!passesLogFilter(category)) return;



    const round = Number(event?.round);



    if (Number.isFinite(round) && round !== lastRound) {



      if (logFilterPhase?.checked ?? true) {



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



  const shouldAutoScroll = logAutoScrollToggle?.checked ?? true;



  const maxScrollTop = Math.max(0, logEl.scrollHeight - logEl.clientHeight);



  const wasNearBottom = maxScrollTop - logEl.scrollTop <= 24;



  logEl.classList.toggle("compact", !!logCompactToggle?.checked);



  logEl.innerHTML = "";



  merged.slice(-240).forEach((line) => {



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



  prompts.forEach((prompt) => {



    const wrapper = document.createElement("div");



    wrapper.className = "prompt-item";



    const label = document.createElement("div");



    label.textContent = `${prompt.label} from ${prompt.actor_id || "unknown"} (vs ${prompt.defender_id || "?"})`;



    const details = document.createElement("div");



    if (prompt.detail) {



      details.textContent = String(prompt.detail || "");



    } else {



      details.textContent = `Move: ${prompt.move || "-"} Trigger: ${prompt.trigger_move || "-"}`;



    }



    const choice = document.createElement("div");



    choice.className = "prompt-choice";



    const yes = document.createElement("button");



    yes.textContent = prompt.yes_label || "Yes";



    const no = document.createElement("button");



    no.textContent = prompt.no_label || "No";



    const id = prompt.id;



    const update = () => {



      const value = promptAnswers[id];



      yes.classList.toggle("active", value === true);



      no.classList.toggle("active", value === false);



    };



    yes.addEventListener("click", () => {



      promptAnswers[id] = true;



      update();



    });



    no.addEventListener("click", () => {



      promptAnswers[id] = false;



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



  await loadMasterData({ fullCatalog: true });



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







function hasFullPokemonBuilderData() {
  return !!(
    masterData &&
    Array.isArray(masterData?.pokemon?.moves) &&
    masterData.pokemon.moves.length > 0 &&
    Array.isArray(masterData?.pokemon?.abilities) &&
    masterData.pokemon.abilities.length > 0 &&
    learnsetData &&
    moveRecordMap &&
    evolutionMinLevelData &&
    pokemonMoveSourceData
  );
}

async function loadMasterData(options = {}) {



  const fullCatalog = !!options.fullCatalog;



  if (fullCatalog) {



    if (hasFullPokemonBuilderData()) return;



  } else if (masterData) {



    return;



  }



  const needsMasterCatalog = () =>



    !masterData ||



    !Array.isArray(masterData?.pokemon?.moves) ||



    masterData.pokemon.moves.length === 0 ||



    !Array.isArray(masterData?.pokemon?.abilities) ||



    masterData.pokemon.abilities.length === 0;



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



  if (!fullCatalog) {



    if (!masterData) moveRecordMap = null;



    return;



  }



  if (!masterData && window.__AUTO_PTU_MASTER_DATA) {



    masterData = window.__AUTO_PTU_MASTER_DATA;



    const list = masterData?.pokemon?.moves || [];



    moveRecordMap = new Map(list.map((entry) => [_normalizeMoveKey(entry.name), entry]));


  }



  if (!learnsetData && window.__AUTO_PTU_LEARNSET_DATA) {



    learnsetData = window.__AUTO_PTU_LEARNSET_DATA;



  }



  if (!characterData && location.protocol !== "file:") {



    try {



      const payload = await api("/api/character_creation");



      const hasClasses = Array.isArray(payload?.classes) && payload.classes.length > 0;



      characterData = hasClasses ? payload : null;



    } catch {



      characterData = null;



    }



  }



  if (!pokemonMoveSourceData && window.__AUTO_PTU_POKEMON_MOVE_SOURCES) {



    pokemonMoveSourceData = window.__AUTO_PTU_POKEMON_MOVE_SOURCES;



  }



  if (needsMasterCatalog()) {



    try {



      const response = await fetch("master_dataset.json");



      if (response.ok) {



        masterData = await response.json();



        const list = masterData?.pokemon?.moves || [];



        moveRecordMap = new Map(list.map((entry) => [_normalizeMoveKey(entry.name), entry]));



      }



    } catch {



      // Keep embedded/cached data if present.



    }



  }



  if (needsMasterCatalog() && location.protocol === "file:") {



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



      const list = masterData?.pokemon?.moves || [];



      moveRecordMap = new Map(list.map((entry) => [_normalizeMoveKey(entry.name), entry]));



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



  if (!pokemonMoveSourceData) {



    try {



      const moveSourceResponse = await fetch("pokemon_move_sources.json");



      if (moveSourceResponse.ok) {



        pokemonMoveSourceData = await moveSourceResponse.json();



      }



    } catch {



      pokemonMoveSourceData = pokemonMoveSourceData || null;



    }



  }



  if (!pokemonMoveSourceData && location.protocol === "file:") {



    try {



      await new Promise((resolve, reject) => {



        const existing = document.querySelector('script[data-fallback-move-sources="true"]');



        if (existing) {



          resolve();



          return;



        }



        const script = document.createElement("script");



        script.src = "pokemon_move_sources.embed.js";



        script.dataset.fallbackMoveSources = "true";



        script.onload = () => resolve();



        script.onerror = () => reject(new Error("Embedded move source dataset failed to load."));



        document.head.appendChild(script);



      });



    } catch {



      // ignore fallback failures



    }



    if (window.__AUTO_PTU_POKEMON_MOVE_SOURCES) {



      pokemonMoveSourceData = window.__AUTO_PTU_POKEMON_MOVE_SOURCES;



    }



  }



  if (!evolutionMinLevelData) {



    try {



      const evolutionResponse = await fetch("evolution_min_levels.json");



      if (evolutionResponse.ok) {



        evolutionMinLevelData = await evolutionResponse.json();



      }



    } catch {



      evolutionMinLevelData = evolutionMinLevelData || null;



    }



  }



  if (!masterData) moveRecordMap = null;



}







function renderCharacterStep() {



  if (!charContentEl) return;



  if (!characterData) {



    charContentEl.textContent = "Loading character data...";



    return;



  }

  _destroySortables();

  _applyNormalizedCharacterPayload(_snapshotCharacterState());

  let guidedNode = null;

  if (characterState.guided_mode) {

    const guided = document.createElement("div");

    guided.className = "char-guided-box";

    const warnings = _validationWarnings();
    const nextStep = getRecommendedCharacterStep();

    const title = document.createElement("div");
    title.className = "char-guided-title";
    title.textContent = "Guided Flow";
    guided.appendChild(title);

    const body = document.createElement("div");
    body.textContent = warnings[0] || `Required steps are in good shape. Next suggested stop: ${getCharacterStepLabel(nextStep)}.`;
    guided.appendChild(body);

    const meta = document.createElement("div");
    meta.className = "char-guided-meta";
    meta.textContent = `Current step: ${getCharacterStepLabel(characterStep)}`;
    guided.appendChild(meta);

    if (nextStep && nextStep !== characterStep) {
      const actions = document.createElement("div");
      actions.className = "char-guided-actions";
      const nextBtn = document.createElement("button");
      nextBtn.type = "button";
      nextBtn.textContent = `Open ${getCharacterStepLabel(nextStep)}`;
      nextBtn.addEventListener("click", () => goToCharacterStep(nextStep));
      actions.appendChild(nextBtn);
      guided.appendChild(actions);
    }

    guidedNode = guided;

  }


  if (characterStep === "profile") {



    renderCharacterProfile();



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

    renderCharacterPokeEdges();


  } else if (characterStep === "extras") {



    renderCharacterExtras();



  } else if (characterStep === "inventory") {



    renderCharacterInventory();



  } else if (characterStep === "pokemon-team") {



    renderCharacterPokemonTeam();



  } else {

    renderCharacterSummary();

  }

  if (guidedNode) {

    charContentEl.prepend(guidedNode);

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



  _renderBuilderPanel(charContentEl);



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

        const level = _normalizeInteger(input.value, 1, 1, 50);

        characterState.profile[field.key] = level;

        input.value = String(level);

        if (characterState.pokemon_team_auto_level) {


          const pokemonLevel = trainerToPokemonLevel(level);



          _ensurePokemonBuilds().forEach((build) => {



            build.level = Number.isFinite(pokemonLevel) ? pokemonLevel : 1;



          });



        }

        saveCharacterToStorage();

        renderCharacterProfile();

        return;

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
  const order = getCharacterStepOrder();

  const validity = getStepValidity();

  let maxIndex = order.length - 1;
  if (characterState.step_by_step) {
    maxIndex = 0;
    for (let i = 0; i < order.length; i += 1) {
      const step = order[i];
      if (!validity[step]) {
        maxIndex = i;
        break;
      }
      maxIndex = Math.min(order.length - 1, i + 1);
    }
  }
  const recommended = getRecommendedCharacterStep();

  charStepButtons.forEach((btn) => {

    const step = btn.getAttribute("data-step");

    const index = order.indexOf(step);

    btn.disabled = characterState.step_by_step && index > maxIndex;
    btn.dataset.stepState = validity[step] ? "complete" : step === recommended ? "next" : "open";
    btn.title = `${getCharacterStepLabel(step)}${validity[step] ? " - complete" : step === recommended ? " - next recommended step" : ""}`;

  });

}

function getCharacterStepOrder() {

  return CHARACTER_STEP_SEQUENCE.slice();

}

function getCharacterStepLabel(step) {

  return CHARACTER_STEP_META[step]?.label || String(step || "");

}

function getRecommendedCharacterStep() {

  const order = getCharacterStepOrder();
  const validity = getStepValidity();
  return order.find((step) => !validity[step]) || "summary";

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



    skills: skillsValid,



    advancement: true,



    class: classValid,



    features: featuresValid && featureCountOk,



    edges: edgesValid && edgeCountOk,



    extras: true,

    inventory: true,

    "pokemon-team": true,

    "poke-edges": true,

    summary: profileValid && skillsValid && classValid && featuresValid && edgesValid && featureCountOk && edgeCountOk,


  };



}







function renderStepGuide() {



  if (!characterState.step_by_step) return;



  const order = getCharacterStepOrder();


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



  stepPill.textContent = `Step ${currentIndex + 1}/${order.length}: ${getCharacterStepLabel(characterStep)}`;


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

    "poke-edges":

      "Assign optional Poke Edges after your team is in place. Click Add to build the list quickly, then reorder only the ones you actually plan to track.",

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



  prev.textContent = currentIndex <= 0 ? "Previous Step" : `Previous: ${getCharacterStepLabel(order[currentIndex - 1])}`;


  prev.disabled = currentIndex <= 0;



  prev.addEventListener("click", () => {



    if (currentIndex <= 0) return;



    goToCharacterStep(order[currentIndex - 1]);


  });



  const next = document.createElement("button");



  next.textContent = currentIndex >= order.length - 1 ? "Finish" : `Next: ${getCharacterStepLabel(order[currentIndex + 1])}`;


  const canAdvance = allowWarnings || validity[characterStep];



  next.disabled = !canAdvance;



  next.addEventListener("click", () => {



    if (!canAdvance) return;



    if (currentIndex >= order.length - 1) return;



    goToCharacterStep(order[currentIndex + 1]);


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



      _setTooltipAttrs(btn, `Class: ${entry.name}`, tooltipBody, _builderSourceNote("class", { ...entry, ...(classNode || {}) }));



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



              .join("\n"),

            _builderSourceNote("feature", node)



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



  _appendLearningPanel(charContentEl, "How To Read Features", [



    "Available means you can take it now. Close means you are one requirement away. Locked or Unavailable means you still need more setup.",



    "Read the short summary first, then use the prerequisite checklist if you want the exact rule path.",



    "Hover a feature name for a plain-language note, a quick example, and its source/version.",



  ]);







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



  const sortSelect = document.createElement("select");



  sortSelect.className = "item-target-select";



  [



    { id: "progressive", label: "Sort: Progressive" },



    { id: "alpha", label: "Sort: Alphabetical" },



  ].forEach((opt) => {



    const option = document.createElement("option");



    option.value = opt.id;



    option.textContent = opt.label;



    if ((characterState.feature_sort_mode || "progressive") === opt.id) option.selected = true;



    sortSelect.appendChild(option);



  });



  sortSelect.addEventListener("change", () => {



    characterState.feature_sort_mode = sortSelect.value;



    renderCharacterFeatures();



  });



  const sortWrap = document.createElement("label");



  sortWrap.className = "char-inline-toggle";



  sortWrap.appendChild(sortSelect);



  filterRow.appendChild(sortWrap);



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



          const featureSummary = _builderQuickSummary("feature", node.effects || "", node);



          _setTooltipAttrs(



            title,



            `Feature: ${node.name}`,



            [



              node.prerequisites ? `Prerequisites: ${node.prerequisites}` : "",



              node.frequency || "",



              node.tags || "",



              featureSummary ? `Quick read: ${featureSummary}` : "",



              node.effects || "",



              ..._builderBasicsLines("feature", node.effects || "", node).slice(0, 2),



              _builderExampleText("feature", node),



            ]



              .filter(Boolean)



              .join("\n"),

            _builderSourceNote("feature", node)



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



          const quickRead = document.createElement("div");



          quickRead.className = "char-row-meta";



          quickRead.textContent = featureSummary ? `Quick read: ${featureSummary}` : "";



          const effects = document.createElement("div");



          effects.className = "char-feature-meta";



          effects.textContent = node.effects || "";



          _attachKeywordTooltip(effects, effects.textContent);



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



          if (quickRead.textContent) body.appendChild(quickRead);



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



          _appendRelationChipRow(body, "Unlocks Next", _unlockTargetsForEntry("feature", node.name, 3));



          _appendRelationChipRow(body, "Related Picks", _relatedTargetsForEntry("feature", node, 3));



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



      const featureSummary = _builderQuickSummary("feature", entry.effects || "", entry);



      _setTooltipAttrs(



        title,



        `Feature: ${entry.name}`,



        [



          entry.prerequisites ? `Prerequisites: ${entry.prerequisites}` : "",



          entry.frequency || "",



          entry.tags || "",



          featureSummary ? `Quick read: ${featureSummary}` : "",



          entry.effects || "",



          ..._builderBasicsLines("feature", entry.effects || "", entry).slice(0, 2),



          _builderExampleText("feature", entry),



        ].filter(Boolean).join("\n"),



        _builderSourceNote("feature", entry)



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



      meta.textContent = [entry.tags].filter(Boolean).join(" | ");



      const quickRead = document.createElement("div");



      quickRead.className = "char-row-meta";



      quickRead.textContent = featureSummary ? `Quick read: ${featureSummary}` : "";



      const effects = document.createElement("div");



      effects.className = "char-feature-meta";



      effects.textContent = entry.effects || "";



      _attachKeywordTooltip(effects, effects.textContent);



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



      if (quickRead.textContent) body.appendChild(quickRead);



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



      _appendRelationChipRow(body, "Unlocks Next", _unlockTargetsForEntry("feature", entry.name, 3));

      _appendRelationChipRow(body, "Related Picks", _relatedTargetsForEntry("feature", entry, 3));

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



        _sortCatalogEntries(groups.get(key) || [], {



          selectedSet: characterState.features,



          mode: characterState.feature_sort_mode || "progressive",



          getStatus: (candidate) => prereqStatus(candidate?.prerequisites, "feature"),



        }).forEach((entry) => {



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



  _appendLearningPanel(charContentEl, "How To Read Edges", [



    "Edges are smaller support picks. Read the quick summary first, then the missing-prerequisite line if you want the exact rule gate.",



    "Connections helps you see what a rule depends on and what it tends to pair with next.",



    "Hover an edge name for a plain-language note, a quick example, and its source/version.",



  ]);







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



  const sortSelect = document.createElement("select");



  sortSelect.className = "item-target-select";



  [



    { id: "progressive", label: "Sort: Progressive" },



    { id: "alpha", label: "Sort: Alphabetical" },



  ].forEach((opt) => {



    const option = document.createElement("option");



    option.value = opt.id;



    option.textContent = opt.label;



    if ((characterState.edge_sort_mode || "progressive") === opt.id) option.selected = true;



    sortSelect.appendChild(option);



  });



  sortSelect.addEventListener("change", () => {



    characterState.edge_sort_mode = sortSelect.value;



    renderCharacterEdges();



  });



  const sortWrap = document.createElement("label");



  sortWrap.className = "char-inline-toggle";



  sortWrap.appendChild(sortSelect);



  filterRow.appendChild(sortWrap);



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



      const edgeSummary = _builderQuickSummary("edge", entry.effects || "", entry);



      _setTooltipAttrs(



        title,



        `Edge: ${entry.name}`,



        [



          entry.prerequisites ? `Prerequisites: ${entry.prerequisites}` : "",



          entry.tags || "",



          edgeSummary ? `Quick read: ${edgeSummary}` : "",



          entry.effects || "",



          ..._builderBasicsLines("edge", entry.effects || "", entry).slice(0, 2),



          _builderExampleText("edge", entry),



        ].filter(Boolean).join("\n"),



        _builderSourceNote("edge", entry)



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



      meta.textContent = entry.tags || "";



      const quickRead = document.createElement("div");



      quickRead.className = "char-row-meta";



      quickRead.textContent = edgeSummary ? `Quick read: ${edgeSummary}` : "";



      const effects = document.createElement("div");



      effects.className = "char-edge-meta";



      effects.textContent = entry.effects || "";



      _attachKeywordTooltip(effects, effects.textContent);



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



      if (quickRead.textContent) body.appendChild(quickRead);



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



      _appendRelationChipRow(body, "Unlocks Next", _unlockTargetsForEntry("edge", entry.name, 3));



      _appendRelationChipRow(body, "Related Picks", _relatedTargetsForEntry("edge", entry, 3));



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



        _sortCatalogEntries(groups.get(key) || [], {



          selectedSet: characterState.edges,



          mode: characterState.edge_sort_mode || "progressive",



          getStatus: (candidate) => prereqStatus(candidate?.prerequisites, "edge"),



        }).forEach((entry) => {



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



  _ensureCharacterPokeEdgesState();



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



  guide.textContent = `Optional step: assign Poke Edges after your team is set. Selected: ${characterState.poke_edges.size}.`;


  charContentEl.appendChild(guide);



  _appendLearningPanel(charContentEl, "How To Read Poke Edges", [



    "Poke Edges are optional polish picks for an individual Pokemon, so browse freely and only add the ones you actually plan to track.",



    "Available means legal now. Close means the Pokemon is almost there. The missing line tells you exactly what still has to change.",



    "Hover a Poke Edge name for a plain-language note, a quick example, and its source/version.",



  ]);



  if (window.PTUCharacterState?.ensureOrderedSet) {



    window.PTUCharacterState.ensureOrderedSet(characterState, "poke_edges", "poke_edge_order");



  }







  charContentEl.appendChild(createStatusLegend());



  const selectedSummary = document.createElement("div");

  selectedSummary.className = "char-summary-box";

  const orderedEdges = characterState.poke_edge_order?.length ? characterState.poke_edge_order : Array.from(characterState.poke_edges);

  selectedSummary.textContent = orderedEdges.length ? `Current order: ${orderedEdges.join(" | ")}` : "No Poke Edges selected yet.";

  charContentEl.appendChild(selectedSummary);






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



  const sortSelect = document.createElement("select");



  sortSelect.className = "item-target-select";



  [



    { id: "progressive", label: "Sort: Progressive" },



    { id: "alpha", label: "Sort: Alphabetical" },



  ].forEach((opt) => {



    const option = document.createElement("option");



    option.value = opt.id;



    option.textContent = opt.label;



    if ((characterState.poke_edge_sort_mode || "progressive") === opt.id) option.selected = true;



    sortSelect.appendChild(option);



  });



  sortSelect.addEventListener("change", () => {



    characterState.poke_edge_sort_mode = sortSelect.value;



    renderCharacterPokeEdges();



  });



  const sortWrap = document.createElement("label");



  sortWrap.className = "char-inline-toggle";



  sortWrap.appendChild(sortSelect);



  filterRow.appendChild(sortWrap);



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



    _sortCatalogEntries(filtered, {



      selectedSet: characterState.poke_edges,



      mode: characterState.poke_edge_sort_mode || "progressive",



      getStatus: (candidate) => prereqStatus(candidate?.prerequisites, "edge"),



    }).forEach((entry) => {



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



      const pokeEdgeSummary = _builderQuickSummary("poke edge", entry.effects || "", entry);



      _setTooltipAttrs(



        title,



        `Poke Edge: ${entry.name}`,



        [



          entry.prerequisites ? `Prerequisites: ${entry.prerequisites}` : "",



          _formatCostLabel(entry.cost),



          pokeEdgeSummary ? `Quick read: ${pokeEdgeSummary}` : "",



          entry.effects || "",



          ..._builderBasicsLines("poke edge", entry.effects || "", entry).slice(0, 2),



          _builderExampleText("poke edge", entry),



        ]



          .filter(Boolean)



          .join("\n"),

        _builderSourceNote("poke edge", entry)



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



      const quickRead = document.createElement("div");



      quickRead.className = "char-row-meta";



      quickRead.textContent = pokeEdgeSummary ? `Quick read: ${pokeEdgeSummary}` : "";



      const effects = document.createElement("div");



      effects.className = "char-edge-meta";



      effects.textContent = entry.effects || "";



      _attachKeywordTooltip(effects, effects.textContent);



      body.appendChild(title);



      body.appendChild(statusPill);



      if (meta.textContent) body.appendChild(meta);



      if (quickRead.textContent) body.appendChild(quickRead);



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



      empty.textContent = "No Poke Edges match your search/filters.";



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

        onMove: (name, direction) => {

          const ordered = (characterState.poke_edge_order || []).slice();

          const currentIndex = ordered.indexOf(name);

          if (currentIndex < 0) return;

          const targetIndex = currentIndex + Number(direction || 0);

          if (targetIndex < 0 || targetIndex >= ordered.length) return;

          const swap = ordered[targetIndex];

          ordered[targetIndex] = name;

          ordered[currentIndex] = swap;

          if (window.PTUCharacterState?.reorder) {

            window.PTUCharacterState.reorder(characterState, "poke_edges", "poke_edge_order", ordered);

          } else {

            characterState.poke_edge_order = ordered.slice();

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

  } else {

    charContentEl.appendChild(

      createSelectedPanel("Selected Poke Edges", orderedEdges, (name) => {

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



  catalogSearch.placeholder = "Search class features...";



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



    body.appendChild(title);



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



  search.placeholder = "Search extras...";



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



  catalogSearch.placeholder = "Search catalog...";



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



  search.placeholder = "Search inventory...";



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



      if (kindFilter === "pokeballs" && entry.category !== "Poke Balls") return;



      if (kindFilter === "equipment" && entry.category !== "Equipment") return;



      if (kindFilter === "held" && entry.category !== "Pokemon Stuff") return;



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



        [entry.prerequisites ? `Prerequisites: ${entry.prerequisites}` : "", entry.effects || ""].filter(Boolean).join("\n"),

        _builderSourceNote("item", entry)



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



      body.appendChild(title);



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



  _appendLearningPanel(charContentEl, "How To Read Team Legality", [



    "Set species and level first. Move, ability, and evolution legality all depend on those two fields.",



    "Fill from species pulls local defaults, but the builder still validates your final moves, abilities, and evolution stage after that.",



    "When something is illegal, the exact rule error stays visible and a plain-English note below it explains what to change.",



  ]);







  const policyPanel = document.createElement("div");

  policyPanel.className = "char-summary-box";

  const policyTitle = document.createElement("div");

  policyTitle.className = "char-section-subtitle";

  policyTitle.textContent = "Data Sources And Rulesets";

  policyPanel.appendChild(policyTitle);

  const policyBlurb = document.createElement("div");

  policyBlurb.className = "char-helper-text";

  policyBlurb.textContent =
    "This builder can mix packaged datasets. The selectors below only appear where multiple legality interpretations exist; the other rows make the active packaged source explicit.";

  policyPanel.appendChild(policyBlurb);

  _builderDataSourceRows().forEach((row) => {

    const entry = document.createElement("div");

    entry.className = "char-detail-card";

    const heading = document.createElement("div");

    heading.className = "char-detail-title";

    heading.textContent = row.label;

    entry.appendChild(heading);

    if (Array.isArray(row.options) && row.options.length > 1 && row.key) {

      const select = document.createElement("select");

      select.className = "char-select";

      row.options.forEach((option) => {

        const opt = document.createElement("option");

        opt.value = option.value;

        opt.textContent = option.label;

        if (option.value === row.value) opt.selected = true;

        select.appendChild(opt);

      });

      const applyPolicySelection = () => {

        characterState.data_policy = _normalizeDataPolicy({

          ...characterState.data_policy,

          [row.key]: select.value,

        });

        saveCharacterToStorage();

        renderCharacterStep();

      };

      select.addEventListener("change", applyPolicySelection);

      select.addEventListener("input", applyPolicySelection);

      entry.appendChild(select);

    }

    const sourceLine = document.createElement("div");

    sourceLine.className = "char-helper-text";

    sourceLine.textContent = `Source: ${row.source} | Version: ${row.version}`;

    entry.appendChild(sourceLine);

    if (row.notes) {

      const noteLine = document.createElement("div");

      noteLine.className = "char-helper-text";

      noteLine.textContent = row.notes;

      entry.appendChild(noteLine);

    }

    policyPanel.appendChild(entry);

  });

  charContentEl.appendChild(policyPanel);

  const builds = _ensurePokemonBuilds();



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



      if (autoLevelInput.checked) {



        const level = trainerToPokemonLevel(characterState.profile.level || 1);



        builds.forEach((build) => {



          build.level = Number.isFinite(level) ? level : 1;



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



    const speciesNames = (masterData?.pokemon?.species || []).map((entry) => entry.name);



    if (!speciesNames.length) {



      const build = _createPokemonBuildFromPrompt();



      if (!build) return;



      renderCharacterPokemonTeam();



      return;



    }



    openListPicker({



      title: "Add Pokemon",



      items: speciesNames,



      onSelect: (name) => {



        const speciesEntry = _getPokemonSpeciesEntry(name);



        const display = speciesEntry?.name || name;



        const level = trainerToPokemonLevel(characterState.profile.level || 1);



        _ensurePokemonBuilds().push({



          name: display,



          species: display,



          level,



          battle_side: "",



          moves: [],



          move_sources: {},



          abilities: [],



          items: [],



          poke_edges: [],



          tutor_points: 0,
          tutor_points_mode: "adjustment",



        });



        if (characterState.pokemon_team_autofill) {



          void _applyPokemonDefaults(builds[builds.length - 1], speciesEntry, false).then(() => {



            saveCharacterToStorage();



            renderCharacterPokemonTeam();



          });



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



  actionRow.appendChild(addBtn);



  actionRow.appendChild(importBtn);



  actionRow.appendChild(battleCsvBtn);



  actionRow.appendChild(submissionBtn);

  const ioNote = document.createElement("div");
  ioNote.className = "char-feature-meta";
  ioNote.textContent = "Save Project ZIP bundles builder JSON, team CSV, and trainer CSV. Team CSV can load by itself and AutoPTU will create an empty trainer shell.";



  actionRow.appendChild(clearBtn);



  charContentEl.appendChild(actionRow);
  charContentEl.appendChild(ioNote);







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



  ensureNatureDatalist();



  const speciesList = (masterData?.pokemon?.species || []).slice();



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
          ensureTypeIcon(typeName).then(() => _queuePokemonTeamRerender());
        }
        if (typeIcon) {
          const img = document.createElement("img");
          img.src = typeIcon;
          img.alt = typeName;
          img.loading = "lazy";
          token.appendChild(img);
        }
        const textNode = document.createElement("span");
        textNode.textContent = typeName;
        token.appendChild(textNode);
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



        const level = trainerToPokemonLevel(characterState.profile.level || 1);



        _ensurePokemonBuilds().push({



          name: entry.name,



          species: entry.name,



          level,



          battle_side: "",



          moves: [],



          move_sources: {},



          abilities: [],



          items: [],



          poke_edges: [],



          tutor_points: 0,
          tutor_points_mode: "adjustment",



        });



        if (characterState.pokemon_team_autofill) {



          void _applyPokemonDefaults(builds[builds.length - 1], entry, false).then(() => {



            saveCharacterToStorage();



            renderCharacterPokemonTeam();



          });



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







  if (!builds.length) {



    const empty = document.createElement("div");



    empty.className = "char-empty";



    empty.textContent = "No Pokemon added yet.";



    teamPanel.appendChild(empty);



  }







  builds.forEach((build, idx) => {



    const card = document.createElement("div");



    card.className = "char-summary-box";

    const heroSpeciesEntry = _getPokemonSpeciesEntry(build.species || build.name || "");
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
    const heroMeta = document.createElement("div");
    heroMeta.className = "char-poke-hero-meta";
    const heroTitle = document.createElement("div");
    heroTitle.className = "char-section-title";
    heroTitle.textContent = build.species || build.name || `Pokemon ${idx + 1}`;
    if (heroSpeciesEntry) {
      heroTitle.tabIndex = 0;
      heroTitle.style.cursor = "pointer";
      heroTitle.title = "Open species details";
      heroTitle.addEventListener("click", () => showSpeciesDetail(heroSpeciesEntry));
      heroTitle.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          showSpeciesDetail(heroSpeciesEntry);
        }
      });
    }
    heroMeta.appendChild(heroTitle);
    const heroSummary = document.createElement("div");
    heroSummary.className = "char-feature-meta";
    heroSummary.textContent = [
      (heroSpeciesEntry?.types || []).join(" | "),
      heroSpeciesEntry?.size ? `Size ${heroSpeciesEntry.size}` : "",
      _hasDisplayValue(heroSpeciesEntry?.weight) ? `Weight ${heroSpeciesEntry.weight}` : "",
    ].filter(Boolean).join(" | ");
    if (heroSummary.textContent) heroMeta.appendChild(heroSummary);
    const typeRow = document.createElement("div");
    typeRow.className = "char-poke-type-row";
    (heroSpeciesEntry?.types || []).forEach((typeName) => {
      const token = document.createElement("span");
      token.className = "char-type-token";
      const typeIcon = typeIconFromCache(typeName);
      if (!typeIcon && !pokeApiCacheHas(pokeApiTypeIconCache, typeName)) {
        ensureTypeIcon(typeName).then(() => _queuePokemonTeamRerender());
      }
      if (typeIcon) {
        const img = document.createElement("img");
        img.src = typeIcon;
        img.alt = typeName;
        img.loading = "lazy";
        token.appendChild(img);
      }
      const textNode = document.createElement("span");
      textNode.textContent = typeName;
      token.appendChild(textNode);
      typeRow.appendChild(token);
    });
    if (typeRow.childElementCount) heroMeta.appendChild(typeRow);
    if (heroSpeciesEntry) {
      const sourceMeta = document.createElement("div");
      sourceMeta.className = "char-source-note";
      sourceMeta.textContent = _builderSourceNote("species", heroSpeciesEntry);
      heroMeta.appendChild(sourceMeta);
    }
    hero.appendChild(heroMeta);
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

    levelInput.disabled = false;

    levelInput.addEventListener("input", () => {

      if (characterState.pokemon_team_auto_level) {

        characterState.pokemon_team_auto_level = false;

        levelInput.disabled = false;

      }

      const typedLevel = Number(levelInput.value || 1);

      build.level = Number.isFinite(typedLevel) ? typedLevel : 1;

      saveCharacterToStorage();



    });



    const commitPokemonLevel = () => {

      if (characterState.pokemon_team_auto_level) {

        characterState.pokemon_team_auto_level = false;

        levelInput.disabled = false;

      }

      const nextLevel = Math.max(1, Math.min(100, Number(levelInput.value || build.level || 1)));


      build.level = Number.isFinite(nextLevel) ? nextLevel : 1;



      levelInput.value = String(build.level);



      saveCharacterToStorage();



      renderCharacterPokemonTeam();



    };



    levelInput.addEventListener("change", commitPokemonLevel);



    levelInput.addEventListener("blur", commitPokemonLevel);



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



    speciesInput.addEventListener("change", async () => {



      const speciesEntry = _getPokemonSpeciesEntry(build.species || build.name || "");



      if (characterState.pokemon_team_autofill && speciesEntry) {



        await _applyPokemonDefaults(build, speciesEntry, false);



      }



      saveCharacterToStorage();



      renderCharacterPokemonTeam();



    });



    speciesField.appendChild(speciesInput);



    const natureField = document.createElement("label");



    natureField.className = "char-field";



    natureField.textContent = "Nature";



    _setTooltipAttrs(
      natureField,
      "Nature",
      "Nature is previewed using the same additive stat modifiers the engine applies in battle. Builder stat overrides are treated as pre-nature values."
    );



    const natureInput = document.createElement("input");



    natureInput.type = "text";



    natureInput.setAttribute("list", "pokemon-nature-list");



    natureInput.placeholder = "Nature";



    natureInput.value = build.nature || "";



    natureInput.addEventListener("input", () => {

      build.nature = natureInput.value;

      saveCharacterToStorage();

    });



    natureInput.addEventListener("change", () => {

      const profile = _natureProfile(natureInput.value);

      build.nature = profile?.name || String(natureInput.value || "").trim();

      natureInput.value = build.nature || "";

      saveCharacterToStorage();

      renderCharacterPokemonTeam();

    });



    natureField.appendChild(natureInput);



    const statModeField = document.createElement("label");



    statModeField.className = "char-field";



    statModeField.textContent = "Stat Mode";



    _setTooltipAttrs(
      statModeField,
      "Stat Mode",
      "Pre-nature means the stored stats are before applying nature modifiers. Post-nature means the stored stats already include nature, and the builder reverses the nature for budgeting and legality."
    );



    const statModeSelect = document.createElement("select");



    [
      { value: "pre_nature", label: "Pre-Nature Stats" },
      { value: "post_nature", label: "Post-Nature Stats" },
    ].forEach((entry) => {
      const option = document.createElement("option");
      option.value = entry.value;
      option.textContent = entry.label;
      statModeSelect.appendChild(option);
    });



    statModeSelect.value = _normalizePokemonStatMode(build.stat_mode);



    statModeSelect.addEventListener("change", () => {
      build.stat_mode = _normalizePokemonStatMode(statModeSelect.value);
      saveCharacterToStorage();
      renderCharacterPokemonTeam();
    });



    statModeField.appendChild(statModeSelect);



    const tutorPointsField = document.createElement("label");



    tutorPointsField.className = "char-field";



    tutorPointsField.textContent = "Tutor Point Adjustment";



    _setTooltipAttrs(
      tutorPointsField,
      "Tutor Point Adjustment",
      "Pokemon Tutor Points start at 1, increase at level 5 and every multiple of 5 after that, then add Poke Edge bonuses. This field is an adjustment on top of the level-based total; use negatives for points spent elsewhere and positives for granted bonus points."
    );



    const tutorPointsInput = document.createElement("input");



    tutorPointsInput.type = "number";



    tutorPointsInput.min = "-99";



    tutorPointsInput.step = "1";



    tutorPointsInput.value = String(_normalizeInteger(build.tutor_points, 0, -999, 999));



    tutorPointsInput.addEventListener("input", () => {
      build.tutor_points = _normalizeInteger(tutorPointsInput.value, 0, -999, 999);
      build.tutor_points_mode = "adjustment";
      saveCharacterToStorage();
      renderCharacterPokemonTeam();
    });



    const tutorPointsMeta = document.createElement("div");



    tutorPointsMeta.className = "char-feature-meta";



    const tutorBase = _pokemonBaseTutorPoints(build.level || 1);
    const tutorBonus = _pokemonBonusTutorPoints(build);
    const tutorAdjustment = _normalizeInteger(build.tutor_points, 0, -999, 999);
    tutorPointsMeta.textContent = `Base from level: ${tutorBase} | Adjustment: ${tutorAdjustment >= 0 ? `+${tutorAdjustment}` : tutorAdjustment} | Bonus from Poke Edges: ${tutorBonus} | Exported total: ${_pokemonEffectiveTutorPoints(build)}`;



    tutorPointsField.appendChild(tutorPointsInput);



    tutorPointsField.appendChild(tutorPointsMeta);



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



      "Check if this Pokemon was caught in the wild. Required when the species is evolved but below its normal evolution level (e.g. Venusaur at level 5)."



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



    grid.appendChild(natureField);



    grid.appendChild(statModeField);



    grid.appendChild(tutorPointsField);



    grid.appendChild(sideField);



    grid.appendChild(caughtField);



    card.appendChild(grid);







    const speciesEntry = _getPokemonSpeciesEntry(build.species || build.name || "");



    if (speciesEntry) {



      const info = document.createElement("div");



      info.className = "char-feature-meta";



      const types = (speciesEntry.types || []).join(" / ") || "-";



      const statRows = _pokemonBuildStatRows(speciesEntry, build);
      const statMap = Object.fromEntries(statRows.map((row) => [row.key, row.base]));



      const statLine = `HP ${statMap.hp ?? "-"} | Atk ${statMap.atk ?? "-"} | Def ${statMap.def ?? "-"} | SpA ${statMap.spatk ?? "-"} | SpD ${statMap.spdef ?? "-"} | Spd ${statMap.spd ?? "-"}`;



      info.textContent = `${types} | Size ${speciesEntry.size || "-"} | Weight ${speciesEntry.weight || "-"} | ${statLine}`;



      card.appendChild(info);



      const natureProfile = _natureProfile(build.nature);



      if (build.nature) {

        const natureInfo = document.createElement("div");

        natureInfo.className = "char-feature-meta";

        natureInfo.textContent = natureProfile
          ? `Nature: ${natureProfile.name} | +${natureProfile.raise === "hp" ? "HP" : natureProfile.raise === "atk" ? "Atk" : natureProfile.raise === "def" ? "Def" : natureProfile.raise === "spatk" ? "SpA" : natureProfile.raise === "spdef" ? "SpD" : "Spd"} | -${natureProfile.lower === "hp" ? "HP" : natureProfile.lower === "atk" ? "Atk" : natureProfile.lower === "def" ? "Def" : natureProfile.lower === "spatk" ? "SpA" : natureProfile.lower === "spdef" ? "SpD" : "Spd"}`
          : `Nature: ${build.nature} (unrecognized; no preview modifiers applied)`;

        card.appendChild(natureInfo);

      }



      const statModeInfo = document.createElement("div");



      statModeInfo.className = "char-feature-meta";



      statModeInfo.textContent =
        _normalizePokemonStatMode(build.stat_mode) === "post_nature"
          ? "Stat mode: stored as post-nature values."
          : "Stat mode: stored as pre-nature values.";



      card.appendChild(statModeInfo);



      if (!build.stats || typeof build.stats !== "object") {



        build.stats = {};



      }



      const statTitle = document.createElement("div");



      statTitle.className = "char-feature-meta";



      statTitle.textContent = "Pokemon Stats";



      card.appendChild(statTitle);



      const statGrid = document.createElement("div");



      statGrid.className = "char-field-grid";



      const statBudget = document.createElement("div");



      statBudget.className = "char-summary-box";



      const derivedStatsBox = document.createElement("div");



      derivedStatsBox.className = "char-summary-box";



      const updatePokemonStatBudget = () => {



        const spent = _pokemonStatPointsSpent(speciesEntry, build);



        const available = _pokemonStatPointBudget(build.level || 1, speciesEntry, build);



        const remaining = available - spent;



        statBudget.textContent = `Stat Points: ${spent}/${available} used${remaining >= 0 ? ` | ${remaining} remaining` : ` | ${Math.abs(remaining)} over budget`}`;



        const derived = _pokemonDerivedStats(speciesEntry, build);



        const natureLabel = derived.nature?.name ? `Nature ${derived.nature.name}` : "Nature neutral";



        const modeLabel = derived.statMode === "post_nature" ? "stored post-nature" : "stored pre-nature";



        derivedStatsBox.textContent =



          `Derived: Max HP ${derived.maxHp} | Phys Eva ${derived.physEvasion} | Spec Eva ${derived.specEvasion} | Spd Eva ${derived.speedEvasion}\n` +

          `${natureLabel} | ${modeLabel}\n` +



          `Effective HP ${derived.effectiveStats.hp} | Atk ${derived.effectiveStats.atk} | Def ${derived.effectiveStats.def} | SpA ${derived.effectiveStats.spatk} | SpD ${derived.effectiveStats.spdef} | Spd ${derived.effectiveStats.spd}\n` +



          `Next thresholds: Def +${derived.nextPhysEvasionIn} | SpD +${derived.nextSpecEvasionIn} | Spd +${derived.nextSpeedEvasionIn}`;



        _setTooltipAttrs(



          derivedStatsBox,



          "Pokemon Derived Stats",



          "These follow the engine formulas used in battle exports. Max HP = Level + (3 x effective HP) + 10; Physical Evasion = floor(effective Defense / 5); Special Evasion = floor(effective Sp. Def / 5); Speed Evasion = floor(effective Speed / 5). Pre-nature mode applies nature on top of stored stats. Post-nature mode treats the stored stats as already nature-adjusted and reverses nature only for budgeting and legality."



        );



      };



      updatePokemonStatBudget();



      card.appendChild(statBudget);



      card.appendChild(derivedStatsBox);



      _pokemonBuildStatRows(speciesEntry, build).forEach((stat) => {



        const statField = document.createElement("label");



        statField.className = "char-field";



        statField.textContent = stat.label;



        _setTooltipAttrs(



          statField,



          `${stat.label} Stat`,



          `Base species stat: ${stat.base}. This builder budgets Pokemon stat points as 11 at level 1, plus 1 more per level after that, spent above species base.`



        );



        const statInput = document.createElement("input");



        statInput.type = "number";



        statInput.min = String(stat.base);



        statInput.value = String(Number.isFinite(stat.value) ? stat.value : stat.base);



        statInput.addEventListener("input", () => {



          if (!build.stats || typeof build.stats !== "object") build.stats = {};



          build.stats[stat.key] = _normalizeInteger(statInput.value, stat.base, stat.base);



          updatePokemonStatBudget();



          saveCharacterToStorage();



        });



        statField.appendChild(statInput);



        const statMeta = document.createElement("div");



        statMeta.className = "char-feature-meta";



        statMeta.textContent = `Base ${stat.base}`;



        statField.appendChild(statMeta);



        statGrid.appendChild(statField);



      });



      card.appendChild(statGrid);



      const resetStatsBtn = document.createElement("button");



      resetStatsBtn.type = "button";



      resetStatsBtn.className = "char-mini-button";



      resetStatsBtn.textContent = "Reset Stats To Species Base";



      resetStatsBtn.addEventListener("click", async () => {



        build.stats = {};



        build.stat_mode = "pre_nature";



        build.level = 1;



        if (speciesEntry) {



          build.moves = [];



          build.move_sources = {};



          build.abilities = [];



          await _applyPokemonDefaults(build, speciesEntry, true);



        }



        saveCharacterToStorage();



        renderCharacterPokemonTeam();



      });



      card.appendChild(resetStatsBtn);







      const effectiveCapabilityNames = _pokemonEffectiveCapabilityNames(speciesEntry, build);
      if (effectiveCapabilityNames.length) {



        const capTitle = document.createElement("div");



        capTitle.className = "char-feature-meta";



        capTitle.textContent = "Capabilities";



        card.appendChild(capTitle);



        const capList = document.createElement("div");



        capList.className = "char-pill-list";



        effectiveCapabilityNames.forEach((cap) => {



          const pill = document.createElement("span");



          pill.className = "char-pill";



          const desc = _getCapabilityDescription(cap);



          _setTooltipAttrs(pill, `Capability: ${cap}`, desc || "");



          pill.textContent = cap;



          capList.appendChild(pill);



        });



        card.appendChild(capList);



      }



      const effectiveCapabilityValues = _pokemonEffectiveCapabilityValues(speciesEntry, build);
      const movementBits = [
        ["Overland", effectiveCapabilityValues.overland],
        ["Burrow", effectiveCapabilityValues.burrow],
        ["Sky", effectiveCapabilityValues.sky],
        ["Swim", effectiveCapabilityValues.swim],
        ["Levitate", effectiveCapabilityValues.levitate],
        ["Teleporter", effectiveCapabilityValues.teleporter],
        ["Power", effectiveCapabilityValues.power],
        ["H Jump", effectiveCapabilityValues.h_jump],
        ["L Jump", effectiveCapabilityValues.l_jump],
        ["Threaded Range", effectiveCapabilityValues.threaded_range],
        ["Threaded AC", effectiveCapabilityValues.threaded_ac],
        ["Invisibility Min", effectiveCapabilityValues.invisibility_minutes],
        ["Tremorsense +m", effectiveCapabilityValues.tremorsense_bonus],
        ["Telepath +Focus", effectiveCapabilityValues.telepath_focus_bonus],
        ["Telekinetic +Focus", effectiveCapabilityValues.telekinetic_focus_bonus],
        ["Tracker +", effectiveCapabilityValues.tracker_bonus],
        ["Alluring +", effectiveCapabilityValues.alluring_bonus],
        ["Gravitic Steps", effectiveCapabilityValues.gravitic_steps],
      ].filter(([, value]) => value !== undefined && value !== null && Number(value) > 0);
      if (movementBits.length) {
        const moveInfo = document.createElement("div");
        moveInfo.className = "char-feature-meta";
        moveInfo.textContent = `Movement / Power: ${movementBits.map(([label, value]) => `${label} ${value}`).join(" | ")}`;
        card.appendChild(moveInfo);
      }



      const effectiveSkills = _pokemonEffectiveSkillMap(speciesEntry, build);
      const skillBits = Object.entries(effectiveSkills)
        .filter(([, value]) => Number(value) > 0)
        .sort((a, b) => String(a[0]).localeCompare(String(b[0])))
        .map(([key, value]) => `${key.replaceAll("_", " ")} ${value}`);
      if (skillBits.length) {
        const skillInfo = document.createElement("div");
        skillInfo.className = "char-feature-meta";
        skillInfo.textContent = `Species Skills: ${skillBits.join(" | ")}`;
        card.appendChild(skillInfo);
      }

      const edgeEffectNotes = _pokemonPokeEdgeEffectNotes(speciesEntry, build);
      if (edgeEffectNotes.length) {
        const edgeEffectsInfo = document.createElement("div");
        edgeEffectsInfo.className = "char-feature-meta";
        edgeEffectsInfo.textContent = `Poke Edge Effects: ${edgeEffectNotes.join(" | ")}`;
        card.appendChild(edgeEffectsInfo);
      }



    } else if (build.species) {



      const warn = document.createElement("div");



      warn.className = "char-feature-meta";



      warn.textContent = "Species not found in dataset. Check spelling.";



      card.appendChild(warn);



    }



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

        const teaching = String(issue?.hint || "").trim() || _validationTeachingText(issue.message);

        if (teaching) {

          const note = document.createElement("div");

          note.className = "char-feature-meta";

          note.textContent = teaching;

          row.appendChild(note);

        }



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



    fillInfo.textContent = "Auto-fill";



    const fillBtn = document.createElement("button");



    fillBtn.type = "button";



    fillBtn.className = "char-mini-button";



    fillBtn.textContent = "Fill from Species";



    fillBtn.addEventListener("click", async () => {



      const entry = _getPokemonSpeciesEntry(build.species || build.name || "");



      if (!entry) {



        alert("Species not found in dataset.");



        return;



      }



      const currentLevel = Number(build.level || 1);

      build.level = Number.isFinite(currentLevel) && currentLevel > 0 ? currentLevel : 1;


      const result = await _applyPokemonDefaults(build, entry, true);



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



      const names = _movePickerItemsForBuild(build, speciesForBuild);



      openListPicker({



        title: "Add Move",



        helpText: "Search by move name, type, class, range, or simple effect. Learnable moves for this species and level are shown first.",



        items: names,



        onSelect: (name) => {



          if (!Array.isArray(build.moves)) build.moves = [];



          if (!build.move_sources || typeof build.move_sources !== "object" || Array.isArray(build.move_sources)) build.move_sources = {};



          if (!build.moves.includes(name)) build.moves.push(name);



          {
            const moveKey = _normalizeMoveKey(name);
            const sourceMap = _effectivePokemonMoveSourceMap(build, speciesForBuild);
            if (moveKey && sourceMap[moveKey]) build.move_sources[moveKey] = sourceMap[moveKey];
          }



          saveCharacterToStorage();



          renderCharacterPokemonTeam();



        },



      });



    });



    moveRow.appendChild(moveLabel);



    moveRow.appendChild(addMove);



    lists.appendChild(moveRow);



    const moveBudget = document.createElement("div");



    moveBudget.className = "char-feature-meta";



    {
      const speciesForBuild = _getPokemonSpeciesEntry(build.species || build.name || "");
      const moveSourceMap = _effectivePokemonMoveSourceMap(build, speciesForBuild);
      const allMoves = Array.isArray(build.moves) ? build.moves : [];
      const tmMovesTaken = allMoves.filter((name) => moveSourceMap[_normalizeMoveKey(name)] === "tm").length;
      const tutorMovesTaken = allMoves.filter((name) => moveSourceMap[_normalizeMoveKey(name)] === "tutor").length;
      const eggMovesTaken = allMoves.filter((name) => moveSourceMap[_normalizeMoveKey(name)] === "egg").length;
      const tutorPointsNeeded = tmMovesTaken + tutorMovesTaken * 2 + eggMovesTaken * 2;
      const freeConnectedMoves = _pokemonAdvancedConnectionFreeMoves(build).size;
      const effectiveMoveCount = _pokemonEffectiveMoveCount(build);
      moveBudget.textContent = `Moves: ${effectiveMoveCount}/${_pokemonMoveSlotLimit(build)} used${freeConnectedMoves ? ` | Connected moves free: ${freeConnectedMoves}` : ""} | TM moves: ${tmMovesTaken} | Tutor moves: ${tutorMovesTaken}/${_pokemonTutorMoveLimit()} | Egg moves: ${eggMovesTaken} | Tutor Points needed: ${tutorPointsNeeded}/${_pokemonEffectiveTutorPoints(build)} available`;
    }



    lists.appendChild(moveBudget);



    const moveList = document.createElement("div");



    moveList.className = "char-pill-list";



    (build.moves || []).forEach((name) => {



      const moveRowCard = document.createElement("div");



      moveRowCard.className = "char-field char-picked-card";



      const pill = _buildRemovablePill(



        name,



        () => {



          build.moves = (build.moves || []).filter((n) => n !== name);



          if (build.move_sources && typeof build.move_sources === "object") delete build.move_sources[_normalizeMoveKey(name)];



          saveCharacterToStorage();



          renderCharacterPokemonTeam();



        },



        () => showMoveDetail(name)



      );



      const moveMainRow = document.createElement("div");
      moveMainRow.className = "char-picked-main";
      moveMainRow.appendChild(pill);



      const speciesForBuild = _getPokemonSpeciesEntry(build.species || build.name || "");



      const availability = _pokemonMoveSourceAvailability(speciesForBuild, build.level || 1, build);



      const moveKey = _normalizeMoveKey(name);



      const options = [];

      const isSmeargleSketchMove = availability.sketch?.has(moveKey) === true;

      if (isSmeargleSketchMove) options.push({ value: "sketch", label: "Sketch" });



      if (availability.natural.has(moveKey)) options.push({ value: "level_up", label: "Level-Up" });



      if (availability.egg.has(moveKey)) options.push({ value: "egg", label: "Egg" });
      if (availability.tm.has(moveKey)) options.push({ value: "tm", label: "TM" });
      if (availability.tutor.has(moveKey)) {
        options.push({
          value: "tutor",
          label: availability.tutorFallback?.has(moveKey) ? "Tutor (Legacy fallback)" : "Tutor",
        });
      }



      if (!options.length) options.push({ value: "", label: "Unknown" });



      if (!build.move_sources || typeof build.move_sources !== "object" || Array.isArray(build.move_sources)) build.move_sources = {};



      const sourceSelect = document.createElement("select");
      sourceSelect.className = "char-picked-select";



      options.forEach((optionEntry) => {
        const option = document.createElement("option");
        option.value = optionEntry.value;
        option.textContent = optionEntry.label;
        sourceSelect.appendChild(option);
      });



      const defaultSource = _effectivePokemonMoveSourceMap(build, speciesForBuild)[moveKey] || options[0]?.value || "";



      sourceSelect.value = defaultSource;



      if (defaultSource) build.move_sources[moveKey] = defaultSource;



      sourceSelect.addEventListener("change", () => {
        if (!build.move_sources || typeof build.move_sources !== "object" || Array.isArray(build.move_sources)) build.move_sources = {};
        const nextSource = _normalizePokemonMoveSource(sourceSelect.value);
        if (nextSource) build.move_sources[moveKey] = nextSource;
        else delete build.move_sources[moveKey];
        saveCharacterToStorage();
        renderCharacterPokemonTeam();
      });



      const moveEntry = _getMoveDetail(name);
      const moveDescription = document.createElement("div");
      moveDescription.className = "char-picked-description";
      moveDescription.textContent = _cleanDetailText(_moveRulesText(moveEntry)) || _movePreviewText(moveEntry);

      const sourceMeta = document.createElement("div");



      sourceMeta.className = "char-feature-meta char-picked-subnote";



      const sourceOrigin = _pokemonMoveSourceOriginNote(availability, moveKey, sourceSelect.value);
      const sourceCost = _pokemonMoveSourceCost(sourceSelect.value);
      sourceMeta.textContent = `${_moveDatasetSourceNote(moveEntry)} | Learn Source: ${sourceSelect.options[sourceSelect.selectedIndex]?.textContent || _pokemonMoveSourceLabel(sourceSelect.value)}${sourceCost > 0 ? ` | costs ${sourceCost} Tutor Point${sourceCost === 1 ? "" : "s"}` : ""}${sourceOrigin ? ` | ${sourceOrigin.replace(/^Origin:\s*/, "")}` : ""}`;



      const edgeNotes = [];
      if ((build.poke_edge_choices?.accuracy_training || []).some((moveName) => _normalizeMoveKey(moveName) === moveKey)) edgeNotes.push("Accuracy Training: AC lowered by 1 in builder preview.");
      if (_pokemonAdvancedConnectionFreeMoves(build).has(moveKey)) edgeNotes.push("Advanced Connection: this connected move does not count against the move limit.");
      if ((build.poke_edge_choices?.underdog_lessons?.moves || []).some((moveName) => _normalizeMoveKey(moveName) === moveKey)) {
        const evolutionName = build.poke_edge_choices?.underdog_lessons?.evolution || "chosen final evolution";
        edgeNotes.push(`Underdog's Lessons: borrowed from ${evolutionName}.`);
      }



      moveMainRow.appendChild(sourceSelect);
      moveRowCard.appendChild(moveMainRow);
      moveRowCard.appendChild(moveDescription);
      if (edgeNotes.length) {
        const edgeNoteEl = document.createElement("div");
        edgeNoteEl.className = "char-feature-meta char-picked-note";
        edgeNoteEl.textContent = edgeNotes.join(" ");
        moveRowCard.appendChild(edgeNoteEl);
      }
      moveRowCard.appendChild(sourceMeta);



      moveList.appendChild(moveRowCard);



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



      const names = _abilityPickerItemsForBuild(build, speciesForBuild);



      openListPicker({



        title: "Add Ability",



        helpText: "Search by ability name, pool, trigger, or plain-English summary. Species-legal abilities for this build are shown first.",



        items: names,



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



    abilityList.className = "char-pill-list";



    (build.abilities || []).forEach((name) => {



      const abilityRowCard = document.createElement("div");
      abilityRowCard.className = "char-field char-picked-card";



      const pill = _buildRemovablePill(



        name,



        () => {



          build.abilities = (build.abilities || []).filter((n) => n !== name);



          saveCharacterToStorage();



          renderCharacterPokemonTeam();



        },



        () => showAbilityDetail(name)



      );



      const abilityEntry = _getAbilityDetail(name);
      const abilityDescription = document.createElement("div");
      abilityDescription.className = "char-picked-description";
      abilityDescription.textContent = _abilityPreviewText(abilityEntry);



      const abilitySummary = document.createElement("div");
      abilitySummary.className = "char-feature-meta char-picked-note";
      abilitySummary.textContent = _eli5AbilitySummary(abilityEntry);



      const abilitySource = document.createElement("div");
      abilitySource.className = "char-feature-meta char-picked-subnote";
      abilitySource.textContent = _builderSourceNote("ability", abilityEntry);



      const abilityMainRow = document.createElement("div");
      abilityMainRow.className = "char-picked-main";
      abilityMainRow.appendChild(pill);



      abilityRowCard.appendChild(abilityMainRow);
      abilityRowCard.appendChild(abilityDescription);
      abilityRowCard.appendChild(abilitySummary);
      abilityRowCard.appendChild(abilitySource);
      abilityList.appendChild(abilityRowCard);



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



      const names = _itemPickerItems();



      openListPicker({



        title: "Add Item",



        helpText: "Search by item name, category, slot, cost, or simple effect.",



        items: names,



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



    itemList.className = "char-pill-list";



    (build.items || []).forEach((name) => {



      const pill = _buildRemovablePill(



        _pokemonBuildItemLabel(name),



        () => {



          build.items = (build.items || []).filter((n) => n !== name);



          saveCharacterToStorage();



          renderCharacterPokemonTeam();



        },



        () => showItemDetail(name)



      );



      itemList.appendChild(pill);



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



          const variantOptions = _pokemonPokeEdgeVariants(name);



          if (variantOptions.length) {



            const alreadyTaken = new Set(_normalizeStringList(build.poke_edges));



            openListPicker({



              title: `${name}: Choose Variant`,



              helpText: "Pick the specific version to add to this Pokemon.",



              items: variantOptions



                .filter((variantName) => !alreadyTaken.has(variantName))



                .map((variantName) => ({ name: variantName, meta: "", hint: "" })),



              onSelect: (variantName) => {



                if (!Array.isArray(build.poke_edges)) build.poke_edges = [];



                if (!build.poke_edges.includes(variantName)) build.poke_edges.push(variantName);



                saveCharacterToStorage();



                renderCharacterPokemonTeam();



              },



            });



            return;



          }



          if (!Array.isArray(build.poke_edges)) build.poke_edges = [];



          if (!build.poke_edges.includes(name)) build.poke_edges.push(name);



          saveCharacterToStorage();



          renderCharacterPokemonTeam();



        },



      });



    });



    const browsePokeEdges = document.createElement("button");



    browsePokeEdges.type = "button";



    browsePokeEdges.className = "char-mini-button";



    browsePokeEdges.textContent = "Open Poke Edges Tab";



    browsePokeEdges.addEventListener("click", () => {



      goToCharacterStep("poke-edges");



    });



    pokeEdgeRow.appendChild(pokeEdgeLabel);



    pokeEdgeRow.appendChild(addPokeEdge);



    pokeEdgeRow.appendChild(browsePokeEdges);



    lists.appendChild(pokeEdgeRow);



    const pokeEdgeList = document.createElement("div");



    pokeEdgeList.className = "char-pill-list";



    (build.poke_edges || []).forEach((name) => {



      const pill = _buildRemovablePill(



        name,



        () => {



          build.poke_edges = (build.poke_edges || []).filter((n) => n !== name);



          saveCharacterToStorage();



          renderCharacterPokemonTeam();



        },



        () => {



          characterState.poke_edge_search = name;



          goToCharacterStep("poke-edges");



        }



      );



      pokeEdgeList.appendChild(pill);



    });



    if (!(build.poke_edges || []).length) {



      const empty = document.createElement("span");



      empty.className = "char-feature-meta";



      empty.textContent = "No Poke Edges selected.";



      pokeEdgeList.appendChild(empty);



    }



    lists.appendChild(pokeEdgeList);



    const edgeConfigList = document.createElement("div");



    edgeConfigList.className = "char-stack";



    _ensurePokemonBuildChoiceState(build);



    (build.poke_edges || []).forEach((name) => {



      if (_pokemonPokeEdgeVariants(name).length) {



        const configCard = document.createElement("div");



        configCard.className = "char-detail-card";



        const heading = document.createElement("div");



        heading.className = "char-detail-title";



        heading.textContent = `${name} needs a specific variant`;



        configCard.appendChild(heading);



        const note = document.createElement("div");



        note.className = "char-helper-text";



        note.textContent = "This generic Poke Edge does not apply a specific effect in the builder until you replace it with one of its variants.";



        configCard.appendChild(note);



        const chooseBtn = document.createElement("button");



        chooseBtn.type = "button";



        chooseBtn.className = "char-mini-button";



        chooseBtn.textContent = "Choose Variant";



        chooseBtn.addEventListener("click", () => {



          const remaining = _pokemonPokeEdgeVariants(name).filter((variantName) => !(build.poke_edges || []).includes(variantName));



          openListPicker({



            title: `${name}: Choose Variant`,



            helpText: "Pick the specific version to replace this generic Poke Edge.",



            items: remaining.map((variantName) => ({ name: variantName, meta: "", hint: "" })),



            onSelect: (variantName) => {



              build.poke_edges = (build.poke_edges || []).filter((edgeName) => edgeName !== name);



              if (!build.poke_edges.includes(variantName)) build.poke_edges.push(variantName);



              saveCharacterToStorage();



              renderCharacterPokemonTeam();



            },



          });



        });



        configCard.appendChild(chooseBtn);



        edgeConfigList.appendChild(configCard);



      }



      if (name === "Accuracy Training") {



        const configCard = document.createElement("div");



        configCard.className = "char-detail-card";



        const heading = document.createElement("div");



        heading.className = "char-detail-title";



        heading.textContent = "Accuracy Training";



        configCard.appendChild(heading);



        const selected = build.poke_edge_choices.accuracy_training || [];



        const note = document.createElement("div");



        note.className = "char-helper-text";



        note.textContent = selected.length ? `Configured moves: ${selected.join(", ")}` : "Pick one of this Pokemon's moves with AC 3 or higher.";



        configCard.appendChild(note);



        const chooseBtn = document.createElement("button");



        chooseBtn.type = "button";



        chooseBtn.className = "char-mini-button";



        chooseBtn.textContent = "Choose Move";



        chooseBtn.addEventListener("click", () => {



          const eligibleMoves = (build.moves || [])



            .map((moveName) => _getMoveDetail(moveName))



            .filter((entry) => entry && Number(entry.ac || 0) >= 3)



            .filter((entry) => !(build.poke_edge_choices.accuracy_training || []).some((moveName) => _normalizeMoveKey(moveName) === _normalizeMoveKey(entry.name)))



            .map((entry) => ({ name: entry.name, meta: `AC ${entry.ac}`, hint: _cleanDetailText(entry.effect || entry.description || "") }));



          openListPicker({



            title: "Accuracy Training",



            helpText: "Choose a move with AC 3 or higher. The builder will mark it as improved by 1 AC.",



            items: eligibleMoves,



            onSelect: (moveName) => {



              build.poke_edge_choices.accuracy_training = _normalizeStringList(build.poke_edge_choices.accuracy_training);



              if (!build.poke_edge_choices.accuracy_training.includes(moveName)) build.poke_edge_choices.accuracy_training.push(moveName);



              saveCharacterToStorage();



              renderCharacterPokemonTeam();



            },



          });



        });



        configCard.appendChild(chooseBtn);



        edgeConfigList.appendChild(configCard);



      }



      if (name === "Advanced Connection") {



        const configCard = document.createElement("div");



        configCard.className = "char-detail-card";



        const heading = document.createElement("div");



        heading.className = "char-detail-title";



        heading.textContent = "Advanced Connection";



        configCard.appendChild(heading);



        const connectedChoices = _pokemonConnectedAbilityChoices(build);



        const selectedAbilities = build.poke_edge_choices.advanced_connection || [];



        const note = document.createElement("div");



        note.className = "char-helper-text";



        note.textContent = connectedChoices.length



          ? `Selected abilities: ${selectedAbilities.join(", ") || "none"}. Connected moves from these abilities do not count against the move limit.`



          : "Add a Connection ability first, then choose it here.";



        configCard.appendChild(note);



        const chooseBtn = document.createElement("button");



        chooseBtn.type = "button";



        chooseBtn.className = "char-mini-button";



        chooseBtn.textContent = "Choose Ability";



        chooseBtn.disabled = !connectedChoices.length;



        chooseBtn.addEventListener("click", () => {



          openListPicker({



            title: "Advanced Connection",



            helpText: "Choose one of this Pokemon's Connection abilities. Its connected move will no longer count against the move limit.",



            items: connectedChoices.filter(({ abilityName }) => !selectedAbilities.includes(abilityName)).map(({ abilityName, moveName }) => ({ name: abilityName, meta: `Connection - ${moveName}`, hint: "" })),



            onSelect: (abilityName) => {



              build.poke_edge_choices.advanced_connection = _normalizeStringList(build.poke_edge_choices.advanced_connection);



              if (!build.poke_edge_choices.advanced_connection.includes(abilityName)) build.poke_edge_choices.advanced_connection.push(abilityName);



              saveCharacterToStorage();



              renderCharacterPokemonTeam();



            },



          });



        });



        configCard.appendChild(chooseBtn);



        edgeConfigList.appendChild(configCard);



      }



      if (name === "Underdog's Lessons") {



        const configCard = document.createElement("div");



        configCard.className = "char-detail-card";



        const heading = document.createElement("div");



        heading.className = "char-detail-title";



        heading.textContent = "Underdog's Lessons";



        configCard.appendChild(heading);



        const speciesForBuild = _getPokemonSpeciesEntry(build.species || build.name || "");



        const finalOptions = speciesForBuild ? _speciesFinalEvolutionNames(speciesForBuild.name) : [];



        const configuredEvolution = build.poke_edge_choices.underdog_lessons?.evolution || "";



        const configuredMoves = build.poke_edge_choices.underdog_lessons?.moves || [];



        const note = document.createElement("div");



        note.className = "char-helper-text";



        note.textContent = configuredEvolution ? `Chosen final evolution: ${configuredEvolution}. Selected lesson moves: ${configuredMoves.join(", ") || "none"}.` : "Pick one final evolution in this line, then choose up to 3 moves from that evolution's level-up, TM, or Tutor sources.";



        configCard.appendChild(note);



        const evoBtn = document.createElement("button");



        evoBtn.type = "button";



        evoBtn.className = "char-mini-button";



        evoBtn.textContent = "Choose Evolution";



        evoBtn.disabled = !finalOptions.length;



        evoBtn.addEventListener("click", () => {



          openListPicker({



            title: "Underdog's Lessons: Final Evolution",



            helpText: "Choose the final evolution whose move options this Pokemon can learn from.",



            items: finalOptions.map((optionName) => ({ name: optionName, meta: "", hint: "" })),



            onSelect: (evolutionName) => {



              build.poke_edge_choices.underdog_lessons.evolution = evolutionName;



              build.poke_edge_choices.underdog_lessons.moves = [];



              saveCharacterToStorage();



              renderCharacterPokemonTeam();



            },



          });



        });



        configCard.appendChild(evoBtn);



        const moveBtn = document.createElement("button");



        moveBtn.type = "button";



        moveBtn.className = "char-mini-button";



        moveBtn.textContent = "Choose Lesson Move";



        moveBtn.disabled = !configuredEvolution || configuredMoves.length >= 3;



        moveBtn.addEventListener("click", () => {



          const evolutionEntry = _getPokemonSpeciesEntry(configuredEvolution);



          const options = evolutionEntry ? _movePickerItemsForBuild({ ...build, species: evolutionEntry.name, name: evolutionEntry.name }, evolutionEntry).filter((entry) => {



            const key = _normalizeMoveKey(entry.name);



            return key && !(build.poke_edge_choices.underdog_lessons.moves || []).some((moveName) => _normalizeMoveKey(moveName) === key);



          }) : [];



          openListPicker({



            title: "Underdog's Lessons: Choose Move",



            helpText: "Pick a move your chosen final evolution can learn. You can store up to 3 lesson moves.",



            items: options,



            onSelect: (moveName) => {



              build.poke_edge_choices.underdog_lessons.moves = _normalizeStringList(build.poke_edge_choices.underdog_lessons.moves).slice(0, 3);



              if (!build.poke_edge_choices.underdog_lessons.moves.includes(moveName)) build.poke_edge_choices.underdog_lessons.moves.push(moveName);



              saveCharacterToStorage();



              renderCharacterPokemonTeam();



            },



          });



        });



        configCard.appendChild(moveBtn);



        edgeConfigList.appendChild(configCard);



      }



    });



    _pokemonGrantedAbilityNames(build).forEach((name) => {



      const abilityRowCard = document.createElement("div");
      abilityRowCard.className = "char-field char-picked-card";



      const label = document.createElement("div");
      label.className = "char-picked-main";
      const pill = document.createElement("span");
      pill.className = "char-pill";
      pill.textContent = `${name} (Granted)`;
      label.appendChild(pill);



      const abilityEntry = _getAbilityDetail(name);
      const abilityDescription = document.createElement("div");
      abilityDescription.className = "char-picked-description";
      abilityDescription.textContent = _abilityPreviewText(abilityEntry);



      const abilitySummary = document.createElement("div");
      abilitySummary.className = "char-feature-meta char-picked-note";
      abilitySummary.textContent = "Granted automatically by a selected Poke Edge.";



      const abilitySource = document.createElement("div");
      abilitySource.className = "char-feature-meta char-picked-subnote";
      abilitySource.textContent = _builderSourceNote("ability", abilityEntry);



      abilityRowCard.appendChild(label);
      abilityRowCard.appendChild(abilityDescription);
      abilityRowCard.appendChild(abilitySummary);
      abilityRowCard.appendChild(abilitySource);
      abilityList.appendChild(abilityRowCard);



    });



    if (edgeConfigList.childNodes.length) lists.appendChild(edgeConfigList);



    card.appendChild(lists);







    const removeRow = document.createElement("div");



    removeRow.className = "char-action-row";



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



    removeRow.appendChild(remove);



    card.appendChild(removeRow);







    teamPanel.appendChild(card);



  });







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



  swift: "Swift: usually a quick action that fits alongside your main turn action, depending on the rule text.",



  "shift action": "Shift Action: repositioning or minor action.",



  shift: "Shift: movement or minor repositioning; many PTU effects let you Shift a set number of meters.",



  "standard action": "Standard Action: main action for your turn.",



  "free action": "Free Action: minor action that does not consume your main action.",



  interrupt: "Interrupt: can be used out of turn when the trigger occurs.",



  reaction: "Reaction: response timing that happens when a listed trigger occurs.",



  priority: "Priority: resolves before normal actions at the same timing.",



  critical: "Critical: the attack scored a crit and may trigger bonus effects or extra damage.",



  crit: "Crit: short for critical hit.",



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



  push: "Push: forced movement away from the source by the listed distance.",



  pull: "Pull: forced movement toward the source by the listed distance.",



  pass: "Pass: lets a move or effect ignore through-target or barrier restrictions in some cases.",



  cs: "CS: Combat Stage; temporary stat stage changes.",



  db: "DB: Damage Base; used to compute damage.",



  stab: "STAB: Same-Type Attack Bonus; attacks matching your type usually hit harder.",



  trigger: "Trigger: the exact moment or condition that turns this effect on.",



  frequency: "Frequency: tells you how often the move, feature, or ability may be used.",



};







function _keywordHelpList(text) {



  const source = String(text || "");



  if (!source) return [];



  return _keywordHelpEntries(source).map(({ key, desc }) => `${key}: ${desc}`);



}



function _keywordHelpEntries(text) {



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



  return Array.from(found.entries()).map(([key, desc]) => ({ key, desc }));



}







function _attachKeywordTooltip(target, text) {



  if (!target) return;



  const lines = _keywordHelpList(text);



  if (!lines.length) return;



  _setTooltipAttrs(target, "Keywords", lines.join("\n"));



}



function _builderBasicsLines(kind, text, entry = null) {



  const lines = [];



  const normalizedKind = String(kind || "").trim().toLowerCase();



  if (normalizedKind === "move") {



    const freq = String(entry?.frequency || entry?.freq || "").trim();



    const category = String(entry?.category || "").trim();



    const range = String(entry?.range || "").trim();



    if (freq) lines.push(`Frequency: ${_plainFrequencyText(freq)}`);



    if (category) lines.push(`Category: ${category} tells you whether the move mainly deals damage, sets a status, or changes the field.`);



    if (range) lines.push(`Range: ${_plainRangeText(range)}`);



  } else if (normalizedKind === "ability") {



    const frequency = String(entry?.frequency || "").trim();



    if (frequency && frequency.toLowerCase() !== "static") lines.push(`Timing: ${_plainFrequencyText(frequency)}`);



    else lines.push("Timing: static abilities are usually always on unless a rule says otherwise.");



    if (entry?.trigger) lines.push("Trigger: this tells you when the ability actually matters in play.");



  } else if (normalizedKind === "feature" || normalizedKind === "edge" || normalizedKind === "poke edge") {



    const prereq = String(entry?.prerequisites || "").trim();



    if (prereq) lines.push("Prerequisites: you only need to satisfy what is listed here before taking it.");



    lines.push(normalizedKind === "feature" ? "Features are your bigger trainer abilities." : "Edges are smaller, supporting upgrades that shape your build.");



  } else if (normalizedKind === "item") {



    lines.push("Items usually work when held, used, consumed, or equipped, depending on the rules text.");



  }




  _keywordHelpList(text).slice(0, 4).forEach((line) => {



    lines.push(line);



  });



  return Array.from(new Set(lines)).filter(Boolean);



}



function _builderExampleText(kind, entry, fallbackText = "") {



  const normalizedKind = String(kind || "").trim().toLowerCase();



  if (normalizedKind === "move" && entry) {



    const name = entry.name || "This move";



    const effect = _firstSentence(_moveRulesText(entry));



    return effect ? `Example: Use ${name} when you want ${effect.charAt(0).toLowerCase()}${effect.slice(1)}` : "Example: use this when the listed range, timing, and effect match your current turn plan.";



  }



  if (normalizedKind === "ability" && entry) {



    const trigger = _cleanDetailText(entry.trigger);



    if (trigger) return `Example: keep this in mind when ${trigger.charAt(0).toLowerCase()}${trigger.slice(1)}.`;



    return "Example: passive abilities matter automatically, so check whether this changes damage, timing, movement, or survivability.";



  }



  if (normalizedKind === "feature") return "Example: trainer features usually define what special actions, passives, or combat tricks your trainer can bring to a fight.";



  if (normalizedKind === "edge") return "Example: edges usually support a broader build plan, like making prerequisites easier, improving a niche, or opening later options.";



  if (normalizedKind === "poke edge") return "Example: Poke Edges are the smaller, optional upgrades you use to fine-tune an individual Pokemon build.";



  if (normalizedKind === "item") return "Example: before equipping or using this, ask who holds it, when it triggers, and whether it is consumed.";



  return fallbackText || "";



}



function _builderQuickSummary(kind, text, entry = null) {



  const cleaned = _cleanDetailText(_firstSentence(text || ""));



  if (cleaned) return cleaned;



  const basics = _builderBasicsLines(kind, text, entry);



  if (basics.length) return basics[0];



  return _builderExampleText(kind, entry, "");



}



function _appendLearningPanel(parent, title, lines) {



  if (!parent) return;



  const items = Array.isArray(lines) ? lines.filter(Boolean) : [];



  if (!items.length) return;



  const panel = document.createElement("div");



  panel.className = "char-summary-box";



  const heading = document.createElement("div");



  heading.className = "char-tier-title";



  heading.textContent = title || "How To Read This";



  panel.appendChild(heading);



  items.forEach((line) => {



    const row = document.createElement("div");



    row.className = "char-feature-meta";



    row.textContent = line;



    panel.appendChild(row);



  });



  parent.appendChild(panel);



}



function _catalogStatusRank(status) {



  switch (String(status || "").toLowerCase()) {



    case "available":



      return 0;



    case "close":



      return 1;



    case "unavailable":



      return 2;



    case "blocked":



      return 3;



    default:



      return 4;



  }



}



function _sortCatalogEntries(entries, options = {}) {



  const list = Array.isArray(entries) ? entries.slice() : [];



  const selectedSet = options.selectedSet instanceof Set ? options.selectedSet : new Set();



  const mode = String(options.mode || "progressive").toLowerCase();



  const getStatus =



    typeof options.getStatus === "function"



      ? options.getStatus



      : () => ({ status: "unavailable", missing: [] });



  if (mode === "alpha" || mode === "alphabetical") {



    return list.sort((a, b) => String(a?.name || "").localeCompare(String(b?.name || "")));



  }



  return list.sort((a, b) => {



    const aSelected = selectedSet.has(String(a?.name || ""));



    const bSelected = selectedSet.has(String(b?.name || ""));



    if (aSelected !== bSelected) return aSelected ? -1 : 1;



    const aStatus = getStatus(a) || {};



    const bStatus = getStatus(b) || {};



    const statusDiff = _catalogStatusRank(aStatus.status) - _catalogStatusRank(bStatus.status);



    if (statusDiff !== 0) return statusDiff;



    const aMissing = Array.isArray(aStatus.missing) ? aStatus.missing.length : 99;



    const bMissing = Array.isArray(bStatus.missing) ? bStatus.missing.length : 99;



    if (aMissing !== bMissing) return aMissing - bMissing;



    return String(a?.name || "").localeCompare(String(b?.name || ""));



  });



}



function _entryRelationStatus(entry, kind) {



  return prereqStatus(entry?.prerequisites || "", kind);



}



function _unlockTargetsForEntry(kind, name, limit = 4) {



  const trimmed = String(name || "").trim();



  if (!trimmed) return [];



  const matches = [];



  const addMatch = (entry, entryKind) => {



    const prereq = String(entry?.prerequisites || "");



    const pattern = _namePattern(trimmed);



    if (!pattern || !pattern.test(prereq)) return;



    matches.push({



      kind: entryKind,



      name: entry.name,



      entry,



      statusInfo: _entryRelationStatus(entry, entryKind),



    });



  };



  (characterData?.features || []).forEach((entry) => {



    if (kind === "feature" && String(entry?.name || "") === trimmed) return;



    addMatch(entry, "feature");



  });



  (characterData?.edges_catalog || []).forEach((entry) => {



    if (kind === "edge" && String(entry?.name || "") === trimmed) return;



    addMatch(entry, "edge");



  });



  return _sortCatalogEntries(matches, {



    selectedSet: new Set(),



    mode: "progressive",



    getStatus: (candidate) => candidate?.statusInfo || { status: "unavailable", missing: [] },



  }).slice(0, Math.max(0, Number(limit || 0)));



}



function _relatedTargetsForEntry(kind, entry, limit = 4) {



  if (!entry) return [];



  const related = [];



  const name = String(entry.name || "").trim();



  const classLabels = kind === "feature" ? getFeatureClassLabels(entry) : getEdgeClassLabels(entry);



  const tags = kind === "feature" ? extractFeatureTags(entry) : [];



  const skills = extractPrereqSkills(entry.prerequisites || "");



  const addCandidate = (candidate, candidateKind) => {



    const candidateName = String(candidate?.name || "").trim();



    if (!candidateName || candidateName === name) return;



    let score = 0;



    const candidateClasses = candidateKind === "feature" ? getFeatureClassLabels(candidate) : getEdgeClassLabels(candidate);



    const candidateTags = candidateKind === "feature" ? extractFeatureTags(candidate) : [];



    const candidateSkills = extractPrereqSkills(candidate.prerequisites || "");



    if (classLabels.some((label) => candidateClasses.includes(label))) score += 3;



    if (skills.some((skill) => candidateSkills.includes(skill))) score += 2;



    if (tags.some((tag) => candidateTags.includes(tag))) score += 1;



    if (_namePattern(candidateName)?.test(String(entry.prerequisites || ""))) score += 1;



    if (_namePattern(name)?.test(String(candidate.prerequisites || ""))) score += 1;



    if (score <= 0) return;



    related.push({



      kind: candidateKind,



      name: candidateName,



      entry: candidate,



      score,



      statusInfo: _entryRelationStatus(candidate, candidateKind),



    });



  };



  (characterData?.features || []).forEach((candidate) => addCandidate(candidate, "feature"));



  (characterData?.edges_catalog || []).forEach((candidate) => addCandidate(candidate, "edge"));



  return related



    .sort((a, b) => {



      const scoreDiff = b.score - a.score;



      if (scoreDiff !== 0) return scoreDiff;



      return _catalogStatusRank(a.statusInfo?.status) - _catalogStatusRank(b.statusInfo?.status) || a.name.localeCompare(b.name);



    })



    .slice(0, Math.max(0, Number(limit || 0)));



}



function _appendRelationChipRow(parent, titleText, items) {



  if (!parent) return;



  const entries = Array.isArray(items) ? items.filter(Boolean) : [];



  if (!entries.length) return;



  const meta = document.createElement("div");



  meta.className = "char-feature-meta";



  meta.textContent = titleText;



  parent.appendChild(meta);



  const row = document.createElement("div");



  row.className = "char-tag-row";



  entries.forEach((item) => {



    const statusText = item?.statusInfo?.status ? ` (${String(item.statusInfo.status)})` : "";



    row.appendChild(



      makeFilterChip(`${item.kind}: ${item.name}${statusText}`, () => {



        if (item.kind === "feature") focusFeature(item.name);



        else if (item.kind === "edge") focusEdge(item.name);



      })



    );



  });



  parent.appendChild(row);



}



function _validationTeachingText(message) {



  const text = String(message || "").trim();



  if (!text) return "";



  let match = text.match(/^Move "(.+)" is not in (.+)'s learnset at level (\d+)\.$/);



  if (match) return `${match[1]} is not level-legal here. Pick a move the species already knows at level ${match[3]}, or raise the level first.`;



  match = text.match(/^Ability "(.+)" is not available for (.+) at level (\d+)\.$/);



  if (match) return `${match[1]} is outside this species' unlocked ability slots at level ${match[3]}. Use one of the species' listed legal abilities instead.`;



  match = text.match(/^(.+) is normally obtained by evolution at level (\d+)\. At level (\d+) it must be marked as Caught \(wild\)\.$/);



  if (match) return `This is an evolved species below its normal evolution level. Mark it as caught in the wild if that is intentional; otherwise use a lower-stage form.`;



  match = text.match(/^Poke Edge "(.+)" requires level (\d+) \(current (\d+)\)\.$/);



  if (match) return `You can read this now, but it is not takeable until level ${match[2]}.`;



  if (/Species not found:/i.test(text)) return "The builder could not match this species name to its local dataset. Check spelling or form naming.";



  if (/Move not found:/i.test(text)) return "The move name did not match the local move dataset exactly. Try the canonical PTU move name.";



  if (/Ability not found:/i.test(text)) return "The ability name did not match the local ability dataset exactly. Try the canonical PTU ability name.";



  if (/Item not found:/i.test(text)) return "The item name did not match the local item dataset exactly.";



  if (/Level must be between 1 and 100/i.test(text)) return "Pokemon legality is always checked against a level from 1 to 100.";



  return "";



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



  (characterData?.poke_edges_catalog || []).forEach((entry) => {



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



    characterState.poke_edge_search = targets.pokeEdges.get(key);



    goToCharacterStep("poke-edges");



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

  const requested = step || characterStep;

  const target = getCharacterStepOrder().includes(requested) ? requested : "profile";


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
  const order = getCharacterStepOrder();
  const currentIndex = order.indexOf(characterStep);
  const prevStep = currentIndex > 0 ? order[currentIndex - 1] : "";
  const nextStep = currentIndex >= 0 && currentIndex < order.length - 1 ? order[currentIndex + 1] : "";

  const stepChip = document.createElement("span");

  stepChip.className = "char-pill";

  stepChip.textContent = currentIndex >= 0 ? `Step ${currentIndex + 1}/${order.length}` : "Builder";

  row.appendChild(stepChip);

  if (prevStep) {

    const prev = document.createElement("button");

    prev.type = "button";

    prev.className = "char-step-link";

    prev.textContent = `Previous: ${getCharacterStepLabel(prevStep)}`;

    prev.addEventListener("click", () => goToCharacterStep(prevStep));

    row.appendChild(prev);

  }

  if (nextStep) {

    const next = document.createElement("button");

    next.type = "button";

    next.className = "char-step-link";

    next.textContent = `Next: ${getCharacterStepLabel(nextStep)}`;

    next.addEventListener("click", () => goToCharacterStep(nextStep));

    row.appendChild(next);

  }

  const jump = document.createElement("button");


  jump.type = "button";



  jump.textContent = "Jump";



  jump.addEventListener("click", () => openJumpPalette());



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



  (characterData?.poke_edges_catalog || []).forEach((entry) => {



    if (!entry?.name) return;



    entries.push({



      kind: "Poke Edge",



      name: entry.name,



      detail: entry.prerequisites || "",



      action: () => {



        characterState.poke_edge_search = entry.name;



        goToCharacterStep("poke-edges");



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



  (masterData?.pokemon?.capabilities || []).forEach((cap) => {



    if (!cap?.name) return;



    entries.push({



      kind: "Capability",



      name: cap.name,



      detail: cap.description || "",



      action: () => showCapabilityDetail(cap.name),



    });



  });



  (masterData?.pokemon?.moves || []).forEach((move) => {



    if (!move?.name) return;



    entries.push({



      kind: "Move",



      name: move.name,



      detail: [move.type, move.category, move.frequency, move.effect].filter(Boolean).join(" | "),



      action: () => showMoveDetail(move.name),



    });



  });



  (masterData?.pokemon?.abilities || []).forEach((ability) => {



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



  box.className = "char-connection-box char-picker-box";



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



  const caps = masterData?.pokemon?.capabilities || [];



  const key = _normalizeMoveKey(name);


  const match = caps.find((cap) => _normalizeSearchText(cap.name) === key);



  return match?.description || "";



}







function _cleanDetailText(value) {



  return String(value || "").replace(/\s+/g, " ").trim();



}







function _firstSentence(value, fallback = "") {



  const text = _cleanDetailText(value);



  if (!text) return fallback;



  const match = text.match(/^.*?[.!?](?:\s|$)/);



  return (match ? match[0] : text).trim();



}







function _plainFrequencyText(value) {



  const text = String(value || "").trim();



  const lower = text.toLowerCase();



  if (!text) return "Frequency is not listed.";



  if (lower === "static") return "This effect is usually always on.";



  if (lower.includes("at-will")) return `You can usually use this whenever you want (${text}).`;



  if (lower.includes("scene")) return `You can use this a limited number of times each scene (${text}).`;



  if (lower.includes("daily")) return `You can use this a limited number of times per day (${text}).`;



  return `Use rate: ${text}.`;



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




function _movePreviewText(entry) {



  if (!entry) return "No move details available.";



  const effectText = String(_moveRulesText(entry)).trim();



  const firstRuleSentence = _firstSentence(effectText);



  if (firstRuleSentence) return firstRuleSentence;



  return _eli5MoveSummary(entry);



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



  if (entry.trigger) lines.push(`It matters when this happens: ${_cleanDetailText(entry.trigger)}`);



  const target = _cleanDetailText(entry.target);



  if (target) lines.push(`It usually affects: ${target}`);



  const effectLine = _firstSentence(entry.effect || entry.effect_2 || entry.description || "");



  if (effectLine) lines.push(`What it does: ${effectLine}`);



  return lines.filter(Boolean).join(" ");



}




function _abilityPreviewText(entry) {



  if (!entry) return "No ability details available.";



  const effectText = String(_moveRulesText(entry)).trim();



  const firstRuleSentence = _firstSentence(effectText);



  if (firstRuleSentence) return firstRuleSentence;



  return _eli5AbilitySummary(entry);



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







function _appendDetailBlock(parent, titleText, bodyText, options = {}) {



  if (!parent || !bodyText) return;



  const title = document.createElement("div");



  title.className = "char-feature-meta";



  title.textContent = titleText;



  parent.appendChild(title);



  const body = document.createElement("div");



  body.className = `char-summary-box char-no-word-links${options.muted ? " char-summary-box-muted" : ""}`;



  body.textContent = bodyText;



  _attachKeywordTooltip(body, bodyText);



  parent.appendChild(body);



}



function _appendGlossaryBlock(parent, text, titleText = "Glossary", limit = 8) {



  if (!parent) return;



  const entries = _keywordHelpEntries(text).slice(0, Math.max(0, Number(limit) || 0));



  if (!entries.length) return;



  const title = document.createElement("div");



  title.className = "char-feature-meta";



  title.textContent = titleText;



  parent.appendChild(title);



  const box = document.createElement("div");



  box.className = "char-summary-box";



  entries.forEach(({ key, desc }) => {



    const row = document.createElement("div");



    row.className = "char-feature-meta";



    row.textContent = `${key}: ${desc}`;



    _setTooltipAttrs(row, `Glossary: ${key}`, desc);



    box.appendChild(row);



  });



  parent.appendChild(box);



}



function _glossaryCategoryLabel(kind) {

  const normalized = String(kind || "").trim().toLowerCase();
  if (normalized === "keyword") return "Keyword";
  if (normalized === "status") return "Status";
  if (normalized === "skill") return "Skill";
  if (normalized === "capability") return "Capability";
  if (normalized === "class") return "Class";
  if (normalized === "feature") return "Feature";
  if (normalized === "edge") return "Edge";
  if (normalized === "poke edge") return "Poke Edge";
  if (normalized === "move") return "Move";
  if (normalized === "ability") return "Ability";
  if (normalized === "item") return "Item";
  if (normalized === "species") return "Species";
  return "Rule";

}



function _speciesStatsSummary(entry) {

  const stats = entry?.base_stats || {};
  const labels = [
    ["HP", stats.hp],
    ["Atk", stats.attack],
    ["Def", stats.defense],
    ["SpA", stats.special_attack],
    ["SpD", stats.special_defense],
    ["Spd", stats.speed],
  ];
  return labels
    .filter(([, value]) => Number.isFinite(Number(value)))
    .map(([label, value]) => `${label} ${value}`)
    .join(" | ");

}



function _speciesRuleText(entry) {

  if (!entry) return "No species details available.";
  const parts = [];
  if (Array.isArray(entry.types) && entry.types.length) parts.push(`Types: ${entry.types.join(" / ")}`);
  if (entry.size) parts.push(`Size: ${entry.size}`);
  if (_hasDisplayValue(entry.weight)) parts.push(`Weight Class: ${entry.weight}`);
  const stats = _speciesStatsSummary(entry);
  if (stats) parts.push(`Base Stats: ${stats}`);
  const movement = entry?.movement && typeof entry.movement === "object"
    ? Object.entries(entry.movement)
      .filter(([, value]) => Number(value) > 0)
      .map(([key, value]) => `${key.replace(/_/g, " ")} ${value}`)
      .join(" | ")
    : "";
  if (movement) parts.push(`Movement: ${movement}`);
  if (Array.isArray(entry.capabilities) && entry.capabilities.length) parts.push(`Capabilities: ${entry.capabilities.join(", ")}`);
  if (Array.isArray(entry.naturewalk) && entry.naturewalk.length) parts.push(`Naturewalk: ${entry.naturewalk.join(", ")}`);
  if (Array.isArray(entry.egg_groups) && entry.egg_groups.length) parts.push(`Egg Groups: ${entry.egg_groups.join(", ")}`);
  return parts.join("\n");

}



function _flattenGlossaryItemSources() {

  const sets = masterData?.items && typeof masterData.items === "object" ? masterData.items : {};
  return Object.entries(sets).flatMap(([group, items]) => {
    if (!Array.isArray(items)) return [];
    return items.map((entry) => ({ ...entry, glossary_group: group }));
  });

}



function _buildRulebookGlossaryIndex() {

  if (rulebookGlossaryIndexCache) return rulebookGlossaryIndexCache;

  const entries = [];
  const pushEntry = (entry) => {
    if (!entry || !entry.name) return;
    const body = _cleanDetailText(entry.body || "");
    const prereq = _cleanDetailText(entry.prerequisites || "");
    const frequency = _cleanDetailText(entry.frequency || "");
    const category = _glossaryCategoryLabel(entry.kind);
    entries.push({
      ...entry,
      category,
      search_blob: _normalizeSearchText(
        `${entry.name}\n${category}\n${body}\n${prereq}\n${frequency}\n${entry.source_note || ""}\n${entry.tags || ""}`
      ),
    });
  };

  Object.entries(KEYWORD_HELP).forEach(([key, desc]) => pushEntry({ kind: "keyword", name: key, body: desc, source_note: "PTU builder keyword glossary" }));
  Object.entries(STATUS_KEYWORD_HELP).forEach(([key, desc]) => pushEntry({ kind: "status", name: key, body: desc, source_note: "PTU status glossary" }));
  (characterData?.skills || []).forEach((skill) => pushEntry({ kind: "skill", name: skill, body: _getSkillDescription(skill), source_note: "PTU 1.05 Core" }));
  (masterData?.pokemon?.capabilities || []).forEach((cap) => pushEntry({ kind: "capability", name: cap.name, body: cap.description || "", source_note: _builderSourceNote("capability", cap) }));
  (masterData?.pokemon?.species || []).forEach((entry) => pushEntry({
    kind: "species",
    name: entry.name,
    body: _speciesRuleText(entry),
    tags: `${(entry.types || []).join(" ")} ${(entry.capabilities || []).join(" ")}`.trim(),
    source_note: _builderSourceNote("species", entry),
    raw_entry: entry,
  }));
  (characterData?.classes || []).forEach((entry) => pushEntry({
    kind: "class",
    name: entry.name,
    body: [entry.effects || "", ...(Array.isArray(entry.mechanics) ? entry.mechanics.map((item) => item.effects || "") : [])].filter(Boolean).join("\n"),
    prerequisites: entry.prerequisites || "",
    frequency: entry.frequency || "",
    tags: Array.isArray(entry.tags) ? entry.tags.join(", ") : "",
    source_note: _builderSourceNote("class", entry),
    raw_entry: entry,
  }));
  (characterData?.features || []).forEach((entry) => pushEntry({
    kind: "feature",
    name: entry.name,
    body: [entry.effects || "", ...(Array.isArray(entry.mechanics) ? entry.mechanics.map((item) => item.effects || "") : [])].filter(Boolean).join("\n"),
    prerequisites: entry.prerequisites || "",
    frequency: entry.frequency || "",
    tags: Array.isArray(entry.tags) ? entry.tags.join(", ") : "",
    source_note: _builderSourceNote("feature", entry),
    raw_entry: entry,
  }));
  (characterData?.edges || []).forEach((entry) => pushEntry({
    kind: "edge",
    name: entry.name,
    body: entry.effects || entry.description || "",
    prerequisites: entry.prerequisites || "",
    frequency: entry.frequency || "",
    tags: Array.isArray(entry.tags) ? entry.tags.join(", ") : "",
    source_note: _builderSourceNote("edge", entry),
    raw_entry: entry,
  }));
  (characterData?.poke_edges || []).forEach((entry) => pushEntry({
    kind: "poke edge",
    name: entry.name,
    body: entry.effects || entry.description || "",
    prerequisites: entry.prerequisites || "",
    frequency: entry.frequency || "",
    tags: Array.isArray(entry.tags) ? entry.tags.join(", ") : "",
    source_note: _builderSourceNote("poke edge", entry),
    raw_entry: entry,
  }));
  (masterData?.pokemon?.moves || []).forEach((entry) => pushEntry({
    kind: "move",
    name: entry.name,
    body: `${_moveRulesText(entry)}\n${entry.keywords || ""}\n${entry.frequency || entry.freq || ""}`,
    frequency: entry.frequency || entry.freq || "",
    tags: Array.isArray(entry.keywords) ? entry.keywords.join(", ") : String(entry.keywords || ""),
    source_note: _builderSourceNote("move", entry),
    raw_entry: entry,
  }));
  (masterData?.pokemon?.abilities || []).forEach((entry) => pushEntry({
    kind: "ability",
    name: entry.name,
    body: `${entry.effect || entry.effect_2 || ""}\n${entry.trigger || ""}\n${entry.keywords || ""}`,
    frequency: entry.frequency || "",
    tags: Array.isArray(entry.keywords) ? entry.keywords.join(", ") : String(entry.keywords || ""),
    source_note: _builderSourceNote("ability", entry),
    raw_entry: entry,
  }));
  _flattenGlossaryItemSources().forEach((entry) => pushEntry({
    kind: "item",
    name: entry.name,
    body: `${entry.description || entry.buff || entry.desc || ""}\n${entry.category || ""}\n${entry.slot || ""}`,
    tags: `${entry.category || ""} ${entry.slot || ""}`.trim(),
    source_note: _builderSourceNote("item", entry),
    raw_entry: entry,
  }));

  rulebookGlossaryIndexCache = entries.sort((a, b) => String(a.name).localeCompare(String(b.name)));
  return rulebookGlossaryIndexCache;

}



function _eli5RuleEntrySummary(entry) {

  if (!entry) return "No rule details available.";
  if (entry.kind === "species") return `This species entry tells you the form data the builder is using. Main data: ${_firstSentence(entry.body || "", "No summary available.")}`;
  if (entry.kind === "class") return `This class sets a build direction. Main rule: ${_firstSentence(entry.body || "", "No summary available.")}`;
  if (entry.kind === "feature") return `This is a larger trainer rule or class benefit. Main rule: ${_firstSentence(entry.body || "", "No summary available.")}`;
  if (entry.kind === "edge") return _eli5EdgeSummary(entry.raw_entry || entry);
  if (entry.kind === "poke edge") return _eli5EdgeSummary(entry.raw_entry || entry, { forPokemon: true });
  if (entry.kind === "keyword" || entry.kind === "status") return _firstSentence(entry.body || "", "No summary available.");
  return _firstSentence(entry.body || "", "No summary available.");

}



function showSpeciesDetail(nameOrEntry) {

  const entry = typeof nameOrEntry === "string" ? _getPokemonSpeciesEntry(nameOrEntry) : nameOrEntry;
  if (!entry) return;

  const modal = document.createElement("div");
  modal.className = "char-connection-modal";
  const box = document.createElement("div");
  box.className = "char-connection-box";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = `Species: ${entry.name || "Unknown Species"}`;
  box.appendChild(title);
  _appendDetailBlock(box, "Rules Text", _speciesRuleText(entry) || "No species details available.");
  _appendDetailBlock(box, "Simple Guide", `This species entry tells you the form, stats, movement, and capabilities the builder is using for ${entry.name || "this Pokemon"}.`, { muted: true });
  _appendGlossaryBlock(box, _speciesRuleText(entry), "Glossary");
  _appendDetailBlock(box, "Source", _builderSourceNote("species", entry));
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

}



function showGlossaryReferenceDetail(entry) {

  if (!entry) return;
  if (entry.kind === "species") return void showSpeciesDetail(entry.raw_entry || entry.name);
  if (entry.kind === "skill") return void showSkillDetail(entry.name);
  if (entry.kind === "capability") return void showCapabilityDetail(entry.name);
  if (entry.kind === "move") return void showMoveDetail(entry.name);
  if (entry.kind === "ability") return void showAbilityDetail(entry.name);
  if (entry.kind === "item") return void showItemDetail(entry.raw_entry || entry, "item");

  const modal = document.createElement("div");
  modal.className = "char-connection-modal";
  const box = document.createElement("div");
  box.className = "char-connection-box";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = `${entry.category}: ${entry.name}`;
  box.appendChild(title);
  _appendDetailBlock(box, "Simple Guide", _eli5RuleEntrySummary(entry));
  if (entry.prerequisites) _appendDetailBlock(box, "Prerequisites", entry.prerequisites);
  if (entry.frequency) _appendDetailBlock(box, "Frequency", entry.frequency);
  _appendDetailBlock(box, "Rules Text", entry.body || "No rules text available.");
  _appendGlossaryBlock(box, `${entry.body || ""}\n${entry.prerequisites || ""}\n${entry.frequency || ""}`, "Glossary");
  if (entry.source_note) _appendDetailBlock(box, "Source", entry.source_note);
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

}



function _builderUsefulChartsUrls() {

  return ["../useful_charts.json", "useful_charts.json"];

}



async function _ensureUsefulChartsData(urls = _builderUsefulChartsUrls()) {

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
      td.textContent = _hasDisplayValue(value) ? String(value) : "-";
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
    const metaBits = [
      item.action ? `Action: ${item.action}` : "",
      item.ac ? `AC ${item.ac}` : "",
      item.move_class ? `Class: ${item.move_class}` : "",
      item.range ? `Range: ${item.range}` : "",
      item.trigger ? `Trigger: ${item.trigger}` : ""
    ].filter(Boolean);
    if (metaBits.length) {
      const meta = document.createElement("div");
      meta.className = "char-feature-meta";
      meta.textContent = metaBits.join(" | ");
      card.appendChild(meta);
    }
    if (item.effect) _appendDetailBlock(card, "Effect", item.effect);
    if (item.special) _appendDetailBlock(card, "Special", item.special, { muted: true });
    if (item.note) _appendDetailBlock(card, "Note", item.note, { muted: true });
    if (Array.isArray(item.details) && item.details.length) {
      const label = document.createElement("div");
      label.className = "char-field-note";
      label.textContent = "Details";
      card.appendChild(label);
      _appendUsefulChartList(card, item.details);
    }
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
    const sub = document.createElement("div");
    sub.className = "char-field-note";
    sub.textContent = title;
    parent.appendChild(sub);
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
    jump.className = "char-pill is-muted char-glossary-chip";
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



async function showUsefulChartsModal() {

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
  intro.textContent = "Quick-reference tables for experience, damage, type matchups, maneuvers, natures, capture, status effects, power, weight, and contests.";
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



function _renderUsefulChartsPanel(container) {

  if (!container) return;
  const panel = document.createElement("div");
  panel.className = "char-summary-box char-glossary-panel";
  const title = document.createElement("div");
  title.className = "char-section-title";
  title.textContent = "Useful Charts";
  panel.appendChild(title);
  const hint = document.createElement("div");
  hint.className = "char-feature-meta";
  hint.textContent = "Open the shared quick-reference charts used across PTUWeb and the Character Builder.";
  panel.appendChild(hint);
  const row = document.createElement("div");
  row.className = "char-pill-list";
  ["Experience", "Damage", "Type", "Maneuvers", "Nature", "Capture", "Status", "Power"].forEach((label) => {
    const pill = document.createElement("span");
    pill.className = "char-pill is-muted char-glossary-chip";
    pill.textContent = label;
    row.appendChild(pill);
  });
  panel.appendChild(row);
  const actions = document.createElement("div");
  actions.className = "char-action-row";
  const open = document.createElement("button");
  open.type = "button";
  open.className = "char-mini-button";
  open.textContent = "Open Useful Charts";
  open.addEventListener("click", () => showUsefulChartsModal().catch(alertError));
  actions.appendChild(open);
  panel.appendChild(actions);
  container.appendChild(panel);

}


function _renderRulebookGlossaryPanel(container) {

  if (!container) return;

  const panel = document.createElement("details");
  panel.className = "char-summary-box char-glossary-panel";
  panel.open = !!characterState.glossary_open;
  panel.addEventListener("toggle", () => {
    characterState.glossary_open = panel.open;
    saveCharacterToStorage();
  });

  const summary = document.createElement("summary");
  summary.className = "char-section-title";
  summary.textContent = "Rulebook Glossary";
  panel.appendChild(summary);

  const hint = document.createElement("div");
  hint.className = "char-feature-meta";
  hint.textContent = "Search rules, keywords, statuses, species, classes, features, edges, moves, abilities, items, skills, and capabilities.";
  panel.appendChild(hint);

  const toolbar = document.createElement("div");
  toolbar.className = "char-list-toolbar";
  const search = document.createElement("input");
  search.className = "char-search";
  search.type = "search";
  search.placeholder = "Search any rule in the game";
  search.value = characterState.glossary_query || "";
  search.addEventListener("input", () => {
    characterState.glossary_query = search.value;
    saveCharacterToStorage();
    renderCharacterStep();
  });
  const category = document.createElement("select");
  category.className = "char-select";
  [
    ["all", "All Rules"],
    ["keyword", "Keywords"],
    ["status", "Statuses"],
    ["class", "Classes"],
    ["feature", "Features"],
    ["edge", "Edges"],
    ["poke edge", "Poke Edges"],
    ["move", "Moves"],
    ["ability", "Abilities"],
    ["item", "Items"],
    ["skill", "Skills"],
    ["capability", "Capabilities"],
  ].forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    if ((characterState.glossary_category || "all") === value) option.selected = true;
    category.appendChild(option);
  });
  category.addEventListener("change", () => {
    characterState.glossary_category = category.value;
    saveCharacterToStorage();
    renderCharacterStep();
  });
  const clear = document.createElement("button");
  clear.type = "button";
  clear.className = "char-mini-button";
  clear.textContent = "Clear";
  clear.addEventListener("click", () => {
    characterState.glossary_query = "";
    characterState.glossary_category = "all";
    saveCharacterToStorage();
    renderCharacterStep();
  });
  toolbar.appendChild(search);
  toolbar.appendChild(category);
  toolbar.appendChild(clear);
  panel.appendChild(toolbar);

  const quickRow = document.createElement("div");
  quickRow.className = "char-pill-list";
  ["Scene", "Daily", "Swift", "Interrupt", "Shift", "Priority", "DB", "Critical", "Evasion", "Flinch"].forEach((term) => {
    const pill = document.createElement("button");
    pill.type = "button";
    pill.className = "char-pill is-muted char-glossary-chip";
    pill.textContent = term;
    pill.addEventListener("click", () => {
      characterState.glossary_query = term;
      characterState.glossary_open = true;
      saveCharacterToStorage();
      renderCharacterStep();
    });
    quickRow.appendChild(pill);
  });
  panel.appendChild(quickRow);

  const query = _normalizeSearchText(characterState.glossary_query || "");
  const categoryFilter = String(characterState.glossary_category || "all").trim().toLowerCase();
  const results = _buildRulebookGlossaryIndex()
    .filter((entry) => (categoryFilter === "all" ? true : String(entry.kind || "").toLowerCase() === categoryFilter))
    .filter((entry) => (!query ? true : entry.search_blob.includes(query)))
    .sort((a, b) => {
      const aStarts = query && _normalizeSearchText(a.name).startsWith(query) ? 0 : 1;
      const bStarts = query && _normalizeSearchText(b.name).startsWith(query) ? 0 : 1;
      if (aStarts !== bStarts) return aStarts - bStarts;
      return String(a.name).localeCompare(String(b.name));
    })
    .slice(0, query ? 30 : 14);

  const count = document.createElement("div");
  count.className = "char-count";
  count.textContent = query ? `${results.length} result(s) shown` : "Browse common rules or search for a specific term.";
  panel.appendChild(count);

  const list = document.createElement("div");
  list.className = "char-glossary-results";
  results.forEach((entry) => {
    const row = document.createElement("div");
    row.className = "char-glossary-result";
    const top = document.createElement("div");
    top.className = "char-action-row";
    const name = document.createElement("button");
    name.type = "button";
    name.className = "char-glossary-link";
    name.textContent = entry.name;
    name.addEventListener("click", () => showGlossaryReferenceDetail(entry));
    const meta = document.createElement("span");
    meta.className = "char-pill is-muted";
    meta.textContent = entry.category;
    top.appendChild(name);
    top.appendChild(meta);
    row.appendChild(top);
    const summaryLine = document.createElement("div");
    summaryLine.className = "char-feature-meta";
    summaryLine.textContent = _firstSentence(entry.body || entry.source_note || "", entry.source_note || "No summary available.");
    row.appendChild(summaryLine);
    if (entry.source_note) {
      const source = document.createElement("div");
      source.className = "char-feature-meta";
      source.textContent = entry.source_note;
      row.appendChild(source);
    }
    list.appendChild(row);
  });
  if (!results.length) {
    const empty = document.createElement("div");
    empty.className = "char-feature-meta";
    empty.textContent = "No matching rules found. Try a move name, status, keyword, class, feature, edge, item, or skill.";
    list.appendChild(empty);
  }
  panel.appendChild(list);
  container.appendChild(panel);

}



function _appendDetailNote(parent, kind, entry) {



  if (!parent) return;



  const note = _builderSourceNote(kind, entry);



  if (!note) return;



  const el = document.createElement("div");



  el.className = "char-detail-note";



  el.textContent = note;



  parent.appendChild(el);



}







function _getMoveDetail(name) {



  const moves = masterData?.pokemon?.moves || [];



  const key = _normalizeMoveKey(name);


  return moves.find((move) => _normalizeMoveKey(move.name) === key) || null;


}







function _getAbilityDetail(name) {



  const abilities = masterData?.pokemon?.abilities || [];



  const key = _normalizeSearchText(name);



  let entry = abilities.find((ab) => _normalizeSearchText(ab.name) === key) || null;



  if (!entry && masterData?.pokemon?.pokedex_abilities) {



    const map = masterData.pokemon.pokedex_abilities || {};



    Object.entries(map).some(([abilityName, value]) => {



      if (_normalizeSearchText(abilityName) === key) {



        entry = { name: abilityName, effect: value?.effect || value?.description || "" };



        return true;



      }



      return false;



    });



  }



  return entry;



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



  const caps = masterData?.pokemon?.capabilities || [];



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







function _minEvolutionLevelForSpecies(speciesName) {



  const map = _activeEvolutionLevelMap();



  if (!map || typeof map !== "object") return null;



  const candidates = Array.from(new Set([



    ..._speciesLookupCandidates(speciesName),



    ..._learnsetKeyCandidates(speciesName),



    ..._abilityKeyCandidates(speciesName).map((value) => _normalizeSpeciesKey(value)),



  ])).filter(Boolean);



  for (const key of candidates) {



    const value = Number(map[key]);



    if (Number.isFinite(value) && value > 1) return value;



  }



  const candidateKeys = candidates.flatMap((key) => _speciesLookupComparableKeys(key));



  for (const [key, rawValue] of Object.entries(map)) {



    if (!_keysIntersect(_speciesLookupComparableKeys(key), candidateKeys)) continue;



    const value = Number(rawValue);



    if (Number.isFinite(value) && value > 1) return value;



  }



  return null;



}



function _builderRawSourceLabel(rawSource) {

  const sourceText = String(rawSource || "").trim();
  const normalized = sourceText.toLowerCase();

  if (normalized === "fancy_abilities_csv") return "Fancy Abilities CSV";
  if (normalized === "fancy_moves_csv") return "Fancy Moves CSV";
  if (normalized === "fancy_inventory_csv") return "Fancy Inventory CSV";
  if (normalized === "species_json") return "Official PTU Species Dataset";
  if (normalized === "swsh_galardex_json") return "SwSh GalarDex + Armor/Crown";
  if (normalized === "hisuidex_json") return "HisuiDex / Arceus";
  if (normalized === "porygon_dream_of_mareep") return "Do Porygon Dream of Mareep?";
  if (normalized === "game_of_throhs") return "Game of Throhs";
  if (normalized === "blessed_and_damned") return "Blessed and the Damned";
  if (normalized === "may_2015_playtest_packet") return "PTU May 2015 Playtest Packet";
  if (normalized === "september_2015_playtest_packet") return "PTU September 2015 Playtest Packet";
  if (normalized === "swsh_references_pdf") return "SwSh + Armor/Crown References";
  if (normalized === "sumo_references_pdf") return "SuMo References";
  if (normalized === "hisui_references_pdf") return "Arceus References";
  if (normalized === "character_creation_json") return "Character Creation JSON";
  if (sourceText) {
    return sourceText
      .replace(/[_-]+/g, " ")
      .replace(/\bjson\b/gi, "JSON")
      .replace(/\bcsv\b/gi, "CSV")
      .trim();
  }
  return "";

}



function _builderSourceLabel(kind, entry) {



  const rawSource = String(entry?.source || entry?.data_source || entry?.origin || "").trim();
  const rawLabel = _builderRawSourceLabel(rawSource);
  if (rawLabel) return rawLabel;



  const key = String(kind || "").trim().toLowerCase();
  const trainerMeta = _builderMasterTrainerSourceMeta(kind, entry);
  if (trainerMeta?.source) return trainerMeta.source;

  const playtestMeta = _builderPlaytestPacketMeta(kind, entry);
  if (playtestMeta?.source) return playtestMeta.source;



if (key === "move") return "AutoPTU Move Dataset";

  if (key === "species") return "Official PTU Species Dataset";



  if (key === "ability") return "AutoPTU Ability Dataset";



  if (key === "item") return "AutoPTU Inventory Dataset";



  return "AutoPTU Character Creation Dataset";



}



function _builderVersionLabel(kind, entry) {



  const explicit = String(entry?.version || entry?.content_version || "").trim();



  if (explicit) return explicit;

  const trainerMeta = _builderMasterTrainerSourceMeta(kind, entry);
  if (trainerMeta?.version) return trainerMeta.version;

  const playtestMeta = _builderPlaytestPacketMeta(kind, entry);
  if (playtestMeta?.version) return playtestMeta.version;



  if (isPlaytestEntry(entry)) return "Playtest";



  const key = String(kind || "").trim().toLowerCase();



if (["class", "feature", "edge", "poke edge", "poke_edge", "rule"].includes(key)) return "Official";

  if (key === "species") return "Official";



  return "Builder Dataset";



}


function _builderMasterTrainerSourceMeta(kind, entry) {

  if (!masterData || !masterData.trainer || !entry) return null;

  const normalizedKind = String(kind || "").trim().toLowerCase();
  const normalizedName = _normalizeSearchText(entry?.name || "");
  if (!normalizedName) return null;

  let collection = null;
  if (normalizedKind === "class") collection = masterData.trainer.classes;
  else if (normalizedKind === "feature") collection = masterData.trainer.features;
  else if (normalizedKind === "edge") collection = masterData.trainer.edges;
  else if (normalizedKind === "poke edge" || normalizedKind === "poke_edge") collection = masterData.trainer.poke_edges;
  if (!Array.isArray(collection)) return null;

  const match = collection.find((item) => _normalizeSearchText(item?.name || "") === normalizedName);
  if (!match) return null;

  const source = _builderRawSourceLabel(match?.source || match?.data_source || match?.origin || "");
  const version = String(match?.version || "").trim();
  if (!source && !version) return null;
  return { source, version };

}



function _builderPlaytestPacketMeta(kind, entry) {

  const key = String(kind || "").trim().toLowerCase();
  const name = String(entry?.name || "").trim();

  if (!name) return null;

  const mayNames = new Set([
    "Backpacker",
    "Item Mastery",
    "Equipment Savant",
    "Hero's Journey",
    "Call to Adventure",
    "Frisk",
    "Handyman",
    "Hat Trick",
    "Movement Mastery",
    "Sole Power",
    "Wayfarer",
    "Wear It Better",
    "Traditional Medicine Reference [5-15 Playtest]",
    "Cap Cannon [5-15 Playtest]",
    "Bean Cap [5-15 Playtest]",
    "Glue Cap [5-15 Playtest]",
    "Net Cap [5-15 Playtest]",
  ]);

  const septemberNames = new Set([
    "Cheerleader [Playtest]",
    "Moment of Action [Playtest]",
    "Cheers [Playtest]",
    "Bring It On! [Playtest]",
    "Inspirational Support [Playtest]",
    "Go, Fight, Win! [Playtest]",
    "Keep Fighting! [Playtest]",
    "Medic",
    "Front Line Healer",
    "Medical Techniques [Medic]",
    "I'm a Doctor",
    "Proper Care",
    "Stay With Us!",
    "Combat Medic's Primer [9-15 Playtest]",
    "Shield [9-15 Playtest]",
    "Light Armor [9-15 Playtest]",
    "Special Armor [9-15 Playtest]",
    "Heavy Armor [9-15 Playtest]",
    "Defense Curl",
    "Hold Hands",
    "Withdraw",
  ]);

  const acceptKinds = new Set(["class", "feature", "move", "item"]);
  if (!acceptKinds.has(key)) return null;
  if (mayNames.has(name)) return { source: "PTU May 2015 Playtest Packet", version: "PTU May 2015 Playtest Packet" };
  if (septemberNames.has(name)) return { source: "PTU September 2015 Playtest Packet", version: "PTU September 2015 Playtest Packet" };
  return null;

}



function _builderSourceNote(kind, entry) {



  const source = _builderSourceLabel(kind, entry);



  const version = _builderVersionLabel(kind, entry);



  const primary = `Source: ${source} | Version: ${version}`;
  const extras = _builderSupplementalSourceLines(kind, entry);
  return extras.length ? `${primary} | Also from: ${extras.join(", ")}` : primary;



}



function _builderSupplementalSourceLines(kind, entry) {



  const items = Array.isArray(entry?.supplemental_sources) ? entry.supplemental_sources : [];



  const lines = [];



  items.forEach((item) => {
    const source = _builderSourceLabel(kind, item);
    const version = _builderVersionLabel(kind, item);
    const text = `${source}${version ? ` (${version})` : ""}`;
    if (!lines.includes(text)) lines.push(text);
  });



  return lines;



}



function _moveDatasetSourceNote(entry) {



  return _builderSourceNote("move", entry);



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

function _abilitySlotCountForLevel(level) {

  const safeLevel = Math.max(1, Math.min(100, Number(level || 1)));

  if (safeLevel >= 40) return 3;

  if (safeLevel >= 20) return 2;

  return 1;

}




function _abilitySlotCountForBuild(level, build) {



  return _abilitySlotCountForLevel(level) + _pokemonBonusAbilitySlots(build);



}



function _formatSuggestionSentence(prefix, items, fallback = "") {



  const list = Array.isArray(items) ? items.filter(Boolean) : [];



  if (!list.length) return fallback;



  return `${prefix}${list.join(", ")}.`;



}



function _suggestLegalAbilitiesForSpecies(speciesEntry, level, excludeName = "", limit = 4) {



  if (!speciesEntry) return [];



  const pools = _getAbilityPoolsForSpecies(speciesEntry.name);



  if (!pools) return [];



  const allowed = _abilityAllowedByLevel(pools, level);



  const excludeKey = _normalizeSearchText(excludeName);



  const ordered = [];



  const pushAll = (list) => {



    (list || []).forEach((name) => {



      const trimmed = String(name || "").trim();



      const key = _normalizeSearchText(trimmed);



      if (!trimmed || key === excludeKey || !allowed.has(key)) return;



      if (!ordered.some((entry) => _normalizeSearchText(entry) === key)) ordered.push(trimmed);



    });



  };



  pushAll(pools.starting);



  pushAll(pools.basic);



  if (Number(level || 1) >= 20) pushAll(pools.advanced);



  if (Number(level || 1) >= 40) pushAll(pools.high);



  return ordered.slice(0, Math.max(1, Number(limit || 4)));



}



function _pokemonBuildStatRows(speciesEntry, build) {



  const baseStats = speciesEntry?.base_stats || {};
  const baseStatBonus = _pokemonGlobalBaseStatBonus(build);



  const overrideStats = build?.stats && typeof build.stats === "object" ? build.stats : {};



  return [



    {



      key: "hp",



      label: "HP",



      base: Number(baseStats.hp ?? 0) + baseStatBonus,



      value: Object.prototype.hasOwnProperty.call(overrideStats, "hp") ? Number(overrideStats.hp ?? 0) : Number(baseStats.hp ?? 0) + baseStatBonus,



    },



    {



      key: "atk",



      label: "Atk",



      base: Number(baseStats.attack ?? 0) + baseStatBonus,



      value: Object.prototype.hasOwnProperty.call(overrideStats, "atk") ? Number(overrideStats.atk ?? 0) : Number(baseStats.attack ?? 0) + baseStatBonus,



    },



    {



      key: "def",



      label: "Def",



      base: Number(baseStats.defense ?? 0) + baseStatBonus,



      value: Object.prototype.hasOwnProperty.call(overrideStats, "def") ? Number(overrideStats.def ?? 0) : Number(baseStats.defense ?? 0) + baseStatBonus,



    },



    {



      key: "spatk",



      label: "SpA",



      base: Number(baseStats.special_attack ?? 0) + baseStatBonus,



      value: Object.prototype.hasOwnProperty.call(overrideStats, "spatk")



        ? Number(overrideStats.spatk ?? 0)



        : Number(baseStats.special_attack ?? 0) + baseStatBonus,



    },



    {



      key: "spdef",



      label: "SpD",



      base: Number(baseStats.special_defense ?? 0) + baseStatBonus,



      value: Object.prototype.hasOwnProperty.call(overrideStats, "spdef")



        ? Number(overrideStats.spdef ?? 0)



        : Number(baseStats.special_defense ?? 0) + baseStatBonus,



    },



    {



      key: "spd",



      label: "Spd",



      base: Number(baseStats.speed ?? 0) + baseStatBonus,



      value: Object.prototype.hasOwnProperty.call(overrideStats, "spd") ? Number(overrideStats.spd ?? 0) : Number(baseStats.speed ?? 0) + baseStatBonus,



    },



  ];



}




function _pokemonHasPokeEdge(build, edgeName) {



  const edges = Array.isArray(build?.poke_edges) ? build.poke_edges : [];



  const target = _normalizeSearchText(edgeName);



  return edges.some((name) => _normalizeSearchText(name) === target);



}




function _pokemonPokeEdgeCount(build, edgeName) {
  const edges = Array.isArray(build?.poke_edges) ? build.poke_edges : [];
  const target = _normalizeSearchText(edgeName);
  return edges.filter((name) => _normalizeSearchText(name) === target).length;
}




function _pokemonGlobalBaseStatBonus(build) {



  return _pokemonHasPokeEdge(build, "Underdog's Strength") || _pokemonHasPokeEdge(build, "Underdog’s Strength") ? 1 : 0;



}




function _pokemonBonusStatPoints(speciesEntry, build) {



  let bonus = 0;

  if (_pokemonHasPokeEdge(build, "Realized Potential")) {
    const stats = speciesEntry?.base_stats || {};
    const total =
      Number(stats.hp ?? 0) +
      Number(stats.attack ?? 0) +
      Number(stats.defense ?? 0) +
      Number(stats.special_attack ?? 0) +
      Number(stats.special_defense ?? 0) +
      Number(stats.speed ?? 0);
    bonus += Math.max(0, 45 - total);
  }

  const mixedSweeperRanks = ["Mixed Sweeper Rank 1", "Mixed Sweeper Rank 2", "Mixed Sweeper Rank 3"];
  mixedSweeperRanks.forEach((name) => {
    if (_pokemonHasPokeEdge(build, name)) bonus += 3;
  });

  return bonus;

}




function _pokemonBonusTutorPoints(build) {



  return _pokemonHasPokeEdge(build, "Expand Horizons") ? 3 : 0;



}



function _pokemonBaseTutorPoints(level) {



  const safeLevel = Math.max(1, _normalizeInteger(level, 1, 1, 100));



  return 1 + Math.floor(safeLevel / 5);



}




function _pokemonEffectiveTutorPoints(build) {



  return Math.max(0, _pokemonBaseTutorPoints(build?.level || 1) + _normalizeInteger(build?.tutor_points, 0, -999, 999) + _pokemonBonusTutorPoints(build));



}




function _pokemonBonusAbilitySlots(build) {



  return _pokemonHasPokeEdge(build, "Ability Mastery") ? 1 : 0;



}




function _pokemonEffectiveMovement(speciesEntry, build) {



  const movement = { ...(speciesEntry?.movement || {}) };
  const bonuses = {
    "Advanced Mobility (Overland)": "overland",
    "Advanced Mobility (Sky)": "sky",
    "Advanced Mobility (Swim)": "swim",
    "Advanced Mobility (Levitate)": "levitate",
    "Advanced Mobility (Burrow)": "burrow",
    "Advanced Mobility (Teleporter)": "teleporter",
  };
  Object.entries(bonuses).forEach(([edgeName, key]) => {
    if (_pokemonHasPokeEdge(build, edgeName)) movement[key] = Number(movement[key] || 0) + 2;
  });
  return movement;



}




function _pokemonEffectiveSkillMap(speciesEntry, build) {



  const skills = { ...(speciesEntry?.skills || {}) };
  const bonuses = {
    "Skill Improvement (Acrobatics)": "acrobatics",
    "Skill Improvement (Athletics)": "athletics",
    "Skill Improvement (Charm)": "charm",
    "Skill Improvement (Combat)": "combat",
    "Skill Improvement (Command)": "command",
    "Skill Improvement (Focus)": "focus",
    "Skill Improvement (General Ed)": "gen_ed",
    "Skill Improvement (Guile)": "guile",
    "Skill Improvement (Intimidate)": "intimidate",
    "Skill Improvement (Intuition)": "intuition",
    "Skill Improvement (Medicine Ed)": "med_ed",
    "Skill Improvement (Occult Ed)": "occult_ed",
    "Skill Improvement (Perception)": "perception",
    "Skill Improvement (Pokémon Ed)": "poke_ed",
    "Skill Improvement (Stealth)": "stealth",
    "Skill Improvement (Survival)": "survival",
    "Skill Improvement (Technology Ed)": "tech_ed",
  };
  Object.entries(bonuses).forEach(([edgeName, key]) => {
    if (_pokemonHasPokeEdge(build, edgeName)) skills[key] = Number(skills[key] || 0) + 1;
  });
  if (_pokemonHasPokeEdge(build, "Digital Avatar")) skills.tech_ed = Math.max(3, Number(skills.tech_ed || 0));
  return skills;



}




function _pokemonEffectiveCapabilityValues(speciesEntry, build) {



  const movement = _pokemonEffectiveMovement(speciesEntry, build);
  if (_pokemonHasPokeEdge(build, "Capability Training (Power)")) movement.power = Number(movement.power || 0) + 1;
  if (_pokemonHasPokeEdge(build, "Capability Training (High Jump)")) movement.h_jump = Number(movement.h_jump || 0) + 1;
  if (_pokemonHasPokeEdge(build, "Capability Training (Long Jump)")) movement.l_jump = Number(movement.l_jump || 0) + 1;
  if (_pokemonHasPokeEdge(build, "Precise Threading")) {
    movement.threaded_range = 6;
    movement.threaded_ac = 3;
  }
  if (_pokemonHasPokeEdge(build, "Extended Invisibility")) movement.invisibility_minutes = 8;
  if (_pokemonHasPokeEdge(build, "Far Reading")) movement.telepath_focus_bonus = 2;
  if (_pokemonHasPokeEdge(build, "TK Mastery")) movement.telekinetic_focus_bonus = 2;
  if (_pokemonHasPokeEdge(build, "Seismometer")) movement.tremorsense_bonus = Number(_pokemonEffectiveSkillMap(speciesEntry, build).perception || 0);
  if (_pokemonHasPokeEdge(build, "Trail Sniffer")) movement.tracker_bonus = Number(_pokemonEffectiveSkillMap(speciesEntry, build).focus || 0);
  if (_pokemonHasPokeEdge(build, "Enticing Bait")) movement.alluring_bonus = Math.max(
    Number(_pokemonEffectiveSkillMap(speciesEntry, build).athletics || 0),
    Number(_pokemonEffectiveSkillMap(speciesEntry, build).focus || 0)
  );
  if (_pokemonHasPokeEdge(build, "Gravity Training")) movement.gravitic_steps = Number(movement.gravitic_steps || 0) + 2;
  return movement;



}


function _pokemonEffectiveCapabilityNames(speciesEntry, build) {

  const names = new Set(_normalizeStringList(speciesEntry?.capabilities));
  if (_pokemonHasPokeEdge(build, "Aura Pulse")) names.add("Aura Pulse");
  if (_pokemonHasPokeEdge(build, "Psychic Navigator")) names.add("Psychic Navigator");
  return Array.from(names);

}


function _pokemonPokeEdgeEffectNotes(speciesEntry, build) {

  const notes = [];
  const capabilityValues = _pokemonEffectiveCapabilityValues(speciesEntry, build);
  const skills = _pokemonEffectiveSkillMap(speciesEntry, build);
  if (_pokemonHasPokeEdge(build, "Attack Conflict")) notes.push("Attack Conflict: Attack/Special Attack base-relation restriction relaxed.");
  if (_pokemonHasPokeEdge(build, "Precise Threading")) notes.push(`Precise Threading: Threaded usable at range ${capabilityValues.threaded_range} with AC ${capabilityValues.threaded_ac}.`);
  if (_pokemonHasPokeEdge(build, "Extended Invisibility")) notes.push(`Extended Invisibility: remain Invisible up to ${capabilityValues.invisibility_minutes} minutes.`);
  if (_pokemonHasPokeEdge(build, "Far Reading")) notes.push(`Far Reading: Telepath range uses Focus as ${Number(skills.focus || 0) + 2}.`);
  if (_pokemonHasPokeEdge(build, "TK Mastery")) notes.push(`TK Mastery: Telekinetic capability uses Focus as ${Number(skills.focus || 0) + 2}.`);
  if (_pokemonHasPokeEdge(build, "Seismometer")) notes.push(`Seismometer: Tremorsense range +${capabilityValues.tremorsense_bonus || 0}m from Perception.`);
  if (_pokemonHasPokeEdge(build, "Trail Sniffer")) notes.push(`Trail Sniffer: Tracker rolls gain +${capabilityValues.tracker_bonus || 0} from Focus.`);
  if (_pokemonHasPokeEdge(build, "Enticing Bait")) notes.push(`Enticing Bait: Alluring rolls gain +${capabilityValues.alluring_bonus || 0}.`);
  if (_pokemonHasPokeEdge(build, "Digital Avatar")) notes.push("Digital Avatar: may dive into computer systems and has at least Technology Education 3.");
  if (_pokemonHasPokeEdge(build, "Gravity Training")) notes.push(`Gravity Training: +${capabilityValues.gravitic_steps || 0} Gravitic Tolerance steps to allocate.`);
  if (_pokemonHasPokeEdge(build, "Vehicle Training")) notes.push("Vehicle Training: may drive appropriately outfitted vehicles as a Standard Action.");
  if (_pokemonHasPokeEdge(build, "Basic Ranged Attacks (Firestarter)")) notes.push("Basic Ranged Attacks: Firestarter Struggle attacks can be used at range 6.");
  if (_pokemonHasPokeEdge(build, "Basic Ranged Attacks (Fountain)")) notes.push("Basic Ranged Attacks: Fountain Struggle attacks can be used at range 6.");
  if (_pokemonHasPokeEdge(build, "Basic Ranged Attacks (Freezer)")) notes.push("Basic Ranged Attacks: Freezer Struggle attacks can be used at range 6.");
  if (_pokemonHasPokeEdge(build, "Basic Ranged Attacks (Guster)")) notes.push("Basic Ranged Attacks: Guster Struggle attacks can be used at range 6.");
  if (_pokemonHasPokeEdge(build, "Basic Ranged Attacks (Materializer)")) notes.push("Basic Ranged Attacks: Materializer Struggle attacks can be used at range 6.");
  if (_pokemonHasPokeEdge(build, "Basic Ranged Attacks (Zapper)")) notes.push("Basic Ranged Attacks: Zapper Struggle attacks can be used at range 6.");
  if (_pokemonHasPokeEdge(build, "Mixed Power [9-15 Playtest]")) notes.push("Mixed Power: grants the Twisted Power ability.");
  if (_pokemonHasPokeEdge(build, "Twisted Power [2-16 Playtest]")) notes.push("Twisted Power: Physical moves add half SpAtk to damage; Special moves add half Atk to damage.");
  return notes;

}


function _pokemonGrantedAbilityNames(build) {

  const out = [];
  if (_pokemonHasPokeEdge(build, "Mixed Power [9-15 Playtest]")) out.push("Twisted Power");
  return out;

}



function _pokemonBuildStatMap(speciesEntry, build) {



  return _pokemonBuildStatRows(speciesEntry, build).reduce((map, stat) => {



    map[stat.key] = Number.isFinite(Number(stat.value)) ? Number(stat.value) : Number(stat.base || 0);



    return map;



  }, {});



}



function _pokemonDerivedStats(speciesEntry, build) {



  const natureAdjusted = _pokemonNatureAdjustedStats(speciesEntry, build);



  const stats = natureAdjusted.effective;



  const level = Math.max(1, Math.min(100, Number(build?.level || 1)));



  const hp = Number(stats.hp || 0);



  const def = Number(stats.def || 0);



  const spdef = Number(stats.spdef || 0);



  const spd = Number(stats.spd || 0);



  const nextThresholdDelta = (value) => {



    const safe = Math.max(0, Number(value || 0));



    const remainder = safe % 5;



    return remainder === 0 ? 5 : 5 - remainder;



  };



  return {



    maxHp: level + hp * 3 + 10,



    physEvasion: Math.floor(def / 5),



    specEvasion: Math.floor(spdef / 5),



    speedEvasion: Math.floor(spd / 5),



    nextPhysEvasionIn: nextThresholdDelta(def),



    nextSpecEvasionIn: nextThresholdDelta(spdef),



    nextSpeedEvasionIn: nextThresholdDelta(spd),



    nature: natureAdjusted.profile,



    effectiveStats: natureAdjusted.effective,



    storedStats: natureAdjusted.stored,



    preNatureStats: natureAdjusted.preNature,



    statMode: natureAdjusted.statMode,



  };



}



function _pokemonStatPointBudget(level, speciesEntry = null, build = null) {



  const safeLevel = Math.max(1, Math.min(100, Number(level || 1)));



  return Math.max(11, safeLevel + 10) + _pokemonBonusStatPoints(speciesEntry, build);



}



function _pokemonStatPointsSpent(speciesEntry, build) {



  const adjusted = _pokemonNatureAdjustedStats(speciesEntry, build);



  return _pokemonBuildStatRows(speciesEntry, { stats: adjusted.preNature }).reduce(
    (total, stat) => total + Math.max(0, Number(stat.value || 0) - Number(stat.base || 0)),
    0
  );



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



  const learnset = speciesEntry ? _getLearnsetForSpecies(speciesEntry.name) : [];



  if (speciesEntry) {
    const adjusted = _pokemonNatureAdjustedStats(speciesEntry, build);

    _pokemonBuildStatRows(speciesEntry, { stats: adjusted.preNature }).forEach((stat) => {

      if (Number(stat.value || 0) < Number(stat.base || 0)) {

        issues.push({

          severity: "error",

          message: `${stat.label} is below ${speciesEntry.name}'s base stat (${stat.value}/${stat.base}).`,

          hint: "Pokemon build stats cannot go below the species base stat in this builder.",

        });

      }

    });



    const spentPoints = _pokemonStatPointsSpent(speciesEntry, build);



    const availablePoints = _pokemonStatPointBudget(safeLevel, speciesEntry, build);



    if (spentPoints > availablePoints) {



      issues.push({



        severity: "error",



        message: `Pokemon stat points exceed budget (${spentPoints}/${availablePoints}) at level ${safeLevel}.`,



        hint: "This builder budgets Pokemon stat points as 11 at level 1, plus 1 more per level after that. Lower some overridden stats or raise the level.",



      });



    }



  }



  const moveAvailability = _pokemonMoveSourceAvailability(speciesEntry, safeLevel, build);
  const effectiveMoveSources = _effectivePokemonMoveSourceMap(build, speciesEntry);



  const moves = Array.isArray(build?.moves) ? build.moves : [];



  const abilities = Array.isArray(build?.abilities) ? build.abilities : [];



  const items = Array.isArray(build?.items) ? build.items : [];



  const pokeEdges = Array.isArray(build?.poke_edges) ? build.poke_edges : [];



  const MAX_ACTIVE_MOVES = _pokemonMoveSlotLimit(build);
  const effectiveMoveCount = _pokemonEffectiveMoveCount(build);
  const freeConnectedMoves = _pokemonAdvancedConnectionFreeMoves(build);
  const sketchSlots = _pokemonSketchSlotLimit(speciesEntry, safeLevel);
  const sketchUsed = _pokemonSketchMovesUsed(build, speciesEntry);
  const tutorMoveCost = 2;
  const tmMoveCost = 1;
  let tmMovesTaken = 0;
  let tutorMovesTaken = 0;
  let eggMovesTaken = 0;



  if (effectiveMoveCount > MAX_ACTIVE_MOVES) {



    issues.push({



      severity: "error",



      message: `Move list exceeds limit (${effectiveMoveCount}/${MAX_ACTIVE_MOVES}).`,
      hint: freeConnectedMoves.size ? `Advanced Connection is currently freeing ${freeConnectedMoves.size} move slot${freeConnectedMoves.size === 1 ? "" : "s"}. Remove some non-connected moves or add another effect that expands the move limit.` : "",



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



      issues.push({



        severity: "error",



        message: `Move not found: ${moveName}.`,



        hint: _formatSuggestionSentence(



          speciesEntry ? `Try one of these ${speciesEntry.name} moves at level ${safeLevel}: ` : "Try a canonical PTU move name. Suggested legal moves: ",



          speciesEntry ? _suggestLegalMovesForSpecies(speciesEntry, safeLevel, moveName, 4) : [],



          "The move name did not match the local move dataset exactly. Try the canonical PTU move name."



        ),



      });



      return;



    }



    if (speciesEntry && learnsetData) {


      const moveKey = _normalizeMoveKey(moveName);



      const sourceMode = effectiveMoveSources[moveKey] || "";
      const sketchEligible = moveAvailability.sketch?.has(moveKey) === true;
      const sketchSlots = _pokemonSketchSlotLimit(speciesEntry, safeLevel);
      const sketchUsed = _pokemonSketchMovesUsed(build, speciesEntry);



      const naturalNow = moveAvailability.natural.has(moveKey);



      const eggEligible = moveAvailability.egg.has(moveKey);



      const tmEligible = moveAvailability.tm.has(moveKey);



      const tutorEligible = moveAvailability.tutor.has(moveKey);



      if (sourceMode === "sketch" && sketchEligible) {
        return;
      }



      if (sourceMode === "egg" && eggEligible) eggMovesTaken += 1;



      if (sourceMode === "tm" && tmEligible) tmMovesTaken += 1;



      if (sourceMode === "tutor" && tutorEligible) tutorMovesTaken += 1;



      const hasSupportedExtraSource = eggEligible || tmEligible || tutorEligible || sketchEligible;
      const selectedExtraSourceIsValid =
        (sourceMode === "egg" && eggEligible) ||
        (sourceMode === "tm" && tmEligible) ||
        (sourceMode === "tutor" && tutorEligible) ||
        (sourceMode === "sketch" && sketchEligible);



      if (!naturalNow && hasSupportedExtraSource && !selectedExtraSourceIsValid && eggEligible && !tutorEligible) {


        issues.push({



          severity: "error",



          message: `Move "${moveName}" requires an Egg source for ${speciesEntry.name}.`,



          hint: `Set this move's source to Egg. In this builder, Egg moves cost ${tutorMoveCost} Tutor Points each.`,



        });



      } else if (!naturalNow && hasSupportedExtraSource && !selectedExtraSourceIsValid && tmEligible && !tutorEligible && !eggEligible) {


        issues.push({



          severity: "error",



          message: `Move "${moveName}" requires a TM source for ${speciesEntry.name}.`,



          hint: `Set this move's source to TM. In this builder, TM moves cost ${tmMoveCost} Tutor Point each.`,



        });



      } else if (!naturalNow && hasSupportedExtraSource && !selectedExtraSourceIsValid && tutorEligible && !tmEligible && !eggEligible) {


        issues.push({



          severity: "error",



          message: `Move "${moveName}" requires a Tutor source for ${speciesEntry.name}.`,



          hint: `Set this move's source to Tutor. In this builder, Tutor moves cost ${tutorMoveCost} Tutor Points each.`,



        });



      } else if (!naturalNow && hasSupportedExtraSource && !selectedExtraSourceIsValid && sketchEligible && !eggEligible && !tmEligible && !tutorEligible) {


        issues.push({



          severity: "error",



          message: `Move "${moveName}" must use Sketch for ${speciesEntry.name}.`,



          hint: "Smeargle learns copied moves through Sketch in this builder. Set the move's source to Sketch.",



        });



      } else if (!naturalNow && hasSupportedExtraSource && !selectedExtraSourceIsValid) {


        issues.push({



          severity: "error",



          message: `Move "${moveName}" needs a matching Egg, TM, or Tutor source for ${speciesEntry.name}.`,



          hint: `This move is legal for ${speciesEntry.name}, but the selected source is not. Choose the matching Level-Up, Egg, TM, or Tutor source.`,



        });



      } else if (!naturalNow && !eggEligible && !tmEligible && !tutorEligible) {


        issues.push({



          severity: "error",



          message: `Move "${moveName}" is not in ${speciesEntry.name}'s learnset at level ${safeLevel}.`,



          hint: _formatSuggestionSentence(



            "Use a level-legal move instead: ",



            _suggestLegalMovesForSpecies(speciesEntry, safeLevel, moveName, 4),



            `${moveName} is not legal here. Pick a move the species already knows at level ${safeLevel}, or a TM/Tutor/Egg move it can actually access.`



          ),



        });



      }



    }



  });



  if (_pokemonHasPokeEdge(build, "Accuracy Training")) {



    (build.poke_edge_choices?.accuracy_training || []).forEach((moveName) => {



      const entry = _getMoveDetail(moveName);



      const acValue = Number(entry?.ac || 0);



      if (!entry || !Number.isFinite(acValue) || acValue < 3) {



        issues.push({



          severity: "error",



          message: `Accuracy Training target "${moveName}" is invalid.`,



          hint: "Accuracy Training only works on moves with AC 3 or higher that this Pokemon currently knows.",



        });



      } else if (!(build.moves || []).some((knownMove) => _normalizeMoveKey(knownMove) === _normalizeMoveKey(moveName))) {



        issues.push({



          severity: "error",



          message: `Accuracy Training target "${moveName}" is not on this Pokemon's move list.`,



          hint: "Choose one of the Pokemon's actual current moves for Accuracy Training.",



        });



      }



    });



  }

  if (sketchSlots > 0 && sketchUsed > sketchSlots) {

    issues.push({

      severity: "error",

      message: `Sketch moves exceed Smeargle's legal Sketch slots (${sketchUsed}/${sketchSlots}).`,

      hint: "Each copied move replaces one legal Sketch slot. Remove a sketched move or keep Sketch itself in one of those slots.",

    });

  }



  if (_pokemonHasPokeEdge(build, "Underdog's Lessons")) {



    const configuredEvolution = String(build.poke_edge_choices?.underdog_lessons?.evolution || "").trim();



    const lessonMoves = _normalizeStringList(build.poke_edge_choices?.underdog_lessons?.moves).slice(0, 3);



    if (!configuredEvolution) {



      issues.push({



        severity: "warn",



        message: "Underdog's Lessons has no chosen final evolution yet.",



        hint: "Choose the final evolution this Pokemon is borrowing lesson moves from.",



      });



    }



    if (lessonMoves.length > 3) {



      issues.push({



        severity: "error",



        message: `Underdog's Lessons exceeds its move limit (${lessonMoves.length}/3).`,



      });



    }



  }



  if (_pokemonHasPokeEdge(build, "Advanced Connection")) {



    const availableConnections = new Set(_pokemonConnectedAbilityChoices(build).map(({ abilityName }) => _normalizeSearchText(abilityName)));



    (build.poke_edge_choices?.advanced_connection || []).forEach((abilityName) => {



      if (!availableConnections.has(_normalizeSearchText(abilityName))) {



        issues.push({



          severity: "error",



          message: `Advanced Connection target "${abilityName}" is not a valid current Connection ability.`,



          hint: "Choose one of this Pokemon's actual current abilities that has the Connection keyword.",



        });



      }



    });



  }



  const tutorPointsAvailable = _pokemonEffectiveTutorPoints(build);



  const tutorPointsRequired = tmMovesTaken * tmMoveCost + tutorMovesTaken * tutorMoveCost + eggMovesTaken * tutorMoveCost;



  const tutorMoveLimit = _pokemonTutorMoveLimit();



  if (tutorPointsRequired > tutorPointsAvailable) {



    issues.push({



      severity: "error",



      message: `Tutor Point spend exceeds available points (${tutorPointsRequired}/${tutorPointsAvailable}).`,



      hint: "TM moves cost 1 Tutor Point each. Tutor and Egg moves cost 2 each. Lower the number of non-level-up moves or raise this Pokemon's Tutor Points.",



    });



  }



  if (tmMovesTaken + tutorMovesTaken > tutorMoveLimit) {



    issues.push({



      severity: "error",



      message: `Tutor/TM-style move limit exceeded (${tmMovesTaken + tutorMovesTaken}/${tutorMoveLimit}).`,



      hint:
        tutorMoveLimit >= 4
          ? "This build is already using the expanded Lifelong Learning tutor-move cap."
          : "Default move-list handling only allows 3 TM/Tutor-style moves unless the trainer has Lifelong Learning.",



    });



  }



  const abilityPools = speciesEntry ? _getAbilityPoolsForSpecies(speciesEntry.name) : null;



  const allowedAbilities = _abilityAllowedByLevel(abilityPools, safeLevel);



  const maxAbilitySlots =

    speciesEntry && abilityPools

      ? Math.max(1, Math.min(_abilitySlotCountForBuild(safeLevel, build), allowedAbilities.size || _abilitySlotCountForBuild(safeLevel, build)))

      : _abilitySlotCountForBuild(safeLevel, build);


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



      issues.push({



        severity: "error",



        message: `Ability not found: ${abilityName}.`,



        hint: _formatSuggestionSentence(



          speciesEntry ? `Try one of these ${speciesEntry.name} abilities at level ${safeLevel}: ` : "Try a canonical PTU ability name. Suggested legal abilities: ",



          speciesEntry ? _suggestLegalAbilitiesForSpecies(speciesEntry, safeLevel, abilityName, 4) : [],



          "The ability name did not match the local ability dataset exactly. Try the canonical PTU ability name."



        ),



      });



      return;



    }



    if (speciesEntry && abilityPools && allowedAbilities.size && !allowedAbilities.has(_normalizeSearchText(abilityName))) {



      issues.push({



        severity: "error",



        message: `Ability "${abilityName}" is not available for ${speciesEntry.name} at level ${safeLevel}.`,



        hint: _formatSuggestionSentence(



          "Use one of this species' unlocked abilities instead: ",



          _suggestLegalAbilitiesForSpecies(speciesEntry, safeLevel, abilityName, 4),



          `${abilityName} is outside this species' unlocked ability slots at level ${safeLevel}. Use one of the species' listed legal abilities instead.`



        ),



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



    const edgeEntry = (characterData?.poke_edges_catalog || []).find(



      (entry) => _normalizeSearchText(entry.name) === _normalizeSearchText(edgeName)



    );



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



      const speciesCaps = new Set(_pokemonEffectiveCapabilityNames(speciesEntry, build).map((cap) => _normalizeSearchText(cap)));



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



  const minEvoLevel = _minEvolutionLevelForSpecies(speciesName);



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



      hint: `Either mark this Pokemon as caught in the wild, or switch to a lower-stage form until level ${minEvoLevel}. Current evolution profile: ${_activeEvolutionProfile()?.label || "Builder Default"}.`,



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



  const list = masterData?.pokemon?.species || [];



  const candidates = _speciesLookupCandidates(name);



  for (const candidate of candidates) {



    const candidateKeys = _speciesLookupComparableKeys(candidate);



    const match = list.find((entry) => {



      const entryName = String(entry?.name || entry?.species || "").trim();



      return _keysIntersect(_speciesLookupComparableKeys(entryName), candidateKeys) || _normalizeSearchText(entryName) === _normalizeSearchText(candidate);



    });



    if (match) return match;



  }



  const key = _normalizeSearchText(name);



  return list.find((entry) => _normalizeSearchText(entry.name) === key) || null;



}







function _normalizeSpeciesKey(name) {



  let text = String(name || "").trim().toLowerCase();



  if (!text) return "";



  text = text.replace("\u2640", "f").replace("\u2642", "m");



  text = text.replace("â™€", "f").replace("â™‚", "m");



  text = text.replace("(", " ").replace(")", " ");

  text = text.replace(/[.,:'’]/g, " ");



  text = text.replace("-", " ");



  text = text.replace(/\s+/g, " ").trim();



  return text;



}

function _speciesLookupComparableKeys(name) {



  const raw = _normalizeSpeciesKey(name);



  if (!raw) return [];



  const keys = [];



  const add = (value) => {



    const key = _normalizeSpeciesKey(value);



    if (key && !keys.includes(key)) keys.push(key);



  };



  add(raw);



  add(raw.replace(/\b(forme|form|mode)\b/g, " ").replace(/\s+/g, " ").trim());



  const stripped = raw.replace(/\b(forme|form|mode)\b/g, " ").replace(/\s+/g, " ").trim();



  add(stripped);



  const compact = (value) => _normalizeSpeciesKey(value).replace(/\s+/g, "");



  const compactRaw = compact(raw);



  if (compactRaw && !keys.includes(compactRaw)) keys.push(compactRaw);



  const compactStripped = compact(stripped);



  if (compactStripped && !keys.includes(compactStripped)) keys.push(compactStripped);



  return keys;



}



function _keysIntersect(left, right) {



  const leftSet = new Set(left || []);



  return (right || []).some((value) => leftSet.has(value));



}







function _speciesLookupCandidates(name) {



  const raw = _normalizeSpeciesKey(name);



  if (!raw) return [];



  const candidates = [];



  const add = (value) => {



    const key = _normalizeSpeciesKey(value);



    if (key && !candidates.includes(key)) candidates.push(key);



  };



  add(raw);



  const tokens = raw.split(" ").filter(Boolean);



  const regionalMap = { alolan: "alola", galarian: "galar", hisuian: "hisui", paldean: "paldea" };



  if (tokens.length > 1) {



    if (regionalMap[tokens[0]]) {



      add(`${tokens.slice(1).join(" ")} ${regionalMap[tokens[0]]}`);



      add(`${tokens.slice(1).join(" ")} ${tokens[0]}`);



      add(tokens.slice(1).join(" "));



    }



    if (regionalMap[tokens[tokens.length - 1]]) {



      add(`${tokens[0]} ${regionalMap[tokens[tokens.length - 1]]}`);



      add(tokens[0]);



    }



    const strippedTokens = tokens.filter((token) => !["form", "forme", "mode"].includes(token));



    if (strippedTokens.length !== tokens.length) {



      add(strippedTokens.join(" "));



      if (regionalMap[strippedTokens[0]]) {



        add(`${strippedTokens.slice(1).join(" ")} ${regionalMap[strippedTokens[0]]}`);



      }



    }



  }



  return candidates;



}



function trainerToPokemonLevel(trainerLevel) {



  const base = Number(trainerLevel || 1);



  const scaled = Math.round(base * 2);



  if (!Number.isFinite(scaled)) return 1;



  return Math.max(1, Math.min(100, scaled));



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



  add(raw.replace(/%/g, "").replace(/\b(forme|form|mode)\b/g, " ").replace(/\s+/g, " ").trim());



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



  if (base === "flabebe" || base === "flabébé") {



    add("flabebe");



    add("flabébé");



  }



  if (base === "stunfisk" && tokens.length > 1 && ["g", "galar", "galarian"].includes(tokens[1])) {



    add("stunfisk galar");



  }



  if (["pumpkaboo", "gourgeist"].includes(base) && tokens.length > 1) {



    const sizeAlias = { a: "average", av: "average", sm: "small", la: "large", su: "super" };



    const size = sizeAlias[tokens[1]] || tokens[1];



    add(`${base} ${size}`);



  }



  if (["giratina", "dialga", "palkia"].includes(base) && tokens.length > 1) {



    const formAlias = { a: "altered", altered: "altered", o: "origin", origin: "origin" };



    const form = formAlias[tokens[1]] || tokens[1];



    add(`${base} ${form}`);



  }



  if (["landorus", "thundurus", "tornadus", "enamorus"].includes(base) && tokens.length > 1) {



    const formAlias = { i: "incarnate", incarnate: "incarnate", t: "therian", therian: "therian" };



    const form = formAlias[tokens[1]] || tokens[1];



    add(`${base} ${form}`);



  }



  if (base === "meloetta" && tokens.length > 1) {



    const formAlias = { a: "aria", aria: "aria", p: "pirouette", pirouette: "pirouette", s: "step", step: "step" };



    const form = formAlias[tokens[1]] || tokens[1];



    add(`meloetta ${form}`);



  }



  if (base === "kyurem" && tokens.length > 1) {



    const formAlias = {



      r: "reshiram",



      reshiram: "reshiram",



      white: "reshiram",



      z: "zekrom",



      zekrom: "zekrom",



      black: "zekrom",



    };



    const form = formAlias[tokens[1]] || tokens[1];



    add(`kyurem ${form}`);



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



  add(rawNoPercent.replace(/\b(forme|form|mode)\b/g, " ").replace(/\s+/g, " ").trim());



  let rawTokens = rawNoPercent.split(" ").map((token) => token.replace(/[^a-z0-9]+/g, ""));



  rawTokens = rawTokens.filter(Boolean);



  const regionalMap = { alolan: "alola", galarian: "galar", hisuian: "hisui", paldean: "paldea" };



  if (rawTokens.length && regionalMap[rawTokens[0]] && rawTokens.length > 1) {



    add(`${rawTokens[1]} ${regionalMap[rawTokens[0]]}`);



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



  const expanded = rawTokens.map((token) => regionalMap[token] || shortMap[token] || token);



  add(expanded.join(" "));



  if (expanded.length && ["alola", "galar", "hisui", "paldea"].includes(expanded[0]) && expanded.length > 1) {



    add(`${expanded[1]} ${expanded[0]}`);



    add(expanded[1]);



  }



  if (expanded.length > 2) add(`${expanded[0]} ${expanded.slice(1).join("")}`);



  if (expanded.length && expanded[0] === "mega" && expanded.length > 1) {



    add(expanded[1]);



    if (expanded.length > 2) add(`${expanded[1]} ${expanded[2]}`);



  }



  const head = expanded[0] || "";



  const tail = expanded.length > 1 ? expanded.slice(1) : [];



  if (head.startsWith("flab")) add("flabebe");



  if (head === "flabebe") add("flab\u00e9b\u00e9");



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




    if (tail.some((token) => ["a", "altered"].includes(token))) add(`${head} altered forme`);



    if (tail.some((token) => ["o", "origin"].includes(token))) {



      add(`${head} origin`);



      add(`${head} origin forme`);



    }



  }



  if (["landorus", "thundurus", "tornadus", "enamorus"].includes(head)) {



    add(head);



    if (tail.some((token) => ["i", "incarnate"].includes(token))) add(`${head} incarnate forme`);



    if (tail.some((token) => ["t", "therian"].includes(token))) add(`${head} therian forme`);



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



    if (tail.some((token) => ["r", "reshiram", "white"].includes(token))) {



      add("kyurem white");



      add("kyurem reshiram");



      add("kyurem reshiram fusion form");



    }



    if (tail.some((token) => ["z", "zekrom", "black"].includes(token))) {



      add("kyurem black");



      add("kyurem zekrom");



      add("kyurem zekrom fusion form");



    }



  }



  if (head === "meloetta") {



    add("meloetta");



    if (tail.some((token) => ["a", "aria"].includes(token))) {



      add("meloetta aria");



      add("meloetta aria form");



    }



    if (tail.some((token) => ["p", "pirouette", "s", "step"].includes(token))) {



      add("meloetta pirouette");



      add("meloetta step");



      add("meloetta step form");



    }



  }



  if (head === "nidoran") {



    if (tail.some((token) => ["f", "female"].includes(token))) add("nidoran f");



    if (tail.some((token) => ["m", "male"].includes(token))) add("nidoran m");



  }



  if (["pumpkaboo", "gourgeist"].includes(head)) add(head);



  return candidates;



}







function _getLearnsetForSpecies(name) {



  if (!learnsetData) return [];



  const candidates = _learnsetKeyCandidates(name);



  for (const key of candidates) {



    const list = learnsetData[key];



    if (list && list.length) return _filterPokemonLearnset(name, list);



  }


  const candidateKeys = candidates.flatMap((key) => _speciesLookupComparableKeys(key));



  for (const [key, list] of Object.entries(learnsetData)) {



    if (!list || !list.length) continue;



    if (_keysIntersect(_speciesLookupComparableKeys(key), candidateKeys)) return _filterPokemonLearnset(name, list);



  }



  return [];



}

function _filterPokemonLearnset(name, list) {

  const blacklist = POKEMON_LEARNSET_BLACKLIST[_normalizeSearchText(name || "")];

  if (!Array.isArray(list) || !list.length) return list;

  const denied = new Set(Array.isArray(blacklist) ? blacklist.map((moveName) => _normalizeMoveKey(moveName)) : []);
  const feintLevels = new Set();
  list.forEach((entry) => {
    const moveKey = _normalizeMoveKey(entry?.move || entry?.name || "");
    const level = Number(entry?.level || 0);
    if (moveKey === "feint") feintLevels.add(level);
  });

  return list.filter((entry) => {
    const moveKey = _normalizeMoveKey(entry?.move || entry?.name || "");
    const level = Number(entry?.level || 0);
    if (denied.has(moveKey)) return false;
    if (moveKey === "feintattack" && feintLevels.has(level)) return false;
    return true;
  });

}




function _getAbilityPoolsForSpecies(name) {



  const pools = masterData?.pokemon?.pokedex_abilities || {};



  const candidates = _abilityKeyCandidates(name);



  for (const key of candidates) {



    if (pools[key]) return pools[key];



  }



  const candidateKeys = candidates.flatMap((key) => _speciesLookupComparableKeys(key));



  for (const [key, value] of Object.entries(pools)) {



    if (_keysIntersect(_speciesLookupComparableKeys(key), candidateKeys)) return value;



  }



  return null;



}







function _pickAbilitiesForLevel(pools, level, build = null) {



  if (!pools) return [];



  const starting = Array.from(new Set(pools.starting || []));



  const basic = Array.from(new Set(pools.basic || []));



  const advanced = Array.from(new Set(pools.advanced || []));



  const high = Array.from(new Set(pools.high || []));



  const basePool = starting.length ? starting : basic;



  const basicPool = Array.from(new Set([...starting, ...basic]));



  const advancedPool = Array.from(new Set([...advanced]));



  const highPool = Array.from(new Set([...high]));



  const desired = _abilitySlotCountForBuild(level, build);


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







function _eligibleAutoFillLearnsetEntries(speciesEntry, level) {

  if (!speciesEntry || !learnsetData) return [];

  const safeLevel = Math.max(1, Math.min(100, Number(level || 1)));

  const learnset = _getLearnsetForSpecies(speciesEntry.name);

  if (!learnset.length) return [];

  const latestByMove = new Map();

  learnset.forEach((entry) => {

    const moveName = String(entry?.move || entry?.name || "").trim();

    const moveLevel = Number(entry?.level || 0);

    if (!moveName || !Number.isFinite(moveLevel) || moveLevel > safeLevel) return;

    const key = _normalizeMoveKey(moveName);

    const existing = latestByMove.get(key);

    if (!existing || moveLevel > Number(existing.level || 0)) {

      latestByMove.set(key, entry);

    }

  });

  const allEligible = Array.from(latestByMove.values());

  const naturalEligible = allEligible.filter((entry) => Number(entry?.level || 0) > 0);

  return naturalEligible;

}



function _suggestLegalMovesForSpecies(speciesEntry, level, excludeName = "", limit = 4) {



  if (!speciesEntry || !moveRecordMap || !learnsetData) return [];



  const excludeKey = _normalizeMoveKey(excludeName);



  const suggestions = [];



  const push = (moveName) => {



    const trimmed = String(moveName || "").trim();



    const key = _normalizeMoveKey(trimmed);



    if (!trimmed || key === excludeKey) return;



    if (!suggestions.some((entry) => _normalizeMoveKey(entry) === key)) suggestions.push(trimmed);



  };



  _selectMovesForSpecies(speciesEntry, level).forEach(push);



  _recordsFromLearnset(_eligibleAutoFillLearnsetEntries(speciesEntry, level))



    .map((record) => record?.name)



    .forEach(push);



  _eligibleAutoFillLearnsetEntries(speciesEntry, level)



    .sort((a, b) => Number(b?.level || 0) - Number(a?.level || 0))



    .map((entry) => entry?.move || entry?.name)



    .forEach(push);



  return suggestions.slice(0, Math.max(1, Number(limit || 4)));



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



  const typed = (masterData?.pokemon?.moves || []).filter(



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



    const record = moveRecordMap?.get(_normalizeMoveKey(entry.move));


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



  const allMoves = masterData?.pokemon?.moves || [];



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
  const autoFillCandidates = _recordsFromLearnset(_eligibleAutoFillLearnsetEntries(speciesEntry, level));
  if (!autoFillCandidates.length) return [];
  return _buildMinMaxMoveset(speciesEntry, autoFillCandidates).slice(0, 4).map((record) => record.name);


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



    const damagingPool = (masterData?.pokemon?.moves || [])



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



  if (!moves.length && masterData?.pokemon?.moves?.length) {



    const fallback =



      masterData.pokemon.moves.find((record) => _isDamagingMove(record)) || masterData.pokemon.moves[0];



    if (fallback) moves.push(fallback);



  }



  return moves.slice(0, 4).map((record) => record.name);



}







async function _applyPokemonDefaults(build, speciesEntry, overwrite = false) {


  const speciesName = String(build?.species || build?.name || speciesEntry?.name || "").trim();



  const level = Number(build?.level || characterState?.profile?.level || 1);



  if (!speciesName) {


    return _autoFillPokemonBuild(build, speciesEntry, overwrite);


  }

  return _autoFillPokemonBuild(build, speciesEntry, overwrite);

  try {


    const params = new URLSearchParams({



      species: speciesName,



      level: String(Math.max(1, Math.min(100, Number.isFinite(level) ? level : 1))),



    });



    const response = await fetch(`/api/pokemon_defaults?${params.toString()}`, { cache: "no-store" });



    if (!response.ok) return _autoFillPokemonBuild(build, speciesEntry, overwrite);



    const payload = await response.json();



    if (!payload || payload.ok === false) return _autoFillPokemonBuild(build, speciesEntry, overwrite);



    let filled = false;



    const messageParts = [];



    const abilities = Array.isArray(payload.abilities) ? payload.abilities.filter(Boolean) : [];



    const moves = Array.isArray(payload.moves) ? payload.moves.filter(Boolean) : [];



    if (abilities.length) {



      if (overwrite || !Array.isArray(build.abilities) || build.abilities.length === 0) {



        build.abilities = abilities.slice(0, 3);



        filled = true;



      }



    } else {



      messageParts.push("No default abilities for this species.");



    }



    if (moves.length) {



      if (overwrite || !Array.isArray(build.moves) || build.moves.length === 0) {



        build.moves = moves.slice(0, 4);



        build.move_sources = {};



        filled = true;



      }



    } else {



      messageParts.push("No default moves for this species.");



    }



    return { filled, message: messageParts.join(" ") };



  } catch (_error) {



    return _autoFillPokemonBuild(build, speciesEntry, overwrite);



  }



}







function _autoFillPokemonBuild(build, speciesEntry, overwrite = false) {



  if (!build || !speciesEntry) return { filled: false, message: "" };



  let filled = false;



  const messageParts = [];



  const level = Number(build.level || characterState.profile.level || 1);



  const pools = _getAbilityPoolsForSpecies(build.species || build.name || speciesEntry.name);



  const abilityList = pools ? _pickAbilitiesForLevel(pools, level, build) : [];



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



      build.move_sources = {};



      filled = true;



    }



  } else {



    messageParts.push("No default moves for this species.");



  }



  return { filled, message: messageParts.join(" ") };



}







function _movePickerItemsForBuild(build, speciesEntry) {



  const buildLevel = Number(build?.level || 1);



  const availability = _pokemonMoveSourceAvailability(speciesEntry, buildLevel, build);



  const moveSources = _effectivePokemonMoveSourceMap(build, speciesEntry);



  return (masterData?.pokemon?.moves || [])



    .slice()



    .map((entry) => {



      const moveKey = _normalizeMoveKey(entry.name);



      const learnableNow = speciesEntry ? availability.natural.has(moveKey) : null;
      const sketchNow = speciesEntry ? availability.sketch?.has(moveKey) === true : null;



      const tmNow = speciesEntry ? availability.tm.has(moveKey) : null;



      const tutorNow = speciesEntry ? availability.tutor.has(moveKey) : null;



      const eggNow = speciesEntry ? availability.egg.has(moveKey) : null;



      const fallbackTutorNow = speciesEntry ? availability.tutorFallback?.has(moveKey) === true : null;



      const assignedSource = moveSources[moveKey] || "";


      return {



        name: entry.name,



        meta: [



          _moveDatasetSourceNote(entry),

          entry.type || "",



          entry.category || "",



          entry.damage_base ? `DB ${entry.damage_base}` : "Status",



          entry.range ? `Range ${entry.range}` : "",



          learnableNow === true
            ? "Learnable now"
            : sketchNow === true
              ? "Sketch"
            : eggNow === true
              ? "Egg Move"
              : tmNow === true
                ? "TM"
              : tutorNow === true
                ? fallbackTutorNow === true
                  ? "Tutor (Legacy fallback)"
                  : "Tutor"
                : speciesEntry
                  ? `Not learnable at Lv ${buildLevel}`
                  : "",



          assignedSource === "tm"
            ? "Using TM source"
            : assignedSource === "tutor"
            ? fallbackTutorNow === true
              ? "Using Tutor source via Legacy Level-0 Fallback"
              : "Using Tutor source"
            : assignedSource === "sketch"
              ? "Using Sketch source"
            : assignedSource === "egg"
              ? "Using Egg source"
              : "",



          _pokemonMoveSourceOriginNote(availability, moveKey, assignedSource),



        ]



          .filter(Boolean)



          .join(" | "),



        hint: _movePreviewText(entry),

        layout: "move",



        sortWeight: learnableNow === true ? 0 : sketchNow === true ? 1 : eggNow === true ? 2 : tmNow === true ? 3 : tutorNow === true ? 4 : speciesEntry ? 5 : 1,



      };



    })



    .sort((a, b) => a.sortWeight - b.sortWeight || a.name.localeCompare(b.name));



}







function _abilityPickerItemsForBuild(build, speciesEntry) {



  const buildLevel = Number(build?.level || 1);



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



  return (masterData?.pokemon?.abilities || [])



    .slice()



    .map((entry) => {



      const key = _normalizeSearchText(entry.name);



      const pool = poolMap.get(key) || "";



      const usableNow = pool ? allowedAbilities.has(key) : null;



      return {



        name: entry.name,



        meta: [



          pool ? `Pool: ${pool}` : "Not listed for this species",



          usableNow === true ? "Available now" : usableNow === false ? `Locked at Lv ${buildLevel}` : "",



          entry.frequency ? `Freq: ${entry.frequency}` : "",



        ]



          .filter(Boolean)



          .join(" | "),



        hint: _abilityPreviewText(entry),



        sortWeight: usableNow === true ? 0 : pool ? 1 : 2,



      };



    })



    .sort((a, b) => a.sortWeight - b.sortWeight || a.name.localeCompare(b.name));



}







function _itemPickerItems() {



  return _allItemCatalogEntries()



    .filter(



      (entry) =>



        String(entry.category || "").trim().length > 0 ||



        _hasDisplayValue(entry.slot) ||



        _hasDisplayValue(entry.cost)



    )



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



  return (characterData?.poke_edges_catalog || [])



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







function ensureSpeciesDatalist() {



  if (document.getElementById("pokemon-species-list")) return;



  const list = document.createElement("datalist");



  list.id = "pokemon-species-list";



  const speciesList = (masterData?.pokemon?.species || []).slice();



  speciesList.sort((a, b) => String(a.name).localeCompare(String(b.name)));



  speciesList.forEach((entry) => {



    const option = document.createElement("option");



    option.value = entry.name;



    list.appendChild(option);



  });



  document.body.appendChild(list);



}



function ensureNatureDatalist() {

  if (document.getElementById("pokemon-nature-list")) return;

  const list = document.createElement("datalist");

  list.id = "pokemon-nature-list";

  POKEMON_NATURES.slice()
    .sort((a, b) => String(a[0]).localeCompare(String(b[0])))
    .forEach((entry) => {
      const option = document.createElement("option");
      option.value = entry[0];
      list.appendChild(option);
    });

  document.body.appendChild(list);

}







function _ensurePokemonBuilds() {



  if (!Array.isArray(characterState.pokemon_builds)) characterState.pokemon_builds = [];



  return characterState.pokemon_builds;



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



  list.className = "char-entry-list char-picker-entry-list";



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

      layout: String(entry?.layout || "").trim(),



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



          return a.sortWeight - b.sortWeight || b.score - a.score || a.label.localeCompare(b.label);



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
      if (entry.layout) row.classList.add(`char-picker-row-${entry.layout}`);



      const label = document.createElement("div");



      label.className = "char-row-title";



      label.textContent = entry.label;



      row.appendChild(label);



      if (entry.hint) {

        const hint = document.createElement("div");

        hint.className = "char-feature-meta";

        hint.textContent = entry.hint;

        row.appendChild(hint);

      }

      if (entry.meta) {



        const meta = document.createElement("div");



        meta.className = "char-row-meta";



        meta.textContent = entry.meta;



        row.appendChild(meta);



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



  const level = Number(prompt("Pokemon level:", String(characterState.profile.level || 1)) || characterState.profile.level || 1);



  const build = {



    name: rawName,



    species: rawName,



    level: Number.isFinite(level) ? level : Number(characterState.profile.level || 1),



    battle_side: "",



    caught: false,



    moves: [],



    move_sources: {},



    abilities: [],



    items: [],



    poke_edges: [],



    tutor_points: 0,
    tutor_points_mode: "adjustment",



  };



  _ensurePokemonBuilds().push(build);



  saveCharacterToStorage();



  return build;



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



    "Paste roster CSV with headers like side,slot,species,level,nickname,ability,item,move1..move8,move_source1..move_source8,tutor_points. CSV tutor_points is treated as the current total remaining; the builder converts that into a level-based adjustment internally.";



  box.appendChild(note);



  const textarea = document.createElement("textarea");



  textarea.className = "char-search";



  textarea.style.minHeight = "260px";



  textarea.placeholder =



    "side,slot,species,level,nickname,ability,item,move1,move2,move3,move4,move5,move6,move7,move8,move_source1,move_source2,move_source3,move_source4,move_source5,move_source6,move_source7,move_source8,tutor_points\nplayer,1,Pikachu,50,Sparky,Static,Light Ball,Thunderbolt,Volt Tackle,Fake Out,Protect,Quick Attack,Iron Tail,,,level_up,tutor,level_up,level_up,level_up,tutor,,,5\nfoe,1,Garchomp,50,,Rough Skin,Yache Berry,Earthquake,Dragon Claw,Rock Slide,Protect,Swords Dance,Crunch,,,level_up,level_up,level_up,level_up,level_up,level_up,,,2";



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



      if (_looksLikeTrainerCsv(textarea.value)) {
        throw new Error("This is a trainer CSV, not a team roster CSV. Use the trainer import button instead.");
      }



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



      if (_looksLikeTrainerCsv(textarea.value)) {
        throw new Error("This is a trainer CSV, not a team roster CSV. Use the trainer import button instead.");
      }



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

  const skillBasics = _builderBasicsLines("skill", desc);

  if (skillBasics.length) _appendDetailBlock(box, "Basics", skillBasics.join("\n"));

  _appendGlossaryBlock(box, desc, "Glossary");



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



  const capabilityBasics = _builderBasicsLines("capability", desc);



  if (capabilityBasics.length) _appendDetailBlock(box, "Basics", capabilityBasics.join("\n"));

  _appendGlossaryBlock(box, desc, "Glossary");



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



    _appendDetailBlock(box, "Rules Text", _moveRulesText(entry));

    _appendDetailBlock(box, "Simple Guide", _eli5MoveSummary(entry), { muted: true });

    const moveBasics = _builderBasicsLines("move", _moveRulesText(entry), entry);

    if (moveBasics.length) _appendDetailBlock(box, "Basics", moveBasics.join("\n"), { muted: true });

    _appendGlossaryBlock(

      box,

      [_moveRulesText(entry), entry.frequency || "", entry.range || "", entry.category || ""].join("\n"),

      "Glossary"

    );

    const moveExample = _builderExampleText("move", entry);

    if (moveExample) _appendDetailBlock(box, "Example", moveExample, { muted: true });

    _appendDetailNote(box, "move", entry);



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

    _appendDetailBlock(box, "Simple Guide", _eli5AbilitySummary(entry), { muted: true });

    const abilityBasics = _builderBasicsLines("ability", `${entry.effect || entry.effect_2 || ""}\n${entry.trigger || ""}\n${entry.keywords || ""}`, entry);

    if (abilityBasics.length) _appendDetailBlock(box, "Basics", abilityBasics.join("\n"), { muted: true });

    _appendGlossaryBlock(box, `${entry.effect || entry.effect_2 || ""}\n${entry.trigger || ""}\n${entry.keywords || ""}\n${entry.frequency || ""}`, "Glossary");

    const abilityExample = _builderExampleText("ability", entry);

    if (abilityExample) _appendDetailBlock(box, "Example", abilityExample, { muted: true });

    _appendDetailNote(box, "ability", entry);



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

  const itemBasics = _builderBasicsLines("item", entry.description || entry.buff || entry.desc || "", entry);

  if (itemBasics.length) _appendDetailBlock(box, "Basics", itemBasics.join("\n"));

  _appendGlossaryBlock(box, `${entry.description || entry.buff || entry.desc || ""}\n${entry.category || ""}\n${entry.type || ""}`, "Glossary");

  const itemExample = _builderExampleText("item", entry);

  if (itemExample) _appendDetailBlock(box, "Example", itemExample);

  _appendDetailNote(box, "item", entry);



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
  _renderRulebookGlossaryPanel(box);
  _renderUsefulChartsPanel(box);







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



      _setTooltipAttrs(row, entry.name, descParts.join("\n"), _builderSourceNote(entry.kind === "feature" ? "feature" : "edge", entry));



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



  _ensureCharacterPokeEdgesState();



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



        <button type="button" class="mini-link" data-mini-action="poke-edges">Poke Edges: ${characterState.poke_edges.size}</button>



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



      } else if (action === "poke-edges") {



        goToCharacterStep("poke-edges");



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

  _applyNormalizedCharacterPayload(_snapshotCharacterState());

  const payload = {
    ..._normalizeCharacterPayload(_snapshotCharacterState()),

    class_name: (characterData.classes || []).find((cls) => cls.id === characterState.class_id)?.name || "",

    signed_by: EXPORT_SIGNATURE,

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



  const pokeEdgeList = Array.from(characterState.poke_edges).sort();



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



  const pokeEdgePills = pokeEdgeList.length



    ? pokeEdgeList



        .map(



          (name) =>



            `<button type="button" class="char-pill char-pill-link" data-sheet-action="poke-edge" data-name="${escapeAttr(



              name



            )}">${escapeHtml(name)}</button>`



        )



        .join("")



    : "<button type=\"button\" class=\"char-pill char-pill-link\" data-sheet-action=\"open-step\" data-step=\"poke-edges\">Open Pok\u00e9 Edges</button>";



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



          return `



            <div class="char-sheet-section">



              <div class="char-sheet-title">${escapeHtml(build.name || build.species || "Pokemon")} (Lv ${escapeHtml(



            build.level || 1



          )})</div>



              <div class="char-sheet-row">${escapeHtml(build.species || build.name || "-")}</div>



              <div class="char-pill-list">${movePills || "<span class=\"char-feature-meta\">No moves</span>"}</div>



              <div class="char-pill-list">${abilityPills || "<span class=\"char-feature-meta\">No abilities</span>"}</div>



              <div class="char-pill-list">${itemPills || "<span class=\"char-feature-meta\">No items</span>"}</div>



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



      <div class="char-sheet-title">Poke Edges (${pokeEdgeList.length})</div>



      <div class="char-pill-list">${pokeEdgePills}</div>



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



      } else if (action === "poke-edge") {



        characterState.poke_edge_search = btn.getAttribute("data-name") || "";



        goToCharacterStep("poke-edges");



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



  download.textContent = "Advanced: Builder JSON";



  download.addEventListener("click", () => {

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });

    _downloadBlobFile("trainer_character.json", blob);

  });


  actions.appendChild(download);

  const exportTeamCsv = document.createElement("button");
  exportTeamCsv.textContent = "Export Team CSV";
  exportTeamCsv.addEventListener("click", () => {
    const roster = _buildRosterCsvFromTrainerPayload(payload, false, false);
    if (!roster?.csvText) throw new Error("No Pokemon builds found to export.");
    _downloadCsvFile("autoptu_team.csv", roster.csvText);
  });
  actions.appendChild(exportTeamCsv);

  const exportTrainerCsv = document.createElement("button");
  exportTrainerCsv.textContent = "Export Trainer CSV";
  exportTrainerCsv.addEventListener("click", () => {
    _downloadCsvFile("autoptu_trainer.csv", _buildTrainerCsvFromTrainerPayload(payload));
  });
  actions.appendChild(exportTrainerCsv);

  const saveProject = document.createElement("button");
  saveProject.textContent = "Save Project ZIP";
  saveProject.addEventListener("click", () => {
    _downloadTournamentSubmissionPack();
  });
  actions.appendChild(saveProject);



  const fancyExport = document.createElement("button");



  fancyExport.textContent = "Export Fancy PTU CSVs";



  fancyExport.addEventListener("click", () => {



    exportFancyPtuSheet().catch(alertError);



  });



  actions.appendChild(fancyExport);



  const exportHint = document.createElement("div");



  exportHint.className = "char-feature-meta";



  exportHint.textContent = "Save Project ZIP is the easiest handoff. Team CSV is for battles, Trainer CSV is for trainer-only data, and Builder JSON is the full advanced save.";



  actions.appendChild(exportHint);



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

      _applyNormalizedCharacterPayload(parsed);

      saveCharacterToStorage();

      renderCharacterStep();

      return;

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



      if (Array.isArray(parsed.pokemon_builds)) characterState.pokemon_builds = parsed.pokemon_builds;



      if (parsed.inventory && typeof parsed.inventory === "object") characterState.inventory = parsed.inventory;



      if (parsed.extras_search !== undefined) characterState.extras_search = parsed.extras_search;



      if (parsed.inventory_search !== undefined) characterState.inventory_search = parsed.inventory_search;



      if (parsed.extras_catalog_search !== undefined) characterState.extras_catalog_search = parsed.extras_catalog_search;



      if (parsed.extras_catalog_scope !== undefined) characterState.extras_catalog_scope = parsed.extras_catalog_scope;



      if (parsed.inventory_catalog_search !== undefined) characterState.inventory_catalog_search = parsed.inventory_catalog_search;



      if (parsed.inventory_catalog_category !== undefined) characterState.inventory_catalog_category = parsed.inventory_catalog_category;



      if (parsed.inventory_catalog_type !== undefined) characterState.inventory_catalog_type = parsed.inventory_catalog_type;



      if (parsed.inventory_catalog_kind !== undefined) characterState.inventory_catalog_kind = parsed.inventory_catalog_kind;



      if (parsed.glossary_query !== undefined) characterState.glossary_query = parsed.glossary_query;



      if (parsed.glossary_category !== undefined) characterState.glossary_category = parsed.glossary_category;



      if (parsed.glossary_open !== undefined) characterState.glossary_open = !!parsed.glossary_open;



      if (parsed.pokemon_team_search !== undefined) characterState.pokemon_team_search = parsed.pokemon_team_search;



      if (parsed.pokemon_team_limit !== undefined) characterState.pokemon_team_limit = parsed.pokemon_team_limit;



      if (parsed.pokemon_team_auto_level !== undefined) characterState.pokemon_team_auto_level = parsed.pokemon_team_auto_level;



      if (parsed.pokemon_team_autofill !== undefined) characterState.pokemon_team_autofill = parsed.pokemon_team_autofill;
      if (parsed.data_policy !== undefined) characterState.data_policy = _normalizeDataPolicy(parsed.data_policy);



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



      poke_edges: Array.from(characterState.poke_edges),



      poke_edge_order: Array.isArray(characterState.poke_edge_order) ? characterState.poke_edge_order.slice() : [],



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



      glossary_query: characterState.glossary_query,



      glossary_category: characterState.glossary_category,



      glossary_open: !!characterState.glossary_open,



      pokemon_team_search: characterState.pokemon_team_search,



      pokemon_team_limit: characterState.pokemon_team_limit,



      pokemon_team_auto_level: characterState.pokemon_team_auto_level,



      pokemon_team_autofill: characterState.pokemon_team_autofill,



      data_policy: _normalizeDataPolicy(characterState.data_policy),



    };



    const serialized = JSON.stringify(_normalizeCharacterPayload(payload));


    localStorage.setItem("autoptu_character", serialized);



    _pushCharacterHistory(serialized);



  } catch {



    // ignore



  }



}







function setCharacterFromPayload(parsed) {

  if (!parsed || typeof parsed !== "object") return;

  _applyNormalizedCharacterPayload(parsed);

  return;

  if (parsed.profile) characterState.profile = { ...characterState.profile, ...parsed.profile };


  if (Array.isArray(parsed.class_ids)) characterState.class_ids = parsed.class_ids.slice();



  if (parsed.class_id) characterState.class_id = parsed.class_id;



  if ((!characterState.class_ids || !characterState.class_ids.length) && characterState.class_id) {



    characterState.class_ids = [characterState.class_id];



  }



  if (Array.isArray(parsed.features)) characterState.features = new Set(parsed.features);



  if (Array.isArray(parsed.edges)) characterState.edges = new Set(parsed.edges);



  if (Array.isArray(parsed.poke_edges)) characterState.poke_edges = new Set(parsed.poke_edges);



  if (Array.isArray(parsed.poke_edge_order)) characterState.poke_edge_order = parsed.poke_edge_order.slice();



  if (Array.isArray(parsed.feature_order)) characterState.feature_order = parsed.feature_order.slice();



  if (Array.isArray(parsed.edge_order)) characterState.edge_order = parsed.edge_order.slice();



  if (window.PTUCharacterState?.ensureOrderedSet) {



    window.PTUCharacterState.ensureOrderedSet(characterState, "poke_edges", "poke_edge_order");



  }



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



  if (Array.isArray(parsed.pokemon_builds)) characterState.pokemon_builds = parsed.pokemon_builds;



  if (parsed.inventory && typeof parsed.inventory === "object") characterState.inventory = parsed.inventory;



  if (parsed.extras_search !== undefined) characterState.extras_search = parsed.extras_search;



  if (parsed.inventory_search !== undefined) characterState.inventory_search = parsed.inventory_search;



  if (parsed.extras_catalog_search !== undefined) characterState.extras_catalog_search = parsed.extras_catalog_search;



  if (parsed.extras_catalog_scope !== undefined) characterState.extras_catalog_scope = parsed.extras_catalog_scope;



  if (parsed.inventory_catalog_search !== undefined) characterState.inventory_catalog_search = parsed.inventory_catalog_search;



  if (parsed.inventory_catalog_category !== undefined) characterState.inventory_catalog_category = parsed.inventory_catalog_category;



  if (parsed.inventory_catalog_type !== undefined) characterState.inventory_catalog_type = parsed.inventory_catalog_type;



  if (parsed.inventory_catalog_kind !== undefined) characterState.inventory_catalog_kind = parsed.inventory_catalog_kind;



  if (parsed.glossary_query !== undefined) characterState.glossary_query = parsed.glossary_query;



  if (parsed.glossary_category !== undefined) characterState.glossary_category = parsed.glossary_category;



  if (parsed.glossary_open !== undefined) characterState.glossary_open = !!parsed.glossary_open;



  if (parsed.pokemon_team_search !== undefined) characterState.pokemon_team_search = parsed.pokemon_team_search;



  if (parsed.pokemon_team_limit !== undefined) characterState.pokemon_team_limit = parsed.pokemon_team_limit;



  if (parsed.pokemon_team_auto_level !== undefined) characterState.pokemon_team_auto_level = parsed.pokemon_team_auto_level;



  if (parsed.pokemon_team_autofill !== undefined) characterState.pokemon_team_autofill = parsed.pokemon_team_autofill;
  if (parsed.data_policy !== undefined) characterState.data_policy = _normalizeDataPolicy(parsed.data_policy);



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







function _ensureCharacterPokeEdgesState() {



  if (!(characterState.poke_edges instanceof Set)) {



    if (Array.isArray(characterState.poke_edges)) {



      characterState.poke_edges = new Set(characterState.poke_edges);



    } else {



      characterState.poke_edges = new Set();



    }



  }



  if (!Array.isArray(characterState.poke_edge_order)) {



    characterState.poke_edge_order = Array.from(characterState.poke_edges);



  }



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

    _applyNormalizedCharacterPayload(parsed);

    _pushCharacterHistory(JSON.stringify(_normalizeCharacterPayload(parsed)));

    return;

    if (parsed.profile) characterState.profile = { ...characterState.profile, ...parsed.profile };


    if (Array.isArray(parsed.class_ids)) characterState.class_ids = parsed.class_ids.slice();



    if (parsed.class_id) characterState.class_id = parsed.class_id;



    if ((!characterState.class_ids || !characterState.class_ids.length) && characterState.class_id) {



      characterState.class_ids = [characterState.class_id];



    }



    if (Array.isArray(parsed.features)) characterState.features = new Set(parsed.features);



    if (Array.isArray(parsed.edges)) characterState.edges = new Set(parsed.edges);



    if (Array.isArray(parsed.poke_edges)) characterState.poke_edges = new Set(parsed.poke_edges);



    if (Array.isArray(parsed.poke_edge_order)) characterState.poke_edge_order = parsed.poke_edge_order.slice();



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



    if (Array.isArray(parsed.pokemon_builds)) characterState.pokemon_builds = parsed.pokemon_builds;



    if (parsed.inventory && typeof parsed.inventory === "object") characterState.inventory = parsed.inventory;



    if (parsed.extras_search !== undefined) characterState.extras_search = parsed.extras_search;



    if (parsed.inventory_search !== undefined) characterState.inventory_search = parsed.inventory_search;



    if (parsed.extras_catalog_search !== undefined) characterState.extras_catalog_search = parsed.extras_catalog_search;



    if (parsed.extras_catalog_scope !== undefined) characterState.extras_catalog_scope = parsed.extras_catalog_scope;



    if (parsed.inventory_catalog_search !== undefined) characterState.inventory_catalog_search = parsed.inventory_catalog_search;



    if (parsed.inventory_catalog_category !== undefined) characterState.inventory_catalog_category = parsed.inventory_catalog_category;



    if (parsed.inventory_catalog_type !== undefined) characterState.inventory_catalog_type = parsed.inventory_catalog_type;



    if (parsed.inventory_catalog_kind !== undefined) characterState.inventory_catalog_kind = parsed.inventory_catalog_kind;



    if (parsed.glossary_query !== undefined) characterState.glossary_query = parsed.glossary_query;



    if (parsed.glossary_category !== undefined) characterState.glossary_category = parsed.glossary_category;



    if (parsed.glossary_open !== undefined) characterState.glossary_open = !!parsed.glossary_open;



    if (parsed.pokemon_team_search !== undefined) characterState.pokemon_team_search = parsed.pokemon_team_search;



    if (parsed.pokemon_team_limit !== undefined) characterState.pokemon_team_limit = parsed.pokemon_team_limit;



    if (parsed.pokemon_team_auto_level !== undefined) characterState.pokemon_team_auto_level = parsed.pokemon_team_auto_level;



    if (parsed.pokemon_team_autofill !== undefined) characterState.pokemon_team_autofill = parsed.pokemon_team_autofill;
    if (parsed.data_policy !== undefined) characterState.data_policy = _normalizeDataPolicy(parsed.data_policy);



    if (parsed.override_prereqs !== undefined) characterState.override_prereqs = parsed.override_prereqs;



    if (parsed.feature_slots_override) {



      characterState.feature_slots_override = { ...parsed.feature_slots_override };



    }



    if (window.PTUCharacterState?.ensureOrderedSet) {



      window.PTUCharacterState.ensureOrderedSet(characterState, "poke_edges", "poke_edge_order");



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



  return state?.combatants?.find((combatant) => combatant.id === value) || null;



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



    case "item":



      category = "item";



      if (event.description) {



        const hpText = hpSuffix(event, event.target ?? event.target_id ?? event.defender ?? event.actor ?? event.actor_id);



        return { text: `${event.description}${hpText ? ` (${hpText})` : ""}`, category, prefix };



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



  const match = state?.combatants?.find((c) => c.id === value);



  if (match) return match.name;



  if (typeof value === "string") return value;



  return String(value);



}







function cleanLogLine(line, previous) {



  if (!line) return null;



  const trimmed = String(line).trim();



  if (!trimmed) return null;



  const lower = trimmed.toLowerCase();



  if (lower === "player.") return null;



  if (lower === "foe.") return null;



  if (lower === "player is up.") return "Player team is up.";



  if (lower === "foe is up.") return "Foe team is up.";



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







function onGridClick(x, y, occupantId) {



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







startButton?.addEventListener("click", () => startBattle().catch(alertError));



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



async function _importBuilderProjectZip(file) {
  const entries = _readZipEntries(await file.arrayBuffer());
  const builderJsonName = Object.keys(entries).find((name) => /team_builder\.json$/i.test(name) || /builder\.json$/i.test(name));
  const trainerCsvName = Object.keys(entries).find((name) => /trainer\.csv$/i.test(name));
  const teamCsvName = Object.keys(entries).find((name) => /team_roster\.csv$/i.test(name) || /team\.csv$/i.test(name));
  let importedPayload = null;
  if (builderJsonName && entries[builderJsonName]) {
    importedPayload = _normalizeCharacterPayload(JSON.parse(entries[builderJsonName]));
  } else if (trainerCsvName && entries[trainerCsvName]) {
    importedPayload = _applyTrainerCsvToPayload(entries[trainerCsvName], _readStoredTrainerPayload() || _snapshotCharacterState());
  }
  if (importedPayload) {
    localStorage.setItem("autoptu_character", JSON.stringify(importedPayload));
    _applyNormalizedCharacterPayload(importedPayload);
    setTrainerProfile(importedPayload);
  }
  if (teamCsvName && entries[teamCsvName]) {
    const importedTeam = _builderPokemonImportFromRosterCsv(entries[teamCsvName]);
    characterState.pokemon_builds = importedTeam.builds;
    _setBattleRosterCsv(importedTeam.csvText, file.name || "project-zip");
    saveCharacterToStorage();
    renderCharacterPokemonTeam();
  }
  if (!importedPayload && !(teamCsvName && entries[teamCsvName])) {
    throw new Error("Project ZIP did not contain a supported builder JSON, trainer CSV, or team CSV.");
  }
}

loadTrainerButton?.addEventListener("click", () => {



  loadTrainerFromStorage();



  saveSettings();



});



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
        await _importBuilderProjectZip(file);
        notifyUI("ok", "Project ZIP imported.", 2200);
      } else {
        const text = await _readTextFile(file);
        const isCsv = lowerName.endsWith(".csv");
        const importedPayload = isCsv
          ? _applyTrainerCsvToPayload(text, _readStoredTrainerPayload() || _snapshotCharacterState())
          : _normalizeCharacterPayload(JSON.parse(text));
        localStorage.setItem("autoptu_character", JSON.stringify(importedPayload));
        _applyNormalizedCharacterPayload(importedPayload);
        setTrainerProfile(importedPayload);
        notifyUI("ok", isCsv ? "Trainer CSV imported." : "Builder JSON imported.", 2200);
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
        _setBattleRosterCsv(entries[teamCsvName], file.name || "imported");
        notifyUI("ok", "Project ZIP team CSV loaded.", 1800);
      } else {
        const text = await _readTextFile(file);
        _setBattleRosterCsv(text, file.name || "imported");
        notifyUI("ok", "Roster CSV loaded.", 1800);
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



clearRosterCsvButton?.addEventListener("click", () => {



  _clearBattleRosterCsv();



  saveSettings();



});



clearTrainerButton?.addEventListener("click", () => {



  trainerProfile = null;



  trainerProfileRaw = null;



  if (useTrainerInput) useTrainerInput.checked = false;



  renderTrainerDetails();



  saveSettings();



});



statusTabs.forEach((tab) => {



  tab.addEventListener("click", () => {



    const filter = tab.getAttribute("data-team-filter") || "all";



    setCombatantTeamFilter(filter);



    render();



  });



});



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

    if (btn.disabled) return;

    goToCharacterStep(step);

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



builderUsefulChartsButton?.addEventListener("click", () => showUsefulChartsModal().catch(alertError));



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



    mode: modeSelect?.value || "sandbox",



    teamSize: teamSizeInput?.value || "3",



    sideCount: sideCountInput?.value || "2",



    circleInterval: circleIntervalInput?.value || "3",



    activeSlots: activeSlotsInput?.value || "1",



    minLevel: minLevelInput?.value || "1",



    maxLevel: maxLevelInput?.value || "10",



    autoInterval: autoIntervalInput?.value || "2000",



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







function _normalizeMoveKey(value) {



  return _normalizeSearchText(value).replace(/\s+/g, "");



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



    _applyCsvModeControls();



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



    input?.addEventListener("change", () => saveSettings());



  }



);



modeSelect?.addEventListener("change", () => {



  applyModeFieldVisibility();



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



    refreshState().catch(() => {});



    const now = Date.now();



    if (now - lastSpritePollAt >= 4500) {



      lastSpritePollAt = now;



      refreshSpriteStatus().catch(() => {});



    }



  }, 1500);



  loadSettings();



  applyModeFieldVisibility();



  _applyCsvModeControls();



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
































