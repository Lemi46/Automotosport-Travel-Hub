# Autor: Marko Mandić 0625/2023;
"""Registracija domenskih tabela u ugrađenom Django administracionom interfejsu."""

from django.contrib import admin

from .models import DigitalniVaucer, Korisnik, Recenzija, Rezervacija, Sektor, Smestaj, Trka


@admin.register(Korisnik)
class KorisnikAdmin(admin.ModelAdmin):
    """Pregled naloga bez prikazivanja lozinke u tabeli."""

    list_display = ("email", "ime", "prezime", "uloga", "status_naloga")
    list_filter = ("uloga", "status_naloga")
    search_fields = ("email", "ime", "prezime")
    exclude = ("lozinka",)


@admin.register(Trka)
class TrkaAdmin(admin.ModelAdmin):
    """Pregled trka po šampionatu i datumu."""

    list_display = (
        "naziv_trke",
        "sampionat",
        "staza",
        "drzava",
        "datum_odrzavanja",
        "id_organizatora",
    )
    list_filter = ("sampionat", "datum_odrzavanja")
    search_fields = ("naziv_trke", "staza", "drzava")


@admin.register(Sektor)
class SektorAdmin(admin.ModelAdmin):
    """Pregled kapaciteta sektora."""

    list_display = (
        "naziv_sektora",
        "id_trke",
        "ukupni_kapacitet",
        "slobodna_mesta",
        "cena_karte",
    )
    search_fields = ("naziv_sektora", "id_trke__naziv_trke")


@admin.register(Smestaj)
class SmestajAdmin(admin.ModelAdmin):
    """Pregled smeštaja po trci i hotelijeru."""

    list_display = (
        "naziv_smestaja",
        "id_trke",
        "id_hotelijera",
        "broj_slobodnih_soba",
        "cena_po_nocenju",
    )
    search_fields = ("naziv_smestaja", "lokacija", "id_trke__naziv_trke")


@admin.register(Rezervacija)
class RezervacijaAdmin(admin.ModelAdmin):
    """Pregled životnog ciklusa rezervacije."""

    list_display = (
        "id_rezervacije",
        "id_kupca",
        "status_rezervacije",
        "ukupna_cena",
        "datum_kreiranja",
    )
    list_filter = ("status_rezervacije", "datum_kreiranja")


@admin.register(DigitalniVaucer)
class DigitalniVaucerAdmin(admin.ModelAdmin):
    """Pregled izdatih vaučera."""

    list_display = ("id_vaucera", "id_rezervacije", "status_vaucera")
    list_filter = ("status_vaucera",)
    search_fields = ("qr_kod",)


@admin.register(Recenzija)
class RecenzijaAdmin(admin.ModelAdmin):
    """Pregled ocena kupaca."""

    list_display = (
        "id_recenzije",
        "id_kupca",
        "ocena_smestaja",
        "ocena_organizatora",
        "datum_objave",
    )
    list_filter = ("ocena_smestaja", "ocena_organizatora")
