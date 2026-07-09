from django.contrib import admin
from django.urls import path
from core import views_organizator

urlpatterns = [
    path('admin/', admin.site.urls),
    path('organizator/', views_organizator.organizator_dashboard, name='organizator_dashboard'),
    path('organizator/dodaj-trku/', views_organizator.dodaj_trku, name='dodaj_trku'),
    path('organizator/trka/<int:id_trke>/sektori/', views_organizator.upravljaj_sektorima, name='upravljaj_sektorima'),
    path('organizator/proveri-naziv/', views_organizator.proveri_naziv_trke, name='proveri_naziv_trke'),
    path('organizator/trka/<int:id_trke>/obrisi/', views_organizator.obrisi_trku, name='obrisi_trku'),
    path('organizator/sektor/<int:id_sektora>/obrisi/', views_organizator.obrisi_sektor, name='obrisi_sektor'),
]