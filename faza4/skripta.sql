-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema automotosport_travel_hub
-- -----------------------------------------------------

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
