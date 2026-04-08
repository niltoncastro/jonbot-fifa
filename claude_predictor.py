"""
claude_predictor.py
-------------------
Módulo de previsão de partidas usando a API do Claude.
Integrado com o banco SQLite existente (database.py / stats.py).

Como usar no main.py:
    from claude_predictor import gerar_previsao_partida

    # Chamado antes da partida começar, quando os times já são conhecidos
    gerar_previsao_partida(
        codigo_partida=codigo_partida,
        time_casa=state.time_casa,
        time_visitante=state.time_visitante,
        nome_liga=state.nome_liga
    )
"""

import anthropic
import os
import sqlite3

import config
from utils import display_message, send_telegram_message

# ============================================================
# CONFIGURAÇÃO
# ============================================================
CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_MODEL   = "claude-sonnet-4-20250514"
CLAUDE_TOKENS  = 1000

db_path = config.paths("db_path")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


# ============================================================
# BUSCA DE DADOS DO BANCO
# ============================================================

def _buscar_estatisticas_partida(time_casa: str, time_visitante: str) -> list[dict]:
    """
    Retorna as últimas estatísticas consolidadas da partida (casa vs visitante)
    da tabela fifa_estatisticas_partida.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT resultado, qtd_total, perc_total, qtd_parcial, perc_parcial,
                   dif_perc_total_parcial, seq_atual, seq_media, seq_maxima,
                   dif_seq_media_atual, dif_seq_media_max,
                   atr_atual, atr_media, atr_maximo,
                   dif_atr_media_atual, dif_atr_media_max
            FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY resultado ORDER BY id DESC) AS rn
                FROM fifa_estatisticas_partida
                WHERE time_casa = '{time_casa}' AND time_visitante = '{time_visitante}'
            )
            WHERE rn = 1
        """)
        rows = cursor.fetchall()
        conn.close()

        cols = ["resultado", "qtd_total", "perc_total", "qtd_parcial", "perc_parcial",
                "dif_perc_total_parcial", "seq_atual", "seq_media", "seq_maxima",
                "dif_seq_media_atual", "dif_seq_media_max",
                "atr_atual", "atr_media", "atr_maximo",
                "dif_atr_media_atual", "dif_atr_media_max"]

        return [dict(zip(cols, row)) for row in rows]

    except sqlite3.Error as e:
        display_message(f"[CLAUDE] Erro ao buscar estatísticas da partida: {e}")
        return []


def _buscar_estatisticas_time(nome_time: str) -> list[dict]:
    """
    Retorna as últimas estatísticas do time (Venceu / Perdeu / Empatou)
    da tabela fifa_estatisticas_time.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT resultado, qtd_total, perc_total, qtd_parcial, perc_parcial,
                   dif_perc_total_parcial, seq_atual, seq_media, seq_maxima,
                   dif_seq_media_atual, dif_seq_media_max,
                   atr_atual, atr_media, atr_maximo,
                   dif_atr_media_atual, dif_atr_media_max
            FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY resultado ORDER BY id DESC) AS rn
                FROM fifa_estatisticas_time
                WHERE time = '{nome_time}'
            )
            WHERE rn = 1
        """)
        rows = cursor.fetchall()
        conn.close()

        cols = ["resultado", "qtd_total", "perc_total", "qtd_parcial", "perc_parcial",
                "dif_perc_total_parcial", "seq_atual", "seq_media", "seq_maxima",
                "dif_seq_media_atual", "dif_seq_media_max",
                "atr_atual", "atr_media", "atr_maximo",
                "dif_atr_media_atual", "dif_atr_media_max"]

        return [dict(zip(cols, row)) for row in rows]

    except sqlite3.Error as e:
        display_message(f"[CLAUDE] Erro ao buscar estatísticas do time {nome_time}: {e}")
        return []


def _buscar_ultimos_resultados(time_casa: str, time_visitante: str, limite: int = 10) -> list[str]:
    """
    Retorna os últimos resultados do confronto direto (casa x visitante).
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT resultado_partida
            FROM fifa_resultados_final
            WHERE time_casa = '{time_casa}' AND time_visitante = '{time_visitante}'
            ORDER BY id DESC
            LIMIT {limite}
        """)
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows]

    except sqlite3.Error as e:
        display_message(f"[CLAUDE] Erro ao buscar histórico: {e}")
        return []


# ============================================================
# MONTAGEM DO PROMPT
# ============================================================

def _formatar_stats_partida(stats: list[dict], time_casa: str, time_visitante: str) -> str:
    if not stats:
        return "  (sem histórico de confronto direto ainda)\n"

    linhas = []
    for s in stats:
        res = s['resultado']
        linhas.append(
            f"  [{res}] "
            f"Total: {s['qtd_total']} ({s['perc_total']}%) | "
            f"Últimas 50: {s['qtd_parcial']} ({s['perc_parcial']}%) | "
            f"Δ%: {s['dif_perc_total_parcial']} | "
            f"Seq atual/média/máx: {s['seq_atual']}/{s['seq_media']}/{s['seq_maxima']} | "
            f"Atraso atual/média/máx: {s['atr_atual']}/{s['atr_media']}/{s['atr_maximo']}"
        )
    return "\n".join(linhas)


def _formatar_stats_time(stats: list[dict], nome_time: str) -> str:
    if not stats:
        return f"  (sem histórico para {nome_time})\n"

    linhas = []
    for s in stats:
        res = s['resultado']
        linhas.append(
            f"  [{res}] "
            f"Total: {s['qtd_total']} ({s['perc_total']}%) | "
            f"Últimas 50: {s['qtd_parcial']} ({s['perc_parcial']}%) | "
            f"Δ%: {s['dif_perc_total_parcial']} | "
            f"Seq atual/média/máx: {s['seq_atual']}/{s['seq_media']}/{s['seq_maxima']} | "
            f"Atraso atual/média/máx: {s['atr_atual']}/{s['atr_media']}/{s['atr_maximo']}"
        )
    return "\n".join(linhas)


def _montar_prompt(time_casa: str, time_visitante: str, nome_liga: str,
                   stats_partida: list, stats_casa: list,
                   stats_visitante: list, historico: list) -> str:

    hist_str = " → ".join(historico[::-1]) if historico else "Nenhum confronto registrado"

    prompt = f"""Você é um analista especializado em partidas de e-Soccer (FIFA controlado por IA).
Analise os dados estatísticos abaixo e gere uma previsão da próxima partida.

=== PARTIDA ===
Liga : {nome_liga}
Times: {time_casa} (casa) x {time_visitante} (visitante)

=== HISTÓRICO DE CONFRONTOS DIRETOS (últimos 10) ===
{hist_str}

=== ESTATÍSTICAS DO CONFRONTO {time_casa} x {time_visitante} ===
(Legenda: Seq=sequência | Atr=atraso | Δ%=diferença percentual total vs parcial)
{_formatar_stats_partida(stats_partida, time_casa, time_visitante)}

=== DESEMPENHO GERAL — {time_casa} ===
{_formatar_stats_time(stats_casa, time_casa)}

=== DESEMPENHO GERAL — {time_visitante} ===
{_formatar_stats_time(stats_visitante, time_visitante)}

=== TAREFA ===
Com base nesses dados, responda em português de forma objetiva:

1. **Resultado mais provável** e por quê (máximo 3 linhas)
2. **Probabilidades estimadas**: % {time_casa} vence | % Empate | % {time_visitante} vence
3. **Nível de confiança**: Baixo / Médio / Alto
4. **Alerta de atraso**: algum resultado está com atraso acima da média? Se sim, qual?
5. **Recomendação**: qual resultado apostar (se houver sinal claro) ou "Aguardar" se incerto

Seja direto e conciso.
"""
    return prompt


# ============================================================
# CHAMADA À API DO CLAUDE
# ============================================================

def _chamar_claude(prompt: str) -> str:
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_TOKENS,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    except Exception as e:
        display_message(f"[CLAUDE] Erro na chamada à API: {e}")
        return None


# ============================================================
# FUNÇÃO PRINCIPAL — CHAME ESTA NO main.py
# ============================================================

def gerar_previsao_partida(codigo_partida: str, time_casa: str,
                           time_visitante: str, nome_liga: str,
                           enviar_telegram: bool = True) -> str | None:
    """
    Gera previsão da partida usando o Claude com base nos dados do banco.

    Parâmetros:
        codigo_partida  : código único da partida (para log)
        time_casa       : nome do time da casa (já formatado)
        time_visitante  : nome do time visitante (já formatado)
        nome_liga       : nome da liga para exibição
        enviar_telegram : se True, envia a previsão via Telegram

    Retorna:
        str com a previsão, ou None em caso de erro
    """
    display_message(f"[CLAUDE] Gerando previsão: {time_casa} x {time_visitante}")

    # Coleta dados do banco
    stats_partida   = _buscar_estatisticas_partida(time_casa, time_visitante)
    stats_casa      = _buscar_estatisticas_time(time_casa)
    stats_visitante = _buscar_estatisticas_time(time_visitante)
    historico       = _buscar_ultimos_resultados(time_casa, time_visitante)

    # Monta prompt e chama Claude
    prompt   = _montar_prompt(time_casa, time_visitante, nome_liga,
                              stats_partida, stats_casa, stats_visitante, historico)
    previsao = _chamar_claude(prompt)

    if previsao:
        header = (
            f"\n{'='*50}\n"
            f"🤖 PREVISÃO CLAUDE — {nome_liga}\n"
            f"⚽ {time_casa} x {time_visitante}\n"
            f"{'='*50}\n"
        )
        mensagem_completa = header + previsao
        display_message(mensagem_completa)

        if enviar_telegram:
            send_telegram_message(mensagem_completa)

    return previsao
