# Autor: Milan Lemić 0323/2023;
"""Registracija, prijava i odjava korisnika."""

from __future__ import annotations

import time

from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from .constants import STATUS_NALOGA_AKTIVNO
from .forms import LoginForm, RegistrationForm
from .models import Korisnik
from .session_auth import (
    get_session_user,
    login_session,
    logout_session,
    redirect_name_for_role,
)

MAX_LOGIN_FAILURES = 5
LOCK_SECONDS = 60


def _password_matches(raw_password: str, stored_password: str) -> bool:
    """Podržava savremeni hash i jednokratnu migraciju starog tekstualnog unosa."""

    try:
        if check_password(raw_password, stored_password):
            return True
    except (ValueError, TypeError):
        pass
    return constant_time_compare(raw_password, stored_password)


def _safe_next(request: HttpRequest) -> str | None:
    """Vraća lokalnu povratnu putanju bez mogućnosti otvorenog preusmerenja."""

    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target
    return None


@require_http_methods(["GET", "POST"])
def prijava_registracija(request: HttpRequest) -> HttpResponse:
    """Obrađuje obe forme na jednoj strani prema SSU 1 i SSU 10."""

    current = get_session_user(request)
    if request.method == "GET" and current is not None:
        return redirect(redirect_name_for_role(current.uloga))

    login_form = LoginForm(prefix="login")
    registration_form = RegistrationForm(prefix="registration")
    action = request.POST.get("akcija")

    if request.method == "POST" and action == "registracija":
        registration_form = RegistrationForm(request.POST, prefix="registration")
        if registration_form.is_valid():
            data = registration_form.cleaned_data
            Korisnik.objects.create(
                ime=data["ime"].strip(),
                prezime=data["prezime"].strip(),
                email=data["email"],
                lozinka=make_password(data["lozinka"]),
                uloga=data["uloga"],
                status_naloga=STATUS_NALOGA_AKTIVNO,
            )
            messages.success(
                request, "Nalog je uspešno kreiran. Sada se možete prijaviti."
            )
            return redirect(f"{reverse('auth')}#prijava")

    if request.method == "POST" and action == "prijava":
        login_form = LoginForm(request.POST, prefix="login")
        now = int(time.time())
        lock_until = int(request.session.get("login_lock_until", 0))
        if lock_until > now:
            login_form.add_error(
                None,
                f"Previše neuspešnih pokušaja. Pokušajte ponovo za {lock_until - now} s.",
            )
        elif login_form.is_valid():
            email = login_form.cleaned_data["email"]
            password = login_form.cleaned_data["lozinka"]
            user = Korisnik.objects.filter(email__iexact=email).first()
            if user is None or not _password_matches(password, user.lozinka):
                failures = int(request.session.get("login_failures", 0)) + 1
                request.session["login_failures"] = failures
                if failures >= MAX_LOGIN_FAILURES:
                    request.session["login_lock_until"] = now + LOCK_SECONDS
                    request.session["login_failures"] = 0
                    login_form.add_error(
                        None,
                        "Previše neuspešnih pokušaja. Prijava je privremeno zaključana.",
                    )
                else:
                    login_form.add_error(
                        None,
                        f"Pogrešan e-mail ili lozinka. Preostalo pokušaja: "
                        f"{MAX_LOGIN_FAILURES - failures}.",
                    )
            elif user.status_naloga != STATUS_NALOGA_AKTIVNO:
                login_form.add_error(None, "Ovaj nalog je suspendovan.")
            else:
                # Stare demo lozinke u čistom tekstu se odmah pretvaraju u hash.
                if not user.lozinka.startswith(("pbkdf2_", "argon2$", "bcrypt")):
                    user.lozinka = make_password(password)
                    user.save(update_fields=["lozinka"])
                request.session.pop("login_failures", None)
                request.session.pop("login_lock_until", None)
                login_session(request, user)
                messages.success(request, f"Dobro došli, {user.ime}.")
                return redirect(_safe_next(request) or redirect_name_for_role(user.uloga))

    return render(
        request,
        "auth.html",
        {
            "login_form": login_form,
            "registration_form": registration_form,
            "next_path": _safe_next(request) or "",
        },
    )


@require_POST
def odjava(request: HttpRequest) -> HttpResponse:
    """Odjavljuje korisnika i rotira/uklanja sesiju."""

    logout_session(request)
    messages.info(request, "Uspešno ste se odjavili.")
    return redirect("index")
