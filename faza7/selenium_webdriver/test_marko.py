# Marko Mandić 0625/2023 - ukršteno testiranje kupovine i administratorske tokove.

from __future__ import annotations

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from conftest import login, open_path, wait


def test_wd_k01_kupovina_paketa_i_pdf_vaucer(driver) -> None:
    """SSU 3/4: paket se plaća,izdaje se vaučer i PDF je stvarno čitljiv."""

    login(driver, "ui.kupac@hub.test")
    open_path(driver, "/trka/9201/")
    waiter = wait(driver)
    Select(waiter.until(EC.element_to_be_clickable((By.ID, "id_id_sektora")))).select_by_value("9301")
    Select(driver.find_element(By.ID, "id_id_smestaja")).select_by_value("9401")
    driver.find_element(By.CSS_SELECTOR, '[data-testid="add-to-cart"]').click()

    cart_item = waiter.until(
        EC.presence_of_element_located(
            (By.XPATH, "//article[contains(., 'UI Test WSBK 2099')]")
        )
    )
    cart_item.find_element(By.CSS_SELECTOR, 'button[data-testid^="pay-"]').click()
    waiter.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Vaš paket je potvrđen."))

    voucher_link = waiter.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, '[data-testid="download-voucher"]')
        )
    )
    voucher_url = voucher_link.get_attribute("href")
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])
    response = session.get(voucher_url, timeout=10)
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 4000


def test_wd_k02_admin_sinhronizuje_tri_izvora_i_upravlja_nalogom(driver) -> None:
    """SSU 5/9: grupna sinhronizacija i suspenzija/aktivacija naloga."""

    login(driver, "ui.admin@hub.test")
    waiter = wait(driver, 20)
    driver.find_element(By.CSS_SELECTOR, '[data-testid="sync-races"]').click()
    waiter.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "F1 sinhronizacija završena"))
    body = driver.find_element(By.TAG_NAME, "body").text
    assert "MotoGP sinhronizacija završena" in body
    assert "WSBK sinhronizacija završena" in body

    target_row = waiter.until(
        EC.presence_of_element_located(
            (By.XPATH, "//tr[contains(., 'ui.target@hub.test')]")
        )
    )
    if "Suspendovano" in target_row.text:
        target_row.find_element(By.XPATH, ".//button[normalize-space()='Aktiviraj']").click()
        target_row = waiter.until(
            EC.presence_of_element_located(
                (By.XPATH, "//tr[contains(., 'ui.target@hub.test') and contains(., 'Aktivno')]")
            )
        )
    target_row.find_element(By.XPATH, ".//button[normalize-space()='Suspenduj']").click()
    suspended = waiter.until(
        EC.presence_of_element_located(
            (By.XPATH, "//tr[contains(., 'ui.target@hub.test') and contains(., 'Suspendovano')]")
        )
    )
    suspended.find_element(By.XPATH, ".//button[normalize-space()='Aktiviraj']").click()
    waiter.until(
        EC.presence_of_element_located(
            (By.XPATH, "//tr[contains(., 'ui.target@hub.test') and contains(., 'Aktivno')]")
        )
    )

    open_path(driver, "/pretraga/?q=UI+API")
    waiter.until(EC.text_to_be_present_in_element((By.ID, "race-results"), "UI API F1 Grand Prix"))
    results = driver.find_element(By.ID, "race-results").text
    assert "UI API MotoGP" in results
    assert "UI API WSBK Round" in results
