# Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;
"""Unit testovi modela i serverskih formi."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from core.forms import PackageForm, RegistrationForm, SektorForm, TrkaForm
from core.models import Korisnik

from .factories import package, user


class ModelAndFormTests(TestCase):
    """Validira pomoćna svojstva i najvažnija ograničenja formi."""

    def test_sector_sold_property(self):
        """Proverava scenario: sector sold property."""
        _race, sector, _accommodation, _organizer, _hotelier = package(seats=7)
        self.assertEqual(sector.broj_prodatih, 3)

    def test_reservation_total_assumption_is_ticket_plus_one_night(self):
        """Proverava scenario: reservation total assumption is ticket plus one night."""
        _race, sector, accommodation, _organizer, _hotelier = package()
        self.assertEqual(sector.cena_karte + accommodation.cena_po_nocenju, Decimal("180.00"))

    def test_registration_rejects_duplicate_email_case_insensitively(self):
        """Proverava scenario: registration rejects duplicate email case insensitively."""
        user(email="postoji@test.rs")
        form = RegistrationForm(
            data={
                "uloga": "Kupac",
                "ime": "Ana",
                "prezime": "Anić",
                "email": "POSTOJI@test.rs",
                "lozinka": "DobraLozinka123!",
                "potvrda_lozinke": "DobraLozinka123!",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_registration_rejects_mismatched_passwords(self):
        """Proverava scenario: registration rejects mismatched passwords."""
        form = RegistrationForm(
            data={
                "uloga": "Kupac",
                "ime": "Ana",
                "prezime": "Anić",
                "email": "novi@test.rs",
                "lozinka": "DobraLozinka123!",
                "potvrda_lozinke": "DrugaLozinka123!",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("potvrda_lozinke", form.errors)

    def test_race_form_rejects_exact_duplicate(self):
        """Proverava scenario: race form rejects exact duplicate."""
        race, _sector, _accommodation, _organizer, _hotelier = package()
        form = TrkaForm(
            data={
                "naziv_trke": race.naziv_trke,
                "staza": "Druga staza",
                "drzava": "Srbija",
                "datum_odrzavanja": race.datum_odrzavanja.isoformat(),
                "sampionat": race.sampionat,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())

    def test_sector_form_preserves_sold_count_when_capacity_changes(self):
        """Proverava scenario: sector form preserves sold count when capacity changes."""
        _race, sector, _accommodation, _organizer, _hotelier = package(seats=6)
        form = SektorForm(
            data={
                "naziv_sektora": sector.naziv_sektora,
                "ukupni_kapacitet": 15,
                "cena_karte": "110.00",
            },
            instance=sector,
        )
        self.assertTrue(form.is_valid(), form.errors)
        updated = form.save()
        self.assertEqual(updated.broj_prodatih, 4)
        self.assertEqual(updated.slobodna_mesta, 11)

    def test_sector_form_rejects_capacity_below_sold_count(self):
        """Proverava scenario: sector form rejects capacity below sold count."""
        _race, sector, _accommodation, _organizer, _hotelier = package(seats=3)
        form = SektorForm(
            data={
                "naziv_sektora": sector.naziv_sektora,
                "ukupni_kapacitet": 6,
                "cena_karte": "110.00",
            },
            instance=sector,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("ukupni_kapacitet", form.errors)

    def test_package_form_lists_only_available_items_for_same_race(self):
        """Proverava scenario: package form lists only available items for same race."""
        race, sector, accommodation, _organizer, _hotelier = package()
        other_race, other_sector, other_accommodation, *_ = package()
        form = PackageForm(race=race)
        self.assertIn(sector, form.fields["id_sektora"].queryset)
        self.assertIn(accommodation, form.fields["id_smestaja"].queryset)
        self.assertNotIn(other_sector, form.fields["id_sektora"].queryset)
        self.assertNotIn(other_accommodation, form.fields["id_smestaja"].queryset)
        self.assertNotEqual(race.pk, other_race.pk)
