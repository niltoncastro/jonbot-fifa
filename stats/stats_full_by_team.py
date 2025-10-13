from datetime import datetime
import pandas as pd

from database import insert_estatistica_time
from database import select_resultados_final_time
from stats import stats_delays_by_team
from stats import stats_percentages_by_team
from stats import stats_sequences_by_team


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
