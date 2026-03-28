(function () {
  function describePaperdoll(profile, className) {
    const level = Number(profile?.level || 1);
    const trainerName = String(profile?.name || "Unnamed Trainer").trim() || "Unnamed Trainer";
    const cls = String(className || "Unclassed").trim() || "Unclassed";
    return `${trainerName} | Level ${level} | ${cls}`;
  }

  window.PTUPaperdollUI = {
    describePaperdoll,
  };
})();
