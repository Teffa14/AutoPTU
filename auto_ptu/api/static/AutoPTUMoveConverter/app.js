const els = {
  kind: document.getElementById("kind"),
  name: document.getElementById("name"),
  text: document.getElementById("text"),
  rangeOverride: document.getElementById("range-override"),
  keywordsOverride: document.getElementById("keywords-override"),
  typeOverride: document.getElementById("type-override"),
  categoryOverride: document.getElementById("category-override"),
  frequencyOverride: document.getElementById("frequency-override"),
  dbOverride: document.getElementById("db-override"),
  useAi: document.getElementById("use-ai"),
  aiProvider: document.getElementById("ai-provider"),
  aiModel: document.getElementById("ai-model"),
  aiBaseUrl: document.getElementById("ai-base-url"),
  aiApiKeyWrap: document.getElementById("ai-api-key-wrap"),
  aiApiKeyLabel: document.getElementById("ai-api-key-label"),
  aiApiKey: document.getElementById("ai-api-key"),
  aiTemperature: document.getElementById("ai-temperature"),
  aiHelp: document.getElementById("ai-help"),
  testConnectionButton: document.getElementById("test-connection-button"),
  aiConnectionResult: document.getElementById("ai-connection-result"),
  aiStatusDetail: document.getElementById("ai-status-detail"),
  aiReasoning: document.getElementById("ai-reasoning"),
  aiPreview: document.getElementById("ai-preview"),
  convertButton: document.getElementById("convert-button"),
  copyJsonButton: document.getElementById("copy-json-button"),
  exampleButton: document.getElementById("example-button"),
  moveName: document.getElementById("move-name"),
  statusPill: document.getElementById("status-pill"),
  moveSummary: document.getElementById("move-summary"),
  moveText: document.getElementById("move-text"),
  jsonOutput: document.getElementById("json-output"),
  requestPreview: document.getElementById("request-preview"),
};

let lastPayload = null;

function shouldUseAi() {
  return els.useAi.checked || Boolean(els.aiModel.value.trim());
}

function backendUnavailableMessage() {
  if (window.location.protocol === "file:") {
    return "This page was opened directly from a file. Launch AutoPTUMoveConverter.exe instead so the local API server is running.";
  }
  return "The local AutoPTU launcher is not reachable. Relaunch AutoPTUMoveConverter.exe and use the newly opened browser tab.";
}

function setConnectionResult(message, tone = "") {
  els.aiConnectionResult.textContent = message;
  els.aiConnectionResult.classList.remove("ok", "error");
  if (tone) {
    els.aiConnectionResult.classList.add(tone);
  }
}

function setAiPreview(message) {
  els.aiPreview.textContent = message || "No AI response yet.";
}

function setAiStatusDetail(message) {
  els.aiStatusDetail.textContent = message || "No AI call yet.";
}

function setAiReasoning(items) {
  if (Array.isArray(items) && items.length) {
    els.aiReasoning.textContent = items.join("\n");
    return;
  }
  els.aiReasoning.textContent = "No AI reasoning yet.";
}

function syncAiProviderUi() {
  const provider = els.aiProvider.value;
  if (provider === "ollama") {
    if (!els.aiBaseUrl.value.trim()) {
      els.aiBaseUrl.value = "http://127.0.0.1:11434";
    }
    els.aiApiKey.value = "";
    els.aiApiKey.disabled = true;
    els.aiApiKey.placeholder = "Not needed for local Ollama";
    els.aiApiKeyWrap.classList.add("field-disabled");
    els.aiApiKeyLabel.textContent = "API Key (not needed for local Ollama)";
    els.aiHelp.textContent = "Local Ollama usually needs no API key. Set a model name, leave the key blank, and use the default local URL.";
    setConnectionResult("Test the local Ollama server before converting if you want to confirm the model is installed.");
    setAiStatusDetail("No AI call yet.");
    setAiReasoning([]);
    setAiPreview("No AI response yet.");
  } else {
    if (!els.aiBaseUrl.value.trim() || els.aiBaseUrl.value.trim() === "http://127.0.0.1:11434") {
      els.aiBaseUrl.value = "http://127.0.0.1:8000";
    }
    els.aiApiKey.disabled = false;
    els.aiApiKey.placeholder = "Optional";
    els.aiApiKeyWrap.classList.remove("field-disabled");
    els.aiApiKeyLabel.textContent = "API Key";
    els.aiHelp.textContent = "Use this mode for OpenAI-compatible local servers or hosted endpoints. Add a key only if that server requires one.";
    setConnectionResult("Use Test Connection to verify the endpoint responds and that the selected model is exposed.");
    setAiStatusDetail("No AI call yet.");
    setAiReasoning([]);
    setAiPreview("No AI response yet.");
  }
  renderRequestPreview();
}

function buildPayload() {
  const dbRaw = String(els.dbOverride.value || "").trim();
  const aiEnabled = shouldUseAi();
  return {
    kind: els.kind.value,
    name: els.name.value.trim(),
    text: els.text.value.trim(),
    range_override: els.rangeOverride.value.trim(),
    keywords_override: els.keywordsOverride.value.trim(),
    type_override: els.typeOverride.value.trim(),
    category_override: els.categoryOverride.value.trim(),
    frequency_override: els.frequencyOverride.value.trim(),
    db_override: dbRaw ? Number(dbRaw) : null,
    use_ai: aiEnabled,
    local_model: {
      enabled: aiEnabled,
      provider: els.aiProvider.value,
      model: els.aiModel.value.trim(),
      base_url: els.aiBaseUrl.value.trim(),
      api_key: els.aiApiKey.value.trim(),
      temperature: Number(els.aiTemperature.value || 0.2),
    },
  };
}

function renderRequestPreview() {
  els.requestPreview.textContent = JSON.stringify(buildPayload(), null, 2);
}

function setStatus(label) {
  els.statusPill.textContent = label;
}

function renderSummary(move) {
  const stats = [
    ["Type", move.type || "-"],
    ["Category", move.category || "-"],
    ["Frequency", move.freq || "-"],
    ["Range", move.range_text || move.range_kind || "-"],
    ["Keywords", Array.isArray(move.keywords) && move.keywords.length ? move.keywords.join(", ") : "-"],
  ];
  els.moveSummary.innerHTML = stats
    .map(
      ([label, value]) => `
        <div class="stat">
          <span class="label">${label}</span>
          <span class="value">${value}</span>
        </div>
      `
    )
    .join("");
}

function renderPayload(payload) {
  lastPayload = payload;
  const move = payload?.move || {};
  els.moveName.textContent = move.name || "Unnamed Move";
  renderSummary(move);
  els.moveText.textContent = [
    `${move.name || "Move"} | ${move.type || "Normal"} | ${move.category || "Status"}`,
    `Freq: ${move.freq || "-"}`,
    `Range: ${move.range_text || move.range_kind || "-"}`,
    `DB: ${move.db ?? 0} | AC: ${move.ac ?? "-"}`,
    "",
    move.effects_text || "No effect text.",
  ].join("\n");
  els.jsonOutput.textContent = JSON.stringify(payload, null, 2);
  const aiStatus = payload?.ai_status || "";
  const aiDetail = payload?.ai_detail || "";
  setAiStatusDetail(aiDetail || "No AI call yet.");
  setAiReasoning(payload?.ai_reasoning || []);
  setAiPreview(payload?.ai_raw_response || "No AI response yet.");
  if (aiStatus === "applied") {
    setConnectionResult(aiDetail || "AI refinement was applied.", "ok");
    setStatus("AI Refined");
  } else if (payload?.request?.use_ai || aiStatus === "attempted_no_change") {
    setConnectionResult(aiDetail || "AI refinement was attempted but did not change the result.", "error");
    setStatus("AI No-Op");
  } else {
    setStatus("Ready");
  }
}

async function runConversion() {
  setStatus("Working");
  try {
    const response = await fetch("/api/convert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload()),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload?.detail || payload?.error || "Conversion failed");
    }
    renderPayload(payload);
  } catch (error) {
    const message = error instanceof TypeError ? backendUnavailableMessage() : String(error);
    setStatus("Error");
    els.moveName.textContent = "Conversion Failed";
    els.moveSummary.innerHTML = "";
    els.moveText.textContent = message;
    els.jsonOutput.textContent = JSON.stringify({ error: message }, null, 2);
    setAiStatusDetail(message);
    setAiReasoning([]);
    setAiPreview(message);
    setConnectionResult(message, "error");
  }
}

async function testConnection() {
  setStatus("Testing");
  setConnectionResult("Checking model endpoint...");
  try {
    const response = await fetch("/api/test-model", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ local_model: buildPayload().local_model }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload?.detail || payload?.error || "Connection test failed");
    }
    const available = payload.model_available;
    const detail = payload.detail || "Connection succeeded.";
    const suffix = typeof available === "boolean" && !available ? " Selected model was not found." : "";
    setConnectionResult(`${detail}${suffix}`, available === false ? "error" : "ok");
    setAiStatusDetail(payload.detail || "Connection succeeded.");
    setAiReasoning([]);
    setAiPreview("No AI response yet.");
    setStatus(available === false ? "Model Missing" : "Connected");
  } catch (error) {
    const message = error instanceof TypeError ? backendUnavailableMessage() : String(error);
    setConnectionResult(message, "error");
    setAiStatusDetail(message);
    setAiReasoning([]);
    setAiPreview(message);
    setStatus("Connection Error");
  }
}

async function copyJson() {
  const text = lastPayload ? JSON.stringify(lastPayload, null, 2) : els.jsonOutput.textContent;
  try {
    await navigator.clipboard.writeText(text);
    setStatus("Copied");
  } catch (_error) {
    setStatus("Copy Failed");
  }
}

function loadExample() {
  const examples = {
    move: {
      name: "Custom Ember",
      text: "Range 4, 1 Target. DB 4. Burns the target on 18+.",
      rangeOverride: "",
      keywordsOverride: "",
    },
    ability: {
      name: "Static",
      text: "",
      rangeOverride: "",
      keywordsOverride: "",
    },
    item: {
      name: "Bright Powder",
      text: "",
      rangeOverride: "",
      keywordsOverride: "",
    },
  };
  const sample = examples[els.kind.value];
  els.name.value = sample.name;
  els.text.value = sample.text;
  els.rangeOverride.value = sample.rangeOverride;
  els.keywordsOverride.value = sample.keywordsOverride;
  renderRequestPreview();
}

els.convertButton.addEventListener("click", runConversion);
els.testConnectionButton.addEventListener("click", testConnection);
els.copyJsonButton.addEventListener("click", copyJson);
els.exampleButton.addEventListener("click", loadExample);
els.kind.addEventListener("change", loadExample);
els.aiProvider.addEventListener("change", syncAiProviderUi);
els.aiModel.addEventListener("input", () => {
  if (els.aiModel.value.trim()) {
    els.useAi.checked = true;
  }
  renderRequestPreview();
});

[
  els.kind,
  els.name,
  els.text,
  els.rangeOverride,
  els.keywordsOverride,
  els.typeOverride,
  els.categoryOverride,
  els.frequencyOverride,
  els.dbOverride,
  els.useAi,
  els.aiProvider,
  els.aiBaseUrl,
  els.aiApiKey,
  els.aiTemperature,
].forEach((el) => {
  el.addEventListener("input", renderRequestPreview);
  el.addEventListener("change", renderRequestPreview);
});

loadExample();
syncAiProviderUi();
renderRequestPreview();
