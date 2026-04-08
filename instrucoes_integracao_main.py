# ================================================================
# INTEGRAÇÃO DO CLAUDE NO main.py
# Adicione apenas as linhas marcadas com [ADD]
# ================================================================

# ------- No topo do main.py, junto com os outros imports -------

from claude_predictor import gerar_previsao_partida   # [ADD]


# ------- Dentro de process_steps_game() -------
# Localize o bloco "PARTIDA INICIADA" (match_status == 6)
# e adicione a chamada ao Claude DENTRO desse bloco, logo após o display_message:

#  ANTES (seu código atual):
#  ─────────────────────────────────────────────────
#  if state.match_status == 6 and (state.sigla_estado_partida != "IP" and state.sigla_estado_partida):
#      state.codigo_partida_atual = codigo_partida
#      state.sigla_estado_partida = "IP"
#      state.last_start_time = time.time()
#      display_message(f"{nome_liga}: [Começou {state.time_casa} x {state.time_visitante}]")


#  DEPOIS (com a integração do Claude):
#  ─────────────────────────────────────────────────
#  if state.match_status == 6 and (state.sigla_estado_partida != "IP" and state.sigla_estado_partida):
#      state.codigo_partida_atual = codigo_partida
#      state.sigla_estado_partida = "IP"
#      state.last_start_time = time.time()
#      display_message(f"{nome_liga}: [Começou {state.time_casa} x {state.time_visitante}]")
#
#      gerar_previsao_partida(                        # [ADD]
#          codigo_partida=codigo_partida,             # [ADD]
#          time_casa=state.time_casa,                 # [ADD]
#          time_visitante=state.time_visitante,       # [ADD]
#          nome_liga=nome_liga,                       # [ADD]
#          enviar_telegram=True                       # [ADD] False para não mandar no Telegram
#      )                                              # [ADD]


# ================================================================
# RESULTADO ESPERADO
# Quando uma partida iniciar, o bot vai:
# 1. Detectar o início (como já faz hoje)
# 2. Buscar automaticamente as stats do banco
# 3. Chamar o Claude para análise
# 4. Printar a previsão no console
# 5. Enviar a previsão via Telegram (opcional)
# 6. Continuar o fluxo normal (pausa de 12min etc.)
# ================================================================
