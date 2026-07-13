# Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;
"""Unit testovi transakcionih servisa i spoljne integracije."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.utils import timezone

from core.constants import (
    STATUS_REZERVACIJE_AKTIVNA,
    STATUS_REZERVACIJE_KORPA,
    STATUS_REZERVACIJE_OTKAZANA,
    STATUS_REZERVACIJE_ZAVRSENA,
)
from core.models import DigitalniVaucer, Rezervacija, Trka
from core.services import (
    AvailabilityError,
    ExternalSyncError,
    SyncResult,
    cancel_reservation,
    create_cart_reservation,
    finalize_reservation,
    mark_past_reservations_complete,
    suspend_user,
    sync_all_motorsports,
    sync_f1_races,
    sync_motogp_races,
    sync_wsbk_races,
)

from .factories import ULOGA_ADMINISTRATOR, package, user


class ReservationServiceTests(TestCase):
    """Proverava promenu statusa i kapaciteta kroz ceo životni ciklus."""

    def setUp(self):
        """Priprema izolovane podatke i klijente potrebne za svaki test."""
        self.buyer = user()
        self.race, self.sector, self.accommodation, *_ = package(seats=2, rooms=2)

    def test_create_cart_does_not_decrement_inventory(self):
        """Proverava scenario: create cart does not decrement inventory."""
        reservation, created = create_cart_reservation(
            buyer=self.buyer, sector=self.sector, accommodation=self.accommodation
        )
        self.assertTrue(created)
        self.assertEqual(reservation.status_rezervacije, STATUS_REZERVACIJE_KORPA)
        self.sector.refresh_from_db()
        self.accommodation.refresh_from_db()
        self.assertEqual(self.sector.slobodna_mesta, 2)
        self.assertEqual(self.accommodation.broj_slobodnih_soba, 2)

    def test_duplicate_cart_item_is_not_created_twice(self):
        """Proverava scenario: duplicate cart item is not created twice."""
        first, first_created = create_cart_reservation(
            buyer=self.buyer, sector=self.sector, accommodation=self.accommodation
        )
        second, second_created = create_cart_reservation(
            buyer=self.buyer, sector=self.sector, accommodation=self.accommodation
        )
        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Rezervacija.objects.count(), 1)

    def test_finalize_decrements_inventory_and_creates_voucher(self):
        """Proverava scenario: finalize decrements inventory and creates voucher."""
        reservation, _ = create_cart_reservation(
            buyer=self.buyer, sector=self.sector, accommodation=self.accommodation
        )
        voucher = finalize_reservation(reservation_id=reservation.pk, buyer=self.buyer)
        reservation.refresh_from_db()
        self.sector.refresh_from_db()
        self.accommodation.refresh_from_db()
        self.assertEqual(reservation.status_rezervacije, STATUS_REZERVACIJE_AKTIVNA)
        self.assertEqual(reservation.ukupna_cena, Decimal("180.00"))
        self.assertEqual(self.sector.slobodna_mesta, 1)
        self.assertEqual(self.accommodation.broj_slobodnih_soba, 1)
        self.assertEqual(voucher.id_rezervacije, reservation)

    def test_finalize_is_idempotent_after_success(self):
        """Proverava scenario: finalize is idempotent after success."""
        reservation, _ = create_cart_reservation(
            buyer=self.buyer, sector=self.sector, accommodation=self.accommodation
        )
        first = finalize_reservation(reservation_id=reservation.pk, buyer=self.buyer)
        second = finalize_reservation(reservation_id=reservation.pk, buyer=self.buyer)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(DigitalniVaucer.objects.count(), 1)

    def test_finalize_rolls_back_when_no_room_is_available(self):
        """Proverava scenario: finalize rolls back when no room is available."""
        reservation, _ = create_cart_reservation(
            buyer=self.buyer, sector=self.sector, accommodation=self.accommodation
        )
        self.accommodation.broj_slobodnih_soba = 0
        self.accommodation.save(update_fields=["broj_slobodnih_soba"])
        with self.assertRaises(AvailabilityError):
            finalize_reservation(reservation_id=reservation.pk, buyer=self.buyer)
        reservation.refresh_from_db()
        self.sector.refresh_from_db()
        self.assertEqual(reservation.status_rezervacije, STATUS_REZERVACIJE_KORPA)
        self.assertEqual(self.sector.slobodna_mesta, 2)

    def test_cancel_active_reservation_restores_inventory(self):
        """Proverava scenario: cancel active reservation restores inventory."""
        reservation, _ = create_cart_reservation(
            buyer=self.buyer, sector=self.sector, accommodation=self.accommodation
        )
        finalize_reservation(reservation_id=reservation.pk, buyer=self.buyer)
        cancel_reservation(reservation_id=reservation.pk, buyer=self.buyer)
        reservation.refresh_from_db()
        self.sector.refresh_from_db()
        self.accommodation.refresh_from_db()
        self.assertEqual(reservation.status_rezervacije, STATUS_REZERVACIJE_OTKAZANA)
        self.assertEqual(self.sector.slobodna_mesta, 2)
        self.assertEqual(self.accommodation.broj_slobodnih_soba, 2)

    def test_past_active_reservation_is_marked_completed(self):
        """Proverava scenario: past active reservation is marked completed."""
        race, sector, accommodation, *_ = package(days=-2)
        reservation = Rezervacija.objects.create(
            id_kupca=self.buyer,
            id_sektora=sector,
            id_smestaja=accommodation,
            ukupna_cena=Decimal("180.00"),
            status_rezervacije=STATUS_REZERVACIJE_AKTIVNA,
        )
        changed = mark_past_reservations_complete(today=date.today())
        reservation.refresh_from_db()
        self.assertEqual(changed, 1)
        self.assertEqual(reservation.status_rezervacije, STATUS_REZERVACIJE_ZAVRSENA)

    def test_suspending_buyer_cancels_and_restores_active_purchase(self):
        """Proverava scenario: suspending buyer cancels and restores active purchase."""
        reservation, _ = create_cart_reservation(
            buyer=self.buyer, sector=self.sector, accommodation=self.accommodation
        )
        finalize_reservation(reservation_id=reservation.pk, buyer=self.buyer)
        admin = user(role=ULOGA_ADMINISTRATOR)
        suspend_user(user_id=self.buyer.pk, acting_admin=admin)
        self.buyer.refresh_from_db()
        reservation.refresh_from_db()
        self.sector.refresh_from_db()
        self.assertEqual(self.buyer.status_naloga, "Suspendovano")
        self.assertEqual(reservation.status_rezervacije, STATUS_REZERVACIJE_OTKAZANA)
        self.assertEqual(self.sector.slobodna_mesta, 2)


class ExternalSyncTests(TestCase):
    """Proverava sinhronizaciju sva tri šampionata bez stvarnih mrežnih poziva."""

    @staticmethod
    def _response(payload):
        """Pravi mock HTTP odgovor sa zadatim JSON sadržajem."""

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = payload
        return response

    @override_settings(F1_API_URL="https://example.test/f1/current.json")
    def test_f1_sync_creates_and_then_skips_same_race(self):
        """Ponovljeni F1 uvoz ne pravi duplikat iste trke."""

        payload = {
            "MRData": {
                "RaceTable": {
                    "Races": [
                        {
                            "raceName": "Test Grand Prix",
                            "date": (
                                timezone.localdate() + timedelta(days=10)
                            ).isoformat(),
                            "Circuit": {
                                "circuitName": "Test Circuit",
                                "Location": {"country": "Testland"},
                            },
                        }
                    ]
                }
            }
        }
        session = Mock()
        session.get.return_value = self._response(payload)

        first = sync_f1_races(session=session)
        second = sync_f1_races(session=session)

        self.assertEqual(first.created, 1)
        self.assertEqual(second.skipped, 1)
        self.assertEqual(Trka.objects.filter(sampionat="F1").count(), 1)

    def test_f1_sync_rejects_unknown_payload(self):
        """Nepoznat F1 format se prijavljuje kao kontrolisana greška."""

        session = Mock()
        session.get.return_value = self._response({"unexpected": True})

        with self.assertRaises(ExternalSyncError):
            sync_f1_races(session=session)

    @override_settings(
        MOTOGP_SEASONS_API_URL="https://example.test/motogp/seasons",
        MOTOGP_EVENTS_API_URL="https://example.test/motogp/events",
    )
    def test_motogp_sync_combines_finished_and_upcoming_events(self):
        """MotoGP uvoz spaja oba API odgovora i preskače test događaje."""

        year = timezone.localdate().year
        season_uuid = "season-current"
        seasons = [{"id": season_uuid, "year": year, "current": True}]
        upcoming = [
            {
                "id": "event-upcoming",
                "sponsored_name": "Upcoming MotoGP",
                "date_start": f"{year}-09-20T08:00:00+02:00",
                "circuit": {"name": "Upcoming Circuit"},
                "country": {"name": "Spain"},
                "test": False,
                "kind": "GP",
            },
            {
                "id": "official-test",
                "sponsored_name": "Official Test",
                "date_start": f"{year}-10-01T08:00:00+02:00",
                "circuit": {"name": "Test Circuit"},
                "country": {"name": "Spain"},
                "test": True,
                "kind": "TEST",
            },
        ]
        finished = [
            {
                "id": "event-finished",
                "sponsored_name": "Finished MotoGP",
                "date_start": f"{year}-03-15T08:00:00+01:00",
                "circuit": {"name": "Finished Circuit"},
                "country": {"name": "Portugal"},
                "test": False,
                "kind": "GP",
            },
            upcoming[0],  # API odgovori mogu preklopiti događaj; mora ostati jedan.
        ]
        session = Mock()
        session.get.side_effect = [
            self._response(seasons),
            self._response(upcoming),
            self._response(finished),
        ]

        result = sync_motogp_races(session=session)

        self.assertEqual(result, SyncResult(created=2, updated=0, skipped=1))
        self.assertEqual(Trka.objects.filter(sampionat="MotoGP").count(), 2)
        self.assertEqual(session.get.call_count, 3)
        first_events_call = session.get.call_args_list[1]
        second_events_call = session.get.call_args_list[2]
        self.assertEqual(
            first_events_call.kwargs["params"],
            {"seasonUuid": season_uuid, "isFinished": "false"},
        )
        self.assertEqual(
            second_events_call.kwargs["params"],
            {"seasonUuid": season_uuid, "isFinished": "true"},
        )

    @override_settings(
        SPORTSDB_API_URL="https://example.test/wsbk/eventsseason.php",
        SPORTSDB_WSBK_LEAGUE_ID="4454",
    )
    def test_wsbk_sync_imports_valid_event_and_skips_bad_date(self):
        """WSBK uvoz koristi samo validne događaje iz sezonskog odgovora."""

        year = timezone.localdate().year
        payload = {
            "events": [
                {
                    "strEvent": "WSBK Test Round",
                    "strVenue": "Test Raceway",
                    "strCountry": "Italy",
                    "dateEvent": f"{year}-08-17",
                },
                {
                    "strEvent": "Broken WSBK Round",
                    "strVenue": "Unknown Raceway",
                    "strCountry": "France",
                    "dateEvent": "not-a-date",
                },
            ]
        }
        session = Mock()
        session.get.return_value = self._response(payload)

        result = sync_wsbk_races(session=session)

        self.assertEqual(result, SyncResult(created=1, updated=0, skipped=1))
        imported = Trka.objects.get(sampionat="WSBK")
        self.assertEqual(imported.naziv_trke, "WSBK Test Round")
        self.assertEqual(imported.staza, "Test Raceway")
        self.assertEqual(
            session.get.call_args.kwargs["params"],
            {"id": "4454", "s": str(year)},
        )

    def test_batch_sync_continues_when_one_championship_fails(self):
        """Greška MotoGP izvora ne sprečava F1 i WSBK sinhronizaciju."""

        session = Mock()
        with (
            patch("core.services.sync_f1_races") as f1_sync,
            patch("core.services.sync_motogp_races") as motogp_sync,
            patch("core.services.sync_wsbk_races") as wsbk_sync,
        ):
            f1_sync.return_value = SyncResult(created=2, updated=0, skipped=1)
            motogp_sync.side_effect = ExternalSyncError("MotoGP nije dostupan.")
            wsbk_sync.return_value = SyncResult(created=3, updated=1, skipped=0)

            results = sync_all_motorsports(session=session)

        self.assertEqual(list(results), ["F1", "MotoGP", "WSBK"])
        self.assertEqual(results["F1"].created, 2)
        self.assertEqual(results["MotoGP"], {"error": "MotoGP nije dostupan."})
        self.assertEqual(results["WSBK"].updated, 1)
        f1_sync.assert_called_once_with(session=session)
        motogp_sync.assert_called_once_with(session=session)
        wsbk_sync.assert_called_once_with(session=session)

