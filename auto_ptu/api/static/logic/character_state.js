(function () {
  function ensureOrderedSet(state, setKey, orderKey) {
    if (!state) return [];
    if (!(state[setKey] instanceof Set)) state[setKey] = new Set(Array.isArray(state[setKey]) ? state[setKey] : []);
    if (!Array.isArray(state[orderKey])) state[orderKey] = [];
    state[orderKey] = state[orderKey].filter((name) => state[setKey].has(name));
    state[setKey].forEach((name) => {
      if (!state[orderKey].includes(name)) state[orderKey].push(name);
    });
    return state[orderKey].slice();
  }

  function addOrdered(state, setKey, orderKey, name) {
    const value = String(name || "").trim();
    if (!value) return false;
    ensureOrderedSet(state, setKey, orderKey);
    if (!state[setKey].has(value)) state[setKey].add(value);
    if (!state[orderKey].includes(value)) state[orderKey].push(value);
    return true;
  }

  function removeOrdered(state, setKey, orderKey, name) {
    const value = String(name || "").trim();
    if (!value) return false;
    ensureOrderedSet(state, setKey, orderKey);
    state[setKey].delete(value);
    state[orderKey] = state[orderKey].filter((entry) => entry !== value);
    return true;
  }

  function reorder(state, setKey, orderKey, names) {
    ensureOrderedSet(state, setKey, orderKey);
    const next = [];
    (names || []).forEach((name) => {
      const value = String(name || "").trim();
      if (value && state[setKey].has(value) && !next.includes(value)) next.push(value);
    });
    state[setKey].forEach((name) => {
      if (!next.includes(name)) next.push(name);
    });
    state[orderKey] = next;
    return next.slice();
  }

  window.PTUCharacterState = {
    ensureOrderedSet,
    addOrdered,
    removeOrdered,
    reorder,
  };
})();
