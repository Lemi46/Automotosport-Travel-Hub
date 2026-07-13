/* # Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;  */

"use strict";

/** Inicijalizuje AJAX pretragu trka i sinhronizaciju URL filtera. */
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("#race-filter-form");
    const results = document.querySelector("#race-results");
    const count = document.querySelector("#result-count");
    if (!form || !results || !count || !form.dataset.ajaxUrl) return;

    let timer = null;
    let controller = null;

    /** Osvežava listu trka bez ponovnog učitavanja cele stranice. */
    const refresh = async () => {
        const params = new URLSearchParams(new FormData(form));
        if (controller) controller.abort();
        controller = new AbortController();
        results.setAttribute("aria-busy", "true");
        try {
            const response = await fetch(`${form.dataset.ajaxUrl}?${params.toString()}`, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                signal: controller.signal,
            });
            if (!response.ok) throw new Error("Pretraga nije dostupna.");
            const payload = await response.json();
            results.innerHTML = payload.html;
            count.textContent = String(payload.count);
            const pageUrl = `${form.action}?${params.toString()}`;
            window.history.replaceState({}, "", pageUrl);
        } catch (error) {
            if (error.name !== "AbortError") {
                results.innerHTML = '<div class="message message-error">Pretraga trenutno nije dostupna.</div>';
            }
        } finally {
            results.setAttribute("aria-busy", "false");
        }
    };

    /** Grupisano pokreće pretragu posle kratkog perioda mirovanja. */
    const schedule = () => {
        window.clearTimeout(timer);
        timer = window.setTimeout(refresh, 260);
    };

    form.addEventListener("input", schedule);
    form.addEventListener("change", schedule);
    /** Sprečava klasično slanje forme i pokreće AJAX osvežavanje. */
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        refresh();
    });
});
