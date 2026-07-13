#!/usr/bin/env python
# Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;
"""Komandni ulaz u Django projekat."""

import os
import sys


def main() -> None:
    """Pokreće izabranu Django administrativnu komandu."""

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "automotosport_hub.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django nije dostupan. Instalirajte zavisnosti iz requirements.txt."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
