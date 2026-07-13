# Faza 7 - DOPUNSKI testovi. Originalni fajlovi faze 5 nisu menjani.
# Autori testova: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023;Marko Mandić 0625/2023;
"""Dopunski Django testovi za tokove koji nisu eksplicitno odradjeni u implementaciji."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.hashers import check_password
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from core.constants import (
    STATUS_REZERVACIJE_AKTIVNA,
    STATUS_REZERVACIJE_KORPA,
    STATUS_REZERVACIJE_ZAVRSENA,
    SYSTEM_ORGANIZER_EMAIL,
)
from core.models import DigitalniVaucer, Korisnik, Recenzija, Rezervacija, Smestaj, Trka
from core.services import RaceData, SyncResult, _store_races
from core.tests.factories import (
    ULOGA_ADMINISTRATOR,
    ULOGA_HOTELIJER,
    ULOGA_ORGANIZATOR,
    logged_client,
    package,
    user,
)


class DopunskiAutentikacijaTestovi(TestCase):
    """SSU 1 i SSU 10 - granični tokovi registracije i prijave."""

    def test_d01_registracija_ne_dozvoljava_administratorsku_ulogu(self):
        response = self.client.post(
            reverse("auth"),
            {
                "akcija": "registracija",
                "registration-uloga": "Administrator",
                "registration-ime": "Neovlasceni",
                "registration-prezime": "Admin",
                "registration-email": "novi-admin@test.rs",
                "registration-lozinka": "DobraLozinka123!",
                "registration-potvrda_lozinke": "DobraLozinka123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Korisnik.objects.filter(email="novi-admin@test.rs").exists())
        self.assertContains(
            response,
            "Administrator nije među ponuđenim vrednostima",
        )

    def test_d02_pet_neuspeha_privremeno_zakljucava_prijavu(self):
        current = user(email="lock@test.rs")
        for _ in range(5):
            response = self.client.post(
                reverse("auth"),
                {
                    "akcija": "prijava",
                    "login-email": current.email,
                    "login-lozinka": "PogresnaLozinka123!",
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "privremeno zaključana")
        self.assertGreater(self.client.session.get("login_lock_until", 0), 0)
        self.assertNotIn("id_korisnika", self.client.session)

    def test_d03_spoljni_next_parametar_ne_pravi_otvoreno_preusmerenje(self):
        current = user(email="safe-next@test.rs")
        response = self.client.post(
            reverse("auth") + "?next=https://example.invalid/phishing",
            {
                "akcija": "prijava",
                "login-email": current.email,
                "login-lozinka": "Test12345!",
                "next": "https://example.invalid/phishing",
            },
        )
        self.assertRedirects(response, reverse("pretraga_trka"))

    def test_d04_stara_tekstualna_lozinka_se_migrira_u_hash(self):
        current = Korisnik.objects.create(
            ime="Legacy",
            prezime="Kupac",
            email="legacy@test.rs",
            lozinka="Legacy123!",
            uloga="Kupac",
            status_naloga="Aktivno",
        )
        response = self.client.post(
            reverse("auth"),
            {
                "akcija": "prijava",
                "login-email": current.email,
                "login-lozinka": "Legacy123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        current.refresh_from_db()
        self.assertNotEqual(current.lozinka, "Legacy123!")
        self.assertTrue(check_password("Legacy123!", current.lozinka))


class DopunskiKupacTestovi(TestCase):
    """SSU 3 i SSU 4 - vlasništvo, istorija, otkazivanje i recenzija."""

    def setUp(self):
        self.buyer = user(email="dopunski-buyer@test.rs")
        self.other = user(email="dopunski-other@test.rs")
        self.race, self.sector, self.accommodation, *_ = package(seats=3, rooms=3)
        self.client = logged_client(self.buyer)

    def _reservation(self, buyer, status):
        return Rezervacija.objects.create(
            id_kupca=buyer,
            id_sektora=self.sector,
            id_smestaja=self.accommodation,
            ukupna_cena=Decimal("180.00"),
            status_rezervacije=status,
        )

    def test_d05_istorija_ne_prikazuje_korpu_ni_tudju_kupovinu(self):
        own_cart = self._reservation(self.buyer, STATUS_REZERVACIJE_KORPA)
        own_active = self._reservation(self.buyer, STATUS_REZERVACIJE_AKTIVNA)
        other_active = self._reservation(self.other, STATUS_REZERVACIJE_AKTIVNA)
        response = self.client.get(reverse("istorija_kupovina"))
        self.assertEqual(response.status_code, 200)
        reservations = list(response.context["rezervacije"])
        self.assertIn(own_active, reservations)
        self.assertNotIn(own_cart, reservations)
        self.assertNotIn(other_active, reservations)

    def test_d06_kupac_ne_moze_ukloniti_tudju_stavku_iz_korpe(self):
        foreign = self._reservation(self.other, STATUS_REZERVACIJE_KORPA)
        response = self.client.post(reverse("ukloni_iz_korpe", args=[foreign.pk]))
        self.assertRedirects(response, reverse("korpa"))
        self.assertTrue(Rezervacija.objects.filter(pk=foreign.pk).exists())

    def test_d07_recenzija_je_dozvoljena_samo_za_zavrsenu_rezervaciju(self):
        active = self._reservation(self.buyer, STATUS_REZERVACIJE_AKTIVNA)
        response = self.client.get(reverse("ostavi_recenziju", args=[active.pk]))
        self.assertEqual(response.status_code, 404)

    def test_d08_jedna_zavrsena_rezervacija_dobija_najvise_jednu_recenziju(self):
        completed = self._reservation(self.buyer, STATUS_REZERVACIJE_ZAVRSENA)
        data = {
            "ocena_smestaja": "5",
            "komentar_smestaja": "Odlično.",
            "ocena_organizatora": "4",
            "komentar_organizatora": "Vrlo dobro.",
        }
        first = self.client.post(reverse("ostavi_recenziju", args=[completed.pk]), data)
        self.assertRedirects(first, reverse("istorija_kupovina"))
        second = self.client.post(reverse("ostavi_recenziju", args=[completed.pk]), data)
        self.assertRedirects(second, reverse("istorija_kupovina"))
        self.assertEqual(Recenzija.objects.filter(id_rezervacije=completed).count(), 1)

    def test_d09_otkazivanje_aktivne_rezervacije_kroz_view_vraca_kapacitete(self):
        active = self._reservation(self.buyer, STATUS_REZERVACIJE_AKTIVNA)
        self.sector.slobodna_mesta = 2
        self.accommodation.broj_slobodnih_soba = 2
        self.sector.save(update_fields=["slobodna_mesta"])
        self.accommodation.save(update_fields=["broj_slobodnih_soba"])
        response = self.client.post(reverse("otkazi_rezervaciju", args=[active.pk]))
        self.assertRedirects(response, reverse("istorija_kupovina"))
        active.refresh_from_db()
        self.sector.refresh_from_db()
        self.accommodation.refresh_from_db()
        self.assertEqual(active.status_rezervacije, "Otkazana")
        self.assertEqual(self.sector.slobodna_mesta, 3)
        self.assertEqual(self.accommodation.broj_slobodnih_soba, 3)


class DopunskiPartneriTestovi(TestCase):
    """SSU 6-8 - CRUD, vlasništvo i zaštita povezanih rezervacija."""

    def test_d10_dodavanje_trke_automatski_vezuje_prijavljenog_organizatora(self):
        organizer = user(role=ULOGA_ORGANIZATOR, email="add-race-org@test.rs")
        client = logged_client(organizer)
        date = timezone.localdate() + timedelta(days=90)
        response = client.post(
            reverse("dodaj_trku"),
            {
                "naziv_trke": "  Nova   Test   Trka  ",
                "staza": "Nova staza",
                "drzava": "Srbija",
                "datum_odrzavanja": date.isoformat(),
                "sampionat": "MotoGP",
            },
        )
        self.assertEqual(response.status_code, 302)
        race = Trka.objects.get(naziv_trke="Nova Test Trka")
        self.assertEqual(race.id_organizatora, organizer)

    def test_d11_trka_sa_rezervacijom_ne_moze_biti_obrisana(self):
        buyer = user(email="block-race-buyer@test.rs")
        race, sector, accommodation, organizer, _ = package()
        Rezervacija.objects.create(
            id_kupca=buyer,
            id_sektora=sector,
            id_smestaja=accommodation,
            ukupna_cena=Decimal("180.00"),
            status_rezervacije=STATUS_REZERVACIJE_KORPA,
        )
        response = logged_client(organizer).post(reverse("obrisi_trku", args=[race.pk]))
        self.assertRedirects(response, reverse("organizator_dashboard"))
        self.assertTrue(Trka.objects.filter(pk=race.pk).exists())

    def test_d12_dodavanje_smestaja_automatski_vezuje_prijavljenog_hotelijera(self):
        race, *_ = package()
        hotelier = user(role=ULOGA_HOTELIJER, email="add-hotel@test.rs")
        response = logged_client(hotelier).post(
            reverse("partner_dashboard"),
            {
                "id_trke": race.pk,
                "naziv_smestaja": "Novi hotel",
                "lokacija": "Centar",
                "udaljenost_od_staze": "4.50",
                "broj_slobodnih_soba": "12",
                "cena_po_nocenju": "99.90",
            },
        )
        self.assertRedirects(response, reverse("partner_dashboard"))
        accommodation = Smestaj.objects.get(naziv_smestaja="Novi hotel")
        self.assertEqual(accommodation.id_hotelijera, hotelier)

    def test_d13_smestaj_sa_rezervacijom_ne_moze_biti_obrisan(self):
        buyer = user(email="block-hotel-buyer@test.rs")
        _race, sector, accommodation, _organizer, hotelier = package()
        Rezervacija.objects.create(
            id_kupca=buyer,
            id_sektora=sector,
            id_smestaja=accommodation,
            ukupna_cena=Decimal("180.00"),
            status_rezervacije=STATUS_REZERVACIJE_KORPA,
        )
        response = logged_client(hotelier).post(
            reverse("obrisi_smestaj", args=[accommodation.pk])
        )
        self.assertRedirects(response, reverse("partner_dashboard"))
        self.assertTrue(Smestaj.objects.filter(pk=accommodation.pk).exists())


class DopunskiAdministratorTestovi(TestCase):
    """SSU 5 i SSU 9 - administracija, statistika i grupna sinhronizacija."""

    def setUp(self):
        self.admin = user(role=ULOGA_ADMINISTRATOR, email="dopunski-admin@test.rs")
        self.client = logged_client(self.admin)

    def test_d14_administrator_ne_moze_suspendovati_drugog_administratora(self):
        other_admin = user(role=ULOGA_ADMINISTRATOR, email="other-admin@test.rs")
        response = self.client.post(
            reverse("suspenduj_korisnika", args=[other_admin.pk]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        other_admin.refresh_from_db()
        self.assertEqual(other_admin.status_naloga, "Aktivno")
        self.assertContains(response, "Administratorski nalog ne može biti suspendovan")

    def test_d15_aktivacija_vraca_suspendovani_nalog_u_aktivno_stanje(self):
        target = user(email="reactivate@test.rs")
        target.status_naloga = "Suspendovano"
        target.save(update_fields=["status_naloga"])
        response = self.client.post(reverse("aktiviraj_korisnika", args=[target.pk]))
        self.assertRedirects(response, reverse("admin_dashboard"))
        target.refresh_from_db()
        self.assertEqual(target.status_naloga, "Aktivno")

    def test_d16_nepoznat_period_statistike_vraca_400(self):
        response = self.client.get(reverse("api_statistika"), {"period": "decenija"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Nepoznat period.")

    @patch("core.views_admin.sync_all_motorsports")
    def test_d17_view_sinhronizacije_prikazuje_odvojeni_ishod_za_sva_tri_izvora(self, sync):
        sync.return_value = {
            "F1": SyncResult(created=2, updated=0, skipped=1),
            "MotoGP": {"error": "MotoGP servis nije dostupan."},
            "WSBK": SyncResult(created=1, updated=1, skipped=0),
        }
        response = self.client.post(reverse("sinhronizuj_trke"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "F1 sinhronizacija završena")
        self.assertContains(response, "MotoGP servis nije dostupan")
        self.assertContains(response, "WSBK sinhronizacija završena")

    def test_d18_sinhronizacija_ne_prepisuje_trku_preuzetu_od_pravog_organizatora(self):
        organizer = user(role=ULOGA_ORGANIZATOR, email="claimed-org@test.rs")
        event_date = timezone.localdate() + timedelta(days=120)
        race = Trka.objects.create(
            id_organizatora=organizer,
            naziv_trke="Claimed Grand Prix",
            staza="Originalna staza",
            drzava="Originalna država",
            datum_odrzavanja=event_date,
            sampionat="F1",
        )
        result = _store_races(
            championship="F1",
            races=[RaceData("Claimed Grand Prix", "API staza", "API država", event_date)],
        )
        race.refresh_from_db()
        self.assertEqual(result, SyncResult(created=0, updated=0, skipped=1))
        self.assertEqual(race.staza, "Originalna staza")

    def test_d19_sinhronizacija_osvezava_stazu_sistemske_trke(self):
        system = Korisnik.objects.create(
            ime="Sistemski",
            prezime="Organizator",
            email=SYSTEM_ORGANIZER_EMAIL,
            lozinka="!",
            uloga=ULOGA_ORGANIZATOR,
            status_naloga="Aktivno",
        )
        event_date = timezone.localdate() + timedelta(days=140)
        race = Trka.objects.create(
            id_organizatora=system,
            naziv_trke="System Grand Prix",
            staza="Stara staza",
            drzava="Stara država",
            datum_odrzavanja=event_date,
            sampionat="MotoGP",
        )
        result = _store_races(
            championship="MotoGP",
            races=[RaceData("System Grand Prix", "Nova staza", "Nova država", event_date)],
        )
        race.refresh_from_db()
        self.assertEqual(result, SyncResult(created=0, updated=1, skipped=0))
        self.assertEqual(race.staza, "Nova staza")
        self.assertEqual(race.drzava, "Nova država")
