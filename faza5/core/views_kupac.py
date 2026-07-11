# Milica Štavljanin 391/2023
# Modul: Kupac i Rezervacija

import uuid

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from .models import Trka, Sektor, Smestaj, Rezervacija, DigitalniVaucer, Korisnik


def _trenutni_kupac(request):
    """
    Pomocna funkcija koja vraca ulogovanog Korisnika (Kupca) na osnovu
    podatka iz sesije, ili None ako niko nije ulogovan.

    Vraca: Korisnik instancu ili None
    """
    id_korisnika = request.session.get('id_korisnika')  # USKLADITI SA PRIJAVOM
    if not id_korisnika:
        return None
    try:
        return Korisnik.objects.get(pk=id_korisnika)
    except Korisnik.DoesNotExist:
        return None


@require_GET
def pretraga_trka(request):
    """
    SSU2 - Glavna stranica za pretragu i filtriranje trkackih dogadjaja.

    Prikazuje pocetnu listu trka i formu za filtriranje po sampionatu i
    lokaciji. Sama lista se dalje osvezava AJAX pozivom (view
    ajax_filtriraj_trke iz ovog fajla), ova funkcija samo iscrtava
    pocetnu stranicu sa svim trkama.

    Vraca: HttpResponse sa render-ovanim kupac/pretraga.html templateom
    """
    sampionati = Trka.objects.values_list('sampionat', flat=True).distinct()
    pocetna_lista_trka = Trka.objects.all().order_by('datum_odrzavanja')

    context = {
        'sampionati': sorted(set(sampionati)),
        'trke': pocetna_lista_trka,
    }
    return render(request, 'kupac/pretraga.html', context)


@require_GET
def ajax_filtriraj_trke(request):
    """
    SSU2 - AJAX endpoint (Posebni zahtevi: filtriranje u realnom vremenu
    bez ponovnog ucitavanja stranice) koji vraca JSON listu trka
    filtriranih po sampionatu i/ili lokaciji (drzava ili staza).

    Ocekivani GET parametri:
        sampionat (str, opciono) - npr. "F1", "MotoGP", "WSBK"
        lokacija (str, opciono)  - pretrazuje po drzavi ili nazivu staze

    Vraca: JsonResponse sa listom trka (ili poruku ako nema rezultata -
    alternativni scenario "Nema rezultata pretrage")
    """
    sampionat = request.GET.get('sampionat', '').strip()
    lokacija = request.GET.get('lokacija', '').strip()

    trke = Trka.objects.all()

    if sampionat:
        trke = trke.filter(sampionat=sampionat)

    if lokacija:
        trke = (
            trke.filter(drzava__icontains=lokacija)
            | trke.filter(staza__icontains=lokacija)
        )

    trke = trke.order_by('datum_odrzavanja')

    if not trke.exists():
        return JsonResponse({
            'rezultati': [],
            'poruka': 'Nema trka za taj filter',
        })

    podaci = [
        {
            'id_trke': t.id_trke,
            'naziv_trke': t.naziv_trke,
            'staza': t.staza,
            'drzava': t.drzava,
            'datum_odrzavanja': t.datum_odrzavanja.strftime('%d.%m.%Y'),
            'sampionat': t.sampionat,
        }
        for t in trke
    ]
    return JsonResponse({'rezultati': podaci, 'poruka': None})


@require_GET
def detalji_trke(request, id_trke):
    """
    SSU2 / SSU3 - Prikaz detalja izabrane trke: dostupni sektori na
    tribinama i lista preporucenih hotela sortirana po udaljenosti od
    staze (najblizi prvi).

    Vraca: HttpResponse sa render-ovanim kupac/detalji_trke.html templateom
    """
    trka = get_object_or_404(Trka, pk=id_trke)
    sektori = Sektor.objects.filter(id_trke=trka).order_by('naziv_sektora')
    smestaji = Smestaj.objects.filter(id_trke=trka).order_by('udaljenost_od_staze')

    context = {
        'trka': trka,
        'sektori': sektori,
        'smestaji': smestaji,
        'nema_smestaja': not smestaji.exists(),
    }
    return render(request, 'kupac/detalji_trke.html', context)


@require_POST
def dodaj_u_korpu(request, id_trke):
    """
    SSU3 - Kupac bira sektor i smestaj, sistem kreira privremenu
    Rezervaciju sa statusom 'U_korpi'.

    Pokriva alternativne scenarije:
        - Nema slobodnih mesta u sektoru
        - Nema dostupnog smestaja

    Ocekivani POST parametri: id_sektora, id_smestaja

    Vraca: redirect na stranicu korpe, ili detalji_trke sa porukom o
    gresci ako nema slobodnih mesta/soba
    """
    kupac = _trenutni_kupac(request)
    if kupac is None:
        return redirect('auth')  # USKLADITI SA PRIJAVOM - naziv url rute za login

    trka = get_object_or_404(Trka, pk=id_trke)
    id_sektora = request.POST.get('id_sektora')
    id_smestaja = request.POST.get('id_smestaja')

    sektor = get_object_or_404(Sektor, pk=id_sektora, id_trke=trka)
    smestaj = get_object_or_404(Smestaj, pk=id_smestaja, id_trke=trka)

    sektori_svi = Sektor.objects.filter(id_trke=trka)
    smestaji_svi = Smestaj.objects.filter(id_trke=trka).order_by('udaljenost_od_staze')

    if sektor.slobodna_mesta <= 0:
        return render(request, 'kupac/detalji_trke.html', {
            'trka': trka, 'sektori': sektori_svi, 'smestaji': smestaji_svi,
            'greska': 'Nema slobodnih mesta u izabranom sektoru',
        })

    if smestaj.broj_slobodnih_soba <= 0:
        return render(request, 'kupac/detalji_trke.html', {
            'trka': trka, 'sektori': sektori_svi, 'smestaji': smestaji_svi,
            'greska': 'Nema dostupnog smestaja za izabrani dogadjaj',
        })

    ukupna_cena = sektor.cena_karte + smestaj.cena_po_nocenju

    Rezervacija.objects.create(
        id_kupca=kupac,
        id_sektora=sektor,
        id_smestaja=smestaj,
        ukupna_cena=ukupna_cena,
        status_rezervacije='U_korpi',
    )

    return redirect('korpa')


@require_GET
def korpa(request):
    """
    SSU3 - Prikaz trenutne korpe kupca: sve njegove Rezervacije sa
    statusom 'U_korpi' koje jos nisu potvrdjene/placene.

    Vraca: HttpResponse sa render-ovanim kupac/korpa.html templateom
    """
    kupac = _trenutni_kupac(request)
    if kupac is None:
        return redirect('auth')  # USKLADITI SA PRIJAVOM

    stavke = Rezervacija.objects.filter(
        id_kupca=kupac, status_rezervacije='U_korpi'
    ).select_related('id_sektora', 'id_smestaja')

    ukupno = sum(s.ukupna_cena for s in stavke)

    return render(request, 'kupac/korpa.html', {
        'stavke': stavke,
        'ukupno': ukupno,
    })


@require_POST
def ukloni_iz_korpe(request, id_rezervacije):
    """
    Uklanja stavku iz korpe (Kupac odustaje pre placanja).

    Vraca: redirect na stranicu korpe
    """
    kupac = _trenutni_kupac(request)
    if kupac is None:
        return redirect('auth')  # USKLADITI SA PRIJAVOM

    rezervacija = get_object_or_404(
        Rezervacija, pk=id_rezervacije, id_kupca=kupac, status_rezervacije='U_korpi'
    )
    rezervacija.delete()
    return redirect('korpa')


@require_POST
def potvrdi_placanje(request, id_rezervacije):
    """
    SSU3 - Kupac potvrdjuje paket i pokrece simulaciju placanja. Ako je
    uspesna, sistem generise digitalni vaucer sa jedinstvenim QR kodom i
    menja status rezervacije u 'Aktivna'.
    """
    kupac = _trenutni_kupac(request)
    if kupac is None:
        return redirect('auth')  # USKLADITI SA PRIJAVOM

    rezervacija = get_object_or_404(
        Rezervacija, pk=id_rezervacije, id_kupca=kupac, status_rezervacije='U_korpi'
    )

    # Alternativni scenario: Neuspešno plaćanje
    if request.POST.get('simulate_failure') == '1':
        stavke = Rezervacija.objects.filter(id_kupca=kupac, status_rezervacije='U_korpi')
        return render(request, 'kupac/korpa.html', {
            'stavke': stavke,
            'ukupno': sum(s.ukupna_cena for s in stavke),
            'greska': 'Placanje nije uspesno, pokusajte ponovo',
        })

    # DOVUČEMO SEKTOR I SMEŠTAJ
    sektor = rezervacija.id_sektora
    smestaj = rezervacija.id_smestaja

    # POSLEDNJA PROVERA: Da li su se mesta rasprodala dok je paket bio u korpi?
    if sektor.slobodna_mesta <= 0 or smestaj.broj_slobodnih_soba <= 0:
        stavke = Rezervacija.objects.filter(id_kupca=kupac, status_rezervacije='U_korpi')
        return render(request, 'kupac/korpa.html', {
            'stavke': stavke,
            'ukupno': sum(s.ukupna_cena for s in stavke),
            'greska': 'Žao nam je, rasprodato je dok je paket bio u korpi!',
        })

    # ODUZIMAMO MESTA IZ BAZE PODATAKA
    sektor.slobodna_mesta -= 1
    sektor.save()

    smestaj.broj_slobodnih_soba -= 1
    smestaj.save()

    # ZAVRŠAVAMO REZERVACIJU
    rezervacija.status_rezervacije = 'Aktivna'
    rezervacija.save()

    vaucer = DigitalniVaucer.objects.create(
        id_rezervacije=rezervacija,
        qr_kod=str(uuid.uuid4()),
        status_vaucera='Validan',
    )

    return render(request, 'kupac/potvrda.html', {
        'rezervacija': rezervacija,
        'vaucer': vaucer,
    })