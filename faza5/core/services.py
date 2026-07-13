# Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;
"""Transakcione poslovne operacije nezavisne od HTTP sloja."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from .constants import (
    SAMPIONATI,
    STATUS_NALOGA_AKTIVNO,
    STATUS_NALOGA_SUSPENDOVANO,
    STATUS_REZERVACIJE_AKTIVNA,
    STATUS_REZERVACIJE_KORPA,
    STATUS_REZERVACIJE_OTKAZANA,
    STATUS_REZERVACIJE_ZAVRSENA,
    SYSTEM_ORGANIZER_EMAIL,
    ULOGA_ADMINISTRATOR,
    ULOGA_KUPAC,
    ULOGA_ORGANIZATOR,
)
from .models import DigitalniVaucer, Korisnik, Rezervacija, Sektor, Smestaj, Trka


class BusinessRuleError(Exception):
    """Greška očekivane poslovne validacije koja se bezbedno prikazuje korisniku."""


class AvailabilityError(BusinessRuleError):
    """Nema dovoljne raspoloživosti u trenutku plaćanja."""


class ExternalSyncError(BusinessRuleError):
    """Eksterni servis nije dostupan ili je vratio neočekivane podatke."""


@dataclass(frozen=True)
class SyncResult:
    """Rezultat sinhronizacije jednog kalendara."""

    created: int
    updated: int
    skipped: int


@transaction.atomic
def create_cart_reservation(
    *, buyer: Korisnik, sector: Sektor, accommodation: Smestaj
) -> tuple[Rezervacija, bool]:
    """Kreira paket u korpi ili vraća već postojeću jednaku stavku."""

    if buyer.uloga != ULOGA_KUPAC:
        raise BusinessRuleError("Samo kupac može kreirati rezervaciju.")
    if sector.id_trke_id != accommodation.id_trke_id:
        raise BusinessRuleError("Sektor i smeštaj moraju pripadati istoj trci.")
    if sector.slobodna_mesta < 1 or accommodation.broj_slobodnih_soba < 1:
        raise AvailabilityError("Izabrani paket više nije raspoloživ.")
    if sector.id_trke.datum_odrzavanja < date.today():
        raise BusinessRuleError("Nije moguće rezervisati paket za završenu trku.")

    existing = Rezervacija.objects.filter(
        id_kupca=buyer,
        id_sektora=sector,
        id_smestaja=accommodation,
        status_rezervacije=STATUS_REZERVACIJE_KORPA,
    ).first()
    if existing:
        return existing, False

    # Šema nema trajanje boravka; paket zato koristi jednu kartu i jedno noćenje.
    total = sector.cena_karte + accommodation.cena_po_nocenju
    reservation = Rezervacija.objects.create(
        id_kupca=buyer,
        id_sektora=sector,
        id_smestaja=accommodation,
        ukupna_cena=total,
        status_rezervacije=STATUS_REZERVACIJE_KORPA,
    )
    return reservation, True


@transaction.atomic
def finalize_reservation(*, reservation_id: int, buyer: Korisnik) -> DigitalniVaucer:
    """Atomski proverava raspoloživost, naplaćuje paket i izdaje vaučer."""

    try:
        reservation = (
            Rezervacija.objects.select_for_update()
            .select_related("id_sektora__id_trke", "id_smestaja")
            .get(pk=reservation_id, id_kupca=buyer)
        )
    except Rezervacija.DoesNotExist as exc:
        raise BusinessRuleError("Rezervacija ne postoji.") from exc

    if reservation.status_rezervacije != STATUS_REZERVACIJE_KORPA:
        if reservation.status_rezervacije == STATUS_REZERVACIJE_AKTIVNA:
            try:
                return reservation.vaucer
            except DigitalniVaucer.DoesNotExist as exc:
                raise BusinessRuleError("Vaučer rezervacije nije pronađen.") from exc
        raise BusinessRuleError("Ovu rezervaciju nije moguće platiti.")

    sector = Sektor.objects.select_for_update().get(pk=reservation.id_sektora_id)
    accommodation = Smestaj.objects.select_for_update().get(
        pk=reservation.id_smestaja_id
    )

    if sector.id_trke_id != accommodation.id_trke_id:
        raise BusinessRuleError("Podaci paketa nisu konzistentni.")
    if sector.id_trke.datum_odrzavanja < date.today():
        raise BusinessRuleError("Trka je već završena.")
    if sector.slobodna_mesta < 1:
        raise AvailabilityError("U izabranom sektoru više nema slobodnih mesta.")
    if accommodation.broj_slobodnih_soba < 1:
        raise AvailabilityError("U izabranom smeštaju više nema slobodnih soba.")

    sector.slobodna_mesta -= 1
    accommodation.broj_slobodnih_soba -= 1
    sector.save(update_fields=["slobodna_mesta"])
    accommodation.save(update_fields=["broj_slobodnih_soba"])

    reservation.ukupna_cena = sector.cena_karte + accommodation.cena_po_nocenju
    reservation.status_rezervacije = STATUS_REZERVACIJE_AKTIVNA
    reservation.save(update_fields=["ukupna_cena", "status_rezervacije"])

    voucher, _ = DigitalniVaucer.objects.get_or_create(
        id_rezervacije=reservation,
        defaults={"qr_kod": uuid.uuid4().hex},
    )
    return voucher


@transaction.atomic
def cancel_reservation(*, reservation_id: int, buyer: Korisnik) -> Rezervacija:
    """Otkazuje korpu ili aktivnu rezervaciju i po potrebi vraća resurse."""

    try:
        reservation = (
            Rezervacija.objects.select_for_update()
            .select_related("id_sektora__id_trke", "id_smestaja")
            .get(pk=reservation_id, id_kupca=buyer)
        )
    except Rezervacija.DoesNotExist as exc:
        raise BusinessRuleError("Rezervacija ne postoji.") from exc

    if reservation.status_rezervacije in {
        STATUS_REZERVACIJE_OTKAZANA,
        STATUS_REZERVACIJE_ZAVRSENA,
    }:
        raise BusinessRuleError("Rezervacija više ne može da se otkaže.")
    if reservation.id_sektora.id_trke.datum_odrzavanja < date.today():
        raise BusinessRuleError("Rezervacija za završenu trku ne može da se otkaže.")

    if reservation.status_rezervacije == STATUS_REZERVACIJE_AKTIVNA:
        sector = Sektor.objects.select_for_update().get(pk=reservation.id_sektora_id)
        accommodation = Smestaj.objects.select_for_update().get(
            pk=reservation.id_smestaja_id
        )
        sector.slobodna_mesta = min(
            sector.ukupni_kapacitet, sector.slobodna_mesta + 1
        )
        accommodation.broj_slobodnih_soba += 1
        sector.save(update_fields=["slobodna_mesta"])
        accommodation.save(update_fields=["broj_slobodnih_soba"])

    reservation.status_rezervacije = STATUS_REZERVACIJE_OTKAZANA
    reservation.save(update_fields=["status_rezervacije"])
    return reservation


def mark_past_reservations_complete(today: date | None = None) -> int:
    """Označava plaćene rezervacije kao završene kada datum trke prođe."""

    cutoff = today or timezone.localdate()
    return Rezervacija.objects.filter(
        status_rezervacije=STATUS_REZERVACIJE_AKTIVNA,
        id_sektora__id_trke__datum_odrzavanja__lt=cutoff,
    ).update(status_rezervacije=STATUS_REZERVACIJE_ZAVRSENA)


@transaction.atomic
def suspend_user(*, user_id: int, acting_admin: Korisnik) -> Korisnik:
    """Suspenduje neadministratorski nalog i otkazuje otvorene kupčeve pakete."""

    if acting_admin.uloga != ULOGA_ADMINISTRATOR:
        raise BusinessRuleError("Samo administrator može suspendovati nalog.")
    try:
        user = Korisnik.objects.select_for_update().get(pk=user_id)
    except Korisnik.DoesNotExist as exc:
        raise BusinessRuleError("Korisnik ne postoji.") from exc
    if user.uloga == ULOGA_ADMINISTRATOR:
        raise BusinessRuleError("Administratorski nalog ne može biti suspendovan.")
    if user.status_naloga == STATUS_NALOGA_SUSPENDOVANO:
        return user

    if user.uloga == ULOGA_KUPAC:
        open_reservations = list(
            Rezervacija.objects.select_for_update()
            .filter(
                id_kupca=user,
                status_rezervacije__in=[
                    STATUS_REZERVACIJE_KORPA,
                    STATUS_REZERVACIJE_AKTIVNA,
                ],
            )
            .select_related("id_sektora", "id_smestaja")
        )
        for reservation in open_reservations:
            if reservation.status_rezervacije == STATUS_REZERVACIJE_AKTIVNA:
                sector = Sektor.objects.select_for_update().get(
                    pk=reservation.id_sektora_id
                )
                accommodation = Smestaj.objects.select_for_update().get(
                    pk=reservation.id_smestaja_id
                )
                sector.slobodna_mesta = min(
                    sector.ukupni_kapacitet, sector.slobodna_mesta + 1
                )
                accommodation.broj_slobodnih_soba += 1
                sector.save(update_fields=["slobodna_mesta"])
                accommodation.save(update_fields=["broj_slobodnih_soba"])
            reservation.status_rezervacije = STATUS_REZERVACIJE_OTKAZANA
            reservation.save(update_fields=["status_rezervacije"])

    user.status_naloga = STATUS_NALOGA_SUSPENDOVANO
    user.save(update_fields=["status_naloga"])
    return user


@transaction.atomic
def activate_user(*, user_id: int, acting_admin: Korisnik) -> Korisnik:
    """Ponovo aktivira nalog bez automatskog obnavljanja otkazanih rezervacija."""

    if acting_admin.uloga != ULOGA_ADMINISTRATOR:
        raise BusinessRuleError("Samo administrator može aktivirati nalog.")
    try:
        user = Korisnik.objects.select_for_update().get(pk=user_id)
    except Korisnik.DoesNotExist as exc:
        raise BusinessRuleError("Korisnik ne postoji.") from exc
    user.status_naloga = STATUS_NALOGA_AKTIVNO
    user.save(update_fields=["status_naloga"])
    return user


def _system_organizer() -> Korisnik:
    """Vraća tehničkog organizatora za trke uvezene sa eksternih servisa."""

    organizer, created = Korisnik.objects.get_or_create(
        email=SYSTEM_ORGANIZER_EMAIL,
        defaults={
            "ime": "Sistemski",
            "prezime": "Uvoz",
            "lozinka": make_password(uuid.uuid4().hex),
            "uloga": ULOGA_ORGANIZATOR,
            "status_naloga": STATUS_NALOGA_AKTIVNO,
        },
    )
    if not created and organizer.uloga != ULOGA_ORGANIZATOR:
        raise ExternalSyncError(
            "Sistemska e-mail adresa već pripada korisniku druge uloge."
        )
    return organizer


@dataclass(frozen=True)
class RaceData:
    """Normalizovani podaci trke spremni za upis u postojeću MySQL tabelu."""

    name: str
    circuit: str
    country: str
    race_date: date


def _clean_text(value: Any, max_length: int, fallback: str = "") -> str:
    """Normalizuje tekst i ograničava ga na dužinu odgovarajuće kolone."""

    text = " ".join(str(value or "").split()).strip() or fallback
    return text[:max_length]


def _parse_api_date(value: Any) -> date:
    """Čita ISO datum ili ISO datum-vreme koje vraćaju eksterni servisi."""

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value or "").strip()
    if not text:
        raise ValueError("Datum nije naveden.")

    # Sva tri izvora koriste ISO oblik; prvih deset znakova je YYYY-MM-DD.
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise ValueError("Datum nije u podržanom ISO formatu.") from exc


def _fetch_json(
    *,
    session: Any,
    url: str,
    timeout: int,
    source_name: str,
    params: dict[str, str] | None = None,
) -> Any:
    """Preuzima JSON i pretvara mrežne/JSON greške u poslovnu grešku."""

    request_kwargs: dict[str, Any] = {"timeout": timeout}
    if params is not None:
        request_kwargs["params"] = params

    try:
        response = session.get(url, **request_kwargs)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError, TypeError) as exc:
        raise ExternalSyncError(
            f"Konekcija sa izvorom za {source_name} nije uspela."
        ) from exc


@transaction.atomic
def _store_races(
    *, championship: str, races: list[RaceData], initially_skipped: int = 0
) -> SyncResult:
    """Atomski upisuje jedan kalendar, bez menjanja trka pravih organizatora."""

    supported_championships = {value for value, _label in SAMPIONATI}
    if championship not in supported_championships:
        raise ExternalSyncError(
            f"Šampionat {championship} nije dozvoljen postojećom šemom baze."
        )

    organizer = _system_organizer()
    created = 0
    updated = 0
    skipped = initially_skipped

    for item in races:
        race_name = _clean_text(item.name, 100)
        circuit = _clean_text(item.circuit, 100, "Staza nije navedena")
        country = _clean_text(item.country, 50, "Država nije navedena")
        if not race_name:
            skipped += 1
            continue

        race = (
            Trka.objects.select_for_update()
            .select_related("id_organizatora")
            .filter(
                naziv_trke=race_name,
                datum_odrzavanja=item.race_date,
                sampionat=championship,
            )
            .order_by("id_trke")
            .first()
        )
        if race is None:
            Trka.objects.create(
                id_organizatora=organizer,
                naziv_trke=race_name,
                staza=circuit,
                drzava=country,
                datum_odrzavanja=item.race_date,
                sampionat=championship,
            )
            created += 1
            continue

        # Ne prepisuje podatke događaja koji je preuzeo pravi organizator.
        if race.id_organizatora.email != SYSTEM_ORGANIZER_EMAIL:
            skipped += 1
            continue

        changed_fields: list[str] = []
        if race.staza != circuit:
            race.staza = circuit
            changed_fields.append("staza")
        if race.drzava != country:
            race.drzava = country
            changed_fields.append("drzava")

        if changed_fields:
            race.save(update_fields=changed_fields)
            updated += 1
        else:
            skipped += 1

    return SyncResult(created=created, updated=updated, skipped=skipped)


def _extract_f1_races(payload: Any) -> list[dict[str, Any]]:
    """Bezbedno čita Ergast/Jolpica oblik F1 kalendara."""

    try:
        races = payload["MRData"]["RaceTable"]["Races"]
    except (KeyError, TypeError) as exc:
        raise ExternalSyncError("F1 servis je vratio nepoznat format.") from exc
    if not isinstance(races, list):
        raise ExternalSyncError("F1 servis nije vratio listu trka.")
    return races


def sync_f1_races(*, session: Any = requests) -> SyncResult:
    """Sinhronizuje F1 kalendar preko Jolpica/Ergast izvora."""

    payload = _fetch_json(
        session=session,
        url=settings.F1_API_URL,
        timeout=settings.F1_API_TIMEOUT,
        source_name="F1",
    )

    normalized: list[RaceData] = []
    skipped = 0
    for item in _extract_f1_races(payload):
        try:
            normalized.append(
                RaceData(
                    name=_clean_text(item["raceName"], 100),
                    circuit=_clean_text(item["Circuit"]["circuitName"], 100),
                    country=_clean_text(
                        item["Circuit"]["Location"]["country"], 50
                    ),
                    race_date=_parse_api_date(item["date"]),
                )
            )
        except (KeyError, TypeError, ValueError):
            skipped += 1

    return _store_races(
        championship="F1", races=normalized, initially_skipped=skipped
    )


def _extract_motogp_list(
    payload: Any, key: str, description: str
) -> list[dict[str, Any]]:
    """Prihvata direktnu listu ili listu smeštenu pod zadatim ključem."""

    items = payload.get(key) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise ExternalSyncError(f"MotoGP servis nije vratio {description}.")
    return items


def _is_true(value: Any) -> bool:
    """Tumači tipične JSON prikaze logičke vrednosti."""

    return value is True or str(value).strip().lower() in {"1", "true", "yes"}


def _motogp_season_uuid(payload: Any) -> str:
    """Pronalazi UUID tekuće MotoGP sezone."""

    seasons = _extract_motogp_list(payload, "seasons", "listu sezona")
    current_year = timezone.localdate().year

    selected = next(
        (
            item
            for item in seasons
            if isinstance(item, dict) and str(item.get("year")) == str(current_year)
        ),
        None,
    )
    if selected is None:
        selected = next(
            (
                item
                for item in seasons
                if isinstance(item, dict) and _is_true(item.get("current"))
            ),
            None,
        )

    season_uuid = selected.get("id") if isinstance(selected, dict) else None
    if not season_uuid:
        raise ExternalSyncError("MotoGP servis nema podatke za tekuću sezonu.")
    return str(season_uuid)


def _motogp_event_identity(item: dict[str, Any]) -> str:
    """Vraća stabilan ključ za uklanjanje duplikata iz dva MotoGP odgovora."""

    event_id = item.get("id") or item.get("toad_api_uuid")
    if event_id:
        return str(event_id)
    name = item.get("sponsored_name") or item.get("name") or ""
    event_date = (
        item.get("date_start")
        or item.get("date")
        or item.get("start_date")
        or item.get("dateStart")
        or ""
    )
    return f"{name}|{event_date}"


def sync_motogp_races(*, session: Any = requests) -> SyncResult:
    """Sinhronizuje završene i predstojeće MotoGP događaje jednim postupkom."""

    seasons_payload = _fetch_json(
        session=session,
        url=settings.MOTOGP_SEASONS_API_URL,
        timeout=settings.MOTOGP_API_TIMEOUT,
        source_name="MotoGP",
    )
    season_uuid = _motogp_season_uuid(seasons_payload)

    events: list[dict[str, Any]] = []
    seen: set[str] = set()
    for is_finished in ("false", "true"):
        payload = _fetch_json(
            session=session,
            url=settings.MOTOGP_EVENTS_API_URL,
            timeout=settings.MOTOGP_API_TIMEOUT,
            source_name="MotoGP",
            params={"seasonUuid": season_uuid, "isFinished": is_finished},
        )
        for item in _extract_motogp_list(payload, "events", "listu događaja"):
            if not isinstance(item, dict):
                continue
            identity = _motogp_event_identity(item)
            if identity in seen:
                continue
            seen.add(identity)
            events.append(item)

    normalized: list[RaceData] = []
    skipped = 0
    for item in events:
        if _is_true(item.get("test")) or str(item.get("kind", "")).upper() == "TEST":
            skipped += 1
            continue

        try:
            circuit_data = item.get("circuit")
            country_data = item.get("country")
            circuit = (
                circuit_data.get("name")
                if isinstance(circuit_data, dict)
                else circuit_data
            )
            country = (
                country_data.get("name")
                if isinstance(country_data, dict)
                else country_data
            )
            normalized.append(
                RaceData(
                    name=_clean_text(
                        item.get("sponsored_name") or item.get("name"), 100
                    ),
                    circuit=_clean_text(
                        circuit or item.get("circuit_name"),
                        100,
                        "Staza nije navedena",
                    ),
                    country=_clean_text(
                        country or item.get("country_name"),
                        50,
                        "Država nije navedena",
                    ),
                    race_date=_parse_api_date(
                        item.get("date_start")
                        or item.get("date")
                        or item.get("start_date")
                        or item.get("dateStart")
                    ),
                )
            )
        except (TypeError, ValueError):
            skipped += 1

    return _store_races(
        championship="MotoGP", races=normalized, initially_skipped=skipped
    )


def _extract_sportsdb_events(payload: Any) -> list[dict[str, Any]]:
    """Bezbedno čita TheSportsDB odgovor za jednu sezonu."""

    if not isinstance(payload, dict) or "events" not in payload:
        raise ExternalSyncError("WSBK servis je vratio nepoznat format.")
    events = payload["events"]
    if events is None:
        return []
    if not isinstance(events, list):
        raise ExternalSyncError("WSBK servis nije vratio listu događaja.")
    return events


def sync_wsbk_races(*, session: Any = requests) -> SyncResult:
    """Sinhronizuje WSBK kalendar preko TheSportsDB izvora."""

    payload = _fetch_json(
        session=session,
        url=settings.SPORTSDB_API_URL,
        timeout=settings.SPORTSDB_API_TIMEOUT,
        source_name="WSBK",
        params={
            "id": str(settings.SPORTSDB_WSBK_LEAGUE_ID),
            "s": str(timezone.localdate().year),
        },
    )

    normalized: list[RaceData] = []
    skipped = 0
    for item in _extract_sportsdb_events(payload):
        if not isinstance(item, dict):
            skipped += 1
            continue

        try:
            normalized.append(
                RaceData(
                    name=_clean_text(
                        item.get("strEvent") or item.get("strEventAlternate"), 100
                    ),
                    circuit=_clean_text(
                        item.get("strVenue"), 100, "Staza nije navedena"
                    ),
                    country=_clean_text(
                        item.get("strCountry"), 50, "Država nije navedena"
                    ),
                    race_date=_parse_api_date(
                        item.get("dateEvent") or item.get("strTimestamp")
                    ),
                )
            )
        except (TypeError, ValueError):
            skipped += 1

    return _store_races(
        championship="WSBK", races=normalized, initially_skipped=skipped
    )


def sync_all_motorsports(*, session: Any = requests) -> dict[str, Any]:
    """Jednim pozivom sinhronizuje F1, MotoGP i WSBK.

    Greška jednog izvora ne zaustavlja preostale sinhronizacije, pa administrator
    dobija poseban rezultat za svaki šampionat koji postoji u bazi.
    """

    handlers = (
        ("F1", sync_f1_races),
        ("MotoGP", sync_motogp_races),
        ("WSBK", sync_wsbk_races),
    )
    results: dict[str, Any] = {}

    for championship, handler in handlers:
        try:
            results[championship] = handler(session=session)
        except ExternalSyncError as exc:
            results[championship] = {"error": str(exc)}
        except Exception:
            # Poslednja zaštita: kvar jednog izvora ne sme prekinuti druga dva.
            results[championship] = {
                "error": "Neočekivana greška tokom sinhronizacije."
            }

    return results


def paid_reservations() -> QuerySet[Rezervacija]:
    """Centralizovan skup rezervacija koje predstavljaju ostvarenu prodaju."""

    return Rezervacija.objects.filter(
        status_rezervacije__in=[
            STATUS_REZERVACIJE_AKTIVNA,
            STATUS_REZERVACIJE_ZAVRSENA,
        ]
    )
