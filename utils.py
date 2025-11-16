from datetime import datetime

import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


def create_driver():
    options = Options()
    options.headless = True

    # 🔥 Reduz uso de CPU/RAM drasticamente
    options.set_preference("browser.tabs.remote.autostart", False)
    options.set_preference("browser.tabs.remote.autostart.1", False)
    options.set_preference("browser.tabs.remote.autostart.2", False)
    options.set_preference("dom.ipc.processCount", 1)
    options.set_preference("browser.sessionstore.resume_from_crash", False)
    options.set_preference("browser.shell.checkDefaultBrowser", False)
    options.set_preference("permissions.default.image", 2)  # não carrega imagens
    options.set_preference("network.http.pipelining", True)

    driver = webdriver.Firefox(options=options)
    driver.set_page_load_timeout(20)

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
