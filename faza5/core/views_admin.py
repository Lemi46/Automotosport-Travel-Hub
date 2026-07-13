# Autor: Marko Mandić 0625/2023;
"""Administracija naloga, statistika i integracija kalendara trka."""

from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .constants import ULOGA_ADMINISTRATOR
from .models import Korisnik, Trka
from .services import (
    BusinessRuleError,
    activate_user,
    mark_past_reservations_complete,
    paid_reservations,
    suspend_user,
    sync_all_motorsports,
)
from .session_auth import role_required


@require_GET
@role_required(ULOGA_ADMINISTRATOR)
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    """Prikazuje korisnike, osnovne brojače i upravljanje sinhronizacijom."""

    mark_past_reservations_complete()
    users = Korisnik.objects.all().order_by("uloga", "prezime", "ime")
    return render(
        request,
        "admin/admin_panel.html",
        {
            "korisnici": users,
            "broj_trka": Trka.objects.count(),
            "broj_korisnika": users.count(),
            "broj_prodaja": paid_reservations().count(),
        },
    )


@require_GET
@role_required(ULOGA_ADMINISTRATOR)
def api_statistika(request: HttpRequest) -> JsonResponse:
    """AJAX statistika plaćenih paketa za izabrani vremenski period."""

    period = request.GET.get("period", "sve")
    reservations = paid_reservations()
    now = timezone.now()
    if period == "mesec":
        reservations = reservations.filter(
            datum_kreiranja__gte=now - timedelta(days=30)
        )
    elif period == "godina":
        reservations = reservations.filter(
            datum_kreiranja__gte=now - timedelta(days=365)
        )
    elif period != "sve":
        return JsonResponse({"error": "Nepoznat period."}, status=400)

    revenue = reservations.aggregate(total=Sum("ukupna_cena"))["total"] or 0
    return JsonResponse(
        {
            "zarada": float(revenue),
            "prodato": reservations.count(),
            "period": period,
        }
    )


@require_POST
@role_required(ULOGA_ADMINISTRATOR)
def suspenduj_korisnika(request: HttpRequest, id_korisnika: int) -> HttpResponse:
    """Suspenduje nalog i primenjuje pravila nad otvorenim kupčevim paketima."""

    try:
        user = suspend_user(
            user_id=id_korisnika, acting_admin=request.current_user
        )
    except BusinessRuleError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"Nalog {user.email} je suspendovan.")
    return redirect("admin_dashboard")


@require_POST
@role_required(ULOGA_ADMINISTRATOR)
def aktiviraj_korisnika(request: HttpRequest, id_korisnika: int) -> HttpResponse:
    """Ponovo aktivira izabrani korisnički nalog."""

    try:
        user = activate_user(user_id=id_korisnika, acting_admin=request.current_user)
    except BusinessRuleError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"Nalog {user.email} je aktiviran.")
    return redirect("admin_dashboard")


@require_POST
@role_required(ULOGA_ADMINISTRATOR)
def sinhronizuj_trke(request: HttpRequest) -> HttpResponse:
    """Jednim zahtevom sinhronizuje F1, MotoGP i WSBK kalendare."""

    for sampionat, result in sync_all_motorsports().items():
        if isinstance(result, dict) and "error" in result:
            messages.error(request, f"{sampionat}: {result['error']}")
            continue

        messages.success(
            request,
            f"{sampionat} sinhronizacija završena: "
            f"novih {result.created}, izmenjenih {result.updated}, "
            f"preskočenih {result.skipped}."
        )

    return redirect("admin_dashboard")
