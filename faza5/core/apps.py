# Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;
"""Konfiguracija Django aplikacije core."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Registruje aplikaciju koja sadrži ceo domen projekta."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Automotosport Travel Hub"
