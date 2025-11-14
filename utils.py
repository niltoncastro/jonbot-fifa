import os

import requests

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

from datetime import datetime
from config import paths


def iniciar_driver(headless):
    env_type = os.getenv("ENV_TYPE", "local")  # default = local

    # ===============================
    # 🟩 SERVIDOR → CHROME (HEADLESS)
    # ===============================
    if env_type == "server":
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()

        # ESSENCIAIS PARA VPS
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Evita travamentos
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")

        # Faz o Chrome renderizar páginas pesadas sem travar
        options.add_argument("--remote-debugging-port=9222")

        # Usa menos memória
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        return driver

    # ===============================
    # 🟦 LOCAL → FIREFOX
    # ===============================
    else:
        from selenium.webdriver.firefox.options import Options
        from selenium.webdriver.firefox.service import Service
        from selenium import webdriver

        options = Options()
        options.binary_location = paths("fire_fox")

        # Preferências para performance
        options.set_preference("permissions.default.image", 2)
        options.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", False)
        options.set_preference("browser.cache.disk.enable", False)
        options.set_preference("browser.cache.memory.enable", False)
        options.set_preference("browser.cache.offline.enable", False)
        options.set_preference("network.http.use-cache", False)

        # Local headless opcional
        if headless:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.set_preference("general.useragent.override",
                                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")

        # Firefox local usa Selenium Manager automaticamente
        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(30)
        return driver


def display_message(message):
    """Exibe mensagens formatadas com a data e hora."""
    current_time = datetime.now().strftime('%Y%m%d%H%M%S')
    formatted_message = f"{current_time} - {message}"

    # log_writer(formatted_message)
    print(formatted_message)


def send_telegram_message(message):
    bot_token = "7631694559:AAFgiQKT_XcIW7SGi7Fvgz_K9VKMYwEU9dc"
    chat_id = "7120515251"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise HTTPError for bad responses
    except requests.exceptions.RequestException as e:
        display_message(f"Error sending message: {e}")


def format_team_name(parameter):
    mapping = {
        "Dep. Táchira": "Tachira",
        "Dep. La Guaira": "Guaira",
        "Caracas F.C.": "Caracas"
    }
    return mapping.get(parameter, parameter)
