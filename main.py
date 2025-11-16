import time

import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException

from GameStateForLeague import game_states, GameState
from config import TOURNAMENT_CONFIG
from database import insert_resultado_final
from selenium_manager import SeleniumManager
from stats import process_stats_match, process_stats_team
from utils import display_message, format_team_name

STR_SEARCH = "live"
TIME_SLEEP = 750

# ============================================================
# TEMPOS IMPORTANTES
# ============================================================
TIMEOUT_TENTATIVA = 35  # tempo mínimo entre ciclos (~30s)
TEMPO_JOGO_ANDAMENTO = 12 * 60  # 12 minutos
STR_SKIP_MSG = "[INFO] Jogo em andamento, aguardando..."


# ============================================================
# CONTROLE DE PAUSA DE 12 MIN NO INÍCIO DO JOGO
# ============================================================
def should_delay_due_match_start(tournament_id):
    """Evita consultas enquanto o jogo está rolando nos primeiros 12 minutos."""
    state = game_states.get(tournament_id)

    if state and state.sigla_estado_partida == "IP":  # IP = Início da Partida
        elapsed = time.time() - state.last_start_time

        if elapsed < TEMPO_JOGO_ANDAMENTO:
            falta = int(TEMPO_JOGO_ANDAMENTO - elapsed)
            m = falta // 60
            s = falta % 60
            display_message(f"{STR_SKIP_MSG} Retorna em {m:02d}:{s:02d}")
            return True

    return False


# =====================================================================
# BAIXAR JSON
# =====================================================================
def baixar_json_torneio(link_json, tries=2, timeout=10):
    for attempt in range(1, tries + 1):
        try:
            response = requests.get(link_json, timeout=timeout)

            if response.status_code == 200:
                return response.json()

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


# =====================================================================
# EXTRAI EVENTOS
# =====================================================================
def extrair_eventos(json_content):
    return json_content.get("events", {})


# =====================================================================
# BUSCA JSON DA LIGA
# =====================================================================
def get_json_content_for_league(html_source, tournament_id):
    soup = BeautifulSoup(html_source, 'html.parser')

    for tag_link in soup.find_all('link', href=True):
        href = tag_link['href'].strip()

        if STR_SEARCH not in href.lower():
            continue

        json_ret = baixar_json_torneio(href)
        if not json_ret:
            continue

        eventos = extrair_eventos(json_ret)

        for ev in eventos.values():
            if str(ev.get("desc", {}).get("tournament")) == str(tournament_id):
                return json_ret

    return None


# =====================================================================
# PROCESSA EVENTOS DA LIGA
# =====================================================================
def processar_eventos(content_json, tournament_id, nome_liga, flg_stats):
    eventos = extrair_eventos(content_json)

    for key, evento in eventos.items():
        if str(evento.get("desc", {}).get("tournament")) != str(tournament_id):
            continue

        if tournament_id not in game_states:
            game_states[tournament_id] = GameState(key, tournament_id)

        process_steps_game(evento, key, game_states[tournament_id], nome_liga, flg_stats)


# =====================================================================
# SKIP para evitar processamento contínuo após início da partida
# =====================================================================
def should_skip_liga_delay(tournament_id):
    state = game_states.get(tournament_id)

    if state and state.last_start_time:
        if (time.time() - state.last_start_time) < TIME_SLEEP:
            return True

    return False


# =====================================================================
# PROCESSAMENTO PRINCIPAL DOS ESTADOS DA PARTIDA
# =====================================================================
def process_steps_game(json_evento, codigo_partida, state: GameState, nome_liga, flg_stats):
    competitors = json_evento.get("desc", {}).get("competitors")
    state.time_casa = format_team_name(competitors[0].get("name", "Casa"))
    state.time_visitante = format_team_name(competitors[1].get("name", "Visitante"))
    state.match_status = json_evento.get("state", {}).get("match_status")
    state.nome_liga = nome_liga

    # ---------------- PARTIDA INICIADA ----------------
    if state.match_status == 6 and (state.sigla_estado_partida != "IP" and state.sigla_estado_partida):
        state.codigo_partida_atual = codigo_partida
        state.sigla_estado_partida = "IP"
        state.last_start_time = time.time()

        display_message(f"{nome_liga}: [Começou {state.time_casa} x {state.time_visitante}]")

    # ---------------- PARTIDA FINALIZADA ----------------
    if state.match_status == 100 and (state.sigla_estado_partida != "PF" or not state.sigla_estado_partida):
        state.sigla_estado_partida = "PF"

        state.placar_casa = json_evento.get("score", {}).get("home_score", 0)
        state.placar_visitante = json_evento.get("score", {}).get("away_score", 0)
        state.placar_final = f"{state.placar_casa}x{state.placar_visitante}"

        display_message(
            f"{nome_liga}: [Terminou. Código: {state.codigo_partida_atual} - "
            f"Placar final: {state.time_casa} {state.placar_casa} x {state.placar_visitante} {state.time_visitante}]"
        )

        # Resultado
        if state.placar_casa > state.placar_visitante:
            state.resultado_partida = state.time_casa
        elif state.placar_visitante > state.placar_casa:
            state.resultado_partida = state.time_visitante
        else:
            state.resultado_partida = "Empate"

        # Banco
        insert_resultado_final(
            state.codigo_partida_atual,
            state.codigo_liga,
            nome_liga,
            state.time_casa,
            state.placar_casa,
            state.time_visitante,
            state.placar_visitante,
            state.placar_final,
            state.resultado_partida
        )

        # Stats
        if flg_stats:
            process_stats_match(codigo_partida, state.time_casa, state.time_visitante)
            process_stats_team(codigo_partida, state.time_casa)
            process_stats_team(codigo_partida, state.time_visitante)

        GameState.reset_state(state)
        state.sigla_estado_partida = "PF"


# ============================================================
# MAIN OTIMIZADA
# ============================================================
def main():

    # ------------------------------
    # Inicia o Selenium Manager
    # ------------------------------
    selenium = SeleniumManager(headless=False)
    selenium.start()
    driver = selenium.get_driver()

    while True:
        inicio = time.time()

        # ------------------------------
        # LOOP DE TODAS AS LIGAS
        # ------------------------------
        for tournament_id, cfg in TOURNAMENT_CONFIG.items():

            url = cfg["url"]
            nome_liga = cfg["name"]
            flg_stats = cfg.get("stats", False)

            # ----------------------------------------
            # 1) VERIFICA SE DEVE PULAR (JOGO EM CURSO)
            # ----------------------------------------
            if should_delay_due_match_start(tournament_id):
                continue

            # ----------------------------------------
            # 2) GARANTE QUE O DRIVER ESTÁ VIVO
            # ----------------------------------------
            if not selenium.is_driver_alive():
                display_message("[INFO] Driver caiu. Reiniciando...")
                selenium.restart_driver()
                time.sleep(1)
                driver = selenium.get_driver()

            # ----------------------------------------
            # 3) ABRE A PÁGINA DA LIGA
            # ----------------------------------------
            try:
                driver.get(url)
            except TimeoutException:
                display_message(f"[WARN] Timeout ao carregar {nome_liga}")
                continue
            except Exception as e:
                display_message(f"[ERRO] Falha ao abrir página da liga {nome_liga}: {e}")
                continue

            page_html = driver.page_source
            if not page_html:
                display_message(f"[ERRO] Página vazia para {nome_liga}")
                continue

            # ----------------------------------------
            # 4) EXTRAI JSON DA LIGA
            # ----------------------------------------
            json_content = get_json_content_for_league(page_html, tournament_id)
            if not json_content:
                display_message(f"[ERRO] {nome_liga}: JSON da liga não encontrado.")
                continue

            # ----------------------------------------
            # 5) PROCESSA OS EVENTOS (SEUS ESTADOS)
            # ----------------------------------------
            try:
                processar_eventos(json_content, tournament_id, nome_liga, flg_stats)
            except Exception as e:
                display_message(f"[ERRO] processar_eventos falhou em {nome_liga}: {e}")

        # ----------------------------------------
        # CONTROLE PARA NÃO EXECUTAR ANTES DE ~30s
        # ----------------------------------------
        tempo_exec = time.time() - inicio
        if tempo_exec < TIMEOUT_TENTATIVA:
            time.sleep(TIMEOUT_TENTATIVA - tempo_exec)


# ============================================================
# START
# ============================================================
if __name__ == "__main__":
    main()
