import pandas as pd


def stats_percentages_by_match(data, last_n=50):

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

    # Map resultado values to display team names or "Empate"
    stats['resultado'] = stats['resultado'].map({
        'Casa': stats['time_casa'].iloc[0],  # Assuming consistent naming within a group
        'Visitante': stats['time_visitante'].iloc[0],
        'Empate': 'Empate'
    })

    # Format the output as requested
    stats = stats[
        ['time_casa', 'time_visitante', 'resultado', 'qtd_total', 'perc_total', 'qtd_parcial', 'perc_parcial',
         'dif_perc_total_parcial']]

    # Format percentages to two decimal places
    stats['perc_total'] = stats['perc_total'].map('{:.2f}'.format)
    stats['perc_parcial'] = stats['perc_parcial'].map('{:.2f}'.format)
    stats['dif_perc_total_parcial'] = stats['dif_perc_total_parcial'].map('{:.2f}'.format)

    return stats
