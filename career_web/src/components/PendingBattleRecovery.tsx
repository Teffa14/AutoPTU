import { navigate } from "../App";
import { pendingBattleRecovery } from "../seasonRecovery";
import type { CareerRun, Locale } from "../types";

export function PendingBattleRecovery({ run, locale }: { run: CareerRun; locale: Locale }) {
  const recovery = pendingBattleRecovery(run);
  if (!recovery) return null;

  return (
    <section className="battle-error pending-battle-recovery">
      <p className="eyebrow">{locale === "es" ? "TEMPORADA EN CURSO" : "SEASON IN PROGRESS"}</p>
      <h1>{locale === "es" ? "El combate sigue pendiente" : "The battle is still pending"}</h1>
      <p>
        {locale === "es"
          ? "Tus decisiones ya quedaron registradas. El calendario no se reinició. Volvé a intentar cargar el mismo combate."
          : "Your decisions are already recorded. The schedule was not reset. Retry loading the same battle."}
      </p>
      <p>
        <b>{recovery.decisionsCompleted}/{recovery.decisionsRequired}</b>{" "}
        {locale === "es" ? "decisiones registradas" : "decisions recorded"} · {locale === "es" ? "temporada" : "season"} {recovery.seasonNumber}
      </p>
      {recovery.battleId ? (
        <button className="primary-action" type="button" onClick={() => navigate(`battle/${run.id}/${recovery.battleId}`)}>
          {locale === "es" ? "Reintentar combate" : "Retry battle"}
        </button>
      ) : (
        <p className="form-error" role="alert">
          {locale === "es"
            ? "La temporada está en fase de combate pero no tiene un battle_id guardado. Recargá el estado antes de continuar."
            : "The season is in battle phase but has no saved battle_id. Reload the state before continuing."}
        </p>
      )}
      <button className="text-action" type="button" onClick={() => window.location.reload()}>
        {locale === "es" ? "Recargar estado" : "Reload state"}
      </button>
    </section>
  );
}
