# Autor: Milan Lemić 0323/2023;
"""Upravljanje trkama i sektorima prijavljenog organizatora."""

from __future__ import annotations

from django.contrib import messages
from django.db.models import Count
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .constants import SYSTEM_ORGANIZER_EMAIL, ULOGA_ORGANIZATOR
from .forms import SektorForm, TrkaForm
from .models import Rezervacija, Sektor, Trka
from .session_auth import role_required


@require_GET
@role_required(ULOGA_ORGANIZATOR)
def organizator_dashboard(request: HttpRequest) -> HttpResponse:
    """Prikazuje isključivo sopstvene trke i trke dostupne za preuzimanje."""

    races = (
        Trka.objects.filter(id_organizatora=request.current_user)
        .annotate(broj_sektora=Count("sektori", distinct=True))
        .order_by("datum_odrzavanja")
    )
    imported = (
        Trka.objects.filter(id_organizatora__email=SYSTEM_ORGANIZER_EMAIL)
        .select_related("id_organizatora")
        .order_by("datum_odrzavanja")[:30]
    )
    return render(
        request,
        "organizator/dashboard.html",
        {"trke": races, "uvezene_trke": imported},
    )


@require_http_methods(["GET", "POST"])
@role_required(ULOGA_ORGANIZATOR)
def dodaj_trku(request: HttpRequest) -> HttpResponse:
    """Kreira novu trku i vezuje je za prijavljenog organizatora."""

    form = TrkaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        race = form.save(commit=False)
        race.id_organizatora = request.current_user
        race.save()
        messages.success(request, "Trka je uspešno dodata.")
        return redirect("upravljaj_sektorima", id_trke=race.pk)
    return render(
        request,
        "organizator/trka_form.html",
        {"form": form, "naslov": "Dodavanje trke", "akcija": "Dodaj trku"},
    )


@require_http_methods(["GET", "POST"])
@role_required(ULOGA_ORGANIZATOR)
def izmeni_trku(request: HttpRequest, id_trke: int) -> HttpResponse:
    """Menja samo trku čiji je vlasnik prijavljeni organizator."""

    race = get_object_or_404(
        Trka, pk=id_trke, id_organizatora=request.current_user
    )
    form = TrkaForm(request.POST or None, instance=race)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Podaci o trci su sačuvani.")
        return redirect("organizator_dashboard")
    return render(
        request,
        "organizator/trka_form.html",
        {"form": form, "naslov": "Izmena trke", "akcija": "Sačuvaj izmene"},
    )


@require_POST
@role_required(ULOGA_ORGANIZATOR)
def preuzmi_trku(request: HttpRequest, id_trke: int) -> HttpResponse:
    """Dodeljuje uvezenu sistemsku trku prijavljenom organizatoru."""

    race = get_object_or_404(
        Trka, pk=id_trke, id_organizatora__email=SYSTEM_ORGANIZER_EMAIL
    )
    race.id_organizatora = request.current_user
    race.save(update_fields=["id_organizatora"])
    messages.success(request, "Uvezena trka je dodeljena vašem nalogu.")
    return redirect("organizator_dashboard")


@require_http_methods(["GET", "POST"])
@role_required(ULOGA_ORGANIZATOR)
def upravljaj_sektorima(request: HttpRequest, id_trke: int) -> HttpResponse:
    """Prikazuje i dodaje sektore jedne organizatorove trke."""

    race = get_object_or_404(
        Trka, pk=id_trke, id_organizatora=request.current_user
    )
    form = SektorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        sector = form.save(commit=False)
        sector.id_trke = race
        sector.slobodna_mesta = sector.ukupni_kapacitet
        sector.save()
        messages.success(request, "Sektor je dodat.")
        return redirect("upravljaj_sektorima", id_trke=race.pk)
    return render(
        request,
        "organizator/sektori.html",
        {"trka": race, "sektori": race.sektori.all(), "form": form},
    )


@require_http_methods(["GET", "POST"])
@role_required(ULOGA_ORGANIZATOR)
def izmeni_sektor(request: HttpRequest, id_sektora: int) -> HttpResponse:
    """Menja sektor uz očuvanje broja već prodatih karata."""

    sector = get_object_or_404(
        Sektor.objects.select_related("id_trke"),
        pk=id_sektora,
        id_trke__id_organizatora=request.current_user,
    )
    form = SektorForm(request.POST or None, instance=sector)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sektor je izmenjen.")
        return redirect("upravljaj_sektorima", id_trke=sector.id_trke_id)
    return render(
        request,
        "organizator/sektor_form.html",
        {"form": form, "sektor": sector},
    )


@require_GET
@role_required(ULOGA_ORGANIZATOR)
def proveri_naziv_trke(request: HttpRequest) -> JsonResponse:
    """AJAX provera naziva pomaže formi, ali server i dalje vrši punu validaciju."""

    name = request.GET.get("naziv", "").strip()
    exclude_id = request.GET.get("izuzmi")
    races = Trka.objects.filter(naziv_trke__iexact=name)
    if exclude_id and exclude_id.isdigit():
        races = races.exclude(pk=int(exclude_id))
    return JsonResponse(
        {
            "available": bool(name) and not races.exists(),
            "message": (
                "Naziv je dostupan."
                if name and not races.exists()
                else "Naziv je već u upotrebi."
            ),
        }
    )


@require_POST
@role_required(ULOGA_ORGANIZATOR)
def obrisi_trku(request: HttpRequest, id_trke: int) -> HttpResponse:
    """Briše trku samo kada ni jedan njen sektor nema rezervaciju."""

    race = get_object_or_404(
        Trka, pk=id_trke, id_organizatora=request.current_user
    )
    if Rezervacija.objects.filter(id_sektora__id_trke=race).exists():
        messages.error(request, "Trka sa postojećim rezervacijama ne može biti obrisana.")
    else:
        race.delete()
        messages.success(request, "Trka je obrisana.")
    return redirect("organizator_dashboard")


@require_POST
@role_required(ULOGA_ORGANIZATOR)
def obrisi_sektor(request: HttpRequest, id_sektora: int) -> HttpResponse:
    """Briše sektor bez rezervacija i proverava vlasništvo nad trkom."""

    sector = get_object_or_404(
        Sektor.objects.select_related("id_trke"),
        pk=id_sektora,
        id_trke__id_organizatora=request.current_user,
    )
    race_id = sector.id_trke_id
    if sector.rezervacije.exists():
        messages.error(request, "Sektor sa postojećim rezervacijama ne može biti obrisan.")
    else:
        sector.delete()
        messages.success(request, "Sektor je obrisan.")
    return redirect("upravljaj_sektorima", id_trke=race_id)
