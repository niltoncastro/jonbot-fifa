from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import WebDriverException


class SeleniumManager:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None

    # ------------------------------------------------------
    # INICIA O DRIVER
    # ------------------------------------------------------
    # noinspection AiaStyle
    def start(self):
        """Inicia o driver apenas uma vez e retorna o mesmo driver."""
        if self.driver is not None:
            return self.driver

        options = Options()

        if self.headless:
            options.add_argument("--headless")

        # 🔧 Melhor estabilidade no Firefox
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("media.peerconnection.enabled", False)
        options.set_preference("useAutomationExtension", False)

        # 🔧 Reduz falhas de renderização e crash ao acessar páginas JS pesadas
        options.set_preference(
            "general.useragent.override",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0"
        )

        try:
            self.driver = webdriver.Firefox(options=options)
        except Exception as e:
            print(f"[ERRO] Falha ao iniciar Firefox: {e}")
            self.driver = None

        return self.driver

    # ------------------------------------------------------
    # RETORNA O DRIVER ATUAL
    # ------------------------------------------------------
    def get_driver(self):
        return self.driver

    # ------------------------------------------------------
    # TESTA SE O DRIVER ESTÁ VIVO
    # ------------------------------------------------------
    def is_driver_alive(self):
        """Retorna True se o driver estiver funcionando sem travar."""
        if self.driver is None:
            return False

        try:
            # Teste leve e seguro (não gera warning)
            self.driver.execute_script("return document.readyState")
            return True

        except WebDriverException:
            return False
        except Exception:
            return False

    # ------------------------------------------------------
    # REINICIA O DRIVER
    # ------------------------------------------------------
    def restart_driver(self):
        """Fecha o driver atual e recria um novo."""
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass

        self.driver = None
        return self.start()

    # ------------------------------------------------------
    # ENCERRA O DRIVER
    # ------------------------------------------------------
    def quit(self):
        """Fecha completamente o driver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

        self.driver = None
