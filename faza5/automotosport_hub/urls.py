from django.contrib import admin
from django.urls import path
from core import views_organizator

urlpatterns = [
    path('admin/', admin.site.urls),
    path('organizator/', views_organizator.organizator_dashboard, name='organizator_dashboard'),
    path('organizator/dodaj-trku/', views_organizator.dodaj_trku, name='dodaj_trku'),

    # Novi link za sektore koji prima ID trke (npr. /organizator/trka/3/sektori/)
    # ISPRAVNO:
    path('organizator/trka/<int:id_trke>/sektori/', views_organizator.upravljaj_sektorima, name='upravljaj_sektorima'),
]