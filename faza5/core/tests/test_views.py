# Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;
"""Funkcionalni HTTP testovi ključnih korisničkih tokova."""

from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from core.constants import (
    STATUS_REZERVACIJE_AKTIVNA,
    STATUS_REZERVACIJE_KORPA,
)
from core.models import DigitalniVaucer, Korisnik, Rezervacija, Smestaj, Trka

from .factories import (
    ULOGA_ADMINISTRATOR,
    ULOGA_HOTELIJER,
    ULOGA_ORGANIZATOR,
    logged_client,
    package,
    user,
)


class AuthenticationViewTests(TestCase):
    """Testira registraciju, prijavu i zaštitu sesije."""

    def test_registration_hashes_password(self):
        """Proverava scenario: registration hashes password."""
        response = self.client.post(
            reverse("auth"),
            {
                "akcija": "registracija",
                "registration-uloga": "Kupac",
                "registration-ime": "Nova",
                "registration-prezime": "Kupac",
                "registration-email": "nova@test.rs",
                "registration-lozinka": "DobraLozinka123!",
                "registration-potvrda_lozinke": "DobraLozinka123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        created = Korisnik.objects.get(email="nova@test.rs")
        self.assertNotEqual(created.lozinka, "DobraLozinka123!")
        self.assertTrue(created.lozinka.startswith("pbkdf2_"))

    def test_login_redirects_to_role_dashboard(self):
        """Proverava scenario: login redirects to role dashboard."""
        current = user(email="prijava@test.rs")
        response = self.client.post(
            reverse("auth"),
            {
                "akcija": "prijava",
                "login-email": current.email,
                "login-lozinka": "Test12345!",
            },
        )
        self.assertRedirects(response, reverse("pretraga_trka"))
        self.assertEqual(self.client.session["id_korisnika"], current.pk)

    def test_suspended_user_cannot_login(self):
        """Proverava scenario: suspended user cannot login."""
        current = user(email="suspendovan@test.rs")
        current.status_naloga = "Suspendovano"
        current.save(update_fields=["status_naloga"])
        response = self.client.post(
            reverse("auth"),
            {
                "akcija": "prijava",
                "login-email": current.email,
                "login-lozinka": "Test12345!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "suspendovan")
        self.assertNotIn("id_korisnika", self.client.session)

    def test_logout_requires_post(self):
        """Proverava scenario: logout requires post."""
        self.assertEqual(self.client.get(reverse("odjava")).status_code, 405)


class PublicAndBuyerFlowTests(TestCase):
    """Testira pretragu, korpu, plaćanje, PDF i vlasništvo kupca."""

    def setUp(self):
        """Priprema izolovane podatke i klijente potrebne za svaki test."""
        self.buyer = user(email="buyer-flow@test.rs")
        self.race, self.sector, self.accommodation, *_ = package(seats=2, rooms=2)
        self.client = logged_client(self.buyer)

    def test_ajax_search_returns_filtered_html_and_count(self):
        """Proverava scenario: ajax search returns filtered html and count."""
        response = Client().get(
            reverse("ajax_filtriraj_trke"), {"sampionat": "F1", "lokacija": "Srbija"}
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 1)
        self.assertIn(self.race.naziv_trke, payload["html"])

    def test_add_to_cart_and_payment_flow(self):
        """Proverava scenario: add to cart and payment flow."""
        add = self.client.post(
            reverse("dodaj_u_korpu", args=[self.race.pk]),
            {"id_sektora": self.sector.pk, "id_smestaja": self.accommodation.pk},
        )
        self.assertRedirects(add, reverse("korpa"))
        reservation = Rezervacija.objects.get(id_kupca=self.buyer)
        self.assertEqual(reservation.status_rezervacije, STATUS_REZERVACIJE_KORPA)

        paid = self.client.post(reverse("potvrdi_placanje", args=[reservation.pk]))
        self.assertEqual(paid.status_code, 200)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status_rezervacije, STATUS_REZERVACIJE_AKTIVNA)
        voucher = DigitalniVaucer.objects.get(id_rezervacije=reservation)

        pdf = self.client.get(reverse("preuzmi_vaucer", args=[voucher.pk]))
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))

    def test_simulated_payment_failure_does_not_change_inventory(self):
        """Proverava scenario: simulated payment failure does not change inventory."""
        reservation = Rezervacija.objects.create(
            id_kupca=self.buyer,
            id_sektora=self.sector,
            id_smestaja=self.accommodation,
            ukupna_cena=Decimal("180.00"),
            status_rezervacije=STATUS_REZERVACIJE_KORPA,
        )
        response = self.client.post(
            reverse("potvrdi_placanje", args=[reservation.pk]),
            {"simuliraj_neuspeh": "1"},
        )
        self.assertRedirects(response, reverse("korpa"))
        reservation.refresh_from_db()
        self.sector.refresh_from_db()
        self.assertEqual(reservation.status_rezervacije, STATUS_REZERVACIJE_KORPA)
        self.assertEqual(self.sector.slobodna_mesta, 2)

    def test_other_buyer_cannot_download_voucher(self):
        """Proverava scenario: other buyer cannot download voucher."""
        reservation = Rezervacija.objects.create(
            id_kupca=self.buyer,
            id_sektora=self.sector,
            id_smestaja=self.accommodation,
            ukupna_cena=Decimal("180.00"),
            status_rezervacije=STATUS_REZERVACIJE_AKTIVNA,
        )
        voucher = DigitalniVaucer.objects.create(
            id_rezervacije=reservation, qr_kod="PRIVATE-QR"
        )
        other = user(email="other@test.rs")
        response = logged_client(other).get(reverse("preuzmi_vaucer", args=[voucher.pk]))
        self.assertEqual(response.status_code, 302)


class PartnerAndAdminViewTests(TestCase):
    """Testira autorizaciju organizatora, hotelijera i administratora."""

    def test_organizer_sees_only_own_races(self):
        """Proverava scenario: organizer sees only own races."""
        own_race, *_rest, organizer, _hotelier = package()
        other_race, *_ = package()
        client = logged_client(organizer)
        response = client.get(reverse("organizator_dashboard"))
        self.assertContains(response, own_race.naziv_trke)
        self.assertNotContains(response, other_race.naziv_trke)

    def test_organizer_cannot_edit_foreign_race(self):
        """Proverava scenario: organizer cannot edit foreign race."""
        race, *_ = package()
        foreign_organizer = user(role=ULOGA_ORGANIZATOR, email="foreign-org@test.rs")
        response = logged_client(foreign_organizer).get(
            reverse("izmeni_trku", args=[race.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_hotelier_cannot_delete_foreign_accommodation(self):
        """Proverava scenario: hotelier cannot delete foreign accommodation."""
        _race, _sector, accommodation, _organizer, _hotelier = package()
        foreign_hotelier = user(role=ULOGA_HOTELIJER, email="foreign-hotel@test.rs")
        response = logged_client(foreign_hotelier).post(
            reverse("obrisi_smestaj", args=[accommodation.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Smestaj.objects.filter(pk=accommodation.pk).exists())

    def test_admin_statistics_exclude_cart(self):
        """Proverava scenario: admin statistics exclude cart."""
        buyer = user(email="stats-buyer@test.rs")
        _race, sector, accommodation, *_ = package()
        Rezervacija.objects.create(
            id_kupca=buyer,
            id_sektora=sector,
            id_smestaja=accommodation,
            ukupna_cena=Decimal("180.00"),
            status_rezervacije=STATUS_REZERVACIJE_KORPA,
        )
        Rezervacija.objects.create(
            id_kupca=buyer,
            id_sektora=sector,
            id_smestaja=accommodation,
            ukupna_cena=Decimal("180.00"),
            status_rezervacije=STATUS_REZERVACIJE_AKTIVNA,
        )
        admin = user(role=ULOGA_ADMINISTRATOR, email="stats-admin@test.rs")
        payload = logged_client(admin).get(reverse("api_statistika")).json()
        self.assertEqual(payload["prodato"], 1)
        self.assertEqual(payload["zarada"], 180.0)

    def test_destructive_endpoints_reject_get(self):
        """Proverava scenario: destructive endpoints reject get."""
        admin = user(role=ULOGA_ADMINISTRATOR, email="get-admin@test.rs")
        target = user(email="target@test.rs")
        client = logged_client(admin)
        response = client.get(reverse("suspenduj_korisnika", args=[target.pk]))
        self.assertEqual(response.status_code, 405)
