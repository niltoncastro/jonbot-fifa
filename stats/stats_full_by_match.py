from datetime import datetime

import pandas as pd

from database import insert_estatistica_partida
from stats import stats_delays_by_match
from stats import stats_percentages_by_match
from stats import stats_sequences_by_match
from database import select_resultados_final_partida


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
