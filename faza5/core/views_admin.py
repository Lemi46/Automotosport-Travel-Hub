from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from core.models import Rezervacija, Korisnik


def admin_dashboard(request):
    """
    Prikazuje glavnu admin tablu sa listom korisnika (priprema za SSU 5).
    """
    # Povlačimo sve korisnike da bi admin mogao da ih vidi i suspenduje
    korisnici = Korisnik.objects.all()
    return render(request, 'admin/admin_panel.html', {'korisnici': korisnici})


def api_statistika(request):
    """
    AJAX endpoint: Vraća statistiku zarade i prodatih aranžmana.
    Reaguje na promenu vremenskog perioda (sve, mesec, godina).
    """
    period = request.GET.get('period', 'sve')
    rezervacije = Rezervacija.objects.all()

    # Filtriranje po vremenskom periodu
    sada = timezone.now()
    if period == 'mesec':
        rezervacije = rezervacije.filter(datum_kreiranja__gte=sada - timedelta(days=30))
    elif period == 'godina':
        rezervacije = rezervacije.filter(datum_kreiranja__gte=sada - timedelta(days=365))

    # Izračunavanje sume (ukupna_cena) i prebrojavanje rezervacija
    ukupna_zarada = rezervacije.aggregate(Sum('ukupna_cena'))['ukupna_cena__sum'] or 0
    broj_prodatih = rezervacije.count()

    # Vraćamo JSON odgovor koji će naš JavaScript (AJAX) pročitati
    return JsonResponse({
        'zarada': float(ukupna_zarada),
        'prodato': broj_prodatih
    })


def suspenduj_korisnika(request, id_korisnika):
    """
    SSU 5: Suspenzija korisničkog naloga.
    Administratori ne mogu biti suspendovani.
    """
    korisnik = Korisnik.objects.filter(id_korisnika=id_korisnika).first()

    if korisnik and korisnik.uloga != 'Administrator':
        korisnik.status_naloga = 'Suspendovan'
        korisnik.save()

    return redirect('admin_dashboard')