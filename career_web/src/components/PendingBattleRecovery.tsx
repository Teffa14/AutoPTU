import { navigate } from "../App";
import { loadBattleCheckpoint, restoreBattleCheckpoint, saveLocalRun } from "../localCareer";
import { pendingBattleRecovery, repairExhaustedDecisionPhase } from "../seasonRecovery";
import type { CareerRun, Locale } from "../types";

export function PendingBattleRecovery({ run, locale, onRun }: { run: CareerRun; locale: Locale; onRun: (run: CareerRun) => void }) {
  const recovery = pendingBattleRecovery(run);
  if (!recovery) return null;
  const activeRecovery = recovery;
  const checkpoint = loadBattleCheckpoint(run.id);

  function retryBattle() {
    if (!activeRecovery.battleId) return;
    if (activeRecovery.phaseRepairNeeded) {
      const repaired = repairExhaustedDecisionPhase(run);
      if (!repaired) return;
      saveLocalRun(repaired);
      onRun(repaired);
    }
    navigate(`battle/${run.id}/${activeRecovery.battleId}`);
  }

  function rollbackBattle() {
    const restored = restoreBattleCheckpoint(run.id);
    if (!restored) return;
    window.location.reload();
  }

  return (
    <section className="battle-error pending-battle-recovery">
      <p className="eyebrow">{locale === "es" ? "TEMPORADA EN CURSO" : "SEASON IN PROGRESS"}</p>
      <h1>{locale === "es" ? "El combate sigue pendiente" : "The battle is still pending"}</h1>
      <p>
        {activeRecovery.phaseRepairNeeded
          ? (locale === "es"
            ? "La temporada quedó en una fase imposible después de registrar todas las decisiones. Podés reparar el estado y volver al combate sin perder la carrera."
            : "The season was left in an impossible phase after all decisions were recorded. Repair the state and return to battle without losing the career.")
          : (locale === "es"
            ? "Tus decisiones ya quedaron registradas. El calendario no se reinició. Primero podés volver a intentar cargar el mismo combate."
            : "Your decisions are already recorded. The schedule was not reset. You can first retry loading the same battle.")}
      </p>
      <p>
        <b>{activeRecovery.decisionsCompleted}/{activeRecovery.decisionsRequired}</b>{" "}
        {locale === "es" ? "decisiones registradas" : "decisions recorded"} · {locale === "es" ? "temporada" : "season"} {activeRecovery.seasonNumber}
      </p>
      {activeRecovery.battleId ? (
        <button className="primary-action" type="button" onClick={retryBattle}>
          {activeRecovery.phaseRepairNeeded
            ? (locale === "es" ? "Reparar y volver al combate" : "Repair and return to battle")
            : (locale === "es" ? "Reintentar combate" : "Retry battle")}
        </button>
      ) : (
        <p className="form-error" role="alert">
          {locale === "es"
            ? "La temporada quedó trabada y no tiene un battle_id guardado. Usá el punto seguro si está disponible."
            : "The season is stuck and has no saved battle_id. Use the safe checkpoint if available."}
        </p>
      )}
      {checkpoint ? (
        <button className="text-action" type="button" onClick={rollbackBattle}>
          {locale === "es" ? "Volver al punto seguro antes del combate" : "Restore pre-battle safe point"}
        </button>
      ) : null}
      <button className="text-action" type="button" onClick={() => window.location.reload()}>
        {locale === "es" ? "Recargar estado" : "Reload state"}
      </button>
    </section>
  );
}
