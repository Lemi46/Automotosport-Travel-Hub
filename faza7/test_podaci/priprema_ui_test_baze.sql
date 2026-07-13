-- Faza 7 - deterministički podaci za Selenium IDE/WebDriver testove.
-- Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023.
--
-- Pokrenuti u MySQL Workbench-u NAKON skripte:
-- ../../faza5/database/automotosport_travel_hub.sql
--
-- Svi UI nalozi koriste lozinku: Test12345!

USE `automotosport_travel_hub`;
SET FOREIGN_KEY_CHECKS = 0;
SET SQL_SAFE_UPDATES = 0;

-- Brišu se isključivo podaci rezervisani za automatizovano testiranje.
DELETE FROM `recenzija` WHERE `id_recenzije` BETWEEN 9701 AND 9799;
DELETE FROM `digitalni_vaucer` WHERE `id_vaucera` BETWEEN 9601 AND 9699;
DELETE FROM `rezervacija` WHERE `id_rezervacije` BETWEEN 9501 AND 9599;
DELETE FROM `smestaj` WHERE `id_smestaja` BETWEEN 9401 AND 9499;
DELETE FROM `sektor` WHERE `id_sektora` BETWEEN 9301 AND 9399;
DELETE FROM `trka` WHERE `id_trke` BETWEEN 9201 AND 9299;
DELETE FROM `korisnik`
WHERE `id_korisnika` BETWEEN 9101 AND 9199
   OR `email` LIKE 'ui.%@hub.test';

-- Hash je generisan Django PBKDF2 hasher-om za lozinku Test12345!.
INSERT INTO `korisnik`
(`id_korisnika`, `ime`, `prezime`, `email`, `lozinka`, `uloga`, `status_naloga`)
VALUES
(9101, 'UI', 'Administrator', 'ui.admin@hub.test',
 'pbkdf2_sha256$1200000$bDowoN1r25WwpjwZOi0l7r$8hTZh5VAIoHIuIjpy/p1PId/qN3NB6mFRvILwfeC4b0=',
 'Administrator', 'Aktivno'),
(9102, 'UI', 'Kupac', 'ui.kupac@hub.test',
 'pbkdf2_sha256$1200000$bDowoN1r25WwpjwZOi0l7r$8hTZh5VAIoHIuIjpy/p1PId/qN3NB6mFRvILwfeC4b0=',
 'Kupac', 'Aktivno'),
(9103, 'UI', 'Organizator', 'ui.organizator@hub.test',
 'pbkdf2_sha256$1200000$bDowoN1r25WwpjwZOi0l7r$8hTZh5VAIoHIuIjpy/p1PId/qN3NB6mFRvILwfeC4b0=',
 'Organizator', 'Aktivno'),
(9104, 'UI', 'Hotelijer', 'ui.hotelijer@hub.test',
 'pbkdf2_sha256$1200000$bDowoN1r25WwpjwZOi0l7r$8hTZh5VAIoHIuIjpy/p1PId/qN3NB6mFRvILwfeC4b0=',
 'Hotelijer', 'Aktivno'),
(9105, 'UI', 'Suspendovan', 'ui.suspendovan@hub.test',
 'pbkdf2_sha256$1200000$bDowoN1r25WwpjwZOi0l7r$8hTZh5VAIoHIuIjpy/p1PId/qN3NB6mFRvILwfeC4b0=',
 'Kupac', 'Suspendovano'),
(9106, 'UI', 'Ciljni nalog', 'ui.target@hub.test',
 'pbkdf2_sha256$1200000$bDowoN1r25WwpjwZOi0l7r$8hTZh5VAIoHIuIjpy/p1PId/qN3NB6mFRvILwfeC4b0=',
 'Kupac', 'Aktivno');

INSERT INTO `trka`
(`id_trke`, `id_organizatora`, `naziv_trke`, `staza`, `drzava`, `datum_odrzavanja`, `sampionat`)
VALUES
(9201, 9103, 'UI Test WSBK 2099', 'UI Test Staza', 'UI Srbija', '2099-05-20', 'WSBK'),
(9202, 9103, 'UI Test F1 2099', 'UI Formula Staza', 'UI Italija', '2099-06-20', 'F1'),
(9203, 9103, 'UI Završena MotoGP trka', 'UI Stara Staza', 'UI Portugal', '2025-03-20', 'MotoGP');

INSERT INTO `sektor`
(`id_sektora`, `id_trke`, `naziv_sektora`, `ukupni_kapacitet`, `slobodna_mesta`, `cena_karte`)
VALUES
(9301, 9201, 'UI Glavna tribina', 40, 39, 120.00),
(9302, 9202, 'UI F1 tribina', 30, 30, 180.00),
(9303, 9203, 'UI Završena tribina', 25, 24, 100.00);

INSERT INTO `smestaj`
(`id_smestaja`, `id_hotelijera`, `id_trke`, `naziv_smestaja`, `lokacija`,
 `udaljenost_od_staze`, `broj_slobodnih_soba`, `cena_po_nocenju`)
VALUES
(9401, 9104, 9201, 'UI Trackside Hotel', 'UI Centar', 2.50, 19, 95.00),
(9402, 9104, 9202, 'UI Formula Hotel', 'UI Monca', 4.00, 20, 130.00),
(9403, 9104, 9203, 'UI Istorijski Hotel', 'UI Porto', 3.00, 14, 80.00);

-- Aktivna, završena i korpa omogućavaju ponovljive testove istorije, PDF-a i plaćanja.
INSERT INTO `rezervacija`
(`id_rezervacije`, `id_kupca`, `id_sektora`, `id_smestaja`, `datum_kreiranja`,
 `ukupna_cena`, `status_rezervacije`)
VALUES
(9501, 9102, 9301, 9401, '2026-07-01 10:00:00', 215.00, 'Aktivna'),
(9502, 9102, 9303, 9403, '2025-02-01 10:00:00', 180.00, 'Zavrsena'),
(9503, 9102, 9301, 9401, '2026-07-12 10:00:00', 215.00, 'U_korpi');

INSERT INTO `digitalni_vaucer`
(`id_vaucera`, `id_rezervacije`, `qr_kod`, `status_vaucera`)
VALUES
(9601, 9501, 'UI-AKTIVNI-VAUCER-9501', 'Validan'),
(9602, 9502, 'UI-ZAVRSENI-VAUCER-9502', 'Iskoriscen_Sve');

SET FOREIGN_KEY_CHECKS = 1;
SET SQL_SAFE_UPDATES = 1;
