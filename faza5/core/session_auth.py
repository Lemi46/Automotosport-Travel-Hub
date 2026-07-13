# Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;
"""Jednostavna autentifikacija zasnovana na tabeli Korisnik i Django sesiji."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from .constants import (
    STATUS_NALOGA_AKTIVNO,
    ULOGA_ADMINISTRATOR,
    ULOGA_HOTELIJER,
    ULOGA_KUPAC,
    ULOGA_ORGANIZATOR,
)
from .models import Korisnik

SESSION_USER_KEY = "id_korisnika"
SESSION_ROLE_KEY = "uloga"


def get_session_user(request: HttpRequest) -> Korisnik | None:
    """Vraća korisnika iz sesije ili ``None`` ako sesija više nije validna."""

    cached = getattr(request, "_automotosport_user", None)
    if cached is not None:
        return cached

    user_id = request.session.get(SESSION_USER_KEY)
    if not user_id:
        return None

    try:
        user = Korisnik.objects.get(pk=user_id)
    except Korisnik.DoesNotExist:
        request.session.flush()
        return None

    request._automotosport_user = user
    return user


def login_session(request: HttpRequest, user: Korisnik) -> None:
    """Rotira identifikator sesije i upisuje minimalne podatke korisnika."""

    request.session.cycle_key()
    request.session[SESSION_USER_KEY] = user.pk
    request.session[SESSION_ROLE_KEY] = user.uloga
    request.session["ime_korisnika"] = user.ime


def logout_session(request: HttpRequest) -> None:
    """Potpuno briše postojeću sesiju."""

    request.session.flush()


def redirect_name_for_role(role: str) -> str:
    """Vraća početnu rutu odgovarajuću ulozi."""

    return {
        ULOGA_KUPAC: "pretraga_trka",
        ULOGA_ORGANIZATOR: "organizator_dashboard",
        ULOGA_HOTELIJER: "partner_dashboard",
        ULOGA_ADMINISTRATOR: "admin_dashboard",
    }.get(role, "index")


def role_required(*allowed_roles: str) -> Callable:
    """Dekorator koji proverava prijavu, aktivan nalog i dozvoljenu ulogu."""

    def decorator(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
        """Kreira dekorator koji proverava prijavu i dozvoljene korisničke uloge."""

        @wraps(view_func)
        def wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
            """Proverava sesiju, status naloga i ulogu pre poziva zaštićenog kontrolera."""
            user = get_session_user(request)
            if user is None:
                messages.warning(request, "Prijavite se da biste pristupili ovoj stranici.")
                login_url = f"{reverse('auth')}?next={request.get_full_path()}"
                return redirect(login_url)

            if user.status_naloga != STATUS_NALOGA_AKTIVNO:
                logout_session(request)
                messages.error(request, "Vaš nalog je suspendovan.")
                return redirect("auth")

            if allowed_roles and user.uloga not in allowed_roles:
                messages.error(request, "Nemate ovlašćenje za traženu akciju.")
                return redirect(redirect_name_for_role(user.uloga))

            request.current_user = user
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
