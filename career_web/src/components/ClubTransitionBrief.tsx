import { clubTransitionQuestionText, latestClubTransition } from "../clubTransitionPresentation";
import type { CareerRun, Locale } from "../types";

export function ClubTransitionBrief({ run, locale }: { run: CareerRun; locale: Locale }) {
  const brief = latestClubTransition(run);
  if (!brief) return null;

  const es = locale === "es";
  return (
    <div className="market-block club-transition-brief" aria-label={es ? "Presentación del contrato" : "Contract presentation"}>
      <div className="market-title">
        <b>{brief.renewal ? (es ? "Continuidad confirmada" : "Continuity confirmed") : (es ? "Cambio de club" : "Club move")}</b>
        <span>{es ? "HECHOS DE LA CARRERA" : "CAREER FACTS"}</span>
      </div>
      <div className="market-grid sponsor-grid">
        <article className="market-card club-card">
          <span className="market-tag">{es ? "CAPÍTULO ANTERIOR" : "PREVIOUS CHAPTER"}</span>
          <h3>{brief.previousClub || (es ? "Primer contrato" : "First contract")}</h3>
          {brief.record ? <strong>{brief.record}</strong> : null}
          <p>{brief.record
            ? (es ? "Registro de la última temporada cerrada." : "Record from the latest completed season.")
            : (es ? "No hay una temporada anterior cerrada para resumir." : "There is no previous completed season to summarize.")}</p>
        </article>

        <article className="market-card club-card">
          <span className="market-tag">{es ? "PLANTEL" : "SQUAD"}</span>
          <h3>{es ? "Consecuencias del vínculo" : "Contract consequences"}</h3>
          {brief.returnedLoans.length ? <p><b>{es ? "Volvieron al club anterior:" : "Returned to the previous club:"}</b> {brief.returnedLoans.join(" · ")}</p> : null}
          {brief.incomingLoans.length ? <p><b>{es ? "Cedidos registrados:" : "Registered loans:"}</b> {brief.incomingLoans.join(" · ")}</p> : null}
          {brief.giftSpecies ? <p><b>{es ? "Regalo permanente:" : "Permanent signing gift:"}</b> {brief.giftSpecies}</p> : null}
          {!brief.returnedLoans.length && !brief.incomingLoans.length && !brief.giftSpecies ? <p>{es ? "Sin cambios de propiedad Pokémon registrados por este contrato." : "No Pokémon ownership changes were recorded by this contract."}</p> : null}
        </article>

        <article className="market-card club-card">
          <span className="market-tag">{es ? "NUEVO CONTRATO" : "NEW CONTRACT"}</span>
          <h3>{brief.newClub}</h3>
          <strong>₽ {brief.salary} <small>/{es ? "temporada" : "season"}</small></strong>
          <p>{brief.seasons} {brief.seasons === 1 ? (es ? "temporada" : "season") : (es ? "temporadas" : "seasons")}</p>
          {brief.perkLabel ? <p>{brief.perkLabel}</p> : null}
          <p>{es ? `Reputación actual: ${run.reputation}` : `Current reputation: ${run.reputation}`}</p>
        </article>
      </div>
      <div className="decision-ledger">
        <b>{es ? "Preguntas de prensa" : "Press questions"}</b>
        {brief.questions.map((question) => <div key={question}><strong>{clubTransitionQuestionText(question, brief, locale)}</strong></div>)}
      </div>
      <p className="market-note">{es ? "Estas preguntas registran el contexto público del cambio. No modifican reputación, relaciones, salario ni combate." : "These questions frame the public context of the move. They do not change reputation, relationships, salary, or battle rules."}</p>
    </div>
  );
}
