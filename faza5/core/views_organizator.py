# Autor: Milan
# Modul: Organizator i upravljanje trkama

from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date
from .models import Trka, Korisnik
from .models import Sektor

def organizator_dashboard(request):
    trke = Trka.objects.all()
    return render(request, 'organizator/dashboard.html', {'trke': trke})

def dodaj_trku(request):
    if request.method == 'POST':
        naziv = request.POST.get('naziv_trke')
        sampionat = request.POST.get('sampionat')
        staza = request.POST.get('staza')
        drzava = request.POST.get('drzava')
        datum = request.POST.get('datum_odrzavanja')

        organizator = Korisnik.objects.first()

        if organizator:
            nova_trka = Trka(
                id_organizatora=organizator,
                naziv_trke=naziv,
                staza=staza,
                drzava=drzava,
                datum_odrzavanja=parse_date(datum),
                sampionat=sampionat
            )
            nova_trka.save()

        return redirect('organizator_dashboard')
    return redirect('organizator_dashboard')


def upravljaj_sektorima(request, id_trke):
    """
    Slučaj upotrebe: Pregled i dodavanje sektora za izabranu trku.
    """
    # Pronalazimo trku za koju radimo sektore
    trka = Trka.objects.get(pk=id_trke)

    if request.method == 'POST':
        naziv = request.POST.get('naziv_sektora')
        kapacitet = request.POST.get('kapacitet')
        cena = request.POST.get('cena')

        # Pravimo novi sektor i vezujemo ga za ovu trku
        novi_sektor = Sektor(
            id_trke=trka,
            naziv_sektora=naziv,
            ukupni_kapacitet=kapacitet,  # Ovde smo stavili tačno ime iz tvog modela
            slobodna_mesta=kapacitet,  # I ovde
            cena_karte=cena
        )
        novi_sektor.save()
        return redirect('upravljaj_sektorima', id_trke=id_trke)

    # Izvlačimo sve sektore koji pripadaju samo ovoj trci
    sektori = Sektor.objects.filter(id_trke=trka)

    return render(request, 'organizator/sektori.html', {
        'trka': trka,
        'sektori': sektori
    })