from threading import Thread
import time

import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from app import create_app
from database import Database


@pytest.mark.selenium
def test_dashboard_loads_in_real_browser(database):
    app = create_app(database)
    server = Thread(
        target=lambda: app.run(host="127.0.0.1", port=5055, debug=False, use_reloader=False),
        daemon=True,
    )
    server.start()
    time.sleep(1)

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as error:
        pytest.skip(f"Chrome WebDriver unavailable: {error}")

    try:
        driver.get("http://127.0.0.1:5055/signup")
        name = driver.find_element(By.NAME, "name")
        email = driver.find_element(By.NAME, "email")
        password = driver.find_element(By.NAME, "password")
        name.send_keys("Browser Admin")
        email.send_keys("browser@example.com")
        password.send_keys("password123")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        driver.get("http://127.0.0.1:5055/")
        assert "Clinic Appointment System" in driver.title
        assert driver.find_element(By.TAG_NAME, "main")
    finally:
        driver.quit()
