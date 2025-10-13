import utils
import time

from utils import display_message
from stats import process_stats_match
from stats import process_stats_team
from database import insert_resultado_final

from GameStateForLeague import GameState


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
