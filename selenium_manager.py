from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import WebDriverException
import traceback


class SeleniumManager:
    def __init__(self):
        self.driver = None

    # ------------------------------------------------------
    # INICIAR DRIVER
    # ------------------------------------------------------
    def start(self):
        if self.driver is not None:
            return self.driver

        options = Options()
        options.headless = True

        # ESSENCIAIS PARA VPS / HEADLESS
        options.set_preference("browser.cache.disk.enable", False)
        options.set_preference("browser.cache.memory.enable", False)
        options.set_preference("browser.cache.offline.enable", False)
        options.set_preference("network.http.use-cache", False)

        options.set_preference("browser.tabs.unloadOnLowMemory", False)
        options.set_preference("browser.sessionstore.resume_from_crash", False)

        # EVITA CRASH DO MARIONETTE
        options.set_preference("marionette.force-local", True)
        options.set_preference("dom.ipc.processCount", 1)

        # EVITA QUEBRA DE HEADLESS
        options.set_preference("gfx.webrender.all", False)
        options.set_preference("layers.acceleration.disabled", True)

        # USER AGENT FIX
        options.set_preference(
            "general.useragent.override",
            "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/140.0"
        )

        # TELA FIXA
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")

        # ARGS OPCIONAIS
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        try:
            self.driver = webdriver.Firefox(options=options)
        except Exception as e:
            print("\n[ERRO AO INICIAR FIREFOX]")
            print(str(e))
            print(traceback.format_exc())
            self.driver = None

        return self.driver

    # ------------------------------------------------------
    def get_driver(self):
        return self.driver

    # ------------------------------------------------------
    # TESTE SE DRIVER ESTÁ VIVO
    # ------------------------------------------------------
    def is_driver_alive(self):
        if self.driver is None:
            return False

        try:
            self.driver.execute_script("return document.readyState")
            return True
        except Exception:
            return False

    # ------------------------------------------------------
    # REINICIAR DRIVER
    # ------------------------------------------------------
    def restart_driver(self):
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass

        self.driver = None
        return self.start()

    # ------------------------------------------------------
    # ENCERRAR DRIVER
    # ------------------------------------------------------
    def quit(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

        self.driver = None
