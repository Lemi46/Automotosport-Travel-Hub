# Autor: Milan Lemić 0323/2023;
"""Domensке konstante izvedene isključivo iz šeme baze."""

ULOGA_KUPAC = "Kupac"
ULOGA_ORGANIZATOR = "Organizator"
ULOGA_HOTELIJER = "Hotelijer"
ULOGA_ADMINISTRATOR = "Administrator"

ULOGE = (
    (ULOGA_KUPAC, "Kupac"),
    (ULOGA_ORGANIZATOR, "Organizator"),
    (ULOGA_HOTELIJER, "Hotelijer"),
    (ULOGA_ADMINISTRATOR, "Administrator"),
)
ULOGE_ZA_REGISTRACIJU = ULOGE[:3]

STATUS_NALOGA_AKTIVNO = "Aktivno"
STATUS_NALOGA_SUSPENDOVANO = "Suspendovano"
STATUSI_NALOGA = (
    (STATUS_NALOGA_AKTIVNO, "Aktivno"),
    (STATUS_NALOGA_SUSPENDOVANO, "Suspendovano"),
)

STATUS_REZERVACIJE_KORPA = "U_korpi"
STATUS_REZERVACIJE_AKTIVNA = "Aktivna"
STATUS_REZERVACIJE_ZAVRSENA = "Zavrsena"
STATUS_REZERVACIJE_OTKAZANA = "Otkazana"
STATUSI_REZERVACIJE = (
    (STATUS_REZERVACIJE_KORPA, "U korpi"),
    (STATUS_REZERVACIJE_AKTIVNA, "Aktivna"),
    (STATUS_REZERVACIJE_ZAVRSENA, "Završena"),
    (STATUS_REZERVACIJE_OTKAZANA, "Otkazana"),
)

STATUS_VAUCERA_VALIDAN = "Validan"
STATUS_VAUCERA_STAZA = "Iskoriscen_Staza"
STATUS_VAUCERA_HOTEL = "Iskoriscen_Hotel"
STATUS_VAUCERA_SVE = "Iskoriscen_Sve"
STATUSI_VAUCERA = (
    (STATUS_VAUCERA_VALIDAN, "Validan"),
    (STATUS_VAUCERA_STAZA, "Iskorišćen na stazi"),
    (STATUS_VAUCERA_HOTEL, "Iskorišćen u hotelu"),
    (STATUS_VAUCERA_SVE, "U potpunosti iskorišćen"),
)

SAMPIONATI = (("F1", "Formula 1"), ("MotoGP", "MotoGP"), ("WSBK", "WSBK"))

SYSTEM_ORGANIZER_EMAIL = "api@automotosport.local"
