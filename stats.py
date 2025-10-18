from collections import defaultdict, Counter
from statistics import mean
from datetime import datetime
import pandas as pd
from database import select_resultados_final_partida, insert_estatistica_partida, select_resultados_final_time, \
    insert_estatistica_time, select_max_atraso_partida, select_max_atraso_time, select_max_seq_time, \
    select_max_seq_partida

# mostra todas as linhas
pd.set_option("display.max_rows", None)

# mostra todas as colunas
pd.set_option("display.max_columns", None)

# aumenta largura máxima de cada coluna (para não quebrar linha)
pd.set_option("display.width", None)

# mostra todo o conteúdo da célula, sem cortar
pd.set_option("display.max_colwidth", None)

global time_casa, time_visitante, match, time


# noinspection PyShadowingNames
def process_stats_match(codigo_partida, time_casa, time_visitante):
    all_results = select_resultados_final_partida(time_casa, time_visitante)
    all_results_df = pd.DataFrame(all_results, columns=["time_casa", "time_visitante", "resultado"])

    # Obter todas as combinações únicas de partidas
    unique_matches = all_results_df.groupby(["time_casa", "time_visitante"]).size().reset_index().iloc[:, :2]

    # Processar cada partida separadamente
    consolidated_results = []

    for _, match in unique_matches.iterrows():
        time_casa, time_visitante = match["time_casa"], match["time_visitante"]
        match_results_df = all_results_df[
            (all_results_df["time_casa"] == time_casa) &
            (all_results_df["time_visitante"] == time_visitante)
            ]

        match_results_list = match_results_df.to_records(index=False).tolist()

        # Calcular estatísticas
        percentages = stats_percentages_by_match(match_results_df)

        sequences = pd.DataFrame(stats_sequences_by_match(match_results_list))

        delays = pd.DataFrame(stats_delays_by_match(match_results_list))

        # Ajustar chaves para evitar conflitos
        sequences = sequences.rename(columns={"resultado": "resultado"})
        delays = delays.rename(columns={"resultado": "resultado"})

        # Consolidar dados da partida
        consolidated = percentages.merge(
            sequences,
            on=["time_casa", "time_visitante", "resultado"],
            how="outer"
        ).merge(
            delays,
            on=["time_casa", "time_visitante", "resultado"],
            how="outer"
        )

        # Adicionar coluna de data_criacao
        consolidated["data_criacao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        consolidated_results.append(consolidated)

    # Concatenar os resultados de todas as partidas
    if not consolidated_results:
        print("Nenhuma estatística consolidada encontrada.")
        return
    final_consolidated = pd.concat(consolidated_results, ignore_index=True)

    # Reordenar colunas
    final_consolidated = final_consolidated[[
        "time_casa", "time_visitante", "resultado", "qtd_total", "perc_total", "qtd_parcial", "perc_parcial",
        "dif_perc_total_parcial", "seq_atual", "seq_media", "seq_maxima", "dif_seq_media_atual", "dif_seq_media_max",
        "atr_atual", "atr_media", "atr_maximo", "dif_atr_media_atual", "dif_atr_media_max", "data_criacao"
    ]]

    # Salvar os dados no banco de dados
    for idx, row in final_consolidated.iterrows():
        insert_estatistica_partida(
            codigo_partida=codigo_partida,
            time_casa=row["time_casa"],
            time_visitante=row["time_visitante"],
            resultado=row["resultado"],
            qtd_total=row["qtd_total"],
            perc_total=row["perc_total"],
            qtd_parcial=row["qtd_parcial"],
            perc_parcial=row["perc_parcial"],
            dif_perc_total_parcial=row["dif_perc_total_parcial"],
            seq_atual=row["seq_atual"],
            seq_media=row["seq_media"],
            seq_maxima=row["seq_maxima"],
            dif_seq_media_atual=row["dif_seq_media_atual"],
            dif_seq_media_max=row["dif_seq_media_max"],
            atr_atual=row["atr_atual"],
            atr_media=row["atr_media"],
            atr_maximo=row["atr_maximo"],
            dif_atr_media_atual=row["dif_atr_media_atual"],
            dif_atr_media_max=row["dif_atr_media_max"],
            data_criacao=row["data_criacao"]
        )


def process_stats_team(codigo_partida, nome_time):
    # Selecionar os resultados finais do time
    all_results = select_resultados_final_time(nome_time)
    all_results_df = pd.DataFrame(all_results, columns=["nome_time", "resultado"])

    # Garantir que existam dados para processar
    if all_results_df.empty:
        print(f"Nenhum resultado encontrado para o time {nome_time}.")
        return

    # Converter os resultados numa lista de registros
    all_results_list = all_results_df.to_records(index=False).tolist()

    # Calcular estatísticas
    percentages = stats_percentages_by_team(all_results_df)
    sequences = pd.DataFrame(stats_sequences_by_team(all_results_list))
    delays = pd.DataFrame(stats_delays_by_team(all_results_list))

    # Ajustar chaves para evitar conflitos
    sequences = sequences.rename(columns={"resultado": "resultado"})
    delays = delays.rename(columns={"resultado": "resultado"})

    # Consolidar dados da partida
    consolidated = percentages.merge(
        sequences,
        on=["nome_time", "resultado"],
        how="outer"
    ).merge(
        delays,
        on=["nome_time", "resultado"],
        how="outer"
    )

    # Adicionar coluna de data_criacao
    consolidated["data_criacao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Remover duplicatas antes de consolidar
    consolidated = consolidated.drop_duplicates()

    # Reordenar colunas
    final_consolidated = consolidated[[
        "nome_time", "resultado", "qtd_total", "perc_total", "qtd_parcial", "perc_parcial",
        "dif_perc_total_parcial", "seq_atual", "seq_media", "seq_maxima", "dif_seq_media_atual", "dif_seq_media_max",
        "atr_atual", "atr_media", "atr_maximo", "dif_atr_media_atual", "dif_atr_media_max", "data_criacao"
    ]]

    # Salvar os dados no banco de dados
    for idx, row in final_consolidated.iterrows():
        insert_estatistica_time(
            codigo_partida=codigo_partida,
            nome_time=row["nome_time"],
            resultado=row["resultado"],
            qtd_total=row["qtd_total"],
            perc_total=row["perc_total"],
            qtd_parcial=row["qtd_parcial"],
            perc_parcial=row["perc_parcial"],
            dif_perc_total_parcial=row["dif_perc_total_parcial"],
            seq_atual=row["seq_atual"],
            seq_media=row["seq_media"],
            seq_maxima=row["seq_maxima"],
            dif_seq_media_atual=row["dif_seq_media_atual"],
            dif_seq_media_max=row["dif_seq_media_max"],
            atr_atual=row["atr_atual"],
            atr_media=row["atr_media"],
            atr_maximo=row["atr_maximo"],
            dif_atr_media_atual=row["dif_atr_media_atual"],
            dif_atr_media_max=row["dif_atr_media_max"],
            data_criacao=row["data_criacao"]
        )

    # Exibir e salvar a tabela consolidada
    # print(final_consolidated.to_csv(sep='\t', index=False))


def stats_delays_by_match(results_list):
    global time_casa, time_visitante, match, time

    match_delay_data = defaultdict(lambda: defaultdict(Counter))

    # Variáveis para rastrear atrasos
    current_delays = defaultdict(int)  # Armazena o atraso atual por resultado

    for time_casa, time_visitante, resultado_partida in results_list:
        match = f"{time_casa} vs {time_visitante}"
        resultado = resultado_partida

        # Atualizar atrasos para cada tipo de resultado
        for res in [time_casa, time_visitante, "Empate"]:
            if res == resultado:
                # Se o resultado ocorreu, zerar o atraso atual
                delay = current_delays[res]
                if delay > 0:
                    match_delay_data[match][res][delay] += 1
                current_delays[res] = 0
            else:
                # Se o resultado não ocorreu, incrementar o atraso atual
                current_delays[res] += 1

        # Atualizar "current_delay" no dicionário de dados
        for res in [time_casa, time_visitante, "Empate"]:
            match_delay_data[match][res]["current_delay"] = current_delays[res]

    # Finalizar atrasos pendentes
    for match in match_delay_data:
        for res in match_delay_data[match]:
            delay = match_delay_data[match][res]["current_delay"]
            if delay > 0:
                match_delay_data[match][res][delay] += 1
                match_delay_data[match][res]["current_delay"] = delay

    # Preparar os dados detalhados
    detailed_data = []

    for match, results in match_delay_data.items():
        for resultado, counters in results.items():
            delays = [delay_len for delay_len in counters if isinstance(delay_len, int)]

            # Calcular métricas para atrasos
            current_delay = counters["current_delay"] if "current_delay" in counters else 0

            max_delay = max(delays) if delays else 0
            max_delay_current = select_max_atraso_partida(time_casa, time_visitante, resultado)

            mean_delay = int(mean(delays)) if delays else 0
            dif_atr_media_atual = mean_delay - current_delay
            dif_atr_media_max = max_delay - mean_delay

            if max_delay_current > max_delay:
                max_delay = max_delay_current

            detailed_data.append({
                "time_casa": time_casa,
                "time_visitante": time_visitante,
                "resultado": resultado,
                "atr_atual": current_delay,
                "atr_media": mean_delay,
                "atr_maximo": max_delay,
                "dif_atr_media_atual": dif_atr_media_atual,
                "dif_atr_media_max": dif_atr_media_max,
            })

    return detailed_data


def stats_delays_by_team(results_list):
    global time_casa, time_visitante, match, time

    match_delay_data = defaultdict(lambda: defaultdict(Counter))

    # Variáveis para rastrear atrasos
    current_delays = defaultdict(int)  # Armazena o atraso atual por resultado

    for time, resultado in results_list:
        # Atualizar atrasos para cada tipo de resultado
        for res in ["Venceu", "Perdeu", "Empatou"]:
            if res == resultado:
                # Se o resultado ocorreu, zerar o atraso atual
                delay = current_delays[res]
                if delay > 0:
                    match_delay_data[time][res][delay] += 1
                current_delays[res] = 0
            else:
                # Se o resultado não ocorreu, incrementar o atraso atual
                current_delays[res] += 1

        # Atualizar "current_delay" no dicionário de dados
        for res in ["Venceu", "Perdeu", "Empatou"]:
            match_delay_data[time][res]["current_delay"] = current_delays[res]

    # Finalizar atrasos pendentes
    for time in match_delay_data:
        for res in match_delay_data[time]:
            delay = match_delay_data[time][res]["current_delay"]
            if delay > 0:
                match_delay_data[time][res][delay] += 1
                match_delay_data[time][res]["current_delay"] = delay

    # Preparar os dados detalhados
    detailed_data = []

    for time, results in match_delay_data.items():
        for resultado, counters in results.items():
            delays = [delay_len for delay_len in counters if isinstance(delay_len, int)]

            # Calcular métricas para atrasos
            current_delay = counters["current_delay"] if "current_delay" in counters else 0
            max_delay = max(delays) if delays else 0
            max_delay_current = select_max_atraso_time(time, resultado)
            mean_delay = int(mean(delays)) if delays else 0
            dif_atr_media_atual = mean_delay - current_delay
            dif_atr_media_max = max_delay - mean_delay

            if max_delay_current > max_delay:
                max_delay = max_delay_current

            detailed_data.append({
                "nome_time": time,
                "resultado": resultado,
                "atr_atual": current_delay,
                "atr_media": mean_delay,
                "atr_maximo": max_delay,
                "dif_atr_media_atual": dif_atr_media_atual,
                "dif_atr_media_max": dif_atr_media_max,
            })

    return detailed_data


def stats_percentages_by_match(data, last_n=50):
    # print("stats_percentages_by_match")
    # Ensure the DataFrame has the required columns
    required_columns = {'time_casa', 'time_visitante', 'resultado'}
    if not required_columns.issubset(data.columns):
        raise ValueError(f"Input DataFrame must contain the following columns: {required_columns}")

    # Compute partial statistics based on the last N matches
    partial_data = data.tail(last_n)

    if partial_data.empty:
        raise ValueError("Not enough data to calculate partial statistics.")

    partial_stats = (
        partial_data.groupby(['time_casa', 'time_visitante', 'resultado'])
        .size()
        .reset_index(name='qtd_parcial')
    )
    partial_stats['perc_parcial'] = (
            partial_stats['qtd_parcial'] / partial_stats.groupby(['time_casa', 'time_visitante'])['qtd_parcial'].transform('sum') * 100
    )

    # Exclude the last N matches from the total statistics
    total_data = data.iloc[:-last_n]

    total_stats = (
        total_data.groupby(['time_casa', 'time_visitante', 'resultado'])
        .size()
        .reset_index(name='qtd_total')
    )
    total_stats['perc_total'] = (
            total_stats['qtd_total'] / total_stats.groupby(['time_casa', 'time_visitante'])['qtd_total'].transform('sum') * 100
    )

    # Merge total and partial statistics
    stats = pd.merge(
        total_stats,
        partial_stats,
        on=['time_casa', 'time_visitante', 'resultado'],
        how='outer'
    ).fillna(0)

    # Compute the difference between total and partial statistics
    stats['dif_perc_total_parcial'] = stats['perc_parcial'] - stats['perc_total']

    # Format the output as requested
    stats = stats[
        ['time_casa', 'time_visitante', 'resultado', 'qtd_total', 'perc_total', 'qtd_parcial', 'perc_parcial',
         'dif_perc_total_parcial']]

    # Format percentages to two decimal places
    stats['perc_total'] = stats['perc_total'].map('{:.2f}'.format)
    stats['perc_parcial'] = stats['perc_parcial'].map('{:.2f}'.format)
    stats['dif_perc_total_parcial'] = stats['dif_perc_total_parcial'].map('{:.2f}'.format)

    return stats


def stats_percentages_by_team(data, last_n=50):
    # print("stats_percentages_by_team")
    # Ensure the DataFrame has the required columns
    required_columns = {'nome_time', 'resultado'}

    if not required_columns.issubset(data.columns):
        raise ValueError(f"Input DataFrame must contain the following columns: {required_columns}")

    # Compute partial statistics based on the last N matches
    partial_data = data.tail(last_n)
    if partial_data.empty:
        raise ValueError("Not enough data to calculate partial statistics.")

    partial_stats = (
        partial_data.groupby(['nome_time', 'resultado'])
        .size()
        .reset_index(name='qtd_parcial')
    )
    partial_stats['perc_parcial'] = (
            partial_stats['qtd_parcial'] / partial_stats.groupby(['nome_time'])['qtd_parcial'].transform('sum') * 100
    )

    # Exclude the last N matches from the total statistics
    total_data = data.iloc[:-last_n]
    total_stats = (
        total_data.groupby(['nome_time', 'resultado'])
        .size()
        .reset_index(name='qtd_total')
    )
    total_stats['perc_total'] = (
            total_stats['qtd_total'] / total_stats.groupby(['nome_time'])['qtd_total'].transform('sum') * 100
    )

    # Merge total and partial statistics
    stats = pd.merge(
        total_stats,
        partial_stats,
        on=['nome_time', 'resultado'],
        how='outer'
    ).fillna(0)

    # Compute the difference between total and partial statistics
    stats['dif_perc_total_parcial'] = stats['perc_parcial'] - stats['perc_total']

    # Format the output as requested
    stats = stats[
        ['nome_time', 'resultado', 'qtd_total', 'perc_total', 'qtd_parcial', 'perc_parcial',
         'dif_perc_total_parcial']]

    # Format percentages to two decimal places
    stats['perc_total'] = stats['perc_total'].map('{:.2f}'.format)
    stats['perc_parcial'] = stats['perc_parcial'].map('{:.2f}'.format)
    stats['dif_perc_total_parcial'] = stats['dif_perc_total_parcial'].map('{:.2f}'.format)

    return stats


def stats_sequences_by_match(results_list):
    # print("stats_sequences_by_match")
    global time_casa, time_visitante, match
    match_sequence_data = defaultdict(lambda: defaultdict(Counter))

    # Initialize tracking variables for sequences
    last_result = None
    current_streak = 0
    streaks_by_result = defaultdict(int)

    for time_casa, time_visitante, descricao_resultado in results_list:
        match = f"{time_casa} vs {time_visitante}"
        resultado = descricao_resultado

        if resultado == last_result:
            current_streak += 1
        else:
            if last_result is not None:
                streaks_by_result[last_result] = current_streak
                match_sequence_data[match][last_result][current_streak] += 1
            last_result = resultado
            current_streak = 1

        match_sequence_data[match][resultado]["current_sequence"] = current_streak

    # Finalize the last streak
    if last_result is not None:
        streaks_by_result[last_result] = current_streak
        match_sequence_data[match][last_result][current_streak] += 1

    # Add calculation for additional metrics
    detailed_data = []

    for match, results in match_sequence_data.items():
        for resultado, counters in results.items():
            sequences = [seq_len for seq_len in counters if isinstance(seq_len, int)]

            # Only use the sequence lengths (ignore occurrences) for these calculations
            current_sequence = current_streak if resultado == last_result else 0
            mean_sequence = int(mean(sequences)) if sequences else 0
            max_sequence = max(sequences) if sequences else 0
            max_sequence_current = select_max_seq_partida(time_casa, time_visitante, resultado)
            dif_seq_media_atual = mean_sequence - current_sequence
            dif_seq_media_max = max_sequence - mean_sequence

            if max_sequence_current > max_sequence:
                max_sequence = max_sequence_current

            detailed_data.append({
                "time_casa": time_casa,
                "time_visitante": time_visitante,
                "resultado": resultado,
                "seq_atual": current_sequence,
                "seq_media": mean_sequence,
                "seq_maxima": max_sequence,
                "dif_seq_media_atual": dif_seq_media_atual,
                "dif_seq_media_max": dif_seq_media_max
            })


    return detailed_data


def stats_sequences_by_team(results_list):
    # print("stats_sequences_by_team")
    global match, time
    match_sequence_data = defaultdict(lambda: defaultdict(Counter))

    # Initialize tracking variables for sequences
    last_result = None
    current_streak = 0
    streaks_by_result = defaultdict(int)

    for time, resultado in results_list:
        match = f"{time}"
        if resultado == last_result:
            current_streak += 1
        else:
            if last_result is not None:
                streaks_by_result[last_result] = current_streak
                match_sequence_data[match][last_result][current_streak] += 1
            last_result = resultado
            current_streak = 1

        match_sequence_data[match][resultado]["current_sequence"] = current_streak

    # Finalize the last streak
    if last_result is not None:
        streaks_by_result[last_result] = current_streak
        match_sequence_data[match][last_result][current_streak] += 1

    # Add calculation for additional metrics
    detailed_data = []

    for match, results in match_sequence_data.items():
        for resultado, counters in results.items():
            sequences = [seq_len for seq_len in counters if isinstance(seq_len, int)]

            # Only use the sequence lengths (ignore occurrences) for these calculations
            current_sequence = current_streak if resultado == last_result else 0
            mean_sequence = int(mean(sequences)) if sequences else 0
            max_sequence = max(sequences) if sequences else 0
            max_sequence_current = select_max_seq_time(time, resultado)
            dif_seq_media_atual = mean_sequence - current_sequence
            dif_seq_media_max = max_sequence - mean_sequence

            if max_sequence_current > max_sequence:
                max_sequence = max_sequence_current

            detailed_data.append({
                "nome_time": time,
                "resultado": resultado,
                "seq_atual": current_sequence,
                "seq_media": mean_sequence,
                "seq_maxima": max_sequence,
                "dif_seq_media_atual": dif_seq_media_atual,
                "dif_seq_media_max": dif_seq_media_max
            })

    return detailed_data


if __name__ == "__main__":
    process_stats_match('999999999', 'Tachira', 'Caracas')
