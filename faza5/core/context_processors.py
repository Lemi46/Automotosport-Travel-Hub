# Autor: Milan Lemić 0323/2023;
"""Kontekst procesori za podatke o korisničkoj sesiji."""

from django.conf import settings

from .session_auth import get_session_user


def session_user(request):
    """Dodaje prijavljenog korisnika i demo režim u svaki template."""

    return {
        "session_user": get_session_user(request),
        "demo_mode": settings.DEMO_MODE,
    }
