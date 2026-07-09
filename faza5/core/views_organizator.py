# Autor: Milan
# Modul: Organizator i upravljanje trkama

from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date
from .models import Trka, Korisnik

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