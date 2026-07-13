# Autor:Milica Štavljanin 0391/2023;
"""Javne stranice i kompletan tok kupovine paketa za kupca."""

from __future__ import annotations

from datetime import date

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .constants import (
    SAMPIONATI,
    STATUS_REZERVACIJE_AKTIVNA,
    STATUS_REZERVACIJE_KORPA,
    STATUS_REZERVACIJE_ZAVRSENA,
    ULOGA_ADMINISTRATOR,
    ULOGA_KUPAC,
)
from .forms import PackageForm, RecenzijaForm
from .models import DigitalniVaucer, Recenzija, Rezervacija, Smestaj, Trka
from .pdf_utils import build_voucher_pdf
from .services import (
    AvailabilityError,
    BusinessRuleError,
    cancel_reservation,
    create_cart_reservation,
    finalize_reservation,
    mark_past_reservations_complete,
)
from .session_auth import get_session_user, role_required


def _filtered_races(request: HttpRequest):
    """Gradi upit za pretragu isključivo nad kolonama tabele ``trka``."""

    races = Trka.objects.filter(datum_odrzavanja__gte=date.today()).select_related(
        "id_organizatora"
    )
    championship = request.GET.get("sampionat", "").strip()
    location = request.GET.get("lokacija", "").strip()
    race_date = request.GET.get("datum", "").strip()
    query = request.GET.get("q", "").strip()

    if championship in dict(SAMPIONATI):
        races = races.filter(sampionat=championship)
    if location:
        races = races.filter(
            Q(drzava__icontains=location) | Q(staza__icontains=location)
        )
    if race_date:
        races = races.filter(datum_odrzavanja=race_date)
    if query:
        races = races.filter(
            Q(naziv_trke__icontains=query)
            | Q(staza__icontains=query)
            | Q(drzava__icontains=query)
        )

    return races.prefetch_related("sektori", "smestaji").order_by(
        "datum_odrzavanja", "naziv_trke"
    )


@require_GET
def index_strana(request: HttpRequest) -> HttpResponse:
    """Prikazuje javnu naslovnu stranu i najbliže raspoložive trke."""

    races = (
        Trka.objects.filter(
            datum_odrzavanja__gte=date.today(),
            sektori__slobodna_mesta__gt=0,
            smestaji__broj_slobodnih_soba__gt=0,
        )
        .distinct()
        .select_related("id_organizatora")
        .order_by("datum_odrzavanja")[:6]
    )
    return render(request, "kupac/index.html", {"trke": races})


@require_GET
def pretraga_trka(request: HttpRequest) -> HttpResponse:
    """Prikazuje punu stranu pretrage sa početnim rezultatima."""

    races = _filtered_races(request)
    return render(
        request,
        "kupac/pretraga.html",
        {
            "trke": races,
            "sampionati": SAMPIONATI,
            "broj_rezultata": races.count(),
        },
    )


@require_GET
def ajax_filtriraj_trke(request: HttpRequest) -> JsonResponse:
    """AJAX endpoint vraća HTML kartica i broj rezultata bez osvežavanja strane."""

    races = _filtered_races(request)
    html = render_to_string(
        "kupac/_lista_trka.html", {"trke": races}, request=request
    )
    return JsonResponse({"html": html, "count": races.count()})


@require_GET
def detalji_trke(request: HttpRequest, id_trke: int) -> HttpResponse:
    """Prikazuje sektore, smeštaje i postojeće recenzije jedne trke."""

    race = get_object_or_404(
        Trka.objects.select_related("id_organizatora").prefetch_related(
            "sektori", "smestaji"
        ),
        pk=id_trke,
    )
    reviews = Recenzija.objects.filter(
        id_rezervacije__id_sektora__id_trke=race
    ).select_related("id_kupca")[:8]
    form = PackageForm(race=race)
    return render(
        request,
        "kupac/detalji_trke.html",
        {"trka": race, "package_form": form, "recenzije": reviews},
    )


@require_POST
@role_required(ULOGA_KUPAC)
def dodaj_u_korpu(request: HttpRequest, id_trke: int) -> HttpResponse:
    """Dodaje izabrani paket u korpu bez rezervisanja kapaciteta pre plaćanja."""

    race = get_object_or_404(Trka, pk=id_trke)
    form = PackageForm(request.POST, race=race)
    if form.is_valid():
        try:
            reservation, created = create_cart_reservation(
                buyer=request.current_user,
                sector=form.cleaned_data["id_sektora"],
                accommodation=form.cleaned_data["id_smestaja"],
            )
        except BusinessRuleError as exc:
            messages.error(request, str(exc))
        else:
            if created:
                messages.success(
                    request,
                    f"Paket #{reservation.pk} je dodat u korpu. Kapacitet se "
                    "konačno proverava pri plaćanju.",
                )
            else:
                messages.info(request, "Isti paket se već nalazi u vašoj korpi.")
            return redirect("korpa")
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect("detalji_trke", id_trke=race.pk)


@require_GET
@role_required(ULOGA_KUPAC)
def korpa(request: HttpRequest) -> HttpResponse:
    """Prikazuje samo neplaćene rezervacije prijavljenog kupca."""

    reservations = Rezervacija.objects.filter(
        id_kupca=request.current_user,
        status_rezervacije=STATUS_REZERVACIJE_KORPA,
    ).select_related("id_sektora__id_trke", "id_smestaja")
    return render(request, "kupac/korpa.html", {"rezervacije": reservations})


@require_POST
@role_required(ULOGA_KUPAC)
def ukloni_iz_korpe(request: HttpRequest, id_rezervacije: int) -> HttpResponse:
    """Trajno uklanja neplaćenu stavku iz korpe njenog vlasnika."""

    deleted, _ = Rezervacija.objects.filter(
        pk=id_rezervacije,
        id_kupca=request.current_user,
        status_rezervacije=STATUS_REZERVACIJE_KORPA,
    ).delete()
    if deleted:
        messages.info(request, "Paket je uklonjen iz korpe.")
    else:
        messages.error(request, "Stavka korpe nije pronađena.")
    return redirect("korpa")


@require_POST
@role_required(ULOGA_KUPAC)
def potvrdi_placanje(request: HttpRequest, id_rezervacije: int) -> HttpResponse:
    """Obrađuje uspešno ili demonstraciono neuspešno plaćanje."""

    if settings.DEMO_MODE and request.POST.get("simuliraj_neuspeh") == "1":
        messages.error(
            request,
            "Plaćanje nije uspelo. Rezervacija je ostala u korpi i kapacitet nije promenjen.",
        )
        return redirect("korpa")
    try:
        voucher = finalize_reservation(
            reservation_id=id_rezervacije, buyer=request.current_user
        )
    except AvailabilityError as exc:
        messages.error(request, f"Plaćanje nije izvršeno: {exc}")
        return redirect("korpa")
    except BusinessRuleError as exc:
        messages.error(request, str(exc))
        return redirect("korpa")

    messages.success(request, "Plaćanje je uspešno. Digitalni vaučer je izdat.")
    return render(request, "kupac/potvrda.html", {"vaucer": voucher})


@require_POST
@role_required(ULOGA_KUPAC)
def otkazi_rezervaciju(request: HttpRequest, id_rezervacije: int) -> HttpResponse:
    """Otkazuje kupčevu rezervaciju uz vraćanje zauzetih kapaciteta."""

    try:
        cancel_reservation(
            reservation_id=id_rezervacije, buyer=request.current_user
        )
    except BusinessRuleError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Rezervacija je otkazana.")
    return redirect("istorija_kupovina")


@require_http_methods(["GET", "POST"])
@role_required(ULOGA_KUPAC)
def ostavi_recenziju(request: HttpRequest, id_rezervacije: int) -> HttpResponse:
    """Dozvoljava jednu recenziju samo za završenu kupovinu."""

    mark_past_reservations_complete()
    reservation = get_object_or_404(
        Rezervacija.objects.select_related(
            "id_sektora__id_trke", "id_smestaja"
        ),
        pk=id_rezervacije,
        id_kupca=request.current_user,
        status_rezervacije=STATUS_REZERVACIJE_ZAVRSENA,
    )
    if Recenzija.objects.filter(id_rezervacije=reservation).exists():
        messages.info(request, "Ova rezervacija je već ocenjena.")
        return redirect("istorija_kupovina")

    form = RecenzijaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)
        review.id_rezervacije = reservation
        review.id_kupca = request.current_user
        review.save()
        messages.success(request, "Hvala! Recenzija je sačuvana.")
        return redirect("istorija_kupovina")
    return render(
        request,
        "kupac/recenzija_form.html",
        {"form": form, "rezervacija": reservation},
    )


@require_GET
@role_required(ULOGA_KUPAC, ULOGA_ADMINISTRATOR)
def preuzmi_vaucer(request: HttpRequest, id_vaucera: int) -> HttpResponse:
    """Vraća PDF samo vlasniku vaučera ili administratoru."""

    query = DigitalniVaucer.objects.select_related(
        "id_rezervacije__id_kupca",
        "id_rezervacije__id_sektora__id_trke",
        "id_rezervacije__id_smestaja",
    )
    voucher = get_object_or_404(query, pk=id_vaucera)
    user = get_session_user(request)
    if user.uloga != ULOGA_ADMINISTRATOR and voucher.id_rezervacije.id_kupca_id != user.pk:
        messages.error(request, "Nemate pristup ovom vaučeru.")
        return redirect("istorija_kupovina")

    response = HttpResponse(build_voucher_pdf(voucher), content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="vaucer-{voucher.id_vaucera}.pdf"'
    )
    return response


@require_GET
@role_required(ULOGA_KUPAC)
def istorija_kupovina(request: HttpRequest) -> HttpResponse:
    """Prikazuje sve kupčeve plaćene, završene i otkazane pakete."""

    mark_past_reservations_complete()
    reservations = (
        Rezervacija.objects.filter(id_kupca=request.current_user)
        .exclude(status_rezervacije=STATUS_REZERVACIJE_KORPA)
        .select_related("id_sektora__id_trke", "id_smestaja")
        .prefetch_related("vaucer", "recenzija")
    )
    return render(
        request,
        "kupac/istorija.html",
        {
            "rezervacije": reservations,
            "status_aktivna": STATUS_REZERVACIJE_AKTIVNA,
            "status_zavrsena": STATUS_REZERVACIJE_ZAVRSENA,
        },
    )
