(function () {
  function getElements(root = document) {
    return {
      gridEl: root.getElementById("grid"),
      combatantListEl: root.getElementById("combatant-list"),
      detailsEl: root.getElementById("combatant-details"),
      trainerDetailsEl: root.getElementById("trainer-details"),
      moveListEl: root.getElementById("move-list"),
      logEl: root.getElementById("log"),
      partyBarEl: root.getElementById("party-bar"),
      turnOrderBarEl: root.getElementById("turn-order-bar"),
      roundInfoEl: root.getElementById("round-info"),
      terrainInfoEl: root.getElementById("terrain-info"),
      weatherInfoEl: root.getElementById("weather-info"),
      mapSeedEl: root.getElementById("map-seed"),
      sidebarRoundInfoEl: root.getElementById("sidebar-round-info"),
      sidebarTerrainInfoEl: root.getElementById("sidebar-terrain-info"),
      sidebarWeatherInfoEl: root.getElementById("sidebar-weather-info"),
      startButton: root.getElementById("start-battle"),
      endTurnButton: root.getElementById("end-turn"),
      aiStepButton: root.getElementById("ai-step"),
      aiAutoButton: root.getElementById("ai-auto"),
      undoButton: root.getElementById("undo-action"),
      zoomInButton: root.getElementById("zoom-in"),
      zoomOutButton: root.getElementById("zoom-out"),
      zoomFitButton: root.getElementById("zoom-fit"),
      moveTooltip: root.getElementById("move-tooltip"),
      selectedTileInfoEl: root.getElementById("selected-tile-info"),
      topbarEl: root.querySelector(".topbar"),
    };
  }

  function computeLifecycle(state, flags) {
    const hasBattle = !!state && state.status === "ok";
    const pendingPrompts = hasBattle ? (state.pending_prompts || []).length : 0;
    const promptLocked = pendingPrompts > 0;
    const isAiMode = hasBattle && state.mode === "ai";
    const isPlayerTurn = hasBattle && !!state.current_actor_is_player;
    const battleOver = hasBattle && !!state.battle_over;
    const autoActive = !!flags?.autoActive;

    return {
      hasBattle,
      isAiMode,
      isPlayerTurn,
      promptLocked,
      pendingPrompts,
      battleOver,
      autoActive,
      canStartBattle: !autoActive,
      canEndTurn: hasBattle && !battleOver && isPlayerTurn && !promptLocked,
      canAiStep: hasBattle && isAiMode && !battleOver && !promptLocked,
      canToggleAuto: hasBattle && isAiMode && !battleOver,
      canUndo: hasBattle && !battleOver,
      reason: promptLocked ? "Resolve pending prompts before continuing." : "",
    };
  }

  function applyLifecycleControls(elements, lifecycle) {
    if (!elements || !lifecycle) return;
    if (elements.startButton) elements.startButton.disabled = !lifecycle.canStartBattle;
    if (elements.endTurnButton) elements.endTurnButton.disabled = !lifecycle.canEndTurn;
    if (elements.aiStepButton) elements.aiStepButton.disabled = !lifecycle.canAiStep;
    if (elements.aiAutoButton) elements.aiAutoButton.disabled = !lifecycle.canToggleAuto;
    if (elements.undoButton) elements.undoButton.disabled = !lifecycle.canUndo;
    if (elements.aiAutoButton) {
      elements.aiAutoButton.textContent = lifecycle.autoActive ? "Auto On" : "Auto Off";
      if (lifecycle.promptLocked) {
        elements.aiAutoButton.title = lifecycle.reason;
      } else {
        elements.aiAutoButton.removeAttribute("title");
      }
    }
  }

  window.PTUBattleUI = {
    getElements,
    computeLifecycle,
    applyLifecycleControls,
  };
})();
