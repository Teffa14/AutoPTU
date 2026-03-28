(function () {
  const tooltipClass = "ds-tooltip";
  const tooltipOffset = 8;
  const tooltipPadding = 10;
  let tooltipEl = null;
  let activeTooltipTarget = null;
  let lastFocused = null;

  function ensureTooltip() {
    if (tooltipEl) return tooltipEl;
    tooltipEl = document.createElement("div");
    tooltipEl.className = tooltipClass;
    tooltipEl.style.display = "none";
    tooltipEl.setAttribute("role", "tooltip");
    document.body.appendChild(tooltipEl);
    return tooltipEl;
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(value, max));
  }

  function computeCoords(reference, floating, placement) {
    const ref = reference.getBoundingClientRect();
    const float = floating.getBoundingClientRect();
    const centerX = ref.left + ref.width / 2 - float.width / 2;
    const centerY = ref.top + ref.height / 2 - float.height / 2;
    if (placement === "top") {
      return { x: centerX, y: ref.top - float.height - tooltipOffset };
    }
    if (placement === "bottom") {
      return { x: centerX, y: ref.bottom + tooltipOffset };
    }
    if (placement === "left") {
      return { x: ref.left - float.width - tooltipOffset, y: centerY };
    }
    return { x: ref.right + tooltipOffset, y: centerY };
  }

  function placementsForAuto(reference, floating) {
    const ref = reference.getBoundingClientRect();
    const float = floating.getBoundingClientRect();
    const space = {
      top: ref.top,
      bottom: window.innerHeight - ref.bottom,
      left: ref.left,
      right: window.innerWidth - ref.right,
    };
    return Object.keys(space)
      .map((key) => ({ key, space: space[key] }))
      .sort((a, b) => b.space - a.space)
      .map((entry) => entry.key)
      .filter((key) => {
        if (key === "top" || key === "bottom") return space[key] >= float.height + tooltipOffset;
        return space[key] >= float.width + tooltipOffset;
      });
  }

  function computePosition(reference, floating, placement) {
    const placements = ["top", "bottom", "right", "left"];
    let desired = placement || "top";
    if (desired === "auto") {
      const auto = placementsForAuto(reference, floating);
      desired = auto.length ? auto[0] : "top";
    }
    let coords = computeCoords(reference, floating, desired);

    const fits = (coordsToCheck) => {
      return (
        coordsToCheck.x >= tooltipPadding &&
        coordsToCheck.y >= tooltipPadding &&
        coordsToCheck.x + floating.offsetWidth <= window.innerWidth - tooltipPadding &&
        coordsToCheck.y + floating.offsetHeight <= window.innerHeight - tooltipPadding
      );
    };

    if (!fits(coords)) {
      const order = placements.filter((p) => p !== desired);
      for (const fallback of order) {
        const next = computeCoords(reference, floating, fallback);
        if (fits(next)) {
          desired = fallback;
          coords = next;
          break;
        }
      }
    }

    coords.x = clamp(coords.x, tooltipPadding, window.innerWidth - floating.offsetWidth - tooltipPadding);
    coords.y = clamp(coords.y, tooltipPadding, window.innerHeight - floating.offsetHeight - tooltipPadding);

    return { x: coords.x, y: coords.y, placement: desired };
  }

  function showTooltip(target) {
    const tooltip = ensureTooltip();
    const text = target.getAttribute("data-tooltip");
    if (!text) return;
    activeTooltipTarget = target;
    tooltip.textContent = text;
    tooltip.style.display = "block";
    const placement = target.getAttribute("data-tooltip-placement") || "top";
    const pos = computePosition(target, tooltip, placement);
    tooltip.style.left = `${pos.x}px`;
    tooltip.style.top = `${pos.y}px`;
  }

  function hideTooltip() {
    if (!tooltipEl) return;
    tooltipEl.style.display = "none";
    activeTooltipTarget = null;
  }

  function initTooltips() {
    document.addEventListener("mouseover", (event) => {
      const target = event.target.closest("[data-tooltip]");
      if (!target) return;
      showTooltip(target);
    });
    document.addEventListener("mouseout", (event) => {
      if (event.target.closest("[data-tooltip]")) hideTooltip();
    });
    document.addEventListener("focusin", (event) => {
      const target = event.target.closest("[data-tooltip]");
      if (!target) return;
      showTooltip(target);
    });
    document.addEventListener("focusout", (event) => {
      if (event.target.closest("[data-tooltip]")) hideTooltip();
    });
    window.addEventListener("scroll", hideTooltip, true);
    window.addEventListener("resize", () => {
      if (activeTooltipTarget) showTooltip(activeTooltipTarget);
    });
  }

  function initTabs() {
    document.querySelectorAll("[data-tablist]").forEach((tablist) => {
      const tabs = Array.from(tablist.querySelectorAll("[data-tab]"));
      const root = tablist.closest("[data-tab-root]") || tablist.parentElement;
      const panels = root ? Array.from(root.querySelectorAll("[data-tab-panel]")) : [];
      tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
          const target = tab.getAttribute("data-tab");
          tabs.forEach((t) => t.setAttribute("aria-selected", t === tab ? "true" : "false"));
          panels.forEach((panel) => {
            panel.classList.toggle("active", panel.getAttribute("data-tab-panel") === target);
          });
        });
      });
    });
  }

  function openModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    lastFocused = document.activeElement;
    modal.classList.remove("hidden");
    modal.setAttribute("aria-hidden", "false");
    const focusTarget =
      modal.querySelector("[data-modal-focus]") ||
      modal.querySelector("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
    if (focusTarget) focusTarget.focus();
  }

  function closeModal(modal) {
    if (!modal) return;
    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");
    if (lastFocused && typeof lastFocused.focus === "function") {
      lastFocused.focus();
    }
  }

  function trapFocus(modal, event) {
    if (event.key !== "Tab") return;
    const focusables = Array.from(
      modal.querySelectorAll("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])")
    ).filter((el) => !el.disabled && el.offsetParent !== null);
    if (!focusables.length) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function initModals() {
    document.querySelectorAll("[data-modal-open]").forEach((btn) => {
      btn.addEventListener("click", () => openModal(btn.getAttribute("data-modal-open")));
    });
    document.querySelectorAll("[data-modal-close]").forEach((btn) => {
      btn.addEventListener("click", () => closeModal(btn.closest("[data-modal]")));
    });
    document.querySelectorAll("[data-modal]").forEach((modal) => {
      modal.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
          closeModal(modal);
        }
        trapFocus(modal, event);
      });
    });
  }

  function initAccordions() {
    document.querySelectorAll("[data-accordion]").forEach((accordion) => {
      accordion.querySelectorAll("[data-accordion-trigger]").forEach((trigger) => {
        const panelId = trigger.getAttribute("data-accordion-trigger");
        const panel = panelId ? accordion.querySelector(`[data-accordion-panel='${panelId}']`) : null;
        if (!panel) return;
        trigger.setAttribute("aria-expanded", trigger.getAttribute("aria-expanded") || "false");
        panel.hidden = trigger.getAttribute("aria-expanded") !== "true";
        trigger.addEventListener("click", () => {
          const expanded = trigger.getAttribute("aria-expanded") === "true";
          trigger.setAttribute("aria-expanded", expanded ? "false" : "true");
          panel.hidden = expanded;
        });
      });
    });
  }

  function toast(message, timeout = 2500, type = "info") {
    let wrap = document.querySelector(".ds-toast-wrap");
    if (!wrap) {
      wrap = document.createElement("div");
      wrap.className = "ds-toast-wrap";
      document.body.appendChild(wrap);
    }
    const item = document.createElement("div");
    item.className = `ds-toast ${type ? `ds-toast-${type}` : ""}`.trim();
    item.textContent = message;
    wrap.appendChild(item);
    setTimeout(() => item.remove(), timeout);
  }

  function notify(type, message, timeout = 2800) {
    const kind = String(type || "info").toLowerCase();
    const normalized = kind === "error" || kind === "warn" || kind === "success" ? kind : "info";
    toast(message, timeout, normalized);
  }

  function isTypingContext(event) {
    const target = event?.target;
    if (!target) return false;
    if (target.isContentEditable) return true;
    return ["INPUT", "SELECT", "TEXTAREA"].includes(target.tagName);
  }

  window.DSUI = { toast, notify, openModal, closeModal, isTypingContext };

  document.addEventListener("DOMContentLoaded", () => {
    initTooltips();
    initTabs();
    initModals();
    initAccordions();
  });
})();
