# Milica Štavljanin 0391/2023  - ukršteno testiranje autentikacije i organizatora.

from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from conftest import login, open_path, wait


def test_wd_l01_registracija_i_prijava_novog_kupca(driver) -> None:
    """SSU 1/10: javna registracija, hashovana lozinka posredno i prijava."""

    open_path(driver, "/auth/")
    waiter = wait(driver)
    email = f"ui.webdriver.{int(time.time() * 1000)}@hub.test"

    Select(
        waiter.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[data-testid="registration-role"]')
            )
        )
    ).select_by_value("Kupac")
    driver.find_element(
        By.CSS_SELECTOR, '[data-testid="registration-first-name"]'
    ).send_keys("WebDriver")
    driver.find_element(
        By.CSS_SELECTOR, '[data-testid="registration-last-name"]'
    ).send_keys("Kupac")
    driver.find_element(
        By.CSS_SELECTOR, '[data-testid="registration-email"]'
    ).send_keys(email)
    driver.find_element(
        By.CSS_SELECTOR, '[data-testid="registration-password"]'
    ).send_keys("DobraLozinka123!")
    driver.find_element(
        By.CSS_SELECTOR, '[data-testid="registration-password-confirm"]'
    ).send_keys("DobraLozinka123!")
    driver.find_element(
        By.CSS_SELECTOR, '[data-testid="registration-submit"]'
    ).click()

    waiter.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Nalog je uspešno kreiran"))
    login(driver, email, "DobraLozinka123!")
    waiter.until(EC.url_contains("/pretraga/"))
    assert "WebDriver · Kupac" in driver.find_element(By.CSS_SELECTOR, ".user-chip").text


def test_wd_l02_organizator_kreira_trku_i_sektor(driver) -> None:
    """SSU 6: organizator kreira sopstvenu trku i njen sektor."""

    login(driver, "ui.organizator@hub.test")
    waiter = wait(driver)
    driver.find_element(By.CSS_SELECTOR, '[data-testid="add-race-link"]').click()

    unique_name = f"UI WD MotoGP {int(time.time() * 1000)}"
    waiter.until(EC.visibility_of_element_located((By.ID, "id_naziv_trke"))).send_keys(unique_name)
    driver.find_element(By.ID, "id_staza").send_keys("UI WD Staza")
    driver.find_element(By.ID, "id_drzava").send_keys("UI Španija")
    date_input = driver.find_element(By.ID, "id_datum_odrzavanja")
    driver.execute_script(
        "arguments[0].value = '2099-09-15'; "
        "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
        date_input,
    )
    Select(driver.find_element(By.ID, "id_sampionat")).select_by_value("MotoGP")
    driver.find_element(By.CSS_SELECTOR, '[data-testid="save-race"]').click()

    row = waiter.until(
        EC.presence_of_element_located(
            (By.XPATH, f"//tr[contains(., {unique_name!r})]")
        )
    )
    row.find_element(By.LINK_TEXT, "Sektori").click()
    waiter.until(EC.visibility_of_element_located((By.ID, "id_naziv_sektora"))).send_keys("UI WD Tribina")
    driver.find_element(By.ID, "id_ukupni_kapacitet").send_keys("75")
    driver.find_element(By.ID, "id_cena_karte").send_keys("149.90")
    driver.find_element(By.CSS_SELECTOR, '[data-testid="add-sector"]').click()

    waiter.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "UI WD Tribina"))
    assert "75" in driver.find_element(By.TAG_NAME, "body").text
