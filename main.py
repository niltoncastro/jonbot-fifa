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
TIMEOUT_TENTATIVA = 5  # tempo mínimo entre ciclos (~30s)
INTERVALO_LOOP = 3  # intervalo mínimo entre ciclos (quando não em pausa)
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
# MAIN OTIMIZADA SUPER RÁPIDA (3s por ciclo)
# ============================================================
# ============================================================
# CONFIGURAÇÃO DE LOG
# ============================================================
LOG_TEMPO = True  # deixe False para desligar logs de tempo


# ============================================================
# MAIN OTIMIZADA SUPER RÁPIDA (3s por ciclo)
# ============================================================
def main():
    selenium = SeleniumManager()
    selenium.start()
    driver = selenium.get_driver()

    # controla se já fizemos pausa para cada liga
    pausa_em_andamento = {}  # tournament_id -> bool

    while True:
        ciclo_inicio = time.time()

        # percorre ligas
        for tournament_id, cfg in TOURNAMENT_CONFIG.items():
            liga_inicio = time.time()

            url = cfg["url"]
            nome_liga = cfg.get("name") or cfg.get("nome_liga") or str(tournament_id)
            flg_stats = cfg.get("stats", False)

            # Verifica se o driver está vivo, recria se necessário
            if not selenium.is_driver_alive():
                display_message("[INFO] Driver caiu. Reiniciando...")
                selenium.restart_driver()
                time.sleep(1)
                driver = selenium.get_driver()

            # carregar página
            try:
                driver.set_page_load_timeout(10)
                driver.get(url)
            except TimeoutException:
                display_message(f"[WARN] Timeout ao carregar {nome_liga}")
                continue
            except Exception as e:
                display_message(f"[ERRO] Falha ao abrir {nome_liga}: {e}")
                continue

            html = driver.page_source
            if not html:
                display_message(f"[ERRO] HTML vazio para {nome_liga}")
                continue

            # extrai JSON
            json_content = get_json_content_for_league(html, tournament_id)
            if not json_content:
                if LOG_TEMPO:
                    dur_liga = time.time() - liga_inicio
                    display_message(f"[TEMPO] {nome_liga}: {dur_liga:.2f} segundos (sem JSON)")
                continue

            # processa eventos (vai atualizar game_states)
            try:
                processar_eventos(json_content, tournament_id, nome_liga, flg_stats)
            except Exception as e:
                display_message(f"[ERRO] processar_eventos falhou em {nome_liga}: {e}")
                continue

            # ------------------------------------------------------
            # 5) PAUSA AUTOMÁTICA — SOMENTE 1 VEZ POR JOGO
            # ------------------------------------------------------
            st = game_states.get(tournament_id)

            if st and st.sigla_estado_partida == "IP":

                # estado inicial = nunca pausou
                if pausa_em_andamento.get(tournament_id) is None:
                    pausa_em_andamento[tournament_id] = False

                # Se ainda não pausou este jogo, pausar agora
                if pausa_em_andamento[tournament_id] is False:

                    display_message(f"[INFO] {nome_liga}: Jogo em andamento — pausando por 12:00")

                    pausa_em_andamento[tournament_id] = True  # impede repetição

                    # libera driver
                    try:
                        selenium.quit()
                    except:
                        pass

                    # pausa de 12 minutos
                    time.sleep(12 * 60)

                    # após pausa → recria driver
                    selenium.start()
                    driver = selenium.get_driver()

                    display_message(f"[INFO] Processo retomado após pausa do jogo {nome_liga}.")

                    # volta início para reprocessar
                    continue

            else:
                # jogo finalizado ou não iniciado → reseta pausa
                pausa_em_andamento[tournament_id] = False

            # ------------------------------------------------------
            # Log tempo por liga
            # ------------------------------------------------------
            if LOG_TEMPO:
                dur_liga = time.time() - liga_inicio
                display_message(f"[TEMPO] {nome_liga}: {dur_liga:.2f} segundos")

        # ------------------------------------------------------
        # Log tempo total do ciclo
        # ------------------------------------------------------
        ciclo_dur = time.time() - ciclo_inicio
        if LOG_TEMPO:
            display_message(f"[TEMPO] Ciclo completo: {ciclo_dur:.2f} segundos")

        # respeita intervalo mínimo
        if ciclo_dur < INTERVALO_LOOP:
            time.sleep(INTERVALO_LOOP - ciclo_dur)


# START
# ============================================================
if __name__ == "__main__":
    main()
