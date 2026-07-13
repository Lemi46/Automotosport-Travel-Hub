# Autor: Milan Lemić 0323/2023;
"""Forme i validacije nad kolonama postojeće baze."""

from __future__ import annotations

from datetime import date

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .constants import ULOGE_ZA_REGISTRACIJU
from .models import Korisnik, Recenzija, Sektor, Smestaj, Trka


class StyledFormMixin:
    """Dodaje zajedničke CSS klase bez menjanja domenskih podataka."""

    def apply_styles(self) -> None:
        """Primenjuje odgovarajuću klasu na svako vidljivo polje."""

        for field in self.fields.values():
            widget = field.widget
            current = widget.attrs.get("class", "")
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css_class = "form-select"
            elif isinstance(widget, forms.CheckboxInput):
                css_class = "form-check-input"
            else:
                css_class = "form-control"
            widget.attrs["class"] = f"{current} {css_class}".strip()


class LoginForm(StyledFormMixin, forms.Form):
    """Podaci potrebni za prijavljivanje korisnika."""

    email = forms.EmailField(label="E-mail", max_length=100)
    lozinka = forms.CharField(label="Lozinka", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        """Inicijalizuje objekat i prilagođava polja trenutnom kontekstu."""
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["email"].widget.attrs.update(
            {"autocomplete": "email", "data-testid": "login-email"}
        )
        self.fields["lozinka"].widget.attrs.update(
            {"autocomplete": "current-password", "data-testid": "login-password"}
        )

    def clean_email(self) -> str:
        """Normalizuje e-mail pre pretrage u bazi."""

        return self.cleaned_data["email"].strip().lower()


class RegistrationForm(StyledFormMixin, forms.Form):
    """Registracija uloga koje šema dozvoljava samostalnom korisniku."""

    uloga = forms.ChoiceField(label="Uloga", choices=ULOGE_ZA_REGISTRACIJU)
    ime = forms.CharField(label="Ime", max_length=50)
    prezime = forms.CharField(label="Prezime", max_length=50)
    email = forms.EmailField(label="E-mail", max_length=100)
    lozinka = forms.CharField(label="Lozinka", widget=forms.PasswordInput)
    potvrda_lozinke = forms.CharField(
        label="Potvrda lozinke", widget=forms.PasswordInput
    )

    def __init__(self, *args, **kwargs):
        """Inicijalizuje objekat i prilagođava polja trenutnom kontekstu."""
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["uloga"].widget.attrs["data-testid"] = "registration-role"
        self.fields["ime"].widget.attrs.update(
            {"autocomplete": "given-name", "data-testid": "registration-first-name"}
        )
        self.fields["prezime"].widget.attrs.update(
            {"autocomplete": "family-name", "data-testid": "registration-last-name"}
        )
        self.fields["email"].widget.attrs.update(
            {"autocomplete": "email", "data-testid": "registration-email"}
        )
        self.fields["lozinka"].widget.attrs.update(
            {"autocomplete": "new-password", "data-testid": "registration-password"}
        )
        self.fields["potvrda_lozinke"].widget.attrs.update(
            {
                "autocomplete": "new-password",
                "data-testid": "registration-password-confirm",
            }
        )

    def clean_email(self) -> str:
        """Sprečava dupliranje naloga bez obzira na veličinu slova."""

        email = self.cleaned_data["email"].strip().lower()
        if Korisnik.objects.filter(email__iexact=email).exists():
            raise ValidationError("Nalog sa ovom e-mail adresom već postoji.")
        return email

    def clean(self):
        """Proverava podudaranje i jačinu lozinke."""

        cleaned = super().clean()
        password = cleaned.get("lozinka")
        confirmation = cleaned.get("potvrda_lozinke")
        if password and confirmation and password != confirmation:
            self.add_error("potvrda_lozinke", "Lozinke se ne podudaraju.")
        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error("lozinka", exc)
        return cleaned


class TrkaForm(StyledFormMixin, forms.ModelForm):
    """Unos i izmena trke bez menjanja njenog organizatora kroz formu."""

    class Meta:
        """Povezuje formu sa modelom i ograničava dozvoljena polja."""
        model = Trka
        fields = (
            "naziv_trke",
            "staza",
            "drzava",
            "datum_odrzavanja",
            "sampionat",
        )
        labels = {
            "naziv_trke": "Naziv trke",
            "staza": "Staza",
            "drzava": "Država",
            "datum_odrzavanja": "Datum održavanja",
            "sampionat": "Šampionat",
        }
        widgets = {"datum_odrzavanja": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        """Inicijalizuje objekat i prilagođava polja trenutnom kontekstu."""
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["naziv_trke"].widget.attrs["data-testid"] = "race-name"
        self.fields["datum_odrzavanja"].widget.attrs["data-testid"] = "race-date"

    def clean_naziv_trke(self) -> str:
        """Uklanja višak razmaka iz naziva."""

        return " ".join(self.cleaned_data["naziv_trke"].split())

    def clean(self):
        """Sprečava duplu trku istog šampionata na isti datum."""

        cleaned = super().clean()
        name = cleaned.get("naziv_trke")
        race_date = cleaned.get("datum_odrzavanja")
        championship = cleaned.get("sampionat")
        if name and race_date and championship:
            duplicates = Trka.objects.filter(
                naziv_trke__iexact=name,
                datum_odrzavanja=race_date,
                sampionat=championship,
            )
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise ValidationError(
                    "Trka sa ovim nazivom, datumom i šampionatom već postoji."
                )
        return cleaned


class SektorForm(StyledFormMixin, forms.ModelForm):
    """Unos sektora uz očuvanje broja već prodatih mesta pri izmeni."""

    class Meta:
        """Povezuje formu sa modelom i ograničava dozvoljena polja."""
        model = Sektor
        fields = ("naziv_sektora", "ukupni_kapacitet", "cena_karte")
        labels = {
            "naziv_sektora": "Naziv sektora",
            "ukupni_kapacitet": "Ukupan kapacitet",
            "cena_karte": "Cena karte (EUR)",
        }
        widgets = {
            "ukupni_kapacitet": forms.NumberInput(attrs={"min": 1}),
            "cena_karte": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        """Inicijalizuje objekat i prilagođava polja trenutnom kontekstu."""
        super().__init__(*args, **kwargs)
        self._original_sold = self.instance.broj_prodatih if self.instance.pk else 0
        self.apply_styles()

    def clean_ukupni_kapacitet(self) -> int:
        """Ne dozvoljava kapacitet manji od broja prodatih karata."""

        capacity = self.cleaned_data["ukupni_kapacitet"]
        if self.instance.pk and capacity < self._original_sold:
            raise ValidationError(
                f"Kapacitet ne može biti manji od {self._original_sold}, "
                "jer je toliko karata već prodato."
            )
        return capacity

    def save(self, commit: bool = True):
        """Podešava slobodna mesta tako da se broj prodatih ne promeni."""

        sector = super().save(commit=False)
        sector.slobodna_mesta = sector.ukupni_kapacitet - self._original_sold
        if commit:
            sector.save()
        return sector


class SmestajForm(StyledFormMixin, forms.ModelForm):
    """Unos agregiranog smeštaja tačno prema šemi baze."""

    class Meta:
        """Povezuje formu sa modelom i ograničava dozvoljena polja."""
        model = Smestaj
        fields = (
            "id_trke",
            "naziv_smestaja",
            "lokacija",
            "udaljenost_od_staze",
            "broj_slobodnih_soba",
            "cena_po_nocenju",
        )
        labels = {
            "id_trke": "Trka",
            "naziv_smestaja": "Naziv smeštaja",
            "lokacija": "Lokacija",
            "udaljenost_od_staze": "Udaljenost od staze (km)",
            "broj_slobodnih_soba": "Broj slobodnih soba",
            "cena_po_nocenju": "Cena po noćenju (EUR)",
        }
        widgets = {
            "udaljenost_od_staze": forms.NumberInput(
                attrs={"min": "0", "step": "0.01"}
            ),
            "broj_slobodnih_soba": forms.NumberInput(attrs={"min": 0}),
            "cena_po_nocenju": forms.NumberInput(
                attrs={"min": "0.01", "step": "0.01"}
            ),
        }

    def __init__(self, *args, **kwargs):
        """Inicijalizuje objekat i prilagođava polja trenutnom kontekstu."""
        super().__init__(*args, **kwargs)
        self.apply_styles()
        upcoming = Trka.objects.filter(datum_odrzavanja__gte=date.today())
        if self.instance.pk and self.instance.id_trke_id:
            upcoming = Trka.objects.filter(
                pk__in=list(upcoming.values_list("pk", flat=True))
                + [self.instance.id_trke_id]
            )
        self.fields["id_trke"].queryset = upcoming.select_related(
            "id_organizatora"
        ).order_by("datum_odrzavanja")


class PackageForm(StyledFormMixin, forms.Form):
    """Bira sektor i smeštaj iste trke za jedan paket."""

    id_sektora = forms.ModelChoiceField(
        label="Sektor", queryset=Sektor.objects.none(), empty_label=None
    )
    id_smestaja = forms.ModelChoiceField(
        label="Smeštaj", queryset=Smestaj.objects.none(), empty_label=None
    )

    def __init__(self, *args, race: Trka, **kwargs):
        """Inicijalizuje objekat i prilagođava polja trenutnom kontekstu."""
        super().__init__(*args, **kwargs)
        self.race = race
        self.fields["id_sektora"].queryset = race.sektori.filter(
            slobodna_mesta__gt=0
        ).order_by("cena_karte", "naziv_sektora")
        self.fields["id_smestaja"].queryset = race.smestaji.filter(
            broj_slobodnih_soba__gt=0
        ).order_by("cena_po_nocenju", "udaljenost_od_staze")
        self.apply_styles()
        self.fields["id_sektora"].widget.attrs["data-testid"] = "package-sector"
        self.fields["id_smestaja"].widget.attrs["data-testid"] = "package-accommodation"

    def clean(self):
        """Ponovo proverava pripadnost i raspoloživost server-side."""

        cleaned = super().clean()
        sector = cleaned.get("id_sektora")
        accommodation = cleaned.get("id_smestaja")
        if sector and sector.id_trke_id != self.race.pk:
            self.add_error("id_sektora", "Izabrani sektor ne pripada ovoj trci.")
        if accommodation and accommodation.id_trke_id != self.race.pk:
            self.add_error("id_smestaja", "Izabrani smeštaj ne pripada ovoj trci.")
        if sector and sector.slobodna_mesta < 1:
            self.add_error("id_sektora", "U sektoru više nema slobodnih mesta.")
        if accommodation and accommodation.broj_slobodnih_soba < 1:
            self.add_error("id_smestaja", "U smeštaju više nema slobodnih soba.")
        return cleaned


class RecenzijaForm(StyledFormMixin, forms.ModelForm):
    """Ocena smeštaja i organizatora završene rezervacije."""

    class Meta:
        """Povezuje formu sa modelom i ograničava dozvoljena polja."""
        model = Recenzija
        fields = (
            "ocena_smestaja",
            "komentar_smestaja",
            "ocena_organizatora",
            "komentar_organizatora",
        )
        labels = {
            "ocena_smestaja": "Ocena smeštaja",
            "komentar_smestaja": "Komentar smeštaja",
            "ocena_organizatora": "Ocena organizatora",
            "komentar_organizatora": "Komentar organizatora",
        }
        widgets = {
            "ocena_smestaja": forms.Select(choices=[(i, i) for i in range(1, 6)]),
            "ocena_organizatora": forms.Select(choices=[(i, i) for i in range(1, 6)]),
            "komentar_smestaja": forms.Textarea(attrs={"rows": 3}),
            "komentar_organizatora": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        """Inicijalizuje objekat i prilagođava polja trenutnom kontekstu."""
        super().__init__(*args, **kwargs)
        self.apply_styles()
