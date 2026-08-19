import { useState } from "react";

import { careerApi } from "../api";
import type { CareerRun, Locale } from "../types";

interface Props {
  run: CareerRun;
  locale: Locale;
  onRun: (run: CareerRun) => void;
  compact?: boolean;
}

const PRODUCTS = [
  { id: "pokeball", price: 30, es: "Poké Ball", en: "Poké Ball", esDetail: "Una captura futura.", enDetail: "One future capture." },
  { id: "super_potion", price: 75, es: "Super Potion", en: "Super Potion", esDetail: "+12 salud al usarla.", enDetail: "+12 health when used." },
  { id: "club_resource", price: 100, es: "Sanear recursos", en: "Fund resources", esDetail: "+1 recurso; reduce la deuda.", enDetail: "+1 resource; reduces debt." },
  { id: "training_kit", price: 125, es: "Training Kit", en: "Training Kit", esDetail: "+2 a un stat. Consume 12 de salud competitiva del Pokémon; abusarlo acelera su retiro.", enDetail: "+2 to a stat. Costs 12 Pokémon career health; repeated use accelerates retirement." },
  { id: "facility_pass", price: 180, es: "Facility Pass", en: "Facility Pass", esDetail: "+2 desarrollo al usarlo.", enDetail: "+2 development when used." },
  { id: "pokedex_upgrade", price: 300, es: "Pokédex Upgrade", en: "Pokédex Upgrade", esDetail: "Mejores encuentros para siempre.", enDetail: "Better encounters permanently." },
] as const;

export function EconomyShop({ run, locale, onRun, compact = false }: Props) {
  const [busyProduct, setBusyProduct] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function buy(productId: string, label: string) {
    setBusyProduct(productId);
    setMessage("");
    setError("");
    try {
      const updated = await careerApi.purchase(run, productId);
      onRun(updated);
      setMessage(locale === "es" ? `${label} comprado. Saldo: ₽ ${updated.money}.` : `${label} purchased. Balance: ₽ ${updated.money}.`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusyProduct("");
    }
  }

  const visibleProducts = compact ? PRODUCTS.slice(0, 4) : PRODUCTS;
  return (
    <div className={`economy-market ${compact ? "compact" : ""}`} aria-label={locale === "es" ? "Mercado de carrera" : "Career market"}>
      <header>
        <div><small>{locale === "es" ? "DINERO DISPONIBLE" : "AVAILABLE MONEY"}</small><strong>₽ {run.money ?? 0}</strong></div>
        <p>{locale === "es" ? "El salario llega a este saldo al final de cada temporada. Comprá objetos o cubrí deuda del club." : "Salary reaches this balance after every season. Buy items or clear club debt."}</p>
      </header>
      <div className="market-grid">
        {visibleProducts.map((product) => {
          const label = locale === "es" ? product.es : product.en;
          return <article key={product.id} className={product.id === "club_resource" && run.finances < 0 ? "recommended" : ""} title={locale === "es" ? product.esDetail : product.enDetail}>
            <div><b>{label}</b><small>{locale === "es" ? product.esDetail : product.enDetail}</small></div>
            <button type="button" onClick={() => buy(product.id, label)} disabled={Boolean(busyProduct) || (run.money ?? 0) < product.price}>
              {busyProduct === product.id ? "…" : `${locale === "es" ? "Comprar" : "Buy"} · ₽ ${product.price}`}
            </button>
          </article>;
        })}
      </div>
      {message ? <p className="market-message" role="status">{message}</p> : null}
      {error ? <p className="form-error" role="alert">{error}</p> : null}
    </div>
  );
}
