# Autor:Marko Mandić 2023/0625;
"""Upravljanje agregiranim smeštajem prijavljenog hotelijera."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .constants import ULOGA_HOTELIJER
from .forms import SmestajForm
from .models import Smestaj
from .session_auth import role_required


@require_http_methods(["GET", "POST"])
@role_required(ULOGA_HOTELIJER)
def partner_dashboard(request: HttpRequest) -> HttpResponse:
    """Prikazuje smeštaje korisnika i formu za dodavanje novog zapisa."""

    form = SmestajForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        accommodation = form.save(commit=False)
        accommodation.id_hotelijera = request.current_user
        accommodation.save()
        messages.success(request, "Smeštaj je dodat.")
        return redirect("partner_dashboard")

    accommodations = Smestaj.objects.filter(
        id_hotelijera=request.current_user
    ).select_related("id_trke")
    return render(
        request,
        "hotelijer/partner_panel.html",
        {"smestaji": accommodations, "form": form},
    )


@require_http_methods(["GET", "POST"])
@role_required(ULOGA_HOTELIJER)
def izmeni_smestaj(request: HttpRequest, id_smestaja: int) -> HttpResponse:
    """Menja smeštaj koji pripada prijavljenom hotelijeru."""

    accommodation = get_object_or_404(
        Smestaj,
        pk=id_smestaja,
        id_hotelijera=request.current_user,
    )
    form = SmestajForm(request.POST or None, instance=accommodation)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Smeštaj je izmenjen.")
        return redirect("partner_dashboard")
    return render(
        request,
        "hotelijer/smestaj_form.html",
        {"form": form, "smestaj": accommodation},
    )


@require_POST
@role_required(ULOGA_HOTELIJER)
def obrisi_smestaj(request: HttpRequest, id_smestaja: int) -> HttpResponse:
    """Briše smeštaj samo ako nema rezervacija koje ga referenciraju."""

    accommodation = get_object_or_404(
        Smestaj,
        pk=id_smestaja,
        id_hotelijera=request.current_user,
    )
    if accommodation.rezervacije.exists():
        messages.error(
            request, "Smeštaj sa postojećim rezervacijama ne može biti obrisan."
        )
    else:
        accommodation.delete()
        messages.success(request, "Smeštaj je obrisan.")
    return redirect("partner_dashboard")
