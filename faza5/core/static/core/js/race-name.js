/* # Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;  */

"use strict";

/** Inicijalizuje odloženu proveru dostupnosti naziva trke. */
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("#race-form");
    const input = document.querySelector("#id_naziv_trke");
    const feedback = document.querySelector("#race-name-feedback");
    if (!form || !input || !feedback || !form.dataset.nameCheckUrl) return;

    let timer = null;
    /** Zakazuje proveru naziva posle izmene polja. */
    input.addEventListener("input", () => {
        window.clearTimeout(timer);
        const name = input.value.trim();
        if (name.length < 3) {
            feedback.textContent = "Unesite najmanje tri znaka za proveru naziva.";
            return;
        }
        /** Poziva serverski endpoint i prikazuje rezultat provere naziva. */
        timer = window.setTimeout(async () => {
            const params = new URLSearchParams({ naziv: name });
            if (form.dataset.raceId) params.set("izuzmi", form.dataset.raceId);
            try {
                const response = await fetch(`${form.dataset.nameCheckUrl}?${params}`);
                const payload = await response.json();
                feedback.textContent = payload.message;
                feedback.dataset.available = String(payload.available);
            } catch (_error) {
                feedback.textContent = "Provera naziva nije dostupna; validacija će biti izvršena pri čuvanju.";
            }
        }, 300);
    });
});
