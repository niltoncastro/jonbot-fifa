import requests

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from datetime import datetime
from config import paths


def iniciar_driver(headless):
    firefox_options = Options()
    firefox_options.binary_location = paths("fire_fox")

    options = Options()
    options.set_preference("permissions.default.image", 2)  # não carrega imagens
    options.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", False)  # desabilita plugins
    options.set_preference("browser.cache.disk.enable", False)  # sem cache
    options.set_preference("browser.cache.memory.enable", False)
    options.set_preference("browser.cache.offline.enable", False)
    options.set_preference("network.http.use-cache", False)
    options.add_argument("--headless")

    if headless:
        firefox_options.add_argument("--headless")  # executa sem abrir janela

    # Selenium Manager baixa/configura o driver automaticamente
    driver = webdriver.Firefox(options=firefox_options)
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
