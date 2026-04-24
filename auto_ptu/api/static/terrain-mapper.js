const analysisCanvas = document.getElementById("analysis-canvas");
const downloadLink = document.getElementById("download-link");
const stageEl = document.getElementById("tm-stage");
const stageScrollerEl = document.getElementById("stage-scroller");
const atlasImageEl = document.getElementById("atlas-image");
const gridEl = document.getElementById("tm-grid");
const segmentOverlayEl = document.getElementById("tm-segments");
const summaryEl = document.getElementById("map-summary");
const predictionSummaryEl = document.getElementById("prediction-summary");
const tileInfoEl = document.getElementById("tile-info");
const reviewListEl = document.getElementById("review-list");
const askPanelEl = document.getElementById("ask-panel");
const askSummaryEl = document.getElementById("ask-summary");
const predictionReviewBannerEl = document.getElementById("prediction-review-banner");
const predictionReviewSummaryEl = document.getElementById("prediction-review-summary");
const mapLibraryEl = document.getElementById("map-library");
const segmentListEl = document.getElementById("segment-list");
const segmentPreviewCanvasEl = document.getElementById("segment-preview");
const segmentPreviewInfoEl = document.getElementById("segment-preview-info");
const profileMetaEl = document.getElementById("profile-meta");
const predictionStatsEl = document.getElementById("prediction-stats");
const editorModeHelpEl = document.getElementById("editor-mode-help");
const presetSummaryEl = document.getElementById("preset-summary");
const nextStepTitleEl = document.getElementById("next-step-title");
const nextStepBodyEl = document.getElementById("next-step-body");
const showLabelsEl = document.getElementById("show-labels");
const actionStatusEl = document.getElementById("action-status");

const mapNameEl = document.getElementById("map-name");
const mapTagsEl = document.getElementById("map-tags");
const profileSelectEl = document.getElementById("profile-select");
const profileNameEl = document.getElementById("profile-name");
const profileCategoryEl = document.getElementById("profile-category");
const profileTagsEl = document.getElementById("profile-tags");

const gridWidthEl = document.getElementById("grid-width");
const gridHeightEl = document.getElementById("grid-height");
const offsetXEl = document.getElementById("offset-x");
const offsetYEl = document.getElementById("offset-y");
const tileWidthEl = document.getElementById("tile-width");
const tileHeightEl = document.getElementById("tile-height");
const zoomEl = document.getElementById("view-zoom");
const highConfidenceEl = document.getElementById("high-confidence");
const mediumConfidenceEl = document.getElementById("medium-confidence");

const labelSurfaceEl = document.getElementById("label-surface");
const labelStructureEl = document.getElementById("label-structure");
const labelPropEl = document.getElementById("label-prop");
const labelHeightEl = document.getElementById("label-height");
const labelHazardEl = document.getElementById("label-hazard");
const labelMovementEl = document.getElementById("label-movement");
const labelVisibilityEl = document.getElementById("label-visibility");
const labelCoverEl = document.getElementById("label-cover");
const labelStandableEl = document.getElementById("label-standable");
const hazardSpikesEl = document.getElementById("hazard-spikes");
const hazardToxicSpikesEl = document.getElementById("hazard-toxic-spikes");
const hazardStickyWebEl = document.getElementById("hazard-sticky-web");
const hazardStealthRockEl = document.getElementById("hazard-stealth-rock");
const hazardStealthRockFairyEl = document.getElementById("hazard-stealth-rock-fairy");
const hazardFireHazardsEl = document.getElementById("hazard-fire-hazards");
const trapDustEl = document.getElementById("trap-dust");
const trapTangleEl = document.getElementById("trap-tangle");
const trapSlickEl = document.getElementById("trap-slick");
const trapAbrasionEl = document.getElementById("trap-abrasion");
const trapGenericEl = document.getElementById("trap-generic");
const barrierCountEl = document.getElementById("barrier-count");
const barrierSourceNameEl = document.getElementById("barrier-source-name");
const barrierMoveNameEl = document.getElementById("barrier-move-name");
const frozenCountEl = document.getElementById("frozen-count");
const frozenSourceNameEl = document.getElementById("frozen-source-name");
const frozenDcEl = document.getElementById("frozen-dc");

const segmentNameEl = document.getElementById("segment-name");
const segmentRowEl = document.getElementById("segment-row");
const segmentColEl = document.getElementById("segment-col");
const segmentWidthEl = document.getElementById("segment-width");
const segmentHeightEl = document.getElementById("segment-height");
const segmentDrawToggleEl = document.getElementById("toggle-segment-draw");

const DEFAULT_SEGMENT_WIDTH = 9;
const DEFAULT_SEGMENT_HEIGHT = 7;

const SURFACE_OPTIONS = [
  ["", "Unknown"],
  ["grass", "Grass"],
  ["grassy", "Grassy"],
  ["grassland", "Grassland"],
  ["forest", "Forest"],
  ["water", "Water"],
  ["coast", "Coast"],
  ["ocean", "Ocean"],
  ["sand", "Sand"],
  ["desert", "Desert"],
  ["wetlands", "Wetlands"],
  ["rock", "Rock"],
  ["mountain", "Mountain"],
  ["road", "Road"],
  ["urban", "Urban"],
  ["cave", "Cave"],
  ["snow", "Snow"],
  ["ice", "Ice"],
  ["tundra", "Tundra"],
  ["ruins", "Ruins"],
  ["industrial", "Industrial"],
  ["roof", "Roof"],
  ["psychic", "Psychic"],
  ["volcanic", "Volcanic"],
];

const STRUCTURE_OPTIONS = [
  ["", "None"],
  ["wall", "Wall"],
  ["pillar", "Pillar"],
  ["fence", "Fence"],
  ["bridge", "Bridge"],
  ["ledge", "Ledge"],
  ["boulder", "Boulder"],
  ["tree", "Tree"],
];

const PROP_OPTIONS = [
  ["", "None"],
  ["bench", "Bench"],
  ["table", "Table"],
  ["crate", "Crate"],
  ["barrel", "Barrel"],
  ["machine", "Machine"],
  ["bush", "Bush"],
  ["rock", "Loose Rock"],
  ["waterfall", "Waterfall"],
  ["rubble", "Rubble"],
];

const HAZARD_OPTIONS = [
  ["", "None"],
  ["spikes", "Spikes"],
  ["toxic_spikes", "Toxic Spikes"],
  ["sticky_web", "Sticky Web"],
  ["stealth_rock", "Stealth Rock"],
  ["stealth_rock_fairy", "Fairy Stealth Rock"],
  ["fire_hazards", "Fire Hazards"],
];

const MOVEMENT_OPTIONS = [
  ["open", "Open"],
  ["difficult", "Difficult"],
  ["blocked", "Blocked / Impassable"],
];

const VISIBILITY_OPTIONS = [
  ["clear", "Clear"],
  ["covering", "Obscures Some Vision"],
  ["blocks_los", "Blocks Line Of Sight"],
];

const COVER_OPTIONS = [
  ["none", "None"],
  ["low", "Low Cover"],
  ["high", "High Cover"],
  ["full", "Full Cover"],
];

const TILE_PRESETS = [
  {
    id: "open-grass",
    name: "Open Grass",
    note: "Walkable ground",
    labels: { surface: "grass", structure: "", prop: "", height: 0, hazard: "", movement: "open", visibility: "clear", cover: "none", standable: true },
  },
  {
    id: "wall",
    name: "Wall",
    note: "Blocks movement and sight",
    labels: { surface: "", structure: "wall", prop: "", height: 2, hazard: "", movement: "blocked", visibility: "blocks_los", cover: "full", standable: false },
  },
  {
    id: "boulder",
    name: "Raised Rock",
    note: "Blocking terrain with elevation",
    labels: { surface: "rock", structure: "boulder", prop: "", height: 1, hazard: "", movement: "blocked", visibility: "covering", cover: "high", standable: false },
  },
  {
    id: "tree",
    name: "Tree",
    note: "Natural blocker",
    labels: { surface: "forest", structure: "tree", prop: "", height: 2, hazard: "", movement: "blocked", visibility: "blocks_los", cover: "high", standable: false },
  },
  {
    id: "bench",
    name: "Bench",
    note: "Prop with low cover",
    labels: { surface: "urban", structure: "", prop: "bench", height: 0, hazard: "", movement: "open", visibility: "clear", cover: "low", standable: true },
  },
  {
    id: "table",
    name: "Table",
    note: "Furniture obstacle",
    labels: { surface: "urban", structure: "", prop: "table", height: 1, hazard: "", movement: "difficult", visibility: "covering", cover: "low", standable: false },
  },
  {
    id: "bridge",
    name: "Bridge",
    note: "Standable over hazard",
    labels: { surface: "water", structure: "bridge", prop: "", height: 0, hazard: "", movement: "open", visibility: "clear", cover: "none", standable: true },
  },
  {
    id: "water",
    name: "Water",
    note: "Hazardous or slow ground",
    labels: { surface: "water", structure: "", prop: "", height: 0, hazard: "", movement: "difficult", visibility: "clear", cover: "none", standable: true },
  },
];

const state = {
  mapId: "",
  imageUrl: "",
  imageName: "",
  imageDataUrl: "",
  imageMeta: { width: 0, height: 0, source_name: "" },
  selectedKey: "",
  activeSegmentId: "",
  segmentToolActive: false,
  isDraggingSegment: false,
  isPainting: false,
  paintLastKey: "",
  suppressTileClick: false,
  segmentDraft: null,
  editorMode: "inspect",
  library: [],
  profiles: [],
  currentProfile: null,
  activePresetId: "",
  atlas: {
    grid: { width: 15, height: 10, offset_x: 0, offset_y: 0, tile_width: 52, tile_height: 52 },
    image_scale: 1,
    review_rules: { high_confidence: 0.82, medium_confidence: 0.58 },
    tiles: [],
  },
  segments: [],
  lastPredictionStats: null,
  lowConfidenceQueue: [],
  mediumConfidenceQueue: [],
  showLabels: false,
  autosaveTimer: null,
  suspendAutosave: false,
};

function api(path, payload, method = "POST") {
  return fetch(path, {
    method,
    headers: method === "GET" ? undefined : { "Content-Type": "application/json" },
    body: method === "GET" ? undefined : JSON.stringify(payload || {}),
  }).then(async (res) => {
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  });
}

function tileKey(row, col) {
  return `${row},${col}`;
}

function setActionStatus(message, kind = "ok") {
  if (!actionStatusEl) return;
  const text = String(message || "").trim();
  if (!text) {
    actionStatusEl.hidden = true;
    actionStatusEl.textContent = "";
    actionStatusEl.className = "tm-status";
    return;
  }
  actionStatusEl.hidden = false;
  actionStatusEl.textContent = text;
  actionStatusEl.className = `tm-status ${kind}`;
}

function inferDefaultAtlasName() {
  const explicit = String(mapNameEl.value || "").trim();
  if (explicit) return explicit;
  const sourceName = String(state.imageName || state.imageMeta?.source_name || "").trim();
  if (sourceName) {
    return sourceName.replace(/\.[^.]+$/, "").trim() || "terrain-atlas";
  }
  return `terrain-atlas-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}`;
}

function hasWorkspaceContent() {
  const hasImage = Boolean(state.imageDataUrl || state.imageUrl || state.imageName);
  const hasName = Boolean(String(mapNameEl.value || "").trim());
  const hasTags = Boolean(String(mapTagsEl.value || "").trim());
  const hasSegments = Array.isArray(state.segments) && state.segments.length > 0;
  const hasAnnotations = Array.isArray(state.atlas?.tiles) && state.atlas.tiles.some((tile) => hasLabels(tile.labels));
  return hasImage || hasName || hasTags || hasSegments || hasAnnotations;
}

async function saveWorkspaceDraftNow() {
  if (state.suspendAutosave) return;
  if (!hasWorkspaceContent()) return;
  const payload = buildMapPayload();
  await api("/api/terrain/workspace", payload);
}

function scheduleWorkspaceAutosave() {
  if (state.suspendAutosave) return;
  if (state.autosaveTimer) clearTimeout(state.autosaveTimer);
  state.autosaveTimer = setTimeout(() => {
    saveWorkspaceDraftNow().catch(() => {});
  }, 700);
}

async function clearWorkspaceDraft() {
  if (state.autosaveTimer) {
    clearTimeout(state.autosaveTimer);
    state.autosaveTimer = null;
  }
  await api("/api/terrain/workspace/clear", {});
}

function parseTags(value) {
  return String(value || "")
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

function makeEmptyTile(row, col) {
  return {
    row,
    col,
    labels: {
      surface: "",
      structure: "",
      prop: "",
      object: "",
      height: 0,
      hazard: "",
      hazards: {},
      traps: {},
      barriers: [],
      frozen_domain: [],
      trap_sources: {},
      movement: "open",
      visibility: "clear",
      cover: "none",
      standable: true,
      blocks_movement: false,
      difficult: false,
      blocks_los: false,
    },
    feature_vector: [],
    tile_image_hash: "",
    tile_crop_data_url: "",
    confirmed_by_user: false,
    source: "unlabeled",
    status: "unlabeled",
    review_state: "low",
    confidence: 0,
    confidence_before_correction: 0,
    neighbor_summary: { surface_counts: {}, hazard_counts: {}, blocking_neighbors: 0 },
    matches: [],
  };
}

function cloneTile(tile) {
  return {
    ...tile,
    labels: { ...tile.labels },
    feature_vector: Array.isArray(tile.feature_vector) ? [...tile.feature_vector] : [],
    neighbor_summary: {
      surface_counts: { ...(tile.neighbor_summary?.surface_counts || {}) },
      hazard_counts: { ...(tile.neighbor_summary?.hazard_counts || {}) },
      blocking_neighbors: Number(tile.neighbor_summary?.blocking_neighbors || 0),
    },
    matches: Array.isArray(tile.matches) ? tile.matches.map((entry) => ({ ...entry, labels: { ...(entry.labels || {}) } })) : [],
  };
}

function hasLabels(labels) {
  return Boolean(
    labels.surface ||
      labels.structure ||
      labels.prop ||
      labels.object ||
      labels.hazard ||
      Object.keys(labels.hazards || {}).length ||
      Object.keys(labels.traps || {}).length ||
      (Array.isArray(labels.barriers) && labels.barriers.length) ||
      (Array.isArray(labels.frozen_domain) && labels.frozen_domain.length) ||
      Number(labels.height || 0) > 0 ||
      labels.blocks_movement ||
      labels.difficult ||
      labels.cover === "low" ||
      labels.cover === "high" ||
      labels.cover === "full"
  );
}

function readCountInput(inputEl) {
  return Math.max(0, Number(inputEl?.value || 0) || 0);
}

function buildCountMap(entries) {
  const result = {};
  for (const [key, count] of entries) {
    const value = Math.max(0, Number(count || 0) || 0);
    if (value > 0) result[key] = value;
  }
  return result;
}

function firstNonEmptyKey(value) {
  if (!value || typeof value !== "object") return "";
  return Object.keys(value).find((key) => Number(value[key] || 0) > 0) || "";
}

function createOption(selectEl, value, label) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = label;
  selectEl.appendChild(option);
}

function fillSelect(selectEl, options) {
  selectEl.replaceChildren();
  for (const [value, label] of options) {
    createOption(selectEl, value, label);
  }
}

function fillHeightSelect() {
  labelHeightEl.replaceChildren();
  createOption(labelHeightEl, "0", "0");
  for (let value = 1; value <= 9; value += 1) {
    createOption(labelHeightEl, String(value), String(value));
  }
}

function readEditorLabels() {
  const movement = String(labelMovementEl.value || "open");
  const visibility = String(labelVisibilityEl.value || "clear");
  const hazards = buildCountMap([
    ["spikes", readCountInput(hazardSpikesEl)],
    ["toxic_spikes", readCountInput(hazardToxicSpikesEl)],
    ["sticky_web", readCountInput(hazardStickyWebEl)],
    ["stealth_rock", readCountInput(hazardStealthRockEl)],
    ["stealth_rock_fairy", readCountInput(hazardStealthRockFairyEl)],
    ["fire_hazards", readCountInput(hazardFireHazardsEl)],
  ]);
  const quickHazard = String(labelHazardEl.value || "");
  if (quickHazard && !hazards[quickHazard]) hazards[quickHazard] = 1;
  const traps = buildCountMap([
    ["dust_trap", readCountInput(trapDustEl)],
    ["tangle_trap", readCountInput(trapTangleEl)],
    ["slick_trap", readCountInput(trapSlickEl)],
    ["abrasion_trap", readCountInput(trapAbrasionEl)],
    ["trap", readCountInput(trapGenericEl)],
  ]);
  const barrierCount = readCountInput(barrierCountEl);
  const barriers = Array.from({ length: barrierCount }, () => ({
    move: String(barrierMoveNameEl.value || "").trim() || "Barrier",
    source_name: String(barrierSourceNameEl.value || "").trim() || null,
    source_id: null,
  }));
  const frozenCount = readCountInput(frozenCountEl);
  const frozenDomain = Array.from({ length: frozenCount }, () => ({
    source_name: String(frozenSourceNameEl.value || "").trim() || null,
    source_id: null,
    trainer_id: null,
    dc: Math.max(1, Number(frozenDcEl.value || 4) || 4),
  }));
  return {
    surface: String(labelSurfaceEl.value || ""),
    structure: String(labelStructureEl.value || ""),
    prop: String(labelPropEl.value || ""),
    object: String(labelStructureEl.value || "") || String(labelPropEl.value || ""),
    height: Math.max(0, Number(labelHeightEl.value || 0)),
    hazard: quickHazard || firstNonEmptyKey(hazards),
    hazards,
    traps,
    barriers,
    frozen_domain: frozenDomain,
    trap_sources: {},
    movement,
    visibility,
    cover: String(labelCoverEl.value || "none"),
    standable: Boolean(labelStandableEl.checked),
    blocks_movement: movement === "blocked",
    difficult: movement === "difficult",
    blocks_los: visibility === "blocks_los",
  };
}

function setEditorMode(mode) {
  state.editorMode = mode;
  document.querySelectorAll(".tm-chip[data-editor-mode]").forEach((chip) => {
    chip.classList.toggle("active", chip.dataset.editorMode === mode);
  });
  if (editorModeHelpEl) {
    if (mode === "teach") {
      editorModeHelpEl.textContent = "Teach is active. Pick a Quick Pick or PTU labels, then click or drag across matching tiles.";
    } else if (mode === "clear") {
      editorModeHelpEl.textContent = "Erase is active. Click or drag across tiles to remove labels.";
    } else {
      editorModeHelpEl.textContent = "Inspect is active. Click one tile to see its details and fix it if needed.";
    }
  }
}

function syncSegmentDrawToggle() {
  if (!segmentDrawToggleEl) return;
  segmentDrawToggleEl.classList.toggle("active", state.segmentToolActive);
  segmentDrawToggleEl.textContent = state.segmentToolActive ? "Draw Segment On Atlas: ON" : "Draw Segment On Atlas";
}

function setEditorLabels(labels) {
  const next = {
    ...makeEmptyTile(0, 0).labels,
    ...(labels || {}),
  };
  labelSurfaceEl.value = next.surface || "";
  labelStructureEl.value = next.structure || "";
  labelPropEl.value = next.prop || "";
  labelHeightEl.value = String(Number(next.height || 0));
  const hazards = next.hazards && typeof next.hazards === "object" ? next.hazards : {};
  const traps = next.traps && typeof next.traps === "object" ? next.traps : {};
  labelHazardEl.value = next.hazard || firstNonEmptyKey(hazards) || "";
  hazardSpikesEl.value = String(Number(hazards.spikes || 0));
  hazardToxicSpikesEl.value = String(Number(hazards.toxic_spikes || 0));
  hazardStickyWebEl.value = String(Number(hazards.sticky_web || 0));
  hazardStealthRockEl.value = String(Number(hazards.stealth_rock || 0));
  hazardStealthRockFairyEl.value = String(Number(hazards.stealth_rock_fairy || 0));
  hazardFireHazardsEl.value = String(Number(hazards.fire_hazards || 0));
  trapDustEl.value = String(Number(traps.dust_trap || 0));
  trapTangleEl.value = String(Number(traps.tangle_trap || 0));
  trapSlickEl.value = String(Number(traps.slick_trap || 0));
  trapAbrasionEl.value = String(Number(traps.abrasion_trap || 0));
  trapGenericEl.value = String(Number(traps.trap || 0));
  barrierCountEl.value = String(Array.isArray(next.barriers) ? next.barriers.length : 0);
  barrierSourceNameEl.value = Array.isArray(next.barriers) && next.barriers[0] ? String(next.barriers[0].source_name || "") : "";
  barrierMoveNameEl.value = Array.isArray(next.barriers) && next.barriers[0] ? String(next.barriers[0].move || "Barrier") : "Barrier";
  frozenCountEl.value = String(Array.isArray(next.frozen_domain) ? next.frozen_domain.length : 0);
  frozenSourceNameEl.value = Array.isArray(next.frozen_domain) && next.frozen_domain[0] ? String(next.frozen_domain[0].source_name || "") : "";
  frozenDcEl.value = String(Array.isArray(next.frozen_domain) && next.frozen_domain[0] ? Math.max(1, Number(next.frozen_domain[0].dc || 4)) : 4);
  labelMovementEl.value = next.movement || (next.blocks_movement ? "blocked" : next.difficult ? "difficult" : "open");
  labelVisibilityEl.value = next.visibility || (next.blocks_los ? "blocks_los" : "clear");
  labelCoverEl.value = next.cover || "none";
  labelStandableEl.checked = Boolean(next.standable);
}

function applyPreset(preset) {
  state.activePresetId = preset.id;
  setEditorLabels(preset.labels);
  if (presetSummaryEl) {
    presetSummaryEl.textContent = `${preset.name}: ${preset.note}`;
  }
  document.querySelectorAll("#preset-palette button").forEach((button) => {
    button.classList.toggle("active", button.dataset.presetId === preset.id);
  });
}

function syncInputsFromState() {
  gridWidthEl.value = String(state.atlas.grid.width);
  gridHeightEl.value = String(state.atlas.grid.height);
  offsetXEl.value = String(state.atlas.grid.offset_x);
  offsetYEl.value = String(state.atlas.grid.offset_y);
  tileWidthEl.value = String(state.atlas.grid.tile_width);
  tileHeightEl.value = String(state.atlas.grid.tile_height);
  zoomEl.value = String(state.atlas.image_scale || 1);
  highConfidenceEl.value = String(state.atlas.review_rules.high_confidence);
  mediumConfidenceEl.value = String(state.atlas.review_rules.medium_confidence);
}

function resetSegmentInputs() {
  segmentNameEl.value = "";
  segmentRowEl.value = "0";
  segmentColEl.value = "0";
  segmentWidthEl.value = String(DEFAULT_SEGMENT_WIDTH);
  segmentHeightEl.value = String(DEFAULT_SEGMENT_HEIGHT);
}

function clampSegmentValue(value, maxExclusive) {
  return Math.max(0, Math.min(maxExclusive - 1, Number(value || 0)));
}

function normalizeSegmentRect(value) {
  if (!value) return null;
  const rowA = clampSegmentValue(value.row ?? value.anchorRow ?? 0, state.atlas.grid.height);
  const colA = clampSegmentValue(value.col ?? value.anchorCol ?? 0, state.atlas.grid.width);
  const rowB = clampSegmentValue(value.row2 ?? value.currentRow ?? rowA, state.atlas.grid.height);
  const colB = clampSegmentValue(value.col2 ?? value.currentCol ?? colA, state.atlas.grid.width);
  const row = Math.min(rowA, rowB);
  const col = Math.min(colA, colB);
  const height = Math.max(1, Math.abs(rowB - rowA) + 1);
  const width = Math.max(1, Math.abs(colB - colA) + 1);
  return {
    row,
    col,
    width: Math.min(width, state.atlas.grid.width - col),
    height: Math.min(height, state.atlas.grid.height - row),
  };
}

function activeSegmentOrDraft() {
  return normalizeSegmentRect(state.segmentDraft) || activeSegment() || null;
}

function ensureTiles() {
  const next = [];
  const current = new Map((state.atlas.tiles || []).map((tile) => [tileKey(tile.row, tile.col), cloneTile(tile)]));
  for (let row = 0; row < state.atlas.grid.height; row += 1) {
    for (let col = 0; col < state.atlas.grid.width; col += 1) {
      next.push(current.get(tileKey(row, col)) || makeEmptyTile(row, col));
    }
  }
  state.atlas.tiles = next;
}

function getTile(row, col) {
  ensureTiles();
  return state.atlas.tiles.find((tile) => tile.row === row && tile.col === col) || null;
}

function getSelectedTile() {
  if (!state.selectedKey) return null;
  const [row, col] = state.selectedKey.split(",").map((value) => Number(value));
  return getTile(row, col);
}

function imageScaleValue() {
  const scale = Number(zoomEl.value || state.atlas.image_scale || 1);
  return Math.max(0.25, Number.isFinite(scale) ? scale : 1);
}

function displayImageMetrics() {
  const imageScale = imageScaleValue();
  state.atlas.image_scale = imageScale;
  return {
    imageScale,
    imageWidth: Number(state.imageMeta.width || 0) * imageScale,
    imageHeight: Number(state.imageMeta.height || 0) * imageScale,
  };
}

function stageMetrics() {
  const { imageScale, imageWidth, imageHeight } = displayImageMetrics();
  const gridWidth = Number(state.atlas.grid.offset_x) + Number(state.atlas.grid.tile_width) * Number(state.atlas.grid.width);
  const gridHeight = Number(state.atlas.grid.offset_y) + Number(state.atlas.grid.tile_height) * Number(state.atlas.grid.height);
  return {
    imageScale,
    imageWidth,
    imageHeight,
    stageWidth: Math.max(320, imageWidth, gridWidth),
    stageHeight: Math.max(240, imageHeight, gridHeight),
  };
}

function captureStageViewport() {
  const stageWidth = Math.max(1, stageEl.scrollWidth || stageEl.clientWidth || 1);
  const stageHeight = Math.max(1, stageEl.scrollHeight || stageEl.clientHeight || 1);
  return {
    centerX: (stageScrollerEl.scrollLeft + stageScrollerEl.clientWidth / 2) / stageWidth,
    centerY: (stageScrollerEl.scrollTop + stageScrollerEl.clientHeight / 2) / stageHeight,
  };
}

function restoreStageViewport(viewport) {
  if (!viewport) return;
  const stageWidth = Math.max(1, stageEl.scrollWidth || stageEl.clientWidth || 1);
  const stageHeight = Math.max(1, stageEl.scrollHeight || stageEl.clientHeight || 1);
  const targetLeft = stageWidth * viewport.centerX - stageScrollerEl.clientWidth / 2;
  const targetTop = stageHeight * viewport.centerY - stageScrollerEl.clientHeight / 2;
  stageScrollerEl.scrollLeft = Math.max(0, Math.round(targetLeft));
  stageScrollerEl.scrollTop = Math.max(0, Math.round(targetTop));
}

function briefLabel(labels) {
  const parts = [];
  if (labels.surface) parts.push(labels.surface);
  if (labels.structure) parts.push(labels.structure);
  else if (labels.prop) parts.push(labels.prop);
  else if (labels.object) parts.push(labels.object);
  if (!parts.length && labels.hazard) parts.push(labels.hazard);
  if (!parts.length) {
    const firstHazard = firstNonEmptyKey(labels.hazards || {});
    const firstTrap = firstNonEmptyKey(labels.traps || {});
    if (firstHazard) parts.push(firstHazard);
    else if (firstTrap) parts.push(firstTrap);
    else if (Array.isArray(labels.barriers) && labels.barriers.length) parts.push("barrier");
    else if (Array.isArray(labels.frozen_domain) && labels.frozen_domain.length) parts.push("frozen");
  }
  if (!parts.length && labels.blocks_movement) parts.push("blocked");
  if (!parts.length && labels.difficult) parts.push("difficult");
  return parts.join(" / ") || "Unlabeled";
}

function compactLabel(labels) {
  const parts = [];
  if (labels.surface) parts.push(labels.surface);
  if (labels.structure) parts.push(labels.structure);
  else if (labels.prop) parts.push(labels.prop);
  else if (labels.object) parts.push(labels.object);
  if (!parts.length && labels.blocks_movement) parts.push("blocked");
  if (!parts.length && labels.difficult) parts.push("difficult");
  if (!parts.length) {
    const firstHazard = labels.hazard || firstNonEmptyKey(labels.hazards || {}) || firstNonEmptyKey(labels.traps || {});
    if (firstHazard) parts.push(firstHazard);
  }
  return parts.join(" · ") || "tile";
}

function tileMarkerBadges(labels) {
  const badges = [];
  if (labels.blocks_movement) badges.push({ text: "BLK", kind: "blocked" });
  else if (labels.difficult) badges.push({ text: "DIF", kind: "difficult" });
  if (Number(labels.height || 0) > 0) badges.push({ text: `H${Number(labels.height || 0)}`, kind: "height" });
  const firstHazard = labels.hazard || firstNonEmptyKey(labels.hazards || {}) || firstNonEmptyKey(labels.traps || {});
  if (firstHazard) badges.push({ text: "HZ", kind: "hazard" });
  return badges.slice(0, 3);
}

function renderPredictionBadges() {
  predictionSummaryEl.replaceChildren();
  const counts = { high: 0, medium: 0, low: 0 };
  for (const tile of state.atlas.tiles) {
    if (!hasLabels(tile.labels) || tile.confirmed_by_user) continue;
    if (tile.review_state === "high") counts.high += 1;
    else if (tile.review_state === "medium") counts.medium += 1;
    else counts.low += 1;
  }
  for (const band of ["high", "medium", "low"]) {
    const badge = document.createElement("div");
    badge.className = `tm-badge ${band}`;
    badge.textContent = `${band.toUpperCase()}: ${counts[band]}`;
    predictionSummaryEl.appendChild(badge);
  }
}

function updateSummary() {
  const confirmed = state.atlas.tiles.filter((tile) => tile.confirmed_by_user && hasLabels(tile.labels)).length;
  const predicted = state.atlas.tiles.filter((tile) => !tile.confirmed_by_user && hasLabels(tile.labels)).length;
  const review = state.atlas.tiles.filter(
    (tile) => !tile.confirmed_by_user && hasLabels(tile.labels) && (tile.review_state === "medium" || tile.review_state === "low")
  ).length;
  const profileText = state.currentProfile ? `Profile ${state.currentProfile.name}` : "No profile";
  summaryEl.textContent =
    `${state.atlas.grid.width}x${state.atlas.grid.height} grid | ${confirmed} confirmed | ${predicted} predicted | ${review} review | ${profileText}`;
  updateGuide();
}

function updateGuide() {
  let title = "Step 1: Load a map";
  let body = "Open a saved atlas or import a new image.";
  const hasImage = Boolean(state.imageDataUrl || state.imageUrl);
  const hasProfile = Boolean(state.currentProfile || String(profileNameEl.value || "").trim());
  const confirmed = state.atlas.tiles.filter((tile) => tile.confirmed_by_user && hasLabels(tile.labels)).length;
  const reviewCount = state.atlas.tiles.filter(
    (tile) => !tile.confirmed_by_user && hasLabels(tile.labels) && (tile.review_state === "medium" || tile.review_state === "low")
  ).length;
  if (hasImage) {
    title = "Step 2: Line the grid up";
    body = "Use Grid Columns, Grid Rows, Tile Width, Tile Height, Offset X, Offset Y, and Image Scale until the lines match the art.";
  }
  if (hasImage && !hasProfile) {
    title = "Step 3: Choose a profile";
    body = "Pick an old profile if this map uses a familiar tileset. Otherwise type a new name and save it.";
  }
  if (hasImage && hasProfile && confirmed < 6) {
    title = "Step 4: Teach a few tiles";
    body = "Pick a Quick Pick like Open Grass, Wall, Tree, or Water. Switch to Teach, then click several matching tiles.";
  }
  if (hasImage && hasProfile && confirmed >= 6 && reviewCount === 0) {
    title = "Step 5: Fill the rest";
    body = "Click Fill Map And Review. The mapper will fill easy tiles and ask you about unsure ones.";
  }
  if (reviewCount > 0) {
    title = "Step 6: Review the unsure tiles";
    body = "Use the Review Queue. Pick the shown tile, fix it if needed, then confirm it.";
  }
  if (state.activeSegmentId || normalizeSegmentRect(state.segmentDraft)) {
    title = "Step 7: Export a battle section";
    body = "Your active segment is ready. Apply it to the battle or export JSON.";
  }
  if (nextStepTitleEl) nextStepTitleEl.textContent = title;
  if (nextStepBodyEl) nextStepBodyEl.textContent = body;
}

function renderTileInfo() {
  const tile = getSelectedTile();
  if (!tile) {
    tileInfoEl.textContent = "No tile selected.";
    return;
  }
  const labels = tile.labels || {};
  const hazardKeys = Object.keys(labels.hazards || {});
  const trapKeys = Object.keys(labels.traps || {});
  tileInfoEl.textContent = [
    `Row ${tile.row + 1}, Col ${tile.col + 1}`,
    `Surface: ${labels.surface || "-"}`,
    `Structure: ${labels.structure || "-"}`,
    `Prop: ${labels.prop || "-"}`,
    `Movement: ${labels.movement || "-"}`,
    `Height: ${Number(labels.height || 0)}`,
    `Cover: ${labels.cover || "-"}`,
    `Visibility: ${labels.visibility || "-"}`,
    `Hazards: ${hazardKeys.length ? hazardKeys.join(", ") : labels.hazard || "-"}`,
    `Traps: ${trapKeys.length ? trapKeys.join(", ") : "-"}`,
    `Confirmed: ${tile.confirmed_by_user ? "yes" : "no"}`,
    `Confidence: ${tile.confidence ? `${Math.round(tile.confidence * 100)}%` : "-"}`,
  ].join("\n");
  setEditorLabels(tile.labels);
}

function renderAskPanel() {
  const lowQueue = state.lowConfidenceQueue.filter((key) => {
    const [row, col] = key.split(",").map((value) => Number(value));
    const tile = getTile(row, col);
    return tile && !tile.confirmed_by_user && tile.review_state === "low";
  });
  state.lowConfidenceQueue = lowQueue;
  const nextKey = lowQueue[0];
  if (!nextKey) {
    askPanelEl.hidden = true;
    askPanelEl.classList.remove("attention");
    askSummaryEl.textContent = "No active question.";
    return;
  }
  const [row, col] = nextKey.split(",").map((value) => Number(value));
  const tile = getTile(row, col);
  askPanelEl.hidden = false;
  askPanelEl.classList.add("attention");
  askSummaryEl.textContent = `Question ${1} of ${lowQueue.length}: tile ${row + 1}, ${col + 1} needs an answer now. Predicted: ${briefLabel(tile.labels)} at ${Math.round(tile.confidence * 100)}%. Adjust labels if needed, then accept or skip.`;
}

function renderPredictionReviewBanner() {
  const low = state.lowConfidenceQueue.length;
  const medium = state.mediumConfidenceQueue.length;
  if (!state.lastPredictionStats) {
    predictionReviewBannerEl.hidden = true;
    predictionReviewSummaryEl.textContent = "No review summary yet.";
    return;
  }
  predictionReviewBannerEl.hidden = false;
  if (low > 0) {
    predictionReviewSummaryEl.textContent = `The fill step is waiting on you. ${low} low-confidence tiles require confirmation now, and ${medium} medium-confidence tiles are queued for review after that.`;
    predictionReviewBannerEl.classList.add("attention");
    return;
  }
  predictionReviewBannerEl.classList.remove("attention");
  if (medium > 0) {
    predictionReviewSummaryEl.textContent = `Autofill completed. ${medium} medium-confidence tiles still need review before you should trust the atlas.`;
  } else {
    predictionReviewSummaryEl.textContent = "Autofill completed. No review items remain.";
  }
}

function renderReviewList() {
  reviewListEl.replaceChildren();
  const queue = state.atlas.tiles
    .filter((tile) => !tile.confirmed_by_user && hasLabels(tile.labels) && (tile.review_state === "medium" || tile.review_state === "low"))
    .sort((a, b) => {
      const priority = { low: 0, medium: 1 };
      return priority[a.review_state] - priority[b.review_state] || a.row - b.row || a.col - b.col;
    });
  if (!queue.length) {
    const empty = document.createElement("div");
    empty.className = "tm-empty";
    empty.textContent = "No review items. Teach examples or run prediction.";
    reviewListEl.appendChild(empty);
    renderAskPanel();
    renderPredictionReviewBanner();
    return;
  }
  for (const tile of queue) {
    const button = document.createElement("button");
    button.type = "button";
    if (tileKey(tile.row, tile.col) === state.selectedKey) button.classList.add("active");
    const name = document.createElement("div");
    name.className = "tm-review-name";
    name.textContent = `Row ${tile.row + 1}, Col ${tile.col + 1}`;
    const meta = document.createElement("div");
    meta.className = "tm-review-meta";
    meta.textContent = `${tile.review_state.toUpperCase()} | ${Math.round(tile.confidence * 100)}% | ${briefLabel(tile.labels)}`;
    button.append(name, meta);
    button.addEventListener("click", async () => {
      setEditorMode("inspect");
      state.selectedKey = tileKey(tile.row, tile.col);
      renderGrid();
    });
    reviewListEl.appendChild(button);
  }
  renderAskPanel();
  renderPredictionReviewBanner();
}

function renderLibrary() {
  mapLibraryEl.replaceChildren();
  if (!state.library.length) {
    const empty = document.createElement("div");
    empty.className = "tm-empty";
    empty.textContent = "No saved atlases yet.";
    mapLibraryEl.appendChild(empty);
    return;
  }
  for (const entry of state.library) {
    const button = document.createElement("button");
    button.type = "button";
    const name = document.createElement("div");
    name.className = "tm-library-name";
    name.textContent = entry.name || entry.id;
    const meta = document.createElement("div");
    meta.className = "tm-library-meta";
    meta.textContent = `${entry.profile_id || "No profile"} | ${entry.annotated_tiles || 0} annotated | ${entry.segment_count || 0} segments`;
    button.append(name, meta);
    button.addEventListener("click", async () => {
      await loadSavedMap(entry.id);
    });
    mapLibraryEl.appendChild(button);
  }
}

function renderProfiles() {
  const currentValue = profileSelectEl.value;
  profileSelectEl.replaceChildren();
  createOption(profileSelectEl, "", "No profile selected");
  for (const profile of state.profiles) {
    createOption(profileSelectEl, profile.id, `${profile.name} (${profile.example_count || 0})`);
  }
  profileSelectEl.value = state.currentProfile?.id || currentValue || "";
  if (state.currentProfile) {
    profileMetaEl.textContent =
      `${state.currentProfile.name}\nCategory: ${state.currentProfile.category || "custom"}\nExamples: ${state.currentProfile.example_count || 0}\nUpdated: ${state.currentProfile.updated_at || "n/a"}`;
  } else {
    profileMetaEl.textContent = "Profiles keep confirmed tile examples and corrections grouped by style. Choose an existing profile when this map matches a known tileset, otherwise create a new one.";
  }
}

function renderPresetPalette() {
  const box = document.getElementById("preset-palette");
  box.replaceChildren();
  for (const preset of TILE_PRESETS) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.presetId = preset.id;
    button.classList.toggle("active", preset.id === state.activePresetId);
    const title = document.createElement("strong");
    title.textContent = preset.name;
    const note = document.createElement("span");
    note.textContent = preset.note;
    button.append(title, note);
    button.addEventListener("click", () => applyPreset(preset));
    box.appendChild(button);
  }
}

function renderSegments() {
  segmentListEl.replaceChildren();
  if (!state.segments.length) {
    const empty = document.createElement("div");
    empty.className = "tm-empty";
    empty.textContent = "No saved battlefield segments.";
    segmentListEl.appendChild(empty);
    renderSegmentPreview();
    return;
  }
  for (const segment of state.segments) {
    const button = document.createElement("button");
    button.type = "button";
    if (segment.id === state.activeSegmentId) button.classList.add("active");
    const name = document.createElement("div");
    name.className = "tm-library-name";
    name.textContent = segment.name;
    const meta = document.createElement("div");
    meta.className = "tm-library-meta";
    meta.textContent = `r${segment.row + 1}, c${segment.col + 1} | ${segment.width}x${segment.height}`;
    button.append(name, meta);
    button.addEventListener("click", () => {
      state.activeSegmentId = segment.id;
      renderSegments();
      renderGrid();
    });
    segmentListEl.appendChild(button);
  }
  renderSegmentPreview();
}

function segmentPixelBounds(segment) {
  const offsetX = Number(state.atlas.grid.offset_x);
  const offsetY = Number(state.atlas.grid.offset_y);
  const tileWidth = Number(state.atlas.grid.tile_width);
  const tileHeight = Number(state.atlas.grid.tile_height);
  return {
    left: offsetX + segment.col * tileWidth,
    top: offsetY + segment.row * tileHeight,
    width: segment.width * tileWidth,
    height: segment.height * tileHeight,
  };
}

function renderSegmentOverlay() {
  const { stageWidth, stageHeight } = stageMetrics();
  segmentOverlayEl.style.width = `${stageWidth}px`;
  segmentOverlayEl.style.height = `${stageHeight}px`;
  segmentOverlayEl.replaceChildren();

  for (const segment of state.segments) {
    const bounds = segmentPixelBounds(segment);
    const box = document.createElement("button");
    box.type = "button";
    box.className = "tm-segment-box";
    if (segment.id === state.activeSegmentId) box.classList.add("active");
    box.style.left = `${bounds.left}px`;
    box.style.top = `${bounds.top}px`;
    box.style.width = `${bounds.width}px`;
    box.style.height = `${bounds.height}px`;
    const label = document.createElement("span");
    label.className = "tm-segment-label";
    label.textContent = `${segment.name} (${segment.width}x${segment.height})`;
    box.appendChild(label);
    box.addEventListener("click", () => {
      state.activeSegmentId = segment.id;
      segmentRowEl.value = String(segment.row);
      segmentColEl.value = String(segment.col);
      segmentWidthEl.value = String(segment.width);
      segmentHeightEl.value = String(segment.height);
      segmentNameEl.value = segment.name;
      renderSegments();
      renderGrid();
    });
    segmentOverlayEl.appendChild(box);
  }

  const draft = normalizeSegmentRect(state.segmentDraft);
  if (draft) {
    const bounds = segmentPixelBounds(draft);
    const box = document.createElement("div");
    box.className = "tm-segment-box draft";
    box.style.left = `${bounds.left}px`;
    box.style.top = `${bounds.top}px`;
    box.style.width = `${bounds.width}px`;
    box.style.height = `${bounds.height}px`;
    const label = document.createElement("span");
    label.className = "tm-segment-label";
    label.textContent = `Draft ${draft.width}x${draft.height}`;
    box.appendChild(label);
    segmentOverlayEl.appendChild(box);
  }
}

function renderSegmentPreview() {
  const segment = activeSegmentOrDraft();
  const draft = normalizeSegmentRect(state.segmentDraft);
  const ctx = segmentPreviewCanvasEl.getContext("2d");
  ctx.clearRect(0, 0, segmentPreviewCanvasEl.width, segmentPreviewCanvasEl.height);

  if (!segment) {
    segmentPreviewInfoEl.textContent = "No active segment. Export will use the full atlas.";
    ctx.fillStyle = "rgba(14, 22, 18, 0.96)";
    ctx.fillRect(0, 0, segmentPreviewCanvasEl.width, segmentPreviewCanvasEl.height);
    ctx.fillStyle = "#a2b9a6";
    ctx.font = "14px Trebuchet MS";
    ctx.fillText("No segment selected", 16, 28);
    return;
  }

  const widthPx = Math.max(1, Number(state.atlas.grid.tile_width) * segment.width);
  const heightPx = Math.max(1, Number(state.atlas.grid.tile_height) * segment.height);
  const { imageScale } = displayImageMetrics();
  const sx = (Number(state.atlas.grid.offset_x) + segment.col * Number(state.atlas.grid.tile_width)) / imageScale;
  const sy = (Number(state.atlas.grid.offset_y) + segment.row * Number(state.atlas.grid.tile_height)) / imageScale;
  const sourceWidth = widthPx / imageScale;
  const sourceHeight = heightPx / imageScale;
  segmentPreviewInfoEl.textContent = draft
    ? `Draft export: row ${segment.row + 1}, col ${segment.col + 1}, ${segment.width}x${segment.height} tiles. Save Segment to keep it in the atlas.`
    : `Active export: row ${segment.row + 1}, col ${segment.col + 1}, ${segment.width}x${segment.height} tiles.`;

  ctx.fillStyle = "rgba(14, 22, 18, 0.96)";
  ctx.fillRect(0, 0, segmentPreviewCanvasEl.width, segmentPreviewCanvasEl.height);

  const scale = Math.min(segmentPreviewCanvasEl.width / widthPx, segmentPreviewCanvasEl.height / heightPx);
  const drawWidth = Math.max(1, Math.floor(widthPx * scale));
  const drawHeight = Math.max(1, Math.floor(heightPx * scale));
  const dx = Math.floor((segmentPreviewCanvasEl.width - drawWidth) / 2);
  const dy = Math.floor((segmentPreviewCanvasEl.height - drawHeight) / 2);

  if (state.imageUrl && atlasImageEl.naturalWidth > 0) {
    ctx.drawImage(atlasImageEl, sx, sy, sourceWidth, sourceHeight, dx, dy, drawWidth, drawHeight);
  } else {
    ctx.fillStyle = "rgba(37, 58, 49, 0.96)";
    ctx.fillRect(dx, dy, drawWidth, drawHeight);
  }

  ctx.strokeStyle = "rgba(243, 207, 121, 0.92)";
  ctx.lineWidth = 2;
  ctx.strokeRect(dx, dy, drawWidth, drawHeight);
}

function updatePredictionStats() {
  if (!state.lastPredictionStats) {
    predictionStatsEl.textContent = "High confidence autofills. Medium confidence is queued for review. Low confidence asks back to you.";
    return;
  }
  const stats = state.lastPredictionStats;
  predictionStatsEl.textContent =
    `Knowledge examples: ${stats.knowledge_examples}\nTiles considered: ${stats.tiles_considered}\nHigh: ${stats.counts.high} | Medium: ${stats.counts.medium} | Low: ${stats.counts.low} | Confirmed: ${stats.counts.known}`;
}

function renderGrid() {
  ensureTiles();
  const { imageWidth, imageHeight, stageWidth, stageHeight } = stageMetrics();
  stageEl.style.width = `${stageWidth}px`;
  stageEl.style.height = `${stageHeight}px`;
  atlasImageEl.style.width = `${imageWidth}px`;
  atlasImageEl.style.height = `${imageHeight}px`;
  atlasImageEl.style.display = state.imageUrl ? "block" : "none";
  gridEl.style.width = `${stageWidth}px`;
  gridEl.style.height = `${stageHeight}px`;

  const offsetX = Number(state.atlas.grid.offset_x);
  const offsetY = Number(state.atlas.grid.offset_y);
  const tileWidth = Number(state.atlas.grid.tile_width);
  const tileHeight = Number(state.atlas.grid.tile_height);

  gridEl.replaceChildren();
  for (const tile of state.atlas.tiles) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "tm-cell";
    const selected = tileKey(tile.row, tile.col) === state.selectedKey;
    const showPrimaryLabel = selected || tile.review_state === "medium" || tile.review_state === "low";
    if (selected) button.classList.add("selected");
    if (tile.confirmed_by_user) button.classList.add("confirmed");
    else if (hasLabels(tile.labels)) button.classList.add("predicted");
    if (tile.review_state === "medium") button.classList.add("review-medium");
    if (tile.review_state === "low" && !tile.confirmed_by_user) button.classList.add("review-low");
    if (tile.labels.blocks_movement) button.classList.add("is-blocked");
    else if (tile.labels.difficult) button.classList.add("is-difficult");
    if ((tile.labels.surface || "").includes("water")) button.classList.add("is-water");
    if (Number(tile.labels.height || 0) > 0) button.classList.add("is-elevated");
    if (
      tile.labels.hazard
      || firstNonEmptyKey(tile.labels.hazards || {})
      || firstNonEmptyKey(tile.labels.traps || {})
      || (Array.isArray(tile.labels.barriers) && tile.labels.barriers.length)
      || (Array.isArray(tile.labels.frozen_domain) && tile.labels.frozen_domain.length)
    ) {
      button.classList.add("has-hazard");
    }
    button.style.left = `${offsetX + tile.col * tileWidth}px`;
    button.style.top = `${offsetY + tile.row * tileHeight}px`;
    button.style.width = `${tileWidth}px`;
    button.style.height = `${tileHeight}px`;
    button.dataset.row = String(tile.row);
    button.dataset.col = String(tile.col);
    button.addEventListener("mousedown", (event) => {
      if (event.button !== 0) return;
      if (!state.segmentToolActive && (state.editorMode === "teach" || state.editorMode === "clear")) {
        state.isPainting = true;
        state.paintLastKey = "";
        void handleTilePaint(tile.row, tile.col);
        event.preventDefault();
        return;
      }
      if (!state.segmentToolActive) return;
      state.isDraggingSegment = true;
      state.suppressTileClick = true;
      state.segmentDraft = {
        anchorRow: tile.row,
        anchorCol: tile.col,
        currentRow: tile.row,
        currentCol: tile.col,
      };
      segmentRowEl.value = String(tile.row);
      segmentColEl.value = String(tile.col);
      segmentWidthEl.value = "1";
      segmentHeightEl.value = "1";
      renderSegmentOverlay();
      renderSegmentPreview();
      event.preventDefault();
    });
    button.addEventListener("mouseenter", () => {
      if (!state.segmentToolActive && state.isPainting && (state.editorMode === "teach" || state.editorMode === "clear")) {
        void handleTilePaint(tile.row, tile.col);
        return;
      }
      if (!state.segmentToolActive || !state.isDraggingSegment || !state.segmentDraft) return;
      state.segmentDraft.currentRow = tile.row;
      state.segmentDraft.currentCol = tile.col;
      const draft = normalizeSegmentRect(state.segmentDraft);
      segmentRowEl.value = String(draft.row);
      segmentColEl.value = String(draft.col);
      segmentWidthEl.value = String(draft.width);
      segmentHeightEl.value = String(draft.height);
      renderSegmentOverlay();
      renderSegmentPreview();
    });
    button.addEventListener("click", async () => {
      await handleTileClick(tile.row, tile.col);
    });

    if (hasLabels(tile.labels) && (showPrimaryLabel || state.showLabels)) {
      const label = document.createElement("span");
      label.className = "tm-cell-label";
      label.textContent = compactLabel(tile.labels).slice(0, 18);
      button.appendChild(label);
    }
    if (!tile.confirmed_by_user && tile.confidence > 0 && (showPrimaryLabel || state.showLabels)) {
      const confidence = document.createElement("span");
      confidence.className = "tm-cell-confidence";
      confidence.textContent = `${Math.round(tile.confidence * 100)}%`;
      button.appendChild(confidence);
    }
    const markers = tileMarkerBadges(tile.labels);
    if (markers.length) {
      const markerRow = document.createElement("span");
      markerRow.className = "tm-cell-markers";
      for (const marker of markers) {
        const badge = document.createElement("span");
        badge.className = `tm-cell-marker ${marker.kind}`;
        badge.textContent = marker.text;
        markerRow.appendChild(badge);
      }
      button.appendChild(markerRow);
    }
    if (showPrimaryLabel || state.showLabels) {
      const badgeLabel = tile.labels.hazard || firstNonEmptyKey(tile.labels.hazards || {}) || firstNonEmptyKey(tile.labels.traps || {});
      if (badgeLabel) {
        const hazard = document.createElement("span");
        hazard.className = "tm-cell-hazard";
        hazard.textContent = badgeLabel.replace(/_/g, " ").slice(0, 12);
        button.appendChild(hazard);
      }
    }
    gridEl.appendChild(button);
  }
  updateSummary();
  renderPredictionBadges();
  renderReviewList();
  renderTileInfo();
  renderSegmentOverlay();
  renderSegmentPreview();
  scheduleWorkspaceAutosave();
}

function fnvHash(data) {
  let hash = 2166136261;
  for (let idx = 0; idx < data.length; idx += 1) {
    hash ^= data[idx];
    hash = Math.imul(hash, 16777619);
  }
  return `fnv-${(hash >>> 0).toString(16)}`;
}

function buildNeighborSummary(row, col) {
  const offsets = [
    [-1, 0],
    [1, 0],
    [0, -1],
    [0, 1],
    [-1, -1],
    [-1, 1],
    [1, -1],
    [1, 1],
  ];
  const surface_counts = {};
  const hazard_counts = {};
  let blocking_neighbors = 0;
  for (const [dr, dc] of offsets) {
    const tile = getTile(row + dr, col + dc);
    if (!tile) continue;
    if (tile.labels.surface) surface_counts[tile.labels.surface] = Number(surface_counts[tile.labels.surface] || 0) + 1;
    if (tile.labels.hazard) hazard_counts[tile.labels.hazard] = Number(hazard_counts[tile.labels.hazard] || 0) + 1;
    if (tile.labels.blocks_movement) blocking_neighbors += 1;
  }
  return { surface_counts, hazard_counts, blocking_neighbors };
}

function sampleTile(row, col, { includeCrop = false } = {}) {
  const tile = getTile(row, col);
  if (!tile) return null;
  const width = Number(state.atlas.grid.tile_width || 0);
  const height = Number(state.atlas.grid.tile_height || 0);
  const imageScale = Math.max(0.25, Number(state.atlas.image_scale || 1));
  const sx = (Number(state.atlas.grid.offset_x || 0) + col * width) / imageScale;
  const sy = (Number(state.atlas.grid.offset_y || 0) + row * height) / imageScale;
  const sw = width / imageScale;
  const sh = height / imageScale;
  if (!state.imageUrl || !state.imageMeta.width || !state.imageMeta.height || width <= 0 || height <= 0) {
    return {
      ...cloneTile(tile),
      neighbor_summary: buildNeighborSummary(row, col),
    };
  }
  const ctx = analysisCanvas.getContext("2d", { willReadFrequently: true });
  analysisCanvas.width = 16;
  analysisCanvas.height = 16;
  ctx.clearRect(0, 0, 16, 16);
  ctx.drawImage(atlasImageEl, sx, sy, sw, sh, 0, 0, 16, 16);
  const imageData = ctx.getImageData(0, 0, 16, 16);
  const data = imageData.data;
  let avgR = 0;
  let avgG = 0;
  let avgB = 0;
  let avgLuma = 0;
  let avgSat = 0;
  let dark = 0;
  let light = 0;
  let redDominant = 0;
  let greenDominant = 0;
  let blueDominant = 0;
  for (let idx = 0; idx < data.length; idx += 4) {
    const r = data[idx] / 255;
    const g = data[idx + 1] / 255;
    const b = data[idx + 2] / 255;
    avgR += r;
    avgG += g;
    avgB += b;
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const luma = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    avgLuma += luma;
    avgSat += max <= 0 ? 0 : (max - min) / max;
    if (luma < 0.28) dark += 1;
    if (luma > 0.72) light += 1;
    if (r >= g && r >= b) redDominant += 1;
    if (g >= r && g >= b) greenDominant += 1;
    if (b >= r && b >= g) blueDominant += 1;
  }
  const pixelCount = data.length / 4 || 1;
  avgR /= pixelCount;
  avgG /= pixelCount;
  avgB /= pixelCount;
  avgLuma /= pixelCount;
  avgSat /= pixelCount;

  let variance = 0;
  let contrast = 0;
  let edges = 0;
  const lumas = [];
  for (let idx = 0; idx < data.length; idx += 4) {
    const r = data[idx] / 255;
    const g = data[idx + 1] / 255;
    const b = data[idx + 2] / 255;
    const luma = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    lumas.push(luma);
    variance += (luma - avgLuma) ** 2;
    contrast = Math.max(contrast, luma);
  }
  let minLuma = 1;
  for (const value of lumas) {
    minLuma = Math.min(minLuma, value);
  }
  contrast -= minLuma;
  for (let y = 0; y < 16; y += 1) {
    for (let x = 0; x < 16; x += 1) {
      const index = y * 16 + x;
      const current = lumas[index];
      const right = x < 15 ? lumas[index + 1] : current;
      const down = y < 15 ? lumas[index + 16] : current;
      edges += Math.abs(current - right) + Math.abs(current - down);
    }
  }
  variance /= pixelCount;
  edges /= pixelCount * 2;

  const feature_vector = [
    avgR,
    avgG,
    avgB,
    avgLuma,
    avgSat,
    variance,
    edges,
    dark / pixelCount,
    light / pixelCount,
    redDominant / pixelCount,
    greenDominant / pixelCount,
    blueDominant / pixelCount,
    contrast,
  ].map((value) => Number(value.toFixed(6)));

  let cropDataUrl = tile.tile_crop_data_url || "";
  if (includeCrop) {
    analysisCanvas.width = 32;
    analysisCanvas.height = 32;
    ctx.clearRect(0, 0, 32, 32);
    ctx.drawImage(atlasImageEl, sx, sy, sw, sh, 0, 0, 32, 32);
    cropDataUrl = analysisCanvas.toDataURL("image/png");
  }

  return {
    ...cloneTile(tile),
    feature_vector,
    tile_image_hash: fnvHash(data),
    tile_crop_data_url: cropDataUrl,
    neighbor_summary: buildNeighborSummary(row, col),
  };
}

function collectTilesForPrediction() {
  ensureTiles();
  return state.atlas.tiles.map((tile) => {
    const sampled = sampleTile(tile.row, tile.col, { includeCrop: false });
    return sampled || cloneTile(tile);
  });
}

function upsertTile(tile) {
  const key = tileKey(tile.row, tile.col);
  state.atlas.tiles = state.atlas.tiles.map((entry) => (tileKey(entry.row, entry.col) === key ? tile : entry));
}

function focusQueuedQuestion() {
  setEditorMode("inspect");
  if (!state.lowConfidenceQueue.length) return;
  const nextKey = state.lowConfidenceQueue[0];
  state.selectedKey = nextKey;
  const tile = getSelectedTile();
  if (tile) setEditorLabels(tile.labels);
  setTimeout(() => {
    askPanelEl.scrollIntoView({ behavior: "smooth", block: "center" });
    const selectedCell = document.querySelector(`#tm-grid .tm-cell.selected`);
    selectedCell?.scrollIntoView({ behavior: "smooth", block: "center", inline: "center" });
  }, 0);
}

function advanceQuestionQueue() {
  if (!state.lowConfidenceQueue.length) return;
  state.lowConfidenceQueue.shift();
  focusQueuedQuestion();
}

async function handleTilePaint(row, col) {
  const key = tileKey(row, col);
  if (state.paintLastKey === key) return;
  state.paintLastKey = key;
  state.selectedKey = key;
  if (state.editorMode === "teach") {
    await applyLabelsToSelectedTile();
    return;
  }
  if (state.editorMode === "clear") {
    clearSelectedTile();
    return;
  }
  renderGrid();
}

function mergePrediction(prediction) {
  const tile = getTile(prediction.row, prediction.col);
  if (!tile || tile.confirmed_by_user) return;
  tile.labels = { ...prediction.labels };
  tile.confidence = Number(prediction.confidence || 0);
  tile.review_state = String(prediction.review_state || "low");
  tile.status = String(prediction.status || "needs_review");
  tile.source = String(prediction.source || "profile-memory");
  tile.matches = Array.isArray(prediction.matches) ? prediction.matches : [];
}

async function handleTileClick(row, col) {
  if (state.suppressTileClick) {
    state.suppressTileClick = false;
    return;
  }
  state.selectedKey = tileKey(row, col);
  if (state.editorMode === "teach") {
    await applyLabelsToSelectedTile();
    return;
  }
  if (state.editorMode === "clear") {
    clearSelectedTile();
    return;
  }
  renderGrid();
}

async function applyLabelsToSelectedTile() {
  const selected = getSelectedTile();
  if (!selected) return;
  const wasLowQuestion = state.lowConfidenceQueue.includes(tileKey(selected.row, selected.col));
  const sampled = sampleTile(selected.row, selected.col, { includeCrop: true }) || cloneTile(selected);
  const next = {
    ...sampled,
    labels: readEditorLabels(),
    confirmed_by_user: true,
    source: "user",
    status: "confirmed",
    review_state: "confirmed",
    confidence_before_correction: Number(selected.confidence || 0),
    confidence: 1,
    matches: [],
  };
  upsertTile(next);
  state.lowConfidenceQueue = state.lowConfidenceQueue.filter((key) => key !== tileKey(selected.row, selected.col));
  state.mediumConfidenceQueue = state.mediumConfidenceQueue.filter((key) => key !== tileKey(selected.row, selected.col));
  if (wasLowQuestion) focusQueuedQuestion();
  renderGrid();
}

async function confirmSelectedTile() {
  const selected = getSelectedTile();
  if (!selected || !hasLabels(selected.labels)) return;
  const wasLowQuestion = state.lowConfidenceQueue.includes(tileKey(selected.row, selected.col));
  const sampled = sampleTile(selected.row, selected.col, { includeCrop: true }) || cloneTile(selected);
  const next = {
    ...sampled,
    labels: { ...selected.labels },
    confirmed_by_user: true,
    source: selected.source === "user" ? "user" : "reviewed",
    status: "confirmed",
    review_state: "confirmed",
    confidence_before_correction: Number(selected.confidence || 0),
    confidence: 1,
  };
  upsertTile(next);
  state.lowConfidenceQueue = state.lowConfidenceQueue.filter((key) => key !== tileKey(selected.row, selected.col));
  state.mediumConfidenceQueue = state.mediumConfidenceQueue.filter((key) => key !== tileKey(selected.row, selected.col));
  if (wasLowQuestion) focusQueuedQuestion();
  renderGrid();
}

function clearSelectedTile() {
  const selected = getSelectedTile();
  if (!selected) return;
  const wasLowQuestion = state.lowConfidenceQueue.includes(tileKey(selected.row, selected.col));
  upsertTile(makeEmptyTile(selected.row, selected.col));
  state.lowConfidenceQueue = state.lowConfidenceQueue.filter((key) => key !== tileKey(selected.row, selected.col));
  state.mediumConfidenceQueue = state.mediumConfidenceQueue.filter((key) => key !== tileKey(selected.row, selected.col));
  if (wasLowQuestion) focusQueuedQuestion();
  renderGrid();
}

function markSelectedReviewed() {
  const selected = getSelectedTile();
  if (!selected || !hasLabels(selected.labels)) return;
  selected.review_state = selected.confirmed_by_user ? "confirmed" : "medium";
  state.mediumConfidenceQueue = state.mediumConfidenceQueue.filter((key) => key !== tileKey(selected.row, selected.col));
  renderGrid();
}

async function runPrediction() {
  if (!profileSelectEl.value && !String(profileNameEl.value || "").trim()) {
    throw new Error("Choose an existing profile or create a new one before prediction.");
  }
  if (!profileSelectEl.value && String(profileNameEl.value || "").trim()) {
    await saveProfile();
  }
  const tiles = collectTilesForPrediction();
  const examples = tiles.filter((tile) => tile.confirmed_by_user && hasLabels(tile.labels));
  const payload = {
    profile_id: profileSelectEl.value || "",
    tiles,
    examples,
    high_confidence: Number(highConfidenceEl.value || 0.82),
    medium_confidence: Number(mediumConfidenceEl.value || 0.58),
  };
  const data = await api("/api/terrain/predict", payload);
  for (const prediction of data.predictions || []) {
    mergePrediction(prediction);
  }
  state.lowConfidenceQueue = (data.predictions || [])
    .filter((prediction) => prediction.review_state === "low")
    .map((prediction) => tileKey(prediction.row, prediction.col));
  state.mediumConfidenceQueue = (data.predictions || [])
    .filter((prediction) => prediction.review_state === "medium")
    .map((prediction) => tileKey(prediction.row, prediction.col));
  focusQueuedQuestion();
  state.lastPredictionStats = data.stats || null;
  updatePredictionStats();
  renderGrid();
  if (!state.lowConfidenceQueue.length && state.mediumConfidenceQueue.length) {
    const nextKey = state.mediumConfidenceQueue[0];
    state.selectedKey = nextKey;
    const tile = getSelectedTile();
    if (tile) setEditorLabels(tile.labels);
    setTimeout(() => predictionReviewBannerEl.scrollIntoView({ behavior: "smooth", block: "center" }), 0);
  }
}

function slugify(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || `segment-${Math.random().toString(16).slice(2, 8)}`;
}

function activeSegment() {
  return state.segments.find((segment) => segment.id === state.activeSegmentId) || null;
}

function finishSegmentDrag() {
  state.isPainting = false;
  state.paintLastKey = "";
  if (!state.isDraggingSegment) return;
  state.isDraggingSegment = false;
  const draft = normalizeSegmentRect(state.segmentDraft);
  if (!draft) {
    state.segmentDraft = null;
    renderSegmentOverlay();
    renderSegmentPreview();
    return;
  }
  segmentRowEl.value = String(draft.row);
  segmentColEl.value = String(draft.col);
  segmentWidthEl.value = String(draft.width);
  segmentHeightEl.value = String(draft.height);
  state.activeSegmentId = "";
  if (!String(segmentNameEl.value || "").trim()) {
    segmentNameEl.value = `Segment ${draft.row + 1}-${draft.col + 1}`;
  }
  renderSegmentOverlay();
  renderSegments();
  renderSegmentPreview();
}

function buildSegmentImagePayload(segment = null) {
  if (!state.imageUrl || !atlasImageEl.naturalWidth || !atlasImageEl.naturalHeight) return null;
  const startRow = segment ? segment.row : 0;
  const startCol = segment ? segment.col : 0;
  const widthTiles = segment ? segment.width : state.atlas.grid.width;
  const heightTiles = segment ? segment.height : state.atlas.grid.height;
  const widthPx = Math.max(1, Number(state.atlas.grid.tile_width) * widthTiles);
  const heightPx = Math.max(1, Number(state.atlas.grid.tile_height) * heightTiles);
  const imageScale = Math.max(0.25, Number(state.atlas.image_scale || 1));
  const sx = (Number(state.atlas.grid.offset_x) + startCol * Number(state.atlas.grid.tile_width)) / imageScale;
  const sy = (Number(state.atlas.grid.offset_y) + startRow * Number(state.atlas.grid.tile_height)) / imageScale;
  const sw = widthPx / imageScale;
  const sh = heightPx / imageScale;
  analysisCanvas.width = Math.max(1, Math.round(widthPx));
  analysisCanvas.height = Math.max(1, Math.round(heightPx));
  const ctx = analysisCanvas.getContext("2d");
  ctx.clearRect(0, 0, analysisCanvas.width, analysisCanvas.height);
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(atlasImageEl, sx, sy, sw, sh, 0, 0, analysisCanvas.width, analysisCanvas.height);
  return {
    data_url: analysisCanvas.toDataURL("image/png"),
    width_px: analysisCanvas.width,
    height_px: analysisCanvas.height,
    image_name: state.imageName || "",
    image_scale: imageScale,
  };
}

function buildGridPayloadForSegment(segment = null) {
  const startRow = segment ? segment.row : 0;
  const startCol = segment ? segment.col : 0;
  const width = segment ? segment.width : state.atlas.grid.width;
  const height = segment ? segment.height : state.atlas.grid.height;
  const blockers = [];
  const tiles = [];
  for (const tile of state.atlas.tiles) {
    if (tile.row < startRow || tile.col < startCol) continue;
    if (tile.row >= startRow + height || tile.col >= startCol + width) continue;
    if (!hasLabels(tile.labels)) continue;
    const localRow = tile.row - startRow;
    const localCol = tile.col - startCol;
    const type = [tile.labels.surface, tile.labels.object].filter(Boolean).join(" ").trim();
    const hazards = Object.keys(tile.labels.hazards || {}).length
      ? tile.labels.hazards
      : tile.labels.hazard
        ? { [tile.labels.hazard]: 1 }
        : null;
    const traps = Object.keys(tile.labels.traps || {}).length ? tile.labels.traps : null;
    const barriers = Array.isArray(tile.labels.barriers) && tile.labels.barriers.length ? tile.labels.barriers : null;
    const frozenDomain = Array.isArray(tile.labels.frozen_domain) && tile.labels.frozen_domain.length ? tile.labels.frozen_domain : null;
    const trapSources = tile.labels.trap_sources && Object.keys(tile.labels.trap_sources).length ? tile.labels.trap_sources : null;
    const heightValue = Number(tile.labels.height || 0) || null;
    const difficult = tile.labels.difficult || null;
    const obstacle = tile.labels.blocks_movement || null;
    if (obstacle) blockers.push([localCol, localRow]);
    tiles.push([localCol, localRow, type, hazards, traps, barriers, frozenDomain, trapSources, heightValue, difficult, obstacle]);
  }
  return {
    width,
    height,
    blockers,
    tiles,
    map: {
      source: "terrain-mapper",
      annotation_workflow: true,
      profile_id: profileSelectEl.value || "",
      segment: segment ? { ...segment } : null,
      grid_alignment: { ...state.atlas.grid },
      image: buildSegmentImagePayload(segment),
    },
  };
}

function buildMapPayload() {
  return {
    id: state.mapId || undefined,
    name: String(mapNameEl.value || "").trim(),
    profile_id: profileSelectEl.value || "",
    image_name: state.imageName || undefined,
    image_data_url: state.imageDataUrl || undefined,
    image_meta: { ...state.imageMeta },
    tags: parseTags(mapTagsEl.value),
    atlas: {
      grid: { ...state.atlas.grid },
      image_scale: Math.max(0.25, Number(state.atlas.image_scale || 1)),
      review_rules: {
        high_confidence: Number(highConfidenceEl.value || 0.82),
        medium_confidence: Number(mediumConfidenceEl.value || 0.58),
      },
      tiles: state.atlas.tiles.map((tile) => cloneTile(tile)),
    },
    segments: state.segments.map((segment) => ({ ...segment })),
    grid: buildGridPayloadForSegment(null),
  };
}

function buildExportGridPayload() {
  const segment = activeSegmentOrDraft();
  const grid = buildGridPayloadForSegment(segment);
  grid.map = {
    ...(grid.map || {}),
    export_target: "autoptuweb",
    atlas_name: String(mapNameEl.value || "").trim(),
    segment_name: segment ? segment.name : "",
    tags: parseTags(mapTagsEl.value),
  };
  return grid;
}

async function applyToBattle() {
  const grid = buildGridPayloadForSegment(activeSegmentOrDraft());
  await api("/api/terrain/apply", { grid });
}

async function exportJson() {
  const segment = activeSegmentOrDraft();
  const payload = buildExportGridPayload();
  const suffix = segment ? `${slugify(segment.name)}-battle-grid` : "battle-grid";
  const atlasName = inferDefaultAtlasName();
  if (!String(mapNameEl.value || "").trim()) {
    mapNameEl.value = atlasName;
  }
  const filename = `${slugify(atlasName)}-${suffix}.json`;
  try {
    const saved = await api("/api/terrain/export", {
      filename,
      payload,
    });
    const message = `Exported AutoPTUWeb JSON\n${saved.path}`;
    predictionStatsEl.textContent = `Exported AutoPTUWeb JSON to ${saved.path}`;
    setActionStatus(message, "ok");
    return;
  } catch (err) {
    setActionStatus(`Export failed\n${err.message || err}`, "error");
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    downloadLink.href = URL.createObjectURL(blob);
    downloadLink.download = filename;
    downloadLink.click();
    setTimeout(() => URL.revokeObjectURL(downloadLink.href), 1000);
  }
}

async function exportJsonAs() {
  const segment = activeSegmentOrDraft();
  const payload = buildExportGridPayload();
  const suffix = segment ? `${slugify(segment.name)}-battle-grid` : "battle-grid";
  const atlasName = inferDefaultAtlasName();
  if (!String(mapNameEl.value || "").trim()) {
    mapNameEl.value = atlasName;
  }
  const filename = `${slugify(atlasName)}-${suffix}.json`;
  const saved = await api("/api/terrain/save_as", {
    title: "Export AutoPTUWeb Terrain JSON",
    filename,
    payload,
  });
  if (saved.status === "cancelled") {
    setActionStatus("Export cancelled", "error");
    return;
  }
  predictionStatsEl.textContent = `Exported AutoPTUWeb JSON to ${saved.path}`;
  setActionStatus(`Exported AutoPTUWeb JSON\n${saved.path}`, "ok");
}

async function saveMap() {
  const atlasName = inferDefaultAtlasName();
  if (!String(mapNameEl.value || "").trim()) {
    mapNameEl.value = atlasName;
  }
  if (!profileSelectEl.value && String(profileNameEl.value || "").trim()) {
    await saveProfile();
  }
  for (const tile of state.atlas.tiles) {
    if (!tile.confirmed_by_user) continue;
    const sampled = sampleTile(tile.row, tile.col, { includeCrop: true });
    if (sampled) {
      upsertTile({
        ...sampled,
        labels: { ...tile.labels },
        confirmed_by_user: true,
        source: tile.source,
        status: "confirmed",
        review_state: "confirmed",
        confidence: 1,
        confidence_before_correction: Number(tile.confidence_before_correction || tile.confidence || 0),
        matches: [],
      });
    }
  }
  const data = await api("/api/terrain/maps/save", buildMapPayload());
  state.mapId = String(data.map?.id || state.mapId || "");
  state.imageDataUrl = "";
  await loadLibrary();
  const savedPath = String(data.map?.path || "").trim();
  if (savedPath) {
    predictionStatsEl.textContent = `Saved atlas to ${savedPath}`;
    setActionStatus(`Saved atlas\n${savedPath}`, "ok");
  }
}

async function saveMapAs() {
  const atlasName = inferDefaultAtlasName();
  if (!String(mapNameEl.value || "").trim()) {
    mapNameEl.value = atlasName;
  }
  if (!profileSelectEl.value && String(profileNameEl.value || "").trim()) {
    await saveProfile();
  }
  const payload = buildMapPayload();
  const filename = `${slugify(atlasName)}.json`;
  const saved = await api("/api/terrain/save_as", {
    title: "Save Atlas Copy As",
    filename,
    payload,
  });
  if (saved.status === "cancelled") {
    setActionStatus("Save As cancelled", "error");
    return;
  }
  setActionStatus(`Saved atlas copy\n${saved.path}`, "ok");
}

function fitGridToImage() {
  if (!state.imageMeta.width || !state.imageMeta.height) return;
  const { imageWidth, imageHeight } = displayImageMetrics();
  state.atlas.grid.offset_x = 0;
  state.atlas.grid.offset_y = 0;
  state.atlas.grid.tile_width = Number((imageWidth / state.atlas.grid.width).toFixed(3));
  state.atlas.grid.tile_height = Number((imageHeight / state.atlas.grid.height).toFixed(3));
  syncInputsFromState();
  renderGrid();
}

function setImageSource(url, { sourceName = "", imageName = "" } = {}) {
  return new Promise((resolve) => {
    if (!url) {
      state.imageUrl = "";
      state.imageName = imageName || "";
      state.imageMeta = { width: 0, height: 0, source_name: sourceName || "" };
      atlasImageEl.removeAttribute("src");
      renderGrid();
      resolve();
      return;
    }
    atlasImageEl.onload = () => {
      state.imageUrl = url;
      state.imageName = imageName || state.imageName;
      state.imageMeta = {
        width: atlasImageEl.naturalWidth,
        height: atlasImageEl.naturalHeight,
        source_name: sourceName || state.imageMeta.source_name || state.imageName,
      };
      renderGrid();
      resolve();
    };
    atlasImageEl.onerror = () => {
      state.imageUrl = "";
      state.imageMeta = { width: 0, height: 0, source_name: sourceName || "" };
      renderGrid();
      resolve();
    };
    atlasImageEl.src = url;
  });
}

function normalizeTile(raw) {
  const base = makeEmptyTile(Number(raw.row || 0), Number(raw.col || 0));
  return {
    ...base,
    ...raw,
    labels: {
      surface: String(raw.labels?.surface || ""),
      structure: String(raw.labels?.structure || ""),
      prop: String(raw.labels?.prop || ""),
      object: String(raw.labels?.object || ""),
      height: Math.max(0, Number(raw.labels?.height || 0)),
      hazard: String(raw.labels?.hazard || ""),
      hazards: raw.labels?.hazards && typeof raw.labels.hazards === "object" ? raw.labels.hazards : {},
      traps: raw.labels?.traps && typeof raw.labels.traps === "object" ? raw.labels.traps : {},
      barriers: Array.isArray(raw.labels?.barriers) ? raw.labels.barriers : [],
      frozen_domain: Array.isArray(raw.labels?.frozen_domain) ? raw.labels.frozen_domain : [],
      trap_sources: raw.labels?.trap_sources && typeof raw.labels.trap_sources === "object" ? raw.labels.trap_sources : {},
      movement: String(raw.labels?.movement || (raw.labels?.blocks_movement ? "blocked" : raw.labels?.difficult ? "difficult" : "open")),
      visibility: String(raw.labels?.visibility || (raw.labels?.blocks_los ? "blocks_los" : "clear")),
      cover: String(raw.labels?.cover || "none"),
      standable: raw.labels?.standable !== false,
      blocks_movement: Boolean(raw.labels?.blocks_movement) || String(raw.labels?.movement || "") === "blocked",
      difficult: Boolean(raw.labels?.difficult) || String(raw.labels?.movement || "") === "difficult",
      blocks_los: Boolean(raw.labels?.blocks_los) || String(raw.labels?.visibility || "") === "blocks_los",
    },
    feature_vector: Array.isArray(raw.feature_vector) ? raw.feature_vector.map((value) => Number(value || 0)) : [],
    confidence: Number(raw.confidence || 0),
    confidence_before_correction: Number(raw.confidence_before_correction || 0),
    confirmed_by_user: Boolean(raw.confirmed_by_user),
    review_state: String(raw.review_state || (raw.confirmed_by_user ? "confirmed" : "low")),
    status: String(raw.status || "unlabeled"),
    neighbor_summary: raw.neighbor_summary || base.neighbor_summary,
    matches: Array.isArray(raw.matches) ? raw.matches : [],
  };
}

function parseLegacyType(typeName) {
  const lowered = String(typeName || "").trim().toLowerCase();
  const tokens = lowered.split(/\s+/).filter(Boolean);
  const surface = SURFACE_OPTIONS.map((entry) => entry[0]).find((value) => value && tokens.includes(value)) || "";
  const structure = STRUCTURE_OPTIONS.map((entry) => entry[0]).find((value) => value && tokens.includes(value)) || "";
  const prop = PROP_OPTIONS.map((entry) => entry[0]).find((value) => value && tokens.includes(value)) || "";
  return { surface, structure, prop, object: structure || prop };
}

function atlasFromLegacyGrid(grid) {
  const width = Math.max(1, Number(grid.width || 15));
  const height = Math.max(1, Number(grid.height || 10));
  const tiles = [];
  const tileMap = new Map();
  for (const entry of Array.isArray(grid.tiles) ? grid.tiles : []) {
    if (!Array.isArray(entry) || entry.length < 3) continue;
    const [col, row, type, hazards, , , , , heightValue, difficult, obstacle] = entry;
    const traps = entry[4];
    const barriers = entry[5];
    const frozenDomain = entry[6];
    const trapSources = entry[7];
    const parsed = parseLegacyType(type);
    const hazard = hazards && typeof hazards === "object" ? Object.keys(hazards)[0] || "" : "";
    tileMap.set(tileKey(Number(row), Number(col)), normalizeTile({
      row: Number(row),
      col: Number(col),
      labels: {
        surface: parsed.surface,
        structure: parsed.structure,
        prop: parsed.prop,
        object: parsed.object,
        height: Math.max(0, Number(heightValue || 0)),
        hazard,
        hazards: hazards && typeof hazards === "object" ? hazards : {},
        traps: traps && typeof traps === "object" ? traps : {},
        barriers: Array.isArray(barriers) ? barriers : [],
        frozen_domain: Array.isArray(frozenDomain) ? frozenDomain : [],
        trap_sources: trapSources && typeof trapSources === "object" ? trapSources : {},
        movement: Boolean(obstacle) ? "blocked" : Boolean(difficult) ? "difficult" : "open",
        visibility: Boolean(obstacle) ? "blocks_los" : "clear",
        cover: Boolean(obstacle) ? "high" : "none",
        standable: !Boolean(obstacle),
        blocks_movement: Boolean(obstacle),
        difficult: Boolean(difficult),
        blocks_los: Boolean(obstacle),
      },
      confirmed_by_user: true,
      confidence: 1,
      review_state: "confirmed",
      status: "confirmed",
      source: "legacy",
    }));
  }
  for (let row = 0; row < height; row += 1) {
    for (let col = 0; col < width; col += 1) {
      tiles.push(tileMap.get(tileKey(row, col)) || makeEmptyTile(row, col));
    }
  }
  return {
    grid: {
      width,
      height,
      offset_x: 0,
      offset_y: 0,
      tile_width: 52,
      tile_height: 52,
    },
    image_scale: 1,
    review_rules: { high_confidence: 0.82, medium_confidence: 0.58 },
    tiles,
  };
}

function normalizeLoadedRecord(record) {
  return {
    id: String(record.id || ""),
    name: String(record.name || ""),
    profile_id: String(record.profile_id || ""),
    tags: Array.isArray(record.tags) ? record.tags : [],
    image: String(record.image || ""),
    image_meta: record.image_meta || { width: 0, height: 0, source_name: "" },
    atlas: record.atlas
      ? {
          grid: {
            width: Math.max(1, Number(record.atlas.grid?.width || 15)),
            height: Math.max(1, Number(record.atlas.grid?.height || 10)),
            offset_x: Number(record.atlas.grid?.offset_x || 0),
            offset_y: Number(record.atlas.grid?.offset_y || 0),
            tile_width: Number(record.atlas.grid?.tile_width || 52),
            tile_height: Number(record.atlas.grid?.tile_height || 52),
          },
          image_scale: Math.max(0.25, Number(record.atlas.image_scale || 1)),
          review_rules: {
            high_confidence: Number(record.atlas.review_rules?.high_confidence || 0.82),
            medium_confidence: Number(record.atlas.review_rules?.medium_confidence || 0.58),
          },
          tiles: Array.isArray(record.atlas.tiles) ? record.atlas.tiles.map((tile) => normalizeTile(tile)) : [],
        }
      : atlasFromLegacyGrid(record.grid || {}),
    segments: Array.isArray(record.segments)
      ? record.segments.map((segment) => ({
          id: String(segment.id || slugify(segment.name || "segment")),
          name: String(segment.name || "Battlefield"),
          row: Math.max(0, Number(segment.row || 0)),
          col: Math.max(0, Number(segment.col || 0)),
          width: Math.max(1, Number(segment.width || 1)),
          height: Math.max(1, Number(segment.height || 1)),
        }))
      : [],
  };
}

async function selectProfile(profileId) {
  if (!profileId) {
    state.currentProfile = null;
    renderProfiles();
    return;
  }
  const data = await api(`/api/terrain/profiles/${encodeURIComponent(profileId)}`, null, "GET");
  const profile = data.profile || {};
  const summary = state.profiles.find((entry) => entry.id === profileId) || {};
  state.currentProfile = {
    ...summary,
    ...profile,
    example_count: Array.isArray(profile.knowledge_examples) ? profile.knowledge_examples.length : Number(summary.example_count || 0),
  };
  renderProfiles();
}

async function applyLoadedRecord(record, imageUrl = "") {
  state.suspendAutosave = true;
  const normalized = normalizeLoadedRecord(record);
  state.mapId = normalized.id;
  mapNameEl.value = normalized.name;
  mapTagsEl.value = normalized.tags.join(", ");
  state.atlas = normalized.atlas;
  state.segments = normalized.segments;
  state.activeSegmentId = normalized.segments[0]?.id || "";
  state.lastPredictionStats = null;
  state.lowConfidenceQueue = [];
  state.mediumConfidenceQueue = [];
  syncInputsFromState();
  if (normalized.profile_id) {
    profileSelectEl.value = normalized.profile_id;
    await selectProfile(normalized.profile_id);
  } else {
    state.currentProfile = null;
    profileSelectEl.value = "";
    renderProfiles();
  }
  const resolvedImageUrl = imageUrl || (record.image_data_url || "");
  state.imageName = record.image || state.imageName;
  await setImageSource(resolvedImageUrl, {
    sourceName: normalized.image_meta?.source_name || normalized.name,
    imageName: record.image || state.imageName,
  });
  ensureTiles();
  renderSegments();
  updatePredictionStats();
  state.suspendAutosave = false;
  renderGrid();
  scheduleWorkspaceAutosave();
}

async function loadSavedMap(mapId) {
  const data = await api(`/api/terrain/maps/${encodeURIComponent(mapId)}`, null, "GET");
  await applyLoadedRecord(data.map || {}, data.image_url || "");
}

async function loadLibrary() {
  const data = await api("/api/terrain/maps", null, "GET");
  state.library = Array.isArray(data.maps) ? data.maps : [];
  renderLibrary();
}

async function loadWorkspaceDraft() {
  const data = await api("/api/terrain/workspace", null, "GET");
  if (data.status !== "ok" || !data.map) return false;
  await applyLoadedRecord(data.map || {}, data.image_url || "");
  setActionStatus(`Restored local workspace draft\n${data.path}`, "ok");
  return true;
}

async function loadProfiles() {
  const data = await api("/api/terrain/profiles", null, "GET");
  state.profiles = Array.isArray(data.profiles) ? data.profiles : [];
  renderProfiles();
}

async function saveProfile() {
  const name = String(profileNameEl.value || "").trim();
  if (!name) throw new Error("Profile name is required");
  const payload = {
    id: profileSelectEl.value || undefined,
    name,
    category: String(profileCategoryEl.value || "").trim(),
    tags: parseTags(profileTagsEl.value),
  };
  const data = await api("/api/terrain/profiles/save", payload);
  await loadProfiles();
  profileSelectEl.value = String(data.profile?.id || "");
  await selectProfile(profileSelectEl.value);
  scheduleWorkspaceAutosave();
}

async function loadBattleGrid() {
  const data = await api("/api/terrain/load_battle", null, "GET");
  state.mapId = "";
  mapNameEl.value = "Battle Grid";
  mapTagsEl.value = "battle";
  state.atlas = atlasFromLegacyGrid(data.grid || {});
  state.segments = [];
  state.activeSegmentId = "";
  state.imageName = "";
  state.imageDataUrl = "";
  await setImageSource("", { sourceName: "Battle Grid" });
  syncInputsFromState();
  renderSegments();
  updatePredictionStats();
  renderGrid();
}

function importJson(file) {
  const reader = new FileReader();
  reader.onload = async () => {
    const payload = JSON.parse(String(reader.result || "{}"));
    if (payload && typeof payload === "object" && payload.atlas) {
      await applyLoadedRecord(payload, payload.image_data_url || "");
      return;
    }
    if (payload && typeof payload === "object" && Number.isFinite(Number(payload.width)) && Number.isFinite(Number(payload.height))) {
      state.mapId = "";
      mapNameEl.value = String(payload.map?.atlas_name || payload.map?.name || "Imported Battle Grid");
      mapTagsEl.value = Array.isArray(payload.map?.tags) ? payload.map.tags.join(", ") : "";
      state.atlas = atlasFromLegacyGrid(payload);
      state.segments = [];
      state.activeSegmentId = "";
      state.imageName = "";
      state.imageDataUrl = "";
      await setImageSource("", { sourceName: "Imported Battle Grid" });
      syncInputsFromState();
      renderSegments();
      updatePredictionStats();
      renderGrid();
      return;
    }
    await applyLoadedRecord(payload, payload.image_data_url || "");
  };
  reader.readAsText(file);
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error(`Failed reading ${file?.name || "file"}`));
    reader.readAsDataURL(file);
  });
}

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error(`Failed reading ${file?.name || "file"}`));
    reader.readAsText(file);
  });
}

function measureImageDataUrl(dataUrl) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve({ width: image.naturalWidth, height: image.naturalHeight });
    image.onerror = () => reject(new Error("Failed to load imported image"));
    image.src = dataUrl;
  });
}

async function saveImportedAtlasRecord(payload) {
  const data = await api("/api/terrain/maps/save", payload);
  return data.map || null;
}

async function importJsonFiles(files) {
  const queue = Array.from(files || []).filter(Boolean);
  if (!queue.length) return;
  if (queue.length === 1) {
    importJson(queue[0]);
    return;
  }
  let firstSavedId = "";
  let firstPayload = null;
  let importCount = 0;
  for (const file of queue) {
    const text = await readFileAsText(file);
    const payload = JSON.parse(text);
    const normalized = normalizeLoadedRecord(payload);
    const savePayload = {
      id: normalized.id || undefined,
      name: normalized.name || String(file.name || "").replace(/\.[^.]+$/, "") || "Imported Atlas",
      profile_id: normalized.profile_id || "",
      tags: Array.isArray(normalized.tags) ? normalized.tags : [],
      image: String(payload.image || ""),
      image_data_url: String(payload.image_data_url || ""),
      image_meta: normalized.image_meta || payload.image_meta || { width: 0, height: 0, source_name: "" },
      atlas: normalized.atlas,
      segments: normalized.segments,
    };
    const saved = await saveImportedAtlasRecord(savePayload);
    if (!firstSavedId) {
      firstSavedId = String(saved?.id || "");
      firstPayload = payload;
    }
    importCount += 1;
  }
  await loadLibrary();
  if (firstSavedId) {
    await loadSavedMap(firstSavedId);
  } else if (firstPayload) {
    await applyLoadedRecord(firstPayload, String(firstPayload.image_data_url || ""));
  }
  setActionStatus(`Imported ${importCount} atlas JSON files. The first atlas is open now.`, "ok");
}

async function importAtlasImageFiles(files) {
  const queue = Array.from(files || []).filter(Boolean);
  if (!queue.length) return;
  if (queue.length === 1) {
    loadImageFile(queue[0]);
    return;
  }
  const gridWidth = Math.max(1, Number(gridWidthEl.value || 15));
  const gridHeight = Math.max(1, Number(gridHeightEl.value || 10));
  let firstSavedId = "";
  let importCount = 0;
  for (const file of queue) {
    const imageDataUrl = await readFileAsDataUrl(file);
    const meta = await measureImageDataUrl(imageDataUrl);
    const name = String(file.name || "").replace(/\.[^.]+$/, "") || `atlas-${importCount + 1}`;
    const tiles = [];
    for (let row = 0; row < gridHeight; row += 1) {
      for (let col = 0; col < gridWidth; col += 1) {
        tiles.push(makeEmptyTile(row, col));
      }
    }
    const payload = {
      name,
      profile_id: String(profileSelectEl.value || ""),
      tags: parseTags(mapTagsEl.value),
      image: String(file.name || ""),
      image_data_url: imageDataUrl,
      image_meta: { width: meta.width, height: meta.height, source_name: file.name || name },
      atlas: {
        grid: {
          width: gridWidth,
          height: gridHeight,
          offset_x: Number(offsetXEl.value || 0),
          offset_y: Number(offsetYEl.value || 0),
          tile_width: Math.max(1, Number(tileWidthEl.value || 52)),
          tile_height: Math.max(1, Number(tileHeightEl.value || 52)),
        },
        image_scale: imageScaleValue(),
        review_rules: {
          high_confidence: Number(highConfidenceEl.value || 0.82),
          medium_confidence: Number(mediumConfidenceEl.value || 0.58),
        },
        tiles,
      },
      segments: [],
    };
    const saved = await saveImportedAtlasRecord(payload);
    if (!firstSavedId) firstSavedId = String(saved?.id || "");
    importCount += 1;
  }
  await loadLibrary();
  if (firstSavedId) {
    await loadSavedMap(firstSavedId);
  }
  setActionStatus(`Imported ${importCount} atlas images. The first atlas is open now.`, "ok");
}

function loadImageFile(file) {
  const reader = new FileReader();
  reader.onload = async () => {
    state.imageDataUrl = String(reader.result || "");
    state.imageName = file.name;
    await setImageSource(state.imageDataUrl, { sourceName: file.name, imageName: file.name });
    if (!state.mapId && !mapNameEl.value.trim()) {
      mapNameEl.value = file.name.replace(/\.[^.]+$/, "");
    }
    scheduleWorkspaceAutosave();
  };
  reader.readAsDataURL(file);
}

function updateGridFromInputs(event) {
  const viewport = captureStageViewport();
  const shouldRefocusStage = event?.target === zoomEl;
  state.atlas.image_scale = imageScaleValue();
  state.atlas.grid.width = Math.max(1, Number(gridWidthEl.value || 15));
  state.atlas.grid.height = Math.max(1, Number(gridHeightEl.value || 10));
  state.atlas.grid.offset_x = Number(offsetXEl.value || 0);
  state.atlas.grid.offset_y = Number(offsetYEl.value || 0);
  state.atlas.grid.tile_width = Math.max(1, Number(tileWidthEl.value || 52));
  state.atlas.grid.tile_height = Math.max(1, Number(tileHeightEl.value || 52));
  state.atlas.review_rules.high_confidence = Number(highConfidenceEl.value || 0.82);
  state.atlas.review_rules.medium_confidence = Number(mediumConfidenceEl.value || 0.58);
  ensureTiles();
  renderGrid();
  requestAnimationFrame(() => {
    restoreStageViewport(viewport);
    if (shouldRefocusStage) {
      stageScrollerEl.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
}

function addSegment() {
  const segment = {
    id: slugify(segmentNameEl.value || `segment-${state.segments.length + 1}`),
    name: String(segmentNameEl.value || "").trim() || `Segment ${state.segments.length + 1}`,
    row: Math.max(0, Number(segmentRowEl.value || 0)),
    col: Math.max(0, Number(segmentColEl.value || 0)),
    width: Math.max(1, Number(segmentWidthEl.value || 1)),
    height: Math.max(1, Number(segmentHeightEl.value || 1)),
  };
  state.segments = state.segments.filter((entry) => entry.id !== segment.id).concat(segment);
  state.activeSegmentId = segment.id;
  state.segmentDraft = null;
  renderSegments();
  renderGrid();
}

function segmentFromSelected() {
  const tile = getSelectedTile();
  if (!tile) return;
  segmentRowEl.value = String(tile.row);
  segmentColEl.value = String(tile.col);
}

function resetAtlas(options = {}) {
  const clearDraft = Boolean(options.clearDraft);
  state.mapId = "";
  state.imageUrl = "";
  state.imageName = "";
  state.imageDataUrl = "";
  state.imageMeta = { width: 0, height: 0, source_name: "" };
  state.selectedKey = "";
  state.activeSegmentId = "";
  state.segmentToolActive = false;
  state.isDraggingSegment = false;
  state.suppressTileClick = false;
  state.segmentDraft = null;
  state.segments = [];
  state.currentProfile = null;
  state.activePresetId = TILE_PRESETS[0]?.id || "";
  profileSelectEl.value = "";
  mapNameEl.value = "";
  mapTagsEl.value = "";
  state.atlas = {
    grid: { width: 15, height: 10, offset_x: 0, offset_y: 0, tile_width: 52, tile_height: 52 },
    image_scale: 1,
    review_rules: { high_confidence: 0.82, medium_confidence: 0.58 },
    tiles: [],
  };
  state.lastPredictionStats = null;
  state.lowConfidenceQueue = [];
  state.mediumConfidenceQueue = [];
  atlasImageEl.removeAttribute("src");
  ensureTiles();
  syncInputsFromState();
  resetSegmentInputs();
  if (TILE_PRESETS[0]) applyPreset(TILE_PRESETS[0]);
  updatePredictionStats();
  renderGrid();
  renderSegments();
  renderProfiles();
  segmentDrawToggleEl.classList.remove("active");
  if (clearDraft) {
    clearWorkspaceDraft().catch(() => {});
    setActionStatus("Started a new blank atlas", "ok");
  }
}

document.getElementById("new-atlas").addEventListener("click", () => resetAtlas({ clearDraft: true }));
document.getElementById("load-battle").addEventListener("click", () => loadBattleGrid().catch((err) => alert(err.message)));
document.getElementById("run-prediction").addEventListener("click", () => runPrediction().catch((err) => alert(err.message)));
document.getElementById("save-map").addEventListener("click", () => saveMap().catch((err) => alert(err.message)));
document.getElementById("save-map-as").addEventListener("click", () => saveMapAs().catch((err) => alert(err.message)));
document.getElementById("apply-battle").addEventListener("click", () => applyToBattle().catch((err) => alert(err.message)));
document.getElementById("save-profile").addEventListener("click", () => saveProfile().catch((err) => alert(err.message)));
document.getElementById("apply-labels").addEventListener("click", () => applyLabelsToSelectedTile().catch((err) => alert(err.message)));
document.getElementById("confirm-tile").addEventListener("click", () => confirmSelectedTile().catch((err) => alert(err.message)));
document.getElementById("clear-tile").addEventListener("click", clearSelectedTile);
document.getElementById("mark-selected-reviewed").addEventListener("click", markSelectedReviewed);
document.getElementById("ask-accept").addEventListener("click", () => confirmSelectedTile().catch((err) => alert(err.message)));
document.getElementById("ask-skip").addEventListener("click", () => {
  advanceQuestionQueue();
  renderGrid();
});
document.getElementById("fit-grid").addEventListener("click", fitGridToImage);
document.getElementById("reset-view").addEventListener("click", () => {
  zoomEl.value = "1";
  state.atlas.image_scale = 1;
  renderGrid();
});
document.getElementById("segment-from-selected").addEventListener("click", segmentFromSelected);
document.getElementById("add-segment").addEventListener("click", addSegment);
document.getElementById("export-json").addEventListener("click", () => exportJson().catch((err) => alert(err.message)));
document.getElementById("export-json-as").addEventListener("click", () => exportJsonAs().catch((err) => alert(err.message)));
segmentDrawToggleEl.addEventListener("click", () => {
  state.segmentToolActive = !state.segmentToolActive;
  syncSegmentDrawToggle();
  if (!state.segmentToolActive) {
    state.isDraggingSegment = false;
    state.segmentDraft = null;
    renderGrid();
  }
});
document.addEventListener("mouseup", finishSegmentDrag);

document.getElementById("image-file").addEventListener("change", (event) => {
  const files = Array.from(event.target.files || []).filter(Boolean);
  if (!files.length) return;
  importAtlasImageFiles(files).catch((err) => alert(err.message));
  event.target.value = "";
});

document.getElementById("import-json").addEventListener("change", (event) => {
  const files = Array.from(event.target.files || []).filter(Boolean);
  if (!files.length) return;
  importJsonFiles(files).catch((err) => alert(err.message));
  event.target.value = "";
});

profileSelectEl.addEventListener("change", () => {
  selectProfile(profileSelectEl.value).catch((err) => alert(err.message));
  scheduleWorkspaceAutosave();
});

[gridWidthEl, gridHeightEl, offsetXEl, offsetYEl, tileWidthEl, tileHeightEl, zoomEl, highConfidenceEl, mediumConfidenceEl].forEach((input) => {
  input.addEventListener("input", updateGridFromInputs);
});

[mapNameEl, mapTagsEl, profileNameEl, profileCategoryEl, profileTagsEl, segmentNameEl, segmentRowEl, segmentColEl, segmentWidthEl, segmentHeightEl].forEach((input) => {
  input.addEventListener("input", () => {
    renderSegmentPreview();
    scheduleWorkspaceAutosave();
  });
});

document.querySelectorAll(".tm-chip[data-editor-mode]").forEach((chip) => {
  chip.addEventListener("click", () => setEditorMode(chip.dataset.editorMode));
});
showLabelsEl.addEventListener("change", () => {
  state.showLabels = Boolean(showLabelsEl.checked);
  renderGrid();
});

fillSelect(labelSurfaceEl, SURFACE_OPTIONS);
fillSelect(labelStructureEl, STRUCTURE_OPTIONS);
fillSelect(labelPropEl, PROP_OPTIONS);
fillSelect(labelHazardEl, HAZARD_OPTIONS);
fillSelect(labelMovementEl, MOVEMENT_OPTIONS);
fillSelect(labelVisibilityEl, VISIBILITY_OPTIONS);
fillSelect(labelCoverEl, COVER_OPTIONS);
fillHeightSelect();
renderPresetPalette();
resetAtlas();
syncSegmentDrawToggle();
updateGuide();
Promise.all([loadProfiles().catch(() => {}), loadLibrary().catch(() => {})])
  .then(() => loadWorkspaceDraft().catch(() => false))
  .catch(() => {});
