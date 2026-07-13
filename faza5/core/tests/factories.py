# Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;
"""Male fabričke funkcije za izolovane test podatke."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.test import Client
from django.utils import timezone

from core.constants import (
    ULOGA_ADMINISTRATOR,
    ULOGA_HOTELIJER,
    ULOGA_KUPAC,
    ULOGA_ORGANIZATOR,
)
from core.models import Korisnik, Sektor, Smestaj, Trka


def user(*, role: str = ULOGA_KUPAC, email: str | None = None) -> Korisnik:
    """Kreira aktivnog korisnika zadate uloge sa poznatom lozinkom."""

    email = email or f"{role.lower()}-{Korisnik.objects.count()}@test.rs"
    return Korisnik.objects.create(
        ime="Test",
        prezime=role,
        email=email,
        lozinka=make_password("Test12345!"),
        uloga=role,
        status_naloga="Aktivno",
    )


def package(*, days: int = 30, seats: int = 5, rooms: int = 5):
    """Kreira organizatora, hotelijera, trku, sektor i smeštaj."""

    organizer = user(role=ULOGA_ORGANIZATOR)
    hotelier = user(role=ULOGA_HOTELIJER)
    race = Trka.objects.create(
        id_organizatora=organizer,
        naziv_trke=f"Test trka {Trka.objects.count()}",
        staza="Test staza",
        drzava="Srbija",
        datum_odrzavanja=timezone.localdate() + timedelta(days=days),
        sampionat="F1",
    )
    sector = Sektor.objects.create(
        id_trke=race,
        naziv_sektora="Tribina A",
        ukupni_kapacitet=10,
        slobodna_mesta=seats,
        cena_karte=Decimal("100.00"),
    )
    accommodation = Smestaj.objects.create(
        id_hotelijera=hotelier,
        id_trke=race,
        naziv_smestaja="Test hotel",
        lokacija="Centar",
        udaljenost_od_staze=Decimal("3.50"),
        broj_slobodnih_soba=rooms,
        cena_po_nocenju=Decimal("80.00"),
    )
    return race, sector, accommodation, organizer, hotelier


def logged_client(current_user: Korisnik) -> Client:
    """Vraća test klijent sa sesijom kompatibilnom sa aplikacijom."""

    client = Client()
    session = client.session
    session["id_korisnika"] = current_user.pk
    session["uloga"] = current_user.uloga
    session["ime_korisnika"] = current_user.ime
    session.save()
    return client


__all__ = [
    "user",
    "package",
    "logged_client",
    "ULOGA_ADMINISTRATOR",
    "ULOGA_HOTELIJER",
    "ULOGA_KUPAC",
    "ULOGA_ORGANIZATOR",
]
