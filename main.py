import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

import utils
from GameStateForLeague import game_states, GameState
from utils import iniciar_driver, display_message
from stats import process_stats_match
from stats import process_stats_team
from database import insert_resultado_final

import time
import gc
from selenium.common.exceptions import WebDriverException

STR_SEARCH = "live"
TIME_SLEEP = 800

# configuração das ligas/torneios
TOURNAMENT_CONFIG = {
    "2361937986599399439": {
        "name": "Venezuela",
        "url": "https://jonbet.bet.br/pt/sports?bt-path=%2Ffifa%2Fvenezuela%2Fliga-futve-2361937986599399439",
        "stats": False
    }
}


# --- Funções auxiliares --- #
# noinspection GrazieInspection
def acessar_url(driver, url, timeout=10):
    """
    Abre a URL e aguarda o body. Se a janela for perdida, levanta exceção controlada.
    """
    driver.set_page_load_timeout(timeout)
    try:
        driver.get(url)
        WebDriverWait(driver, timeout).until(
            ec.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except NoSuchWindowException as e:
        # Janela fechada → reinicialização obrigatória
        raise WebDriverException("Browsing context perdido, reiniciando driver...") from e
    except Exception as e:
        display_message(f"Timeout ou erro ao carregar página {url}: {e}")
        raise WebDriverException(f"Não foi possível carregar a página {url}") from e


def baixar_json_torneio(link_json, tries=2, timeout=10):
    for attempt in range(1, tries + 1):
        try:
            response = requests.get(link_json, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            else:
                display_message(f"Erro ao acessar {link_json}, status: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            display_message(f"Timeout ao tentar acessar {link_json} ({attempt}/{tries})")
        except requests.exceptions.RequestException as e:
            display_message(f"Erro HTTP ao acessar {link_json} ({attempt}/{tries}): {str(e)}")
        except Exception as e:
            display_message(f"Erro inesperado ao baixar {link_json} ({attempt}/{tries}): {str(e)}")
        if attempt < tries:
            time.sleep(0.5)
    return None


def extrair_eventos(json_content):
    return json_content.get("events", {})


# noinspection GrazieInspection
def get_json_content_for_league(html_source, tournament_id):
    soup = BeautifulSoup(html_source, 'html.parser')

    for tag_link in soup.find_all('link', href=True):
        href = tag_link['href'].strip()

        if STR_SEARCH.lower() not in href.lower():
            continue

        # display_message(f"Consultando API candidate: {href} para buscar tournament {tournament_id}")
        content_json = baixar_json_torneio(href)
        if not content_json:
            continue

        eventos = extrair_eventos(content_json)
        for ev in eventos.values():
            if str(ev.get("desc", {}).get("tournament")) == str(tournament_id):
                # display_message(f"Encontrado JSON com tournament {tournament_id} em {href}")
                return content_json

    return None


def processar_eventos(content_json, tournament_id, nome_liga, flg_stats):
    eventos = extrair_eventos(content_json)
    for key, dados_evento in eventos.items():
        if str(dados_evento.get("desc", {}).get("tournament")) == str(tournament_id):
            if tournament_id not in game_states:
                game_states[tournament_id] = GameState(key, tournament_id)
            process_steps_game(dados_evento, key, game_states[tournament_id], nome_liga, flg_stats)


def should_skip_liga_delay(tournament_id):
    state = game_states.get(tournament_id)
    if state and state.last_start_time:
        elapsed = time.time() - state.last_start_time
        if elapsed < TIME_SLEEP:
            return True
    return False


# FUNCAO PRINCIPAL
# noinspection GrazieInspection
def process_steps_game(json_evento, codigo_partida, state: GameState, nome_liga, flg_stats):
    """  -----------------------------------------------------------------------------------------------------------"""
    """ FUNCAO PRINCIPAL"""
    """  -----------------------------------------------------------------------------------------------------------"""
    # Obtém o 'status' e informações do evento
    times = json_evento.get("desc", {}).get("competitors")
    state.time_casa = utils.format_team_name(times[0].get("name", "time_casa"))
    state.time_visitante = utils.format_team_name(times[1].get("name", "time_visitante"))
    state.match_status = json_evento.get("state", {}).get("match_status")

    """ Processa os estados do jogo """
    # Variaveis de configuracao
    state.nome_liga = nome_liga

    # [PI] PARTIDA INICIADA
    if state.match_status == 6 and (state.sigla_estado_partida != "IP" and state.sigla_estado_partida):
        state.last_start_time = time.time()

        """  -----------------------------------------------------------------------------  ------------------------------"""
        """ INICIO DA PARTIDA """
        """  -----------------------------------------------------------------------------------------------------------"""
        state.codigo_partida_atual = codigo_partida
        state.sigla_estado_partida = "IP"

        # Mensagem de início de jogoAtual
        message_inicio_partida = f"{state.nome_liga}: [Começou {state.time_casa} x {state.time_visitante}]"
        display_message(message_inicio_partida)

    # [PF] PARTIDA FINALIZADA
    if state.match_status == 100 and (state.sigla_estado_partida != "PF" or not state.sigla_estado_partida):
        state.sigla_estado_partida = "PF"
        """  -----------------------------------------------------------------------------------------------------------"""
        """ FINAL DA PARTIDA """
        """  -----------------------------------------------------------------------------------------------------------"""
        # Atualiza o estado para "Partida Finalizada"
        state.placar_casa = json_evento.get("score", {}).get("home_score", state.placar_casa)
        state.placar_visitante = json_evento.get("score", {}).get("away_score", state.placar_visitante)

        # Mensagem no console e log
        state.placar_final = f"{state.placar_casa}x{state.placar_visitante}"
        display_message(f"{state.nome_liga}: [Terminou. Código: {state.codigo_partida_atual} - "
                        f"Placar final: {state.time_casa} {state.placar_casa} x {state.placar_visitante} {state.time_visitante}]")

        if state.placar_casa > state.placar_visitante:
            state.resultado_partida = state.time_casa
        if state.placar_casa < state.placar_visitante:
            state.resultado_partida = state.time_visitante
        if state.placar_casa == state.placar_visitante:
            state.resultado_partida = "Empate"

        # Salva o resultado final no banco de dados
        insert_resultado_final(
            state.codigo_partida_atual, state.codigo_liga, state.nome_liga, state.time_casa, state.placar_casa,
            state.time_visitante, state.placar_visitante, state.placar_final, state.resultado_partida)

        # Processa estatísticas se habilitado
        if flg_stats:
            process_stats_match(codigo_partida, state.time_casa, state.time_visitante)
            process_stats_team(codigo_partida, state.time_casa)
            process_stats_team(codigo_partida, state.time_visitante)

        # Reset de variáveis no estado
        GameState.reset_state(state)
        state.sigla_estado_partida = "PF"


if __name__ == "__main__":
    print("__main__")


# --- Loop principal --- #
def main():
    driver = iniciar_driver(headless=True)  # inicia apenas uma vez
    iteration = 0
    RESTART_INTERVAL = 30  # número de ciclos antes de reiniciar

    while True:
        iteration += 1
        ciclo_inicio = time.time()

        for tournament_id, config in TOURNAMENT_CONFIG.items():
            liga_inicio = time.time()
            try:
                # 🚀 Checa antes de abrir URL → performance melhor
                if should_skip_liga_delay(tournament_id):
                    display_message(
                        f"Jogo da Liga {config['name']} em andamento..."
                    )
                    driver.quit()
                    time.sleep(TIME_SLEEP)
                    driver = iniciar_driver(headless=True)  # inicia apenas uma vez
                    continue

                acessar_url(driver, config["url"])
                html_source = driver.page_source
                content_json = get_json_content_for_league(html_source, tournament_id)

                if content_json:
                    processar_eventos(content_json, tournament_id, config['name'], config["stats"])

                # 🔹 Limpa cookies e libera memória
                driver.delete_all_cookies()
                del html_source, content_json

            except WebDriverException as inner_e:
                msg = str(inner_e)
                if "Browsing context" in msg or "InvalidSessionID" in msg:
                    display_message("Driver perdeu contexto, reiniciando...")
                    try:
                        driver.quit()
                    except:
                        pass
                    time.sleep(1)
                    driver = iniciar_driver(headless=True)
                else:
                    display_message(f"Erro ao processar liga {config['name']}: {inner_e}")
                    time.sleep(1)

            liga_duracao = time.time() - liga_inicio
            display_message(f"Processamento da Liga {config['name']}: {liga_duracao:.2f} segundos")

        # 🔄 reinicia driver a cada X ciclos (não a cada loop!)
        if iteration % RESTART_INTERVAL == 0:
            display_message(f"Reiniciando driver após {RESTART_INTERVAL} ciclos...")
            try:
                driver.quit()
            except:
                pass
            driver = iniciar_driver(headless=True)

        # 🔹 Força limpeza de memória
        gc.collect()

        ciclo_duracao = time.time() - ciclo_inicio
        display_message(f"Processamento Total: {ciclo_duracao:.2f} segundos")
        print("*" * 79)


if __name__ == "__main__":
    main()
