/* # Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;  */

"use strict";

/** Povezuje zajedničke navigacione, poruke i potvrde akcija. */
document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector("[data-nav-toggle]");
    const nav = document.querySelector("[data-nav]");
    if (toggle && nav) {
        /** Otvara ili zatvara mobilnu navigaciju i ažurira ARIA stanje. */
        toggle.addEventListener("click", () => {
            const open = nav.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", String(open));
        });
    }

    /** Omogućava korisniku da ukloni prikazanu sistemsku poruku. */
    document.querySelectorAll("[data-dismiss-message]").forEach((button) => {
        button.addEventListener("click", () => button.closest(".message")?.remove());
    });

    /** Dodaje potvrdu svim formama označenim kao destruktivne. */
    document.querySelectorAll("form[data-confirm]").forEach((form) => {
        /** Zaustavlja slanje kada korisnik odbije potvrdu. */
        form.addEventListener("submit", (event) => {
            const text = form.dataset.confirm || "Potvrditi akciju?";
            if (!window.confirm(text)) event.preventDefault();
        });
    });
});
