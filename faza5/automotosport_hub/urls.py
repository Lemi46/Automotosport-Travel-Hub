# Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;
"""URL konfiguracija Automotosport Travel Hub aplikacije."""

from django.contrib import admin
from django.urls import path

from core import views_admin, views_auth, views_hotelijer, views_kupac, views_organizator

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", views_kupac.index_strana, name="index"),
    path("auth/", views_auth.prijava_registracija, name="auth"),
    path("odjava/", views_auth.odjava, name="odjava"),
    path("pretraga/", views_kupac.pretraga_trka, name="pretraga_trka"),
    path("api/filtriraj-trke/", views_kupac.ajax_filtriraj_trke, name="ajax_filtriraj_trke"),
    path("trka/<int:id_trke>/", views_kupac.detalji_trke, name="detalji_trke"),
    path("trka/<int:id_trke>/dodaj-u-korpu/", views_kupac.dodaj_u_korpu, name="dodaj_u_korpu"),
    path("korpa/", views_kupac.korpa, name="korpa"),
    path("korpa/ukloni/<int:id_rezervacije>/", views_kupac.ukloni_iz_korpe, name="ukloni_iz_korpe"),
    path("korpa/potvrdi/<int:id_rezervacije>/", views_kupac.potvrdi_placanje, name="potvrdi_placanje"),
    path("rezervacija/<int:id_rezervacije>/otkazi/", views_kupac.otkazi_rezervaciju, name="otkazi_rezervaciju"),
    path("rezervacija/<int:id_rezervacije>/recenzija/", views_kupac.ostavi_recenziju, name="ostavi_recenziju"),
    path("vaucer/<int:id_vaucera>/pdf/", views_kupac.preuzmi_vaucer, name="preuzmi_vaucer"),
    path("istorija/", views_kupac.istorija_kupovina, name="istorija_kupovina"),
    path("organizator/", views_organizator.organizator_dashboard, name="organizator_dashboard"),
    path("organizator/dodaj-trku/", views_organizator.dodaj_trku, name="dodaj_trku"),
    path("organizator/trka/<int:id_trke>/izmeni/", views_organizator.izmeni_trku, name="izmeni_trku"),
    path("organizator/trka/<int:id_trke>/preuzmi/", views_organizator.preuzmi_trku, name="preuzmi_trku"),
    path("organizator/trka/<int:id_trke>/sektori/", views_organizator.upravljaj_sektorima, name="upravljaj_sektorima"),
    path("organizator/sektor/<int:id_sektora>/izmeni/", views_organizator.izmeni_sektor, name="izmeni_sektor"),
    path("organizator/proveri-naziv/", views_organizator.proveri_naziv_trke, name="proveri_naziv_trke"),
    path("organizator/trka/<int:id_trke>/obrisi/", views_organizator.obrisi_trku, name="obrisi_trku"),
    path("organizator/sektor/<int:id_sektora>/obrisi/", views_organizator.obrisi_sektor, name="obrisi_sektor"),
    path("hotelijer/", views_hotelijer.partner_dashboard, name="partner_dashboard"),
    path("hotelijer/smestaj/<int:id_smestaja>/izmeni/", views_hotelijer.izmeni_smestaj, name="izmeni_smestaj"),
    path("hotelijer/smestaj/<int:id_smestaja>/obrisi/", views_hotelijer.obrisi_smestaj, name="obrisi_smestaj"),
    path("admin-panel/", views_admin.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/statistika/", views_admin.api_statistika, name="api_statistika"),
    path("admin-panel/suspenduj/<int:id_korisnika>/", views_admin.suspenduj_korisnika, name="suspenduj_korisnika"),
    path("admin-panel/aktiviraj/<int:id_korisnika>/", views_admin.aktiviraj_korisnika, name="aktiviraj_korisnika"),
    path("admin-panel/sinhronizuj/", views_admin.sinhronizuj_trke, name="sinhronizuj_trke"),
]
