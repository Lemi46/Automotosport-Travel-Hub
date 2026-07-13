# Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;
"""Django podešavanja za Automotosport Travel Hub.

Aplikacija koristi isključivo MySQL šemu ``automotosport_travel_hub``. Domenske
tabele se kreiraju u MySQL Workbench-u pokretanjem priložene SQL skripte. Komanda
``migrate --fake-initial`` zatim evidentira odgovarajuću početnu migraciju i
kreira potrebne Django pomoćne tabele.
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-automotosport-travel-hub-demo-key-change-me",
)
DEBUG = os.getenv("DJANGO_DEBUG", "1").lower() in {"1", "true", "yes", "on"}

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver"
    ).split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "automotosport_hub.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.session_user",
            ],
        },
    },
]

WSGI_APPLICATION = "automotosport_hub.wsgi.application"
ASGI_APPLICATION = "automotosport_hub.asgi.application"

# Isključivo MySQL. Podrazumevane vrednosti odgovaraju prvoj verziji projekta i
# lokalnoj konekciji koja se obično koristi iz MySQL Workbench-a.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "automotosport_travel_hub"),
        "USER": os.getenv("DB_USER", "root"),
        "PASSWORD": os.getenv("DB_PASSWORD", "admin"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        "TEST": {
            "NAME": os.getenv("DB_TEST_NAME", "test_automotosport_travel_hub")
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "sr-latn"
TIME_ZONE = "Europe/Belgrade"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Demo opcija potrebna za prikaz alternativnog scenarija neuspešnog plaćanja.
DEMO_MODE = os.getenv("DEMO_MODE", "1").lower() in {"1", "true", "yes", "on"}

# Izvori za sinhronizaciju tri šampionata dozvoljena šemom baze.
F1_API_URL = os.getenv(
    "F1_API_URL", "https://api.jolpi.ca/ergast/f1/current.json"
)
F1_API_TIMEOUT = int(os.getenv("F1_API_TIMEOUT", "10"))

MOTOGP_SEASONS_API_URL = os.getenv(
    "MOTOGP_SEASONS_API_URL",
    "https://api.motogp.pulselive.com/motogp/v1/results/seasons",
)
MOTOGP_EVENTS_API_URL = os.getenv(
    "MOTOGP_EVENTS_API_URL",
    "https://api.motogp.pulselive.com/motogp/v1/results/events",
)
MOTOGP_API_TIMEOUT = int(os.getenv("MOTOGP_API_TIMEOUT", "10"))

SPORTSDB_API_URL = os.getenv(
    "SPORTSDB_API_URL",
    "https://www.thesportsdb.com/api/v1/json/123/eventsseason.php",
)
SPORTSDB_API_TIMEOUT = int(os.getenv("SPORTSDB_API_TIMEOUT", "10"))
SPORTSDB_WSBK_LEAGUE_ID = os.getenv("SPORTSDB_WSBK_LEAGUE_ID", "4454")
