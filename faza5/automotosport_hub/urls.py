from django.contrib import admin
from django.urls import path
from core import views_organizator
from core import views_hotelijer
from core import views_admin
from core import views_kupac
urlpatterns = [
    path('admin/', admin.site.urls),
    path('organizator/', views_organizator.organizator_dashboard, name='organizator_dashboard'),
    path('organizator/dodaj-trku/', views_organizator.dodaj_trku, name='dodaj_trku'),
    path('organizator/trka/<int:id_trke>/sektori/', views_organizator.upravljaj_sektorima, name='upravljaj_sektorima'),
    path('organizator/proveri-naziv/', views_organizator.proveri_naziv_trke, name='proveri_naziv_trke'),
    path('organizator/trka/<int:id_trke>/obrisi/', views_organizator.obrisi_trku, name='obrisi_trku'),
    path('organizator/sektor/<int:id_sektora>/obrisi/', views_organizator.obrisi_sektor, name='obrisi_sektor'),

    path('hotelijer/', views_hotelijer.partner_dashboard, name='partner_dashboard'),
    path('hotelijer/obrisi/<int:id_smestaja>/', views_hotelijer.obrisi_smestaj, name='obrisi_smestaj'),


    path('admin-panel/', views_admin.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/statistika/', views_admin.api_statistika, name='api_statistika'),
    path('admin-panel/suspenduj/<int:id_korisnika>/', views_admin.suspenduj_korisnika, name='suspenduj_korisnika'),

    path('', views_kupac.pretraga_trka, name='pretraga_trka'),
    path('api/filtriraj-trke/', views_kupac.ajax_filtriraj_trke, name='ajax_filtriraj_trke'),
    path('trka/<int:id_trke>/', views_kupac.detalji_trke, name='detalji_trke'),
    path('trka/<int:id_trke>/dodaj-u-korpu/', views_kupac.dodaj_u_korpu, name='dodaj_u_korpu'),
    path('korpa/', views_kupac.korpa, name='korpa'),
    path('korpa/ukloni/<int:id_rezervacije>/', views_kupac.ukloni_iz_korpe, name='ukloni_iz_korpe'),
    path('korpa/potvrdi/<int:id_rezervacije>/', views_kupac.potvrdi_placanje, name='potvrdi_placanje'),
]