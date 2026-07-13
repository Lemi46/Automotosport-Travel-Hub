-- Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;
-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema automotosport_travel_hub
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `automotosport_travel_hub` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ;
USE `automotosport_travel_hub` ;

-- -----------------------------------------------------
-- Table `automotosport_travel_hub`.`korisnik`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `automotosport_travel_hub`.`korisnik` (
  `id_korisnika` INT NOT NULL AUTO_INCREMENT,
  `ime` VARCHAR(50) NOT NULL,
  `prezime` VARCHAR(50) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `lozinka` VARCHAR(255) NOT NULL,
  `uloga` ENUM('Kupac', 'Organizator', 'Hotelijer', 'Administrator') NOT NULL,
  `status_naloga` ENUM('Aktivno', 'Suspendovano') NOT NULL DEFAULT 'Aktivno',
  PRIMARY KEY (`id_korisnika`),
  UNIQUE INDEX `UQ_Korisnik_Email` (`email` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Table `automotosport_travel_hub`.`trka`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `automotosport_travel_hub`.`trka` (
  `id_trke` INT NOT NULL AUTO_INCREMENT,
  `id_organizatora` INT NOT NULL,
  `naziv_trke` VARCHAR(100) NOT NULL,
  `staza` VARCHAR(100) NOT NULL,
  `drzava` VARCHAR(50) NOT NULL,
  `datum_odrzavanja` DATE NOT NULL,
  `sampionat` ENUM('F1', 'MotoGP', 'WSBK') NOT NULL,
  PRIMARY KEY (`id_trke`),
  INDEX `FK_Trka_Organizator` (`id_organizatora` ASC) VISIBLE,
  CONSTRAINT `FK_Trka_Organizator`
    FOREIGN KEY (`id_organizatora`)
    REFERENCES `automotosport_travel_hub`.`korisnik` (`id_korisnika`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Table `automotosport_travel_hub`.`sektor`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `automotosport_travel_hub`.`sektor` (
  `id_sektora` INT NOT NULL AUTO_INCREMENT,
  `id_trke` INT NOT NULL,
  `naziv_sektora` VARCHAR(50) NOT NULL,
  `ukupni_kapacitet` INT NOT NULL,
  `slobodna_mesta` INT NOT NULL,
  `cena_karte` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`id_sektora`),
  INDEX `FK_Sektor_Trka` (`id_trke` ASC) VISIBLE,
  CONSTRAINT `FK_Sektor_Trka`
    FOREIGN KEY (`id_trke`)
    REFERENCES `automotosport_travel_hub`.`trka` (`id_trke`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Table `automotosport_travel_hub`.`smestaj`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `automotosport_travel_hub`.`smestaj` (
  `id_smestaja` INT NOT NULL AUTO_INCREMENT,
  `id_hotelijera` INT NOT NULL,
  `id_trke` INT NOT NULL,
  `naziv_smestaja` VARCHAR(100) NOT NULL,
  `lokacija` VARCHAR(255) NOT NULL,
  `udaljenost_od_staze` DECIMAL(5,2) NOT NULL,
  `broj_slobodnih_soba` INT NOT NULL,
  `cena_po_nocenju` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`id_smestaja`),
  INDEX `FK_Smestaj_Hotelijer` (`id_hotelijera` ASC) VISIBLE,
  INDEX `FK_Smestaj_Trka` (`id_trke` ASC) VISIBLE,
  CONSTRAINT `FK_Smestaj_Hotelijer`
    FOREIGN KEY (`id_hotelijera`)
    REFERENCES `automotosport_travel_hub`.`korisnik` (`id_korisnika`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `FK_Smestaj_Trka`
    FOREIGN KEY (`id_trke`)
    REFERENCES `automotosport_travel_hub`.`trka` (`id_trke`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Table `automotosport_travel_hub`.`rezervacija`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `automotosport_travel_hub`.`rezervacija` (
  `id_rezervacije` INT NOT NULL AUTO_INCREMENT,
  `id_kupca` INT NOT NULL,
  `id_sektora` INT NOT NULL,
  `id_smestaja` INT NOT NULL,
  `datum_kreiranja` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ukupna_cena` DECIMAL(10,2) NOT NULL,
  `status_rezervacije` ENUM('U_korpi', 'Aktivna', 'Zavrsena', 'Otkazana') NOT NULL DEFAULT 'U_korpi',
  PRIMARY KEY (`id_rezervacije`),
  INDEX `FK_Rezervacija_Kupac` (`id_kupca` ASC) VISIBLE,
  INDEX `FK_Rezervacija_Sektor` (`id_sektora` ASC) VISIBLE,
  INDEX `FK_Rezervacija_Smestaj` (`id_smestaja` ASC) VISIBLE,
  CONSTRAINT `FK_Rezervacija_Kupac`
    FOREIGN KEY (`id_kupca`)
    REFERENCES `automotosport_travel_hub`.`korisnik` (`id_korisnika`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `FK_Rezervacija_Sektor`
    FOREIGN KEY (`id_sektora`)
    REFERENCES `automotosport_travel_hub`.`sektor` (`id_sektora`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `FK_Rezervacija_Smestaj`
    FOREIGN KEY (`id_smestaja`)
    REFERENCES `automotosport_travel_hub`.`smestaj` (`id_smestaja`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Table `automotosport_travel_hub`.`digitalni_vaucer`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `automotosport_travel_hub`.`digitalni_vaucer` (
  `id_vaucera` INT NOT NULL AUTO_INCREMENT,
  `id_rezervacije` INT NOT NULL,
  `qr_kod` VARCHAR(255) NOT NULL,
  `status_vaucera` ENUM('Validan', 'Iskoriscen_Staza', 'Iskoriscen_Hotel', 'Iskoriscen_Sve') NOT NULL DEFAULT 'Validan',
  PRIMARY KEY (`id_vaucera`),
  UNIQUE INDEX `UQ_Vaucer_Rezervacija` (`id_rezervacije` ASC) VISIBLE,
  UNIQUE INDEX `UQ_Vaucer_QR` (`qr_kod` ASC) VISIBLE,
  CONSTRAINT `FK_DigitalniVaucer_Rezervacija`
    FOREIGN KEY (`id_rezervacije`)
    REFERENCES `automotosport_travel_hub`.`rezervacija` (`id_rezervacije`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------
-- Table `automotosport_travel_hub`.`recenzija`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `automotosport_travel_hub`.`recenzija` (
  `id_recenzije` INT NOT NULL AUTO_INCREMENT,
  `id_rezervacije` INT NOT NULL,
  `id_kupca` INT NOT NULL,
  `ocena_smestaja` INT NOT NULL,
  `komentar_smestaja` TEXT NULL DEFAULT NULL,
  `ocena_organizatora` INT NOT NULL,
  `komentar_organizatora` TEXT NULL DEFAULT NULL,
  `datum_objave` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_recenzije`),
  UNIQUE INDEX `UQ_Recenzija_Rezervacija` (`id_rezervacije` ASC) VISIBLE,
  INDEX `FK_Recenzija_Kupac` (`id_kupca` ASC) VISIBLE,
  CONSTRAINT `FK_Recenzija_Kupac`
    FOREIGN KEY (`id_kupca`)
    REFERENCES `automotosport_travel_hub`.`korisnik` (`id_korisnika`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `FK_Recenzija_Rezervacija`
    FOREIGN KEY (`id_rezervacije`)
    REFERENCES `automotosport_travel_hub`.`rezervacija` (`id_rezervacije`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

-- -----------------------------------------------------
-- Demonstracioni podaci pete faze
-- Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023;
-- -----------------------------------------------------
USE `automotosport_travel_hub`;
SET FOREIGN_KEY_CHECKS=0;
SET SQL_SAFE_UPDATES = 0;
DELETE FROM `recenzija`;
DELETE FROM `digitalni_vaucer`;
DELETE FROM `rezervacija`;
DELETE FROM `smestaj`;
DELETE FROM `sektor`;
DELETE FROM `trka`;
DELETE FROM `korisnik`;
INSERT INTO `korisnik` (`id_korisnika`, `ime`, `prezime`, `email`, `lozinka`, `uloga`, `status_naloga`) VALUES
  (1, 'Ana', 'Administrator', 'admin@hub.rs', 'pbkdf2_sha256$1200000$OpOwEwnJb7TLybmKLT7qdi$83bjAmctAm3KybbdHhKNNrqw4Kkx/Zp/rvtXmpl9Ecs=', 'Administrator', 'Aktivno'),
  (2, 'Katarina', 'Kupac', 'kupac@hub.rs', 'pbkdf2_sha256$1200000$v14NKcEaobV40HH0xQj6gl$zp7F+fiwLraGIqyXNod6IJ7hoE1AxLoXuEz4q6zbxlM=', 'Kupac', 'Aktivno'),
  (3, 'Nikola', 'Navijač', 'kupac2@hub.rs', 'pbkdf2_sha256$1200000$p0CeUCKX0LxOSpdKig4HQM$fqAXUG8q6TEoOGFEHX9Z+YPr4SzXxLFq9MX+GpO3H9s=', 'Kupac', 'Aktivno'),
  (4, 'Ognjen', 'Organizator', 'organizator@hub.rs', 'pbkdf2_sha256$1200000$gJZIs2dQDGGTkmV01ZfG19$W7GH9Lc0256t9u2wKYzVquINjmMfW3X1wBaR0FhOf9Q=', 'Organizator', 'Aktivno'),
  (5, 'Helena', 'Hotelijer', 'hotelijer@hub.rs', 'pbkdf2_sha256$1200000$idTw6oBMCrpQvIp2hb5S0W$pb7uEUlPSGb4LM/i8xfXYait1/SKgDSSKurU9MdkRaA=', 'Hotelijer', 'Aktivno');
INSERT INTO `trka` (`id_trke`, `id_organizatora`, `naziv_trke`, `staza`, `drzava`, `datum_odrzavanja`, `sampionat`) VALUES
  (1, 4, 'WSBK Australije', 'Phillip Island Grand Prix Circuit', 'Australija', '2026-02-22', 'WSBK'),
  (2, 4, 'WSBK Holandije', 'TT Circuit Assen', 'Holandija', '2026-04-19', 'WSBK'),
  (3, 4, 'WSBK Italije', 'Misano World Circuit', 'Italija', '2026-06-14', 'WSBK'),
  (4, 4, 'WSBK Velike Britanije', 'Donington Park', 'Velika Britanija', '2026-07-25', 'WSBK'),
  (5, 4, 'WSBK Češke', 'Autodrom Most', 'Češka', '2026-08-09', 'WSBK'),
  (6, 4, 'WSBK Portugala', 'Algarve International Circuit', 'Portugal', '2026-09-06', 'WSBK'),
  (7, 4, 'WSBK Francuske', 'Circuit de Nevers Magny-Cours', 'Francuska', '2026-09-27', 'WSBK'),
  (8, 4, 'WSBK Španije', 'Circuito de Jerez', 'Španija', '2026-10-18', 'WSBK');

INSERT INTO `sektor` (`id_sektora`, `id_trke`, `naziv_sektora`, `ukupni_kapacitet`, `slobodna_mesta`, `cena_karte`) VALUES
  (1, 1, 'Glavna tribina', 500, 498, 150.00),
  (2, 1, 'Paddock Pass', 200, 200, 250.00),
  (3, 2, 'Glavna tribina', 600, 600, 140.00),
  (4, 2, 'Tribina B', 300, 300, 90.00),
  (5, 3, 'Glavna tribina', 500, 497, 155.00),
  (6, 3, 'Paddock Pass', 150, 150, 260.00),
  (7, 4, 'Glavna tribina', 400, 399, 140.00),
  (8, 4, 'Stajanje (General Adm.)', 1000, 1000, 75.00),
  (9, 5, 'Glavna tribina', 350, 349, 160.00),
  (10, 5, 'Tribina T1', 250, 250, 110.00),
  (11, 6, 'Glavna tribina', 500, 500, 145.00),
  (12, 6, 'Tribina B', 300, 300, 95.00),
  (13, 7, 'Glavna tribina', 450, 450, 150.00),
  (14, 7, 'Paddock Pass', 200, 200, 270.00),
  (15, 8, 'Glavna tribina', 600, 600, 135.00),
  (16, 8, 'Tribina X', 400, 400, 85.00);

INSERT INTO `smestaj` (`id_smestaja`, `id_hotelijera`, `id_trke`, `naziv_smestaja`, `lokacija`, `udaljenost_od_staze`, `broj_slobodnih_soba`, `cena_po_nocenju`) VALUES
  (1, 5, 1, 'Phillip Island Resort', 'Obala, Australija', 2.50, 14, 120.00),
  (2, 5, 1, 'Cowes Budget Stay', 'Centar grada, Australija', 8.00, 25, 65.00),
  (3, 5, 2, 'Assen Trackside Hotel', 'Okolina staze, Holandija', 1.50, 10, 130.00),
  (4, 5, 2, 'Groningen Inn', 'Groningen, Holandija', 25.00, 40, 70.00),
  (5, 5, 3, 'Misano Adriatico Spa', 'Rivijera, Italija', 4.00, 12, 100.00),
  (6, 5, 3, 'Rimini Budget Rooms', 'Rimini, Italija', 15.00, 30, 55.00),
  (7, 5, 4, 'Donington Manor', 'Castle Donington, UK', 3.00, 8, 110.00),
  (8, 5, 4, 'Derby Express Hotel', 'Derby, UK', 18.00, 50, 60.00),
  (9, 5, 5, 'Most City Hotel', 'Centar, Češka', 5.50, 19, 130.00),
  (10, 5, 5, 'Prague Airport Stay', 'Prag, Češka', 70.00, 100, 80.00),
  (11, 5, 6, 'Algarve Trackside', 'Portimao, Portugal', 2.00, 15, 90.00),
  (12, 5, 6, 'Faro Beach Resort', 'Faro, Portugal', 65.00, 20, 140.00),
  (13, 5, 7, 'Nevers Classic Hotel', 'Nevers, Francuska', 12.00, 22, 115.00),
  (14, 5, 7, 'Magny-Cours Motel', 'Okolina staze, Francuska', 5.00, 18, 75.00),
  (15, 5, 8, 'Jerez Plaza Hotel', 'Centar, Španija', 10.00, 35, 105.00),
  (16, 5, 8, 'Cadiz Ocean View', 'Kadiz, Španija', 35.00, 28, 150.00);

INSERT INTO `rezervacija` (`id_rezervacije`, `id_kupca`, `id_sektora`, `id_smestaja`, `datum_kreiranja`, `ukupna_cena`, `status_rezervacije`) VALUES
  (1, 2, 1, 1, '2026-01-15 10:30:00', 270.00, 'Zavrsena'),
  (2, 2, 7, 7, '2026-07-01 14:15:00', 250.00, 'Aktivna'),
  (3, 3, 9, 9, '2026-07-12 09:00:00', 290.00, 'U_korpi'),
  (4, 3, 11, 11, '2026-06-20 18:45:00', 235.00, 'Otkazana'),
  (5, 2, 5, 5, '2026-05-10 11:20:00', 255.00, 'Zavrsena');

INSERT INTO `digitalni_vaucer` (`id_vaucera`, `id_rezervacije`, `qr_kod`, `status_vaucera`) VALUES
  (1, 1, 'WSBK-ZAVRSENI-VAUCER-001', 'Iskoriscen_Sve'),
  (2, 2, 'WSBK-AKTIVNI-VAUCER-002', 'Validan'),
  (3, 5, 'WSBK-ZAVRSENI-VAUCER-003', 'Iskoriscen_Sve');

INSERT INTO `recenzija` (`id_recenzije`, `id_rezervacije`, `id_kupca`, `ocena_smestaja`, `komentar_smestaja`, `ocena_organizatora`, `komentar_organizatora`, `datum_objave`) VALUES
  (1, 1, 2, 5, 'Fenomenalan smeštaj, pogled na okean i jako blizu staze.', 5, 'Organizacija u Australiji je uvek besprekorna.', '2026-02-25 12:00:00'),
  (2, 5, 2, 4, 'Hotel je okej, ali je bilo malo gužve oko doručka.', 4, 'Odlična trka, ali su redovi za ulazak bili dugački.', '2026-06-18 09:30:00');
SET FOREIGN_KEY_CHECKS=1;
SET SQL_SAFE_UPDATES = 1;