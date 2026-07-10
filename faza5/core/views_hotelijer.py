from django.shortcuts import render, redirect
from core.models import Smestaj, Trka, Korisnik


def partner_dashboard(request):
    """
    Prikazuje kontrolnu tablu hotelijera sa formom za dodavanje i tabelom postojećih smeštaja.
    """
    # Za sada simuliramo ulogovanog hotelijera (npr. korisnik sa ID=2)
    # Kada proradi login sistem, ovde će ići request.user
    hotelijer = Korisnik.objects.filter(id_korisnika=2).first()

    if request.method == 'POST':
        # Prikupljamo podatke iz HTML forme
        naziv = request.POST.get('naziv_smestaja')
        lokacija = request.POST.get('lokacija')
        udaljenost = request.POST.get('udaljenost')
        broj_soba = request.POST.get('broj_soba')
        cena = request.POST.get('cena')
        id_trke = request.POST.get('trka_id')

        trka_obj = Trka.objects.filter(id_trke=id_trke).first()

        if naziv and trka_obj and hotelijer:
            # Čuvamo novi smeštaj u bazu
            Smestaj.objects.create(
                id_hotelijera=hotelijer,
                id_trke=trka_obj,
                naziv_smestaja=naziv,
                lokacija=lokacija,
                udaljenost_od_staze=udaljenost,
                broj_slobodnih_soba=broj_soba,
                cena_po_nocenju=cena
            )
        return redirect('partner_dashboard')

    # Povlačimo podatke za prikaz na stranici
    moji_smestaji = Smestaj.objects.filter(id_hotelijera=hotelijer)
    sve_trke = Trka.objects.all()  # Da hotelijer može da izabere za koju trku vezuje smeštaj

    context = {
        'smestaji': moji_smestaji,
        'trke': sve_trke
    }
    return render(request, 'hotelijer/partner_panel.html', context)


def obrisi_smestaj(request, id_smestaja):
    """Briše smeštaj iz baze."""
    smestaj = Smestaj.objects.filter(id_smestaja=id_smestaja).first()
    if smestaj:
        smestaj.delete()
    return redirect('partner_dashboard')