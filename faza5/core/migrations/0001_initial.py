# Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    """Kreira početnu Django šemu koja odgovara sedam tabela baze faze 4."""
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Korisnik',
            fields=[
                ('id_korisnika', models.AutoField(primary_key=True, serialize=False)),
                ('ime', models.CharField(max_length=50)),
                ('prezime', models.CharField(max_length=50)),
                ('email', models.CharField(max_length=100, unique=True)),
                ('lozinka', models.CharField(max_length=255)),
                ('uloga', models.CharField(choices=[('Kupac', 'Kupac'), ('Organizator', 'Organizator'), ('Hotelijer', 'Hotelijer'), ('Administrator', 'Administrator')], max_length=13)),
                ('status_naloga', models.CharField(choices=[('Aktivno', 'Aktivno'), ('Suspendovano', 'Suspendovano')], default='Aktivno', max_length=12)),
            ],
            options={
                'verbose_name': 'korisnik',
                'verbose_name_plural': 'korisnici',
                'db_table': 'korisnik',
                'ordering': ('prezime', 'ime', 'email'),
            },
        ),
        migrations.CreateModel(
            name='Sektor',
            fields=[
                ('id_sektora', models.AutoField(primary_key=True, serialize=False)),
                ('naziv_sektora', models.CharField(max_length=50)),
                ('ukupni_kapacitet', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('slobodna_mesta', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('cena_karte', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
            ],
            options={
                'verbose_name': 'sektor',
                'verbose_name_plural': 'sektori',
                'db_table': 'sektor',
                'ordering': ('naziv_sektora',),
            },
        ),
        migrations.CreateModel(
            name='Rezervacija',
            fields=[
                ('id_rezervacije', models.AutoField(primary_key=True, serialize=False)),
                ('datum_kreiranja', models.DateTimeField(default=django.utils.timezone.now)),
                ('ukupna_cena', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status_rezervacije', models.CharField(choices=[('U_korpi', 'U korpi'), ('Aktivna', 'Aktivna'), ('Zavrsena', 'Završena'), ('Otkazana', 'Otkazana')], default='U_korpi', max_length=8)),
                ('id_kupca', models.ForeignKey(db_column='id_kupca', on_delete=django.db.models.deletion.CASCADE, related_name='rezervacije', to='core.korisnik')),
                ('id_sektora', models.ForeignKey(db_column='id_sektora', on_delete=django.db.models.deletion.PROTECT, related_name='rezervacije', to='core.sektor')),
            ],
            options={
                'verbose_name': 'rezervacija',
                'verbose_name_plural': 'rezervacije',
                'db_table': 'rezervacija',
                'ordering': ('-datum_kreiranja',),
            },
        ),
        migrations.CreateModel(
            name='Recenzija',
            fields=[
                ('id_recenzije', models.AutoField(primary_key=True, serialize=False)),
                ('ocena_smestaja', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('komentar_smestaja', models.TextField(blank=True, null=True)),
                ('ocena_organizatora', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('komentar_organizatora', models.TextField(blank=True, null=True)),
                ('datum_objave', models.DateTimeField(default=django.utils.timezone.now)),
                ('id_kupca', models.ForeignKey(db_column='id_kupca', on_delete=django.db.models.deletion.CASCADE, related_name='recenzije', to='core.korisnik')),
                ('id_rezervacije', models.OneToOneField(db_column='id_rezervacije', on_delete=django.db.models.deletion.CASCADE, related_name='recenzija', to='core.rezervacija')),
            ],
            options={
                'verbose_name': 'recenzija',
                'verbose_name_plural': 'recenzije',
                'db_table': 'recenzija',
                'ordering': ('-datum_objave',),
            },
        ),
        migrations.CreateModel(
            name='DigitalniVaucer',
            fields=[
                ('id_vaucera', models.AutoField(primary_key=True, serialize=False)),
                ('qr_kod', models.CharField(max_length=255, unique=True)),
                ('status_vaucera', models.CharField(choices=[('Validan', 'Validan'), ('Iskoriscen_Staza', 'Iskorišćen na stazi'), ('Iskoriscen_Hotel', 'Iskorišćen u hotelu'), ('Iskoriscen_Sve', 'U potpunosti iskorišćen')], default='Validan', max_length=16)),
                ('id_rezervacije', models.OneToOneField(db_column='id_rezervacije', on_delete=django.db.models.deletion.CASCADE, related_name='vaucer', to='core.rezervacija')),
            ],
            options={
                'verbose_name': 'digitalni vaučer',
                'verbose_name_plural': 'digitalni vaučeri',
                'db_table': 'digitalni_vaucer',
            },
        ),
        migrations.CreateModel(
            name='Smestaj',
            fields=[
                ('id_smestaja', models.AutoField(primary_key=True, serialize=False)),
                ('naziv_smestaja', models.CharField(max_length=100)),
                ('lokacija', models.CharField(max_length=255)),
                ('udaljenost_od_staze', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('broj_slobodnih_soba', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('cena_po_nocenju', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('id_hotelijera', models.ForeignKey(db_column='id_hotelijera', on_delete=django.db.models.deletion.PROTECT, related_name='smestaji', to='core.korisnik')),
            ],
            options={
                'verbose_name': 'smeštaj',
                'verbose_name_plural': 'smeštaji',
                'db_table': 'smestaj',
                'ordering': ('udaljenost_od_staze', 'naziv_smestaja'),
            },
        ),
        migrations.AddField(
            model_name='rezervacija',
            name='id_smestaja',
            field=models.ForeignKey(db_column='id_smestaja', on_delete=django.db.models.deletion.PROTECT, related_name='rezervacije', to='core.smestaj'),
        ),
        migrations.CreateModel(
            name='Trka',
            fields=[
                ('id_trke', models.AutoField(primary_key=True, serialize=False)),
                ('naziv_trke', models.CharField(max_length=100)),
                ('staza', models.CharField(max_length=100)),
                ('drzava', models.CharField(max_length=50)),
                ('datum_odrzavanja', models.DateField()),
                ('sampionat', models.CharField(choices=[('F1', 'Formula 1'), ('MotoGP', 'MotoGP'), ('WSBK', 'WSBK')], max_length=6)),
                ('id_organizatora', models.ForeignKey(db_column='id_organizatora', on_delete=django.db.models.deletion.PROTECT, related_name='trke', to='core.korisnik')),
            ],
            options={
                'verbose_name': 'trka',
                'verbose_name_plural': 'trke',
                'db_table': 'trka',
                'ordering': ('datum_odrzavanja', 'naziv_trke'),
            },
        ),
        migrations.AddField(
            model_name='smestaj',
            name='id_trke',
            field=models.ForeignKey(db_column='id_trke', on_delete=django.db.models.deletion.CASCADE, related_name='smestaji', to='core.trka'),
        ),
        migrations.AddField(
            model_name='sektor',
            name='id_trke',
            field=models.ForeignKey(db_column='id_trke', on_delete=django.db.models.deletion.CASCADE, related_name='sektori', to='core.trka'),
        ),
    ]
