import { useEffect, useMemo, useState, type FormEvent } from "react";
import { careerApi } from "../api";
import { t } from "../i18n";
import type { CareerCatalog, CareerMode, CareerRun, Locale } from "../types";
import { StarterPicker } from "./StarterPicker";

interface Props { locale: Locale; onCreated: (run: CareerRun) => void }

export function CreateScreen({ locale, onCreated }: Props) {
  const copy = t(locale);
  const [catalog, setCatalog] = useState<CareerCatalog | null>(null);
  const [region, setRegion] = useState("kanto");
  const [starter, setStarter] = useState("Bulbasaur");
  const [trainerClass, setTrainerClass] = useState("Ace Trainer");
  const [name, setName] = useState("");
  const [mode, setMode] = useState<CareerMode>("simple");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    careerApi.catalog(locale).then(setCatalog).catch((reason: Error) => setError(reason.message));
  }, [locale]);
  const selectedRegion = useMemo(() => catalog?.regions.find((entry) => entry.id === region), [catalog, region]);

  function chooseRegion(value: string) {
    setRegion(value);
    const next = catalog?.regions.find((entry) => entry.id === value)?.partner_choices[0];
    if (next) setStarter(next);
  }

  async function begin(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      onCreated(await careerApi.create({ name, region, starter, classes: [trainerClass], mode, locale }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="creation-scene">
      <div className="creation-atmosphere" aria-hidden="true"><span /><span /><span /></div>
      <header className="creation-copy">
        <p className="eyebrow">Junior intake · age 12</p>
        <h1>{copy.createTitle}</h1>
        <p>{copy.createBody}</p>
      </header>
      {!catalog ? <div className="ticket-loader">Preparing the regional registry…</div> : (
        <form className="registration-book" onSubmit={begin}>
          <div className="book-spine" aria-hidden="true" />
          <div className="form-row">
            <label><span>{locale === "es" ? "Nombre" : "Name"}</span><input value={name} onChange={(event) => setName(event.target.value)} required maxLength={30} placeholder="Ari Vale" /></label>
            <label><span>{locale === "es" ? "Región" : "Region"}</span><select value={region} onChange={(event) => chooseRegion(event.target.value)}>{catalog.regions.map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}</select></label>
          </div>
          <fieldset className="starter-field">
            <legend>{locale === "es" ? "Elegí tu compañero regional" : "Choose your regional partner"}</legend>
            <StarterPicker starters={selectedRegion?.starters ?? []} underdogs={selectedRegion?.underdogs ?? []} value={starter} locale={locale} onChange={setStarter} />
          </fieldset>
          <div className="form-row final-row">
            <label className="class-choice"><span>{locale === "es" ? "Clase PTU" : "PTU class"}</span><select value={trainerClass} onChange={(event) => setTrainerClass(event.target.value)}>{catalog.classes.map((entry) => <option key={entry.id} value={entry.name}>{entry.name}</option>)}</select><small>{classDescription(catalog, trainerClass, locale)}</small></label>
            <div className="mode-switch" role="group" aria-label="Career mode">
              {(["simple", "advanced"] as CareerMode[]).map((entry) => <button type="button" key={entry} className={mode === entry ? "active" : ""} aria-pressed={mode === entry} onClick={() => setMode(entry)}><b>{entry}</b><small>{entry === "simple" ? "15–20 min" : "30–45 min"}</small></button>)}
            </div>
          </div>
          <div className="registration-footer"><span><b>10</b> Poké Balls</span><span><b>{catalog.decision_signature_count.toLocaleString()}</b> decision contexts</span><button className="primary-action" disabled={busy}>{busy ? "Signing…" : copy.start}</button></div>
          {error ? <p className="form-error" role="alert">{error}</p> : null}
        </form>
      )}
    </section>
  );
}

function classDescription(catalog: CareerCatalog, name: string, locale: Locale) {
  const entry = catalog.classes.find((item) => item.name === name);
  return entry ? (locale === "es" ? entry.description_es : entry.description_en) : "";
}
