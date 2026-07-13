# Milan Lemić 0323/2023 - ukršteno testiranje kupčeve i hotelijerske funkcionalnosti.

from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from conftest import login, open_path, wait


def test_wd_m01_ajax_pretraga_i_prazan_rezultat(driver) -> None:
    """SSU 2: filteri rade bez reload-a, a prazan skup ima jasnu poruku."""

    open_path(driver, "/pretraga/")
    waiter = wait(driver)
    championship = Select(
        waiter.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[data-testid="search-championship"]')
            )
        )
    )
    championship.select_by_value("WSBK")
    location = driver.find_element(
        By.CSS_SELECTOR, '[data-testid="search-location"]'
    )
    location.clear()
    location.send_keys("UI Srbija")

    waiter.until(lambda d: d.find_element(By.ID, "result-count").text == "1")
    results = driver.find_element(By.ID, "race-results").text
    assert "UI Test WSBK 2099" in results

    query = driver.find_element(By.CSS_SELECTOR, '[data-testid="search-query"]')
    query.send_keys("nepostojeca-ui-trka-xyz")
    waiter.until(lambda d: d.find_element(By.ID, "result-count").text == "0")
    assert driver.find_element(By.CSS_SELECTOR, '[data-testid="no-races"]').is_displayed()


def test_wd_m02_hotelijer_dodaje_i_menja_smestaj(driver) -> None:
    """SSU 7/8 u granicama baze: unos soba i jedinstvene cene po noćenju."""

    login(driver, "ui.hotelijer@hub.test")
    waiter = wait(driver)
    waiter.until(EC.url_contains("/hotelijer/"))

    unique_name = f"UI WebDriver Hotel {int(time.time() * 1000)}"
    Select(driver.find_element(By.ID, "id_id_trke")).select_by_value("9201")
    driver.find_element(By.ID, "id_naziv_smestaja").send_keys(unique_name)
    driver.find_element(By.ID, "id_lokacija").send_keys("UI Novi Beograd")
    driver.find_element(By.ID, "id_udaljenost_od_staze").send_keys("5.25")
    driver.find_element(By.ID, "id_broj_slobodnih_soba").send_keys("12")
    driver.find_element(By.ID, "id_cena_po_nocenju").send_keys("109.90")
    driver.find_element(By.CSS_SELECTOR, '[data-testid="add-accommodation"]').click()

    row = waiter.until(
        EC.presence_of_element_located(
            (By.XPATH, f"//tr[contains(., {unique_name!r})]")
        )
    )
    row.find_element(By.LINK_TEXT, "Izmeni").click()
    price = waiter.until(EC.visibility_of_element_located((By.ID, "id_cena_po_nocenju")))
    price.clear()
    price.send_keys("111.50")
    driver.find_element(By.XPATH, "//button[normalize-space()='Sačuvaj izmene']").click()

    waiter.until(EC.url_contains("/hotelijer/"))
    updated_row = waiter.until(
        EC.presence_of_element_located(
            (By.XPATH, f"//tr[contains(., {unique_name!r})]")
        )
    )
    assert "111.50 EUR" in updated_row.text
