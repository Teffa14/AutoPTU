(function () {
  function _pillStatus(status) {
    if (status === "available") return "status-available";
    if (status === "close") return "status-close";
    if (status === "blocked") return "status-blocked";
    return "status-unavailable";
  }

  function _buildDeckCard(entry, evalResult, handlers) {
    const card = document.createElement("div");
    card.className = `char-deck-card ${_pillStatus(evalResult.status)}`;
    card.dataset.entryName = entry.name;
    card.dataset.entryKind = "poke-edge";
    card.setAttribute("tabindex", "0");

    const head = document.createElement("div");
    head.className = "char-card-head";
    const icon = document.createElement("span");
    icon.className = `char-card-icon ${_pillStatus(evalResult.status)}`;
    icon.textContent = "PE";
    icon.setAttribute("aria-hidden", "true");
    const title = document.createElement("div");
    title.className = "char-deck-title";
    title.textContent = entry.name;
    head.appendChild(icon);
    head.appendChild(title);

    const meta = document.createElement("div");
    meta.className = "char-row-meta";
    const cost = entry.cost ? `Cost: ${entry.cost}` : "Cost: -";
    meta.textContent = `${cost} | ${evalResult.status}`;

    const detail = document.createElement("div");
    detail.className = "char-edge-meta";
    detail.textContent = evalResult.reason || entry.effects || "No description.";

    const actions = document.createElement("div");
    actions.className = "char-board-card-actions";
    const add = document.createElement("button");
    add.type = "button";
    add.textContent = handlers.isSelected ? "Added" : "Add";
    add.disabled = handlers.isSelected;
    add.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (handlers.isSelected) return;
      if (evalResult.reason) {
        handlers.notify(evalResult.reason);
        return;
      }
      handlers.onAdd(entry.name);
    });
    actions.appendChild(add);

    card.appendChild(head);
    card.appendChild(meta);
    card.appendChild(detail);
    card.appendChild(actions);
    return card;
  }

  function _buildSlotCard(name, index, total, handlers) {
    const item = document.createElement("div");
    item.className = "char-shelf-card";
    item.dataset.entryName = name;
    item.dataset.entryKind = "poke-edge";

    const head = document.createElement("div");
    head.className = "char-card-head";
    const icon = document.createElement("span");
    icon.className = "char-card-icon status-available";
    icon.textContent = "PE";
    icon.setAttribute("aria-hidden", "true");
    const title = document.createElement("div");
    title.className = "char-shelf-title";
    title.textContent = name;
    head.appendChild(icon);
    head.appendChild(title);

    const controls = document.createElement("div");
    controls.className = "char-shelf-controls";

    const earlier = document.createElement("button");
    earlier.type = "button";
    earlier.className = "char-shelf-shift";
    earlier.textContent = "Earlier";
    earlier.disabled = index <= 0;
    earlier.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      handlers.onMove(name, -1);
    });

    const later = document.createElement("button");
    later.type = "button";
    later.className = "char-shelf-shift";
    later.textContent = "Later";
    later.disabled = index >= total - 1;
    later.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      handlers.onMove(name, 1);
    });

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "char-shelf-remove";
    remove.textContent = "Remove";
    remove.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      handlers.onRemove(name);
    });

    controls.appendChild(earlier);
    controls.appendChild(later);
    controls.appendChild(remove);

    item.appendChild(head);
    item.appendChild(controls);
    return item;
  }

  function renderPokeEdgeBoard(config) {
    const {
      edges,
      selected,
      evaluate,
      onAdd,
      onRemove,
      onMove,
      onReorder,
      notify,
      sortableEnabled,
      registerSortable,
      ghostReason,
      setGhostReason,
    } = config;

    const wrap = document.createElement("div");
    wrap.className = "char-board-grid";

    const deckPanel = document.createElement("div");
    deckPanel.className = "char-list-panel";
    const deckTitle = document.createElement("div");
    deckTitle.className = "char-section-title";
    deckTitle.textContent = "Available Poke Edges";
    deckPanel.appendChild(deckTitle);
    const deckMeta = document.createElement("div");
    deckMeta.className = "char-row-meta";
    deckMeta.textContent = "Pick from the catalog. Click Add for the fastest flow.";
    deckPanel.appendChild(deckMeta);
    const deck = document.createElement("div");
    deck.className = "char-entry-list char-deck-list";
    deckPanel.appendChild(deck);

    const slotPanel = document.createElement("div");
    slotPanel.className = "char-list-panel";
    const slotTitle = document.createElement("div");
    slotTitle.className = "char-section-title";
    slotTitle.textContent = "Selected Order";
    slotPanel.appendChild(slotTitle);
    const slotMeta = document.createElement("div");
    slotMeta.className = "char-row-meta";
    slotMeta.textContent = "Review your chosen Poke Edges here. Use Earlier/Later to reorder, or drag if you prefer.";
    slotPanel.appendChild(slotMeta);
    const ghostNote = document.createElement("div");
    ghostNote.className = "char-ghost-reason";
    ghostNote.textContent = ghostReason || "";
    slotPanel.appendChild(ghostNote);
    const slots = document.createElement("div");
    slots.className = "char-slot-board";
    slotPanel.appendChild(slots);

    edges.forEach((entry) => {
      const evalResult = evaluate(entry.name);
      const card = _buildDeckCard(entry, evalResult, {
        isSelected: selected.includes(entry.name),
        onAdd,
        notify,
      });
      deck.appendChild(card);
    });

    const ordered = selected.slice();
    ordered.forEach((name, index) => {
      slots.appendChild(_buildSlotCard(name, index, ordered.length, { onRemove, onMove }));
    });

    if (!ordered.length) {
      const empty = document.createElement("div");
      empty.className = "char-slot-empty";
      empty.textContent = "No Poke Edges selected yet.";
      slots.appendChild(empty);
    }

    if (sortableEnabled && window.Sortable) {
      const deckSortable = new Sortable(deck, {
        group: { name: "poke-edge-board", pull: "clone", put: false },
        sort: false,
        animation: 120,
        ghostClass: "char-ghost",
        draggable: ".char-deck-card",
      });
      if (typeof registerSortable === "function") registerSortable(deckSortable);

      const slotSortable = new Sortable(slots, {
        group: { name: "poke-edge-board", pull: true, put: true },
        animation: 140,
        ghostClass: "char-ghost",
        draggable: ".char-shelf-card, .char-deck-card",
        filter: ".char-slot-empty",
        onMove: (evt) => {
          const name = String(evt.dragged?.dataset?.entryName || "").trim();
          const evalResult = evaluate(name);
          const reason = evalResult.reason;
          if (reason) {
            slots.classList.add("slot-invalid");
            setGhostReason(reason);
            ghostNote.textContent = reason;
          } else {
            slots.classList.remove("slot-invalid");
            setGhostReason("");
            ghostNote.textContent = "";
          }
          return true;
        },
        onAdd: (evt) => {
          slots.classList.remove("slot-invalid");
          const card = evt.item;
          const name = String(card?.dataset?.entryName || "").trim();
          const evalResult = evaluate(name);
          if (evalResult.reason) {
            card.remove();
            setGhostReason(evalResult.reason);
            ghostNote.textContent = evalResult.reason;
            notify(evalResult.reason);
            return;
          }
          const added = onAdd(name);
          card.remove();
          if (!added) {
            notify(`Already selected: ${name}`);
            return;
          }
        },
        onUpdate: () => {
          const next = Array.from(slots.querySelectorAll(".char-shelf-card")).map((el) => el.dataset.entryName).filter(Boolean);
          onReorder(next);
        },
      });
      if (typeof registerSortable === "function") registerSortable(slotSortable);
    }

    wrap.appendChild(deckPanel);
    wrap.appendChild(slotPanel);
    return wrap;
  }

  window.PTUBuilderUI = {
    renderPokeEdgeBoard,
  };
})();
