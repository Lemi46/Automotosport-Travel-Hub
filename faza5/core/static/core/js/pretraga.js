// Autor: Milica Štavljanin 391/2023
// AJAX (Fetch API) filtriranje trkackih dogadjaja - SSU2: filtriranje i
// prikaz rezultata u realnom vremenu bez ponovnog ucitavanja stranice.

/**
 * Sastavlja URL za stranicu detalja trke na osnovu id-a.
 * @param {number} idTrke - ID trke
 * @returns {string} kompletna putanja ka stranici detalja
 */
function urlDetaljiTrke(idTrke) {
    return URL_DETALJI_TRKE_SABLON.replace('0', idTrke);
}

/**
 * Generise HTML kod jedne kartice trke.
 * @param {Object} trka - objekat sa poljima id_trke, naziv_trke, staza,
 * drzava, datum_odrzavanja, sampionat
 * @returns {string} HTML markup kartice
 */
function napraviKarticuTrke(trka) {
    // Određujemo boju bedža u zavisnosti od šampionata
    let bojaBedza = trka.sampionat === 'F1' ? 'bg-danger' : 'bg-primary';

    return `
        <div class="col-md-6 col-lg-4">
            <div class="card trka-card shadow-sm h-100 border-0">
                <div class="card-body d-flex flex-column">
                    <span class="badge ${bojaBedza} mb-2 align-self-start">${trka.sampionat}</span>
                    <h5 class="card-title fw-bold fs-4">${trka.naziv_trke}</h5>
                    <p class="card-text text-muted mb-1">📍 ${trka.staza}, ${trka.drzava}</p>
                    <p class="card-text text-muted mb-4">📅 ${trka.datum_odrzavanja}</p>
                    <a href="${urlDetaljiTrke(trka.id_trke)}" class="btn btn-outline-dark fw-bold w-100 mt-auto">Detalji i rezervacija</a>
                </div>
            </div>
        </div>
    `;
}

/**
 * Poziva AJAX endpoint sa trenutno izabranim filterima i osvezava
 * listu trka na stranici bez reload-a.
 * @returns {Promise<void>}
 */
async function ucitajFiltriraneTrke() {
    const sampionat = document.getElementById('filter-sampionat').value;
    const lokacija = document.getElementById('filter-lokacija').value;

    const parametri = new URLSearchParams({ sampionat, lokacija });

    const listaDiv = document.getElementById('lista-trka');
    const porukaDiv = document.getElementById('poruka-bez-rezultata');

    try {
        const odgovor = await fetch(`${URL_AJAX_FILTER}?${parametri.toString()}`);
        const podaci = await odgovor.json();

        listaDiv.innerHTML = '';

        if (!podaci.rezultati || podaci.rezultati.length === 0) {
            porukaDiv.textContent = podaci.poruka || 'Nema trka za taj filter. Pokušajte sa drugim parametrima.';
            porukaDiv.style.display = 'block';
            return;
        }

        porukaDiv.style.display = 'none';
        podaci.rezultati.forEach(trka => {
            listaDiv.insertAdjacentHTML('beforeend', napraviKarticuTrke(trka));
        });
    } catch (greska) {
        console.error('Greska pri ucitavanju trka:', greska);
        porukaDiv.textContent = 'Doslo je do greske prilikom pretrage. Pokusajte ponovo.';
        porukaDiv.style.display = 'block';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btn-pretrazi').addEventListener('click', ucitajFiltriraneTrke);
    document.getElementById('filter-sampionat').addEventListener('change', ucitajFiltriraneTrke);
});