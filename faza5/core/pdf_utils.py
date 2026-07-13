# Autor:  Milica Štavljanin 0391/2023;

"""Generisanje digitalnog vaučera kao PDF dokumenta."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .models import DigitalniVaucer

_FONT_REGULAR = "HubSans"
_FONT_BOLD = "HubSans-Bold"
_FONTS_REGISTERED = False


def _register_fonts() -> tuple[str, str]:
    """Registruje Unicode fontove dostupne na sistemu, uz bezbedan fallback."""

    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return _FONT_REGULAR, _FONT_BOLD

    candidates = [
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
        (
            Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
        ),
    ]
    for regular_path, bold_path in candidates:
        if regular_path.exists() and bold_path.exists():
            pdfmetrics.registerFont(TTFont(_FONT_REGULAR, str(regular_path)))
            pdfmetrics.registerFont(TTFont(_FONT_BOLD, str(bold_path)))
            _FONTS_REGISTERED = True
            return _FONT_REGULAR, _FONT_BOLD

    # Helvetica je podržana u svakom PDF čitaču, ali nema sva srpska slova.
    return "Helvetica", "Helvetica-Bold"


def _fit_text(pdf: canvas.Canvas, value: str, max_width: float, font: str, size: int) -> str:
    """Skraćuje predugačku vrednost tako da ostane unutar A4 stranice."""

    text = str(value)
    if pdf.stringWidth(text, font, size) <= max_width:
        return text
    ellipsis = "..."
    while text and pdf.stringWidth(text + ellipsis, font, size) > max_width:
        text = text[:-1]
    return f"{text}{ellipsis}"


def build_voucher_pdf(voucher: DigitalniVaucer) -> bytes:
    """Vraća PDF vaucer sa podacima rezervacije i QR kodom."""

    regular_font, bold_font = _register_fonts()
    reservation = voucher.id_rezervacije
    buyer = reservation.id_kupca
    race = reservation.id_sektora.id_trke

    qr_buffer = BytesIO()
    qr_image = qrcode.make(voucher.qr_kod)
    qr_image.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    pdf.setTitle(f"Digitalni vaucer #{voucher.id_vaucera}")
    pdf.setAuthor("Milan Lemić; Milica Štavljanin; Marko Mandić")

    pdf.setFillColor(colors.HexColor("#0B1F3A"))
    pdf.rect(0, height - 115, width, 115, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont(bold_font, 22)
    pdf.drawString(42, height - 55, "AUTOMOTOSPORT TRAVEL HUB")
    pdf.setFont(regular_font, 12)
    pdf.drawString(42, height - 82, "Digitalni vaucer za trku i smeštaj")

    pdf.setFillColor(colors.HexColor("#20242A"))
    pdf.setFont(bold_font, 15)
    pdf.drawString(42, height - 155, f"Vaucer #{voucher.id_vaucera}")
    details = [
        ("Kupac", buyer.puno_ime),
        ("Trka", race.naziv_trke),
        ("Šampionat", race.sampionat),
        ("Staza", race.staza),
        ("Država", race.drzava),
        ("Datum", race.datum_odrzavanja.strftime("%d.%m.%Y.")),
        ("Sektor", reservation.id_sektora.naziv_sektora),
        ("Smeštaj", reservation.id_smestaja.naziv_smestaja),
        ("Lokacija", reservation.id_smestaja.lokacija),
        ("Ukupna cena", f"{reservation.ukupna_cena:.2f} EUR"),
        ("Status vaucera", voucher.get_status_vaucera_display()),
    ]
    y = height - 190
    value_x = 145
    max_value_width = width - value_x - 42
    for label, value in details:
        pdf.setFont(bold_font, 10)
        pdf.drawString(42, y, f"{label}:")
        pdf.setFont(regular_font, 10)
        pdf.drawString(
            value_x,
            y,
            _fit_text(pdf, str(value), max_value_width, regular_font, 10),
        )
        y -= 23

    pdf.setStrokeColor(colors.HexColor("#D7DCE2"))
    pdf.line(42, y + 7, width - 42, y + 7)
    pdf.drawImage(ImageReader(qr_buffer), width - 205, height - 410, 155, 155)
    pdf.setFont(regular_font, 8)
    pdf.drawCentredString(width - 127, height - 425, voucher.qr_kod)

    pdf.setFillColor(colors.HexColor("#D11A2A"))
    pdf.setFont(bold_font, 10)
    pdf.drawString(42, 78, "Vaucer je jedinstven i vezan za navedenu rezervaciju.")
    pdf.setFillColor(colors.HexColor("#5B6573"))
    pdf.setFont(regular_font, 8)
    pdf.drawString(
        42,
        58,
        "Dokument je automatski generisan iz podataka relacione baze projekta.",
    )
    pdf.showPage()
    pdf.save()
    return output.getvalue()
