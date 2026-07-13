# Faza 7 - zajedničke Selenium WebDriver pomoćne funkcije.
# Autori: Milan Lemić 0323/2023; Milica Štavljanin 0391/2023; Marko Mandić 0625/2023.

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
DEFAULT_PASSWORD = "Test12345!"


def open_path(driver: webdriver.Chrome, path: str) -> None:
    """Otvara putanju u odnosu na testirani Django server."""

    driver.get(f"{BASE_URL}/{path.lstrip('/')}")


def wait(driver: webdriver.Chrome, seconds: int = 12) -> WebDriverWait:
    """Vraća eksplicitno čekanje umesto vremenski osetljivih sleep poziva."""

    return WebDriverWait(driver, seconds)


def login(
    driver: webdriver.Chrome,
    email: str,
    password: str = DEFAULT_PASSWORD,
) -> None:
    """Prijavljuje nalog kroz javni UI, bez direktnog menjanja sesije."""

    open_path(driver, "/auth/")
    waiter = wait(driver)
    email_input = waiter.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, '[data-testid="login-email"]')
        )
    )
    email_input.clear()
    email_input.send_keys(email)
    password_input = driver.find_element(
        By.CSS_SELECTOR, '[data-testid="login-password"]'
    )
    password_input.clear()
    password_input.send_keys(password)
    driver.find_element(By.CSS_SELECTOR, '[data-testid="login-submit"]').click()
    waiter.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, '[data-testid="logout-button"]')
        )
    )


@pytest.fixture
def driver() -> Iterator[webdriver.Chrome]:
    """Pokreće izolovan Chromium/Chrome za svaki test i bezbedno ga zatvara."""

    options = Options()
    if os.getenv("HEADLESS", "1").lower() not in {"0", "false", "no"}:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1100")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    binary = os.getenv("CHROME_BINARY")
    if binary:
        options.binary_location = str(Path(binary))

    driver_path = os.getenv("CHROMEDRIVER")
    service = Service(executable_path=driver_path) if driver_path else Service()

    try:
        browser = webdriver.Chrome(service=service, options=options)
    except WebDriverException as exc:
        pytest.skip(
            "Chrome/Chromium ili kompatibilan ChromeDriver nije dostupan: "
            f"{exc.msg or exc}"
        )

    browser.set_page_load_timeout(20)
    yield browser
    browser.quit()
