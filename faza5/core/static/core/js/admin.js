/* # Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;  */

"use strict";

/** Inicijalizuje administratorsku AJAX statistiku kada je dokument spreman. */
document.addEventListener("DOMContentLoaded", () => {
    const panel = document.querySelector("#statistics-panel");
    const period = document.querySelector("#stats-period");
    const revenue = document.querySelector("#stats-revenue");
    const sales = document.querySelector("#stats-sales");
    if (!panel || !period || !revenue || !sales || !panel.dataset.statsUrl) return;

    /** Učitava prodaju i zaradu za trenutno izabrani period. */
    const load = async () => {
        revenue.textContent = "…";
        sales.textContent = "…";
        try {
            const response = await fetch(`${panel.dataset.statsUrl}?period=${encodeURIComponent(period.value)}`, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            if (!response.ok) throw new Error("Statistika nije dostupna.");
            const payload = await response.json();
            revenue.textContent = `${Number(payload.zarada).toFixed(2)} EUR`;
            sales.textContent = String(payload.prodato);
        } catch (_error) {
            revenue.textContent = "Greška";
            sales.textContent = "Greška";
        }
    };

    period.addEventListener("change", load);
    load();
});
